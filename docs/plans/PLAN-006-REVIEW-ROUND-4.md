# PLAN-006 Independent Re-review · รอบ 4

**Verdict `changes_requested`** · **วันที่ 2026-11-21**

ยืนยัน snapshot ตรงกับที่ส่งมา HEAD `7b723bc8966089d9be16883f30b8af62ab4a49f7` และ SHA-256 ของ `git diff --binary HEAD` เท่ากับ `39f139c93a684870e5251382a1794ac3760eaa9afe07fcd7a839bdec904cce49` ขอบเขตมีไฟล์ tracked เปลี่ยน 22 ไฟล์ รายงานรอบก่อนที่ยัง untracked อยู่นอก snapshot [Verdict รอบ 3](PLAN-006-REVIEW-ROUND-3.md)

## สิ่งที่ยังต้องแก้

| ระดับ | WS | ข้อค้นพบและเกณฑ์รับงาน |
|---|---|---|
| **Blocker** | E · Pilot PR/CI | ยังขาด PR และผล CI ที่ผูกกับ pilot revision เดียวกัน ค้น GitHub ด้วย `INT-001` ไม่พบ PR และการค้น CI แบบ PR-triggered สำหรับ HEAD นี้ไม่พบ run แนบ PR head SHA และ CI run URLs ก่อนส่งให้ Maintainer พิจารณา Gate 3 [REVIEW.md:10](work/INT-001/REVIEW.md#L10) · [PLAN-006:142](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md#L142) |
| **Important** | E · Traceability | ปิดกรณีไม่มีหรือขาดคู่ในตาราง spec แล้ว แต่ QA validator รวม TC ตาม FS และยอมให้แถว `URD–FS` ที่ระบุ Covered มี TC ว่าง เมื่อทดสอบด้วยสำเนาที่เพิ่ม URD อีกหนึ่งรายการให้ใช้ FS เดียวกันโดยไม่มี TC ของแถวนั้น ทั้ง work-item validator และ contract validator ยังคืน exit `0` ให้บังคับ TC อย่างน้อยหนึ่งรายการสำหรับแต่ละคู่ที่ Covered และเพิ่ม regression case นี้ [validate_work_item.py:76](scripts/validate_work_item.py#L76) · [validate_work_item.py:145](scripts/validate_work_item.py#L145) |
| **Important** | D · Scope | CI เปิด live เฉพาะ Claude ซึ่งปิด Blocker เรื่องการจำกัดค่าใช้จ่ายของ Codex ใน CI ได้ ส่วน D-01 ยังรวม Antigravity และเอกสารระบุชัดว่าการลด scope รอ Maintainer อนุมัติ บันทึกการตัดสินใจของ Maintainer หรือแนบผล live Antigravity ที่ยืนยัน sandbox และ budget cap [evals-live.yml:6](.github/workflows/evals-live.yml#L6) · [PLAN-006:85](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md#L85) |

**Nit 0 รายการ**

## คำชี้แจงเรื่อง Gate 1–2

ผู้ใช้แจ้งในแชทนี้เมื่อ 2026-11-21 ว่า Human Gate 1 และ Gate 2 ของ `INT-001` ได้รับอนุมัติผ่านแชทก่อนเริ่ม implementation และไม่ได้บันทึกหลักฐานแยกไว้ รายงานนี้บันทึกคำชี้แจงย้อนหลัง โดยยังไม่มีข้อความอนุมัติต้นฉบับให้ตรวจเวลา ผู้อนุมัติ หรือ revision ของ intent/spec แยกจากคำชี้แจง วันที่ข้างต้นคือวันที่รับคำชี้แจง

## ปิดจากรอบสาม

- **WS-D · CI budget** Codex ถูกถอดออกจาก workflow และ help ของ local CLI ระบุว่าคำสั่งที่ไม่มี budget ในตัวจะตรวจเฉพาะค่าใช้จ่ายที่รายงานหลังรัน ไม่มีการอ้างว่าบังคับเพดาน local Codex ระหว่างรัน [evals-live.yml:47](.github/workflows/evals-live.yml#L47) · [run_evals.py:198](evals/run_evals.py#L198)
- **WS-D · Oracle paths** Grader อ่านรายการไฟล์แบบ NUL-delimited และปิด rename detection เพื่อให้เห็นทั้ง path เดิมและใหม่ เทสต์ Unicode และ rename ผ่าน [run_evals.py:91](evals/run_evals.py#L91) · [test_eval_runner.py:21](tests/test_eval_runner.py#L21)
- **WS-C · File-backed token registry** คู่มือมีคำสั่ง bind mount แบบ read-only และระบุสิทธิ์อ่านสำหรับ UID 1000 ยืนยันแยกด้วย Docker build จาก snapshot ที่ตรวจและ container ชั่วคราว ผล healthcheck เป็น `healthy`, UID `1000`, `/health` คืน `200`, token ขาดหรือผิดคืน `401` และ token จากไฟล์คืน `404` เมื่อเรียก run ที่ไม่มีอยู่ [orchestrator/README.md:43](orchestrator/README.md#L43)
- **WS-E · Canonical URD–FS mapping** เทสต์ยืนยันว่า validator คืน exit `1` เมื่อขาด mapping ทั้งตารางหรือขาดบาง URD ส่วนช่องว่างของ TC ต่อคู่แสดงไว้ในตารางด้านบน [test_work_item_validator.py:32](tests/test_work_item_validator.py#L32)

## ผลรันจริง

- `git diff --check`, `git diff --cached --check`, `git diff --check HEAD` และ `git diff --check c78aed9..HEAD` ผ่าน
- รันครบทั้ง 7 คำสั่งเดิม Adapter parity, context budget, contract validation, work-item validation และ doctor ผ่าน Contract evals ผ่าน **10/10** ส่วน unittest ผ่าน **231 จาก 234** ข้าม Windows launcher สองเทสต์และ FastAPI หนึ่งเทสต์
- ชุด Orchestrator API ผ่าน **7/7** เมื่อรันแยกจากสำเนา snapshot พร้อม FastAPI และ httpx ใน environment ที่มี dependencies อยู่แล้ว
- `docker compose config --quiet` ผ่านทั้ง profile `orchestrator` และ `monitoring` ส่วน Docker build และ file-backed smoke ผ่านบน OrbStack
- ทดสอบ Alloy → Loki ใน Compose project ชั่วคราวจาก snapshot นี้ ส่ง synthetic trace ผ่าน Alloy และ query event เดียวกันจาก Loki ได้ งานนี้ครอบคลุมเฉพาะ Alloy และ Loki
- ตรวจ SHA-256 ของ QA test report ตรงกับ baseline `7b723bc` และไม่มี diff การ export ซ้ำได้ตัวเลขและคำสั่งตรงกับไฟล์สรุป **1 session, 8 events, 3 Bash tool calls** จากการตรวจผลบน `main`
- สแกนไฟล์ใน tracked diff ครบ 22 ไฟล์ ไม่พบ credential ตามรูปแบบที่ตัวสแกนตรวจได้

## หลักฐานที่ยังขาด

- ยังไม่มีผลรันอิสระของ live agent evals จาก harness จริง หรือหลักฐานการ reload hook ใน Antigravity session ใหม่
- ยังขาด PR และ CI matrix สำหรับ pilot revision ตามแผน ให้ Maintainer ลงนาม Gate 3 หลังตรวจหลักฐานและผ่าน independent re-review
