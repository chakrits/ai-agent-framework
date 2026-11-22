# AGENTS.md — AI-Native SDLC Framework

> **Purpose:** Cross-harness entrypoint (Map & Gate) for Claude Code, OpenAI Codex, Antigravity (`agy`), and `orchestrator/`.
> Keep this file structured and scannable (CI budget: ≤ 500 lines; reserve headroom for evolving team rules).

---

## 1. Project Identity & Topology Mapping

| Logical Concept | Project Mapping / Convention (`ai-agent-framework`) |
| :--- | :--- |
| **Primary Stack & Runtime** | Python 3.10+ (stdlib core + optional FastAPI), POSIX/PowerShell hooks, Docker |
| **VCS & CLI Platform** | GitHub (`gh`) & GitLab (`glab`) — `main` protected; PR/MR required |
| **Knowledge Base / Domain Docs** | `docs/operating-model/`, `docs/workflow/`, `docs/contracts/`, `docs/plans/`, `docs/guides/` |
| **Active Work-Item State Dir** | `work/<INT-xxx>/` (`work/index.yaml`) · Local agent traces in `.sdlc/traces/` (`scripts/sdlc_trace.py`) |
| **Playbooks & Reusable Skills** | `.agents/` (`agents/`, `skills/`, `workflows/`) mirrored to `.claude/`, `.codex/`, `.agent/` |
| **Read-Only / Domain Overlays** | `docs/reference-architecture/` (archive); domain packs in `examples/project-packs/` (e.g., `ebmc/`) |
| **Workspace Isolation Rule** | `feat/<INT-xxx>-<slug>` via `python3 scripts/worktree.py create <INT-xxx> <slug>` (`.worktrees/`) |
| **Communication Language** | Thai for chat, work-item artifacts, and handoffs/digests; English for code, identifiers, schemas, commit messages, and framework core docs/templates/contracts (headings may be bilingual) |
| **Reference Timestamp** | `YYYY-MM-DD HH:mm:ss +07 (Asia/Bangkok)` *(human docs/reports; traces use ISO-8601 `+07:00`)* |

### Repository Map
- **Canonical Core (Source of Truth):** `.agents/agents/`, `.agents/skills/`, `.agents/workflows/`
- **Host Adapters (Generated Mirrors — do not edit directly):** `.claude/`, `.codex/`, `.agent/`
- **Governance & Routing:** [constitution.md](docs/operating-model/constitution.md), [core-bootloader.md](docs/workflow/core-bootloader.md), [dynamic-routing.md](docs/workflow/dynamic-routing.md)
- **Contracts & Templates:** `docs/contracts/` (JSON/YAML schemas), `docs/templates/` (incl. [AGENTS.template.md](docs/templates/AGENTS.template.md))
- **Guardrails, Validators & Tools:** `scripts/sdlc_hook.py`, `scripts/sdlc_guard/`, `scripts/sync-adapters.py`, `scripts/worktree.py`, `scripts/validate_work_item.py`
- **Orchestrator & Evals:** `orchestrator/` (CLI + optional FastAPI), `evals/` (contract + isolated live evals), `tests/`

### Canonical Artifact Placement
Work-item files live in `work/<INT-xxx>/` (registered in `work/index.yaml`), framework plans in `docs/plans/plan-<NNN>-<slug>.md`, handoffs in `docs/handoff/`, runtime state in gitignored `.sdlc/`. **Never place `intent.md`, `spec.md`, `plan.md`, `tasks.json`, or `REVIEW.md` at the repo root.** Full table and rules: [docs/contracts/README.md](docs/contracts/README.md).

---

## 2. Operating Philosophy & Dynamic Routing

- **Dynamic, Not Linear:** Never force every request through a fixed waterfall (`PM -> BA -> SA -> Dev -> QA`). Classify change type, blast radius, and risk level first using [core-bootloader.md](docs/workflow/core-bootloader.md) & [dynamic-routing.md](docs/workflow/dynamic-routing.md), then pick the **Minimum Safe Workflow**.
- **Progressive Disclosure:** Do not load every guideline upfront. Consult `.agents/skills/` and `.agents/workflows/` only when triggered:
  - *Ambiguous Request* → Requirement discovery / brainstorming (`ba-po-agent`, `spec-driven-design`)
  - *High-Stakes Tradeoff / Pivot* → Multi-lens pressure-testing (`council-pressure-test` — Contrarian, First Principles, Expansionist, Outsider, Executor)
  - *Non-trivial / Multi-file Change* → Architecture & implementation planning (`sa-architect-agent`)
  - *Behavior Change* → Test-Driven Development (`qa-function-agent`, `istqb-test-design`, `tdd-implementation`)
  - *Logic Modification* → Static logic dry-run (trace inputs through the changed branches by hand) as a pass in `code-reviewer-agent`, before execution
  - *Bug / Regression* → Failing reproduction test & root-cause tracing before patching
  - *Pre-Completion / Pre-Merge* → Independent review & security gate (`code-reviewer-agent`, `security-audit-agent`, `owasp-security-review`)

---

## 3. Lifecycle & Tiered Gate Governance

Agents propose, implement, and verify; **Humans approve gates and hold sole merge authority** (see [constitution.md](docs/operating-model/constitution.md)).

Gate numbers mean the same thing in every Tier (a Tier only skips gates). Full definitions and the Risk → Tier mapping live in [constitution.md §1](docs/operating-model/constitution.md) — do not restate them here.

- **Standard Tier:** Plan Checkpoint (approved in chat, recorded under `## Plan Checkpoint` in the PR/MR) → Implement & Verify (lightweight `REVIEW.md` by an independent reviewer) → **Gate 3: Release & Merge**
- **High-Risk Tier:** **Gate 1: Intent** → **Gate 2: Spec/ADR** → TDD & Build → **Gate 3: Release & Merge** (Framework Changes and high-risk bug fix / config changes skip Gate 1: Framework uses `docs/plans/plan-<NNN>-<slug>.md` as the Gate 2 spec, bug fix / config use a Fast-Track Spec / Change Plan — see the constitution mapping)

1. **Define & Classify:** Determine change scope, risk tier, and required artifacts. Escalate to High-Risk immediately if a low-risk task touches auth, schema, secrets, CI gates, or framework paths, or if the task's total diff grows past ~300 lines across more than one module.
2. **Plan Packet:** Propose target files, test strategy, verification commands, risks, and rollback steps.
3. **Pre-Build Gate:** Obtain Human approval before modifying behavior (Plan Checkpoint for Standard; Gate 1/2 for High-Risk).
4. **Implement (Atomic Increments):** Execute in small, reviewable steps. If scope, touched files, or risk drifts from the approved plan, pause and re-route to the Plan Checkpoint (Standard) or Gate 1/2 (High-Risk).
5. **Verify (Independent Check):** Run automated checks and cite observed outputs verbatim.
6. **Integration Gate:** Open PR/MR referencing the tracking item (`Related to #ID`, never auto-close prematurely) with attached evidence; Human reviews and merges.
7. **Closeout & Compound Learning:** Update `ROADMAP.md`, `CHANGELOG.md`, `work/index.yaml`, and Knowledge Base **only after merge**.

---

## 4. Engineering Discipline & Role Boundaries

- **Separation of Duties (`Implementer ≠ Verifier ≠ Approver`):** Never let the same execution pass that writes code act as final verifier. Hand off via structured artifacts (`intent.md`, `spec.md`, `test-report.md`, `tasks.json`, `REVIEW.md`), not informal chat summaries.
- **Change Sizing (three separate measures):** (1) Target **~100–300 changed lines per commit/increment**. (2) Any single PR exceeding **~1,000 lines must be split** into Stacked PRs, Vertical Slices, or Reviewer File Groups. (3) The risk-escalation test in §3 is independent: a task whose *total* diff passes ~300 lines across more than one module escalates to High-Risk, however many commits it is split into.
- **Clean Commits:** Land refactoring and functional behavior changes in separate commits, even when small. Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- **Test-First Discipline:** Write or identify a failing test before changing behavior, or explicitly document why no test seam exists. Coding agents must never weaken existing QA test oracles.
- **Human Comprehension First (ELI10 Rule):** Explain every change clearly in plain language (like explaining to a smart 10-year-old: *what file changed, why/for what work, core concept/steps, and observed evidence*), scaling depth proportionately with common sense. **High-Risk / Framework Tier:** write a Pre-PR **Change Digest file** (`work/<INT-xxx>/change-digest.md`, or `docs/handoff/YYYY-MM-DD-<slug>-digest.md` when no work item exists, using [change-digest.template.md](docs/templates/change-digest.template.md)) before opening the PR; it is checked by `validate_work_item.py <work-dir> --require-digest`, or `validate_work_item.py --digest-file <path>` for a `docs/handoff/` digest. Neither is wired into CI/hooks yet, so the reviewer must run it. **Standard Tier:** a short ELI10 section in the PR/MR description is enough. Humans must stay ahead of AI speed.
- **Enterprise-Agnostic Core:** Never place project-specific business rules (e.g., EBMC) into `.agents/` or `docs/contracts/`. Place domain overlays in `examples/project-packs/`.

---

## 5. Source of Truth & Knowledge Loop

When information conflicts, resolve in strict descending order:
1. Explicit Human instruction in the active session
2. Approved project specs (`intent.md`, `spec.md`, ADR, `constitution.md`)
3. Project status & architectural decision logs (`ROADMAP.md`, `docs/adr/`)
4. Current repository code and passing tests
5. Historical session handoffs (`docs/handoff/`) or trace summaries
6. Agent inference *(must be explicitly labeled `[Assumption]`, never stated as confirmed fact)*

- **Search Before Asking:** Always search `docs/` and `work/<INT-xxx>/` before claiming ignorance or asking the Human for context.
- **Feedback Loop:** Capture newly discovered edge cases, bug patterns, and business clarifications into PR notes/Knowledge Base and `evals/datasets/` at closeout (promote recurring rules into `AGENTS.md` via Human-approved Framework Change).

---

## 6. Operational Command Reference

- **Health & Parity:**
  - `python3 scripts/doctor.py` — check OS, Python, Git, and hook readiness (Windows: `py -3`)
  - `python3 scripts/sync-adapters.py --sync` / `--check` — regenerate & verify `.claude/`, `.codex/`, `.agent/` from `.agents/` + `trace_hooks.py`
  - `python3 scripts/validate-context-budget.py` — verify instruction file line budgets
- **Contracts, Work Items & Evals:**
  - `python3 scripts/validate-contracts.py --check-defaults`
  - `python3 scripts/validate_work_item.py work/<INT-xxx> --require-review` (add `--require-digest` for High-Risk / Framework Tier)
  - `python3 evals/run_evals.py --mode contract`
  - `python3 -m unittest discover -s tests -v`
- **Worktrees & Traces:**
  - `python3 scripts/worktree.py create <INT-xxx> <slug>` / `list` / `cleanup <INT-xxx>`
  - `python3 scripts/sdlc_trace.py list` / `show <id>` / `export --work-item <INT-xxx> --out work/<INT-xxx>/trace-summary.md`

---

## 7. Guardrails, Circuit Breakers & Common Pitfalls

### Always
- Classify risk and verify workspace isolation before creating or editing files.
- Run verification checks after the final edit before claiming any task is done, fixed, or ready.
- Save heavy outputs (full test logs, trace exports) as files inside `work/<INT-xxx>/` instead of pasting inline.
- Record durable architectural or security trade-offs as an ADR in `docs/adr/` (see [adr.template.md](docs/templates/adr.template.md)) before closeout.

### Ask First (Mandatory Human Confirmation)
- **Before every commit:** List exact staged files and confirm secret/privacy scan results.
- **Before external platform actions:** Draft PR/MR descriptions, issue comments, or external API calls and wait for confirmation.
- **Protected & High-Risk Changes:** Scope changes, auth/permission/payment/security logic, DB migrations, CI gates, or editing `protected_globs` in [policy.json](scripts/sdlc_guard/policy.json) (Human maintainer must commit protected paths with `SDLC_ALLOW_PROTECTED=1`).

### Never
- Commit or expose secrets, `.env*`, unmasked PII/PHI, or raw `.sdlc/traces/` logs.
- Edit `.claude/settings.json`, `.codex/hooks.json`, or `.agent/hooks.json` by hand — edit `scripts/sdlc_guard/trace_hooks.py` or `scripts/sync-adapters.py` and run `--sync`.
- Set `SDLC_TRACE_DIR` to the real store during tests (always use a temp dir or `SDLC_TRACE_LEVEL=off`).
- Modify `docs/reference-architecture/` (except approved archival cleanup) unless explicitly asked.
- Merge PRs/MRs directly, set `SDLC_ALLOW_PROTECTED=1`, declare tests passed without running them, or include unrelated changes inside an approved task.

### Stop Conditions (Circuit Breakers)
Halt autonomous execution and escalate to the Human immediately when:
- Missing requirements or contracts force risky guesswork on business behavior.
- A fix fails verification after **two** `verify -> rework` cycles (**2-Strike Rule**).
- Failures occur outside the expected blast radius or contradict approved specs.

---

## 8. Definition of Done (DoD)

An agent may only report a task as **Ready for Human Gate** (never self-closed/merged) when all applicable criteria hold **after the final edit**:

### Baseline DoD (Every Task)
- **Fresh Verification:** All impacted checks (`sync-adapters.py --check`, `validate-context-budget.py`, `validate-contracts.py`, `evals`, `unittest`) executed cleanly *after* the last edit — stale results do not count.
- **Honest Evidence:** Report exact commands run, observed pass/fail/skip counts, and explicitly note any untested runtime/OS (e.g., Windows, Docker, optional deps).
- **Clean Diff & Hygiene:** `git diff --check` passes; zero untracked scratch files, secrets, PII, or raw `.sdlc/traces/` staged; all artifacts placed in their canonical paths.
- **Human-Readable Explanation:** Changes are summarized clearly in plain language (what, why, how, evidence); High-Risk / Framework PRs include an up-to-date change-digest file before PR creation; Standard PRs include a short ELI10 section in the PR/MR description.

### Extended DoD (Behavior Changes & High-Risk Tier)
- **Spec & Oracle Integrity:** Implementation matches approved `spec.md`; QA test oracles were not weakened; `tasks.json` marks `"passes": true` only with observed `evidence`.
- **Cross-Artifact Traceability:** `work/<INT-xxx>/` passes `python3 scripts/validate_work_item.py work/<INT-xxx> --require-review --require-digest` (High-Risk / Framework; Standard Tier omits `--require-digest`).
- **Independent Review & Trace Export:** `REVIEW.md` produced by an independent verifier pass (`Implementer ≠ Verifier`) and `trace-summary.md` exported via `scripts/sdlc_trace.py export`.
- **True Closeout:** Only after Human Gate approval and PR/MR merge are `ROADMAP.md`, `CHANGELOG.md`, and Knowledge Base updated.
