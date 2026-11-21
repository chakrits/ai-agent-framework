"""Unit tests for Phase 3 deterministic validators, guards, and eval suite."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


validate_contracts = load_module("validate_contracts", "scripts/validate-contracts.py")
validate_budget = load_module("validate_context_budget", "scripts/validate-context-budget.py")


class TestPhase3Harness(unittest.TestCase):
    def test_defaults_and_templates_pass_contract_validation(self) -> None:
        errors = validate_contracts.check_defaults()
        self.assertEqual(errors, [])

    def test_tasks_passes_true_without_evidence_is_rejected(self) -> None:
        bad_tasks = {
            "intent_ref": "INT-001",
            "spec_ref": "SPEC-001",
            "tasks": [
                {
                    "task_id": "TASK-001",
                    "title": "Sample task",
                    "fs_refs": ["FS-001"],
                    "test_refs": ["TC-HC-001"],
                    "status": "completed",
                    "passes": True,
                    "verification_cmd": "pytest",
                    "evidence": "",
                }
            ],
        }
        errors = validate_contracts.validate_tasks_data(bad_tasks)
        self.assertTrue(any("evidence is empty" in e for e in errors))

    def test_test_report_missing_section_or_gap_is_rejected(self) -> None:
        schema = json.loads((ROOT / "docs" / "contracts" / "test-report.schema.json").read_text(encoding="utf-8"))
        bad_md = "## Section 1: Header Information\n## Section 12: Traceability Matrix\n| URD-001 | FS-001 | SCR-001 | TC-HC-001 | Gap |\n"
        errors = validate_contracts.validate_test_report_markdown(bad_md, schema)
        self.assertTrue(any("Missing required section" in e for e in errors))
        self.assertTrue(any("Gap" in e for e in errors))

    def test_context_budget_passes(self) -> None:
        violations = validate_budget.check_context_budgets(ROOT)
        self.assertEqual(violations, [])

    def test_adapter_parity_passes(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "sync-adapters.py"), "--check"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, msg=res.stderr)

    def test_guard_blocks_dev_agent_editing_constitution_and_test_oracle(self) -> None:
        env = dict(os.environ, SDLC_ACTIVE_ROLE="dev-coding-agent")
        guard = [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py")]

        res_const = subprocess.run([*guard, "--check-path", "docs/operating-model/constitution.md"], env=env, capture_output=True)
        self.assertEqual(res_const.returncode, 2)

        res_oracle = subprocess.run([*guard, "--check-path", "ebmc/test-cases/function-test-report.md"], env=env, capture_output=True)
        self.assertEqual(res_oracle.returncode, 2)

        res_src = subprocess.run([*guard, "--check-path", "src/service.py"], env=env, capture_output=True)
        self.assertEqual(res_src.returncode, 0)

    def test_guard_blocks_unapproved_production_deploy(self) -> None:
        guard = [sys.executable, str(ROOT / "scripts" / "sdlc_hook.py")]
        env = {k: v for k, v in os.environ.items() if k not in {"RELEASE_APPROVAL", "SDLC_ACTIVE_ROLE"}}
        res = subprocess.run([*guard, "--check-cmd", "make deploy production"], env=env, capture_output=True)
        self.assertEqual(res.returncode, 2)

    def test_eval_suite_passes(self) -> None:
        res = subprocess.run(
            [sys.executable, str(ROOT / "evals" / "run_evals.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, msg=res.stderr)


if __name__ == "__main__":
    unittest.main()
