"""State-graph SDLC pipeline supporting sequential, parallel, retry loops, and HITL gates."""

from __future__ import annotations

import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from orchestrator.core.loader import FrameworkBundle, assemble_agent_prompt
from orchestrator.core.router import RoutePlan, RouteStage
from orchestrator.telemetry.tracker import TelemetryTracker


@dataclass
class AgentExecutionResult:
    """Result returned by an AgentExecutor after running a single canonical agent."""

    agent_name: str
    success: bool
    output: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class AgentExecutor(Protocol):
    """Protocol implemented by dry-run, CLI-harness, or LLM SDK executors."""

    def execute(self, agent_name: str, assembled_prompt: str, state: "PipelineState") -> AgentExecutionResult: ...


class DryRunExecutor:
    """Deterministic executor for planning, routing verification, and CI smoke tests."""

    def execute(self, agent_name: str, assembled_prompt: str, state: "PipelineState") -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=agent_name,
            success=True,
            output=f"[dry-run] {agent_name} ready (prompt_chars={len(assembled_prompt)})",
            input_tokens=max(1, len(assembled_prompt) // 4),
            output_tokens=64,
            cost_usd=0.0,
            latency_ms=1.0,
        )


class CliHarnessExecutor:
    """Invoke an external non-interactive CLI harness (e.g., `claude -p` or `codex exec -`).

    Cross-platform: the executable is resolved with shutil.which so Windows `.cmd`/`.exe` shims (npm installs)
    are found, and the prompt is sent on stdin (UTF-8) by default because Windows limits a command line to
    roughly 32K characters. Use prompt_mode="argv" only for harnesses that cannot read stdin.
    """

    def __init__(self, command_prefix: list[str], timeout_seconds: int = 300, prompt_mode: str = "stdin") -> None:
        if prompt_mode not in {"stdin", "argv"}:
            raise ValueError("prompt_mode must be 'stdin' or 'argv'")
        self.command_prefix = command_prefix
        self.timeout_seconds = timeout_seconds
        self.prompt_mode = prompt_mode

    def _resolved_command(self, prompt: str) -> list[str]:
        exe = shutil.which(self.command_prefix[0]) or self.command_prefix[0]
        cmd = [exe, *self.command_prefix[1:]]
        return [*cmd, prompt] if self.prompt_mode == "argv" else cmd

    def execute(self, agent_name: str, assembled_prompt: str, state: "PipelineState") -> AgentExecutionResult:
        start = time.monotonic()
        proc = subprocess.run(
            self._resolved_command(assembled_prompt),
            input=assembled_prompt if self.prompt_mode == "stdin" else None,
            cwd=str(state.workspace_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )
        elapsed_ms = (time.monotonic() - start) * 1000.0
        output = proc.stdout if proc.returncode == 0 else f"{proc.stdout}\n{proc.stderr}".strip()
        return AgentExecutionResult(
            agent_name=agent_name,
            success=proc.returncode == 0,
            output=output.strip(),
            latency_ms=elapsed_ms,
        )


@dataclass
class PipelineState:
    """Mutable state carried across SDLC state-graph nodes."""

    run_id: str
    workspace_root: str
    task_summary: str
    route_plan: RoutePlan
    scope: str = "default"
    owner_actor_id: str = ""
    current_stage_index: int = 0
    status: str = "running"  # running | waiting_human_gate | completed | failed
    pending_gate: str | None = None
    approved_gates: list[str] = field(default_factory=list)
    gate_approvals: list[dict[str, str]] = field(default_factory=list)
    stage_outputs: dict[str, list[AgentExecutionResult]] = field(default_factory=dict)
    attempts: dict[str, int] = field(default_factory=dict)
    error: str | None = None


class SDLCPipelineRunner:
    """Executes a RoutePlan over a FrameworkBundle with HITL gates, parallel stages, and retries."""

    def __init__(
        self,
        bundle: FrameworkBundle,
        executor: AgentExecutor | None = None,
        tracker: TelemetryTracker | None = None,
        max_retries: int = 2,
    ) -> None:
        self.bundle = bundle
        self.executor = executor or DryRunExecutor()
        self.tracker = tracker
        self.max_retries = max_retries

    def run(self, state: PipelineState, auto_approve_gates: bool = False) -> PipelineState:
        """Execute stages starting from state.current_stage_index until done, failed, or HITL gate."""
        state.status = "running"
        state.pending_gate = None

        while state.current_stage_index < len(state.route_plan.stages):
            stage = state.route_plan.stages[state.current_stage_index]
            results = self._execute_stage_with_retry(stage, state)
            state.stage_outputs[stage.stage_id] = results

            if any(not r.success for r in results):
                state.status = "failed"
                state.error = f"Stage '{stage.stage_id}' failed after {state.attempts.get(stage.stage_id, 1)} attempt(s)"
                self._record_event(state.run_id, "stage_failed", {"stage": stage.stage_id, "error": state.error})
                return state

            state.current_stage_index += 1

            if stage.human_gate_after and stage.human_gate_after not in state.approved_gates:
                if auto_approve_gates:
                    state.approved_gates.append(stage.human_gate_after)
                    self._record_event(state.run_id, "gate_auto_approved", {"gate": stage.human_gate_after})
                else:
                    state.status = "waiting_human_gate"
                    state.pending_gate = stage.human_gate_after
                    self._record_event(state.run_id, "gate_paused", {"gate": stage.human_gate_after})
                    return state

        state.status = "completed"
        self._record_event(state.run_id, "pipeline_completed", {"stages_executed": len(state.stage_outputs)})
        return state

    def approve_gate(
        self,
        state: PipelineState,
        gate_name: str | None = None,
        approver_id: str = "human-cli",
    ) -> PipelineState:
        """Record human gate approval with approver identity and resume pipeline execution."""
        target_gate = gate_name or state.pending_gate
        if not target_gate:
            raise ValueError("No pending gate to approve")
        actor = approver_id.strip()
        if not actor:
            raise ValueError("approver_id must be a non-empty human identifier")
        if target_gate not in state.approved_gates:
            state.approved_gates.append(target_gate)
            state.gate_approvals.append(
                {
                    "gate": target_gate,
                    "approver_id": actor,
                    "approved_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds"),
                }
            )
        self._record_event(state.run_id, "gate_approved", {"gate": target_gate, "approver_id": actor})
        return self.run(state, auto_approve_gates=False)

    def _execute_stage_with_retry(self, stage: RouteStage, state: PipelineState) -> list[AgentExecutionResult]:
        max_attempts = 1 + self.max_retries if stage.retry_on_fail else 1
        results: list[AgentExecutionResult] = []
        for attempt in range(1, max_attempts + 1):
            state.attempts[stage.stage_id] = attempt
            results = self._execute_stage_once(stage, state)
            if all(r.success for r in results):
                break
        return results

    def _execute_stage_once(self, stage: RouteStage, state: PipelineState) -> list[AgentExecutionResult]:
        context = self._build_stage_context(stage, state)

        def run_one(agent_name: str) -> AgentExecutionResult:
            prompt = assemble_agent_prompt(self.bundle, agent_name, context)
            res = self.executor.execute(agent_name, prompt, state)
            self._record_event(
                state.run_id,
                "agent_executed",
                {
                    "stage": stage.stage_id,
                    "agent": agent_name,
                    "success": res.success,
                    "input_tokens": res.input_tokens,
                    "output_tokens": res.output_tokens,
                    "cost_usd": res.cost_usd,
                    "latency_ms": res.latency_ms,
                },
            )
            return res

        if stage.parallel and len(stage.agents) > 1:
            with ThreadPoolExecutor(max_workers=len(stage.agents)) as pool:
                return list(pool.map(run_one, stage.agents))
        return [run_one(name) for name in stage.agents]

    def _build_stage_context(self, stage: RouteStage, state: PipelineState) -> str:
        prior = "\n".join(
            f"- {sid}: {len(res)} result(s), success={all(r.success for r in res)}"
            for sid, res in state.stage_outputs.items()
        )
        return (
            f"Run ID: {state.run_id}\n"
            f"Work Type: {state.route_plan.work_type.value}\n"
            f"Risk Tier: {state.route_plan.risk_tier.value}\n"
            f"Stage: {stage.stage_id}\n"
            f"Task Summary: {state.task_summary}\n"
            f"Prior Stages:\n{prior or '- none'}"
        )

    def _record_event(self, run_id: str, event_type: str, payload: dict) -> None:
        if self.tracker is not None:
            self.tracker.record(run_id, event_type, payload)
