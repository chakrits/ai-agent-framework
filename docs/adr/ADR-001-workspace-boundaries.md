---
adr_id: ADR-001
title: Framework and target repository boundaries
status: accepted
date: 2026-11-27
work_item: PLAN-010
supersedes: null
---

# ADR-001 · Framework and Target Repository Boundaries

## Context

The framework owns shared SDLC instructions and validators, while the runtime pilot needs an application checkout, a known revision, and verifiable work-item evidence. The [PLAN-010 review](../plans/plan-010-review.md) found that the current orchestrator starts runs at the framework root and uses a dry-run executor.

## Options Considered

| Option | Benefits | Costs |
|---|---|---|
| Use a target repository for the pilot | Keeps application ownership and release in the product repository | Requires a way to reference the target revision and verification |
| Add application directories to the framework repository | Enables cross-component changes in one checkout | Requires runtime selection and scoped CI and release behavior |
| Package the framework for multiple consumers | Allows consumers to pin versions and upgrade independently | Adds release compatibility and installer maintenance |

## Decision

Use a target repository for the first runtime pilot. Keep shared instructions and contracts in the framework repository, domain guidance in project packs, and product source in the target repository. The pilot's own spec will define how to link a checkout and revision to work-item evidence.

## Consequences

- Framework and application releases can proceed independently during the pilot.
- The pilot must show how the reviewer identifies the target checkout and its verification evidence.
- Revisit packaging or a monorepo after the pilot. Supersede this ADR if the boundary later changes.

## Approval

- **Approver (Gate 2, Human SA / Tech Lead):** `@chakrits`
- **Decision:** Accepted. PR comment: “approve ADR-001”
- **Date:** 2026-11-27
- **Evidence Link:** [PR #18 approval comment](https://github.com/chakrits/ai-agent-framework/pull/18#issuecomment-7219540245)
