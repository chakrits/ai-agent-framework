---
intent_id: INT-001
title: "Cross-Artifact Work Item Traceability Validator"
work_type: new_feature
risk_tier: medium
status: approved
owner: human-maintainer
---

# Intent: Cross-Artifact Work Item Traceability Validator

## Header & Context
| Item | Detail |
| :--- | :--- |
| **Intent ID** | `INT-001` |
| **Stakeholders** | PO, BA, SA, Dev, QA, Maintainer |
| **Source Request** | `PLAN-006` WS-E Real E2E Pilot (ROADMAP P6 + P9) |

## Problem Statement & Objective
- **Problem:** `scripts/validate-contracts.py` checks `tasks.json` and `test-report.md` in isolation, so broken `URD-xxx -> FS-xxx -> TASK-xxx` links across a work item directory (`work/INT-xxx/`) go undetected until manual review.
- **Objective:** Provide a single-command validator (`scripts/validate_work_item.py`) that verifies cross-artifact presence and ID traceability across `intent.md`, `spec.md`, `test-report.md`, `tasks.json`, and `REVIEW.md`.

## Business Flow Summary
| # | Flow Type | Flow Name | Description | Pre-condition | Post-condition |
| :-: | :--- | :--- | :--- | :--- | :--- |
| 1 | Main | Validate Work Item | Scan `work/INT-xxx/` artifacts and assert every `URD-xxx` maps to `FS-xxx` and every `FS-xxx` is covered by `tasks.json` and `test-report.md` | Work item directory exists | Exit `0` with coverage summary |
| 2 | Alternative | Report Traceability Gap | Detect missing artifact, broken `URD`/`FS` link, or unapproved gate status | Work item has missing file or orphan ID | Exit `1` with actionable error list |

## Requirements & Acceptance Criteria
| URD ID | Requirement Summary | Measurable Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- |
| `URD-001` | Cross-check `URD-xxx` coverage between `intent.md` and `spec.md` | Every `URD-xxx` in `intent.md` appears in `spec.md`; missing mapping fails with exit code `1` | High |
| `URD-002` | Cross-check `FS-xxx` coverage across `spec.md`, `tasks.json`, and `test-report.md` | Every `FS-xxx` in `spec.md` appears in `tasks.json` (`fs_refs`) and `test-report.md`; missing coverage fails with exit code `1` | High |

## Business Rules & Constraints
| Rule ID | Description | Boundary / Constraint |
| :--- | :--- | :--- |
| `BR-001` | Zero external dependencies | Must run with Python 3.10+ stdlib only across macOS, Linux, and Windows |
| `BR-002` | Deterministic exit codes | Exit `0` only when all required artifacts exist and 100% traceability holds; otherwise exit `1` |

## Out of Scope
- Modifying `intent.md` or `spec.md` automatically during validation (validator is strictly read-only)

## Risks & Open Questions
- [x] Should `REVIEW.md` be optional while a work item is still in Build stage? Yes, support `--require-review` for Gate 3 enforcement while defaulting to checking all core chain artifacts.

## Gate 1 Approval
- **Reviewer:** `human-maintainer (PLAN-006 approved)`
- **Decision:** `Approved`
- **Timestamp:** `2026-11-21`
