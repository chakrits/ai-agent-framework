"""One-time, per-clone setup for Windows / macOS / Linux / WSL (replaces scripts/setup-hooks.sh)."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

from . import doctor

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLES = (".githooks/pre-commit", "scripts/bin/sdlc-hook", "scripts/sdlc_hook.py")


def main(args: list[str]) -> int:
    try:
        subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        print("Not inside a Git repository (or git is missing). Run 'git init' first, then re-run setup.")
        return 1

    subprocess.run(["git", "-C", str(ROOT), "config", "core.hooksPath", ".githooks"], check=True)
    print("Configured core.hooksPath=.githooks")

    if os.name != "nt":
        for rel in EXECUTABLES:
            p = ROOT / rel
            if p.exists():
                p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("Marked hook launchers executable")

    rc = doctor.cli(["--strict"])
    if rc != 0:
        print("\nSetup finished with errors above; fix them and re-run setup.")
    return rc
