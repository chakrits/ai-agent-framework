"""Conventional Commits check for the git ``commit-msg`` hook (release-please derives versions from these)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
_HEADER = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([A-Za-z0-9._/-]+\))?!?: \S.*$")
_PASS_THROUGH = ("Merge ", 'Revert "', "fixup! ", "squash! ", "amend! ")


def check(message: str) -> str | None:
    """Return an error message, or None when the first non-comment line is acceptable."""
    for line in message.splitlines():
        if line.startswith("#"):
            continue
        header = line.rstrip()
        if not header:
            continue
        if header.startswith(_PASS_THROUGH) or _HEADER.match(header):
            return None
        return (
            f"Commit message does not follow Conventional Commits: {header!r}\n"
            f"  Expected: <type>(<optional scope>)!: <subject>   with type one of: {', '.join(TYPES)}\n"
            "  Example:  fix(guard): resolve relative hook cwd against repo root"
        )
    return "Commit message is empty (expected a Conventional Commits header)."


def main(args: list[str]) -> int:
    if not args:
        print("usage: sdlc_hook.py commit-msg <message-file>", file=sys.stderr)
        return 2
    try:
        message = Path(args[0]).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"commit-msg: cannot read {args[0]}: {exc}", file=sys.stderr)
        return 2
    error = check(message)
    if error:
        print(f"commit-msg BLOCKED: {error}", file=sys.stderr)
        return 1
    return 0
