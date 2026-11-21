# Dynamic Work Routing

> Select the smallest safe workflow that satisfies quality and governance requirements for the classified task.

## Routing Matrix

| Work Type | Stage Route | Required Artifacts | Mandatory Gates |
| :--- | :--- | :--- | :--- |
| **New Feature** | BA/PO → SA → QA (TDD) → Dev → Reviewer + Security | `intent.md`, `spec.md`, `test-report.md`, `plan.md`, `REVIEW.md` | Gate 1, Gate 2, Gate 3 |
| **Bug Fix (Low/Med)** | Dev (Repro + Root Cause) → QA Verify → Reviewer | Defect summary, regression test, `REVIEW.md` | Gate 3 |
| **Bug Fix (High / Prod)** | Ops/Dev Triage → SA Impact Check → Dev → QA → Security → Reviewer | Postmortem note, regression test, `REVIEW.md` | Gate 2 (fast-track), Gate 3 |
| **API / Schema Change** | BA/PO → SA (Contract/ADR) → QA → Dev → Security + Reviewer | `spec.md`, Contract diff, migration rollback plan, `REVIEW.md` | Gate 2, Gate 3 |
| **Config / Data Change** | SA/Dev Impact Check → Validation & Rollback Plan → Reviewer | Change checklist, rollback evidence | Gate 3 |
| **Test-Only / Docs-Only** | Specialist (QA or Docs) → Reviewer | Updated test/doc + verification output | Gate 3 (lightweight) |
| **Framework Change** | Architect/Orchestrator → Contract & Parity Checks → Human Maintainer | Updated specs + passing CI parity/evals | Gate 2, Gate 3 |

## Escalation Rules

- If a **Low** risk task touches authentication, permissions, payment/financial calculations, or shared database schemas, **immediately escalate to High Risk** and require Gate 2 (SA/Security review).
- If requirements are ambiguous during Build, **stop coding** and route back to BA/PO or SA to update `intent.md` / `spec.md`.
