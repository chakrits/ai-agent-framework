---
review_id: REV-009
pr_ref: none (local branch feat/PLAN-009-ci-evidence-and-trace-scrub, not pushed) — reviewed 3f082dc..eadcc983fd91e4ba5d3b9e347eccf74950848763
spec_ref: PLAN-009
verdict: changes_requested
---

# Code & Security Review Report

> **SHA ที่ตรวจ:** `eadcc983fd91e4ba5d3b9e347eccf74950848763` เทียบกับ `main` `3f082dcb717f1a32aa3644f7272262965b2ef4da` (commits `db79c77`, `89cd7c4`, `eadcc98`) ยังไม่ push จึงไม่มี PR และ CI run ส่วน `spec_ref` ใช้ `PLAN-009` เพราะ Framework Change นี้ไม่มี `SPEC-xxx`

## Review Scope & Traceability Check
- **Intent / Spec:** N/A (Framework Change) / `docs/plans/plan-009-ci-evidence-and-trace-scrub.md` (Gate 2 บันทึกใน §8)
- **Tasks Completed (per diff):** WS-A, WS-B, WS-C และแก้สถานะแผน PLAN-004, PLAN-005, PLAN-006
- **Diff Summary:** 7 ไฟล์ +163 / -7: `trace_cli.py`, `tests/test_trace.py`, `.github/workflows/validate.yml` และเอกสารแผน 4 ไฟล์
- **Review order:** ตรวจ raw diff และสรุป findings ก่อน แล้วจึงอ่าน digest ที่ยังไม่ commit
- **Tier:** High-Risk (Framework) แตะ protected path `scripts/sdlc_guard/trace_cli.py`
- **Verdict:** `changes_requested` (Blocker 1, Major 1, Minor 7) Blocker เป็นเรื่องหลักฐานที่ยังขาด **ไม่พบว่าโค้ดใน diff ทำงานผิดจากแผน**

## Spec Compliance & Architectural Drift

- [x] WS-A ตรงแผน §2: `summarize()` มี argument `scrub` (ค่าเริ่มต้นคืนข้อความเดิม), scrub ก่อน `[:100]`, `cmd_export` ยัง scrub ทั้งเอกสารรอบสุดท้าย, `summary` ในเครื่องไม่ส่ง `scrub`
- [x] `eadcc98` มี `trace_cli.py` และ test ใน commit เดียว
- [x] WS-B และ WS-C: คำสั่งใน workflow ตรงกับ §3 และ §4 ชื่อ job เดิมไม่เปลี่ยน step ใหม่ของ FastAPI อยู่ท้ายสุด
- [ ] §5.4 (CI 6 job และ log ว่า `TestFastAPIHttpEndpoints` รันจริง) ยังไม่มีหลักฐาน ดู B1
- [ ] §5.6: digest มีในเครื่องแต่ยังไม่ commit และยังไม่มี PR description
- ลำดับ commit จริงต่างจาก §7 (`ci` มาก่อน `fix`) ไม่พบผลกระทบ เพราะสอง commit ไม่พึ่งกัน ยืนยันจาก Git ไม่ได้ว่าใครเป็นผู้ apply หรือใช้ `SDLC_ALLOW_PROTECTED=1` (`eadcc98` ไม่มี trailer `Co-Authored-By` ต่างจากอีกสอง commit)

### ตรวจคำอ้างสถานะแผนเก่า (Git, tags, `gh` แบบ read-only)

| คำอ้าง | ผล |
| :--- | :--- |
| PLAN-004: `f44211d` (2026-11-21), `v0.1.0` | ยืนยันได้ (`merge-base --is-ancestor`) |
| PLAN-005: `c78aed9` (2026-11-21), `v0.2.0` | ยืนยันได้ และ `c78aed9` ไม่อยู่ใน `v0.1.0` |
| PLAN-006: `5ae1169`, `16db38c`, `v0.3.0` | ยืนยันได้ ทั้งสองอยู่ใน `v0.3.0`; `16db38c` ไม่อยู่ใน `v0.2.0` (วันที่ของ `5ae1169` เป็น author date, commit date คือ 2026-11-22) |
| PR #2 merge `eca7f22`, Windows ทั้งสอง job fail | ยืนยันได้ |
| PR #4 merge `d764d5f`, run `45005508352` ผ่าน 6/6 | ยืนยันได้ (head `64a29ea`) |
| approval checkbox ไม่ถูกติ๊ก, มีอนุมัติ D-01 ในแชท | ยืนยันได้ (`:119`, `:91`) |
| รอบ 6 เป็น `changes_requested`, ติดตามที่ `work/INT-001` Gate 3 | ยืนยันได้ ไม่พบไฟล์รีวิว PLAN-006 ที่ใหม่กว่า และ `work/INT-001/REVIEW.md` บน `main` ยังเป็น `changes_requested` |

## Verification Evidence (Tests & Linters)

รันบน clone ใน temp directory ที่ checkout `eadcc98` (ไม่รวมไฟล์ untracked) ตั้ง `SDLC_TRACE_DIR` ไป temp directory เครื่อง macOS

| Command | ผล |
| :--- | :--- |
| `git diff --check 3f082dc..eadcc98` | exit 0 |
| `scripts/sync-adapters.py --check` | PASSED |
| `scripts/validate-context-budget.py` | PASSED |
| `scripts/validate-contracts.py --check-defaults` | PASSED |
| `evals/run_evals.py --mode contract` | PASSED 10/10 |
| `python3 -m unittest discover -s tests -v` (3.14.10) | 253 tests, OK, skipped=3 (Windows launcher 2, FastAPI 1) |
| `python3.11 -m unittest discover -s tests` | OK, skipped=3 |
| test ใหม่กับ `trace_cli.py` จาก `3f082dc` (path ยาว 141 และ 57 ตัวอักษร) | fail ทั้ง subTest `repo` และ `home` ทั้งสองความยาว |
| test ใหม่กับโค้ดที่ `eadcc98` (ทั้งสองความยาว) | ผ่าน |
| step digest ที่ดึงจาก YAML รันด้วย `bash --noprofile --norc -eo pipefail` (bash 3.2) | ไฟล์จริง 3 ไฟล์ผ่าน exit 0 |
| step เดียวกันกับ template หรือไฟล์ว่าง ชื่อเรียงก่อน/หลังสุด ทั้งสอง glob และชื่อมีช่องว่าง | exit 1 ทุกกรณี |
| step เดียวกันกับ `PYTHONIOENCODING=cp1252` และ digest เสีย | exit 1 (ข้อความ Thai ถูก escape) |
| step เดียวกันเมื่อไม่มีไฟล์ตรง pattern / ไฟล์ชื่อ `*-digest-v2.md` ที่เสีย | exit 0 (ดู m4) |
| `--digest-file docs/templates/change-digest.template.md` | exit 1 |
| `--digest-file` กับ digest จริงสองไฟล์ที่แปลงเป็น CRLF | exit 0 |
| `--digest-file` กับ digest ของ PLAN-009 (untracked) และของ INT-001 บน `feat/INT-001-gate3-rereview` | exit 0 ทั้งคู่ |
| step FastAPI โดยไม่มี dependency (3.11, 3.14) | exit 1 ตามแผน |
| step FastAPI กับ stub package `fastapi` + จำลองความเสียหายของ test (3.11, 3.14) | ดู m1 |
| `gh api .../actions/permissions/workflow` | `default_workflow_permissions: read` |

**ไม่ได้ตรวจ:** CI บน GitHub, Linux, Windows (Git Bash), Python 3.10 / 3.12 (ในเครื่องไม่มี), การติดตั้ง `fastapi` / `httpx` จริง, ความเข้ากันได้ของ `TestClient` กับ version ล่าสุด, HTTP endpoint test, Docker, live eval ผลที่เกี่ยวกับ path บน Windows เป็นการเรียกฟังก์ชันด้วย string รูปแบบ Windows บน macOS เท่านั้น

## Test Oracle Integrity Check
- [x] `tests/test_trace.py` เป็น `+20 / -0` ไม่มี assertion เดิมถูกแก้หรือลบ ไม่มีการแก้ test อื่น
- [x] test ใหม่ fail กับโค้ดเดิมจริง (ตารางด้านบน)
- ผู้ implement และผู้เขียน test คือ main session เดียวกันตามที่แผนระบุ ผู้ตรวจรอบนี้ไม่ได้เขียนโค้ดใน diff
- **test จับ regression ได้ แต่บางส่วนว่างเปล่า (จำลองด้วย string บน macOS ไม่ได้รันบน runner):**

| รูป path ของ runner | โค้ดเดิม subTest `repo` | โค้ดเดิม subTest `home` | โค้ดใหม่ |
| :--- | :--- | :--- | :--- |
| Linux (`/home/runner/work/...`) | `assertNotIn` **ผ่าน (ว่างเปล่า)**, `assertIn("<repo>")` fail | ทั้งสอง assert fail | ผ่านทั้งหมด |
| macOS (`/Users/runner/work/...`) | `assertNotIn` **ผ่าน (ว่างเปล่า)**, `assertIn("<repo>")` fail | ทั้งสอง assert fail | ผ่านทั้งหมด |
| Windows (`D:\a\...`, home `C:\Users\runneradmin`) | ทั้งสอง assert fail | ทั้งสอง assert fail | ผ่านทั้งหมด |


## Security & OWASP Findings
- [x] AuthN/AuthZ: diff ไม่แตะ endpoint หรือสิทธิ์
- [x] Injection: step ใหม่ไม่ใช้ `${{ }}` จากข้อมูลภายนอก และ quote `"$f"` แล้ว
- [ ] Secret / PII: การรั่วจุดตัด 100 ตัวอักษรถูกแก้แล้ว แต่ยังมีทางอื่นที่มีอยู่ก่อน diff นี้ (M1, m2)
- [ ] Supply chain: ดู m7
- ไม่พบช่องโหว่ Critical / High ที่ diff นี้สร้างขึ้น

## Findings Summary (Blocker / Major / Minor)

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Blocker** B1 (Compliance) | PLAN-009 §5.4 | ไม่มี push, PR หรือ CI run สำหรับ `eadcc98` สิ่งที่ WS-C ตั้งใจส่งมอบ (รัน FastAPI endpoint test จริง) พิสูจน์ได้ใน CI เท่านั้นในรอบนี้ จึงยังไม่เคยถูกพิสูจน์ และ test ใหม่ยังไม่เคยรันบน Linux / Windows ที่นับเป็น Blocker (ต่างจาก PLAN-008 รอบ 3 ที่ตั้ง CI เป็นเงื่อนไขก่อน merge) เพราะ PLAN-009 §5 กำหนด CI ไว้ใต้ “ก่อนขอ Gate 3” | Human สั่ง push และเปิด PR แนบ PR URL, head SHA, CI ครบ 6 job และบรรทัด log `test_endpoints_auth_rbac_scope_and_lifecycle ... ok` จากนั้นรีวิวส่วนนี้ซ้ำ |
| **Major** M1 (Security, มีอยู่ก่อน, นอก scope G11) | `trace_cli.py:222-230` (`scrub_paths`) | ชื่อผู้ใช้ยังออกไปกับไฟล์ export ได้ ดูรายละเอียดด้านล่าง | ไม่ใช่ regression และไม่จำเป็นต้องแก้ใน diff นี้ แต่ให้ Human รับทราบและเปิดงานติดตาม (protected path) จนกว่าจะแก้ ต้องอ่านไฟล์ export ก่อน commit ตาม `docs/guides/agent-trace-manual.md:27` |
| Minor m1 (Bugs) | `.github/workflows/validate.yml:91-94` | step FastAPI ผ่านได้แม้ endpoint test ถูกถอดหรือข้ามในโค้ด: ลบ class, ใส่ `@unittest.skip`, เปลี่ยนชื่อ method → exit 0 ทั้ง 3.11 และ 3.14; ลบทั้งไฟล์ → exit 0 บน 3.11 (`Ran 0 tests ... OK`), exit 5 บน 3.14 คาดว่า job 3.10 จะเหมือน 3.11 (ยังไม่ได้รัน) guard `import` ครอบเฉพาะกรณี dependency ขาด ซึ่งตรงตามแผน | แทนบรรทัด discover ด้วยคำสั่งที่ fail เมื่อ class ไม่ได้รันจริง (ตัวอย่างด้านล่าง) |
| Minor m2 (Security, มีอยู่ก่อน) | `trace.py` `_prep(r, 500)` และ `_prep(command, limit)` | มีการตัดอีกสองจุดตอน **บันทึก** ก่อน scrub: จำลอง guard reason ยาวจน path คร่อม byte 500 ได้ `/Users/alic` ในไฟล์ export; คำสั่งที่ path คร่อม byte 2048 หลัง path ยาวมาก (~200 ตัวอักษร) ซ้ำหลายครั้ง ก็ได้ชิ้นเดียวกันใน 100 ตัวแรก เกิดยากทั้งสองกรณี | บันทึกเป็นข้อจำกัด หรือรวมในงานติดตามของ M1 (เช่น scrub ชิ้น path ที่ค้างหน้า marker การตัด) |
| Minor m3 (Bugs / test) | `tests/test_trace.py:352-353,364` | (ก) เมื่อ repo อยู่ใต้ home (Linux / macOS runner) โค้ดเดิมให้ `~/work/<ชื่อ repo>...` เพราะ scrub รอบท้ายแทน home ในชิ้นที่ถูกตัด `assertNotIn` ของ subTest `repo` จึงผ่านเสมอ ชื่อโฟลเดอร์ที่หลุดจริงไม่ถูก assert และ regression ถูกจับด้วย `assertIn("<repo>")` อย่างเดียว (ข) เมื่อ `len(base) > 97` padding ติดลบกลายเป็นว่าง จุดตัดเก็บได้แค่ `base[:94]` แต่ assert หาชิ้นที่ยาวกว่า จึงว่างเปล่าเช่นกัน (ค) `assertIn("~", text)` อ่อน และ test ไม่ครอบ `block_reasons` | assert ชิ้นส่วนหลังแทน home ด้วย (เช่นไม่มี `~/` ตามด้วยโฟลเดอร์ของ repo), ให้ `kept = min(len(base) - 3, 94)` หรือใช้ base จำลองคงที่ และ assert รูป `~/private` |
| Minor m4 (Bugs) | `validate.yml:48-53` | fail-open: ไม่มีไฟล์ตรง pattern → exit 0 โดยไม่พิมพ์อะไร; digest ที่ตั้งชื่อนอก pattern ถูกข้ามเงียบ | พิมพ์จำนวนไฟล์ที่ตรวจ หรือ fail เมื่อเป็น 0 |
| Minor m5 (Compliance) | `README.md:93`, `ROADMAP.md:93-94` | README ยังบอกว่า “digest checks are not run by CI” ซึ่งจะผิดหลัง merge (`--require-digest` และการบังคับให้มี digest ยังไม่อยู่ใน CI จริง ต้องคงส่วนนั้นไว้) ROADMAP ยังระบุว่างาน digest ใน CI ต้องแตะ protected path ซึ่งรอบนี้ไม่ต้อง | แก้ README ใน PR นี้; ติ๊ก ROADMAP หลังมี CI evidence |
| Minor m6 (Compliance) | front matter ของ PLAN-004/005/006 | ใช้ `status: released` ขณะที่ PLAN-007/008 ซึ่ง release แล้วใช้ `merged` และ `status_note` ว่าไม่พบชุดสถานะที่กำหนด PLAN-006 ที่เป็น `released` ยังมีรีวิว `changes_requested` (มี `review_note` กำกับแล้ว) | เลือกคำเดียวให้ตรงกัน หรือกำหนดชุดสถานะ |
| Minor m7 (Security) | `validate.yml` (ทั้งไฟล์), `:87-89` | ติดตั้ง package ไม่ pin จาก PyPI ใน job ที่ไม่มี `permissions:` และ `actions/checkout` เก็บ credential ไว้ตามค่าเริ่มต้น ค่า default ของ repo เป็น `read` จึงจำกัดผลกระทบ | เพิ่ม `permissions: contents: read` และ `persist-credentials: false`; พิจารณาเพดาน version ตาม §6 |

### M1: ทางที่ path ในเครื่องยังไปถึง summary ได้

ทดสอบด้วย `build_event` → `summarize(scrub)` → `render_markdown` → `scrub` ของ `eadcc98` ใช้ path สมมติ

| รูปแบบในคำสั่ง | ผลในไฟล์ export |
| :--- | :--- |
| ชื่อโฟลเดอร์ที่ Claude Code สร้างจาก path: `-Users-<user>-...` (scratchpad, `~/.claude/projects/`) | ชื่อผู้ใช้และโครงสร้างโฟลเดอร์หลุด |
| Git Bash `/c/Users/<user>/...`, WSL `/mnt/c/Users/<user>/...` | หลุดทั้ง path |
| drive ตัวพิมพ์เล็ก `c:\users\...`, backslash ซ้อน `C:\\Users\\...`, 8.3 `<USER>~1`, ตัวพิมพ์ต่างบน macOS | หลุด |
| ชื่อผู้ใช้เปล่า (`chown <user>`, `ps -u <user>`) | หลุด |
| path ที่ escape ช่องว่าง `.../GitHub\ Code/...` | home ถูกแทนด้วย `~` แต่ชื่อโฟลเดอร์ของ repo ยังอยู่ |

**หลักฐานจาก trace จริงในเครื่อง (อ่านอย่างเดียว รายงานเฉพาะจำนวน):** นับเฉพาะ tool result ที่ลงเวลาก่อน 2026-11-27 17:00 +07 (ก่อนเริ่มรีวิวนี้) หลัง scrub และตัดแล้ว มี **58 จาก 392 บรรทัดคำสั่งที่ยังมีชื่อผู้ใช้** (2 sessions) ทั้งหมดเป็นรูป `-Users-<user>` เป็นจำนวนก่อนคัด top 5 ของ export ส่วน export ของ `INT-001` จาก trace ในเครื่องและ `work/INT-001/trace-summary.md` ใน repo ไม่พบชื่อผู้ใช้

จัดเป็น Major ไม่ใช่ Blocker เพราะมีอยู่บน `main` แล้ว diff นี้ไม่ได้ทำให้กว้างขึ้น อยู่นอกปัญหาที่ §2 อนุมัติ และการ export กับ commit เป็นขั้นที่คนสั่งเอง Human อาจยกระดับได้

### ตัวอย่างสำหรับ m1

```bash
python -c 'import sys,unittest; s=unittest.defaultTestLoader.loadTestsFromName("tests.test_orchestrator_api.TestFastAPIHttpEndpoints"); r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(0 if r.testsRun and r.wasSuccessful() and not r.skipped else 1)'
```

ทดสอบบน 3.11: ลบ class, skip, เปลี่ยนชื่อ method, ลบไฟล์ (ใช้ stub) และไม่มี dependency ให้ exit 1 ทุกกรณี กรณีไม่มี dependency ยืนยันว่า loader import module ได้และรายงาน `skipped 'fastapi optional dependency ...'` กรณีผ่านจริงยังไม่ได้ทดสอบ เพราะไม่มี FastAPI ในเครื่อง และการแก้นี้ต่างจากคำสั่งใน §4 จึงควรบันทึกในแผน

## Digest Claim Audit (อ่านเป็นลำดับสุดท้าย)

ไฟล์ `docs/handoff/2026-11-27-plan-009-ci-evidence-digest.md` (untracked ไม่อยู่ใน SHA ที่ตรวจ)

- **ยืนยันได้:** `:29` (คำสั่งรันได้ 1 test, OK), `:34` (SHA ตรง), `:35`, `:36` (ใช้ `3f082dc..eadcc98`), `:38` (ไฟล์ใน repo 3 + ตัว digest ผ่าน และ template exit 1), `:39`, `:40`
- **ยืนยันไม่ได้:** `:11,16` (ว่า Human เป็นผู้ apply และ commit `eadcc98`), `:37` (ว่าไฟล์ที่ commit ตรงกับสำเนาที่ทดสอบก่อน commit) แต่ผลรันบน SHA ที่ commit แล้วผ่าน
- **เวลาไม่สอดคล้อง:** หัวไฟล์ `:4` ลง 17:20:00 ซึ่งก่อน `eadcc98` (17:21:51) ที่ `:36` อ้างว่าตรวจแล้ว และ mtime ของไฟล์คือ 17:25 หัวไฟล์จึงไม่บอกเวลาที่เก็บหลักฐาน
- **ควรแก้ก่อน commit:** `:10-11,23` อ่านแล้วอาจเข้าใจว่า export ไม่หลุด path แล้ว ควรระบุข้อจำกัด M1 / m2; `:25` ควรระบุว่า guard ครอบเฉพาะ dependency ขาด (m1); `:33` “รีวิวอิสระยังไม่ได้ทำ” ต้องเปลี่ยนเป็นลิงก์ไฟล์นี้และ verdict
- ไม่พบคำอ้างว่า CI ผ่าน

## Council Pressure-Test
- **Lenses Used:** Contrarian, Executor, Outsider (โมเดลเดียวสวมหลายมุม ไม่ใช่ผู้ตรวจหลายคน)
- **Preserved Dissent (Contrarian):** "This change fixes the rare leak and leaves the common one: a path cut at character 100 needs bad luck, but the dash-encoded home directory appears in ordinary agent commands, so calling the export safe to commit is still not true."
- **Executor:** diff เล็กและย้อนกลับได้ทีละ commit การ push เพื่อให้ได้ CI evidence คือขั้นที่ปลด Blocker โดยตรง ไม่ควรขยาย scope ใน PR นี้ไปแก้ `scrub_paths` ทั้งหมด
- **Outsider:** คำว่า “CI รัน FastAPI endpoint test” ทำให้คนอ่านเชื่อว่า CI จะ fail ถ้า test หายไป ซึ่งไม่จริง (m1); docstring “safe to commit to a public repo” สัญญาเกินกว่าที่ฟังก์ชันทำได้
- **Blind-Spot Check:** ทั้งแผนและ diff คิดเรื่อง scrub เป็นการแทน string ของ path สองค่า ไม่ได้ถามว่าตัวตนของผู้ใช้ปรากฏในรูปใดบ้างใน trace จริง และไม่มี test ที่ตรวจไฟล์ export ว่าไม่มีชื่อผู้ใช้
- **Verdict & One Next Step:** `changes_requested`; ขั้นถัดไปคือ push และเปิด PR เพื่อให้ได้ CI 6 job (แก้ m1, m3, m5 ใน revision เดียวกันได้ ถ้า Human เห็นชอบ โดย m3 อยู่ใน `tests/` ไม่ใช่ protected path)

## เงื่อนไขก่อนขอ Gate 3 รอบถัดไป
- ปิด B1 ด้วย PR URL, head SHA และผล CI ของ revision เดียวกัน
- Human ตัดสินเรื่อง M1 (รับความเสี่ยงและเปิดงานติดตาม หรือขยาย scope ด้วยการแก้แผน)
- Commit review และ digest ตาม §7 หากแก้โค้ดหลังรอบนี้ต้องรีวิวส่วนที่เปลี่ยน

## Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** Pending
