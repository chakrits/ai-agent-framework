## Summary & Traceability
- **Intent / Spec:** `INT-xxx` / `SPEC-xxx`
- **Work Type:** `new_feature` | `bug_fix` | `api_schema_change` | `config_data_change` | `test_or_docs_only` | `framework_change`
- **Risk Tier:** `low` | `medium` | `high`

## Gate & Verification Checklist
- [ ] `intent.md` and `spec.md` approved (if required by `dynamic-routing.md`)
- [ ] QA test oracles preserved (not weakened by implementation agent)
- [ ] `REVIEW.md` generated (`code-reviewer-agent` + `security-audit-agent` for medium/high risk)
- [ ] All CI checks pass (`sync-adapters`, `context-budget`, `contracts`, `unittest`, `evals`)
