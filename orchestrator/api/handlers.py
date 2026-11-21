"""Framework-agnostic service handlers backing both FastAPI endpoints and CLI commands."""

from __future__ import annotations

import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from orchestrator.api.auth import AuthenticatedActor, authorize_gate
from orchestrator.core.loader import FrameworkBundle, load_framework
from orchestrator.core.router import classify_and_route
from orchestrator.core.state_store import FileStateStore
from orchestrator.graphs.sdlc_pipeline import DryRunExecutor, PipelineState, SDLCPipelineRunner
from orchestrator.telemetry.bands import draft_incident_intent, evaluate_control_band, load_bands_config
from orchestrator.telemetry.tracker import TelemetryTracker


class GatePolicyError(PermissionError):
    """Raised when a caller attempts to bypass HITL gates where prohibited."""


class GateConflictError(RuntimeError):
    """Raised when expected_gate does not match the run's currently pending gate (HTTP 409)."""


class OrchestratorService:
    """Stateless service facade reading canonical definitions directly from the repository."""

    def __init__(
        self,
        repo_root: Path,
        telemetry_log: Path | None = None,
        runs_dir: Path | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.telemetry_log = telemetry_log or (repo_root / ".sdlc" / "telemetry" / "runs.jsonl")
        self.tracker = TelemetryTracker(self.telemetry_log)
        self.state_store = FileStateStore(runs_dir or (repo_root / ".sdlc" / "runs"))

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
        allow_auto_approve: bool | None = None,
    ) -> dict[str, Any]:
        can_auto = (
            allow_auto_approve
            if allow_auto_approve is not None
            else os.environ.get("SDLC_ORCHESTRATOR_ALLOW_AUTO_APPROVE") == "1"
        )
        if auto_approve_gates and not can_auto:
            raise GatePolicyError("auto_approve_gates is disabled; human approval via /approve is required")

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
        self.state_store.save(state)
        return self._serialize_state(state)

    def approve_run_gate(
        self,
        run_id: str,
        approver_id: str,
        expected_gate: str | None = None,
        actor: AuthenticatedActor | None = None,
        project_pack: str | None = None,
    ) -> dict[str, Any]:
        with self.state_store.locked(run_id):
            state = self.state_store.load(run_id)
            if not state.pending_gate:
                raise GateConflictError(f"Run '{run_id}' has no pending gate (status={state.status})")
            if expected_gate is not None and state.pending_gate != expected_gate:
                raise GateConflictError(
                    f"Gate mismatch: expected '{expected_gate}', but pending gate is '{state.pending_gate}'"
                )
            if actor is not None:
                authorize_gate(actor, state.pending_gate)
                verified_approver = actor.actor_id
            else:
                verified_approver = approver_id

            bundle = self.get_bundle(project_pack=project_pack)
            runner = SDLCPipelineRunner(bundle=bundle, executor=DryRunExecutor(), tracker=self.tracker)
            state = runner.approve_gate(state, gate_name=state.pending_gate, approver_id=verified_approver)
            self.state_store.save(state)
            return self._serialize_state(state)

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._serialize_state(self.state_store.load(run_id))

    def check_band(
        self,
        metric_name: str,
        baseline_samples: list[float],
        observed_value: float,
        affected_systems: str = "core-api",
        evidence_summary: str = "Automated threshold breach detected.",
        intent_id: str = "INT-900",
    ) -> dict[str, Any]:
        bands_path = self.repo_root / "docs" / "operating-model" / "bands.yaml"
        bands_cfg = load_bands_config(bands_path) if bands_path.exists() else None
        evaluation = evaluate_control_band(metric_name, baseline_samples, observed_value, bands_config=bands_cfg)
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
            "gate_approvals": list(state.gate_approvals),
            "current_stage_index": state.current_stage_index,
            "stages_completed": list(state.stage_outputs.keys()),
            "telemetry": asdict(summary),
        }
