---
plan_id: PLAN-008
intent_ref: N/A (Framework / Process Change)
spec_ref: this document (Framework Spec — Gate 2)
owner: sa-architect-agent (design) / dev-coding-agent (implement)
status: approved
created: 2026-11-27 (Asia/Bangkok)
amendment: A1 approved (see §7); A2 approved (see §8)
---

# Implementation Plan: Prompt Consistency and Standard-Tier Records (G1 = Option A)

> **Route:** Framework Change → **Gate 2: Framework Spec** (อนุมัติแผนนี้) → Implement → **Gate 3: Release & Merge**
> **ที่มา:** [Prompt audit 2026-11-27](../handoff/2026-11-27-prompt-audit.md) · Human เลือก G1 ทางเลือก A ("เก็บใน PR") เมื่อ 2026-11-27
> **Protected paths ที่แตะ:** `docs/operating-model/constitution.md`, `docs/contracts/README.md` → Human maintainer ต้อง commit ด้วย `SDLC_ALLOW_PROTECTED=1`
> **Branch:** `feat/PLAN-008-prompt-consistency` (จาก `origin/main` `c39c6cc`)

## 1. Scope

**ทำในรอบนี้**
1. Findings F1, F2, F4–F11 และ C1 จาก audit (11 ข้อ)
2. G1 ทางเลือก A (รวมคำตอบของ G5 เฉพาะเรื่องที่ลงของผล security)

**ไม่ทำ (follow-up):** G2 ลำดับ digest · G3 Fast-Track flow / template · G4 escalation · G5 ใครต้องรัน security audit · G6 `work_type` ใน intent schema · G7 role ของ Framework route · G8 EBMC pack ไม่ถูกโหลด · G9 Jira linkage · H1–H3 orchestrator / evals · keyword `auth` จับ "author" · validator โหมด Standard

## 2. กติกาใหม่ (ความหมายของ A)

| กรณี | Plan | หลักฐานทดสอบ | Review | Validator / trace export |
| :--- | :--- | :--- | :--- | :--- |
| Standard **ไม่มี** work item | PR/MR `## Plan Checkpoint` | PR/MR `## Verification` | PR/MR `## Review` | ไม่ต้อง |
| Standard ที่ **มี** work item อยู่แล้ว | `work/<INT-xxx>/plan.md` + `tasks.json` | `tasks.json` | `work/<INT-xxx>/REVIEW.md` | validator ไม่ต้อง (ต้องมี intent/spec) |
| High-Risk / Framework | เหมือนเดิม | เหมือนเดิม | เหมือนเดิม | เหมือนเดิม |

- `## Review` ใช้หัวข้อเดียวกับ `required_sections` ใน `review-gate.schema.yaml` (หัวข้อที่ไม่เกี่ยวเขียน `N/A`) และลงท้ายด้วย verdict `approved_for_human_gate` / `changes_requested` / `blocked_security`
- **Implementer ≠ Verifier ยังบังคับ:** ผู้ตรวจอิสระเป็นคนเขียนเนื้อหา `## Review`
- ถ้า `security-audit-agent` ถูกเรียก (router เรียกใน Standard ระดับ medium) ผลลงใน `## Review` หัวข้อ Security & OWASP Findings
- **การโพสต์ลง PR/MR เป็น external action:** agent ร่างข้อความ → Human ยืนยันทุกครั้ง → จึงโพสต์ (กฎ Ask First เดิม) ถ้ายังไม่มี PR ให้ใส่ในร่าง description
- Gate 3 sign-off ของ Standard = Human กด merge
- **ความเสี่ยงที่ยอมรับ:** PR description แก้ย้อนหลังได้และไม่อยู่ใน git

## 3. การแก้ไขราย commit

### Commit 1 — `docs(plans): add PLAN-008 and prompt audit report`
`docs/plans/plan-008-prompt-consistency.md`, `docs/handoff/2026-11-27-prompt-audit.md` (ไม่ commit `.patch` และ `.obsidian/`)

### Commit 2 — `fix(agents): align role prompts with routes and contracts`
Apply `docs/handoff/2026-11-27-prompt-audit.patch` แล้ว `sync-adapters.py --sync` (F1, F2, F4–F11, C1; ไฟล์: `AGENTS.md`, `.agents/`, `evals/datasets/06-*.json`, mirrors) รายละเอียดอยู่ในรายงาน §2

### Commit 3 — `docs(governance): record Standard-tier plan and review in the PR`
เขียนทับข้อความ **หลัง** Commit 2

| ไฟล์ : บรรทัด | ข้อความใหม่ |
| :--- | :--- |
| `AGENTS.md:31` | ต่อท้าย: "Standard-Tier work without a work item records its plan, verification, and review in the PR/MR description." |
| `AGENTS.md:55` | "(lightweight `REVIEW.md` by an independent reviewer)" → "(lightweight review by an independent reviewer: `## Review` in the PR/MR, or `REVIEW.md` when a work item exists)" |
| `AGENTS.md:70` | ต่อท้ายรายการ artifact: "; for Standard work without a work item, the PR/MR `## Plan Checkpoint`, `## Verification`, and `## Review` sections" |
| `AGENTS.md:102` | วงเล็บท้ายคำสั่ง → "(High-Risk / Framework work items; add `--require-digest`)" |
| `AGENTS.md:116` | "...inside `work/<INT-xxx>/` (Standard work without a work item: attach to the PR/MR) instead of pasting inline." |
| `AGENTS.md:149` | "### Extended DoD (High-Risk / Framework Tier)" |
| `AGENTS.md:150-152` | คงสาระเดิม ตัด "Standard Tier omits `--require-digest`" และเพิ่มก่อนหัวข้อ Extended: "- **Standard Tier:** QA test oracles not weakened; observed verification and an independent review are recorded (PR/MR sections, or the work item when one exists)." |
| `CLAUDE.md:8` | "Always enter **Plan Mode** before multi-file implementation and record the plan where its tier requires: Standard work without a work item in the PR/MR `## Plan Checkpoint`; work items in `work/<INT-xxx>/plan.md` + `tasks.json`; framework changes without a work item in `docs/plans/plan-<NNN>-<slug>.md`. Never create ... at the repo root." |
| `dev-coding-agent.md` Outputs | `plan.md` / `tasks.json` ขึ้นต้น "With a work item:" + เพิ่ม "Standard Tier without a work item: no `plan.md` / `tasks.json`; the plan is the PR/MR `## Plan Checkpoint` and commands with observed output go under `## Verification`." |
| `dev-coding-agent.md` step 1, 3, 5, 6 | 1: "write the plan before editing source code (`plan.md` + `tasks.json` with a work item, otherwise the Plan Checkpoint packet)" · 3: "one slice (`TASK-xxx`) at a time" · 5: "With a work item, set `\"passes\": true` ... ; otherwise record the command and observed output under `## Verification`." · 6: "Update the recorded plan ..." |
| `tdd-implementation` 9, 11, 13 | หลักเดียวกับ dev agent (เงื่อนไข "with a work item") |
| `code-reviewer-agent.md:3` และ description ของ `dev-coding-agent`, `tdd-implementation` | reviewer: "produces a review record with Blocker / Major / Minor findings"; อีกสองไฟล์: "`tasks.json` state tracking for work items" |
| `code-reviewer-agent.md:12,15,26` | อ้าง "the artifacts the route produced" แทนการบังคับ `intent.md` / `spec.md` / `plan.md` / `tasks.json` |
| `code-reviewer-agent.md` Outputs | "With a work item: `work/<INT-xxx>/REVIEW.md` ... Standard Tier without a work item: a draft `## Review` section for the PR/MR using the same headings and verdict values; post it only after Human confirmation." |
| `code-reviewer-agent.md` step 0, 3, 4 | "still produce `REVIEW.md`" → "still produce the review record"; step 3: "in `tasks.json`, `## Verification`, or CI output"; step 4: "record the result under `## Council Pressure-Test` in the review record" |
| `security-audit-agent.md` Outputs | "Security findings section in the review record (`REVIEW.md`, or the PR/MR `## Review` draft) ..." |
| `qa-function-agent.md` Outputs | เพิ่ม "Bug Fix or Test-Only without a work item: the test or doc itself; no `test-report.md`." |
| `sa-architect-agent.md` Outputs | เพิ่ม "Standard impact check without a work item: impact and rollback notes for the Plan Checkpoint; no `spec.md`." |
| `council-pressure-test` 10, 32 | "in the review record (`REVIEW.md` or the PR/MR `## Review`) or in an ADR" |
| `bug-fix-flow.md` step 4–5 | "generate the review record (`REVIEW.md`, or the PR/MR `## Review` for Standard work without a work item)"; "Human Maintainer reads the review record and merges" |
| `dynamic-routing.md:12,15,16` | "`REVIEW.md` (lightweight)" → "lightweight review (PR/MR `## Review`, or `REVIEW.md` with a work item)" คงเงื่อนไข full passes ของแถว 16 |
| `README.md:32` | "...→ `change-digest.md`) live together in `work/<INT-xxx>/` ... Standard-Tier work without a work item keeps its plan, verification, and review in the PR/MR. Artifacts never go at the repo root." |
| `README.md:45` | "Plan Checkpoint (recorded in the PR/MR)" → "Plan Checkpoint and review (recorded in the PR/MR)" |
| `review.template.md` | เพิ่มใต้หัวเรื่อง: "> Standard Tier without a work item: copy the `##` headings below (as `###`) into the PR/MR `## Review` section and omit the frontmatter; end with the verdict." |
| `evals/datasets/03-*.json` prompt | ขึ้นต้น "For a bug fix tracked as work item INT-102, ..." |
| PR template **และ** GitLab MR template | ดูด้านล่าง (คงความต่างเดิมของบรรทัด 14, 18) |

เพิ่มก่อน `## Gate & Verification Checklist`:

```markdown
## Verification *(Standard Tier without a work item)*
- **Command / observed result:** `<command>` → `<pass / fail / skip counts>`

## Review *(Standard Tier without a work item; written by an independent reviewer)*
### Review Scope & Traceability Check
### Spec Compliance & Architectural Drift
### Verification Evidence (Tests & Linters)
### Test Oracle Integrity Check
### Security & OWASP Findings
### Findings Summary (Blocker / Major / Minor)
### Gate 3 Human Sign-Off
- **Reviewer verdict:** `approved_for_human_gate` | `changes_requested` | `blocked_security`
- Human sign-off = merge
```

บรรทัด checklist:
- 13: "Independent review recorded (`REVIEW.md` with a work item, otherwise `## Review` above); lightweight for Standard Tier; `code-reviewer-agent` + `security-audit-agent` for medium/high risk"
- 17: "Agent trace summary attached for High-Risk work (`...export...`)" — ให้ตรง constitution บรรทัด 16 (เดิม "medium/high")

### Commit 4 — `docs(governance): allow PR review records for Standard tier` *(Human, `SDLC_ALLOW_PROTECTED=1`)*

`constitution.md:16` เปลี่ยนเฉพาะคำว่า `` `REVIEW.md` `` เป็น:

```text
`REVIEW.md` (Standard work without a work item: the `## Review` section of the PR/MR description)
```

`docs/contracts/README.md` เพิ่มแถวใต้ Work-Item Artifacts (หลังบรรทัด 9):

```text
| **Standard-Tier Plan & Review** *(no work item)* | PR/MR description: `## Plan Checkpoint`, `## Verification`, `## Review` | No (platform record) | No `plan.md`, `tasks.json`, `REVIEW.md`, validator run, or trace export. The `## Review` section uses the `required_sections` of [review-gate.schema.yaml](review-gate.schema.yaml); its frontmatter applies only to `REVIEW.md` files |
```

ไม่แก้ `review-gate.schema.yaml` และ `validate_work_item.py` (ไม่พบ script ที่อ่าน schema นี้)

### Commit 5 — `docs(handoff): add PLAN-008 digest and review`
`docs/handoff/<date>-plan-008-prompt-consistency-digest.md`, `docs/plans/plan-008-review.md`

## 4. Verification (ก่อนขอ Gate 3)

```bash
python3 scripts/sync-adapters.py --check
python3 scripts/validate-context-budget.py
python3 scripts/validate-contracts.py --check-defaults
python3 evals/run_evals.py --mode contract
python3 -m unittest discover -s tests
python3 scripts/validate_work_item.py --digest-file docs/handoff/<date>-plan-008-prompt-consistency-digest.md
git diff --check
git grep -n -E "REVIEW\.md|plan\.md|tasks\.json|work/<INT" -- AGENTS.md CLAUDE.md README.md .agents docs/workflow docs/operating-model .github .gitlab
```

**เกณฑ์ผ่าน:** คำสั่งทั้งหมดผ่าน · ทุกผลของ `git grep` ผูกกับ "มี work item" หรือ High-Risk หรือเป็นข้อห้ามวางไฟล์ที่ root / ตารางตำแหน่งไฟล์ · ผู้ตรวจอิสระ approve · CI ผ่าน 6/6

## 5. Risks & Rollback

| ความเสี่ยง | การรับมือ |
| :--- | :--- |
| Merge โดยไม่มี Commit 4 ทำให้ constitution ยังบังคับ `REVIEW.md` | ห้าม merge จนกว่า Commit 4 อยู่ใน PR |
| พฤติกรรม agent เปลี่ยนแต่ evals ตรวจแค่โครงสร้าง | ระบุใน digest ว่ายังไม่ได้ทดสอบด้วย live eval |
| High-Risk ที่ไม่มี work item export trace ไม่ได้ (`--work-item` บังคับ) | ช่องว่างเดิม บันทึกเป็น follow-up ไม่แก้ในรอบนี้ |
| release-please ออก patch release จาก `fix(agents)` | ตั้งใจ |

**Rollback:** revert merge commit แล้ว `sync-adapters.py --sync` ไม่มี migration หรือข้อมูล runtime

## 6. Gate 2 Approval
- **Approver:** Human maintainer
- **Decision:** `Approved`
- **Timestamp:** 2026-11-27 13:20:14 +07
- **Evidence:** chat reply "อนุมัติ เริ่มทำ"

## 7. Amendment A1 — แก้ตามผลรีวิวอิสระ

- **Status:** `Approved`
- **ที่มา:** [plan-008-review.md](plan-008-review.md) verdict `changes_requested` (Major 3, Minor 6 + 2)
- **Protected paths:** ไม่มีการแก้เพิ่ม
- **ความสัมพันธ์กับ §2–§3:** ข้อความใน A1 ใช้แทนข้อความเดิมเมื่อขัดกัน และรับรองข้อความกรณี Framework ที่ไม่มี work item ซึ่งเพิ่มเกินแผนตอน implement

### 7.1 การตัดสินใจที่ต้องอนุมัติ
1. **Framework Change ที่ไม่มี work item:** บันทึกรีวิว (รวม security และ council) อยู่ที่ `docs/plans/plan-<NNN>-review.md`; หลักฐานคือ CI หรือคำสั่งที่ผู้ตรวจรันเอง change digest เป็นข้ออ้างที่ต้องตรวจ
2. **QA กับ High-Risk bug fix:** ไม่บังคับ report 13 sections แต่ต้อง map ทุกพฤติกรรมใน Fast-Track Spec ไปยัง regression test และรายงานช่องว่าง ใช้เป็นหลักฐาน traceability ของ Gate 3 (ที่ลง / template ของ Fast-Track Spec ยังเป็น G3)
3. **Standard ก่อนมี PR:** ร่างใน chat หรือ `docs/handoff/` แล้วโพสต์หลัง Human ยืนยัน

### 7.2 ข้อความที่แก้ (`-` เดิม, `+` ใหม่)

#### A1-01 (M1) — `code-reviewer-agent.md`

```diff
-`## Verification` (Standard) or the `docs/plans/` spec and change digest evidence (Framework).
+`## Verification` (Standard) or the `docs/plans/` spec (Framework).
```

#### A1-02 (M1) — `code-reviewer-agent.md`

```diff
-3. Verify fresh execution evidence in `tasks.json`, `## Verification`, or CI output (no skipped assertions).
+3. Verify fresh execution evidence in `tasks.json`, `## Verification`, CI output, or commands you run yourself (no skipped assertions). A change digest is a claim to check, not evidence.
```

#### A1-03 (M1) — `security-audit-agent.md`

```diff
-or the PR/MR `## Review` draft for Standard work without a work item)
+the PR/MR `## Review` draft for Standard work without a work item, or `docs/plans/plan-<NNN>-review.md` for a Framework Change without one)
```

#### A1-04 (M1+m1) — `council-pressure-test/SKILL.md`

```diff
-under `## Council Pressure-Test` in the review record (`REVIEW.md` or the PR/MR `## Review`) or in an ADR (`docs/adr/`)
+under `## Council Pressure-Test` in `REVIEW.md` or `docs/plans/plan-<NNN>-review.md`, under `### Council Pressure-Test` inside the PR/MR `## Review`, or in an ADR (`docs/adr/`)
```

#### A1-05 (m1) — `code-reviewer-agent.md`

```diff
-record the result under `## Council Pressure-Test` in the review record,
+record the result under `## Council Pressure-Test` in the review record (`###` inside a PR/MR `## Review`),
```

#### A1-06 (M1) — `dev-coding-agent.md`

```diff
-- High-Risk / Framework Tier: `work/<INT-xxx>/change-digest.md` ([change-digest.template.md](../../docs/templates/change-digest.template.md)) before PR/MR creation.
+- High-Risk / Framework Tier: `work/<INT-xxx>/change-digest.md`, or `docs/handoff/YYYY-MM-DD-<slug>-digest.md` without a work item ([change-digest.template.md](../../docs/templates/change-digest.template.md)), before PR/MR creation.
```

#### A1-07 (M1) — PR template และ GitLab MR template

```diff
-- [ ] Independent review recorded (`REVIEW.md` with a work item, otherwise `## Review` above);
+- [ ] Independent review recorded (`REVIEW.md` with a work item; without one, `## Review` above for Standard or `docs/plans/plan-<NNN>-review.md` for a Framework Change);
```

#### A1-08 (M2a+M2b) — `qa-function-agent.md`

```diff
-- Bug Fix or Test-Only without a work item: the test or doc itself; no `test-report.md`.
+- Bug Fix, Test-Only, or Docs-Only without a work item: the test or doc itself, with each command and its observed result under the PR/MR `## Verification`; no `test-report.md`.
+- High-risk bug fix: a table under the PR/MR `## Verification` that maps each behaviour in the Fast-Track Spec to a regression test.
```

#### A1-09 (M2b) — `qa-function-agent.md`

```diff
-Bug Fix and Test-Only / Docs-Only routes have neither: write the reproduction test or the requested test/doc from the summary, and skip steps 2-5.
+Bug Fix and Test-Only / Docs-Only routes have neither: write the reproduction test or the requested test/doc from the summary and record each command with its observed result; steps 2-5 do not apply. For a high-risk bug fix, also map every behaviour in the Fast-Track Spec to a regression test, cover the negative and security cases it names, and report any behaviour left without a test as a gap: this mapping is the Gate 3 traceability evidence.
```

#### A1-10 (M2b+M3) — PR template และ GitLab MR template

```diff
-## Verification *(Standard Tier without a work item)*
-- **Command / observed result:** `<command>` → `<pass / fail / skip counts>`
+## Verification *(Standard Tier without a work item; also the high-risk bug fix traceability mapping)*
+- **Command / observed result:** `<command>` → `<pass / fail / skip counts>`
+- **Traceability (high-risk bug fix only):** `<Fast-Track Spec behaviour>` → `<regression test>`
```

#### A1-11 (M3) — PR template และ GitLab MR template

```diff
-- **Link to approval (chat/comment):** `<url or quote>`
+- **Link to approval (chat/comment):** `<url or quote>`
+- **Target files:** `<paths>`
+- **Test strategy:** `<failing test first / checks>`
+- **Verification commands:** `<commands>`
+- **Risks:** `<risks>`
+- **Rollback:** `<steps>`
```

#### A1-12 (M3) — `AGENTS.md`

```diff
-2. **Plan Packet:** Propose target files, test strategy, verification commands, risks, and rollback steps.
+2. **Plan Packet:** Propose target files, test strategy, verification commands, risks, and rollback steps. Before a PR/MR exists, keep the Standard-Tier `## Plan Checkpoint`, `## Verification`, and `## Review` text as a draft description (in chat, or in `docs/handoff/` if it must outlive the session) and post it after Human confirmation.
```

#### A1-13 (m1) — PR template และ GitLab MR template

```diff
-### Findings Summary (Blocker / Major / Minor)
+### Findings Summary (Blocker / Major / Minor)
+### Council Pressure-Test *(optional: `risk_tier: high` only)*
```

#### A1-14 (m2) — `sa-architect-agent.md`

```diff
-- Standard impact check without a work item: impact and rollback notes for the Plan Checkpoint; no `spec.md`.
+- Standard impact check without a work item: impact and rollback notes for the Plan Checkpoint; no `spec.md`.
+- Framework Change without a work item: the Framework Spec at `docs/plans/plan-<NNN>-<slug>.md`.
```

#### A1-15 (m2) — `sa-architect-agent.md`

```diff
-6. Stop at **Gate 2 Approval** for SA/Tech Lead sign-off.
+6. On routes with Gate 2, stop at **Gate 2 Approval** for SA/Tech Lead sign-off. A Standard impact check has no Gate 2: hand the notes to the Plan Checkpoint.
```

#### A1-16 (m3) — `dev-coding-agent.md`

```diff
-6. Update the recorded plan in the same commit if implementation details change, and,
+6. Update the recorded plan if implementation details change (in the same commit when the plan is a file; otherwise edit the PR/MR section). If scope, touched files, or risk drift from the approved plan, stop and get re-approval (`AGENTS.md` §3). Also,
```

#### A1-17 (m4) — `AGENTS.md`

```diff
-(Standard work without a work item: attach them to the PR/MR)
+(Standard work without a work item: attach test logs to the PR/MR after Human confirmation; no trace export)
```

#### A1-18 (minor) — `AGENTS.md`

```diff
-short ELI10 section in the PR/MR description.
-
-- **Standard Tier:**
+short ELI10 section in the PR/MR description.
+- **Standard Tier:**
```

### 7.3 ขั้นตอนและเกณฑ์ผ่าน
1. แก้ตาม 7.2 → `sync-adapters.py --sync` (รวมเข้า Commit 3)
2. อัปเดต change digest: ตัดข้ออ้างว่าคู่มือตรงกันทุก route และ "High-Risk / Framework ยังใช้ชุดเดิม", เพิ่ม follow-up ที่ตกหล่น, บันทึกผลรีวิว (m5)
3. รันคำสั่งใน §4 ใหม่ทั้งหมด
4. ผู้ตรวจอิสระรีวิวซ้ำส่วนที่เปลี่ยน
5. Stage ไฟล์ทีละรายการ ห้าม `git add docs/` และไม่ commit `.patch`, `.obsidian/` (m6); `plan-008-review.md` อยู่ใน Commit 5

### 7.4 Follow-up ที่เพิ่ม (ไม่ทำใน A1)
- **G10:** `constitution.md:16`, `dynamic-routing.md:17`, Extended DoD ยังเรียก `REVIEW.md` / `work/` สำหรับ Framework ที่ไม่มี work item
- **G11:** trace export ตัดคำสั่งก่อนแทน path (`trace_cli.py:84`, `:240`) ทำให้ absolute path ยาวหลุดบางส่วน
- **G12:** `## Review` ยังไม่ระบุ commit SHA ที่ตรวจ verdict จึงไม่หมดอายุเมื่อมี commit ใหม่
- CI ไม่ติดตั้ง FastAPI ทำให้เทสต์ HTTP endpoint ของ orchestrator ถูกข้าม
- ชื่อไฟล์ `06-code-review-nit-cap.json` ยังอ้าง nit cap (คงไว้)

### 7.5 Gate 2 Approval (A1)
- **Approver:** Human maintainer
- **Decision:** `Approved`
- **Timestamp:** 2026-11-27 13:55:18 +07
- **Evidence:** chat reply "อนุมัติ A1"

## 8. Amendment A2 — แก้ตามผลรีวิวรอบ 2

- **Status:** `Approved`
- **ที่มา:** [plan-008-review.md](plan-008-review.md) Round 2 `changes_requested` (Major 1, Minor 5)
- **Protected paths:** ไม่มีการแก้เพิ่ม
- **ความสัมพันธ์กับ §7:** ใช้แทนข้อความใน A1 เมื่อขัดกัน

### 8.1 การตัดสินใจที่ต้องอนุมัติ
1. **High-Risk bug fix:** ทุกพฤติกรรมใน Fast-Track Spec ต้องมี regression test พฤติกรรมที่ไม่มีเทสต์หรือไม่มีตารางเป็น **Blocker** ของ Gate 3 (ตรงกับ "100% traceability" ใน constitution) ไม่เพิ่มช่องทาง waive
2. **เจ้าของตาราง:** `qa-function-agent`; ถ้า QA ไม่ได้รัน ผู้เขียนเทสต์เป็นคนทำ; reviewer ตรวจเทียบกับ Fast-Track Spec เอง
3. **ร่างใน `docs/handoff/`:** ไม่ commit และเมื่อโพสต์แล้ว PR/MR เป็นบันทึกเดียว

### 8.2 ข้อความที่แก้ (`-` เดิม, `+` ใหม่)

#### A2-01 (R2-M1) — `code-reviewer-agent.md`

```diff
-A change digest is a claim to check, not evidence.
+A change digest is a claim to check, not evidence. For a high-risk bug fix, check the traceability table in `## Verification` against the Fast-Track Spec yourself: a missing table, or any behaviour without a regression test, is a **Blocker**.
```

#### A2-02 (R2-M1) — `qa-function-agent.md`

```diff
-and report any behaviour left without a test as a gap: this mapping is the Gate 3 traceability evidence.
+and put the table under `## Verification`: it is the Gate 3 traceability evidence, and any behaviour left without a regression test blocks Gate 3.
```

#### A2-03 (R2-M1) — `workflows/bug-fix-flow.md`

```diff
-   - Lock the test oracle (do not weaken assertions during Step 3).
+   - Lock the test oracle (do not weaken assertions during Step 3).
+   - High-Risk: put a table under the PR/MR `## Verification` that maps every Fast-Track Spec behaviour to a regression test. `qa-function-agent` owns it; if QA does not run, whoever writes the tests does. A behaviour without a test blocks Gate 3.
```

#### A2-04 (R2-M1) — `dev-coding-agent.md`

```diff
-2. For bug fixes, write a failing reproduction test first and confirm it fails as expected before coding the fix.
+2. For bug fixes, write a failing reproduction test first and confirm it fails as expected before coding the fix. On a high-risk bug fix where `qa-function-agent` did not run, also write the table under `## Verification` that maps every Fast-Track Spec behaviour to a regression test.
```

#### A2-05 (R2-M1) — PR template และ GitLab MR template

```diff
-- **Traceability (high-risk bug fix only):** `<Fast-Track Spec behaviour>` → `<regression test>`
+- **Traceability (high-risk bug fix only; one line per Fast-Track Spec behaviour, a missing test blocks Gate 3):** `<behaviour>` → `<regression test>`
```

#### A2-06 (R2-m1) — `qa-function-agent.md`

```diff
-- `work/<INT-xxx>/test-report.md` conforming to
+- New Feature / API-Schema Change: `work/<INT-xxx>/test-report.md` conforming to
```

#### A2-07 (R2-m1) — `qa-function-agent.md`

```diff
-- Bug Fix, Test-Only, or Docs-Only without a work item: the test or doc itself, with each command and its observed result under the PR/MR `## Verification`; no `test-report.md`.
+- Bug Fix, Test-Only, or Docs-Only: the test or doc itself and each command with its observed result, under the PR/MR `## Verification` (without a work item) or in the work item's `tasks.json` evidence; no `test-report.md`.
```

#### A2-08 (R2-m2) — `AGENTS.md`

```diff
-(in chat, or in `docs/handoff/` if it must outlive the session) and post it after Human confirmation.
+(in chat, or in an uncommitted file under `docs/handoff/` if it must outlive the session) and post it after Human confirmation; the PR/MR copy is then the only record.
```

#### A2-09 (R2-m3) — PR template และ GitLab MR template

```diff
-### Council Pressure-Test *(optional: `risk_tier: high` only)*
+### Council Pressure-Test *(optional: `risk_tier: high` or Human-flagged high reversal cost)*
```

### 8.3 ขั้นตอนและเกณฑ์ผ่าน
1. แก้ตาม 8.2 → `sync-adapters.py --sync`
2. อัปเดต digest: เพิ่มสิ่งที่ A1 / A2 เพิ่มลงตารางไฟล์ และระบุว่าหลักฐาน Gate 3 ของ High-Risk bug fix เปลี่ยน (R2-m4)
3. รันคำสั่งใน §4 ใหม่ทั้งหมด และให้ผู้ตรวจคนเดิมรีวิวเฉพาะส่วนที่เปลี่ยน
4. Stage ไฟล์ทีละรายการ ไม่ commit `.patch` และ `.obsidian/` (R2-m5)

### 8.4 ข้อจำกัดที่ยังเหลือ (ให้ Human รับทราบที่ Gate 3)
- ตาราง traceability อยู่ใน PR description ที่แก้ย้อนหลังได้ (§2 ยอมรับความเสี่ยงนี้เฉพาะ Standard; A2 ขยายถึง High-Risk bug fix)
- High-Risk Fast-Track ที่ไม่มี work item ยังไม่มีที่ลงผลรีวิว (รวมใน G3)
- `validate_work_item.py` ต้องมี `intent.md` งาน Fast-Track จึงผ่าน Extended DoD ไม่ได้ (มีมาก่อน รวมใน G3)
- QA ครอบเฉพาะกรณีที่ Fast-Track Spec ระบุ ตามที่อนุมัติใน §7.1
- ไม่มี validator ตรวจตาราง การบังคับพึ่ง reviewer และ Human

### 8.5 Gate 2 Approval (A2)
- **Approver:** Human maintainer
- **Decision:** `Approved`
- **Timestamp:** 2026-11-27 14:04:38 +07
- **Evidence:** chat answer "อนุมัติ A2 และรีวิวรอบ 3"
