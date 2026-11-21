---
name: robot-framework-ebmc
description: Domain-specific context, output path conventions, and Robot Framework alignment for Enterprise BDMs Checkup (EBMC) projects.
---

# EBMC Domain & Robot Framework Skill

## Context
- **System:** Enterprise BDMs Checkup (EBMC)
- **Primary Automation Framework:** Robot Framework
- **Target Stakeholders:** PO, BA, SA, Dev, QA/QC

## Output Conventions
- **File Naming:** `function-test-report_<module-name>_<timestamp>.md`
- **Default Output Path:** `ebmc/_SOP/skills/check-formular-condition/test-cases/` (or user-specified path)
- **Language:** Thai for Descriptions and Expected Results; English for Technical Terms.

## Automation Handoff Notes
- Map each `TC-HC-xxx`, `TC-NEG-xxx`, `TC-BVA-xxx`, and `TC-EP-xxx` case cleanly so Robot Framework test suites can reference Test Case IDs as `[Tags]`.
