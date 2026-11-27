---
review_id: REV-001
pr_ref: PR-001
spec_ref: SPEC-001
verdict: pending_review
---

# Code & Security Review Report

> Standard Tier without a work item: copy the `##` headings below (as `###`) into the PR/MR `## Review` section, omit the frontmatter, and end with the verdict.

## Review Scope & Traceability Check
- **Intent / Spec:** `INT-001` / `SPEC-001`
- **Tasks Completed:** `TASK-001`
- **Diff Summary:** [Files changed and summary]

## Spec Compliance & Architectural Drift
- [ ] Implementation matches IPO Matrix and API/Data contracts in `SPEC-001`.
- [ ] No duplication or drift from repository patterns.

## Verification Evidence (Tests & Linters)
- **Command Executed:** `[exact command]`
- **Observed Result:** `[e.g., 24 passed, 0 failed, 0 skipped]`

## Test Oracle Integrity Check
- [ ] Confirmed production coding agent did NOT weaken or bypass QA test oracles.

## Security & OWASP Findings
- [ ] AuthN/AuthZ boundaries verified
- [ ] Input validation & injection checks passed
- [ ] No hardcoded secrets or PII leaks

## Findings Summary (Blocker / Major / Minor)
| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| `None` | - | No blockers found | - |

## Council Pressure-Test *(optional — `risk_tier: high` or Human-flagged high reversal cost)*
- **Lenses Used:** `[e.g., Contrarian, Outsider]`
- **Preserved Dissent:** `[the strongest unresolved objection, kept verbatim]`
- **Blind-Spot Check (what did all passes miss?):** `[...]`
- **Verdict & One Next Step:** `[...]`

## Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer / Tech Lead]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`
