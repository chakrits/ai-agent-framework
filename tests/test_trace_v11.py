"""Trace v1.1: local-time stamps, model/effort, new hook events, level config, hooks CLI and agent guard rules."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import commands, trace, trace_cli, trace_config, trace_hooks, trace_state  # noqa: E402

BKK = timezone(timedelta(hours=7))
BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith("SDLC_") and k not in {"CLAUDE_PROJECT_DIR", "ANTHROPIC_MODEL"}}


def tool_payload(session: str = "s1", **extra) -> dict:
    payload = {
        "session_id": session,
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_use_id": "tu1",
        "tool_input": {"command": "echo hi"},
        "tool_response": {"stdout": "hi", "stderr": ""},
    }
    payload.update(extra)
    return payload


class V11Case(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_dir = Path(self.tmp.name)
        self.dir = self.state_dir / "traces"
        self.env = dict(BASE_ENV, SDLC_TRACE_DIR=str(self.dir))

    def rec(self, payload: dict, platform: str = "claude", **kw) -> Path | None:
        return trace.record(payload, platform=platform, repo_root=str(ROOT), env=self.env, **kw)

    def events(self) -> list[dict]:
        out: list[dict] = []
        for f in sorted(self.dir.rglob("*.jsonl")):
            out.extend(json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line)
        return out


class TestTimestamps(V11Case):
    def test_local_stamp_keeps_machine_offset_and_day_dir(self) -> None:
        path = self.rec(tool_payload(), now=datetime(2026, 11, 22, 0, 30, tzinfo=BKK))
        assert path is not None
        self.assertEqual(self.events()[0]["ts"], "2026-11-22T00:30:00.000+07:00")
        self.assertEqual(path.parent.name, "2026-11-22")

    def test_utc_mode_converts(self) -> None:
        self.env["SDLC_TRACE_TZ"] = "utc"
        path = self.rec(tool_payload(), now=datetime(2026, 11, 22, 0, 30, tzinfo=BKK))
        assert path is not None
        self.assertEqual(self.events()[0]["ts"], "2026-11-21T17:30:00.000+00:00")
        self.assertEqual(path.parent.name, "2026-11-21")

    def test_default_stamp_is_now_with_offset(self) -> None:
        self.rec(tool_payload())
        ts = self.events()[0]["ts"]
        self.assertRegex(ts, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$")
        self.assertLess(abs((datetime.fromisoformat(ts) - datetime.now(timezone.utc)).total_seconds()), 10)

    @unittest.skipIf(os.name == "nt", "TZ database selection via env is POSIX-only")
    def test_machine_in_bangkok_gets_plus_seven(self) -> None:
        code = "import sys; sys.path.insert(0, sys.argv[1]); from sdlc_guard import trace; print(trace.stamp('local'))"
        out = subprocess.run(
            [sys.executable, "-c", code, str(ROOT / "scripts")],
            env=dict(BASE_ENV, TZ="Asia/Bangkok"), capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertTrue(out.endswith("+07:00"), out)

    def test_cli_orders_by_instant_not_by_string(self) -> None:
        day = self.dir / "2026-11-21"
        day.mkdir(parents=True)
        later_utc = {"ts": "2026-11-21T00:00:00.000+00:00", "session_id": "b"}
        earlier_bkk = {"ts": "2026-11-21T01:00:00.000+07:00", "session_id": "a"}  # = 2026-11-20T18:00Z
        (day / "x.jsonl").write_text("\n".join(json.dumps(e) for e in (later_utc, earlier_bkk)) + "\n", encoding="utf-8")
        self.assertEqual([e["session_id"] for e in trace_cli.load_events(self.dir)], ["a", "b"])


class TestModelAndEffort(V11Case):
    def test_claude_model_from_session_start_then_state(self) -> None:
        self.rec({"session_id": "m1", "hook_event_name": "SessionStart", "model": "claude-opus-5-5", "source": "startup"})
        self.rec(tool_payload("m1"))
        first, second = self.events()
        self.assertEqual((first["model"], first["model_source"]), ("claude-opus-5-5", "payload"))
        self.assertEqual((second["model"], second["model_source"]), ("claude-opus-5-5", "state"))
        self.assertEqual(trace_state.load(self.state_dir, "m1")["model"], "claude-opus-5-5")

    def test_effort_object_is_flattened_and_remembered(self) -> None:
        self.rec(tool_payload("e1", effort={"level": "medium"}))
        self.rec({"session_id": "e1", "hook_event_name": "Stop", "last_assistant_message": "done"})
        a, b = self.events()
        self.assertEqual((a["effort"], a["effort_source"]), ("medium", "payload"))
        self.assertEqual((b["effort"], b["effort_source"]), ("medium", "state"))

    def test_effort_string_and_unavailable(self) -> None:
        self.rec(tool_payload("e2", effort="high"))
        self.rec(tool_payload("e3"))
        a, b = self.events()
        self.assertEqual(a["effort"], "high")
        self.assertNotIn("effort", b)
        self.assertEqual(b["effort_source"], "unavailable")

    def test_post_model_switch_updates_but_pre_does_not(self) -> None:
        self.rec({"session_id": "w1", "hook_event_name": "SessionStart", "model": "claude-opus-5-5"})
        self.rec({"session_id": "w1", "hook_event_name": "PreModelSwitch", "from_model": "claude-opus-5-5", "to_model": "claude-sonnet-5-5", "source": "command"})
        self.rec(tool_payload("w1"))
        self.assertEqual(self.events()[-1]["model"], "claude-opus-5-5")
        self.rec({"session_id": "w1", "hook_event_name": "PostModelSwitch", "from_model": "claude-opus-5-5", "to_model": "claude-sonnet-5-5", "source": "command"})
        self.rec(tool_payload("w1"))
        evs = self.events()
        self.assertEqual(evs[-2]["model"], "claude-sonnet-5-5")
        self.assertEqual(evs[-2]["to_model"], "claude-sonnet-5-5")
        self.assertEqual(evs[-2]["switch_source"], "command")
        self.assertEqual(evs[-1]["model"], "claude-sonnet-5-5")

    def test_env_fallback_and_unknown(self) -> None:
        self.rec(tool_payload("u1"))
        self.env["ANTHROPIC_MODEL"] = "claude-from-env"
        self.rec(tool_payload("u2"))
        a, b = self.events()
        self.assertEqual((a["model"], a["model_source"]), ("unknown", "unknown"))
        self.assertEqual((b["model"], b["model_source"]), ("claude-from-env", "env"))

    def test_codex_model_on_every_event_and_no_effort(self) -> None:
        self.rec(tool_payload("c1", model="gpt-5-codex"), platform="codex")
        ev = self.events()[0]
        self.assertEqual((ev["model"], ev["model_source"]), ("gpt-5-codex", "payload"))
        self.assertEqual(ev["effort_source"], "unavailable")
        self.assertNotIn("effort", ev)

    def test_sessions_do_not_share_state(self) -> None:
        self.rec({"session_id": "a1", "hook_event_name": "SessionStart", "model": "claude-opus-5-5"})
        self.rec(tool_payload("b1"))
        self.assertEqual(self.events()[1]["model"], "unknown")

    def test_agent_tool_records_subagent_model(self) -> None:
        payload = tool_payload("g1", tool_name="Agent")
        payload["tool_response"] = {"resolvedModel": "claude-haiku-5-5", "content": "ok"}
        self.rec(payload)
        self.assertEqual(self.events()[0]["subagent_model"], "claude-haiku-5-5")

    def test_event_survives_a_failing_state_write(self) -> None:
        """On Windows os.replace can fail while another hook holds the state file; the event must still be written."""
        from unittest import mock

        with mock.patch.object(trace_state, "save", side_effect=PermissionError("locked")):
            path = self.rec({"session_id": "w2", "hook_event_name": "SessionStart", "model": "claude-opus-5-5"})
        self.assertIsNotNone(path)
        self.assertEqual(self.events()[0]["model"], "claude-opus-5-5")

    def test_state_cleanup_removes_old_files_only(self) -> None:
        trace_state.save(self.state_dir, "old", {"model": "x"})
        trace_state.save(self.state_dir, "new", {"model": "y"})
        old = trace_state.state_file(self.state_dir, "old")
        past = (datetime.now() - timedelta(days=45)).timestamp()
        os.utime(old, (past, past))
        self.assertEqual(trace_state.cleanup(self.state_dir, retention_days=30), 1)
        self.assertFalse(old.exists())
        self.assertTrue(trace_state.state_file(self.state_dir, "new").exists())


class TestNewEvents(V11Case):
    def one(self, payload: dict, platform: str = "claude") -> dict:
        self.rec(payload, platform=platform)
        ev = self.events()[-1]
        self.assertEqual(trace.validate_event(ev), [], ev)
        return ev

    def test_permission_request_and_denied(self) -> None:
        ev = self.one({"session_id": "p", "hook_event_name": "PermissionRequest", "tool_name": "Bash", "tool_input": {"command": "rm -rf x"}, "permission_mode": "default"})
        self.assertEqual((ev["operation"], ev["input"]["command"], ev["permission_mode"]), ("permission", "rm -rf x", "default"))
        ev = self.one({"session_id": "p", "hook_event_name": "PermissionDenied", "tool_name": "Bash", "tool_input": {"command": "x"}, "reason": "auto mode classifier"})
        self.assertEqual((ev["operation"], ev["reason"]), ("permission", "auto mode classifier"))

    def test_config_change_and_instructions_loaded(self) -> None:
        ev = self.one({"session_id": "c", "hook_event_name": "ConfigChange", "source": "project_settings", "file_path": "/r/.claude/settings.json"})
        self.assertEqual((ev["operation"], ev["config_source"], ev["file_path"]), ("config", "project_settings", "/r/.claude/settings.json"))
        self.assertNotIn("source", ev)
        ev = self.one({"session_id": "c", "hook_event_name": "InstructionsLoaded", "file_path": "CLAUDE.md", "memory_type": "Project", "load_reason": "session_start"})
        self.assertEqual((ev["operation"], ev["memory_type"], ev["load_reason"]), ("config", "Project", "session_start"))

    def test_stop_failure(self) -> None:
        ev = self.one({"session_id": "f", "hook_event_name": "StopFailure", "error": "rate_limit", "error_details": "429 too many"})
        self.assertEqual((ev["operation"], ev["error_type"], ev["error"]), ("turn_end", "rate_limit", "429 too many"))

    def test_codex_post_model_request_tokens(self) -> None:
        ev = self.one({"session_id": "x", "hook_event_name": "PostModelRequest", "turn_id": "t1", "model": "gpt-5-codex", "status": "completed",
                       "token_usage": {"input_tokens": 10, "output_tokens": 5, "note": "ignored"}}, platform="codex")
        self.assertEqual((ev["operation"], ev["status"], ev["turn_id"]), ("model", "completed", "t1"))
        self.assertEqual(ev["token_usage"], {"input_tokens": 10, "output_tokens": 5})

    def test_notification_compaction_task_interrupt(self) -> None:
        ev = self.one({"session_id": "n", "hook_event_name": "Notification", "message": "needs input", "notification_type": "idle_prompt", "title": "T"})
        self.assertEqual((ev["operation"], ev["message"], ev["notification_type"]), ("notification", "needs input", "idle_prompt"))
        ev = self.one({"session_id": "n", "hook_event_name": "PreCompact", "trigger": "auto"})
        self.assertEqual((ev["operation"], ev["trigger"]), ("compaction", "auto"))
        ev = self.one({"session_id": "n", "hook_event_name": "TaskCreated", "task_id": "t1", "task_subject": "do it"})
        self.assertEqual((ev["operation"], ev["task_id"], ev["task_subject"]), ("task", "t1", "do it"))
        ev = self.one({"session_id": "n", "hook_event_name": "Interrupt", "turn_id": "t9", "permission_mode": "plan"}, platform="codex")
        self.assertEqual((ev["operation"], ev["turn_id"]), ("turn_end", "t9"))

    def test_ids_mcp_and_batch(self) -> None:
        payload = tool_payload("i", prompt_id="pr-1", permission_mode="bypassPermissions", mcp_server={"name": "fs", "source": "project"})
        ev = self.one(payload)
        self.assertEqual((ev["prompt_id"], ev["permission_mode"], ev["mcp_server"]), ("pr-1", "bypassPermissions", "fs"))
        ev = self.one({"session_id": "i", "hook_event_name": "PostToolBatch", "tool_calls": [{}, {}, {}]})
        self.assertEqual(ev["tool_count"], 3)

    def test_secrets_in_new_text_fields_are_redacted(self) -> None:
        token = "ghp_" + "a1B2c3D4" * 5
        self.one({"session_id": "r", "hook_event_name": "Notification", "message": f"use {token}", "title": "t"})
        self.assertNotIn(token, "\n".join(f.read_text(encoding="utf-8") for f in self.dir.rglob("*.jsonl")))


class TestConfigPrecedence(V11Case):
    def setUp(self) -> None:
        super().setUp()
        self.cfg_path = trace_config.config_path(self.state_dir)

    def test_default_then_file_then_env(self) -> None:
        self.assertEqual(trace_config.effective({}, {})["level"], "info")
        eff = trace_config.effective({}, {"level": "debug"})
        self.assertEqual((eff["level"], eff["level_source"]), ("debug", "config"))
        eff = trace_config.effective({"SDLC_TRACE_LEVEL": "off"}, {"level": "debug"})
        self.assertEqual((eff["level"], eff["level_source"]), ("off", "env"))

    def test_invalid_values_fall_back(self) -> None:
        eff = trace_config.effective({"SDLC_TRACE_LEVEL": "loud", "SDLC_TRACE_TZ": "mars"}, {"level": "nope", "tz": "x", "retention_days": -3})
        self.assertEqual((eff["level"], eff["tz"], eff["retention_days"]), ("info", "local", 30))

    def test_ttl_expires_back_to_default(self) -> None:
        now = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
        trace_config.set_level(self.cfg_path, "debug", minutes=30, now=now)
        cfg = trace_config.load(self.cfg_path)
        self.assertEqual(trace_config.effective({}, cfg, now=now + timedelta(minutes=29))["level"], "debug")
        eff = trace_config.effective({}, cfg, now=now + timedelta(minutes=31))
        self.assertEqual((eff["level"], eff["level_source"], eff["expired"]), ("info", "default", True))

    def test_tz_and_retention_settings(self) -> None:
        eff = trace_config.effective({}, {"tz": "utc", "retention_days": 7})
        self.assertEqual((eff["tz"], eff["retention_days"]), ("utc", 7))
        eff = trace_config.effective({"SDLC_TRACE_RETENTION_DAYS": "90"}, {"retention_days": 7})
        self.assertEqual((eff["retention_days"], eff["retention_source"]), (90, "env"))

    def test_parse_duration(self) -> None:
        self.assertEqual([trace_config.parse_duration_minutes(x) for x in ("30m", "2h", "45", " 10 M ")], [30, 120, 45, 10])
        for bad in ("0m", "abc", "-5m", "1.5h", ""):
            with self.assertRaises(ValueError):
                trace_config.parse_duration_minutes(bad)

    def test_corrupt_file_is_ignored(self) -> None:
        self.cfg_path.write_text("{not json", encoding="utf-8")
        self.assertEqual(trace_config.load(self.cfg_path), {})

    def test_record_honours_config_file(self) -> None:
        trace_config.set_level(self.cfg_path, "debug")
        self.rec(tool_payload())
        self.assertEqual(self.events()[0]["level"], "debug")
        self.assertIn("input_raw", self.events()[0])
        trace_config.set_level(self.cfg_path, "off")
        before = len(self.events())
        self.rec(tool_payload())
        self.assertEqual(len(self.events()), before)

    def test_config_tz_used_by_record(self) -> None:
        trace_config.set_value(self.cfg_path, "tz", "utc")
        self.rec(tool_payload(), now=datetime(2026, 11, 22, 0, 30, tzinfo=BKK))
        self.assertTrue(self.events()[0]["ts"].endswith("+00:00"))


class CliCase(V11Case):
    def run_cli(self, *argv: str, tty: bool = False, env: dict | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = trace_cli.main(list(argv), trace_dir=self.dir, is_tty=lambda: tty, repo_root=self.state_dir / "repo", env=env or self.env)
            except SystemExit as exc:  # argparse errors
                rc = int(exc.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def cfg(self) -> dict:
        return trace_config.load(trace_config.config_path(self.state_dir))


class TestConfigCli(CliCase):
    def test_show_reports_values_and_sources(self) -> None:
        rc, out, _ = self.run_cli("config", "show")
        self.assertEqual(rc, 0)
        self.assertIn("level", out)
        self.assertIn("info", out)
        self.assertIn("default", out)
        data = json.loads(self.run_cli("config", "show", "--json")[1])
        self.assertEqual((data["level"], data["tz"], data["retention_days"]), ("info", "local", 30))

    def test_agent_may_raise_to_debug_with_ttl_and_it_is_audited(self) -> None:
        rc, out, _ = self.run_cli("config", "set", "level", "debug", "--for", "30m", tty=False)
        self.assertEqual(rc, 0, out)
        cfg = self.cfg()
        self.assertEqual(cfg["level"], "debug")
        self.assertIn("expires_at", cfg)
        ev = [e for e in self.events() if e["event"] == "TraceConfigChange"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["operation"], "config")
        self.assertIn("debug", ev[0]["reason"])

    def test_agent_cannot_do_human_only_changes(self) -> None:
        for argv in (("config", "set", "level", "off"), ("config", "set", "level", "debug"), ("config", "set", "level", "off", "--for", "10m"),
                     ("config", "set", "level", "info"), ("config", "unset", "level"), ("config", "set", "tz", "utc"),
                     ("config", "set", "retention_days", "7")):
            with self.subTest(argv=argv):
                rc, _, err = self.run_cli(*argv, tty=False)
                self.assertEqual(rc, 3, err)
                self.assertIn("human", err)
        self.assertEqual(self.cfg(), {})

    def test_agent_cannot_override_a_level_a_human_set(self) -> None:
        self.run_cli("config", "set", "level", "off", tty=True)
        rc, _, err = self.run_cli("config", "set", "level", "debug", "--for", "30m", tty=False)
        self.assertEqual(rc, 3, err)
        self.assertIn("human", err)
        self.assertEqual(self.cfg()["level"], "off")
        self.run_cli("config", "set", "level", "debug", tty=True)  # persistent human debug must not be downgraded by a TTL
        self.assertEqual(self.run_cli("config", "set", "level", "debug", "--for", "10m", tty=False)[0], 3)
        self.assertNotIn("expires_at", self.cfg())

    def test_agent_may_renew_its_own_ttl_and_human_may_override_it(self) -> None:
        self.assertEqual(self.run_cli("config", "set", "level", "debug", "--for", "10m", tty=False)[0], 0)
        self.assertEqual(self.run_cli("config", "set", "level", "debug", "--for", "20m", tty=False)[0], 0)
        self.assertEqual(self.run_cli("config", "set", "level", "off", tty=True)[0], 0)
        self.run_cli("config", "unset", "level", tty=True)
        self.assertEqual(self.run_cli("config", "set", "level", "debug", "--for", "5m", tty=False)[0], 0)

    def test_ttl_is_capped_at_120_minutes(self) -> None:
        for tty in (False, True):
            rc, _, err = self.run_cli("config", "set", "level", "debug", "--for", "3h", tty=tty)
            self.assertEqual(rc, 2, err)
        rc, _, _ = self.run_cli("config", "set", "level", "debug", "--for", "2h", tty=False)
        self.assertEqual(rc, 0)

    def test_human_can_change_everything(self) -> None:
        self.assertEqual(self.run_cli("config", "set", "level", "debug", tty=True)[0], 0)
        self.assertEqual(self.cfg()["level"], "debug")
        self.assertNotIn("expires_at", self.cfg())
        self.assertEqual(self.run_cli("config", "set", "tz", "utc", tty=True)[0], 0)
        self.assertEqual(self.run_cli("config", "set", "retention_days", "7", tty=True)[0], 0)
        self.assertEqual((self.cfg()["tz"], self.cfg()["retention_days"]), ("utc", 7))
        self.assertEqual(self.run_cli("config", "set", "level", "off", tty=True)[0], 0)
        self.assertEqual(self.cfg()["level"], "off")
        self.assertEqual(self.run_cli("config", "unset", "level", tty=True)[0], 0)
        self.assertNotIn("level", self.cfg())

    def test_off_change_is_audited_before_it_takes_effect(self) -> None:
        self.run_cli("config", "set", "level", "off", tty=True)
        ev = [e for e in self.events() if e["event"] == "TraceConfigChange"]
        self.assertEqual(len(ev), 1)
        self.assertIn("off", ev[0]["reason"])

    def test_invalid_values_rejected(self) -> None:
        for argv in (("config", "set", "level", "loud"), ("config", "set", "tz", "mars"), ("config", "set", "retention_days", "0"), ("config", "set", "colour", "x")):
            with self.subTest(argv=argv):
                self.assertEqual(self.run_cli(*argv, tty=True)[0], 2)

    def test_env_override_is_reported(self) -> None:
        env = dict(self.env, SDLC_TRACE_LEVEL="debug")
        rc, out, err = self.run_cli("config", "show", env=env)
        self.assertIn("env", out)
        rc, out, err = self.run_cli("config", "set", "level", "off", tty=True, env=env)
        self.assertEqual(rc, 0)
        self.assertIn("SDLC_TRACE_LEVEL", out + err)


class TestHooksCli(CliCase):
    def settings_local(self) -> Path:
        return self.state_dir / "repo" / ".claude" / "settings.local.json"

    def test_list_shows_tiers(self) -> None:
        rc, out, _ = self.run_cli("hooks", "list")
        self.assertEqual(rc, 0)
        for needle in ("PermissionRequest", "ConfigChange", "cwd", "CwdChanged", "model-switch"):
            self.assertIn(needle, out)

    def test_enable_disable_roundtrip_preserves_other_settings(self) -> None:
        self.settings_local().parent.mkdir(parents=True)
        self.settings_local().write_text(json.dumps({"model": "keep-me", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}}), encoding="utf-8")
        self.assertEqual(self.run_cli("hooks", "enable", "cwd", tty=True)[0], 0)
        data = json.loads(self.settings_local().read_text(encoding="utf-8"))
        handler = data["hooks"]["CwdChanged"][0]["hooks"][0]
        self.assertEqual((handler["type"], handler["async"]), ("command", True))
        self.assertIn("sdlc-hook", handler["command"])
        self.assertEqual(data["model"], "keep-me")
        self.assertEqual(self.run_cli("hooks", "enable", "cwd", tty=True)[0], 0)  # idempotent
        self.assertEqual(len(json.loads(self.settings_local().read_text(encoding="utf-8"))["hooks"]["CwdChanged"]), 1)
        self.assertEqual(self.run_cli("hooks", "disable", "cwd", tty=True)[0], 0)
        data = json.loads(self.settings_local().read_text(encoding="utf-8"))
        self.assertNotIn("CwdChanged", data["hooks"])
        self.assertEqual(data["hooks"]["Stop"][0]["hooks"][0]["command"], "echo mine")
        self.assertEqual(data["model"], "keep-me")

    def test_enable_requires_human_and_known_group(self) -> None:
        self.assertEqual(self.run_cli("hooks", "enable", "cwd", tty=False)[0], 3)
        self.assertFalse(self.settings_local().exists())
        self.assertEqual(self.run_cli("hooks", "enable", "nonsense", tty=True)[0], 2)

    def test_list_marks_enabled_group(self) -> None:
        self.run_cli("hooks", "enable", "elicitation", tty=True)
        out = self.run_cli("hooks", "list")[1]
        self.assertRegex(out, r"elicitation\s+.*enabled")


class TestAgentGuardRules(unittest.TestCase):
    def reasons(self, cmd: str) -> list[str]:
        return commands.dangerous_command_reasons(commands.analyze(cmd, "posix"), {}, allow_force_with_lease=False)

    def test_allowed_for_agents(self) -> None:
        for cmd in (
            "python3 scripts/sdlc_trace.py config show",
            "python3 scripts/sdlc_trace.py config show --json",
            "python3 scripts/sdlc_trace.py config set level debug --for 30m",
            "python3 scripts/sdlc_trace.py config set level debug --for=2h",
            "py -3 scripts\\sdlc_trace.py config set level DEBUG --for 45",
            "python3 scripts/sdlc_hook.py traces config set level debug --for 10m",
            "python3 scripts/sdlc_trace.py hooks list",
            "python3 scripts/sdlc_trace.py list",
            "python3 scripts/sdlc_trace.py show abc --output",
            "python3 scripts/sdlc_trace.py summary --json",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.reasons(cmd), [], cmd)

    def test_blocked_for_agents(self) -> None:
        for cmd in (
            "python3 scripts/sdlc_trace.py config set level off",
            "python3 scripts/sdlc_trace.py config set level debug",
            "python3 scripts/sdlc_trace.py config set level debug --for 3h",
            "python3 scripts/sdlc_trace.py config set level debug --for 121m",
            "python3 scripts/sdlc_trace.py config set level info --for 10m",
            "python3 scripts/sdlc_trace.py config unset level",
            "python3 scripts/sdlc_trace.py config set tz utc",
            "python3 scripts/sdlc_trace.py config set retention_days 1",
            "python3 scripts/sdlc_trace.py hooks enable cwd",
            "python3 scripts/sdlc_trace.py hooks disable cwd",
            "python3 scripts/sdlc_hook.py traces config set level off",
            "python3 scripts/sdlc_hook.py traces hooks enable cwd",
            "cd repo && python3 scripts/sdlc_trace.py config set level off",
        ):
            with self.subTest(cmd=cmd):
                self.assertTrue(self.reasons(cmd), cmd)


class TestHookRegistrations(unittest.TestCase):
    def test_claude_settings_register_tier1_and_never_forbidden_events(self) -> None:
        hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
        for ev in trace_hooks.CLAUDE_TIER1_ASYNC:
            handler = hooks[ev][0]["hooks"][0]
            self.assertTrue(handler.get("async"), ev)
            self.assertIn("trace --platform claude", handler["command"])
        for ev in trace_hooks.CLAUDE_TIER1_SYNC:
            self.assertNotIn("async", hooks[ev][0]["hooks"][0], ev)
        for ev in trace_hooks.FORBIDDEN_TRACE_EVENTS:
            self.assertNotIn(ev, hooks)
        for group_events in trace_hooks.CLAUDE_TIER2.values():
            for ev in group_events:
                self.assertNotIn(ev, hooks, "tier 2 events are opt-in")

    def test_codex_hooks_register_tier1(self) -> None:
        hooks = json.loads((ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        for ev in trace_hooks.CODEX_TIER1_ASYNC:
            handler = hooks[ev][0]["hooks"][0]
            self.assertTrue(handler.get("async"), ev)
            self.assertIn("commandWindows", handler)
        for ev in trace_hooks.FORBIDDEN_TRACE_EVENTS:
            self.assertNotIn(ev, hooks)

    def test_trace_handlers_never_return_decisions(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py"), "trace", "--platform", "claude"],
            input=json.dumps({"session_id": "q", "hook_event_name": "PermissionRequest", "tool_name": "Bash", "tool_input": {"command": "ls"}}),
            capture_output=True, text=True, env=dict(BASE_ENV, SDLC_TRACE_LEVEL="off"), check=False,
        )
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))


class TestDocs(unittest.TestCase):
    def test_manual_covers_levels_and_who_can_change(self) -> None:
        text = (ROOT / "docs" / "guides" / "agent-trace-manual.md").read_text(encoding="utf-8")
        for needle in ("SDLC_TRACE_LEVEL", "off", "info", "debug", "--for", "config set", "UTC+7", "bypassPermissions", "agent", "Windows"):
            self.assertIn(needle, text, needle)

    def test_monitoring_guide_and_examples(self) -> None:
        guide = (ROOT / "docs" / "guides" / "agent-trace-monitoring.md").read_text(encoding="utf-8")
        for needle in ("Grafana", "Loki", "Elastic", "OpenSearch", "OpenTelemetry", "ทดสอบ"):
            self.assertIn(needle, guide, needle)
        ex = ROOT / "docs" / "guides" / "examples"
        for name in ("alloy.config", "filebeat.yml", "otelcol.yaml", "opensearch-index-template.json"):
            self.assertTrue((ex / name).is_file(), name)
        template = json.loads((ex / "opensearch-index-template.json").read_text(encoding="utf-8"))
        props = template["template"]["mappings"]["properties"]
        self.assertEqual(props["ts"]["type"], "date")
        for field in ("model", "effort", "role", "tool_name", "operation"):
            self.assertEqual(props[field]["type"], "keyword", field)

    def test_agent_trace_skill_exists_and_is_mirrored(self) -> None:
        for base in (".agents", ".claude", ".agent"):
            text = (ROOT / base / "skills" / "agent-trace" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: agent-trace", text)
            self.assertIn("--for", text)
        self.assertLessEqual(len((ROOT / ".agents" / "skills" / "agent-trace" / "SKILL.md").read_text(encoding="utf-8").splitlines()), 35)


if __name__ == "__main__":
    unittest.main()
