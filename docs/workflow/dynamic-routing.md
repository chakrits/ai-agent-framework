# Dynamic Work Routing

> Select the smallest safe workflow that satisfies quality and governance requirements for the classified task.

## Routing Matrix

Tier and gate definitions live in [constitution.md](../operating-model/constitution.md) (§1 Risk → Tier Mapping). Artifact paths: `work/<INT-xxx>/`, or `docs/plans/plan-<NNN>-<slug>.md` for framework changes (see [contracts/README.md](../contracts/README.md)).

| Work Type | Tier | Stage Route | Required Artifacts | Mandatory Gates |
| :--- | :--- | :--- | :--- | :--- |
| **New Feature** | High-Risk | BA/PO → SA → QA (TDD) → Dev → Reviewer + Security | `intent.md`, `spec.md`, `test-report.md`, `plan.md`, `REVIEW.md`, `change-digest.md` | Gate 1, Gate 2, Gate 3 |
| **Bug Fix (Low/Med)** | Standard | Dev (Repro + Root Cause) → QA Verify → Reviewer | Defect summary, regression test, `REVIEW.md` (lightweight) | Plan Checkpoint, Gate 3 |
| **Bug Fix (High / Prod)** | High-Risk | Ops/Dev Triage → SA Impact Check → Dev → QA → Security → Reviewer | Postmortem note, regression test, `REVIEW.md`, `change-digest.md` | Gate 2 (Fast-Track Spec), Gate 3 |
| **API / Schema Change** | High-Risk | BA/PO → SA (Contract/ADR) → QA → Dev → Security + Reviewer | `spec.md`, Contract diff, migration rollback plan, `REVIEW.md`, `change-digest.md` | Gate 1, Gate 2, Gate 3 |
| **Config / Data Change** | Standard (High if risk high → Gate 2 Change Plan) | SA/Dev Impact Check → Validation & Rollback Plan → Reviewer | Change checklist, rollback evidence, `REVIEW.md` (lightweight) | Plan Checkpoint, Gate 3 |
| **Test-Only / Docs-Only** | Standard | Specialist (QA or Docs) → Reviewer | Updated test/doc + verification output, `REVIEW.md` (lightweight) | Plan Checkpoint, Gate 3 |
| **Framework Change** | High-Risk (Framework) | Architect/Orchestrator → Contract & Parity Checks → Human Maintainer | `docs/plans/plan-<NNN>-<slug>.md` + passing CI parity/evals, `REVIEW.md`, `change-digest.md` | Gate 2 (Framework Spec), Gate 3 |

## Escalation Rules

- If a **Low** risk task touches authentication, permissions, payment/financial calculations, or shared database schemas, **immediately escalate to High Risk** and apply the High-Risk gates (Gate 1/2 as the route requires, SA/Security review).
- If requirements are ambiguous during Build, **stop coding** and route back to BA/PO or SA to update `intent.md` / `spec.md`.
