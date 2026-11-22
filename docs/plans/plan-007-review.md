---
review_id: REV-PLAN-007
pr_ref: uncommitted working tree on main (no PR yet)
spec_ref: PLAN-007
verdict: approved
---

# Code & Security Review Report

## Review Scope & Traceability Check
- **Intent / Spec:** N/A (Framework Change) / `docs/plans/plan-007-governance-consistency.md` (Gate 2 Framework Spec, decisions D1-D4 treated as final)
- **Tasks Completed (per diff):** A1-A5, B1-B3, C1-C2, D1-D6, E1-E6, F1. F2 is this review. F3 (staged-file list for the Human) is not yet done.
- **Diff Summary:** 32 modified files, 1 deleted (root `plan.md`), 11 untracked paths. Docs and templates (constitution, routing, bootloader, AGENTS.md, contracts README, PR/MR templates), 5 agent files plus the new `council-pressure-test` skill (mirrored), `scripts/validate_work_item.py` (`--require-digest`), `scripts/validate-context-budget.py`, 6 new tests, `work/index.yaml`, and the INT-001 digest backfill.
- **Review order:** the raw diff was reviewed first. The PLAN-007 digest was read last and checked against the diff (see "Digest Claim Audit").
- **Tier:** Framework Change, High-Risk. Protected paths touched: constitution, `docs/contracts/**`, `scripts/validate-*.py`. The Human must commit with `SDLC_ALLOW_PROTECTED=1`.

## Spec Compliance & Architectural Drift
- [x] Single Gate model (Plan Checkpoint / Gate 1 / Gate 2 / Gate 3) is used in the constitution, AGENTS.md, templates and routing. `orchestrator/**` is untouched, and `router.py` / `auth.py` gate strings match the documented names.
- [x] Root `plan.md` moved to `docs/plans/plan-005-trace-v1-1.md`. The 3 inbound or internal links were updated: `governance-review.md:96`, `2026-11-21-trace-v1.1.md:4`, and the `trace-versioning-plan.md` link inside the moved file. No `DECISIONS.md` or `](plan.md)` references remain outside PLAN-007 prose.
- [x] D1 (Plan Checkpoint is PR-only), D2 (old plans not renamed, grandfathered text added), D3 (digest file only for High-Risk/Framework at the validator level) and D4 (AGENTS.md budget 500) are honored in the budget script, the validator and the contracts README.
- [ ] D3 is not honored consistently in prose (Finding I2).
- [ ] The Risk to Tier table contradicts the routing matrix and `router.py` for high-risk bug fix and config work (Finding I1).
- [ ] Phase C3 and the "tighten" commit group are not met. Budgets were loosened (Finding I4).
- **Mirror parity:** `sync-adapters.py --check` passes. The `.claude/` and `.agent/` copies of the 5 agent files and the `council-pressure-test` skill are byte-identical to `.agents/`. `.codex/README.md` changed only by the generated skill line. I found no hand edits under `.claude/` or `.agent/`.
- **Done beyond the plan:** `council-pressure-test` agent/skill wiring (`ba-po`, `sa-architect`, `code-reviewer` front-matter and prose) and the `work/<INT-xxx>/` path prefixes in all agent files. These belong to the pre-existing uncommitted change and are not listed in the plan's "Files to Modify". This is low risk, but the PLAN-007 file list under-describes the diff.

## Verification Evidence (Tests & Linters)
- **Commands Executed (SDLC_TRACE_LEVEL=off, run by me in this review):**
  - `python3 scripts/sync-adapters.py --check` -> PASSED
  - `python3 scripts/validate-context-budget.py` -> PASSED
  - `python3 scripts/validate-contracts.py --check-defaults` -> PASSED
  - `python3 evals/run_evals.py --mode contract` -> PASSED (10/10)
  - `python3 scripts/validate_work_item.py work/INT-001 --require-review --require-digest` -> PASSED
  - `python3 -m unittest discover -s tests` -> 242 tests OK (skipped=3). This is +6 over the 236 baseline, which matches the 6 new tests.
  - `git diff --check` -> clean
- **Not verified:** Windows, Docker, and real GitHub/GitLab CI. The grep checks listed in plan section 4 were run in a broader form and found nothing stale.
- **Ad-hoc probes of `check_change_digest` (my own):**
  - The PLAN-007 handoff digest passes.
  - The raw template fails (6 placeholders reported).
  - A template with only the date and `path/to/file` replaced still fails.
  - `"# x\nok"` PASSES (false negative).
  - A digest that quotes the string `YYYY-MM-DD HH:mm:ss` in prose FAILS (false positive).
  - The alternative `[คำสั่งสั้น` in `DIGEST_PLACEHOLDER_RE` matches nothing in the template (dead pattern).

## Test Oracle Integrity Check
- [x] No existing test was changed. The diff to `tests/test_work_item_validator.py` is purely additive (+82 lines), and orchestrator, router and auth tests are untouched.
- [x] The 6 new tests prove presence, the opt-in flag, empty content and the unfilled template. They also check CLI exit codes and that the real INT-001 digest is valid.
- [ ] They do NOT prove placeholder coverage (only the whole template is tested), partial fills, false positives, or minimum content (Nit N1, Finding I3).

## Security & OWASP Findings
- [x] AuthN/AuthZ: no change to `orchestrator/api/auth.py`. The role map still matches the documented gates, and Plan Checkpoint has no RBAC (accepted under D1).
- [x] Input validation: `--require-digest` reads a file at a fixed name `change-digest.md` inside the given work dir. There is no path injection. `read_text(encoding="utf-8")` can raise on a non-UTF-8 file (traceback instead of a clean error), which is low severity.
- [x] No secrets, PII, or raw `.sdlc/traces` in the diff.
- Governance-security note: Plan Checkpoint is an unauthenticated, self-attested PR field (see Finding I3 and Nit N4). It is accepted under D1 but should be stated as a residual risk.

## Findings Summary (Blocker / Major / Minor)
Blockers: none. Important findings: 4 (all must be fixed or explicitly waived by the Human before Gate 3).

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Important** I1 | `docs/operating-model/constitution.md` Risk to Tier table, row 2 (`risk_tier: high` -> Gate 1 -> Gate 2 -> Gate 3); `AGENTS.md:56`; vs `docs/workflow/dynamic-routing.md:13,15` and `orchestrator/core/router.py:121-123,135` | The "single source" table says every `risk_tier: high` task takes Gate 1, then 2, then 3. Routing and the router give a high-risk bug fix only "Gate 2 (Fast-Track Spec), Gate 3" and a high-risk config change only "Gate 2: Change Plan". Neither has a Gate 1 stage. Failure scenario: a production hotfix is classed `bug_fix` / `high`. An agent that follows constitution and AGENTS.md demands an approved `intent.md` (Gate 1) before the fix. The orchestrator never creates that gate, so the run stalls or the agent invents an out-of-band approval. An agent that follows routing skips Gate 1 and violates the "single source". Because `router.py` is out of scope (D1), the docs must give way. | Make row 2 `new_feature` / `api_schema_change` -> Gate 1, 2, 3, and add a row for `bug_fix` / `config_data_change` at high risk -> Gate 2 variant (Fast-Track Spec or Change Plan), then Gate 3. Fix the AGENTS.md:56 wording to match ("High-Risk Tier" gates vary by Work Type; link to the table). |
| **Important** I2 | `.agents/agents/dev-coding-agent.md:19` (and the `.claude/` and `.agent/` mirrors); `docs/templates/change-digest.template.md:3`; `AGENTS.md` Baseline DoD ("meaningful PRs include an up-to-date `change-digest.md` before PR creation") | D3 says the digest FILE is required only for High-Risk/Framework, and Standard uses a short PR-description ELI10. Three places still require the file unconditionally or for "Feature/Behavior" changes. Failure scenario: a Standard bug fix. `dev-coding-agent` lists `work/<INT-xxx>/change-digest.md` as an unconditional output, so it writes one. Standard bug-fix work items often have no `work/` dir at all, and the baseline DoD blocks "Ready for Human Gate" without a file the policy says is optional. Different agents give different answers for the same task. | Scope all three statements to "High-Risk / Framework: file; Standard: PR-description ELI10". Change the template header to say the same. Run `sync-adapters.py --sync` after editing `.agents/`. |
| **Important** I3 | `scripts/validate_work_item.py:159-171` (`DIGEST_PLACEHOLDER_RE`, `check_change_digest`); `AGENTS.md` section 4 ELI10 rule ("it is checked by `--require-digest`"); Extended DoD; `.github/pull_request_template.md:18` | The new rule is claimed as enforced but is only weakly enforced. (a) The validator only runs on `work/<INT-xxx>` dirs. Framework Changes have no work item (the plan itself, and `docs/handoff/...-digest.md`), so the main case the rule names ("Framework Tier") can never be checked by `--require-digest`. (b) No CI job, hook, or script calls `validate_work_item.py` (grep over `.github`, `.gitlab-ci.yml`, `scripts/` finds only the PR checklist text). Enforcement relies on a checkbox. (c) The content check is placeholder-only: a one-line digest `"# x\nok"` passes, and unfilled sections that do not use the exact bracket tokens pass. `[คำสั่งสั้น` is a dead alternative (it does not occur in the template). (d) A digest that quotes `YYYY-MM-DD HH:mm:ss` or `path/to/file` in prose is rejected. Failure scenario: a High-Risk change adds `work/INT-002/change-digest.md` containing only a title and "done". `--require-digest` passes, the PR checkbox is ticked, and the Human receives no real walkthrough. For a Framework Change under `docs/handoff/` nothing is validated at all. | Either (1) add a minimum-structure check (the five numbered section headings from the template, plus a non-empty body each), and a `--digest-file PATH` option (or validate `docs/handoff/*-digest.md` / a plan-referenced path) so Framework Changes are covered; or (2) downgrade the AGENTS.md wording to "template-guided, human-checked". Add a CI step or document that enforcement is manual. Remove the dead alternative and anchor the regex on section content. |
| **Important** I4 | `scripts/validate-context-budget.py:12-16`; `docs/plans/plan-007...md` section 3 commit 4 ("tighten context budgets") and section 6 ("never expand a budget"); digest section 2 ("ลด budget") | Versus HEAD, `agents/*.md` went 120 -> 150, `skills/*/SKILL.md` 150 -> 200 and `workflows/*.md` 120 -> 150. Only AGENTS.md was raised intentionally (D4). The largest actual files are 35 lines (agents) and 32 lines (skills), so the headroom has no consumer. This LOOSENS a CI gate while the plan and the digest say "tighten / reduce". Failure scenario: a later change bloats a skill to 190 lines (and an agent file to 140). CI passes where it used to fail, and the context-budget guard no longer protects the progressive-disclosure goal. The plan's Phase C3 text is itself self-contradictory (it lists the new loosened numbers as "change to"), but the implementer followed it literally. | Restore `agents` 120, `skills` 150 and `workflows` 120 (all current files pass), keep `AGENTS.md: 500` per D4, and fix plan C3 and the commit-4 title. Correct the digest claim. If a loosening is truly intended, record that as a Human decision. |

### Nits (5 shown, 4 more omitted)
| # | Location | Nit |
| :--- | :--- | :--- |
| N1 | `tests/test_work_item_validator.py` (`TestChangeDigestRequirement`) | Add parametrized tests for each placeholder token, a partially filled template, a digest that legitimately quotes a token (documents the false-positive decision), and a minimal-content digest. Currently only the whole template is exercised. |
| N2 | `docs/plans/plan-007-governance-consistency.md:6` | `status: draft_pending_gate_2` while the digest says D1-D4 and the plan were approved in chat on 2026-11-22. Record the Gate 2 approval (who and when) in the plan itself, per the new Plan Checkpoint auditability principle. |
| N3 | `work/INT-001/spec.md:28` | The CLI line lists only `[--require-review]`. The digest already admits this. Either bump the spec through its normal path or add the flag via an addendum. |
| N4 | `.agents/workflows/bug-fix-flow.md`, `new-feature-flow.md` | The workflows have no Plan Checkpoint step for Standard work and do not mention the Tier. Acceptable under D1, but add one line so the playbooks match the constitution. Also note, as a documented residual risk, that Plan Checkpoint approver identity is not machine-verified. |
| N5 | `docs/adr/README.md` | The ADR index is a placeholder row. The "Lifecycle" says `accepted` requires Gate 2 approval, but the template and README give no place to record the approver. |

- **Additional nits omitted (count):** 4 (wording and formatting in AGENTS.md section 3 and the PR/MR template notes; the plan file list not mentioning the council wiring; the `read_text` non-UTF-8 traceback; inconsistent `Fast-Track Spec` vs `Fast-track` capitalization).

## Digest Claim Audit (done last)
Source: `docs/handoff/2026-11-22-governance-consistency-digest.md`.
- **Unsupported:** "ลด budget (AGENTS.md คง 500 ตาม D4)" (Phase C row). The diff raises three of the four non-AGENTS budgets (Finding I4).
- **Unsupported / unverifiable from the diff:** "เขียนเทสต์ก่อน" (tests written first). The diff cannot show ordering. The count of 6 tests is correct.
- **Overstated:** "ให้กฎ digest มีตัวบังคับ" and "ปฏิเสธ digest ที่ไม่มี ว่าง หรือยังเป็น template" are true only for `work/<INT-xxx>` dirs and for the exact placeholder tokens (Finding I3).
- **Overstated:** "ให้ routing ตรงกับ `router.py`" does not hold for high-risk bug fix and config rows (Finding I1).
- **Stale timing:** "Checks Executed (หลังแก้ครั้งล่าสุดของ Phase E)" is plausible and my re-run agrees (all green), but I did not see the original run.
- **Supported:** the 3 link fixes, the root `plan.md` move, `work/index.yaml` `change_digest`, the INT-001 backfill, the mirror claims, and the "not verified: Windows/Docker/CI" disclosure.
- **Supported and honest:** the INT-001 spec CLI-line caveat.

## Council Pressure-Test *(risk_tier: high, Framework Change)*
- **Lenses Used:** Contrarian, Outsider, Executor.
- **Preserved Dissent (Contrarian):** "The change adds more rules than enforcement. Plan Checkpoint is a PR text field, the digest rule is checked by nothing in CI, and the Tier table contradicts the router it claims to mirror. A fourth consistent-looking document set can hide that the system still runs on honor."
- **Outsider:** a new contributor reading `AGENTS.md` -> constitution -> `dynamic-routing.md` will meet two different answers for a high-risk bug fix (I1) and two for when a digest is needed (I2).
- **Blind-Spot Check (what did all passes miss?):** wiring `validate_work_item.py --require-digest` into CI or a hook was never planned, and neither was a validator for Framework Changes without a work item. The plan treated "has a flag" as "is enforced".
- **Verdict & One Next Step:** `changes_requested`. Fix I1 and I2 (docs-only), restore the three budgets (I4), then either extend the validator for the no-work-item case or soften the AGENTS.md wording (I3). Re-run the 7 verification commands after the final edit.

## Re-review (Round 2)
Raw diff reviewed first; the handoff digest and the Author Response were read afterwards and treated as claims. Verdict for this round: **approved** (no Blocker, no Important). The Gate 3 Human Sign-Off below is still `Pending`. The round-1 content above is unchanged and records the earlier `changes_requested` verdict.

### Status of round-1 Important findings
| ID | Status | Evidence (from the diff) |
| :--- | :--- | :--- |
| I1 | **Fixed** | `constitution.md` Risk to Tier table now has separate rows: `new_feature` / `api_schema_change` -> Gate 1, 2, 3; `risk_tier: high` bug fix or config/data -> Gate 2 (Fast-Track Spec / Change Plan) then Gate 3; framework -> Gate 2 then Gate 3. This matches `router.py:121-123,135` and `dynamic-routing.md:13,15`. `AGENTS.md` section 3 High-Risk line now says Framework and high-risk bug fix / config skip Gate 1. |
| I2 | **Fixed** | `dev-coding-agent.md:19` (`.agents`; `.claude` and `.agent` mirrors pass parity) scopes the digest file to High-Risk / Framework, with a Standard PR/MR ELI10 alternative. The `change-digest.template.md` banner and the AGENTS.md Baseline DoD say the same. No unconditional digest requirement remains. |
| I3 | **Fixed (with accepted residual)** | `check_change_digest` requires `## 1.` to `## 5.`, anchors the date and path placeholders to the template's line shapes, and drops the dead `[คำสั่งสั้น` pattern. `--digest-file` validates standalone `docs/handoff/` digests. `work_dir` is now optional, and the CLI exits 2 when neither it nor `--digest-file` is given. The tests cover each placeholder, stubs, prose false-positive, digest-file mode (good, bad, missing, no-args exit 2), the real handoff digest and INT-001. AGENTS.md section 4 now states honestly that this is not wired into CI or hooks, so the reviewer must run it. That residual is out of scope because the CI files are protected paths. |
| I4 | **Fixed** | `validate-context-budget.py` differs from HEAD only by `AGENTS.md: 500` (D4). Agents 120, skills 150, workflows 120 and CLAUDE.md 80 are restored. |

### New observations (all Nit, none blocking)
- **R2-N1 (digest claim):** the handoff digest says "เทสต์ 15 ข้อ". The suite grew 242 -> 247 (+5 this round, 11 in the digest test class, 20 test methods in the file). The 15 figure is not supported by the diff. Correct the number or drop it.
- **R2-N2:** the section check only tests for the `## N.` headings, so a digest made of five empty headings still passes (I confirmed `[]`). Better than round 1 (a stub is now rejected), but the digest is not proven to have content. It is acceptable for a template-plus-human-review gate.
- **R2-N3:** `--require-review` and `--require-digest` are silently ignored when only `--digest-file` is given (no work dir). Harmless, but it could warn.
- **R2-N4:** the Tier table leaves unspecified a `medium` task that is NOT isolated, and a `high`-risk test/docs-only change. The "escalates to High-Risk immediately" sentence covers the first. Route both explicitly if you want the table to be exhaustive.
- **R2-N5:** the round-1 nits N2 (plan `status` still `draft_pending_gate_2`), N3 (INT-001 spec CLI line), N4 (workflows have no Plan Checkpoint step) and N5 (ADR approver slot) remain open. The Author Response lists them as intentionally open. None blocks merge.

### Digest and Author Response audit
- Supported by the diff: the I1-I4 fixes described above, the budget restoration (the digest now says "ไม่ได้ลด" and explains the earlier mistake), and the "not wired into CI/hook" disclosure.
- Unsupported: the "15 tests" count (R2-N1). Author Response "20 pass now" matches the 20 methods in the file, but that count includes pre-existing tests.
- "Tests were written first and failed before the fix" cannot be verified from a working-tree diff.

### Re-review verification (SDLC_TRACE_LEVEL=off, run by me after the fixes)
- `python3 scripts/sync-adapters.py --check` -> PASSED (parity 100%)
- `python3 scripts/validate-context-budget.py` -> PASSED
- `python3 scripts/validate-contracts.py --check-defaults` -> PASSED
- `python3 evals/run_evals.py --mode contract` -> PASSED (10/10)
- `python3 scripts/validate_work_item.py work/INT-001 --require-review --require-digest` -> PASSED
- `python3 scripts/validate_work_item.py --digest-file docs/handoff/2026-11-22-governance-consistency-digest.md` -> PASSED
- `python3 scripts/validate_work_item.py --require-digest` (no target) -> exit 2 with a usage error, as designed
- `python3 -m unittest discover -s tests` -> 247 tests OK (skipped=3)
- `git diff --check` -> clean
- Not verified: Windows, Docker, real CI.

Remaining before Gate 3: fix R2-N1 (optional), then the Human reviews the staged-file list (plan F3) and commits protected paths with `SDLC_ALLOW_PROTECTED=1`.

## Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer / Tech Lead]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`

## Author Response (2026-11-22, implementer — not a re-review)
The verdict above stays `changes_requested` until an independent reviewer re-checks. Fixes applied after this report:
- **I1:** `constitution.md` mapping now has a separate row for `risk_tier: high` bug fix / config change (Gate 2 Fast-Track Spec / Change Plan → Gate 3, no `intent.md`), and `AGENTS.md` §3 matches. `router.py` unchanged.
- **I2:** `dev-coding-agent.md` (+ mirrors), `change-digest.template.md` banner, and the AGENTS.md Baseline DoD now require the digest *file* only for High-Risk / Framework; Standard uses a PR/MR ELI10 section.
- **I3:** `check_change_digest` now requires sections `## 1.`–`## 5.`, anchors the date/path placeholders to the template's line shapes (no false positive on prose), and drops the dead `[คำสั่งสั้น` pattern. New `--digest-file` mode validates `docs/handoff/` digests. Tests were written first (5 failed before the fix; 20 pass now). Still NOT wired into CI/hooks (protected paths, out of scope) — documented in AGENTS.md.
- **I4:** budgets restored to HEAD values (120/150/120, CLAUDE.md 80); AGENTS.md stays 500 per D4. Plan C3 and the digest were corrected.
- **Digest claims:** "ลด budget" and routing/enforcement statements corrected in the handoff digest.
- **Not addressed (nits left open):** N-level items on INT-001 spec CLI line, workflow Plan Checkpoint steps, and the ADR approver slot.
