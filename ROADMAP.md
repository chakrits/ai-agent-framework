# AI-Native SDLC Agent Framework — Roadmap (v2)

> **Architecture:** Enterprise-agnostic Canonical Core (`.agents/` + `docs/`) + Thin Multi-Harness Adapters (`.claude/`, `.codex/`, `.agent/`) + Deterministic Cross-Platform Guardrails (`scripts/sdlc_guard/`) + Optional Python Orchestrator
> **Analysis & Rationale:** [Framework Review & Roadmap v2](docs/plans/framework-review-roadmap-v2.md) · [Claude AI-Native SDLC Playbook Analysis](docs/reference-architecture/benchmarks/claude-ai-native-sdlc-playbook-analysis.md) · [Cross-Platform Plan](plan.md)
> **Last re-baseline:** 2026-11-21

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
| P7 | Agent Trace & Observability | ⬜ | Trace จากทุก platform | trace จาก Claude + Codex ผ่าน schema validation และอ้างอิง `INT-xxx` ได้ |
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
- [ ] CI บน GitLab (ยังไม่ได้ผูก remote) + ตั้ง branch protection บน `main`
- [ ] ยืนยันบน Windows จริง: Git Bash รับ path `C:\…` ใน `CLAUDE_PROJECT_DIR`, ชื่อ tool PowerShell ของ Claude, Codex `commandWindows` + การ pipe stdin ผ่าน `$input`
- [ ] ให้ `routing.yaml` เป็นแหล่งข้อมูลเดียว (แก้ปัญหา routing ใน doc กับ `router.py` ไม่ตรงกัน)

### P6: Runtime Registry & Work Records — ⬜
- [ ] `runtimes/registry.yaml` + `runtimes/<app>/runtime.yaml` (stack FE/BE/DB/Redis/API, คำสั่ง build/test/lint/run, env, ports, health)
- [ ] `AGENTS.md` แยกต่อ runtime (ไฟล์ที่ใกล้ที่สุดมีผล) + `STATUS.md` + `CHANGELOG.md` + `decisions/` (ADR แบบ MADR)
- [ ] `work/INT-xxx/` เก็บ intent / spec / plan / tasks / test-report / REVIEW + `log.md` และ `work/index.yaml`
- [ ] Validators: `validate-runtimes`, validator ของ intent / spec / review + แปลง contracts เป็น JSON Schema จริง

### P7: Agent Trace & Observability — ⬜
- [ ] Trace schema ตาม OTel GenAI (`invoke_agent`, `execute_tool`, `gate_decision`, `artifact_write`) โดยอ้างอิง `work_item` + `runtime`
- [ ] เขียน trace จาก hooks (Claude: Pre/PostToolUse, SubagentStart/Stop, Stop; Codex hooks) และให้ orchestrator ใช้ schema เดียวกัน
- [ ] ส่งออก OTel ได้ (optional) + สรุป trace ต่อ work item

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
- Codex hooks จะยังไม่รันจนกว่าจะ trust ด้วย `/hooks`; Antigravity ไม่มี tool hook จึงพึ่ง pre-commit / CI
- Windows ที่ไม่มี Python 3.10+ จะถูก block ทุก tool call (fail-closed ตามที่ออกแบบ)
