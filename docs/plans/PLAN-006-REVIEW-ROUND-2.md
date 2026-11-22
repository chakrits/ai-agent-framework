# PLAN-006 Independent Re-review

**Verdict `changes_requested`** · **วันที่ 2026-11-21**

ตรวจ commit `7b723bc8966089d9be16883f30b8af62ab4a49f7` เทียบกับ parent `c78aed92ad498b7c2ebc415d60a18aac485a04a1` และ [verdict รอบแรก](PLAN-006-REVIEW-VERDICT.md) การยืนยันตัวตนของผู้อนุมัติ การป้องกัน approval retry ในเส้นทางปกติ และความปลอดภัยของ Compose ดีขึ้นแล้ว ยังขาดการตรวจสิทธิ์ระดับ run, หลักฐาน pilot และการทำงานของ live eval ให้ครบตามแผน

## สิ่งที่ต้องแก้ก่อนส่งกลับ

| ระดับ | WS | ข้อค้นพบและเกณฑ์รับงาน |
|---|---|---|
| **Blocker** | B · Security | HTTP ใช้ Bearer token และบันทึก actor จาก server แล้ว แต่การอนุมัติตรวจเพียง role ของ Gate ไม่มีขอบเขตสิทธิ์ระดับ run และ GET run รับ token ใดก็ได้ที่ registry รู้จัก เพิ่ม owner หรือขอบเขตทีมให้ run แล้วบังคับสิทธิ์กับทั้ง GET และ approve ยืนยันว่า actor ใน role เดียวกันแต่คนละขอบเขตเข้าถึงไม่ได้ อีกทางคือระบุและขออนุมัติโมเดล single-tenant ที่อนุญาต role ให้ทำงานกับทุก run อย่างชัดเจน [main.py:106](orchestrator/api/main.py#L106) · [handlers.py:107](orchestrator/api/handlers.py#L107) · [auth.py:73](orchestrator/api/auth.py#L73) |
| **Blocker** | E · Spec Compliance | Trace summary ใน commit มี 3 events แต่ tool calls เป็น 0 และแหล่ง trace ใน checkout ที่ตรวจได้คืน 0 events เอกสาร intent/spec และ QA oracle เข้าประวัติ Git ใน commit เดียวกับ implementation จึงยังยืนยันลำดับ Gate และ QA baseline ไม่ได้ แนบ approval ของ Gate 1–2 ที่ตรวจย้อนกลับได้, หลักฐาน branch/PR และ CI, baseline ของ QA และ trace ที่แสดงขั้นตอน pilot จริง ให้ Maintainer พิจารณา Gate 3 หลัง re-review [trace-summary.md:3](work/INT-001/trace-summary.md#L3) · [REVIEW.md:23](work/INT-001/REVIEW.md#L23) · [PLAN-006:136](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md#L136) |
| **Important** | A · Spec Compliance | `SessionStart` ยังคืน `injectSteps` และเทสต์ยังคาดค่านี้ ขณะที่ PLAN-006 กำหนด `{}` ปรับ implementation กับเทสต์ให้ตรงแผน หรือบันทึกการเปลี่ยน contract ที่ได้รับอนุมัติพร้อมผลทดสอบจาก Antigravity session จริง [doctor.py:143](scripts/sdlc_guard/doctor.py#L143) · [test_agy_hooks.py:127](tests/test_agy_hooks.py#L127) |
| **Important** | B · Bugs | `expected_gate` และ lock ป้องกัน duplicate approval ในผลรันปกติ แต่ lock เดินต่อเมื่อ acquire ล้มเหลว การอ่านและอัปเดต state ต้องหยุดเมื่อถือ lock ไม่ได้ เพิ่ม regression case ที่ยืนยันว่า failure ไม่เขียน approval หรือ telemetry [state_store.py:30](orchestrator/core/state_store.py#L30) |
| **Important** | C · Deployability | Compose ไม่ส่ง token registry ให้ Orchestrator จึงตั้งค่า authenticated API ผ่าน config ที่ส่งมาด้วยไม่ได้ และ profile `orchestrator` อย่างเดียวก็ยังติดการบังคับกรอก `GRAFANA_ADMIN_PASSWORD` ยืนยันจาก `docker compose --profile orchestrator config --quiet` ให้แยกข้อกำหนดของ monitoring และรองรับ registry ผ่าน secret/config ที่ระบุในคู่มือ [docker-compose.yml:2](docker-compose.yml#L2) · [docker-compose.yml:30](docker-compose.yml#L30) · [auth.py:38](orchestrator/api/auth.py#L38) |
| **Important** | C · Path containment | Helper resolve `.worktrees` ก่อนใช้เป็นขอบเขต ดังนั้นถ้า directory นี้ชี้ออกนอก repo ขอบเขตก็ย้ายตาม ตรวจ root ที่ resolve แล้วเทียบกับ checkout ก่อนสร้างหรือ cleanup และเพิ่ม regression case สำหรับตำแหน่ง parent นี้ [worktree.py:39](scripts/worktree.py#L39) |
| **Important** | D · Live CI / Budget | ช่องส่ง workflow input เข้า shell โดยตรงถูกแก้แล้ว แต่ job Antigravity ยังไม่มีขั้นติดตั้ง `agy` มีเพียง Claude ที่รับ budget ผ่าน flag ของ CLI ส่วน Codex และ Antigravity รับแค่ environment variable ของโครงการ โดย runner ยังไม่บังคับเพดาน Antigravity ไม่มี sandbox argument จาก runner ให้ติดตั้ง harness และยืนยัน budget กับขอบเขตการทำงานจริง หรือปิดตัวเลือกที่ยังรับประกันเงื่อนไขไม่ได้ [evals-live.yml:89](.github/workflows/evals-live.yml#L89) · [run_evals.py:31](evals/run_evals.py#L31) · [run_evals.py:137](evals/run_evals.py#L137) |
| **Important** | D · Oracle integrity | เทสต์ใหม่จับการแก้ oracle ที่ยังค้างใน working tree ได้ แต่ grader อาศัย `git status` และละเลย exit code ให้เทียบกับ baseline commit ที่ runner เก็บไว้ก่อนเรียก harness และคืน `FAIL` เมื่ออ่านสถานะ Git ไม่สำเร็จ [run_evals.py:73](evals/run_evals.py#L73) · [test_eval_runner.py:69](tests/test_eval_runner.py#L69) |
| **Important** | E · Traceability | เพิ่ม `TC-EP-001` และตรวจ `FS → TC → TASK` แล้ว แต่ parser ยังทิ้งคอลัมน์ URD ทดสอบกับสำเนาชั่วคราวโดยเปลี่ยนแถว `FS-001` ให้ชี้ `URD-002` ผิดจาก spec แล้ว validator คืนผลไร้ error ให้ตรวจคู่ `URD ↔ FS` ระหว่าง spec และ QA matrix โดยตรง [validate_work_item.py:32](scripts/validate_work_item.py#L32) · [tasks.json:11](work/INT-001/tasks.json#L11) |

**Nit 0 รายการ**

## ยืนยันแล้วจากผลรันจริง

- Adapter parity, context budget, contract validation, work-item validation, doctor และ contract evals **10/10** ผ่าน ชุด unittest บน macOS / Python 3.14.4 ผ่าน **225 จาก 228** ข้าม Windows launcher สองเทสต์และ FastAPI หนึ่งเทสต์
- ชุด Orchestrator API บนสำเนาจาก `git archive` พร้อม dependencies ผ่าน **6/6** ครอบคลุม HTTP auth และ Gate RBAC, duplicate approval, คำขอพร้อมกัน, การโหลด state ผ่าน service instance ใหม่ และ threshold จาก YAML
- Compose config ผ่านเมื่อใส่ค่า Grafana password สำหรับทดสอบ จาก config ยืนยันว่าปิด anonymous Admin ใช้ loopback สำหรับ Grafana และไม่ได้ publish พอร์ต Loki ส่วน live eval test ใช้ subprocess จำลองและจับการแก้ oracle แบบยังไม่ commit ได้
- `git diff --check` ผ่าน สแกนไฟล์เปลี่ยนแปลง 51 ไฟล์แล้วไม่พบ credential ตามรูปแบบของตัวสแกน และไม่มีไฟล์ trace ดิบที่ Git ติดตาม

## ยังขาดผลรัน

- Docker build, container health และ Alloy → Loki ingestion เพราะ Docker daemon เชื่อมต่อไม่ได้
- Antigravity session reload, live eval ผ่าน harness จริง, FastAPI ผ่าน Uvicorn จริงบน revision นี้ และ CI matrix สาม OS ตามแผน

แนบ SHA และหลักฐานของแต่ละ Blocker เมื่อส่งกลับมา re-review
