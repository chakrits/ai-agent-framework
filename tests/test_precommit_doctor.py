"""Tests for the cross-platform pre-commit gate and the SessionStart doctor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import doctor, guard, precommit  # noqa: E402


class TestPrecommitStaged(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = guard.load_policy()

    def test_secret_file_blocked(self) -> None:
        errs = precommit.check_staged(["services/api/.env", "README.md"], self.policy, {})
        self.assertEqual(len(errs), 1)
        self.assertIn(".env", errs[0])

    def test_env_example_allowed(self) -> None:
        self.assertEqual(precommit.check_staged([".env.example"], self.policy, {}), [])

    def test_protected_requires_human_override(self) -> None:
        self.assertTrue(precommit.check_staged(["docs/contracts/intent.schema.yaml"], self.policy, {}))
        self.assertEqual(
            precommit.check_staged(["docs/contracts/intent.schema.yaml"], self.policy, {"SDLC_ALLOW_PROTECTED": "1"}), []
        )

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_staged_files_from_real_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo with space"
            (repo / "sub dir").mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "sub dir" / ".env").write_text("A=1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            self.assertEqual(precommit.staged_files(repo), ["sub dir/.env"])


@unittest.skipUnless(shutil.which("git"), "git required")
class TestContentScan(unittest.TestCase):
    TOKEN = "ghp_" + "a1B2c3D4" * 5

    def stage(self, files: dict[str, str]) -> Path:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        repo = Path(self.tmp.name) / "repo with space"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        return repo

    def test_secret_in_added_line_is_reported_without_leaking_value(self) -> None:
        repo = self.stage({"src/app.py": f"x = 1\nKEY = '{self.TOKEN}'\n"})
        hits = precommit.scan_staged_content(repo)
        self.assertEqual(len(hits), 1)
        self.assertIn("src/app.py:2", hits[0])
        self.assertIn("github_token", hits[0])
        self.assertNotIn(self.TOKEN, hits[0])

    def test_clean_files_and_allow_marker(self) -> None:
        repo = self.stage({"a.py": "print('hi')\n", "b.py": f"T = '{self.TOKEN}'  # sdlc-allow-secret\n"})
        self.assertEqual(precommit.scan_staged_content(repo), [])

    def test_only_added_lines_are_scanned(self) -> None:
        repo = self.stage({"a.py": f"T = '{self.TOKEN}'  # sdlc-allow-secret\n"})
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "init"],
            check=True,
        )
        (repo / "a.py").write_text(f"T = '{self.TOKEN}'  # sdlc-allow-secret\nprint(1)\n", encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        self.assertEqual(precommit.scan_staged_content(repo), [])

    def test_binary_file_is_skipped(self) -> None:
        repo = self.stage({})
        (repo / "bin.dat").write_bytes(b"\x00\x01" + self.TOKEN.encode() + b"\x00")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        self.assertEqual(precommit.scan_staged_content(repo), [])


class TestDoctor(unittest.TestCase):
    def test_report_includes_framework_version(self) -> None:
        report = doctor.collect()
        self.assertEqual(report["framework_version"], (ROOT / "version.txt").read_text(encoding="utf-8").strip())
        self.assertIn(report["framework_version"], doctor.render_context(report))

    def test_collect_has_environment_and_checks(self) -> None:
        report = doctor.collect()
        self.assertIn(report["environment"]["os"], {"windows", "macos", "linux", "wsl", "other"})
        self.assertTrue(any(c["id"] == "python" for c in report["checks"]))

    def test_session_start_claude_json_never_blocks(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py"), "session-start", "--platform", "claude"],
            stdin=subprocess.DEVNULL,
            env=dict(os.environ, SDLC_TRACE_LEVEL="off"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("Host OS", out["hookSpecificOutput"]["additionalContext"])

    def test_session_start_codex_plain_text(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py"), "session-start", "--platform", "codex"],
            stdin=subprocess.DEVNULL,
            env=dict(os.environ, SDLC_TRACE_LEVEL="off"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue(res.stdout.startswith("[sdlc-doctor]"))


if __name__ == "__main__":
    unittest.main()
