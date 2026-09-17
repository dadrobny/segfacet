<!-- aide-template: item 1 -->
# Item 161 — Validate stage 31: Post-Sign-Off Maintenance

> **Created:** 2026-09-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 161
> **Objectives:** G7, G8
> **Suggested branch:** `aide/161-validate-stage-31-post-sign`

---

## Description

Stage 31 **D7**. This item closes Stage 31 by replaying the stage's five
acceptance criteria end to end from a clean tree. Items 152–160 each proved
their own deliverable against their own tests. This item asks the stage-level
question: does the merged tree meet the five criteria in `roadmap.md`'s Stage 31
"Validation / acceptance" block? It records the measured answer in
`progress.md`, one criterion at a time, even when the answer is no. It fixes
nothing it finds.

**How the replay is built.** Every stage-level claim in Stage 31 already has an
in-suite check, merged with the item that made the claim true:

- `tests/test_152_retire_vision_seed.py`: the §6 checks.
- `tests/test_153_eval_harness_rekey.py`: the legacy map and the re-keying.
- `tests/test_154_ladder_remeasurement.py`: fresh transcription and provenance.
- `tests/test_155_corpus_case_kind.py`: the `failure_mode == 0` scan.
- `tests/test_160_insight_triage.py`: the triage dispositions.

The replay runs those checks by node id in a fresh clone that has its own venv.
Those runs are the named checks behind each criterion. The replay does not copy
the checks into a new module. The new module,
`tests/test_161_stage31_validation.py`, holds only what no merged test covers:
the invariant that every Stage 31 acceptance box is either attested with
evidence or annotated with a reason. The replay also measures the things that
have no stable in-suite form:

- the engine version against the framework's version at planning time;
- a prose scan of `src/segfacet/` for text claiming §6 carries numbered modes;
- the harness re-run and its constants;
- the triage counts;
- `aide check`;
- the environment profiles.

**"From a clean tree" means a fresh `git clone` with its own venv.** Item 151
set this rule. CLAUDE.md's Gotchas say why a second tree reached through
`PYTHONPATH` is invalid: the editable install shadows it.

**What is measured already (2026-09-17, branch base `6d90126`, engine
1.52.1).** These values are starting points. The item re-measures every one.

- **Criterion 1.** `.aide/VERSION` reads `1.52.1`. It was installed by D0 commit
  `159aa65` (2026-09-16 13:06 +0100). Queue-021 was planned at `99520a9`
  (2026-09-16 17:20 +0100). At that moment, the latest `core/VERSION` on
  `aide-loop` `origin/main` was `1.52.1` (`5e305c5`). The framework moved to
  `1.53.0` later, at `ee23311` (2026-09-16 18:12 +0100). The local checkout now
  reads `1.53.1`. So the criterion's wording holds, and the later gap is
  recorded, not counted against it.
- **Criterion 2.** `docs/aide/vision.md` on this branch is v4. Its §6 names
  `segfacet.failure_modes.SPECIFICATION` and has no numbered list. Item 152
  merged it into the queue branch from PR #77, and PR #77 is **not yet on
  `main`**: `origin/main`'s `vision.md` is still v3. No production module reads
  `vision.md` (test_152 AC3/AC5). But a prose scan finds **42** matches of
  `§6 [failure ]mode(s) N` or `§6's [eight ]numbered` in 16 files under
  `src/segfacet/`, for example:
  - `heuristics/overlap.py:3`: "targeting §6 failure mode 8";
  - `heuristics/intensity.py:139`: "not one of §6's numbered eight".

  Only one of the 42 lines names v3 as history (`failure_modes.py:117`). Most of
  the rest use the pre-sign-off ids: overlap is now mode 15, not 8. **Under
  reading R2 this criterion is at risk.**
- **Criterion 3.** `LEGACY_STAGE18_MODE_NAMES` appears nowhere under `src/` or
  `tests/`. The harness is keyed by metric and operator names, and each mode id
  it carries is in `SPECIFICATION` or is `None` (reading R1). The constants
  committed in `src/segfacet/eval/severity_ladder.py` are:
  - `RECORDED_MARGINS`: `displace inf`, `fragment inf`, `inject_islands 112.0`,
    `relabel_swap inf`, `remove_level inf`, `crop_at_border 0.3585`,
    `sequence_break inf`, `force_overlap 1.038`.
  - `KNOWN_CROSS_MODE_COUPLINGS`: `crop_at_border → unanchored_foreground_fraction 2.79`
    and `force_overlap → unanchored_foreground_fraction 0.9629`.
  - Provenance: every value carries `MeasurementProvenance(corpus="geometric",
    base_params=_BASE_PARAMS, measured_on="2026-09-16")`.

  **None of this is in `progress.md` yet.** Item 154 left that to this item.
- **Criterion 4.** Already ticked on 2026-09-16, with evidence from item 155's
  in-tree run of `test_ac12_…`. The replay re-verifies it from the clean clone
  and does not read the tick as settled.
- **Criterion 5.** Item 160 recorded 29 stage-start `defect`/`gap` entries:
  **18 ticked, 10 re-homed, 1 left open**. It also recorded 6 in-queue entries:
  2 ticked, 0 re-homed, 4 left open. **The counts are not in `progress.md`
  yet.**

**In scope:**

- the clean-clone replay;
- the measurements;
- the Stage 31 acceptance bookkeeping in `progress.md`, done through `aide
  progress accept` / `amend` / `retract`, plus the hand-written reason
  annotation §1 allows beside a box left unticked;
- the in-suite bookkeeping module;
- one-line `insights.md` findings.

**Not in scope:**

- Fixing anything the replay finds, including the §6 prose in AC5. A
  divergence becomes a finding, never a remediation.
- Editing any deliverable bullet, including D1's 🚧, which is process work with
  no item and no verb.
- Editing any Environment-Gated row. Stage 31 introduces no gated capability.
- Editing `roadmap.md` or `vision.md`.
- Merging PR #77.
- Ticking any insight entry.

## Acceptance Criteria

Two kinds of criterion sit below, as in item 151. **In-suite** criteria are
pinned by `tests/test_161_stage31_validation.py`. **Replay** criteria are run by
the builder and re-run by the validator. Their observed output is recorded
verbatim in Decisions & Trade-offs. "The clone" is AC1's clone, and "passes in
the clone" means `python -P -m pytest <clone>/<node ids> -q` run from the
clone's venv exits `0` with no skip among the named tests. A criterion annotated
*(closes Stage 31 criterion M)* is evidence for that criterion. A criterion
without the annotation closes none.

### The clean-tree rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  (Replay.) `git clone --branch aide/161-validate-stage-31-post-sign <this repo>
  <scratchpad>/clone`, then
  `python <clone>/.aide/scripts/aide.py --repo <clone> env --bootstrap`. Record:
  - the clone path;
  - the clone's `HEAD` SHA, which equals this branch's tip at clone time;
  - `segfacet.__file__` as printed by `python -P` from the clone's venv, which
    resolves under the clone.

  A resolution under the working checkout invalidates every clone result.

### Criterion 1 — the engine version

- [ ] **AC2: the installed engine equals the framework's version at the
  planning commit.** (Replay.) Take `X`, the content of the clone's
  `.aide/VERSION`. Resolve the queue-021 planning commit fresh by its subject
  `docs(aide): add work queue 021` (`99520a9` at writing) and read its committer
  date `T`. On the `aide-loop` checkout, `git log origin/main --before=<T> -1 --
  core/VERSION` names a commit, and `core/VERSION` at that commit equals `X`.
  Also record the framework's current `origin/main` `core/VERSION`, as
  information that does not affect the criterion. If this machine has no
  `aide-loop` checkout, the check is recorded as not performed, and criterion 1
  stays unticked with that reason. *(closes Stage 31 criterion 1)*

### Criterion 2 — `vision.md` §6 and the modules that describe it

- [ ] **AC3: §6 names the specification and carries no numbered list.**
  (Replay.) `test_152_retire_vision_seed.py::test_ac1_section_six_carries_no_numbered_list`
  and `::test_ac2_section_six_names_the_specification` pass in the clone.
  *(closes Stage 31 criterion 2)*
- [ ] **AC4: no production module reads `vision.md` or names a retired
  seed-parse function.** (Replay.)
  `test_152_retire_vision_seed.py::test_ac3_no_production_module_names_vision_md_as_a_path`
  and `::test_ac5_no_source_text_names_a_retired_function` pass in the clone.
  *(closes Stage 31 criterion 2)*
- [ ] **AC5: the prose scan's hit count is recorded, and criterion 2 is ticked
  only when it is zero.** (Replay.) In the clone, run
  `grep -rnoE "§6('s)? (failure[ -])?modes? [0-9]+|§6's (eight )?numbered|numbered eight" src/segfacet --include='*.py'`.
  A hit counts unless its full source line contains the token `v3`. Record the
  counted hits verbatim, with their total and their file count (42 and 16 on
  2026-09-17). Criterion 2 is ticked only if AC3 and AC4 pass **and** the count
  is `0`. Otherwise it stays unticked with the AC16 annotation, and one `defect`
  entry is appended to `docs/aide/insights.md`. That entry names
  `stage 31 criterion 2`, the count, the files, and the fact that the cited ids
  are pre-sign-off ids. *(closes Stage 31 criterion 2, under reading R2)*

### Criterion 3 — the harness keys and the re-measured constants

- [ ] **AC6: the legacy map is gone.** (Replay.)
  `test_153_eval_harness_rekey.py::test_ac1_legacy_map_is_gone` and
  `::test_ac2_no_source_or_test_names_the_legacy_map` pass in the clone.
  *(closes Stage 31 criterion 3)*
- [ ] **AC7: no per-mode metric, ladder or cohort count is keyed by an id
  outside the specification.** (Replay.) These tests in
  `test_153_eval_harness_rekey.py` pass in the clone:
  - `test_ac5_homes_are_derived_from_the_specification`
  - `test_ac17_ladders_are_keyed_by_operator`
  - `test_ac20_margins_are_keyed_by_operator`
  - `test_ac21_couplings_name_a_ladder_and_a_foreign_metric`
  - `test_ac26_cohort_aggregates_follow_the_registry`
  - `test_ac27_scale_specs_are_keyed_by_metric`
  - `test_ac30_every_emitted_mode_id_is_valid`

  *(closes Stage 31 criterion 3, under reading R1)*
- [ ] **AC8: the eval harness re-run from the clone reproduces the committed
  constants.** (Replay.) From the clone's venv, run the item-154 Validation
  command with `python -P`. It prints `score_harness(run_severity_harness())`'s
  summary, and each ladder's margin and responses. Record the printed output
  verbatim and the `passed` value, which is `True`.
  `test_154_ladder_remeasurement.py::test_ac8_coupling_set_is_what_is_measured`,
  `::test_ac9_each_coupling_value_is_a_fresh_transcription` and
  `::test_ac10_each_margin_is_a_fresh_transcription` pass in the clone.
  *(closes Stage 31 criterion 3)*
- [ ] **AC9: the re-measured constants are recorded in `progress.md` with what
  they were measured on.** (Replay.) Criterion 3's evidence note in
  `progress.md` contains all of the following:
  - every `RECORDED_MARGINS` operator with its value, written `inf` for
    infinity;
  - both `KNOWN_CROSS_MODE_COUPLINGS` entries, as `operator → foreign_metric
    value`;
  - the provenance corpus, the base parameters and `measured_on`;
  - AC8's clone commit and replay date.

  Each value equals the one read from the clone's
  `segfacet.eval.severity_ladder` at replay time, and the validator re-reads
  them to check. *(closes Stage 31 criterion 3)*

### Criterion 4 — no zero-comparison consumer

- [ ] **AC10: the zero-comparison scan holds in the clone, and criterion 4's
  existing tick carries a dated correction trail.** (Replay.)
  `test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`
  and every parametrisation of `::test_ac13_scan_detects_each_forbidden_shape`
  pass in the clone. Stage 31's fourth box then carries a trail line dated on or
  after 2026-09-17 that names item 161. If the tests pass, the trail comes from
  `aide progress amend 31 --criterion 4`, and its evidence names the clone
  commit. If either test fails, it comes from `aide progress retract 31
  --criterion 4`. The box's original line, including its 2026-09-16 annotation,
  is unchanged. *(closes Stage 31 criterion 4)*

### Criterion 5 — the triage counts

- [ ] **AC11: every stage-start disposition holds in the clone.** (Replay.) In
  the clone, `test_160_insight_triage.py` tests `test_ac1_…` through
  `test_ac8_…` pass. *(closes Stage 31 criterion 5)*
- [ ] **AC12: the counts are re-measured, not copied.** (Replay.) In the working
  checkout, after every commit of this item that touches `insights.md`, run
  `python .aide/scripts/aide.py insights list --trail`. Classify each of item
  160's rows S1–S29 and Q1–Q6 by item 160's AC2/AC4/AC7 predicates:
  - **ticked**: ticked, with a pointer that does not start `re-homed (`;
  - **re-homed**: ticked, with a pointer that starts `re-homed (`;
  - **left open**: unticked, with a `left open:` trail line.

  Rows resolve by item 160's keys (type, provenance, date, claim substring),
  never by list number. Record the per-cohort counts and the list's summary
  line. If a count differs from item 160's recorded 18/10/1 (stage start) or
  2/0/4 (in-queue), the difference is explained in Decisions, row by row.
  *(closes Stage 31 criterion 5)*
- [ ] **AC13: the counts are recorded in `progress.md`.** (Replay.) Criterion 5's
  evidence note contains the clause
  `stage-start defect/gap entries: N — ticked A, re-homed B, left open C`, then
  the clause `in-queue: M — ticked D, re-homed E, left open F`. Every integer
  equals AC12's measurement, `A + B + C == N`, and `D + E + F == M`.
  *(closes Stage 31 criterion 5)*

### Bookkeeping, environment, check, suite

- [ ] **AC14: every Stage 31 acceptance box is attested with evidence or
  annotated with a reason.** (In-suite.) Locate Stage 31's section with
  `.aide/scripts/aide.py`'s `stage_section`, loaded in-process (the
  `test_150_maintainer_sign_off.py` idiom). Take its boxes from
  `acceptance_boxes`. A box's text is its checkbox line plus the indented
  continuation lines that follow it, stopping at a trail line, a blank line, the
  next box or the section end. Every box's text contains at least one non-empty
  `*(…)*` annotation, anywhere in it. A ticked box's annotation is its evidence.
  An unticked box's annotation is its reason, or the original annotation a
  retraction keeps.
- [ ] **AC15: the parser sees exactly the roadmap's criteria.** (In-suite.) The
  number of boxes AC14 finds in `progress.md`'s Stage 31 section equals
  `len(roadmap_acceptance_bullets(<roadmap.md lines>, "31"))`, from the same
  in-process module (5 == 5 at writing).
- [ ] **AC16: each criterion is attested, corrected or annotated through the
  matching verb.** (Replay.) Record in Decisions the exact command and the
  evidence or reason text for each criterion:
  - **Criteria 1, 2, 3 and 5**, where their ACs hold:
    `python .aide/scripts/aide.py progress accept 31 --criterion N --evidence "<text>"`.
    The text names the ACs above and the clone commit, and for 3 and 5 it
    carries the AC9 or AC13 content.
  - **Criterion 4**: AC10's `amend` or `retract`.
  - **A criterion whose ACs do not hold**: it stays unticked. A hand-written
    annotation ` *(not attested YYYY-MM-DD, item 161: <measured reason>)*` is
    appended to the end of its box's last line, and one `insights.md` entry
    (`defect` or `gap`) names `stage 31 criterion N`.

  No box is ticked on evidence that failed.
- [ ] **AC17: the environment profiles are evaluated and the gated table is left
  unchanged, for a recorded reason.** (Replay.) Record the output and exit code
  of `python .aide/scripts/aide.py env` and of `env --profile pyradiomics`,
  `--profile docker` and `--profile gpu`. `progress.md`'s Environment-Gated
  Capability Verification table has no row whose introducing stage is 31
  (verified by reading its rows). The table is left unchanged. Decisions records
  the reason: Stage 31 introduced no gated capability, and no replay above
  depends on a profile.
- [ ] **AC18: `aide check` raises nothing attributable to this stage.**
  (Replay.) After the bookkeeping, `python .aide/scripts/aide.py check` reports
  no error. Record every warning line verbatim. No warning text contains
  `stage 31`, `queue-021`, or a spec filename `152-` through `161-`. The one
  exception is a `stage 31 criterion 4 was retracted` warning, which is expected
  if and only if AC10 retracted. The baseline measured 2026-09-17 on `6d90126`
  was `OK (7 warning(s))`:
  - 1 assumptions-block warning;
  - 2 awaiting-a-decision warnings (gates 1 and 2);
  - 4 retracted-criterion warnings (Stage 20 criteria 1, 3, 4, 5).

  That baseline is recorded for comparison and **pinned nowhere in the suite**,
  by count or by class.
- [ ] **AC19: the full suite is green in a fresh clone of the final commit.**
  (Replay.) Once every commit of this item has landed on the branch, clone that
  final commit fresh, or bring AC1's clone up to it with
  `python <clone>/.aide/scripts/aide.py --repo <clone> sync --item 161`. Print
  AC1's resolution proof again. Run `python -P -m pytest <clone>/tests -n auto`
  in the foreground, split into chunks if one call would exceed the tool
  timeout. Record pass, skip and fail counts, the commit, and the reason for
  every environment-gated skip. The run has no failures. A skip is never
  recorded as verification.

## Assumptions

- **A1: items 152–160 are merged (✅) before this item starts.** Measured
  2026-09-17: every D2–D6 bullet in Stage 31 is ✅. If one is not, the item halts
  and reports.
- **A2: "a named check in the validation module" can be a merged test run by
  node id in the clean clone.** Queue-021's item-161 text asks for each
  acceptance line to be "replayed by a named check in the validation module".
  Copying the tree-wide scans of test_152, test_153, test_154, test_155 and
  test_160 into `test_161` would give each claim two copies that could drift
  apart. So the named checks are those tests' node ids, run in the clone
  (AC3–AC11). `test_161` holds only the bookkeeping invariant no merged test
  covers (AC14, AC15). A human who wants the scans duplicated can say so at the
  queue boundary. Nothing downstream depends on the choice.
- **A3: reading R1 for criterion 3.** Item 153 re-keyed the harness by metric
  name and operator, not by specification id, and carries the mode as a
  nullable `failure_mode` field. "Keys … by an id outside
  `failure_modes.SPECIFICATION`" is read as "no key is a mode id outside the
  specification, and every mode id the harness emits is in `SPECIFICATION` or
  is `None`". A key set of names satisfies this vacuously, and the emitted ids
  are what test_153 AC5/AC19/AC30 measure. Criterion 3's evidence note states
  this reading.
- **A4: reading R2 for criterion 2.** "No module under `src/segfacet/` asserts
  that it does" covers module prose as well as code. A docstring or comment
  that attributes a numbered mode to §6 ("targeting §6 failure mode 8") asserts
  that §6 carries a numbered list. Roadmap Stage 31 D2 treats prose the same
  way: it required the specification's docstring and note to "stop describing
  §6 as a seed list". A line naming v3 is history, not a present claim, and is
  excluded. This is this spec's own reading and it is stricter than code alone.
  If a human judges prose out of scope, criterion 2 closes on AC3 and AC4
  alone. That decision is recorded at the queue boundary, and no gate is
  raised: the item can proceed either way, and its only consequence is whether
  one box is ticked.
- **A5: criterion 2 is measured on this branch, not on `main`.** `vision.md` v4
  reached `aide/queue-021` through item 152's merge of PR #77's branch. PR #77
  has not merged to `main`. AC3's evidence says it was measured on the queue
  branch. Merging PR #77 before or with the queue PR is a human's action, and
  so is flipping D1's 🚧 bullet: no item carries it, and `aide progress set`
  takes only an item number. Until both happen, the stage's rollup stays 🚧
  whatever this item finds.
- **A6 (engine 1.52.1):** a few verb behaviours are assumed.
  - `aide progress accept 31 --criterion N --evidence` ticks one unticked box
    and appends ` *(<text>)*` to the box's **first** physical line. On Stage
    31's wrapped boxes, the annotation therefore lands mid-criterion, as it did
    on criterion 4 (captured to `insights.md` 2026-09-17).
  - `amend` refuses an unticked box. `retract` unticks, adds a `retracted: `
    trail, and captures a `gap` insight.
  - No verb annotates an unticked box, so AC16's reason annotation is a hand
    edit (the item-151 A4 precedent).
  - AC14's "anywhere in the box text" rule tolerates the mid-criterion
    annotation.
- **A7 (engine 1.52.1):** `aide progress set 161 in-progress` rewrites D7's
  bullet in place. That bullet names only item 161, so it is not a shared bullet
  and no identical-prose split is expected. If the verb nonetheless splits a
  bullet into copies with identical prose (the defect item 158 met), the builder
  rewords each copy to its own item before committing. The D1 bullet must not
  be touched.
- **A8: the framework checkout is per-machine.** AC2 reads `aide-loop` through
  the `$AIDE_LOOP` path from the machine's own configuration (CLAUDE.md,
  "Updating the framework"). That checkout is a declared sibling, so `git -C`
  against it is permitted (§3, §8). Nothing in this spec or its tests records
  the path.
- **A9: every number above is a starting point** (measured 2026-09-17 at
  `6d90126`). Where a re-measurement differs, the measured value wins, and
  Decisions records the difference.

## Implementation Steps

1. **Preconditions.** Confirm A1 with `python .aide/scripts/aide.py status`.
   Record `aide check`'s baseline (AC18).
2. **Rig (AC1).** Clone into the scratchpad. Bootstrap the clone's venv. Print
   the resolution proof.
3. **Named checks (AC3, AC4, AC6, AC7, AC8's tests, AC10's tests, AC11).** Run
   each group of node ids in the clone, in the foreground, and record the
   output.
4. **Measurements (AC2, AC5, AC8's harness print, AC12).** Record each verbatim.
5. **Findings.** Append one `insights.md` line per failed criterion (AC5, AC16)
   and one per out-of-scope finding. Tick no existing entry.
6. **Write `tests/test_161_stage31_validation.py` (AC14, AC15).** The
   test-writer does this. It needs no production change.
7. **Bookkeeping (AC9, AC10, AC13, AC16).** Criterion by criterion, in order
   1→5, run the matching `aide progress` verb, or add the hand annotation for a
   criterion that does not hold. Every evidence note names its ACs and the
   clone commit.
8. **Environment (AC17).** Run `aide env` and the three profile checks.
9. **Check (AC18).** Re-run `aide check` and compare it against the baseline.
10. **Suite (AC19).** Bring the clone up to the final commit, run the full
    suite, record the counts, then delete the clone.
11. Record everything in Decisions & Trade-offs.

## Authorised paths

**May change:**

- `tests/test_161_stage31_validation.py` — the bookkeeping invariant module
  (AC14, AC15)

`docs/aide/progress.md` (Stage 31's five acceptance boxes, and D7's bullet via
`aide progress set`), `docs/aide/insights.md` (appended findings, and a
retraction's `gap` entry) and this spec are always authorised. No other part of
`progress.md` is edited.

**Asserts against:**

- `.aide/scripts/aide.py` — `stage_section`, `acceptance_boxes`,
  `roadmap_acceptance_bullets` loaded in-process (AC14, AC15)
- `docs/aide/roadmap.md` — Stage 31's acceptance bullet count (AC15)
- `.aide/VERSION` — the installed engine (AC2)
- `docs/aide/vision.md` — §6, read by the named checks (AC3)
- `src/segfacet/**` — the prose scan and the named scans (AC4–AC7, AC10)
- `src/segfacet/eval/severity_ladder.py` — the constants and provenance recorded
  in `progress.md` (AC8, AC9)
- `tests/test_152_retire_vision_seed.py` — named checks (AC3, AC4)
- `tests/test_153_eval_harness_rekey.py` — named checks (AC6, AC7)
- `tests/test_154_ladder_remeasurement.py` — named checks (AC8)
- `tests/test_155_corpus_case_kind.py` — named checks (AC10)
- `tests/test_160_insight_triage.py` — named checks (AC11)
- `docs/aide/items/160-insight-triage-to-a-known.md` — the recorded counts AC12
  compares against
- `docs/aide/queue/queue-021.md` — the planning commit AC2 resolves

## Testing Strategy

New module `tests/test_161_stage31_validation.py`. It is deliberately small (A2).

- **AC14:** one test over the live Stage 31 section.
- **AC15:** one test comparing the box count with the roadmap's bullet count.
- **Parsing** goes through `.aide/scripts/aide.py`, loaded in-process, never a
  private reimplementation of stage or box detection. Continuation-line
  gathering is the one helper the module writes.

**Adversarial cases.** Each is an in-memory `progress.md` text passed to the
same helper, and none writes a file.

- A ticked box with no annotation is flagged.
- An unticked box with no annotation is flagged.
- A wrapped box whose annotation sits at the end of its **first** physical line,
  with criterion text continuing below it (the shape `accept` writes, A6), is
  not flagged.
- A wrapped box whose annotation sits on its last continuation line (the AC16
  hand-annotation shape) is not flagged.
- A retracted box is not flagged: unticked, its original annotation kept, a
  `retracted: ` trail line below.
- A trail line's `*(…)*` does not count as the box's own annotation. A box whose
  only annotation is inside a trail line is flagged.
- An empty annotation `*()*` is flagged.
- A section with a sixth box makes AC15's equality fail against a five-bullet
  roadmap block.

**Discipline.**

- The module asserts no count of `aide check` warnings or warning classes,
  which item 159 removed from test_146 and test_150.
- It asserts no triage count, harness constant or engine version. Those are
  dated measurements that later verbs and stages legitimately move, so they live
  in `progress.md`'s evidence and in Decisions.
- It pins no insight entry. If a later edit adds one, it must search
  `docs/aide/insights/archive-*.md` as well as the inbox.
- It reads no git history and needs no clone, network or profile.

**Existing tests to reconcile.** None expected. Swept 2026-09-17: no test
under `tests/` parses Stage 31's acceptance boxes. `test_159` and `test_160`
mention "Stage 31" only in a docstring or an in-memory fixture. Ticking,
amending or annotating those boxes moves no existing assertion.
`tests/test_aide_check_no_errors.py` asserts no errors only. A retraction adds a
warning, not an error.

## Validation

This item **is** the stage validation. The validator re-executes the replay
criteria, not just the suite, and confirms each Decisions record against its
own run:

- the rig and the resolution proof (AC1);
- the engine comparison (AC2);
- each named-check group's exit code (AC3, AC4, AC6, AC7, AC8, AC10, AC11);
- the prose scan's counted hits (AC5);
- the harness print (AC8);
- the evidence values in `progress.md` against a fresh read of
  `severity_ladder` (AC9);
- the triage classification (AC12, AC13);
- each `aide progress` command against the `progress.md` diff (AC16);
- the profiles (AC17);
- `aide check` (AC18);
- the full-suite counts (AC19);
- `python .aide/scripts/aide.py scope`.

**Environment gating.** No criterion depends on a `[validation]` profile.
`pyradiomics`, `docker` and `gpu` are evaluated and recorded only (AC17). The
only external needs are `git`, disk space for one clone and its venv, and, for
AC2, the machine's `aide-loop` checkout.

**Honest downgrade.** A replay that cannot run is recorded as not performed,
naming what was missing. Its criterion stays unticked with that reason. A
skip-clean run is never evidence.

## Dependencies

- **Item 152** — §6 seed check retired, and vision v4 merged into the queue
  branch (criterion 2).
- **Item 153** — harness re-keyed, and the legacy map retired (criterion 3).
- **Item 154** — constants re-measured with provenance (criterion 3).
- **Item 155** — the corpus-case `kind` discriminator and its scan
  (criterion 4).
- **Item 156** — the conformance seams (Stage 31 D4).
- **Item 157** — the case-id rename (Stage 31 D4).
- **Item 158** — the committed-artifact guard (Stage 31 D5).
- **Item 159** — the prerequisite defects, and warning-count pins removed
  (Stage 31 D5).
- **Item 160** — the triage and its recorded counts (criterion 5).

**Downstream:** Stage 32 (Selected-Mode Refinement) is planned after this item
closes Stage 31. A Stage 32 item that re-measures a ladder constant, or that
rewrites the heuristic-module prose AC5 counts, leaves this item's
`progress.md` evidence standing as a dated record. It corrects that evidence
with `aide progress amend 31`, never by editing the note.

## Decisions & Trade-offs

- **2026-09-17 — the rig (AC1).** Cloned `aide/161-validate-stage-31-post-sign` into
  the session scratchpad: `git clone --branch aide/161-validate-stage-31-post-sign
  <this repo> <scratchpad>/clone`. Clone `HEAD` at clone time:
  `6bf417df59d5ec22c1c6bcfcc9190ad2582537c5`, equal to the branch tip at that
  moment. Bootstrapped with `python <clone>/.aide/scripts/aide.py --repo <clone>
  env --bootstrap` (ok: venv is Python 3.11; `import segfacet`/`import pytest`
  succeed). Resolution proof: `<clone>/.venv/bin/python -P -c "import segfacet;
  print(segfacet.__file__)"` printed
  `<scratchpad>/clone/src/segfacet/__init__.py` — resolves under the clone, not
  the working checkout.

- **2026-09-17 — Criterion 1, the engine version (AC2).** `X` = clone's
  `.aide/VERSION` = `1.52.1`. Queue-021's planning commit resolved fresh by
  subject `docs(aide): add work queue 021`: `99520a9faf5ce7ae7cf669a4a6b12d37dba55624`,
  committer date `2026-09-16T17:20:06+01:00`. On the declared `aide-loop`
  sibling (`/mnt/data/spine/codes/aide-loop`, `[framework] local_path`),
  `git fetch origin main` then `git log origin/main --before=2026-09-16T17:20:06+01:00
  -1 --format='%H %cI' -- core/VERSION` names `5e305c5ca5e62da20a08ff2fca6b551801968442`
  (2026-09-15T13:49:20+01:00); `core/VERSION` at that commit is `1.52.1`, equal
  to `X`. Framework's current `origin/main` `core/VERSION` is `1.53.1`
  (informational; recorded, does not affect this criterion). **Criterion 1
  holds.** Attested: `aide progress accept 31 --criterion 1 --evidence "..."`
  (commit `056716b`).

- **2026-09-17 — Criterion 2, `vision.md` §6 (AC3–AC5).** AC3/AC4:
  `test_152_retire_vision_seed.py::test_ac1_section_six_carries_no_numbered_list`,
  `::test_ac2_section_six_names_the_specification`,
  `::test_ac3_no_production_module_names_vision_md_as_a_path`,
  `::test_ac5_no_source_text_names_a_retired_function` — 4 passed in the clone.
  AC5: `grep -rnoE "§6('s)? (failure[ -])?modes? [0-9]+|§6's (eight )?numbered|numbered
  eight" src/segfacet --include='*.py'` in the clone returns **42** matching
  lines across **16** files (matches the 2026-09-17 starting-point measurement
  in the Description exactly). Exactly one line contains the token `v3`
  (`failure_modes.py:117`, `"v3 vision.md §6's numbered eight. It entered
  through this module's schema,"`) and is excluded per AC5's rule, leaving
  **41** hits that count against the zero threshold. The count is non-zero, so
  under reading R2 (A4) **criterion 2 does not hold** and stays unticked. A
  hand-written annotation was appended to the box's last line (commit
  `dd6505b`, folded into the `progress set` commit since it was made before
  that command ran) and one `defect` entry was appended to `insights.md`
  (commit `58c17a5`) naming `stage 31 criterion 2`, the count (42/16, 41
  counted), the two example files, and that the cited ids are pre-sign-off
  ids. Per A4, if a human later judges prose out of scope, criterion 2 closes
  on AC3/AC4 alone — that decision is left to the queue boundary, not made
  here.

- **2026-09-17 — Criterion 3, the harness re-key and constants (AC6–AC9).**
  AC6/AC7: `test_153_eval_harness_rekey.py`'s
  `test_ac1_legacy_map_is_gone`, `test_ac2_no_source_or_test_names_the_legacy_map`,
  `test_ac5_homes_are_derived_from_the_specification`,
  `test_ac17_ladders_are_keyed_by_operator`, `test_ac20_margins_are_keyed_by_operator`,
  `test_ac21_couplings_name_a_ladder_and_a_foreign_metric`,
  `test_ac26_cohort_aggregates_follow_the_registry`,
  `test_ac27_scale_specs_are_keyed_by_metric`, `test_ac30_every_emitted_mode_id_is_valid`
  — 9 passed in the clone. AC8: `score_harness(run_severity_harness())` run from
  the clone's venv (`python -P -c ...`) printed `passed=True`, with per-ladder
  margins `displace inf`, `fragment inf`, `inject_islands 112.04`, `relabel_swap
  inf`, `remove_level inf`, `crop_at_border 0.3585`, `sequence_break inf`,
  `force_overlap 1.0386` and couplings `crop_at_border → unanchored_foreground_fraction
  2.789`, `force_overlap → unanchored_foreground_fraction 0.9628` (unrounded;
  matches the committed 4-sig-fig constants). `test_154_ladder_remeasurement.py`'s
  `test_ac8_coupling_set_is_what_is_measured`, `test_ac9_each_coupling_value_is_a_fresh_transcription`,
  `test_ac10_each_margin_is_a_fresh_transcription` — 3 passed in the clone. AC9,
  the re-measured constants read fresh from the clone's
  `segfacet.eval.severity_ladder` (replay date 2026-09-17, clone commit
  `6bf417d`):
  - `RECORDED_MARGINS`: `displace=inf`, `fragment=inf`, `inject_islands=112.0`,
    `relabel_swap=inf`, `remove_level=inf`, `crop_at_border=0.3585`,
    `sequence_break=inf`, `force_overlap=1.038`.
  - `KNOWN_CROSS_MODE_COUPLINGS`: `crop_at_border → unanchored_foreground_fraction
    2.79`, `force_overlap → unanchored_foreground_fraction 0.9629`.
  - Provenance: `corpus="geometric"`, `base_params={levels: (L1,L2,L3,L4,L5),
    spacing: (1.0,1.0,1.0), curve_amplitude_mm: 6.0}`, `measured_on="2026-09-16"`.

  Every value equals the corresponding starting-point value in the Description
  exactly — no drift since 2026-09-16. **Criterion 3 holds.** Attested:
  `aide progress accept 31 --criterion 3 --evidence "..."` (commit `1e9f009`).

- **2026-09-17 — Criterion 4, no zero-comparison consumer (AC10).**
  `test_155_corpus_case_kind.py::test_ac12_no_tree_wide_zero_comparison_of_failure_mode_remains`
  and every parametrisation of `::test_ac13_scan_detects_each_forbidden_shape` —
  8 passed in the clone. Since the tests pass, the correction is an `amend`,
  not a `retract`: `aide progress amend 31 --criterion 4 --evidence "..."`
  (commit `f7e4b28`), which appends a `- **2026-09-17** → ...` trail line
  under the box while leaving its original 2026-09-16 attestation and tick
  unchanged, exactly as A6 describes. **Criterion 4 holds, re-confirmed.**

- **2026-09-17 — Criterion 5, the triage counts (AC11–AC13).**
  `test_160_insight_triage.py`'s `test_ac1_…` through `test_ac8_…`
  parametrisations — 125 passed in the clone (every S1–S29/Q1–Q6 row
  classifies exactly as item 160 recorded; a mismatch would have failed one of
  these parametrised tests). AC12, re-measured (not copied) from
  `python .aide/scripts/aide.py insights list --trail` on the working
  checkout (89 entries total, 24 open) classified by item 160's own AC2/AC4/AC7
  predicates, keyed by row (type, provenance, date, claim substring), never by
  list number:
  - **Stage-start (S1–S29):** 29 rows — **18 ticked, 10 re-homed, 1 left open**.
  - **In-queue (Q1–Q6):** 6 rows — **2 ticked, 0 re-homed, 4 left open**.

  Both cohorts match item 160's recorded 18/10/1 and 2/0/4 exactly; no
  difference to explain. Independently cross-checked by counting the raw
  markers in `docs/aide/insights.md`: `grep -c "re-homed ("` → 10 (matches
  10+0); `grep -c "→ left open:"` → 5 (matches 1+4). **Criterion 5 holds.**
  Attested: `aide progress accept 31 --criterion 5 --evidence "..."` (commit
  `ff004cc`), whose evidence note carries the AC13 clause
  `stage-start defect/gap entries: 29 — ticked 18, re-homed 10, left open 1`
  followed by `in-queue: 6 — ticked 2, re-homed 0, left open 4`
  (18+10+1=29, 2+0+4=6).

- **2026-09-17 — Bookkeeping order and verbs (AC16).** Run in order 1→5:
  `accept --criterion 1`, `accept --criterion 3`, `amend --criterion 4`,
  `accept --criterion 5` (each via the CLI, each auto-committed), then a hand
  edit for criterion 2 (unticked, per AC5) plus its `insights.md` defect entry
  (committed separately, `58c17a5`, since it predated the verb calls in
  wall-clock order but was folded into the `progress set` commit for the
  progress.md side). No box was ticked on evidence that failed. `aide progress
  set 161 in-progress` (commit `dd6505b`) flipped D7's bullet from 📋 to 🚧; it
  names only item 161, so no identical-prose split occurred (A7) and no
  reword was needed.

- **2026-09-17 — Environment (AC17).** `aide env` → `OK` (venv is Python 3.11;
  `import segfacet`/`import pytest` succeed). `aide env --profile pyradiomics`
  → exit 1, `ModuleNotFoundError: No module named 'radiomics'` (recorded as ❓
  Unverified, never a silent pass, per the profile's own contract).
  `aide env --profile docker` → exit 1, docker not satisfied.
  `aide env --profile gpu` → exit 1, `ModuleNotFoundError: No module named
  'cupy'`. `progress.md`'s Environment-Gated Capability Verification table has
  no row whose "Introduced by" column names Stage 31 (verified by reading
  every row) — Stage 31 introduces no gated capability, and none of the
  replays above depend on a profile. The table is left unchanged.

- **2026-09-17 — `aide check` (AC18).** Baseline before this item's
  bookkeeping (on `6d90126`, tree clean): `OK (7 warning(s))` — 1
  assumptions-block warning, 2 awaiting-a-decision warnings (gates 1, 2), 4
  retracted-criterion warnings (Stage 20 criteria 1, 3, 4, 5). After every
  bookkeeping commit above: `OK (7 warning(s))`, byte-identical set (same 7
  lines). No warning text contains `stage 31`, `queue-021`, or a spec filename
  `152-` through `161-`. No `stage 31 criterion 4 was retracted` warning
  appeared, consistent with AC10's tests passing (an `amend`, not a
  `retract`). The baseline is recorded for comparison only, pinned nowhere in
  the suite.

- **2026-09-17 — the in-suite module (AC14/AC15).** `tests/test_161_stage31_validation.py`
  (written by the test-writer before this item's bookkeeping ran) passes in
  full against the bookkept `progress.md`: `.venv/bin/python -m pytest
  tests/test_161_stage31_validation.py -q` → 11 passed. AC14: every Stage 31
  acceptance box (criteria 1, 3, 4, 5 ticked with evidence; criterion 2
  unticked with its hand-written reason) carries a non-empty `*(...)*`
  annotation. AC15: `progress.md`'s Stage 31 section has 5 acceptance boxes,
  equal to `roadmap_acceptance_bullets(..., "31")`'s 5 bullets.

- **2026-09-17 — the full suite in a fresh clone of the final commit (AC19).**
  See the paragraph below, added after the branch's final commit landed.
