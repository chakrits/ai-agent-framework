"""Cross-platform git pre-commit gate: framework validators + staged-diff secret/protected-path checks.

This is the enforcement layer that applies to every agent platform (including ones without tool hooks).
Protected governance files may only be committed when a human exports SDLC_ALLOW_PROTECTED=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import guard, paths

ROOT = Path(__file__).resolve().parents[2]
VALIDATORS = (
    ("scripts/sync-adapters.py", "--check"),
    ("scripts/validate-context-budget.py",),
    ("scripts/validate-contracts.py", "--check-defaults"),
)


def staged_files(root: Path = ROOT) -> list[str]:
    res = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRD"],
        capture_output=True,
        check=True,
    )
    # git always reports forward-slash, repo-relative paths on every OS.
    return [p for p in res.stdout.decode("utf-8", errors="replace").split("\0") if p]


def check_staged(files: list[str], policy: dict, env: dict) -> list[str]:
    errors: list[str] = []
    allow_protected = env.get("SDLC_ALLOW_PROTECTED") == "1"
    for rel in files:
        if paths.matches(rel, policy["secret_globs"]) and not paths.matches(rel, policy.get("secret_allow_globs", [])):
            errors.append(f"Secret file staged: {rel} (unstage it: git restore --staged -- {rel})")
        elif paths.matches(rel, policy["protected_globs"]) and not allow_protected:
            errors.append(
                f"Protected governance path staged: {rel} - Framework Change requires human approval; "
                "a human maintainer re-runs the commit with SDLC_ALLOW_PROTECTED=1"
            )
    return errors


def main() -> int:
    failures: list[str] = []
    for script, *args in VALIDATORS:
        res = subprocess.run([sys.executable, str(ROOT / script), *args], check=False)
        if res.returncode != 0:
            failures.append(f"{script} failed")

    try:
        files = staged_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        failures.append(f"cannot list staged files: {exc}")
        files = []
    failures.extend(check_staged(files, guard.load_policy(), dict(os.environ)))

    if failures:
        print("pre-commit BLOCKED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("pre-commit PASSED")
    return 0
