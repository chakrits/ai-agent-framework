"""Unit tests for dual-mode evals/run_evals.py (contract mode, budget cap, committed oracle diff, isolated live)."""

from __future__ import annotations

import importlib.util
import subprocess
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
    def test_git_diff_reports_unicode_paths_on_both_sides_of_renames(self) -> None:
        for commit_rename in (False, True):
            with self.subTest(committed=commit_rename), tempfile.TemporaryDirectory() as tmp:
                sandbox = Path(tmp)
                source = "tests/ต้นทาง.py"
                target = "docs/contracts/ปลายทาง.py"
                for path in (source, target):
                    (sandbox / path).parent.mkdir(parents=True)
                (sandbox / source).write_text("sample\n", encoding="utf-8")
                baseline = run_evals._init_sandbox_git(sandbox)
                subprocess.run(["git", "mv", source, target], cwd=sandbox, check=True)
                if commit_rename:
                    subprocess.run(
                        ["git", "commit", "-m", "move fixture"], cwd=sandbox, check=True, capture_output=True
                    )
                errors = run_evals._check_sandbox_diff(sandbox, baseline, "EVAL-TEST")
                for path in (source, target):
                    self.assertTrue(any(error.endswith(path) for error in errors), errors)

    def test_contract_mode_passes_at_least_10_cases(self) -> None:
        datasets = sorted((ROOT / "evals" / "datasets").glob("*.json"))
        self.assertGreaterEqual(len(datasets), 10)
        rc = run_evals.main(["--mode", "contract"])
        self.assertEqual(rc, 0)

    def test_harness_command_includes_budget_and_sandbox_and_rejects_unsupported(self) -> None:
        claude_cmd = run_evals.build_harness_command("claude", 1.5)
        self.assertIn("--max-budget-usd", claude_cmd)
        self.assertIn("--permission-mode", claude_cmd)
        codex_cmd = run_evals.build_harness_command("codex", 1.5)
        self.assertIn("--sandbox", codex_cmd)
        with self.assertRaises(ValueError):
            run_evals.build_harness_command("antigravity", 1.5)

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

    def test_live_mode_fails_if_agent_modifies_and_commits_qa_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tamper_cli = Path(tmp) / "tamper_commit_cli.py"
            tamper_cli.write_text(
                """import json, subprocess
from pathlib import Path
Path("tests/test_oracle.py").write_text("# committed tampering\\n", encoding="utf-8")
subprocess.run(["git", "add", "tests/test_oracle.py"], check=True)
subprocess.run(["git", "commit", "-m", "hide oracle edit"], check=True, capture_output=True)
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

    def test_live_mode_fails_closed_if_git_state_unreadable_or_budget_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corrupt_cli = Path(tmp) / "corrupt_git_cli.py"
            corrupt_cli.write_text(
                """import json, shutil
shutil.rmtree(".git")
print(json.dumps({"intent_ref": "INT-102", "spec_ref": "SPEC-102", "tasks": []}))
""",
                encoding="utf-8",
            )
            errors = run_evals.evaluate_live_case(
                ROOT / "evals" / "datasets" / "03-bugfix-regression.json",
                [sys.executable, str(corrupt_cli)],
            )
            self.assertTrue(any("fail-closed" in e for e in errors))

            over_budget_cli = Path(tmp) / "over_budget_cli.py"
            over_budget_cli.write_text(
                """import json
print(json.dumps({
  "cost_usd": 5.0,
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
            budget_errs = run_evals.evaluate_live_case(
                ROOT / "evals" / "datasets" / "03-bugfix-regression.json",
                [sys.executable, str(over_budget_cli)],
                max_budget=1.0,
            )
            self.assertTrue(any("exceeds max_budget" in e for e in budget_errs))


if __name__ == "__main__":
    unittest.main()
