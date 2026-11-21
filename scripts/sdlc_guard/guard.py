"""PreToolUse decision engine shared by Claude Code and Codex payloads on every OS."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from . import commands, paths

POLICY_PATH = Path(__file__).with_name("policy.json")
REPO_ROOT = Path(__file__).resolve().parents[2]
_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$|^\*\*\* Move to: (.+?)\s*$", re.MULTILINE)


@dataclass
class Event:
    tool_name: str
    tool_input: dict[str, Any]
    cwd: str | None
    agent_type: str | None
    hook_event: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    allowed: bool
    reason: str = ""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_event(data: Mapping[str, Any]) -> Event:
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {"command": tool_input}
    return Event(
        tool_name=str(data.get("tool_name") or ""),
        tool_input=tool_input,
        cwd=data.get("cwd"),
        agent_type=data.get("agent_type") or None,
        hook_event=data.get("hook_event_name"),
        raw=dict(data),
    )


def resolve_role(event: Event, env: Mapping[str, str]) -> str:
    """Claude sends agent_type inside subagents; fall back to SDLC_ACTIVE_ROLE, then 'main'."""
    role = event.agent_type or env.get("SDLC_ACTIVE_ROLE") or "main"
    return role.rsplit(":", 1)[-1].strip() or "main"


def _command_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return " ".join(f'"{v}"' if (" " in v and '"' not in v) else v for v in value)
    return None


def event_paths(event: Event) -> list[str]:
    ti = event.tool_input
    found = [str(ti[k]) for k in ("file_path", "path", "notebook_path") if isinstance(ti.get(k), str) and ti.get(k)]
    if event.tool_name == "apply_patch":
        patch = _command_text(ti.get("command")) or str(ti.get("input") or ti.get("patch") or "")
        for m in _PATCH_FILE_RE.finditer(patch):
            found.append(m.group(1) or m.group(2))
    return found


def git_is_tracked(repo_root: str) -> Callable[[str], bool]:
    """Case-insensitive tracked-file check.

    Git pathspecs are case-sensitive, so `TESTS/Test_A.py` would look untracked on NTFS/APFS even though it
    is the same file. Read the index once and compare casefolded paths instead.
    """
    cache: dict[str, set[str] | None] = {}

    def tracked_set() -> set[str] | None:
        if "v" not in cache:
            try:
                res = subprocess.run(
                    ["git", "-C", repo_root, "ls-files", "-z"], capture_output=True, check=False, timeout=10
                )
                cache["v"] = (
                    {p.casefold() for p in res.stdout.decode("utf-8", errors="replace").split("\0") if p}
                    if res.returncode == 0
                    else None
                )
            except (OSError, subprocess.SubprocessError):
                cache["v"] = None
        return cache["v"]

    def check(rel: str) -> bool:
        files = tracked_set()
        if files is None:
            return True  # cannot prove it is new -> treat as an existing oracle (fail closed)
        return rel.replace("\\", "/").casefold() in files

    return check


def decide(
    event: Event,
    policy: Mapping[str, Any],
    env: Mapping[str, str],
    repo_root: str,
    windows_host: bool,
    is_tracked: Callable[[str], bool],
) -> Decision:
    role = resolve_role(event, env)
    role_rules: Mapping[str, Any] = policy.get("roles", {}).get(role, {})
    cwd = event.cwd or repo_root
    reasons: list[str] = []

    def check_path(raw_path: str, write: bool, _depth: int = 0) -> None:
        rel, abs_path = paths.to_repo_relative(raw_path, repo_root=repo_root, cwd=cwd, windows_host=windows_host)
        shown = rel if rel is not None else abs_path
        candidates = [c for c in (rel, abs_path) if c]
        if any(paths.matches(c, policy["secret_globs"]) for c in candidates) and not paths.matches(
            shown, policy.get("secret_allow_globs", [])
        ):
            reasons.append(f"Access to sensitive secret path is denied: {shown}")
        if write and role_rules and rel is not None:
            if role_rules.get("deny_protected_writes") and paths.matches(rel, policy["protected_globs"]):
                reasons.append(f"{role} cannot modify protected governance/contract path: {rel}")
            if paths.matches(rel, role_rules.get("ci_gate_globs", [])):
                reasons.append(f"{role} cannot modify CI gate / validator scripts: {rel} (Framework Change route)")
            if paths.matches(rel, role_rules.get("qa_artifact_globs", [])):
                reasons.append(f"Test oracle integrity rule forbids {role} from altering QA test specs: {rel}")
            mode = role_rules.get("test_code_mode", "off")
            if paths.matches(rel, role_rules.get("test_code_globs", [])) and (
                mode == "all" or (mode == "tracked" and is_tracked(rel))
            ):
                reasons.append(
                    f"Test oracle integrity rule forbids {role} from editing committed tests: {rel} "
                    "(add new test files instead, or route the change to qa-function-agent)"
                )
        # Re-check the real target of symlinks that exist on this host.
        if _depth == 0 and os.path.lexists(abs_path):
            real = os.path.realpath(abs_path)
            if paths.canonical(real, windows_host=windows_host).casefold() != abs_path.casefold():
                check_path(real, write, _depth=1)

    is_write_tool = event.tool_name in policy.get("write_tools", [])
    for p in event_paths(event):
        check_path(p, write=is_write_tool)

    command = _command_text(event.tool_input.get("command"))
    if command and event.tool_name != "apply_patch":
        family, inner = commands.detect_family(event.tool_name, command, windows_host=windows_host)
        facts = commands.analyze(inner, family)
        reasons.extend(
            commands.dangerous_command_reasons(
                facts, env, allow_force_with_lease=bool(policy.get("allow_force_with_lease", False))
            )
        )
        for tok in sorted(facts.path_tokens):
            check_path(tok, write=tok in facts.write_targets)

    reasons = list(dict.fromkeys(reasons))
    return Decision(allowed=not reasons, reason="; ".join(reasons))
