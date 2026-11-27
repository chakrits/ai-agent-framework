---
plan_id: PLAN-010
intent_ref: N/A (Framework / Process Change)
spec_ref: this document (Framework Spec — Gate 2, Wave 1 only)
owner: main agent session (design และ implement) / Human maintainer (Gate 2 และ Gate 3)
status: approved_in_progress
created: 2026-11-27 17:38:00 +07 (Asia/Bangkok)
---

# PLAN-010 · Workspace, Knowledge & Runtime Architecture

> **Route:** Framework Change → Gate 2 (Wave 1 เท่านั้น) → Implement & Verify → Gate 3
> **Tracking Issue:** [#13](https://github.com/chakrits/ai-agent-framework/issues/13) (`Related to #13`)
> **Worktree / Branch:** `.worktrees/PLAN-010` · `docs/PLAN-010-workspace-and-runtime-architecture`
> **Baseline:** `3f082dc` · [ผลรีวิวร่างเดิม](plan-010-review.md)

## 0. Workspace Map

| ชั้น | ตำแหน่งและหน้าที่ |
|---|---|
| **Framework Core** | `.agents/`, `AGENTS.md`, constitution, routing และ contracts กำหนดขั้นตอนที่ใช้ร่วมกัน |
| **Knowledge** | Wave 1 เพิ่ม `docs/knowledge/` สำหรับบทสรุปที่ย้อนหาแหล่งที่มาได้ ส่วน `docs/adr/` เป็นที่เก็บการตัดสินใจพร้อมหลักฐานอนุมัติ |
| **Project Pack** | `examples/project-packs/` เก็บคำแนะนำเฉพาะโดเมน เช่น EBMC และ Robot Framework |
| **Product Runtime** | แอปพลิเคชันที่ build/test ได้ อยู่ใน target repo ที่เลือกสำหรับ pilot ส่วน `runtimes/<app>/` เป็นทางเลือกในอนาคต |

`work/<INT-xxx>/` เก็บหลักฐาน work item, `.sdlc/` เก็บ state และ traces ในเครื่อง และ `.worktrees/PLAN-010` คือ Git checkout สำหรับทำงานแผนนี้

## 1. Evidence

- ที่ `3f082dc` งานตรวจใน PLAN-010 พบ archive 2 ไฟล์ ไม่มีโฟลเดอร์ย่อยว่าง และไม่มี `.sdlc-telemetry/` ตัวเลข 60 โฟลเดอร์ว่างมาจาก worktree หลัก ไฟล์ [ADR index](../adr/README.md) มีอยู่แล้ว
- `README.md` อยู่ใน scope ของ PLAN-009 และ PLAN-010 ให้ตรวจ diff บนฐานล่าสุดหลัง integrate PLAN-009 ก่อนแก้ README
- CLI/API ปัจจุบันยังไม่มี runtime selector ส่วน service ใช้ framework root และ dry-run executor ตาม [start_run](../../orchestrator/api/handlers.py#L69)
- Probe จากการรีวิวพบว่า EBMC skill เข้า bundle แต่ prompt ทั้ง 7 roles เท่ากับ core และ loader รับ `['ebmc', None]` เมื่อ run ที่เริ่มด้วย EBMC ถูก resume โดยไม่ส่ง pack ซ้ำ [Loader](../../orchestrator/core/loader.py#L124) · [Approve handler](../../orchestrator/api/handlers.py#L109)
- [Release config](../../release-please-config.json#L8) ใช้ package เดียวที่ root และ [CI matrix](../../.github/workflows/validate.yml#L10) รัน framework suite ร่วมกัน ผลของ runtime-only commit ต่อ release ยังต้องพิสูจน์ก่อนเลือก monorepo

<a id="2-three-unified-alternatives-alt-1-vs-alt-2-vs-alt-3"></a>

## 2. Alternatives

| ทางเลือก | ผลส่งมอบและ trade-off |
|---|---|
| **ALT 1 · Surgical, จำกัด scope** | ทำ Wave 1 เป็นเอกสารขนาดเล็กที่ย้อนกลับได้ จากนั้นแยก runtime pilot ใน target repo ด้วยสเปกและ Gate 2 ใหม่ |
| **ALT 2 · Monorepo + CI/release แยกส่วน** | ใช้เมื่อ framework กับแอปต้องเปลี่ยนร่วมกันบ่อย ต้องออกแบบ runtime selection, สิทธิ์, CI และ release สำหรับ runtime-only, framework-only และ mixed commits |
| **ALT 3 · Package + lock สำหรับหลาย repo** | ใช้เมื่อมีหลายทีมต้อง pin และอัปเกรด framework คนละจังหวะ ต้องพิสูจน์ install/update/rollback ผ่าน CI ของ consumer หลังมีหลักฐานจาก P9 |

## 3. Recommendation

เสนอ **ALT 1 แบบจำกัดขอบเขต** ให้ Gate 2 รอบนี้ตัดสินเฉพาะ Wave 1 ตาม §4.1 ใช้ผลจาก Wave 2 pilot ตัดสินว่าจะขยายไป ALT 2 หรือ ALT 3 การอนุมัติ Wave 1 มีขอบเขตตามรายการไฟล์และเกณฑ์ตรวจรับด้านล่าง

<a id="4-proposed-changes-alt-1--wave-1--wave-2"></a>

## 4. Scope

### 4.1 Wave 1 · Workspace Map, Provenance & ADR

| รายการ | การเปลี่ยนแปลงที่เสนอ |
|---|---|
| `AGENTS.md`, `README.md` | อธิบายตำแหน่งของ core, knowledge, pack, product checkout และ local state เพิ่มลิงก์เข้า knowledge index โดยรักษาข้อมูล CI จาก PLAN-009 |
| `docs/knowledge/README.md` | เพิ่มสารบัญและที่มาของความรู้ ระบุว่า approved spec/ADR และ authority order ใน `AGENTS.md` ใช้ตัดสินเมื่อข้อความขัดกัน หลักการจาก benchmark มีสถานะเป็นข้อเสนอจนผ่านกระบวนการอนุมัติ ใช้ 150 บรรทัดเป็นแนวทางสำหรับ reviewer |
| `docs/reference-architecture/benchmarks/claude-ai-native-sdlc-playbook-analysis.md` | ย้ายไป `docs/knowledge/benchmarks/` คงเนื้อหาการวิเคราะห์และเพิ่ม provenance ที่อ้าง path เดิมกับ revision ต้นทาง ตรวจ relative links ของไฟล์ที่ย้าย |
| `ROADMAP.md`, `docs/plans/framework-review-roadmap-v2.md` | เปลี่ยนลิงก์ไปยัง benchmark ตำแหน่งใหม่ใน PR ส่วนการเปลี่ยนสถานะ Roadmap ทำหลัง merge ตาม closeout |
| `docs/reference-architecture/04. Agent Workflows/Testing Agents/function-test-agent.md`, `examples/project-packs/ebmc/README.md` | เก็บ legacy prompt ที่ path เดิมเพื่อรักษาที่มา เพิ่มป้าย historical ใน EBMC README และตรวจว่าลิงก์ต้นทางเปิดได้ |
| `docs/adr/ADR-001-workspace-boundaries.md`, `docs/adr/README.md` | บันทึกการตัดสินใจเรื่องขอบเขตระหว่าง framework repo กับ target repo ใช้เลข ADR ถัดไปหากฐานใหม่มี ADR แล้ว ตั้ง `proposed` จนมีหลักฐาน Human approval และลงสถานะ/index ตาม ADR lifecycle |

ขอบเขต Wave 1 เป็นเอกสาร การแก้ loader, policy, contracts, CI, release หรือ product ต้องระบุในสเปกและขออนุมัติแยก การลบโฟลเดอร์ในเครื่องอยู่นอก scope

### 4.2 Wave 2 · Follow-up สำหรับ runtime pilot และ G8

ก่อนเริ่ม ให้จัดทำ Framework Spec แยกและขอ Gate 2 ใหม่ เลือก target repo สำหรับ pilot แล้วกำหนดว่าจะส่ง **metadata-only** หรือทำให้ CLI/API เลือก checkout ได้จริง หากเลือกอย่างหลัง สเปกต้องระบุ runtime ID, ผู้มีสิทธิ์เลือก target, checkout และ revision, policy/hook source, work-item binding และหลักฐาน verification ที่จะบันทึก

เกณฑ์ตั้งต้นสำหรับร่าง Wave 2

- **P6 evidence:** runtime ตัวอย่าง 2 ตัวและ work item 1 ชุดที่ validator ยืนยันความสัมพันธ์ได้ ระบุส่วนของ P6 ที่ยังค้างก่อนเปลี่ยนสถานะ Roadmap
- **กรณีเลือก execution pilot:** พิสูจน์ flow จาก entry point จริงหนึ่งรอบ ตั้งแต่เลือก runtime จนได้ verification ที่ผูก checkout/revision และ work item เดิมหลัง resume พร้อมกรณี runtime ID ไม่รู้จักหรือ target ที่ไม่ได้รับอนุญาต
- **G8:** ตัดสินว่าจะใช้ pack ด้วยมือหรือรองรับ binding อัตโนมัติ ถ้าเลือกอัตโนมัติ ให้ระบุ role mapping, กติกาชื่อชนกับ core, pack/revision ที่เก็บใน run state, พฤติกรรมเมื่อข้อมูลเปลี่ยน และ state เก่า ทดสอบว่า QA role ที่ผูกกับ EBMCได้รับเฉพาะ skill ที่ผูกไว้, core-only และ role อื่นคงเดิม และ resume ใช้ pack ตัวเดิม
- **ก่อนนำ app เข้า monorepo:** พิสูจน์ผลของ runtime-only, framework-only และ mixed commits ต่อ framework version และ required checks ก่อนอนุมัติเปลี่ยนโครงสร้างหรือ release config

## 5. Verification & Rollback

### Wave 1 Acceptance Criteria

1. ตรวจฐานหลัง integrate PLAN-009 และบันทึก SHA ที่ใช้เทียบ ตรวจ README ที่ซ้อนกันเพื่อรักษาข้อมูล CI ล่าสุด
2. ตรวจจาก Git diff ว่า benchmark ย้ายหนึ่งไฟล์และมี provenance, legacy prompt ยังอยู่ path เดิม และไม่มีไฟล์นอกขอบเขต §4.1 ยกเว้น review และ change digest ตามกติกา
3. ตรวจ local Markdown links และ heading anchors ที่เพิ่มหรือเปลี่ยนในไฟล์ scope เทียบกับไฟล์ tracked และไฟล์ใหม่ที่จะรวมใน PR ตรวจ README, Roadmap, framework analysis และ EBMC README ว่าชี้ไปที่ปลายทางที่เลือก ตรวจว่าไม่มีลิงก์ใช้งานที่ยังชี้ไป path เก่าของ benchmark
4. ตรวจว่า knowledge อ้างแหล่งที่มาได้ และ ADR index ตรงกับสถานะใน ADR ถ้าเป็น `accepted` ต้องมีหลักฐาน Human approval
5. หลังแก้ครั้งสุดท้าย ให้รันชุดตรวจด้านล่างโดยชี้ `SDLC_TRACE_DIR` ไป temporary directory แล้วบันทึก pass/fail/skip จากการรันจริง ให้ผู้ตรวจอิสระตรวจ Wave 1 diff และบันทึกใน `docs/plans/plan-010-review.md` เป็นรอบใหม่ พร้อม digest ก่อนเปิด PR

```bash
python3 scripts/sync-adapters.py --check
python3 scripts/validate-context-budget.py
python3 scripts/validate-contracts.py --check-defaults
python3 evals/run_evals.py --mode contract
python3 -m unittest discover -s tests -v
git diff --check
# ใช้ path จริงของ Change Digest เมื่อเตรียมเอกสารแล้ว
python3 scripts/validate_work_item.py --digest-file docs/handoff/YYYY-MM-DD-workspace-and-runtime-digest.md
```

**Rollback** ให้เก็บการย้าย benchmark พร้อมลิงก์ที่เกี่ยวข้องเป็นชุดเดียวเพื่อให้ย้อนกลับได้พร้อมกัน หาก rollback หลัง merge ให้ revert เฉพาะ Wave 1 ผ่าน PR แล้วตรวจลิงก์เดิมซ้ำ สำหรับ ADR ที่ accepted แล้ว ให้บันทึก ADR ที่ supersede ตาม lifecycle

## 6. Gate 2 Approval

- **Approved scope** `ALT 1 / Wave 1 only` ตาม §4.1
- **Approver** Human Maintainer
- **Decision** `Approved`
- **Recorded at** 2026-11-27 18:15 +07 (Asia/Bangkok)
- **Evidence** ข้อความในแชต “อนุมัติ PLAN-010 ครับ”
- **Wave 2** ต้องมี Framework Spec และหลักฐานอนุมัติ Gate 2 แยก ก่อนเริ่มงาน implementation
