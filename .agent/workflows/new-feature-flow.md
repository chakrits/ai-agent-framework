# Workflow: New Feature Flow

> Triggered when [core-bootloader.md](../../docs/workflow/core-bootloader.md) classifies a task as `New Feature` or `API / Schema Change`.

## Stage Pipeline & Artifacts

**Tier:** always **High-Risk** (Gate 1 → Gate 2 → Gate 3; no Plan Checkpoint), per [constitution.md §1](../../docs/operating-model/constitution.md). All artifacts live in `work/<INT-xxx>/`.

1. **Plan (`ba-po-agent`)** → Output: `intent.md` (`INT-xxx`, `URD-xxx`, `BR-xxx`)
2. **HITL Gate 1:** PO/BA reviews and approves `intent.md`
3. **Design (`sa-architect-agent`)** → Output: `spec.md` (`SPEC-xxx`, `FS-xxx`, IPO Matrix, API/Data Contract, Rollback)
4. **HITL Gate 2:** SA/Tech Lead reviews `spec.md` and flagged concerns
5. **TDD Design (`qa-function-agent`)** → Output: `test-report.md` (`QAR-xxx` with 13 sections & 100% traceability)
6. **Build (`dev-coding-agent`)** → Output: `plan.md` + `tasks.json` + code + passing tests (`passes: true`)
7. **Review & Security (`code-reviewer-agent` + `security-audit-agent` in parallel)** → Output: `REVIEW.md` (`REV-xxx`)
8. **Change Digest (`dev-coding-agent`)** → Output: `change-digest.md`, checked by `validate_work_item.py work/<INT-xxx> --require-review --require-digest`
9. **HITL Gate 3:** Human Maintainer approves PR merge & release
