# Implementation Plan Packet: AI-Native SDLC Agent Framework

**Document ID:** `PLAN-SDLC-001`  
**Status:** Approved for Phase 0 Execution  
**Architecture Choice:** Structure Option A (Separated Reference Library + Root Executable Core) + Hybrid Runtime (File-First Canonical Core + Thin Harness Adapters → Stateless Python Orchestrator in Phase 3–4)  
**Domain Scope:** Enterprise-agnostic Core with Pluggable Project Packs (e.g., `examples/project-packs/ebmc/`)

---

## 1. Executive Summary & Design Invariants

1. **Single Canonical Source of Truth:** Role definitions, skills, workflows, and contracts live in `.agents/` and `docs/`. Harnesses (`.claude/`, `.codex/`, `.agent/`) and the future Python Orchestrator **must consume or mirror from `.agents/`** — never duplicate business logic.
2. **Dynamic Risk-Based Routing:** Not every task needs PM → BA → SA → Dev → QA. Tasks are classified first via `docs/workflow/core-bootloader.md` and routed to the smallest safe workflow.
3. **Harness over Prompting:** Natural-language rules are backed by deterministic validators (`scripts/`), edit guards, and CI evals.
4. **Enterprise-Agnostic Core:** Domain-specific rules (e.g., EBMC, Robot Framework) live strictly inside `examples/project-packs/` or target project repositories.

---

## 2. Workstream Breakdown & Concrete Tasks

### Workstream A: Phase 0 — Repository Restructure & Governance (Current Sprint)
| Task ID | Task Description | Target Files / Paths | Verification Criteria |
| :--- | :--- | :--- | :--- |
| `P0-01` | Move 01–09 taxonomy folders into `docs/reference-architecture/` | `docs/reference-architecture/01..09` | Zero `01.`–`09.` folders at repo root |
| `P0-02` | Create cross-harness entrypoint & pointer | `AGENTS.md`, `CLAUDE.md`, `README.md` | Clear map, gates, and < 150 lines in `AGENTS.md` |
| `P0-03` | Establish enterprise-agnostic constitution & HITL gates | `docs/operating-model/constitution.md` | Defines 3 mandatory HITL gates & protected paths |
| `P0-04` | Establish dynamic routing bootloader | `docs/workflow/core-bootloader.md`, `docs/workflow/dynamic-routing.md` | Covers Feature, Bug, Config, Data, Docs routes |
| `P0-05` | Scaffold canonical core, adapters & EBMC example pack | `.agents/`, `.agent/`, `.claude/`, `.codex/`, `examples/project-packs/ebmc/` | Directories & initial EBMC skill/agent example created |

### Workstream B: Phase 1 — Spec-Driven Artifact Spine (Next Sprint)
| Task ID | Task Description | Target Files / Paths | Verification Criteria |
| :--- | :--- | :--- | :--- |
| `P1-01` | Define `intent` & `spec-ipo` machine-readable schemas | `docs/contracts/intent.schema.yaml`, `docs/contracts/spec-ipo.schema.yaml` | Validated by JSON/YAML schema linter |
| `P1-02` | Define `tasks.schema.json` for long-horizon coding loops | `docs/contracts/tasks.schema.json` | Supports `task_id`, `spec_ref`, `passes: boolean` |
| `P1-03` | Define `test-report.schema.json` & `review-gate.schema.yaml` | `docs/contracts/test-report.schema.json`, `docs/contracts/review-gate.schema.yaml` | Enforces `URD`→`FS`→`TC` traceability |
| `P1-04` | Create Markdown templates for all SDLC artifacts | `docs/templates/*.md` | Templates align 1:1 with contracts |

### Workstream C: Phase 2 — Canonical Agents, Generic Skills & Adapters
| Task ID | Task Description | Target Files / Paths | Verification Criteria |
| :--- | :--- | :--- | :--- |
| `P2-01` | Author 7 canonical SDLC agents (model-agnostic) | `.agents/agents/*.md` | Each agent < 120 lines, explicit I/O contract |
| `P2-02` | Author 4 generic SDLC skills | `.agents/skills/*/SKILL.md` | `spec-driven-design`, `istqb-test-design`, `tdd-implementation`, `owasp-security-review` |
| `P2-03` | Refactor `function-test-agent.md` into EBMC Project Pack | `examples/project-packs/ebmc/` | Domain knowledge separated from core QA agent |
| `P2-04` | Build adapter sync/parity script for Claude, Codex, Antigravity | `.claude/`, `.codex/`, `.agent/`, `scripts/sync-adapters.py` | 100% parity across all 3 harnesses |

### Workstream D: Phase 3 — Deterministic Validators, Hooks & CI Evals
| Task ID | Task Description | Target Files / Paths | Verification Criteria |
| :--- | :--- | :--- | :--- |
| `P3-01` | Implement contract & traceability validator | `scripts/validate-contracts.py` | Catches missing sections, invalid IDs, broken traceability |
| `P3-02` | Implement adapter parity & context budget checker | `scripts/validate-adapter-parity.py`, `scripts/validate-context-budget.py` | Fails CI if adapters drift or `AGENTS.md` bloats |
| `P3-03` | Implement edit guard hooks (protect test oracles & constitution) | `.githooks/pre-commit`, `scripts/guard-protected-paths.sh` | Blocks unauthorized edits by dev agents |
| `P3-04` | Setup GitHub Actions scoped CI + Golden Eval dataset | `.github/workflows/validate.yml`, `evals/` | CI runs scoped checks + 3–5 anonymized eval cases |

### Workstream E: Phase 4 — Stateless Python Orchestrator & Stage 6 Loop
| Task ID | Task Description | Target Files / Paths | Verification Criteria |
| :--- | :--- | :--- | :--- |
| `P4-01` | Build Python loader for `.agents/` + `docs/contracts/` | `orchestrator/core/loader.py` | Zero hardcoded prompts in Python |
| `P4-02` | Implement State-Graph Pipeline (LangGraph or Google ADK) | `orchestrator/graphs/sdlc_pipeline.py` | Supports Sequential, Parallel Review, and Loop retries |
| `P4-03` | Expose FastAPI / CLI runner + Telemetry & Cost logger | `orchestrator/api/main.py`, `orchestrator/telemetry/` | Logs token cost, latency, and gate outcomes |
| `P4-04` | Add `bands.yaml` & `ops-maintain-agent` closed-loop | `docs/operating-model/bands.yaml` | Anomaly draft creates `intent.md` PR for human review |

---

## 3. Definition of Done (DoD) Across All Phases
- Every new policy or contract has a corresponding automated check or test.
- No hardcoded secrets, credentials, or organization-specific private URLs in Core.
- All changes preserve compatibility across Claude Code, Codex, and Antigravity.
