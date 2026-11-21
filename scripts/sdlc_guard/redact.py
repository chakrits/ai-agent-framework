"""Secret detection, redaction and truncation shared by agent traces and the pre-commit content scan.

Two pattern sets:
- TOKEN_PATTERNS: high-confidence credential formats. Used for the pre-commit content scan and for redaction.
- Key/value, bearer and URL-credential patterns: broader, redaction only (too noisy to block commits).
"""

from __future__ import annotations

import re
from typing import Mapping

TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"\bsk-(?!ant-)[A-Za-z0-9_-]{20,}")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
)
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----.*?(?:-----END (?:[A-Z]+ )*PRIVATE KEY-----|\Z)", re.DOTALL
)
_PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")

_KEY_VALUE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)s?\b"
    r"(\s*[:=]\s*)(\"[^\"]+\"|'[^']+'|[^\s,;&]+)"
)
_BEARER = re.compile(r"(?i)(authorization\s*:\s*(?:bearer|basic|token)\s+)[^\s'\"]+")
_URL_CREDENTIALS = re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^\s:/@'\"]+:)([^\s@/'\"]+)(@)")
_SECRET_ENV_NAME = re.compile(r"(?i)(secret|token|password|passwd|api[_-]?key|private[_-]?key|credential|auth)")
_MIN_ENV_SECRET_LEN = 8


def find_secrets(text: str) -> list[str]:
    """Names of high-confidence secret formats present in ``text`` (never the values)."""
    found = [name for name, rx in TOKEN_PATTERNS if rx.search(text)]
    if _PRIVATE_KEY_HEADER.search(text):
        found.append("private_key")
    return found


def redact(text: str, env: Mapping[str, str] | None = None) -> str:
    """Replace secrets with ``[REDACTED:<kind>]`` markers. Idempotent."""
    if not text:
        return text
    out = _PRIVATE_KEY_BLOCK.sub("[REDACTED:private_key]", text)
    for name, rx in TOKEN_PATTERNS:
        out = rx.sub(f"[REDACTED:{name}]", out)
    out = _BEARER.sub(r"\1[REDACTED:bearer]", out)
    out = _URL_CREDENTIALS.sub(r"\1[REDACTED:url_password]\3", out)
    out = _KEY_VALUE.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED:{m.group(1).lower()}]" if "[REDACTED" not in m.group(3) else m.group(0), out)
    if env:
        for name, value in env.items():
            if value and len(value) >= _MIN_ENV_SECRET_LEN and _SECRET_ENV_NAME.search(name):
                out = out.replace(value, f"[REDACTED:env:{name}]")
    return out


def truncate(text: str, limit: int) -> tuple[str, bool, int]:
    """Cut ``text`` to ``limit`` UTF-8 bytes (never splitting a character).

    Returns (text, was_truncated, original_size_in_bytes).
    """
    raw = text.encode("utf-8", errors="replace")
    size = len(raw)
    if size <= limit:
        return text, False, size
    cut = raw[:limit].decode("utf-8", errors="ignore")
    return f"{cut}\n...[truncated {size - limit} of {size} bytes]", True, size
