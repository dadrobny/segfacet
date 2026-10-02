<!-- aide-template: item 3 -->
# Item 204 — Validate stage 33: Corpus & Rule Re-grounding: modes 3 and 4 to the bar

> **Created:** 2026-10-02 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D6)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 204
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/204-validate-stage-33-corpus-rule`

---

## Description

Roadmap Stage 33 **D6**: stage validation, which also closes Stage 32. Items
170–203 and 205–208 each proved their own deliverable against their own
tests. This item asks the stage-level question: does the merged tree, measured
from a clean clone, meet the five criteria in [`roadmap.md`](../roadmap.md)'s
Stage 33 "Validation / acceptance" block? It also re-runs Stage 32's D3 on the
re-grounded corpus and attests Stage 32's criterion 1, which item 169 left
open on 2026-09-22 because no mode had been signed at the bar. It records the
measured answer in `progress.md` one criterion at a time, **including where
the answer is no.** It fixes nothing it finds.

**The selected modes are 2 and 3, not 3 and 4.** The stage title and the
queue title still say "modes 3 and 4". Gate `gate-51da` was declined on
2026-09-30, and the maintainer re-drew the mode 2/3 boundary. Stage 33's
criterion 1 was reworded with `aide progress reword` that day to name modes 2
and 3. Gate `gate-0133` (`Blocks: 203, 204`) was approved on 2026-10-02 with
the evidence "modes 2 and 3 are at the bar". Item 203 transcribed that
outcome into `MODE_SIGN_OFFS`, and its spec hands the Stage 33 and Stage 32
criterion-1 attestations to this item. Mode 4 keeps its `gate-bb24`
intermediate-state record, and no criterion in force asks anything of it.

**"From a clean clone" means a fresh `git clone` with its own venv** (item 135's
rig, which items 151, 161 and 169 adopted). CLAUDE.md's Gotchas say why a
second tree reached through `PYTHONPATH` is invalid: the editable install's
meta-path finder resolves `segfacet` ahead of `sys.path`, so every "clean"
result would come silently from the working checkout.

**How the replay is built.** Nearly every stage-level claim already has an
in-suite check, merged with the item that made it true. The replay runs those
checks by module or node id in the clone and records what they measure. It
does not copy them. The one new test (AC8) covers the single criterion whose
merged check is narrower than the criterion's wording (A3).

**Live state on 2026-10-02**, measured on this branch at `6ebc5d1` (items
200–203 and 205–208 merged on `aide/queue-027`) with `.venv/bin/python`. These
are starting points. The item re-measures every one in the clone. Where a
re-measurement differs, the measured value wins and Decisions records the
difference.

- **Derived status over the 16 modes:** validated 6, implemented 3, specified
  2, proposed 5.
- **Derived mode rungs:** synthetic-demonstrable 6, needs-real-data 2,
  structurally-unobservable 1, none 7.
- **Sign-offs:** `MODE_SIGN_OFFS` keys `2, 3, 4`. Modes 2 and 3 are
  `2026-10-02, at-the-bar`. Mode 4 is `2026-09-22, intermediate-state`.
- **The bar:** `bar_conditions` conditions 1–5 all met for modes 1, 2, 3, 4
  and 16. Mode 9 fails condition 3 only. At the bar, with condition 6 read
  from `MODE_SIGN_OFFS`: modes **2 and 3**.
- **Conformance:** 18 committed cases, 14 geometric (`clean_control`,
  `crop_at_border`, `crop_fov_si`, `displace`, `fragment`, `fuse_adjacent`,
  `fuse_separate`, `inject_islands`, `relabel_swap`, `remove_level`,
  `remove_level_relabel`, `sequence_break`, `split`, `split_own_label`) and 4
  intensity (`clean_hu`, `degenerate_uniform`, `implausible_metal`,
  `implausible_soft_tissue`). Every case agrees. `specification_conflicts()`
  returns `()`.
- **Attribution:** `crop_at_border` and `crop_fov_si` are `fov_truncation`
  condition cases, and `displace` is the `displaced_vertebra` condition case.
  The modes are: `fragment` 1; `fuse_adjacent`, `split`, `fuse_separate` 2;
  `split_own_label` 3; `inject_islands` 4; `remove_level`,
  `remove_level_relabel` 6; `relabel_swap`, `sequence_break` 9; the three
  intensity failure cases 16. `force_overlap` is in neither manifest.
- **Detector → modes** (`modes_for_detector`, the Modes column of
  `docs/aide/rules.generated.md`):
  - `fragmentation/components` serves 1, and `fragmentation/islands` serves 4.
  - `neighbour_contact/stray_contact` and `fused_label/fused_label` serve 2.
  - `split_fragment/split_fragment` serves 3.
  - `bounds/metric_out_of_range` serves 2, 3 and 4. It is a proxy, and
    `PROXY_RULE_IDS` excludes it from condition 4.
  - `mislabel/ordering`, `sequence/swap` and `sequence/shift` serve 9.
  - The three `coverage` detectors and `sequence/skip` serve 10.
  - `sequence/transitional` serves 11.
  - `overlap/overlapping_segments` serves 15.
  - The three `intensity` detectors serve 16.
  - These serve no mode: the two `border` detectors,
    `spline_offset/spline_offset` (the `displaced_vertebra` condition's), and
    every `reference_delta` and `intensity_reference_delta` detector.
- **The T12/L1 map** (item 186's six-block T12, L1–L5 layout, no T13):
  `relationships.missing_levels == []`. Under the bundled default config,
  every finding `run_rules` returns is `border/unexpected_clip`, because the
  fixture's blocks touch the grid faces. No `coverage` finding and no
  `sequence/skip` finding is returned.
- **`aide check`:** `OK (8 warning(s))`. The eight are: 1 assumptions-block
  warning; 2 awaiting-a-decision warnings (gate-ae46, gate-2f91); 1
  declined-gate warning (gate-51da); and 4 retracted-then-re-accepted warnings
  (Stage 20 criteria 1, 3, 4, 5). Engine 2.25.0.

**In scope:**

- the clean-clone replay and its recorded measurements;
- Stage 33's and Stage 32's acceptance bookkeeping in `progress.md`, through
  `aide progress accept` and `amend`, plus the hand-written annotation §1
  allows beside a box left unticked;
- resolving Stage 32's unmarked D0 deliverable bullet to ❌, with a pointer
  to the items that shipped it (A4);
- the one new in-suite test (AC8), and retiring the one existing test that
  ticking Stage 32's criterion 1 makes false by design;
- one-line `insights.md` findings.

**Not in scope:**

- Fixing anything the replay finds. Each divergence becomes a finding.
- Any change to a mode, rule, detector, threshold, fixture or sign-off.
- Renaming Stage 33 in `roadmap.md` or `progress.md` (a root-document edit).
- Editing `src/segfacet/**`, `vision.md` or any Environment-Gated row.
- Ticking, rewording or archiving any existing `insights.md` entry.

## Acceptance Criteria

There are two kinds of criterion, as in items 151, 161 and 169.

- **In-suite** criteria are pinned by `tests/test_204_stage33_validation.py`.
- **Replay** criteria are executed by the builder and re-executed by the
  validator. Their observed output is recorded verbatim in Decisions &
  Trade-offs, and they add no test.

"The clone" is AC1's clone. "Passes in the clone" means that the named modules
or node ids, run from the clone's own venv in the foreground, exit `0` with no
skip among them. A criterion annotated *(closes Stage N criterion M)* is the
evidence for that criterion. A criterion with no annotation closes none.

### The clean-clone rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  (Replay.) Clone this branch into the session scratchpad. Bootstrap the
  clone's venv with `python <clone>/.aide/scripts/aide.py --repo <clone> env
  --bootstrap`. Record three things:
  - the clone path;
  - the clone's `HEAD` SHA, which equals this branch's tip at clone time;
  - `segfacet.__file__`, as printed by `<clone>/.venv/bin/python -P`, which
    resolves under the clone.

  A resolution under the working checkout invalidates every clone result
  below. The branch tip must already carry the test-writer's commit (AC8), so
  that the clone holds the new module.

### Every generated artifact is current

- [ ] **AC2: each committed generated artifact equals a fresh regeneration in
  the clone.** (Replay.) From the clone's venv, regenerate each artifact into
  a temporary directory and compare the output with the committed file using
  `read_bytes()`. Every comparison must be equal.
  - `docs/aide/failure_modes.generated.json` and `.md`:
    `python -P -m segfacet.failure_modes --json <tmp>/fm.json --md <tmp>/fm.md`
  - `docs/aide/traceability_matrix.generated.json` and `.md`:
    `python -P -m segfacet.traceability --json <tmp>/tm.json --md <tmp>/tm.md`
  - `docs/aide/feature_catalogue.generated.json` and `.md`:
    `python -P -m segfacet.catalogue --json <tmp>/fc.json --md <tmp>/fc.md`
  - `docs/aide/golden_evidence.generated.json`:
    `python -P -m segfacet.golden_evidence --out <tmp>/ge.json`
  - `docs/aide/rules.generated.md`:
    `python -P -m segfacet.rule_table --md <tmp>/rules.md`
  - `tests/corpus/manifest.json` and every file it names:
    `python -P -m segfacet.synth.corpus --out <tmp>/corpus`
  - `tests/corpus/intensity/manifest.json` and every file it names:
    `python -P -m segfacet.synth.intensity --out <tmp>/intensity`

  `docs/aide/corpus_sheet.png` is the one exception. Its bytes depend on the
  matplotlib, FreeType and zlib versions, as `segfacet.synth.corpus_sheet`'s
  module docstring states. So it is checked by its embedded input digest
  instead: `tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current`
  passes in the clone.

  Record each artifact with its result. A mismatch is recorded with its diff
  and is not repaired here.

### Stage 33 criterion 1 / Stage 32 criterion 1: the bar

- [ ] **AC3: modes 2 and 3 each meet all six conditions, recomputed in the
  clone.** (Replay.) For each of modes 2 and 3, in the clone:
  - every record that `traceability.bar_conditions(mode_id)` returns has
    `met is True`, which covers conditions 1–5;
  - `failure_modes.mode_sign_off(mode_id).outcome == "at-the-bar"`, which is
    condition 6 (A7).

  `tests/test_203_modes_2_and_3_signed_at_the_bar.py` and
  `tests/test_168_maintainer_sign_off.py::test_ac9_at_the_bar_claims_are_cross_checked_against_live_state`
  pass in the clone. Record each mode's five `BarCondition` records (number,
  `met`, subjects) and its sign-off record (date, outcome).
  *(closes Stage 33 criterion 1)* *(closes Stage 32 criterion 1)*

### Stage 33 criterion 2: attribution and firing

- [ ] **AC4: every committed case's measured firing equals its expected set,
  across both corpora.** (Replay.) `tests/test_163_specificity_ratchet.py`
  passes in the clone, in full. Read `traceability.build_matrix().conformance`
  in the clone and record:
  - the case ids driven, split by corpus;
  - the count of cases whose `agrees` is `False`, which is expected to be `0`.

  The driven case-id set equals the union of both committed manifests'
  `case_id` values, so no case is exempt.
  *(closes Stage 33 criterion 2)*
- [ ] **AC5: no committed case is attributed to a mode or condition its label
  map does not express, read as A1 defines it.** (Replay.) In the clone:
  - `failure_modes.specification_conflicts()` returns `()`.
  - These modules pass: `tests/test_175_crop_fov_si.py`,
    `tests/test_176_fuse_bridged.py`, `tests/test_195_force_overlap_removed.py`,
    `tests/test_205_mode_2_3_boundary.py` and
    `tests/test_206_fuse_separate_fixture.py`.

  Record one row per committed failure or condition case. Each row gives the
  corpus, the `kind`, the mode or condition the case is attributed to, and
  the dated decision record behind that attribution: the item spec or the
  `insights.md` entry. Each finding of the 2026-09-22 review that named a
  mis-attribution is checked live against its resolution:
  - `crop_at_border` is a `fov_truncation` condition case, not a mode case
    (item 175);
  - `fuse_adjacent`'s fused label is one connected component (item 176);
  - `force_overlap` is absent from both manifests (item 195);
  - `split` is attributed to mode 2, and `split_own_label` to mode 3
    (item 205).

  A case with no recorded decision behind its attribution leaves criterion 2
  unticked, with that case named as the reason.
  *(closes Stage 33 criterion 2)*

### Stage 33 criterion 3: detectors and their modes

- [ ] **AC6: every detector the 2026-09-22 review re-homed serves the mode it
  was re-homed to, and condition 4 is computed per detector.** (Replay.)
  These modules pass in the clone:
  - `tests/test_164_detector_ids.py`
  - `tests/test_187_neighbour_contact_rule.py`
  - `tests/test_188_coverage_rehomed.py`
  - `tests/test_189_spline_offset_condition.py`
  - `tests/test_192_sequence_sub_types.py`
  - `tests/test_193_reference_delta_mode_less.py`
  - `tests/test_194_mode_1_catch_all.py`
  - `tests/test_200_bar_condition_2.py`
  - `tests/test_202_rule_table.py`
  - `tests/test_205_mode_2_3_boundary.py`

  Record every registered `(rule_id, detector_id)` with
  `failure_modes.modes_for_detector` read in the clone. That is the Modes
  column of the regenerated `rules.generated.md` (AC2). Check it against
  these targets:

  | Re-homing | Target |
  |---|---|
  | `fragmentation`'s detectors | neither serves mode 2 or 3 |
  | `neighbour_contact/stray_contact` | `(2,)`. The roadmap named mode 3, and gate-51da re-drew it to mode 2. |
  | each `coverage` detector | `(10,)` |
  | `mislabel/ordering` | `(9,)` |
  | `spline_offset/spline_offset` | `()` |
  | `sequence/swap`, `sequence/shift` | `(9,)` |
  | `sequence/skip` | `(10,)` |
  | `sequence/transitional` | `(11,)` |
  | any `sequence` detector | does not serve mode 12 |
  | every `reference_delta` and `intensity_reference_delta` detector | `()` |

  Also record condition 4's subjects for modes 2 and 3 from
  `bar_conditions`. Each is a `rule_id/detector_id` string, and none names a
  `PROXY_RULE_IDS` rule.
  *(closes Stage 33 criterion 3)*

### Stage 33 criterion 4: the T12/L1 map

- [ ] **AC7: the T12/L1 attestation is replayed in the clone.** (Replay.)
  `tests/test_204_stage33_validation.py` and
  `tests/test_186_expected_level_sequence.py::test_ac2_t12_map_no_coverage_finding`
  pass in the clone. Record each finding that AC8's map produces, as
  `(rule_id, detector_id)`.
  *(closes Stage 33 criterion 4)*
- [ ] **AC8: a label map holding T12 and L1 and no T13 produces no finding
  from any missing-level detector.** (In-suite.) Build the six-block map of
  `tests/test_186_expected_level_sequence.py`: labels 19–24 (T12, L1–L5) and
  no label 28 (T13). Run it through `pipeline.extract_feature_record` and
  `heuristics.run_rules` under `config.bundled_default_config()`. No returned
  finding has a `(rule_id, detector_id)` whose
  `failure_modes.modes_for_detector` intersects `{6, 10}`, the two modes
  that describe an absent level (A3). The missing-level detector set is
  derived from the live rule registry, never listed as a literal, and the
  test asserts that the set is non-empty before it asserts that nothing in
  it fired.

### Stage 33 criterion 5 / Stage 32 criterion 5: the detection count

- [ ] **AC9: Stage 33's criterion-5 evidence states the status and rung
  counts, and each equals a live recomputation.** (Replay.) The evidence
  written by `aide progress accept 33 --criterion 5` contains both of these
  clauses, in item 169's wording:
  - `derived status counts over N modes: validated a, implemented b, specified c, proposed d`
  - `derived mode rung counts: synthetic-demonstrable e, needs-real-data f, structurally-unobservable g, none h`

  It also names what they were measured on: the clone commit and
  `segfacet.failure_modes`. Each integer equals the count recomputed in the
  clone from `SPECIFICATION`, `derive_status` and `derive_mode_rung`, with a
  rung of `None` counted as `none`. The validator recomputes them.
  *(closes Stage 33 criterion 5)*
- [ ] **AC10: Stage 32's criterion 5 is re-stated on the re-grounded corpus,
  and each clause equals a live recomputation.** (Replay.) An
  `aide progress amend 32 --criterion 5` line carries AC9's two clauses plus
  the clause `modes refined by stages 32 and 33: <ids>; at the
  fully-specified bar: <ids>; left as documented drafts: <n>`. In that
  clause:
  - the refined ids are `sorted(MODE_SIGN_OFFS)`;
  - the at-the-bar ids are AC3's set, recomputed over every mode in
    `SPECIFICATION`;
  - `<n>` equals `len(SPECIFICATION) - len(MODE_SIGN_OFFS)`.

  Every value is read in the clone. This is the re-run of Stage 32's D3. Its
  2026-09-22 clause stands as the record of that date.
  *(closes Stage 32 criterion 5)*

### Bookkeeping

- [ ] **AC11: each criterion is attested through the matching verb, and no box
  is ticked on evidence that failed.** (Replay.) Record the exact command and
  the evidence text for each criterion, in ascending order:
  - **Stage 32 criterion 1:** `aide progress accept 32 --criterion 1
    --evidence "…"`, citing AC3. The text states that it supersedes the
    `not attested 2026-09-22` note on the same box.
  - **Stage 32 criterion 5:** `aide progress amend 32 --criterion 5
    --evidence "…"` (AC10).
  - **Stage 33 criteria 1, 2, 3 and 5:** `aide progress accept 33 --criterion
    N --evidence "…"`, citing AC3, AC4 with AC5, AC6, and AC9 respectively.
  - **Stage 33 criterion 4:** this box is already ticked from item 186. The
    clone evidence is appended with `aide progress amend 33 --criterion 4
    --evidence "…"`, citing AC7 and AC8 (A5).

  Each text names the AC or ACs behind it, the clone commit, and the measured
  values. When a criterion's AC does not hold, its box stays unticked:
  - a hand-written ` *(not attested 2026-MM-DD, item 204: <measured
    reason>)*` is appended to the end of its last line;
  - one `gap` line naming the stage, the criterion and the reason is appended
    to `docs/aide/insights.md`.
- [ ] **AC12: Stage 32's unmarked D0 deliverable bullet reads ❌, with a dated
  pointer to items 162 and 163.** (Replay.) Stage 32's D0 bullet is the one
  that says its deliverables "stay tracked by their Stage 20 bullets". The
  diff of this item flips its leading icon from 📋 to ❌ by hand and appends a
  dated (2026-MM-DD) note: the work shipped as items 162 and 163, both ✅
  under Stage 20. No other Stage 32 bullet is hand-edited (A4).

### Environment and suite

- [ ] **AC13: Stage 33 introduces no environment-gated capability, and the
  table is left unchanged.** (Replay.) The builder confirms and records two
  facts:
  - no row of `progress.md`'s Environment-Gated Capability Verification table
    names Stage 33, or any of items 170–208, in its "Introduced by" cell;
  - no item spec numbered 170–208 carries a `## Environment / Hardware
    Dependencies` section.

  Record the output and exit code of `python .aide/scripts/aide.py env`, and
  of `env --profile pyradiomics`, `--profile docker` and `--profile gpu`. The
  table is not edited.
- [ ] **AC14: the full configured suite is green in a fresh clone of the final
  commit.** (Replay.) Once every commit of this item has landed:
  1. Bring AC1's clone up to the branch tip with `python
     <clone>/.aide/scripts/aide.py --repo <clone> sync --item 204`.
  2. Re-print AC1's resolution proof.
  3. Run the configured suite from the clone's venv in the foreground, with no
     explicit path, so that `pyproject.toml`'s `testpaths` covers both `tests`
     and `.aide/scripts/tests`. Use `-n auto`.

  Record:
  - the pass, skip and fail counts;
  - the commit;
  - the reason for each environment-gated skip.

  The run has no failures. A skip is never recorded as verification.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
dependency below had merged before this spec was written, so nothing here pins
an interface ahead of its build. Every value was measured on 2026-10-02 at
`6ebc5d1`.

- **A1: criterion 2's first half is attested against the review's findings and
  the specification's own consistency check.** "No case is attributed to a
  mode or condition its label map does not express" is a judgement about each
  label map, and nothing computes it. The roadmap's D2 lists the
  mis-attributions the 2026-09-22 review found, and each was resolved by a
  merged item with its own tests. AC5 reads the criterion as three facts:
  - the specification's attribution is internally consistent
    (`specification_conflicts() == ()`);
  - every finding the review named is resolved live;
  - every case's attribution has a dated decision behind it.

  The evidence text states this reading, so a reader sees what was checked.
  The legacy `crop_at_border` is still a translate-then-clip, not a true
  in-plane volume crop (item 175, Left open). Its attribution to
  `fov_truncation`'s unexpected in-plane form was kept by the maintainer's
  2026-09-24 decision, which AC5's table cites.
- **A2: criterion 3's first half is attested against the detectors the review
  re-homed.** "No rule declares a mode through a detector that reads another
  mode's signal" also has no computed predicate. Two different modes may
  legitimately read one path: `fused_label` (mode 2) and `split_fragment`
  (mode 3) both read `physical_volume_mm3`. So an overlap of signal paths is
  not the test. The roadmap's D3 names the detectors whose home was wrong, and
  AC6 checks each one's live `modes_for_detector` against its target. Gate
  `gate-51da` re-drew `stray_contact`'s target from mode 3 to mode 2. The
  criterion's second sentence is mechanical as written: condition 4 reads
  `modes_for_detector(rule_id, detector_id)`, which is detector-granular since
  item 164.
- **A3: a "missing-level finding" is a finding from a detector serving mode 6
  (vertebra not segmented) or mode 10 (skipped level label).** Those are the
  two modes that describe an absent level. Item 186's AC2 checked `coverage`
  only, because `sequence/skip`, which also reports an absent level, arrived
  later with item 192. Deriving the set from `modes_for_detector` covers both,
  and it covers a future mode-6 rule without an edit to the test. On
  2026-10-02 the set is the three `coverage` detectors plus `sequence/skip`,
  and mode 6 has no rule.
- **A4 (engine 2.25.0): Stage 32's D0 bullet is resolved to ❌ by hand.** The
  bullet carries no `*(Item NNN)*` marker, so no `aide merge` will ever move
  it. With that bullet left 📋, Stage 32 cannot roll up even once every
  criterion is ticked, which contradicts roadmap D6, "closing Stage 32". Two
  facts rule out the other routes:
  - no verb writes ❌, and `aide progress set --stage 32 --deliverable 1
    deferred` would roll the stage to ⏸️ instead;
  - ✅ is written only by `aide merge`.

  Item 169 used this exact shape for Stage 20's item-141 bullet, a hand-flip
  to ❌ with a dated pointer to where the work landed. Stage 32's D3 bullet
  carries `*(Item 204)*`, so `aide merge 204` flips it ✅ and rolls the stage
  up. A hand ❌ inside the always-authorised `progress.md` is allowed (item
  169 A4).
- **A5 (engine 2.25.0): already-ticked boxes take `amend`, and Stage 32's
  annotated, unticked criterion-1 box takes `accept`.** `accept_criteria`
  reports an already-ticked box as unchanged, so Stage 33 criterion 4 and
  Stage 32 criterion 5 take `amend`. It does not refuse an unticked box that
  carries a hand annotation; only `reword` refuses that. So Stage 32
  criterion 1 is ticked with `accept`, and the 2026-09-22 note stays as the
  record of that date.
- **A6: "every generated artifact" is AC2's list.** That is item 169's six
  generators, plus item 202's `rules.generated.md`, plus item 178's
  `corpus_sheet.png`. The sheet is checked by its embedded input digest, not
  by its bytes, as its module docstring requires. `.gitattributes` pins the
  manifests `text eol=lf` and the `.nii.gz` fixtures `binary`, so the CRLF
  gotcha does not apply.
- **A7: bar condition 6 is a sign-off whose `outcome` is `"at-the-bar"`.** This
  is item 169 A1 and item 203 A2: `BAR_CONDITIONS` is five entries long by
  design, and condition 6 is the `MODE_SIGN_OFFS` record.
- **A8: no new human gate is raised.** `gate-0133` (`Blocks: 203, 204`) is
  `✅ Approved (2026-10-02)`, and the decision this item needs is already
  recorded. `gate-51da` is declined and holds nothing named.
- **A9: the item keeps the queue's title.** "modes 3 and 4" in the stage title
  is stale since `gate-51da`. Renaming a stage is a `roadmap.md` edit, so it
  is captured to `insights.md` and not made here.

## Implementation Steps

1. **Preconditions.** Run `python .aide/scripts/aide.py status` and confirm
   that items 200–203 and 205–208 are ✅. Record `aide check`'s baseline.
2. **Rig (AC1).** Clone the branch tip, after the test-writer's commit, into
   the scratchpad. Bootstrap the clone's venv with the clone's own `aide env
   --bootstrap`, and print the resolution proof.
3. **Artifacts (AC2).** Run the seven regeneration commands into a scratch
   directory from the clone's venv, and compare with
   `pathlib.Path.read_bytes`. Reuse each module's own `--json`, `--md` and
   `--out` arguments. Write no generator and no comparison helper.
4. **Named checks (AC2–AC7).** Run each named module or node id in the clone,
   in the foreground, and record exit codes and counts.
5. **Measurements (AC3–AC6, AC9, AC10).** From the clone's venv, read the
   following, building each once and reusing it:
   - `catalogue.build_catalogue(strict=True)`, passed to every
     `bar_conditions` call;
   - `traceability.build_matrix().conformance`;
   - `failure_modes.specification_conflicts()`;
   - `modes_for_detector` over every registered detector;
   - `MODE_SIGN_OFFS`;
   - `derive_status` and `derive_mode_rung` over `SPECIFICATION`.

   Record each value verbatim.
6. **Bookkeeping (AC10–AC12).** Run the verbs in AC11's order, stage 32
   first. Then hand-flip Stage 32's D0 bullet (AC12).
7. **Findings.** Append one `insights.md` line per divergence the replay
   finds, and one per criterion left unticked. Tick, reword or archive no
   existing entry.
8. **Environment (AC13).** Run `aide env` and the three profile checks, then
   read the gated table and the specs.
9. **Check.** Re-run `aide check`. Record every warning and compare the set
   with the Description's baseline. A new error is a finding, and `aide merge`
   refuses on one (§4). The warning set is pinned nowhere.
10. **Suite (AC14).** Bring the clone up to the final commit, run the
    configured suite, record the counts, then delete the clone.
11. Record everything in Decisions & Trade-offs.

No `src/segfacet/**` change and no new dependency.

## Authorised paths

**May change:**

- `tests/test_204_stage33_validation.py` — the in-suite module (AC8)
- `tests/test_169_stage32_validation.py` — `test_ac10_…` and its orphaned helpers retired (Testing Strategy)

`docs/aide/progress.md` is always authorised, along with `docs/aide/insights.md`
and this spec. The parts of `progress.md` this item edits are: Stage 32's
criteria 1 and 5, Stage 32's D0 bullet, Stage 33's criteria 1–5, and the two
`*(Item 204)*` bullets that `aide progress set` and `aide merge` move. No
other part of `progress.md` is edited.

**Asserts against:**

- `src/segfacet/failure_modes.py` — `SPECIFICATION`, `MODE_SIGN_OFFS`, `modes_for_detector` read live (AC8)
- `src/segfacet/heuristics/**` — every registered rule run over AC8's map
- `src/segfacet/pipeline.py` — `extract_feature_record` builds AC8's record
- `src/segfacet/labels.py` — `CANONICAL_ORDER` decides AC8's missing levels
- `src/segfacet/traceability.py` — `bar_conditions`, `build_matrix` (AC3, AC4, AC6)
- `src/segfacet/catalogue.py` — the catalogue `bar_conditions` reads (AC3)
- `docs/aide/roadmap.md` — Stage 33's and Stage 32's criteria and the bar (AC3–AC11)
- `docs/aide/failure_modes.generated.json` — regenerated and compared (AC2)
- `docs/aide/failure_modes.generated.md` — regenerated and compared (AC2)
- `docs/aide/traceability_matrix.generated.json` — regenerated and compared (AC2)
- `docs/aide/traceability_matrix.generated.md` — regenerated and compared (AC2)
- `docs/aide/feature_catalogue.generated.json` — regenerated and compared (AC2)
- `docs/aide/feature_catalogue.generated.md` — regenerated and compared (AC2)
- `docs/aide/golden_evidence.generated.json` — regenerated and compared (AC2)
- `docs/aide/rules.generated.md` — regenerated and compared; its Modes column (AC2, AC6)
- `docs/aide/corpus_sheet.png` — input digest checked (AC2)
- `tests/corpus/manifest.json` — regenerated and compared; case-id set (AC2, AC4)
- `tests/corpus/fixtures/**` — regenerated and compared (AC2)
- `tests/corpus/intensity/manifest.json` — regenerated and compared; case-id set (AC2, AC4)
- `tests/corpus/intensity/fixtures/**` — regenerated and compared (AC2)
- `tests/test_163_specificity_ratchet.py` — named check (AC4)
- `tests/test_164_detector_ids.py` — named check (AC6)
- `tests/test_168_maintainer_sign_off.py` — named check (AC3)
- `tests/test_175_crop_fov_si.py` — named check (AC5)
- `tests/test_176_fuse_bridged.py` — named check (AC5)
- `tests/test_178_corpus_sheet.py` — named check (AC2)
- `tests/test_186_expected_level_sequence.py` — named check; AC8's map layout (AC7)
- `tests/test_187_neighbour_contact_rule.py` — named check (AC6)
- `tests/test_188_coverage_rehomed.py` — named check (AC6)
- `tests/test_189_spline_offset_condition.py` — named check (AC6)
- `tests/test_192_sequence_sub_types.py` — named check (AC6)
- `tests/test_193_reference_delta_mode_less.py` — named check (AC6)
- `tests/test_194_mode_1_catch_all.py` — named check (AC6)
- `tests/test_195_force_overlap_removed.py` — named check (AC5)
- `tests/test_200_bar_condition_2.py` — named check (AC6)
- `tests/test_202_rule_table.py` — named check (AC6)
- `tests/test_203_modes_2_and_3_signed_at_the_bar.py` — named check (AC3)
- `tests/test_205_mode_2_3_boundary.py` — named check (AC5, AC6)
- `tests/test_206_fuse_separate_fixture.py` — named check (AC5)

## Testing Strategy

**New module:** `tests/test_204_stage33_validation.py`. It is deliberately
small: one AC test (AC8) plus the one case below. Every other criterion is a
replay. Its evidence is the output recorded in Decisions, which the validator
re-executes.

**AC8.**
- Build the map with `tests/synthetic.py`'s `make_labelmap`, in
  `tests/test_186_expected_level_sequence.py`'s six-block layout.
- Build the record once, in a module-scoped fixture, with
  `extract_feature_record` and `bundled_default_config()`.
- Derive the missing-level detector set from
  `heuristics.rule.iter_rules()`. It is every `(rule.rule_id,
  detector.detector_id)` over `rule.mode_declaration.detectors` whose
  `failure_modes.modes_for_detector` intersects `{6, 10}`. Assert that the
  set is non-empty, then that no finding's `(rule_id, detector_id)` is in it.
- Write no rule id or detector id as a literal.

**Adversarial case.** The test-writer writes this one and no other.

- `skipped-level-is-seen:` drop label 22 (L3) from the same layout. The AC8
  predicate, applied to that map's findings, must report at least one
  missing-level finding. This guards a predicate that passes vacuously: one
  that never matches because it reads the wrong attribute, takes `None` for
  `detector_id`, or derives an empty set.

**Discipline.** The module pins nothing that later work legitimately moves:
- no `aide check` warning count;
- no status or rung count;
- no suite total;
- no `progress.md` text;
- no `insights.md` entry;
- no engine version.

The `progress.md` clauses are dated measurements, which the validator checks
on the branch (AC9, AC10). They are not suite assertions, because
`test_169`'s AC8 was retired on 2026-10-02 for pinning exactly such a clause.

**Existing tests to reconcile.** `tests/` was grepped on 2026-10-02 for
`stage_section`, `acceptance_boxes`, `_STAGE_32`, `Stage 33`, `**D0**` and
`Item 204`.

- **Retire**
  `tests/test_169_stage32_validation.py::test_ac10_stage32_criterion1_box_unticked_with_dated_reason`.
  It asserts that Stage 32's first acceptance box stays `- [ ]`. AC11 ticks
  that box, so the test becomes false by design. Also retire what only it
  uses: `_STAGE_32`, `_ANNOTATION_RE` and `_box_text`. Add one dated line to
  the module docstring naming the retirement and its reason, following item
  203's line in the same docstring. AC6, AC7 and AC13 of `test_169` read
  Stage 20 only and stay green: no mode's status or rung moves in this item,
  and Stage 20's last clauses were written by item 208.
- **No edit, checked:**
  - `tests/test_203_modes_2_and_3_signed_at_the_bar.py` reads `gate-0133`,
    not an acceptance box.
  - `tests/test_151_stage30_validation.py`, `tests/test_161_stage31_validation.py`,
    `tests/test_135_*`, `tests/test_125_*` and `tests/test_115_*` read their
    own stages' sections.
  - `tests/test_aide_check_no_errors.py` asserts no errors. A hand ❌ on a
    bullet and a hand annotation on a box are both shapes `aide check`
    accepts (item 169 precedent).

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

This item **is** the stage validation. The validator re-executes the replay
criteria, not only the suite, and checks each Decisions record against its
own run:

- the rig and the resolution proof (AC1);
- each artifact comparison and the sheet digest (AC2);
- the bar recomputation for modes 2 and 3 (AC3);
- the conformance report and the attribution table (AC4, AC5);
- the detector → modes table against AC6's targets (AC6);
- the T12/L1 replay (AC7);
- each `progress.md` clause against a fresh read of `failure_modes` (AC9,
  AC10);
- each `aide progress` command against the `progress.md` diff (AC11);
- the Stage 32 D0 bullet in the diff (AC12);
- the profiles and the gated table (AC13);
- the full-suite counts from a fresh clone of the final commit (AC14);
- `python .aide/scripts/aide.py scope`.

**Environment gating.** No criterion depends on a `[validation]` profile.
`pyradiomics`, `docker` and `gpu` are evaluated and recorded only (AC13).

**Honest downgrade.** A replay that cannot run is recorded as **not
performed**, naming what was missing, and its criterion stays unticked with
that reason. A skip-clean run is never evidence.

**Do not run `aide gate approve` or `aide gate decline`.**

## Dependencies

- **Item 200**: condition 2 made existential and detector-granular (AC3, AC6).
  Merged ✅.
- **Item 201**: the severity-ladder constants re-measured, held by the suite
  (AC14). Merged ✅.
- **Item 202**: `docs/aide/rules.generated.md` (AC2, AC6). Merged ✅.
- **Item 203**: modes 2 and 3 recorded at the bar from `gate-0133` (AC3).
  Merged ✅.
- **Item 205**: the mode 2/3 boundary re-drawn (AC5, AC6). Merged ✅.
- **Item 206**: `fuse_separate` (AC4, AC5). Merged ✅.
- **Item 207**: `fused_label`, mode 2's condition-4 detector (AC3, AC6).
  Merged ✅.
- **Item 208**: `split_fragment`, mode 3's condition-4 detector (AC3, AC6).
  Merged ✅.

Gate `gate-0133` names its reach — `Blocks: 203, 204` — and is approved.

**Downstream:** none in this queue. Item 204 runs last.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** a computed predicate for "a case's label map expresses the
  mode or condition it is attributed to" (A1). AC5 attests on decision
  records, and nothing would catch a future mis-attribution that agrees with
  its own expected set. Building one is a feature item, not a validation.
- **Left open:** a computed predicate for "a detector reads another mode's
  signal" (A2). A plain overlap of signal paths would report `fused_label` and
  `split_fragment`, which legitimately share `physical_volume_mm3`. So the
  question needs a per-mode notion of "own signal", which the specification
  does not author.
- **Left open:** whether the legacy `crop_at_border` should be re-authored as
  a true in-plane volume crop (item 175's own Left open). It still carries
  the stage's only `border` firing.
