#!/usr/bin/env python3
"""CLI runner for inspecting canonical agents, previewing routes, running dry-runs, and checking bands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator.api.handlers import OrchestratorService

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-Native SDLC Orchestrator CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_agents = sub.add_parser("agents", help="List canonical agents loaded from .agents/")
    p_agents.add_argument("--project-pack", default=None)

    p_route = sub.add_parser("route", help="Preview dynamic routing plan for a task")
    p_route.add_argument("--work-type", required=True)
    p_route.add_argument("--risk", default="medium")
    p_route.add_argument("--summary", default="")

    p_run = sub.add_parser("run-dry", help="Execute a dry-run SDLC pipeline")
    p_run.add_argument("--work-type", required=True)
    p_run.add_argument("--summary", required=True)
    p_run.add_argument("--risk", default="medium")
    p_run.add_argument("--project-pack", default=None)
    p_run.add_argument("--auto-approve", action="store_true")

    p_band = sub.add_parser("check-band", help="Evaluate Stage 6 deterministic control band")
    p_band.add_argument("--metric", required=True)
    p_band.add_argument("--baseline", nargs="+", type=float, required=True)
    p_band.add_argument("--observed", type=float, required=True)

    args = parser.parse_args()
    svc = OrchestratorService(repo_root=REPO_ROOT)

    if args.cmd == "agents":
        print(json.dumps(svc.list_agents(project_pack=args.project_pack), indent=2))
    elif args.cmd == "route":
        print(json.dumps(svc.preview_route(args.work_type, args.risk, args.summary), indent=2))
    elif args.cmd == "run-dry":
        print(
            json.dumps(
                svc.start_run(
                    work_type=args.work_type,
                    summary=args.summary,
                    risk_tier=args.risk,
                    project_pack=args.project_pack,
                    auto_approve_gates=args.auto_approve,
                    allow_auto_approve=args.auto_approve,
                ),
                indent=2,
            )
        )
    elif args.cmd == "check-band":
        print(json.dumps(svc.check_band(args.metric, args.baseline, args.observed), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
