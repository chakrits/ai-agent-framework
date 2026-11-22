# Change Digest (Human-Friendly Walkthrough — ELI10)

- **Work Item / Branch:** `PLAN-007` — Governance Consistency Fixes (Framework Change, High-Risk) · branch `main` (ยังไม่ commit)
- **Date (`Asia/Bangkok`):** 2026-11-22
- **Target Audience:** Human Maintainer / Reviewer
- **Plan:** [plan-007-governance-consistency.md](../plans/plan-007-governance-consistency.md)

---

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)
- **ปัญหาก่อนหน้า:** กฎของ framework ถูกเขียนใหม่ (แบ่งงานเป็น 2 ระดับ, กำหนดที่วางไฟล์, ต้องเขียนสรุปให้คนอ่าน) แต่เอกสารและโค้ดบางส่วนยังใช้กฎเก่า ทำให้ "Gate 2" แปลได้สองแบบ, CLAUDE.md สั่งให้สร้าง `plan.md` ที่ root ซึ่งกฎใหม่ห้ามไว้, และกฎบางข้อไม่มีอะไรตรวจจริง
- **รอบนี้ทำอะไร:** ทำให้ทุกที่พูดตรงกัน เลข Gate มีความหมายเดียว ย้ายไฟล์ที่วางผิดที่ เพิ่มตัวตรวจ digest (`--require-digest`) และเพิ่มที่เก็บ ADR ให้กฎที่เคยลอยอยู่มีที่อ้างอิงจริง

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)
| ไฟล์ | ทำอะไรกับไฟล์นี้ | เปลี่ยนเพื่อใช้กับงานอะไร |
| :--- | :--- | :--- |
| `docs/operating-model/constitution.md` | รวมตาราง Gate + ตารางแปลง risk เป็น Tier ไว้ที่เดียว | Phase A: เลข Gate ต้องมีความหมายเดียว |
| `docs/workflow/dynamic-routing.md`, `core-bootloader.md` | เพิ่มคอลัมน์ Tier, Plan Checkpoint, ลิงก์ไป constitution | Phase A: ให้ routing ตรงกับ AGENTS.md และ `router.py` (หลัง review แก้ constitution ให้ระบุ high-risk bug fix/config ที่ใช้ Gate 2 Fast-Track โดยไม่มี Gate 1 ตาม `router.py`) |
| `AGENTS.md`, `docs/templates/AGENTS.template.md` | ตัดตารางซ้ำ, ปรับเกณฑ์ขนาดงาน, ระบุภาษา, ผูก dry-run กับ reviewer | Phase A/C/E |
| `CLAUDE.md` | แก้กฎที่เก็บแผน | Phase B: ไม่ให้ขัดกับกฎห้ามไฟล์ที่ root |
| `plan.md` → `docs/plans/plan-005-trace-v1-1.md` (+ แก้ลิงก์ 3 จุด) | ย้ายไฟล์ | Phase B |
| `scripts/validate_work_item.py`, `tests/test_work_item_validator.py` | เพิ่ม `--require-digest` และ `--digest-file` (ตรวจ digest ที่ไม่มี work item) + เทสต์ใหม่ 11 ข้อ (ไฟล์มีทั้งหมด 20 ข้อ) เขียนเทสต์ก่อนและเห็นว่า fail ก่อนแก้โค้ดในเซสชันนี้ (ตรวจย้อนจาก diff ไม่ได้) | Phase D + แก้ตาม review I3: ตัวตรวจ ตรวจหัวข้อ 1–5 และ placeholder แต่ **ยังไม่ถูกเรียกจาก CI/hook** ผู้ review ต้องรันเอง |
| `work/INT-001/change-digest.md`, `work/index.yaml` | backfill digest | Phase D |
| `docs/adr/README.md`, `docs/templates/adr.template.md` | สร้างที่เก็บ ADR | Phase D: แทน `DECISIONS.md` ที่ไม่มีอยู่จริง |
| `docs/contracts/README.md` | แยกแถว digest ออกจาก review schema | Phase D |
| `scripts/validate-context-budget.py` | AGENTS.md budget 500 ตาม D4 ส่วนอื่นคงค่าเดิมของ HEAD (120/150/120, CLAUDE.md 80) — **ไม่ได้ลด** ร่างแรกเคยขยายแล้วถูก review ตีกลับ (I4) | Phase C |
| `.agents/agents/code-reviewer-agent.md`, `.agents/skills/council-pressure-test/SKILL.md`, `docs/templates/review.template.md` | reviewer อ่าน diff ก่อน digest, REVIEW.md ทุก Tier, บันทึกผล council | Phase E |
| `.github/pull_request_template.md`, `.gitlab/merge_request_templates/Default.md` | เพิ่ม Plan Checkpoint, คำสั่ง digest | Phase D/E |
| `.claude/`, `.agent/`, `.codex/README.md` | mirror ที่ `sync-adapters.py --sync` สร้างให้ | ต้องตรงกับ `.agents/` |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)
1. **ตรึงเลข Gate:** Gate 1 = Intent, Gate 2 = Spec, Gate 3 = Merge ตลอดทั้งระบบ งานเล็ก (Standard) แค่ข้าม Gate 1/2 แล้วใช้ "Plan Checkpoint" แทน ไม่ต้องนับเลขใหม่ จึงไม่ต้องแตะ orchestrator/RBAC/เทสต์เดิม
2. **ต้นฉบับที่เดียว:** ตาราง Gate อยู่ที่ constitution, ตารางที่วางไฟล์อยู่ที่ contracts/README ไฟล์อื่นลิงก์ไป
3. **กฎที่ตรวจได้ต้องมีตัวตรวจ:** `--require-digest` ปฏิเสธ digest ที่ไม่มี ว่าง หรือยังเป็น template

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)
```bash
export SDLC_TRACE_LEVEL=off
python3 scripts/sync-adapters.py --check
python3 scripts/validate-context-budget.py
python3 scripts/validate_work_item.py work/INT-001 --require-review --require-digest
python3 -m unittest tests.test_work_item_validator -v
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)
- **Specs / Review:** [plan-007-governance-consistency.md](../plans/plan-007-governance-consistency.md) (Gate 2: Human อนุมัติ D1–D4 ในแชทเมื่อ 2026-11-22) · [plan-007-review.md](../plans/plan-007-review.md)
- **Checks Executed (หลังแก้ครั้งล่าสุดของ Phase E):** `sync-adapters.py --check` PASSED · `validate-context-budget.py` PASSED · `validate-contracts.py --check-defaults` PASSED · `evals --mode contract` 10/10 · `validate_work_item.py work/INT-001 --require-review --require-digest` PASSED · `unittest discover` OK (skipped=3) · `git diff --check` clean
- **ยังไม่ได้ตรวจ:** Windows/Docker, CI ของ GitHub/GitLab จริง (รันเฉพาะบนเครื่อง macOS นี้), ตัว `orchestrator` ไม่ได้ถูกแก้ จึงไม่มีเทสต์ใหม่ฝั่งนั้น
- **ข้อควรรู้:** `spec.md` ของ INT-001 ยังระบุ CLI แค่ `[--require-review]` ทั้งที่ตอนนี้มี `--require-digest` เพิ่ม (ไม่ได้แก้ spec ที่อนุมัติแล้ว)
