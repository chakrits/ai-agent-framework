---
review_id: REV-010
spec_ref: PLAN-010
review_stage: pre_gate_2
base_commit: 3f082dcb717f1a32aa3644f7272262965b2ef4da
reviewed_draft_sha256: c1b00f7ff7747ab5083fed54856afadcbc58c89035e7428f5839bab1806add9f
verdict: changes_requested
---

# PLAN-010 Architecture Review

ตรวจร่างที่ยังไม่อยู่ใน Git จาก worktree `.worktrees/PLAN-010` บน branch `docs/PLAN-010-workspace-and-runtime-architecture` อ้างเลขบรรทัดของ [ร่าง PLAN-010](plan-010-workspace-and-runtime-architecture.md) ณ SHA-256 ด้านบน

**คำตัดสินก่อน Gate 2** ขอให้แก้แผนก่อนอนุมัติ เลือก **ALT 1 ฉบับจำกัด scope** ให้ Wave 1 รับผิดชอบโครงเอกสารและแหล่งอ้างอิง ส่วน pilot ที่ต้องเปลี่ยนพฤติกรรมให้มีสเปกและ Gate 2 ของตัวเอง การแยก core, knowledge, pack และ product เป็นกรอบที่ใช้ได้ แต่สอง wave ในร่างมีผลส่งมอบและหลักฐานคนละแบบ

## Findings

### M1 · Wave 2 ยังส่งมอบ Runtime Onboarding ตาม P6 ไม่ได้

แผน §4 บรรทัด 118–125 ระบุ schema, registry, validator และคู่มือ ตัวรับงาน CLI/API ไม่มี runtime selector ส่วน service สร้าง state โดยตั้ง `workspace_root` เป็น root ของ framework และใช้ `DryRunExecutor` ทั้งตอนเริ่มและอนุมัติ gate จากการรันจริง state ที่บันทึกยังไม่มี runtime ID หรือ work-item ID ส่วน executor แบบ CLI ถ้าถูกนำมาใช้ จะตั้ง cwd จาก `state.workspace_root` โดยตรง เมื่อมี registry เพิ่มขึ้น ผู้ใช้จึงยังไม่มีทางส่งงานไปที่ application checkout จาก entry point ที่ระบุในแผน

P6 ระบุผลส่งมอบเป็น runtime ตัวอย่างสองตัวและ work item หนึ่งชุดที่ผ่าน validator รวมถึงรายการงาน STATUS, CHANGELOG และ work log แผนยังไม่กำหนด fixture ที่พิสูจน์ความเชื่อมโยงนี้ ให้แยกว่ารอบนี้ส่งเพียง **runtime metadata** หรือจะรองรับ **การเลือก checkout สำหรับ run** หากเลือก metadata ให้ยืนยันจากสอง fixture และ work item หนึ่งตัวอย่าง พร้อมคง P6 เป็นงานบางส่วนจนกว่าจะตรงเกณฑ์ Roadmap หากเลือกการรัน ให้กำหนดผู้มีสิทธิ์เลือก target, revision, hook/policy source, cwd, work item และชื่อ field ที่ใช้เก็บหลักฐาน

หลักฐาน [Roadmap P6](../../ROADMAP.md#p6-runtime-registry--work-records--) · [CLI](../../orchestrator/cli.py#L17) · [API request](../../orchestrator/api/main.py#L45) · [เริ่ม run](../../orchestrator/api/handlers.py#L69) · [executor](../../orchestrator/graphs/sdlc_pipeline.py#L52)

### M2 · แก้ G8 ที่ loader อย่างเดียวแล้ว pack ยังหลุดตอนผ่าน Gate

`load_framework(project_pack="ebmc")` โหลด `robot-framework-ebmc` เข้า dictionary แต่ไม่โหลด wrapper agent หรือใช้ `extends` ส่วน `assemble_agent_prompt()` อ่านเฉพาะ skills ที่ role ผูกไว้ Probe ยืนยันว่า prompt ทั้ง **7/7 roles เหมือนกันทุกตัว** ระหว่าง core กับ EBMC นอกจากนี้ service probe ซึ่งใช้ state/telemetry ใน temp dir พบ loader ถูกเรียกด้วย `['ebmc', None]` ตอนเริ่ม run แล้วอนุมัติ Gate 1 ตามปกติโดยไม่ส่ง pack ซ้ำ เพราะ state ไม่เก็บ pack ส่วน request ตอน approve รับ pack ได้อิสระ เมื่อเริ่มฉีด pack จริง จุดนี้ทำให้คำสั่งที่ใช้หลังผ่าน gate เปลี่ยนไปตาม request ได้

กำหนด mapping จาก pack ไปยัง role อย่างชัดเจน เลือกว่าจะรองรับ wrapper/extends หรือใช้ manifest แบบง่าย ให้ core เป็นเจ้าของ skill ชื่อเดิมและ reject ชื่อชน เพราะปัจจุบันใช้ `dict.update()` หลังโหลด core ถ้ารองรับ run/resume ให้ผูก pack ที่ validate แล้วตอน start และโหลดค่าเดิมจาก state ตอน approve ระบุพฤติกรรมเมื่อ pack หรือ revision เปลี่ยน และกรณี resume state เก่า เพิ่ม regression ที่พิสูจน์ว่า QA เห็น EBMC, roles ที่ไม่เกี่ยวข้องไม่เห็น, no-pack prompt คงเดิม และ resume ไม่ทำ pack หลุดหรือเปลี่ยนตัว

Unit test เดิม assert แค่ว่า skill อยู่ใน dictionary และ core ISTQB ปรากฏใน prompt ส่วน EVAL-009 แบบ contract ตรวจ sample output จึงผ่านได้แม้ G8 ยังอยู่

หลักฐาน [Loader](../../orchestrator/core/loader.py#L98) · [EBMC wrapper](../../examples/project-packs/ebmc/agents/ebmc-function-test-agent.md#L1) · [Approve handler](../../orchestrator/api/handlers.py#L109) · [State serialization](../../orchestrator/core/state_store.py#L109) · [Loader test](../../tests/test_phase4_orchestrator.py#L34) · [EVAL-009](../../evals/datasets/09-ebmc-project-pack-overlay.json) · [Contract evaluator](../../evals/run_evals.py#L132)

### M3 · ขอบเขต release และ CI ของ product ยังไม่มีเงื่อนไขตรวจรับ

Release config มี package เดียวที่ `"."` และ workflow ทำงานเมื่อ push เข้า `main` ส่วน CI มีหก jobs จาก matrix OS/Python และทุก job ใช้ framework suite ชุดเดียว ร่าง §4 บอกให้แก้ release config แต่ยังไม่เลือกนโยบายสำหรับ runtime-only, framework-only และ mixed changes หรือตั้งเงื่อนไขสำหรับ required checks ของแต่ละกรณี จึงยืนยันได้ว่ามีจุดเสี่ยงจาก config ร่วมกัน ส่วนคำอ้างว่าจะ bump framework version ทุกกรณียังไม่มีหลักฐานจาก release run

สำหรับ runtime ที่ปล่อยอิสระ ให้ใช้ target repo เดิมใน pilot และบันทึก revision อ้างอิงกลับมา ถ้าจะเพิ่ม monorepo ในรอบถัดไป ให้ทดสอบผล release ทั้งสามกรณี ตรวจว่าชื่อ required checks และผลรวมของ CI ใช้งานได้ แล้วระบุวิธีย้อน config Artifacts ของ Framework ตอนนี้ใช้ `docs/plans/` และ state อยู่ `.sdlc/` อยู่แล้ว

หลักฐาน [Release config](../../release-please-config.json#L8) · [Release workflow](../../.github/workflows/release-please.yml#L8) · [Validation matrix](../../.github/workflows/validate.yml#L3) · [Artifact placement](../contracts/README.md#canonical-artifact-placement)

### M4 · Baseline และลำดับงานของ Wave 1 ต้องแก้ก่อนอนุมัติการลบหรือย้าย

- ใน PLAN-010 พบ archive **2 ไฟล์และ 0 โฟลเดอร์ย่อยว่าง** ส่วน `.sdlc-telemetry/` ไม่มีอยู่ ตัวเลข **60 โฟลเดอร์ว่าง** และ telemetry dir ว่างมาจาก worktree หลักคนละ branch ตามที่นับซ้ำได้ จึงให้ดูแลเป็น local hygiene แยกจาก patch การตรวจ empty dir ทั้ง `docs/` ผ่านอยู่แล้วใน checkout นี้และขึ้นกับไฟล์ท้องถิ่น หากย้าย reference ให้ verify ลิงก์ใน README, Roadmap, EBMC README และ roadmap analysis เดิม ใช้ Git history/revert สำหรับไฟล์ tracked และแยกการตัดสินใจเกี่ยวกับ legacy prompt ให้ชัด ถ้ายังไม่มีเหตุผลที่จะลบ ให้คง archive พร้อมป้าย historical หรือย้ายพร้อม provenance ต้นทาง
- `README.md` ถูกแก้แล้วบน PLAN-009 ที่ `f4edda2` และอยู่ใน scope PLAN-010 ด้วย จึงมีจุดประสานงานที่ทราบจริง ส่วน merge conflict ยังไม่ได้ทดสอบ ให้ตรวจฐานใหม่และลิงก์หลัง integrate PLAN-009 หรือตัดส่วน README ที่ซ้อนกัน
- แผนวาง `ROADMAP.md` ไว้ใน implementation แต่ AGENTS ให้ทำ status closeout หลัง merge ถ้าต้องย้ายลิงก์เพื่อให้ยังเปิดได้ ให้เขียนในแผนชัดว่าแก้ลิงก์ใน PR และบันทึกความคืบหน้าหลัง merge สำหรับ ADR ให้ร่าง decision ที่ต้องการตัดสินจริงและผูกหลักฐาน Gate 2 ก่อนตั้งเป็น accepted ADR README มีอยู่แล้ว

หลักฐาน [ร่าง §4–5](plan-010-workspace-and-runtime-architecture.md#4-proposed-changes-alt-1--wave-1--wave-2) · [Closeout](../../AGENTS.md#3-lifecycle--tiered-gate-governance) · [Archive rule](../../AGENTS.md#L128) · [README](../../README.md#L69) · [Roadmap](../../ROADMAP.md#L4) · [Framework analysis](framework-review-roadmap-v2.md#L223) · [EBMC provenance](../../examples/project-packs/ebmc/README.md#L5) · [ADR lifecycle](../adr/README.md#L5)

### m1 · ระบุที่มาและอำนาจของ Knowledge ก่อนเขียนกฎเพิ่ม

`AGENTS.md` ใช้ Rank 5 กับ handoff และ trace ร่างยังไม่อธิบายว่า knowledge ที่โยงข้อกำหนดที่อนุมัติแล้วมีผลอย่างไรเมื่อข้อความขัดกัน ให้เก็บ knowledge เป็นคำอธิบายที่มีลิงก์และสถานะ ตรวจย้อนหา approved spec/ADR ได้ ให้กฎที่ต้อง enforce มี canonical owner และ test ที่เจาะพฤติกรรม ตัวตรวจ context budget ปัจจุบันไม่มี glob สำหรับ knowledge ถ้าจะใช้เพดาน 150 บรรทัด ให้ระบุว่าเป็นแนวทางสำหรับ reviewer หรือเพิ่ม exact check ในขอบเขตที่อนุมัติ

หลักฐาน [Authority order](../../AGENTS.md#5-source-of-truth--knowledge-loop) · [Context budgets](../../scripts/validate-context-budget.py#L11)

### m2 · แยก path policy, ธรรมเนียม และชื่อที่ใช้ในงานจริง

`docs/contracts/**` ถูกคุ้มครองทั้ง subtree ส่วน operating model ที่อยู่ใน protected globs คือ `constitution.md` เท่านั้น Wave 1 มี 0 ไฟล์ที่ตรง protected globs ตามรายการปัจจุบันและยังต้องมีอนุมัติ Gate 2 กับ archival decision ก่อนแก้ archive ส่วน Wave 2 อาจต้องแตะ tracked tests หรือ CI ตาม acceptance criteria จึงต้องระบุผู้รับผิดชอบแต่ละไฟล์ตาม role policy ข้อความว่าได้คุณค่า 85–90% และตัวเลขไฟล์ของ ALT 2/3 ยังไม่มีวิธีนับในแผน เก็บคำเปรียบเทียบเชิงคุณภาพหรือแนบ inventory ที่คำนวณซ้ำได้

ใช้คำให้แยกชัดว่า `runtimes/` คือแนวคิดที่เสนอสำหรับ product, `.sdlc/` เก็บ state ในเครื่อง และ `.worktrees/PLAN-010` เป็น Git checkout ที่มีอยู่จริง ตัวช่วย `scripts/worktree.py` รองรับ ID `INT-xxx` และสร้าง `feat/` เท่านั้น ให้คู่มือ framework worktree ระบุวิธีสำหรับ `PLAN-xxx` ตามที่เลือก

หลักฐาน [Guard globs](../../scripts/sdlc_guard/policy.json#L9) · [Role-scoped paths](../../scripts/sdlc_guard/policy.json#L23) · [Worktree helper](../../scripts/worktree.py#L23) · [ร่าง §2–3](plan-010-workspace-and-runtime-architecture.md#2-three-unified-alternatives-alt-1-vs-alt-2-vs-alt-3)

## Council Pressure-Test

- **Contrarian** — “ถ้า gate อนุมัติ run ที่เริ่มด้วย EBMC แต่ resume กลับใช้ core อย่างเดียว การแก้ prompt ที่ loader จะทำให้ความต่างนี้มีผลจริง แม้ test suite เดิมเขียวทั้งหมด”
- **First Principles** — ระบุเจ้าของ runtime identity และหลักฐานที่ต้องตามข้าม Gate ก่อนเลือกตำแหน่ง directory
- **Expansionist** — ใช้ contract เดียวสำหรับ runtime ตัวอย่างและ target repo เมื่อมี pilot ยืนยันว่าต้องใช้ซ้ำ
- **Executor** — ส่งมอบ Wave 1 ที่ตรวจลิงก์และย้อนกลับได้เป็นชุดเล็ก จากนั้นพิสูจน์ flow เดียวที่เริ่มจาก registry ไปถึงผล verification
- **Outsider** — คู่มือต้องพาไปถึงคำสั่งที่รับ runtime ID และได้ผลที่อ้าง work item กลับมา บอกให้ชัดถ้ารอบนี้ยังเป็น metadata-only

## ALT 3 ทางเลือก

| ทางเลือก | ขอบเขตและผลตรวจรับ | Trade-off |
|---|---|---|
| **ALT 1 · Surgical แบบลด scope (แนะนำ)** | Wave 1 ทำแผนที่ workspace, เก็บ provenance และบันทึก ADR เฉพาะ decision ที่ต้องตัดสิน ทดสอบลิงก์จาก tracked content หลัง integrate PLAN-009 ต่อด้วย Wave 2 ที่มี Gate 2 แยก ใช้ target repo ที่เลือกเพื่อทำ pilot และ fixtures สำหรับ P6 กำหนด G8 แยกเป็น manual pack หรือ explicit binding พร้อม start/resume test | ส่งมอบเร็วและพิสูจน์ความต้องการก่อนสร้าง runtime platform การรองรับ monorepo รอหลักฐานจาก pilot |
| **ALT 2 · Monorepo พร้อม CI/release แยกส่วน** | เพิ่ม registry และ runtime selectors พร้อม path/permission policy, work-item binding, fixtures และ CI/release scenarios ทั้งสามแบบ ค่อยย้าย `governance/` หาก inventory ยืนยันว่าจำเป็น | รองรับ app ใน repo เดียว ต้นทุน CI, rollback และการรักษา compatibility สูงขึ้น |
| **ALT 3 · Package แบบ pin เวอร์ชันสำหรับหลาย repo** | ให้ consumer ติดตั้งจาก release ที่ pin ด้วย lock มี install/update/rollback และ CI smoke ที่พิสูจน์บน repos ที่เป็นอิสระ | เหมาะกับหลายทีมที่ต้องอัปเกรดต่างจังหวะ เพิ่ม compatibility matrix และภาระดูแล installer เหมาะหลังมี P9 pilot และผู้ใช้ภายนอก workspace ที่ต้องใช้ซ้ำจริง |

**Recommendation** แก้ §4–6 ให้ Gate 2 รอบนี้ตัดสินเฉพาะ Wave 1 กำหนดว่าจะเก็บหรือย้ายไฟล์ archive ทีละรายการ ระบุ scope, acceptance criteria และ rollback แล้วเปิดสเปก Wave 2 แยกเมื่อพร้อมตัดสินเรื่อง runtime identity และการเก็บ pack ข้าม Gate ให้แผน Wave 2 ระบุหลักฐานที่ต้องเห็นจาก target checkout จริงและเงื่อนไขก่อนปิด P6

## Verification Evidence

รันจาก worktree ที่ระบุบน macOS / Python 3.14.10 ตั้ง trace store ของการรันทดสอบเป็น temp dir

| คำสั่งหรือ probe | ผลที่เห็น |
|---|---|
| `python3 scripts/sync-adapters.py --check`, `python3 scripts/validate-context-budget.py`, `python3 scripts/validate-contracts.py --check-defaults` | ผ่านทั้งหมด |
| `python3 evals/run_evals.py --mode contract` | ผ่าน 10/10 |
| `python3 -m unittest discover -s tests -v` | 252 tests, ผ่าน 249, ข้าม 3 (Windows launcher 2, FastAPI dependency 1) |
| เรียก `load_framework()` และ `assemble_agent_prompt()` จาก worktree | EBMC skill อยู่ใน bundle, เพิ่ม agent 0 ตัว, prompt เท่ากับ core 7/7 |
| เรียก `OrchestratorService.start_run()` และ `approve_run_gate()` โดยใช้ state/telemetry ชั่วคราว | คง cwd ของ framework และ pack เปลี่ยนจาก `ebmc` เป็น `None` เมื่อ approve request ไม่ส่ง pack |
| `git diff --name-status 3f082dc...feat/PLAN-009-ci-evidence-and-trace-scrub` | ยืนยันว่า branch PLAN-009 แก้ README และ CI จริง |

ผลทดสอบเป็น baseline สำหรับร่างนี้ Wave 2 validator, GitHub release behavior, Docker และ end-to-end ข้าม application ยังไม่ได้ตรวจรัน

## Round 2 · Independent Wave 1 Implementation Review

- **Reviewed base** `f80092e6a9a40e83de2bd06d4d6232ec4ae3deae` หลังรวม PLAN-009
- **Scope** docs-only Wave 1 จาก Gate 2 ที่อนุมัติ ตรวจ diff ทั้ง tracked และไฟล์ใหม่ใน worktree PLAN-010
- **Reviewer** independent Codex reviewer pass
- **Verdict** ผ่านการตรวจอิสระ ไม่มีข้อค้าง

ผู้ตรวจยืนยันขอบเขตไฟล์, legacy EBMC prompt ตรงกับต้นฉบับทุกไบต์, ข้อความ CI ของ PLAN-009 ใน README ยังอยู่ และ ADR/index ตรงกันที่ `proposed` ลิงก์ภายในที่เพิ่มหรือเปลี่ยน 55 รายการรวม anchors ผ่านการตรวจ และตัวตรวจ Change Digest ผ่าน

ผู้ตรวจขอแก้ถ้อยคำ provenance ให้ชัดว่า `f80092e` เป็น revision ที่ใช้เป็นต้นทางการย้าย ผู้ลงมือแก้ข้อความเป็น “Moved from … as recorded in …” และผู้ตรวจยืนยันซ้ำว่าเนื้อหา benchmark ตรงกับต้นฉบับทุกไบต์เมื่อไม่นับข้อความ provenance ที่เพิ่ม `git diff --check` ผ่าน

Gate 3 Human sign-off ยังรอการพิจารณา
