"""Versioning, release automation, Conventional Commits hook, license and README badge tests."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import commitmsg  # noqa: E402

ENTRY = ROOT / "scripts" / "sdlc_hook.py"
REPO = "chakrits/ai-agent-framework"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


class TestVersioning(unittest.TestCase):
    def test_version_file_is_semver(self) -> None:
        self.assertRegex((ROOT / "version.txt").read_text(encoding="utf-8").strip(), SEMVER)

    def test_manifest_matches_version_file(self) -> None:
        manifest = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["."], (ROOT / "version.txt").read_text(encoding="utf-8").strip())

    def test_release_please_config(self) -> None:
        cfg = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["release-type"], "simple")
        self.assertTrue(cfg["bump-minor-pre-major"])
        self.assertIn(".", cfg["packages"])

    def test_release_workflow(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release-please.yml").read_text(encoding="utf-8")
        self.assertIn("googleapis/release-please-action@v4", text)
        self.assertIn("pull-requests: write", text)
        self.assertIn("contents: write", text)

    def test_changelog_mentions_current_version(self) -> None:
        version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
        self.assertIn(version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_version_flag(self) -> None:
        res = subprocess.run([sys.executable, str(ENTRY), "--version"], capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), (ROOT / "version.txt").read_text(encoding="utf-8").strip())


class TestCommitMsg(unittest.TestCase):
    def test_valid_messages(self) -> None:
        for msg in (
            "feat: add trace",
            "fix(guard): resolve relative cwd",
            "docs!: drop old guide",
            "chore(main): release 0.2.0",
            "feat(scope-x/y): thing\n\nBody text.\n\nCo-Authored-By: Someone <a@example.invalid>",
            'Revert "feat: add trace"',
            "Merge pull request #1 from a/b",
            "fixup! feat: add trace",
            "# comment line\nfeat: after comment",
        ):
            with self.subTest(msg=msg):
                self.assertIsNone(commitmsg.check(msg))

    def test_invalid_messages(self) -> None:
        for msg in ("", "update stuff", "Feat: caps", "feat:no space", "feat(): empty scope", "unknown: type", "feat: "):
            with self.subTest(msg=msg):
                self.assertIsNotNone(commitmsg.check(msg))

    def test_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp) / "good", Path(tmp) / "bad"
            good.write_text("feat: ok\n", encoding="utf-8")
            bad.write_text("random message\n", encoding="utf-8")
            run = lambda p: subprocess.run([sys.executable, str(ENTRY), "commit-msg", str(p)], capture_output=True, text=True, check=False)  # noqa: E731
            self.assertEqual(run(good).returncode, 0)
            res = run(bad)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Conventional Commits", res.stderr)

    def test_hook_file_is_lf_and_calls_launcher(self) -> None:
        raw = (ROOT / ".githooks" / "commit-msg").read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertIn(b"sdlc-hook", raw)
        self.assertIn(b"commit-msg", raw)


class TestLicenseAndReadme(unittest.TestCase):
    def test_license_is_mit(self) -> None:
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Permission is hereby granted, free of charge", text)
        self.assertIn("2026", text)

    def test_readme_badges_and_links(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for needle in (
            f"img.shields.io/github/stars/{REPO}",
            f"img.shields.io/github/contributors/{REPO}",
            f"img.shields.io/github/discussions/{REPO}",
            f"img.shields.io/github/v/release/{REPO}",
            f"img.shields.io/github/actions/workflow/status/{REPO}/validate.yml",
            f"img.shields.io/github/license/{REPO}",
            "img.shields.io/badge/platform-",
            "img.shields.io/badge/built%20with-",
            "img.shields.io/badge/agents-",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            f"github.com/{REPO}/releases",
            f"github.com/{REPO}/discussions",
        ):
            self.assertIn(needle, text, needle)

    def test_contributing_mentions_core_workflow(self) -> None:
        text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        for needle in ("Conventional Commits", "scripts/setup.py", "SDLC_ALLOW_PROTECTED", "release-please"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
