---
plan_id: PLAN-INT-001
intent_ref: INT-001
spec_ref: SPEC-001
owner: dev-coding-agent
---

# Implementation Plan: Work Item Traceability Validator (`INT-001`)

## 1. Scope & Target Files
- **Files to Create:** `scripts/validate_work_item.py`, `tests/test_work_item_validator.py`
- **Files to Modify:** None
- **Protected Files (Do Not Modify):** `work/INT-001/test-report.md`, `docs/operating-model/constitution.md`, `docs/contracts/**`

## 2. Step-by-Step Execution Strategy
1. **Task `TASK-001` (`FS-001`):** Implement `check_intent_to_spec` checking `URD-xxx` coverage and non-empty invariant.
2. **Task `TASK-002` (`FS-002`):** Implement `check_spec_downstream` + CLI (`validate_work_item.py`) checking `FS-xxx` coverage across `spec.md`, `tasks.json`, `test-report.md`, and optional `--require-review`.
3. Verify `work/INT-001` itself passes both `validate-contracts.py` and `validate_work_item.py`, then record evidence in `tasks.json`.

## 3. Verification Commands
- Unit tests: `python3 -m unittest tests/test_work_item_validator.py -v`
- Contract & work item validation: `python3 scripts/validate_work_item.py work/INT-001 --require-review`

## 4. Rollback / Failure Plan
- Delete `scripts/validate_work_item.py` and `tests/test_work_item_validator.py`.
