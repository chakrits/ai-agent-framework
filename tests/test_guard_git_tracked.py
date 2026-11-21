"""Test-oracle lock against a real git repository (no injected is_tracked)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import guard  # noqa: E402


@unittest.skipUnless(shutil.which("git"), "git required")
class TestRealGitTracked(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo with space"
        (self.repo / "tests").mkdir(parents=True)
        (self.repo / "tests" / "test_a.py").write_text("assert True\n", encoding="utf-8")
        git = ["git", "-C", str(self.repo)]
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run(
            [*git, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.hooksPath=/dev/null",
             "commit", "-q", "-m", "init"],
            check=True,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def decide(self, rel: str) -> guard.Decision:
        event = guard.parse_event(
            {"tool_name": "Edit", "agent_type": "dev-coding-agent", "cwd": str(self.repo), "tool_input": {"file_path": rel}}
        )
        return guard.decide(
            event, guard.load_policy(), {}, str(self.repo), sys.platform == "win32", guard.git_is_tracked(str(self.repo))
        )

    def test_committed_test_blocked(self) -> None:
        self.assertFalse(self.decide("tests/test_a.py").allowed)

    def test_case_variant_of_committed_test_blocked(self) -> None:
        self.assertFalse(self.decide("TESTS/TEST_A.py").allowed)

    def test_windows_spelling_of_committed_test_blocked(self) -> None:
        self.assertFalse(self.decide("tests\\test_a.py").allowed)

    def test_new_test_file_allowed(self) -> None:
        self.assertTrue(self.decide("tests/test_b.py").allowed)


if __name__ == "__main__":
    unittest.main()
