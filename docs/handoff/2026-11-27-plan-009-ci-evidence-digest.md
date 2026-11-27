# Change Digest: PLAN-009 Trace Export Path Scrub และ CI Evidence

- **Work Item / Branch:** PLAN-009 (`feat/PLAN-009-ci-evidence-and-trace-scrub`)
- **Date (`Asia/Bangkok`):** `2026-11-27 17:39:33 +07` (อัปเดตล่าสุด หลังแก้ตามรีวิว)
- **Target Audience:** Human Maintainer / Reviewer

---

## 1. สรุปสั้นๆ แบบเด็ก 10 ขวบเข้าใจได้ (What & Why)
- **ปัญหาก่อนหน้าคืออะไร:** รายการคำสั่งในไฟล์สรุป trace อาจหลุด path บางส่วน เพราะโปรแกรมตัดข้อความให้สั้นก่อนแล้วค่อยแทน path ส่วน CI ไม่ได้ตรวจ digest และข้าม FastAPI test
- **รอบนี้เพิ่ม/แก้ความสามารถอะไรเข้าไป:** ลบ path ก่อนตัด (Human apply และ commit ใน `eadcc98`), CI ตรวจรูปแบบ digest และรัน FastAPI endpoint test
- **ยังไม่ได้แก้:** ไฟล์ export **ยังอาจมีชื่อผู้ใช้หรือชื่อโฟลเดอร์** ในรูปอื่น (เช่น `-Users-<user>-...`, Git Bash / WSL path, path ที่ escape ช่องว่าง) และการตัดตอนบันทึก trace (รีวิว M1 / m2) ต้องอ่านไฟล์ก่อน commit

## 2. รายการไฟล์ที่แก้/สร้าง และเหตุผล (Files Changed)
| ไฟล์ | ทำอะไรกับไฟล์นี้ | เปลี่ยนเพื่อใช้กับงานอะไร |
| :--- | :--- | :--- |
| `scripts/sdlc_guard/trace_cli.py` (protected, Human commit `eadcc98`) | scrub บรรทัดคำสั่งก่อนตัด 100 ตัวอักษร | WS-A (G11) |
| `tests/test_trace.py` | เพิ่ม regression test กรณีจุดตัดตกกลาง path | WS-A |
| `.github/workflows/validate.yml` | เพิ่ม step ตรวจ digest, ติดตั้ง dependency และรัน FastAPI test | WS-B, WS-C |
| `README.md` | แก้ข้อความว่า CI ตรวจ digest อะไรบ้าง | Amendment A1 |
| `docs/plans/plan-009-review.md` | ผลรีวิวอิสระที่ `eadcc98` | Gate 3 |
| `docs/plans/plan-009-ci-evidence-and-trace-scrub.md` | แผนและบันทึก Gate 2 | ทุก WS |
| `docs/plans/plan-005-trace-v1-1.md`, `plan-006-agy-hooks-fastapi-pilot-evals-docker.md`, `trace-versioning-plan.md` | แก้สถานะแผนที่ล้าสมัยตามหลักฐาน Git / GitHub | เก็บงานค้าง |

## 3. แนวคิดและขั้นตอนการทำงานเบื้องหลัง (How It Works)
1. ตอน export โปรแกรมหยิบบรรทัดแรกของแต่ละคำสั่ง แทน path ของ repo และ home ด้วย `<repo>` และ `~` แล้วจึงตัดให้เหลือ 100 ตัวอักษร
2. CI วนตรวจ digest ทุกไฟล์ใน `docs/handoff/*-digest.md` และ `work/INT-*/change-digest.md` ไฟล์ที่ยังมี placeholder ทำให้ job fail แต่ CI **ไม่ได้บังคับ** ว่า PR ต้องมี digest
3. หลัง step เดิมทั้งหมด CI ติดตั้ง FastAPI และ `httpx` แล้วรัน endpoint test job จะ fail ถ้า import ไม่ได้ หรือ test ถูกถอด เปลี่ยนชื่อ หรือถูกข้าม

## 4. ลองใช้งาน / ทดสอบเองได้อย่างไร (Try It Yourself)
```bash
python3 -m unittest tests.test_trace -k cut_by
```

## 5. หลักฐานอ้างอิงที่ตรวจผ่านแล้ว (Verified Evidence)
- **Specs / Review:** [PLAN-009](../plans/plan-009-ci-evidence-and-trace-scrub.md) · [รีวิวอิสระ](../plans/plan-009-review.md) ที่ `eadcc98`: `changes_requested` (B1 ไม่มีหลักฐาน CI, M1 path รูปอื่น, Minor 7) การแก้ตาม Amendment A1 ยังไม่ได้รีวิวซ้ำ
- **Commits:** `db79c77` (แผน), `89cd7c4` (CI), `eadcc98` (G11)
- **กับโค้ดก่อนแก้ (`3f082dc`):** test ที่ปรับใน A1 fail ทั้งกรณี repo และ home
- **บน HEAD `eadcc98` ในเครื่อง:** unit test 253 ตัวผ่าน (skipped=3), contract eval 10/10, adapter sync, context budget, contracts และ `git diff --check main..HEAD` ผ่าน
- **หลังแก้ A1 (บนสำเนาของ working tree):** test ใหม่ผ่าน, unit test ทั้งชุดผ่าน (skipped=3), contract eval 10/10, adapter sync, context budget และ contracts ผ่าน
- **คำสั่ง FastAPI ใหม่:** ไม่มี dependency และกรณี class ถูกถอด คืน exit 1 ส่วนกรณีผ่านจริงยังไม่ได้ทดสอบ
- **Digest step:** รันการตรวจแบบเดียวกับ step ในเครื่องผ่าน 4 ไฟล์ (รวมไฟล์นี้) และ loop เดียวกันกับ template ที่ยังไม่กรอกคืน exit 1
- **ยังไม่ยืนยัน:** การติดตั้ง dependency, FastAPI endpoint test ที่ผ่านจริง และผล CI 6 job ของ PR
- **ตรวจ `work/INT-001/trace-summary.md`:** ค้นหาชื่อผู้ใช้ โฟลเดอร์ `WorkSpace` / `GitHub Code` และ path ที่ขึ้นต้น `/U` ไม่พบ
