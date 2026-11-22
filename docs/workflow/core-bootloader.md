# Core Bootloader

> Read this file first at the start of any SDLC task to classify the work and load **only** the policies and roles needed.

## Step 1: Classify the Task

Determine the **Work Type** and **Risk Tier**:

| Work Type | Examples | Risk Tier (Typical) |
| :--- | :--- | :--- |
| **New Feature** | New endpoint, UI flow, business rule, module | Medium / High |
| **Bug Fix** | Defect reproduction, hotfix, regression fix | Low / Medium / High |
| **API / Schema Change** | Breaking contract change, DB migration, auth change | High |
| **Config / Data Change** | Env config, feature flag, reference data update | Low / Medium |
| **Test-Only / Docs-Only** | Adding Robot/unit tests, updating README/SOP | Low |
| **Framework / Process Change** | Editing `AGENTS.md`, `.agents/`, `docs/contracts/`, CI gates | High |

## Step 2: Select Route

Map Risk Tier to governance Tier (Standard vs High-Risk) with the table in [constitution.md §1](../operating-model/constitution.md), then follow [dynamic-routing.md](dynamic-routing.md) for the exact stage sequence, required artifacts, and HITL gates.

## Step 3: Load Context Economically

1. Load `docs/operating-model/constitution.md` (always).
2. Load only the active stage's **Agent Role** from `.agents/agents/`.
3. Load only relevant **Skills** from `.agents/skills/` (and active Project Pack if applicable).
4. Load the target **Template** from `docs/templates/`.
