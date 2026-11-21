"""Detect host OS, WSL, Git Bash/MSYS and the active shell (used by guard + SessionStart doctor)."""

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Mapping


def is_windows_host(env: Mapping[str, str] | None = None) -> bool:
    """True for native Windows Python, or when running under MSYS/Git Bash."""
    env = os.environ if env is None else env
    return os.name == "nt" or bool(env.get("MSYSTEM"))


def is_wsl(env: Mapping[str, str] | None = None) -> bool:
    env = os.environ if env is None else env
    if not sys.platform.startswith("linux"):
        return False
    if env.get("WSL_DISTRO_NAME") or env.get("WSL_INTEROP"):
        return True
    return "microsoft" in platform.release().casefold()


def host_os(env: Mapping[str, str] | None = None) -> str:
    """Return one of: windows, macos, wsl, linux, other."""
    if os.name == "nt":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "wsl" if is_wsl(env) else "linux"
    return "other"


def detect_shell(env: Mapping[str, str] | None = None) -> str:
    """Best-effort name of the shell that launched this process."""
    env = os.environ if env is None else env
    if env.get("MSYSTEM"):
        return "git-bash"
    shell = env.get("SHELL", "")
    if shell:
        return Path(shell.replace("\\", "/")).name.removesuffix(".exe")
    if os.name == "nt":
        if env.get("PSModulePath") and env.get("PSExecutionPolicyPreference") is not None:
            return "powershell"
        comspec = env.get("COMSPEC", "")
        return Path(comspec.replace("\\", "/")).name.removesuffix(".exe").lower() or "cmd"
    return "sh"


def which_all(names: tuple[str, ...]) -> dict[str, str | None]:
    return {n: shutil.which(n) for n in names}


def describe(env: Mapping[str, str] | None = None) -> dict[str, object]:
    env = os.environ if env is None else env
    return {
        "os": host_os(env),
        "platform": sys.platform,
        "release": platform.release(),
        "machine": platform.machine(),
        "shell": detect_shell(env),
        "windows_path_semantics": is_windows_host(env),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "tools": which_all(("git", "bash", "sh", "pwsh", "powershell", "python3", "python", "py")),
    }
