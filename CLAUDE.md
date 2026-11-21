# CLAUDE.md

Read and follow [AGENTS.md](AGENTS.md) as the canonical repository instruction map.

## Claude Code Specific Notes
- Load specialist roles from `.claude/agents/` (mirrored from `.agents/agents/`).
- Load reusable skills from `.claude/skills/` (mirrored from `.agents/skills/`).
- Always enter **Plan Mode** before multi-file implementation and record the plan in `plan.md` or `tasks.json`.
- Never bypass pre-tool or pre-commit validation hooks.
