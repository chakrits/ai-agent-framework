"""Normalize file paths from any OS / shell into one canonical form for policy matching.

Handles Windows drive paths (``C:\\x``), long-path prefixes (``\\\\?\\C:\\x``), UNC shares, MSYS/Git Bash
(``/c/x``), WSL mounts (``/mnt/c/x``), POSIX paths with spaces, relative paths and ``..`` traversal.
All functions are pure (host OS is passed in), so Windows behaviour can be unit-tested on macOS/Linux.
"""

from __future__ import annotations

import fnmatch
import posixpath
import re

_DRIVE_RE = re.compile(r"^([A-Za-z]):(?:/(.*))?$")
_MSYS_RE = re.compile(r"^/([A-Za-z])(?:/(.*))?$")
_WSL_RE = re.compile(r"^/mnt/([A-Za-z])(?:/(.*))?$")


def _split_anchor(p: str, windows_host: bool) -> tuple[str, str]:
    """Return (anchor, rest) where anchor is '', '/', 'c:/' or '//server/share/'."""
    if p.startswith("//?/"):
        p = p[4:]
        if p[:4].casefold() == "unc/":
            p = "//" + p[4:]

    if p.startswith("//"):
        parts = p[2:].split("/", 2)
        if len(parts) >= 2 and parts[0] and parts[1]:
            return f"//{parts[0]}/{parts[1]}/", parts[2] if len(parts) > 2 else ""

    m = _DRIVE_RE.match(p)
    if m:
        return f"{m.group(1).lower()}:/", m.group(2) or ""

    m = _WSL_RE.match(p)
    if m:
        return f"{m.group(1).lower()}:/", m.group(2) or ""

    if windows_host:
        m = _MSYS_RE.match(p)
        if m:
            return f"{m.group(1).lower()}:/", m.group(2) or ""

    if p.startswith("/"):
        return "/", p.lstrip("/")
    return "", p


def _normalize_rest(rest: str, anchored: bool) -> str:
    if not rest:
        return ""
    if anchored:
        # Prevent '..' from climbing above the anchor (root / drive / share).
        norm = posixpath.normpath("/" + rest).lstrip("/")
    else:
        norm = posixpath.normpath(rest)
    return "" if norm == "." else norm


def canonical(path: str, *, windows_host: bool) -> str:
    """Convert any path spelling into a canonical, forward-slash form (case preserved)."""
    p = path.strip().strip("\"'").replace("\\", "/")
    anchor, rest = _split_anchor(p, windows_host)
    rest = _normalize_rest(rest, anchored=bool(anchor))
    if anchor and not rest:
        return anchor.rstrip("/") if anchor not in {"/"} and not anchor.endswith(":/") else anchor
    return anchor + rest


def is_absolute(canon: str) -> bool:
    return canon.startswith("/") or bool(_DRIVE_RE.match(canon))


def join(base: str, rel: str, *, windows_host: bool) -> str:
    base_c = canonical(base, windows_host=windows_host)
    if not base_c:
        return canonical(rel, windows_host=windows_host)
    return canonical(f"{base_c.rstrip('/')}/{rel}", windows_host=windows_host)


def to_repo_relative(
    path: str,
    *,
    repo_root: str,
    cwd: str | None = None,
    windows_host: bool,
) -> tuple[str | None, str]:
    """Return (repo-relative POSIX path or None if outside the repo, absolute canonical path).

    Relative paths are resolved against ``cwd`` (taken from the hook payload) and then ``repo_root``.
    Prefix comparison is case-insensitive because NTFS and APFS are case-insensitive by default.
    """
    canon = canonical(path, windows_host=windows_host)
    if not is_absolute(canon):
        base = repo_root
        if cwd:
            cwd_c = canonical(cwd, windows_host=windows_host)
            # A relative cwd (e.g. "." from a hook payload) is relative to the repo root, not to "/".
            base = cwd if is_absolute(cwd_c) else join(repo_root, cwd_c, windows_host=windows_host)
        canon = join(base, canon, windows_host=windows_host)

    root = canonical(repo_root, windows_host=windows_host).rstrip("/")
    c_fold, r_fold = canon.casefold(), root.casefold()
    if c_fold == r_fold:
        return ".", canon
    if c_fold.startswith(r_fold + "/"):
        return canon[len(root) + 1 :], canon
    return None, canon


def _match_one(path_fold: str, pattern: str) -> bool:
    pat = pattern.replace("\\", "/").casefold()
    if "/" not in pat:
        # Bare patterns (".env", "*.pem") match any path segment's basename.
        return fnmatch.fnmatchcase(posixpath.basename(path_fold), pat)
    if fnmatch.fnmatchcase(path_fold, pat):
        return True
    if pat.startswith("**/"):
        tail = pat[3:]
        if fnmatch.fnmatchcase(path_fold, tail) or fnmatch.fnmatchcase(path_fold, "*/" + tail):
            return True
    if pat.endswith("/**"):
        head = pat[:-3]
        if path_fold == head:
            return True
    return False


def matches(path: str, patterns: list[str]) -> bool:
    """Case-insensitive glob match; ``**/x`` also matches at the root, bare names match basenames."""
    path_fold = path.replace("\\", "/").casefold()
    return any(_match_one(path_fold, p) for p in patterns)
