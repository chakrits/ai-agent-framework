"""FastAPI entrypoint for the stateless SDLC Orchestrator Service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator.api.handlers import OrchestratorService

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
service = OrchestratorService(repo_root=REPO_ROOT)

app = FastAPI(
    title="AI-Native SDLC Orchestrator",
    version="0.1.0",
    description="Stateless orchestrator loading canonical roles, skills, and routing directly from .agents/ and docs/.",
)


class RouteRequest(BaseModel):
    work_type: str
    risk_tier: str = "medium"
    summary: str = ""


class RunRequest(BaseModel):
    work_type: str
    summary: str
    risk_tier: str = "medium"
    project_pack: str | None = None
    auto_approve_gates: bool = False


class BandCheckRequest(BaseModel):
    metric_name: str
    baseline_samples: list[float] = Field(min_length=2)
    observed_value: float
    affected_systems: str = "core-api"
    evidence_summary: str = "Automated threshold breach detected."
    intent_id: str = "INT-900"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agents")
def list_agents(project_pack: str | None = None) -> list[dict[str, Any]]:
    try:
        return service.list_agents(project_pack=project_pack)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/route")
def preview_route(req: RouteRequest) -> dict[str, Any]:
    try:
        return service.preview_route(req.work_type, req.risk_tier, req.summary)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/runs")
def start_run(req: RunRequest) -> dict[str, Any]:
    try:
        return service.start_run(
            work_type=req.work_type,
            summary=req.summary,
            risk_tier=req.risk_tier,
            project_pack=req.project_pack,
            auto_approve_gates=req.auto_approve_gates,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/runs/{run_id}/approve")
def approve_gate(run_id: str, project_pack: str | None = None) -> dict[str, Any]:
    try:
        return service.approve_run_gate(run_id=run_id, project_pack=project_pack)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/telemetry/check-band")
def check_band(req: BandCheckRequest) -> dict[str, Any]:
    return service.check_band(
        metric_name=req.metric_name,
        baseline_samples=req.baseline_samples,
        observed_value=req.observed_value,
        affected_systems=req.affected_systems,
        evidence_summary=req.evidence_summary,
        intent_id=req.intent_id,
    )
