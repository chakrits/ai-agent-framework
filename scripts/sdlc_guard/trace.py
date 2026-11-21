"""Agent trace: append-only JSONL records of what agents asked, ran and got back (Claude Code and Codex hooks).

Stored locally and gitignored (``.sdlc/traces/YYYY-MM-DD/<session>.jsonl``). Secrets are redacted and large
outputs truncated *before* anything is written. Tracing is fail-open: it never blocks a tool call (the guard
decision is independent and stays fail-closed).

Env: SDLC_TRACE_LEVEL=off|info|debug (default info) · SDLC_TRACE_DIR · SDLC_TRACE_RETENTION_DAYS (default 30)
     SDLC_WORK_ITEM (e.g. INT-001; otherwise derived from the git branch name)
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from . import platform_env, redact, version

SCHEMA_VERSION = 1
PLATFORMS = ("claude", "codex", "orchestrator")
OPERATIONS = ("session", "user_prompt", "execute_tool", "invoke_agent", "turn_end", "gate_decision", "other")
LEVELS = ("off", "info", "debug")
REQUIRED_FIELDS = ("v", "ts", "level", "framework_version", "platform", "os", "session_id", "event", "operation")
LIMITS = {"info": 2048, "debug": 65536}
_PRE_CUT_SLACK = 4096  # redact a bit more than we keep so a secret straddling the cut cannot leak partially

_OPERATION_BY_EVENT = {
    "SessionStart": "session",
    "SessionEnd": "session",
    "UserPromptSubmit": "user_prompt",
    "PreToolUse": "execute_tool",
    "PostToolUse": "execute_tool",
    "PostToolUseFailure": "execute_tool",
    "PermissionRequest": "execute_tool",
    "SubagentStart": "invoke_agent",
    "SubagentStop": "invoke_agent",
    "Stop": "turn_end",
}
_EXIT_CODE_RE = re.compile(r"^Exit code (-?\d+)", re.MULTILINE)
_WORK_ITEM_RE = re.compile(r"\bINT-\d{3,}\b")


def trace_level(env: Mapping[str, str]) -> str:
    value = (env.get("SDLC_TRACE_LEVEL") or "info").strip().lower()
    return value if value in LEVELS else "info"


def trace_root(repo_root: str | Path, env: Mapping[str, str]) -> Path:
    override = env.get("SDLC_TRACE_DIR")
    return Path(override) if override else Path(repo_root) / ".sdlc" / "traces"


def sanitize_session_id(value: Any) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", str(value or ""))[:64]
    return cleaned or "unknown"


def read_git_branch(repo_root: str | Path) -> str | None:
    """Current branch (or short detached SHA) read straight from .git without spawning git."""
    git = Path(repo_root) / ".git"
    try:
        if git.is_file():
            text = git.read_text(encoding="utf-8").strip()
            if text.startswith("gitdir:"):
                target = Path(text[len("gitdir:") :].strip())
                git = target if target.is_absolute() else Path(repo_root) / target
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return head[len("ref: refs/heads/") :] if head.startswith("ref: refs/heads/") else head[:12] or None


def detect_work_item(env: Mapping[str, str], branch: str | None) -> str | None:
    explicit = (env.get("SDLC_WORK_ITEM") or "").strip()
    if _WORK_ITEM_RE.fullmatch(explicit):
        return explicit
    m = _WORK_ITEM_RE.search(branch or "")
    return m.group(0) if m else None


def _prep(text: Any, limit: int, env: Mapping[str, str]) -> tuple[str, bool, int]:
    """Truncate (with slack) -> redact -> truncate. Returns (text, truncated, original_bytes)."""
    s = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False, default=str)
    size = len(s.encode("utf-8", errors="replace"))
    pre, _, _ = redact.truncate(s, limit + _PRE_CUT_SLACK)
    cleaned = redact.redact(pre, env)
    out, _, _ = redact.truncate(cleaned, limit)
    return out, size > limit, size


def _response_parts(resp: Any) -> tuple[Any, Any, int | None]:
    """Normalize a tool_response (Claude dict / Codex string or dict) into (stdout, stderr, exit_code)."""
    if resp is None:
        return "", "", None
    exit_code = None
    if isinstance(resp, dict):
        for key in ("exit_code", "exitCode", "returncode"):
            if isinstance(resp.get(key), int):
                exit_code = resp[key]
        if "stdout" in resp or "stderr" in resp:
            return resp.get("stdout") or "", resp.get("stderr") or "", exit_code
    return resp, "", exit_code


def build_event(
    payload: Mapping[str, Any],
    *,
    platform: str,
    env: Mapping[str, str],
    repo_root: str | Path,
    decision: Mapping[str, Any] | None = None,
    hook_event: str | None = None,
) -> dict[str, Any]:
    level = trace_level(env)
    limit = LIMITS.get(level, LIMITS["info"])
    hook = str(payload.get("hook_event_name") or hook_event or "unknown")
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    branch = read_git_branch(repo_root)
    agent_type = payload.get("agent_type")
    role = (str(agent_type) if agent_type else env.get("SDLC_ACTIVE_ROLE") or "main").rsplit(":", 1)[-1]

    event: dict[str, Any] = {
        "v": SCHEMA_VERSION,
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "level": level,
        "framework_version": version.framework_version(),
        "platform": platform if platform in PLATFORMS else "claude",
        "os": platform_env.host_os(),
        "session_id": sanitize_session_id(payload.get("session_id")),
        "event": hook,
        "operation": _OPERATION_BY_EVENT.get(hook, "other"),
        "role": role,
    }
    for src, dst in (("agent_type", "agent_type"), ("agent_id", "agent_id"), ("tool_name", "tool_name"),
                     ("tool_use_id", "tool_use_id"), ("cwd", "cwd")):
        if payload.get(src):
            event[dst] = str(payload[src])
    if branch:
        event["git_branch"] = branch
    work_item = detect_work_item(env, branch)
    if work_item:
        event["work_item"] = work_item

    if tool_input:
        inp: dict[str, Any] = {}
        if tool_input.get("command") is not None:
            command = tool_input["command"]
            command = command if isinstance(command, str) else json.dumps(command, ensure_ascii=False)
            inp["command"] = _prep(command, limit, env)[0]
        for key in ("file_path", "path", "notebook_path"):
            if isinstance(tool_input.get(key), str):
                inp[key] = _prep(tool_input[key], 1024, env)[0]
        if not inp:  # e.g. MCP tools: keep a short summary of the arguments even at info level
            inp["summary"] = _prep(tool_input, 512, env)[0]
        event["input"] = inp
        if level == "debug":
            event["input_raw"] = _prep(tool_input, limit, env)[0]

    if "tool_response" in payload:
        stdout, stderr, exit_code = _response_parts(payload.get("tool_response"))
        out_text, t1, s1 = _prep(stdout, limit, env)
        err_text, t2, s2 = _prep(stderr, limit, env)
        event["output"] = {"stdout": out_text, "stderr": err_text, "truncated": t1 or t2, "bytes": s1 + s2}
        if exit_code is not None:
            event["exit_code"] = exit_code
    if payload.get("error"):
        error, _, _ = _prep(payload["error"], limit, env)
        event["error"] = error
        m = _EXIT_CODE_RE.search(str(payload["error"]))
        if m:
            event["exit_code"] = int(m.group(1))
    if isinstance(payload.get("is_interrupt"), bool):
        event["is_interrupt"] = payload["is_interrupt"]
    if isinstance(payload.get("duration_ms"), (int, float)):
        event["duration_ms"] = payload["duration_ms"]
    if payload.get("prompt"):
        event["prompt"] = _prep(payload["prompt"], limit, env)[0]
    if payload.get("last_assistant_message"):
        event["message"] = _prep(payload["last_assistant_message"], limit, env)[0]
    for key in ("reason", "source"):
        if payload.get(key):
            event[key] = str(payload[key])[:200]
    if decision is not None:
        event["decision"] = {
            "allowed": bool(decision.get("allowed")),
            "reasons": [_prep(r, 500, env)[0] for r in decision.get("reasons", [])],
        }
    return event


def validate_event(event: Mapping[str, Any]) -> list[str]:
    errors = [f"missing required field: {f}" for f in REQUIRED_FIELDS if f not in event]
    if event.get("platform") not in PLATFORMS:
        errors.append(f"invalid platform: {event.get('platform')!r}")
    if event.get("operation") not in OPERATIONS:
        errors.append(f"invalid operation: {event.get('operation')!r}")
    if event.get("v") != SCHEMA_VERSION:
        errors.append(f"unsupported schema version: {event.get('v')!r}")
    return errors


def _locked_append(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+b") as fh:
        locked = False
        try:
            if os.name == "nt":
                import msvcrt

                fh.seek(1 << 30)  # lock a byte far past EOF so readers of real data are never blocked
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            locked = True
        except (OSError, ImportError):
            pass  # best effort: a single O_APPEND write is still effectively atomic for small lines
        try:
            fh.seek(0, os.SEEK_END)
            fh.write(data)
            fh.flush()
        finally:
            if locked:
                try:
                    if os.name == "nt":
                        import msvcrt

                        fh.seek(1 << 30)
                        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                except (OSError, ImportError):
                    pass


def record(
    payload: Mapping[str, Any],
    *,
    platform: str,
    repo_root: str | Path,
    env: Mapping[str, str] | None = None,
    decision: Mapping[str, Any] | None = None,
    hook_event: str | None = None,
) -> Path | None:
    env = os.environ if env is None else env
    if trace_level(env) == "off":
        return None
    event = build_event(payload, platform=platform, env=env, repo_root=repo_root, decision=decision, hook_event=hook_event)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = trace_root(repo_root, env) / day / f"{event['session_id']}.jsonl"
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    _locked_append(path, line.encode("utf-8"))
    return path


def safe_record(*args: Any, **kwargs: Any) -> Path | None:
    """Tracing must never break or block a hook."""
    try:
        return record(*args, **kwargs)
    except Exception:  # noqa: BLE001
        return None


def retention_days(env: Mapping[str, str]) -> int:
    try:
        return max(1, int(env.get("SDLC_TRACE_RETENTION_DAYS", "30")))
    except ValueError:
        return 30


def cleanup(root: Path, retention_days: int, now: datetime | None = None) -> int:
    """Delete day directories older than ``retention_days``; returns how many were removed."""
    if not root.is_dir():
        return 0
    cutoff = ((now or datetime.now(timezone.utc)) - timedelta(days=retention_days)).date()
    removed = 0
    for child in root.iterdir():
        if not child.is_dir() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", child.name):
            continue
        try:
            day = datetime.strptime(child.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        if day < cutoff:
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed
