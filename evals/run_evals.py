#!/usr/bin/env python3
"""Dual-mode SDLC eval runner: deterministic contract evals (PR) and isolated live CLI evals."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("validate_contracts", ROOT / "scripts" / "validate-contracts.py")
assert _spec and _spec.loader
validate_contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_contracts)

PROTECTED_SANDBOX_PREFIXES = (
    "tests/",
    "docs/contracts/",
    "docs/operating-model/constitution.md",
)


def build_harness_command(harness: str, max_budget: float) -> list[str]:
    """Return sandboxed, budget-capped CLI invocation prefix for the selected harness."""
    if harness == "claude":
        return ["claude", "-p", "--permission-mode", "plan", "--max-budget-usd", f"{max_budget:.2f}"]
    if harness == "codex":
        return ["codex", "exec", "--sandbox", "workspace-write"]
    if harness == "antigravity":
        return ["agy", "-p"]
    raise ValueError(f"Unsupported harness: {harness}")


def grade_output(case: dict[str, Any], text: str, parsed_json: Any = None) -> list[str]:
    """Deterministically grade agent output against contract schemas and case assertions."""
    errors: list[str] = []
    eval_id = case["eval_id"]
    validator = case.get("validator")

    if validator == "tasks_json":
        obj = parsed_json
        if obj is None:
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                return [f"{eval_id}: output is not valid JSON for tasks_json ({exc})"]
        errors.extend(f"{eval_id}: {e}" for e in validate_contracts.validate_tasks_data(obj))
    elif validator == "test_report_markdown":
        schema = json.loads((ROOT / "docs" / "contracts" / "test-report.schema.json").read_text(encoding="utf-8"))
        errors.extend(f"{eval_id}: {e}" for e in validate_contracts.validate_test_report_markdown(text, schema))

    assertions = case.get("assertions", {})
    for marker in assertions.get("required_markers", []):
        if marker not in text:
            errors.append(f"{eval_id}: missing marker '{marker}'")
    for prefix in assertions.get("required_id_prefixes", []):
        if prefix not in text:
            errors.append(f"{eval_id}: missing ID prefix '{prefix}'")
    for forbidden in assertions.get("forbidden_markers", []):
        if forbidden in text:
            errors.append(f"{eval_id}: forbidden marker present '{forbidden}'")

    return errors


def _init_sandbox_git(sandbox: Path) -> None:
    subprocess.run(["git", "init", "-b", "main", str(sandbox)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(sandbox), "config", "user.email", "eval@example.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(sandbox), "config", "user.name", "Eval Sandbox"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(sandbox), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(sandbox), "commit", "-m", "chore: eval baseline"], check=True, capture_output=True)


def _check_sandbox_diff(sandbox: Path, eval_id: str) -> list[str]:
    res = subprocess.run(
        ["git", "-C", str(sandbox), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    errors: list[str] = []
    for line in res.stdout.splitlines():
        if len(line) < 4:
            continue
        rel = line[3:].strip().replace("\\", "/")
        if any(rel.startswith(prefix) or "test-report" in rel for prefix in PROTECTED_SANDBOX_PREFIXES):
            errors.append(f"{eval_id}: agent modified protected/oracle file in sandbox: {rel}")
    return errors


def evaluate_contract_case(case_path: Path) -> list[str]:
    """Run deterministic structural checks against the case's sample output."""
    case: dict[str, Any] = json.loads(case_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for req in ("eval_id", "title", "target_agent", "prompt", "required_artifacts"):
        if not case.get(req):
            errors.append(f"{case_path.name}: missing required field '{req}'")
    if errors:
        return errors

    ref = case.get("sample_output_ref")
    raw_sample = (ROOT / ref).read_text(encoding="utf-8") if ref else case.get("sample_output", "")
    text = raw_sample if isinstance(raw_sample, str) else json.dumps(raw_sample, ensure_ascii=False)
    parsed = raw_sample if isinstance(raw_sample, dict) else None
    return grade_output(case, text, parsed_json=parsed)


def evaluate_live_case(
    case_path: Path,
    command_prefix: list[str],
    timeout_seconds: int = 120,
    max_budget: float = 2.0,
) -> list[str]:
    """Run an agent CLI inside an isolated git-tracked temp copy with SDLC_TRACE_DIR redirected."""
    case: dict[str, Any] = json.loads(case_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        sandbox = tmp_root / "workspace"
        sandbox.mkdir()
        for folder in (".agents", "docs"):
            src = ROOT / folder
            if src.exists():
                shutil.copytree(src, sandbox / folder)
        shutil.copy2(ROOT / "AGENTS.md", sandbox / "AGENTS.md")
        (sandbox / "tests").mkdir(exist_ok=True)
        (sandbox / "tests" / "test_oracle.py").write_text("# protected QA oracle\n", encoding="utf-8")
        _init_sandbox_git(sandbox)

        env = dict(os.environ)
        env["SDLC_TRACE_DIR"] = str(tmp_root / "isolated-traces")
        env["SDLC_EVAL_MODE"] = "live"
        env["SDLC_EVAL_MAX_BUDGET_USD"] = f"{max_budget:.2f}"

        prompt = f"Active role: {case['target_agent']}.\n{case['prompt']}"
        proc = subprocess.run(
            [*command_prefix, prompt],
            cwd=str(sandbox),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            return [f"{case['eval_id']}: live command exited with {proc.returncode}: {proc.stderr.strip()}"]
        errors = _check_sandbox_diff(sandbox, case["eval_id"])
        errors.extend(grade_output(case, proc.stdout))
        return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SDLC framework evals.")
    parser.add_argument("--mode", choices=("contract", "live"), default="contract")
    parser.add_argument("--harness", choices=("claude", "codex", "antigravity"), default="claude")
    parser.add_argument("--live-cmd", nargs="+", help="Custom command prefix overriding --harness in live mode.")
    parser.add_argument("--limit", type=int, default=0, help="Max eval cases to run (0 = all).")
    parser.add_argument("--max-budget", type=float, default=2.0, help="Max USD budget per case in live mode.")
    parser.add_argument("--timeout", type=int, default=120, help="Per-case timeout in live mode.")
    args = parser.parse_args(argv)

    if args.max_budget <= 0:
        parser.error("--max-budget must be > 0")

    dataset_dir = Path(__file__).resolve().parent / "datasets"
    cases = sorted(dataset_dir.glob("*.json"))
    if args.limit > 0:
        cases = cases[: args.limit]
    if not cases:
        print("No eval cases found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    cmd_prefix = args.live_cmd or build_harness_command(args.harness, args.max_budget)
    for case_path in cases:
        if args.mode == "contract":
            all_errors.extend(evaluate_contract_case(case_path))
        else:
            all_errors.extend(
                evaluate_live_case(
                    case_path,
                    cmd_prefix,
                    timeout_seconds=args.timeout,
                    max_budget=args.max_budget,
                )
            )

    if all_errors:
        print(f"Eval suite ({args.mode}) FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Eval suite ({args.mode}) PASSED ({len(cases)}/{len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
