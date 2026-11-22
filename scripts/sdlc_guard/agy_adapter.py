"""Adapter normalizing Antigravity (agy) camelCase hooks.json payloads and stdout JSON responses."""

from __future__ import annotations

import json
from typing import Any, Mapping

_TOOL_NAME_MAP: dict[str, str] = {
    "run_command": "Bash",
    "write_to_file": "Write",
    "replace_file_content": "Edit",
    "multi_replace_file_content": "Edit",
    "view_file": "Read",
    "view_file_outline": "Read",
    "view_code_item": "Read",
}


def _map_tool_input(args: Mapping[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    if isinstance(args.get("CommandLine"), str):
        mapped["command"] = args["CommandLine"]
    elif isinstance(args.get("command"), str):
        mapped["command"] = args["command"]

    for key in ("TargetFile", "AbsolutePath", "Path", "file_path", "path"):
        val = args.get(key)
        if isinstance(val, str) and val:
            mapped["file_path"] = val
            break

    if not mapped and args:
        return dict(args)
    return mapped


def normalize_payload(raw: Mapping[str, Any], default_event: str | None = None) -> dict[str, Any]:
    """Translate Antigravity camelCase stdin JSON into canonical SDLC hook payload keys."""
    out: dict[str, Any] = dict(raw)

    if "session_id" not in out and raw.get("conversationId"):
        out["session_id"] = raw["conversationId"]
    if "hook_event_name" not in out:
        out["hook_event_name"] = raw.get("hookEventName") or default_event or "unknown"
    if "model" not in out and raw.get("modelName"):
        out["model"] = raw["modelName"]
    if "prompt" not in out and raw.get("lastUserInput"):
        out["prompt"] = raw["lastUserInput"]

    tool_call = raw.get("toolCall")
    if isinstance(tool_call, Mapping):
        raw_name = str(tool_call.get("name") or "")
        out.setdefault("tool_name", _TOOL_NAME_MAP.get(raw_name, raw_name))
        if tool_call.get("id") and "tool_use_id" not in out:
            out["tool_use_id"] = tool_call["id"]
        args = tool_call.get("args")
        if isinstance(args, Mapping) and "tool_input" not in out:
            out["tool_input"] = _map_tool_input(args)

    if out.get("hook_event_name") == "PostToolUse" and "tool_response" not in out and raw.get("error"):
        out["tool_response"] = {"stdout": "", "stderr": str(raw["error"]), "exit_code": 1}

    if raw.get("terminationReason") and "reason" not in out:
        out["reason"] = raw["terminationReason"]

    return out


def format_pretooluse_decision(allowed: bool, reason: str = "") -> str:
    """Render Antigravity PreToolUse stdout JSON."""
    payload: dict[str, Any] = {"decision": "allow" if allowed else "deny"}
    if not allowed and reason:
        payload["reason"] = reason
    return json.dumps(payload, ensure_ascii=False)


def format_empty_response() -> str:
    """Render empty JSON acknowledgment expected by PostToolUse / Stop hooks."""
    return "{}"
