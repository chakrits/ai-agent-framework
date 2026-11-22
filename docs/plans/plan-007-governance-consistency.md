---
plan_id: PLAN-007
intent_ref: N/A (Framework / Process Change)
spec_ref: this document (Framework Spec — Gate 2)
owner: sa-architect-agent (design) / dev-coding-agent (implement)
status: merged
created: 2026-11-22 (Asia/Bangkok)
merged: 2026-11-22 16:05:10 +07 (PR #4, merge commit d764d5f)
released_in: v0.3.0
---

# Implementation Plan: Governance Consistency Fixes (Gate Model, Routing, Placement, Enforcement)

> **Route:** Framework Change (High) → **Gate 2: Framework Spec** (อนุมัติแผนนี้) → Implement → **Gate 3: Release & Merge**
> **ที่มา:** รีวิว uncommitted change บน `main` (AGENTS.md rewrite, Tiered Gates, Artifact Placement, ELI10 Change Digest, `council-pressure-test`) พบกฎที่ขัดกันเองและกฎที่ไม่มีตัวบังคับ
> **Protected paths ที่แตะ:** `docs/operating-model/constitution.md`, `docs/contracts/**`, `scripts/validate-*.py` (CI gate) → Human maintainer ต้อง commit ด้วย `SDLC_ALLOW_PROTECTED=1`

---

## 0. หลักการออกแบบ (Design Decision)

**ตรึงความหมายของเลข Gate ไว้ตายตัว แล้วให้แต่ละ Tier "ข้าม" Gate ที่ไม่จำเป็น** แทนการนับเลขใหม่ต่อ Tier

| Gate | ความหมายเดียวทั้งระบบ | ผู้อนุมัติ (ตรงกับ `orchestrator/api/auth.py`) |
| :--- | :--- | :--- |
| **Plan Checkpoint** *(ไม่มีเลข)* | อนุมัติ plan packet ของงาน Standard | Maintainer / Tech Lead (บันทึกใน PR description) |
| **Gate 1: Scope & Intent** | `intent.md` | PO / BA |
| **Gate 2: Architecture & Spec** (+ variants `Fast-Track Spec`, `Change Plan`, `Framework Spec`) | `spec.md` / `docs/plans/plan-NNN-*.md` | SA / Tech Lead |
| **Gate 3: Release & Merge** | PR/MR merge | Maintainer / Tech Lead |

**เหตุผล:** `orchestrator/core/router.py`, `auth.py`, tests (`test_phase4_orchestrator.py`, `test_orchestrator_api.py`), evals datasets และ agent/skill อื่น (`code-reviewer-agent`, `owasp-security-review`, `bug-fix-flow`) ใช้โมเดลนี้อยู่แล้ว วิธีนี้แก้แค่เอกสาร **ไม่ต้องแก้ orchestrator, RBAC หรือ test** ส่วนการตั้งชื่อ Standard Tier ว่า "Gate 1 / Gate 2" แบบใน change ปัจจุบันจะทำให้ merge ของงาน Standard ไปเข้า RBAC ของ SA

**Tier mapping (แหล่งเดียว ไว้ที่ constitution):**

| Risk (bootloader / `risk_tier`) | Tier | Gates |
| :--- | :--- | :--- |
| `low`, `medium` + isolated (ไม่แตะ auth/schema/secrets/CI/framework) | **Standard** | Plan Checkpoint → Gate 3 |
| `high` หรือ `new_feature` / `api_schema_change` | **High-Risk** | Gate 1 → Gate 2 → Gate 3 |
| `framework_change` | **High-Risk (Framework)** | Gate 2: Framework Spec (`docs/plans/plan-NNN`) → Gate 3 — ไม่ต้องมี `intent.md` (ตรงกับ `router.py:148`) |

---

## 1. Scope & Target Files

- **Files to Create:**
  - `docs/adr/README.md`, `docs/templates/adr.template.md` (ใช้แทน `DECISIONS.md` ที่ไม่มีอยู่จริง)
  - `docs/handoff/2026-11-22-governance-consistency-digest.md` (digest ของ change รอบนี้)
  - `work/INT-001/change-digest.md` (backfill)
  - tests ใหม่ใน `tests/test_work_item_validator.py`
- **Files to Modify:** `AGENTS.md`, `CLAUDE.md`, `docs/operating-model/constitution.md`, `docs/workflow/dynamic-routing.md`, `docs/workflow/core-bootloader.md`, `docs/contracts/README.md`, `docs/templates/AGENTS.template.md`, `docs/templates/review.template.md`, `.github/pull_request_template.md`, `.gitlab/merge_request_templates/Default.md`, `.agents/agents/code-reviewer-agent.md`, `.agents/skills/council-pressure-test/SKILL.md`, `scripts/validate-context-budget.py`, `scripts/validate_work_item.py`, `work/index.yaml`
- **Files to Move:** `plan.md` (root, PLAN-005) → `docs/plans/plan-005-trace-v1-1.md`
- **Do Not Modify:** `orchestrator/**`, `scripts/sdlc_guard/**`, existing test oracles (gate names in tests stay as-is), `docs/reference-architecture/`
- **Mirrors:** แก้ที่ `.agents/` เท่านั้น แล้วรัน `python3 scripts/sync-adapters.py --sync`

---

## 2. Step-by-Step Execution Strategy

### Phase A — รวม Gate model ให้เป็นหนึ่งเดียว *(เอกสารล้วน, แก้ Blocker #1, #2)*
1. **`TASK-A1`:** `constitution.md` §1 เปลี่ยนตาราง Standard Tier เป็น `Plan Checkpoint → Gate 3: Release & Merge` และเพิ่มตาราง Tier mapping จาก §0 (ให้ที่นี่เป็นแหล่งเดียวของ gate definitions)
2. **`TASK-A2`:** `dynamic-routing.md` เพิ่มคอลัมน์ `Tier` และใส่ `Plan Checkpoint` ให้ route Standard (Bug Fix Low/Med, Config/Data, Test/Docs-only) ส่วน Framework Change คง `Gate 2 (Framework Spec), Gate 3` แต่ระบุ artifact เป็น `docs/plans/plan-NNN-<slug>.md`
3. **`TASK-A3`:** `core-bootloader.md` Step 1 เพิ่มบรรทัด "Risk → Tier" ลิงก์ไปตารางใน constitution
4. **`TASK-A4`:** `AGENTS.md` §3 ย่อตาราง Tier ให้เหลือ 2 บรรทัด อ้าง Gate ด้วยเลขเดียวกับ constitution แล้วลิงก์ไป ขั้นที่ 4 เปลี่ยน "re-route to Gate 1/2" เป็น "re-route to Plan Checkpoint (Standard) หรือ Gate 1/2 (High-Risk)"
5. **`TASK-A5`:** `AGENTS.template.md` ใช้โมเดลเดียวกัน

### Phase B — แก้คำสั่งที่ขัดกันเรื่องที่วาง artifact *(Blocker #3, #4)*
1. **`TASK-B1`:** `CLAUDE.md` เปลี่ยนเป็น "record the plan in `work/<INT-xxx>/plan.md` + `tasks.json`, or `docs/plans/plan-<NNN>-<slug>.md` for framework changes (never at repo root)"
2. **`TASK-B2`:** `git mv plan.md docs/plans/plan-005-trace-v1-1.md` แล้วแก้ลิงก์ที่อ้างถึง: ตรวจแล้วพบ 2 จุดคือ `docs/plans/governance-review.md:96` และ `docs/handoff/2026-11-21-trace-v1.1.md:4` (ให้รัน `grep -rn "](plan.md)\|/plan.md)" docs README.md ROADMAP.md` ซ้ำก่อนทำ)
3. **`TASK-B3`:** `AGENTS.md` และ `contracts/README.md` ระบุว่า naming `plan-<NNN>-<slug>.md` ใช้กับไฟล์ใหม่ ส่วนไฟล์เดิม (`PLAN-006-REVIEW-ROUND-*`, `trace-versioning-plan.md`) **grandfathered** ไม่ rename เพื่อไม่ให้ลิงก์ใน history/PR พัง *(Decision D2)*

### Phase C — ลดเนื้อหาซ้ำ + ปรับ context budget กลับ *(Should-fix #6)*
1. **`TASK-C1`:** ตาราง Canonical Artifact Placement มีที่เดียวคือ `docs/contracts/README.md` ส่วน AGENTS.md เหลือ 1 บรรทัด ("Work-item files live in `work/<INT-xxx>/`, never at root — see contracts/README") + ลิงก์
2. **`TASK-C2`:** ตาราง Gate มีที่เดียวคือ constitution (ทำต่อจาก A1/A4)
3. **`TASK-C3`:** `validate-context-budget.py` คง `AGENTS.md: 500` (ตาม D4) และ **คงค่าเดิมของ HEAD ไว้ทั้งหมด** (`CLAUDE.md: 80`, `agents/*.md: 120`, `skills/*/SKILL.md: 150`, `workflows/*.md: 120`) ไม่ขยาย budget; ยังต้องลดเนื้อหาซ้ำตาม C1/C2 *(แก้หลัง review REV-PLAN-007 I4: ร่างแรกเขียนว่า "tighten" แต่ตัวเลข 150/200/150 เป็นการขยายจาก HEAD)*

### Phase D — ทำให้กฎใหม่มีตัวบังคับ *(Should-fix #5, TDD)*
1. **`TASK-D1` (test first):** ใน `tests/test_work_item_validator.py` เพิ่ม failing tests:
   - `--require-digest` ต้อง fail ถ้าไม่มี `change-digest.md`
   - digest ที่ยังมี placeholder (`[อธิบาย`, `YYYY-MM-DD`) ต้อง fail
   - ไม่ส่ง flag ต้องทำงานเหมือนเดิม (backward compatible)
2. **`TASK-D2`:** implement `--require-digest` ใน `scripts/validate_work_item.py` (presence + placeholder check, stdlib only)
3. **`TASK-D3`:** `work/index.yaml` เพิ่ม `artifacts.change_digest` ให้ INT-001 และ backfill `work/INT-001/change-digest.md`
4. **`TASK-D4`:** `contracts/README.md` แถว Stage 5 แยก digest ออกจาก `review-gate.schema.yaml` (digest = template-only + validator check, ไม่มี schema)
5. **`TASK-D5`:** สร้าง `docs/adr/README.md` (naming `ADR-<NNN>-<slug>.md`) + `adr.template.md` แล้วแทน `DECISIONS.md` ใน AGENTS.md §5 ด้วย `docs/adr/`
6. **`TASK-D6`:** DoD และ PR/MR templates อ้างคำสั่ง `validate_work_item.py ... --require-review --require-digest`

### Phase E — ชี้แจงกฎที่กำกวม *(Should-fix #7–#10, Nits)*
1. **`TASK-E1` (เกณฑ์ขนาดงาน):** "Escalate risk เมื่อ **diff รวมของ task** > ~300 บรรทัดและแตะ >1 module" แยกจาก "เป้าหมาย 100–300 บรรทัดต่อ commit" และ "~1,000 บรรทัดต่อ PR ต้อง split"
2. **`TASK-E2` (reviewer):** `code-reviewer-agent.md` workflow ข้อ 0: "Review the raw diff against spec first; read `change-digest.md` only after forming findings, and flag any digest claim not supported by the diff"
3. **`TASK-E3` (Standard Tier):** `REVIEW.md` บังคับทุก Tier (Standard = lightweight: ทำ Bugs/Compliance pass เดียว) เพื่อให้ Implementer ≠ Verifier ใช้กับทุกงาน ส่วน PR/MR templates เพิ่มหัวข้อ `## Plan Checkpoint` (ผู้อนุมัติ + เวลา + ลิงก์ comment) ให้ audit ได้
4. **`TASK-E4` (digest ตาม Tier):** Standard = ใส่ ELI10 สั้น ๆ ใน PR description, High-Risk/Framework = ไฟล์ `change-digest.md` (`--require-digest`) *(Decision D3)*
5. **`TASK-E5` (council output):** `review.template.md` เพิ่ม optional `## Council Pressure-Test` (lenses used, dissent ที่เก็บไว้, verdict) และ SKILL.md นิยาม "high-stakes" = `risk_tier: high` หรือ reversal cost สูงที่ Human ระบุ พร้อมแก้คำบรรยายเป็น "single-model multi-lens (inspired by Karpathy's LLM Council)"
6. **`TASK-E6` (Nits):** `AGENTS.template.md` ใช้ timestamp `<YYYY-MM-DD HH:mm:ss ±HH (TZ)>` (placeholder), AGENTS.md ระบุขอบเขตภาษาเป็น "Thai for chat, work-item artifacts and handoffs; framework core docs/templates stay English (headings bilingual)", และ trigger "Logic Modification" ผูกกับ `code-reviewer-agent` (dry-run pass) หรือลบออก

### Phase F — ทำให้ change นี้เองถูกกฎ *(Blocker #4)*
1. **`TASK-F1`:** เขียน `docs/handoff/2026-11-22-governance-consistency-digest.md` ตาม `change-digest.template.md`
2. **`TASK-F2`:** independent review (`code-reviewer-agent` คนละ pass กับคนเขียน) แล้วบันทึกเป็น `docs/plans/plan-007-review.md`
3. **`TASK-F3`:** ส่งรายการไฟล์ staged ต่อ commit ให้ Human ตรวจก่อน commit

---

## 3. Commit Grouping (Clean Commits)

| # | Commit | Protected? |
| :--- | :--- | :---: |
| 1 | `docs(governance): add tiered gates, artifact placement, ELI10 digest, council skill` *(change เดิมที่ปรับตาม Phase A–C แล้ว)* | ✅ Human |
| 2 | `refactor(docs): move root plan.md to docs/plans/plan-005-trace-v1-1.md` | — |
| 3 | `feat(validator): add --require-digest to validate_work_item` *(tests + impl)* | — |
| 4 | `chore(ci): set AGENTS.md budget to 500 (D4), keep other budgets at HEAD values` | ✅ Human (CI gate) |
| 5 | `docs: add ADR dir, digest backfill, PLAN-007 digest/review` | — |

---

## 4. Verification Commands

```bash
export SDLC_TRACE_LEVEL=off
python3 scripts/sync-adapters.py --sync && python3 scripts/sync-adapters.py --check
python3 scripts/validate-context-budget.py
python3 scripts/validate-contracts.py --check-defaults
python3 scripts/validate_work_item.py work/INT-001 --require-review --require-digest
python3 evals/run_evals.py --mode contract
python3 -m unittest discover -s tests -v
git diff --check
grep -rnE "Gate 1 \(Plan|Gate 2 \(PR|Gate 2: Integration" AGENTS.md docs .agents   # ต้องไม่เจอ
grep -rn "DECISIONS.md\|record the plan in \`plan.md\`" AGENTS.md CLAUDE.md docs   # ต้องไม่เจอ
```

**Baseline ก่อนเริ่ม (2026-11-22):** parity PASS, budget PASS (ใช้ budget 500), contracts PASS, unittest 236 OK (skip 3), evals 10/10, INT-001 PASS

---

## 5. Decision Points (Human ตัดสินแล้ว 2026-11-22)

**Gate 2 Approval (Framework Spec):** approved by the Human maintainer in the Claude Code chat session on 2026-11-22 (Asia/Bangkok), choosing the recommended options for D1–D3 and `500` for D4. Evidence: chat transcript only (no PR comment); self-reported, not machine-verified.

| # | คำถาม | ผลการตัดสิน |
| :--- | :--- | :--- |
| **D1** | Plan Checkpoint ของงาน Standard ควรเป็น gate ใน orchestrator ด้วยไหม | ✅ **ยังไม่ต้อง**: บันทึกใน PR ไปก่อน แล้วค่อยทำเป็น PLAN ถัดไปถ้าต้องการ (ต้องแก้ router/auth/tests) |
| **D2** | rename ไฟล์เก่าใน `docs/plans/` ให้ตรง naming ใหม่ไหม | ✅ **ไม่ rename** (grandfather) ย้ายแค่ root `plan.md` |
| **D3** | digest บังคับเป็นไฟล์สำหรับ Tier ไหน | ✅ **High-Risk + Framework** เท่านั้น ส่วน Standard ใช้ PR description |
| **D4** | budget ของ AGENTS.md | ✅ **500** (คงตาม change ปัจจุบัน แต่ยังทำ C1/C2 ลดเนื้อหาซ้ำ) |

---

## 6. Rollback / Failure Plan

- Phase A–C, E, F เป็นเอกสารล้วน: revert ทีละ commit ได้ (`git revert <sha>`)
- Phase D: flag `--require-digest` เป็น opt-in ถ้าเกิดปัญหาให้เอาออกจาก DoD/PR template ได้โดยไม่กระทบ CI เดิม
- ถ้า budget ใหม่ทำให้ CI fail ให้ตัดเนื้อหาไฟล์ที่เกิน **ห้ามขยาย budget** ใน PR เดียวกัน
- 2-Strike Rule: ถ้า verification fail 2 รอบติดให้หยุดและ escalate

---

## 7. Closeout (2026-11-22, after merge)

| Item | Result | Evidence |
| :--- | :--- | :--- |
| Gate 3 (Release & Merge) | Merged by the Human maintainer with a merge commit | [PR #4](https://github.com/chakrits/ai-agent-framework/pull/4), merge commit `d764d5f`, 2026-11-22 16:05:10 +07 |
| CI at final PR head `64a29ea` | 6/6 jobs green (ubuntu / macOS / Windows × py3.10 / 3.12) | [run 45005508352](https://github.com/chakrits/ai-agent-framework/actions/runs/45005508352) |
| CI on `main` after both merges (`32ca870`) | `SDLC Framework Validation & Agent Evals` completed `success` | GitHub Actions on `main` |
| Release | `v0.3.0` tagged by release-please; CHANGELOG lists `feat(validator)` + 2 `fix(validator)` commits from this plan | [PR #3](https://github.com/chakrits/ai-agent-framework/pull/3), merge commit `32ca870` |
| Independent review | Round 1 `changes_requested` → Round 2 `approved` → Round 3 `approved` (commits 7–9 + Windows fixture) | [plan-007-review.md](plan-007-review.md) |
| Not reviewed independently | `3fce192` (validator: code-fence headings / real content) and `64a29ea` (constitution wording) — round-3 nit fixes, covered by CI only | — |

### Lessons (feed back into the framework)
1. **Windows + `.git` fixtures:** Git marks object files read-only, so `shutil.rmtree(".git")` fails on Windows. Tests that delete a repo must clear the read-only bit (fixed in `tests/test_eval_runner.py`, `8c4ae79`). This failure was already on `main` (`eca7f22`) before PLAN-007.
2. **Merge method matters for releases:** squash-merging a mixed PR under a `docs(...)` title would hide its `feat`/`fix` commits from release-please. Use a merge commit (or rebase) for PRs that contain releasable commits.
3. **Implementer claims drift:** the independent review caught the digest overstating facts 3 times (budget "reduced", test counts, enforcement). Keep "diff first, digest last" in `code-reviewer-agent`.

### Still open after closeout
- `main` has **no branch protection** (GitHub API: `Branch not protected`), although `AGENTS.md` §1 says `main` is protected and PR-only. A repo admin must enable it (ROADMAP P5).
- The digest validator (`--require-digest` / `--digest-file`) is not run by CI or the git hooks yet (protected paths; needs its own Framework Change).
- `routing.yaml` as the single source for routing (ROADMAP P5) is still not done; PLAN-007 only aligned the docs with `router.py`.
