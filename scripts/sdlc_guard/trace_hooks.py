"""Single source of truth for which hook events carry the agent trace on Claude Code and Codex.

Tier 1: registered by default (low volume, high audit value). Tier 2: opt-in per group via
`scripts/sdlc_trace.py hooks enable <group>` (written to the user's gitignored .claude/settings.local.json).
Never trace: WorktreeCreate / WorktreeRemove (a hook replaces git's worktree handling), MessageDisplay
(fires per streamed delta), Setup (only for --init). Trace handlers print nothing and always exit 0, so they
never alter decisions of hooks that can make them (PermissionRequest, ConfigChange, PreCompact, ...).
"""

from __future__ import annotations

from typing import Any

CLAUDE_COMMAND = 'sh "$CLAUDE_PROJECT_DIR/scripts/bin/sdlc-hook" {sub} --platform claude'

CLAUDE_TIER1_ASYNC = (
    "UserPromptSubmit", "PostToolUse", "PostToolUseFailure", "SubagentStart", "SubagentStop", "Stop", "StopFailure",
    "PostModelSwitch", "PermissionRequest", "PermissionDenied", "ConfigChange", "InstructionsLoaded",
    "PreCompact", "PostCompact", "Notification", "TaskCreated", "TaskCompleted",
)
CLAUDE_TIER1_SYNC = ("SessionEnd",)
CLAUDE_MATCH_ALL_TOOLS = ("PostToolUse", "PostToolUseFailure")
CLAUDE_TIER2: dict[str, tuple[str, ...]] = {
    "cwd": ("CwdChanged",),
    "commands": ("UserPromptExpansion",),
    "batch": ("PostToolBatch",),
    "elicitation": ("Elicitation", "ElicitationResult"),
    "directories": ("DirectoryAdded",),
    "model-switch": ("PreModelSwitch",),
}
CODEX_TIER1_ASYNC = (
    "UserPromptSubmit", "PostToolUse", "SubagentStart", "SubagentStop", "Stop",
    "PermissionRequest", "PostModelRequest", "PreCompact", "PostCompact", "Interrupt",
)
CODEX_TIER1_SYNC = ("SessionEnd",)
FORBIDDEN_TRACE_EVENTS = ("WorktreeCreate", "WorktreeRemove", "MessageDisplay", "Setup")

CLAUDE_PERMISSIONS_ALLOW = (
    "Bash(git status*)", "Bash(git diff*)", "Bash(python3 scripts/*)", "Bash(python scripts/*)", "Bash(py -3 scripts/*)",
    "Bash(python3 -m unittest*)", "Bash(python -m unittest*)", "Bash(py -3 -m unittest*)",
    "Bash(python3 evals/*)", "Bash(python evals/*)", "Bash(sh scripts/bin/sdlc-hook *)",
)


def claude_handler(sub: str, *, timeout: int = 10, background: bool = False) -> dict[str, Any]:
    handler: dict[str, Any] = {"type": "command", "command": CLAUDE_COMMAND.format(sub=sub), "timeout": timeout}
    if background:
        handler["async"] = True
    return handler


def claude_trace_entry(event: str) -> dict[str, Any]:
    """One settings entry for a trace-only hook (silent, async, never blocks)."""
    entry: dict[str, Any] = {"hooks": [claude_handler("trace", background=True)]}
    if event in CLAUDE_MATCH_ALL_TOOLS:
        entry = {"matcher": "*", **entry}
    return entry


def render_claude_settings() -> dict[str, Any]:
    """The complete, generated .claude/settings.json (do not edit by hand; run scripts/sync-adapters.py --sync)."""
    hooks: dict[str, Any] = {
        "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [claude_handler("session-start", timeout=30)]}],
        "UserPromptSubmit": [claude_trace_entry("UserPromptSubmit")],
        "PreToolUse": [{
            "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell|Read",
            "hooks": [claude_handler("pretooluse", timeout=30)],
        }],
    }
    for event in CLAUDE_TIER1_ASYNC:
        hooks.setdefault(event, [claude_trace_entry(event)])
    for event in CLAUDE_TIER1_SYNC:
        hooks[event] = [{"hooks": [claude_handler("trace")]}]
    return {"permissions": {"allow": list(CLAUDE_PERMISSIONS_ALLOW)}, "hooks": hooks}
