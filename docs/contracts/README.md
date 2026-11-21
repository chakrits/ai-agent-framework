# Artifact Contracts & Traceability Standard

This directory defines the machine-readable contracts between SDLC stages. Every artifact produced by an agent must conform to its schema and preserve end-to-end traceability IDs.

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
| **1. Plan (PO/BA)** | `intent.md` | [intent.schema.yaml](intent.schema.yaml) | [intent.template.md](../templates/intent.template.md) |
| **2. Design (SA)** | `spec.md` | [spec-ipo.schema.yaml](spec-ipo.schema.yaml) | [spec.template.md](../templates/spec.template.md) |
| **3. TDD / QA** | `test-report.md` | [test-report.schema.json](test-report.schema.json) | [function-test-report.template.md](../templates/function-test-report.template.md) |
| **4. Build (Dev)** | `plan.md` / `tasks.json` | [tasks.schema.json](tasks.schema.json) | [plan.template.md](../templates/plan.template.md) / [tasks.template.json](../templates/tasks.template.json) |
| **5. Review & Gate** | `REVIEW.md` | [review-gate.schema.yaml](review-gate.schema.yaml) | [review.template.md](../templates/review.template.md) |
