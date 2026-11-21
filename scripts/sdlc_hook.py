#!/usr/bin/env python3
"""Single cross-platform entrypoint for SDLC hooks (Claude Code, Codex, git) on Windows/macOS/Linux/WSL.

Usage:
  sdlc_hook.py pretooluse   [--platform claude|codex]   # reads hook JSON on stdin; exit 2 = block
  sdlc_hook.py session-start [--platform claude|codex]  # SessionStart doctor + trace (never blocks)
  sdlc_hook.py trace        [--platform claude|codex]   # record any hook event as an agent trace (never blocks)
  sdlc_hook.py traces list|show|summary|export ...      # inspect local traces (scripts/sdlc_trace.py)
  sdlc_hook.py commit-msg FILE                          # Conventional Commits check (git commit-msg hook)
  sdlc_hook.py --version
  sdlc_hook.py doctor [--json] [--strict]
  sdlc_hook.py precommit
  sdlc_hook.py setup
  sdlc_hook.py --check-path PATH | --check-cmd COMMAND | --pre-commit   # legacy flags
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_guard import guard, platform_env, trace, version  # noqa: E402

BLOCK = 2


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _read_stdin() -> str:
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    return sys.stdin.buffer.read().decode("utf-8", errors="replace")


def _repo_root() -> str:
    return os.environ.get("SDLC_REPO_ROOT") or str(guard.REPO_ROOT)


def _read_stdin_timeout(seconds: float = 2.0) -> str:
    """Read stdin without ever hanging a hook if the parent leaves the pipe open."""
    import threading

    box: list[str] = []
    t = threading.Thread(target=lambda: box.append(_read_stdin()), daemon=True)
    t.start()
    t.join(seconds)
    return box[0] if box else ""


def _trace(payload: dict, platform: str, decision: guard.Decision | None = None) -> None:
    trace.safe_record(
        payload,
        platform=platform,
        repo_root=_repo_root(),
        env=os.environ,
        decision=None if decision is None else {"allowed": decision.allowed, "reasons": list(decision.reasons)},
    )


def _evaluate(payload: dict, platform: str = "claude", record: bool = False) -> int:
    root = _repo_root()
    decision = guard.decide(
        guard.parse_event(payload),
        policy=guard.load_policy(),
        env=os.environ,
        repo_root=root,
        windows_host=platform_env.is_windows_host(),
        is_tracked=guard.git_is_tracked(root),
    )
    if record:
        _trace(payload, platform, decision)
    if decision.allowed:
        return 0
    print(f"BLOCKED: {decision.reason}", file=sys.stderr)
    return BLOCK


def _fail_closed(exc: BaseException) -> int:
    if os.environ.get("SDLC_GUARD_FAIL_OPEN") == "1":
        print(f"WARNING: sdlc guard error ignored (SDLC_GUARD_FAIL_OPEN=1): {exc!r}", file=sys.stderr)
        return 0
    print(f"BLOCKED: sdlc guard internal error (fail-closed): {exc!r}", file=sys.stderr)
    return BLOCK


def cmd_pretooluse(platform: str = "claude") -> int:
    raw = _read_stdin()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("hook payload must be a JSON object")
        return _evaluate(payload, platform, record=True)
    except Exception as exc:  # noqa: BLE001 - guard must fail closed on any error
        return _fail_closed(exc)


def cmd_trace(platform: str) -> int:
    """Record a hook event. Always exits 0: tracing must never break or block the agent."""
    try:
        raw = _read_stdin_timeout()
        payload = json.loads(raw) if raw.strip() else {}
        if isinstance(payload, dict):
            _trace(payload, platform)
    except Exception:  # noqa: BLE001
        pass
    return 0


def main(argv: list[str]) -> int:
    _configure_stdio()
    if not argv:
        return cmd_pretooluse()

    head, rest = argv[0], argv[1:]
    platform = "claude"
    if "--platform" in rest:
        idx = rest.index("--platform")
        platform = rest[idx + 1] if idx + 1 < len(rest) else platform

    if head in {"--version", "version"}:
        print(version.framework_version())
        return 0
    if head == "trace":
        return cmd_trace(platform)
    if head == "traces":
        from sdlc_guard import trace_cli

        return trace_cli.main(rest)
    if head == "commit-msg":
        from sdlc_guard import commitmsg

        return commitmsg.main(rest)

    try:
        if head in {"pretooluse", "hook"}:
            return cmd_pretooluse(platform)
        if head == "--check-path":
            return _evaluate({"tool_name": "Write", "tool_input": {"file_path": rest[0] if rest else ""}, "cwd": _repo_root()})
        if head == "--check-cmd":
            return _evaluate({"tool_name": "Bash", "tool_input": {"command": rest[0] if rest else ""}, "cwd": _repo_root()})
    except Exception as exc:  # noqa: BLE001
        return _fail_closed(exc)

    if head == "session-start":
        from sdlc_guard import doctor

        # Never block on stdin: the parent may leave the pipe open.
        try:
            raw = _read_stdin_timeout()
            payload = json.loads(raw) if raw.strip() else {}
            payload = payload if isinstance(payload, dict) else {}
            payload.setdefault("hook_event_name", "SessionStart")
            _trace(payload, platform)
            trace.cleanup(trace.trace_root(_repo_root(), os.environ), trace.retention_days(os.environ))
        except Exception:  # noqa: BLE001
            pass
        return doctor.session_start(platform=platform)
    if head == "doctor":
        from sdlc_guard import doctor

        return doctor.cli(rest)
    if head in {"precommit", "--pre-commit"}:
        from sdlc_guard import precommit

        return precommit.main()
    if head == "setup":
        from sdlc_guard import setup

        return setup.main(rest)

    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
