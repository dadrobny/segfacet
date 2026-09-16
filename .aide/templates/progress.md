<!--
  AIDE progress template. Step 3. THE single source of truth for status (item
  specs carry none). Parsed by aide.py and the status report — follow the
  shapes EXACTLY:
    - Stage summary table  | Stage | Title | Objectives | Status |  (Stage = int, Status = one icon)
    - Objective coverage   | Objective | Delivered by | Status |    (Objective starts with G<n>)
    - One "## Stage N — <title> — <icon>" section per stage, each with:
        Deliverables = FLAT bullets "- <icon> <text>. *(Item NNN)*"  (no nested status bullets)
        Acceptance   = "- [ ]" / "- [x]" checkboxes
  A stage's icon and the Status cell of its summary row are DERIVED from the
  Deliverables bullets, and each Objective row's Status cell follows the
  stages that deliver it, subject to the Outcome targets gate — none of them
  is typed; the rows themselves — which objectives exist, which stages
  deliver each — are yours to write. The derivation is stated in
  `python .aide/scripts/aide.py progress -h`; what a stage's ✅ means and how
  the Outcome targets table gates the Objective rows are conventions.md §1 →
  progress.md; what each icon asserts is §1 → Status icons; the two other
  optional tables are §1 → Human gates and §1 → Environment-gated
  capabilities. Read them there; nothing here restates them.
  Optional sections, each deleted if the project has no use for it:
  Environment-Gated Capability Verification, Outcome targets, Human gates.

  Fill-in conventions: `{{slot}}` = literal value; _italic line_ = guidance to
  read then replace. Delete this comment in the generated file,
  and keep the aide-template line below it.
-->
<!-- aide-template: progress 1 -->
# {{project-name}} — Progress Tracker

> **Status:** Draft v1 · **Created:** {{yyyy-mm-dd}}
> Step 3 of the AIDE loop · mirrors [`roadmap.md`](roadmap.md) · the single
> source of truth for status; queue state is derived from it, and item specs
> deliberately carry none.

## Status legend

| Icon | Meaning |
|------|---------|
| 📋 | Planned |
| 🚧 | In Progress |
| 🔍 | In Review |
| ✅ | Complete |
| ⏸️ | Deferred |
| ❌ | Excluded |

## Stage summary

_One row per roadmap stage._

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 0 | {{title}} | (foundation) | 📋 |

## Objective coverage

_One row per vision objective._

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 {{short}} | Stage 1 | 📋 |

## Environment-Gated Capability Verification  <!-- OPTIONAL: delete if not applicable -->

_One row per environment-gated capability (conventions.md §1 →
Environment-gated capabilities says which, and what counts as verified).
Status is `❓ Unverified` until the gated path has run with the dependency
present, then `✅ Verified (YYYY-MM-DD, host/CI description)`. Keep the
`` (`name` profile) `` part only when a `[validation]` profile checks for
the dependency._

| Capability | Package / Tool | Introduced by | Status | Notes |
|------------|-----------------|----------------|--------|-------|
| {{capability}} | {{package or tool name}} (`{{profile}}` profile) | Stage {{n}} *(Item {{nnn}})* | ❓ Unverified | {{notes}} |

## Outcome targets  <!-- OPTIONAL: delete if no roadmap stage commits to a measured result -->

_One row per measured outcome the roadmap commits to. Status is
`❓ Unverified` until measured, then `✅ Met (YYYY-MM-DD, evidence)` or
`❌ Not met (measured result → follow-up)`. What a target gates, and what a
`❌ Not met` obliges, is conventions.md §1 → progress.md._

| Target | Objective | Attempted by | Status | Evidence / follow-up |
|--------|-----------|--------------|--------|----------------------|
| {{measurable target}} | G{{n}} | Stage {{n}} | ❓ Unverified | {{notes}} |

---

## Human gates  <!-- OPTIONAL: delete if no work waits on a person's decision -->

_One row per decision only a person can make. **Blocks** is `stage N`, `all`,
or item numbers (`106`, `110, 111`, `106–108`); **Status** is `⏳ Awaiting`,
then `✅ Approved (YYYY-MM-DD)` or `❌ Declined (YYYY-MM-DD)`.
What each reach holds and why a queue is never one, who may raise and resolve
a gate and how, and why a decline keeps blocking: conventions.md §1 → Human
gates._

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
| {{what must be decided}} | {{item numbers, stage N, or all}} | ⏳ Awaiting | {{notes}} |

---

## Stage 0 — {{title}} — 📋

**Goal.** {{one line}}

**Deliverables.**

_Flat bullets only — one per deliverable, each with its item reference. See
`.aide/conventions.md` §1 for the exact shape._

- 📋 {{deliverable}}. *(Item {{nnn}})*

**Acceptance.**

_One checkbox per acceptance criterion of the matching roadmap stage, ticked
only via `python .aide/scripts/aide.py progress accept` — never by the rollup.
The verbs that correct a box, and why a stage may be ✅ over an unticked one,
are `progress -h` and conventions.md §1 → progress.md._

- [ ] {{acceptance check}}

---

_Repeat "## Stage N — Title — icon" per stage._
