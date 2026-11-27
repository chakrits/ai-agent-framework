---
plan_id: PLAN-009
intent_ref: N/A (Framework / Process Change)
spec_ref: this document (Framework Spec — Gate 2)
owner: main agent session (design และ implement) / Human maintainer (protected commit)
status: merged
merged: 2026-11-27 17:48:38 +07 (PR #14, merge commit 0553126)
released_in: v0.3.2
created: 2026-11-27 (Asia/Bangkok)
---

# Implementation Plan: Trace Export Path Scrub และ CI Evidence

> **Route:** Framework Change → **Gate 2: Framework Spec** (อนุมัติแผนนี้) → Implement → **Gate 3: Release & Merge**
> **ที่มา:** งานค้างของ [PLAN-007](plan-007-governance-consistency.md) (digest validator ใน CI) และ [PLAN-008](plan-008-prompt-consistency.md) (G11, FastAPI test ที่ถูกข้าม)
> **Protected path ที่แตะ:** `scripts/sdlc_guard/trace_cli.py` → Human maintainer เป็นผู้ apply และ commit ด้วย `SDLC_ALLOW_PROTECTED=1`
> **ผู้ implement:** main session ไม่ใช้ `dev-coding-agent` เพราะ guard ห้าม role นี้เขียน `.github/workflows/**` และแก้ test ที่ tracked อยู่ (ประเด็นเดียวกับ G7 ซึ่งรอบนี้ไม่ได้แก้) ส่วน pre-commit บังคับเฉพาะ protected paths
> **Branch:** `feat/PLAN-009-ci-evidence-and-trace-scrub` (จาก `main` `3f082dc`; ตอนร่างใช้ชื่อ `docs/PLAN-009-backlog` แล้วเปลี่ยนชื่อหลังอนุมัติ)

## 1. Scope

| WS | งาน | ไฟล์ | Protected |
| :--- | :--- | :--- | :---: |
| A | G11: แทน path ก่อนตัดข้อความใน trace export | `scripts/sdlc_guard/trace_cli.py`, `tests/test_trace.py` | ✅ (`trace_cli.py`) |
| B | CI ตรวจรูปแบบ Change Digest | `.github/workflows/validate.yml` | — |
| C | CI รัน FastAPI endpoint test จริง | `.github/workflows/validate.yml` | — |

**ไม่ทำในรอบนี้:** P5 (ไม่มี GitLab CI และ Windows จริง ตามที่ Human สั่งข้าม) · git hook ใน `.githooks/` · G2–G10, G12, H1–H3 · INT-001 Gate 3 · repository settings (CODEOWNERS, PAT / GitHub App)

## 2. WS-A: Trace export path scrub (G11)

**ปัญหา:** `summarize()` ตัดบรรทัดแรกของคำสั่งเหลือ 100 ตัวอักษร (`trace_cli.py:84`) ก่อนที่ `cmd_export` จะเรียก `scrub_paths()` กับ Markdown ที่ render แล้ว (`:240`) ถ้าจุดตัดตกกลาง path ของ repo หรือ home ชิ้นส่วนที่เหลือจะไม่ตรงกับ string ที่ค้นหา จึงหลุดเข้าไฟล์ที่ตั้งใจให้ commit ได้

**แก้:**
- `summarize()` รับ argument เสริม `scrub` (ค่าเริ่มต้นคืนข้อความเดิม) และเรียกกับบรรทัดคำสั่ง **ก่อน** `[:100]`
- `cmd_export` ส่ง `scrub_paths(..., guard.REPO_ROOT)` เข้าไป และยังคง scrub รอบสุดท้ายกับทั้งเอกสาร
- ผลของ `summary` (ดูในเครื่อง) ไม่เปลี่ยน

**Test (เขียนก่อน ต้อง fail กับโค้ดเดิม):** คำสั่งที่จุดตัดตกกลาง path ของ repo และอีกกรณีกลาง path ของ home แล้ว assert ว่าไฟล์ export ไม่มีส่วนนำของทั้งสอง path ตั้งแต่ความยาวที่ระบุตัวเครื่องหรือผู้ใช้ได้

คำนวณความยาว padding ของคำสั่งจาก `len()` ของ path ขณะรัน เพื่อให้จุดตัดตัวที่ 100 ตกกลาง path ทุก runner (ความยาว repo root ต่างกันในแต่ละ OS) และ assert ครบทุกรูปสะกดที่ `scrub_paths` รองรับ (`/` และ `\`)

**การส่งมอบ:** agent เขียน test และเตรียม patch ของ `trace_cli.py` จากสำเนาใน scratchpad (ไม่เก็บ `.patch` ใน repo) ตรวจด้วย `git apply --check` และรัน test บนสำเนาที่ apply แล้ว จากนั้น Human apply และ commit `trace_cli.py` พร้อม test ใน commit เดียว เพื่อไม่ให้มี commit ที่ test fail

## 3. WS-B: Change Digest ใน CI

เพิ่ม step หลัง contract validation:

```bash
shopt -s nullglob
for f in docs/handoff/*-digest.md work/INT-*/change-digest.md; do
  python scripts/validate_work_item.py --digest-file "$f"
done
```

- GitHub Actions รัน `shell: bash` ด้วย `-eo pipefail` จึง fail ที่ digest แรกที่ไม่ผ่าน
- Pattern `*-digest.md` ไม่รวม `2026-11-21-trace-v1.1.md` ซึ่งเป็น handoff ไม่ใช่ digest
- **ข้อจำกัด:** ตรวจเฉพาะรูปแบบของ digest ที่มีอยู่ **ไม่ได้บังคับว่า PR ระดับ High-Risk / Framework ต้องมี digest** เพราะ CI ยังไม่รู้ tier ของ PR (ต้องออกแบบแยก)

## 4. WS-C: FastAPI test ใน CI

เพิ่มสอง step **หลัง** step เดิมทั้งหมด เพื่อให้ unit test และ contract eval รอบแรกยังพิสูจน์ว่า core ใช้ stdlib อย่างเดียวได้:

```bash
python -m pip install -r orchestrator/requirements.txt httpx
python -c "import fastapi.testclient"
python -m unittest discover -s tests -p test_orchestrator_api.py -v
```

- บรรทัด `import fastapi.testclient` ทำให้ job fail ถ้า dependency ไม่ครบ แทนที่ test จะถูกข้ามเงียบ ๆ
- ชื่อ job เดิมไม่เปลี่ยน จึงไม่ต้องแก้ required checks ของ ruleset `protect-main`
- **ยังไม่ยืนยัน:** ชุด dependency ที่ `TestClient` ต้องใช้บน version ล่าสุด และผลบน 6 job จะยืนยันจาก CI ของ PR

> **แก้โดย Amendment A1 (§9):** บรรทัด `unittest discover` ด้านบนถูกแทนด้วยคำสั่งใน §9

## 5. Verification (ก่อนขอ Gate 3)

1. Test ใหม่ของ WS-A: fail กับโค้ดเดิม และผ่านหลัง apply patch (บันทึก output)
2. รัน loop ของ WS-B ในเครื่องต้องผ่าน และ `--digest-file docs/templates/change-digest.template.md` ต้อง fail
3. `git diff --check` · `sync-adapters.py --check` · `validate-context-budget.py` · `validate-contracts.py --check-defaults` · `evals/run_evals.py --mode contract` · `unittest discover -s tests`
4. CI ของ PR ผ่านครบ 6 job และ log แสดงว่า `TestFastAPIHttpEndpoints` รันจริง ไม่ถูกข้าม
5. ผู้ตรวจอิสระบันทึกผลใน `docs/plans/plan-009-review.md` พร้อม commit SHA ที่ตรวจ
6. Change Digest ใน `docs/handoff/` และ PR description

## 6. Risks & Rollback

| ความเสี่ยง | รับมือ |
| :--- | :--- |
| ติดตั้ง dependency จาก PyPI ใน CI และ version เป็น `>=` ไม่มีเพดาน จึงอาจพังจาก release ใหม่ (รวมรอบ nightly) | ยอมรับในรอบแรก ถ้าพังให้เพิ่มเพดาน version หรือ revert step ของ WS-C |
| Digest เก่าไม่ผ่านกติกาที่เข้มขึ้นในอนาคต ทำให้ทุก PR แดง | ปัจจุบันทุกไฟล์ผ่าน การเปลี่ยนกติกาต้องแก้ digest เก่าใน change เดียวกัน |
| `scrub` ทำให้ข้อความ top commands เปลี่ยน (token สั้นกว่า path) | เป็นผลที่ต้องการ มีเฉพาะใน export |

**Rollback:** revert แต่ละ commit ได้อิสระ ไม่มี data migration

## 7. Commits

| # | ข้อความ | ผู้ commit |
| :---: | :--- | :--- |
| 1 | `docs(plans): add PLAN-009 and correct stale plan statuses` | agent เมื่อ Human สั่ง |
| 2 | `fix(trace): scrub paths before truncating exported commands` | **Human** (`SDLC_ALLOW_PROTECTED=1`) |
| 3 | `ci: validate change digests and run FastAPI endpoint tests` | agent เมื่อ Human สั่ง |
| 4 | `docs(plans): add PLAN-009 review and change digest` | agent เมื่อ Human สั่ง |

## 8. Gate 2 Approval

- **Approver:** Human Maintainer (ตอบในแชท)
- **Decision:** `Approved` — ข้อความ: “อนุมัติ PLAN-009 และเริ่มรีวิว INT-001 ได้เลย”
- **Recorded at:** 2026-11-27 17:16 +07 (เวลาที่บันทึก ไม่ใช่เวลาอนุมัติที่แน่นอน)

## 9. Amendment A1 — แก้ตาม[รีวิวอิสระ](plan-009-review.md) (`eadcc98`)

| ข้อ | การแก้ |
| :--- | :--- |
| m1 | step FastAPI ใช้คำสั่งด้านล่างแทน `unittest discover` เพื่อให้ fail เมื่อ endpoint test ถูกถอด เปลี่ยนชื่อ หรือถูกข้าม |
| m3 | test ของ WS-A ใช้ path จำลองคงที่ (repo อยู่ใต้ home) แทนการคำนวณจาก path ของ runner ตาม §2 และ assert ชิ้นส่วนหลังแทน home ด้วย |
| m5 | เพิ่ม `README.md` เข้า scope เพื่อแก้ข้อความเรื่อง digest ใน CI ส่วน `ROADMAP.md` อัปเดตหลัง merge |

```bash
python -c 'import sys,unittest; s=unittest.defaultTestLoader.loadTestsFromName("tests.test_orchestrator_api.TestFastAPIHttpEndpoints"); r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(0 if r.testsRun and r.wasSuccessful() and not r.skipped else 1)'
```

**ข้อจำกัดที่ไม่แก้ในแผนนี้ (follow-up):**
- **M1:** `scrub_paths` ยังปล่อยชื่อผู้ใช้หรือชื่อโฟลเดอร์ในรูปอื่น เช่น `-Users-<user>-...`, Git Bash / WSL path และ path ที่ escape ช่องว่าง จนกว่าจะแก้ ต้องอ่านไฟล์ export ก่อน commit
- **m2:** การตัดข้อความตอนบันทึก trace ยังเกิดก่อน scrub
- **m4, m6, m7:** digest loop ผ่านเมื่อไม่พบไฟล์, ชื่อสถานะแผนไม่ตรงกัน, และการ pin dependency / `permissions` ใน workflow
- คำสั่งใน §7: เพิ่ม commit สำหรับ A1 ก่อน commit ชุดที่ 4

- **Approver:** Human Maintainer (ตอบในแชทต่อข้อเสนอแก้ m1, m3, README และ digest)
- **Decision:** `Approved` — ข้อความ: “แก้เลย” (การรับความเสี่ยง M1 ยังไม่ได้ตัดสิน ให้ตัดสินที่ Gate 3)

## 10. Closeout (บันทึก 2026-11-27 17:52 +07, หลัง merge)

| รายการ | ผล | หลักฐาน |
| :--- | :--- | :--- |
| Merge | Human maintainer merge ด้วย merge commit ขณะ[ผลรีวิว](plan-009-review.md)ยังเป็น `changes_requested` ไม่มี sign-off เป็นลายลักษณ์อักษร และ PR ไม่มี GitHub review | [PR #14](https://github.com/chakrits/ai-agent-framework/pull/14), head `f4edda2`, merge commit `0553126`, 2026-11-27 17:48:38 +07 |
| CI ที่ PR head `f4edda2` | ผ่าน 6/6 (ubuntu / macOS / Windows × py3.10 / 3.12) | [run 45984856538](https://github.com/chakrits/ai-agent-framework/actions/runs/45984856538) |
| §5.4 FastAPI test รันจริง | `test_endpoints_auth_rbac_scope_and_lifecycle` ใน step ใหม่ได้ `ok` และ `Ran 1 test` ครบ 6 job (ในรอบ unit test ก่อนติดตั้ง dependency ยังถูกข้ามตามที่ออกแบบ) | log ของ run เดียวกัน; ติดตั้ง `fastapi 0.165.0`, `starlette 1.10.0`, `httpx 0.29.0`, `pydantic 2.14.4` |
| Test ของ WS-A บน Linux / Windows | ผ่านในรอบ unit test ของ run เดียวกัน | เช่นเดียวกัน |
| CI บน `main` หลัง merge (`0553126`) | ผ่าน 6/6 | [run 45985223645](https://github.com/chakrits/ai-agent-framework/actions/runs/45985223645) |
| Release | `v0.3.2` เผยแพร่ 2026-11-27 17:51:51 +07 | [PR #15](https://github.com/chakrits/ai-agent-framework/pull/15) (`1654475`), [release v0.3.2](https://github.com/chakrits/ai-agent-framework/releases/tag/v0.3.2) |
| Independent review | รอบเดียวที่ `eadcc98`: `changes_requested` (Blocker 1, Major 1, Minor 7) | [plan-009-review.md](plan-009-review.md) |

### สถานะของ finding
| ข้อ | สถานะ |
| :--- | :--- |
| B1 (ไม่มีหลักฐาน CI) | มีหลักฐานแล้วตามตารางข้างบน (ผู้ implement บันทึก ยังไม่ได้รีวิวซ้ำ) |
| m1, m3, m5 (README) | แก้ใน `5662ae3` **ยังไม่ได้รีวิวซ้ำโดยผู้ตรวจอิสระ** |
| M1 (path / ชื่อผู้ใช้รูปอื่น) | **เปิดอยู่ และ Human ยังไม่ได้ตัดสินรับความเสี่ยง** จนกว่าจะแก้ ต้องอ่านไฟล์ export ก่อน commit |
| m2, m4, m6, m7 | เปิดอยู่ |

### พบเพิ่มจาก CI
- `StarletteDeprecationWarning`: การใช้ `httpx` กับ `starlette.testclient` ถูก deprecate และแนะนำ `httpx2` (follow-up รวมกับ m7)

### ไม่ได้ตรวจ
- live eval, Docker, Windows เครื่องจริง และการรีวิวส่วนที่เปลี่ยนหลัง `eadcc98`

### บทเรียน
1. **การแก้ปัญหา path หลุดแบบเจาะจุดเดียวไม่พอ:** G11 ปิดกรณีตัดกลาง path แต่รีวิวพบรูปอื่นที่พบบ่อยกว่า (M1) งานถัดไปควรมี test ที่ตรวจไฟล์ export ว่าไม่มีชื่อผู้ใช้
2. **step CI ต้อง fail เมื่อ test ไม่ได้รัน:** `unittest discover` ผ่านได้แม้ test ถูกข้าม (m1)
