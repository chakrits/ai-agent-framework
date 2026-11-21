---
name: agent-trace
description: Inspect your own agent trace (commands, outputs, guard blocks, model/effort) to debug a failure or show what happened; request temporary debug logging.
---

# Agent Trace Skill

Traces are local, redacted JSONL in `.sdlc/traces/`. Use the CLI; never read, edit or delete trace files by hand.

## Debug a failure
1. `python3 scripts/sdlc_trace.py list --limit 5` to find the session (Windows: `py -3 scripts\sdlc_trace.py`).
2. `python3 scripts/sdlc_trace.py show <session-prefix> --tool Bash --output` shows each command with ok / FAILED / BLOCKED and its output (first 2 KB at `info`).
3. `python3 scripts/sdlc_trace.py summary --session <session-prefix>` shows blocks, failures, model and effort.
A `BLOCKED: <reason>` line is a guard decision: fix the cause, do not retry the same command.

## Need the full output?
Raise detail temporarily; it reverts by itself (max 120 minutes):
`python3 scripts/sdlc_trace.py config set level debug --for 30m`, then check with `config show`.

## Human-only (the guard blocks these; ask the user)
Turning tracing `off`, persistent level/tz/retention changes, `config unset`, `hooks enable|disable`.

## Evidence
Do not commit raw traces. Attach only the output of
`python3 scripts/sdlc_trace.py export --work-item INT-xxx --out work/INT-xxx/trace-summary.md`.
