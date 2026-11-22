"""FastAPI entrypoint for the stateless SDLC Orchestrator Service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from orchestrator.api.auth import (
    AuthenticatedActor,
    AuthenticationError,
    AuthorizationError,
    authenticate_bearer,
    load_token_registry,
)
from orchestrator.api.handlers import GateConflictError, GatePolicyError, OrchestratorService
from orchestrator.core.state_store import StateLockError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
service = OrchestratorService(repo_root=REPO_ROOT)

app = FastAPI(
    title="AI-Native SDLC Orchestrator",
    version="0.2.0",
    description="Stateless orchestrator loading canonical roles, skills, and routing directly from .agents/ and docs/.",
)


def require_authenticated_actor(authorization: str | None = Header(default=None)) -> AuthenticatedActor:
    try:
        registry = load_token_registry()
        return authenticate_bearer(authorization, registry)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


class RouteRequest(BaseModel):
    work_type: str
    risk_tier: str = "medium"
    summary: str = ""


class RunRequest(BaseModel):
    work_type: str
    summary: str
    risk_tier: str = "medium"
    scope: str = "default"
    project_pack: str | None = None
    auto_approve_gates: bool = False


class ApproveRequest(BaseModel):
    expected_gate: str = Field(min_length=1)
    project_pack: str | None = None


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
def start_run(
    req: RunRequest,
    actor: AuthenticatedActor = Depends(require_authenticated_actor),
) -> dict[str, Any]:
    try:
        return service.start_run(
            work_type=req.work_type,
            summary=req.summary,
            risk_tier=req.risk_tier,
            scope=req.scope,
            project_pack=req.project_pack,
            auto_approve_gates=req.auto_approve_gates,
            actor=actor,
        )
    except (GatePolicyError, AuthorizationError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except StateLockError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/runs/{run_id}")
def get_run(
    run_id: str,
    actor: AuthenticatedActor = Depends(require_authenticated_actor),
) -> dict[str, Any]:
    try:
        return service.get_run(run_id, actor=actor)
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except StateLockError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/runs/{run_id}/approve")
def approve_gate(
    run_id: str,
    req: ApproveRequest,
    actor: AuthenticatedActor = Depends(require_authenticated_actor),
) -> dict[str, Any]:
    try:
        return service.approve_run_gate(
            run_id=run_id,
            approver_id=actor.actor_id,
            expected_gate=req.expected_gate,
            actor=actor,
            project_pack=req.project_pack,
        )
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except GateConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StateLockError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
