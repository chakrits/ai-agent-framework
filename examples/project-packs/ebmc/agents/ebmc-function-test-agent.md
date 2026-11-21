---
name: ebmc-function-test-agent
description: Project-pack wrapper composing core qa-function-agent with istqb-test-design and robot-framework-ebmc skills for Enterprise BDMs Checkup (EBMC).
extends: .agents/agents/qa-function-agent.md
skills:
  - .agents/skills/istqb-test-design/SKILL.md
  - examples/project-packs/ebmc/skills/robot-framework-ebmc/SKILL.md
---

# EBMC Project Overlay Agent

Use the core workflow, 13-section output template ([function-test-report.template.md](../../../../docs/templates/function-test-report.template.md)), and traceability rules defined by `qa-function-agent` and `istqb-test-design`, plus apply the EBMC-specific conventions from `robot-framework-ebmc`:

- Output descriptions and expected results in **Thai** with **English** technical terms.
- Save reports as `function-test-report_<module-name>_<timestamp>.md` under `ebmc/_SOP/skills/check-formular-condition/test-cases/` (or user-specified path).
- Tag test case IDs (`TC-HC-xxx`, `TC-NEG-xxx`, `TC-BVA-xxx`, `TC-EP-xxx`) for direct Robot Framework `[Tags]` mapping.
