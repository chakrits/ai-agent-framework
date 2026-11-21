"""Local trace configuration (.sdlc/trace.json). Precedence: environment variable > config file > default.

Settings:  level (off|info|debug, optional expires_at) · tz (local|utc) · retention_days
Env:       SDLC_TRACE_LEVEL · SDLC_TRACE_TZ · SDLC_TRACE_RETENTION_DAYS
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

LEVELS = ("off", "info", "debug")
TZ_MODES = ("local", "utc")
MAX_TTL_MINUTES = 120
DEFAULT_RETENTION_DAYS = 30
CONFIG_NAME = "trace.json"
SETTABLE_KEYS = ("level", "tz", "retention_days")


def config_path(state_dir: str | Path) -> Path:
    return Path(state_dir) / CONFIG_NAME


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def parse_duration_minutes(text: str) -> int:
    """'30m' -> 30, '2h' -> 120, '45' -> 45. Raises ValueError for anything else (including zero)."""
    m = re.fullmatch(r"\s*(\d+)\s*([mh]?)\s*", str(text).lower())
    if not m:
        raise ValueError(f"invalid duration {text!r}; use e.g. 30m or 2h")
    minutes = int(m.group(1)) * (60 if m.group(2) == "h" else 1)
    if minutes < 1:
        raise ValueError("duration must be at least 1 minute")
    return minutes


def _aware_utc(now: datetime | None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc)


def _parse_dt(value: Any) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def effective(env: Mapping[str, str], cfg: Mapping[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Resolve the settings actually in force, and where each one came from."""
    now_utc = _aware_utc(now)
    out: dict[str, Any] = {"expired": False, "expires_at": None, "env_overrides": []}

    env_level = (env.get("SDLC_TRACE_LEVEL") or "").strip().lower()
    cfg_level = cfg.get("level") if cfg.get("level") in LEVELS else None
    expires = _parse_dt(cfg.get("expires_at")) if cfg.get("expires_at") else None
    if cfg_level and expires and now_utc >= expires.astimezone(timezone.utc):
        cfg_level, out["expired"] = None, True
    if env_level in LEVELS:
        out["level"], out["level_source"] = env_level, "env"
        if cfg_level and cfg_level != env_level:
            out["env_overrides"].append("level")
    elif cfg_level:
        out["level"], out["level_source"] = cfg_level, "config"
        out["expires_at"] = cfg.get("expires_at") if expires else None
    else:
        out["level"], out["level_source"] = "info", "default"

    env_tz = (env.get("SDLC_TRACE_TZ") or "").strip().lower()
    if env_tz in TZ_MODES:
        out["tz"], out["tz_source"] = env_tz, "env"
    elif cfg.get("tz") in TZ_MODES:
        out["tz"], out["tz_source"] = cfg["tz"], "config"
    else:
        out["tz"], out["tz_source"] = "local", "default"

    env_days = _positive_int(env.get("SDLC_TRACE_RETENTION_DAYS"))
    cfg_days = _positive_int(cfg.get("retention_days"))
    if env_days:
        out["retention_days"], out["retention_source"] = env_days, "env"
    elif cfg_days:
        out["retention_days"], out["retention_source"] = cfg_days, "config"
    else:
        out["retention_days"], out["retention_source"] = DEFAULT_RETENTION_DAYS, "default"
    return out


def _positive_int(value: Any) -> int | None:
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def set_level(path: Path, level: str, minutes: int | None = None, now: datetime | None = None, by: str = "human") -> dict[str, Any]:
    if level not in LEVELS:
        raise ValueError(f"level must be one of {', '.join(LEVELS)}")
    now_utc = _aware_utc(now)
    cfg = load(path)
    cfg["level"] = level
    if minutes:
        cfg["expires_at"] = (now_utc + timedelta(minutes=minutes)).isoformat(timespec="seconds")
    else:
        cfg.pop("expires_at", None)
    cfg["updated_at"], cfg["updated_by"] = now_utc.isoformat(timespec="seconds"), by
    save(path, cfg)
    return cfg


def set_value(path: Path, key: str, value: str, by: str = "human", now: datetime | None = None) -> dict[str, Any]:
    cfg = load(path)
    if key == "tz":
        if value not in TZ_MODES:
            raise ValueError(f"tz must be one of {', '.join(TZ_MODES)}")
        cfg["tz"] = value
    elif key == "retention_days":
        days = _positive_int(value)
        if not days:
            raise ValueError("retention_days must be a whole number >= 1")
        cfg["retention_days"] = days
    else:
        raise ValueError(f"unknown key {key!r}")
    cfg["updated_at"], cfg["updated_by"] = _aware_utc(now).isoformat(timespec="seconds"), by
    save(path, cfg)
    return cfg


def unset(path: Path, key: str) -> dict[str, Any]:
    if key not in SETTABLE_KEYS:
        raise ValueError(f"unknown key {key!r}")
    cfg = load(path)
    cfg.pop(key, None)
    if key == "level":
        cfg.pop("expires_at", None)
    save(path, cfg)
    return cfg
