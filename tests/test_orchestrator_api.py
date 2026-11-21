"""Tests for Orchestrator v1 auth/RBAC, locking, idempotency, unified trace, bands.yaml, and FastAPI."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import trace  # noqa: E402
from orchestrator.api.auth import (  # noqa: E402
    AuthenticatedActor,
    AuthenticationError,
    AuthorizationError,
    authenticate_bearer,
    load_token_registry,
)
from orchestrator.api.handlers import GateConflictError, GatePolicyError, OrchestratorService  # noqa: E402
from orchestrator.telemetry.bands import evaluate_control_band, load_bands_config  # noqa: E402

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None


class TestOrchestratorV1Hardening(unittest.TestCase):
    def test_auth_and_gate_rbac_enforcement(self) -> None:
        reg = load_token_registry(
            {
                "SDLC_ORCHESTRATOR_TOKENS_JSON": json.dumps(
                    {
                        "tok-po": {"actor_id": "po-alice", "roles": ["po"]},
                        "tok-sa": {"actor_id": "sa-bob", "roles": ["sa"]},
                        "tok-maint": {"actor_id": "maint-carol", "roles": ["maintainer"]},
                    }
                )
            }
        )
        with self.assertRaises(AuthenticationError):
            authenticate_bearer(None, reg)
        with self.assertRaises(AuthenticationError):
            authenticate_bearer("Bearer wrong-token", reg)

        po = authenticate_bearer("Bearer tok-po", reg)
        sa = authenticate_bearer("Bearer tok-sa", reg)
        self.assertEqual(po.actor_id, "po-alice")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            svc = OrchestratorService(ROOT, telemetry_log=tmp_dir / "r.jsonl", runs_dir=tmp_dir / "runs")
            started = svc.start_run("new_feature", "Add export")
            run_id = started["run_id"]

            # PO approves Gate 1
            res1 = svc.approve_run_gate(
                run_id, approver_id="ignored", expected_gate="Gate 1: Scope & Intent", actor=po
            )
            self.assertEqual(res1["pending_gate"], "Gate 2: Architecture & Spec")
            self.assertEqual(res1["gate_approvals"][0]["approver_id"], "po-alice")

            # Retrying Gate 1 returns GateConflictError (never approves Gate 2)
            with self.assertRaises(GateConflictError):
                svc.approve_run_gate(run_id, approver_id="ignored", expected_gate="Gate 1: Scope & Intent", actor=po)

            # PO is forbidden from approving Gate 2
            with self.assertRaises(AuthorizationError):
                svc.approve_run_gate(run_id, approver_id="ignored", expected_gate="Gate 2: Architecture & Spec", actor=po)

            # SA approves Gate 2
            res2 = svc.approve_run_gate(
                run_id, approver_id="ignored", expected_gate="Gate 2: Architecture & Spec", actor=sa
            )
            self.assertEqual(res2["pending_gate"], "Gate 3: Release & Merge")

    def test_concurrent_approvals_serialize_without_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            svc = OrchestratorService(ROOT, telemetry_log=tmp_dir / "c.jsonl", runs_dir=tmp_dir / "runs")
            started = svc.start_run("new_feature", "Concurrent test")
            run_id = started["run_id"]
            po = AuthenticatedActor("po-alice", frozenset({"po"}))

            def attempt() -> str:
                try:
                    svc.approve_run_gate(run_id, approver_id="po-alice", expected_gate="Gate 1: Scope & Intent", actor=po)
                    return "ok"
                except GateConflictError:
                    return "conflict"

            with ThreadPoolExecutor(max_workers=4) as pool:
                outcomes = list(pool.map(lambda _: attempt(), range(4)))

            self.assertEqual(outcomes.count("ok"), 1)
            self.assertEqual(outcomes.count("conflict"), 3)
            self.assertEqual(len(svc.get_run(run_id)["gate_approvals"]), 1)

    def test_auto_approve_blocked_by_default_and_state_persists_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            log_path = tmp_dir / "runs.jsonl"
            runs_dir = tmp_dir / "runs"

            svc1 = OrchestratorService(ROOT, telemetry_log=log_path, runs_dir=runs_dir)
            with self.assertRaises(GatePolicyError):
                svc1.start_run("new_feature", "Add export", auto_approve_gates=True)

            started = svc1.start_run("new_feature", "Add export")
            run_id = started["run_id"]

            # Simulate server restart
            svc2 = OrchestratorService(ROOT, telemetry_log=log_path, runs_dir=runs_dir)
            loaded = svc2.get_run(run_id)
            self.assertEqual(loaded["run_id"], run_id)

    def test_orchestrator_telemetry_matches_trace_event_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            log_path = tmp_dir / "runs.jsonl"
            svc = OrchestratorService(ROOT, telemetry_log=log_path, runs_dir=tmp_dir / "runs")
            res = svc.start_run("bug_fix", "Fix null pointer", risk_tier="low")
            svc.approve_run_gate(res["run_id"], approver_id="techlead-bob")

            lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertTrue(lines)
            for evt in lines:
                self.assertEqual(trace.validate_event(evt), [], msg=f"Invalid trace event: {evt}")
                self.assertEqual(evt["platform"], "orchestrator")

    def test_bands_py_reads_custom_thresholds_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom_yaml = Path(tmp) / "bands.yaml"
            custom_yaml.write_text(
                """version: "1.0"
metrics:
  custom_rate:
    tiers:
      1sigma:
        threshold: 0.5
        action: "log"
        mode: "none"
      2sigma:
        threshold: 1.0
        action: "diagnose"
        mode: "read_only"
      3sigma:
        threshold: 1.5
        action: "propose"
        mode: "gated_pr"
        routes: ["draft_intent"]
""",
                encoding="utf-8",
            )
            cfg = load_bands_config(custom_yaml)
            # baseline [0.0, 2.0] -> mean=1.0, stddev=1.0; observed=2.6 -> sigma=1.6 (>= 1.5 -> 3sigma!)
            ev = evaluate_control_band("custom_rate", [0.0, 2.0], 2.6, bands_config=cfg)
            self.assertEqual(ev.tier, "3sigma")
            self.assertEqual(ev.routes, ("draft_intent",))


@unittest.skipUnless(HAS_FASTAPI, "fastapi optional dependency not installed in base environment")
class TestFastAPIHttpEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        from orchestrator.api import main

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_path = Path(self.tmp.name)
        main.service = OrchestratorService(ROOT, telemetry_log=tmp_path / "api.jsonl", runs_dir=tmp_path / "runs")
        os.environ["SDLC_ORCHESTRATOR_TOKENS_JSON"] = json.dumps(
            {
                "tok-po": {"actor_id": "po-alice", "roles": ["po"]},
                "tok-maint": {"actor_id": "maint-carol", "roles": ["maintainer"]},
            }
        )
        self.client = TestClient(main.app)

    def test_endpoints_auth_rbac_and_lifecycle(self) -> None:
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(self.client.post("/runs", json={"work_type": "bug_fix", "summary": "x"}).status_code, 401)

        po_hdr = {"Authorization": "Bearer tok-po"}
        maint_hdr = {"Authorization": "Bearer tok-maint"}

        started = self.client.post(
            "/runs", json={"work_type": "test_or_docs_only", "summary": "Update docs"}, headers=po_hdr
        ).json()
        run_id = started["run_id"]

        # PO cannot approve Gate 3 -> 403
        forbidden = self.client.post(
            f"/runs/{run_id}/approve", json={"expected_gate": "Gate 3: Release & Merge"}, headers=po_hdr
        )
        self.assertEqual(forbidden.status_code, 403)

        # Maintainer approves Gate 3 -> 200 completed
        ok = self.client.post(
            f"/runs/{run_id}/approve", json={"expected_gate": "Gate 3: Release & Merge"}, headers=maint_hdr
        )
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["status"], "completed")

        # Duplicate retry -> 409 Conflict
        dup = self.client.post(
            f"/runs/{run_id}/approve", json={"expected_gate": "Gate 3: Release & Merge"}, headers=maint_hdr
        )
        self.assertEqual(dup.status_code, 409)


if __name__ == "__main__":
    unittest.main()
