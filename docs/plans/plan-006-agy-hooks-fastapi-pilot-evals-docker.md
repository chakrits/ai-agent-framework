---
plan_id: PLAN-006
intent_ref: N/A (Framework & Roadmap Execution Plan)
spec_ref: docs/plans/framework-review-roadmap-v2.md
owner: sa-architect-agent / human-maintainer
status: released
commits: 5ae1169 (2026-11-21), 16db38c (2026-11-22)
merged: PR #2, merge commit eca7f22 (both Windows jobs failed in that PR; all six jobs passed later in PR #4, merge commit d764d5f, run 45005508352)
released_in: v0.3.0
approval_record: no written approval of the whole plan found in this file; its approval checkbox is unchecked. See §D-01 note for one scoped chat approval
review_note: the latest PLAN-006 review file (round 6) is changes_requested (pilot PR/CI evidence); no later re-review file found. Tracked under work/INT-001 Gate 3
status_note: released is used because no defined plan-status set was found; status updated 2026-11-27 from Git history and GitHub; the body below is the historical plan text
---

# Implementation Plan (PLAN-006): Antigravity Hooks/Trace, FastAPI Testing, Docker/Worktree, Live Evals & Real E2E Pilot

> **Route:** Framework / Process Change (**High Risk**) — เอกสารนี้จัดทำขึ้นเพื่อ **ทบทวนและอนุมัติก่อนลงมือแก้ไขโค้ด** (ครอบคลุม `ROADMAP.md` ช่วง P6, P7, P8, P9, P10 และงานที่ค้างจาก `docs/handoff/2026-11-21-trace-v1.1.md`)

---

## 1. เป้าหมายและขอบเขต (5 Workstreams)

| Workstream | ชื่อภารกิจ | เชื่อมโยง ROADMAP / Handoff | ลำดับที่แนะนำ |
| :--- | :--- | :--- | :---: |
| **WS-A** | **Antigravity (`agy`) Hooks & Trace Integration** | P8 (Multi-Platform Parity) + P7 (Trace) | **1** |
| **WS-B** | **FastAPI Server Verification & Orchestrator v1 Hardening** | P10 (Orchestrator v1) + P7 (`TelemetryTracker` unified schema) | **2** |
| **WS-C** | **Worktree Helper, Orchestrator Dockerfile & Monitoring Stack Test** | P10 + Handoff §8.5 (ทดสอบ Alloy/Loki/OTel stack จริง) | **3** |
| **WS-D** | **Live Eval Mode & Expanded Regression Dataset** | P10 (Agent Evals `claude -p` / `codex exec`) | **4** |
| **WS-E** | **Real E2E Pilot Feature (`INT-001`)** | P6 (Work Records) + P9 (Real E2E Pilot ผ่าน 3 HITL Gates) | **5** |

### Dependency Flow

```text
[WS-A: agy Hooks & Trace] ──┐
[WS-B: FastAPI & Orch v1]  ──┼──► [WS-D: Live Eval Mode] ──► [WS-E: Real E2E Pilot (INT-001)]
[WS-C: Worktree & Docker]  ──┘
```

---

## 2. รายละเอียดแผนงานราย Workstream

### WS-A: Antigravity (`agy`) Hooks & Trace Integration (Single Source of Truth)
**เป้าหมาย:** ให้ Antigravity ใช้ `scripts/sdlc_hook.py`, `scripts/sdlc_guard/guard.py`, `policy.json`, และ `trace.py` ชุดเดียวกับ Claude Code และ Codex โดยไม่เขียน logic ซ้ำ

**ข้อกำหนดทางเทคนิค (จากสเปค `hooks.json` ของ Antigravity):**
- Antigravity ค้นพบ `.agent/hooks.json` (หรือ `.agents/hooks.json`) และอ่าน `AGENTS.md` / `.agents/skills/` โดยตรง
- Hook รันแบบ **Synchronous เท่านั้น** (ยังไม่รองรับ `async: true`) → ลงทะเบียนเฉพาะ 4 events ที่คุ้มค่า: `SessionStart`, `PreToolUse` (matcher: `run_command|write_to_file|replace_file_content|multi_replace_file_content|view_file`), `PostToolUse` (`run_command|write_to_file|replace_file_content|multi_replace_file_content`), `Stop`
- Input `stdin` เป็น **camelCase** (`conversationId`, `modelName`, `lastUserInput`, `toolCall.id`, `toolCall.name`, `toolCall.args.CommandLine` / `Path` / `TargetFile`, `error`)
- Output `stdout` ต้องเป็น JSON: `PreToolUse` → `{"decision":"allow"}` หรือ `{"decision":"deny","reason":"..."}` · `SessionStart` / `PostToolUse` / `Stop` → `{}`

| Task ID | งานที่ต้องทำ | ไฟล์เป้าหมาย | หมายเหตุสำคัญ |
| :--- | :--- | :--- | :--- |
| `A-01` | เพิ่ม `"antigravity"` ใน `PLATFORMS` และ `trace-event.schema.json` | `scripts/sdlc_guard/trace.py`, `docs/contracts/trace-event.schema.json` | Protected path — human commit |
| `A-02` | สร้าง `agy_adapter.py` (normalize camelCase `toolCall` → canonical `payload` + format `stdout` JSON decision) และต่อเข้า `sdlc_hook.py --platform antigravity` | `scripts/sdlc_guard/agy_adapter.py`*, `scripts/sdlc_hook.py` | Map `run_command`→`Bash`, `write_to_file`/`replace_file_content`/`multi_replace_file_content`→`Write`/`Edit`, `view_file`→`Read`, `modelName`→`model` |
| `A-03` | Generate `.agent/hooks.json` จาก `trace_hooks.py` + `sync-adapters.py` และเพิ่ม `.agent/hooks.json` ใน `policy.json` (`protected_globs`) | `scripts/sdlc_guard/trace_hooks.py`, `scripts/sync-adapters.py`, `.agent/hooks.json`*, `scripts/sdlc_guard/policy.json` | เพิ่ม parity check ของ `.agent/hooks.json` ใน `sync-adapters.py --check` |
| `A-04` | เขียน unit tests สำหรับ Antigravity payload normalization, deny/allow JSON output, และ schema validation + อัปเดต `ROADMAP.md` (แก้ Known Limitation บรรทัด 116) | `tests/test_agy_hooks.py`*, `ROADMAP.md` | ตั้ง `SDLC_TRACE_LEVEL=off` / temp dir ใน test |

---

### WS-B: FastAPI Server Verification & Orchestrator v1 Hardening
**เป้าหมาย:** พิสูจน์การทำงานของ HTTP layer (`orchestrator/api/main.py`) และอัปเกรด Orchestrator ให้พร้อมใช้งานจริง (persistent state, unified trace, strict gate control)

| Task ID | งานที่ต้องทำ | ไฟล์เป้าหมาย | หมายเหตุสำคัญ |
| :--- | :--- | :--- | :--- |
| `B-01` | สร้าง `.venv` ทดสอบติดตั้ง `orchestrator/requirements.txt` + `httpx` และเขียน integration test ด้วย `TestClient` ครบ 6 endpoints + error cases (`400`/`404`/`422`) | `tests/test_orchestrator_api.py`* | ใช้ `pytest` หรือ `unittest` + skip cleanly ถ้าไม่มี `fastapi` ใน env พื้นฐาน (เพื่อให้ CI พื้นฐานที่ไม่มี deps ยังผ่าน) |
| `B-02` | ปิด/จำกัด `auto_approve_gates` ใน `POST /runs` (อนุญาตเฉพาะ dev/test flag), เพิ่ม `approver_id` + timestamp ใน `POST /runs/{run_id}/approve` | `orchestrator/api/main.py`, `orchestrator/api/handlers.py`, `orchestrator/graphs/sdlc_pipeline.py` | ปิดความเสี่ยงข้าม HITL gate ผ่าน API |
| `B-03` | Persist `PipelineState` ลงไฟล์ JSON (`.sdlc/runs/<run_id>.json`) แทน `self.runs` ใน memory เพื่อให้ resume หลัง restart ได้ | `orchestrator/api/handlers.py`, `orchestrator/core/state_store.py`* | — |
| `B-04` | ให้ `TelemetryTracker` เขียน trace ตาม `docs/contracts/trace-event.schema.json` (`platform: "orchestrator"`, `operation: "gate_decision"`) และให้ `bands.py` อ่าน config จาก `docs/operating-model/bands.yaml` จริง | `orchestrator/telemetry/tracker.py`, `orchestrator/telemetry/bands.py` | เชื่อม P7 + P10 |

---

### WS-C: Worktree Helper, Orchestrator Dockerfile & Monitoring Stack Test
**เป้าหมาย:** รองรับการทำงานขนานอย่างปลอดภัยด้วย `git worktree`, บรรจุ Orchestrator ลง Container และทดสอบการส่ง trace เข้า Stack จริง (Loki / OTel Collector)

| Task ID | งานที่ต้องทำ | ไฟล์เป้าหมาย | หมายเหตุสำคัญ |
| :--- | :--- | :--- | :--- |
| `C-01` | สร้าง Worktree Helper (`create <INT-xxx> <slug>`, `list`, `cleanup <INT-xxx>`) ใต้ `.worktrees/` (เพิ่มใน `.gitignore`) และเช็ก `git rev-parse` / hook readiness | `scripts/worktree.py`*, `.gitignore`, `tests/test_worktree.py`* | ใช้ `git worktree` ตรงๆ (ห้ามใช้ Claude `WorktreeCreate` hook) |
| `C-02` | สร้าง `orchestrator/Dockerfile` (non-root `python:3.12-slim`, healthcheck `/health`) และ `.dockerignore` | `orchestrator/Dockerfile`*, `.dockerignore`* | — |
| `C-03` | สร้าง `docker-compose.yml` (profile `orchestrator` + profile `monitoring` ใช้ `docs/guides/examples/alloy.config` หรือ `otelcol.yaml`) และทดสอบยิง trace จริงเพื่อปรับจูน config ตัวอย่าง | `docker-compose.yml`*, `docs/guides/examples/*`, `docs/guides/agent-trace-monitoring.md` | ปิดรายการ "ยังไม่ยืนยัน §5.2" ใน Handoff |

**ผลทดสอบรอบ 3:** Docker build และ smoke test แบบ file-backed ผ่านบน OrbStack ใช้ UID `1000` และ read-only mount, `/health` คืน `200`, token ขาดหรือผิดคืน `401` และ token จากไฟล์ผ่าน authentication ก่อนคืน `404` สำหรับ run ที่ไม่มีอยู่ [คำสั่ง Compose](../../orchestrator/README.md#file-backed-token-registry)

---

### WS-D: Live Eval Mode & Expanded Regression Dataset
**เป้าหมาย:** แยก Contract Evals (เร็ว/ฟรีใน PR) ออกจาก Live Agent Evals (รัน CLI จริงใน Sandbox พร้อม budget cap และ deterministic grader)

**สถานะรอบ 3:** CI ให้รัน live เฉพาะ Claude ผ่าน `--max-budget-usd` ของ CLI ส่วน Codex ยังเรียกได้จาก CLI ในเครื่อง ค่า `--max-budget` ใช้ตรวจค่าใช้จ่ายที่รายงานหลังรันสำหรับคำสั่งที่ไม่มีตัวควบคุมในตัว การเปิด Codex ใน CI รอวิธีจำกัดค่าใช้จ่ายระหว่างรันพร้อมผลทดสอบ

**การอนุมัติขอบเขต D-01 (รอบ 4):** Maintainer ตอบในแชทว่า “อนุมัติให้เลื่อนเฉพาะ live eval” ตามคำขอเลื่อน Antigravity live eval ไปงานถัดไป งาน Antigravity Hooks และการตรวจ hook ใน session ใหม่ยังอยู่ใน WS-A งาน live eval ของ Antigravity ต้องมี sandbox และเพดานค่าใช้จ่ายระหว่างรันก่อนเปิดใช้

| Task ID | งานที่ต้องทำ | ไฟล์เป้าหมาย | หมายเหตุสำคัญ |
| :--- | :--- | :--- | :--- |
| `D-01` | เพิ่ม `--mode contract\|live` และ `--harness claude\|codex` + `--max-budget` / `--timeout` ใน `evals/run_evals.py` | `evals/run_evals.py`, `tests/test_eval_runner.py`* | บังคับ `SDLC_TRACE_DIR` ชี้ temp dir เพื่อไม่ให้ปน trace จริง CI ใช้ Claude เท่านั้น |
| `D-02` | สร้าง Fixture Sandbox และขยาย Eval Dataset จาก 3 เคสเป็น ≥ 10 เคส (Plan, Spec IPO, QA 13-section, Bugfix failing-test-first, Protected-path block, Security OWASP) | `evals/fixtures/*`*, `evals/datasets/04..10-*.json`* | Grader ใช้ `validate-contracts.py` + `git diff` check เท่านั้น |
| `D-03` | เพิ่ม CI workflow `evals-live.yml` (รันเฉพาะ `workflow_dispatch` / weekly `schedule` เพื่อควบคุมค่า token) | `.github/workflows/evals-live.yml`* | — |

---

### WS-E: Real E2E Pilot Feature (`INT-001`)
**เป้าหมาย:** พิสูจน์ Framework ทั้งระบบกับ Feature จริง 1 งาน ตั้งแต่ต้นจน Merge ผ่าน 3 HITL Gates พร้อมหลักฐานครบชุด

| Task ID | งานที่ต้องทำ | ไฟล์เป้าหมาย / หลักฐาน | Gate |
| :--- | :--- | :--- | :---: |
| `E-01` | กำหนด Pilot Scope + สร้างพื้นที่ `work/INT-001/` (โครง P6) + สร้าง branch `feat/INT-001-<slug>` ผ่าน `scripts/worktree.py` | `work/INT-001/README.md`, `work/index.yaml` | — |
| `E-02` | Stage 1 Plan (`ba-po-agent`) → สร้าง `work/INT-001/intent.md` | `work/INT-001/intent.md` | **Gate 1 (Human)** |
| `E-03` | Stage 2 Design (`sa-architect-agent`) → สร้าง `work/INT-001/spec.md` (IPO Matrix + API/Data Contract + ADR) | `work/INT-001/spec.md` | **Gate 2 (Human)** |
| `E-04` | Stage 3–4 TDD & Build (`qa-function-agent` → `dev-coding-agent` ภายใต้ hook guard) | `work/INT-001/test-report.md`, `plan.md`, `tasks.json`, โค้ด + test | — |
| `E-05` | Stage 5 Review & Trace Evidence (`code-reviewer-agent` + `security-audit-agent` + `sdlc_trace.py export`) | `work/INT-001/REVIEW.md`, `work/INT-001/trace-summary.md` | **Gate 3 (Human PR Merge)** |

`(*)` = ไฟล์ใหม่ที่จะสร้างเมื่อเริ่มลงมือ

---

## 3. Master Verification Checklist (ตรวจการทำงานทีละขั้น)

### Checklist A — Pre-Implementation Gate (ก่อนแก้ไฟล์แรก)
- [ ] ผู้ใช้งานอนุมัติแผน `PLAN-006` (เลือกทำครบทุก WS หรือเลือกเฉพาะ WS ที่ต้องการเริ่มก่อน)
- [ ] ยืนยันข้อจำกัดการ Commit Protected Files: งานใน WS-A มีการแก้ `scripts/sdlc_guard/**`, `scripts/sdlc_hook.py`, `docs/contracts/trace-event.schema.json` → ต้องให้ Human เป็นผู้รัน `SDLC_ALLOW_PROTECTED=1 git commit ...`
- [ ] ตรวจสุขภาพ repo ปัจจุบันก่อนเริ่ม: `python3 scripts/doctor.py` และ `python3 -m unittest discover -s tests -v` ผ่านครบ

### Checklist B — Verification สำหรับ WS-A (Antigravity Hooks & Trace)
- [ ] `python3 scripts/sync-adapters.py --check` ผ่าน และตรวจพบ `.agent/hooks.json` ตรงกับ `trace_hooks.py` 100%
- [ ] ทดสอบ pipe JSON payload ของ Antigravity (`conversationId`, `modelName`, `toolCall`) เข้า `python3 scripts/sdlc_hook.py pretooluse --platform antigravity`:
  - [ ] คำสั่งปกติ → exit `0` และ `stdout` เป็น `{"decision": "allow"}`
  - [ ] `dev-coding-agent` แก้ protected path / `.env` / test oracle → `stdout` เป็น `{"decision": "deny", "reason": "BLOCKED: ..."}`
- [ ] ทดสอบ `posttooluse`, `session-start`, `stop` ด้วย `--platform antigravity` → `stdout` เป็น `{}` และเขียน event ลง `.sdlc/traces/` ผ่าน `trace.validate_event()` โดย `platform == "antigravity"` และ `model` ไม่เป็น `unknown`
- [ ] ทดสอบรันจริงใน Antigravity session ใหม่ แล้วเช็กด้วย `python3 scripts/sdlc_trace.py list` ว่าเห็น session จาก `antigravity` จริง

### Checklist C — Verification สำหรับ WS-B (FastAPI Server & Orchestrator v1)
- [ ] `TestClient` ผ่านครบ 6 endpoints + error status codes (`400`, `404`, `422`) ใน `tests/test_orchestrator_api.py`
- [ ] ทดสอบ `uvicorn orchestrator.api.main:app --port 8000`: `GET /health` คืน `200`, `GET /docs` เปิดได้
- [ ] ทดสอบ `POST /runs` → ปฏิเสธ auto-approve ในโหมด production; เมื่อเรียก `POST /runs/{run_id}/approve` พร้อม `approver_id` แล้วจำลอง **restart server** → state ยังโหลดกลับมาทำ Gate ถัดไปได้
- [ ] ตรวจไฟล์ trace ที่ Orchestrator สร้างว่าผ่าน schema `docs/contracts/trace-event.schema.json` และ `bands.py` โหลดค่า threshold จาก `docs/operating-model/bands.yaml` จริง

### Checklist D — Verification สำหรับ WS-C (Docker & Worktree Helper)
- [ ] `python3 scripts/worktree.py create INT-001 pilot-test` สร้าง worktree ที่ `.worktrees/INT-001` บน branch `feat/INT-001-pilot-test` และ `git worktree list` แสดงครบ; `cleanup` ลบได้สะอาด
- [ ] ใน worktree ใหม่ `python3 scripts/sdlc_hook.py doctor` ผ่าน และ trace จับ `work_item: "INT-001"` จากชื่อ branch ได้อัตโนมัติ
- [ ] `docker build -t sdlc-orchestrator -f orchestrator/Dockerfile .` สำเร็จ และ `curl http://localhost:8000/health` คืน `200` (non-root user)
- [ ] *(ถ้ามี Docker/OrbStack บนเครื่อง)* `docker compose --profile monitoring up` รับ trace จาก `.sdlc/traces/` เข้า Loki/OTel Collector สำเร็จ และอัปเดตผลยืนยันใน `docs/guides/agent-trace-monitoring.md`

### Checklist E — Verification สำหรับ WS-D (Live Eval Mode)
- [ ] `python3 evals/run_evals.py --mode contract` ผ่าน ≥ 10 เคสโดยไม่เรียก API ภายนอก
- [ ] `python3 evals/run_evals.py --mode live --harness claude --limit 2` รันใน temp directory โดย **ไม่สร้าง session ปนใน `.sdlc/traces/` จริง** และเคารพ `--max-budget` / timeout
- [ ] Negative test: ถ้า Agent ในโหมด live แอบแก้ไฟล์ test oracle → deterministic grader ตี `FAIL`

### Checklist F — Verification สำหรับ WS-E (Real E2E Pilot `INT-001`)
- [ ] ครบทุก artifact: `intent.md`, `spec.md`, `test-report.md`, `plan.md`, `tasks.json` (`passes: true` + `evidence`), `REVIEW.md`, `trace-summary.md`
- [ ] `python3 scripts/validate-contracts.py --tasks work/INT-001/tasks.json --test-report work/INT-001/test-report.md` → **PASSED**
- [ ] `python3 scripts/sdlc_trace.py export --work-item INT-001 --out work/INT-001/trace-summary.md` มีข้อมูลครบและไม่มี secret รั่ว
- [ ] ผ่าน Human Sign-off ครบ **Gate 1, Gate 2, Gate 3** และผ่าน CI บน GitHub (3 OS × Python 3.10/3.12)

### Checklist G — Final Framework Health Gate (หลังจบทุก Workstream)
- [ ] `python3 scripts/sync-adapters.py --check` → PASSED
- [ ] `python3 scripts/validate-context-budget.py` → PASSED
- [ ] `python3 scripts/validate-contracts.py --check-defaults` → PASSED
- [ ] `python3 -m unittest discover -s tests -v` → ALL PASSED (0 unexpected failures)
- [ ] `python3 evals/run_evals.py` → PASSED
- [ ] `python3 scripts/doctor.py` → PASSED
- [ ] `ROADMAP.md` และ `CHANGELOG.md` อัปเดตสถานะจริงพร้อมลิงก์หลักฐาน (CI run / test output)

---

## 4. ความเสี่ยงและ Rollback
- **Antigravity hook latency:** เนื่องจาก `agy` รัน hook แบบ sync ถ้า `sdlc_hook.py` ช้าอาจหน่วง tool call → แยก `PreToolUse`/`PostToolUse` เฉพาะ tools แก้ไฟล์/รันคำสั่ง และวัด latency ใน `test_agy_hooks.py`; ปิดได้ทันทีด้วย `enabled: false` ใน `.agent/hooks.json`
- **Live Eval API cost:** จำกัด `--limit` และ `--max-budget` เสมอ และแยกรันเฉพาะ `workflow_dispatch`/schedule
- **Protected file commits:** แบ่ง PR/commit ของ WS-A (protected) ให้ชัดเจนเพื่อให้ human review และ commit ด้วย `SDLC_ALLOW_PROTECTED=1` ได้ง่าย
