---
name: tdd-implementation
description: Execute coding tasks via Plan Mode, tasks.json state tracking, failing-test-first reproduction, single-command verification, and strict test-oracle preservation.
---

# TDD Implementation Skill

## Execution Discipline
1. **Plan Before Editing:** Explore read-only and draft `plan.md` + `tasks.json` first. Never start multi-file edits blindly.
2. **Bug Fixes — Failing Test First:** Reproduce the defect as an automated failing test, verify it fails for the expected reason, then fix production code without altering the test oracle.
3. **Incremental Slices:** Work through `TASK-xxx` items one by one. Keep changes small and reviewable.
4. **Single-Command Verification:** Run the repository's canonical build, test, and lint commands (`verification_cmd`).
5. **Evidence Gate:** Only mark `"passes": true` in `tasks.json` after observing exit code `0` with zero skipped assertions. Paste exact command and summary output into `evidence`.
6. **Mistake-Twice Rule:** If you hit a recurring project gotcha twice, propose adding a concise rule to `AGENTS.md` / `CLAUDE.md`.
