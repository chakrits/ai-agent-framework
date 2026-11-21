"""Agent trace: append-only JSONL records of what agents asked, ran and got back (Claude Code and Codex hooks).

Stored locally and gitignored (``.sdlc/traces/YYYY-MM-DD/<session>.jsonl``). Secrets are redacted and large
outputs truncated *before* anything is written. Tracing is fail-open: it never blocks a tool call (the guard
decision is independent and stays fail-closed). Timestamps are the machine's local time with a UTC offset
(e.g. ``+07:00`` in Bangkok); the day directory uses the same local date.

Settings (env > ``.sdlc/trace.json`` > default, see trace_config.py):
  SDLC_TRACE_LEVEL=off|info|debug · SDLC_TRACE_TZ=local|utc · SDLC_TRACE_RETENTION_DAYS · SDLC_TRACE_DIR
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

from . import platform_env, redact, trace_config, trace_state, version

SCHEMA_VERSION = 1
PLATFORMS = ("claude", "codex", "orchestrator")
OPERATIONS = (
    "session", "user_prompt", "execute_tool", "invoke_agent", "turn_end", "gate_decision",
    "permission", "config", "model", "compaction", "task", "notification", "other",
)
LEVELS = trace_config.LEVELS
REQUIRED_FIELDS = ("v", "ts", "level", "framework_version", "platform", "os", "session_id", "event", "operation")
LIMITS = {"info": 2048, "debug": 65536}
_PRE_CUT_SLACK = 4096  # redact a bit more than we keep so a secret straddling the cut cannot leak partially

_OPERATION_BY_EVENT = {
    "SessionStart": "session", "SessionEnd": "session",
    "UserPromptSubmit": "user_prompt", "UserPromptExpansion": "user_prompt",
    "PreToolUse": "execute_tool", "PostToolUse": "execute_tool", "PostToolUseFailure": "execute_tool", "PostToolBatch": "execute_tool",
    "SubagentStart": "invoke_agent", "SubagentStop": "invoke_agent",
    "Stop": "turn_end", "StopFailure": "turn_end", "Interrupt": "turn_end",
    "PermissionRequest": "permission", "PermissionDenied": "permission",
    "ConfigChange": "config", "InstructionsLoaded": "config", "TraceConfigChange": "config",
    "PostModelSwitch": "model", "PreModelSwitch": "model", "PostModelRequest": "model", "PreModelRequest": "model",
    "PreCompact": "compaction", "PostCompact": "compaction",
    "TaskCreated": "task", "TaskCompleted": "task",
    "Notification": "notification",
}
# payload key -> event key, copied as short redacted strings
_SHORT_FIELDS = {
    "prompt_id": "prompt_id", "turn_id": "turn_id", "permission_mode": "permission_mode", "trigger": "trigger",
    "notification_type": "notification_type", "title": "title", "memory_type": "memory_type", "load_reason": "load_reason",
    "task_id": "task_id", "task_subject": "task_subject", "status": "status", "command_name": "command_name",
    "old_cwd": "old_cwd", "new_cwd": "new_cwd", "from_model": "from_model", "to_model": "to_model",
}
_EXIT_CODE_RE = re.compile(r"^Exit code (-?\d+)", re.MULTILINE)
_WORK_ITEM_RE = re.compile(r"\bINT-\d{3,}\b")


def trace_level(env: Mapping[str, str]) -> str:
    """Level from the environment only (default info). The full precedence lives in trace_config.effective()."""
    value = (env.get("SDLC_TRACE_LEVEL") or "info").strip().lower()
    return value if value in LEVELS else "info"


def trace_root(repo_root: str | Path, env: Mapping[str, str]) -> Path:
    override = env.get("SDLC_TRACE_DIR")
    return Path(override) if override else Path(repo_root) / ".sdlc" / "traces"


def state_dir_for(repo_root: str | Path, env: Mapping[str, str]) -> Path:
    """Directory holding trace.json and state/ (sibling of the traces directory)."""
    return trace_root(repo_root, env).parent


def stamp(tz_mode: str, now: datetime | None = None) -> str:
    """ISO-8601 timestamp with millisecond precision and UTC offset (machine-local by default)."""
    if now is None:
        dt = datetime.now(timezone.utc) if tz_mode == "utc" else datetime.now(timezone.utc).astimezone()
    else:
        dt = now if now.tzinfo else now.astimezone()
        if tz_mode == "utc":
            dt = dt.astimezone(timezone.utc)
    return dt.isoformat(timespec="milliseconds")


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


def _effort_level(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("level")
    return str(value) if isinstance(value, (str, int)) and str(value) else None


def _resolve_model(payload: Mapping[str, Any], hook: str, platform: str, state: Mapping[str, Any], env: Mapping[str, str]) -> tuple[str, str]:
    """model + where it came from. Claude reports it on SessionStart / PostModelSwitch only; Codex on every event."""
    direct = payload.get("model") or (payload.get("to_model") if hook == "PostModelSwitch" else None)
    if direct:
        return str(direct), "payload"
    if state.get("model"):
        return str(state["model"]), "state"
    if platform != "codex" and env.get("ANTHROPIC_MODEL"):
        return str(env["ANTHROPIC_MODEL"]), "env"
    return "unknown", "unknown"


def build_event(
    payload: Mapping[str, Any],
    *,
    platform: str,
    env: Mapping[str, str],
    repo_root: str | Path,
    decision: Mapping[str, Any] | None = None,
    hook_event: str | None = None,
    level: str | None = None,
    tz_mode: str | None = None,
    session_state: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    level = level if level in ("info", "debug") else ("debug" if trace_level(env) == "debug" else "info")
    limit = LIMITS[level]
    state = session_state or {}
    hook = str(payload.get("hook_event_name") or hook_event or "unknown")
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    branch = read_git_branch(repo_root)
    agent_type = payload.get("agent_type")
    role = (str(agent_type) if agent_type else env.get("SDLC_ACTIVE_ROLE") or "main").rsplit(":", 1)[-1]
    model, model_source = _resolve_model(payload, hook, platform, state, env)
    effort = _effort_level(payload.get("effort"))
    effort_source = "payload"
    if not effort:
        effort, effort_source = (_effort_level(state.get("effort")), "state") if state.get("effort") else (None, "unavailable")

    event: dict[str, Any] = {
        "v": SCHEMA_VERSION,
        "ts": stamp(tz_mode or "local", now),
        "level": level,
        "framework_version": version.framework_version(),
        "platform": platform if platform in PLATFORMS else "claude",
        "os": platform_env.host_os(),
        "session_id": sanitize_session_id(payload.get("session_id")),
        "event": hook,
        "operation": _OPERATION_BY_EVENT.get(hook, "other"),
        "role": role,
        "model": model,
        "model_source": model_source,
        "effort_source": effort_source,
    }
    if effort:
        event["effort"] = effort
    for src in ("agent_type", "agent_id", "tool_name", "tool_use_id", "cwd"):
        if payload.get(src):
            event[src] = str(payload[src])
    if branch:
        event["git_branch"] = branch
    work_item = detect_work_item(env, branch)
    if work_item:
        event["work_item"] = work_item

    for src, dst in _SHORT_FIELDS.items():
        if payload.get(src) not in (None, ""):
            event[dst] = _prep(str(payload[src]), 512, env)[0]
    source = payload.get("source")
    if source:
        if hook == "ConfigChange":
            event["config_source"] = str(source)[:200]
        elif hook in ("PreModelSwitch", "PostModelSwitch"):
            event["switch_source"] = str(source)[:200]
        else:
            event["source"] = str(source)[:200]
    for src in ("file_path", "directory"):
        if isinstance(payload.get(src), str) and payload[src]:
            event["file_path"] = _prep(payload[src], 1024, env)[0]
    mcp = payload.get("mcp_server")
    mcp_name = mcp.get("name") if isinstance(mcp, dict) else (mcp if isinstance(mcp, str) else payload.get("mcp_server_name"))
    if mcp_name:
        event["mcp_server"] = str(mcp_name)[:200]
    if isinstance(payload.get("tool_calls"), list):
        event["tool_count"] = len(payload["tool_calls"])
    if isinstance(payload.get("token_usage"), dict):
        usage = {k: v for k, v in payload["token_usage"].items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        if usage:
            event["token_usage"] = usage

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
        resp = payload.get("tool_response")
        if payload.get("tool_name") == "Agent" and isinstance(resp, dict) and resp.get("resolvedModel"):
            event["subagent_model"] = str(resp["resolvedModel"])[:200]

    if hook == "StopFailure":
        if payload.get("error"):
            event["error_type"] = str(payload["error"])[:100]
        if payload.get("error_details"):
            event["error"] = _prep(payload["error_details"], limit, env)[0]
    elif payload.get("error"):
        event["error"] = _prep(payload["error"], limit, env)[0]
        m = _EXIT_CODE_RE.search(str(payload["error"]))
        if m:
            event["exit_code"] = int(m.group(1))
    if isinstance(payload.get("is_interrupt"), bool):
        event["is_interrupt"] = payload["is_interrupt"]
    if isinstance(payload.get("duration_ms"), (int, float)):
        event["duration_ms"] = payload["duration_ms"]
    if payload.get("prompt"):
        event["prompt"] = _prep(payload["prompt"], limit, env)[0]
    text = payload.get("last_assistant_message") or (payload.get("message") if isinstance(payload.get("message"), str) else None)
    if text:
        event["message"] = _prep(text, limit, env)[0]
    if payload.get("reason"):
        event["reason"] = _prep(payload["reason"], 500, env)[0]
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
    now: datetime | None = None,
) -> Path | None:
    env = os.environ if env is None else env
    state_dir = state_dir_for(repo_root, env)
    eff = trace_config.effective(env, trace_config.load(trace_config.config_path(state_dir)))
    if eff["level"] == "off":
        return None
    sid = sanitize_session_id(payload.get("session_id"))
    state = trace_state.load(state_dir, sid)
    event = build_event(
        payload, platform=platform, env=env, repo_root=repo_root, decision=decision, hook_event=hook_event,
        level=eff["level"], tz_mode=eff["tz"], session_state=state, now=now,
    )
    path = trace_root(repo_root, env) / event["ts"][:10] / f"{sid}.jsonl"
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    _locked_append(path, line.encode("utf-8"))  # the event comes first: it must never be lost to a state-file problem
    updates = {
        key: event[key]
        for key in ("model", "effort")
        if event.get(key) and event.get(f"{key}_source") == "payload" and state.get(key) != event[key]
    }
    if updates:
        try:
            trace_state.save(state_dir, sid, {**state, **updates})
        except OSError:
            pass  # e.g. Windows: another hook holds the state file; the next event re-derives it from its own payload
    return path


def safe_record(*args: Any, **kwargs: Any) -> Path | None:
    """Tracing must never break or block a hook."""
    try:
        return record(*args, **kwargs)
    except Exception:  # noqa: BLE001
        return None


def retention_days(env: Mapping[str, str]) -> int:
    """Retention from the environment only (default 30); see trace_config.effective() for the full precedence."""
    return trace_config.effective(env, {})["retention_days"]


def cleanup(root: Path, retention_days: int, now: datetime | None = None) -> int:
    """Delete day directories older than ``retention_days``; returns how many were removed."""
    if not root.is_dir():
        return 0
    cutoff = ((now or datetime.now(timezone.utc).astimezone()) - timedelta(days=retention_days)).date()
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


def maintenance(repo_root: str | Path, env: Mapping[str, str] | None = None) -> dict[str, int]:
    """Housekeeping run at SessionStart: apply retention to trace days and session state files."""
    env = os.environ if env is None else env
    state_dir = state_dir_for(repo_root, env)
    days = trace_config.effective(env, trace_config.load(trace_config.config_path(state_dir)))["retention_days"]
    return {
        "traces_removed": cleanup(trace_root(repo_root, env), days),
        "state_removed": trace_state.cleanup(state_dir, days),
    }
