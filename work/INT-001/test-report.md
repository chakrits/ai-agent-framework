---
report_id: QAR-001
intent_ref: INT-001
spec_ref: SPEC-001
status: approved
owner: qa-function-agent
---

# Function Test Report

## Section 1: Header Information
| Item | Detail |
| :--- | :--- |
| **Report ID** | `QAR-001` |
| **Project / Module** | `AI-Native SDLC Framework / Work Item Validator (INT-001)` |
| **Document Version** | `1.0` |
| **Created By** | `qa-function-agent` |
| **Created Date** | `2026-11-21` |
| **Reference Documents** | `INT-001`, `SPEC-001` |

## Section 2: Scope & Objectives
Verify cross-artifact traceability enforcement across `intent.md`, `spec.md`, `tasks.json`, `test-report.md`, and `REVIEW.md` for `FS-001` and `FS-002`.

## Section 3: IPO Matrix (Input -> Process -> Output)
| Function ID | Function Name | Input | Process/Logic | Expected Output | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | `check_intent_to_spec` | `intent.md`, `spec.md` | Compare `URD-xxx` sets | Empty error list or missing URD errors | Non-empty `URD-xxx` set in intent |
| `FS-002` | `check_spec_downstream` | `spec.md`, `tasks.json`, `test-report.md` | Compare `FS-xxx` sets | Empty error list or missing FS errors | Non-empty `FS-xxx` set in spec |

## Section 4: High-Level Scenario (Happy Case Flow)
Run `validate_work_item.py` against a complete work item directory where all `URD-xxx` and `FS-xxx` IDs match across all artifacts and confirm exit code `0`.

## Section 5: Happy Case Test Scenarios (Detailed Level)
| Test Case ID | Test Case Name | Description | Pre-condition | Test Steps | Test Data | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-HC-001` | Valid Complete Work Item | Verify `INT-001` directory passes all checks | All 5 artifacts exist with matching IDs | 1. Run `python3 scripts/validate_work_item.py <dir> --require-review` | `INT-001` valid bundle | Exit code `0` and stdout `Work item validation PASSED` | High |

## Section 6: Test Case Design (Happy Case + Negative Case)
| Test Case ID | Test Case Name | Test Type | Description | Pre-condition | Test Steps | Test Data | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-HC-001` | Valid Complete Work Item | Happy | All URD/FS IDs aligned | Valid `work/INT-001` | 1. Run CLI | Complete bundle | Exit `0` | High |
| `TC-NEG-001` | Missing URD in Spec | Negative | Detect `URD-002` omitted from `spec.md` | `URD-002` in `intent.md` only | 1. Run CLI | `spec.md` without `URD-002` | Exit `1` with error mentioning `URD-002` | High |
| `TC-NEG-002` | Missing FS in Tasks | Negative | Detect `FS-002` omitted from `tasks.json` | `FS-002` in `spec.md` only | 1. Run CLI | `tasks.json` with `FS-001` only | Exit `1` with error mentioning `FS-002` | High |

## Section 7: Negative Test Coverage
| Test Case ID | Test Case Name | Description | Invalid Input / Condition | Expected Result (Error Handling) | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-NEG-001` | Unmapped URD | `intent.md` defines `URD-002` missing in `spec.md` | Missing `URD-002` | Exit `1`, stderr lists uncovered `URD-002` | High |
| `TC-NEG-002` | Unimplemented FS | `spec.md` defines `FS-002` missing in `tasks.json` | Missing `FS-002` in `fs_refs` | Exit `1`, stderr lists uncovered `FS-002` | High |
| `TC-NEG-003` | Missing Artifact File | Directory lacks `spec.md` or `REVIEW.md` with `--require-review` | Absent `REVIEW.md` | Exit `1`, stderr lists missing file `REVIEW.md` | High |

## Section 8: BVA / EP
### Boundary Value Analysis
| Field Name | Min | Min-1 | Min+1 | Max | Max-1 | Max+1 | Test Case IDs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `URD-xxx` count in `intent.md` | `1` | `0` (invalid) | `2` | `N/A` | `N/A` | `N/A` | `TC-BVA-001` |
| `FS-xxx` count in `spec.md` | `1` | `0` (invalid) | `2` | `N/A` | `N/A` | `N/A` | `TC-BVA-002` |

### Equivalence Partitioning
| Field Name | Valid Partitions | Invalid Partitions | Test Case IDs |
| :--- | :--- | :--- | :--- |
| ID Pattern | `URD-001`, `FS-001`, `URD-1000` | `URD-1`, `FS-abc`, empty | `TC-EP-001` |

## Section 9: API Test Case
| Test Case ID | API Endpoint | Method | Request Body | Expected Status | Expected Response | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-API-001` | `N/A — CLI tool only` | `N/A` | `N/A` | `N/A` | `N/A` | Low |

## Section 10: Risk-based Testing
| Risk ID | Function/Area | Risk Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Priority | Mitigation Test Cases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `R-001` | `FS-001` / `FS-002` | False-positive pass when `tasks.json` or `intent.md` has 0 IDs | 3 | 4 | 12 | High | `TC-BVA-001`, `TC-BVA-002`, `TC-NEG-001` |

## Section 11: Exploratory Session Charter
| Charter ID | Mission | Scope | Time-box | Focus Area | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `EXP-001` | Probe malformed Markdown headings and partial IDs (e.g., `URD-12`) | `scripts/validate_work_item.py` | 30 min | Regex boundary & missing files | Ensure clean non-zero exit |

## Section 12: Traceability Matrix
| Requirement ID | FS Reference | SCR Reference | Test Case IDs | Status |
| :--- | :--- | :--- | :--- | :--- |
| `URD-001` | `FS-001` | `CLI-001` | `TC-HC-001`, `TC-NEG-001`, `TC-BVA-001`, `TC-EP-001` | Covered |
| `URD-002` | `FS-002` | `CLI-001` | `TC-HC-001`, `TC-NEG-002`, `TC-NEG-003`, `TC-BVA-002` | Covered |

## Section 13: Performance & Security Test Fundamentals
### Performance Test Cases
| Test Case ID | Test Scenario | Test Type | Target Metric | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-PERF-001` | Validate single work item directory | Latency | Execution time | `< 200 ms` | Low |

### Security Test Cases
| Test Case ID | Test Scenario | OWASP Category | Test Method | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-SEC-001` | Malicious shell syntax inside `intent.md` | A03:2021 | Pass Markdown with `$(whoami)` to validator | Pure text parsing; zero command execution | High |
