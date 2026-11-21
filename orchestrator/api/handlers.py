"""Framework-agnostic service handlers backing both FastAPI endpoints and CLI commands."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from orchestrator.core.loader import FrameworkBundle, load_framework
from orchestrator.core.router import classify_and_route
from orchestrator.graphs.sdlc_pipeline import DryRunExecutor, PipelineState, SDLCPipelineRunner
from orchestrator.telemetry.bands import draft_incident_intent, evaluate_control_band
from orchestrator.telemetry.tracker import TelemetryTracker


class OrchestratorService:
    """Stateless service facade reading canonical definitions directly from the repository."""

    def __init__(self, repo_root: Path, telemetry_log: Path | None = None) -> None:
        self.repo_root = repo_root
        self.telemetry_log = telemetry_log or (repo_root / ".sdlc-telemetry" / "runs.jsonl")
        self.tracker = TelemetryTracker(self.telemetry_log)
        self.runs: dict[str, PipelineState] = {}

    def get_bundle(self, project_pack: str | None = None) -> FrameworkBundle:
        return load_framework(self.repo_root, project_pack=project_pack)

    def list_agents(self, project_pack: str | None = None) -> list[dict[str, Any]]:
        bundle = self.get_bundle(project_pack=project_pack)
        return [
            {
                "name": a.name,
                "role": a.role,
                "stage": a.stage,
                "skills": list(a.skills),
                "description": a.description,
            }
            for a in bundle.agents.values()
        ]

    def preview_route(self, work_type: str, risk_tier: str = "medium", summary: str = "") -> dict[str, Any]:
        plan = classify_and_route(work_type=work_type, requested_risk=risk_tier, summary=summary)
        return {
            "work_type": plan.work_type.value,
            "risk_tier": plan.risk_tier.value,
            "escalated": plan.escalated,
            "escalation_reason": plan.escalation_reason,
            "stages": [asdict(s) for s in plan.stages],
        }

    def start_run(
        self,
        work_type: str,
        summary: str,
        risk_tier: str = "medium",
        project_pack: str | None = None,
        auto_approve_gates: bool = False,
    ) -> dict[str, Any]:
        bundle = self.get_bundle(project_pack=project_pack)
        plan = classify_and_route(work_type=work_type, requested_risk=risk_tier, summary=summary)
        run_id = f"RUN-{uuid.uuid4().hex[:8]}"
        state = PipelineState(
            run_id=run_id,
            workspace_root=str(self.repo_root),
            task_summary=summary,
            route_plan=plan,
        )
        runner = SDLCPipelineRunner(bundle=bundle, executor=DryRunExecutor(), tracker=self.tracker)
        state = runner.run(state, auto_approve_gates=auto_approve_gates)
        self.runs[run_id] = state
        return self._serialize_state(state)

    def approve_run_gate(self, run_id: str, project_pack: str | None = None) -> dict[str, Any]:
        if run_id not in self.runs:
            raise KeyError(f"Run not found: {run_id}")
        state = self.runs[run_id]
        bundle = self.get_bundle(project_pack=project_pack)
        runner = SDLCPipelineRunner(bundle=bundle, executor=DryRunExecutor(), tracker=self.tracker)
        state = runner.approve_gate(state)
        return self._serialize_state(state)

    def check_band(
        self,
        metric_name: str,
        baseline_samples: list[float],
        observed_value: float,
        affected_systems: str = "core-api",
        evidence_summary: str = "Automated threshold breach detected.",
        intent_id: str = "INT-900",
    ) -> dict[str, Any]:
        evaluation = evaluate_control_band(metric_name, baseline_samples, observed_value)
        draft = None
        if evaluation.tier in {"2sigma", "3sigma"}:
            draft = draft_incident_intent(
                evaluation=evaluation,
                intent_id=intent_id,
                affected_systems=affected_systems,
                evidence_summary=evidence_summary,
            )
        return {"evaluation": asdict(evaluation), "draft_intent_md": draft}

    def _serialize_state(self, state: PipelineState) -> dict[str, Any]:
        summary = self.tracker.summarize_run(state.run_id)
        return {
            "run_id": state.run_id,
            "status": state.status,
            "pending_gate": state.pending_gate,
            "approved_gates": list(state.approved_gates),
            "current_stage_index": state.current_stage_index,
            "stages_completed": list(state.stage_outputs.keys()),
            "telemetry": asdict(summary),
        }
