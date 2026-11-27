# EBMC Project Pack (Example Domain Overlay)

This directory demonstrates how to keep the **SDLC Agent Framework Core** enterprise-agnostic while plugging in project-specific domain knowledge.

## Origin
Historical source for this pack: [function-test-agent.md](../../../docs/reference-architecture/04.%20Agent%20Workflows/Testing%20Agents/function-test-agent.md).

## Contents
- `skills/robot-framework-ebmc/SKILL.md` — Domain context for **Enterprise BDMs Checkup (EBMC)**, Robot Framework automation conventions, and EBMC output path rules (`ebmc/_SOP/...`).

## How to Use
When running the core `qa-function-agent` on an EBMC project, load this project pack alongside the generic `istqb-test-design` skill.
