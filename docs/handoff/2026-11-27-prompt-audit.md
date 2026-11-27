# Prompt Audit: ai-agent-framework

- **วันที่:** 2026-11-27 (Asia/Bangkok) · **ฐานที่ตรวจ:** `origin/main` `c39c6cc`
- **Diff ที่เสนอ:** `2026-11-27-prompt-audit.patch` (ไฟล์ชั่วคราวในเครื่อง ยังไม่ได้ apply)

## 0. ข้อสมมติและขอบเขต

- **Target model:** Claude Sonnet 5.5 (โมเดลที่รัน audit; repo ไม่ pin โมเดลให้ agent ใด)
- **ผู้อ่านอื่น:** Codex และ Antigravity อ่าน `AGENTS.md` / `.agents/` ด้วย (พบ `gpt-5-codex`, `gemini-*`, `.codex/`) จึงไม่เสนอแก้แบบเฉพาะ Claude
- **ตรวจ:** `AGENTS.md`, `CLAUDE.md`, `.agents/` (7 agents, 6 skills, 2 workflows), mirror ใน `.claude/` `.agent/` (ตรวจผ่าน parity check), `.codex/README.md`, `docs/workflow/`, `constitution.md`, `docs/contracts/`, `docs/templates/`, `examples/project-packs/ebmc/`, โค้ดประกอบ prompt (`orchestrator/core`, `graphs`), `evals/run_evals.py` และ eval case ที่เกี่ยวข้อง (06, 09, 10), guard policy
- **ไม่ได้ตรวจ:** ไฟล์ settings / hooks ของ agent (ตั้งใจไม่เปิด), `docs/reference-architecture/` (archive อ่านอย่างเดียว; พบ pin `claude sonnet 4.6` ที่ `function-test-agent.md:7` ไม่เสนอแก้), config ระดับผู้ใช้นอก workspace (`~/.claude/`), memory ของ agent, eval case อื่น และเอกสารแผน / คู่มือใน `docs/plans`, `docs/guides`
- **ที่มาของข้อความ:** git history มี 4 commit ของ prompt (`851a3f7`, `c78aed9` = 2026-11-21; `a40866e`, `211d7c2` = 2026-11-22) ไม่มีบรรทัดที่แก้อาการของโมเดลรุ่นเก่า

## 1. สรุป

ข้อความแทบไม่มีรูปแบบล้าสมัยของโมเดลรุ่นเก่า (ไม่มี pressure language ที่ต้องลด, ไม่มี prefill / think-step-by-step) ปัญหาจริงคือ **prompt ขัดกับระบบเอง**:

1. **Role prompt ไม่ตรงกับ route** ที่ `router.py` เรียกใช้: QA / SA / Dev ถูกสั่งให้ต้องมี `intent.md` / `spec.md` ใน route ที่ไม่มีไฟล์นั้น เมื่อรันแบบ non-interactive อาจค้างที่คำถามหรือทำต่อไม่ได้
2. **Standard Tier ไม่มีที่ลงของ artifact** ที่สอดคล้องกัน (routing, `CLAUDE.md`, schema, validator พูดไม่ตรงกัน) ข้อนี้ต้องให้คุณตัดสิน
3. **ภาษาของผลรีวิวไม่ตรงกัน** (Important/Nit กับ Blocker/Major/Minor) และ security audit ถูกสั่งให้อ่าน `REVIEW.md` ที่ยังไม่ถูกสร้าง

| กลุ่ม | จำนวน | ใน diff |
| :--- | ---: | ---: |
| 1. ข้อความล้าสมัย (numeric cap) | 1 | 1 |
| 2. ข้อมูลเก่า / ขัดกันเอง | 19 | 10 |
| 3. Tool descriptions | N/A (ไม่มี tool schema) | - |
| 4. Config / สถาปัตยกรรม | 3 | 0 |

## 2. Findings ที่มีใน diff

| ID | ตำแหน่ง | หลักฐาน (quote) | ปัญหา (pattern: เหตุผล) | ความมั่นใจ | Action |
| :-- | :--- | :--- | :--- | :-- | :--- |
| F1 | `sa-architect-agent.md:16,23` · `qa-function-agent.md:14,21` · `dev-coding-agent.md:14` | "Verify `intent.md` has Gate 1 approval." / "if missing, ask before designing tests" | ขัดกัน: `router.py:123-150` เรียก SA ใน `impact_check`, `spec_update`; QA ใน `reproduce_oracle`, `author_tests_or_docs`; constitution บอกว่า route เหล่านี้ไม่มี `intent.md` | High | rewrite ให้ input ขึ้นกับ route (ยังบังคับ Gate 1 ใน route ที่มี Gate 1) |
| F2 | `security-audit-agent.md:14` | "PR diff, and `REVIEW.md`" | ขัดกัน: audit รันขนานกับ review (`router.py:95-100`, `new-feature-flow.md:15`) | High | rewrite |
| F4 | `code-reviewer-agent.md:3,29` | "**Important** ... vs **Nit**" | ขัดกัน: template และ `review-gate.schema.yaml` ใช้ Blocker/Major/Minor; บรรทัด 34 ของไฟล์เดียวกันบล็อกด้วย "Blocker" | High | rewrite |
| F5 | `AGENTS.md:64,153` | "Update ... `CHANGELOG.md`" | ข้อมูลเก่า: `CONTRIBUTING.md:73` ห้ามแก้ด้วยมือ และ release-please เป็นผู้สร้าง | High | rewrite |
| F6 | `dev-coding-agent.md:28` | "update `AGENTS.md` / `CLAUDE.md` if a recurring mistake rule" | ขัดกับ `AGENTS.md:90` และ `tdd-implementation` (ต้องเสนอเป็น Framework Change) การแก้ทำให้เข้มขึ้น | High | rewrite |
| F9 | `bug-fix-flow.md:16` | "Confirm regression test existed ... generate `REVIEW.md`." | ขัดกัน: constitution ต้องมี security audit สำหรับ High-Risk และ router รัน security agent แต่ workflow ไม่มี | High | rewrite (เข้มขึ้น) |
| F10 | `AGENTS.md:58` | "if a low-risk task touches auth, ..." | ขัดกับ constitution บรรทัด 27 ที่ครอบ low/medium | High | rewrite (เข้มขึ้น) |
| F11 | `AGENTS.md:16,24` | "mirrored to `.claude/`, `.codex/`, `.agent/`" | ข้อมูลเก่า: `sync-adapters.py:21-25` ไม่ mirror agents/skills ไป `.codex/` และ workflows ไป `.agent/` เท่านั้น | High | rewrite |
| F7 | `review.template.md:5` (แก้ผ่าน `code-reviewer-agent.md:19`) | `verdict: pending_review` | ค่าไม่อยู่ใน enum ของ schema | Medium | add คำสั่งให้แทนค่า |
| F8 | `dev-coding-agent.md:31` | "Never delete, skip, or weaken QA assertions" | อธิบายไม่ครบ: guard บล็อก role นี้ไม่ให้แก้ test ที่ commit แล้วและ test report ทุกกรณี (`policy.json` roles) agent เดาไม่ได้ | Medium | add |
| C1 | `code-reviewer-agent.md:29` (+ eval 06) | "**Cap Nits at maximum 5 items**" | กลุ่ม 1f numeric output ceiling: โมเดลปัจจุบันทำตามตัวเลขตรงตัว บอกเป็นเกณฑ์ ("ที่ maintainer จะลงมือแก้") ได้ผลตรงเจตนากว่า | Medium | rewrite |

**หมายเหตุ:** F4 กับ C1 อยู่บรรทัดเดียวกันจึงรวมเป็น hunk เดียว ถ้าต้องการคง cap ให้เปลี่ยนท้ายประโยคเป็น "cap Minor findings at 5 items and give a count for the rest" และไม่ต้องรับ hunk ที่สองของ eval 06 ส่วน F9, F10 อ้างอิง constitution โดยไม่แก้ constitution

## 3. Flag (ไม่มีใน diff: ต้องตัดสินใจ หรือเป็นโค้ด / ไฟล์ protected)

| ID | ตำแหน่ง | ปัญหา | ความมั่นใจ | ทางเลือกที่แนะนำ |
| :-- | :--- | :--- | :-- | :--- |
| G1 | `CLAUDE.md:8`, `dev-coding-agent.md:17-18,23`, `tdd-implementation:9`, `AGENTS.md:151`, `dynamic-routing.md:12,15,16`, `tasks.schema.json:7`, `validate_work_item.py:234` | Routing บอกว่า Standard ใช้แค่ defect summary / regression test / `REVIEW.md` แต่ที่อื่นบังคับ `plan.md` + `tasks.json`; `tasks.json` ต้องมี `INT`/`SPEC`; validator ต้องมี 4 ไฟล์; ไม่มีที่วาง `REVIEW.md` ของงานที่ไม่มี work item | High | กำหนดว่า Standard **ไม่ต้องมี work item** (บันทึก plan และ review ใน PR) แล้วแก้ทั้งชุดพร้อมกัน |
| G2 | `new-feature-flow.md:15-16` กับ `code-reviewer-agent.md:16,22` | Digest ถูกสร้างหลัง review แต่ reviewer ต้องตรวจข้ออ้างใน digest; `bug-fix-flow` ไม่มีขั้นสร้าง digest | High | ย้ายขั้น digest ไปก่อน review (คง "diff first, digest last") |
| G3 | `dynamic-routing.md:13`, `bug-fix-flow.md:7-16`, `router.py:120-131` | ลำดับ QA / Dev / Security ของ high-risk bug fix ไม่ตรงกัน; "Fast-Track Spec", "Change Plan", "Postmortem note" ไม่มี template หรือที่วาง | High | เลือกลำดับตาม router แล้วกำหนด template |
| G4 | `dynamic-routing.md:21` | Escalation พูดถึงเฉพาะ **Low** (constitution ครอบ low/medium) และกฎ ~300 บรรทัดใน `AGENTS.md:58` ไม่อยู่ใน constitution | High | แก้เป็น low/medium และระบุเกณฑ์ขนาดที่ constitution (protected) |
| G5 | `security-audit-agent.md:3`, `code-reviewer-agent.md:22`, `router.py:97`, `dynamic-routing.md:12` | Medium bug fix: router รัน security agent แต่ routing doc ไม่มี; "add Security only if sensitive areas are touched" เกิดไม่ได้ใน Standard เพราะแตะแล้วต้อง escalate | Medium | กำหนดเกณฑ์เดียว |
| G6 | `intent.schema.yaml:10` (protected) กับ `router.py:9-15` | `work_type` ของ intent มี `enhancement` และไม่มี `config_data_change` ฯลฯ | High | ปรับ contract โดยมนุษย์ (`SDLC_ALLOW_PROTECTED=1`) |
| G7 | `router.py:146-150` กับ `policy.json` roles | Framework route ให้ `dev-coding-agent` implement แต่ guard ห้าม role นี้เขียน protected / CI paths; `constitution.md:35` พูดถึง agent ทุกตัว แต่ guard บังคับเฉพาะ role นี้ (กับ pre-commit) | Medium | ตัดสินว่า Framework Change ใช้ role ใด |
| G8 | `ebmc-function-test-agent.md:4-7`, `loader.py:98-148` | Orchestrator โหลด skill ของ pack แต่ไม่โหลด pack agent และ **ไม่ใส่ `robot-framework-ebmc` เข้า prompt ใดเลย** (รันยืนยันแล้ว: `False`); `extends:` ไม่มีใคร parse | High | แก้ loader ให้รองรับ overlay หรือระบุใน pack README ว่าใช้ด้วยมือเท่านั้น |
| G9 | `ba-po-agent.md:31` | "if `docs/workflow/` specifies Jira/GitHub linkage" แต่ไฟล์ใน `docs/workflow/` ไม่มีข้อกำหนดนี้ (อาจตั้งใจไว้สำหรับ repo ปลายทาง) | Low | ชี้ไปที่ `spec-driven-design` ข้อ 3 |
| H1 | `sdlc_pipeline.py:223-235` | Stage context ส่งแค่ success ของ stage ก่อนหน้า agent ไม่ได้รับ path ของ artifact (ROADMAP มีแผนแล้ว) | High | ส่ง work item path |
| H2 | `sdlc_pipeline.py:87-92` | `CliHarnessExecutor` ไม่บันทึก token / cost จึงวัดผลการปรับ prompt ไม่ได้ | High | อ่าน usage จาก output ของ CLI |
| H3 | `run_evals.py:44-45` | Live eval ใช้ `--permission-mode plan` ขณะที่ case ขอ artifact; ยังไม่ได้ทดลองรันว่ากระทบผลหรือไม่ | Low | ทดลองรัน 1 case |

**นอกขอบเขต prompt แต่พบระหว่างตรวจ:** `router.py:73` จับ keyword แบบ substring ทำให้ "author unit tests" ถูก escalate เป็น high เพราะมี `auth` (รันยืนยันแล้ว)

## 4. สิ่งที่ตั้งใจคงไว้

- รายการ **Always / Ask First / Never** ใน `AGENTS.md` และ constitution: เป็นนโยบายจริงพร้อมเหตุผล
- ข้อความ "ONLY ... never" ใน description ของ `council-pressure-test`: เป็น trigger text
- Gate และขั้นตอนที่เป็นเลขลำดับ: ลำดับมีผลจริง
- ข้อบังคับ 13 sections และ ID pattern ของ QA: เป็น contract ที่ validator ตรวจ

## 5. การตรวจ diff

ทดสอบบนสำเนาของ `origin/main` ใน scratchpad (ไม่ได้แก้ repo):

- `git apply --check` กับ working tree ปัจจุบัน: ผ่าน
- `sync-adapters.py --sync` / `--check`, context budget, contract validation, contract evals 10/10: ผ่าน
- Unit tests 252: fail 1, skip 3 (`test_export_scrubs_repo_and_home_paths`) ซึ่ง **fail เหมือนกันบนฐานที่ยังไม่แก้** สาเหตุที่คาดคือ path ของ scratchpad ยาวจนคำสั่งถูกตัด (ยังไม่ได้พิสูจน์)
- ยังไม่ได้ทดสอบพฤติกรรมจริงของ agent ก่อน/หลังแก้ (ต้องรัน live eval ซึ่งมีค่าใช้จ่าย)

## 6. ขั้นต่อไป

การนำ diff ไปใช้และการแก้ G1 อยู่ใน [PLAN-008](../plans/plan-008-prompt-consistency.md) ซึ่งเป็น Framework Change (Gate 2 → Gate 3) ไฟล์ `.patch` เป็นไฟล์ทำงานชั่วคราวที่ไม่ commit
