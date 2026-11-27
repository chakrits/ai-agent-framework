# Framework Structure Review & Roadmap v2

- **Document ID:** `PLAN-SDLC-002` (ข้อเสนอ — ยังไม่ได้แทนที่ [ROADMAP.md](../../ROADMAP.md))
- **Date:** 2026-11-21
- **Scope:** วิเคราะห์โครงสร้าง Framework ปัจจุบันเทียบกับเป้าหมาย "กฎระเบียบ + การควบคุมทิศทาง + บันทึกการทำงาน (runtime records & agent trace)" สำหรับ **หลาย runtime application** (FE / BE / DB / Redis / APIs) บน **หลาย agent platform** (Claude Code, Codex, Antigravity)
- **Method:** อ่าน source code ทั้งหมดใน repo, รัน validators/tests/evals จริง, probe hook ด้วย payload จริง, และเทียบกับเอกสาร official/community (แหล่งอ้างอิงท้ายเอกสาร)
- **Route classification:** เอกสารนี้เป็น *Framework / Process Change* (High) ตาม [core-bootloader.md](../workflow/core-bootloader.md) → ต้องผ่าน Gate 2/3 โดย human maintainer ก่อนนำไปแก้ `ROADMAP.md`

---

## 0. Executive Summary

Framework นี้ **วางแนวคิดถูกทาง** (Canonical core + thin adapters, Spec-driven artifacts, Dynamic routing, Advisory vs Deterministic, HITL gates, Stage 6 closed loop) และสอดคล้องกับ Claude AI-Native SDLC Playbook, OpenAI Harness Engineering และ Spec-Kit

แต่สถานะจริงคือ **"Scaffolded" ไม่ใช่ "Done"**: ทุก Phase ใน ROADMAP ถูกติ๊ก `[x]` ขณะที่ (1) repo ยังไม่มี commit เลย → CI ไม่เคยรัน, (2) guardrail ที่เป็น deterministic ที่สำคัญที่สุด **ไม่ทำงานจริงใน hook mode**, (3) evals ไม่ได้ทดสอบ agent จริง, และ (4) **ยังไม่มีโครงสร้างรองรับเป้าหมายหลัก 2 ข้อ** คือ *หลาย runtime application* และ *บันทึกการทำงาน (runtime status / task log / changelog / ADR / agent trace)*

---

## 1. สิ่งที่ตรวจสอบแล้ว (Evidence Log)

| # | สิ่งที่ทดสอบ | ผลลัพธ์ | หลักฐาน |
| :-: | :--- | :--- | :--- |
| E1 | `sync-adapters --check`, `validate-context-budget`, `validate-contracts --check-defaults`, `unittest` (13 tests), `run_evals` (3 cases) | ผ่านทั้งหมด | รันในเครื่อง 2026-11-21 |
| E2 | Hook payload `{"tool_name":"Bash","tool_input":{"command":"./deploy.sh production"}}` | **exit 0 (ไม่ block)** | `scripts/guard-protected-paths.sh` |
| E3 | Hook payload `git push -f origin main` | **exit 0 (ไม่ block)** | เดียวกัน |
| E4 | `--check-cmd "./deploy.sh production"` (direct mode) | exit 2 (block) | unit test ทดสอบเฉพาะโหมดนี้ |
| E5 | `printf 'Bash\t\tgit push -f\n' \| IFS=$'\t' read a b c` | `[Bash][git push -f][]` — tab ติดกันถูกยุบ, command ไหลไปอยู่ตัวแปร path | [guard-protected-paths.sh:78](../../scripts/guard-protected-paths.sh:78) |
| E6 | Dev agent แก้ `tests/test_login.py` | exit 0 (ไม่ block test oracle) | pattern ครอบคลุมแค่ `*test-report*`/`*test_cases*` |
| E7 | `SDLC_ACTIVE_ROLE` ถูก set ที่ไหน | มีแค่ใน unit test → role guard เป็น dead code ใน Claude Code จริง | [guard-protected-paths.sh:12](../../scripts/guard-protected-paths.sh:12), `tests/test_phase3_harness.py:73` |
| E8 | `bands.py` โหลด `bands.yaml` หรือไม่ | ไม่โหลด; tier hardcode, ไม่มี Western Electric rules | [bands.py:45](../../orchestrator/telemetry/bands.py:45) |
| E9 | Bug Fix Low/Med route | Doc: Dev repro → QA verify; Code: QA `reproduce_oracle` → Dev | [dynamic-routing.md:10](../workflow/dynamic-routing.md:10) vs [router.py:126](../../orchestrator/core/router.py:126) |
| E10 | Evals ทดสอบอะไร | ตรวจ `sample_output` ที่ฝังไว้ใน dataset เอง → ผ่านเสมอไม่ว่า agent จะเปลี่ยนอย่างไร | [run_evals.py:33](../../evals/run_evals.py:33) |
| E11 | HITL bypass | HTTP API รับ `auto_approve_gates`; approve ไม่บันทึกตัวตนผู้อนุมัติ; runs อยู่ใน in-memory dict | [main.py:34](../../orchestrator/api/main.py:34), [handlers.py:24](../../orchestrator/api/handlers.py:24) |
| E12 | ส่งต่อ artifact ระหว่าง stage | context มีแค่ "stage X success=True" ไม่มี path/เนื้อหา artifact | [sdlc_pipeline.py:187](../../orchestrator/graphs/sdlc_pipeline.py:187) |
| E13 | ADR / CHANGELOG / runtime registry | ไม่มีโฟลเดอร์/ไฟล์ใด ๆ (มีแค่ ID pattern `ADR-xxx` ใน spec schema) | `grep` ทั้ง `docs/ .agents/` |
| E14 | Contract validator ครอบคลุม | ตรวจจริงแค่ `tasks.json` + test report; `intent`/`spec`/`REVIEW` ยังไม่มี validator; YAML "schema" ไม่ใช่ JSON Schema จริง | [validate-contracts.py](../../scripts/validate-contracts.py) |
| E15 | Git history | `main` ยังไม่มี commit → CI ไม่เคยรัน, ไม่มี pilot artifact (INT/SPEC instance) | `git log` |

---

## 2. Pros (จุดแข็ง)

1. **Canonical core + thin adapters** — ลด dual-truth ของ prompt; มี parity check ที่ทำงานจริง (E1). สอดคล้องกับ AGENTS.md open standard และ Agent Skills open standard (SKILL.md) ที่ทั้ง Claude, Codex, Antigravity รองรับ
2. **AGENTS.md เป็น "map" สั้น** (31 บรรทัด) + context budget validator — ตรงกับบทเรียน OpenAI Harness Engineering ที่ให้ AGENTS.md เป็นสารบัญ ~100 บรรทัด ไม่ใช่สารานุกรม
3. **Dynamic risk-based routing** + keyword escalation — ไม่บังคับ ceremony เต็มกับงานเล็ก (จุดที่ Playbook ไม่ได้ระบุชัด)
4. **Traceability ID chain** (`INT→URD→FS→TC→TASK→PR/REV`) และ `tasks.json` ที่ `passes` ต้องมี `evidence` — machine-verifiable
5. **แยก Advisory vs Deterministic ชัดในเชิงแนวคิด** (constitution, hooks, CI) และแยก Separation of Duties (dev ≠ QA oracle ≠ approver)
6. **Project Pack pattern** แยก domain (EBMC) ออกจาก core
7. **Orchestrator stdlib-only** — `AgentExecutor` Protocol ทำให้สลับ DryRun / CLI harness (`claude -p`, `codex exec`) ได้, มี HITL pause/resume, parallel review, retry
8. **Stage 6 closed loop** ออกแบบ deterministic detection → draft `intent.md` (ไม่ให้ LLM ตัดสิน anomaly)
9. **CI parity GitHub + GitLab** ใช้คำสั่งเดียวกัน

## 3. Cons (จุดอ่อน / ความเสี่ยง) — เรียงตามความรุนแรง

### Critical
- **C1. Guardrail ไม่ guard จริง (E2–E5):** bug `IFS=$'\t'` ยุบ tab ว่าง → Bash command ไม่ถูกตรวจใน hook mode เลย (deploy production, force push ผ่านหมด). Tests ครอบคลุมเฉพาะ `--check-cmd` จึงไม่เห็น
- **C2. Role-based guard เป็น dead code (E7):** ไม่มีอะไร set `SDLC_ACTIVE_ROLE`. Claude Code ส่ง `agent_type`/`agent_id` มาใน hook input อยู่แล้วเมื่อ hook fire ใน subagent — ควรอ่านจาก payload
- **C3. Test-oracle lock ไม่ครอบคลุม test files จริง (E6)** — ขัด Playbook Play 8 ที่ให้ hook ห้ามแก้ test ระหว่าง bug fix
- **C4. Roadmap รายงานสถานะเกินจริง (E15):** ทุก phase `[x]` แต่ไม่มี commit, CI ไม่เคยรัน, milestone "E2E pilot ผ่าน 3 gates" ไม่มี artifact รองรับ

### High
- **C5. ไม่มีแนวคิด "Runtime Application"** — ไม่มี registry/manifest ต่อ runtime (stack FE/BE/DB/Redis, คำสั่ง build/test/lint เดียว, env, ports, dependencies, owners). Project pack อยู่ใต้ `examples/` จึงไม่ใช่ที่วาง runtime จริง
- **C6. ไม่มีที่เก็บ "บันทึกการทำงาน" (E13):** templates มี แต่ไม่มีที่วาง *instance* ของ intent/spec/plan/review ต่อ feature; ไม่มี ADR log, changelog, runtime status, task log
- **C7. Agent trace ไม่มีจริงใน interactive sessions:** telemetry เกิดเฉพาะ orchestrator dry-run และถูก gitignore (`.sdlc-telemetry/`); session ของ Claude/Codex/Antigravity ไม่ถูกบันทึกเลย; schema event ไม่อิงมาตรฐาน (OTel GenAI)
- **C8. Enforcement เป็น Claude-only:** `.codex/` มีแค่ README ทั้งที่ Codex รองรับ `PreToolUse` hooks ผ่าน `.codex/hooks.json`/`config.toml` แล้ว; Antigravity ไม่มี deterministic hook → ต้องพึ่ง git pre-commit/CI
- **C9. HITL bypass ได้ผ่าน API (E11)** และ approval ไม่มี identity/audit; state หายเมื่อ restart (ไม่ใช่ "stateless" จริง แต่เป็น in-memory stateful)
- **C10. Evals เป็น self-fulfilling (E10)** — ไม่ได้รัน agent จริง จึงจับ regression ของ prompt/skill/model ไม่ได้ (Playbook Play 9)

### Medium
- **C11. Dual-truth ระหว่าง doc กับ code (E9)**: routing matrix อยู่ทั้งใน `dynamic-routing.md` และ `router.py` (hardcode) — ขัดหลัก "Zero Dual-Truth"; `bands.yaml` ก็ไม่ถูกอ่าน (E8)
- **C12. Adapter redundancy:** Antigravity ปัจจุบันอ่าน `.agents/rules/` และ `AGENTS.md` โดยตรง (`.agent/` เป็น legacy); Codex อ่าน `.agents/skills` เอง → mirror `.agent/` (3 ชุดซ้ำ) อาจไม่จำเป็น เหลือ mirror ให้ Claude อย่างเดียว
- **C13. Contract validator ไม่ครบ (E14)**; YAML schema เป็น custom format ไม่ใช่ JSON Schema จริง จึงใช้ tooling มาตรฐานไม่ได้
- **C14. Pre-commit ไม่ตรวจ staged diff** — รันแค่ validators ไม่ได้ตรวจว่าไฟล์ protected/test ถูกแก้ใน commit
- **C15. Orchestrator ไม่ส่ง artifact ระหว่าง stage (E12)**, `CliHarnessExecutor` ส่ง prompt เป็น argv (เสี่ยง ARG_MAX), ไม่มี worktree isolation ต่อ run
- **C16. Reference architecture `01.`–`09.` เป็นโฟลเดอร์ว่าง** (มีแค่ `.DS_Store` + 1 ไฟล์) — เพิ่ม noise ให้ agent ค้นหา
- **C17. Agents/skills สั้นมาก (13–32 บรรทัด)** — เป็น checklist มากกว่า institutional knowledge; ยังไม่มี skill ต่อ stack (API design, DB migration, Redis/caching, frontend)

---

## 4. Target Architecture (โครงสร้างที่เสนอ)

### 4.1 Decision: Framework กับ Runtime อยู่ที่ไหน

| Option | คำอธิบาย | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **A. Monorepo `runtimes/`** (แนะนำเริ่มต้น) | framework + หลาย runtime อยู่ repo เดียว | trace/ADR/changelog ข้ามระบบที่เดียว, nested AGENTS.md ทำงานได้ทันที | repo ใหญ่, CI ต้อง scope ตาม path |
| B. Framework เป็น package/plugin/submodule | runtime repo แยก ดึง framework เวอร์ชันที่ pin | แยกสิทธิ์/วงจร release | ต้องมี installer + version pinning + sync ข้าม repo |

**ข้อเสนอ:** เริ่มด้วย **A** แต่ออกแบบ `framework/` core ให้ "แพ็กได้" (versioned, มี `framework.lock`) เพื่อย้ายไป **B** ได้ภายหลัง

### 4.2 Directory Layout ที่เสนอ

```text
AGENTS.md                         # map ≤100 บรรทัด (ทุก platform อ่าน)
CLAUDE.md / GEMINI.md             # pointer → AGENTS.md (+ platform notes)
.agents/                          # canonical (Codex skills + Antigravity rules/workflows อ่านตรง)
  agents/  skills/  workflows/  rules/
.claude/                          # generated: agents/, skills/, settings.json (hooks)
.codex/                           # generated: config.toml / hooks.json (PreToolUse → guard เดียวกัน)
governance/                       # (ย้ายจาก docs/operating-model) constitution, bands.yaml, policies
  routing.yaml                    # ★ single source ของ routing matrix (doc + router.py generate/อ่านจากนี้)
contracts/  templates/            # JSON Schema จริง (draft 2020-12) ทุก artifact
runtimes/                         # ★ ใหม่: 1 โฟลเดอร์ต่อ runtime application
  registry.yaml                   # รายการ runtime + owner + dependency graph
  <app-name>/
    runtime.yaml                  # stack, components(fe/be/db/redis/api), commands(build/test/lint/run), envs, ports, health
    AGENTS.md                     # nested rules เฉพาะ runtime (closest-wins)
    STATUS.md                     # runtime status (generated จาก trace + CI)
    CHANGELOG.md                  # Keep-a-Changelog, generate จาก conventional commits
    decisions/                    # ADR (MADR) เฉพาะ runtime
    contracts/                    # OpenAPI / DB schema / Redis key conventions
work/                             # ★ ใหม่: instance ของ artifacts ต่อ work item
  INT-123-<slug>/
    intent.md spec.md plan.md tasks.json test-report.md REVIEW.md
    log.md                        # task log / decision log (append-only)
  index.yaml                      # สถานะทุก work item (generated)
docs/decisions/                   # ADR ระดับ framework/cross-runtime
traces/                           # ★ agent trace (JSONL, schema อิง OTel GenAI) — commit summary, raw ไป OTel backend
scripts/ hooks/ evals/ orchestrator/
```

### 4.3 Record Model (บันทึกการทำงาน)

| Record | เก็บที่ | ผู้เขียน | วิธีบังคับ |
| :--- | :--- | :--- | :--- |
| Intent/Spec/Plan/Review | `work/INT-xxx/` | agent ตาม stage | schema validator + CI |
| Task log / decision log | `work/INT-xxx/log.md`, `tasks.json` | dev agent | hook `PostToolUse`/`Stop` append |
| ADR | `runtimes/<app>/decisions/`, `docs/decisions/` | SA agent | review gate: spec ที่มี breaking change ต้องอ้าง `ADR-xxx` |
| Changelog | `runtimes/<app>/CHANGELOG.md` | generated | conventional commits + CI check |
| Runtime status | `runtimes/<app>/STATUS.md` | generated | script รวม CI + health + bands |
| Agent trace | `traces/YYYY/MM/<run_id>.jsonl` + OTel exporter | hooks / orchestrator | schema validator |

**Agent trace schema (ขั้นต่ำ):** `trace_id, span_id, parent_span_id, ts, platform(claude|codex|antigravity|orchestrator), session_id, agent_type, operation(invoke_agent|execute_tool|gate_decision|artifact_write), tool_name, target_path, work_item(INT-xxx), runtime, outcome, blocked_reason, tokens_in/out, cost, approver` — ชื่อ operation อิง OTel GenAI (`invoke_agent`, `execute_tool`); Claude Code มี native OTel export (`CLAUDE_CODE_ENABLE_TELEMETRY`) ใช้เสริมได้

### 4.4 Multi-Platform Enforcement Matrix

| Control | Claude Code | Codex | Antigravity | ทุก platform (fallback) |
| :--- | :--- | :--- | :--- | :--- |
| Instructions | `CLAUDE.md` → `AGENTS.md` | `AGENTS.md` (nested) | `AGENTS.md` / `.agents/rules` | — |
| Skills | `.claude/skills` (mirror) | `.agents/skills` (native) | ตรวจสอบ path (ดู §8) | — |
| Pre-tool guard | `PreToolUse` hook (+ `agent_type`) | `.codex/hooks.json` PreToolUse | ไม่มี (ณ ที่ตรวจ) | **git pre-commit (staged diff) + CI + branch protection** |
| Trace | hooks + native OTel | hooks | git/CI-derived | orchestrator tracker |

หลักการ: **guard script เดียว** (`hooks/guard.py`) รับ payload ได้หลายรูปแบบผ่าน adapter เล็ก ๆ; ชั้นสุดท้ายที่บังคับได้ทุก platform คือ pre-commit + CI + branch protection

---

## 5. แผนปรับปรุงแก้ไข (Remediation Plan)

| ID | แก้อะไร | ไฟล์ | Exit criteria (วัดได้) |
| :--- | :--- | :--- | :--- |
| R1 | เขียน guard ใหม่เป็น Python (parse JSON ตรง, ไม่ใช้ IFS) | `scripts/guard-protected-paths.sh` → `hooks/guard.py` | unit test ส่ง **hook payload** จริง: `git push -f`, `deploy production`, `cat .env` → exit 2 |
| R2 | อ่าน role จาก `agent_type` ใน payload (fallback env) | guard | test: payload `agent_type=dev-coding-agent` แก้ `tests/**` ระหว่าง bug-fix → exit 2 |
| R3 | ขยาย test-oracle patterns (`tests/**`, `**/*.spec.*`, `**/*_test.*`, `robot/**`) ตั้งค่าได้ต่อ runtime | guard + `runtime.yaml` | test ครอบทุก pattern |
| R4 | matcher ครบ `Edit\|Write\|MultiEdit\|NotebookEdit\|Bash` | `.claude/settings.json` | parity test |
| R5 | pre-commit ตรวจ staged diff เทียบ protected paths | `.githooks/pre-commit` | test ด้วย temp repo |
| R6 | Codex hook adapter → guard เดียวกัน | `.codex/hooks.json` (generated) | sync-adapters สร้าง + parity check |
| R7 | `routing.yaml` เป็น single source; `router.py` อ่าน, doc generate | `governance/routing.yaml` | test: doc ↔ yaml ↔ router ไม่ drift (แก้ E9) |
| R8 | `bands.py` อ่าน `bands.yaml` จริง + Western Electric rules 1–4 | telemetry | test ต่อ rule |
| R9 | ปิด `auto_approve_gates` ใน API (CLI dry-run เท่านั้น), approval ต้องมี `approver`, persist state เป็นไฟล์/SQLite | orchestrator api | test: API ปฏิเสธ auto-approve; restart แล้ว resume ได้ |
| R10 | ส่ง artifact paths/digest ระหว่าง stage; prompt ผ่าน stdin/file | pipeline | test pipeline อ่าน output stage ก่อน |
| R11 | แปลง contracts เป็น JSON Schema จริง + validator intent/spec/review (frontmatter + sections) | `contracts/` | `check-jsonschema` ผ่าน; negative fixtures fail |
| R12 | Evals 2 ชั้น: (a) structural (ของเดิม, เปลี่ยนชื่อเป็น contract tests) (b) **agent evals** รัน `claude -p` / `codex exec` บน fixtures แล้ว grade ด้วย validator (scheduled/manual, มี budget cap) | `evals/` | อย่างน้อย 10 เคสจริง, รายงาน pass-rate ต่อ model |
| R13 | ลด mirror `.agent/` (ตรวจ Antigravity version ก่อน) | adapters | Antigravity โหลด rules/skills จาก `.agents/` ได้ (manual verification log) |
| R14 | ลบโฟลเดอร์ reference ว่าง หรือย้ายเป็น `docs/reference/` ที่มีเนื้อหาจริง | docs | ไม่มีโฟลเดอร์ว่าง |
| R15 | Re-baseline ROADMAP ด้วยสถานะ *Scaffolded / Verified / Missing* และ commit แรก + เปิด CI | `ROADMAP.md` | CI เขียวบน remote อย่างน้อย 1 ครั้ง |

---

## 6. Roadmap ฉบับปรับปรุง (v2)

> สถานะ: **Verified** = มี test/CI รันผ่านบน remote · **Scaffolded** = มีไฟล์/โค้ดแต่ยังไม่พิสูจน์ · **Missing** = ยังไม่มี

### Re-baseline ของเดิม

| Phase เดิม | สถานะจริง | เหตุผล |
| :--- | :--- | :--- |
| P0 Foundation & Governance | Scaffolded | ไฟล์ครบ แต่ไม่มี commit; reference folders ว่าง |
| P1 Artifact Spine | Scaffolded | schema ครบ, validator ครอบแค่ 2/5 artifact |
| P2 Agents/Skills/Adapters | Scaffolded | parity ผ่าน; ไม่มี E2E pilot |
| P3 Harness/Hooks/Evals | **Scaffolded (มี defect)** | C1–C3, C10 |
| P4 Orchestrator & Stage 6 | Scaffolded | dry-run only; bands.yaml ไม่ถูกอ่าน; HITL bypass |

### Phase ใหม่

| Phase | ชื่อ | ระยะ | เป้าหมาย | Exit criteria |
| :--- | :--- | :--- | :--- | :--- |
| **P5** | **Hardening & Truth Baseline** | 1–2 สัปดาห์ | R1–R5, R7, R15 | guard tests ผ่านด้วย payload จริง; commit แรก + CI เขียวบน GitHub & GitLab; ROADMAP แสดงสถานะจริง |
| **P6** | **Runtime Registry & Work Records** | 2 สัปดาห์ | `runtimes/` + `runtime.yaml` schema + nested AGENTS.md; `work/INT-xxx/` + `index.yaml`; ADR (MADR) + CHANGELOG + STATUS generator | runtime ตัวอย่าง 2 ตัว (เช่น `web-frontend`, `core-api` + Postgres + Redis) ผ่าน `validate-runtimes`; work item ตัวอย่าง 1 ชุดผ่าน validator ครบ 5 artifact |
| **P7** | **Agent Trace & Observability** | 2 สัปดาห์ | trace schema (OTel GenAI aligned), Claude hooks (`PreToolUse/PostToolUse/SubagentStart/SubagentStop/Stop`) + Codex hooks เขียน trace, orchestrator ใช้ schema เดียวกัน, optional OTel exporter | 1 session ต่อ platform (Claude, Codex) สร้าง trace ที่ validate ผ่าน และ link ไป `INT-xxx` + runtime; มีรายงานสรุปต่อ work item |
| **P8** | **Multi-Platform Parity** | 1–2 สัปดาห์ | R6, R13, `GEMINI.md`, platform capability matrix ที่ทดสอบจริง | parity check ครอบ Codex hooks; verification log ต่อ platform/เวอร์ชัน |
| **P9** | **Real E2E Pilot** | 2 สัปดาห์ | รัน 1 feature จริงข้าม 2 runtime (FE+BE+DB migration) ผ่าน 3 HITL gates ด้วย agent จริง | artifacts ครบใน `work/`, ADR 1 ฉบับ, CHANGELOG อัปเดต, trace ครบ, PR merge ผ่าน branch protection |
| **P10** | **Agent Evals & Orchestrator v1** | 2–3 สัปดาห์ | R8–R12: real agent evals, persistent state, artifact handoff, worktree ต่อ run | eval ≥10 เคสรันตาม schedule; orchestrator resume หลัง restart; approval มี identity |
| **P11** | **Closed-Loop Ops & Stack Skills** | ต่อเนื่อง | bands จาก metric จริง (CI, 5xx, latency), incident → eval ถาวร; skills ต่อ stack (API design, DB migration/rollback, Redis caching/keys, frontend) | breach จริง 1 ครั้งสร้าง draft intent อัตโนมัติ; skill ใหม่แต่ละตัวมี eval |
| P12 (option) | Framework Packaging | ตามต้องการ | แพ็ก core เป็น plugin/package + `framework.lock` สำหรับ runtime repo แยก (Option B) | runtime repo ภายนอก 1 ตัว install & ผ่าน CI |

**ลำดับความสำคัญ:** P5 ก่อนเสมอ (guardrail ที่ไม่ทำงานอันตรายกว่าการไม่มี เพราะสร้างความมั่นใจผิด ๆ) → P6/P7 ตอบโจทย์หลักของผู้ใช้ → P9 พิสูจน์ทั้งระบบ

---

## 7. Design Principles ที่ควรเพิ่มใน Constitution

1. **Every rule has an enforcer and a test** — rule ที่ไม่มี hook/CI ให้ระบุเป็น *advisory* ชัดเจน
2. **Single source per fact** — routing, bands, protected paths, runtime commands อยู่ใน YAML เดียว; doc/code อ่านหรือ generate จากมัน
3. **Records are append-only and linked** — ทุก trace/log ต้องมี `work_item` + `runtime`
4. **Lowest common denominator enforcement** — platform ที่ไม่มี hook ต้องถูกจับได้ที่ pre-commit/CI/branch protection
5. **Status claims require evidence** — roadmap `[x]` ต้องอ้าง CI run หรือ artifact

---

## 8. ยังไม่ได้ยืนยัน (Not Yet Verified)

- Path ของ workspace **skills** ใน Antigravity (`.agents/skills` vs `.agent/skills`) — หน้า official rules ไม่ระบุ; community sources ขัดกัน
- หน้า Codex skills official redirect ไป host อื่น ยังไม่ได้อ่านฉบับเต็ม (ข้อมูล `.agents/skills` มาจาก search snippet ของ developers.openai.com)
- ตำแหน่ง `specs/` ของ Spec-Kit (root vs `.specify/specs/`) แหล่งข้อมูลขัดกัน
- `agent_id` presence rule ใน Claude Code hooks — docs ระบุชัดเฉพาะ `agent_type` (ใน subagent หรือ `--agent`)
- Antigravity มี deterministic pre-tool hook หรือไม่ — ไม่พบในเอกสารที่ตรวจ

---

## 9. แหล่งอ้างอิง

- Claude AI-Native SDLC Playbook — https://claude.com/resources/articles/the-ai-native-sdlc-playbook (วิเคราะห์ใน [benchmark doc](../knowledge/benchmarks/claude-ai-native-sdlc-playbook-analysis.md))
- Claude Code Hooks reference — https://code.claude.com/docs/en/hooks
- Claude Code Monitoring (OpenTelemetry) — https://code.claude.com/docs/en/monitoring-usage
- Codex AGENTS.md guide — https://developers.openai.com/codex/guides/agents-md
- Codex Skills — https://developers.openai.com/codex/skills
- Codex Advanced Configuration (hooks) — https://developers.openai.com/codex/config-advanced
- OpenAI Harness Engineering — https://openai.com/index/harness-engineering/
- Codex ExecPlans (PLANS.md) — https://developers.openai.com/cookbook/articles/codex_exec_plans
- Antigravity Rules — https://antigravity.google/docs/rules
- Antigravity Skills codelab — https://codelabs.developers.google.com/getting-started-with-antigravity-skills
- Agent Skills specification — https://agentskills.io/specification
- OpenTelemetry GenAI agent spans — https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
- GitHub Spec Kit — https://github.com/github/spec-kit ; Microsoft blog https://developer.microsoft.com/blog/spec-driven-development-spec-kit/
- MADR — https://adr.github.io/madr ; https://github.com/adr/madr
