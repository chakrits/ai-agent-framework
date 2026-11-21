#!/usr/bin/env python3
"""Cross-artifact traceability validator (URD -> FS -> TC -> TASK) for work/INT-xxx directories."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

URD_RE = re.compile(r"\bURD-[0-9]{3,}\b")
FS_RE = re.compile(r"\bFS-[0-9]{3,}\b")
TC_RE = re.compile(r"\b(?:TC-(?:HC|NEG|BVA|EP|API|PERF|SEC)-[0-9]{3,}|EXP-[0-9]{3,})\b")


def extract_ids(pattern: re.Pattern[str], text: str) -> set[str]:
    return set(pattern.findall(text))


def check_intent_to_spec(intent_text: str, spec_text: str) -> list[str]:
    """Verify every URD-xxx defined in intent.md appears in spec.md."""
    intent_urds = extract_ids(URD_RE, intent_text)
    if not intent_urds:
        return ["intent.md does not define any URD-xxx requirements"]
    spec_urds = extract_ids(URD_RE, spec_text)
    missing = sorted(intent_urds - spec_urds)
    return [f"URD-xxx missing from spec.md: {', '.join(missing)}"] if missing else []


def parse_traceability_matrix(report_text: str) -> tuple[dict[str, set[str]], list[str]]:
    """Parse Section 12 Traceability Matrix mapping FS-xxx -> TC-xxx and checking Covered status."""
    idx = report_text.find("## Section 12: Traceability Matrix")
    if idx == -1:
        return {}, ["test-report.md missing '## Section 12: Traceability Matrix'"]
    next_idx = report_text.find("## Section 13:", idx)
    block = report_text[idx : next_idx if next_idx != -1 else len(report_text)]

    fs_to_tcs: dict[str, set[str]] = {}
    errors: list[str] = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("| Requirement") or line.startswith("| :---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        fs_ids = extract_ids(FS_RE, cells[1])
        tc_ids = extract_ids(TC_RE, cells[3])
        status = cells[4].lower()
        if status != "covered":
            errors.append(f"Traceability Matrix row not Covered ({cells[0]} / {cells[1]}): {cells[4]}")
        for fs_id in fs_ids:
            fs_to_tcs.setdefault(fs_id, set()).update(tc_ids)

    if not fs_to_tcs:
        errors.append("Section 12 Traceability Matrix contains no FS-xxx mappings")
    return fs_to_tcs, errors


def check_spec_downstream(spec_text: str, tasks_data: dict[str, Any], report_text: str) -> list[str]:
    """Verify full FS -> TC -> TASK traceability across spec.md, test-report.md, and tasks.json."""
    spec_fs = extract_ids(FS_RE, spec_text)
    if not spec_fs:
        return ["spec.md does not define any FS-xxx functions"]

    fs_to_tcs, errors = parse_traceability_matrix(report_text)
    all_report_tcs = extract_ids(TC_RE, report_text)

    task_fs: set[str] = set()
    fs_to_task_tcs: dict[str, set[str]] = {}
    for idx, task in enumerate(tasks_data.get("tasks", [])):
        if not isinstance(task, dict):
            continue
        tid = str(task.get("task_id") or f"tasks[{idx}]")
        t_fs = [str(fs) for fs in task.get("fs_refs", [])]
        t_tcs = [str(tc) for tc in task.get("test_refs", [])]
        if not t_tcs:
            errors.append(f"{tid} has empty test_refs")
        for tc in t_tcs:
            if tc not in all_report_tcs:
                errors.append(f"{tid} references unknown TC not in test-report.md: {tc}")
            for fs in t_fs:
                allowed = fs_to_tcs.get(fs)
                if allowed is not None and tc not in allowed:
                    errors.append(f"{tid} links {tc} to {fs}, which is not mapped in Section 12 Traceability Matrix")
        task_fs.update(t_fs)
        for fs in t_fs:
            fs_to_task_tcs.setdefault(fs, set()).update(t_tcs)

    missing_in_tasks = sorted(spec_fs - task_fs)
    if missing_in_tasks:
        errors.append(f"FS-xxx missing from tasks.json: {', '.join(missing_in_tasks)}")
    missing_in_report = sorted(spec_fs - set(fs_to_tcs))
    if missing_in_report:
        errors.append(f"FS-xxx missing from test-report.md Section 12: {', '.join(missing_in_report)}")

    for fs_id, expected_tcs in sorted(fs_to_tcs.items()):
        covered_tcs = fs_to_task_tcs.get(fs_id, set())
        missing_tcs = sorted(expected_tcs - covered_tcs)
        if missing_tcs:
            errors.append(f"TC-xxx in test-report.md for {fs_id} missing from tasks.json test_refs: {', '.join(missing_tcs)}")

    return errors


def validate_work_item_dir(work_dir: Path, require_review: bool = False) -> list[str]:
    """Validate artifact presence and cross-artifact URD -> FS -> TC -> TASK traceability in work_dir."""
    if not work_dir.is_dir():
        return [f"Work item directory not found: {work_dir}"]

    required_files = ["intent.md", "spec.md", "test-report.md", "tasks.json"]
    if require_review:
        required_files.append("REVIEW.md")

    errors: list[str] = []
    for fname in required_files:
        if not (work_dir / fname).is_file():
            errors.append(f"Missing required artifact: {fname}")
    if errors:
        return errors

    intent_text = (work_dir / "intent.md").read_text(encoding="utf-8")
    spec_text = (work_dir / "spec.md").read_text(encoding="utf-8")
    report_text = (work_dir / "test-report.md").read_text(encoding="utf-8")
    tasks_data = json.loads((work_dir / "tasks.json").read_text(encoding="utf-8"))

    errors.extend(check_intent_to_spec(intent_text, spec_text))
    errors.extend(check_spec_downstream(spec_text, tasks_data, report_text))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate cross-artifact traceability for a work item directory.")
    parser.add_argument("work_dir", type=Path, help="Path to work/INT-xxx directory")
    parser.add_argument("--require-review", action="store_true", help="Require REVIEW.md presence (Gate 3)")
    args = parser.parse_args(argv)

    errors = validate_work_item_dir(args.work_dir, require_review=args.require_review)
    if errors:
        print("Work item validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Work item validation PASSED ({args.work_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
