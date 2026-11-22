#!/usr/bin/env python3
"""Deterministic contract validator for SDLC artifacts (tasks.json and test reports)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from qa_report import TEST_CASE_ID_RE, defined_test_case_ids, table_cells

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "contracts"

TASK_ID_RE = re.compile(r"^TASK-[0-9]{3,}$")
INTENT_ID_RE = re.compile(r"^INT-[0-9]{3,}$")
SPEC_ID_RE = re.compile(r"^SPEC-[0-9]{3,}$")
FS_ID_RE = re.compile(r"^FS-[0-9]{3,}$")
TEST_REF_RE = re.compile(r"^(TC-(HC|NEG|BVA|EP|API|PERF|SEC)-[0-9]{3,}|EXP-[0-9]{3,}|UNIT-[0-9]{3,})$")


def validate_tasks_data(data: Any) -> list[str]:
    """Validate a tasks.json object against tasks.schema.json core invariants."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["tasks.json root must be a JSON object"]

    for field in ("intent_ref", "spec_ref", "tasks"):
        if field not in data:
            errors.append(f"Missing required root field: {field}")

    if "intent_ref" in data and not INTENT_ID_RE.match(str(data["intent_ref"])):
        errors.append(f"Invalid intent_ref format: {data['intent_ref']!r}")
    if "spec_ref" in data and not SPEC_ID_RE.match(str(data["spec_ref"])):
        errors.append(f"Invalid spec_ref format: {data['spec_ref']!r}")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty list")
        return errors

    for idx, task in enumerate(tasks):
        prefix = f"tasks[{idx}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for req in ("task_id", "title", "fs_refs", "test_refs", "status", "passes", "verification_cmd"):
            if req not in task:
                errors.append(f"{prefix} missing required field: {req}")

        if "task_id" in task and not TASK_ID_RE.match(str(task["task_id"])):
            errors.append(f"{prefix}.task_id invalid: {task['task_id']!r}")
        if task.get("status") not in {"pending", "in_progress", "blocked", "completed"}:
            errors.append(f"{prefix}.status invalid: {task.get('status')!r}")
        if not isinstance(task.get("passes"), bool):
            errors.append(f"{prefix}.passes must be a boolean")
        if task.get("passes") is True and not str(task.get("evidence", "")).strip():
            errors.append(f"{prefix}.passes is true but evidence is empty")

        for fs_ref in task.get("fs_refs", []):
            if not FS_ID_RE.match(str(fs_ref)):
                errors.append(f"{prefix}.fs_refs invalid ID: {fs_ref!r}")
        for test_ref in task.get("test_refs", []):
            if not TEST_REF_RE.match(str(test_ref)):
                errors.append(f"{prefix}.test_refs invalid ID: {test_ref!r}")

    return errors


def validate_test_report_markdown(text: str, schema: dict[str, Any]) -> list[str]:
    """Validate a QA Function Test Report Markdown file against test-report.schema.json."""
    errors: list[str] = []
    required_sections = schema["properties"]["required_sections"]["const"]

    last_pos = -1
    for section in required_sections:
        marker = f"## {section}"
        pos = text.find(marker)
        if pos == -1:
            errors.append(f"Missing required section heading: '{marker}'")
            continue
        if pos < last_pos:
            errors.append(f"Section out of order: '{marker}'")
        last_pos = pos

    trace_section_idx = text.find("## Section 12: Traceability Matrix")
    if trace_section_idx != -1:
        next_section_idx = text.find("## Section 13:", trace_section_idx)
        trace_block = text[trace_section_idx : next_section_idx if next_section_idx != -1 else len(text)]
        if "| Gap |" in trace_block or "| gap |" in trace_block:
            errors.append("Traceability Matrix contains uncovered 'Gap' entries")
        if not re.search(r"URD-[0-9]{3,}", trace_block):
            errors.append("Traceability Matrix must reference at least one URD-xxx ID")
        defined_ids = defined_test_case_ids(text)
        for line in trace_block.splitlines():
            cells = table_cells(line)
            if len(cells) < 5 or cells[4].casefold() not in {"covered", "partial", "gap"}:
                continue
            test_refs = set(TEST_CASE_ID_RE.findall(cells[3]))
            if cells[4].casefold() == "covered" and not test_refs:
                errors.append(f"Covered Traceability Matrix row ({cells[0]} / {cells[1]}) requires a test case ID")
            for tc in sorted(test_refs - defined_ids):
                errors.append(f"Traceability Matrix row ({cells[0]} / {cells[1]}) references undefined test case ID: {tc}")

    return errors


def check_defaults() -> list[str]:
    """Verify repository schemas and templates parse cleanly and satisfy invariants."""
    errors: list[str] = []
    for json_path in sorted(CONTRACTS.glob("*.json")):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {json_path.relative_to(ROOT)}: {exc}")

    tasks_tpl_path = ROOT / "docs" / "templates" / "tasks.template.json"
    tasks_tpl = json.loads(tasks_tpl_path.read_text(encoding="utf-8"))
    for err in validate_tasks_data(tasks_tpl):
        errors.append(f"{tasks_tpl_path.relative_to(ROOT)}: {err}")

    report_schema = json.loads((CONTRACTS / "test-report.schema.json").read_text(encoding="utf-8"))
    report_tpl_path = ROOT / "docs" / "templates" / "function-test-report.template.md"
    report_tpl = report_tpl_path.read_text(encoding="utf-8")
    for err in validate_test_report_markdown(report_tpl, report_schema):
        errors.append(f"{report_tpl_path.relative_to(ROOT)}: {err}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SDLC contract artifacts.")
    parser.add_argument("--check-defaults", action="store_true", help="Validate repository contracts and templates.")
    parser.add_argument("--tasks", type=Path, help="Path to a tasks.json file to validate.")
    parser.add_argument("--test-report", type=Path, help="Path to a function-test-report Markdown file.")
    args = parser.parse_args()

    if not any((args.check_defaults, args.tasks, args.test_report)):
        parser.error("Provide at least one of --check-defaults, --tasks, or --test-report")

    errors: list[str] = []
    if args.check_defaults:
        errors.extend(check_defaults())
    if args.tasks:
        data = json.loads(args.tasks.read_text(encoding="utf-8"))
        errors.extend(f"{args.tasks}: {e}" for e in validate_tasks_data(data))
    if args.test_report:
        schema = json.loads((CONTRACTS / "test-report.schema.json").read_text(encoding="utf-8"))
        text = args.test_report.read_text(encoding="utf-8")
        errors.extend(f"{args.test_report}: {e}" for e in validate_test_report_markdown(text, schema))

    if errors:
        print("Contract validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
