"""Unit tests for dual-mode evals/run_evals.py (contract mode, budget, sandbox diff, isolated live)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("run_evals", ROOT / "evals" / "run_evals.py")
assert spec and spec.loader
run_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_evals)


class TestDualModeEvalRunner(unittest.TestCase):
    def test_contract_mode_passes_at_least_10_cases(self) -> None:
        datasets = sorted((ROOT / "evals" / "datasets").glob("*.json"))
        self.assertGreaterEqual(len(datasets), 10)
        rc = run_evals.main(["--mode", "contract"])
        self.assertEqual(rc, 0)

    def test_harness_command_includes_budget_and_sandbox_flags(self) -> None:
        claude_cmd = run_evals.build_harness_command("claude", 1.5)
        self.assertIn("--max-budget-usd", claude_cmd)
        self.assertIn("--permission-mode", claude_cmd)
        codex_cmd = run_evals.build_harness_command("codex", 1.5)
        self.assertIn("--sandbox", codex_cmd)

    def test_live_mode_runs_in_isolated_temp_dir_and_grades_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mock_cli = Path(tmp) / "mock_cli.py"
            trace_probe = Path(tmp) / "saw_trace_dir.txt"
            mock_cli.write_text(
                f"""import json, os, sys
from pathlib import Path
Path({str(trace_probe)!r}).write_text(os.environ.get("SDLC_TRACE_DIR", ""), encoding="utf-8")
sample = {{
  "intent_ref": "INT-102",
  "spec_ref": "SPEC-102",
  "tasks": [{{
    "task_id": "TASK-001",
    "title": "Fix bug with evidence",
    "fs_refs": ["FS-001"],
    "test_refs": ["TC-HC-001"],
    "status": "completed",
    "passes": True,
    "verification_cmd": "pytest",
    "evidence": "1 passed"
  }}]
}}
print(json.dumps(sample))
""",
                encoding="utf-8",
            )
            rc = run_evals.evaluate_live_case(
                ROOT / "evals" / "datasets" / "03-bugfix-regression.json",
                [sys.executable, str(mock_cli)],
            )
            self.assertEqual(rc, [])
            saw_dir = trace_probe.read_text(encoding="utf-8")
            self.assertIn("isolated-traces", saw_dir)
            self.assertNotIn(str(ROOT / ".sdlc" / "traces"), saw_dir)

    def test_live_mode_fails_if_agent_modifies_qa_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tamper_cli = Path(tmp) / "tamper_cli.py"
            tamper_cli.write_text(
                """import json
from pathlib import Path
Path("tests/test_oracle.py").write_text("# weakened\\n", encoding="utf-8")
print(json.dumps({
  "intent_ref": "INT-102",
  "spec_ref": "SPEC-102",
  "tasks": [{
    "task_id": "TASK-001",
    "title": "Fix bug",
    "fs_refs": ["FS-001"],
    "test_refs": ["TC-HC-001"],
    "status": "completed",
    "passes": True,
    "verification_cmd": "pytest",
    "evidence": "1 passed"
  }]
}))
""",
                encoding="utf-8",
            )
            errors = run_evals.evaluate_live_case(
                ROOT / "evals" / "datasets" / "03-bugfix-regression.json",
                [sys.executable, str(tamper_cli)],
            )
            self.assertTrue(any("protected/oracle file" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
