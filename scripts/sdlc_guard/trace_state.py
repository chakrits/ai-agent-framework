"""Per-session trace state (.sdlc/state/<session>.json): remembers the last known model and effort.

Claude Code only reports ``model`` on SessionStart / PostModelSwitch and ``effort`` on events with a tool context,
and every hook is a fresh process, so the last known values are persisted here and attached to later events.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def state_file(state_dir: str | Path, session_id: str) -> Path:
    return Path(state_dir) / "state" / f"{session_id}.json"


def load(state_dir: str | Path, session_id: str) -> dict[str, Any]:
    try:
        data = json.loads(state_file(state_dir, session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(state_dir: str | Path, session_id: str, data: dict[str, Any]) -> None:
    path = state_file(state_dir, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)  # atomic on POSIX and Windows


def cleanup(state_dir: str | Path, retention_days: int, now: datetime | None = None) -> int:
    """Delete state files not touched for ``retention_days`` days; returns the number removed."""
    folder = Path(state_dir) / "state"
    if not folder.is_dir():
        return 0
    cutoff = ((now.timestamp() if now else datetime.now().timestamp())) - retention_days * 86400
    removed = 0
    for f in folder.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        except OSError:
            continue
    return removed
