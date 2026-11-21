"""Tests for Antigravity (agy) hooks.json generation, payload normalization, and guard/trace parity."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import agy_adapter, trace, trace_hooks  # noqa: E402

BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith("SDLC_")}


class TestAgyAdapter(unittest.TestCase):
    def test_normalize_pretooluse_run_command(self) -> None:
        raw = {
            "conversationId": "conv-123",
            "modelName": "gemini-4-hydrogen",
            "hookEventName": "PreToolUse",
            "cwd": str(ROOT),
            "toolCall": {
                "id": "tc-1",
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            },
        }
        norm = agy_adapter.normalize_payload(raw)
        self.assertEqual(norm["session_id"], "conv-123")
        self.assertEqual(norm["model"], "gemini-4-hydrogen")
        self.assertEqual(norm["tool_name"], "Bash")
        self.assertEqual(norm["tool_use_id"], "tc-1")
        self.assertEqual(norm["tool_input"]["command"], "git status")

    def test_normalize_write_to_file_and_posttooluse_error(self) -> None:
        raw = {
            "conversationId": "conv-456",
            "hookEventName": "PostToolUse",
            "toolCall": {
                "id": "tc-2",
                "name": "write_to_file",
                "args": {"TargetFile": str(ROOT / "README.md")},
            },
            "error": "exit status 1",
        }
        norm = agy_adapter.normalize_payload(raw)
        self.assertEqual(norm["tool_name"], "Write")
        self.assertEqual(norm["tool_input"]["file_path"], str(ROOT / "README.md"))
        self.assertEqual(norm["tool_response"]["exit_code"], 1)
        self.assertEqual(norm["tool_response"]["stderr"], "exit status 1")

    def test_render_agy_hooks_is_synchronous_and_valid(self) -> None:
        cfg = trace_hooks.render_agy_hooks()
        self.assertIn("sdlc-guard", cfg)
        guard_cfg = cfg["sdlc-guard"]
        for evt in ("SessionStart", "PreToolUse", "PostToolUse", "Stop"):
            self.assertIn(evt, guard_cfg)
        for group in guard_cfg["PreToolUse"]:
            for handler in group["hooks"]:
                self.assertNotIn("async", handler)
                self.assertIn("--platform antigravity", handler["command"])


class TestAgyHookEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.trace_dir = Path(self.tmp.name) / "traces"
        self.env = dict(BASE_ENV, SDLC_TRACE_DIR=str(self.trace_dir))

    def _run_hook(self, sub: str, payload: dict, extra_env: dict | None = None) -> subprocess.CompletedProcess:
        env = dict(self.env, **(extra_env or {}))
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py"), sub, "--platform", "antigravity"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_pretooluse_allows_safe_command_and_writes_trace(self) -> None:
        payload = {
            "conversationId": "agy-allow-1",
            "modelName": "gemini-4-hydrogen",
            "hookEventName": "PreToolUse",
            "cwd": str(ROOT),
            "toolCall": {"id": "t1", "name": "run_command", "args": {"CommandLine": "git status"}},
        }
        res = self._run_hook("pretooluse", payload)
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        out = json.loads(res.stdout)
        self.assertEqual(out, {"decision": "allow"})

        files = list(self.trace_dir.rglob("*.jsonl"))
        self.assertEqual(len(files), 1)
        event = json.loads(files[0].read_text(encoding="utf-8").strip())
        self.assertEqual(trace.validate_event(event), [])
        self.assertEqual(event["platform"], "antigravity")
        self.assertEqual(event["model"], "gemini-4-hydrogen")
        self.assertEqual(event["model_source"], "payload")

    def test_pretooluse_denies_dev_agent_protected_write_via_json_stdout(self) -> None:
        payload = {
            "conversationId": "agy-deny-1",
            "modelName": "gemini-4-hydrogen",
            "hookEventName": "PreToolUse",
            "cwd": str(ROOT),
            "toolCall": {
                "id": "t2",
                "name": "replace_file_content",
                "args": {"TargetFile": str(ROOT / "docs" / "operating-model" / "constitution.md")},
            },
        }
        res = self._run_hook("pretooluse", payload, extra_env={"SDLC_ACTIVE_ROLE": "dev-coding-agent"})
        self.assertEqual(res.returncode, 0)
        out = json.loads(res.stdout)
        self.assertEqual(out["decision"], "deny")
        self.assertIn("BLOCKED:", out["reason"])

    def test_session_start_and_trace_return_valid_json_stdout(self) -> None:
        ss = self._run_hook(
            "session-start",
            {"conversationId": "agy-ss-1", "modelName": "gemini-4-hydrogen", "hookEventName": "SessionStart"},
        )
        self.assertEqual(ss.returncode, 0)
        ss_json = json.loads(ss.stdout)
        self.assertIn("injectSteps", ss_json)

        tr = self._run_hook(
            "trace",
            {"conversationId": "agy-ss-1", "modelName": "gemini-4-hydrogen", "hookEventName": "Stop"},
        )
        self.assertEqual(tr.returncode, 0)
        self.assertEqual(json.loads(tr.stdout), {})


if __name__ == "__main__":
    unittest.main()
