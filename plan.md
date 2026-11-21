---
plan_id: PLAN-005
intent_ref: N/A (Framework / Process Change)
spec_ref: docs/plans/trace-versioning-plan.md (extends the agent trace, schema v1)
owner: dev-coding-agent
status: pending_approval
---

# Implementation Plan: Trace v1.1 — model / effort, local-time timestamps, more hook events, level control, manual, monitoring

> Route: **Framework Change (High)** → ต้องได้ human approval ก่อนลงมือ และ human commit (แตะ guard / hooks / settings / contracts)
> แผนก่อนหน้า (implemented, รอ commit): [trace-versioning-plan.md](docs/plans/trace-versioning-plan.md)
> **Schema ยังเป็น `v: 1`**: เพิ่ม field แบบ optional เท่านั้น และ `ts` เป็น ISO-8601 เหมือนเดิม (เปลี่ยนแค่ offset) จึงอ่านไฟล์เก่าได้

## 0. ผล research (official docs) ที่กำหนดการออกแบบ

อ่านจาก [Claude Code hooks](https://code.claude.com/docs/en/hooks), [Claude Code monitoring](https://code.claude.com/docs/en/monitoring-usage), [Codex hooks](https://learn.chatgpt.com/docs/hooks) (อ่านครบทั้งหน้า ยกเว้นที่ระบุในหัวข้อ "ยังไม่ยืนยัน")

| ข้อค้นพบ | ผลต่อการออกแบบ |
| :--- | :--- |
| Claude: `effort` อยู่ใน payload ทุก hook ที่มี tool context เป็น **object** `{level: low\|medium\|high\|xhigh\|max}` (เฉพาะ model ที่รองรับ) | เก็บ `effort` = `level` (string) และจำค่าล่าสุดไว้ใน session state |
| Claude: field `model` มีเฉพาะ **SessionStart** (optional, หายได้หลัง `/clear`); ไม่มี `$CLAUDE_MODEL`; event **PostModelSwitch** บอก `to_model` เมื่อเปลี่ยน model (รวม auto fallback และ resume) | hook เป็น process ใหม่ทุกครั้ง จึงต้องมี **session state** `.sdlc/state/<session>.json` เก็บ model ล่าสุดจาก SessionStart / PostModelSwitch แล้วแนบให้ทุก event |
| Codex: `model` (slug) อยู่ใน stdin **ทุก event**; **ไม่มี effort ใน hook** (มีแค่ใน OTel ของ Codex) | `model` ได้ตรง ๆ, `effort` ของ Codex = ไม่มีข้อมูล (บันทึก `effort_source: "unavailable"` ไม่เดา) |
| Codex: `PostModelRequest` มี `status`, `error`, `token_usage` ต่อ request | trace token usage ของ Codex ได้จาก hook |
| Claude hooks ไม่มี token / cost แต่ **OTel ของ Claude** มี `api_request` (model, effort, tokens, cost, duration), `tool_result`, `prompt.id` | ใช้ 2 ชั้นคู่กัน: JSONL ของเรา = governance (guard decision, role, work item) / OTel = cost + tokens; join ด้วย `session_id`, `prompt_id`, `tool_use_id` |
| Claude มี **33 hook events** (เดิมเราใช้ 10) | ดูตารางเลือก event ใน §2 |
| `WorktreeCreate` "replaces default git behavior"; `MessageDisplay` ยิงทุก streaming delta (display-only) | **ห้ามใช้เป็น trace hook** (WorktreeCreate จะทำให้ worktree พัง; MessageDisplay noisy) |
| ตัวแปร `OTEL_*` ถูกเมินใน project `.claude/settings*.json` และไม่ถูกส่งต่อให้ hook | เปิด OTel ต้องตั้งที่ user settings / shell เท่านั้น (ใส่ในคู่มือ) |
| ยังไม่มีเอกสารยืนยันว่า settings `env` block ถูกส่งเข้า hook process | **ไม่พึ่ง** `env` ใน settings สำหรับ `SDLC_TRACE_LEVEL` → ใช้ไฟล์ config ของเราเอง (§3) |

## 1. Schema เพิ่ม (v1.1, ทุก field optional)

| Field | ที่มา | หมายเหตุ |
| :--- | :--- | :--- |
| `model` | Claude: SessionStart `model` / PostModelSwitch `to_model` (จำใน state) → env `ANTHROPIC_MODEL` → `"unknown"`; Codex: payload `model` | เช่น `claude-opus-5-5` |
| `model_source` | `payload` \| `state` \| `env` \| `unknown` | บอกว่าค่านี้เชื่อถือได้แค่ไหน |
| `effort` | Claude: `effort.level` (จำล่าสุดใน state); Codex: ไม่มี | เช่น `medium` |
| `effort_source` | `payload` \| `state` \| `unavailable` | |
| `prompt_id` | Claude common field `prompt_id` | join กับ OTel `prompt.id` |
| `turn_id` | Codex `turn_id` | |
| `permission_mode` | `default` \| `plan` \| `acceptEdits` \| `auto` \| `dontAsk` \| `bypassPermissions` | สำคัญต่อ audit (เห็นว่าใช้ bypass หรือไม่) |
| `mcp_server` | payload `mcp_server.name` | เฉพาะ MCP tool |
| `subagent_model` | tool `Agent` → `tool_response.resolvedModel` | model จริงของ subagent |
| `status`, `token_usage` | Codex PostModelRequest | tokens ต่อ request |
| `from_model`, `to_model`, `switch_source` | Pre/PostModelSwitch | |
| `trigger`, `notification_type`, `title` | PreCompact/PostCompact, Notification | |
| `config_source`, `file_path`, `memory_type`, `load_reason` | ConfigChange, InstructionsLoaded | |
| `task_id`, `task_subject` | TaskCreated/Completed | |
| `error_type` | StopFailure `error` (rate_limit, authentication_failed, ...) | |

`operation` เพิ่มค่า: `permission`, `config`, `model`, `compaction`, `task`, `notification` (ของเดิมคงไว้)

### 1.1 Timestamp ตามเวลาเครื่อง (UTC+7 สำหรับกรุงเทพ)
- `ts` = `datetime.now().astimezone().isoformat(timespec="milliseconds")` → เช่น `2026-11-21T12:34:56.789+07:00` (ตัว offset ทำให้ Elastic / Loki / OTel parse เป็น instant เดียวกันได้ ไม่กำกวม)
- โฟลเดอร์รายวัน `.sdlc/traces/YYYY-MM-DD/` และ retention ใช้ **วันที่ local**
- `SDLC_TRACE_TZ=local` (default) | `utc` (แนะนำสำหรับ CI / server) | ตั้งผ่าน config file ได้ด้วย (§3)
- ไฟล์เก่าที่เป็น `+00:00` ยังอ่านและเรียงได้ถูก (CLI เรียงตาม instant ไม่ใช่ string)

## 2. Hook events: เลือกอะไรมา trace

**Tier 1 (ลงทะเบียนเป็นค่าเริ่มต้น, ปริมาณต่ำ, คุณค่า audit สูง)**

| Platform | Events |
| :--- | :--- |
| Claude | เดิม: SessionStart, SessionEnd, UserPromptSubmit, PreToolUse (guard), PostToolUse, PostToolUseFailure, SubagentStart, SubagentStop, Stop. **ใหม่:** `PostModelSwitch` (model), `PermissionRequest`, `PermissionDenied`, `StopFailure` (rate limit / auth / billing / server error), `ConfigChange` (ตรวจจับการแก้ settings / skills ระหว่าง session), `InstructionsLoaded` (CLAUDE.md / rules ที่โหลดจริง), `PreCompact`, `PostCompact`, `Notification`, `TaskCreated`, `TaskCompleted` |
| Codex | เดิม: SessionStart, SessionEnd, UserPromptSubmit, PreToolUse (guard), PostToolUse, SubagentStart, SubagentStop, Stop. **ใหม่:** `PermissionRequest`, `PostModelRequest` (status + token_usage), `PreCompact`, `PostCompact`, `Interrupt` |

**Tier 2 (opt-in ผ่าน `scripts/sdlc_trace.py hooks enable <group>` เพราะ noisy หรือมีผลข้างเคียง)**
`CwdChanged`, `FileChanged` (ต้องระบุ matcher), `UserPromptExpansion` (slash command), `PostToolBatch`, `Elicitation` / `ElicitationResult`, `DirectoryAdded`, `PreModelSwitch`, Codex `PreModelRequest`

**ห้ามใช้เพื่อ trace:** `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `Setup` (ใช้เฉพาะ `--init`)

ข้อควรระวัง: hook trace ต้อง **ไม่ส่ง output / decision กลับ** (exit 0 เงียบ) เพื่อไม่ไปเปลี่ยนผลของ `PermissionRequest`, `ConfigChange`, `PreCompact` ที่ hook ตัดสินได้ · Codex จำกัด background hook ราว 8 ตัวต่อ session (ตามเอกสาร) จึงใช้ `async` เฉพาะ event ที่ถี่ และคุมจำนวน

## 3. การควบคุม `SDLC_TRACE_LEVEL` (และ config อื่น)

**ตัวเลือก level = 3:** `off` · `info` (default) · `debug`

**ลำดับความสำคัญ:** env `SDLC_TRACE_LEVEL` > ไฟล์ `.sdlc/trace.json` (local, gitignored) > default `info`

| วิธีเปลี่ยน | ใครทำได้ | มีผลเมื่อ |
| :--- | :--- | :--- |
| `export SDLC_TRACE_LEVEL=debug` ใน shell ที่เปิด Claude / Codex | **Human เท่านั้น** (agent ตั้ง env ให้ hook ไม่ได้อยู่แล้ว) | session ถัดไป |
| `python3 scripts/sdlc_trace.py config set level debug` | Human (ถาวร) | ทันที (hook อ่านไฟล์ทุกครั้ง ไม่ต้อง restart) |
| `python3 scripts/sdlc_trace.py config set level debug --for 30m` | **Human หรือ agent** (auto กลับเป็น `info` เมื่อหมดเวลา, สูงสุด 120 นาที) | ทันที |
| `python3 scripts/sdlc_trace.py config set level off` | **Human เท่านั้น** (CLI ปฏิเสธถ้า stdin ไม่ใช่ TTY และ guard block ถ้า agent พยายามรัน) | ทันที |
| `config show` / `config unset level` | ทุกคน (unset ถึงจะมีผลก็ต่อเมื่อ human เพราะเป็นการลดระดับ → ตรวจแบบเดียวกับ `off`) | — |

อื่น ๆ ใน config: `retention_days` (default 30), `tz` (`local`\|`utc`), `hooks.tier2` (กลุ่มที่เปิด)
**ข้อจำกัดที่ต้องเขียนในคู่มือ:** เป็น audit aid ไม่ใช่ระบบกันแก้ไข — agent หลักยังแก้ไฟล์ `.sdlc/trace.json` ตรง ๆ ได้ (`.sdlc/**` ป้องกันเฉพาะ role dev); การเช็ค TTY เป็น heuristic

## 4. คู่มือ (Human manual)
สร้าง `docs/guides/agent-trace-manual.md` (ภาษาไทย + ศัพท์เทคนิคอังกฤษ ตามสไตล์ repo):
1. Trace คืออะไร / เก็บอะไร / ไม่เก็บอะไร / เก็บที่ไหน
2. Quickstart (list → show → summary → export)
3. ตาราง event × field (Claude / Codex) และสิ่งที่ platform ไม่มีให้ (effort ของ Codex, token ของ Claude hooks)
4. ระดับ `off|info|debug` ทีละข้อ: เก็บอะไร ขนาด และผลต่อ privacy
5. **ใครเปลี่ยนอะไรได้ (matrix §3)** พร้อมคำสั่งของ agent ที่เรียกได้และที่ห้าม
6. Redaction, retention, timezone, privacy (prompt ถูกบันทึก), การ commit เฉพาะ summary ที่ export
7. Troubleshooting (ไม่มี trace, `unknown` model, hook ไม่ทำงานบน Windows, Codex ต้อง `/hooks` trust)
8. เปิด OTel ของ Claude / Codex เพื่อได้ token + cost (ตั้งที่ user settings เท่านั้น)

และ skill สั้น `.agents/skills/agent-trace/SKILL.md` (≤30 บรรทัด) สอน agent ว่าจะดู trace ของตัวเองอย่างไรตอน debug และเมื่อไรขอ `debug --for 30m` (ต้อง sync adapters)

## 5. Monitoring: ต่อยอดไป Grafana / Elastic / OpenSearch
สร้าง `docs/guides/agent-trace-monitoring.md` + ตัวอย่างใน `docs/guides/examples/`:

| Stack | วิธีนำเข้า (จากไฟล์ JSONL) | ตัวอย่างที่จะให้ |
| :--- | :--- | :--- |
| **Grafana Loki** | Grafana Alloy `loki.source.file` → `loki.process` (`stage.json` + `stage.timestamp`, labels เฉพาะ low-cardinality: `platform, os, operation, event, role, tool_name, model, effort`; ที่เหลือเป็น structured metadata) | `alloy.config` + LogQL panels |
| **Elastic** | Filebeat `filestream` + parser `ndjson` (`target: ""`) + `timestamp` processor จาก `ts` | `filebeat.yml` + index template (`output.stdout` เป็น `text`/ไม่ index) |
| **OpenSearch** | Fluent Bit / Filebeat-OSS / OTel Collector → index template เดียวกัน | mapping + ตัวอย่าง query |
| **OpenTelemetry Collector** (กลาง) | `filelog` receiver + `json_parser` (timestamp จาก `ts`) → OTLP ไป backend ใดก็ได้ | `otelcol.yaml` |

Panels ที่แนะนำ: tool calls ต่อเวลา แยกตาม tool / role / work_item · อัตรา block + top block reasons · failure rate · p95 `duration_ms` · sessions ตาม model / effort / platform · permission_mode = bypassPermissions · ConfigChange ระหว่าง session · Codex token usage · คำสั่งที่รันบ่อยสุด
**cost / tokens ของ Claude** มาจาก OTel ของ Claude (`api_request`) ไม่ใช่ hook → คู่มือสอน join ด้วย `session.id` / `prompt.id`
**ข้อกำหนด:** ตัวอย่าง config เหล่านี้ **ยังไม่ได้ทดสอบกับ stack จริง** (ไม่มี stack ในเครื่อง) ต้องระบุในเอกสารตรง ๆ และอ้าง docs ของแต่ละเวอร์ชัน

## 6. Files

**สร้าง:** `scripts/sdlc_guard/trace_config.py` (อ่าน/เขียน `.sdlc/trace.json`, TTL, precedence), `scripts/sdlc_guard/trace_state.py` (session state: model/effort), `docs/guides/agent-trace-manual.md`, `docs/guides/agent-trace-monitoring.md`, `docs/guides/examples/{alloy.config,filebeat.yml,otelcol.yaml,opensearch-index-template.json}`, `.agents/skills/agent-trace/SKILL.md` (+ mirror ผ่าน sync), tests ใหม่
**แก้:** `scripts/sdlc_guard/trace.py` (ts local, model/effort/ฟิลด์ใหม่, operations), `trace_cli.py` (`config`, `hooks`, เรียงตาม instant, แสดง model/effort), `commands.py` (กฎ agent: อนุญาตเฉพาะ `config show` และ `config set level debug --for ≤120m`), `scripts/sdlc_hook.py`, `.claude/settings.json`, `scripts/sync-adapters.py` (Codex events), `docs/contracts/trace-event.schema.json`, `README.md`, `CONTRIBUTING.md`, `ROADMAP.md`

## 7. Tasks

| Task | ทำอะไร | Verify |
| :--- | :--- | :--- |
| `TASK-001` | Failing tests: ts offset (`+07:00` ด้วย `TZ=Asia/Bangkok`), model/effort จาก state, event ใหม่ทุกตัว, config precedence + TTL, guard rule ของ agent, TTY check | fail ตามคาด |
| `TASK-002` | `trace_state.py` + model/effort ใน `build_event` + ฟิลด์ใหม่ต่อ event | tests ผ่าน; payload จริงของ Claude ได้ `model`/`effort` |
| `TASK-003` | `ts` ตามเวลาเครื่อง + `SDLC_TRACE_TZ`; โฟลเดอร์วัน / retention แบบ local; CLI เรียงตาม instant | test ด้วย `TZ=Asia/Bangkok` และ `UTC` |
| `TASK-004` | `trace_config.py` + CLI `config show/set/unset` + `--for` TTL + TTY guard | tests ผ่านบน 3 OS |
| `TASK-005` | guard: agent เรียก `config show` และ `config set level debug --for ≤120m` ได้; ห้าม `off`/ถาวร/`unset` | fixtures ผ่าน |
| `TASK-006` | Tier 1 hooks ใน `.claude/settings.json` + Codex generator; CLI `hooks enable/disable/list` สำหรับ Tier 2 (generate เข้า settings **local** ของผู้ใช้) | parity check ผ่าน; ไม่มี hook ที่ส่ง output |
| `TASK-007` | Schema + `validate_event` อัปเดต, test sync กับ schema | tests ผ่าน |
| `TASK-008` | คู่มือ + monitoring guide + ตัวอย่าง config + skill + README/CONTRIBUTING | link-check; context-budget ผ่าน |
| `TASK-009` | CI: ทดสอบ tz + config บน 3 OS | CI เขียว |
| `TASK-010` | ROADMAP (P7) | — |

## 8. ยังไม่ยืนยัน / ความเสี่ยง
- `effort` มาเฉพาะ event ที่มี tool context และเฉพาะ model ที่รองรับ → บาง event จะว่าง (ใช้ค่าล่าสุดจาก state และติดป้าย `effort_source`)
- ไม่มีเอกสารยืนยันว่า settings `env` ถูกส่งเข้า hook; Claude `tool_response` ของ Edit / Read ไม่มีเอกสาร; Codex `tool_response`, exit code, `token_usage` sub-fields และ effort ใน hook ไม่มีเอกสาร
- `SessionStart` อาจไม่มี `model` (เช่น หลัง `/clear`) → ใช้ค่าล่าสุดจาก state
- ตัวอย่าง config ของ Grafana / Elastic / OpenSearch / OTel Collector ยังไม่ได้ทดสอบกับ stack จริง
- Windows: การ lock และ TTY check ต้องรอ CI; Codex ต้อง `/hooks` trust ใหม่หลังไฟล์เปลี่ยน
- Hook ที่ถี่ขึ้น = Python spawn มากขึ้น (≈50–100 ms ต่อครั้ง; ส่วนใหญ่ `async`); วัด overhead ใน TASK-009

## 9. Rollback
ปิดทั้งหมดได้ด้วย `SDLC_TRACE_LEVEL=off`; Tier 2 ปิดด้วย `hooks disable`; ทุกอย่างอยู่ใน commit แยก revert ได้
