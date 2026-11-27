# PLAN-010 Wave 1 Change Digest

- **Work Item / Branch** PLAN-010 · `docs/PLAN-010-workspace-and-runtime-architecture`
- **Date** 2026-11-27 (Asia/Bangkok)
- **Target Audience** Human Maintainer and independent reviewer
- **Base Commit** `f80092e6a9a40e83de2bd06d4d6232ec4ae3deae`, after PLAN-009 closeout

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)

คนทำงานเปิด knowledge index เพื่อหา benchmark และรู้ว่าข้อมูลมาจากไหน กติกาที่มีผลกับงานยังอ้างตามลำดับใน AGENTS.md ส่วน source code ของแอปจะอยู่ใน repo ที่เลือกสำหรับ pilot ใน Wave 2

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)

| ไฟล์ | สิ่งที่เปลี่ยน |
|---|---|
| `AGENTS.md`, `README.md` | เพิ่มแหล่งค้น knowledge และตำแหน่ง product checkout |
| `docs/knowledge/README.md`, `docs/knowledge/benchmarks/claude-ai-native-sdlc-playbook-analysis.md` | เพิ่ม index และย้าย benchmark พร้อม revision ต้นทาง |
| `ROADMAP.md`, `docs/plans/framework-review-roadmap-v2.md` | เปลี่ยนลิงก์ benchmark ไปตำแหน่งใหม่ |
| `examples/project-packs/ebmc/README.md` | ระบุที่มาของ pack และเก็บ legacy prompt ที่ตำแหน่งเดิม |
| `docs/adr/README.md`, `docs/adr/ADR-001-workspace-boundaries.md` | บันทึกขอบเขตที่เสนอสำหรับ runtime pilot |
| `docs/plans/plan-010-workspace-and-runtime-architecture.md`, `docs/plans/plan-010-review.md` | เก็บแผนที่อนุมัติและหลักฐานการรีวิว |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)

1. เริ่มจาก README หรือ AGENTS.md แล้วเปิด knowledge index
2. อ่าน benchmark พร้อม path เดิมและ Git revision ถ้าต้องการตามที่มา
3. ตรวจ approved spec หรือ ADR ตาม authority order ก่อนนำข้อเสนอใน benchmark ไปใช้

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)

```bash
python3 scripts/validate-context-budget.py
python3 scripts/validate_work_item.py --digest-file docs/handoff/2026-11-27-workspace-and-runtime-digest.md
git diff --check
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)

- [PLAN-010 Gate 2](../plans/plan-010-workspace-and-runtime-architecture.md#6-gate-2-approval) ระบุการอนุมัติเฉพาะ Wave 1
- [PLAN-010 review](../plans/plan-010-review.md) เก็บผลรีวิวแผนและใช้บันทึกผลตรวจอิสระของ Wave 1
- ผู้ตรวจอิสระตรวจลิงก์ภายในที่เพิ่มหรือเปลี่ยน 55 รายการ ครบทั้ง file targets และ anchors ที่เกี่ยวข้อง ไม่มีข้อค้างหลังตรวจถ้อยคำ provenance ซ้ำ
- Adapter parity, context budget, contract validation และ Change Digest ผ่าน Contract eval ผ่าน 10/10
- Unit suite บน macOS ผ่าน 250 จาก 253 รายการ ข้าม Windows launcher 2 และ FastAPI 1 เพราะเป็น optional dependency ในเครื่อง
- ตรวจว่า legacy EBMC prompt ตรงกับฐานทุกไบต์ และ benchmark ตรงกับฐานเมื่อไม่นับ provenance ที่เพิ่ม
