# Workflow: New Feature Flow

> Triggered when [core-bootloader.md](../../docs/workflow/core-bootloader.md) classifies a task as `New Feature` or `API / Schema Change`.

## Stage Pipeline & Artifacts

1. **Plan (`ba-po-agent`)** → Output: `intent.md` (`INT-xxx`, `URD-xxx`, `BR-xxx`)
2. **HITL Gate 1:** PO/BA reviews and approves `intent.md`
3. **Design (`sa-architect-agent`)** → Output: `spec.md` (`SPEC-xxx`, `FS-xxx`, IPO Matrix, API/Data Contract, Rollback)
4. **HITL Gate 2:** SA/Tech Lead reviews `spec.md` and flagged concerns
5. **TDD Design (`qa-function-agent`)** → Output: `test-report.md` (`QAR-xxx` with 13 sections & 100% traceability)
6. **Build (`dev-coding-agent`)** → Output: `plan.md` + `tasks.json` + code + passing tests (`passes: true`)
7. **Review & Security (`code-reviewer-agent` + `security-audit-agent` in parallel)** → Output: `REVIEW.md` (`REV-xxx`)
8. **HITL Gate 3:** Human Maintainer approves PR merge & release
