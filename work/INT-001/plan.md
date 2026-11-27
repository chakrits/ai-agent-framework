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

## Review Round 3

- Reproduce missing and partial mappings with copies of the pilot artifacts. Keep the QA test report as the baseline.
- Read URD/FS pairs from the Requirement-to-Spec Mapping columns and require each intent URD to have a mapped FS. Compare those pairs with the QA traceability matrix.
- Record local verification and the evidence needed for the human gates in `REVIEW.md`.

## Review Round 4

- In a temporary copy of the pilot, add a second URD that maps to an existing FS. Verify both validators return exit `1` when its Covered row lacks a valid test case ID.
- Enforce the requirement on each row before aggregating test references by function. Verify the same fixture passes once the shared function's existing test case is listed on the new row.
- Record the retrospective Gate 1–2 statement and track the PR head and CI run evidence for Gate 3.

## Review Round 5

- Reproduce undefined test case references in both CLI validators using a temporary pilot copy.
- Read defined test case IDs from the QA report's definition tables. Require traceability and work-item task references to resolve to a definition and report the missing ID.
- Verify from the staged snapshot and record the PR and CI evidence required for Gate 3.

## 4. Rollback / Failure Plan
- Delete `scripts/validate_work_item.py` and `tests/test_work_item_validator.py`.

## Addendum A1 — As-built scope (อนุมัติแล้ว)

ใช้คู่กับ [SPEC-001 Addendum A1](spec.md#addendum-a1--as-built-behaviour) บันทึกสิ่งที่ทำจริงในรีวิวรอบ 3–5 (PR #2) ไม่มีการแก้โค้ดเพิ่ม

- **Files to Create (แทน §1):** `scripts/validate_work_item.py`, `scripts/qa_report.py`, `tests/test_work_item_validator.py`
- **Files to Modify (แทน "None" ใน §1):** `scripts/validate-contracts.py` (CI gate)
- **Protected Files:** ตามเดิม
- **Verification Commands (เพิ่มจาก §3):**
  - `python3 scripts/validate-contracts.py --check-defaults`
  - `python3 scripts/validate-contracts.py --tasks work/INT-001/tasks.json --test-report work/INT-001/test-report.md`
- **Regression tests ของกติกาที่เพิ่ม** (`tests/test_work_item_validator.py`):
  - `test_mismatched_urd_fs_pair_in_traceability_matrix_fails`
  - `test_covered_pair_on_shared_fs_requires_its_own_test_reference` (ทั้งสองตัวตรวจ)
  - `test_undefined_test_case_in_matrix_and_tasks_is_rejected` (ทั้งสองตัวตรวจ)
  - `test_empty_test_refs_or_missing_tc_or_wrong_fs_mapping_fails`
- **Rollback (แทน §4):** ตาม SPEC-001 A1.6 ห้ามลบไฟล์ตรง ๆ
