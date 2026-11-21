# Workflow: Bug Fix Flow

> Triggered when [core-bootloader.md](../../docs/workflow/core-bootloader.md) classifies a task as `Bug Fix`.

## Stage Pipeline

1. **Triage & Scope Check:**
   - Low/Medium risk: proceed directly to reproduction.
   - High risk / Production / Auth / Schema: run fast-track `sa-architect-agent` impact check (Gate 2) first.
2. **Reproduce as Failing Test (`qa-function-agent` or `dev-coding-agent`):**
   - Write an automated failing test that reproduces the exact bug and verify it fails as expected.
   - Lock the test oracle (do not weaken assertions during Step 3).
3. **Fix & Self-Verify (`dev-coding-agent`):**
   - Implement the minimal root-cause fix and run the full test + lint target.
4. **Review (`code-reviewer-agent`):**
   - Confirm regression test existed before/alongside fix, check for side effects, and generate `REVIEW.md`.
5. **HITL Gate 3:** Human Maintainer reviews `REVIEW.md` and merges PR.
6. **Prevent Recurrence:** Add a regression eval case if the bug escaped from a previous change.
