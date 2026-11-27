---
review_id: REV-001
pr_ref: https://github.com/chakrits/ai-agent-framework/pull/2
spec_ref: SPEC-001
verdict: changes_requested
---

# Code & Security Review Report (`INT-001`)

> **รอบ 7** (independent re-review ก่อน Gate 3) · 2026-11-27 17:26:17 +07 · **Verdict: `changes_requested`**
> **Reviewed commit:** `3f082dcb717f1a32aa3644f7272262965b2ef4da` (`main`)
> Blocker เดิมปิดแล้วสำหรับ revision นี้ แต่ยังมี spec drift (M-01) ที่ block Gate 3 และมีข้อเบี่ยงเบนด้าน process (M-02) ที่ Human ต้องตัดสิน

## Review Scope & Traceability Check
- **Intent / Spec:** `INT-001` / `SPEC-001` ([intent.md](intent.md), [spec.md](spec.md)) · **Tasks:** `TASK-001`, `TASK-002` ([tasks.json](tasks.json))
- **ขอบเขต:** `scripts/validate_work_item.py`, `scripts/qa_report.py`, ส่วนตรวจ test report ใน `scripts/validate-contracts.py`, `tests/test_work_item_validator.py` และ artifacts ใน `work/INT-001/` ที่ revision ข้างต้น (อ่าน `change-digest.md` หลังสรุป finding แล้ว)
- **Pilot revision:** [PR #2](https://github.com/chakrits/ai-agent-framework/pull/2) head `16db38c533a7acc57d34c5c6c68d290d92c42d52`, merge `eca7f225c66ecde7e1eaa84ce0b99c1a2453b656` (tree เดียวกัน `8078a31c7dabeaef2d540bc86abb82bd9e5f7ae8`), merge เมื่อ `2026-11-22T05:05:50Z`
  - CI [run 44987700139](https://github.com/chakrits/ai-agent-framework/actions/runs/44987700139) = **failure**: Ubuntu และ macOS 4 jobs ผ่าน, Windows py3.10/py3.12 ไม่ผ่าน
- **Revision ถัดมา:** [PR #4](https://github.com/chakrits/ai-agent-framework/pull/4) (`PLAN-007`) head `64a29eab720f27d2b692055928bd8f2bf266a8fc`, merge `d764d5fe18bc1441dae909503ad8b8e36354bfc2`, [run 45005508352](https://github.com/chakrits/ai-agent-framework/actions/runs/45005508352) ผ่านครบ 6 jobs
- **Revision ที่ review:** `3f082dcb717f1a32aa3644f7272262965b2ef4da`, push [run 45977410340](https://github.com/chakrits/ai-agent-framework/actions/runs/45977410340) ผ่านครบ 6 jobs

### การตัดสิน Blocker เดิม (Pilot PR/CI evidence pending)
**ปิดแล้ว โดยย้ายจุดอ้างอิงของ Gate 3 มาที่ `3f082dc`** ไม่ใช่การถือว่า pilot revision ผ่าน CI

1. **CI เขียวของ revision ถัดมาไม่ได้ทำให้ `16db38c` ผ่าน** เพราะเป็นคนละ tree และ `validate_work_item.py` กับ test ของมันเปลี่ยนไปแล้ว หลักฐานของ `16db38c` ยังเป็น `failure`
2. **สาเหตุที่ `16db38c` ไม่ผ่าน:** Windows ล้ม 1 test คือ `test_live_mode_fails_closed_if_git_state_unreadable_or_budget_exceeded` (`tests/test_eval_runner.py:136`, workstream live eval ซึ่งอยู่นอก `FS-001`/`FS-002`) จาก `Ran 236 tests` / `FAILED (failures=1, skipped=3)` ส่วน validator tests ของ INT-001 ทั้ง 9 ข้อเป็น `ok` บน Windows ทั้งสอง version ขั้นตอน eval suite, smoke และ hook smoke บน Windows ถูก `skipped` จึง**ไม่เคยรันกับ pilot revision**
3. **การแก้ใน PR #4** เปลี่ยนเฉพาะ fixture ให้ลบ `.git` แบบ read-only บน Windows ได้ assertion คงเดิม
4. **ความต่อเนื่องของโค้ด INT-001 (`eca7f22..3f082dc`):** `qa_report.py` และ `validate-contracts.py` ไม่มี diff, ฟังก์ชันตรวจ `FS-001`/`FS-002` ไม่ถูกแก้ (บรรทัดที่ถูกลบมีเฉพาะ signature, argparse และข้อความ output ของ `PLAN-007`), test file มีแต่บรรทัดเพิ่ม และ `test-report.md` hash เดิม
5. **หลักฐานที่ revision ที่ review:** ใน run 45977410340 job Windows py3.10 และ py3.12 ได้ `Ran 252 tests` / `OK (skipped=3)` และ `test_work_item_validator` เป็น `ok` 25 ข้อต่อ job

## Spec Compliance & Architectural Drift
- [x] `FS-001`: ทุก `URD-xxx` ใน intent ต้องมี mapping ใน spec (เข้มกว่าข้อความ `intent_urds - spec_urds` ใน IPO Matrix)
- [x] `FS-002`: `spec_fs <= task_fs` และ `spec_fs <= report_fs` ทำงานตาม spec
- [x] CLI exit `0`/`1`/`2` และใช้ stdlib เท่านั้น (`BR-001`)
- [ ] **มี drift (M-01):** พฤติกรรมและ module ที่เพิ่มในรอบ review 3–6 ไม่อยู่ใน `spec.md`
- **แก้ข้อความรอบก่อน:** "clean separation from `scripts/validate-contracts.py`" **ไม่ถูกต้อง** เพราะทั้งสอง validator import `scripts/qa_report.py` และ `validate-contracts.py` ถูกแก้ใน PR #2
- `AGENTS.md` / `CLAUDE.md`: ไม่พบส่วนที่ล้าสมัยจากโค้ด INT-001

## Verification Evidence (Tests & Linters)
รันเองบน macOS, Python 3.14.10, `SDLC_TRACE_DIR` เป็น temp directory ที่ `3f082dc` (ก่อนแก้ไฟล์นี้)

| Command | Observed Result |
| :--- | :--- |
| `python3 scripts/doctor.py` | exit 0 |
| `python3 scripts/sync-adapters.py --check` | `Adapter parity check PASSED`, exit 0 |
| `python3 scripts/validate-context-budget.py` | `Context budget check PASSED`, exit 0 |
| `python3 scripts/validate-contracts.py --check-defaults` | `Contract validation PASSED`, exit 0 |
| `python3 scripts/validate-contracts.py --tasks work/INT-001/tasks.json --test-report work/INT-001/test-report.md` | `Contract validation PASSED`, exit 0 |
| `python3 scripts/validate_work_item.py work/INT-001 --require-review --require-digest` | `Work item validation PASSED`, exit 0 |
| `python3 evals/run_evals.py --mode contract` และ `python3 evals/run_evals.py` | `10/10 cases`, exit 0 ทั้งสองคำสั่ง |
| `python3 -m unittest tests/test_work_item_validator.py -v` | `Ran 25 tests`, `OK` |
| `python3 -m unittest discover -s tests -v` | `Ran 252 tests`, `OK (skipped=3)`: Windows launcher 2, FastAPI 1 |
| `git diff --check` และ `git diff --check 0e27e94 eca7f22` | exit 0 |

**Pilot snapshot** (`git archive eca7f22` ลง temp directory, macOS): parity, context budget, contracts (2 คำสั่ง), work item (`--require-review`) และ contract evals `10/10` ผ่าน, validator tests `Ran 9 tests OK`, ทั้งชุด `Ran 236 tests OK (skipped=3)` ผลนี้ไม่แทน Windows

**Manual probes** บนสำเนาชั่วคราวของ `work/INT-001` ที่ `3f082dc`:

| กรณี | ผล |
| :--- | :--- |
| `TC-HC-001` baseline | exit 0 |
| `TC-NEG-001`, `TC-NEG-002`, `TC-NEG-003` (ขาด `spec.md` / `REVIEW.md`) | exit 1 พร้อมระบุสิ่งที่ขาด |
| `TC-BVA-001` (0 URD), `TC-BVA-002` (0 FS) | exit 1 |
| `TC-EP-001`: `URD-1`, `FS-abc` แทน ID ใน intent | exit 1 |
| `TC-EP-001`: `URD-1000` ไม่มี mapping / มี mapping ครบ | exit 1 / exit 0 (ถูกต้อง) |
| `TC-SEC-001`: shell syntax ใน `intent.md` | exit 0, ไม่มีไฟล์ถูกสร้างจากคำสั่ง |
| `TC-PERF-001` | ประมาณ 30–36 ms ต่อรอบ (`< 200 ms`) |

## Test Oracle Integrity Check
- [x] `test-report.md` SHA-256 `f6a9930441f848650ec915cb734416d1d1e6e0de5f33008017eb197cf391fb67` ตรงกันที่ `5ae1169`, `16db38c`, `eca7f22`, `d764d5f`, `3f082dc`
- [x] **Baseline ที่ตรวจซ้ำได้:** `5ae1169` (อยู่บน `main`) ส่วน `7b723bc` ที่รอบก่อนอ้าง มีใน local object store แต่ `git for-each-ref --contains` ไม่พบ ref และ GitHub API ตอบ 422 จึงไม่ควรใช้เป็น baseline ต่อ
- [x] `tests/test_work_item_validator.py`: `5ae1169..16db38c` บรรทัดที่ถูกลบเป็น comment 2 บรรทัด, `eca7f22..3f082dc` ไม่มีบรรทัดถูกลบ
- [x] `tests/test_eval_runner.py` ใน PR #4: แก้ fixture เท่านั้น
- **ข้อจำกัด:** `test-report.md` เข้า history พร้อม implementation ใน commit เดียว (`5ae1169`) จึงพิสูจน์ไม่ได้ว่า QA oracle เขียนก่อนโค้ด

## Security & OWASP Findings
- [x] **A03 Injection:** `validate_work_item.py` และ `qa_report.py` ไม่มี `subprocess`, `eval`, `exec`, การเขียนหรือลบไฟล์ และ probe `TC-SEC-001` ไม่เกิดการรันคำสั่ง
- [x] **A02/A09 Secrets/PII:** สแกน `work/INT-001/` และไฟล์โค้ด/test ของ INT-001 ด้วย pattern ของ key/token/private key ไม่พบ
- [x] **A01/A07:** ไม่เกี่ยวข้อง (local read-only CLI ไม่มี endpoint)
- [x] **External integrations:** ไม่มี network call, import เฉพาะ stdlib และ module ใน repo
- [ ] Spec NFR ระบุให้ resolve `<work_item_dir>` แต่โค้ดไม่ได้ `resolve()` หรือจำกัด symlink (m-06, ความเสี่ยงต่ำ)
- **ไม่พบ Critical/High**

## Findings Summary (Blocker / Major / Minor)
**Blocker 0 · Major 2 · Minor 8**

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| ~~Blocker~~ ปิดแล้ว | INT-001 pilot PR/CI | หลักฐานครบสำหรับ `3f082dc` ส่วน `16db38c` บันทึกว่า CI ไม่ผ่านบน Windows | ไม่มีสำหรับ finding นี้ การรับ merge เดิมอยู่ใน M-02 |
| **Major** M-01 (block Gate 3) | [spec.md](spec.md), [plan.md](plan.md), [validate_work_item.py](../../scripts/validate_work_item.py), [validate-contracts.py](../../scripts/validate-contracts.py) | โค้ดบังคับ (ก) คู่ URD/FS ใน spec และ Section 12 ตรงกันทั้งสองทิศ (ข) ทุกแถวต้อง `Covered` และมี TC (ค) TC ต้องมีนิยาม (ง) `test_refs` ห้ามว่างและต้องโยง TC/FS/TASK ตรงกับ matrix แต่ `FS-002` ระบุเพียง subset ของ FS นอกจากนี้ Impacted Modules ระบุเฉพาะไฟล์ใหม่ 2 ไฟล์ ขณะที่มี `qa_report.py` เพิ่ม และ `validate-contracts.py` (CI รันอยู่) ปฏิเสธ report ที่เคยผ่าน `plan.md` ยังระบุ "Files to Modify: None" และ rollback "ลบ 2 ไฟล์ใหม่" ไม่คืนพฤติกรรมของ contract validator เข้าเงื่อนไข `Business logic changed without corresponding update to spec.md or intent.md` | เพิ่ม addendum ใน `spec.md` (IPO/Validation Rules, Impacted Modules, rollback) และปรับ `plan.md` ให้ Human อนุมัติแบบ Gate 2 แล้วส่ง re-review ที่ SHA ใหม่พร้อม CI โดยไม่ต้องแก้โค้ดเพื่อปิดข้อนี้ |
| **Major** M-02 | PR #2, [PLAN-006](../../docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md) Checklist F | PR #2 ถูก merge โดย Maintainer ขณะ Windows แดง (job สุดท้ายจบ `05:05:04Z`), `REVIEW.md` ใน tree ที่ merge เป็น `changes_requested` มี Blocker และ Gate 3 `Pending`, PR ไม่มี review และ body ยังเป็น template ruleset `protect-main` สร้างภายหลัง (`2026-11-22T17:10:46+07:00` = `10:10:46Z`) เกณฑ์ "Gate 1–3 และ CI 3 OS ผ่านก่อน merge" จึงไม่สำเร็จตามแผน | แก้ย้อนหลังด้วยโค้ดไม่ได้ ใน Gate 3 sign-off ให้ Human ระบุว่ารับหรือไม่รับโค้ดบน `main` แบบย้อนหลัง โดยอ้าง `16db38c`/`eca7f22` และ SHA ที่ re-review ไม่ควรใช้ INT-001 เป็นหลักฐานปิด ROADMAP P9 (คงสถานะ ⬜) |
| Minor m-01 | [intent.md](intent.md) Business Flow 2 | ระบุว่า "unapproved gate status" ต้อง exit 1 แต่ไม่มี URD/FS/TC รองรับ ตั้ง intent และ spec เป็น `draft`/`Pending` แล้วยัง exit 0 | ตัดสินใน addendum เดียวกับ M-01 ว่าจะเลื่อนออกนอก scope หรือเปิดงาน implement |
| Minor m-02 | `check_spec_downstream`, `--require-review` | ผ่าน (exit 0) ทั้งกรณี `FS-999` เกินใน tasks, `URD-999` ใน spec/report ที่ไม่มีใน intent, `passes=false`/`blocked`, task ที่ `fs_refs` ว่าง และ `REVIEW.md` ว่าง | แจ้งผู้ใช้ว่า exit 0 ไม่ได้แปลว่าผ่าน Gate 3, เปิด follow-up |
| Minor m-03 | [qa_report.py](../../scripts/qa_report.py) `DEFINITION_HEADERS[8]` | `TC-HC-998` ที่ไม่มีนิยามจริง แต่ใส่ในคอลัมน์ `Test Case IDs` ของ Section 8 (พร้อม matrix และ tasks) ผ่านทั้งสอง validator เป็นส่วนที่เหลือจาก finding รอบ 5 | Section 8 ควรรับเฉพาะ `TC-BVA`/`TC-EP` พร้อม regression test |
| Minor m-04 | [tasks.json](tasks.json), [test-report.md](test-report.md), [trace-summary.md](trace-summary.md) | evidence `9 tests` เป็นของ pilot (ปัจจุบัน 25), evidence ของ `TASK-002` อ้าง contract validation ซึ่งไม่อยู่ใน `verification_cmd`, ไม่พบ automated test เฉพาะของ `TC-BVA-002`, `TC-EP-001`, `TC-SEC-001`, `TC-PERF-001` (รอบนี้ probe ด้วยมือ), trace สร้าง `2026-11-21 18:57` ก่อน commit `16db38c` และมีเฉพาะคำสั่งตรวจ 3 คำสั่ง | อัปเดต evidence ที่ SHA ใหม่ และเพิ่ม regression test |
| Minor m-05 | `validate_work_item_dir` | `tasks.json` ที่ parse ไม่ได้, root เป็น list หรือ `tasks: null` ได้ traceback แทนข้อความ error (exit 1) | จับ error และรายงานตามรูปแบบปกติ |
| Minor m-06 | `main` / `validate_work_item_dir` | ไม่มี `resolve()` ตาม Spec NFR | เพิ่ม หรือแก้ข้อความ NFR |
| Minor m-07 | [change-digest.md](change-digest.md) | ตารางไฟล์ไม่กล่าวถึง `qa_report.py` และ `validate-contracts.py` และคำอธิบายว่าจับทุกรหัสที่ขาด/โยงผิดกว้างกว่าผลจริง (ดู m-02) ส่วนสถานะ verdict และ `pending_gate_3` ตรงกับไฟล์ | อัปเดตพร้อม M-01 |
| Minor m-08 | `risk_tier: medium` | ตามกติกา `AGENTS.md` ปัจจุบัน งานที่แตะ CI gate หรือ diff เกินประมาณ 300 บรรทัดข้าม module จะ escalate เป็น High (ไม่พบข้อความกติกานี้ใน `AGENTS.md` ที่ `eca7f22`) และ addendum ของ `PLAN-007` แก้ spec ที่อนุมัติแล้ว | Human ยืนยัน tier และรับทราบ addendum |

### สิ่งที่ยังตรวจยืนยันไม่ได้
- ข้อความอนุมัติ Gate 1–2 ต้นฉบับ ผู้อนุมัติ เวลา และ revision (มีเพียงคำชี้แจงย้อนหลังที่บันทึกในรอบ 4)
- ความตรงของ `trace-summary.md` กับ raw trace (อยู่นอกขอบเขต worktree นี้) ตัวเลขในไฟล์จึงไม่ได้ export ซ้ำ
- พฤติกรรม Windows ของ pilot revision ในขั้นตอนที่ถูก `skipped`
- การรันเองบน Windows/Linux และ Python 3.10/3.12 (อาศัย CI), FastAPI endpoint test (skip ทั้ง local และ CI), Docker, live agent evals
- มี branch protection รูปแบบอื่นก่อน ruleset `protect-main` หรือไม่

## Council Pressure-Test
- **Lenses Used:** Contrarian, Outsider, Executor (single-model)
- **Preserved Dissent (คัดจาก acceptance criterion รอบ 6):** "ให้ Maintainer ดำเนินการ protected commit ตาม workflow แล้วแนบ PR URL, PR head SHA และผล CI ที่ครอบคลุมสาม OS ตามแผนสำหรับ revision เดียวกัน" มุมนี้เห็นว่า `16db38c` ไม่ผ่านเกณฑ์และการย้ายจุดอ้างอิงไป `3f082dc` เป็นการเปลี่ยนเกณฑ์ ซึ่ง Human ต้องยอมรับเอง
- **ข้อโต้แย้งต่อ verdict:** อาจมองได้ว่าควรเป็น `approved_for_human_gate` เพราะการตรวจที่เพิ่มทำให้ validator เข้มขึ้นเท่านั้น ถูกบันทึกใน `plan.md` (Review Round 3–5) และ `tasks.json` แล้ว และการแก้เป็นเพียงเอกสาร ผู้ review ไม่รับข้อโต้แย้งนี้ เพราะ `spec.md` ไม่มีพฤติกรรมตาม M-01, ไม่พบบันทึกการอนุมัติ Gate 2 ของส่วนที่เพิ่ม และทั้ง role rule (`unaddressed spec drift`) กับ `review-gate.schema.yaml` ให้ block
- **Blind-Spot Check:** exit 0 ของ validator ไม่ตรวจสถานะอนุมัติหรือ verdict และ pilot นี้ไม่ได้พิสูจน์ว่า gate หยุด merge ได้จริง
- **Verdict & One Next Step:** `changes_requested` · เขียน spec addendum ตาม M-01 แล้วเสนอ Human อนุมัติ

## Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer]`
- **Decision:** `Pending` — ต้องปิด M-01 และ re-review ก่อน จากนั้น Human ตัดสิน M-02 (รับโค้ดแบบย้อนหลังหรือไม่)
- **Timestamp:** Pending human decision.

---

## Review History
รายงานรอบก่อนหน้า: [รอบแรก](../../docs/plans/PLAN-006-REVIEW-VERDICT.md) · [รอบ 2](../../docs/plans/PLAN-006-REVIEW-ROUND-2.md) · [รอบ 3](../../docs/plans/PLAN-006-REVIEW-ROUND-3.md) · [รอบ 4](../../docs/plans/PLAN-006-REVIEW-ROUND-4.md) · [รอบ 5](../../docs/plans/PLAN-006-REVIEW-ROUND-5.md) · [รอบ 6](../../docs/plans/PLAN-006-REVIEW-ROUND-6.md)

ด้านล่างคือเนื้อหา `REVIEW.md` ฉบับก่อนรอบ 7 เก็บตามเดิม (ลดระดับ heading; frontmatter เดิม `pr_ref: pending`, `verdict: changes_requested`) ข้อความบางส่วนล้าสมัยหรือถูกแก้โดยรอบ 7 แล้ว

### Round 6 record (previous `REVIEW.md`)

#### Review Scope & Traceability Check
- **Gate 1–2:** The Round 4 report records the user's statement received on 2026-11-21 that both gates were approved in chat before implementation. This date records when the statement was received. The original messages, approver identities, approval times, and approved revisions are unavailable for independent verification. [Intent](intent.md) · [Spec](spec.md)
- **Tasks Completed:** `TASK-001`, `TASK-002` ([tasks.json](tasks.json))
- **Trace Evidence:** [trace-summary.md](trace-summary.md) records one session and three verification commands across eight events on `main`.
- **Revision Links:** Round 5 reviewed the staged diff at baseline `7b723bc8966089d9be16883f30b8af62ab4a49f7` (SHA-256 `cb0f3b03430b0e9aa6b621a59b587f8dd51399a9b9450fc4cba157bd21719915`). Follow-up edits are on local branch `feat/INT-001-round-4`. The combined patch includes protected paths and awaits the Maintainer's commit. The GitHub lookup found no matching remote branch, pilot PR or PR-triggered CI run for the baseline.
- **PR URL / head SHA / CI run URLs:** Pending publication of the pilot revision.
- **Diff Summary:** Both CLI validators require Covered rows in Section 12 to reference defined test cases. The work-item validator also checks each task's test references against the same QA definitions.

#### Spec Compliance & Architectural Drift
- [x] Implementation matches `SPEC-001` IPO Matrix (`FS-001`, `FS-002`) and CLI contract, enforcing exact `(URD-xxx, FS-xxx)` pairs between `spec.md` and `test-report.md` Section 12.
- [x] Zero external dependencies; clean separation from `scripts/validate-contracts.py`.

#### Verification Evidence (Tests & Linters)
- **Command Executed:** `python3 -m unittest tests/test_work_item_validator.py -v && python3 scripts/validate_work_item.py work/INT-001 --require-review && python3 scripts/validate-contracts.py --tasks work/INT-001/tasks.json --test-report work/INT-001/test-report.md`
- **Observed Result:** 9 validator tests passed. Both CLIs returned exit `1` and named `TC-HC-998` while it appeared only in references and prose. Both returned exit `0` when a test definition was added to the temporary report.

#### Test Oracle Integrity Check
- [x] **QA Oracle Baseline Commit:** `7b723bc8966089d9be16883f30b8af62ab4a49f7` (`work/INT-001/test-report.md`)
- [x] **QA Oracle SHA-256:** `f6a9930441f848650ec915cb734416d1d1e6e0de5f33008017eb197cf391fb67`
- [x] **Provenance Verification:** `git diff 7b723bc8966089d9be16883f30b8af62ab4a49f7 -- work/INT-001/test-report.md` produces **0 lines changed** (QA oracle remained strictly frozen while `scripts/validate_work_item.py` was updated).

#### Security & OWASP Findings
- [x] Pure read-only Markdown/JSON parsing; zero shell execution on parsed text (`TC-SEC-001`).
- [x] No hardcoded secrets or PII.

#### Findings Summary (Blocker / Major / Minor)
| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| Blocker | INT-001 pilot PR/CI | The PR head and CI results for the pilot are pending. | Record the PR URL, head SHA and three-OS CI run URLs for that revision before requesting Gate 3. |

#### Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer]`
- **Decision:** `Pending` — requires the pilot evidence above and independent re-review.
- **Timestamp:** Pending human decision.
