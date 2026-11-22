# AGENTS.md — Target Project Template

> Copy this file to the root of a target repository and fill out **Section 1** once.

## 1. Project Identity & Topology Mapping
*(Customize this table once per repository; all rules below reference these logical roles)*

| Logical Concept | Project Mapping / Convention |
| :--- | :--- |
| **Primary Stack & Runtime** | `<e.g., Node.js/TypeScript, Python, Go, Monorepo>` |
| **VCS & CLI Platform** | `<e.g., GitLab (glab) / GitHub (gh)>` |
| **Knowledge Base / Domain Docs** | `<e.g., docs/knowledge/ or wiki/>` |
| **Active Work-Item State Dir** | `<e.g., work/<issue-id>/ or .agent-state/>` |
| **Playbooks & Reusable Skills** | `<e.g., docs/workflows/ and .agents/skills/>` |
| **Read-Only External Repos** | `<e.g., vendor/, external/, or "None">` |
| **Workspace Isolation Rule** | `<e.g., Feature branch per issue / External git worktree>` |
| **Communication Language** | `<e.g., Thai for docs/reports; English for code/identifiers>` |
| **🕒 Reference Timestamp** | `<YYYY-MM-DD HH:mm:ss ±HH (IANA timezone, e.g., Asia/Bangkok)>` |

---

## 2. Operating Philosophy & Dynamic Routing
- **Dynamic, Not Linear:** Never force every request through a fixed waterfall (`PM -> BA -> SA -> Dev -> QA`). Classify the change first (type, blast radius, risk level) and select the **Minimum Safe Workflow**.
- **Progressive Disclosure:** Do not load every guideline upfront. Consult `<Playbooks & Reusable Skills>` only when triggered by the active task type:
  - *Ambiguous Request* → Requirement discovery / brainstorming workflow
  - *Non-trivial Change* → Architecture & implementation planning workflow
  - *Behavior Change* → Test-Driven Development (TDD) workflow
  - *Logic Modification* → Static logic dry-run review
  - *Bug / Regression* → Reproduction & root-cause tracing before patching
  - *Pre-Completion / Pre-Merge* → Independent verification & code review gate

---

## 3. Lifecycle & Tiered Gate Governance
Agents propose, implement, and verify; **the Human approves gates and holds sole merge authority.**

1. **Define & Classify:** Determine change scope, risk tier, and required artifacts.
2. **Plan Packet:** Propose target files, test strategy, verification commands, risks, and rollback steps.
3. **Pre-Build Gate:** Obtain Human approval before modifying behavior.
   - *Standard Tier:* Plan Checkpoint — plan approved directly in chat for isolated, low-risk changes and recorded in the PR/MR; the only later gate is Merge (Gate 3).
   - *High-Risk Tier (Ask First):* Gate 1 (Intent) → Gate 2 (Spec/Plan) — requires committed artifacts + formal Human sign-off before implementation; Merge is Gate 3.
   - Gate numbers keep one meaning across Tiers; a Tier only skips gates it does not need.
4. **Implement (Atomic Increments):** Execute in small, reviewable commits. If scope, touched files, or risk drifts from the approved plan, pause and re-route to the Plan Checkpoint (Standard) or Gate 1/2 (High-Risk).
5. **Verify (Independent Check):** Run automated tests, linters, and quality checks; cite actual execution logs.
6. **Integration Gate:** Open PR/MR referencing the tracking issue (`Related to #ID`, never auto-close prematurely) with attached evidence. Human reviews and merges.
7. **Closeout & Compound Learning:** Update high-level project status, changelogs, and `<Knowledge Base>` **only after merge**.

---

## 4. Engineering Discipline & Role Boundaries
- **Separation of Duties (Implementer ≠ Verifier):** Never allow the same execution pass that writes code to act as its final verifier. Hand off between implementation and verification using structured artifacts, not informal chat summaries.
- **Change Sizing:** Target **~100–300 changed lines** per commit/increment. Any task exceeding **~1,000 lines must be split** into Stacked PRs, Vertical Slices, or Reviewer File Groups.
- **Clean Commits:** Land refactoring and functional behavior changes in separate commits, even when small.
- **Test-First Discipline:** Write or identify a failing test before changing behavior, or explicitly document why no test seam exists.
- **Human Comprehension First (ELI10 Rule):** Explain every change in plain, intuitive language (*what files changed, why/goal, how it works, and proof*) scaled proportionately to change size; produce a Pre-PR Change Digest for multi-file or feature PRs so Humans never lose track of what AI built.

---

## 5. Source of Truth & Knowledge Loop
When information conflicts, resolve in strict descending order:
1. Explicit Human instruction in the active session
2. Approved project specs (Requirements, SDD, TDD, ADR, Test Plans)
3. Project status & architectural decision logs
4. Current repository code and passing tests
5. Historical session logs or notes
6. Agent inference *(must be explicitly labeled `[Assumption]`, never stated as confirmed fact)*

- **Search Before Asking:** Always search `<Knowledge Base>` and `<Active Work-Item State Dir>` before claiming ignorance or asking the Human for domain context.
- **Feedback Loop:** Capture newly discovered edge cases, bug patterns, and business clarifications into `<Knowledge Base>` and regression suites at closeout.

---

## 6. Guardrails & Circuit Breakers

### Always
- Classify risk and verify workspace isolation before creating or editing files.
- Run verification checks before claiming any task is done, fixed, or ready.
- Save heavy outputs (screenshots, full logs) as files inside `<Active Work-Item State Dir>` rather than pasting inline into chat or PR/MR descriptions.
- Record durable architectural or security trade-offs as an ADR before closeout.

### Ask First (Mandatory Human Confirmation)
- **Before every commit:** List exact staged files and confirm secret/privacy scan results.
- **Before external platform actions:** Draft PR/MR descriptions, issue comments, or external API calls and wait for confirmation.
- **Structural & High-Risk Changes:** Scope changes, cross-system architecture shifts, auth/permission/payment/security logic, destructive DB migrations, CI/CD gate changes, or weakening existing tests/lint rules.

### Never
- Commit or expose secrets, tokens, `.env*` files, or unmasked sensitive/personal data (PII/PHI) unless an explicit Human mock-data waiver is recorded.
- Modify `<Read-Only External Repos>` unless explicitly authorized.
- Merge PRs/MRs directly, declare tests passed without running them, or include unrelated changes inside an approved task.

### Stop Conditions (Circuit Breakers)
Halt autonomous execution and escalate to the Human immediately when:
- Missing requirements or contracts force risky guesswork on business behavior.
- A fix fails verification after **two** `verify -> rework` cycles (**2-Strike Rule**).
- Failures occur outside the expected blast radius or contradict approved specs.

---

## 7. Definition of Done (DoD)
An agent may report work as **Ready for Human Review/Gate** only when all hold **after the final edit**:
- **Fresh Evidence:** Automated tests, linters, and contract checks ran cleanly after the last change (cite exact counts and any skipped/untested scope).
- **Clean Diff & Scope:** Zero unrelated edits, secret/PII leaks, or scratch files; refactoring and behavior changes remain cleanly separated; artifacts placed in `<Active Work-Item State Dir>`.
- **Artifact & Review Completeness:** Required specs/plans/task states are updated (`Implementer ≠ Verifier`), heavy logs are saved in `<Active Work-Item State Dir>`, a plain-language Change Digest is ready for the Human before opening PR/MR, and Human Gate sign-off is requested before merge/closeout.
