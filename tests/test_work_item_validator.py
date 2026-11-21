"""Unit tests for scripts/validate_work_item.py (INT-001 pilot implementation)."""

from __future__ import annotations

import json
import shutil
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

    def test_empty_test_refs_or_missing_tc_or_wrong_fs_mapping_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "INT-998"
            shutil.copytree(ROOT / "work" / "INT-001", bundle)
            tasks = json.loads((bundle / "tasks.json").read_text(encoding="utf-8"))
            # Remove test_refs from TASK-001 -> must fail mentioning TC-EP-001 / empty test_refs
            tasks["tasks"][0]["test_refs"] = []
            (bundle / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")

            errs_empty = validate_work_item.validate_work_item_dir(bundle, require_review=False)
            self.assertTrue(any("empty test_refs" in e for e in errs_empty))
            self.assertTrue(any("TC-EP-001" in e for e in errs_empty))

            # Assign TC-EP-001 (which belongs to FS-001) to TASK-002 (FS-002) -> must fail
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


if __name__ == "__main__":
    unittest.main()
