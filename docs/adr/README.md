# Architecture Decision Records (ADR)

Durable architectural or security trade-offs are recorded here before closeout (see [AGENTS.md](../../AGENTS.md) §5 and §7).

- **Naming:** `ADR-<NNN>-<slug>.md` (`<NNN>` = next unused number, zero-padded).
- **Template:** [adr.template.md](../templates/adr.template.md).
- **When to write one:** a decision that is costly to reverse, changes a contract/gate/guardrail, or resolves a high-stakes tradeoff (e.g., after a `council-pressure-test`).
- **Lifecycle:** `proposed` → `accepted` (Human approval at Gate 2) → optionally `superseded by ADR-xxx`. Never rewrite an accepted ADR; supersede it.
- **Recording approval:** fill the ADR's `## Approval` section (approver, decision, date, evidence link) and set the front-matter `status: accepted` in the same commit. An ADR without an evidence link is still `proposed`.
- **Index:** list every ADR below in numeric order.

| ADR | Title | Status | Approver / Date |
| :--- | :--- | :--- | :--- |
| [ADR-001](ADR-001-workspace-boundaries.md) | Framework and target repository boundaries | Accepted | `@chakrits` / 2026-11-27 |
