"""Environment preflight ("doctor") for Windows / macOS / Linux / WSL.

Used as a SessionStart hook to tell the agent which OS, shell and path style it is running in, and as a
CLI (`sdlc_hook.py doctor`) for humans and CI. It never selects which guard runs: the PreToolUse guard
detects the platform itself on every call, so a failed or skipped SessionStart cannot weaken it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from . import platform_env, version

ROOT = Path(__file__).resolve().parents[2]
LF_CRITICAL = ("scripts/bin/sdlc-hook", ".githooks/pre-commit", "scripts/sdlc_hook.py")
CRLF_CRITICAL = ("scripts/bin/sdlc-hook.cmd",)


@dataclass
class Check:
    id: str
    status: str  # ok | info | warn | error
    message: str
    fix: str = ""


def _git(*args: str) -> str | None:
    try:
        res = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout.strip() if res.returncode == 0 else ""


def python_cmd(os_name: str) -> str:
    return "py -3" if os_name == "windows" else "python3"


def collect() -> dict:
    info = platform_env.describe()
    os_name = str(info["os"])
    py = python_cmd(os_name)
    checks: list[Check] = []

    ok_py = sys.version_info >= (3, 10)
    checks.append(Check("python", "ok" if ok_py else "error", f"Python {info['python']}", "" if ok_py else "Install Python 3.10+"))

    git_version = _git("--version")
    if git_version is None:
        checks.append(Check("git", "error", "git not found on PATH", "Install Git (Windows: Git for Windows)"))
    else:
        checks.append(Check("git", "ok", git_version or "git available"))
        hooks_path = _git("config", "--get", "core.hooksPath")
        if hooks_path != ".githooks":
            checks.append(Check("hooks_path", "warn", f"core.hooksPath={hooks_path or '(unset)'}", f"{py} scripts/setup.py"))
        else:
            checks.append(Check("hooks_path", "ok", "core.hooksPath=.githooks"))
        autocrlf = _git("config", "--get", "core.autocrlf") or "(unset)"
        checks.append(Check("autocrlf", "info", f"core.autocrlf={autocrlf} (.gitattributes pins script line endings)"))

    if not (ROOT / ".gitattributes").exists():
        checks.append(Check("gitattributes", "error", ".gitattributes missing", "Restore .gitattributes from the framework"))

    for rel in LF_CRITICAL:
        p = ROOT / rel
        if p.exists() and b"\r\n" in p.read_bytes():
            checks.append(
                Check("line_endings", "error", f"{rel} has CRLF line endings (sh will fail)", "git add --renormalize . && git checkout -- .")
            )
    for rel in CRLF_CRITICAL:
        p = ROOT / rel
        if os_name == "windows" and p.exists() and b"\r\n" not in p.read_bytes():
            checks.append(Check("line_endings", "warn", f"{rel} should use CRLF on Windows", "git add --renormalize ."))

    tools = info["tools"]
    assert isinstance(tools, dict)
    if os_name == "windows":
        if not tools.get("sh") and not tools.get("bash"):
            checks.append(
                Check("posix_shell", "error", "No sh/bash on PATH: Claude Code hooks and git hooks need Git for Windows",
                      "Install Git for Windows and add its bin directory to PATH")
            )
        if len(str(ROOT)) > 200:
            checks.append(Check("long_paths", "warn", f"Repository path is {len(str(ROOT))} chars", "git config core.longpaths true"))
    if os_name == "wsl" and str(ROOT).startswith("/mnt/"):
        checks.append(
            Check("wsl_mount", "warn", "Repository is on a Windows drive mounted in WSL (/mnt/...): slower I/O and case/permission differences",
                  "Clone inside the WSL filesystem (e.g. ~/src) or use Windows-native tools for this checkout")
        )
    if " " in str(ROOT):
        checks.append(Check("path_spaces", "info", "Repository path contains spaces (supported; hook commands are quoted)"))

    return {"framework_version": version.framework_version(), "environment": info, "repo_root": str(ROOT), "python_command": py, "checks": [asdict(c) for c in checks]}


def render_context(report: dict) -> str:
    env = report["environment"]
    os_name = env["os"]
    shell = env["shell"]
    lines = [f"[sdlc-doctor] SDLC framework v{report['framework_version']} | Host OS: {os_name} | shell: {shell} | Python: {env['python']} | repo: {report['repo_root']}"]
    if os_name == "windows":
        lines.append(
            "- Windows: the Bash tool runs Git Bash (POSIX syntax, paths like /c/Users/... or C:/Users/...); "
            "PowerShell uses Windows syntax (C:\\Users\\...). Run Python as `py -3`."
        )
    elif os_name == "wsl":
        lines.append("- WSL: Linux shell; Windows drives appear under /mnt/<drive>/. Run Python as `python3`.")
    else:
        lines.append("- POSIX shell. Run Python as `python3`.")
    lines.append("- Guardrails run on every tool call via scripts/bin/sdlc-hook; do not bypass hooks or use --no-verify.")
    for c in report["checks"]:
        if c["status"] in {"warn", "error"}:
            lines.append(f"- {c['status'].upper()} {c['id']}: {c['message']}" + (f" -> fix: {c['fix']}" if c["fix"] else ""))
    return "\n".join(lines)


def _write_env_snapshot(report: dict) -> None:
    out = ROOT / ".sdlc" / "env.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except OSError:
        pass


def session_start(platform: str, stdin: str = "") -> int:
    """SessionStart hook: inject environment context; never blocks the session."""
    try:
        report = collect()
        _write_env_snapshot(report)
        text = render_context(report)
    except Exception as exc:  # noqa: BLE001 - doctor must never break a session
        text = f"[sdlc-doctor] environment check failed: {exc!r}"
    if platform == "claude":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
    else:
        print(text)
    return 0


def cli(args: list[str]) -> int:
    report = collect()
    if "--json" in args:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_context(report))
        for c in report["checks"]:
            print(f"  [{c['status']:5}] {c['id']}: {c['message']}")
    if "--strict" in args and any(c["status"] == "error" for c in report["checks"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
