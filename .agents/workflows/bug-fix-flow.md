# Workflow: Bug Fix Flow

> Triggered when [core-bootloader.md](../../docs/workflow/core-bootloader.md) classifies a task as `Bug Fix`.

## Stage Pipeline

1. **Triage & Scope Check** (Tier per [constitution.md §1](../../docs/operating-model/constitution.md)):
   - Low/Medium and isolated (**Standard Tier**): post a plan packet and get the **Plan Checkpoint** approval in chat, record it under `## Plan Checkpoint` in the PR/MR, then proceed to reproduction. *Residual risk:* the approver's identity in that PR field is self-reported, not machine-verified.
   - High risk / Production / Auth / Schema (**High-Risk Fast-Track**): run fast-track `sa-architect-agent` impact check (Gate 2: Fast-Track Spec) first; no Gate 1 / `intent.md`.
2. **Reproduce as Failing Test (`qa-function-agent` or `dev-coding-agent`):**
   - Write an automated failing test that reproduces the exact bug and verify it fails as expected.
   - Lock the test oracle (do not weaken assertions during Step 3).
   - High-Risk: put a table under the PR/MR `## Verification` that maps every Fast-Track Spec behaviour to a regression test. `qa-function-agent` owns it; if QA does not run, whoever writes the tests does. A behaviour without a test blocks Gate 3.
3. **Fix & Self-Verify (`dev-coding-agent`):**
   - Implement the minimal root-cause fix and run the full test + lint target.
4. **Review (`code-reviewer-agent`):**
   - Confirm regression test existed before/alongside fix, check for side effects, and generate the review record (`REVIEW.md`, or the PR/MR `## Review` for Standard work without a work item). High-Risk also runs `security-audit-agent` (required Gate 3 evidence).
5. **HITL Gate 3:** Human Maintainer reads the review record and merges PR (High-Risk also needs `change-digest.md`, checked by `validate_work_item.py --require-digest`).
6. **Prevent Recurrence:** Add a regression eval case if the bug escaped from a previous change.
