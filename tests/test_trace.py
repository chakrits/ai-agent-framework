"""Agent trace tests: event building, levels, redaction, concurrency, retention, CLI and hook integration."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import trace, trace_cli  # noqa: E402

ENTRY = ROOT / "scripts" / "sdlc_hook.py"
GH = "ghp_" + "a1B2c3D4" * 5
BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith("SDLC_") and k != "CLAUDE_PROJECT_DIR"}


def post_payload(stdout: str = "ok", stderr: str = "", session: str = "sess-1", **extra) -> dict:
    payload = {
        "session_id": session,
        "cwd": "/repo",
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_use_id": "tu1",
        "tool_input": {"command": "echo hi"},
        "tool_response": {"stdout": stdout, "stderr": stderr, "interrupted": False, "isImage": False},
    }
    payload.update(extra)
    return payload


class TraceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "traces"
        self.env = dict(BASE_ENV, SDLC_TRACE_DIR=str(self.dir))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def events(self) -> list[dict]:
        out: list[dict] = []
        for f in sorted(self.dir.rglob("*.jsonl")):
            out.extend(json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line)
        return out

    def record(self, payload: dict, **kw) -> Path | None:
        return trace.record(payload, platform=kw.pop("platform", "claude"), repo_root=str(ROOT), env=self.env, **kw)


class TestLevels(TraceCase):
    def test_default_level_is_info(self) -> None:
        self.assertEqual(trace.trace_level({}), "info")
        self.assertEqual(trace.trace_level({"SDLC_TRACE_LEVEL": "DEBUG"}), "debug")
        self.assertEqual(trace.trace_level({"SDLC_TRACE_LEVEL": "nonsense"}), "info")

    def test_off_writes_nothing(self) -> None:
        self.env["SDLC_TRACE_LEVEL"] = "off"
        self.assertIsNone(self.record(post_payload()))
        self.assertFalse(self.dir.exists())

    def test_info_truncates_output_to_2kb(self) -> None:
        self.record(post_payload(stdout="x" * 10000))
        out = self.events()[0]["output"]
        self.assertTrue(out["truncated"])
        self.assertEqual(out["bytes"], 10000)
        self.assertLess(len(out["stdout"]), 2200)

    def test_debug_keeps_up_to_64kb_and_raw_input(self) -> None:
        self.env["SDLC_TRACE_LEVEL"] = "debug"
        self.record(post_payload(stdout="x" * 100000))
        ev = self.events()[0]
        self.assertTrue(ev["output"]["truncated"])
        self.assertGreater(len(ev["output"]["stdout"]), 60000)
        self.assertLess(len(ev["output"]["stdout"]), 66000)
        self.assertIn("echo hi", ev["input_raw"])


class TestEventContent(TraceCase):
    def test_post_tool_use_fields(self) -> None:
        path = self.record(post_payload(stdout="hello", agent_type="dev-coding-agent", agent_id="a1", duration_ms=42))
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path.parent.parent, self.dir)
        self.assertEqual(path.name, "sess-1.jsonl")
        ev = self.events()[0]
        self.assertEqual(trace.validate_event(ev), [])
        self.assertEqual(ev["event"], "PostToolUse")
        self.assertEqual(ev["operation"], "execute_tool")
        self.assertEqual(ev["platform"], "claude")
        self.assertEqual(ev["tool_name"], "Bash")
        self.assertEqual(ev["input"]["command"], "echo hi")
        self.assertEqual(ev["output"]["stdout"], "hello")
        self.assertEqual(ev["role"], "dev-coding-agent")
        self.assertEqual(ev["agent_id"], "a1")
        self.assertEqual(ev["duration_ms"], 42)
        self.assertRegex(ev["framework_version"], r"^\d+\.\d+\.\d+")

    def test_failure_event_keeps_error_and_exit_code(self) -> None:
        payload = post_payload(hook_event_name="PostToolUseFailure", error="Exit code 2\nboom", is_interrupt=False)
        payload.pop("tool_response")
        self.record(payload)
        ev = self.events()[0]
        self.assertEqual(ev["event"], "PostToolUseFailure")
        self.assertIn("Exit code 2", ev["error"])
        self.assertEqual(ev["exit_code"], 2)

    def test_codex_string_and_dict_responses(self) -> None:
        for resp in ("plain text result", {"output": "from dict", "exit_code": 0}):
            payload = post_payload(session="cx")
            payload["tool_response"] = resp
            self.record(payload, platform="codex")
        evs = self.events()
        self.assertEqual({e["platform"] for e in evs}, {"codex"})
        self.assertIn("plain text result", evs[0]["output"]["stdout"])
        self.assertIn("from dict", evs[1]["output"]["stdout"])

    def test_user_prompt_and_stop(self) -> None:
        self.record({"session_id": "s", "hook_event_name": "UserPromptSubmit", "prompt": "fix the bug"})
        self.record({"session_id": "s", "hook_event_name": "Stop", "last_assistant_message": "done " * 1000})
        a, b = self.events()
        self.assertEqual(a["operation"], "user_prompt")
        self.assertEqual(a["prompt"], "fix the bug")
        self.assertEqual(b["operation"], "turn_end")
        self.assertLess(len(b["message"]), 2200)

    def test_subagent_events(self) -> None:
        self.record({"session_id": "s", "hook_event_name": "SubagentStart", "agent_type": "qa-function-agent", "agent_id": "x"})
        self.assertEqual(self.events()[0]["operation"], "invoke_agent")

    def test_secrets_redacted_everywhere(self) -> None:
        payload = post_payload(stdout=f"token {GH}", stderr="password=hunter2hunter2")
        payload["tool_input"] = {"command": f"curl -H 'Authorization: Bearer abcdef123456' {GH}"}
        self.record(payload)
        self.record({"session_id": "sess-1", "hook_event_name": "UserPromptSubmit", "prompt": f"use {GH}"})
        raw = "\n".join(f.read_text(encoding="utf-8") for f in self.dir.rglob("*.jsonl"))
        for secret in (GH, "hunter2hunter2", "abcdef123456"):
            self.assertNotIn(secret, raw)

    def test_mcp_tool_input_gets_summary_at_info_level(self) -> None:
        payload = post_payload()
        payload["tool_name"] = "mcp__x__y"
        payload["tool_input"] = {"query": "find the thing"}
        self.record(payload)
        self.assertIn("find the thing", self.events()[0]["input"]["summary"])

    def test_decision_recorded(self) -> None:
        payload = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push -f"}}
        self.record(payload, decision={"allowed": False, "reasons": ["Force push is prohibited by repository guardrails."]})
        ev = self.events()[0]
        self.assertFalse(ev["decision"]["allowed"])
        self.assertIn("Force push", ev["decision"]["reasons"][0])

    def test_session_id_is_sanitized(self) -> None:
        path = self.record(post_payload(session="../../etc/passwd"))
        assert path is not None
        self.assertEqual(path.parent.parent, self.dir)
        self.assertNotIn("..", path.name)
        path2 = self.record({"hook_event_name": "Stop"})
        assert path2 is not None
        self.assertEqual(path2.name, "unknown.jsonl")

    def test_work_item_from_env_then_branch(self) -> None:
        self.assertEqual(trace.detect_work_item({"SDLC_WORK_ITEM": "INT-042"}, "main"), "INT-042")
        self.assertEqual(trace.detect_work_item({}, "feat/INT-007-add-filter"), "INT-007")
        self.assertIsNone(trace.detect_work_item({}, "main"))

    def test_validate_event_reports_missing_fields(self) -> None:
        self.assertTrue(trace.validate_event({"v": 1}))

    def test_schema_file_matches_validator(self) -> None:
        schema = json.loads((ROOT / "docs" / "contracts" / "trace-event.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(schema["required"]), sorted(trace.REQUIRED_FIELDS))
        self.assertEqual(sorted(schema["properties"]["platform"]["enum"]), sorted(trace.PLATFORMS))
        self.assertEqual(sorted(schema["properties"]["operation"]["enum"]), sorted(trace.OPERATIONS))


class TestConcurrencyAndRetention(TraceCase):
    def test_concurrent_appends_stay_valid_jsonl(self) -> None:
        def worker(n: int) -> None:
            for i in range(25):
                self.record(post_payload(stdout=f"w{n}-{i}-" + "y" * 500))

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(self.events()), 100)

    def test_cleanup_removes_only_old_day_dirs(self) -> None:
        now = datetime(2026, 11, 21, tzinfo=timezone.utc)
        for days_ago in (0, 10, 45, 90):
            d = self.dir / (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            d.mkdir(parents=True)
            (d / "s.jsonl").write_text("{}\n", encoding="utf-8")
        (self.dir / "not-a-date").mkdir()
        removed = trace.cleanup(self.dir, retention_days=30, now=now)
        self.assertEqual(removed, 2)
        left = sorted(p.name for p in self.dir.iterdir())
        self.assertEqual(left, ["2026-11-11", "2026-11-21", "not-a-date"])

    def test_safe_record_never_raises(self) -> None:
        blocker = Path(self.tmp.name) / "file"
        blocker.write_text("x", encoding="utf-8")
        env = dict(BASE_ENV, SDLC_TRACE_DIR=str(blocker / "sub"))
        self.assertIsNone(trace.safe_record(post_payload(), platform="claude", repo_root=str(ROOT), env=env))


class TestHookIntegration(TraceCase):
    def run_hook(self, *args: str, payload: dict | str) -> subprocess.CompletedProcess:
        data = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(
            [sys.executable, str(ENTRY), *args], input=data, capture_output=True, text=True, encoding="utf-8", env=self.env, check=False
        )

    def test_trace_subcommand_records_and_exits_zero(self) -> None:
        res = self.run_hook("trace", "--platform", "claude", payload=post_payload(stdout="via hook"))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.events()[0]["output"]["stdout"], "via hook")

    def test_trace_subcommand_bad_json_still_exits_zero(self) -> None:
        self.assertEqual(self.run_hook("trace", "--platform", "claude", payload="{broken").returncode, 0)

    def test_pretooluse_records_block_decision_and_still_blocks(self) -> None:
        payload = {"session_id": "g1", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push --force"}, "cwd": str(ROOT)}
        res = self.run_hook("pretooluse", "--platform", "claude", payload=payload)
        self.assertEqual(res.returncode, 2, res.stderr)
        ev = self.events()[0]
        self.assertFalse(ev["decision"]["allowed"])
        self.assertEqual(ev["event"], "PreToolUse")

    def test_pretooluse_allowed_is_recorded(self) -> None:
        payload = {"session_id": "g2", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(ROOT)}
        self.assertEqual(self.run_hook("pretooluse", "--platform", "claude", payload=payload).returncode, 0)
        self.assertTrue(self.events()[0]["decision"]["allowed"])

    def test_pretooluse_blocks_even_if_trace_dir_unwritable(self) -> None:
        blocker = Path(self.tmp.name) / "file"
        blocker.write_text("x", encoding="utf-8")
        self.env["SDLC_TRACE_DIR"] = str(blocker / "sub")
        payload = {"tool_name": "Bash", "tool_input": {"command": "git push -f"}, "cwd": str(ROOT)}
        self.assertEqual(self.run_hook("pretooluse", payload=payload).returncode, 2)

    def test_session_start_records_event(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ENTRY), "session-start", "--platform", "codex"],
            input=json.dumps({"session_id": "ss1", "hook_event_name": "SessionStart", "source": "startup"}),
            capture_output=True, text=True, encoding="utf-8", env=self.env, check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.events()[0]["operation"], "session")

    def test_block_reasons_are_recorded_whole(self) -> None:
        payload = {"session_id": "r1", "hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": "export RELEASE_APPROVAL=1"}, "cwd": str(ROOT)}
        self.assertEqual(self.run_hook("pretooluse", payload=payload).returncode, 2)
        reasons = self.events()[0]["decision"]["reasons"]
        self.assertEqual(len(reasons), 1)
        self.assertIn("a human must export it", reasons[0])


class TestCli(TraceCase):
    def seed(self) -> None:
        self.record(post_payload(stdout="a", session="alpha-111"), decision=None)
        self.record({"session_id": "alpha-111", "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push -f"}},
                    decision={"allowed": False, "reasons": ["Force push is prohibited by repository guardrails."]})
        failure = post_payload(hook_event_name="PostToolUseFailure", error="Exit code 1\nbad", session="alpha-111")
        failure.pop("tool_response")
        self.record(failure)
        self.record(post_payload(stdout=f"leak {GH}", session="beta-222"))
        self.env["SDLC_WORK_ITEM"] = "INT-009"
        self.record(post_payload(stdout="tagged", session="gamma-333"))

    def run_cli(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = trace_cli.main(list(argv), trace_dir=self.dir)
        return rc, buf.getvalue()

    def test_list(self) -> None:
        self.seed()
        rc, out = self.run_cli("list")
        self.assertEqual(rc, 0)
        for sid in ("alpha-111", "beta-222", "gamma-333"):
            self.assertIn(sid, out)

    def test_show_by_prefix_and_tool_filter(self) -> None:
        self.seed()
        rc, out = self.run_cli("show", "alpha")
        self.assertEqual(rc, 0)
        self.assertIn("git push -f", out)
        self.assertIn("BLOCKED", out)
        rc, out = self.run_cli("show", "alpha", "--tool", "Nope")
        self.assertNotIn("git push", out)

    def test_show_unknown_session_fails(self) -> None:
        self.seed()
        self.assertEqual(self.run_cli("show", "zzz")[0], 1)

    def test_summary_counts(self) -> None:
        self.seed()
        rc, out = self.run_cli("summary", "--json")
        data = json.loads(out)
        self.assertEqual(data["sessions"], 3)
        self.assertEqual(data["blocked"], 1)
        self.assertEqual(data["failures"], 1)
        self.assertEqual(data["tools"]["Bash"], 5)

    def test_summary_filtered_by_work_item(self) -> None:
        self.seed()
        data = json.loads(self.run_cli("summary", "--work-item", "INT-009", "--json")[1])
        self.assertEqual(data["sessions"], 1)

    def test_export_writes_markdown_without_secrets(self) -> None:
        self.seed()
        out_file = Path(self.tmp.name) / "trace-summary.md"
        rc, _ = self.run_cli("export", "--work-item", "INT-009", "--out", str(out_file))
        self.assertEqual(rc, 0)
        text = out_file.read_text(encoding="utf-8")
        self.assertIn("INT-009", text)
        self.assertNotIn(GH, text)

    def test_export_scrubs_repo_and_home_paths(self) -> None:
        home = str(Path.home())
        self.env["SDLC_WORK_ITEM"] = "INT-010"
        payload = post_payload(session="paths")
        payload["tool_input"] = {"command": f"python3 {ROOT}/scripts/run.py --out {home}/private/out.txt"}
        self.record(payload)
        out_file = Path(self.tmp.name) / "scrubbed.md"
        self.assertEqual(self.run_cli("export", "--work-item", "INT-010", "--out", str(out_file))[0], 0)
        text = out_file.read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT), text)
        self.assertNotIn(home + "/private", text)
        self.assertIn("<repo>/scripts/run.py", text)

    def test_scrub_paths_handles_windows_spellings(self) -> None:
        out = trace_cli.scrub_paths(r"type C:\Users\dev\repo\a.txt and C:/Users/dev/repo/b.txt", r"C:\Users\dev\repo", home=r"C:\Users\dev")
        self.assertEqual(out, "type <repo>\\a.txt and <repo>/b.txt")

    def test_empty_store(self) -> None:
        rc, out = self.run_cli("list")
        self.assertEqual(rc, 0)
        self.assertIn("No traces", out)


if __name__ == "__main__":
    unittest.main()
