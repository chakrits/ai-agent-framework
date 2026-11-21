# คู่มือ Agent Trace (สำหรับ Human)

> **Agent trace** คือบันทึกในเครื่องว่า agent (Claude Code / Codex) *ได้รับคำสั่งอะไร ใช้ tool หรือ command อะไร ได้ output อะไร ถูก guard block เพราะอะไร* เพื่อใช้ debug และวิเคราะห์ย้อนหลัง
> Schema: [trace-event.schema.json](../contracts/trace-event.schema.json) · โค้ด: `scripts/sdlc_guard/trace*.py` · แผนต่อยอด monitoring: [agent-trace-monitoring.md](agent-trace-monitoring.md)

## 1. เก็บอะไร ที่ไหน

| หัวข้อ | รายละเอียด |
| :--- | :--- |
| ที่เก็บ | `.sdlc/traces/YYYY-MM-DD/<session_id>.jsonl` (ในเครื่อง, **gitignored**) หนึ่งบรรทัด = หนึ่ง event (JSON) |
| เวลา (`ts`) | **เวลาท้องถิ่นของเครื่อง พร้อม offset** เช่นเครื่องในกรุงเทพ (UTC+7): `2026-11-21T12:34:56.789+07:00` โฟลเดอร์รายวันใช้วันที่ท้องถิ่นเดียวกัน ตั้งเป็น UTC ได้ด้วย `SDLC_TRACE_TZ=utc` (แนะนำบน CI/server) |
| อายุ | ลบอัตโนมัติหลัง 30 วัน (ปรับได้) |
| ความปลอดภัย | redact secret (token, password, private key, Bearer, URL credential) ก่อนเขียน และตัด output ที่ยาวเกิน |
| **ไม่เก็บ** | token/cost ของ Claude (hook ไม่มีข้อมูลนี้ ดูหัวข้อ 7), effort ของ Codex (Codex hook ไม่ส่งมา) |

แต่ละ event มี: เวลา, platform (`claude`/`codex`), **model**, **effort**, session, role (agent ไหน), tool, command/ไฟล์, output, error/exit code, ระยะเวลา, `permission_mode` และผลการตัดสินของ guard

## 2. เริ่มใช้เร็ว

```bash
python3 scripts/sdlc_trace.py list                         # session ล่าสุด (มี model / effort)
python3 scripts/sdlc_trace.py show <session-prefix> --output   # timeline: command → ok/FAILED/BLOCKED + output
python3 scripts/sdlc_trace.py summary --work-item INT-001      # สรุปจำนวน tool call, block, failure, model
python3 scripts/sdlc_trace.py export --work-item INT-001 --out work/INT-001/trace-summary.md
```

Windows: ใช้ `py -3 scripts\sdlc_trace.py ...` · `export` ตัด path ของ repo/home ออก (`<repo>`, `~`) แต่ควรอ่านก่อน commit และ **อย่า commit ไฟล์ trace ดิบ**

## 3. Event ที่บันทึก

| กลุ่ม | Claude Code | Codex |
| :--- | :--- | :--- |
| Session | SessionStart (มี `model`), SessionEnd | SessionStart, SessionEnd |
| Prompt | UserPromptSubmit | UserPromptSubmit |
| Tool call | PreToolUse (+ผล guard), PostToolUse, PostToolUseFailure | PreToolUse (+ผล guard), PostToolUse |
| Subagent | SubagentStart, SubagentStop | SubagentStart, SubagentStop |
| จบ turn | Stop, **StopFailure** (rate limit / auth / billing) | Stop, Interrupt |
| Model | **PostModelSwitch** (เปลี่ยน model กลาง session) | **PostModelRequest** (status + token_usage) |
| Permission | **PermissionRequest**, **PermissionDenied** | **PermissionRequest** |
| Config | **ConfigChange** (settings/skills ถูกแก้ระหว่าง session), **InstructionsLoaded** (CLAUDE.md ที่โหลดจริง) | — |
| อื่น ๆ | PreCompact/PostCompact, Notification, TaskCreated/Completed | PreCompact/PostCompact |

ตัวหนา = เพิ่มใน v1.1 · event เสริม (Tier 2: `CwdChanged`, `UserPromptExpansion`, `PostToolBatch`, `Elicitation`, `DirectoryAdded`, `PreModelSwitch`) เปิดเองได้: `python3 scripts/sdlc_trace.py hooks list` ดูรายการ
**ไม่ trace โดยตั้งใจ:** `WorktreeCreate`/`WorktreeRemove` (hook จะไปแทนที่การทำงานของ git worktree), `MessageDisplay` (ยิงทุก streaming delta)

## 4. ระดับ log: `SDLC_TRACE_LEVEL` (มี 3 ตัวเลือก)

| ระดับ | เก็บอะไร | ใช้เมื่อ |
| :--- | :--- | :--- |
| `off` | ไม่เขียนอะไรเลย | ไม่ต้องการ trace (เช่น งานที่มีข้อมูลอ่อนไหวมาก) |
| `info` (ค่าเริ่มต้น) | event, tool, command/path, ผล guard, exit/error, ระยะเวลา, model/effort, prompt และ output **2 KB แรก** | ใช้ประจำวัน |
| `debug` | เหมือน `info` + output เต็ม **64 KB** + `tool_input` ทั้งก้อน (`input_raw`) | ตามหาสาเหตุปัญหา (ไฟล์ใหญ่ขึ้นและมีข้อมูลมากขึ้น แม้ redact แล้ว) |

## 5. ใครเปลี่ยนอะไรได้ (สำคัญ)

ลำดับความสำคัญ: **ตัวแปร env** > **ไฟล์ `.sdlc/trace.json`** (local) > ค่าเริ่มต้น `info`

| วิธีเปลี่ยน | Human | Agent | มีผลเมื่อ |
| :--- | :---: | :---: | :--- |
| ตั้ง env `SDLC_TRACE_LEVEL` ก่อนเปิด Claude/Codex | ✓ | ✗ (ตั้งให้ hook ไม่ได้) | session ถัดไป |
| `config set level debug --for 30m` (ชั่วคราว ≤120 นาที แล้วกลับเป็นค่าเดิมเอง) | ✓ | **✓** | ทันที |
| `config set level debug` / `info` (ถาวร) | ✓ | ✗ | ทันที |
| `config set level off` | ✓ | ✗ | ทันที |
| `config unset <key>`, `config set tz ...`, `config set retention_days ...` | ✓ | ✗ | ทันที |
| `hooks enable/disable <group>` (Tier 2) | ✓ | ✗ | session ถัดไป |
| `config show`, `hooks list`, `list/show/summary/export` | ✓ | ✓ | — |

คำสั่ง (รันใน terminal ของคุณเอง):

```bash
python3 scripts/sdlc_trace.py config show                       # ดูค่าที่ใช้อยู่ + ที่มา (env/config/default)
python3 scripts/sdlc_trace.py config set level debug --for 30m  # ชั่วคราว (agent เรียกได้)
python3 scripts/sdlc_trace.py config set level debug            # ถาวร (human เท่านั้น)
python3 scripts/sdlc_trace.py config set level off              # ปิด (human เท่านั้น)
python3 scripts/sdlc_trace.py config unset level                # กลับค่าเริ่มต้น
python3 scripts/sdlc_trace.py config set tz utc                 # ใช้เวลา UTC แทนเวลาเครื่อง
python3 scripts/sdlc_trace.py config set retention_days 7
```

ตั้งผ่าน env (ถาวรสำหรับ shell นั้น): macOS/Linux `export SDLC_TRACE_LEVEL=debug` · Windows PowerShell `$env:SDLC_TRACE_LEVEL="debug"` · cmd `set SDLC_TRACE_LEVEL=debug` แล้วค่อยเปิด `claude` / `codex` ใน shell เดียวกัน
**ข้อควรรู้:** ถ้าตั้ง env ไว้ env จะชนะไฟล์เสมอ (`config show` จะแจ้ง)

**ค่าที่ human ตั้งไว้ agent เปลี่ยนไม่ได้:** ถ้าไฟล์ config มีระดับที่ human ตั้ง (เช่น `off` หรือ `debug` ถาวร) คำสั่ง `config set level debug --for ...` ของ agent จะถูกปฏิเสธ จะ renew ได้เฉพาะค่าชั่วคราวที่ agent ตั้งเอง

**"Human เท่านั้น" บังคับอย่างไร:** (1) CLI ปฏิเสธถ้า stdin ไม่ใช่ terminal จริง (agent รันผ่าน tool ไม่มี TTY — ตรวจแล้วว่าใน Bash tool ของ Claude Code `stdin.isatty()` เป็น `False`; **ของ Codex ยังไม่ได้ตรวจ** จึงอาศัย guard เป็นหลัก) และ (2) guard ของ agent block คำสั่งเหล่านี้ · ทุกการเปลี่ยนค่าถูกบันทึกเป็น event `TraceConfigChange` (ก่อนมีผล) **ข้อจำกัด:** นี่เป็นเครื่องมือ audit ไม่ใช่ระบบกันแก้ไข — agent หลักยังแก้ไฟล์ `.sdlc/trace.json` หรือลบ `.sdlc/` ตรง ๆ ได้ จึงควรดู trace ร่วมกับ git history และ CI

## 6. ความเป็นส่วนตัว

- **prompt ของคุณถูกบันทึก** (หลัง redact และตัดความยาว) รวมถึง output ของคำสั่ง ถ้าไม่ต้องการให้ตั้ง `off`
- redact ครอบคลุมรูปแบบที่รู้จัก ไม่ใช่ทุกกรณี อย่าถือว่าปลอดภัยเต็มร้อย
- trace ไม่ถูก commit (อยู่ใน `.gitignore`) ส่งต่อได้เฉพาะ summary ที่ `export` แล้ว
- **`permission_mode = bypassPermissions`** ใน summary คือสัญญาณว่า session นั้นข้ามการขออนุญาต ควรตรวจสอบ

## 7. ต่อยอด: token และ cost

hook ของ Claude Code ไม่มี token/cost แต่ Claude Code ส่ง **OpenTelemetry** เองได้ (event `api_request` มี model, effort, tokens, cost) ตั้ง **ที่ shell หรือ user settings เท่านั้น** (ถูกเมินถ้าตั้งใน `.claude/settings*.json` ของโปรเจกต์):

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

จับคู่กับ trace ของเราด้วย `session_id` และ `prompt_id` (= `prompt.id` ใน OTel) · Codex มี OTel เช่นกัน (ตั้งใน `config.toml` ระดับ user) ดู [agent-trace-monitoring.md](agent-trace-monitoring.md)

## 8. แก้ปัญหา

| อาการ | สาเหตุ / วิธีแก้ |
| :--- | :--- |
| ไม่มีไฟล์ใน `.sdlc/traces/` | ระดับเป็น `off`? (`config show`) · hook ไม่ทำงาน? ลอง `python3 scripts/doctor.py` · Codex ต้อง trust hook ด้วย `/hooks` หลังไฟล์เปลี่ยน |
| `model` เป็น `unknown` | Claude ส่ง model มากับ SessionStart เท่านั้น (อาจหายหลัง `/clear`) ถ้า session เริ่มก่อนติดตั้ง trace จะไม่มีค่า → เปิด session ใหม่ |
| ไม่มี `effort` | Claude ส่งเฉพาะ event ที่เกี่ยวกับ tool และเฉพาะ model ที่รองรับ; **Codex ไม่ส่ง effort ใน hook** (ดู `effort_source`) |
| เวลาไม่ตรง | ดู offset ท้าย `ts` (`+07:00`); ถ้าใช้ `utc` จะเป็น `+00:00` · CLI เรียงตามเวลาจริงไม่ใช่ตามตัวอักษร |
| Windows: hook ไม่ทำงาน | ต้องมี Git for Windows (`sh`) และ Python 3.10+ (`py -3`); รัน `py -3 scripts\doctor.py` |
| `refused: ... is human-only` | ถูกต้อง: รันคำสั่งนั้นใน terminal ของคุณเอง ไม่ใช่ผ่าน agent |
| ไฟล์ trace ใหญ่ | ลด `retention_days` หรือกลับไป `info`; `debug` เก็บ output สูงสุด 64 KB ต่อ event |
