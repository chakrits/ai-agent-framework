---
plan_id: PLAN-004
intent_ref: N/A (Framework / Process Change)
spec_ref: docs/plans/governance-review.md (C7, C9, C10, C11, C12)
owner: dev-coding-agent
status: implemented_pending_commit
---

# Implementation Plan: Agent Trace + Versioning/Release + README Badges + Governance Quick Fixes

> Route: **Framework Change (High)** → ต้องได้ human approval ก่อนลงมือ และ human commit (แตะไฟล์ protected)
> Decisions ที่ตกลงแล้ว: **License = MIT** · **Trace เก็บในเครื่อง ไม่ commit** · **Release = release-please**
> แผนรอบก่อน (เสร็จแล้ว): [cross-platform-harness-plan.md](docs/plans/cross-platform-harness-plan.md)

## 1. Agent Trace (แก้ C10)

### 1.1 เป้าหมาย
บันทึกให้ตอบได้ว่า agent ตัวไหน, ใน session ไหน, ได้รับ prompt อะไร, เรียก tool / command อะไร, ได้ output อะไร, ใช้เวลานานเท่าไร, ถูก guard block เพราะกฎข้อไหน เพื่อใช้วิเคราะห์ย้อนหลัง โดย**ไม่ทำให้ agent ช้าลงและไม่ทำให้ secret หลุด**

### 1.2 แหล่งข้อมูล (hook events)

| Event | Claude Code | Codex | สิ่งที่บันทึก |
| :--- | :---: | :---: | :--- |
| SessionStart | ✓ (มีอยู่แล้ว: doctor) | ✓ | OS, shell, Python, framework version, git branch/commit |
| UserPromptSubmit | ✓ | ✓ | prompt (ตัดความยาว + redact) |
| PreToolUse | ✓ (guard อยู่แล้ว) | ✓ | tool, input (command / file path), **guard decision + rule** |
| PostToolUse (`async: true`) | ✓ | ✓ | `tool_response` (stdout/stderr ตัดความยาว), duration |
| PostToolUseFailure (`async: true`) | ✓ | — | `error` (มี exit code), `is_interrupt` |
| SubagentStart / SubagentStop | ✓ | ✓ | agent_type, agent_id, ข้อความสุดท้ายของ subagent |
| Stop | ✓ | ✓ | `last_assistant_message` (สรุปจบ turn) |
| SessionEnd | ✓ | ✓ | reason |

- Hook ฝั่ง trace ใช้ `async: true` เท่าที่ทำได้ จึงไม่หน่วง tool call; guard (PreToolUse) ยัง sync และ fail-closed เหมือนเดิม
- **Trace เป็น fail-open เสมอ:** ถ้าเขียน trace ไม่สำเร็จจะไม่ block งาน (แต่ guard ยัง block ตามกฎเดิม)

### 1.3 ระดับ (`SDLC_TRACE_LEVEL`)

| ระดับ | บันทึกอะไร |
| :--- | :--- |
| `off` | ไม่บันทึก |
| `info` (default) | event, tool, command / file path, guard decision, exit status / error, duration, prompt และ output **2 KB แรก** |
| `debug` | เหมือน info + output เต็มสูงสุด **64 KB** ต่อ event + `tool_input` ทั้งหมด |

### 1.4 Schema & Storage
- **Contract:** `docs/contracts/trace-event.schema.json` (JSON Schema 2020-12) อิงชื่อ operation ตาม OTel GenAI (`invoke_agent`, `execute_tool`)
- **Fields หลัก:** `v`, `ts`, `level`, `framework_version`, `platform` (claude|codex), `os`, `session_id`, `turn_id` / `prompt_id`, `agent_type`, `agent_id`, `role`, `event`, `operation`, `tool_name`, `tool_use_id`, `input`, `output{stdout,stderr,truncated,bytes}`, `error`, `duration_ms`, `decision{allowed,reasons}`, `work_item`, `git{branch,commit}`
- **`work_item`:** อ่านจาก `SDLC_WORK_ITEM` หรือดึง `INT-xxx` จากชื่อ branch
- **ที่เก็บ:** `.sdlc/traces/YYYY-MM-DD/<session_id>.jsonl` (gitignored แล้ว), 1 ไฟล์ต่อ session, เขียนแบบ append + file lock ข้าม OS (`fcntl` / `msvcrt`) เพราะ hook หลายตัวรันพร้อมกันได้
- **Retention:** ลบไฟล์เก่ากว่า `SDLC_TRACE_RETENTION_DAYS` (default 30) ตอน SessionStart

### 1.5 Redaction (ก่อนเขียนลงดิสก์)
- **Token patterns:** AWS `AKIA…`, GitHub `ghp_` / `github_pat_`, OpenAI / Anthropic `sk-…`, Slack `xox…`, Google `AIza…`, JWT, `-----BEGIN … PRIVATE KEY-----`
- **Key-value ที่ชื่อสื่อว่า secret:** `password=`, `token:`, `api_key`, `Authorization: Bearer …`, connection string ที่มี password
- **ค่าของ env var ที่ชื่อมี SECRET / TOKEN / PASSWORD / KEY** ถ้าปรากฏใน output
- ใช้ pattern ชุดเดียวกันกับ content secret scan ใน pre-commit (แก้ C-ข้อ content scan ใน review §4.3)

### 1.6 การใช้งาน (CLI)
```
python3 scripts/trace.py list                         # sessions ล่าสุด
python3 scripts/trace.py show <session> [--level debug] [--tool Bash]
python3 scripts/trace.py summary [--work-item INT-001] # สรุปจำนวน tool call, block, error, เวลา
python3 scripts/trace.py export --work-item INT-001 --out work/INT-001/trace-summary.md   # สรุปแบบ redact แล้ว พร้อม commit เป็นหลักฐาน
```

### 1.7 นอกขอบเขตรอบนี้
- ให้ orchestrator `TelemetryTracker` ใช้ schema เดียวกัน และ export ไป OTel backend (อยู่ใน P7)
- Antigravity (ไม่มี hook)

## 2. Versioning & Release (แก้ C11)

- **SemVer** เริ่มที่ `0.1.0` (pre-1.0: feat → minor, fix → patch ผ่าน `bump-minor-pre-major`)
- **แหล่ง version เดียว:** `version.txt` (default ของ release-please `simple`) อ่านโดย `sdlc_hook.py --version`, doctor และ trace
- **release-please v4:** `release-please-config.json` + `.release-please-manifest.json` + `.github/workflows/release-please.yml`
  - merge เข้า `main` → bot เปิด Release PR (bump version + CHANGELOG) → คน merge → สร้าง tag `vX.Y.Z` + GitHub Release
- **Conventional Commits:** เพิ่ม `.githooks/commit-msg` (ผ่าน launcher ข้าม OS) ตรวจ `type(scope): subject` เพราะ release-please อ่านจาก commit message
- **`CHANGELOG.md`:** seed รายการของ 0.1.0
- **Framework version ใน trace / doctor:** รู้ว่าแต่ละ run ใช้กฎ version ไหน

## 3. README Badges & Docs

แถว badge (shields.io) เหมือนตัวอย่าง:

| Badge | แหล่งข้อมูล |
| :--- | :--- |
| Stars | `github/stars` (social) |
| contributors | `github/contributors` |
| discussions | `github/discussions` (**ต้องเปิด Discussions ใน repo settings ก่อน**) |
| release | `github/v/release` (แสดง "no releases" จนกว่าจะ release แรก) |
| build | `github/actions/workflow/status/.../validate.yml?branch=main` |
| license | `github/license` (อ่านจาก `LICENSE` → MIT) |
| platform | static: `macOS · Windows · Linux · WSL` |
| built with | static: `Python 3.10+` |
| agents | static: `Claude Code · Codex · Antigravity` |

- **แถวลิงก์:** Docs · Roadmap · Changelog · Releases · Discussions · Contributing
- **ไฟล์ใหม่:** `LICENSE` (MIT, Copyright (c) 2026 chakrits and contributors), `CONTRIBUTING.md` (setup, Conventional Commits, rules, release flow)

## 4. Governance Quick Fixes (จาก [governance-review.md](docs/plans/governance-review.md))

| ID | แก้อะไร |
| :--- | :--- |
| C7 | constitution: เปลี่ยน `.sdlc` / "CI gate scripts" เป็นการอ้างอิง `protected_globs` + `ci_gate_globs` ใน `policy.json` |
| C9 | `settings.json`: ลบ `Read(.env*)` (ให้ guard ตัดสิน), ลบ `curl` / `wget` deny ที่ให้ความรู้สึกปลอดภัยเกินจริง พร้อมเขียนเหตุผลใน README |
| C12 | PR / MR template: ใช้ชื่อ CI check ปัจจุบัน + ช่อง Framework Change / human override / Conventional Commit |
| Content scan | pre-commit สแกนเนื้อหา staged diff ด้วย pattern เดียวกับ trace redaction |

Rule registry (C1, C2, C8) และความขัดแย้ง C3, C4 ทำในรอบถัดไป

## 5. Tasks

| Task | ทำอะไร | Verify |
| :--- | :--- | :--- |
| `TASK-001` | Failing tests: redaction, trace writer (lock, truncation, levels, retention), schema, CLI, commit-msg, version | fail ตามคาด |
| `TASK-002` | `scripts/sdlc_guard/redact.py` + content scan ใน pre-commit | test redaction ผ่าน; staged secret content ถูก block |
| `TASK-003` | `scripts/sdlc_guard/trace.py` + `trace-event.schema.json` + `scripts/trace.py` CLI | test writer / CLI ผ่านบน 3 OS |
| `TASK-004` | ต่อ hooks: guard บันทึก decision; events ใหม่ใน `.claude/settings.json` + `.codex/hooks.json` (async) | smoke: payload จริงสร้าง trace ที่ validate ผ่าน schema; guard ยัง block ได้ |
| `TASK-005` | `version.txt`, release-please config / manifest / workflow, `--version`, doctor แสดง version | `python3 scripts/sdlc_hook.py --version` = `0.1.0` |
| `TASK-006` | `.githooks/commit-msg` (Conventional Commits) | test ด้วย temp repo |
| `TASK-007` | `LICENSE`, `CONTRIBUTING.md`, `CHANGELOG.md`, README badges + ลิงก์ | badge URL ตอบ 200 (ตรวจหลัง push) |
| `TASK-008` | Governance quick fixes (C7, C9, C12) | validators ผ่าน |
| `TASK-009` | CI: อัป `actions/checkout` / `setup-python` (Node 20 deprecated), รัน trace tests | CI เขียว 6 jobs |
| `TASK-010` | อัปเดต ROADMAP (P5 / P7) | — |

## 6. Verification
- `python3 -m unittest discover -s tests -v` (Windows: `py -3 -m unittest discover -s tests -v`)
- Validators + evals + pre-commit
- Smoke: ส่ง payload Claude / Codex (Pre / Post / Failure) เข้า hook แล้วตรวจไฟล์ใน `.sdlc/traces/` ว่ามี event ครบ, secret ถูก redact และ output ถูกตัดตามระดับ

## 7. สิ่งที่คุณต้องทำเอง (ผมทำแทนไม่ได้ / ต้องได้รับอนุญาต)
1. **Commit + push** (แตะไฟล์ protected): `SDLC_ALLOW_PROTECTED=1`
2. **GitHub Settings → Actions → General:** เปิด "Allow GitHub Actions to create and approve pull requests" (release-please ต้องใช้)
3. **GitHub Settings → General → Features:** เปิด **Discussions** (badge discussions)
4. **Release แรก `v0.1.0`:** merge Release PR ที่ bot เปิด หรือให้ผมสร้าง tag + GitHub Release ให้หลังคุณยืนยัน

**ข้อจำกัดที่รู้:** PR ที่ release-please เปิดด้วย `GITHUB_TOKEN` จะไม่ trigger CI workflow อื่นตามข้อจำกัดของ GitHub ถ้าต้องการให้ CI รันบน Release PR ต้องใช้ PAT หรือ GitHub App token

## 8. Rollback
- ทุกอย่างเป็น commit แยก revert ได้
- ปิด trace ได้ทันทีด้วย `SDLC_TRACE_LEVEL=off`
- ลบ workflow release-please ได้โดยไม่กระทบ CI หลัก
