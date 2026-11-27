# Change Digest: PLAN-011 Import Isolation ของ Python Entry Points

- **Work Item / Branch:** PLAN-011 (`fix/PLAN-011-import-isolation`)
- **Date (`Asia/Bangkok`):** `2026-11-27 19:48:42 +07`
- **Target Audience:** Human Maintainer / Reviewer

---

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)
- **ปัญหาก่อนหน้าคืออะไร:** โปรแกรมตรวจความปลอดภัยของ repo อาจหยิบโค้ดผิดตัวมารันจากโฟลเดอร์ที่มันอยู่ ทำให้การตรวจไม่ทำงาน (SEC-B1)
- **รอบนี้เพิ่ม/แก้ความสามารถอะไรเข้าไป:** โปรแกรมหยิบโค้ดของเราตามที่อยู่ไฟล์ที่ระบุชัด และไม่ค้นหาโค้ดจากโฟลเดอร์ตัวเองตามชื่ออีก นอกจากนี้ ถ้าโค้ดตัวตรวจโหลดไม่ได้ จะบล็อกไว้ก่อนแทนที่จะปล่อยผ่าน
- **ยังไม่ได้แก้:** agent ยังสร้าง script ใหม่แล้วรันได้โดยไม่ถูกถาม (Human รับความเสี่ยงไว้ที่ Gate 2 เป็น follow-up) และการคุ้มครองไฟล์ตาม SEC-M4

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)
| ไฟล์ | ทำอะไรกับไฟล์นี้ | เปลี่ยนเพื่อใช้กับงานอะไร |
| :--- | :--- | :--- |
| `scripts/sdlc_hook.py`, `scripts/bin/sdlc-hook`, `scripts/bin/sdlc-hook.cmd`, `scripts/sdlc_guard/precommit.py` (protected) | แยกเส้นทาง import และรัน Python ด้วย `-I` | guard และ pre-commit |
| `scripts/validate-contracts.py`, `validate_work_item.py`, `validate-context-budget.py`, `sync-adapters.py` | แยกเส้นทาง import | validator ที่ใช้ใน CI และ pre-commit |
| `scripts/doctor.py`, `precommit.py`, `setup.py`, `sdlc_trace.py`, `worktree.py` | แยกเส้นทาง import | คำสั่งที่ผู้ใช้และ agent เรียก |
| `evals/run_evals.py` | แยกเส้นทาง import และโหลด validator จาก source | eval gate |
| `tests/test_import_isolation.py` | test ใหม่ 6 ตัว | กันการถอยกลับ และบังคับให้ entry script ใหม่มีการป้องกัน |
| `docs/plans/plan-011-import-isolation.md` | แผนและบันทึก Gate 2 | governance |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)
1. บรรทัดแรกของแต่ละโปรแกรมเอาโฟลเดอร์ของตัวเองออกจากรายการค้นหาโค้ด
2. โค้ดของ framework ที่ต้องใช้ถูกโหลดตาม path ที่ระบุ ไฟล์เดี่ยวถูกอ่านจากต้นฉบับทุกครั้ง ไม่ใช้ cache
3. ตัวเรียก (launcher) และ pre-commit เปิด Python ในโหมดแยกตัว (`-I`)
4. ถ้าโหลดโค้ดตัวตรวจไม่สำเร็จ คำสั่งตรวจจะจบด้วย exit 2 (บล็อก) ส่วนการบันทึก trace และตอนเริ่ม session ไม่บล็อก

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)
```bash
python3 -m unittest tests.test_import_isolation -v
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)
- **Specs / Review:** [PLAN-011](../plans/plan-011-import-isolation.md) · การรีวิวอิสระยังไม่ได้ทำ
- **บนโค้ดก่อนแก้ (`f80092e`):** test ใหม่ fail
- **หลังแก้ บนสำเนาชั่วคราวที่ apply patch แล้ว (macOS):** unit test 259 ตัวผ่าน (skipped=3) บน Python 3.14.10 และ 3.11.18, contract eval 10/10, validator, adapter sync, context budget และ `git diff --check` ผ่าน
- **ยังไม่ยืนยัน:** Windows, Linux, Python 3.10/3.12 (รอ CI)
