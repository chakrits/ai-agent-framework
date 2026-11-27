# SDLC Framework Constitution

> Non-negotiable engineering, security, and governance rules for all agents and workflows operating under this framework.

## 1. Human-in-the-Loop (HITL) Tiered Gate Governance

Agents propose, implement, and verify; **human sign-off is mandatory** at these gates and Humans hold sole merge authority:

**Gate numbers have one fixed meaning everywhere** (constitution, routing, orchestrator RBAC, agents). A Tier does not renumber gates; it only *skips* gates it does not need.

| Gate | Transition | Required Evidence | Approver Role |
| :--- | :--- | :--- | :--- |
| **Plan Checkpoint** *(Standard Tier only, unnumbered)* | Plan → Implement | Plan packet (target files, test strategy, verification cmds, rollback) approved in chat; approval recorded under `## Plan Checkpoint` in the PR/MR description | Maintainer / Tech Lead |
| **Gate 1: Scope & Intent** | Plan → Design | `intent.md` (`URD-xxx`, business rules, measurable acceptance criteria) | PO / BA |
| **Gate 2: Architecture & Spec** *(variants: Fast-Track Spec, Change Plan, Framework Spec)* | Design → Build/Test | `spec.md` (`FS-xxx`, IPO Matrix, API/DB contracts, security notes, rollback) or `docs/plans/plan-<NNN>-<slug>.md` for framework changes | SA / Tech Lead |
| **Gate 3: Release & Merge** | Verify → Deploy | Passing tests, `REVIEW.md` (Standard work without a work item: the `## Review` section of the PR/MR description), `Related to #ID`; High-Risk also needs security audit, 100% traceability, trace summary, `change-digest.md` | Maintainer / Tech Lead |

### Risk → Tier Mapping (single source; routing and bootloader link here)

| Condition | Tier | Gates |
| :--- | :--- | :--- |
| `risk_tier` low/medium **and** isolated (no auth, permissions, payment, schema, secrets, CI gates, framework paths) | **Standard** | Plan Checkpoint → Gate 3 |
| `new_feature` or `api_schema_change` | **High-Risk** | Gate 1 → Gate 2 → Gate 3 |
| `risk_tier: high` **bug fix** or **config/data change** | **High-Risk (Fast-Track)** | Gate 2 (Fast-Track Spec / Change Plan) → Gate 3; no `intent.md` required (matches `router.py`) |
| `framework_change` | **High-Risk (Framework)** | Gate 2 (Framework Spec) → Gate 3; no `intent.md` required |
| `test_or_docs_only` at **any** `risk_tier` (no product behavior changes) | **Standard** | Plan Checkpoint → Gate 3 (gate flow matches `router.py`). At `risk_tier: high` the reviewer must run the full Bugs/Security/Compliance passes instead of a lightweight review. *This is a reviewer rule only: `router.py` always routes this work type to a single-agent `lightweight_review`, so the orchestrator does not enforce it.* Docs/tests under framework or protected paths are a `framework_change` instead |
| low/medium task that is **not** isolated (touches any excluded area above) | **High-Risk** — treated as `risk_tier: high` | Re-classify with the `risk_tier: high` row for its work type: Gate 1 → 2 → 3, or the Fast-Track / Framework row |

A Standard task that touches any excluded area **escalates to High-Risk immediately**. `orchestrator/core/router.py` (`classify_and_route`) escalates automatically in only two cases: sensitive-scope keywords in the task summary, and `api_schema_change` / `framework_change` requested at `low` risk. Every other non-isolated task must be escalated by the classifier by hand.

## 2. Bounded Autonomy & Protected Paths

- **No Self-Approval:** An agent that writes code must never approve its own PR or merge directly to `main`.
- **Test Oracle Integrity:** Coding agents (`dev-coding-agent`) must not modify or weaken QA test specifications or acceptance criteria to force a green build.
- **Constitution Protection:** Agents cannot modify the paths listed in `protected_globs` and `roles.*.ci_gate_globs` of [`scripts/sdlc_guard/policy.json`](../../scripts/sdlc_guard/policy.json) (constitution, contracts, guard and hooks, CI workflows and validators) unless explicitly tasked with a *Framework/Process Change* workflow and reviewed by a human maintainer. Committing them requires the maintainer to set `SDLC_ALLOW_PROTECTED=1`; agents must never set it.

## 3. Security & Secret Hygiene

- Never hardcode API keys, tokens, passwords, or internal private endpoints in prompts, contracts, or code.
- External data / untrusted inputs must be validated at boundaries; follow OWASP Top 10 checks before Integration/Merge Gate.
- Coding agents should execute inside isolated sandboxes or dedicated Git worktrees.

## 4. Evidence Over Confidence & Circuit Breakers

- Never claim a task is complete based on model confidence alone.
- Completion requires deterministic evidence: passing test logs, schema validation output, and updated traceability links.
- **2-Strike Rule:** Stop and escalate to the Human if a fix fails verification after two `verify -> rework` cycles.
