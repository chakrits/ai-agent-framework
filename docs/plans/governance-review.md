# Governance & Rules Review

- **Document ID:** `PLAN-SDLC-004-A` (analysis; proposes changes, does not change rules by itself)
- **Date:** 2026-11-21
- **Scope:** ไฟล์ที่กำหนดกฎทั้งหมดใน framework
  - **เอกสารกฎ:** `docs/operating-model/constitution.md`, `AGENTS.md`, `CLAUDE.md`, `docs/workflow/core-bootloader.md`, `docs/workflow/dynamic-routing.md`, `docs/operating-model/bands.yaml`
  - **ส่วนที่บังคับใช้จริง:** `scripts/sdlc_guard/policy.json`, `.claude/settings.json`, `.codex/hooks.json`, `docs/contracts/*`
  - **ส่วนประกอบอื่น:** `.agents/agents/*` (Rules & Boundaries), `.agents/skills/*`, `.agents/workflows/*`, PR/MR templates
- **Method:** อ่านทุกไฟล์และใช้ `grep` นับว่ากฎแต่ละข้อถูกเขียนซ้ำกี่ที่ แล้วเทียบว่ากฎใดมี hook / pre-commit / CI บังคับจริง (อ้างอิงผล test และ CI run [44866058493](https://github.com/chakrits/ai-agent-framework/actions/runs/44866058493))

---

## 1. แผนที่กฎปัจจุบัน: กฎไหนมีอะไรบังคับจริง

| กฎ | เขียนไว้ที่ (จำนวนไฟล์) | ระดับการบังคับจริง |
| :--- | :--- | :--- |
| Test Oracle Integrity | 10 ไฟล์ (constitution, AGENTS.md, 3 agents, tdd skill, bug-fix flow, review schema, PR/MR templates) | 🟢 **Hook:** dev agent แก้ test ที่ commit แล้ว / QA spec ไม่ได้ |
| No Self-Approval | 3 ไฟล์ (constitution, dev agent, reviewer agent) | 🔴 **Advisory อย่างเดียว:** ไม่มี branch protection / CODEOWNERS |
| HITL Gates 1–3 | constitution, routing, workflows, templates | 🟠 **Markdown เท่านั้น:** `Decision: Pending` ไม่มีหลักฐานว่าใครอนุมัติเมื่อไร; orchestrator API ข้าม gate ได้ |
| Protected paths / Constitution protection | constitution, policy.json | 🟢 **Hook + pre-commit** (ต้องมี human override) |
| Secret hygiene | constitution, owasp skill, policy.json, settings.json | 🟢 **Hook + pre-commit** สำหรับ path; 🔴 ไม่มี secret scanner สำหรับ *เนื้อหา* ของไฟล์ |
| Evidence over confidence | constitution, dev agent, tdd skill | 🟡 **Validator** ตรวจ `tasks.json` (`passes:true` ต้องมี evidence) แต่ไม่ได้เช็คว่า evidence จริง |
| Spec before code | AGENTS.md, routing, workflows | 🔴 **Advisory:** ไม่มีอะไรตรวจว่ามี `intent.md` / `spec.md` ที่ approved ก่อนเขียน code |
| Classify before acting | AGENTS.md, bootloader | 🔴 **Advisory** |
| Sandbox / worktree isolation | constitution ("should") | 🔴 **ไม่ได้ตั้งค่า** (ไม่มี sandbox ใน `settings.json`) |
| Context budget | validator | 🟢 **CI** |
| Adapter parity | validator | 🟢 **CI** |
| Plan Mode ก่อนแก้หลายไฟล์ | CLAUDE.md, dev agent, tdd skill | 🔴 **Advisory** |
| Mistake-twice → update AGENTS.md | dev agent, tdd skill, reviewer | 🔴 **Advisory** และ **ขัดกับ routing** (ดู C3) |
| Stage 6 bands | bands.yaml | 🔴 `bands.py` ไม่ได้อ่านไฟล์นี้ |

**สรุปตัวเลข:** จากกฎหลัก 13 ข้อ มี 5 ข้อที่บังคับใช้ได้จริง (🟢), 2 ข้อบังคับบางส่วน และ 6 ข้อเป็นเพียงคำแนะนำ

---

## 2. Pros

1. **แยก Advisory กับ Deterministic ชัดเจนในเชิงหลักการ**: ตรงกับ Claude Playbook (Play 5–6) และตอนนี้มี guard ข้าม OS ที่ทำงานจริงบน 3 OS แล้ว
2. **Constitution สั้น (4 หัวข้อ, ~30 บรรทัด)**: อ่านจบเร็ว และไม่กิน context
3. **Risk-based routing**: ไม่บังคับ ceremony เต็มกับงานเล็ก มี escalation rule สำหรับ auth / payment / schema
4. **HITL 3 gates ผูกกับ artifact ชัด**: Gate 1 = intent, Gate 2 = spec, Gate 3 = REVIEW + tests
5. **Separation of Duties ครบ 3 ทาง**: คนเขียน code ≠ คนเขียน test oracle ≠ คน approve
6. **Policy-as-data**: `policy.json` เป็นแหล่งเดียวของ protected / secret / role rules และทดสอบได้ด้วย fixtures
7. **Reviewer มี Nit cap (≤5) และแยก Important / Nit**: ลดภาระคนตรวจ

## 3. Cons

| # | ปัญหา | หลักฐาน | ผลกระทบ |
| :-: | :--- | :--- | :--- |
| **C1** | **กฎเดียวเขียนซ้ำหลายที่ ไม่มี Rule ID** | test-oracle อยู่ใน 10 ไฟล์ | แก้กฎแล้วต้องตามแก้หลายจุด จึง drift ง่าย; อ้างอิงกฎใน review / trace ไม่ได้ |
| **C2** | **กฎสำคัญยังเป็นแค่คำแนะนำ** | ตาราง §1 (6/13 ข้อ) | ขัดกับหลัก "Harness over Prompting" ของ framework เอง |
| **C3** | **Mistake-twice rule ขัดกับ routing** | dev agent ถูกสั่งให้แก้ `AGENTS.md` แต่ bootloader จัดการแก้ `AGENTS.md` เป็น Framework Change (High, ต้องผ่าน Gate 2/3) | agent ได้รับคำสั่งที่ขัดกันเอง |
| **C4** | **Plan Mode "Always" ขัดกับ "minimum safe workflow"** | `CLAUDE.md:8` กับ `AGENTS.md` ข้อ 1 | งานเล็ก (docs / typo) ต้องเขียน plan เกินจำเป็น; ใช้ `plan.md` ไฟล์เดียวที่ root ทำให้งานหลายชิ้นชนกัน |
| **C5** | **Gate approval ไม่มีหลักฐานที่ตรวจสอบได้** | template ใช้ `Reviewer: [Name]` / `Decision: Pending` | ใครก็แก้ Markdown ให้เป็น `Approved` ได้ (รวมถึง agent) |
| **C6** | **No Self-Approval ไม่มีกลไกบังคับ** | ไม่มี branch protection / CODEOWNERS บน GitHub | push ตรงเข้า `main` ได้ |
| **C7** | **อ้างอิง path ที่ไม่มีอยู่** | constitution อ้าง `.sdlc` / "CI gate scripts" โดยไม่ระบุไฟล์ | กฎคลุมเครือ |
| **C8** | **คำว่า should / must ปนกัน** | "Coding agents should execute inside isolated sandboxes" | ไม่รู้ว่าข้อไหนห้ามละเมิดเด็ดขาด |
| **C9** | **Permissions ใน `settings.json` ไม่สอดคล้องกับ policy** | `Read(.env*)` block `.env.example` ด้วย แต่ policy อนุญาต; `Bash(curl *)` ข้ามได้ด้วย `python -c` หรือ `Invoke-WebRequest` | ให้ความรู้สึกปลอดภัยเกินจริง; Codex / Antigravity ไม่มี permission ชุดนี้ |
| **C10** | **ไม่มีบันทึกว่าใครทำอะไร** | ไม่มี agent trace / audit log | ตรวจย้อนหลังไม่ได้ว่ากฎถูกละเมิดหรือ agent ใช้คำสั่งอะไร |
| **C11** | **ไม่มี versioning ของกฎ** | ไม่มี version / CHANGELOG / tag | แยกไม่ได้ว่า run / trace ไหนใช้กฎ version ใด |
| **C12** | **PR template ไม่ครอบคลุมสิ่งที่ CI ตรวจจริงแล้ว** | ยังอ้าง check ชื่อเดิม; ไม่มีช่อง Framework Change / human override | checklist ไม่ตรงกับความจริง |

---

## 4. ข้อเสนอ: ปรับ / แก้ / ลด

### 4.1 รวมกฎเป็น Rule Registry เดียว (แก้ C1, C2, C8, C11)

สร้าง `docs/operating-model/rules.yaml` เป็นแหล่งเดียว โดยแต่ละกฎมี:

```yaml
- id: SDLC-R03
  title: Test oracle integrity
  level: MUST            # MUST = ต้องมี enforcer; SHOULD = advisory
  statement: Implementation agents never weaken or edit committed QA test oracles.
  enforced_by: [hook:policy.roles.dev-coding-agent, review:REVIEW.md#test-oracle]
  tests: [tests/test_guard_git_tracked.py]
  since: 0.2.0
```

- **CI validator:** กฎ `MUST` ทุกข้อต้องมี `enforced_by` และ `tests` อย่างน้อย 1 ตัว ไม่อย่างนั้น CI fail (บังคับใช้หลัก "Every rule has an enforcer and a test")
- **Constitution:** สร้างตารางกฎจาก registry อัตโนมัติ ส่วนไฟล์อื่น (agents / skills / templates) อ้างแค่ `SDLC-Rxx` ไม่ต้องเขียนกฎซ้ำ
- **Trace:** บันทึก rule ID ทุกครั้งที่ guard block (ผูกกับ §5 ของ plan)

### 4.2 แก้ความขัดแย้ง (C3, C4, C7)

| ปัญหา | ข้อเสนอ |
| :--- | :--- |
| C3 Mistake-twice | agent **เสนอ** กฎใหม่ลงใน `docs/operating-model/mistake-log.md` (ไม่ protected) แล้วให้คนย้ายขึ้น `AGENTS.md` ผ่าน Framework Change |
| C4 Plan Mode | เปลี่ยนเป็น "plan ตาม risk tier": low = ไม่ต้องมี plan; medium/high = `work/<ID>/plan.md`; เลิกใช้ `plan.md` ไฟล์เดียวที่ root |
| C7 `.sdlc` | ให้ constitution อ้าง `protected_globs` ใน `policy.json` แทนการเขียน path เอง |

### 4.3 เพิ่มกลไกบังคับ (C5, C6, C10)

- **Gate evidence:** การอนุมัติใช้ GitHub PR review approval หรือ signed tag แทนการแก้ Markdown (ทาง D ที่คุยไว้; ทำเมื่อคุณพร้อม)
- **Agent trace:** บันทึกทุก tool call ใน local (ดู [plan-005-trace-v1-1.md](plan-005-trace-v1-1.md)) เป็น audit log
- **Content secret scan:** เพิ่มใน pre-commit (regex เดียวกับที่ใช้ redact trace)

### 4.4 ลด / ตัดออก

| สิ่งที่ลด | เหตุผล |
| :--- | :--- |
| ประโยคกฎที่ซ้ำใน agents / skills / templates (~20 บรรทัด) | อ้าง rule ID แทน ช่วยลด context ที่ agent ต้องโหลด |
| `Bash(curl *)`, `Bash(wget *)` ใน deny list | ให้ความรู้สึกปลอดภัยเกินจริง ควรย้ายเรื่อง network ไปใช้ sandbox / network policy ของ harness และระบุเป็น SHOULD |
| `Read(.env*)` | ให้ guard เป็นตัวตัดสินแทน เพราะ policy มี allowlist `.env.example` อยู่แล้ว |
| โฟลเดอร์ reference `01.`–`09.` ที่ว่าง | เป็น noise สำหรับ agent ที่ค้นไฟล์ |
| `scripts/guard-protected-paths.sh`, `setup-hooks.sh` | wrapper ที่ deprecated แล้ว ลบได้ใน release ถัดไป |

### 4.5 สิ่งที่ควรคงไว้
Constitution ขนาดสั้น, 3 HITL gates, risk-based routing, Nit cap และ `policy.json` เป็น data

---

## 5. ลำดับที่แนะนำ

1. **รอบนี้ (คู่กับ trace + versioning):** C11 versioning, C10 trace, C9 permissions, C7 `.sdlc`, C12 PR template
2. **รอบถัดไป:** Rule registry + validator (C1, C2, C8) และแก้ C3, C4
3. **เมื่อพร้อมเปิด branch protection:** C5, C6
