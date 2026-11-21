#!/usr/bin/env python3
"""Cross-platform wrapper: python scripts/doctor.py (Windows: py -3 scripts\\doctor.py)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlc_hook import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["doctor", *sys.argv[1:]]))
