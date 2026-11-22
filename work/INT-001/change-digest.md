# Change Digest (Human-Friendly Walkthrough — ELI10)

- **Work Item / Branch:** `INT-001` (pilot; digest backfilled on 2026-11-22 because the digest rule was introduced after this work item was implemented)
- **Date (`Asia/Bangkok`):** 2026-11-22
- **Target Audience:** Human Maintainer / Reviewer

---

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)
- **ปัญหาก่อนหน้า:** เอกสารของงานหนึ่งชิ้น (ความต้องการ, สเปก, รายงานทดสอบ, รายการงาน) ต้องตรงกันทุกจุด แต่ตัวตรวจเดิมตรวจทีละไฟล์ จึงไม่รู้ว่ามีข้อไหนหายไปหรือโยงผิดข้อ จนมีคนมาอ่านเอง
- **รอบนี้เพิ่มอะไร:** คำสั่งเดียว `validate_work_item.py` ที่เทียบรหัสข้ามไฟล์ (`URD` → `FS` → `TC` → `TASK`) แล้วบอกเลยว่าอะไรขาดหรือโยงผิด

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)
| ไฟล์ | ทำอะไรกับไฟล์นี้ | เปลี่ยนเพื่อใช้กับงานอะไร |
| :--- | :--- | :--- |
| `scripts/validate_work_item.py` | เพิ่มตัวตรวจข้ามไฟล์ | ตรวจความครบและการโยงรหัสของ work item |
| `tests/test_work_item_validator.py` | เพิ่มเทสต์ | พิสูจน์ว่าตัวตรวจจับกรณีรหัสหาย/โยงผิดได้จริง |
| `work/INT-001/*` | เพิ่มชุดเอกสารตัวอย่าง | เป็น pilot ที่รันตัวตรวจกับงานจริง |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)
1. อ่าน `intent.md`, `spec.md`, `test-report.md`, `tasks.json` (และ `REVIEW.md` ถ้าสั่ง `--require-review`)
2. ดึงรหัส `URD-xxx` / `FS-xxx` / `TC-xxx` แล้วเทียบกันว่าทุกข้อมีปลายทางรองรับ
3. ถ้าขาดหรือโยงผิด พิมพ์รายการข้อผิดพลาดและจบด้วย exit `1`; ถ้าครบ จบด้วย exit `0`

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)
```bash
python3 scripts/validate_work_item.py work/INT-001 --require-review
python3 -m unittest tests/test_work_item_validator.py -v
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)
- **Specs / Review:** `work/INT-001/intent.md`, `spec.md`, `REVIEW.md` (verdict ใน `REVIEW.md` ยังเป็น `changes_requested`; สถานะใน `work/index.yaml` คือ `pending_gate_3`)
- **Checks Executed:** ดูผลที่รันหลังแก้ล่าสุดใน PR (digest นี้ backfill ภายหลัง จึงไม่คัดลอกตัวเลขเก่ามาซ้ำ)
