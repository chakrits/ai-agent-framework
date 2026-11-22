#!/usr/bin/env python3
"""Enforce context-window line budgets on entrypoints, canonical agents, and skills."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUDGETS: list[tuple[str, int]] = [
    ("AGENTS.md", 500),
    ("CLAUDE.md", 80),
    (".agents/agents/*.md", 120),
    (".agents/skills/*/SKILL.md", 150),
    (".agents/workflows/*.md", 120),
]


def check_context_budgets(root: Path = ROOT) -> list[str]:
    """Return a list of violation strings if any instruction file exceeds its line budget."""
    violations: list[str] = []
    for pattern, max_lines in BUDGETS:
        matches = sorted(root.glob(pattern))
        if not matches:
            violations.append(f"No files matched required pattern: {pattern}")
            continue
        for path in matches:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > max_lines:
                rel = path.relative_to(root)
                violations.append(f"{rel}: {line_count} lines exceeds budget of {max_lines}")
    return violations


def main() -> int:
    violations = check_context_budgets()
    if violations:
        print("Context budget check FAILED:", file=sys.stderr)
        for item in violations:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("Context budget check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
