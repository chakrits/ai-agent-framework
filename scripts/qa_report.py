"""Read test case definitions from the canonical QA report tables."""

from __future__ import annotations

import re

TEST_CASE_ID_RE = re.compile(
    r"(?<![\w-])(?:TC-(?:HC|NEG|BVA|EP|API|PERF|SEC)|EXP|UNIT)-[0-9]{3,}(?![\w-])"
)
SECTION_RE = re.compile(r"^## Section ([0-9]+):")
DEFINITION_HEADERS = {
    5: "Test Case ID",
    6: "Test Case ID",
    7: "Test Case ID",
    8: "Test Case IDs",
    9: "Test Case ID",
    11: "Charter ID",
    13: "Test Case ID",
}


def table_cells(line: str) -> list[str]:
    row = line.strip()
    if not row.startswith("|"):
        return []
    return [cell.strip() for cell in row[1:].removesuffix("|").split("|")]


def defined_test_case_ids(report_text: str) -> set[str]:
    """Collect IDs from the definition column, including BVA and EP rows in Section 8."""
    ids: set[str] = set()
    header = ""
    column = None
    for line in report_text.splitlines():
        section = SECTION_RE.match(line)
        if section:
            header = DEFINITION_HEADERS.get(int(section[1]), "")
        cells = table_cells(line)
        if not cells:
            column = None
        elif header and header in cells:
            column = cells.index(header)
        elif column is not None and column < len(cells):
            ids.update(TEST_CASE_ID_RE.findall(cells[column]))
    return ids
