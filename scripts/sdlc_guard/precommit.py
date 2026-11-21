"""Cross-platform git pre-commit gate: framework validators + staged-diff secret/protected-path checks.

This is the enforcement layer that applies to every agent platform (including ones without tool hooks).
Protected governance files may only be committed when a human exports SDLC_ALLOW_PROTECTED=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import re

from . import guard, paths, redact

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


ALLOW_MARKER = "sdlc-allow-secret"
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def scan_staged_content(root: Path = ROOT) -> list[str]:
    """Scan *added* lines of the staged diff for high-confidence secrets.

    Reports ``path:line (kind)`` only, never the secret value. A line containing ``sdlc-allow-secret`` is
    skipped (for documented fake tokens). Binary files are skipped by git.
    """
    res = subprocess.run(
        ["git", "-C", str(root), "-c", "core.quotepath=false", "diff", "--cached", "-U0", "--no-color",
         "--no-renames", "--diff-filter=ACM"],
        capture_output=True,
        check=True,
    )
    hits: list[str] = []
    path = ""
    lineno = 0
    for raw in res.stdout.decode("utf-8", errors="replace").splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else ""
            continue
        m = _HUNK_RE.match(raw)
        if m:
            lineno = int(m.group(1))
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            text = raw[1:]
            if path and ALLOW_MARKER not in text:
                for kind in redact.find_secrets(text):
                    hits.append(f"{path}:{lineno} ({kind})")
            lineno += 1
    return hits


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
    try:
        for hit in scan_staged_content():
            failures.append(
                f"Possible secret in staged content: {hit} - remove it, or append '# {ALLOW_MARKER}' to a documented fake token"
            )
    except (OSError, subprocess.CalledProcessError) as exc:
        failures.append(f"cannot scan staged content: {exc}")

    if failures:
        print("pre-commit BLOCKED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("pre-commit PASSED")
    return 0
