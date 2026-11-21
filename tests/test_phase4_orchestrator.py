"""Unit tests for Phase 4 stateless Python orchestrator, telemetry, and Stage 6 control bands."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from orchestrator.api.handlers import OrchestratorService
from orchestrator.core.loader import assemble_agent_prompt, load_framework
from orchestrator.core.router import RiskTier, WorkType, classify_and_route
from orchestrator.graphs.sdlc_pipeline import AgentExecutionResult, CliHarnessExecutor, PipelineState, SDLCPipelineRunner
from orchestrator.telemetry.bands import draft_incident_intent, evaluate_control_band
from orchestrator.telemetry.tracker import TelemetryTracker

ROOT = Path(__file__).resolve().parent.parent


class FlakyOnceDevExecutor:
    """Fails dev-coding-agent on first attempt to verify self-correction retry loop."""

    def __init__(self) -> None:
        self.dev_calls = 0

    def execute(self, agent_name: str, assembled_prompt: str, state: PipelineState) -> AgentExecutionResult:
        if agent_name == "dev-coding-agent":
            self.dev_calls += 1
            if self.dev_calls == 1:
                return AgentExecutionResult(agent_name, False, "test failed once", 100, 20, 0.01, 5.0)
        return AgentExecutionResult(agent_name, True, f"ok:{agent_name}", 120, 30, 0.02, 4.0)


class TestPhase4Orchestrator(unittest.TestCase):
    def test_loader_loads_canonical_core_and_optional_ebmc_pack(self) -> None:
        core = load_framework(ROOT)
        self.assertGreaterEqual(len(core.agents), 7)
        self.assertIn("qa-function-agent", core.agents)
        self.assertNotIn("robot-framework-ebmc", core.skills)

        ebmc = load_framework(ROOT, project_pack="ebmc")
        self.assertIn("robot-framework-ebmc", ebmc.skills)

        prompt = assemble_agent_prompt(ebmc, "qa-function-agent", "Analyze SPEC-001")
        self.assertIn("Governance Constitution", prompt)
        self.assertIn("ISTQB Test Design Skill", prompt)

    def test_router_escalates_low_risk_auth_bug_to_high_risk(self) -> None:
        plan = classify_and_route(WorkType.BUG_FIX, RiskTier.LOW, "Fix auth JWT validation bypass")
        self.assertEqual(plan.risk_tier, RiskTier.HIGH)
        self.assertTrue(plan.escalated)
        self.assertEqual(plan.stages[0].stage_id, "impact_check")
        self.assertTrue(plan.stages[-1].parallel)

    def test_pipeline_pauses_at_hitl_gates_and_retries_build(self) -> None:
        bundle = load_framework(ROOT)
        plan = classify_and_route(WorkType.NEW_FEATURE, RiskTier.MEDIUM, "Add claim export CSV")
        with tempfile.TemporaryDirectory() as tmp:
            tracker = TelemetryTracker(Path(tmp) / "runs.jsonl")
            runner = SDLCPipelineRunner(bundle, executor=FlakyOnceDevExecutor(), tracker=tracker, max_retries=2)
            state = PipelineState("RUN-TEST-01", str(ROOT), "Add claim export CSV", plan)

            # Pauses at Gate 1
            state = runner.run(state)
            self.assertEqual(state.status, "waiting_human_gate")
            self.assertEqual(state.pending_gate, "Gate 1: Scope & Intent")

            # Approve Gate 1 -> pauses at Gate 2
            state = runner.approve_gate(state)
            self.assertEqual(state.status, "waiting_human_gate")
            self.assertEqual(state.pending_gate, "Gate 2: Architecture & Spec")

            # Approve Gate 2 -> runs QA, Dev (with 1 retry), Parallel Review -> pauses at Gate 3
            state = runner.approve_gate(state)
            self.assertEqual(state.status, "waiting_human_gate")
            self.assertEqual(state.pending_gate, "Gate 3: Release & Merge")
            self.assertEqual(state.attempts["build"], 2)
            self.assertEqual(len(state.stage_outputs["review_and_security"]), 2)

            # Approve Gate 3 -> completed
            state = runner.approve_gate(state)
            self.assertEqual(state.status, "completed")

            summary = tracker.summarize_run("RUN-TEST-01")
            self.assertEqual(len(summary.gates_approved), 3)
            self.assertGreater(summary.total_cost_usd, 0.0)

    def test_stage6_control_band_breach_drafts_intent(self) -> None:
        baseline = [0.02, 0.03, 0.02, 0.01, 0.02, 0.02]
        normal = evaluate_control_band("ci_test_failure_rate", baseline, 0.02)
        self.assertFalse(normal.breached)

        breach = evaluate_control_band("ci_test_failure_rate", baseline, 0.12)
        self.assertTrue(breach.breached)
        self.assertEqual(breach.tier, "3sigma")
        self.assertEqual(breach.action, "propose")

        draft = draft_incident_intent(breach, "INT-901", "claims-api", "Spike after nightly build.")
        self.assertIn("intent_id: INT-901", draft)
        self.assertIn("## Gate 1 Approval", draft)

    def test_service_facade_end_to_end_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svc = OrchestratorService(ROOT, telemetry_log=Path(tmp) / "svc.jsonl")
            res = svc.start_run("test_or_docs_only", "Update README examples", risk_tier="low", auto_approve_gates=True)
            self.assertEqual(res["status"], "completed")
            self.assertEqual(res["stages_completed"], ["author_tests_or_docs", "lightweight_review"])


class TestCliHarnessExecutorCrossPlatform(unittest.TestCase):
    def test_prompt_sent_via_stdin_with_unicode(self) -> None:
        script = "import sys; d = sys.stdin.buffer.read().decode('utf-8'); print(len(d)); sys.exit(0 if 'ทดสอบ' in d else 3)"
        executor = CliHarnessExecutor([sys.executable, "-c", script])
        plan = classify_and_route(WorkType.TEST_OR_DOCS_ONLY, RiskTier.LOW, "docs")
        state = PipelineState(run_id="RUN-x", workspace_root=str(ROOT), task_summary="t", route_plan=plan)
        prompt = "ทดสอบ " + "x" * 40000  # longer than the Windows command-line limit
        res = executor.execute("qa-function-agent", prompt, state)
        self.assertTrue(res.success, res.output)
        self.assertEqual(res.output, str(len(prompt)))

    def test_invalid_prompt_mode(self) -> None:
        with self.assertRaises(ValueError):
            CliHarnessExecutor(["x"], prompt_mode="file")


if __name__ == "__main__":
    unittest.main()
