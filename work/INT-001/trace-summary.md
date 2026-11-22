# Agent trace summary — INT-001

_Generated 2026-11-21 18:57 +0700 from local traces; secrets redacted, outputs truncated._

| Metric | Value |
| :--- | :--- |
| Sessions | 1 |
| Events | 8 |
| Tool calls (completed, failed or blocked) | 3 |
| Blocked by guard | 0 |
| Failed tool calls | 0 |
| Avg tool duration (ms) | 42.0 |
| Models | gemini-4-argon (8) |
| Effort levels | - |
| Permission modes | - |
| Window | 2026-11-21T18:57:17.498+07:00 → 2026-11-21T18:57:17.767+07:00 |

## Tool calls

| Tool | Count |
| :--- | ---: |
| Bash | 3 |

## Guard blocks

- none

## Most frequent commands

- `python3 scripts/validate-contracts.py --tasks work/INT-001/tasks.json --test-report work/INT-001/tes` (x1)
- `python3 scripts/validate_work_item.py work/INT-001 --require-review` (x1)
- `python3 -m unittest tests/test_work_item_validator.py -v` (x1)
