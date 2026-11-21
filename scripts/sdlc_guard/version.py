"""Framework version (single source: version.txt at the repository root, managed by release-please)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def framework_version(root: Path = ROOT) -> str:
    try:
        return (root / "version.txt").read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"
