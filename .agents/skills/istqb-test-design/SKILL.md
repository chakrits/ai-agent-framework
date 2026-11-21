---
name: istqb-test-design
description: Design comprehensive, measurable QA test suites using Happy Path, Negative, BVA, EP, Exploratory Charters, Risk-based Testing, Traceability Matrix, and Perf/Security fundamentals.
---

# ISTQB Test Design Skill

## Required Test Techniques
1. **Happy Case Scenarios:** Step-by-step main flows mapped directly to `URD-xxx` (`TC-HC-xxx`).
2. **Negative Coverage:** Invalid inputs, missing auth, boundary violations, and deterministic error handling (`TC-NEG-xxx`).
3. **Boundary Value Analysis (BVA):** Test `Min`, `Min-1`, `Min+1`, `Max`, `Max-1`, `Max+1` for every bounded input field (`TC-BVA-xxx`).
4. **Equivalence Partitioning (EP):** Divide inputs into Valid and Invalid partitions with representative samples (`TC-EP-xxx`).
5. **API Test Cases:** Endpoint, method, payload, expected HTTP status, and response assertions (`TC-API-xxx`).
6. **Risk-based Testing:** Score each area using `Likelihood (1-5) x Impact (1-5)` and prioritize mitigating tests (`R-xxx`).
7. **Exploratory Session Charters:** Define Mission, Scope, Time-box, and Focus Area (`EXP-xxx`).
8. **Performance & Security Fundamentals:** Basic response-time/load targets (`TC-PERF-xxx`) and OWASP checks (`TC-SEC-xxx`).
9. **100% Traceability Matrix:** Map every `URD-xxx` -> `FS-xxx` -> `TC-xxx` with zero uncovered requirements.

## Quality Rules
- Every table column must be filled (write `N/A` if not applicable; never leave blanks).
- Expected Results must be concrete and verifiable (e.g., `"HTTP 400 with error code VAL_001"` rather than `"system works"`).
