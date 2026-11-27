---
spec_id: SPEC-001
intent_ref: INT-001
status: approved
owner: sa-architect-agent
amendment: A1 approved at Gate 2 (see Addendum A1)
---

# Technical & Functional Specification: Work Item Traceability Validator

## Header & References
| Item | Detail |
| :--- | :--- |
| **Spec ID** | `SPEC-001` |
| **Intent Reference** | `INT-001` |
| **Related ADRs** | `N/A` (additive read-only validator module) |

## Architecture & Component Impact
- **Impacted Modules:** `scripts/validate_work_item.py` (new), `tests/test_work_item_validator.py` (new)
- **Data Flow Summary:** Read `intent.md`, `spec.md`, `test-report.md`, `tasks.json`, and optionally `REVIEW.md` inside `work/<INT-xxx>/` → extract `URD-[0-9]{3,}` and `FS-[0-9]{3,}` sets → validate set inclusion and contract invariants.

> **Addendum A1 (อนุมัติแล้ว):** พฤติกรรมและ module ที่ใช้จริงต่างจากส่วน Architecture, IPO Matrix และ Rollback ด้านล่าง ดู [Addendum A1](#addendum-a1--as-built-behaviour) ท้ายเอกสาร

## IPO Matrix (Input -> Process -> Output)
| Function ID | Function Name | URD Reference | Input | Process/Logic | Expected Output | Validation Rules |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | `check_intent_to_spec` | `URD-001` | `intent_text: str`, `spec_text: str` | Extract unique `URD-xxx` IDs from `intent.md` and `spec.md`; compute `intent_urds - spec_urds` | `list[str]` error messages (empty if covered) | Must contain >= 1 `URD-xxx` in `intent.md`; any uncovered `URD-xxx` yields error |
| `FS-002` | `check_spec_downstream` | `URD-002` | `spec_text: str`, `tasks_data: dict`, `report_text: str` | Extract `FS-xxx` from `spec.md`, `tasks.json` (`fs_refs`), and `test-report.md`; verify `spec_fs <= task_fs` and `spec_fs <= report_fs` | `list[str]` error messages (empty if covered) | Must contain >= 1 `FS-xxx` in `spec.md`; missing `FS-xxx` in tasks or test report yields error |

## API & Data Contracts
- **CLI Interface:** `python3 scripts/validate_work_item.py <work_item_dir> [--require-review]`
  - *Addendum (PLAN-007, 2026-11-22 — outside INT-001 scope, does not change `FS-001`/`FS-002`):* the same script later gained `[--require-digest]` (requires a filled `change-digest.md` in the work item) and `[--digest-file PATH]` (checks a standalone digest; `<work_item_dir>` becomes optional). Both flags are opt-in, so the contract above is unchanged when they are omitted.
- **Exit Codes:** `0` = valid & 100% covered; `1` = missing file or traceability error; `2` = CLI usage error.
- **Database / Migration Impact & Rollback:** `N/A` — pure read-only CLI script; rollback is removing the two new files.

## Security, Privacy & NFR Constraints
- **Path Traversal Guard:** Resolve `<work_item_dir>` cleanly and read files read-only; never execute shell commands from parsed Markdown.
- **Performance Target:** `< 200ms` per work item directory.

## Requirement-to-Spec Mapping
| URD ID | Function ID (`FS-xxx`) | Screen / Endpoint (`SCR-xxx`) | Notes |
| :--- | :--- | :--- | :--- |
| `URD-001` | `FS-001` | `CLI-001` | Covered |
| `URD-002` | `FS-002` | `CLI-001` | Covered |

## Gate 2 Approval
- **Reviewer:** `human-maintainer (PLAN-006 approved)`
- **Decision:** `Approved`
- **Timestamp:** `2026-11-21`

---

## Addendum A1 — As-built behaviour

> **ร่างเมื่อ:** 2026-11-27 · **ตรวจกับโค้ดที่:** `3f082dc` · **ที่มา:** finding M-01 ใน [REVIEW.md](REVIEW.md) รอบ 7
> พฤติกรรมใน A1.2 และ module ใน A1.1 เพิ่มเข้ามาระหว่างรีวิวรอบ 3–5 **หลัง** Gate 2 เดิม และเข้า `main` แล้วใน PR #2 การอนุมัติ A1 จึงเป็นการรับรองย้อนหลัง
> A1 **ไม่เปลี่ยนโค้ด** เมื่อข้อความเดิมขัดกับ A1 ให้ใช้ A1 และยังคงใช้ `FS-001` / `FS-002` เดิม

### A1.1 Architecture & Component Impact (แทนรายการ Impacted Modules)

| Module | สถานะ | หน้าที่ |
| :--- | :--- | :--- |
| `scripts/validate_work_item.py` | new | ตัวตรวจ traceability ของ work item |
| `scripts/qa_report.py` | new | อ่านนิยาม test case จากตารางใน QA report ใช้ร่วมกันสองตัวตรวจ |
| `scripts/validate-contracts.py` | **modified** | CI gate: เพิ่มกติกาใน A1.3 มีผลกับ test report ทุกไฟล์ที่ส่งเข้าตรวจ รวม template ใน `--check-defaults` |
| `tests/test_work_item_validator.py` | new | regression tests |

### A1.2 กติกาจริงของ `validate_work_item.py`

**`FS-001`**
- `intent.md` ต้องมี `URD-xxx` อย่างน้อยหนึ่งรายการ
- ทุก URD ใน intent ต้องจับคู่กับ FS ในตาราง Requirement-to-Spec Mapping (สองคอลัมน์แรก) การกล่าวถึงที่อื่นใน spec ไม่นับ

**`FS-002`**
- `spec.md` ต้องมี FS ID และตาราง mapping ต้องมีคู่ URD/FS อย่างน้อยหนึ่งคู่
- คู่ URD/FS ในตาราง mapping กับใน Section 12 ของ `test-report.md` ต้อง **ตรงกันทั้งสองทิศ**
- Section 12 ต้องมีอยู่ และมี FS อย่างน้อยหนึ่งรายการ ทุกแถวข้อมูล (ตั้งแต่ 5 คอลัมน์) ต้องมี URD, มีสถานะ `Covered` (ไม่สนตัวพิมพ์) และแถว `Covered` ต้องมี test case ID
- test case ID ที่ Section 12 หรือ `test_refs` อ้างถึง ต้องมีนิยามในคอลัมน์นิยามของ Section 5–9, 11 หรือ 13
- ทุก task ต้องมี `test_refs` ไม่ว่าง
- สำหรับ FS ใน `fs_refs` ของ task ที่ปรากฏใน Section 12: test case **ทุกตัว** ของ task ต้องผูกกับ FS นั้นใน Section 12 (task ที่อ้างหลาย FS จึงถูกตรวจทุกคู่)
- FS ทุกตัวใน `spec.md` (ทั้งไฟล์) ต้องอยู่ใน `fs_refs` ของ task และใน Section 12 (การกล่าวถึงนอก Section 12 ไม่นับ)
- test case ทุกตัวที่ Section 12 ผูกกับ FS ต้องอยู่ใน `test_refs` ของ task อย่างน้อยหนึ่ง task ที่อ้าง FS นั้น
- `--require-review` ตรวจเพียงว่ามีไฟล์ `REVIEW.md`

### A1.3 กติกาที่เพิ่มใน `validate-contracts.py`

สำหรับแถว Section 12 ที่มีสถานะ `Covered`, `Partial` หรือ `Gap`: แถว `Covered` ต้องมี test case ID และ ID ที่อ้างต้องมีนิยาม

**สองตัวตรวจไม่เท่ากัน (ตั้งใจ):** `validate-contracts.py` ตรวจรูปแบบรายงานทั่วไป จึงยอมให้ `Partial` ผ่าน (ปฏิเสธ `Gap` ตามกติกาเดิม) ส่วน `validate_work_item.py` ตรวจความครบก่อนส่งงาน จึงรับเฉพาะ `Covered`

### A1.4 สิ่งที่ตัวตรวจ **ไม่** บังคับ (known limitations)

exit `0` จึง **ไม่ได้** แปลว่างานผ่าน Gate 3

| กรณี | ผลปัจจุบัน | อ้างอิง |
| :--- | :--- | :--- |
| FS ที่มีเฉพาะใน `tasks.json` | ผ่าน | m-02 |
| URD ใน spec และ report ที่ไม่มีใน intent | ผ่าน | m-02 |
| task ที่ `passes=false`, สถานะ `blocked` หรือ `fs_refs` ว่าง | ผ่าน | m-02 |
| `REVIEW.md` ว่าง | ผ่านแม้ใช้ `--require-review` | m-02 |
| test case ที่ไม่มีนิยามจริงแต่เขียนในคอลัมน์ `Test Case IDs` ของ Section 8 | ถูกนับเป็นนิยาม | m-03 |
| `tasks.json` เสีย, root ไม่ใช่ object หรือ `tasks: null` | traceback แทนข้อความ error | m-05 |
| สถานะ Gate ที่ยังไม่อนุมัติใน intent / spec | ผ่าน | m-01 |
| NFR เรื่อง resolve `<work_item_dir>` | โค้ดไม่เรียก `resolve()` (ยังอ่านอย่างเดียวและไม่รัน shell) | m-06 |

### A1.5 คำตัดสินใน Gate 2

1. **m-01:** ถอด "unapproved gate status" ของ intent Business Flow 2 ออกจาก scope ของ `SPEC-001` (ไม่มี URD / FS / test case รองรับ) โดยไม่แก้ `intent.md` ย้อนหลัง
2. **m-06:** **คง** ข้อกำหนด Path Traversal Guard ไว้ตามเดิม รับว่าโค้ดยังไม่ครบ และทำเป็น follow-up
3. **Risk tier (m-08):** ยกจาก `medium` เป็น `high` เพราะแก้ CI gate (`validate-contracts.py`) หลังอนุมัติจึงแก้ `intent.md` / `work/index.yaml` ใน change แยก
4. **m-02, m-03, m-05:** รับเป็น known limitations และเปิด follow-up นอก `INT-001`

### A1.6 Rollback (แทนข้อความ "removing the two new files")

ลบไฟล์ตรง ๆ **ไม่ได้** แล้ว เพราะ:
- `validate-contracts.py` import `qa_report.py` การลบไฟล์นี้ทำให้ CI พัง
- `validate_work_item.py` มี `--require-digest` / `--digest-file` จาก `PLAN-007` ซึ่ง DoD และ PR/MR template ใช้ และ `PLAN-009` ใช้ใน CI (merge แล้วใน PR #14)

**Rollback:** revert เฉพาะพฤติกรรม traceability ใน change เดียว คือ (ก) ถอด import และกติกา A1.3 ออกจาก `validate-contracts.py` (ข) ถอดการตรวจ `FS-001` / `FS-002` ออกจาก `validate_work_item.py` โดยเก็บส่วน digest ไว้ (ค) ลบ `qa_report.py` หลังไม่มีผู้ import และปรับ tests กับเอกสารที่อ้างคำสั่งเดิมให้ตรงกัน ไม่มี data migration

### Gate 2 Approval (A1)
- **Reviewer:** Human Maintainer (ตอบในแชท)
- **Decision:** `Approved` — ข้อความ: “อนุมัติตามข้อเสนอ” ครอบคลุม A1.1–A1.6 รวมความต่างของสองตัวตรวจ (A1.3) และคำตัดสิน A1.5
- **Recorded at:** 2026-11-27 17:35 +07 (เวลาที่บันทึก ไม่ใช่เวลาอนุมัติที่แน่นอน)
