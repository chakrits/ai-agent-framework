---
name: tdd-implementation
description: Execute coding tasks via Plan Mode, tasks.json state tracking for work items, failing-test-first reproduction, single-command verification, and strict test-oracle preservation.
---

# TDD Implementation Skill

## Execution Discipline
1. **Plan Before Editing:** Explore read-only and draft the plan first (`plan.md` + `tasks.json` with a work item; without one, the PR/MR `## Plan Checkpoint` packet for Standard work or the approved `docs/plans/` spec for a Framework Change). Never start multi-file edits blindly.
2. **Bug Fixes — Failing Test First:** Reproduce the defect as an automated failing test, verify it fails for the expected reason, then fix production code without altering the test oracle.
3. **Incremental Slices:** Work through slices (`TASK-xxx`) one by one. Keep changes small and reviewable.
4. **Single-Command Verification:** Run the repository's canonical build, test, and lint commands (`verification_cmd`).
5. **Evidence Gate:** Report success only after observing exit code `0` with zero skipped assertions. With a work item, then mark `"passes": true` in `tasks.json` and paste the exact command and summary output into `evidence`; without one, put them under `## Verification` in the PR/MR (Standard) or in the change digest (Framework).
6. **Mistake-Twice Rule:** If you hit a recurring project gotcha twice, propose adding a concise rule to `AGENTS.md` / `CLAUDE.md`.
