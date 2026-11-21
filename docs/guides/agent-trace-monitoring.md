# ต่อยอด Agent Trace ไปยัง Monitoring (Grafana / Elastic / OpenSearch / OpenTelemetry)

> ไฟล์ trace เป็น **JSONL หนึ่งบรรทัดต่อหนึ่ง event** มี `ts` เป็นเวลาท้องถิ่นพร้อม offset (เช่น `+07:00`) จึงให้ agent ของ log shipper อ่านต่อได้ตรง ๆ โดยไม่ต้องแปลงรูปแบบ
> รู้จักข้อมูลก่อน: [agent-trace-manual.md](agent-trace-manual.md) · Schema: [trace-event.schema.json](../contracts/trace-event.schema.json)
>
> **สถานะ: ตัวอย่าง config ทุกไฟล์ใน [examples/](examples/) ยังไม่ได้ทดสอบกับ stack จริง** (ไม่มี Grafana/Elastic/OpenSearch ในสภาพแวดล้อมที่เขียน) ไฟล์ JSON ผ่านการตรวจ syntax เท่านั้น ให้ตรวจชื่อ option กับเอกสารของเวอร์ชันที่ใช้ก่อนนำไปใช้จริง

## 1. ภาพรวม: ข้อมูลสองชั้นที่ใช้คู่กัน

| ชั้น | แหล่ง | มีอะไร | ไม่มีอะไร |
| :--- | :--- | :--- | :--- |
| **Governance trace** (ของ framework นี้) | hooks → `.sdlc/traces/*.jsonl` | command/output, **ผล guard (blocked + เหตุผล)**, role, work item, permission_mode, ConfigChange, model/effort | token และ cost ของ Claude |
| **Native OpenTelemetry** (ของ Claude Code / Codex เอง) | ส่งตรงไป OTLP endpoint | token, **cost**, ระยะเวลา API, model, effort, tool result | ผล guard ของเรา, role, work item |

เชื่อมสองชั้นด้วย **`session_id`** และ **`prompt_id`** (Claude OTel เรียก `prompt.id`) และ `tool_use_id` แล้วจึงตอบคำถามเช่น "งาน INT-001 ใช้ cost เท่าไรและถูก guard block กี่ครั้ง"
ตั้ง OTel ที่ shell/user settings เท่านั้น (ดูวิธีใน [คู่มือ §7](agent-trace-manual.md)) · เปิด `OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_TOOL_DETAILS` เฉพาะเมื่อยอมรับเรื่อง privacy และควรลบ attribute `prompt` ที่ Collector

## 2. เลือกเส้นทางนำเข้า

| ต้องการ | เลือก | ไฟล์ตัวอย่าง |
| :--- | :--- | :--- |
| Dashboard + ค้น log ด้วย Grafana | **Grafana Alloy → Loki** | [alloy.config](examples/alloy.config) |
| ค้นข้อความ/วิเคราะห์ด้วย Kibana | **Filebeat → Elasticsearch** | [filebeat.yml](examples/filebeat.yml) + [index template](examples/opensearch-index-template.json) |
| OpenSearch / OpenSearch Dashboards | Filebeat OSS, Fluent Bit หรือ Data Prepper | [index template](examples/opensearch-index-template.json) |
| กลาง ไม่ผูก vendor / ส่งต่อหลาย backend | **OpenTelemetry Collector** (`filelog` receiver) | [otelcol.yaml](examples/otelcol.yaml) |

## 3. ข้อควรออกแบบก่อนนำเข้า

1. **เวลา:** `ts` มี offset จึงถูกแปลงเป็น instant เดียวกันได้ ไม่ต้องกังวลถ้าทีมอยู่คนละ timezone · เครื่อง CI/server ควรตั้ง `SDLC_TRACE_TZ=utc`
2. **ตั้ง label/field ให้ถูก:** ใน Loki ให้เป็น label เฉพาะค่าที่มีจำนวนน้อย (`platform, os, operation, event, role, tool_name, model, effort`) ส่วน `session_id`, `work_item`, `prompt_id`, command เก็บในเนื้อ log หรือ structured metadata ไม่งั้น cardinality ระเบิด · ใน Elastic/OpenSearch ใช้ template (`dynamic: false` กัน mapping บวม)
3. **ฟิลด์ใหญ่:** `output.stdout/stderr` (สูงสุด 2 KB ที่ `info`, 64 KB ที่ `debug`) ควรเป็น `text` ไม่ใช่ `keyword`; `input_raw` (เฉพาะ `debug`) ไม่ต้อง index
4. **ความลับ:** trace ถูก redact แล้ว แต่ไม่ครบทุกรูปแบบ ตั้งสิทธิ์เข้าถึง index ให้เหมาะสม และอย่าเปิดสาธารณะ
5. **ที่อยู่ไฟล์:** ชี้ shipper ไปที่ `.sdlc/traces/*/*.jsonl` (บน Windows ใช้ `\`) ไฟล์ถูก append เท่านั้นและมีไฟล์ใหม่ทุกวัน/ทุก session
6. **หลายเครื่อง:** ติดตั้ง shipper บนเครื่องของแต่ละ dev (หรือ sync ไฟล์ไป collector กลาง) และเพิ่ม attribute ระบุเครื่อง/คน เช่น `OTEL_RESOURCE_ATTRIBUTES` หรือ processor ของ shipper

## 4. Panel / alert ที่แนะนำ

| คำถาม | ใช้ field | ตัวอย่าง |
| :--- | :--- | :--- |
| agent ใช้ tool อะไรบ่อย | `tool_name`, `role` | Loki: `sum by (tool_name) (count_over_time({job="sdlc-agent-trace", event="PostToolUse"}[1h]))` |
| guard block อะไรและทำไม | `decision.allowed`, `decision.reasons` | Loki: `{job="sdlc-agent-trace"} \| json \| decision_allowed="false"` · Kibana: `decision.allowed : false` |
| tool ล้มเหลวบ่อยแค่ไหน | `event: PostToolUseFailure`, `exit_code` | อัตรา failure ต่อ tool |
| tool ช้า | `duration_ms` | Loki: `quantile_over_time(0.95, {job="sdlc-agent-trace"} \| json \| unwrap duration_ms [5m]) by (tool_name)` |
| session ใช้ model/effort อะไร | `model`, `effort` | นับ session แยกตาม model, effort |
| ใครรันแบบข้ามการขออนุญาต | `permission_mode: bypassPermissions` | alert เมื่อพบ |
| settings ถูกแก้ระหว่างทำงาน | `event: ConfigChange` | alert ทุกครั้ง (โดยเฉพาะ `config_source: project_settings`) |
| ปิด/ลด trace เมื่อไร | `event: TraceConfigChange` | audit ว่าใครเปลี่ยน level |
| งานชิ้นหนึ่งใช้ agent เท่าไร | `work_item` | จำนวน tool call, block, failure ต่อ INT-xxx (cost จาก OTel) |
| rate limit / auth ล่ม | `event: StopFailure`, `error_type` | alert เมื่อ `rate_limit` ถี่ |
| Codex ใช้ token เท่าไร | `event: PostModelRequest`, `token_usage` | รวมต่อ session |

## 5. วิธีตรวจว่าทำงาน

1. สร้าง event: เปิด session ของ agent แล้วใช้งานสั้น ๆ → `python3 scripts/sdlc_trace.py list`
2. ดูว่า shipper อ่านไฟล์: ดู log ของ Filebeat/Alloy/Collector (ควรเห็นจำนวน event เพิ่ม)
3. ตรวจเวลา: event ล่าสุดใน dashboard ต้องตรงกับเวลาจริง (ถ้าเลื่อนไป 7 ชั่วโมง แปลว่า parse offset ไม่ถูก)
4. ตรวจ mapping: ค้น `decision.allowed : false` ต้องได้ event ที่ถูก block

## 6. ถัดไป (ไม่ได้อยู่ใน release นี้)
- คำสั่ง `export --format` สำหรับ ECS / OTLP-JSON ถ้าต้องการนำเข้าแบบ batch
- ให้ orchestrator เขียน trace schema เดียวกัน (`platform: orchestrator`) และเพิ่ม field `runtime` เมื่อมี runtime registry
