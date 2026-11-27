## Summary & Traceability
- **Intent / Spec:** `INT-xxx` / `SPEC-xxx`
- **Work Type:** `new_feature` | `bug_fix` | `api_schema_change` | `config_data_change` | `test_or_docs_only` | `framework_change`
- **Risk Tier:** `low` | `medium` | `high`

## Plan Checkpoint *(Standard Tier only; High-Risk uses Gate 1/2 artifacts)*
- **Approved by / when:** `<name, YYYY-MM-DD>`
- **Link to approval (chat/comment):** `<url or quote>`
- **Target files:** `<paths>`
- **Test strategy:** `<failing test first / checks>`
- **Verification commands:** `<commands>`
- **Risks:** `<risks>`
- **Rollback:** `<steps>`

## Verification *(Standard Tier without a work item; also the high-risk bug fix traceability mapping)*
- **Command / observed result:** `<command>` → `<pass / fail / skip counts>`
- **Traceability (high-risk bug fix only; one line per Fast-Track Spec behaviour, a missing test blocks Gate 3):** `<behaviour>` → `<regression test>`

## Review *(Standard Tier without a work item; written by an independent reviewer)*
### Review Scope & Traceability Check
### Spec Compliance & Architectural Drift
### Verification Evidence (Tests & Linters)
### Test Oracle Integrity Check
### Security & OWASP Findings
### Findings Summary (Blocker / Major / Minor)
### Council Pressure-Test *(optional: `risk_tier: high` or Human-flagged high reversal cost)*
### Gate 3 Human Sign-Off
- **Reviewer verdict:** `approved_for_human_gate` | `changes_requested` | `blocked_security`
- Human sign-off = merge

## Gate & Verification Checklist
- [ ] `intent.md` and `spec.md` approved (if required by `dynamic-routing.md`)
- [ ] QA test oracles preserved (not weakened by implementation agent)
- [ ] Independent review recorded (`REVIEW.md` with a work item; without one, `## Review` above for Standard or `docs/plans/plan-<NNN>-review.md` for a Framework Change); lightweight for Standard Tier; `code-reviewer-agent` + `security-audit-agent` for medium/high risk
- [ ] All CI checks pass (`validate-and-eval`: ubuntu / macOS / Windows x Python 3.10 / 3.12)
- [ ] Commit messages follow Conventional Commits (release-please reads them)
- [ ] If this is a **Framework Change** (constitution, contracts, guard/hooks, CI gates): a human maintainer reviewed it and committed with `SDLC_ALLOW_PROTECTED=1`
- [ ] Agent trace summary attached for High-Risk work (`python3 scripts/sdlc_trace.py export --work-item INT-xxx --out work/INT-xxx/trace-summary.md`)
- [ ] Human-readable Change Digest (ELI10) explaining what changed, why, how it works, and proof — **High-Risk / Framework:** `work/INT-xxx/change-digest.md` (or `docs/handoff/`), checked by `python3 scripts/validate_work_item.py work/INT-xxx --require-review --require-digest`; **Standard:** a short ELI10 section in this PR description
