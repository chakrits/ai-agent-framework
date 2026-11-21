---
plan_id: PLAN-003
intent_ref: N/A (Framework / Process Change)
spec_ref: docs/plans/framework-review-roadmap-v2.md (R1–R5, P5)
owner: dev-coding-agent
status: implemented_pending_windows_verification
---

> **Progress (2026-11-21):** TASK-001–010 implemented. macOS verification: 78 tests OK (2 Windows-only skipped) on Python 3.14 and 3.11; validators + evals pass; the real `.claude/settings.json` hook command blocks force-push / prod deploy / `C:\x\.env` / case-variant constitution edits on a path with spaces. Not yet verified: Windows/Linux CI (repo has no commits/remote yet) and §8 manual Windows checks.

# Implementation Plan: Cross-Platform Harness (Windows / macOS / Linux / WSL) + P5 Guard Hardening

> Route: **Framework Change (High)** → ต้องได้ human approval ก่อนลงมือ (Gate 2) และ review ก่อน merge (Gate 3)
> Prerequisites ที่ตกลงแล้ว: **Python 3.10+** และ **Git for Windows** บนเครื่อง Windows; รองรับ **macOS, Linux, WSL**

## 0. ปัญหาที่พบ (ทดสอบจริงบนเครื่องนี้ 2026-11-21)

| # | ปัญหา | หลักฐาน | ผลกระทบ |
| :-: | :--- | :--- | :--- |
| X1 | hook command ใน `.claude/settings.json` ไม่ได้ใส่ quote → path ที่มีช่องว่าง (`GitHub Code`) ทำให้ bash แยกคำ | `bash -c '${CLAUDE_PROJECT_DIR}/scripts/guard-protected-paths.sh'` → `No such file`, **exit 127** | exit ≠ 2 = non-blocking error → **guard ไม่ทำงานเลยบนเครื่องนี้** |
| X2 | Windows path `C:\repo\docs\operating-model\constitution.md` ไม่ match | `--check-path` → exit 0 | Windows bypass |
| X3 | Path traversal `docs/operating-model/../operating-model/constitution.md` ไม่ match | exit 0 | bypass |
| X4 | ตัวพิมพ์ต่าง `DOCS/Operating-Model/Constitution.md` ไม่ match (NTFS/APFS default case-insensitive) | exit 0 | bypass |
| X5 | Guard เป็น bash script, tests exec `.sh` ตรงและเรียก `"python3"` | `tests/test_phase3_harness.py:65,74` | Windows รัน test ไม่ได้ (`python3` มักไม่มี/เป็น Store stub) |
| X6 | ไม่มี `.gitattributes` | `ls .gitattributes` | `core.autocrlf=true` บน Windows → `.sh`/hook เป็น CRLF → `\r: command not found` |
| X7 | `write_text()` ใช้ newline ของ OS | `scripts/sync-adapters.py` `write_codex_index` | Windows เขียน CRLF → diff noise |
| X8 | CI รันแค่ `ubuntu-latest` | `.github/workflows/validate.yml` | ไม่มีหลักฐานว่าใช้ได้บน Windows/macOS |
| X9 | P5 เดิม: IFS bug, role guard dead code, test-oracle gap, matcher ไม่ครบ | ดู `docs/plans/framework-review-roadmap-v2.md` §1 | Bash guard ไม่ทำงาน |
| X10 | `CliHarnessExecutor` ส่ง prompt ทาง argv และไม่ resolve `.cmd` shim | `orchestrator/graphs/sdlc_pipeline.py` | Windows: หา `claude`/`codex` ไม่เจอ, prompt ยาวชน command-line limit |

## 1. Design Decision: ควรมี SessionStart script ตรวจ OS ก่อนไหม?

**คำตอบ: ควรมี แต่ใช้เป็น "preflight/doctor + context" เท่านั้น ไม่ใช้เป็นตัวเลือกว่าจะรัน hook ตัวไหน**

เหตุผล:
1. **Hook command ถูกกำหนดใน settings ก่อน session เริ่ม** — SessionStart เปลี่ยนคำสั่งของ `PreToolUse` ใน session ปัจจุบันไม่ได้ ถ้าจะให้ SessionStart เลือก hook ต้องเขียน settings ใหม่แล้ว restart ซึ่งเปราะ
2. **Fail-open risk** — ถ้า SessionStart พัง/ถูกข้าม (Codex: hook ใหม่/ที่ถูกแก้จะถูก skip จนกว่าจะ trust; Antigravity ไม่มี hook) guard ที่พึ่ง state จาก SessionStart จะหลุดทั้งหมด
3. **State ข้าม hook ไม่น่าเชื่อถือบน Windows** — มีรายงานว่า `CLAUDE_ENV_FILE` บน Windows 11 เขียนสำเร็จแต่ตัวแปรว่างใน session
4. **OS ของ host ≠ รูปแบบ path ใน payload เสมอไป** — เช่น Claude บน Windows รัน hook ใต้ Git Bash (path `/c/...`), agent ใน WSL แก้ repo บน `/mnt/c/...` → ต้องตรวจ **ทุกครั้งที่ hook ถูกเรียก** จาก payload เอง

**สถาปัตยกรรมที่เลือก — 3 ชั้น:**

| ชั้น | เมื่อไร | ทำอะไร | ถ้าล้ม |
| :--- | :--- | :--- | :--- |
| **L0 Setup** (`scripts/setup.py`) | ครั้งเดียวต่อเครื่อง/clone | ตั้ง `core.hooksPath`, ตรวจ Python/Git, ตรวจ line endings, รัน doctor | แจ้ง error ชัดเจน |
| **L1 SessionStart Doctor** (`scripts/doctor.py --hook`) | ทุก session (Claude + Codex) | ตรวจ OS (Windows/macOS/Linux/WSL), shell (Git Bash/PowerShell/cmd/zsh/bash), Python, Git, `core.hooksPath`, CRLF; **ฉีด context** ให้ agent รู้ shell/path style ที่ต้องใช้; เขียน `.sdlc/env.json` (gitignored) เพื่อ diagnostics | **exit 0 เสมอ** (เตือน ไม่ block) |
| **L2 Runtime Guard** (`scripts/sdlc_guard/`) | ทุก tool call (PreToolUse) | ตรวจ OS + path style **จาก payload + host ณ เวลานั้น** (stateless), normalize path, ตรวจ command ตาม shell family | **fail-closed: exit 2** |

ชั้นสุดท้ายที่ใช้ได้ทุก platform (รวม Antigravity): **git pre-commit (staged diff) + CI matrix + branch protection**

## 2. Scope & Target Files

**Create**
- `scripts/sdlc_guard/__init__.py`
- `scripts/sdlc_guard/platform_env.py` — detect OS/WSL/MSYS/shell, หา Python
- `scripts/sdlc_guard/paths.py` — normalize path ทุกรูปแบบ → repo-relative POSIX (pure functions, ทดสอบ path Windows ได้บน mac)
- `scripts/sdlc_guard/commands.py` — วิเคราะห์ command ของ bash / PowerShell / cmd
- `scripts/sdlc_guard/policy.json` — protected paths, test-oracle globs, secret globs, deny-command rules, role map (single source)
- `scripts/sdlc_guard/guard.py` — entry: adapter payload Claude/Codex → decision → exit 0/2
- `scripts/bin/sdlc-hook` — POSIX `sh` launcher (macOS/Linux/WSL/Git Bash) เลือก `python3` → `python` → `py -3` พร้อมตรวจ version ≥ 3.10 (กัน Windows Store stub); หาไม่เจอ → exit 2
- `scripts/bin/sdlc-hook.cmd` — launcher สำหรับ `cmd.exe`/PowerShell (ใช้กับ Codex `commandWindows` และ fallback)
- `scripts/doctor.py`, `scripts/setup.py`, `scripts/precommit.py`
- `.gitattributes` — `* text=auto eol=lf`, `*.cmd *.bat *.ps1 eol=crlf`, binary types
- `.codex/hooks.json` (generated โดย `sync-adapters.py`) — `PreToolUse` + `SessionStart` พร้อม `commandWindows`
- `tests/test_paths_crossplatform.py`, `tests/test_commands_crossplatform.py`, `tests/test_guard_payloads.py`
- `tests/fixtures/hook-payloads/{claude,codex}/{posix,windows}/*.json`

**Modify**
- `.claude/settings.json` — command quote + ผ่าน launcher; matcher `Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell`; เพิ่ม `SessionStart` doctor; allow `Bash(python *)`, `Bash(py *)`
- `.githooks/pre-commit` — `#!/bin/sh` launcher → `scripts/precommit.py`
- `scripts/guard-protected-paths.sh`, `scripts/setup-hooks.sh` — เหลือเป็น wrapper เรียก Python (backward compat 1 รอบ แล้วลบ)
- `scripts/sync-adapters.py` — `newline="\n"`, parity เทียบแบบ normalize CRLF, generate `.codex/hooks.json`
- `scripts/validate-*.py`, `evals/run_evals.py` — UTF-8 stdout, `newline="\n"`
- `tests/test_phase3_harness.py` — ใช้ `sys.executable` แทน `"python3"`, เรียก guard ผ่าน Python
- `orchestrator/graphs/sdlc_pipeline.py` — `shutil.which` resolve `.cmd`, ส่ง prompt ทาง stdin
- `.github/workflows/validate.yml` — matrix `ubuntu / macos / windows` × Python `3.10 / 3.12`; Windows รันทั้ง `shell: bash` และ `shell: pwsh`
- `.gitlab-ci.yml` — คง Linux; เพิ่ม Windows job แบบ optional (ต้องยืนยัน runner tag)
- `.gitignore` — `.sdlc/`
- `README.md` — Prerequisites + setup ต่อ OS

**Protected (ไม่แตะ):** `docs/operating-model/constitution.md`, `docs/contracts/*`

## 3. Path Normalization Spec (`paths.py`)

Input ที่ต้องรองรับ → Output เป็น repo-relative POSIX + casefold สำหรับ matching

| รูปแบบ | ตัวอย่าง | วิธี |
| :--- | :--- | :--- |
| Windows drive | `C:\Users\a\repo\docs\x.md`, `c:/Users/a/repo/docs/x.md` | `\`→`/`, drive เป็นตัวเล็ก |
| Windows long path | `\\?\C:\Users\a\repo\x` | ตัด `\\?\` |
| UNC | `\\server\share\repo\x` | เก็บเป็น `//server/share/...` |
| MSYS / Git Bash | `/c/Users/a/repo/x` | → `c:/Users/a/repo/x` (เฉพาะเมื่อ host = Windows หรือ `MSYSTEM` ถูกตั้ง) |
| WSL | `/mnt/c/Users/a/repo/x` | → `c:/Users/a/repo/x` เมื่อเทียบกับ repo root ฝั่ง Windows |
| macOS / Linux | `/Users/a/GitHub Code/repo/x` | คงเดิม (รองรับช่องว่าง) |
| Relative | `docs\x.md`, `./docs/x.md` | join กับ `cwd` **จาก payload** (ไม่ใช่ cwd ของ process) |
| Traversal | `src/../docs/x.md` | `posixpath.normpath` แบบ lexical หลัง canonicalize |
| Symlink | ไฟล์จริงอยู่ใน protected path | ถ้าไฟล์มีอยู่จริงบน host → `os.path.realpath` ตรวจซ้ำ |

Repo root: `CLAUDE_PROJECT_DIR` → payload `cwd` + `git rev-parse --show-toplevel` → fallback ตำแหน่ง script
Matching: `fnmatch` บน path ที่ casefold แล้วเสมอ (ปลอดภัยกว่าเพราะ NTFS/APFS ไม่สนตัวพิมพ์โดย default); path นอก repo ยังตรวจ secret globs (`~/.ssh/**`, `~/.aws/credentials`)

## 4. Command Analysis Spec (`commands.py`)

- Shell family จาก `tool_name` (`Bash` / `PowerShell` / Codex shell tool) + host; tokenize ด้วย `shlex` (POSIX) หรือ tokenizer PowerShell/cmd แบบง่าย (quote, `;`, `|`, `&&`)
- กฎใน `policy.json` (regex, case-insensitive):
  - `git push` แบบ force (`--force`, `-f`, `+refspec`) → block; `--force-with-lease` ตั้งค่าได้ใน policy
  - `git commit --no-verify` และการแก้ `core.hooksPath` → block (กันข้าม hook ตาม CLAUDE.md)
  - deploy production ที่ไม่มี `RELEASE_APPROVAL` → block
  - token ใดที่ resolve แล้วเป็น secret path (`.env`, `secrets/**`) ไม่ว่าคำสั่งไหน (`cat`, `type`, `Get-Content`, `gc`) → block
  - คำสั่งเขียนไฟล์ (`>`, `>>`, `tee`, `sed -i`, `cp`, `mv`, `rm`, `Set-Content`, `Add-Content`, `Out-File`, `Copy-Item`, `Move-Item`, `Remove-Item`, `New-Item`, `copy`, `move`, `del`) + target เป็น protected/test-oracle สำหรับ role ที่ถูกจำกัด → block
- **ข้อจำกัด:** วิเคราะห์ command เป็น best-effort (script ซ้อน, obfuscation) → defense-in-depth ที่ pre-commit/CI

## 5. Role Resolution (P5)

`payload.agent_type` (Claude subagent / `--agent`) → `SDLC_ACTIVE_ROLE` env → `main`
Test-oracle globs ปรับตาม runtime ได้: `tests/**`, `**/test_*.py`, `**/*_test.*`, `**/*.spec.*`, `**/*.test.*`, `**/robot/**`, `**/test-report*.md`, `**/test-cases/**`

## 6. Step-by-Step Tasks

| Task | ทำอะไร | Verify |
| :--- | :--- | :--- |
| `TASK-001` | `.gitattributes` + `.gitignore` | `git ls-files --eol` ไฟล์ `.sh`/hook เป็น `lf` |
| `TASK-002` | **Failing tests ก่อน**: path matrix (§3), command matrix (bash/pwsh/cmd), payload fixtures (X1–X4, X9) | รันแล้ว fail ตามคาด |
| `TASK-003` | `paths.py` + `platform_env.py` | test path matrix ผ่านบนทุก OS |
| `TASK-004` | `commands.py` + `policy.json` | test command matrix ผ่าน |
| `TASK-005` | `guard.py` + launchers (`sdlc-hook`, `.cmd`) fail-closed | payload `git push -f`, `deploy production`, `cat .env`, `Get-Content .env`, `C:\...\constitution.md`, path มีช่องว่าง → exit 2 |
| `TASK-006` | `.claude/settings.json` + `.codex/hooks.json` (generated) + parity check | `sync-adapters.py --check` ผ่าน; test จำลองการเรียก command string ผ่าน shell พร้อม path มีช่องว่าง |
| `TASK-007` | `doctor.py` (SessionStart) + `setup.py` | doctor ออก JSON `additionalContext` (Claude) / plain text (Codex); exit 0 เสมอ |
| `TASK-008` | `precommit.py` (validators + staged-diff secret/protected check) + `.githooks/pre-commit` | test ด้วย temp git repo |
| `TASK-009` | ปรับ scripts/tests เดิม (`sys.executable`, UTF-8, `newline="\n"`) + orchestrator executor | test เดิมทั้งหมดผ่าน |
| `TASK-010` | CI matrix GitHub (+ GitLab Windows optional) + README prerequisites | CI เขียวทั้ง 3 OS (ต้อง push ก่อน — ยังไม่มี commit/remote) |

## 7. Verification Commands

- macOS / Linux / WSL: `python3 -m unittest discover -s tests -v`
- Windows (PowerShell): `py -3 -m unittest discover -s tests -v`
- Windows (Git Bash): `python -m unittest discover -s tests -v`
- Validators: `python3 scripts/sync-adapters.py --check && python3 scripts/validate-context-budget.py && python3 scripts/validate-contracts.py --check-defaults && python3 evals/run_evals.py`
- Hook smoke: `echo '<payload>' | scripts/bin/sdlc-hook pretooluse` → ต้องได้ exit 2 สำหรับ payload อันตราย

## 8. ต้องยืนยันบนเครื่อง Windows จริง (ทำบน mac ไม่ได้)

- [ ] Claude Code บน Windows: hook รันใต้ Git Bash จริงหรือไม่ และ `CLAUDE_PROJECT_DIR` มาในรูป `C:\...` หรือ `/c/...` → เก็บ payload จริงเป็น fixture
- [ ] ชื่อ tool PowerShell ของ Claude Code บน Windows และรูปแบบ `tool_input`
- [ ] Codex บน Windows: ชื่อ tool shell ใน `PreToolUse`, command ถูก wrap ด้วย PowerShell หรือไม่, `commandWindows` ทำงาน
- [ ] Git for Windows รัน `.githooks/pre-commit` (`#!/bin/sh`) ผ่าน `core.hooksPath`
- [ ] GitLab SaaS Windows runner tag ที่ใช้ได้

## 9. Rollback / Failure Plan

- ทุกอย่างอยู่ใน commit เดียวบน branch แยก (`feat/cross-platform-harness`) → revert ได้ทันที
- wrapper `.sh` เดิมยังอยู่ 1 รอบ → ถ้า launcher มีปัญหา ชี้ `settings.json` กลับไป wrapper ได้
- Emergency: `SDLC_GUARD_FAIL_OPEN=1` ทำให้ guard error ไม่ block (ต้องตั้งเองโดยคน, ถูกบันทึกใน stderr) — ไม่มีผลกับกฎ deny ที่ match ชัดเจน

## 10. References

- Claude Code hooks (exit 2 blocks PreToolUse, `agent_type`, SessionStart): https://code.claude.com/docs/en/hooks
- Claude Code hooks guide (Windows `powershell.exe` example): https://code.claude.com/docs/en/hooks-guide
- Windows hook shell behavior (community bug reports): https://github.com/anthropics/claude-code/issues/21878 , https://claudeissues.com/issue/59225-bug-windows-model-is-told-shell-powershell-while-hooks-execute-under-bash-cross , https://claudeissues.com/issue/90077-bug-hooks-with-shell-powershell-spawn-pwsh-with-no-powershell-exe-fallback-so-ho
- `CLAUDE_ENV_FILE` on Windows test: https://dev.classmethod.jp/en/articles/claude-code-session-start-hook-verification/
- Codex hooks (`commandWindows`, trust review): https://developers.openai.com/codex/hooks
- Codex Windows shell interception gap (third-party): https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/main/docs/codex-integration.md
- Git hooks / `core.hooksPath`: https://kernel.org/pub/software/scm/git/docs/githooks.html
