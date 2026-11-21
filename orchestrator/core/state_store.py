"""File-backed atomic JSON persistence for PipelineState across server restarts."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from orchestrator.core.router import RiskTier, RoutePlan, RouteStage, WorkType
from orchestrator.graphs.sdlc_pipeline import AgentExecutionResult, PipelineState


class FileStateStore:
    """Persist and reload PipelineState as JSON under .sdlc/runs/<run_id>.json."""

    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, run_id: str) -> Path:
        safe = "".join(ch for ch in run_id if ch.isalnum() or ch in "-_")
        if not safe:
            raise ValueError(f"Invalid run_id: {run_id!r}")
        return self.runs_dir / f"{safe}.json"

    @contextmanager
    def locked(self, run_id: str) -> Iterator[None]:
        """Acquire an exclusive advisory lock around load -> modify -> save for run_id."""
        lock_path = self.path_for(run_id).with_suffix(".lock")
        with lock_path.open("a+b") as fh:
            locked = False
            try:
                if os.name == "nt":
                    import msvcrt

                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                locked = True
            except (OSError, ImportError):
                pass
            try:
                yield
            finally:
                if locked:
                    try:
                        if os.name == "nt":
                            import msvcrt

                            fh.seek(0)
                            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl

                            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                    except (OSError, ImportError):
                        pass

    def save(self, state: PipelineState) -> Path:
        target = self.path_for(state.run_id)
        payload = self._serialize(state)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(self.runs_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            os.replace(tmp_name, target)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
        return target

    def load(self, run_id: str) -> PipelineState:
        target = self.path_for(run_id)
        if not target.exists():
            raise KeyError(f"Run not found: {run_id}")
        data = json.loads(target.read_text(encoding="utf-8"))
        return self._deserialize(data)

    def _serialize(self, state: PipelineState) -> dict[str, Any]:
        return {
            "run_id": state.run_id,
            "workspace_root": state.workspace_root,
            "task_summary": state.task_summary,
            "route_plan": {
                "work_type": state.route_plan.work_type.value,
                "risk_tier": state.route_plan.risk_tier.value,
                "escalated": state.route_plan.escalated,
                "escalation_reason": state.route_plan.escalation_reason,
                "stages": [asdict(s) for s in state.route_plan.stages],
            },
            "current_stage_index": state.current_stage_index,
            "status": state.status,
            "pending_gate": state.pending_gate,
            "approved_gates": list(state.approved_gates),
            "gate_approvals": list(state.gate_approvals),
            "stage_outputs": {
                sid: [asdict(r) for r in results]
                for sid, results in state.stage_outputs.items()
            },
            "attempts": dict(state.attempts),
            "error": state.error,
        }

    def _deserialize(self, data: dict[str, Any]) -> PipelineState:
        rp_raw = data["route_plan"]
        stages = tuple(
            RouteStage(
                stage_id=s["stage_id"],
                agents=tuple(s["agents"]),
                parallel=bool(s.get("parallel", False)),
                retry_on_fail=bool(s.get("retry_on_fail", False)),
                human_gate_after=s.get("human_gate_after"),
            )
            for s in rp_raw["stages"]
        )
        plan = RoutePlan(
            work_type=WorkType(rp_raw["work_type"]),
            risk_tier=RiskTier(rp_raw["risk_tier"]),
            escalated=bool(rp_raw["escalated"]),
            escalation_reason=rp_raw.get("escalation_reason"),
            stages=stages,
        )
        outputs = {
            sid: [AgentExecutionResult(**item) for item in items]
            for sid, items in data.get("stage_outputs", {}).items()
        }
        return PipelineState(
            run_id=data["run_id"],
            workspace_root=data["workspace_root"],
            task_summary=data["task_summary"],
            route_plan=plan,
            current_stage_index=int(data.get("current_stage_index", 0)),
            status=str(data.get("status", "running")),
            pending_gate=data.get("pending_gate"),
            approved_gates=list(data.get("approved_gates", [])),
            gate_approvals=list(data.get("gate_approvals", [])),
            stage_outputs=outputs,
            attempts=dict(data.get("attempts", {})),
            error=data.get("error"),
        )
