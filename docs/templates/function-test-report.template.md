---
report_id: QAR-001
intent_ref: INT-001
spec_ref: SPEC-001
status: draft
owner: qa-function-agent
---

# Function Test Report

## Section 1: Header Information
| Item | Detail |
| :--- | :--- |
| **Report ID** | `QAR-001` |
| **Project / Module** | `[Project / Module Name]` |
| **Document Version** | `1.0` |
| **Created By** | `qa-function-agent` |
| **Created Date** | `YYYY-MM-DD` |
| **Reference Documents** | `INT-001`, `SPEC-001` |

## Section 2: Scope & Objectives
[Summarize test scope, in-scope functions, and test objectives.]

## Section 3: IPO Matrix (Input -> Process -> Output)
| Function ID | Function Name | Input | Process/Logic | Expected Output | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | ... | ... | ... | ... | ... |

## Section 4: High-Level Scenario (Happy Case Flow)
[Overview of main end-to-end happy flows.]

## Section 5: Happy Case Test Scenarios (Detailed Level)
| Test Case ID | Test Case Name | Description | Pre-condition | Test Steps | Test Data | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-HC-001` | ... | ... | ... | 1. ... 2. ... | ... | ... | High |

## Section 6: Test Case Design (Happy Case + Negative Case)
| Test Case ID | Test Case Name | Test Type | Description | Pre-condition | Test Steps | Test Data | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-HC-001` | ... | Happy | ... | ... | 1. ... | ... | ... | High |
| `TC-NEG-001` | ... | Negative | ... | ... | 1. ... | ... | ... | High |

## Section 7: Negative Test Coverage
| Test Case ID | Test Case Name | Description | Invalid Input / Condition | Expected Result (Error Handling) | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-NEG-001` | ... | ... | ... | ... | High |

## Section 8: BVA / EP
### Boundary Value Analysis
| Field Name | Min | Min-1 | Min+1 | Max | Max-1 | Max+1 | Test Case IDs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ... | ... | ... | ... | ... | ... | ... | `TC-BVA-001` |

### Equivalence Partitioning
| Field Name | Valid Partitions | Invalid Partitions | Test Case IDs |
| :--- | :--- | :--- | :--- |
| ... | ... | ... | `TC-EP-001` |

## Section 9: API Test Case
| Test Case ID | API Endpoint | Method | Request Body | Expected Status | Expected Response | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-API-001` | `/api/v1/...` | `POST` | `{...}` | `200` | `{...}` | High |

## Section 10: Risk-based Testing
| Risk ID | Function/Area | Risk Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Priority | Mitigation Test Cases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `R-001` | ... | ... | 3 | 4 | 12 | High | `TC-HC-001`, `TC-NEG-001` |

## Section 11: Exploratory Session Charter
| Charter ID | Mission | Scope | Time-box | Focus Area | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `EXP-001` | ... | ... | 60 min | ... | ... |

## Section 12: Traceability Matrix
| Requirement ID | FS Reference | SCR Reference | Test Case IDs | Status |
| :--- | :--- | :--- | :--- | :--- |
| `URD-001` | `FS-001` | `SCR-001` | `TC-HC-001`, `TC-NEG-001` | Covered |

## Section 13: Performance & Security Test Fundamentals
### Performance Test Cases
| Test Case ID | Test Scenario | Test Type | Target Metric | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-PERF-001` | ... | Load Test | Response Time | `< 3 sec` | Medium |

### Security Test Cases
| Test Case ID | Test Scenario | OWASP Category | Test Method | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-SEC-001` | Input Injection | A03:2021 | ... | Input rejected cleanly | High |
