# Artifact Contracts, Placement & Traceability Standard

This directory defines the machine-readable contracts between SDLC stages and where every artifact must live.

## Canonical Artifact Placement

| Artifact Category | Canonical Path | Git Tracked | Rules |
| :--- | :--- | :---: | :--- |
| **Work-Item Artifacts** (`intent.md`, `spec.md`, `test-report.md`, `plan.md`, `tasks.json`, `REVIEW.md`, `trace-summary.md`, `change-digest.md`) | `work/<INT-xxx>/` + registered in `work/index.yaml` | Yes | Never place `intent.md`, `spec.md`, `tasks.json`, or `REVIEW.md` at the repo root |
| **Framework / Multi-WS Plans & Reviews** | `docs/plans/plan-<NNN>-<slug>.md` | Yes | For framework changes without an `INT-xxx` work item (never at repo root). `<NNN>` is the next unused plan number. Naming applies to **new** files; earlier files (`PLAN-006-REVIEW-ROUND-*`, `trace-versioning-plan.md`, etc.) are grandfathered and not renamed so existing links and PR history stay valid |
| **Session Handoffs & Pre-PR Digests** | `docs/handoff/YYYY-MM-DD-<slug>.md` | Yes | Used when handing off across sessions or when a change has no `work/<INT-xxx>/` dir |
| **Runtime State & Traces** (`runs/`, `traces/`, `telemetry/`, `state/`) | `.sdlc/` | **No (gitignored)** | Never commit raw `.sdlc/` files; export summaries to `work/<INT-xxx>/trace-summary.md` |

## End-to-End Traceability Chain

```text
URD-xxx / INT-xxx (Intent & Business Rules)
   └──► FS-xxx / SCR-xxx (Functional Spec & IPO Matrix)
           ├──► TC-{HC|NEG|BVA|EP|API|PERF|SEC}-xxx / EXP-xxx / R-xxx (QA Test Cases)
           └──► TASK-xxx (Implementation Tasks in tasks.json)
                   └──► PR-xxx / REV-xxx (Review & Security Gate)
```

## Contract Inventory

| Stage | Artifact | Schema Contract | Template |
| :--- | :--- | :--- | :--- |
| **1. Plan (PO/BA)** | `work/<INT-xxx>/intent.md` | [intent.schema.yaml](intent.schema.yaml) | [intent.template.md](../templates/intent.template.md) |
| **2. Design (SA)** | `work/<INT-xxx>/spec.md` | [spec-ipo.schema.yaml](spec-ipo.schema.yaml) | [spec.template.md](../templates/spec.template.md) |
| **3. TDD / QA** | `work/<INT-xxx>/test-report.md` | [test-report.schema.json](test-report.schema.json) | [function-test-report.template.md](../templates/function-test-report.template.md) |
| **4. Build (Dev)** | `work/<INT-xxx>/plan.md` / `tasks.json` | [tasks.schema.json](tasks.schema.json) | [plan.template.md](../templates/plan.template.md) / [tasks.template.json](../templates/tasks.template.json) |
| **5. Review & Gate** | `work/<INT-xxx>/REVIEW.md` | [review-gate.schema.yaml](review-gate.schema.yaml) | [review.template.md](../templates/review.template.md) |
| **5b. Change Digest** *(High-Risk / Framework)* | `work/<INT-xxx>/change-digest.md` | *None (template + validator check only)* — `python3 scripts/validate_work_item.py work/<INT-xxx> --require-digest` rejects a missing, empty, or still-templated digest | [change-digest.template.md](../templates/change-digest.template.md) |
