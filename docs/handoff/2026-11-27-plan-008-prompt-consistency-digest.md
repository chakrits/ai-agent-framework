# Change Digest (Human-Friendly Walkthrough — ELI10)

- **Work Item / Branch:** PLAN-008 (`feat/PLAN-008-prompt-consistency`) — Framework Change ไม่มี work item
- **Date (`Asia/Bangkok`):** 2026-11-27 14:04:38 +07
- **Target Audience:** Human Maintainer / Reviewer

---

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)
- **ปัญหาก่อนหน้าคืออะไร:** คู่มือของผู้ช่วย AI แต่ละตัวบอกไม่ตรงกัน บางตัวถูกสั่งให้รอเอกสารที่งานประเภทนั้นไม่มี และงานเล็กไม่รู้ว่าต้องเก็บแผนกับผลรีวิวไว้ที่ไหน
- **รอบนี้เพิ่ม/แก้ความสามารถอะไรเข้าไป:** คู่มือของ agent บอกข้อมูลเข้าตาม route และที่ลงของแผน ผลทดสอบ และรีวิวสำหรับงาน Standard กับงาน Framework ที่ไม่มี work item ช่องว่างบางส่วนยังเหลือ (ดู "ยังค้าง")

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)
| ไฟล์ | ทำอะไรกับไฟล์นี้ | เปลี่ยนเพื่อใช้กับงานอะไร |
| :--- | :--- | :--- |
| `.agents/agents/` (reviewer, dev, qa, sa, security) | input / output ขึ้นกับ route และการมี work item; ผลรีวิวใช้ Blocker / Major / Minor; ที่ลงรีวิวของ Framework; ตาราง traceability ของ High-Risk bug fix | audit F1, F2, F4, F6, F7, F8, C1, G1, A1, A2 |
| `.agents/skills/` (tdd, council), `.agents/workflows/bug-fix-flow.md` | บันทึกผลตามที่ลงของงาน; High-Risk bug fix ต้องมี security audit และตาราง traceability | G1, F9, A1, A2 |
| `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/workflow/dynamic-routing.md` | กติกา Standard Tier และร่างก่อนมี PR, CHANGELOG เป็นไฟล์ที่ release-please สร้าง, escalation low/medium, รายการ adapter | G1, F5, F10, F11, A1, A2 |
| PR template, GitLab MR template, `review.template.md` | ช่อง plan packet ใน `## Plan Checkpoint`, หัวข้อ `## Verification` (รวม traceability) และ `## Review` (รวม Council); trace summary เฉพาะ High-Risk | G1, A1, A2 |
| `docs/operating-model/constitution.md`, `docs/contracts/README.md` *(protected)* | Gate 3 ยอมรับ `## Review` ของงาน Standard; เพิ่มแถวตำแหน่ง artifact | G1 |
| `evals/datasets/03-*.json`, `06-*.json` | ปรับ title / prompt ให้ตรงกติกาใหม่ | G1, F4, C1 |
| `.claude/`, `.agent/` | สร้างใหม่ด้วย `sync-adapters.py --sync` | mirror |
| `docs/plans/plan-008-prompt-consistency.md`, `docs/handoff/2026-11-27-prompt-audit.md` | แผนที่อนุมัติ Gate 2 และรายงานต้นทาง | หลักฐาน |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)
1. agent ดูก่อนว่างานเป็น route ไหน แล้วจึงรู้ว่าต้องมีเอกสารอะไรเป็นข้อมูลเข้า
2. ถ้าเป็นงาน Standard ที่ไม่มี work item: แผนอยู่ใน `## Plan Checkpoint`, คนเขียนโค้ดใส่ผลทดสอบใน `## Verification`, ผู้ตรวจอิสระร่าง `## Review` และโพสต์หลัง Human ยืนยัน
3. Human กด merge เป็น Gate 3 งาน Framework ที่ไม่มี work item เก็บผลรีวิวใน `docs/plans/plan-<NNN>-review.md` จำนวน gate ไม่เปลี่ยน แต่ **หลักฐาน Gate 3 ของ High-Risk bug fix เปลี่ยน:** ต้องมีตารางจับคู่ทุกพฤติกรรมใน Fast-Track Spec กับ regression test ใน `## Verification` ขาดข้อใดเป็น Blocker

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)
```bash
python3 scripts/sync-adapters.py --check
python3 evals/run_evals.py --mode contract
python3 -m unittest discover -s tests
git grep -n -E "REVIEW\.md|plan\.md|tasks\.json|work/<INT" -- AGENTS.md CLAUDE.md README.md .agents docs/workflow docs/operating-model .github .gitlab
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)
- **Specs / Review:** `docs/plans/plan-008-prompt-consistency.md` (Gate 2, A1, A2 Approved) · `docs/plans/plan-008-review.md` รอบ 1 และ 2 `changes_requested`; แก้ตาม A1 และ A2 แล้ว ผลรอบ 3 ดูในไฟล์รีวิว
- **Checks Executed:** หลังแก้ครั้งสุดท้าย: adapter parity ผ่าน, context budget ผ่าน, contract validation ผ่าน, eval contract 10/10, unit tests 252 รัน ผ่าน (ข้าม 3), `git diff --check` ผ่าน, digest validator ผ่าน
- **ยังไม่ได้ตรวจ:** พฤติกรรมจริงของ agent (ไม่ได้รัน live eval), CI บน remote, Windows
- **ต่างจากแผนรอบแรก:** ข้อความกรณี Framework Change ที่ไม่มี work item ถูกเพิ่มตอน implement และรับรองภายหลังใน Amendment A1
- **ความเสี่ยงที่ยอมรับ:** ข้อความใน PR แก้ย้อนหลังได้และไม่อยู่ใน git (รวมตาราง traceability ของ High-Risk bug fix) และไม่มี validator ตรวจตาราง
- **ยังค้าง:** G2–G12, H1–H3, High-Risk ที่ไม่มี work item ยัง export trace ไม่ได้, keyword `auth` ของ router จับคำว่า "author", validator ยังไม่มีโหมด Standard และ CI ไม่ติดตั้ง FastAPI จึงข้ามเทสต์ HTTP endpoint
