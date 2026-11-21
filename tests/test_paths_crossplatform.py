"""Cross-platform path normalization tests (pure functions; run identically on every OS)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import paths  # noqa: E402


class TestCanonical(unittest.TestCase):
    def test_windows_drive_backslash(self) -> None:
        self.assertEqual(paths.canonical(r"C:\Users\a\repo\docs\x.md", windows_host=True), "c:/Users/a/repo/docs/x.md")

    def test_windows_drive_forward_slash(self) -> None:
        self.assertEqual(paths.canonical("c:/Users/a/repo/x.md", windows_host=False), "c:/Users/a/repo/x.md")

    def test_windows_long_path_prefix(self) -> None:
        self.assertEqual(paths.canonical(r"\\?\C:\Users\a\repo\x.md", windows_host=True), "c:/Users/a/repo/x.md")

    def test_unc_path(self) -> None:
        self.assertEqual(paths.canonical(r"\\server\share\repo\x.md", windows_host=True), "//server/share/repo/x.md")

    def test_msys_path_on_windows_host(self) -> None:
        self.assertEqual(paths.canonical("/c/Users/a/repo/x.md", windows_host=True), "c:/Users/a/repo/x.md")

    def test_msys_like_path_on_posix_host_is_untouched(self) -> None:
        self.assertEqual(paths.canonical("/c/Users/a/repo/x.md", windows_host=False), "/c/Users/a/repo/x.md")

    def test_wsl_mount_path(self) -> None:
        self.assertEqual(paths.canonical("/mnt/c/Users/a/repo/x.md", windows_host=False), "c:/Users/a/repo/x.md")

    def test_macos_path_with_spaces(self) -> None:
        self.assertEqual(
            paths.canonical("/Users/a/GitHub Code/repo/x.md", windows_host=False), "/Users/a/GitHub Code/repo/x.md"
        )

    def test_traversal_is_collapsed(self) -> None:
        self.assertEqual(paths.canonical("docs/a/../b/./x.md", windows_host=False), "docs/b/x.md")
        self.assertEqual(paths.canonical(r"C:\repo\src\..\docs\x.md", windows_host=True), "c:/repo/docs/x.md")

    def test_quotes_are_stripped(self) -> None:
        self.assertEqual(paths.canonical('"docs/x.md"', windows_host=False), "docs/x.md")


class TestRepoRelative(unittest.TestCase):
    def test_windows_absolute_inside_repo(self) -> None:
        rel, _ = paths.to_repo_relative(
            r"C:\Users\A\Repo\docs\operating-model\constitution.md", repo_root=r"C:\Users\a\repo", windows_host=True
        )
        self.assertEqual(rel, "docs/operating-model/constitution.md")

    def test_msys_path_against_windows_root(self) -> None:
        rel, _ = paths.to_repo_relative("/c/Users/a/repo/docs/x.md", repo_root=r"C:\Users\a\repo", windows_host=True)
        self.assertEqual(rel, "docs/x.md")

    def test_wsl_path_against_windows_root(self) -> None:
        rel, _ = paths.to_repo_relative("/mnt/c/Users/a/repo/docs/x.md", repo_root=r"C:\Users\a\repo", windows_host=False)
        self.assertEqual(rel, "docs/x.md")

    def test_relative_path_joined_with_payload_cwd(self) -> None:
        rel, _ = paths.to_repo_relative(
            r"..\docs\x.md", repo_root="/Users/a/GitHub Code/repo", cwd="/Users/a/GitHub Code/repo/src", windows_host=False
        )
        self.assertEqual(rel, "docs/x.md")

    def test_outside_repo(self) -> None:
        rel, abs_path = paths.to_repo_relative("/etc/hosts", repo_root="/Users/a/repo", windows_host=False)
        self.assertIsNone(rel)
        self.assertEqual(abs_path, "/etc/hosts")

    def test_prefix_sibling_is_not_inside_repo(self) -> None:
        rel, _ = paths.to_repo_relative("/Users/a/repo-other/x.md", repo_root="/Users/a/repo", windows_host=False)
        self.assertIsNone(rel)

    def test_traversal_escaping_repo(self) -> None:
        rel, _ = paths.to_repo_relative("docs/../../outside.md", repo_root="/Users/a/repo", windows_host=False)
        self.assertIsNone(rel)


class TestGlobMatching(unittest.TestCase):
    def test_case_insensitive(self) -> None:
        self.assertTrue(paths.matches("DOCS/Operating-Model/Constitution.md", ["docs/operating-model/constitution.md"]))

    def test_double_star_matches_root_and_nested(self) -> None:
        self.assertTrue(paths.matches("test_login.py", ["**/test_*.py"]))
        self.assertTrue(paths.matches("app/tests/unit/test_login.py", ["**/test_*.py"]))

    def test_basename_pattern(self) -> None:
        self.assertTrue(paths.matches("services/api/.env", [".env"]))
        self.assertTrue(paths.matches("c:/Users/a/.ssh/id_rsa", ["**/.ssh/**"]))
        self.assertFalse(paths.matches("docs/environment.md", [".env"]))

    def test_directory_glob(self) -> None:
        self.assertTrue(paths.matches("docs/contracts/intent.schema.yaml", ["docs/contracts/**"]))
        self.assertFalse(paths.matches("docs/contracts-old.md", ["docs/contracts/**"]))


if __name__ == "__main__":
    unittest.main()
