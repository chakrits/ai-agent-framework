# SDLC Framework Constitution

> Non-negotiable engineering, security, and governance rules for all agents and workflows operating under this framework.

## 1. Human-in-the-Loop (HITL) Approval Gates

Agents may draft, analyze, implement, and verify, but **human sign-off is mandatory** at these gates:

| Gate | Transition | Required Evidence | Approver Role |
| :--- | :--- | :--- | :--- |
| **Gate 1: Scope & Intent** | Plan → Design | `intent.md` with clear business rules & acceptance criteria | PO / BA |
| **Gate 2: Architecture & Spec** | Design → Build/Test | `spec.md` (FS, IPO Matrix, API/DB contracts, security notes) | SA / Tech Lead |
| **Gate 3: Release & Merge** | Verify → Deploy | Passing tests, security check, `REVIEW.md`, traceability 100% | Maintainer / Tech Lead |

## 2. Bounded Autonomy & Protected Paths

- **No Self-Approval:** An agent that writes code must never approve its own PR or merge directly to `main`.
- **Test Oracle Integrity:** Coding agents (`dev-coding-agent`) must not modify or weaken QA test specifications or acceptance criteria to force a green build.
- **Constitution Protection:** Agents cannot modify `docs/operating-model/constitution.md` or `.sdlc` / CI gate scripts unless explicitly tasked with a *Framework/Process Change* workflow and reviewed by a human maintainer.

## 3. Security & Secret Hygiene

- Never hardcode API keys, tokens, passwords, or internal private endpoints in prompts, contracts, or code.
- External data / untrusted inputs must be validated at boundaries; follow OWASP Top 10 checks before Gate 3.
- Coding agents should execute inside isolated sandboxes or dedicated Git worktrees.

## 4. Evidence Over Confidence

- Never claim a task is complete based on model confidence alone.
- Completion requires deterministic evidence: passing test logs, schema validation output, and updated traceability links.
