#!/usr/bin/env python3
"""Cross-artifact traceability validator (URD <-> FS <-> TC <-> TASK) for work/INT-xxx directories."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from qa_report import TEST_CASE_ID_RE, defined_test_case_ids, table_cells

URD_RE = re.compile(r"\bURD-[0-9]{3,}\b")
FS_RE = re.compile(r"\bFS-[0-9]{3,}\b")


def extract_ids(pattern: re.Pattern[str], text: str) -> set[str]:
    return set(pattern.findall(text))


def check_intent_to_spec(intent_text: str, spec_text: str) -> list[str]:
    """Verify every intent URD has a function in the canonical mapping."""
    intent_urds = extract_ids(URD_RE, intent_text)
    if not intent_urds:
        return ["intent.md does not define any URD-xxx requirements"]
    mapped_urds = {urd for urd, _ in parse_spec_urd_fs_pairs(spec_text)}
    missing = sorted(intent_urds - mapped_urds)
    if missing:
        return [f"URD-xxx without an FS mapping in spec.md: {', '.join(missing)}"]
    return []


def parse_spec_urd_fs_pairs(spec_text: str) -> set[tuple[str, str]]:
    """Read URD and FS IDs from the first two columns of the canonical table."""
    mapping = re.search(r"^##[ \t]+Requirement-to-Spec Mapping[ \t]*\r?$", spec_text, re.MULTILINE)
    if not mapping:
        return set()

    pairs: set[tuple[str, str]] = set()
    for raw in spec_text[mapping.end():].lstrip().splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            break
        cells = line[1:].removesuffix("|").split("|")
        if len(cells) < 2:
            continue
        urds = extract_ids(URD_RE, cells[0])
        fss = extract_ids(FS_RE, cells[1])
        for u in urds:
            for f in fss:
                pairs.add((u, f))
    return pairs


def parse_traceability_matrix(
    report_text: str,
    defined_ids: set[str],
) -> tuple[dict[str, set[str]], set[tuple[str, str]], list[str]]:
    """Parse Section 12 Traceability Matrix mapping FS-xxx -> TC-xxx, (URD, FS) pairs, and Covered status."""
    idx = report_text.find("## Section 12: Traceability Matrix")
    if idx == -1:
        return {}, set(), ["test-report.md missing '## Section 12: Traceability Matrix'"]
    next_idx = report_text.find("## Section 13:", idx)
    block = report_text[idx : next_idx if next_idx != -1 else len(report_text)]

    fs_to_tcs: dict[str, set[str]] = {}
    urd_fs_pairs: set[tuple[str, str]] = set()
    errors: list[str] = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("| Requirement") or line.startswith("| :---"):
            continue
        cells = table_cells(line)
        if len(cells) < 5:
            continue
        urd_ids = extract_ids(URD_RE, cells[0])
        fs_ids = extract_ids(FS_RE, cells[1])
        tc_ids = extract_ids(TEST_CASE_ID_RE, cells[3])
        status = cells[4].lower()
        if not urd_ids:
            errors.append(f"Traceability Matrix row missing URD-xxx in column 1: {line}")
        if status != "covered":
            errors.append(f"Traceability Matrix row not Covered ({cells[0]} / {cells[1]}): {cells[4]}")
        elif not tc_ids:
            errors.append(f"Covered Traceability Matrix row ({cells[0]} / {cells[1]}) requires a test case ID")
        for tc in sorted(tc_ids - defined_ids):
            errors.append(f"Traceability Matrix row ({cells[0]} / {cells[1]}) references undefined test case ID: {tc}")
        for u in urd_ids:
            for f in fs_ids:
                urd_fs_pairs.add((u, f))
        for fs_id in fs_ids:
            fs_to_tcs.setdefault(fs_id, set()).update(tc_ids)

    if not fs_to_tcs:
        errors.append("Section 12 Traceability Matrix contains no FS-xxx mappings")
    return fs_to_tcs, urd_fs_pairs, errors


def check_spec_downstream(spec_text: str, tasks_data: dict[str, Any], report_text: str) -> list[str]:
    """Verify full URD <-> FS -> TC -> TASK traceability across spec.md, test-report.md, and tasks.json."""
    spec_fs = extract_ids(FS_RE, spec_text)
    if not spec_fs:
        return ["spec.md does not define any FS-xxx functions"]

    spec_pairs = parse_spec_urd_fs_pairs(spec_text)
    all_report_tcs = defined_test_case_ids(report_text)
    fs_to_tcs, report_pairs, errors = parse_traceability_matrix(report_text, all_report_tcs)

    if not spec_pairs:
        errors.append("spec.md Requirement-to-Spec Mapping contains no URD/FS pairs")
    missing_pairs = sorted(spec_pairs - report_pairs)
    extra_pairs = sorted(report_pairs - spec_pairs)
    if missing_pairs:
        formatted = ", ".join(f"{u}->{f}" for u, f in missing_pairs)
        errors.append(f"(URD, FS) pairs in spec.md missing from test-report.md Section 12: {formatted}")
    if extra_pairs:
        formatted = ", ".join(f"{u}->{f}" for u, f in extra_pairs)
        errors.append(f"(URD, FS) pairs in test-report.md Section 12 do not match spec.md: {formatted}")

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
                errors.append(f"{tid} references undefined test case ID in test-report.md: {tc}")
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
    """Validate artifact presence and cross-artifact URD <-> FS -> TC -> TASK traceability in work_dir."""
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
