#!/usr/bin/env python3
"""Deterministic golden eval runner for SDLC agent contracts and assertions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import importlib.util

_spec = importlib.util.spec_from_file_location("validate_contracts", ROOT / "scripts" / "validate-contracts.py")
assert _spec and _spec.loader
validate_contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_contracts)


def evaluate_case(case_path: Path) -> list[str]:
    """Run deterministic structural checks for a single eval dataset file."""
    case: dict[str, Any] = json.loads(case_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    for req in ("eval_id", "title", "target_agent", "prompt", "required_artifacts"):
        if not case.get(req):
            errors.append(f"{case_path.name}: missing required field '{req}'")

    validator = case.get("validator")
    if validator == "tasks_json":
        sample = case.get("sample_output")
        errors.extend(f"{case['eval_id']}: {e}" for e in validate_contracts.validate_tasks_data(sample))
    elif validator == "test_report_markdown":
        schema = json.loads((ROOT / "docs" / "contracts" / "test-report.schema.json").read_text(encoding="utf-8"))
        ref = case.get("sample_output_ref")
        text = (ROOT / ref).read_text(encoding="utf-8") if ref else str(case.get("sample_output", ""))
        errors.extend(f"{case['eval_id']}: {e}" for e in validate_contracts.validate_test_report_markdown(text, schema))

    assertions = case.get("assertions", {})
    if assertions:
        ref = case.get("sample_output_ref")
        text = (ROOT / ref).read_text(encoding="utf-8") if ref else str(case.get("sample_output", ""))
        for marker in assertions.get("required_markers", []):
            if marker not in text:
                errors.append(f"{case['eval_id']}: missing marker '{marker}'")
        for prefix in assertions.get("required_id_prefixes", []):
            if prefix not in text:
                errors.append(f"{case['eval_id']}: missing ID prefix '{prefix}'")

    return errors


def main() -> int:
    dataset_dir = Path(__file__).resolve().parent / "datasets"
    cases = sorted(dataset_dir.glob("*.json"))
    if not cases:
        print("No eval cases found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for case_path in cases:
        all_errors.extend(evaluate_case(case_path))

    if all_errors:
        print("Eval suite FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Eval suite PASSED ({len(cases)}/{len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
