---
name: council-pressure-test
description: Single-model multi-lens adversarial decision and review pass (inspired by Karpathy's LLM Council; one model plays opposing lenses, not a multi-model council). Use ONLY for high-stakes tradeoffs, ambiguous requirements, architectural pivots, or blind-spot reviews where being wrong is expensive — never for trivial lookups or routine tasks.
---

# Council Pressure-Test Mindset

## 1. When to Apply (and Skip)
- **"High-stakes" means:** `risk_tier: high`, or a decision the Human flags as costly to reverse. Not a judgment the agent makes alone for routine work.
- **Record the output:** write it under `## Council Pressure-Test` in `REVIEW.md` or `docs/plans/plan-<NNN>-review.md`, under `### Council Pressure-Test` inside the PR/MR `## Review`, or in an ADR (`docs/adr/`), keeping the strongest dissent verbatim, so it can be audited.
- **Use when:** Requirements are ambiguous with multiple options, architectural/schema decisions carry high reversal cost, or high-risk code reviews risk subtle blind spots.
- **Skip when:** A task has a single deterministic answer, routine bug fix, or low-risk docs/config change (respect `dynamic-routing.md`).

## 2. Five Cognitive Lenses (Natural Tensions)
Instead of mimicking job titles, analyze from opposing thinking lenses that challenge each other:
1. **The Contrarian** *(Downside)* — Assume the plan will fail; hunt for fatal flaws, hidden failure modes, and avoided edge cases.
2. **The Expansionist** *(Upside)* — Look for missed leverage, simpler unifying abstractions, or undervalued opportunities (balances Contrarian).
3. **The First Principles Thinker** *(Rethink)* — Strip away legacy assumptions and ask: *"Are we even solving the right problem?"*
4. **The Executor** *(Just Do It)* — Ignore abstract theory; ask *"What is the smallest concrete, shippable first step?"* (balances First Principles).
5. **The Outsider** *(Zero Context)* — Catch the *Curse of Knowledge*: assumptions, jargon, or UX/API gaps obvious to insiders but confusing to newcomers or downstream consumers.

## 3. Core Mechanics for Independent Judgment
- **Anti-Hedging:** Do not soften each angle into safe "on one hand / on the other hand" compromises. Surface each tension sharply first; synthesize later.
- **Neutral Framing:** Present context cleanly without steering toward a preferred option.
- **Blind-Spot Check:** Ask *"What did ALL passes miss?"* before finalizing a recommendation.
- **Non-Majority Verdict:** Never vote blindly by headcount; if 1 dissenting finding exposes a critical risk, side with the stronger reasoning.
- **No "It Depends" Cop-Out:** End with a clear recommendation, explicit trade-offs, and **one concrete next step**.

## 4. SDLC Gate Integration
- **Gate 1 (`ba-po-agent`):** Apply *First Principles* + *The Outsider* on ambiguous `intent.md` drafts before locking `URD-xxx`.
- **Gate 2 (`sa-architect-agent`):** Apply *Contrarian vs. Expansionist* + *Executor* before finalizing high-risk `spec.md` / ADRs.
- **Gate 3 (`code-reviewer-agent`):** Preserve genuine clashes in the review record and ask what both implementation and spec overlooked.
