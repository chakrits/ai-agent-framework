---
review_id: REV-008
pr_ref: uncommitted working tree on feat/PLAN-008-prompt-consistency (no PR yet)
spec_ref: PLAN-008
verdict: approved_for_human_gate
---

# Code & Security Review Report

> ยังไม่มี commit และยังไม่ได้เปิด PR ส่วน `spec_ref` ใช้ `PLAN-008` เพราะ Framework Change นี้ไม่มี `SPEC-xxx`

## Review Scope & Traceability Check
- **Intent / Spec:** N/A (Framework Change) / `docs/plans/plan-008-prompt-consistency.md` (Gate 2 Approved 2026-11-27 13:20:14 +07); ต้นทาง `docs/handoff/2026-11-27-prompt-audit.md`
- **Tasks Completed (per diff):** Findings F1, F2, F4-F11, C1 และ G1 ทางเลือก A ครบตามตาราง §3 ของแผน (ยังไม่แยกเป็น commit 1-5)
- **Diff Summary:** 34 tracked files แก้ไข (+174 / -117) เทียบ `origin/main` `c39c6cc` และเอกสารใหม่ใน `docs/plans/`, `docs/handoff/` ไม่มีการแก้ `scripts/`, `orchestrator/`, `tests/`
- **Review order:** ตรวจ raw diff ก่อน อ่าน change digest หลังสรุป findings แล้ว
- **Tier:** High-Risk (Framework) แตะ protected paths: `docs/operating-model/constitution.md`, `docs/contracts/README.md`
- **Verdict:** `changes_requested` (Blocker 0, Major 3, Minor 6 ที่รายงาน)

## Spec Compliance & Architectural Drift

### เทียบกับแผน
- [x] ทุกแถวของตาราง §3 Commit 3 มีใน diff
- [x] ข้อความ `constitution.md:16` และแถวใหม่ `docs/contracts/README.md:10` ตรงกับข้อความใน Commit 4
- [x] PR template และ GitLab MR template มีหัวข้อ `## Verification` / `## Review` ตามแผน หัวข้อย่อยตรงกับ `required_sections` ทั้ง 7 และยังต่างกันเฉพาะบรรทัดเดิม (28, 32)
- [x] ไฟล์ที่ `.patch` แตะ ต่างจากผล apply patch บน `c39c6cc` เฉพาะส่วนที่ Commit 3 เขียนทับ และส่วน "เกินแผน" ด้านล่าง
- [x] แผนระบุว่าไม่พบ script ที่อ่าน `review-gate.schema.yaml`: ยืนยันด้วย `grep -rn "review-gate" scripts evals orchestrator tests` (ไม่พบ)
- [ ] **เกินแผน (digest เปิดเผยแล้ว):** ข้อความกรณี Framework Change ที่ไม่มี work item ใน `code-reviewer-agent.md:15,21`, `dev-coding-agent.md:25,29`, `tdd-implementation/SKILL.md:9,13` ทิศทางสมเหตุผล แต่ใส่ไม่ครบชุด (M1) Human ต้องยอมรับที่ Gate 3
- [ ] กฎใน §2 "ถ้ายังไม่มี PR ให้ใส่ในร่าง description" ไม่ปรากฏในไฟล์คำสั่งใด (M3)

### Governance: สิ่งที่ผ่อนลง

| การเปลี่ยน | ระบุในแผนหรือไม่ |
| :--- | :--- |
| Extended DoD แคบลงจาก "Behavior Changes & High-Risk" เป็น "High-Risk / Framework" (`AGENTS.md:151`) มี Standard bullet ใหม่ที่ `AGENTS.md:149` | ระบุ |
| Trace summary ใน PR/MR checklist จาก medium/high เป็น High-Risk (`.github/pull_request_template.md:31`) | ระบุ (ตรง constitution) |
| Standard ไม่ต้องรัน validator / trace export; Gate 3 ยอมรับ `## Review` ใน PR | ระบุ |
| Checklist "`REVIEW.md` with a work item, otherwise `## Review` above" ครอบ High-Risk / Framework ที่ไม่มี work item ด้วย | ข้อความตรงแผน แต่ขัด §2 "High-Risk / Framework เหมือนเดิม" (M1) |
| QA ข้าม steps 2-5 (รวม 100% traceability) ในทุก Bug Fix รวม High-Risk | อนุมัติผ่าน patch ของ Commit 2 (ข้อความแผน / audit §2 ไม่ได้อธิบายการข้ามขั้น) แต่ขัดกับ High-Risk 100% traceability ใน `constitution.md:16` (M2) |

ข้อที่เข้มขึ้น (F6, F8, F9, F10) ตรงกับแผน ข้อความ F8 ตรงกับ `scripts/sdlc_guard/guard.py` และ `policy.json` สำหรับ write tools

### Walk ตาม route

| Route | Input / Output / ผู้ตรวจ | ผล |
| :--- | :--- | :--- |
| New Feature, API/Schema | ครบเหมือนเดิม | ผ่าน |
| Standard ไม่มี work item (bug fix, config) | ที่ลงของ verification / review ชัด; ที่ลงของ plan ยังไม่พร้อม | M3; SA stop point (m2) |
| Standard มี work item | `plan.md`, `tasks.json`, `REVIEW.md` ชัด | ติดข้อจำกัด `tasks.schema.json` เดิม |
| High-Risk bug fix / config (Fast-Track) | QA ถูกสั่งข้าม traceability; ที่ลงกรณีไม่มี work item ไม่ระบุ | M2, G3 |
| Test-Only / Docs-Only | ไม่มี agent ใน route ที่ถูกสั่งให้เขียน `## Verification` | M2 |
| Framework ไม่มี work item | ที่ลงของ review / security / evidence ขัดกัน | M1 |

## Verification Evidence (Tests & Linters)

รันโดยผู้ตรวจเมื่อ 2026-11-27 (macOS, Python 3.14.10), `PYTHONDONTWRITEBYTECODE=1`, `SDLC_TRACE_DIR` ชี้ temp dir

| คำสั่ง | ที่รัน | ผลที่เห็น |
| :--- | :--- | :--- |
| `python3 scripts/sync-adapters.py --check` | สำเนา working tree | `Adapter parity check PASSED (100% synced with .agents/)` exit 0 |
| `python3 scripts/validate-context-budget.py` | สำเนา | `Context budget check PASSED` exit 0 |
| `python3 scripts/validate-contracts.py --check-defaults` | สำเนา | `Contract validation PASSED` exit 0 |
| `python3 evals/run_evals.py --mode contract` | สำเนา | `PASSED (10/10 cases)` exit 0 |
| `python3 scripts/validate_work_item.py --digest-file docs/handoff/2026-11-27-plan-008-prompt-consistency-digest.md` | สำเนา | `Work item validation PASSED` exit 0 |
| `python3 -m unittest discover -s tests` | repo จริง | `Ran 252 tests` / `OK (skipped=3)` exit 0 |
| `python3 -m unittest discover -s tests` | สำเนาใน path ยาว | fail 1, skip 3 (`test_export_scrubs_repo_and_home_paths`) |
| เหมือนกัน บน clone ของ `c39c6cc` ใน path ยาว | clone | fail ตัวเดียวกัน (มีอยู่ก่อน diff นี้) |
| `git diff --check` และ `git diff origin/main --check` | repo จริง | ไม่มีผลลัพธ์, exit 0; เอกสาร untracked 3 ไฟล์ (`.md`) ไม่มี trailing whitespace |
| `git grep` ตาม §4 | repo จริง | 54 บรรทัด ผ่านแบบมีข้อสังเกต: `qa-function-agent.md:19`, `sa-architect-agent.md:21`, `ba-po-agent.md:18` ไม่ผูกเงื่อนไขในบรรทัดเอง (สองไฟล์แรกมี bullet ข้อยกเว้นเฉพาะบางกรณี) |
| `diff -rq .agents/... .claude/... .agent/...` | repo จริง | agents, skills ตรงทั้งสอง mirror; workflows ตรงกับ `.agent/` |

- ระหว่างรัน unittest ใน repo จริง ไฟล์ใต้ `.sdlc/` ที่เปลี่ยนมีเพียง mtime ของ `.sdlc/env.json` (gitignored, ขนาดเท่าเดิม); ไฟล์ใน `.sdlc/traces/` ไม่เปลี่ยน และ `git status` ไม่เปลี่ยน
- เกณฑ์ "CI ผ่าน 6/6" ยังตรวจไม่ได้

### สิ่งที่ไม่ได้ตรวจ
- พฤติกรรมจริงของ agent ก่อน/หลังแก้ (ไม่ได้รัน live eval)
- CI บน GitHub / GitLab, Windows, Linux, Python 3.10 / 3.12, Docker, FastAPI optional deps
- การแยก commit 1-5 และผล `sync-adapters.py --check` ราย commit (ยังไม่มี commit) โดย Commit 2 และ 3 แก้ไฟล์ซ้อนกัน
- guard ฝั่ง shell command และ hooks ของ Codex / Antigravity
- ไม่ได้ตรวจซ้ำความครบถ้วนของ findings ใน audit ทั้งหมด (G2-G9, H1-H3) และ `docs/reference-architecture/`

## Test Oracle Integrity Check
- [x] ไม่มีการแก้ `tests/`
- [x] `evals/datasets/03-bugfix-regression.json` และ `06-code-review-nit-cap.json` แก้เฉพาะ title / prompt; assertions และ sample output เดิม
- [ ] `evals/**` อยู่ใน `ci_gate_globs` ของ `dev-coding-agent` Human ต้องรับรู้ว่า diff แตะ CI gate input
- [ ] Contract evals ตรวจโครงสร้าง sample ไม่ได้ตรวจว่า agent ทำตาม prompt ใหม่

## Security & OWASP Findings
- [x] AuthN/AuthZ, input validation: ไม่มีการแก้ code (`orchestrator/`, guard, hooks)
- [x] ค้น path ส่วนตัวและรูปแบบ token ในเอกสารใหม่ 3 ไฟล์ (`.md`) ไม่พบ
- [ ] **มีอยู่ก่อน diff, ไม่อยู่ใน follow-up ของแผน (A09, Low):** `scripts/sdlc_trace` export ตัดคำสั่งที่ 100 ตัวอักษร (`scripts/sdlc_guard/trace_cli.py:84`) ก่อน `scrub_paths` (`trace_cli.py:240`) เมื่อ path ของ repo ยาว ส่วนต้นของ absolute path จึงไม่ถูกแทนด้วย `<repo>` (เห็นจริงในผล test ที่ fail) แนะนำเพิ่มเป็น follow-up
- [ ] `AGENTS.md:116` ให้แนบ full test log / trace export ใน PR ซึ่งเป็น external action (m4)

ไม่พบช่องโหว่ระดับ Critical / High

## Findings Summary (Blocker / Major / Minor)

**Blocker:** ไม่มี

### ที่มาของ Major: ช่องว่างของแผน หรือ implementation ต่างจากแผน

การแก้ข้อที่เป็น "ช่องว่างของแผน" เป็นการเพิ่มข้อความเกินที่ Gate 2 อนุมัติ ต้องแก้ PLAN-008 ให้ Human อนุมัติก่อน มิฉะนั้นรอบ review ถัดไปจะนับเป็น scope drift

| ข้อ | ประเภท | หมายเหตุ |
| :--- | :--- | :--- |
| M1 (1) ที่ลงของ security / council | Implementation เกินแผนไม่ครบชุด | bullet Framework ของ reviewer ไม่อยู่ในแผน |
| M1 (2) checklist "`## Review` above" | ช่องว่างของแผน | ข้อความมาจากแผน §3 |
| M1 (3) digest เป็นหลักฐาน | Implementation เกินแผน | `reviewer:15`, `dev:29` |
| M1 (4) path ของ digest ใน `dev:21` | มีอยู่ก่อน | ถูกอ้างจากข้อความใหม่ |
| M2 (a) ไม่มีผู้เขียน `## Verification` | ช่องว่างของแผน | diff สร้างที่ลงใหม่โดยไม่ระบุผู้เขียนใน route นี้ |
| M2 (b) QA ข้าม steps 2-5 | ช่องว่างของแผน (มาจาก patch ของ Commit 2) | หลักฐาน traceability ของ Fast-Track ซึ่งยังไม่มี template เกี่ยวกับ G3 |
| M3 ที่ลงของ Plan Checkpoint | ช่องว่างของแผน และตกกฎ draft description ของ §2 | `CLAUDE.md:8` ตรงตามแผน แต่แผนไม่ได้เพิ่มช่องใน template |

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Major** M1 | `code-reviewer-agent.md:15,16,21`; `security-audit-agent.md:17`; `council-pressure-test/SKILL.md:10`; `dev-coding-agent.md:21,29`; PR/MR template `:27`; `constitution.md:16`; `dynamic-routing.md:17`; `AGENTS.md:153-154` | **Framework Change ที่ไม่มี work item ได้คำตอบไม่ตรงกัน** (1) reviewer เขียน `docs/plans/plan-<NNN>-review.md` (ใหม่) แต่ security agent ซึ่ง router เรียกคู่กันใน route นี้ มีที่ลงแค่ `work/.../REVIEW.md` หรือ `## Review` ของ Standard; council skill ก็เช่นกัน ทั้งที่ Framework เป็น high risk (2) checklist ใหม่ใน PR/MR ชี้ไป "`## Review` above" ซึ่งหัวข้อนั้นระบุว่าใช้กับ Standard เท่านั้น (3) `dev:29` ให้บันทึกหลักฐานใน change digest และ `reviewer:15` นับเป็น input แต่ `reviewer:16` ระบุว่า digest ไม่ใช่หลักฐาน และ step 3 (`:30`) ไม่รวม digest (4) `dev:21` ยังวาง digest ที่ `work/<INT-xxx>/` อย่างเดียว ขณะ `AGENTS.md:74` ให้ใช้ `docs/handoff/` (ข้อ 4 มีอยู่ก่อน แต่ถูกอ้างจาก step 5 ใหม่) ส่วน `constitution.md:16`, `dynamic-routing.md:17`, `AGENTS.md:153-154` ที่ยังบังคับ `REVIEW.md` / `work/` สำหรับ Framework มีอยู่ก่อน | เพิ่มที่ลงกรณี Framework ใน `security-audit-agent.md` และ council skill; จำกัด checklist `:27` ให้ `## Review` ใช้กับ Standard เท่านั้น; ให้ reviewer ใช้ผลคำสั่งที่รันเองหรือ CI เป็นหลักฐาน (digest เป็นเพียงข้ออ้างที่ต้องตรวจ); ใส่ path `docs/handoff/` ใน `dev:21` สำหรับ constitution / routing ให้ Human ตัดสินว่าจะแก้ในแผนนี้หรือบันทึกเป็น follow-up |
| **Major** M2 | `qa-function-agent.md:15,20,23`; `dev-coding-agent.md:29`; `tdd-implementation/SKILL.md:13`; `constitution.md:16`; `dynamic-routing.md:16`; `router.py` (`TEST_OR_DOCS_ONLY`, `BUG_FIX`) | **(a)** route Test-Only / Docs-Only คือ QA แล้ว reviewer ไม่มี dev stage แต่ข้อความให้เขียน `## Verification` มีเฉพาะใน dev agent และ `tdd-implementation` QA บอกเพียง "the test or doc itself" ขณะที่ routing ต้องการ verification output และ reviewer จัด "missing evidence" เป็น Blocker (`reviewer:31`) อีกทั้ง `:20` เขียน "Bug Fix or Test-Only" ตก Docs-Only **(b)** step 1 สั่ง Bug Fix ทุก risk "skip steps 2-5" รวม step 5 (100% traceability) และ step 3 (เทคนิคทดสอบรวม security fundamentals); `:20` ให้ไม่ต้องมี `test-report.md` เมื่อไม่มี work item แม้ high risk ขณะ constitution กำหนดให้ High-Risk มี 100% traceability ที่ Gate 3 (เดิม prompt ไม่มีทางทำ route นี้ได้ถูกต้องเช่นกัน แต่ข้อความใหม่เปลี่ยนจาก "ถามก่อน" เป็น "ข้าม") | (a) ให้ QA บันทึกคำสั่งและผลใน `## Verification` เมื่อไม่มี work item (หรือใน work item) และเพิ่ม Docs-Only ใน `:20` (b) จำกัดการข้ามขั้นไว้ที่ Standard หรือระบุว่า High-Risk bug fix ใช้หลักฐาน traceability อะไร (เช่น defect / Fast-Track Spec -> regression test) หรือให้ Human อนุมัติข้อยกเว้นอย่างชัดแจ้ง |
| **Major** M3 | PR template `:6-8` (MR template เช่นกัน); `dev-coding-agent.md:20,25,30`; `tdd-implementation/SKILL.md:9`; `CLAUDE.md:8`; `code-reviewer-agent.md:15` | **ที่ลงของ plan สำหรับ Standard ที่ไม่มี work item ยังใช้ไม่ได้ครบ** diff กำหนดว่า "the plan is the PR/MR `## Plan Checkpoint`" แต่ template มีเพียง approver และ link ไม่มีช่อง target files / test strategy / verification commands / rollback (`constitution.md:13`) และไม่มีไฟล์ใดบอกว่าก่อนเปิด PR ให้เก็บใน draft description ตาม §2 ของแผน จึงให้ "write the plan before editing source code" ลงในที่ที่ยังไม่มี และ reviewer อาจไม่มี plan ให้ทำ Compliance pass | เพิ่มช่อง plan packet ใน `## Plan Checkpoint` ของทั้งสอง template และเพิ่มกฎ draft description (ร่างก่อน, โพสต์หลัง Human ยืนยัน) ใน `AGENTS.md` หรือ dev agent |
| **Minor** m1 | PR/MR template `:13-22`; `review.template.md:10`; `code-reviewer-agent.md:31`; council skill `:10` | PR template ไม่มีช่อง Council Pressure-Test และคำสั่งให้เขียนใต้ `## Council Pressure-Test` ขัดกับกฎลดระดับเป็น `###` (ถ้าใช้ `##` จะหลุดจาก `## Review`) กรณีที่เกิดได้: Standard test/docs ที่ `risk_tier: high` | ระบุว่าใน PR ใช้ `### Council Pressure-Test` |
| **Minor** m2 | `sa-architect-agent.md:21,25,30` | step 1 จำกัดเฉพาะ steps 3, 5 กับ route ที่มี Gate 1 ทำให้ step 6 "Stop at Gate 2" ครอบ Standard config impact check ซึ่ง router ไม่มี gate; Outputs `:21` ยังเป็น `work/.../spec.md` ไม่ตรงกับ Inputs `:17` (Framework Spec อยู่ `docs/plans/`) | ผูก step 6 กับ risk / route และระบุ output ราย route |
| **Minor** m3 | `dev-coding-agent.md:30` | "Update the recorded plan in the same commit" ทำไม่ได้กับ PR description และไม่เตือนว่าต้องกลับไปขออนุมัติเมื่อ scope drift (`AGENTS.md:61`) | แยกกรณี PR และอ้างกฎ re-approval |
| **Minor** m4 | `AGENTS.md:116`; `docs/contracts/README.md:10` | "full test logs, trace exports ... attach them to the PR/MR" ขัดกับ "No ... trace export" ของ Standard ที่ไม่มี work item (และ export ต้องมี `--work-item`); ไม่ย้ำว่าต้องให้ Human ยืนยันก่อนแนบ | ตัด trace exports ออกจากกรณีนี้และอ้าง Ask First |
| **Minor** m5 | change digest `:4,11,28,39,44` | ดู Digest Claim Audit ด้านล่าง | อัปเดตก่อน Commit 5 |
| **Minor** m6 | `.obsidian/`, `docs/handoff/2026-11-27-prompt-audit.patch` | `.obsidian/` ไม่อยู่ใน `.gitignore` และ `.patch` อยู่ใน `docs/handoff/`; `git add docs/` จะ commit `.patch` ที่แผนห้าม | stage รายไฟล์ |

Minor อื่นที่ไม่ลงรายละเอียด: 2 ข้อ (ชื่อไฟล์ `06-code-review-nit-cap.json` ยังอ้าง nit cap; บรรทัดว่างแยก Standard bullet ที่ `AGENTS.md:148`)

### ปัญหาที่มีอยู่ก่อน diff นี้

| เรื่อง | สถานะในแผน |
| :--- | :--- |
| ลำดับ route ของ high-risk bug fix และที่ลง Fast-Track Spec / Change Plan (รวมกรณีไม่มี work item ใน `CLAUDE.md:8`, `dev:25,29`) | follow-up G3 |
| `dynamic-routing.md:21` ยังเขียน "Low" ขณะ `AGENTS.md:58` ใหม่เป็น low/medium | follow-up G4 |
| router เรียก security audit ใน Standard medium แต่ routing doc / reviewer step 0 ไม่ตรง | follow-up G5 |
| Framework route ใช้ `dev-coding-agent` ซึ่ง guard ห้ามแก้ protected / `evals/**` | follow-up G7 |
| agent ไม่ได้รับ path ของ work item ทั้งที่เงื่อนไขใหม่พึ่ง "มี work item หรือไม่" และ orchestrator ใส่เฉพาะ constitution, role, skills (`orchestrator/core/loader.py:133-152`) | follow-up H1 (บางส่วน) |
| Standard ที่มี work item แต่ไม่มี `SPEC` ไม่ผ่าน `tasks.schema.json` | ครอบคลุมเพียงบางส่วนโดย "validator โหมด Standard" |
| Framework ยังถูกบังคับ `REVIEW.md` ใน constitution / routing / Extended DoD | ไม่อยู่ใน follow-up (ดู M1) |
| High-Risk ไม่มี work item export trace ไม่ได้ | แผน §5 บันทึกแล้ว |
| trace export scrub path หลังตัดข้อความ | ไม่อยู่ใน follow-up |

### Digest Claim Audit (อ่านเป็นลำดับสุดท้าย)
Source: `docs/handoff/2026-11-27-plan-008-prompt-consistency-digest.md`

- **ยืนยันได้:** รายการไฟล์และ finding ที่อ้าง; adapter parity, context budget, contract validation, eval 10/10, digest validator; unit tests 252 (ข้าม 3, ที่เหลือผ่าน) ใน repo จริง; `git diff --check`; ส่วน "ต่างจากแผน"; ข้อจำกัด live eval / CI / Windows
- **กล่าวเกินจริง:** "คู่มือบอกตรงกันว่างานแต่ละประเภทใช้อะไรเป็นข้อมูลเข้า" (`:11`) ยังไม่จริงสำหรับ Framework, Test/Docs และ Plan Checkpoint (M1-M3)
- **กล่าวเกินจริง:** "งาน High-Risk / Framework ยังใช้เอกสารและ gate ชุดเดิม" (`:28`) Framework review มีที่ลงใหม่ และ QA ของ High-Risk bug fix ถูกให้ข้ามขั้น
- **ล้าสมัยเมื่อ commit:** "independent review ยังไม่ได้ทำ" (`:39`)
- **ไม่ครบ:** รายการค้าง (`:44`) ไม่มี keyword `auth` จับ "author" และ validator โหมด Standard ที่แผน §1 ระบุ
- **ยืนยันไม่ได้:** ผลตรวจ "หลังแก้ครั้งสุดท้าย" ของผู้ทำ; เวลาในหัว digest (13:21:20) อยู่ก่อน mtime ล่าสุดของไฟล์ที่แก้ (13:21:49) ผลที่ผู้ตรวจรันซ้ำตรงกับที่อ้าง

## Council Pressure-Test
- **Lenses Used:** Contrarian, Outsider, Executor
- **Preserved Dissent (Contrarian):** "Option A moves the Standard-tier record into a mutable PR description that git does not hold and no validator reads. Implementer and Verifier can write into the same field, so after merge nobody can prove who wrote the verdict or which commit it covered."
  แผน §2 ยอมรับความเสี่ยงนี้แล้ว จึงไม่นับเป็น finding
- **Outsider:** ผู้ใช้ใหม่ที่ถาม "งาน docs ของฉันใครใส่ผลทดสอบ" หรือ "ผล security ของ Framework ลงที่ไหน" ยังไม่ได้คำตอบเดียว
- **Executor:** M1-M3 แก้ได้ในข้อความของ agent prompts และ PR/MR templates โดยไม่ต้องแก้ code
- **Blind-Spot Check:** ไม่มีกฎว่าเมื่อมี commit ใหม่หลัง review แล้ว verdict ใน `## Review` หมดอายุ ทั้งแผนและ implementation ไม่ได้กล่าวถึง; เสนอให้ `## Review` ระบุ commit SHA ที่ตรวจ (ข้อเสนอ ไม่ใช่เงื่อนไขของ verdict)
- **Verdict & One Next Step:** `changes_requested`; ก้าวแรกคือเสนอ plan amendment ของ PLAN-008 สำหรับข้อที่เป็นช่องว่างของแผน (รวมการตัดสิน M2b) ให้ Human อนุมัติ แล้วแก้ M1-M3, sync adapters และรัน §4 ใหม่

## เงื่อนไขก่อน Merge (หลังแก้ findings)
- Commit 4 (protected paths) ต้องอยู่ใน PR และ Human เป็นผู้ commit ด้วย `SDLC_ALLOW_PROTECTED=1`
- ทุก commit ที่แก้ `.agents/` ต้องมี mirror ตรงกัน และ CI ผ่าน 6/6
- ต้อง re-review ส่วนที่แก้ใหม่

## Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer / Tech Lead]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`

---

## Round 2

> รีวิวซ้ำเมื่อ 2026-11-27 หลัง Amendment A1 (`plan-008-prompt-consistency.md` §7) เลขบรรทัดในส่วนนี้อ้าง tree หลัง A1 ส่วนเลขบรรทัดใน Round 1 อ้าง tree ก่อน A1
> **Verdict รอบ 2: `changes_requested`** (Blocker 0, Major 1, Minor 5)

### Review Scope & Traceability Check
- **Spec:** PLAN-008 §1-§6 และ §7 Amendment A1 (บันทึกว่า Approved 2026-11-27 13:55:18 +07; ผู้ตรวจยืนยันข้อความใน chat เองไม่ได้ Human ยืนยันที่ Gate 3)
- **Diff:** 34 tracked files, +200 / -124 เทียบ `origin/main` `c39c6cc`; ยังไม่ commit, ไม่มีไฟล์ staged
- **วิธีหาส่วนที่เปลี่ยน:** เทียบกับสำเนา working tree ที่เก็บไว้ตอน Round 1 แล้วจึงอ่าน digest เป็นลำดับสุดท้าย

### Spec Compliance & Architectural Drift

#### A1 conformance
- [x] A1-01 ถึง A1-18: ข้อความ `+` ของทุก block อยู่ในไฟล์เป้าหมาย (รวมทั้ง PR และ MR template) และข้อความ `-` ที่ถูกแทนไม่เหลือ (ตรวจด้วย script)
- [x] ส่วนต่างของไฟล์ canonical เทียบ Round 1 มีเฉพาะที่ §7.2 ระบุ
- [x] `plan-008-prompt-consistency.md` §1-§6 ไม่เปลี่ยน เพิ่มเฉพาะ frontmatter `amendment:` และ §7
- [x] นอก §7.2 ที่เปลี่ยน: mirrors, change digest (ตาม §7.3 ข้อ 2) และไฟล์รีวิวนี้ ไม่มีการแก้ `scripts/`, `orchestrator/`, `tests/`, `.codex/`, evals หรือ protected paths เพิ่ม
- [x] ข้อความกรณี Framework ที่เกินแผนใน Round 1 ได้รับการรับรองใน §7

#### สถานะ findings ของ Round 1

| ID | สถานะ | หลักฐาน | ส่วนที่เหลือ |
| :--- | :--- | :--- | :--- |
| M1 | Resolved (ส่วนที่มีอยู่ก่อนเลื่อนเป็น G10) | `code-reviewer-agent.md:15,21,30`; `security-audit-agent.md:17`; `council-pressure-test/SKILL.md:10`; `dev-coding-agent.md:21`; PR/MR template `:34` | `dev:29`, `tdd-implementation/SKILL.md:13` ยังบันทึกหลักฐาน Framework ใน digest แต่สอดคล้องแล้ว เพราะ `reviewer:30` ถือเป็นข้ออ้างที่ต้องตรวจ; `constitution.md:16`, `dynamic-routing.md:17`, `AGENTS.md:152-153` อยู่ใน G10 |
| M2a | Resolved | `qa-function-agent.md:20,24` (รวม Docs-Only, ระบุ `## Verification`) | กรณีมี work item ดู R2-m1 |
| M2b | Partly resolved | `qa-function-agent.md:21,24`; PR/MR template `:15,17` | R2-M1 |
| M3 | Resolved สำหรับ interactive harness | PR/MR template `:9-13`; `AGENTS.md:59` | orchestrator ใส่เฉพาะ constitution, role, skills (`orchestrator/core/loader.py:133-152`) จึงไม่เห็นกฎ draft (เกี่ยว H1); ดู R2-m2 |
| m1 | Resolved | PR/MR template `:26`; `code-reviewer-agent.md:31`; council skill `:10` | ดู R2-m3 |
| m2 | Resolved | `sa-architect-agent.md:23,31` | ที่ลง Fast-Track Spec / Change Plan ยังเป็น G3 (`sa:21`) |
| m3 | Resolved | `dev-coding-agent.md:30` | - |
| m4 | Resolved | `AGENTS.md:116` | - |
| m5 | Resolved เป็นส่วนใหญ่ | digest `:11,28,39,42,44` | ดู R2-m4 |
| m6 | Partly resolved | §7.3 ข้อ 5 เพิ่มกฎ stage รายไฟล์; ยังไม่มีไฟล์ staged | `.obsidian/` ยังไม่อยู่ใน `.gitignore` และ `.patch` ยัง untracked; ตรวจได้จริงตอน commit |
| noted: บรรทัดว่าง | Resolved | `AGENTS.md:147-148` | - |
| noted: ชื่อไฟล์ nit-cap | คงไว้โดยอนุมัติ | §7.4 | - |
| trace scrub / commit SHA / Framework `REVIEW.md` | บันทึกเป็น follow-up | G11 / G12 / G10 | - |

### Findings Summary (Blocker / Major / Minor)

**Blocker:** ไม่มี

| Severity | Location | Finding | Required Action |
| :--- | :--- | :--- | :--- |
| **Major** R2-M1 (ช่องว่างของ A1) | `qa-function-agent.md:21,24`; `constitution.md:16`; `code-reviewer-agent.md:15,30,31`; `review-gate.schema.yaml` `blocking_conditions`; `bug-fix-flow.md:10,16-17` | **Traceability ของ High-Risk bug fix ไม่มีผู้บังคับ และช่องว่างไม่ block** (1) `qa:24` ให้ "report any behaviour left without a test as a gap" และเรียกตารางนั้นว่า Gate 3 traceability evidence ขณะที่ constitution ต้องการ 100% ไม่มีไฟล์ใดระบุว่าพฤติกรรมที่ไม่มี test ทำให้ Gate 3 ไม่ผ่าน: Blocker ใน `reviewer:31` และ `blocking_conditions` กล่าวถึง "missing evidence" / verification output ซึ่งไม่ได้ระบุ coverage ที่ขาด ผู้อ่านจึงอาจนับตารางที่มี gap เป็นหลักฐานครบ (2) reviewer ไม่ถูกสั่งให้ตรวจตารางนี้ และ `reviewer:15` ไม่มี input กรณี High-Risk Fast-Track (3) `bug-fix-flow.md:10` ให้ `dev-coding-agent` เป็นผู้เขียน reproduction test แทน QA ได้ แต่คำสั่งทำตารางอยู่ใน QA prompt เท่านั้น | Amendment A2 (ข้อความใน prompt ไม่ต้องแตะ protected path) เช่น: `qa:24` / reviewer step 3 ระบุว่า "สำหรับ High-Risk bug fix ผู้ตรวจต้องยืนยันตาราง; พฤติกรรมที่ไม่ได้ map เป็น Blocker เว้นแต่ Human waive ในบันทึกรีวิว" และให้ `bug-fix-flow` ระบุเจ้าของตาราง หรือ Human waive R2-M1 อย่างชัดแจ้งที่ Gate 3 พร้อมบันทึกเป็น follow-up ใต้ G3 |
| **Minor** R2-m1 | `qa-function-agent.md:19,21,24` | กรณีมี work item: `:19` ยังกำหนด output เป็น `test-report.md` (schema 13 sections) แต่ `:24` บอกว่า steps 2-5 (รวมการกรอก 13 sections) ไม่ใช้กับ Bug Fix / Test-Only / Docs-Only จึงไม่รู้ว่าบันทึกผลที่ไหน (เกิดจากข้อความรอบแรก ผู้ตรวจไม่ได้แยกเป็นข้อใน Round 1) | ระบุที่ลงกรณีมี work item |
| **Minor** R2-m2 | `AGENTS.md:59`; `docs/contracts/README.md:10,12` | draft ที่เก็บใน `docs/handoff/` เป็นไฟล์ git-tracked อาจกลายเป็นบันทึกชุดที่สองที่ไม่ตรงกับ PR | ระบุว่า PR เป็นฉบับจริงหลังโพสต์ |
| **Minor** R2-m3 | PR/MR template `:26` เทียบ `review.template.md:38`, council skill `:9` | template เขียน "`risk_tier: high` only" แต่ที่อื่นรวมกรณี Human-flagged high reversal cost | ใช้ถ้อยคำเดียวกัน |
| **Minor** R2-m4 | digest `:16-21,28` | ตารางไฟล์ไม่กล่าวถึงช่อง Plan Checkpoint, traceability, Council slot และกฎ draft ที่ A1 เพิ่ม; "(gate ไม่เปลี่ยน)" ไม่บอกว่าหลักฐาน Gate 3 ของ High-Risk bug fix เปลี่ยน และยังมีช่องว่าง R2-M1 | อัปเดต digest |
| **Minor** R2-m5 | `.gitignore`, `docs/handoff/` | m6 ส่วนที่เหลือ: `git add docs/` จะรวม `.patch` | stage รายไฟล์ตาม §7.3 |

#### Walk ตาม route (หลัง A1)

| Route | ผล |
| :--- | :--- |
| New Feature, API/Schema | ไม่มีการเปลี่ยนที่กระทบ |
| Standard ไม่มี work item (bug fix, config) | input, ที่ลง plan / evidence / review และผู้ตรวจชัดแล้ว (R2-m2; orchestrator ติด H1) |
| Standard มี work item | ผ่าน ยกเว้นข้อจำกัด `tasks.schema.json` เดิม |
| Test-Only / Docs-Only | ไม่มี work item: ผ่าน; มี work item: R2-m1 |
| High-Risk bug fix | R2-M1 และเรื่องที่ต้องรับทราบด้านล่าง |
| High-Risk config / data | ไม่มีรูปแบบหลักฐาน traceability (A1 ครอบเฉพาะ bug fix) เกี่ยว G3 มีอยู่ก่อน |
| Framework ไม่มี work item | ที่ลง spec, digest, review, security, council ตรงกันใน prompts และ PR/MR template; เอกสาร governance เป็น G10 |

#### เรื่องที่ Human ต้องรับทราบ (ไม่นับเป็น finding แยก)
- **ที่อยู่ของหลักฐาน High-Risk:** `constitution.md:16` ให้ข้อยกเว้น PR description เฉพาะ Standard และ trace export ต้องมี `--work-item` จึงตีความได้ว่า High-Risk bug fix ต้องมี work item แต่ `qa:21` และ PR/MR template `:15,17` วางตาราง traceability ไว้ใน PR description ที่แก้ย้อนหลังได้ (§2 ยอมรับความเสี่ยงนี้เฉพาะ Standard) ข้อความนี้อยู่ใน §7.2 ที่อนุมัติแล้ว แต่ไม่ได้ระบุความเสี่ยงสำหรับ High-Risk ส่วนกรณีไม่มี work item ไม่มีที่ลง review ของ High-Risk Fast-Track ใน `reviewer:19-21`, `security:17`, PR/MR `:34` (A1 ตัดคำว่า "otherwise" ซึ่งเดิมครอบกรณีนี้แบบผิดเงื่อนไข)
- **การแคบลงที่อนุมัติแล้ว (§7.1 ข้อ 2):** QA ของ High-Risk bug fix ครอบเฉพาะ negative / security cases ที่ Fast-Track Spec ระบุ แทนเทคนิค ISTQB เต็มชุด
- **มีอยู่ก่อน และควรเพิ่มใต้ G3:** `AGENTS.md:152` และ `bug-fix-flow.md:17` ให้รัน `validate_work_item.py` ซึ่งต้องมี `intent.md` และ `test-report.md` (`scripts/validate_work_item.py:234`) งาน Fast-Track จึงผ่านไม่ได้ G10 ครอบเฉพาะ Framework

ข้อเข้มขึ้นจาก A1 (digest ไม่ใช่หลักฐาน, re-approval เมื่อ drift, ไม่แนบ trace export, ต้องยืนยันก่อนแนบ log) ไม่พบการผ่อนกฎอื่น

### Verification Evidence (Tests & Linters)

macOS, Python 3.14.10, `PYTHONDONTWRITEBYTECODE=1`, `SDLC_TRACE_DIR` ชี้ temp dir

| คำสั่ง | ที่รัน | ผลที่เห็น |
| :--- | :--- | :--- |
| `sync-adapters.py --check` | สำเนา | PASSED, exit 0 |
| `validate-context-budget.py` | สำเนา | PASSED, exit 0 |
| `validate-contracts.py --check-defaults` | สำเนา | PASSED, exit 0 |
| `run_evals.py --mode contract` | สำเนา | PASSED 10/10, exit 0 |
| `validate_work_item.py --digest-file <PLAN-008 digest>` | สำเนา | PASSED, exit 0 |
| `python3 -m unittest discover -s tests` | repo จริง | 252 run, OK, skipped 3 |
| เหมือนกัน | สำเนาใน path ยาว | fail 1 (`test_export_scrubs_repo_and_home_paths`, สาเหตุเดิมตาม G11), skipped 3 |
| `git diff --check`, `git diff origin/main --check` | repo จริง | exit 0; ไม่พบ trailing whitespace ในเอกสาร `.md` ใหม่ |
| `git grep` ตาม §4 | repo จริง | 54 บรรทัด ข้อสังเกตเดิมเรื่องบรรทัดที่ไม่ผูกเงื่อนไข |
| `diff -rq` mirrors | repo จริง | ตรงกัน |
| ค้น path ส่วนตัว / token ในเอกสารใหม่ | repo จริง | ไม่พบ |

- ระหว่าง unittest ใน repo จริง ที่ `.sdlc/` เปลี่ยนเพียง mtime ของ `env.json`; ไฟล์ trace ไม่เปลี่ยน
- **ไม่ได้ตรวจ:** live eval / พฤติกรรมจริงของ agent, CI บน remote, Windows, Linux, Python 3.10 / 3.12, Docker, HTTP endpoint tests (ข้ามเมื่อไม่มี FastAPI), การแยก commit และ parity ราย commit

### Test Oracle Integrity Check
- [x] ไม่มีการแก้ `tests/`; evals ไม่เปลี่ยนจาก Round 1

### Security & OWASP Findings
- [x] A1 แก้เฉพาะข้อความ prompt / template ไม่มี code, AuthN/AuthZ, guard หรือ CI เปลี่ยน
- [x] ไม่พบ secret หรือ path ส่วนตัวในเอกสารใหม่
- ไม่พบช่องโหว่ระดับ Critical / High; trace scrub บันทึกเป็น G11 แล้ว

### Digest Claim Audit (อ่านเป็นลำดับสุดท้าย)
- **ยืนยันได้:** `:11` (ระบุว่ายังมีช่องว่าง), `:39` สถานะ approval ตามที่บันทึกในแผนและผล Round 1, `:40` ผลตรวจตรงกับที่ผู้ตรวจรันซ้ำ, `:42`, `:44` (ยืนยันว่า workflow ของ GitHub / GitLab ไม่มีขั้นติดตั้ง package และ `tests/test_orchestrator_api.py:208` ข้ามเมื่อไม่มี FastAPI)
- **ไม่ครบ / ชี้นำเกินไป:** `:16-21`, `:28` (R2-m4)
- **ยืนยันไม่ได้:** ความสดของผลตรวจฝั่งผู้ทำ เพราะเวลาในหัว digest (13:55:18) ตรงกับ mtime ของไฟล์ที่แก้ล่าสุด

### Council Pressure-Test
- **Lenses Used:** Contrarian, Outsider, Executor
- **Preserved Dissent (Contrarian):** "A1 turns 100% traceability for a production bug fix into a free-text table in an editable PR description, written by the party being checked or by QA, with a built-in slot for admitting gaps and nobody told to reject them."
- **Counter-view:** ก่อน A1 route นี้ไม่มีรูปแบบหลักฐานที่ทำได้จริงเลย และการให้รายงาน gap ตรง ๆ ดีกว่าการอ้าง 100% โดยไม่มีข้อมูล จึงจัดเป็น Major ที่แก้ได้ด้วยหนึ่งถึงสองประโยค ไม่ใช่ Blocker
- **Blind-Spot Check:** ตาราง traceability วัดจาก "behaviour" ใน Fast-Track Spec ซึ่งยังไม่มี template หรือ ID (G3) ความครบ 100% จึงขึ้นกับว่า spec เขียนพฤติกรรมครบหรือไม่
- **Verdict & One Next Step:** `changes_requested`; ให้ Human เลือกระหว่างอนุมัติ A2 สำหรับ R2-M1 หรือ waive อย่างชัดแจ้งที่ Gate 3

### เงื่อนไขก่อน Merge
- ปิดหรือ waive R2-M1
- Commit 4 (protected paths) อยู่ใน PR และ Human commit ด้วย `SDLC_ALLOW_PROTECTED=1`
- stage รายไฟล์ ไม่รวม `.patch` และ `.obsidian/`; ทุก commit มี mirror ตรงกัน และ CI ผ่าน 6/6

### Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer / Tech Lead]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`

---

## Round 3

> รีวิวซ้ำเมื่อ 2026-11-27 หลัง Amendment A2 (§8) เฉพาะส่วนที่เปลี่ยนจาก Round 2 เลขบรรทัดอ้าง tree หลัง A2
> **Verdict รอบ 3: `approved_for_human_gate`** (Blocker 0, Major 0, Minor เปิดอยู่ 3: R2-m5, R3-m1, R3-m2)

### Review Scope & Traceability Check
- **Spec:** PLAN-008 §8 (บันทึกว่า Approved 2026-11-27 14:04:38 +07; ผู้ตรวจยืนยันข้อความใน chat เองไม่ได้)
- **Diff:** 34 tracked files, +208 / -130 เทียบ `origin/main`; ยังไม่ commit, ไม่มีไฟล์ staged
- `docs/diagrams/` อยู่นอกขอบเขตและไม่ได้ตรวจ

### Spec Compliance & Architectural Drift
- [x] A2-01 ถึง A2-09 ตรงตาม §8.2 รวม PR และ MR template; ข้อความเดิมที่ถูกแทนไม่เหลือ
- [x] ไฟล์ canonical ที่เปลี่ยนจาก Round 2 มีเฉพาะส่วนใน §8.2; นอกจากนั้นเป็น mirrors, digest, แผน (frontmatter และ §8) และไฟล์รีวิว
- [x] R2-M1 ที่แก้ตาม A2 ตรงกับ "100% traceability" ใน `constitution.md:16`

| ID | สถานะ | หลักฐาน | ส่วนที่เหลือ |
| :--- | :--- | :--- | :--- |
| R2-M1 | Resolved | กฎ block: `code-reviewer-agent.md:30`, `qa-function-agent.md:24`, `bug-fix-flow.md:13`, PR/MR template `:17`; เจ้าของและ fallback: `bug-fix-flow.md:13`, `dev-coding-agent.md:26`; ผู้ตรวจ: `reviewer:30` | `reviewer:15` ยังไม่ระบุ Fast-Track Spec เป็น input และที่ลงของ spec ยังไม่มี (G3); ความครบ 100% ขึ้นกับว่า spec เขียนพฤติกรรมครบ |
| R2-m1 | Resolved | `qa-function-agent.md:19-20` | ดู R3-m1 |
| R2-m2 | Resolved | `AGENTS.md:59` | ดู R3-m2 |
| R2-m3 | Resolved | PR/MR template `:26` | - |
| R2-m4 | Resolved | digest `:16-19,28,43` | - |
| R2-m5 | Open จนถึงตอน stage | §8.3 ข้อ 4; ไม่มีไฟล์ staged | `.obsidian/` ยังไม่ถูก ignore, `.patch` ยัง untracked |

### Findings Summary (Blocker / Major / Minor)
**Blocker:** ไม่มี **Major:** ไม่มี

| Severity | Location | Finding | Suggested Action |
| :--- | :--- | :--- | :--- |
| **Minor** R3-m1 | `AGENTS.md:59`; `code-reviewer-agent.md:30` | กฎ draft ก่อนมี PR ครอบเฉพาะ "Standard-Tier" แต่ตาราง High-Risk bug fix ต้องอยู่ใน `## Verification` และการไม่มีตารางเป็น Blocker จึงไม่ระบุที่อยู่ของตารางหาก review ก่อนเปิด PR | รวมใน G3 |
| **Minor** R3-m2 | `AGENTS.md:59`; `docs/contracts/README.md:12` | A2 ให้วาง draft แบบ uncommitted ใน `docs/handoff/` ซึ่งตาราง placement ระบุว่า Git Tracked และไม่มี `.gitignore` pattern กันไว้ (ความเสี่ยงแบบเดียวกับ `.patch`) | follow-up: กำหนด pattern ที่ ignore หรือย้ายที่เก็บ draft (A2 ไม่เปิดให้แก้ protected path) |
| **Minor** R2-m5 | `.gitignore`, `docs/handoff/` | ตามตารางด้านบน | stage รายไฟล์ |

ข้อจำกัดใน §8.4 (ตารางใน PR ที่แก้ย้อนหลังได้, Fast-Track ที่ไม่มี work item ไม่มีที่ลงรีวิว, validator ต้องมี `intent.md`, ขอบเขต QA, ไม่มี validator ตรวจตาราง) Human ต้องรับทราบที่ Gate 3 เพิ่มเติมใต้ G3: `qa:20` ระบุ "no `test-report.md`" ขณะ validator ต้องการไฟล์นี้ด้วย และ `tasks.json` ของงานที่ไม่มี `SPEC` / `FS` ยังติด `tasks.schema.json` เดิม

### Verification Evidence (Tests & Linters)

| คำสั่ง (`SDLC_TRACE_DIR` ชี้ temp dir) | ผลที่เห็น |
| :--- | :--- |
| `sync-adapters.py --check`, context budget, `validate-contracts.py --check-defaults`, digest validator (สำเนา) | PASSED ทุกคำสั่ง |
| `run_evals.py --mode contract` (สำเนา) | PASSED 10/10 |
| `python3 -m unittest discover -s tests` (repo จริง) | 252 run, OK, skipped 3 |
| เหมือนกัน (สำเนา path ยาว) | fail 1 เดิม (G11), skipped 3 |
| `git diff --check`, `git diff origin/main --check` | exit 0 |
| `git grep` ตาม §4 | 55 บรรทัด; บรรทัดใหม่คือ `qa:20` ซึ่งผูกกับ work item |
| mirrors `diff -rq` | ตรงกัน |
| ค้น path ส่วนตัว / token ในเอกสาร PLAN-008 | ไม่พบ |

- ที่ `.sdlc/` เปลี่ยนระหว่าง unittest ใน repo จริงมีเพียง mtime ของ `env.json`; trace ไม่เปลี่ยน
- **ไม่ได้ตรวจ:** live eval, CI บน remote, Windows, Linux, Python 3.10 / 3.12, Docker, HTTP endpoint tests, การแยก commit

### Test Oracle Integrity Check
- [x] ไม่มีการแก้ `tests/`; evals ไม่เปลี่ยนจาก Round 2

### Security & OWASP Findings
- [x] A2 แก้เฉพาะข้อความ prompt / workflow / template ไม่พบช่องโหว่ระดับ Critical / High

### Digest Claim Audit (อ่านเป็นลำดับสุดท้าย)
- **ยืนยันได้:** `:16-19,28,39,40,43,44` ผลตรวจใน `:40` ตรงกับที่รันซ้ำ
- **ไม่ได้ระบุชื่อ:** ข้อจำกัด Fast-Track สองข้อใน §8.4 (ที่ลงรีวิว, validator ต้องมี `intent.md`) อยู่ใต้ "G2–G12" โดยรวม ให้อ่าน §8.4 ประกอบ
- **ยืนยันไม่ได้:** ความสดของผลตรวจฝั่งผู้ทำ (เวลาในหัว digest ตรงกับ mtime ของการแก้)

### Council Pressure-Test
- **Lenses Used:** Contrarian, Executor
- **Preserved Dissent (Contrarian):** "With no waiver path, a Fast-Track behaviour that cannot be expressed as a regression test, such as a rollback or a monitoring check, blocks Gate 3 with no defined exit; the only way out is an ad hoc Human override under the source-of-truth order."
  Human อนุมัติ "ไม่เพิ่มช่องทาง waive" ใน §8.1 ข้อ 1 จึงไม่นับเป็น finding (ทางออกที่เหลือคือคำสั่งของ Human ตาม `AGENTS.md:82`)
- **Blind-Spot Check:** กฎใหม่บังคับด้วย prompt และ Human เท่านั้น ยังไม่มี live eval ยืนยันว่า reviewer ทำตาม
- **Verdict & One Next Step:** `approved_for_human_gate`; ให้ Human ตัดสิน Gate 3 แล้ว stage รายไฟล์ตามแผน

### เงื่อนไขก่อน Merge
- Commit 4 (protected paths) อยู่ใน PR และ Human commit ด้วย `SDLC_ALLOW_PROTECTED=1`
- stage รายไฟล์ ไม่รวม `.patch`, `.obsidian/` และ draft ใน `docs/handoff/`
- ทุก commit มี mirror ตรงกัน และ CI ผ่าน 6/6
- หากแก้ไฟล์ใดหลังรอบนี้ ต้องรันตรวจใหม่และรีวิวส่วนที่เปลี่ยน

### Gate 3 Human Sign-Off
- **Reviewer:** `[Human Maintainer / Tech Lead]`
- **Decision:** `Pending` (`Approved` / `Changes Requested`)
- **Timestamp:** `YYYY-MM-DD`
