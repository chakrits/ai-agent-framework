---
spec_id: SPEC-001
intent_ref: INT-001
status: approved
owner: sa-architect-agent
---

# Technical & Functional Specification: Work Item Traceability Validator

## Header & References
| Item | Detail |
| :--- | :--- |
| **Spec ID** | `SPEC-001` |
| **Intent Reference** | `INT-001` |
| **Related ADRs** | `N/A` (additive read-only validator module) |

## Architecture & Component Impact
- **Impacted Modules:** `scripts/validate_work_item.py` (new), `tests/test_work_item_validator.py` (new)
- **Data Flow Summary:** Read `intent.md`, `spec.md`, `test-report.md`, `tasks.json`, and optionally `REVIEW.md` inside `work/<INT-xxx>/` → extract `URD-[0-9]{3,}` and `FS-[0-9]{3,}` sets → validate set inclusion and contract invariants.

## IPO Matrix (Input -> Process -> Output)
| Function ID | Function Name | URD Reference | Input | Process/Logic | Expected Output | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | `check_intent_to_spec` | `URD-001` | `intent_text: str`, `spec_text: str` | Extract unique `URD-xxx` IDs from `intent.md` and `spec.md`; compute `intent_urds - spec_urds` | `list[str]` error messages (empty if covered) | Must contain >= 1 `URD-xxx` in `intent.md`; any uncovered `URD-xxx` yields error |
| `FS-002` | `check_spec_downstream` | `URD-002` | `spec_text: str`, `tasks_data: dict`, `report_text: str` | Extract `FS-xxx` from `spec.md`, `tasks.json` (`fs_refs`), and `test-report.md`; verify `spec_fs <= task_fs` and `spec_fs <= report_fs` | `list[str]` error messages (empty if covered) | Must contain >= 1 `FS-xxx` in `spec.md`; missing `FS-xxx` in tasks or test report yields error |

## API & Data Contracts
- **CLI Interface:** `python3 scripts/validate_work_item.py <work_item_dir> [--require-review]`
  - *Addendum (PLAN-007, 2026-11-22 — outside INT-001 scope, does not change `FS-001`/`FS-002`):* the same script later gained `[--require-digest]` (requires a filled `change-digest.md` in the work item) and `[--digest-file PATH]` (checks a standalone digest; `<work_item_dir>` becomes optional). Both flags are opt-in, so the contract above is unchanged when they are omitted.
- **Exit Codes:** `0` = valid & 100% covered; `1` = missing file or traceability error; `2` = CLI usage error.
- **Database / Migration Impact & Rollback:** `N/A` — pure read-only CLI script; rollback is removing the two new files.

## Security, Privacy & NFR Constraints
- **Path Traversal Guard:** Resolve `<work_item_dir>` cleanly and read files read-only; never execute shell commands from parsed Markdown.
- **Performance Target:** `< 200ms` per work item directory.

## Requirement-to-Spec Mapping
| URD ID | Function ID (`FS-xxx`) | Screen / Endpoint (`SCR-xxx`) | Notes |
| :--- | :--- | :--- | :--- |
| `URD-001` | `FS-001` | `CLI-001` | Covered |
| `URD-002` | `FS-002` | `CLI-001` | Covered |

## Gate 2 Approval
- **Reviewer:** `human-maintainer (PLAN-006 approved)`
- **Decision:** `Approved`
- **Timestamp:** `2026-11-21`
