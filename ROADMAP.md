# AI-Native SDLC Agent Framework — Roadmap (v2)

> **Architecture:** Enterprise-agnostic Canonical Core (`.agents/` + `docs/`) + Thin Multi-Harness Adapters (`.claude/`, `.codex/`, `.agent/`) + Deterministic Cross-Platform Guardrails (`scripts/sdlc_guard/`) + Optional Python Orchestrator
> **Analysis & Rationale:** [Framework Review & Roadmap v2](docs/plans/framework-review-roadmap-v2.md) · [Claude AI-Native SDLC Playbook Analysis](docs/reference-architecture/benchmarks/claude-ai-native-sdlc-playbook-analysis.md) · [Cross-Platform Plan](docs/plans/cross-platform-harness-plan.md)
> **Last re-baseline:** 2026-11-21 · **Last update:** 2026-11-22 (PLAN-007 closeout, release `v0.3.0`)

## สถานะที่ใช้

| สถานะ | ความหมาย |
| :--- | :--- |
| ✅ **Verified** | มี test / CI รันผ่านบน remote แล้ว |
| 🟡 **Implemented** | โค้ดเสร็จและผ่าน test ในเครื่อง แต่ยังไม่ผ่าน CI บน remote หรือยังขาดการยืนยันบางส่วน |
| 🟠 **Scaffolded** | มีไฟล์/โครงแล้ว แต่ยังไม่ได้พิสูจน์ว่าใช้งานได้จริง |
| ⬜ **Missing** | ยังไม่ได้เริ่ม |

> กฎ: ห้ามติ๊ก ✅ ถ้าไม่มีหลักฐาน (CI run, artifact หรือ test output) แนบไว้

---

## Overview

| Phase | Name | สถานะ | Primary Goal | Exit Criteria |
| :--- | :--- | :---: | :--- | :--- |
| P0 | Foundation & Governance | 🟠 | `AGENTS.md`, constitution, routing | มี commit แรก + CI เขียว; ลบโฟลเดอร์ reference ที่ว่าง |
| P1 | Spec-Driven Artifact Spine | 🟠 | Contracts + templates + traceability IDs | validator ครบ 5 artifact (ปัจจุบันครบ 2/5) |
| P2 | Core Agents, Skills & Adapters | 🟠 | Canonical agents/skills + adapters | E2E pilot ผ่าน 3 gates (ย้ายไป P9) |
| P3 | Harness, Hooks & CI Evals | 🟠 | Validators, guard, evals | guard ใช้งานได้จริง (แก้ใน P5); evals ยังไม่ได้รัน agent จริง (ย้ายไป P10) |
| P4 | Python Orchestrator & Stage 6 | 🟠 | Orchestrator + `bands.yaml` | ตอนนี้ dry-run เท่านั้น; ยังไม่อ่าน `bands.yaml`; ข้าม HITL gate ผ่าน API ได้ (แก้ใน P10) |
| **P5** | **Hardening & Cross-Platform Baseline** | 🟡 | ให้ guardrail ใช้งานได้จริงบน Windows / macOS / Linux / WSL | CI matrix เขียวทั้ง 3 OS + ผ่าน checklist ยืนยันบน Windows |
| P6 | Runtime Registry & Work Records | ⬜ | รองรับหลาย runtime + บันทึกการทำงาน | runtime ตัวอย่าง 2 ตัว + work item 1 ชุด ผ่าน validator |
| P7 | Agent Trace & Observability | 🟡 | Trace จากทุก platform | trace จาก Claude + Codex ผ่าน schema validation และอ้างอิง `INT-xxx` ได้ |
| P8 | Multi-Platform Parity | ⬜ | Codex / Antigravity / Gemini เท่าเทียมกัน | มีบันทึกการยืนยันต่อ platform และต่อเวอร์ชัน |
| P9 | Real E2E Pilot | ⬜ | ทำ feature จริงข้าม FE + BE + DB | artifacts + ADR + CHANGELOG + trace ครบ, merge ผ่าน branch protection |
| P10 | Agent Evals & Orchestrator v1 | ⬜ | รัน eval กับ agent จริง + persistent state | eval ≥10 เคสรันตาม schedule; resume หลัง restart ได้; การอนุมัติระบุตัวผู้อนุมัติ |
| P11 | Closed-Loop Ops & Stack Skills | ⬜ | ใช้ bands กับ metric จริง + skills ต่อ stack | breach จริงสร้าง draft intent; skill ใหม่ทุกตัวมี eval |
| P12 | Framework Packaging (optional) | ⬜ | แพ็ก core เป็น package/plugin | runtime repo ภายนอกติดตั้งได้และผ่าน CI |

**ลำดับความสำคัญ:** P5 → P6/P7 (ตอบโจทย์หลัก: หลาย runtime + บันทึกการทำงาน) → P9 (พิสูจน์ทั้งระบบ) → P8/P10/P11

---

## Re-baseline ของ P0–P4 (เดิมติ๊ก `[x]` ทั้งหมด)

| Phase | สิ่งที่มีแล้ว | สิ่งที่ยังไม่ได้พิสูจน์ / ข้อบกพร่อง |
| :--- | :--- | :--- |
| P0 | `AGENTS.md`, `CLAUDE.md`, constitution, bootloader, dynamic routing | repo ยังไม่มี commit → CI ไม่เคยรัน; โฟลเดอร์ `01.`–`09.` ส่วนใหญ่ว่าง |
| P1 | 5 schemas, templates, ID chain `URD→FS→TC→TASK→PR` | มี validator แค่ `tasks.json` และ test report; YAML schema ยังไม่ใช่ JSON Schema จริง |
| P2 | 7 agents, 4 skills, EBMC pack, parity check | ยังไม่มี E2E pilot; agents/skills ยังสั้น (13–32 บรรทัด) |
| P3 | validators, CI, evals 3 เคส | guard เดิมไม่ทำงานใน hook mode (แก้แล้วใน P5); evals ตรวจแค่ sample ที่เขียนไว้ล่วงหน้า |
| P4 | loader, router, pipeline, telemetry, bands | routing ใน doc กับ `router.py` ไม่ตรงกัน; `bands.yaml` ไม่ถูกอ่าน; artifact ไม่ถูกส่งต่อระหว่าง stage; state อยู่ใน memory |

---

## Detailed Phase Breakdown

### P5: Hardening & Cross-Platform Baseline — 🟡 Implemented
- [x] เขียน guard ใหม่เป็น Python (`scripts/sdlc_guard/`) แทน bash: แก้ IFS bug และ path ที่มีช่องว่างทำให้ hook ไม่ทำงาน
- [x] Normalize path ข้าม OS (`C:\`, `\\?\`, UNC, `/c/`, `/mnt/c/`, traversal, symlink, ไม่สนตัวพิมพ์)
- [x] วิเคราะห์คำสั่ง bash / PowerShell / cmd รวมคำสั่งที่ถูก wrap (`powershell -Command`, `-EncodedCommand`, `cmd /c`, `bash -lc`)
- [x] อ่าน role จาก `agent_type`; ล็อก test ที่ commit แล้วสำหรับ dev agent (เช็คกับ git แบบไม่สนตัวพิมพ์); ป้องกัน CI/validator scripts จาก dev agent
- [x] Launchers `scripts/bin/sdlc-hook` (sh) และ `sdlc-hook.cmd` แบบ fail-closed; `.gitattributes` ล็อก line endings
- [x] SessionStart doctor (ตรวจ OS / shell / Python / Git / line endings) + `setup.py` + pre-commit ที่ตรวจ staged diff
- [x] Claude `settings.json` (matcher ครบ, path มี quote) + Codex `.codex/hooks.json` (generated, มี `commandWindows`)
- [x] CI matrix ubuntu / macOS / Windows × Python 3.10 / 3.12 (+ GitLab Windows job แบบเลือกเปิดได้)
- [x] Commit แรก + CI เขียวบน GitHub ทั้ง 6 jobs (ubuntu / macOS / Windows × py3.10 / 3.12) — [run 44866058493](https://github.com/chakrits/ai-agent-framework/actions/runs/44866058493); Windows รัน `.cmd` launcher และ `sh` launcher ผ่าน Git Bash จริง
- [x] แก้ bug ที่พบจาก log ของ Windows CI: `cwd` แบบ relative (`"."`) ถูกแปลงเป็น `/` ทำให้เช็ค protected path พลาด
- [x] Versioning: `version.txt` (SemVer, เริ่ม `0.1.0`) + release-please + `CHANGELOG.md` + commit-msg hook บังคับ Conventional Commits + `LICENSE` (MIT) + `CONTRIBUTING.md` + README badges
- [x] Governance quick fixes: constitution อ้าง `policy.json` แทน `.sdlc` ที่คลุมเครือ, ลบ permission ปลอมใน `settings.json`, อัปเดต PR/MR templates, สแกนเนื้อหา staged diff หา secret ใน pre-commit
- [x] แก้ guard ให้นับ override env var เฉพาะที่มีผลจริง (ไม่นับข้อความใน quote/heredoc) + อัป `actions/checkout@v5`, `setup-python@v6`
- [x] Release แรกและรอบถัดไปผ่าน release-please: `v0.1.0`, `v0.2.0`, `v0.3.0` ([releases](https://github.com/chakrits/ai-agent-framework/releases)); Discussions เปิดแล้ว และ GitHub Actions สร้าง Release PR ได้ (PR #1, #3)
- [x] แก้เทสต์ `test_eval_runner` ที่ fail บน Windows CI มาตั้งแต่ `main` `eca7f22`: fixture ลบ `.git` ที่เป็น read-only ไม่ได้ (`8c4ae79`, PR #4) — CI 6/6 เขียวที่ [run 45005508352](https://github.com/chakrits/ai-agent-framework/actions/runs/45005508352)
- [ ] CI บน GitLab (ยังไม่ได้ผูก remote)
- [ ] ตั้ง branch protection บน `main` — **ยังไม่ได้ตั้ง** (GitHub API ตอบ `Branch not protected` เมื่อ 2026-11-22) ทั้งที่ `AGENTS.md` §1 เขียนว่า `main` protected; ต้องให้ admin ของ repo เปิดเอง
- [ ] ยืนยันบน Windows จริง: Git Bash รับ path `C:\…` ใน `CLAUDE_PROJECT_DIR`, ชื่อ tool PowerShell ของ Claude, Codex `commandWindows` + การ pipe stdin ผ่าน `$input`
- [ ] ให้ `routing.yaml` เป็นแหล่งข้อมูลเดียว — *ความคืบหน้า:* PLAN-007 ทำให้ gate model ใน constitution / dynamic-routing / AGENTS.md ตรงกับ `router.py` แล้ว แต่ยังไม่มี `routing.yaml`

### Governance Consistency (PLAN-007) — ✅ Verified
> แผนและผลรีวิว: [plan-007-governance-consistency.md](docs/plans/plan-007-governance-consistency.md) · [plan-007-review.md](docs/plans/plan-007-review.md) · merge [PR #4](https://github.com/chakrits/ai-agent-framework/pull/4) (`d764d5f`) · release `v0.3.0`
- [x] Gate model เดียวทั้งระบบ (Plan Checkpoint / Gate 1 Intent / Gate 2 Spec / Gate 3 Merge) + ตาราง Risk → Tier ที่เดียวใน constitution; routing, bootloader, AGENTS.md, workflows และ README ตรงกัน
- [x] ที่วาง artifact ตายตัว (`work/<INT-xxx>/`, `docs/plans/`, `docs/handoff/`, `.sdlc/`) + ย้าย `plan.md` ที่ root ไป `docs/plans/plan-005-trace-v1-1.md`
- [x] ELI10 Change Digest + `validate_work_item.py --require-digest` / `--digest-file` (เทสต์ 16 ข้อ)
- [x] ที่เก็บ ADR (`docs/adr/` + template), skill `council-pressure-test`, reviewer อ่าน diff ก่อน digest
- [x] Independent review 3 รอบ (สุดท้าย `approved`) + CI 6/6 เขียวที่ head สุดท้าย
- [ ] ให้ CI / git hook เรียก digest validator (ต้องเป็น Framework Change แยก เพราะแตะ protected path)

### P6: Runtime Registry & Work Records — ⬜
- [ ] `runtimes/registry.yaml` + `runtimes/<app>/runtime.yaml` (stack FE/BE/DB/Redis/API, คำสั่ง build/test/lint/run, env, ports, health)
- [ ] `AGENTS.md` แยกต่อ runtime (ไฟล์ที่ใกล้ที่สุดมีผล) + `STATUS.md` + `CHANGELOG.md` + ADR — *ความคืบหน้า:* ที่เก็บ ADR อยู่ที่ `docs/adr/` แล้ว (PLAN-007) และมี [AGENTS.template.md](docs/templates/AGENTS.template.md) สำหรับ repo ปลายทาง
- [ ] `work/INT-xxx/` เก็บ intent / spec / plan / tasks / test-report / REVIEW + `log.md` และ `work/index.yaml` — *ความคืบหน้า:* `work/INT-001/` + `work/index.yaml` มีแล้ว (รวม `change-digest.md`); ยังไม่มี `log.md`
- [ ] Validators: `validate-runtimes`, validator ของ intent / spec / review + แปลง contracts เป็น JSON Schema จริง

### P7: Agent Trace & Observability — ⬜
- [x] Trace schema [`trace-event.schema.json`](docs/contracts/trace-event.schema.json) (operation ตาม OTel GenAI: `invoke_agent`, `execute_tool`) + `work_item`
- [x] เขียน trace จาก hooks ของ Claude (SessionStart/End, UserPromptSubmit, Pre/PostToolUse, PostToolUseFailure, SubagentStart/Stop, Stop) และ Codex (`.codex/hooks.json` generated); เก็บใน `.sdlc/traces/` (local, redact secret, ตัด output, retention 30 วัน, lock ข้าม OS)
- [x] CLI `scripts/sdlc_trace.py` (`list` / `show` / `summary` / `export`) — ยืนยันกับ event จริงของ Claude Code แล้ว; ยังไม่ได้ยืนยัน payload ของ Codex จริง
- [x] Trace v1.1: field `model` / `effort` (+ที่มา), เวลาท้องถิ่นพร้อม offset (UTC+7 ตามเครื่อง, `SDLC_TRACE_TZ=utc` ได้), `prompt_id` / `turn_id` / `permission_mode`, event เพิ่ม (PermissionRequest/Denied, ConfigChange, InstructionsLoaded, StopFailure, PostModelSwitch, Compact, Notification, Task; Codex: PostModelRequest + token_usage, Interrupt) และ Tier 2 แบบ opt-in
- [x] ควบคุม level: `off|info|debug` ผ่าน env > `.sdlc/trace.json`; agent ขอ `debug --for <=120m` ได้, การปิด/ถาวร/unset เป็น human-only (TTY + guard) และบันทึก `TraceConfigChange`
- [x] คู่มือ [agent-trace-manual.md](docs/guides/agent-trace-manual.md), [monitoring guide](docs/guides/agent-trace-monitoring.md) + ตัวอย่าง Alloy/Filebeat/OTel Collector/OpenSearch template (**ยังไม่ได้ทดสอบกับ stack จริง**), skill `agent-trace`
- [ ] ให้ orchestrator `TelemetryTracker` ใช้ schema เดียวกัน + `runtime` field (หลัง P6)
- [ ] ส่งออก OTel (optional) + บันทึก rule ID ของ guard (หลังทำ rule registry)

### P8: Multi-Platform Parity — ⬜
- [ ] ตรวจ Antigravity ว่าอ่าน `.agents/` (rules / skills / workflows) ได้เองหรือไม่ → ลด mirror `.agent/`
- [ ] `GEMINI.md` pointer + capability matrix ที่ทดสอบจริงต่อ platform และเวอร์ชัน

### P9: Real E2E Pilot — ⬜
- [ ] Feature จริงข้าม 2 runtime (FE + BE + DB migration) ผ่าน 3 HITL gates ด้วย agent จริง

### P10: Agent Evals & Orchestrator v1 — ⬜
- [ ] แยก evals เป็น contract tests (ของเดิม) และ agent evals (`claude -p` / `codex exec` บน fixtures, กำหนด budget cap)
- [ ] Orchestrator: ปิด `auto_approve_gates` ใน API, บันทึกตัวผู้อนุมัติ, persist state, ส่ง artifact ระหว่าง stage, ใช้ worktree แยกต่อ run
- [ ] `bands.py` อ่าน `bands.yaml` + Western Electric rules

### P11: Closed-Loop Ops & Stack Skills — ⬜
- [ ] ใช้ bands กับ metric จริง (CI failure rate, 5xx, latency) และแปลง incident เป็น eval ถาวร
- [ ] Skills ต่อ stack: API design, DB migration/rollback, Redis caching/keys, frontend

### P12: Framework Packaging (optional) — ⬜
- [ ] แพ็ก core เป็น plugin/package + `framework.lock` สำหรับ runtime repo ที่แยกออกไป

---

## Known Limitations

- Command analysis เป็นแบบ best-effort: script ซ้อนหรือ obfuscation หลบได้ ด่านสุดท้ายคือ pre-commit + CI + branch protection
- กฎ deploy production จับจากข้อความ จึงมี false positive (เช่น `grep "deploy production"`)
- Codex hooks จะยังไม่รันจนกว่าจะ trust ด้วย `/hooks`; Antigravity รองรับ `hooks.json` แบบ synchronous แล้ว (`.agent/hooks.json` generated โดย `sync-adapters.py`) และควรเปิด session ใหม่เพื่อโหลด hook ล่าสุด
- Windows ที่ไม่มี Python 3.10+ จะถูก block ทุก tool call (fail-closed ตามที่ออกแบบ)
