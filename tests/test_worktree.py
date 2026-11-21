"""Unit tests for scripts/worktree.py using temporary isolated git repositories."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import worktree  # noqa: E402


def _init_temp_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test User"], check=True, capture_output=True)
    (path / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "chore: init"], check=True, capture_output=True)


class TestWorktreeHelper(unittest.TestCase):
    def test_validate_work_item_rejects_bad_format_and_traversal(self) -> None:
        with self.assertRaises(ValueError):
            worktree.validate_work_item("TASK-1")
        with self.assertRaises(ValueError):
            worktree.resolve_worktree_path(ROOT, "../INT-001")
        self.assertEqual(worktree.validate_work_item("int-001"), "INT-001")

    def test_rejects_invalid_or_flag_like_base_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _init_temp_repo(repo)
            with self.assertRaises(ValueError):
                worktree.create_worktree(repo, "INT-001", "bad-base", base="--orphan")
            with self.assertRaises(ValueError):
                worktree.create_worktree(repo, "INT-001", "missing-ref", base="nonexistent-branch")

    def test_create_list_hook_readiness_and_cleanup_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            _init_temp_repo(repo)
            self.assertFalse(worktree.check_hook_readiness(repo))
            subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath", ".githooks"], check=True)
            self.assertTrue(worktree.check_hook_readiness(repo))

            wt_dir, branch = worktree.create_worktree(repo, "INT-001", "Pilot Feature!")
            self.assertTrue(wt_dir.is_dir())
            self.assertTrue(wt_dir.resolve().is_relative_to((repo / ".worktrees").resolve()))
            self.assertEqual(branch, "feat/INT-001-pilot-feature")

            listed = worktree.list_worktrees(repo)
            self.assertEqual(len(listed), 2)

            worktree.cleanup_worktree(repo, "INT-001", delete_branch=True)
            self.assertFalse(wt_dir.exists())
            self.assertEqual(len(worktree.list_worktrees(repo)), 1)


if __name__ == "__main__":
    unittest.main()
