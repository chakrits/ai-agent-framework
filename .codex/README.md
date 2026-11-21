# Codex Adapter Guidance

Follow [AGENTS.md](../AGENTS.md) at the repository root.

- Always start with [core-bootloader.md](../docs/workflow/core-bootloader.md) before modifying files.
- Keep execution scoped to isolated tasks and verify changes with deterministic checks before handoff.

## Canonical Agents (`.agents/agents/`)
- `ba-po-agent`
- `code-reviewer-agent`
- `dev-coding-agent`
- `ops-maintain-agent`
- `qa-function-agent`
- `sa-architect-agent`
- `security-audit-agent`

## Canonical Skills (`.agents/skills/`)
- `istqb-test-design`
- `owasp-security-review`
- `spec-driven-design`
- `tdd-implementation`

## Canonical Workflows (`.agents/workflows/`)
- `bug-fix-flow`
- `new-feature-flow`
