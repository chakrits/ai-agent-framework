# PLAN-006 Independent Review Verdict

**Verdict `changes_requested`** · **วันที่ 2026-11-21**

ส่งกลับให้ Developer แก้ WS-A ถึง WS-E ก่อนขอ review รอบใหม่ จุดที่ต้องจัดการก่อนคือสิทธิ์อนุมัติ HITL, ความปลอดภัยของ live eval CI, การเข้าถึง trace ใน monitoring stack และหลักฐาน E2E ของ `INT-001`

ขอบเขตที่ตรวจคือ working tree บน `main` เทียบกับ `c78aed92ad498b7c2ebc415d60a18aac485a04a1` ณ รอบตรวจ พบไฟล์แก้ไข 17 ไฟล์และไฟล์ใหม่ 31 ไฟล์ ไม่มี staged changes ส่วน `git diff --check` ผ่าน การสแกนไม่พบ credential ตามรูปแบบที่ตรวจได้และไม่มี `.sdlc/traces/` ในรายการเปลี่ยนแปลง [PLAN-006](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md)

## รายการแก้ไขและเกณฑ์รับงาน

| ระดับ | Workstream | สิ่งที่ต้องแก้ | เกณฑ์รับงานรอบถัดไป |
|---|---|---|---|
| **Blocker** | B · Security | `/approve` ใช้ `approver_id` จาก request โดยไม่มีการยืนยันตัวตนหรือสิทธิ์ ให้ใช้ตัวตนที่ระบบยืนยันแล้วและตรวจสิทธิ์ตาม run และ Gate [main.py:96](orchestrator/api/main.py#L96) | ไม่มีตัวตนได้ `401` ผู้ใช้ที่ไม่มีสิทธิ์ได้ `403` และ audit log บันทึกผู้อนุมัติจริงพร้อม timestamp |
| **Blocker** | D · Security | `workflow_dispatch.limit` ถูกแทนค่าลงใน shell script โดยตรงใน step ที่ถือ API keys ให้ส่งค่าผ่าน environment variable ตรวจช่วงของจำนวนเคส และส่งเฉพาะ credential ของ harness ที่เลือก [evals-live.yml:34](.github/workflows/evals-live.yml#L34) | Input ผิดรูปแบบหรือเกินเพดานหยุดงานก่อนเรียก CLI และ workflow ติดตั้ง CLI ที่เลือกได้บน runner ใหม่ |
| **Blocker** | C · Security | ปิด anonymous Admin ใน Grafana และจำกัดการเข้าถึง Grafana กับ Loki ก่อนส่ง trace จริงเข้า stack [docker-compose.yml:12](docker-compose.yml#L12) | ผู้ใช้ที่ไม่ได้รับอนุญาตเปิด dashboard หรือ query trace ไม่ได้ และ Alloy ส่ง synthetic trace เข้า Loki ได้ |
| **Blocker** | E · Spec Compliance | เติมหลักฐาน E2E ของ `INT-001` ให้ตรวจย้อนกลับได้ รอบนี้ export ได้ `0 events` และ Gate 3 ยัง `Pending` [trace-summary.md:3](work/INT-001/trace-summary.md#L3) · [REVIEW.md:35](work/INT-001/REVIEW.md#L35) | แนบหลักฐาน Gate 1 และ Gate 2, ลิงก์ branch/PR และ CI, trace export ที่มี event ของ `INT-001` และส่งให้ Maintainer ลงนาม Gate 3 หลังผ่าน re-review |
| **Important** | A · Spec Compliance | `SessionStart` คืน `injectSteps` และเทสต์ยืนยันพฤติกรรมนี้ แต่ PLAN-006 กำหนด `{}` ให้ปรับ implementation และ assertion ตาม contract หรือขออนุมัติเปลี่ยนแผนพร้อมหลักฐานจาก Antigravity จริง [doctor.py:141](scripts/sdlc_guard/doctor.py#L141) · [test_agy_hooks.py:127](tests/test_agy_hooks.py#L127) | ตรวจ stdout ของทั้งสี่ events ใน session ใหม่ และรัน regression ของ Claude กับ Codex |
| **Important** | B · Bugs | ผูก approval กับ Gate ที่ผู้ใช้ตั้งใจอนุมัติ และควบคุมช่วง load → approve → save ให้ปลอดภัยเมื่อ retry หรือส่งพร้อมกัน [handlers.py:94](orchestrator/api/handlers.py#L94) | ส่ง approval เดิมซ้ำแล้ว Gate ถัดไปไม่ถูกอนุมัติ และคำขอที่ส่งพร้อมกันไม่ทำให้ state หรือ audit log ขัดกัน |
| **Important** | B · Spec Compliance | ให้ threshold อ่านจาก config ตามแผน ปัจจุบัน YAML กำหนด action, mode และ routes แต่จุดตัด sigma ยังอยู่ใน Python [bands.py:93](orchestrator/telemetry/bands.py#L93) | เปลี่ยน threshold ใน fixture แล้วผลจัด tier เปลี่ยนตาม |
| **Important** | C · Security / Spec Compliance | ตรวจว่า worktree ปลายทางอยู่ใต้ repo หลัง resolve path, resolve `--base` เป็น commit ก่อนส่งให้ Git, ตรวจ hook readiness และเพิ่ม profile `orchestrator` ตาม C-03 [worktree.py:39](scripts/worktree.py#L39) · [docker-compose.yml:1](docker-compose.yml#L1) | มีเทสต์ปฏิเสธปลายทางนอก repo และ base ที่ไม่ถูกต้อง พร้อมผลตรวจ service ตาม profile |
| **Important** | D · Spec Compliance | เพิ่ม `--max-budget`, บังคับใช้ sandbox ที่ harness รองรับ และให้ grader ตรวจ Git diff ของ fixture ร่วมกับผลลัพธ์จาก agent [run_evals.py:80](evals/run_evals.py#L80) | Live run จริงเก็บ trace ใน temp, เคารพ budget และ timeout และ fixture ที่ QA oracle ถูกแก้ต้องได้ `FAIL` |
| **Important** | E · Bugs / Spec Compliance | เติม `TC-EP-001` ให้ `TASK-001` และตรวจความสัมพันธ์ `URD → FS → TC → TASK` ตอนนี้ลบ `test_refs` ทั้งหมดจากสำเนาแล้ว validator ยังคืน `PASS` [test-report.md:79](work/INT-001/test-report.md#L79) · [tasks.json:7](work/INT-001/tasks.json#L7) · [validate_work_item.py:31](scripts/validate_work_item.py#L31) | ชุดข้อมูลครบลิงก์ผ่าน ส่วน TC ที่หายหรืออ้างผิด FS ต้องคืน exit `1` พร้อมระบุ ID และแนบ QA baseline สำหรับตรวจ oracle integrity |

**Nit 0 รายการ**

## ยืนยันแล้วจากผลรันจริง

- รันครบทั้ง 7 คำสั่งตามขอบเขต review ได้แก่ adapter parity, context budget, contract validation, work-item validation, contract evals, doctor และ unittest ผล contract evals ผ่าน **10/10** ส่วน unittest ผ่าน **220 จาก 223** บน macOS / Python 3.14.4 ข้าม Windows launcher สองเทสต์และ FastAPI หนึ่งเทสต์
- รันชุด API แยกบนสำเนาชั่วคราวพร้อม dependencies ผ่าน **4/4** ตรวจ HTTP `400`, `404` และ `422` เพิ่มด้วย TestClient และยืนยันผ่าน Uvicorn บน loopback ว่า `/health` และ `/docs` คืน `200`, auto-approve คืน `403` และ state พร้อม timestamp โหลดกลับมาเดินจาก Gate 2 ไป Gate 3 ได้หลัง restart
- ทดสอบ Antigravity hook entrypoint ด้วย camelCase payload ผล allow/deny ตรงตามที่คาด `PostToolUse` และ `Stop` คืน `{}` ส่วน `SessionStart` คืน `injectSteps` ตัวอย่าง trace ของ Antigravity และ Orchestrator ผ่าน `trace.validate_event()`
- สร้างและ cleanup worktree จริงใน Git repo ชั่วคราว `doctor --strict` ผ่านเมื่อ repo ตั้ง hooks ไว้ และ trace อ่าน `INT-001` จากชื่อ branch ได้ ผล `docker compose config` ผ่าน

## หลักฐานที่ยังขาด

- **Docker build, non-root runtime, container health และ Alloy → Loki ingestion** ยังไม่ยืนยันเพราะ OrbStack Docker daemon ไม่มี socket ให้เชื่อมต่อ
- **Antigravity session reload และ live eval ผ่าน harness จริง** รอบนี้ทดสอบถึง hook entrypoint และ subprocess จำลอง
- **QA oracle provenance และ CI matrix** diff ของ `test_phase4_orchestrator.py` คง assertions เดิมและเพิ่ม opt-in สำหรับ dry run แต่ไฟล์ QA ของ pilot ยังไม่มี Git baseline ให้ยืนยันว่า oracle ถูกตรึงก่อน implementation และยังไม่มีหลักฐาน CI ครบสาม OS ตามแผน

แนบ commit SHA, ผลรัน regression ของแต่ละ Blocker และหลักฐานที่ยังขาดตอนส่งกลับมา review เพื่อให้ตรวจซ้ำบน revision เดียวกันได้
