<!-- aide-template: item 3 -->
# Item 236 — Stage archive made safe, then run

> **Created:** 2026-10-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-032.md`](../queue/queue-032.md) · Item 236
> **Objectives:** G7
> **Suggested branch:** `aide/236-stage-archive-made-safe-then`

---

## Description

`aide progress archive` (engine 2.50.0 on) moves each settled stage's section
out of `progress.md` into `progress/stage-N.md`, and its roadmap section into
`roadmap/stage-N.md`. The stage's Stage summary row stays, its Title cell
turned into `[<title>](progress/stage-N.md)`. The archive was tried and undone
on 2026-10-16, because two things in this repository break when it runs. This
item fixes both, settles the two items whose bullets span two stages, and
names the archive run that follows the merge.

**1. The status report follows the archive link** (insight `2026-10-16-50cf`).
`scripts/aide_status_report.py` builds its stage and item model from
`progress.md` alone. Once a stage is archived, every item whose bullets sit
in it drops out of the report, and the stage's title reads as Markdown link
source. The generator is changed to read each archive file a summary row
links to, and to show the row's title without the link. The script is
project-owned (it is not in `.aide/adapter-manifest.txt`). Its skill,
`.claude/skills/aide-status-report/SKILL.md`, is framework-owned and is not
edited.

**2. Tests stop reading archived sections out of `progress.md` and
`roadmap.md`** (insight `2026-10-16-c3e4`). On 2026-10-17 the archive of 19
stages, run in a `git worktree` of `main` at `5b80c1d`, left the suite at 33
failed, 8121 passed and 73 skipped. The failures sat in 11 files plus
`test_aide_status_report::test_build_report_model_on_real_docs`. Nearly all
of them pin the loop's own attestation state, such as a box's tick, a bullet's
icon, or a dated count or wording written into a stage section. Those are
retired under the 2026-09-16 precedent (`CLAUDE.md`, "Updating the
framework", step 4). The one test that uses a stage section to check
something outside the two documents is repointed to read the archive file.
The list is under Testing Strategy.

**3. Items 006 and 204 each end up in one stage.** The archive refuses a
stage when an item its bullets name has a bullet in another stage. Item 006
has a bullet in Stage 0 and one in Stage 1, so both stages are held back.
Item 204 has a bullet in Stage 32 (D3) and one in Stage 33 (D6), so those two
are held back as well. This item takes item 006 off Stage 1's marker and
item 204 off Stage 32's. Each change gets a dated trail line saying where
that item's deliverable is recorded (Implementation Step 1).

**4. The archive run itself, after the merge.** The verb refuses on a claim
branch, so it is not part of this item's diff. Once item 236 has merged into
`aide/queue-032`, the orchestrator runs
`python .aide/scripts/aide.py progress archive` there. Measured on
2026-10-17 at `34db8bea` with step 3 applied (Assumption A1), the run
archives **23 stages: 0–10, 12–14, 18–20, 27, 28 and 30–33**. It keeps 15,
17, 26 and 29 and prints why. Stages 11, 16, 21–25, 34 and 35 are not
✅ or ❌, so the run neither archives nor prints them.

**Not in scope:**
- Any `.aide/**` or `.claude/**` file. The engine's archive and unarchive
  behaviour is taken as it ships (A1, A2).
- Regenerating `docs/aide/status/index.html`. It is a snapshot that
  `/aide-status-report` rewrites, and regenerating it here would also rewrite
  unrelated live status (the item 226 precedent).
- Grouping archived stages under their `# Phase N` header in the report
  (Left open, below).
- Tests that pin attestation state but do not fail once the archive has run,
  such as test_135's Stage 29 boxes and test_115's Stage 26 boxes. They read
  stages the archive keeps, and retiring them is not needed to make the
  archive safe.

## Acceptance Criteria

The trees these criteria name are built by the test from the repository's
own documents (Testing Strategy). The **unarchived tree** is `progress.md`
with every archived section put back by the engine's
`unarchive_stage_text`. The **archived tree** is the unarchived tree with
every stage that the engine's `archive_refusal` accepts moved out by
`archive_stage_text`. Both trees exist whether or not the real archive has
run yet, so every criterion is tested before and after it.

- [ ] **AC1: Archived items keep their status.** The mapping from item number
  to status that `build_report_model` returns over the archived tree equals
  the mapping it returns over the unarchived tree.
- [ ] **AC2: An archived item is reported under its own stage.** For every
  `progress/stage-N.md` in the archived tree, and every item that the engine's
  `stage_item_numbers` reads from that file's Stage N section, the model built
  over the archived tree gives that item stage `"N"`.
- [ ] **AC3: The stage list is unchanged by archiving.** The list of
  `(number, title, objectives, status)` tuples in `model.stages`, built over
  the archived tree, equals the same list built over the unarchived tree.
- [ ] **AC4: Item 006 sits in one stage.** Across the stage sections of the
  repository's `docs/aide/progress.md` and every `docs/aide/progress/stage-N.md`,
  the set of stages whose deliverable bullets name item 006 (the engine's
  `stage_item_numbers`) is exactly `{0}`.
- [ ] **AC5: Item 204 sits in one stage.** Read the same way as AC4, the set
  of stages whose deliverable bullets name item 204 is exactly `{33}`.

## Assumptions

- **A1 (engine 2.52.2): what the archive does, and what it takes here.**
  `archive_stage_text` moves a stage's section, heading included, into
  `progress/stage-N.md` under one `> Stage N's section, archived from …`
  line. It rewrites the summary row's Title cell to
  `[<title>](progress/stage-N.md)` and keeps the Status cell. The roadmap
  half moves to `roadmap/stage-N.md` and leaves a stub heading in
  `roadmap.md`. `archive` and `unarchive` refuse on a claim branch. A stage is
  refused while an item named by its deliverable bullets has a deliverable
  bullet elsewhere. Acceptance boxes and indented trail lines are not
  deliverable bullets for this check (`_parse_item_status`). *Measured
  2026-10-17* in a detached `git worktree` of `34db8bea`: with Step 1's
  two marker edits and trail lines applied, `python
  <wt>/.aide/scripts/aide.py --repo <wt> progress archive --no-commit`
  archived the 23 stages named in the Description, and kept 15 (five open
  bullets), 17, 26 and 29 (each with an unticked box). `aide check` on the
  result reported no error. Without the edits, Stages 0, 1, 32 and 33 are
  kept as well (the orchestrator's 2026-10-17 probe). Nothing a queue-032
  sibling changes reaches these stages: queue-032 lists only Stage 34 items,
  and no claim branch of an item in the 23 stages is unmerged.
- **A2 (engine 2.52.2): the engine functions the new tests call.** They load
  `.aide/scripts/aide.py` by path, as `tests/test_169_stage32_validation.py`'s
  `_aide_module()` does. The calls are `stage_sections(lines)` and
  `stage_section(lines, stage)` (`(start, end, number)` triples),
  `stage_item_numbers(lines, stage)`, and
  `archive_refusal(ddir, lines, stage, None, [])`. With `branches=None` it
  skips the git half. With `rlines=[]` it ignores the roadmap, and with no
  `queue/` folder under `ddir` it reads no queue. The last two calls are
  `archive_stage_text(text, stage)`, which returns
  `(progress_text, archive_text)`, and
  `unarchive_stage_text(text, archive_text, stage)`. Every one of them works on
  an archive file's lines too, because the file keeps the `## Stage N`
  heading.
- **A3: the two marker edits are hand edits, and they move no status.** No
  verb moves an item marker. `aide progress reword --item` refuses a bullet
  whose marker names several items, and it keeps the marker it finds.
  `progress.md` is authorised for every item. Both bullets stay ✅, so no
  rollup cell changes. A ✅ bullet with no marker draws no `aide check`
  warning (measured, A1).
- **A4: which stage keeps each item.** Item 006 keeps Stage 0. Its spec
  delivers the CLI entry point, which is Stage 0's bullet. Stage 1's
  "CLI wires loader → …" bullet goes to item 010 alone, since 010 already
  has the Stage 1 human-report bullet. Item 204 keeps Stage 33, whose
  validation it is (D6). Stage 32's D3 bullet loses its marker and keeps
  its ✅, because the D3 re-run shipped as part of item 204.
- **A5: the reconciliation rule** (the 2026-09-16 precedent named in
  `CLAUDE.md`, "Updating the framework", step 4, and `.aide/conventions.md`
  §6). Some failing tests assert on `progress.md` or `roadmap.md` bookkeeping
  itself: a box's tick, a bullet's icon, an annotation, trail or evidence
  text, or a count or wording recorded in a stage section. Those are
  retired. A synthetic companion goes with them when its only subject is a
  helper that no remaining test calls. A test that uses a stage section as
  input to check something outside the two documents is repointed. It reads
  the archive file when the file exists and the live document otherwise, so
  it passes before and after the archive run. A retirement leaves a dated
  comment block where the test stood, naming item 236 and the reason, and the
  module docstring's AC list says so (the shape of
  `tests/test_135_stage29_validation.py`'s AC26–AC28 blocks).

## Implementation Steps

No dependency is added, and the report script gains no engine import.

1. **Settle items 006 and 204 in `docs/aide/progress.md`** (A3, A4). This is
   a hand edit of two lines, each followed by one new trail line:
   - Stage 1. Change
     `- ✅ CLI wires loader → empty-check → verdict → both report formats. *(Items 006, 010)*`
     to end `*(Item 010)*`, and add beneath it:
     `  - **2026-10-17** → item 006 taken off this bullet's marker by item 236: item 006's deliverable is the CLI entry point, Stage 0's bullet, which this wiring extends.`
   - Stage 32, D3. The bullet's last line is
     `  refined and those left as documented drafts. *(Item 204)*`. Drop the
     ` *(Item 204)*` and add beneath it:
     `  - **2026-10-17** → item 204 taken off this bullet's marker by item 236: item 204 delivered this re-run as Stage 33's D6 bullet, which carries its marker.`

   Then `python .aide/scripts/aide.py check` must report no error.
2. **`scripts/aide_status_report.py`: strip and record the archive link.**
   Give `Stage` an `archive: Optional[str] = None` field. In
   `parse_progress`'s Stage-summary branch, a Title cell matching
   `^\[(.*)\]\((progress/stage-\d+\.md)\)$` sets `title` to group 1 and
   `archive` to group 2. Every other title is kept as written.
3. **`build_report_model`: read each linked archive file.** After
   `parse_progress`, take each stage whose `archive` is set and whose
   `aide_dir / archive` is a file. Read it, take the third value of
   `parse_progress(archive_text)` (its item map, never its stages or
   objectives), and merge it into `item_status`. An archive entry replaces
   the existing one when its `_STATUS_RANK` is at least as high, and it
   records `stage.number` as the stage. That keeps the max-rank status
   (AC1) and makes the deliverable's own stage win a tie (AC2). A link to a
   missing file is skipped: the stage is still listed, and none of its items
   are added.
4. **Reconcile the tests listed under Testing Strategy** (test-writer).
   Follow A5.
5. **After the merge (orchestrator, on `aide/queue-032`, not this
   branch).** Run `python .aide/scripts/aide.py progress archive`. Expect
   the 23 stages of the Description to be archived, and expect 15, 17, 26
   and 29 printed as kept. A different list means a stage's state moved
   after 2026-10-17. Read the verb's reason before going on. Then run
   `python .aide/scripts/aide.py check`, and the suite as `aide merge` runs
   it.

## Authorised paths

**May change:**

- `scripts/aide_status_report.py` — follows the archive link (Steps 2–3)
- `tests/test_236_stage_archive_safe.py` — new module, AC1–AC5 and the adversarial case
- `tests/test_070_acceptance_stage9.py` — AC11 repointed to also read `roadmap/stage-9.md`
- `tests/test_105_golden_decision_table.py` — AC12's real-document test and its companions retired
- `tests/test_106_stage19_validation.py` — Stage 19 section tests and companions retired
- `tests/test_110_neighbourhood_wiring.py` — AC12's three item-024 wording tests retired
- `tests/test_115_stage26_validation.py` — AC7's item-024 wording test retired
- `tests/test_125_stage28_validation.py` — AC17's Stage 28 box tests and companions retired
- `tests/test_135_stage29_validation.py` — AC12's Stage 28 box test retired
- `tests/test_150_maintainer_sign_off.py` — AC13's Stage 20 bullet-icon test retired
- `tests/test_151_stage30_validation.py` — AC35–AC37's Stage 30 tests and companions retired
- `tests/test_161_stage31_validation.py` — AC14, AC15 and the spliced-trail test retired, with companions
- `tests/test_169_stage32_validation.py` — AC6, AC7 and AC13's Stage 20 tests and companions retired

**Asserts against:**

- `.aide/scripts/aide.py` — the AC tests build both trees through its archive and unarchive functions (A2) and read item stages through `stage_item_numbers`
- `docs/aide/progress/*.md` — AC1–AC5 read every archive file present, so the tests hold after the post-merge run
- `docs/aide/roadmap.md` — the repointed test_070 AC11 reads Stage 9's wording here before the archive run
- `docs/aide/roadmap/stage-9.md` — the same test reads it here after the run

## Testing Strategy

New module: `tests/test_236_stage_archive_safe.py`. It imports the report as
`tests/test_aide_status_report.py` does and the engine as
`tests/test_169_stage32_validation.py`'s `_aide_module()` does.

**Building the two trees.** One module-scoped fixture builds both under
`tmp_path_factory`, with no `items/` or `queue/` folder, so the model's
items come from `progress.md` and its archive alone:

- **Unarchived tree.** Start from `docs/aide/progress.md`'s text. For each
  `docs/aide/progress/stage-N.md`, in ascending N, apply
  `unarchive_stage_text(text, archive_text, N)`. Before the post-merge run
  there are none, so the text is the live file.
- **Archived tree.** Start from the unarchived text. For each stage that
  `stage_sections` returns, in ascending order, re-read the current lines and
  ask `archive_refusal(dir, lines, num, None, [])`. When it returns `None`,
  apply `archive_stage_text`, write the archive half to
  `progress/stage-<num>.md`, and carry on with the new progress text.
- The fixture asserts that the archived tree holds at least one archive
  file, so AC1–AC3 cannot pass by comparing a tree with itself.
- Both models are built by `build_report_model(aide_dir=<tree>, now=<fixed>)`.

**One test per AC:**

- AC1 compares `{i.number: i.status}` over the two models.
- AC2 walks the archived tree's `progress/stage-N.md` files and their
  `stage_item_numbers`.
- AC3 compares the stage tuples.
- AC4 and AC5 walk the repository's own `docs/aide/progress.md` sections
  (`stage_sections` plus `stage_item_numbers`) and every
  `docs/aide/progress/stage-N.md`, and collect the stages that name the item.

**Adversarial case, the only one:**

- `dangling-archive-link`: a tmp tree whose summary row links to a
  `progress/stage-N.md` that does not exist still builds a model. That stage
  is in `model.stages` with its plain title, and no exception is raised.
  This guards the generator dying on a half-done archive or unarchive in a
  working tree.

**Existing test that must pass unchanged:**
`tests/test_aide_status_report.py::test_build_report_model_on_real_docs`. It
asserts item 026 is complete. It passes before the archive run, through
`progress.md`, and after it, through `progress/stage-4.md` (Steps 2–3).

**Existing tests to reconcile** (test-writer, under A5). This list comes from
reading the 11 failing files the 2026-10-17 probe named. It found 34 failing
cases, counting test_150's four parametrised cases, against the probe's 33.
Treat it as a lower bound (the `CLAUDE.md` gotcha on spec-time probes):
Validation step 3 checks that it is complete. No test reads Stages 0, 1, 32
or 33 from either document, so archiving those four adds nothing here. The
mentions of `## Stage 32` in test_161 are synthetic text, and test_168 and
test_203 read only Human gates rows, which stay in `progress.md`.

- **Repoint** — `tests/test_070_acceptance_stage9.py::test_ac11_stage9_acceptance_sentence_constant_matches_roadmap_wording`.
  It checks the module's own `STAGE9_ACCEPTANCE_CRITERIA` constant against
  the roadmap. Search the normalised text of `roadmap.md` followed by
  `roadmap/stage-9.md` when that file exists.
- **Retire** — `tests/test_105_golden_decision_table.py`:
  `test_ac12_real_progress_md_stage19_checkbox_is_honest`, plus
  `_stage19_signoff_block`, `_ac12_signoff_ok` and the three
  `test_adv_ac12_*` cases that only exercise them.
- **Retire** — `tests/test_106_stage19_validation.py`:
  `test_ac1_real_progress_md_reports_signed_off`,
  `test_ac3_biconditional_holds_on_real_progress_md`,
  `test_ac4_deliverable_bullets_are_ticked_when_signed_off`,
  `test_ac19_checkbox2_carries_honest_partition_if_ticked`,
  `test_ac20_checkbox1_carries_generated_and_can_fail_evidence_if_ticked`,
  `test_ac22_annotations_state_stage19_decides_stage21_executes_if_ticked`
  and `test_ac24_no_annotation_asserts_real_data_coverage`. The companions
  go too: the `test_adv_signoff_state_*` cases,
  `test_ac3_biconditional_passes_in_both_consistent_states`, the
  `test_adv_ac3_*` cases, and `_stage19_section` with any other helper left
  with no caller. `test_ac21_environment_gated_table_row_count_and_status_cells_unchanged`
  reads the Environment-Gated table, which stays, and is kept.
- **Retire** — `tests/test_110_neighbourhood_wiring.py`: the three `test_ac12_progress_*`
  cases and `_progress_item024_lines`. Item 024's bullets sit in Stage 3.
- **Retire** — `tests/test_115_stage26_validation.py`:
  `test_ac7_progress_md_item_024_bullets_match_observable_behaviour`. Its
  AC12 and AC13 tests read Stage 26 and the Environment-Gated table, which
  both stay, and are kept.
- **Retire** — `tests/test_125_stage28_validation.py`: `test_ac17_stage28_has_five_acceptance_boxes`,
  `test_ac17_every_stage28_box_ticked_implies_evidence_or_unticked_implies_reason`,
  the two `test_adv_stage28_*` companions and `_stage28_section`. The gate-row
  AC1 tests and AC19 (`stray_icon_warnings`, clean on the archived tree,
  A1) are kept.
- **Retire** — `tests/test_135_stage29_validation.py`:
  `test_ac12_stage28_mode4_box_is_ticked_and_annotated`. Its Stage 29 tests
  are kept, because Stage 29 is kept.
- **Retire** — `tests/test_150_maintainer_sign_off.py`:
  `test_ac13_each_stage_20_held_item_bullet_carries_its_recorded_icon` (four
  parametrised cases), `_HELD_ITEMS` and `_stage_20_section`.
- **Retire** — `tests/test_151_stage30_validation.py`: the three
  `test_ac35_*_note_matches_live_derivation`, the two `test_ac36_*` and the
  two `test_ac37_*` cases. The companions go too: the `test_adv_ac35_*`,
  `test_adv_ac36_*` and `test_adv_ac37_*` cases, and `_stage_section`,
  `_criterion7_box` and any parser left with no caller.
- **Retire** — `tests/test_161_stage31_validation.py`:
  `test_ac14_every_stage31_box_is_attested_or_annotated`,
  `test_ac15_box_count_equals_roadmap_bullet_count` and
  `test_live_stage31_section_has_no_spliced_trail_lines`. The companions go
  too: the `test_adv_ac14_*` and `test_adv_ac15_*` cases, and the synthetic
  texts and helpers left with no caller.
- **Retire** — `tests/test_169_stage32_validation.py`:
  `test_ac6_status_count_clause_equals_live_derivation`,
  `test_ac7_rung_count_clause_equals_live_derivation` and
  `test_ac13_no_stage20_bullet_deferred_and_item141_points_to_154`. The
  companions go too: `test_adv_deferred_bullet_anywhere_is_flagged` and any
  other adversarial case or helper left with no caller.

Where a retirement leaves a module import unused (`re`, `pytest`, the
`_aide_module` loader), drop it only if nothing else in the module uses it.

## Validation

Run by the validator on the claim branch, before the merge. It needs no
`[validation]` profile.

1. Create a real worktree of the branch tip, not a copy without `.git`,
   which would skip the git-gated tests (`CLAUDE.md` gotcha):
   `git worktree add --detach <scratch>/wt236 HEAD`.
2. Run `python <scratch>/wt236/.aide/scripts/aide.py --repo <scratch>/wt236 progress archive --no-commit`.
   It must archive the 23 stages of the Description and print 15, 17, 26 and
   29 as kept. Then run `... --repo <scratch>/wt236 check`, which must report
   no error.
3. Run the full suite over the worktree with `-ra`. Before trusting the run,
   confirm that `segfacet.__file__` resolves under the worktree (the
   `CLAUDE.md` gotcha on `PYTHONPATH` against a hatchling editable install).
   The run passes with 0 failed. Its skip reasons are the environment-gated
   ones the main checkout's run also shows, and no others. A failure here is
   a test the reconciliation list missed: it goes back to the test-writer
   under A5.
4. Remove the worktree: `git worktree remove --force <scratch>/wt236`.

## Dependencies

None.

**Downstream:** the post-merge archive run (Implementation Step 5) needs this
item merged into `aide/queue-032`. Items 237–240 are independent of it.

## Decisions & Trade-offs

To be updated during implementation.

- **The archived-tree suite run is a Validation step, not an acceptance
  criterion.** A test that ran the suite over an archived copy of the
  repository would run the suite inside itself. AC1–AC5 cover what the
  archive changes for the report and for the two settled items. Validation
  step 3 covers the rest of the suite.
- **Left open:** the report's grouping of an archived stage under its
  `# Phase N` header. `progress.md` no longer records which header an
  archived stage sat under. The engine's own `unarchive` puts Stage 0 back
  after `# Phase 2` once Stages 0–10 are archived (insight
  `2026-10-17-75bd`). So archived stages are shown in the report's unphased
  table until the engine records the grouping.
