# AGENTS.md — AI-Native SDLC Framework

> **Purpose:** Cross-harness entrypoint (Map & Gate) for Codex, Claude Code, Antigravity, and the Python Orchestrator. Keep this file concise; follow links for detailed policies.

## 1. Repository Map

- **Canonical Core (Source of Truth):** `.agents/`
  - `.agents/agents/` — Specialist SDLC role definitions
  - `.agents/skills/` — Reusable, progressive-disclosure engineering & QA skills
  - `.agents/workflows/` — Reusable end-to-end SDLC workflow playbooks
- **Host Adapters (Thin Mirrors/Configs):**
  - `.claude/` (Claude Code), `.codex/` (OpenAI Codex), `.agent/` (Antigravity)
- **Operating Model & Routing:**
  - [Constitution](docs/operating-model/constitution.md) — Non-negotiable governance, security, and HITL gates
  - [Core Bootloader](docs/workflow/core-bootloader.md) — **Read this first** to classify a task
  - [Dynamic Routing](docs/workflow/dynamic-routing.md) — Risk-based workflow selection
- **Contracts, Templates & Plans:**
  - `docs/contracts/` — Machine-readable artifact schemas
  - `docs/templates/` — Standard Markdown output templates
  - `docs/plans/` — Implementation plans and roadmap ([ROADMAP.md](ROADMAP.md))
- **Examples & Reference Library:**
  - `examples/project-packs/` — Domain-specific overlays (e.g., `ebmc/`)
  - `docs/reference-architecture/` — Conceptual 9-layer AI Agent taxonomy (`01.`–`09.`)

## 2. Mandatory Operating Protocol

1. **Classify Before Acting:** Always start at [core-bootloader.md](docs/workflow/core-bootloader.md) to determine change type and risk tier. Do not force heavy multi-stage ceremonies on trivial docs/config fixes.
2. **Spec Before Code:** For any feature or behavior change, ensure `intent.md` and `spec.md` exist and are approved before writing implementation code.
3. **Separation of Synthesis & Verification:** The agent writing production code must not weaken or rewrite QA test oracles to make tests pass.
4. **Respect Protected Paths & HITL Gates:** Never bypass human approval gates defined in [constitution.md](docs/operating-model/constitution.md).
5. **Enterprise-Agnostic Core:** Never place project-specific business logic (such as EBMC rules) into `.agents/` or `docs/contracts/`. Project specifics belong in `examples/project-packs/` or target project repositories.
