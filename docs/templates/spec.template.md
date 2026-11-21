---
spec_id: SPEC-001
intent_ref: INT-001
status: draft
owner: "[SA / Tech Lead Name]"
---

# Technical & Functional Specification: [Feature / Module Name]

## Header & References
| Item | Detail |
| :--- | :--- |
| **Spec ID** | `SPEC-001` |
| **Intent Reference** | `INT-001` |
| **Related ADRs** | `ADR-001` (or `N/A`) |

## Architecture & Component Impact
- **Impacted Modules:** `[module/service paths]`
- **Data Flow Summary:** [Brief end-to-end flow or Mermaid diagram]

## IPO Matrix (Input -> Process -> Output)
| Function ID | Function Name | URD Reference | Input | Process/Logic | Expected Output | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | [Function name] | `URD-001` | [Typed params / fields] | [Deterministic logic] | [Success & error outputs] | [Min/Max, format, nullability, auth] |

## API & Data Contracts
- **Endpoints / Interfaces:** `[METHOD /api/v1/...]`
- **Request / Response Schema:** [Exact field types & status codes]
- **Database / Migration Impact & Rollback:** [Schema diff + rollback steps, or `N/A`]

## Security, Privacy & NFR Constraints
- **AuthN / AuthZ:** [Role/permission checks]
- **Input Validation & OWASP Controls:** [Sanitization, rate limit, injection prevention]
- **Performance Targets:** [e.g., p95 latency < 300ms]

## Requirement-to-Spec Mapping
| URD ID | Function ID (`FS-xxx`) | Screen / Endpoint (`SCR-xxx`) | Notes |
| :--- | :--- | :--- | :--- |
| `URD-001` | `FS-001` | `SCR-001` | Covered |

## Gate 2 Approval
- **Reviewer:** `[SA / Tech Lead Name]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`
