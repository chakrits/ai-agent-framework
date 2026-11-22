<h1 align="center">AI-Native SDLC Agent Framework</h1>

<p align="center">
  <a href="https://github.com/chakrits/ai-agent-framework/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/chakrits/ai-agent-framework?style=social"></a>
  <a href="https://github.com/chakrits/ai-agent-framework/graphs/contributors"><img alt="contributors" src="https://img.shields.io/github/contributors/chakrits/ai-agent-framework"></a>
  <a href="https://github.com/chakrits/ai-agent-framework/discussions"><img alt="discussions" src="https://img.shields.io/github/discussions/chakrits/ai-agent-framework"></a>
  <a href="https://github.com/chakrits/ai-agent-framework/releases"><img alt="release" src="https://img.shields.io/github/v/release/chakrits/ai-agent-framework"></a>
  <a href="https://github.com/chakrits/ai-agent-framework/actions/workflows/validate.yml"><img alt="build" src="https://img.shields.io/github/actions/workflow/status/chakrits/ai-agent-framework/validate.yml?branch=main"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/github/license/chakrits/ai-agent-framework"></a>
</p>
<p align="center">
  <img alt="platform" src="https://img.shields.io/badge/platform-macOS%20%C2%B7%20Windows%20%C2%B7%20Linux%20%C2%B7%20WSL-lightgrey">
  <img alt="built with" src="https://img.shields.io/badge/built%20with-Python%203.10%2B-3776AB">
  <img alt="agents" src="https://img.shields.io/badge/agents-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Antigravity-blueviolet">
</p>
<p align="center">
  <a href="docs/">Docs</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="https://github.com/chakrits/ai-agent-framework/releases">Releases</a> ·
  <a href="https://github.com/chakrits/ai-agent-framework/discussions">Discussions</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

An **enterprise-agnostic, spec-driven, multi-harness AI Agent Framework** for the Software Development Lifecycle (SDLC).

Designed to work seamlessly across interactive coding harnesses (**Claude Code**, **OpenAI Codex**, **Antigravity**) and scale to headless **CI/CD runners** and a **Python Orchestrator Service** without duplicating prompts or business logic.

## Core Principles

1. **Single Canonical Source of Truth:** All specialist roles, skills, contracts, and routing rules live in `.agents/` and `docs/`. Host folders (`.claude/`, `.codex/`, `.agent/`) are thin adapters.
2. **Spec-Driven Development (SDD):** Version-controlled artifacts (`intent.md` → `spec.md` → `test-report.md` → `plan.md` / `tasks.json` → `REVIEW.md` → `change-digest.md`) live together in `work/<INT-xxx>/` and are the contract between humans and agents. They never go at the repo root.
3. **Dynamic Risk-Based Routing:** Classify tasks first via [core-bootloader.md](docs/workflow/core-bootloader.md) and select the minimum safe workflow ([dynamic-routing.md](docs/workflow/dynamic-routing.md)).
4. **Tiered Human Gates, Fixed Gate Numbers:** Agents propose, implement and verify. Humans approve gates and hold sole merge authority. Gate numbers mean the same thing in every tier (see below).
5. **Deterministic Harness & Gates:** Rules are enforced by validation scripts, path guards, and CI evals — not just natural-language wishes.
6. **Human Comprehension First (ELI10):** Every change is explained in plain language. High-Risk and Framework work ships a validated Change Digest file.
7. **Pluggable Project Packs:** Core remains domain-agnostic; organization/project specifics (like the EBMC + Robot Framework example) live in `examples/project-packs/`.

## Tiered Gate Model

Definitions and the full Risk → Tier mapping live in the [Constitution §1](docs/operating-model/constitution.md). This table is a summary only.

| Tier | Typical work | Gates |
| :--- | :--- | :--- |
| **Standard** | Isolated low/medium bug fix, config, docs/tests | Plan Checkpoint (recorded in the PR/MR) → **Gate 3** Merge |
| **High-Risk** | New feature, API/DB schema | **Gate 1** Intent → **Gate 2** Spec → **Gate 3** Merge |
| **High-Risk (Fast-Track)** | High-risk bug fix or config change | **Gate 2** Fast-Track Spec / Change Plan → **Gate 3** |
| **High-Risk (Framework)** | `AGENTS.md`, `.agents/`, contracts, guards, CI gates | **Gate 2** Framework Spec (`docs/plans/plan-<NNN>-<slug>.md`) → **Gate 3** |

## Repository Structure

| Path | What lives there |
| :--- | :--- |
| `AGENTS.md` / `CLAUDE.md` | Cross-harness entrypoint (map, gates, DoD) and the Claude Code-specific notes |
| `.agents/` | **Canonical source:** `agents/` (7 roles), `skills/` (`agent-trace`, `council-pressure-test`, `istqb-test-design`, `owasp-security-review`, `spec-driven-design`, `tdd-implementation`), `workflows/` |
| `.claude/`, `.codex/`, `.agent/` | Generated host adapters — never edit by hand; run `python3 scripts/sync-adapters.py --sync` |
| `docs/operating-model/` | [Constitution](docs/operating-model/constitution.md): gates, Risk → Tier mapping, protected paths |
| `docs/workflow/` | [Core Bootloader](docs/workflow/core-bootloader.md) and [Dynamic Routing](docs/workflow/dynamic-routing.md) |
| `docs/contracts/` | Machine-readable schemas and the [canonical artifact placement table](docs/contracts/README.md) |
| `docs/templates/` | Artifact templates, incl. [change digest](docs/templates/change-digest.template.md), [ADR](docs/templates/adr.template.md), and [AGENTS.md for target repos](docs/templates/AGENTS.template.md) |
| `docs/adr/` | [Architecture Decision Records](docs/adr/README.md) (`ADR-<NNN>-<slug>.md`) |
| `docs/plans/` | Framework plans and reviews (`plan-<NNN>-<slug>.md` for new files; older files are kept as-is) |
| `docs/handoff/` | Cross-session handoffs and digests for changes without a work item |
| `work/<INT-xxx>/` | Work-item artifacts, registered in `work/index.yaml` |
| `.sdlc/` | Local runtime state and agent traces (gitignored — never commit) |
| `scripts/` | Guards and hooks (`sdlc_hook.py`, `sdlc_guard/`), validators, `sync-adapters.py`, `worktree.py`, `sdlc_trace.py` |
| `orchestrator/`, `evals/`, `tests/` | Python orchestrator (CLI + optional FastAPI), contract/live evals, unit tests |
| `examples/project-packs/` | Domain overlays (e.g., `ebmc/`) |
| `docs/reference-architecture/` | Read-only conceptual archive (01–09) |

## Quick Navigation

- **Start Here (Agents & Humans):** [AGENTS.md](AGENTS.md) | [CLAUDE.md](CLAUDE.md)
- **Roadmap & Plans:** [ROADMAP.md](ROADMAP.md) | [Implementation Plan Packet](docs/plans/implementation-plan-packet.md) | [`docs/plans/`](docs/plans/)
- **Governance:** [Constitution](docs/operating-model/constitution.md) | [Artifact Contracts & Placement](docs/contracts/README.md) | [ADRs](docs/adr/README.md)
- **Routing:** [Core Bootloader](docs/workflow/core-bootloader.md) | [Dynamic Routing](docs/workflow/dynamic-routing.md)
- **Example Project Pack:** [EBMC Project Pack](examples/project-packs/ebmc/README.md)
- **Stateless Python Orchestrator:** [orchestrator/README.md](orchestrator/README.md)
- **Conceptual Knowledge Base:** [Reference Architecture (01–09)](docs/reference-architecture/)

## Verification Commands

```bash
python3 scripts/sync-adapters.py --check                 # .claude/.codex/.agent match .agents/
python3 scripts/validate-context-budget.py               # instruction-file line budgets
python3 scripts/validate-contracts.py --check-defaults   # schemas and templates
python3 scripts/validate_work_item.py work/<INT-xxx> --require-review --require-digest   # traceability + digest (High-Risk)
python3 scripts/validate_work_item.py --digest-file docs/handoff/<date>-<slug>-digest.md   # digest without a work item
python3 evals/run_evals.py --mode contract
python3 -m unittest discover -s tests
```

The digest checks are not run by CI or the git hooks yet, so the reviewer runs them by hand.

## Prerequisites & Setup (Windows / macOS / Linux / WSL)

| OS | Required | Setup command |
| :--- | :--- | :--- |
| macOS / Linux / WSL | Python 3.10+, Git | `python3 scripts/setup.py` |
| Windows | Python 3.10+ (python.org, provides `py`) and **Git for Windows** (provides `sh`/Git Bash, used by Claude Code hooks and git hooks) | `py -3 scripts\setup.py` |

- `setup.py` sets `core.hooksPath=.githooks` and runs the environment doctor (`python scripts/doctor.py`).
- Every hook goes through one entrypoint, `scripts/sdlc_hook.py`, launched by `scripts/bin/sdlc-hook` (sh) or `scripts/bin/sdlc-hook.cmd` (cmd/PowerShell). Rules live in `scripts/sdlc_guard/policy.json`; paths from any OS (`C:\...`, `/c/...`, `/mnt/c/...`, `/Users/...`) are normalized before matching.
- Claude Code: `.claude/settings.json` (SessionStart doctor + PreToolUse guard). Codex: review and trust `.codex/hooks.json` with `/hooks` (generated by `scripts/sync-adapters.py --sync`).
- Committing protected governance files requires a human to set `SDLC_ALLOW_PROTECTED=1` for that commit.

## Agent Trace & Versioning

- **Agent trace:** hooks record prompts, commands, outputs, guard decisions, model and effort to `.sdlc/traces/` (local, gitignored, secrets redacted, timestamps in the machine's local time with UTC offset, e.g. `+07:00`). Inspect with `python3 scripts/sdlc_trace.py list | show | summary | export`; change `SDLC_TRACE_LEVEL` (`off|info|debug`) with `config set` — see the [manual (TH)](docs/guides/agent-trace-manual.md) and the [monitoring guide](docs/guides/agent-trace-monitoring.md) for Grafana / Elastic / OpenSearch / OpenTelemetry.
- **Versioning:** SemVer in `version.txt` (`python3 scripts/sdlc_hook.py --version`), released by [release-please](https://github.com/googleapis/release-please) from [Conventional Commits](https://www.conventionalcommits.org/) — see [CHANGELOG.md](CHANGELOG.md).

## GitHub & GitLab Support
- **CI Pipelines:** [GitHub Actions](.github/workflows/validate.yml) and [GitLab CI](.gitlab-ci.yml) run identical parity, context-budget, contract, unit-test, and eval checks.
- **Templates:** PR/MR and Issue templates are provided under `.github/` and `.gitlab/`.
- **Dual Remotes:** Once you have both remote URLs, run:
  ```bash
  bash scripts/setup-remotes.sh <github_repo_url> <gitlab_repo_url>
  git push all main   # pushes to both GitHub and GitLab
  ```
