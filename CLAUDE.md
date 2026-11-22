# CLAUDE.md

Read and follow [AGENTS.md](AGENTS.md) as the canonical repository instruction map.

## Claude Code Specific Notes
- Load specialist roles from `.claude/agents/` (mirrored from `.agents/agents/`).
- Load reusable skills from `.claude/skills/` (mirrored from `.agents/skills/`).
- Always enter **Plan Mode** before multi-file implementation and record the plan in `work/<INT-xxx>/plan.md` + `tasks.json`, or in `docs/plans/plan-<NNN>-<slug>.md` for framework changes without a work item. Never create `plan.md`, `tasks.json`, `intent.md`, or `spec.md` at the repo root.
- Never bypass pre-tool or pre-commit validation hooks.
