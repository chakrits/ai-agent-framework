"""Unit tests for scripts/validate_work_item.py (INT-001 pilot implementation)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_work_item  # noqa: E402


class TestWorkItemValidator(unittest.TestCase):
    def test_real_pilot_int_001_passes(self) -> None:
        errors = validate_work_item.validate_work_item_dir(ROOT / "work" / "INT-001", require_review=True)
        self.assertEqual(errors, [])

    def test_missing_urd_in_spec_fails(self) -> None:
        errors = validate_work_item.check_intent_to_spec("URD-001\nURD-002\n", "URD-001 only")
        self.assertTrue(any("URD-002" in e for e in errors))

    def test_zero_urds_in_intent_fails(self) -> None:
        errors = validate_work_item.check_intent_to_spec("no ids here", "URD-001")
        self.assertTrue(errors)

    def test_cli_requires_each_urd_in_canonical_mapping(self) -> None:
        spec = (ROOT / "work" / "INT-001" / "spec.md").read_text(encoding="utf-8")
        mapping_start = spec.index("## Requirement-to-Spec Mapping")
        gate_start = spec.index("## Gate 2 Approval")
        mapping = spec[mapping_start:gate_start]
        for replacement, expected in (
            ("URD-001 FS-001; URD-002 FS-002\n\n", "contains no URD/FS pairs"),
            (mapping.replace("| `URD-002` | `FS-002` |", "| `URD-002` | |"), "URD-002"),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                bundle = Path(tmp) / "INT-001"
                shutil.copytree(ROOT / "work" / "INT-001", bundle)
                (bundle / "spec.md").write_text(
                    spec[:mapping_start] + replacement + spec[gate_start:], encoding="utf-8"
                )
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "validate_work_item.py"), str(bundle)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(expected, result.stderr)

    def test_mismatched_urd_fs_pair_in_traceability_matrix_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-997"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            report_path = bundle / "test-report.md"
            text = report_path.read_text(encoding="utf-8")
            # Swap URD-001 -> URD-002 on FS-001 row in Section 12
            tampered = text.replace(
                "| `URD-001` | `FS-001` | `CLI-001` |",
                "| `URD-002` | `FS-001` | `CLI-001` |",
            )
            report_path.write_text(tampered, encoding="utf-8")

            errs = validate_work_item.validate_work_item_dir(bundle, require_review=False)
            self.assertTrue(any("URD-001->FS-001" in e for e in errs))
            self.assertTrue(any("URD-002->FS-001" in e for e in errs))

    def test_covered_pair_on_shared_fs_requires_its_own_test_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-001"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            for name, heading, new_row in (
                (
                    "intent.md", "## Business Rules & Constraints",
                    "| `URD-003` | Additional requirement | Covered by the shared function | High |",
                ),
                (
                    "spec.md", "## Gate 2 Approval",
                    "| `URD-003` | `FS-001` | `CLI-001` | Covered |",
                ),
            ):
                path = bundle / name
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace(f"\n\n{heading}", f"\n{new_row}\n\n{heading}"), encoding="utf-8"
                )

            report = bundle / "test-report.md"
            original = report.read_text(encoding="utf-8")
            report_end = "## Section 13: Performance & Security Test Fundamentals"
            validators = {
                "work-item": ["validate_work_item.py", str(bundle)],
                "contract": ["validate-contracts.py", "--test-report", str(report)],
            }
            for test_cell, expected in (("", 1), ("n/a", 1), ("`TC-HC-001-invalid`", 1), ("`TC-HC-001`", 0)):
                row = f"| `URD-003` | `FS-001` | `CLI-001` | {test_cell} | Covered |"
                report.write_text(
                    original.replace(f"\n\n{report_end}", f"\n{row}\n\n{report_end}"), encoding="utf-8"
                )
                for validator, (script, *args) in validators.items():
                    with self.subTest(validator=validator, test_cell=test_cell):
                        result = subprocess.run(
                            [sys.executable, str(ROOT / "scripts" / script), *args],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                        if expected:
                            self.assertIn("URD-003", result.stderr)
                            self.assertIn("FS-001", result.stderr)
                            self.assertIn("test case ID", result.stderr)

    def test_undefined_test_case_in_matrix_and_tasks_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-001"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            tasks = bundle / "tasks.json"
            data = json.loads(tasks.read_text(encoding="utf-8"))
            data["tasks"][0]["test_refs"].append("TC-HC-998")
            tasks.write_text(json.dumps(data), encoding="utf-8")

            report = bundle / "test-report.md"
            text = report.read_text(encoding="utf-8")
            before, matrix = text.split("## Section 12: Traceability Matrix", 1)
            matrix = matrix.replace("`TC-EP-001` | Covered", "`TC-EP-001`, `TC-HC-998` | Covered", 1)
            before = before.replace("## Section 11:", "An example mentions `TC-HC-998`.\n\n## Section 11:")
            before = before.replace("`TC-BVA-001`, `TC-BVA-002`, `TC-NEG-001` |",
                                    "`TC-BVA-001`, `TC-BVA-002`, `TC-NEG-001`, `TC-HC-998` |")
            undefined = before + "## Section 12: Traceability Matrix" + matrix
            defined = undefined.replace(
                "\n\n## Section 6:",
                "\n| `TC-HC-998` | Additional happy path | Verify output | Work item exists | "
                "Run CLI | Valid input | Exit 0 | High |\n\n## Section 6:",
                1,
            )

            commands = (
                ["validate_work_item.py", str(bundle)],
                ["validate-contracts.py", "--tasks", str(tasks), "--test-report", str(report)],
            )
            for report_text, expected in ((undefined, 1), (defined, 0)):
                report.write_text(report_text, encoding="utf-8")
                for script, *args in commands:
                    with self.subTest(script=script, expected=expected):
                        result = subprocess.run(
                            [sys.executable, str(ROOT / "scripts" / script), *args],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                        if expected:
                            self.assertIn("undefined test case ID: TC-HC-998", result.stderr)
                            self.assertIn("URD-001", result.stderr)
                            if script == "validate_work_item.py":
                                self.assertIn("TASK-001", result.stderr)

    def test_empty_test_refs_or_missing_tc_or_wrong_fs_mapping_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-998"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            tasks = json.loads((bundle / "tasks.json").read_text(encoding="utf-8"))
            tasks["tasks"][0]["test_refs"] = []
            (bundle / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")

            errs_empty = validate_work_item.validate_work_item_dir(bundle, require_review=False)
            self.assertTrue(any("empty test_refs" in e for e in errs_empty))
            self.assertTrue(any("TC-EP-001" in e for e in errs_empty))

            tasks["tasks"][0]["test_refs"] = ["TC-HC-001", "TC-NEG-001", "TC-BVA-001"]
            tasks["tasks"][1]["test_refs"].append("TC-EP-001")
            (bundle / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")

            errs_wrong_fs = validate_work_item.validate_work_item_dir(bundle, require_review=False)
            self.assertTrue(any("TC-EP-001" in e and "FS-002" in e for e in errs_wrong_fs))

    def test_missing_fs_in_tasks_and_missing_review_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-999"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            (bundle / "REVIEW.md").unlink()
            tasks = json.loads((bundle / "tasks.json").read_text(encoding="utf-8"))
            tasks["tasks"] = [tasks["tasks"][0]]  # drop FS-002
            (bundle / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")

            errs_review = validate_work_item.validate_work_item_dir(bundle, require_review=True)
            self.assertTrue(any("REVIEW.md" in e for e in errs_review))

            errs_fs = validate_work_item.validate_work_item_dir(bundle, require_review=False)
            self.assertTrue(any("FS-002" in e for e in errs_fs))


VALID_DIGEST = """# Change Digest (ELI10)

## 1. สรุปสั้นๆ (What & Why)
- ปัญหาก่อนหน้า: ตรวจความสัมพันธ์ระหว่าง artifact ด้วยมือและพลาดบ่อย
- รอบนี้เพิ่ม: validator ตรวจ URD/FS/TC/TASK ให้อัตโนมัติ

## 2. ไฟล์ที่แก้
| ไฟล์ | ทำอะไร | เพื่ออะไร |
| :--- | :--- | :--- |
| `scripts/validate_work_item.py` | เพิ่มสคริปต์ | ตรวจ traceability |

## 3. How It Works
1. อ่านไฟล์ intent, spec, test-report, tasks
2. เทียบ ID ข้ามไฟล์
3. รายงาน error ที่ขาด

## 4. Try It Yourself
```bash
python3 scripts/validate_work_item.py work/INT-001
```

## 5. Verified Evidence
- รัน unittest ผ่านหลังแก้ครั้งสุดท้าย
"""


class TestChangeDigestRequirement(unittest.TestCase):
    def _bundle(self, tmp: str, digest: str | None) -> Path:
        bundle = Path(tmp) / "INT-996"
        shutil.copytree(ROOT / "work" / "INT-001", bundle)
        path = bundle / "change-digest.md"
        if path.exists():
            path.unlink()
        if digest is not None:
            path.write_text(digest, encoding="utf-8")
        return bundle

    def test_missing_digest_fails_only_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._bundle(tmp, None)
            self.assertEqual(validate_work_item.validate_work_item_dir(bundle, require_review=True), [])
            errs = validate_work_item.validate_work_item_dir(bundle, require_review=True, require_digest=True)
            self.assertTrue(any("change-digest.md" in e for e in errs))

    def test_valid_digest_passes_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._bundle(tmp, VALID_DIGEST)
            errs = validate_work_item.validate_work_item_dir(bundle, require_review=True, require_digest=True)
            self.assertEqual(errs, [])

    def test_unfilled_template_digest_is_rejected(self) -> None:
        template = (ROOT / "docs" / "templates" / "change-digest.template.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._bundle(tmp, template)
            errs = validate_work_item.validate_work_item_dir(bundle, require_digest=True)
            self.assertTrue(any("placeholder" in e for e in errs), errs)

    def test_empty_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = self._bundle(tmp, "   \n")
            errs = validate_work_item.validate_work_item_dir(bundle, require_digest=True)
            self.assertTrue(any("change-digest.md" in e for e in errs), errs)

    def test_cli_flag_controls_exit_code(self) -> None:
        script = str(ROOT / "scripts" / "validate_work_item.py")
        for digest, flag, expected in ((None, [], 0), (None, ["--require-digest"], 1), (VALID_DIGEST, ["--require-digest"], 0)):
            with self.subTest(has_digest=digest is not None, flag=flag), tempfile.TemporaryDirectory() as tmp:
                bundle = self._bundle(tmp, digest)
                result = subprocess.run(
                    [sys.executable, script, str(bundle), *flag], capture_output=True, text=True, check=False
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                if expected:
                    self.assertIn("change-digest.md", result.stderr)

    def test_stub_without_required_sections_is_rejected(self) -> None:
        for stub in ("# x\nok", VALID_DIGEST.replace("## 3. How It Works", "## Three")):
            with self.subTest(stub=stub[:20]):
                errs = validate_work_item.check_change_digest(stub)
                self.assertTrue(any("section" in e for e in errs), errs)

    def test_each_template_placeholder_is_detected_when_left_behind(self) -> None:
        leftovers = (
            "- **Date (`Asia/Bangkok`):** `YYYY-MM-DD HH:mm:ss +07`",
            "| `path/to/file` | แก้กฎ | งานนี้ |",
            "- **ปัญหาก่อนหน้า:** [อธิบายภาษาคนธรรมดา 1–2 ประโยค]",
            "- **รอบนี้เพิ่ม:** [สิ่งใหม่ที่ระบบทำได้ตอนนี้]",
            "| `a.py` | [เพิ่มฟังก์ชัน / แก้กฎ] | ok |",
            "| `a.py` | ok | [เหตุผลที่เชื่อมกับเป้าหมายงาน] |",
            "1. [ขั้นที่ 1: เริ่มจากจุดไหน]",
            "- **Checks Executed:** `[ระบุคำสั่งและยอด pass/fail/skip]`",
        )
        for leftover in leftovers:
            with self.subTest(leftover=leftover[:30]):
                errs = validate_work_item.check_change_digest(VALID_DIGEST + "\n" + leftover + "\n")
                self.assertTrue(any("placeholder" in e for e in errs), errs)

    def test_prose_mentioning_date_format_is_not_a_false_positive(self) -> None:
        prose = VALID_DIGEST + "\nเราใช้รูปแบบ YYYY-MM-DD HH:mm:ss ในไฟล์ trace และอ้างถึง path/to/file เป็นตัวอย่าง\n"
        self.assertEqual(validate_work_item.check_change_digest(prose), [])

    def test_digest_file_mode_checks_a_standalone_handoff_digest(self) -> None:
        script = str(ROOT / "scripts" / "validate_work_item.py")
        template = (ROOT / "docs" / "templates" / "change-digest.template.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-digest.md"
            good.write_text(VALID_DIGEST, encoding="utf-8")
            bad = Path(tmp) / "bad-digest.md"
            bad.write_text(template, encoding="utf-8")
            for path, expected in ((good, 0), (bad, 1), (Path(tmp) / "missing.md", 1)):
                with self.subTest(path=path.name):
                    result = subprocess.run(
                        [sys.executable, script, "--digest-file", str(path)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            neither = subprocess.run([sys.executable, script], capture_output=True, text=True, check=False)
            self.assertEqual(neither.returncode, 2, neither.stderr)

    def test_sections_with_headings_but_no_content_are_rejected(self) -> None:
        empty = "# Digest\n\n" + "\n\n".join(f"## {n}. Heading" for n in range(1, 6)) + "\n"
        errs = validate_work_item.check_change_digest(empty)
        self.assertTrue(any("no content" in e for e in errs), errs)
        one_empty = VALID_DIGEST.replace(
            "## 3. How It Works\n1. อ่านไฟล์ intent, spec, test-report, tasks\n2. เทียบ ID ข้ามไฟล์\n3. รายงาน error ที่ขาด\n",
            "## 3. How It Works\n\n",
        )
        self.assertNotEqual(one_empty, VALID_DIGEST)
        errs = validate_work_item.check_change_digest(one_empty)
        self.assertTrue(any("no content" in e and "## 3." in e for e in errs), errs)

    def test_headings_inside_code_fences_do_not_count_as_sections(self) -> None:
        fenced = VALID_DIGEST.replace(
            "## 5. Verified Evidence\n- รัน unittest ผ่านหลังแก้ครั้งสุดท้าย\n",
            "```markdown\n## 5. Verified Evidence\n- example only\n```\n",
        )
        self.assertNotEqual(fenced, VALID_DIGEST)
        errs = validate_work_item.check_change_digest(fenced)
        self.assertTrue(any("missing required section" in e and "## 5." in e for e in errs), errs)

    def test_section_with_only_punctuation_or_subheadings_has_no_content(self) -> None:
        for filler in ("-\n", "### Sub heading\n", "- \n---\n"):
            with self.subTest(filler=filler):
                text = VALID_DIGEST.replace(
                    "## 5. Verified Evidence\n- รัน unittest ผ่านหลังแก้ครั้งสุดท้าย\n",
                    f"## 5. Verified Evidence\n{filler}",
                )
                self.assertNotEqual(text, VALID_DIGEST)
                errs = validate_work_item.check_change_digest(text)
                self.assertTrue(any("no content" in e and "## 5." in e for e in errs), errs)

    def test_code_block_inside_a_section_still_counts_as_content(self) -> None:
        self.assertIn("```bash", VALID_DIGEST)
        self.assertEqual(validate_work_item.check_change_digest(VALID_DIGEST), [])

    def test_work_item_flags_without_work_dir_are_a_usage_error(self) -> None:
        script = str(ROOT / "scripts" / "validate_work_item.py")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-digest.md"
            good.write_text(VALID_DIGEST, encoding="utf-8")
            for flag in ("--require-review", "--require-digest"):
                with self.subTest(flag=flag):
                    result = subprocess.run(
                        [sys.executable, script, "--digest-file", str(good), flag],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("work item directory", result.stderr)

    def test_real_handoff_digest_for_this_plan_is_valid(self) -> None:
        text = (ROOT / "docs" / "handoff" / "2026-11-22-governance-consistency-digest.md").read_text(encoding="utf-8")
        self.assertEqual(validate_work_item.check_change_digest(text), [])

    def test_real_pilot_has_valid_digest(self) -> None:
        errs = validate_work_item.validate_work_item_dir(
            ROOT / "work" / "INT-001", require_review=True, require_digest=True
        )
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
