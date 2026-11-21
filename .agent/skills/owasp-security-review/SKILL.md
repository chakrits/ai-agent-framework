---
name: owasp-security-review
description: Audit specs, API contracts, and code diffs for AuthN/AuthZ gaps, injection risks, secret/PII exposure, and sandbox/permission boundaries.
---

# OWASP Security Review Skill

## Audit Checklist
1. **Authentication & Authorization (A01/A07):** Every non-health endpoint enforces AuthN and explicit role/ownership checks (deny by default).
2. **Input Validation & Injection (A03):** Validate against strict schemas, reject unknown fields, use parameterized queries, and sanitize outputs.
3. **Secrets & PII Hygiene (A02/A09):** Zero hardcoded keys/tokens in code or fixtures; PII-tagged fields must never appear in logs or error payloads.
4. **External Integrations & Agent Safety:** Restrict outbound network domains, prevent SSRF/command injection, and ensure CI/agent tokens follow least privilege.
5. **Severity Classification:** Tag Critical/High vulnerabilities as **Gate 3 Blockers**; never auto-waive without explicit human security sign-off.
