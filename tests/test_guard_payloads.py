"""Hook payload tests: fixture-driven decisions plus end-to-end runs of the entrypoint and launchers."""

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

from sdlc_guard import guard  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "hook-payloads"
ENTRY = ROOT / "scripts" / "sdlc_hook.py"
LAUNCHER_SH = ROOT / "scripts" / "bin" / "sdlc-hook"
LAUNCHER_CMD = ROOT / "scripts" / "bin" / "sdlc-hook.cmd"
CLEAN_ENV = {
    k: v
    for k, v in os.environ.items()
    if k not in {"SDLC_ACTIVE_ROLE", "RELEASE_APPROVAL", "SDLC_GUARD_FAIL_OPEN", "CLAUDE_PROJECT_DIR", "SDLC_TRACE_DIR"}
}
CLEAN_ENV["SDLC_TRACE_LEVEL"] = "off"  # never write test events into the developer's real trace store


class TestFixtureDecisions(unittest.TestCase):
    def test_all_fixtures(self) -> None:
        files = sorted(FIXTURES.rglob("*.json"))
        self.assertGreaterEqual(len(files), 20)
        policy = guard.load_policy()
        for f in files:
            case = json.loads(f.read_text(encoding="utf-8"))
            tracked = {t.casefold() for t in case["tracked"]}
            with self.subTest(fixture=str(f.relative_to(FIXTURES))):
                event = guard.parse_event(case["payload"])
                decision = guard.decide(
                    event,
                    policy=policy,
                    env=case["env"],
                    repo_root=case["repo_root"],
                    windows_host=case["windows_host"],
                    is_tracked=lambda rel: rel.casefold() in tracked,
                )
                self.assertEqual(0 if decision.allowed else 2, case["expect_exit"], decision.reason)

    def test_env_role_fallback(self) -> None:
        event = guard.parse_event({"tool_name": "Edit", "tool_input": {"file_path": "docs/contracts/a.yaml"}, "cwd": "/r"})
        d = guard.decide(event, guard.load_policy(), {"SDLC_ACTIVE_ROLE": "dev-coding-agent"}, "/r", False, lambda _: False)
        self.assertFalse(d.allowed)

    def test_namespaced_agent_type(self) -> None:
        event = guard.parse_event(
            {"tool_name": "Edit", "agent_type": "myplugin:dev-coding-agent", "tool_input": {"file_path": "/r/docs/contracts/a.yaml"}}
        )
        d = guard.decide(event, guard.load_policy(), {}, "/r", False, lambda _: False)
        self.assertFalse(d.allowed)


def run_entry(payload: object, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(ENTRY), *args],
        input=data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env or CLEAN_ENV,
        check=False,
    )


class TestEntrypoint(unittest.TestCase):
    def test_pretooluse_blocks_force_push(self) -> None:
        res = run_entry({"tool_name": "Bash", "tool_input": {"command": "git push -f"}, "cwd": str(ROOT)}, "pretooluse")
        self.assertEqual(res.returncode, 2, res.stderr)
        self.assertIn("BLOCKED", res.stderr)

    def test_pretooluse_allows_safe_command(self) -> None:
        res = run_entry({"tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(ROOT)}, "pretooluse")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_invalid_json_fails_closed(self) -> None:
        res = run_entry("{not json", "pretooluse")
        self.assertEqual(res.returncode, 2)

    def test_fail_open_override(self) -> None:
        env = dict(CLEAN_ENV, SDLC_GUARD_FAIL_OPEN="1")
        res = run_entry("{not json", "pretooluse", env=env)
        self.assertEqual(res.returncode, 0)

    def test_legacy_check_path_and_cmd(self) -> None:
        env = dict(CLEAN_ENV, SDLC_ACTIVE_ROLE="dev-coding-agent")
        self.assertEqual(run_entry("", "--check-path", "docs/operating-model/constitution.md", env=env).returncode, 2)
        self.assertEqual(run_entry("", "--check-path", "src/service.py", env=env).returncode, 0)
        self.assertEqual(run_entry("", "--check-cmd", "make deploy production").returncode, 2)


@unittest.skipUnless(shutil.which("sh"), "POSIX sh not available")
class TestShLauncher(unittest.TestCase):
    def run_sh(self, launcher: Path, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", str(launcher), "pretooluse"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=CLEAN_ENV,
            check=False,
        )

    def test_launcher_blocks(self) -> None:
        res = self.run_sh(LAUNCHER_SH, {"tool_name": "Bash", "tool_input": {"command": "git push --force"}, "cwd": str(ROOT)})
        self.assertEqual(res.returncode, 2, res.stderr)

    def test_launcher_has_lf_line_endings(self) -> None:
        self.assertNotIn(b"\r\n", LAUNCHER_SH.read_bytes())
        self.assertNotIn(b"\r\n", (ROOT / ".githooks" / "pre-commit").read_bytes())

    @unittest.skipIf(os.name == "nt", "directory symlinks need extra privileges on Windows")
    def test_claude_settings_command_survives_path_with_spaces(self) -> None:
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        with tempfile.TemporaryDirectory() as tmp:
            spaced = Path(tmp) / "dir with space"
            spaced.symlink_to(ROOT, target_is_directory=True)
            env = dict(CLEAN_ENV, CLAUDE_PROJECT_DIR=str(spaced))
            res = subprocess.run(
                ["sh", "-c", command],
                input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push -f"}, "cwd": str(spaced)}),
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
        self.assertEqual(res.returncode, 2, res.stderr)


@unittest.skipUnless(os.name == "nt", "Windows-only launcher test")
class TestCmdLauncher(unittest.TestCase):
    def test_cmd_launcher_blocks(self) -> None:
        res = subprocess.run(
            ["cmd", "/c", str(LAUNCHER_CMD), "pretooluse"],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push -f"}, "cwd": str(ROOT)}),
            capture_output=True,
            text=True,
            env=CLEAN_ENV,
            check=False,
        )
        self.assertEqual(res.returncode, 2, res.stderr)

    def test_cmd_launcher_has_crlf(self) -> None:
        self.assertIn(b"\r\n", LAUNCHER_CMD.read_bytes())


class TestAdapterConfig(unittest.TestCase):
    def test_claude_settings_matchers_and_quoting(self) -> None:
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        pre = settings["hooks"]["PreToolUse"][0]
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "PowerShell", "Read"):
            self.assertIn(tool, pre["matcher"].split("|"))
        self.assertIn('"$CLAUDE_PROJECT_DIR/scripts/bin/sdlc-hook"', pre["hooks"][0]["command"])
        self.assertIn("SessionStart", settings["hooks"])

    def test_codex_hooks_has_windows_override(self) -> None:
        hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        handler = hooks["hooks"]["PreToolUse"][0]["hooks"][0]
        self.assertIn("commandWindows", handler)
        self.assertIn("SessionStart", hooks["hooks"])


if __name__ == "__main__":
    unittest.main()
