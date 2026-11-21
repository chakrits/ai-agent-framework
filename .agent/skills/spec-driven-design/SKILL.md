---
name: spec-driven-design
description: Transform raw product requests or incidents into unambiguous intent.md and spec.md artifacts with IPO Matrix, edge cases, and legacy system linkage.
---

# Spec-Driven Design Skill

## When to Apply
Use during **Stage 1 (Plan)** and **Stage 2 (Design)** before writing any implementation plan or code.

## Core Practices
1. **Eliminate the Ambiguity Tax:** Explicitly interview or flag gaps around permissions, empty states, validation bounds, PII handling, and failure rollbacks.
2. **IPO Decomposition:** Every functional requirement (`URD-xxx`) must decompose into `FS-xxx` entries in an **IPO Matrix** (`Input`, `Process/Logic`, `Expected Output`, `Validation Rules`).
3. **Single Source of Truth for Legacy Tools:**
   - When an organization uses Jira/ServiceNow/Figma alongside Git, declare per artifact whether the **Repo is SoT**, the **Legacy System is SoT**, or **Linkage** (store Ticket ID in `intent.md` and commit SHA in the ticket).
4. **Traceability Invariant:** Every `URD-xxx` must map to at least one `FS-xxx`; orphan specs or untracked requirements must be flagged before Gate 2.
