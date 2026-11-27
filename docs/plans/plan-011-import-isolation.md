---
plan_id: PLAN-011
intent_ref: N/A (Framework Change · security fix)
spec_ref: this document (Framework Spec, Gate 2)
owner: main agent session (design และเตรียม patch) / Human maintainer (Gate 2, apply protected patch, Gate 3)
status: implemented_pending_protected_patch
created: 2026-11-27 18:55:13 +07 (Asia/Bangkok)
---

# PLAN-011 · Import Isolation ของ Python Entry Points

> **ห้าม push จนกว่าการรีวิวบน commit ในเครื่องจะผ่าน (§5)** repository นี้เป็น public และเอกสารนี้เกี่ยวกับ finding ความปลอดภัยที่ยังไม่ได้แก้
> **Route:** Framework Change → Gate 2 → Implement & Verify → security re-audit → Gate 3
> **Branch / Worktree:** `fix/PLAN-011-import-isolation` · `.worktrees/PLAN-011` (local เท่านั้น) · **Baseline:** `origin/main` `f80092e`

## 1. ปัญหา

**SEC-B1 (High)** จาก security audit รอบ INT-001 รอบ 8: entry script ของ guard, validator และ eval runner ไม่ได้แยกเส้นทาง import ออกจากเนื้อหาใน working tree ทำให้การควบคุมความปลอดภัยของ repository ถูกทำให้ไม่ทำงานได้ รายงานฉบับเต็มและวิธีทำซ้ำเก็บนอก repository

**เป้าหมาย:** ไฟล์หรือโฟลเดอร์ใหม่ใน `scripts/` หรือ `evals/` รวมถึง bytecode cache ของ module ไฟล์เดียว ต้องไม่ถูกรันแทนโค้ดจริงระหว่าง import ของ hook, pre-commit, validator และ eval (เป้าหมายนี้จำกัดที่การ import ดู §6 และ §8 ข้อ 3)

## 2. หลักฐานจาก prototype (สำเนาชั่วคราว, macOS, Python 3.11 และ 3.14)

| ข้อสังเกต | ผล |
| :--- | :--- |
| Baseline `f80092e` | ยืนยันปัญหาได้ทั้ง PreToolUse hook, launcher, validator และ pre-commit |
| วิธีย้าย path ไปต่อท้าย (ข้อเสนอเดิมใน audit) | **ไม่พอ** ยังมีกรณีที่หลุด เพราะ stdlib บางส่วน import แบบมีทางเลือกตาม OS และเวอร์ชัน รายชื่อไม่คงที่ |
| โหลด module ของเราด้วย path ตรง โดยไม่มีโฟลเดอร์ของเราใน `sys.path` | กรณีทดสอบถูกกันได้ |
| `from __future__` ก่อนบล็อกแยก path | **หลุด** เป็น import จริงและยังไม่ถูกโหลดตอนเริ่ม จึงต้องเอาออกจาก entry script |
| bytecode cache แบบไม่ตรวจ source ของ `qa_report` และ `sdlc_hook` | **หลุด** บน baseline และ prototype ที่โหลดแบบปกติ · กันได้เมื่อ compile จาก source |
| Prototype รุ่นสุดท้าย: entry 9 ตัว × ชื่อทดสอบ 9 ชื่อ × 2 เวอร์ชัน | ไม่มีไฟล์ทดสอบถูกรัน และ exit code เท่ากับกรณีไม่มีไฟล์ทดสอบ |
| Pre-commit ใน git repo ชั่วคราว (ผ่าน launcher และ wrapper) มี protected change ถูก stage | baseline: ผ่านทั้งที่ไม่ควรเมื่อมีไฟล์ทดสอบ · prototype: ปฏิเสธพร้อมข้อความ protected path ทุกกรณี (ไม่มีไฟล์, `__future__`, `json`, `json/`) |
| `sdlc-hook.cmd` และ `scripts/doctor.py` บน prototype | `.cmd` คง CRLF 28 บรรทัด · doctor exit 0 (มี WARN `hooks_path` เพราะสำเนาชั่วคราวยังไม่ได้ setup) |
| Unit tests บน prototype รุ่นสุดท้าย | 3.14: 253 ผ่าน (skip 3) · 3.11: 253 ผ่าน (skip 3) |
| flag `-I` | ตัดโฟลเดอร์ของ script ออกจาก `sys.path` ได้บน 3.9, 3.11, 3.14 (ทดสอบแยก) |

**ยังไม่ได้ตรวจ:** Windows (รวม `sdlc-hook.cmd`), Linux, Python 3.10/3.12/3.13, `scripts/setup.py` (แก้ git config จึงไม่ได้รันใน prototype) (หมายเหตุหลัง implement: `evals/run_evals.py` โหลด `validate-contracts` จาก source แล้ว และมี bytecode test ครอบคลุม ดู §9)

## 3. ทางเลือก

| ทางเลือก | ขอบเขต | ข้อดี / ข้อเสีย |
| :--- | :--- | :--- |
| **ALT 1 (แนะนำ)** Import isolation | launcher ใช้ `-I` และ entry script ทุกตัวแยก path แล้วโหลด module ภายในด้วย path ตรง | ครอบคลุมทั้ง hook, การเรียกตรงใน CI และ pre-commit, diff เล็ก / มีบล็อกซ้ำใน entry script ที่ต้องมี test บังคับ |
| ALT 2 ALT 1 + ขยาย guard policy (รวม SEC-M4) | เพิ่มการคุ้มครองการสร้างและแก้ไฟล์ใน `scripts/` | มีชั้นป้องกันสำรองและปิด SEC-M4 / เปลี่ยนสิทธิ์การทำงานของ agent ต้องตัดสินว่าใช้กับ role ใด และ diff ใหญ่ขึ้น |
| ALT 3 แก้ที่ launcher อย่างเดียว | เพิ่ม `-I` และแก้ entry ของ hook | เร็วสุด / การเรียก script ตรง (CI, eval, agent) ยังเปิดอยู่ จึงไม่แนะนำ |

## 4. Scope (ALT 1)

### 4.1 Invariants

1. ก่อนบล็อกแยก path ห้าม import module ที่ยังไม่ถูกโหลดตอน interpreter เริ่ม (ใช้ได้เฉพาะ `os`, `sys`) ห้ามมี `from __future__` ใน entry script
2. ห้ามใส่ `scripts/` หรือ `evals/` กลับเข้า `sys.path` ไม่ว่าตำแหน่งใด
3. module ภายในโหลดด้วย path ตรง module ไฟล์เดียว (`sdlc_hook`, `qa_report`, `validate-contracts`) ต้อง compile จาก source ไม่อ่าน bytecode cache ส่วน package `sdlc_guard` โหลดตามปกติ โดย `scripts/sdlc_guard/**` (รวม `__pycache__`) อยู่ใต้ protected glob
4. subprocess และ launcher ที่เรียก Python ของ framework ใช้ `-I`
5. เทียบ path ด้วย `os.path.normcase(os.path.realpath(...))` ทั้งสองฝั่ง
6. patch ต้องคง line ending เดิม (`sdlc-hook` เป็น LF, `sdlc-hook.cmd` เป็น CRLF)

### 4.2 ไฟล์และผู้ลงมือ

| ไฟล์ | ระดับคุ้มครองตาม `policy.json` | ผู้ลงมือ |
| :--- | :--- | :--- |
| `scripts/sdlc_hook.py` | protected | Human apply patch |
| `scripts/bin/sdlc-hook` (LF), `scripts/bin/sdlc-hook.cmd` (CRLF) | protected | Human apply patch |
| `scripts/sdlc_guard/precommit.py` | protected | Human apply patch |
| `scripts/validate-contracts.py`, `validate-context-budget.py`, `sync-adapters.py`, `doctor.py`, `precommit.py`, `setup.py`, `evals/run_evals.py` | ci_gate | main session |
| `scripts/validate_work_item.py`, `scripts/sdlc_trace.py`, `scripts/worktree.py` | ไม่ถูกคุ้มครอง | main session |
| `tests/test_import_isolation.py` (ใหม่) | test code | main session |

คำสั่ง inline `python -c` ใน `.github/workflows/validate.yml` (ขั้น trace) ใส่ `scripts` เข้า path เอง อยู่ในสภาพแวดล้อม CI ให้ผู้รีวิวตัดสินว่าจะแก้พร้อมกันหรือไม่ โดยค่าเริ่มต้นไม่แก้

## 5. Test-first และเกณฑ์ตรวจรับ

Test ใหม่คัดลอก repository ไป temporary directory แล้ววางไฟล์ทดสอบในสำเนาเท่านั้น ห้ามวางใน tree จริง

ชื่อหลักที่ต้องแดงบน baseline ทุก OS: `json` (ไฟล์), `json/` (package), `__future__` กรณีเสริม: ชื่อ module ที่ OS นั้นไม่มี (`msvcrt` บน POSIX, `pwd` บน Windows ซึ่งยังไม่ได้ยืนยัน) และ bytecode cache ของ module ไฟล์เดียว

ใช้ `sys.executable`, ตั้ง `SDLC_TRACE_DIR` เป็น temporary directory และคัดลอก repository ครั้งเดียวต่อ test class

1. Test ใหม่ **fail บน `f80092e`** และผ่านหลังแก้
2. ทดสอบทั้งผ่าน launcher และเรียก entry script ตรงโดยไม่มี `-I` (GitLab Windows เรียกแบบนี้)
3. launcher ยังบล็อกการเขียนไฟล์ protected (exit 2)
4. pre-commit ใน git repo ชั่วคราวยังปฏิเสธ protected path ที่ stage ไว้ (exit 1 พร้อมข้อความ protected path)
5. validator ยัง fail เมื่อ input ผิด และผ่านเมื่อ input ถูก
6. Test เดิมไม่ถูกลดความเข้ม
7. ตรวจ encoding บน Windows: `-I` ไม่อ่าน `PYTHONUTF8` / `PYTHONIOENCODING` ให้ใส่ `encoding="utf-8"` ที่ subprocess แบบ text ใน `sdlc_guard/doctor.py` ถ้า test หรือการรีวิวพบว่าจำเป็น
8. ตรวจว่าการแยก path ตอน module ถูก import (ไม่ใช่รันตรง) ไม่ทำให้ผู้ import อื่นพัง
9. Change digest ใน `docs/handoff/`

**ลำดับ (กรณี land แบบ ก):** commit ในเครื่อง → `code-reviewer-agent` และ `security-audit-agent` ตรวจ SHA นั้น บันทึก `docs/plans/plan-011-review.md` → ผลผ่านแล้วจึง push และเปิด PR → CI ผ่านครบ 6 jobs (3 OS × 3.10/3.12) → Gate 3 ช่วงที่การแก้เปิดเผยแต่ยังไม่ merge จึงเหลือประมาณเวลา CI กับการ review ของ Human

## 6. นอก Scope และความเสี่ยงคงเหลือ

- การแก้ไฟล์ของ framework เองที่มีอยู่แล้ว (SEC-M4 ถ้าไม่เลือก ALT 2)
- bytecode cache ใน `scripts/sdlc_guard/__pycache__/` พึ่ง protected glob ซึ่งคุ้มครองเฉพาะสิ่งที่ guard ตรวจเห็น
- สิ่งที่โค้ดของ script ใหม่ทำเองเมื่อถูกรัน ไม่ผ่านการตรวจระดับข้อความคำสั่ง (ดู §8 ข้อ 3)
- ผู้ที่รันคำสั่ง shell ได้ตามใจ หรือควบคุม `PATH` / ตัว interpreter อยู่นอกสิ่งที่ guard นี้ป้องกันได้
- SEC-M1 ถึง SEC-M3 (ตัวตรวจ traceability), งานค้างจาก PLAN-009 (เลื่อนเป็น PLAN-012), `AGENTS.md`, `README.md`, `ROADMAP.md` (PR #18 กำลังแก้ จึงบันทึก Roadmap ตอน closeout)

repository อื่นที่คัดลอก launcher, hook entry และ guard ของ framework นี้ไป จะยังไม่ได้รับการแก้หลัง merge

## 7. Rollback

Revert change ของ PLAN-011 เป็นชุดเดียว (launcher, entry scripts, tests) ไม่มี data migration หาก hook บล็อกทุกคำสั่งหลัง apply ให้ Human reverse patch จาก terminal นอก agent

## 8. Gate 2 · สิ่งที่ Human ต้องตัดสิน

| # | เรื่อง | ข้อเสนอ |
| :--- | :--- | :--- |
| 1 | ทางเลือก | ALT 1 |
| 2 | SEC-M4 | แยกออก ทำหลัง SEC-B1 เพื่อให้แก้ข้อ High ได้เร็ว |
| 3 | allow list `Bash(python3 scripts/*)` และรูปแบบใกล้เคียง: การแก้ import ไม่ปิดทางที่ agent สร้าง script ใหม่แล้วรันได้โดยไม่ถูกถาม | ก) แคบ allow list เป็นรายชื่อ script ใน PLAN-011 (`.claude/settings.json` เป็น protected และมีรายการเดียวกันใน `sdlc_guard/trace_hooks.py` ต้องขยาย scope) · ข) **(แนะนำ)** Human รับความเสี่ยงคงเหลือเป็นลายลักษณ์อักษร แล้วเปิด follow-up เพื่อให้ข้อ High เรื่อง import ลงได้เร็ว หมายเหตุ: security re-audit อาจยังจัดข้อนี้เป็น High |
| 4 | วิธี land | ก) **(แนะนำ)** PR เดียวรวมแผน แก้ และ test แล้ว review กับ merge ในคราวเดียว (การเปิด PR คือการเปิดเผย) · ข) GitHub Security Advisory แบบ private fork (Human เป็นผู้ตั้งค่า, CI ใน private fork อาจไม่รัน ต้องยืนยันก่อนเลือก) |
| 5 | ผู้รีวิว | อนุญาตให้ใช้ subagent `security-audit-agent` และ `code-reviewer-agent` หลัง implement |

- **Approver:** Human Maintainer
- **Decision:** อนุมัติข้อ 1–5 ตามข้อเสนอ: ALT 1 · SEC-M4 แยกทำภายหลัง · ข้อ 3 เลือก ข) · ข้อ 4 เลือก ก) PR เดียว · อนุญาตให้ใช้ `security-audit-agent` และ `code-reviewer-agent`
- **Residual risk ที่ Human รับ (ข้อ 3):** การแก้ import ไม่ปิดทางที่ agent สร้าง script ใหม่แล้วรันได้โดยไม่ถูกถาม ให้ทำเป็น follow-up
- **Timestamp / Evidence:** 2026-11-27 19:38:01 +07 (เวลาที่บันทึก) · ข้อความในแชต "อนุมัติตามข้อเสนอ"

## 9. บันทึกการ Implement (2026-11-27 19:40:37 +07)

- **เพิ่มจาก inventory เดิม:** `scripts/worktree.py` เป็น entry script ที่ §4.2 ตกหล่น structure test พบตอนรันบน baseline จึงแก้ด้วย ภายใต้ ALT 1 ("entry script ทุกตัว")
- **Test-first:** `tests/test_import_isolation.py` fail บน `f80092e` ขณะกรณีควบคุมที่ไม่มีไฟล์ทดสอบผ่าน
- **ไฟล์ไม่ protected:** แก้ใน worktree แล้ว
- **ไฟล์ protected:** เตรียมเป็น patch นอก repository ฉบับรวม Amendment A1 (SHA-256 `e1c23cc510ecf8efa262bc6f1db98b589f7cb132b04252c644766afaae31c268`) รอ Human apply (แทน patch ฉบับก่อน A1)
- **ตรวจบนสำเนาที่ apply patch รวม A1 (macOS):** 259 tests ผ่าน (skip 3) บน Python 3.14.10 และ 3.11.18, contract eval 10/10, validators ผ่าน, `sdlc-hook.cmd` คง CRLF
- **เกณฑ์ §5 ข้อ 7 (encoding):** ยังไม่แก้ `sdlc_guard/doctor.py` รอผล Windows CI และการรีวิว
- **ยังไม่ได้ทำ:** commit, รีวิวอิสระ, CI, Windows / Linux / Python 3.10 และ 3.12

## 10. Amendment A1 · Fail-closed เมื่อโหลด guard ไม่สำเร็จ

- **ที่มา:** พบระหว่าง implement และยืนยันบนสำเนา: ถ้า import ของ guard ล้มเหลว (เช่น `SyntaxError`, `RuntimeError`) คำสั่งของ hook จบด้วย exit 1 ซึ่ง PreToolUse ของ Claude Code ไม่ถือเป็นการบล็อก เป็นพฤติกรรมที่มีมาก่อน PLAN-011
- **การแก้ (`scripts/sdlc_hook.py`):** เมื่อโหลด `sdlc_guard` ไม่ได้และถูกรันตรง
  - คำสั่งทั่วไปรวม `pretooluse`, `hook`, ไม่มี argument, `--check-path`, `--check-cmd`, `precommit`, `commit-msg` จบด้วย exit 2 พร้อมข้อความ `BLOCKED`
  - Antigravity บนคำสั่งตรวจ tool: ตอบ `{"decision": "deny"}` (exit 0 ตาม protocol)
  - `trace` และ `session-start` ยัง exit 0 พร้อม WARNING
  - `SDLC_GUARD_FAIL_OPEN=1` (Human ตั้ง) มีผลเฉพาะคำสั่งตรวจ tool เหมือนพฤติกรรม fail-closed เดิม ไม่มีผลกับ pre-commit และ commit-msg
  - เมื่อถูก import จากไฟล์อื่น ให้ raise ตามเดิม
- **ยังไม่ครอบคลุม:** ถ้าตัว `sdlc_hook.py` เองเสียจน Python รันไม่ได้ หรือ hook หมดเวลา การแก้นี้ช่วยไม่ได้
- **ผลกระทบ:** guard ที่เสียจะบล็อกทุก tool call ต้องแก้จาก terminal ของ Human
- **Test:** เพิ่ม 2 test ใน `tests/test_import_isolation.py` fail ก่อนแก้และผ่านหลังแก้
- **Approver / Evidence:** Human Maintainer · 2026-11-27 19:48:42 +07 (เวลาที่บันทึก) · ข้อความในแชต "เพิ่มใน patch"
