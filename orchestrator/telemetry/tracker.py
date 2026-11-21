"""Structured JSONL telemetry logger for token usage, cost, latency, and gate decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunSummary:
    """Aggregated metrics for a single SDLC pipeline run."""

    run_id: str
    events_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    total_latency_ms: float
    gates_approved: tuple[str, ...]


class TelemetryTracker:
    """Append-only JSONL telemetry writer and aggregator."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, run_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "event_type": event_type,
            **payload,
        }
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def summarize_run(self, run_id: str) -> RunSummary:
        if not self.log_path.exists():
            return RunSummary(run_id, 0, 0, 0, 0.0, 0.0, ())

        events = [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [e for e in events if e.get("run_id") == run_id]

        in_tok = sum(int(e.get("input_tokens", 0)) for e in matching)
        out_tok = sum(int(e.get("output_tokens", 0)) for e in matching)
        cost = round(sum(float(e.get("cost_usd", 0.0)) for e in matching), 6)
        latency = round(sum(float(e.get("latency_ms", 0.0)) for e in matching), 3)
        gates = tuple(
            str(e["gate"])
            for e in matching
            if e.get("event_type") in {"gate_approved", "gate_auto_approved"} and "gate" in e
        )
        return RunSummary(
            run_id=run_id,
            events_count=len(matching),
            total_input_tokens=in_tok,
            total_output_tokens=out_tok,
            total_cost_usd=cost,
            total_latency_ms=latency,
            gates_approved=gates,
        )
