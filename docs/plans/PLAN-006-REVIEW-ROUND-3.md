# PLAN-006 Independent Re-review · รอบ 3

**Verdict `changes_requested`** · **วันที่ 2026-11-21**

ตรวจ working tree บน `main` ที่ HEAD `7b723bc8966089d9be16883f30b8af62ab4a49f7` มีไฟล์ tracked เปลี่ยน 21 ไฟล์และยังไม่ได้ stage SHA-256 ของ `git diff --binary HEAD` สำหรับ snapshot ที่ตรวจคือ `098122ca4dcdfd3369d3270377d0d0f5a525fa43a81ad6e0f8fe28b29127f1bb` [Verdict รอบ 2](PLAN-006-REVIEW-ROUND-2.md)

## รายการแก้ไขและเกณฑ์รับงาน

| ระดับ | WS | ข้อค้นพบและเกณฑ์รับงาน |
|---|---|---|
| **Blocker** | E · Pilot evidence | Export ใหม่ตรงกับ summary ที่แนบ ทั้ง 8 events และ Bash 3 ครั้ง แต่ event ทั้งหมดอยู่บน `main` และคำสั่งที่บันทึกเป็นการตรวจผล ส่วน SHA ที่อ้างสำหรับ Gate 1–2 เป็น commit เดียวกับ implementation ยังยืนยันลำดับการอนุมัติก่อนลงมือไม่ได้ แนบหลักฐานอนุมัติจากมนุษย์และ branch/PR/CI ที่เชื่อมกับ revision ของ pilot ก่อนส่งให้ Maintainer พิจารณา Gate 3 [REVIEW.md:11](work/INT-001/REVIEW.md#L11) · [trace-summary.md:28](work/INT-001/trace-summary.md#L28) · [PLAN-006:89](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md#L89) |
| **Blocker** | D · Live cost cap | Job Codex เปิดให้รันพร้อม API key และประกาศว่าบังคับ budget แต่ตรวจค่าใช้จ่ายหลัง subprocess จบ การประมาณจากขนาด stdout ไม่ครอบคลุม prompt, tool calls หรือ internal turns ค่าใช้จ่ายจึงเกิดขึ้นได้ก่อน grader ตัดสิน ให้บังคับเพดานจริงระหว่างรันหรือปิด live Codex ใน CI จนกว่าจะมีวิธีควบคุมและทดสอบได้ [evals-live.yml:68](.github/workflows/evals-live.yml#L68) · [run_evals.py:32](evals/run_evals.py#L32) · [run_evals.py:182](evals/run_evals.py#L182) |
| **Important** | E · Traceability | Validator ตรวจคู่ `URD ↔ FS` เมื่อ parse เจออย่างน้อยหนึ่งคู่ ทดสอบโดยเอาแถว mapping ออกจาก spec สำเนาชั่วคราวและเหลือ IDs ในข้อความธรรมดา ผลยังผ่าน ให้กำหนดคู่จากตารางที่เป็นแหล่งอ้างอิงและคืน exit `1` เมื่อไม่มีคู่หรือมี URD ที่ไม่มี FS [validate_work_item.py:32](scripts/validate_work_item.py#L32) · [validate_work_item.py:92](scripts/validate_work_item.py#L92) |
| **Important** | D · Oracle integrity | Grader เทียบกับ baseline SHA และตรวจ exit code แล้ว แต่ยังแยก path จาก Git ด้วยบรรทัดและอ่าน output แบบ human-readable จึงจับชื่อที่ Git ใส่ quote หรือรายการ rename ได้ไม่ครบ ให้ใช้ output แบบ NUL-delimited และตรวจทั้ง path ต้นทางกับปลายทาง พร้อม regression สำหรับชื่อ Unicode และ rename [run_evals.py:91](evals/run_evals.py#L91) |
| **Important** | D · Scope | ถอด Antigravity ออกจาก live CLI และ CI แล้ว ส่วน PLAN-006 ยังระบุสาม harness ให้บันทึกการอนุมัติลด scope หรือส่งหลักฐานว่า Antigravity live eval ทำงานพร้อม sandbox และ budget cap [run_evals.py:199](evals/run_evals.py#L199) · [PLAN-006:78](docs/plans/plan-006-agy-hooks-fastapi-pilot-evals-docker.md#L78) |
| **Important** | C · Deployability | Compose ส่งค่า token registry ผ่าน JSON env ได้แล้ว ส่วนตัวเลือก `SDLC_ORCHESTRATOR_TOKENS_FILE` ส่งเพียงชื่อ path เข้า container และ Compose มี mount เฉพาะ volume state ให้เพิ่ม secret mount แบบ read-only หรือระบุวิธี mount และสิทธิ์อ่านของ non-root user ในคู่มือ พร้อม smoke test แบบ file-backed [docker-compose.yml:7](docker-compose.yml#L7) · [orchestrator/README.md:23](orchestrator/README.md#L23) |

**Nit 0 รายการ**

## ยืนยันแล้วจากผลรันจริง

- `git diff --check`, `git diff --cached --check`, `git diff --check 7b723bc` และ `git diff --check c78aed9..HEAD` คืน exit `0`
- รันครบทั้ง 7 คำสั่งเดิม Adapter parity, context budget, contract validation, work-item validation และ doctor ผ่าน ส่วน contract evals ผ่าน **10/10** และ unittest ผ่าน **229 จาก 232** ข้าม Windows launcher สองเทสต์และ FastAPI หนึ่งเทสต์
- ชุด API บนสำเนาชั่วคราวของ snapshot พร้อม dependencies ผ่าน **7/7** ครอบคลุม run-scope isolation, RBAC และ lock failure ที่ไม่เขียน state หรือ telemetry ผล Uvicorn บน loopback ยืนยัน `/health` และ `/docs` คืน `200`, ไม่มี token ได้ `401`, auto-approve ได้ `403` และหลัง restart ยังโหลด run scope, ตัวตนและเวลาผู้อนุมัติ แล้วเดินจาก Gate 2 ไป Gate 3 ได้
- เทสต์ยืนยันว่า Antigravity `SessionStart` คืน `{}`, worktree ปฏิเสธ parent symlink และ eval grader จับการแก้ oracle ที่ commit แล้วพร้อมหยุดเมื่ออ่าน Git ไม่สำเร็จ เทสต์ eval ใช้ CLI จำลอง
- `docker compose config --quiet` ผ่านทั้ง profile `orchestrator` และ `monitoring` โดยไม่ต้องใส่ Grafana password ตอนตรวจ config
- SHA-256 ของ `work/INT-001/test-report.md` ตรงกับ QA baseline ที่ระบุ และ diff จาก `7b723bc` ว่าง ยืนยันว่า QA oracle คงเดิมระหว่างการแก้รอบนี้ Export trace ใหม่ลง temp directory แล้วตัวเลขและคำสั่งตรงกับไฟล์สรุปใน workspace

## หลักฐานที่ยังขาด

- Docker build, container health, การโหลด token จากไฟล์ใน container และ Alloy → Loki ingestion ยังไม่ยืนยันเพราะ OrbStack Docker daemon ไม่มี socket ให้เชื่อมต่อ
- Trace ยืนยัน local Antigravity hook events สำหรับการตรวจ pilot รอบนี้ หลักฐานการ reload ใน session ใหม่, live eval ผ่าน harness จริง และ CI matrix สาม OS ยังไม่ครบ

แนบ SHA และหลักฐานปิด Blocker ทั้งสองข้อเมื่อส่งกลับมา re-review
