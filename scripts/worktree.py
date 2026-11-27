#!/usr/bin/env python3
"""Worktree lifecycle helper for parallel SDLC sessions (.worktrees/INT-xxx)."""

# Import isolation (PLAN-011): keep this file's directory off sys.path so that files placed next to it are
# never imported by name. Nothing above this block may import a module that is not already loaded at startup.
import os
import sys

_HERE = os.path.dirname(os.path.realpath(__file__))
sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.realpath(p or os.curdir)) != os.path.normcase(_HERE)]

import argparse
import re
import subprocess
from pathlib import Path

WORK_ITEM_RE = re.compile(r"^INT-[0-9]{3,}$")
SLUG_RE = re.compile(r"[^a-z0-9-]+")


def sanitize_slug(raw: str) -> str:
    slug = SLUG_RE.sub("-", raw.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"Invalid slug: {raw!r}")
    return slug


def validate_work_item(work_item: str) -> str:
    item = work_item.strip().upper()
    if not WORK_ITEM_RE.match(item):
        raise ValueError(f"Work item must match INT-xxx (e.g. INT-001), got: {work_item!r}")
    return item


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_worktree_path(repo_root: Path, work_item: str) -> Path:
    """Resolve .worktrees/<INT-xxx> and enforce containment under repo_root (rejecting symlinks outside repo)."""
    item = validate_work_item(work_item)
    root_real = repo_root.resolve()
    raw_base = repo_root / ".worktrees"
    if raw_base.is_symlink():
        raise ValueError(f"Worktree parent .worktrees must not be a symlink: {raw_base}")
    base_dir = raw_base.resolve()
    if not base_dir.is_relative_to(root_real) or base_dir == root_real:
        raise ValueError(f"Worktree parent escapes repository root: {base_dir}")

    raw_target = raw_base / item
    if raw_target.is_symlink():
        raise ValueError(f"Worktree target must not be a symlink: {raw_target}")
    target = raw_target.resolve()
    if not target.is_relative_to(base_dir) or target == base_dir or not target.is_relative_to(root_real):
        raise ValueError(f"Worktree path escapes .worktrees boundary: {target}")
    return target


def resolve_base_commit(repo_root: Path, base: str) -> str:
    """Validate and resolve a git base ref to an exact commit SHA."""
    ref = base.strip()
    if not ref or ref.startswith("-"):
        raise ValueError(f"Invalid base ref: {base!r}")
    res = _git(repo_root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if res.returncode != 0:
        raise ValueError(f"Base ref does not resolve to a commit: {base!r}")
    return res.stdout.strip()


def check_hook_readiness(repo_root: Path) -> bool:
    """Return True if core.hooksPath is configured to .githooks."""
    res = _git(repo_root, "config", "--get", "core.hooksPath")
    return res.returncode == 0 and res.stdout.strip() == ".githooks"


def create_worktree(repo_root: Path, work_item: str, slug: str, base: str = "HEAD") -> tuple[Path, str]:
    """Create an isolated git worktree under .worktrees/<INT-xxx> on feat/<INT-xxx>-<slug>."""
    item = validate_work_item(work_item)
    clean_slug = sanitize_slug(slug)
    branch = f"feat/{item}-{clean_slug}"
    wt_dir = resolve_worktree_path(repo_root, item)
    if wt_dir.exists():
        raise FileExistsError(f"Worktree already exists: {wt_dir}")

    commit_sha = resolve_base_commit(repo_root, base)
    wt_dir.parent.mkdir(parents=True, exist_ok=True)
    branch_exists = _git(repo_root, "rev-parse", "--verify", f"refs/heads/{branch}").returncode == 0
    cmd = ["worktree", "add", str(wt_dir), branch] if branch_exists else ["worktree", "add", "-b", branch, str(wt_dir), commit_sha]
    res = _git(repo_root, *cmd)
    if res.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {res.stderr.strip() or res.stdout.strip()}")
    return wt_dir, branch


def list_worktrees(repo_root: Path) -> list[dict[str, str]]:
    """Return parsed worktree entries from `git worktree list --porcelain`."""
    res = _git(repo_root, "worktree", "list", "--porcelain")
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    items: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in res.stdout.splitlines():
        if not line.strip():
            if current:
                items.append(current)
                current = {}
            continue
        key, _, val = line.partition(" ")
        current[key] = val
    if current:
        items.append(current)
    return items


def cleanup_worktree(repo_root: Path, work_item: str, force: bool = False, delete_branch: bool = False) -> Path:
    """Remove .worktrees/<INT-xxx> and optionally delete its feature branch."""
    item = validate_work_item(work_item)
    wt_dir = resolve_worktree_path(repo_root, item)
    if not wt_dir.exists():
        raise FileNotFoundError(f"Worktree does not exist: {wt_dir}")

    branch_name = ""
    if delete_branch:
        br = _git(wt_dir, "rev-parse", "--abbrev-ref", "HEAD")
        if br.returncode == 0:
            branch_name = br.stdout.strip()

    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(wt_dir))
    res = _git(repo_root, *args)
    if res.returncode != 0:
        raise RuntimeError(f"git worktree remove failed: {res.stderr.strip() or res.stdout.strip()}")

    if delete_branch and branch_name and branch_name.startswith(f"feat/{item}-"):
        _git(repo_root, "branch", "-D" if force else "-d", branch_name)

    return wt_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage isolated git worktrees for SDLC work items.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create .worktrees/<INT-xxx> on feat/<INT-xxx>-<slug>")
    p_create.add_argument("work_item")
    p_create.add_argument("slug")
    p_create.add_argument("--base", default="HEAD")

    sub.add_parser("list", help="List active worktrees")

    p_clean = sub.add_parser("cleanup", help="Remove .worktrees/<INT-xxx>")
    p_clean.add_argument("work_item")
    p_clean.add_argument("--force", action="store_true")
    p_clean.add_argument("--delete-branch", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "create":
            wt_dir, branch = create_worktree(args.repo_root, args.work_item, args.slug, base=args.base)
            hooks_ok = check_hook_readiness(args.repo_root)
            print(f"Created worktree: {wt_dir} (branch: {branch}, hooks_ready={hooks_ok})")
        elif args.cmd == "list":
            for item in list_worktrees(args.repo_root):
                print(f"{item.get('worktree')} [{item.get('branch', 'detached')}]")
        elif args.cmd == "cleanup":
            removed = cleanup_worktree(args.repo_root, args.work_item, force=args.force, delete_branch=args.delete_branch)
            print(f"Removed worktree: {removed}")
    except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
