---
review_id: REV-011
pr_ref: none (local branch fix/PLAN-011-import-isolation, not pushed) — current round reviewed 0c5425a..535fa7325b0210af362b84bbd691715a275d38e8
spec_ref: PLAN-011
verdict: approved_for_human_gate
---

# Code & Security Review Report

> **บันทึกปัจจุบัน: รอบที่ 2** ตรวจ `535fa7325b0210af362b84bbd691715a275d38e8` (ส่วนที่เปลี่ยนจาก `0c5425a`; base ของ change คือ `f80092e`) ยังไม่ push จึง **ไม่มี PR และไม่มี CI run** รอบที่ 1 เก็บไว้ท้ายเอกสารเป็นประวัติ
>
> | ส่วน | สถานะที่ `535fa73` |
> | :--- | :--- |
> | Code review (`code-reviewer-agent`) | `approved_for_human_gate`: Blocker 0 / Major 0 / Minor 8 |
> | Security re-audit (`security-audit-agent`) | `approved_for_human_gate`: ไม่มี Blocker หรือ Major ที่ยังรอการตัดสิน โดยอาศัย sign-off ใน PLAN-011 §11 · Minor ใหม่: D-1, N-1 ถึง N-4 |
> | **Verdict รวม** | **`approved_for_human_gate` แบบมีเงื่อนไข** |
>
> **เงื่อนไขของ verdict:** ข้อระดับ High **ยังไม่ได้แก้** (BLK-1 และความเสี่ยงตาม §8 ข้อ 3 ที่ขยายใน §11) เป็นการรับความเสี่ยง ไม่ใช่การปิดข้อ **ห้ามอนุมัติ Gate 3 หรือ merge ถ้าตารางยืนยันในหัวข้อ Gate 3 Human Sign-Off ยังไม่ถูกกรอกโดย Human ผู้อนุมัติ** ถ้าผู้อนุมัติไม่ยืนยันการรับ BLK-1 หรือข้อ High อื่น ให้ถือว่า verdict เป็น `blocked_security`

## Review Scope & Traceability Check
- **Intent / Spec:** N/A (Framework Change · security fix) / `docs/plans/plan-011-import-isolation.md` (รวม §11)
- **Verdict รวม:** `approved_for_human_gate` แบบมีเงื่อนไข (Blocker ที่รอการตัดสิน 0, Major ที่รอการตัดสิน 0, ความเสี่ยงที่รับไว้ยังเปิดตามตาราง Gate 3)
- **Diff Summary (`0c5425a..535fa73`):** 4 ไฟล์ +251 / -11: `tests/test_import_isolation.py` (+6 / -1), แผน (+24 / -6), digest (+4 / -4), เอกสารรีวิวรอบที่ 1 (+217) ไม่มี production code, workflow หรือ git hook เปลี่ยน
- เอกสารรีวิวที่ commit ตรงกับฉบับที่รอบที่ 1 เขียนไว้ใน working tree ก่อนเริ่มรอบนี้
- **Base ปัจจุบัน:** `origin/main` ขยับเป็น `9c801eb` (PR #17, #18) ไม่มีไฟล์ซ้อนกับ change นี้ การเปลี่ยนใน `AGENTS.md` เป็นแถว mapping เรื่องที่เก็บความรู้และ product checkout ไม่กระทบ change นี้ ทดลอง merge ในสำเนาชั่วคราวไม่ conflict และ unit test, eval, validator และการตรวจ digest ตาม workflow ผ่านทั้ง 3.14 และ 3.11 **ไม่ต้อง rebase เพื่อความถูกต้อง** แต่มีข้อความในแผนที่ล้าสมัย (m10)

## Spec Compliance & Architectural Drift

| ข้อ | ผลรอบที่ 2 |
| :--- | :--- |
| M1 (ครอบคลุมจุดโหลดจาก source) | **ปิด** มี 7 จุด และ test มีกรณีครบทั้ง 7 ถอยกลับทีละจุดในสำเนาแล้ว test fail ที่ subTest ของจุดนั้นทุกจุด |
| m8 (เอกสารล้าสมัย) | **ปิดในข้อที่ระบุ:** `status`, สถานะใน §9, คำอธิบายเรื่องลำดับเวลาของ §9, สถานะรีวิวและข้อยกเว้น exit code ใน digest ส่วนที่เหลือย้ายเป็น m10 |
| §9 ผู้ apply และ commit protected path | บันทึกในแผนแล้ว ยืนยันจาก repository ไม่ได้ |
| §11 ผลรีวิวรอบที่ 1 และรายการที่แก้ | ตรงกับบันทึกรอบที่ 1; คำอ้างว่าถอยกลับ 7 จุดแล้ว fail ทั้ง 7 ยืนยันได้; ยืนยันว่าไม่มีโค้ดเปลี่ยน |
| §11 security sign-off | มีบันทึกของ Human Maintainer ครอบ BLK-1, MAJ-1, MAJ-3 และขยายข้อรับความเสี่ยงใน §8 ข้อ 3 ผู้ตรวจทั้งสองยืนยันได้เพียงข้อความที่ผู้ implement บันทึกไว้ในแผน ยืนยันข้อความแชตต้นฉบับ ผู้อนุมัติ และผู้ commit ไม่ได้ |
| MAJ-2 (ข้อความด้านความปลอดภัย) | **ปิด** ตาม security re-audit |
| §1 เป้าหมายฉบับแก้ | ไม่ขัดกับผลทดสอบพฤติกรรมบน macOS |
| §5 ข้อ 7 (encoding บน Windows) | ยังเปิด รอหลักฐานบน Windows |
| การเปิดเผยในข้อความ | §11 ข้อ 3 ตัดสินแล้ว: land เป็น PR เดียว และบันทึกสาธารณะระบุว่ายังมีข้อ High ค้างโดยไม่บอกวิธี code review ไม่พบส่วนที่เกินขอบเขตในข้อความที่แก้ของฉบับล่าสุด ส่วน security audit บันทึก D-1 และ N-1 ไว้ (รายละเอียดเก็บนอก repository) การ publish ย้อนกลับไม่ได้ |
| digest | `--digest-file` ผ่าน |

## Verification Evidence (Tests & Linters)

รันบน clone ชั่วคราวที่ `535fa73`, `SDLC_TRACE_DIR` ชั่วคราว, macOS, 2026-11-27 (Asia/Bangkok)

| Command | 3.14.10 | 3.11.18 |
| :--- | :--- | :--- |
| `python -m unittest discover -s tests -v` | 259 run: 256 pass, 0 fail, 3 skip | 259 run: 256 pass, 0 fail, 3 skip |
| `scripts/sync-adapters.py --check`, `validate-context-budget.py`, `validate-contracts.py --check-defaults` | PASSED | PASSED |
| `evals/run_evals.py --mode contract` | PASSED 10/10 | PASSED 10/10 |
| `scripts/validate_work_item.py --digest-file <digest>` | PASSED | PASSED |
| test ใหม่บน `f80092e` | 6 run, failures 140, errors 4 (ระดับ subTest); กรณีจุดโหลดแดงครบ 7 | เหมือนกัน |
| กรณีควบคุมของ mutation (ไม่แก้อะไร) | `tests.test_import_isolation` ผ่าน | ผ่าน |
| ถอยกลับจุดโหลดทีละจุด 7 จุด | fail 7 / 7 | fail 7 / 7 |
| ทดลอง merge กับ `9c801eb`: unit test | 259 run, 3 skip, ผ่าน | เหมือนกัน |
| ทดลอง merge: `evals/run_evals.py` และ digest loop ของ workflow | PASSED | PASSED |

`git diff --check` ของ `0c5425a..535fa73` และ `f80092e..535fa73` ผ่าน mutation อื่นของรอบที่ 1 ไม่ได้รันซ้ำ เพราะโค้ดและ test ส่วนที่เกี่ยวข้องไม่เปลี่ยน

## Test Oracle Integrity Check
- [x] บรรทัดเดียวที่ถูกแทนคือ label ของ subTest (เพิ่มชื่อ entry) กรณีเดิม 3 กรณีคงอยู่ เพิ่ม 4 กรณี assertion เดิมไม่เปลี่ยน
- [x] ไม่มีไฟล์ test อื่นเปลี่ยน
- [x] กรณีใหม่ fail บน baseline และ fail เมื่อถอยกลับจุดที่ครอบ

## Security & OWASP Findings

### ผล security re-audit รอบ 2 (`security-audit-agent`, `535fa73`): `approved_for_human_gate`
- ไม่มีการเปลี่ยนโค้ด production จาก `0c5425a`; unit test 259 ข้อผ่าน (skip 3) และ contract eval 10/10 บน macOS (Python 3.11, 3.14)
- M1: test จับการถอยกลับได้ครบทั้ง 7 จุดโหลด · MAJ-2: ข้อความในแผนปรับตรงพฤติกรรมแล้ว
- SEC-B1: ปิดตามขอบเขตที่แผนระบุ บน macOS
- ความเสี่ยงที่ Maintainer รับไว้ตามบันทึกในแผน §11 ยังไม่ได้แก้ รวมข้อระดับ High
- ไม่มี Blocker หรือ Major ที่ยังรอการตัดสิน · ก่อน Gate 3: อัปเดต review record และ CI ต้องผ่าน
- ยังไม่ได้ตรวจ: CI, Windows, Linux, Python 3.10/3.12 และ agent client จริง

### การตัดสิน verdict รวม (code reviewer)
- [review-gate.schema.yaml](../contracts/review-gate.schema.yaml) ระบุให้ block เมื่อมี Critical / High ที่ "remains open" และ **ไม่มีข้อความเรื่อง waiver** อ่านตามตัวอักษรอย่างเดียว BLK-1 ยังเปิดอยู่
- skill `owasp-security-review` ระบุว่าห้าม waive อัตโนมัติ "without explicit human security sign-off" จึงมีทางรับความเสี่ยงโดย Human ที่ชัดแจ้ง และ §11 บันทึก sign-off ที่อ้าง ID
- `approved_for_human_gate` หมายถึงพร้อมให้ Human ตัดสิน ไม่ใช่การอนุมัติ การคง `blocked_security` จนกว่าผู้อนุมัติจะยืนยันจะวนเป็นวงกลม เพราะการยืนยันเกิดที่ gate นั้น
- จุดอ่อนของข้อสรุปนี้: หลักฐานการรับความเสี่ยงเป็นข้อความที่ผู้ implement บันทึก จึงกำหนดให้ผู้อนุมัติยืนยันตาม ID ในตาราง Gate 3 ก่อนอนุมัติ agent ไม่ได้ waive ข้อใดเอง

### ความเสี่ยงที่รับไว้ (ยังไม่ได้แก้)

| ID | Severity | สถานะ |
| :--- | :--- | :--- |
| BLK-1 | High | รับไว้ตาม §11 รอยืนยันที่ Gate 3 |
| §8 ข้อ 3 รวมส่วนขยายใน §11 | High | รับไว้ตาม §8 และ §11 รอยืนยันที่ Gate 3 |
| MAJ-1 | Medium | รับไว้ตาม §11 รอยืนยันที่ Gate 3 |
| MAJ-3 | Medium อาจเป็น High (ยังไม่ยืนยัน) | รับไว้ตาม §11 รอยืนยันที่ Gate 3 |
| SEC-M4 | Medium | เลื่อนตั้งแต่ Gate 2 |

- [x] ไม่พบ secret หรือ PII ในส่วนที่เปลี่ยนจากการอ่าน
- [ ] AuthN/AuthZ และขอบเขตการคุ้มครอง: ยังมีข้อเปิดตามตารางข้างบน

## Findings Summary (Blocker / Major / Minor)

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Blocker** BLK-1 (High, มีมาก่อน) | รายละเอียดไม่เปิดเผยตาม §11 ข้อ 3 | รับความเสี่ยงไว้ (§11) **ยังไม่ได้แก้** รอการยืนยันที่ Gate 3 | ยืนยันในตาราง Gate 3 และเปิดแผนติดตาม |
| **Major** MAJ-1, MAJ-3 | รายละเอียดไม่เปิดเผยตาม §11 ข้อ 3 | รับความเสี่ยงไว้ (§11) ยังไม่ได้แก้ (MAJ-3 ยังไม่ยืนยัน) · M1 และ MAJ-2 ปิดแล้ว · code review ไม่พบ Major ใหม่ | ยืนยันในตาราง Gate 3 |
| Minor m1, m3, m4, m5, m6, m7, m9 | ตามรอบที่ 1 | ยังเปิด (แผน §11 เลื่อนไปประเมินในแผนถัดไป) ส่วน m7: จุดโหลดที่เพิ่มในอนาคตจะไม่ได้กรณีทดสอบโดยอัตโนมัติ | ติดตามในแผนถัดไป |
| Minor m10 (Docs) | แผน §6 และ §11, digest §2 | ข้อความเรื่อง PR #18 ล้าสมัยหลัง merge; follow-up ของความเสี่ยงที่รับไว้ยังไม่มีเลขแผนหรือกำหนดเวลา และแผนใช้เลขถัดไปกับงานค้างอื่นอยู่แล้ว; ตารางไฟล์ใน digest ไม่มีเอกสารรีวิว | แก้ก่อนเปิด PR หรือที่ closeout (เกี่ยวกับ N-2) |
| Minor D-1 (security) | รายละเอียดเก็บนอก repository | ข้อสังเกตด้านการเปิดเผย | Human ตัดสินก่อน push |
| Minor N-1 (security) | รายละเอียดเก็บนอก repository | ข้อสังเกตด้านการเปิดเผย | Human พิจารณาก่อน push |
| Minor N-2 (security) | แผน §11 | บันทึกการรับความเสี่ยงยังไม่ครบสำหรับการติดตาม (เกี่ยวกับ m10) | กรอกในตาราง Gate 3 |
| Minor N-3 (security) | เอกสารนี้ | บันทึกรีวิวต้องมีผลรอบนี้และอ้าง sign-off | อัปเดตแล้วในฉบับนี้ ยังไม่ commit และ security audit ยังไม่ได้ตรวจซ้ำ |
| Minor N-4 (security) | รายละเอียดเก็บนอก repository | ความถูกต้องของข้อความในเอกสาร (เกี่ยวกับ MIN-1 รอบก่อน) | ประเมินในแผนถัดไป |
| Minor MIN-1 ถึง MIN-5 (security รอบ 1) | รายละเอียดเก็บนอก repository | ยังเปิด เลื่อนตาม §11 | ประเมินในแผนถัดไป |

## Council Pressure-Test
- **Lenses Used:** Contrarian, Executor, Outsider (โมเดลเดียวสวมหลายมุม)
- **Preserved Dissent (Contrarian):** "High findings ship unfixed on the strength of a sign-off that exists, as far as any reviewer can verify, only as text the implementer wrote; a contract that says High must not remain open is being satisfied by interpretation."
- **Executor:** change ปิด SEC-B1 ตามขอบเขตและไม่มีโค้ดที่ต้องแก้ การถือไว้ไม่ลดความเสี่ยงของข้อที่มีมาก่อน ให้ Human ยืนยันและเปิดแผนติดตาม
- **Outsider:** คำว่า `approved_for_human_gate` อาจอ่านว่าปลอดภัยแล้วหรืออนุมัติแล้ว ซึ่งไม่ใช่ทั้งสองอย่าง ต้องอ่านคู่กับเงื่อนไขต้นเอกสาร
- **Blind-Spot Check:** review contract ไม่มีรูปแบบบันทึก waiver (ใครรับ ข้อใด ถึงเมื่อไร) จึงต้องสร้างตาราง Gate 3 เอง เสนอเป็น follow-up ของ framework ที่ closeout (แก้ contract ต้องผ่านกระบวนการของ protected path)
- **Verdict & One Next Step:** `approved_for_human_gate` แบบมีเงื่อนไข ข้อคัดค้านข้างบนไม่ถูกลดน้ำหนัก ตารางยืนยันคือคำตอบต่อข้อนั้น ขั้นถัดไป: Human ตัดสิน D-1 ก่อน push

## ที่ยังไม่ได้ตรวจ
- CI, Windows, Linux, Python 3.10, 3.12, 3.13, FastAPI endpoint test, Docker, live eval, พฤติกรรมของ agent client จริง
- หลักฐานการอนุมัติและ sign-off ในแชท, ผู้ apply และ commit
- code review ไม่ได้ทำซ้ำการประเมิน D-1, N-1 ถึง N-4 ของ security audit ส่วนการทดสอบข้อที่รับความเสี่ยงไม่ได้รันซ้ำในรอบนี้เพราะโค้ด production ไม่เปลี่ยน

## เงื่อนไขก่อน push และก่อนขอ Gate 3

**ก่อน push**
1. Human ตัดสิน D-1 (ตัวเลือกอยู่ในรายงาน security นอก repository)
2. Human อ่านข้อความที่จะ publish ในมุมการเปิดเผย (รวม N-1, PR title และ description)
3. Commit เอกสารรีวิวฉบับนี้ หากแก้โค้ด, test หรือข้อความในแผน หรือ SHA เปลี่ยน ต้องตรวจส่วนที่เปลี่ยนบน SHA ใหม่

**ก่อนอนุมัติ Gate 3**
4. CI ผ่านครบ 6 jobs บน head ที่เปิด PR พร้อมหลักฐานบน Windows และปิด §5 ข้อ 7
5. ผู้อนุมัติกรอกตารางยืนยันการรับความเสี่ยงด้านล่างครบทุกแถว
6. Agent trace summary / PR description ตาม template ของ repository

## Gate 3 Human Sign-Off

### >>> ต้องกรอกโดย Human ผู้อนุมัติ: ยืนยันการรับความเสี่ยงตาม ID <<<

agent ห้ามกรอกแทน ทุกช่องที่เป็น `Pending` ต้องถูกตัดสินก่อนอนุมัติ Gate 3

| ID | Severity | ยอมรับความเสี่ยง (Yes / No) | แผนติดตาม / ผู้รับผิดชอบ / กำหนดทบทวน | หมายเหตุ |
| :--- | :--- | :--- | :--- | :--- |
| BLK-1 | High | `Pending` | `Pending` | |
| §8 ข้อ 3 รวมส่วนขยายใน §11 | High | `Pending` | `Pending` | |
| MAJ-1 | Medium | `Pending` | `Pending` | |
| MAJ-3 | Medium อาจเป็น High | `Pending` | `Pending` | ถ้ายืนยันภายหลังว่าเป็น High การรับยังมีผลหรือไม่: `Pending` |
| SEC-M4 (เลื่อน) | Medium | `Pending` | `Pending` | |

- **ผู้ยืนยันการรับความเสี่ยง:** `Pending`
- **เวลาและหลักฐาน:** `Pending`

### การตัดสิน Gate 3
- **Reviewer:** `[Human Maintainer]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`

---

## ประวัติ: รอบที่ 1 (`0c5425a`)

> เนื้อหาด้านล่างเป็นบันทึกของรอบที่ 1 ณ เวลานั้น (verdict รวม `blocked_security`) ไม่ได้แก้ถ้อยคำ ปรับเฉพาะระดับหัวข้อ สถานะปัจจุบันให้ดูรอบที่ 2

> **SHA ที่ตรวจ:** `0c5425ac4a1fbdbdac0571c47d5ab3855769d5a6` เทียบกับ base `f80092e6a9a40e83de2bd06d4d6232ec4ae3deae` ยังไม่ push จึง **ไม่มี PR และไม่มี CI run** `spec_ref` ใช้ `PLAN-011` เพราะ Framework Change นี้ไม่มี `SPEC-xxx`
> **Verdict รวม: `blocked_security`** เพราะ security re-audit พบ Blocker 1 ข้อ (BLK-1, High) ที่ยังเปิดอยู่ (details withheld pending maintainer decision)
> | รอบตรวจ (SHA เดียวกัน) | Verdict | Blocker / Major / Minor |
> | :--- | :--- | :--- |
> | Code review (`code-reviewer-agent`) | `changes_requested` | 0 / 1 (M1) / 8 |
> | Security re-audit (`security-audit-agent`) | `blocked_security` | 1 / 3 / 5 (ความเสี่ยงที่รับไว้ 1 ข้อ High และ SEC-M4 ที่เลื่อน ไม่นับรวม) |
>
> BLK-1 มีมาก่อน PLAN-011 และเกิดเหมือนกันบน base ไม่ได้เกิดหรือแย่ลงจาก change นี้ ส่วน code review **ไม่พบว่าโค้ดทำงานผิดจากเกณฑ์ §5 ที่ตรวจได้** โดย M1 เป็นการขาด test บังคับ ซึ่งแก้ได้ใน `tests/`
> **การเปิดเผย:** repository เป็น public และ Maintainer ยังไม่ได้ตัดสินเรื่องการเปิดเผย จึงไม่ควร push ก่อนมีการตัดสิน
> **เรื่อง CI:** การยังไม่มี CI, Windows, Linux และ Python 3.10 / 3.12 ไม่นับเป็น Blocker ในรอบนี้ (ต่างจาก PLAN-009) เพราะ PLAN-011 §5 กำหนดให้รีวิวบน commit ในเครื่องก่อน push จึงเป็นเงื่อนไขก่อน Gate 3 ส่วนหลักฐานในเครื่องรันใหม่ทั้งหมดในรอบนี้

### Review Scope & Traceability Check
- **Intent / Spec:** N/A (Framework Change · security fix) / `docs/plans/plan-011-import-isolation.md` (Gate 2 ใน §8, Amendment A1 ใน §10)
- **Diff Summary:** 17 ไฟล์ +704 / -56: protected 4 ไฟล์ (`scripts/sdlc_hook.py`, `scripts/bin/sdlc-hook`, `scripts/bin/sdlc-hook.cmd`, `scripts/sdlc_guard/precommit.py`), entry script อื่น 10 ไฟล์ (รวม `evals/run_evals.py`), test ใหม่ 1 ไฟล์, แผนและ digest
- **Review order:** ตรวจ raw diff, รัน check และ mutation test ก่อน แล้วจึงอ่าน digest
- **Tier:** High-Risk (Framework) ใช้ lens ของ `council-pressure-test`
- **ขอบเขตที่ไม่ครอบคลุม:** การวิเคราะห์ความปลอดภัยเชิงลึกเป็นของ `security-audit-agent` ซึ่งรวมผลไว้ในหัวข้อ Security & OWASP Findings
- **Base ปัจจุบัน:** ระหว่างตรวจ `origin/main` อยู่ที่ `4d52a3b` (PR #17 แก้เฉพาะ `work/INT-001/`) ไม่มีไฟล์ซ้อนกับ diff นี้ ทดลอง merge ในสำเนาชั่วคราวไม่ conflict และ unit test, eval, validator ผ่านทั้ง 3.14 และ 3.11
- **Verdict รวม:** `blocked_security` (Blocker 1, Major 4, Minor 8 จาก code review และ 5 จาก security audit ซึ่งอาจซ้อนกัน)

### Spec Compliance & Architectural Drift

> ตารางในหัวข้อนี้ตรวจว่าโค้ดตรงกับข้อความของแผนหรือไม่ **ไม่ได้ยืนยันว่าข้อความด้านความปลอดภัยในแผนครอบคลุมครบ** ดู MAJ-2

#### §4 Scope

| ข้อ | ผล | หลักฐาน / หมายเหตุ |
| :--- | :--- | :--- |
| 4.1 (1) ก่อนบล็อกแยก path ใช้เฉพาะ `os`, `sys` และไม่มี future import | ตรง | ทั้ง 11 entry script และ structure test ตรวจ |
| 4.1 (2) ไม่ใส่ `scripts/` / `evals/` กลับเข้า `sys.path` | ตรงในโค้ดปัจจุบัน | test บังคับได้เพียงบางรูปแบบ (m4) |
| 4.1 (3) โหลดด้วย path, module ไฟล์เดียว compile จาก source, package โหลดปกติ | ตรงในโค้ดปัจจุบัน | test บังคับ 3 จาก 7 จุดโหลด (M1) |
| 4.1 (4) subprocess และ launcher ใช้ `-I` | ตรงในโค้ดปัจจุบัน | subprocess ที่เรียก Python ของ framework ใน `scripts/`, `evals/` มีจุดเดียวใน `sdlc_guard/precommit.py` ไม่มี test บังคับ (m1) |
| 4.1 (5) เทียบ path ด้วย `normcase(realpath())` | ตรง | filter ใช้ `normcase(realpath(p or curdir))` เทียบ `normcase(_HERE)` โดย `_HERE` ผ่าน `realpath` แล้ว (m4) |
| 4.1 (6) คง line ending | ตรง | `ls-files --eol`: `sdlc-hook` เป็น LF, `.cmd` ใน working tree เป็น CRLF 28/28 บรรทัดตาม `.gitattributes`; ไม่มี mode change |
| 4.2 รายการไฟล์และระดับคุ้มครอง | ตรง | ครบตามตารางบวก `scripts/worktree.py` ที่บันทึกใน §9; การจัดกลุ่มตรงกับ `policy.json` |
| 4.2 ผู้ลงมือ (Human apply patch) | **ยืนยันจาก repository ไม่ได้** | ดูจาก Git ไม่ได้ว่าใคร apply หรือใช้ตัวแปร override ตอน commit |
| 4.2 inline `python -c` ใน `validate.yml` | **ตัดสิน: ไม่เป็นเงื่อนไขของ change นี้** | เสนอแก้เป็น follow-up |

#### §5 เกณฑ์ตรวจรับ

| ข้อ | ผล | หลักฐาน / หมายเหตุ |
| :--- | :--- | :--- |
| บทนำ: test ใช้สำเนาชั่วคราว, `sys.executable`, `SDLC_TRACE_DIR` ชั่วคราว, คัดลอกครั้งเดียวต่อ class | ตรง | `setUpClass`; ไม่วางไฟล์ใน tree จริง |
| บทนำ: ชื่อทดสอบหลักแดงบน baseline | ตรงบน macOS | ชื่อหลักทั้งสามแดงบน `f80092e` (3.14 และ 3.11) ชื่อเสริมแดงเฉพาะ check ที่ import ถึง กรณี Windows ยังไม่ยืนยัน |
| 1 fail บน `f80092e` ผ่านหลังแก้ | ตรง | baseline: 5 จาก 6 test fail (failures 136, errors 4 ระดับ subTest), กรณีควบคุมผ่าน |
| 2 ผ่าน launcher และเรียกตรงไม่มี `-I` | ตรง | hook และ pre-commit ทั้งสองทาง; validator และ eval เรียกตรง `worktree.py` ถูกตรวจเฉพาะเชิงโครงสร้าง (m4) |
| 3 launcher บล็อก protected write (exit 2) | ตรง | |
| 4 pre-commit ปฏิเสธ protected path ที่ stage | ตรง | exit 1 พร้อมข้อความ |
| 5 validator fail เมื่อ input ผิด ผ่านเมื่อถูก | ตรง | `validate-contracts.py` และ `validate_work_item.py` มีทั้งสองด้าน; `sync-adapters --check` และ context budget มีเฉพาะด้านผ่านใน test ใหม่ |
| 6 test เดิมไม่ถูกลดความเข้ม | ตรง | ดู Test Oracle |
| 7 encoding บน Windows | **code review: ไม่จำเป็นต้องแก้ `sdlc_guard/doctor.py`; ยังรอยืนยันบน Windows** | ดูหัวข้อด้านล่าง |
| 8 การแยก path ตอนถูก import ไม่ทำให้ผู้ import อื่นพัง | ผู้ import ที่มีอยู่ไม่พัง | รัน test ทั้งชุดและรันทีละ module (17 module) ผ่าน แต่มี side effect ต่อผู้ import ใหม่ และแผน / digest ไม่ได้บันทึกหลักฐานข้อนี้ (m5) |
| 9 change digest | ตรง | `--digest-file` ผ่าน |
| ลำดับ (กรณี ก) | อยู่ที่ขั้นรีวิว | commit ในเครื่องแล้ว ยังไม่ push |

#### §5 ข้อ 7: ผลของ `-I` ต่อ encoding

- `-I` ไม่อ่านตัวแปร `PYTHON*` จึงกระทบเฉพาะเครื่องที่ตั้งค่าเอง เครื่อง Windows ที่ใช้ค่าเริ่มต้นไม่เปลี่ยนจากเดิม
- การอ่านไฟล์ข้อความใน `scripts/` และ `evals/` ระบุ `encoding` แล้ว หรือเปิดแบบ binary; hook ตั้ง stdout / stderr เป็น UTF-8 และอ่าน stdin เป็น bytes; ข้อความ stdout ของ validator สามตัวที่ pre-commit เรียกเป็น ASCII ส่วน stderr ของ Python ใช้ `backslashreplace`; ข้อความของ guard ที่โหลดไม่ได้ถูกพิมพ์ก่อน reconfigure แต่ไป stderr และ JSON แบบ ASCII
- จำลองบน macOS (3.11, `-I -X utf8=0`, locale ISO-8859-1): validator สามตัว, `doctor --strict` และ `precommit` ผ่าน
- `_git` ใน `sdlc_guard/doctor.py` decode ด้วย locale แต่รับเฉพาะ version ของ git และค่า config สองค่า ความเสี่ยงมีเฉพาะค่า config ที่ไม่ใช่ ASCII บนเครื่องที่เคยพึ่ง UTF-8 mode และส่งผลต่อ `doctor` / `setup` / `session-start` ไม่ใช่ tool check การใส่ `encoding="utf-8"` เป็น hardening ที่ทำภายหลังได้
- ไม่ได้รันบน Windows จริง CI ไม่ได้ตั้งตัวแปรเหล่านี้ จึงไม่ใช่หลักฐานของกรณีนี้
- security audit ถือว่าข้อนี้ยังค้างจนมีหลักฐานบน Windows จึงใช้ผลที่เข้มกว่า: **ยังเปิดอยู่** ข้อสรุปข้างบนเป็นผลจากการอ่านโค้ดและการจำลองเท่านั้น

#### §9 และ §10

| คำอ้าง | ผล |
| :--- | :--- |
| §9 `worktree.py` ถูกพบด้วย structure test บน baseline | ยืนยันได้ (fail บน `f80092e`) |
| §9 test ใหม่ fail บน baseline, กรณีควบคุมผ่าน | ยืนยันได้ |
| §9 259 tests (skip 3) บน 3.14.10 / 3.11.18, eval 10/10, validators, `.cmd` CRLF | ยืนยันได้บน SHA ที่ commit |
| §9 SHA-256 ของ patch | security audit ตรวจแล้วว่า patch ที่อนุมัติ apply บน base ตรงกับไฟล์ protected 4 ไฟล์ใน commit ทุก byte; code review ไม่ได้ตรวจซ้ำ |
| §9 "ยังไม่ได้ทำ: commit" และ front matter `status` | **ไม่ตรงกับสถานะปัจจุบัน** (m8) |
| §10 คำสั่งตรวจ, ไม่มี argument, `precommit`, `commit-msg` จบ exit 2 พร้อม `BLOCKED` | ยืนยันได้ด้วย test ทั้ง entry และ launcher; ทาง wrapper `scripts/precommit.py` จบ exit 1 ตามข้อ "ถูก import ให้ raise" ซึ่ง Git ยังปฏิเสธ commit |
| §10 Antigravity ตอบ `deny` exit 0 | ยืนยันได้ |
| §10 `trace`, `session-start` exit 0 พร้อม WARNING | exit code และ stdout มี test; ข้อความ WARNING ยืนยันจากการอ่านโค้ด |
| §10 override ของ Human มีผลเฉพาะคำสั่งตรวจ tool | ยืนยันได้ (test ครอบ `pretooluse`, Antigravity, `precommit`; `commit-msg` ยืนยันจากโค้ด) |
| §10 ถูก import ให้ raise | ยืนยันได้ด้วยการรันเอง ไม่มี test (m3) |
| §10 เพิ่ม 2 test, fail ก่อนแก้ | จำนวนถูกต้องและ fail บน `f80092e`; การ fail เทียบกับ patch ก่อน A1 ยืนยันไม่ได้ |
| §2 ผล prototype | ยืนยันซ้ำไม่ได้ (สำเนาอยู่นอก repository) |

A1 ตรวจตามขอบเขตที่ §10 ระบุ คือการโหลด guard ตอนเริ่ม

#### พฤติกรรมของ entry script และความเข้ากันได้

- **เทียบ baseline กับ head (216 ชุดต่อ interpreter, 3.14 และ 3.11):** เรียกตรง, เรียกด้วย path เต็มจากที่อื่น, เรียกจากในโฟลเดอร์ของ script, เรียกด้วย `-I` และคำสั่ง hook 17 แบบกับ stdin 4 แบบทั้ง launcher และ entry
  - คำสั่ง hook: ผลเหมือนกันทุกชุด
  - ต่างกัน 8 ชุด: 4 ชุดเป็น `validate-contracts.py` / `validate_work_item.py` ใต้ `-I` ซึ่ง baseline import ไม่ได้และ head ทำงานได้ (ดีขึ้น) อีก 4 ชุดเป็น traceback เดิมของ `sync-adapters.py --help` ที่ต่างเพียงรายละเอียด traceback (m9)
- **`setup.py`:** เรียกตรง, `-I`, launcher, shim `.sh` และ import ได้ exit 0 ทั้ง baseline และ head; `worktree.py create` / `cleanup` ได้ exit 0 ในสำเนา
- **ถูก import:** ทั้ง 11 ไฟล์ import ได้ แต่ head ลบโฟลเดอร์ของไฟล์ออกจาก `sys.path` ของผู้ import (m5)
- **Python 3.10 / 3.12 (ตรวจด้วยการอ่านและ static เท่านั้น):** `ast.parse(feature_version=(3,10))` กับไฟล์ Python ที่ตรวจไม่พบ error; การถอด future import ทำให้ annotation ประเมินทันที แต่การรันบน 3.11 ซึ่งประเมินทันทีเช่นกันผ่าน; ไม่พบ API เฉพาะ 3.11+; ไม่เห็นจุดที่คาดว่าต่างใน 3.12
- **Windows (อ่านโค้ดเท่านั้น):** `.cmd` เพิ่ม `-I` หลังตัวเลือก version ทั้งสามทางและคง `errorlevel` flow; การเทียบ path ใช้ `normcase` สองฝั่ง; test ใหม่เรียก `.cmd` ด้วย `cmd /c` ซึ่งยังไม่เคยรันจริง
- **Architecture:** ไม่มี dependency ใหม่ มีโค้ดซ้ำตามที่แผนยอมรับ (m7)

### Verification Evidence (Tests & Linters)

รันบน clone ใน temporary directory ที่ checkout `0c5425a`, ตั้ง `SDLC_TRACE_DIR` เป็น temporary directory, macOS ตรวจเมื่อ 2026-11-27 (Asia/Bangkok)

| Command | 3.14.10 | 3.11.18 |
| :--- | :--- | :--- |
| `python -m unittest discover -s tests -v` | 259 run: 256 pass, 0 fail, 3 skip | 259 run: 256 pass, 0 fail, 3 skip |
| รันทีละ module (`python -m unittest tests.<module>`, 17 module) | ผ่านทั้งหมด | ผ่านทั้งหมด |
| `scripts/sync-adapters.py --check` | PASSED | PASSED |
| `scripts/validate-context-budget.py` | PASSED | PASSED |
| `scripts/validate-contracts.py --check-defaults` | PASSED | PASSED |
| `evals/run_evals.py --mode contract` | PASSED 10/10 | PASSED 10/10 |
| `scripts/doctor.py` | exit 0 (WARN `hooks_path` ใน clone) | exit 0 (เช่นเดียวกัน) |
| `scripts/validate_work_item.py --digest-file <digest>` | PASSED | PASSED |
| `scripts/validate_work_item.py work/INT-001 --require-review` | PASSED | PASSED |
| test ใหม่บน `f80092e` | 6 run, fail ตามคาด; กรณีควบคุมผ่าน | เหมือนกัน |
| ชุด test เดิมบน `f80092e` | 253 run: 250 pass, 3 skip | เหมือนกัน |

`git diff --check f80092e..0c5425a` ผ่าน (exit 0) Test ที่ skip: Windows launcher 2 และ FastAPI optional 1

#### Mutation test (สำเนาชั่วคราว, 3.14, รันชุด test ทั้งหมด)

21 mutation: ตรวจจับได้ 9, รอด 12

| กลุ่ม | ผล |
| :--- | :--- |
| ถอด `-I` จาก launcher POSIX / จาก subprocess ของ pre-commit | รอดทั้ง 2 (m1) |
| เปลี่ยนวิธีโหลดไม่ให้ compile จาก source (7 จุด) | จับได้ 3, รอด 4: `validate-contracts` → `qa_report` และ wrapper `precommit`, `setup`, `sdlc_trace` → `sdlc_hook` (M1) |
| ถอดการ raise เมื่อถูก import (A1) | รอด (m3) |
| A1: คืน exit 1 / override ลามถึง pre-commit / จับเฉพาะ `Exception` | จับได้ทั้ง 3 |
| ถอดบล็อกแยก path (`sdlc_hook`, `worktree`) | จับได้ทั้ง 2 |
| ใส่โฟลเดอร์กลับหลังบล็อก (3 แบบ) | จับได้ 1, รอด 2 (m4) |
| ลดความเข้มของการเทียบ path (2 แบบ) | รอดทั้ง 2 บน macOS; ผลบน Windows ไม่ทราบ (m4) |
| เพิ่ม entry script ใหม่ที่ไม่มีบล็อกแยก path และเขียนบรรทัด main ต่างรูปแบบ | รอด (m4) |

### Test Oracle Integrity Check
- [x] diff เพิ่ม `tests/test_import_isolation.py` ไฟล์เดียว ไม่มีไฟล์ test เดิมถูกแก้หรือลบ
- [x] test ใหม่ fail บนโค้ดเดิมจริง และกรณีควบคุมแยกความล้มเหลวของ harness ออกได้
- ผู้เขียน test กับผู้ implement เป็น main session เดียวกันตามแผน ผู้ตรวจรอบนี้ไม่ได้เขียนโค้ดใน diff
- คุณภาพ: test เชิงพฤติกรรมครอบเส้นทางหลักดี (launcher, เรียกตรง, pre-commit ใน git ชั่วคราว, A1) ช่องว่างอยู่ที่การบังคับ invariant รายจุด (M1, m1, m3, m4)

### Security & OWASP Findings

#### ผล security re-audit (`security-audit-agent`, SHA `0c5425a`): `blocked_security`
- SEC-B1: กลไกที่รายงานไว้ปิดแล้วสำหรับโฟลเดอร์ entry script ตามการทดสอบบน macOS (Python 3.11, 3.14); test ใหม่ fail บน base และชุดทดสอบ 259 ข้อผ่าน (skip 3) บน head
- Amendment A1: พฤติกรรม fail-closed ตรงกับที่ระบุในกรณีที่ทดสอบ
- Blocker 1 ข้อ (BLK-1, High, มีมาก่อนการเปลี่ยนแปลงนี้) ต้องแก้หรือมี security sign-off ก่อน Gate 3 (details withheld pending maintainer decision)
- Major 3 ข้อ (MAJ-1 ถึง MAJ-3: ความครอบคลุมของการคุ้มครองและความถูกต้องของเอกสาร; details withheld pending maintainer decision) · Minor 5 ข้อ (เก็บในรายงานนอก repository)
- ความเสี่ยงคงเหลือที่ Maintainer รับไว้ที่ Gate 2 (§8 ข้อ 3): 1 ข้อ (High) พร้อม follow-up · SEC-M4 เลื่อน (Medium)
- ยังไม่ได้ตรวจ: Windows, Linux, Python 3.10/3.12, CI และพฤติกรรมของ agent client จริง

#### การประเมินของ code reviewer ต่อผลข้างต้น (สำเนาชั่วคราว, macOS)

| ID | การประเมิน |
| :--- | :--- |
| BLK-1 | **ยืนยันซ้ำได้** ทั้งบน base และ head รวมผลต่อการควบคุม เห็นด้วยกับ High และว่ามีมาก่อน; ไม่อยู่ในข้อความรับความเสี่ยงของ §8 |
| MAJ-1 | ยืนยันได้บางส่วน (ตรวจผลตัดสินของ guard; ไม่ได้ทำซ้ำผลต่อเนื่องทั้งหมด) เห็นด้วยกับระดับ |
| MAJ-2 | เห็นด้วยจากการอ่านเอกสาร ตาราง compliance ของ code review ไม่ได้จับข้อนี้ |
| MAJ-3 | ยังยืนยันไม่ได้ ตรวจได้เพียงบางเงื่อนไขประกอบ คงระดับตาม audit |

#### จาก code review
- SEC-B1 (High): เนื้อหาใน working tree ทำให้การควบคุมความปลอดภัยไม่ทำงาน — change นี้มุ่งแก้ในระดับการ import ผลการปิดอ้างตาม security audit ข้างต้น
- SEC-M4: การคุ้มครองการแก้ไฟล์ของ framework — นอก scope ตาม Gate 2
- [ ] AuthN/AuthZ และขอบเขตการคุ้มครอง: diff ไม่แตะ endpoint หรือสิทธิ์ แต่มี BLK-1 และ MAJ-1 ถึง MAJ-3 เปิดอยู่
- [x] ไม่พบ secret หรือ PII ใน diff จากการอ่าน (ค่าใน test เป็นค่าตัวอย่าง)

### Findings Summary (Blocker / Major / Minor)

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Blocker** BLK-1 (Security, High, มีมาก่อน) | details withheld pending maintainer decision | การคุ้มครองของ guard ไม่ครอบคลุมทุกกรณี ทำให้การควบคุมความปลอดภัยของ repository ถูกทำให้ไม่ทำงานได้ | แก้ หรือ Human ให้ security sign-off อย่างชัดแจ้งโดยอ้าง ID นี้ |
| **Major** MAJ-1 (Security, Medium) | details withheld pending maintainer decision | ความครอบคลุมของการคุ้มครองไม่ครบ (details withheld pending maintainer decision) | Human รับความเสี่ยงเป็นลายลักษณ์อักษรพร้อม follow-up หรือแก้ |
| **Major** MAJ-2 (Security / Docs) | แผน PLAN-011 | ข้อความด้านความปลอดภัยในเอกสารไม่ตรงกับพฤติกรรมทั้งหมด (details withheld pending maintainer decision) | แก้ข้อความ พร้อมกับ m8 |
| **Major** MAJ-3 (Security, Medium, อาจสูงกว่า, ยังไม่ยืนยัน) | details withheld pending maintainer decision | ความครอบคลุมของการคุ้มครองไม่ครบ (details withheld pending maintainer decision) | แก้ หรือยืนยันด้วยการทดสอบว่าไม่เป็นจริง |
| **Major** M1 (Test / Compliance) | `tests/test_import_isolation.py:181-206`; helper `_load` ใน entry script | PLAN-011 §3 ระบุเงื่อนไขของ ALT 1 ที่อนุมัติว่าบล็อกซ้ำใน entry script "ต้องมี test บังคับ" และ §4.1 (3) กำหนดให้ compile จาก source แต่ test บังคับเพียง 3 จาก 7 จุดโหลด จุดที่เหลือ 4 จุด รวม wrapper ของ pre-commit และ validator ที่ pre-commit เรียก เปลี่ยนวิธีโหลดได้โดยชุด test ยังผ่าน structure test ตรวจเฉพาะ 4 บรรทัดแรก ไม่ตรวจ body ของ helper | เพิ่ม test ให้ครบทุกจุดโหลด หรือบังคับด้วย static test ว่า helper ทุกสำเนาเหมือนกันและ compile จาก source แล้วยืนยันว่าการถอยกลับทั้ง 7 จุดทำให้ test fail |
| Minor m1 (Test) | `tests/test_import_isolation.py`, `scripts/bin/sdlc-hook`, `scripts/sdlc_guard/precommit.py` | invariant 4 (`-I`) ไม่มี regression test เพราะบล็อกแยก path บังผลไว้ ชั้นป้องกันนี้ถูกถอดได้โดย CI ยังเขียว (`.cmd` ไม่ได้ mutate แต่ test ไม่ได้ตรวจข้อความเช่นกัน) | เพิ่ม static assertion กับ launcher ทั้งสองและคำสั่ง subprocess |
| Minor m3 (Test) | `scripts/sdlc_hook.py:71-74` | ข้อกำหนด A1 "ถูก import ให้ raise" ไม่มี test | เพิ่ม test ที่ import ในสำเนาซึ่ง guard เสียและคาด exception |
| Minor m4 (Test) | `tests/test_import_isolation.py:31-59,121-155` | (ก) structure test ห้ามเพียงบางรูปแบบของการใส่โฟลเดอร์กลับ (ข) การหา entry script ผูกกับการเขียนบรรทัด main แบบเดียว (ค) `worktree.py` ไม่ถูกรันในกรณีทดสอบเชิงพฤติกรรม (ง) invariant 5 ไม่มี test ที่แยกผลได้บน POSIX | ตรวจด้วย AST ว่าไม่มีการแก้ `sys.path` นอกบล็อก, หา entry script ด้วย AST และเพิ่ม `worktree.py list` ในรายการรัน |
| Minor m5 (Bugs / Compliance) | บล็อกแยก path ในทั้ง 11 entry script | เมื่อถูก import บล็อกจะลบโฟลเดอร์ของตัวเองออกจาก `sys.path` ของผู้ import ผู้ import ที่เพิ่มโฟลเดอร์นั้นเองแล้ว import `validate_work_item` ต่อด้วย module ข้างเคียงอีกตัวตามชื่อ จะได้ `ModuleNotFoundError` (ทดลองแล้ว 3.14 และ 3.11) ผู้ import ที่มีอยู่ไม่พัง แต่ไม่มี test และแผน / digest ไม่บันทึกผลของ §5 ข้อ 8 | บันทึกว่าเป็นพฤติกรรมที่ยอมรับและใส่ test หรือจำกัดผลเมื่อถูก import หลังให้ security audit ยืนยันว่าไม่เปิดช่องคืน |
| Minor m6 (Bugs) | launcher ทั้งสอง, `scripts/sdlc_guard/precommit.py:89` | `-I` ทำให้ตัวแปร environment ของ Python อื่นนอกจาก encoding ไม่มีผลด้วย (`.gitlab-ci.yml` ตั้งไว้หนึ่งตัว) พฤติกรรม runtime จึงต่างจากเดิม แผนกล่าวถึงเฉพาะผลด้าน encoding | บันทึกผลข้างเคียงในแผน และตัดสินว่าจะคงพฤติกรรมเดิมหรือไม่ |
| Minor m7 (Maintainability) | `_load` ใน 8 ไฟล์, `_load_package` ใน 2 ไฟล์ | helper ซ้ำ (ปัจจุบันเหมือนกันทุกสำเนา) ไม่มีสิ่งบังคับให้ตรงกันต่อไป และถ้าโหลดล้มเหลว module ที่โหลดไม่ครบจะค้างใน `sys.modules` ทำให้ผู้เรียกซ้ำใน process เดิมข้ามการโหลด (จากการอ่านโค้ด; การรันตรงไม่กระทบ) | pop ออกจาก `sys.modules` เมื่อ exception และใส่ test ความเหมือน; ที่ closeout พิจารณาเพิ่มกฎ entry script ใหม่ใน `AGENTS.md` |
| Minor m8 (Docs) | แผน front matter และ §9, digest §3 และ §5 | `status: implemented_pending_protected_patch` และ "ยังไม่ได้ทำ: commit" ล้าสมัย; หัว §9 ลงเวลา 19:40:37 แต่มีผลของ A1 ซึ่งอนุมัติ 19:48:42; digest ยังบอกว่าไม่มีรีวิว และข้อความ "คำสั่งตรวจจบด้วย exit 2" ไม่กล่าวถึงข้อยกเว้นของ Antigravity (exit 0 พร้อม deny) | อัปเดตก่อนเปิด PR (เอกสารเท่านั้น) แก้พร้อมกับ MAJ-2 |
| Minor m9 (Bugs, มีอยู่ก่อน, นอก diff) | `scripts/sync-adapters.py` argparse help | `--help` จบด้วย `ValueError` ทั้ง baseline และ head | แก้ในงานแยก |

### Council Pressure-Test
- **Lenses Used:** Contrarian, Executor, Outsider (โมเดลเดียวสวมหลายมุม ไม่ใช่ผู้ตรวจหลายคน)
- **Preserved Dissent (Executor, ต่อ verdict รวม):** "BLK-1 predates this change and this change does not make it worse, yet holding the change back keeps both High issues open on main for longer." Maintainer ต้องชั่งข้อแลกเปลี่ยนนี้ตอนตัดสิน BLK-1
- **Contrarian (สนับสนุน M1):** "The tests prove today's code is isolated, not that it will stay isolated: twelve of twenty-one mutations pass the whole suite, including removing -I from the launcher, and a security fix whose layers can be deleted silently will be eroded by the next well-meaning refactor."
- **Executor:** พฤติกรรมของ change ตรงเกณฑ์ที่ตรวจได้ และ security audit รายงานว่า SEC-B1 ปิดแล้วตามขอบเขตที่ทดสอบ ขั้นที่เล็กที่สุดสำหรับส่วน code คือแก้ M1 ใน `tests/` มุมนี้เห็นว่าอ่าน §5 แบบราย module ก็ผ่านแล้ว และ BLK-1 ซึ่งมีมาก่อนแยกเป็นการตัดสินของ Human ได้ (ขยาย scope ผ่าน Gate 2, Framework Change แยก หรือ security sign-off)
- **Outsider:** คำว่า "SEC-B1 ปิดแล้ว" อาจทำให้เข้าใจว่าการควบคุมทั้งหมดปลอดภัยแล้ว ซึ่งไม่ใช่ ขอบเขตที่ปิดแคบกว่านั้น และยังมี Blocker เปิดอยู่
- **Blind-Spot Check:** code review ไม่พบ BLK-1 เพราะตรวจตามขอบเขตของ diff และเกณฑ์ในแผน และฝากการวิเคราะห์เชิงลึกไว้กับ security audit แผนและ test ไม่ได้ระบุผลที่ต้องการเมื่อถูก import (m5) หรือผลของ `-I` นอกเรื่อง encoding (m6) หลักฐานทั้งหมดมาจาก macOS ส่วนที่ขึ้นกับ OS ยังไม่เคยรัน
- **Verdict & One Next Step:** `blocked_security` ตามผลที่เข้มกว่า ไม่เฉลี่ยกับ code review และ High ไม่ถูก waive อัตโนมัติ การที่ BLK-1 มีมาก่อนไม่ปิดข้อนี้ ส่วนของ code review คง `changes_requested` สำหรับ M1 เพราะการอ่าน §5 ราย module ไม่ครอบเงื่อนไข "บล็อกซ้ำต้องมี test บังคับ" ใน §3 และ `-I` (m1) คงเป็น Minor เพราะเป็นชั้นเสริมหลังบล็อกแยก path ขั้นถัดไปขั้นเดียว: **Human Maintainer ตัดสินวิธีจัดการ BLK-1 และการเปิดเผย** ก่อน push

### ที่ยังไม่ได้ตรวจ
- CI บน GitHub / GitLab (ยังไม่ push), Windows รวม `sdlc-hook.cmd`, Linux, Python 3.10, 3.12 และ 3.13, FastAPI endpoint test, Docker, live eval
- พฤติกรรมของ harness จริง (Claude Code, Codex, Antigravity) เมื่อ hook คืนผล ตรวจเฉพาะ exit code และ output ของคำสั่ง
- ผู้ apply และ commit protected path, หลักฐานการอนุมัติในแชท, ผล prototype ใน §2 (การตรวจ patch เทียบ commit ทำโดย security audit และ code review ไม่ได้ทำซ้ำ)
- ผลตรวจของ security audit ที่ code reviewer ไม่ได้ทำซ้ำ ตามตารางการประเมินข้างต้น

### เงื่อนไขก่อน push และก่อนขอ Gate 3
1. Human Maintainer ตัดสินเรื่องการเปิดเผย (รวมวิธี land ใน §8 ข้อ 4 ว่ายังเหมาะสมหรือไม่) ก่อน push
2. BLK-1: แก้ (ขยาย scope ของ PLAN-011 ผ่าน Gate 2 หรือ Framework Change แยก) หรือ Human ให้ security sign-off รับความเสี่ยงเป็นลายลักษณ์อักษรโดยอ้าง ID นี้
3. MAJ-2: แก้ข้อความในแผนให้ตรงพฤติกรรม พร้อม m8
4. MAJ-1: รับความเสี่ยงเป็นลายลักษณ์อักษรพร้อม follow-up หรือแก้
5. MAJ-3: แก้ หรือยืนยันด้วยการทดสอบว่าไม่เป็นจริง
6. M1: เพิ่ม test บังคับ
7. หลังแก้โค้ด, test หรือเอกสาร: รีวิวส่วนที่เปลี่ยนบน SHA ใหม่ ทั้ง code review และ security ตามลำดับใน §5 แล้วจึง push
8. CI ผ่านครบ 6 jobs (3 OS × 3.10 / 3.12) บน head ที่เปิด PR พร้อมยืนยันว่า test ใหม่และ hook smoke test รันจริงบน Windows และปิด §5 ข้อ 7
9. Commit เอกสารรีวิว และเตรียม agent trace summary / PR description ตาม template ของ repository

### Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`
