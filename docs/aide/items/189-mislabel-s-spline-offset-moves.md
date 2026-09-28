<!-- aide-template: item 2 -->
# Item 189 — `mislabel`'s `spline_offset` moves to a displaced-vertebra condition

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 189
> **Objectives:** G2, G8
> **Suggested branch:** `aide/189-mislabel-s-spline-offset-moves`

---

## Description

This item implements roadmap Stage 33 D3's third bullet. It closes these
`docs/aide/insights.md` entries:

- the two `gap` entries dated 2026-09-22 (queue-022 review): the `mislabel`
  decision, and the displaced-vertebra decision;
- the `defect` entry dated 2026-09-23 (item 173): `mislabel.py`'s docstring
  quotes box-base offset margins, and `test_123` pins them;
- the `defect` entry dated 2026-09-28 (item 188): `mislabel`'s
  `stage3.per_label_offsets[].offset_mm` consumed-path reason names a
  pre-2026-09-15 mode 6.

**Why the move.** `mislabel` is about label consistency. A vertebra that sits
off the spinal curve is a property of the anatomy or of the case
(spondylolisthesis, scoliosis, a rigid misplacement). It is not a segmentation
defect, and the spline-offset signal serves no failure mode since the item-150
sign-off. So `mislabel` keeps only its `ordering` detector. The `spline_offset`
detector becomes the recorder of a new case condition, `displaced_vertebra`, in
`failure_modes.CONDITIONS` beside `fov_truncation`. `displace` becomes that
condition's fixture, the way `crop_at_border` is `fov_truncation`'s.

**The detector needs a rule of its own.** A `ConditionSpec` must name at least
one recording rule, and a detector belongs to a rule. No rule except `mislabel`
reads the offsets, and the queue requires `mislabel` to fire on no
displaced-only case. So the detector moves into a new mode-less rule,
`spline_offset`, modelled on `border` (the rule that records `fov_truncation`).
The registry grows from 11 rules to 12 (A1).

**What this item changes.**

- A new `heuristics/spline_offset.py` registers `SplineOffsetRule`. Its one
  detector, `spline_offset`, is `mislabel`'s Detector A moved unchanged: the
  same threshold (13.0 mm, fired at `>=`), the same terminal exemption, the same
  direction clause and the same reason text (A2, A3).
- `heuristics/mislabel.py` loses Detector A, its constants and helpers, and the
  six `stage3.per_label_offsets[]` consumed paths. The box-base margins leave its
  docstring. The re-measured margins go into the new module's docstring.
- `failure_modes.py`:
  - it gains `_CONDITION_DISPLACED_VERTEBRA`;
  - `displace` leaves mode 1, and so does mode 1's `offset_mm` candidate
    feature;
  - mode 1's mechanism is rewritten;
  - `fov_truncation`'s terminal-skip exemption and its `crop_at_border`
    expected set move to `spline_offset`.
- `DisplacePerturbation`'s `Expectation` becomes a condition expectation. The
  committed manifest's `displace` entry moves with it. No fixture's bytes move.
- `severity_ladder._LADDER_HOMES["displace"]` becomes the condition.
- Prose that points at `mislabel.py` for the offset or its terminal exclusion is
  re-pointed.
- The generated artifacts are regenerated, and the pins listed under Testing
  Strategy are reconciled.

**Not in scope.**

- No change to the offset feature (`features/spline_offset.py` code) or to the
  threshold value. No re-calibration.
- No change to what the `ordering` detector reads or fires on (A4). The
  pipeline's integer-label centroid order, which misreads TPTBox's T13 and
  `Cocc`, is item 192's (`insights.md`, item 186, 2026-09-27).
- No condition gating of other rules. Inverting `ConditionSpec.exempting_rules`
  is item 191's. The condition-keyed eval bucket is item 190's.
- No change to the parsed default config (A5). `force_overlap` is item 195's.

## Acceptance Criteria

Terms used below:

- **"The manifest"** is `segfacet.synth.corpus.load_manifest()`, and **"the
  `X` case"** is its entry whose `case_id == "X"`.
- **"The condition"** is `segfacet.failure_modes.CONDITIONS["displaced_vertebra"]`.
- **"Findings of case `X`"** is `segfacet.synth.regression.pipeline_findings(<the X case>)`.

- [ ] **AC1: `mislabel` declares the `ordering` detector alone.**
  `tuple(d.detector_id for d in MislabelRule.mode_declaration.detectors) == ("ordering",)`.
- [ ] **AC2: `mislabel` reads no spline-offset path.** Over
  `segfacet.catalogue.build_catalogue(strict=True).entries`, no entry whose
  `path` starts with `"stage3.per_label_offsets[]"` has `"mislabel"` in
  `consuming_rules`.
- [ ] **AC3: the `spline_offset` rule declares no failure mode.**
  `get_rule("spline_offset").mode_declaration.modes == ()`.
- [ ] **AC4: the offset is the condition's signal.** The catalogue entry for
  `stage3.per_label_offsets[].offset_mm` has
  `mode_roles == (("spline_offset", "condition-signal"),)`.
- [ ] **AC5: the condition is recorded by `spline_offset`.**
  `CONDITIONS["displaced_vertebra"].recording_rules == ("spline_offset",)`.
- [ ] **AC6: `displace` is a condition case.**
  `segfacet.synth.perturbation.corpus_case_kind(<the displace case>) == "condition"`.
- [ ] **AC7: `displace` is the condition's fixture.**
  `{c.case_id for c in CONDITIONS["displaced_vertebra"].corpus_cases} == {"displace"}`.
- [ ] **AC8: no mode claims `displace`.** No mode in
  `segfacet.failure_modes.SPECIFICATION` carries a corpus case with
  `case_id == "displace"`.
- [ ] **AC9: `mislabel` fires on no displaced-only case.** For every case `c` in
  the condition's `corpus_cases`, `"mislabel" not in segfacet.failure_modes.measured_firing(c)`.
- [ ] **AC10: the condition is recorded on `displace`.** The findings of case
  `displace` with `rule_id == "spline_offset"` are exactly one finding, with
  `detector_id == "spline_offset"` and `labels == frozenset({22})`.
- [ ] **AC11: `crop_at_border`'s firing is re-measured.** For `c`, the
  `crop_at_border` entry of `CONDITIONS["fov_truncation"].corpus_cases`,
  `set(segfacet.failure_modes.measured_firing(c)) == {"border", "spline_offset"}`.
- [ ] **AC12: the terminal-skip exemption moves with the detector.**
  `set(CONDITIONS["fov_truncation"].exempting_rules) == {"coverage", "spline_offset"}`.
- [ ] **AC13: the ordering detector fires on a non-adjacent swap.** On the
  clean-control label map with labels 21 and 23 exchanged (Testing Strategy),
  run through `segfacet.pipeline.run_qc` with `bundled_default_config()`,
  `{f.detector_id for f in <findings> if f.rule_id == "mislabel"} == {"ordering"}`.
- [ ] **AC14: the recorded corpus margins are live.** Each of the three margins
  the `segfacet.heuristics.spline_offset` module docstring records, formatted
  `f"{v:.6f}"`, appears in that docstring, where each `v` is recomputed in the
  test from `extract_feature_record` over the geometric manifest's cases,
  interior entries only (`is_terminal` falsy):
  - the largest `offset_mm` on a case where `spline_offset` does not fire;
  - `crop_at_border`'s label-22 `offset_mm`;
  - `displace`'s label-22 `offset_mm`.

Why each is written:

- AC1 and AC9 are the queue's "`mislabel` keeps its `ordering` detector" and
  "`mislabel` fires on no displaced-only case". AC2 is the catalogue-derived
  proof that the offsets left `mislabel`'s code, not only its declaration. It
  also removes the stale mode-6 reason, which lived on a path `mislabel` no
  longer reads.
- AC3–AC5 are "a condition entry, not a mode". Without AC3 the new rule could
  declare a mode. Without AC4 the offset could be attributed to a mode, or stay
  bookkeeping. Without AC5 the condition has no recorder.
- AC6–AC8 are the queue's "`displace` is a condition case, and no mode claims
  it", one each for the manifest, the condition and the specification.
- AC10 shows that the condition is still recorded after the move.
- AC11 is "`crop_at_border`'s expected set is re-measured". That the authored
  set equals the measured one is the specificity ratchet's job
  (`tests/test_163_specificity_ratchet.py`), so it is not restated.
- AC12 is read by item 191, which states that "`mislabel`'s terminal skip" holds
  under its new default. After this item that skip is `spline_offset`'s.
- AC13 is the roadmap's "extended to any out-of-sequence label" (A4).
- AC14 is the 2026-09-23 defect: the margins are a factual claim, so the test
  recomputes them. `test_123`'s AC16 only checks that literals are present.
- The severity ladder's re-home is not restated. `tests/test_153_eval_harness_rekey.py::test_ac19_ladder_homes_are_derived_from_the_specification`
  derives every ladder's home live from `SPECIFICATION`/`CONDITIONS`/the
  manifest. It fails unless `_LADDER_HOMES["displace"]` becomes
  `(None, "displaced_vertebra")`.
- Mode 1's derived status and rung are held for all 16 modes by
  `test_151`'s AC13/AC18. Both stay `validated` / `synthetic-demonstrable`
  (A7).

None of these closes a Stage 33 acceptance criterion. Criterion 3 ("no rule
declares a mode through a detector that reads another mode's signal") stays
open until D4's detector-granular bar checker, although after this item
`mislabel` no longer carries the mode-less detector.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on 2026-09-28 with `.venv/bin/python`. The
measurements ran against a scratch clone of this branch that carried a
prototype of Implementation Steps 1–6. The clone was run with `python -S` and
the clone's `src` first on `PYTHONPATH`, so the working checkout's editable
install did not shadow it (`CLAUDE.md`, Gotchas). The builder re-measures each
value on the real change.

- **A1 (defensible default: a new rule, `spline_offset`).**
  - `ConditionSpec.recording_rules` must be non-empty. No other rule reads the
    offsets, and `mislabel` must not fire on `displace`.
  - `rule_id = "spline_offset"`. The detector id stays `spline_offset`, as the
    queue names it. The pair is `("spline_offset", "spline_offset")`.
  - The declaration is mode-less, in `border`'s form:
    - a `mode_less_reason` naming `CONDITIONS['displaced_vertebra']` and
      `displace`;
    - `offset_mm` is `condition-signal`, with a reason naming the condition;
    - `dx_mm`, `dy_mm`, `dz_mm`, `is_terminal`, `label` and `level_name` are
      `bookkeeping`, each with a reason;
    - the detector carries a `mode_less_reason`.
  - The rule count goes from 11 to 12. Item 187 paid the count pins for its own
    rule; this item pays them again (see Testing Strategy).
- **A2 (defensible default: behaviour moves unchanged).**
  - The detector's evaluate logic, `_MISALIGN_TAG`
    (`"Vertebra misaligned from spinal curve:"`), `_DEFAULT_MAX_OFFSET_MM = 13.0`,
    the `>=` comparison, the terminal skip, the direction clause, the
    ascending-label order and the severity `ValueError` move verbatim.
  - The only visible difference is the finding's `rule_id`: `"spline_offset"`
    instead of `"mislabel"`.
- **A3 (defensible default: the rule's params).**
  - The rule reads `rules.spline_offset.params.max_offset_mm` (default 13.0) and
    `rules.spline_offset.params.severity` (default `"flagged-for-review"`).
  - It is enabled when the section is absent, like `neighbour_contact`.
  - `flag_offset_outliers` is retired, and `rules.spline_offset.enabled: false`
    replaces it.
  - `mislabel` keeps reading `severity` and `flag_order_inconsistency` only.
- **A4 (defensible default: the `ordering` detector is not rewritten).**
  - The roadmap says the `ordering` detector is "extended to any out-of-sequence
    label". Measured on the clean control, it already fires on every relabelling
    tried:
    - adjacent swap 21↔22: pairs (L2, L3);
    - non-adjacent swap 21↔23: pairs (L2, L3) and (L3, L4);
    - swap 20↔24;
    - a 3-cycle;
    - L1 moved between L3 and L4.
  - Any non-identity permutation of the integer-label order has a descent in
    `u`. The one exception is a full reversal, which items 131/132's traversal
    normalisation reads as the same spine flipped.
  - So the extension is met by the existing detector and pinned by AC13.
  - Which labels a finding names is left open. For the swap 20↔24 it names
    21–23, the descent pairs, not the moved labels.
- **A5 (forced: the parsed default config does not change).**
  - `reference.artifact.config_hash` hashes the whole `rules` dict. Both
    committed references carry it in their provenance:
    - `tests/test_065_config_intensity.py`'s AC12,
    - `tests/test_090_reference_derived_defaults.py`'s AC16,
    - and `tests/test_123_recalibrate_and_regenerate.py`'s AC20/AC21
    compare it live.
  - Rebuilding `reference_verse_v1.json` needs the real VerSe cohort.
  - So `default_config.yaml` keeps `mislabel.params.max_offset_mm: 13.0` and
    `flag_offset_outliers: true` as unread keys, with a comment saying so and
    why. A commented, section-less `spline_offset` block documents the new
    params, in `neighbour_contact`'s form.
  - `HeuristicConfig` ignores unknown keys (`config.py`), so nothing rejects
    them.
- **A6 (measured: what moves in the corpus and the records).**
  - Regenerating the corpus changes `tests/corpus/manifest.json` only. Every
    fixture is byte-identical.
  - The `displace` entry becomes `condition: "displaced_vertebra"`,
    `failure_mode: 0`,
    `failure_mode_name: "displaced vertebra (condition, not a failure mode)"`,
    `kind: "condition"` and `expected_rule_ids: ["spline_offset"]`.
    `expected_labels [22]` and `flagged-for-review` are unchanged.
  - Geometric kinds become clean_control 1, condition 3, failure 10 (were 1, 2,
    11). `failure_mode` counts: 0:4, 1:1 (were 0:3, 1:2).
  - Findings, by case:
    - `displace`: `spline_offset/spline_offset` on 22 (was
      `mislabel/spline_offset`);
    - `crop_at_border`: `border/unexpected_clip` on 22 and
      `spline_offset/spline_offset` on 22;
    - `relabel_swap`: `mislabel/ordering` on (21, 22), unchanged;
    - every other case of both corpora: unchanged.
  - Displace-ladder rungs (4, 8, 12, 16 mm): the label-22 offset reads 3.9496,
    8.0879, 10.8277 and 14.91 mm. Only the 16 mm rung fires, and it fires
    `spline_offset`. `mislabel` fires on no rung.
  - Interior offsets:
    - largest non-firing: `relabel_swap` label 23, **5.624555**;
    - `crop_at_border` label 22: **18.025609**;
    - `displace` label 22: **14.615923**. That is 1.62 mm above the threshold.
      Item 177's lateral form lowered it from item 173's 17.615126.
  - Derived statuses, rungs, per-edge rungs and the validated split are
    unchanged: validated 6, implemented 3, specified 1, proposed 6; rungs 5/3/1,
    none 7; 18 edges 5/12/1; pipeline 5, reconstructed 1. So `progress.md`
    needs no amendment. Mode 1 stays `validated` through `fragment`.
  - Conformance stays 18 agreeing and 0 disagreeing. `displace`'s row becomes
    `mode 0`, `expected_source "specification-condition"`.
  - `scan_synth_rule_mode_map()["mislabel"]`: (1, 9) → (9,).
    `specification_conflicts()`, `rule_declaration_conflicts()` and
    `path_classification_conflicts()` stay `()`, once the dead Detector A
    helpers are deleted (their literal keys otherwise keep mechanism B
    attributing `is_terminal`/`offset_mm` to `mislabel`).
  - `docs/aide/golden_evidence.generated.json` does not move.
    `docs/aide/corpus_sheet.png` moves, because the manifest digest moves.
- **A7 (measured: generated-artifact deltas).**
  - `feature_catalogue`:
    - the seven `stage3.per_label_offsets[]` paths change `consuming_rules` and
      `rule_evidence` from `mislabel` to `spline_offset`, and `mode_evidence`
      gains `rule_mode_less`;
    - `offset_mm`'s role becomes `condition-signal`, and its evidence becomes
      `rule_mode_less`, `rule_condition_signal`;
    - `non_monotonic_pairs[]`'s `failure_modes` goes (1, 9) → (9,);
    - mode 1's path count goes 13 → 12;
    - there are still 145 leaf paths.
  - `traceability_matrix`:
    - `features.by_rule` has `mislabel` 9 → 2 and `spline_offset` 7;
    - exercise has `mislabel` exercised by `relabel_swap` only, and
      `spline_offset` by `crop_at_border` and `displace`. There are 12 rules:
      10 exercised, and 2 unexercised (`reference_delta`,
      `intensity_reference_delta`);
    - declaration states are 10 declared and 2 mode-less (`border`,
      `spline_offset`);
    - there are 22 `(rule, detector)` pairs;
    - the `mode_to_rule` holes are unchanged;
    - mode 1's row loses `displace`.
  - `failure_modes`: mode 1, the new condition, and `fov_truncation`.
- **A8 (defensible default: the condition's fields).**
  - `id="displaced_vertebra"`.
  - `name="Displaced vertebra (centroid off the spinal curve)"`.
  - `short_name="displaced vertebra (condition, not a failure mode)"`, in
    `fov_truncation`'s form.
  - `scope="vertebra"`.
  - `candidate_features`: `offset_mm`, `dx_mm`, `dy_mm`, `dz_mm`,
    `is_terminal`.
  - `recording_rules=("spline_offset",)`.
  - `exempting_rules=()`: nothing exempts a displaced label today, and item 191
    decides the gate.
  - One corpus case, `displace`, with `expected_firing=("spline_offset",)` and a
    dated `reason` that quotes A6's value.
  - `feature_docs.CONDITION_ANCHOR_PATHS` is **not** extended. That map records
    Stage-18 metric anchors, and no per-mode metric reads the offset. So the two
    tests that pin `set(CONDITION_ANCHOR_PATHS) == set(CONDITIONS)` exempt
    `displaced_vertebra` by name.
- **A9 (defensible default: mode 1's candidate feature).** Mode 1's
  `stage3.per_label_offsets[].offset_mm` candidate feature (hypothesised) is
  removed. It was listed only because of `displace`. The roadmap files the
  offset as an anatomy signal, and it moves to a clinical group in Stage 27.
  Mode 1 keeps `eval.per_mode.unanchored_foreground_fraction`, so that metric's
  home stays mode 1 by `test_153`'s rule (a). The `displace` ladder keeps that
  designated metric. Only the ladder's home moves.
- **A10: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/spline_offset.py`** (new).
   - `SplineOffsetRule`, per A1–A3.
   - Move `_MISALIGN_TAG`, `_DEFAULT_MAX_OFFSET_MM`, the `_dominant_direction`
     helper and `_detect_offset_outliers`'s body from `mislabel.py`.
   - Reuse `mislabel`'s `_severity_from_param` pattern (`border.py` has the same
     one).
   - The module docstring carries:
     - the design decisions and a scope fence;
     - `mislabel.py`'s "Threshold calibration (item 123)" section, moved;
     - the corpus margins re-measured on the lordotic base (A6: 5.624555,
       18.025609 and 14.615923 mm, dated 2026-09-28);
     - the artifact name `reference_verse_v1.json`.
   - `test_123`'s AC16 reads all of these.
2. **`src/segfacet/heuristics/__init__.py`.** Import the module so it
   registers.
3. **`src/segfacet/heuristics/mislabel.py`.**
   - Delete Detector A:
     - the six offsets `ConsumedPath`s and the `spline_offset` `RuleDetector`;
     - `_MISALIGN_TAG`, `_DEFAULT_MAX_OFFSET_MM`, `_dominant_direction` and
       `_detect_offset_outliers`;
     - the `max_offset_mm` and `flag_offset_outliers` reads.
   - The dead helpers must go. Their literal keys otherwise keep catalogue
     mechanism B attributing the offsets to `mislabel` (A6).
   - Rewrite the module docstring, the class docstring, the class comment and
     `evidence`. They describe one detector, serving mode 9, and record that
     item 189 moved the offset detector to `spline_offset`. Drop the box-base
     margins.
   - Cite `failure_modes.SPECIFICATION`, never vision.md §6
     (`test_161`'s criterion-2 prose scan).
4. **`src/segfacet/failure_modes.py`.**
   - Add `_CONDITION_DISPLACED_VERTEBRA` per A8. Append it to the
     `_build_conditions` tuple.
   - Its mechanism says that:
     - `spline_offset` records the condition on `displace`'s label 22 via
       `stage3.per_label_offsets[].offset_mm`;
     - the condition also co-fires on `crop_at_border`, because the crop
       displaces the centroid;
     - the offset is an anatomy signal.
   - `_MODE_1`:
     - remove the `displace` `CorpusCaseExpectation` and the `offset_mm`
       candidate feature (A9);
     - rewrite `mechanism` without the `displace` sentence. It must name
       `fragment` as a whole word. It must name no
       `stage3.per_label_offsets[]` path: `test_138`'s
       `test_ac31_named_feature_path_is_consumed_by_one_of_the_modes_declared_rules`
       requires every catalogue path a mode's mechanism names to be consumed
       by one of that mode's declared rules or by a co-detecting rule (a rule
       in one of its cases' `expected_firing`), and no mode-1 case fires
       `spline_offset`. Item 187 lost a validation round to this check.
   - `_CONDITION_FOV_TRUNCATION`:
     - `exempting_rules=("spline_offset", "coverage")`;
     - `crop_at_border`'s `expected_firing=("border", "spline_offset")`;
     - its `reason` is re-measured and dated. It must still contain `centroid`,
       and `curve` or `spline` (`test_145`'s AC14);
     - the mechanism's two `mislabel` sentences are re-pointed to
       `spline_offset`.
   - Module docstring: add the condition to the taxonomy table, and append a
     dated item-189 paragraph. The 2026-09-14 history bullets stay as the
     record.
5. **`src/segfacet/synth/identity_ordering_alignment.py`.**
   `DisplacePerturbation`'s `Expectation`:
   - `failure_mode=CLEAN_CONTROL_MODE`;
   - `condition="displaced_vertebra"`;
   - `failure_mode_name=CONDITIONS["displaced_vertebra"].short_name`;
   - `expected_rule_ids={"spline_offset"}`.

   Follow `coverage_border_overlap.py`'s `FOV_TRUNCATION_CONDITION` constant
   pattern. Re-point the class and module docstrings. Both detail strings still
   say "held-out per-label spline offset (item 120)", and that stays true.
6. **`src/segfacet/eval/severity_ladder.py`.** Set
   `_LADDER_HOMES["displace"] = (None, "displaced_vertebra")`. Add one dated
   comment line. Constants, margins and `MODE_LADDER_DISPOSITIONS` stay.
7. **Prose re-pointed.** Each of these is comment- or docstring-only:
   - `src/segfacet/feature_docs.py`: the Stage-3 group intro's "the mislabel
     rule", `is_terminal`'s `computation`, and the item-154 anchor comment's
     "(the path itself stays listed there)" sentence;
   - `src/segfacet/features/spline_offset.py`: the docstring's `mislabel`
     pointers;
   - `src/segfacet/reference/ingest.py`: the terminal-exclusion comment;
   - `src/segfacet/heuristics/reference_delta.py`: the class comment's
     "mislabel's offset paths";
   - `scripts/rebuild_verse_reference.py`: the three `mislabel.max_offset_mm`
     strings;
   - `src/segfacet/default_config.yaml`: A5's comments only. The parsed dict
     must not change.
8. **Regenerate.** Run each of the following twice into temp paths,
   byte-compare the two runs, then write the committed copy:
   - `.venv/bin/python -m segfacet.synth.corpus --out <tmp>`. Copy only
     `manifest.json`. Every fixture must byte-match the committed one (A6); if
     one does not, hand back;
   - `segfacet.synth.corpus_sheet`;
   - `segfacet.failure_modes`, `segfacet.traceability` and
     `segfacet.catalogue`;
   - `segfacet.golden_evidence`, which must come out unchanged.
9. **Reconcile** the tests under Testing Strategy, each change with a dated
   item-189 comment.
10. Run `python .aide/scripts/aide.py scope 189` and
    `python .aide/scripts/aide.py check`. Both must report no error.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/spline_offset.py` — **new**: the rule (step 1).
- `src/segfacet/heuristics/__init__.py` — registers it (step 2).
- `src/segfacet/heuristics/mislabel.py` — Detector A removed (step 3).
- `src/segfacet/failure_modes.py` — the condition, mode 1 and `fov_truncation` (step 4).
- `src/segfacet/synth/identity_ordering_alignment.py` — `displace`'s expectation (step 5).
- `src/segfacet/eval/severity_ladder.py` — the ladder home (step 6).
- `src/segfacet/feature_docs.py` — prose (step 7).
- `src/segfacet/features/spline_offset.py` — docstring only (step 7).
- `src/segfacet/reference/ingest.py` — one comment (step 7).
- `src/segfacet/heuristics/reference_delta.py` — one comment (step 7).
- `src/segfacet/default_config.yaml` — comments only (A5).
- `scripts/rebuild_verse_reference.py` — three strings (step 7).
- `tests/corpus/manifest.json` — `displace`'s entry (step 8).
- `docs/aide/corpus_sheet.png` — the manifest digest moved (step 8).
- `docs/aide/failure_modes.generated.json` — regenerated.
- `docs/aide/failure_modes.generated.md` — regenerated.
- `docs/aide/traceability_matrix.generated.json` — regenerated.
- `docs/aide/traceability_matrix.generated.md` — regenerated.
- `docs/aide/feature_catalogue.generated.json` — regenerated.
- `docs/aide/feature_catalogue.generated.md` — regenerated.
- `tests/test_189_spline_offset_condition.py` — **new**: this item's test module.
- `tests/test_033_mislabel.py` — Detector A tests re-pointed to the new rule.
- `tests/test_035_default_config.py` — AC3's constant import.
- `tests/test_039_identity_ordering_alignment_perturbations.py` — `displace`'s expectation.
- `tests/test_041_regression_suite.py` — the `displace` case's rule id.
- `tests/test_098_stray_components.py` — offset-finding rule ids.
- `tests/test_100_severity_ladder.py` — the `displace` ladder's home.
- `tests/test_101_per_mode_cohort.py` — `displace` mode-1 premises.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP["mislabel"]` and the condition-anchor key set.
- `tests/test_109_attribution_scale.py` — `displace` mode-1 premises.
- `tests/test_116_ras_native_corpus.py` — `_ITEM_120_ADDED_MISLABEL_PAIR`'s rule id.
- `tests/test_119_curve_formulation.py` — offset-constant import.
- `tests/test_120_leave_one_out_offset.py` — offset rule id and constant.
- `tests/test_123_recalibrate_and_regenerate.py` — constant, config, docstring and rule-id pins.
- `tests/test_125_stage28_validation.py` — offset threshold and rule-id pins.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — offset rule id and constant.
- `tests/test_136_rule_mode_declarations.py` — rule count, pair count, co-detection witness.
- `tests/test_137_mode_less_rule_disposition.py` — rule count, condition-anchor keys.
- `tests/test_138_traceability_matrix.py` — `RULE_IDS`.
- `tests/test_145_eight_hypothesised_modes.py` — `crop_at_border` expectation, exemption, mode-1 cases.
- `tests/test_148_per_path_mode_attribution.py` — threshold-constant map and rule counts.
- `tests/test_149_conformance_report.py` — `crop_at_border`'s expected firing.
- `tests/test_151_stage30_validation.py` — offset-constant import and `crop_at_border` set.
- `tests/test_154_ladder_remeasurement.py` — only if the suite names it: ladder homes.
- `tests/test_164_detector_ids.py` — the moved `(rule, detector)` pair.
- `tests/test_177_displace_lateral.py` — `displace`'s specification lookup.
- `tests/test_187_neighbour_contact_rule.py` — AC5's rule count, 11 → 12.

**The reconciliation fence.** Every edit to an existing test is one of:

- a moved literal;
- a re-pointed import;
- an offset finding's rule id changed from mislabel to spline_offset;
- a config section re-pointed from rules.mislabel to rules.spline_offset;
- a named exemption (A8).

Each carries a dated item-189 comment. No test is retired, skipped,
`xfail`-marked or loosened. A red test in a file not listed here is a
hand-back to spec-author.

**Asserts against:**

- `tests/corpus/fixtures/displace_seg.nii.gz` — AC10 and AC14 read it. Its bytes must not move (A6).
- `tests/corpus/fixtures/crop_at_border_seg.nii.gz` — AC11 and AC14 read it unchanged.
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC13 builds its swap from it.
- `tests/test_153_eval_harness_rekey.py` — AC19 derives the ladder re-home live (not restated here).
- `tests/test_163_specificity_ratchet.py` — must stay green; red unless step 4 re-authors both expected sets.
- `tests/test_065_config_intensity.py` — AC12's `config_hash` pin proves A5.
- `tests/test_090_reference_derived_defaults.py` — AC16 proves A5.
- `docs/aide/golden_evidence.generated.json` — must not move (A6).

## Testing Strategy

The test module is `tests/test_189_spline_offset_condition.py`, with one test
per AC. AC9–AC11 read firing through `failure_modes.measured_firing` or
`regression.pipeline_findings`, never a re-implementation. AC14 recomputes all
three margins from `extract_feature_record` and derives the "does not fire" set
from `pipeline_findings`, not from a literal case list.

**AC13's map**, verified by a probe on 2026-09-28: the committed clean control
with every voxel of label 21 set to 23 and of 23 set to 21. `run_qc` gives
`mislabel/ordering` findings on (21, 22) and (22, 23), with
`non_monotonic_pairs [["L2","L3"],["L3","L4"]]`, and no other rule fires. The
test asserts AC13's equality, not those pairs.

Named adversarial cases, and no others:

- `every-displace-rung-silent-for-mislabel`: for each rung of
  `severity_ladder.SEVERITY_LADDERS["displace"]`, applied to the clean control
  through the registered operators, `run_qc` yields no `mislabel` finding. It
  guards AC9 passing on one magnitude while the moved detector still lived in
  `mislabel` behind a different threshold. Measured: the rungs read 0.34, 3.95,
  8.09, 10.83 and 14.91 mm, and `mislabel` fires on none.
- `threshold-read-from-own-section`: with `rules.mislabel.params.max_offset_mm`
  set to 1000.0, the displace record still yields its `spline_offset` finding.
  With `rules.spline_offset.params.max_offset_mm` set 1e-9 above that record's
  label-22 `offset_mm`, it yields none. It guards the new rule still reading the
  unread `mislabel` key that A5 keeps.
- `mode-less-detector-excused`: `segfacet.failure_modes.modes_for_detector("spline_offset", "spline_offset") == ()`,
  and the detector's `mode_less_reason` is non-empty. It guards the
  `detector_to_edge` direction treating the detector as an unattributed hole.

**Existing tests to reconcile.** This list comes from targeted greps. They
covered:

- the rule count `== 11`;
- `RULE_IDS`;
- `_DEFAULT_MAX_OFFSET_MM`, `misaligned from spinal`, `flag_offset_outliers`
  and `max_offset_mm`;
- `("mislabel", 1)` and `(1, 9)`;
- `{"border", "mislabel"}`;
- `set(fm.CONDITIONS)`;
- `displace` together with mode/kind/`SPECIFICATION[1]`;
- `exempting_rules`.

Four broader read-only sweeps were launched but had not reported when this spec
was committed. So the builder treats a red test outside this list as a
hand-back.

- **Rule count 11 → 12:**
  - `test_136` lines 194 (`len(pairs) == 11`: re-measure; one entry per
    registered rule → 12) and 255;
  - `test_137` line 224;
  - `test_187` line 250 (AC5);
  - `test_148` lines 365, 1037, 1072 (`checked == 11` → 12), and add
    `"spline_offset": {"_DEFAULT_MAX_OFFSET_MM": 13.0}` beside line 1000,
    removing it from `"mislabel"`.
- **Rule-id enumerations:** `test_138`'s `RULE_IDS` (line 155) gains
  `"spline_offset"` after `"sequence"`.
- **Co-detection and the rule→mode map:**
  - `test_136` line 336 drops `("mislabel", 1)`;
  - `test_103` line 591 `_RULE_MODE_MAP["mislabel"]` becomes `(9,)`, with its
    docstring at line 637.
- **Condition anchors (A8):** `test_137` line 982 and `test_103`'s
  `test_ac14_condition_anchor_paths_key_set_is_the_catalogued_conditions`
  compare against `set(CONDITIONS) - {"displaced_vertebra"}`, exempted by name.
  `test_147` line 337 (`<=`) stays green.
- **`crop_at_border`'s expected set:**
  - `test_145` `test_ac14_fov_truncation_case_expects_border_and_mislabel_with_reason`
    becomes `("border", "spline_offset")`, and its exemption asserts on
    `"spline_offset"`;
  - `test_149` line 845 becomes `["border", "spline_offset"]`;
  - `test_151` line 408 becomes `{"border", "spline_offset"}`;
  - `test_125` AC16 (`test_ac16_mode6_fires_both_border_and_mislabel`) now
    expects `"spline_offset"`.
- **Offset constant, config and rule id:**
  - `test_035_default_config` AC3 imports the constant from
    `segfacet.heuristics.spline_offset`. It still asserts that the retained
    `mislabel.max_offset_mm` key equals it (A5);
  - `test_151` lines 84 and 151 point at `spline_offset`;
  - `test_123`: every `_DEFAULT_MAX_OFFSET_MM` import, `_write_mislabel_config`
    (→ `rules: spline_offset`), `_mislabel_findings` (→ `rule_id ==
    "spline_offset"`), the AC15 `displace`/`crop_at_border` rule ids, AC16's
    docstring pin (module → `segfacet.heuristics.spline_offset`, literals →
    `5.624555`, `18.025609`, `14.615923`), `test_ac45`'s ceiling, and line 728's
    config read;
  - `test_125`: AC9 reads `rules.spline_offset`'s threshold (default 13.0,
    since the section is absent). AC11 filters `spline_offset`;
  - `test_033_mislabel`: every Detector A test (AC3–AC5 and the offset
    adversarials) runs against `SplineOffsetRule` / `rule_id "spline_offset"`
    with `rules.spline_offset` params. The ordering tests stay;
  - `test_120`, `test_129`, `test_119` and `test_098`: offset-finding filters
    and constant imports are re-pointed;
  - `test_116` lines 396–443: `_ITEM_120_ADDED_MISLABEL_PAIR` becomes
    `("spline_offset", (22,))`, with its prose.
- **`displace`'s attribution:**
  - `test_177` line 147 reads the case from
    `CONDITIONS["displaced_vertebra"].corpus_cases`, and line 151 becomes
    `("spline_offset",)`;
  - `test_039` pins `DisplacePerturbation`'s `Expectation` (mode 1,
    `{"mislabel"}`), which becomes failure_mode 0, the condition and
    `{"spline_offset"}`;
  - `test_041` line 290's `displace` case asserts its designated rule;
  - `test_101` and `test_109` use `displace` as a mode-1 example: premises
    re-read against A9;
  - `test_164` line 596 selects `mislabel` for a detector check.
- **Ladder home:** `test_100` (23 hits) and `test_154` line 457 pin
  `displace`'s home or mode. Each becomes `failure_mode is None`,
  `condition == "displaced_vertebra"`. `test_154` is expected green, because
  `MODE_LADDER_DISPOSITIONS[1]` derives from metric homes.
- **`progress.md` clauses:** `test_151` AC35 and `test_169` AC6/AC7 stay green
  unedited, because no count they parse moves (A6).

## Validation

1. Replay `displace` through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/displace_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives. `<tmp>/segfacet_report.json`
   must hold exactly one finding: `rule_id "spline_offset"`, `detector_id
   "spline_offset"`, labels `[22]`, reason `Vertebra misaligned from spinal
   curve: label 22 (L3) centroid lies 14.6 mm off the fitted spinal curve,
   predominantly left-right (threshold 13.0 mm).` The verdict is
   `flagged-for-review`. This was verified on the prototype on 2026-09-28.
2. In `docs/aide/failure_modes.generated.md`:
   - a `## Condition displaced_vertebra` section lists recording rule
     `spline_offset` and case `displace`;
   - mode 1 lists `fragment` only.

No environment profile is needed.

## Dependencies

- Item 186: re-measured the `split_own_label` expected set this item's
  ratchet run reads (✅).
- Item 187: set the rule count this item moves from 11 to 12, and
  `test_187`'s AC5 pins it (✅).
- Item 188: last amended mode 6/10 and the matrix pins this item
  reconciles (✅).

**Downstream:**

- Item 190's condition-keyed eval bucket needs this item's second condition.
- Item 191 reads `fov_truncation.exempting_rules` (AC12), and the new
  condition's gate is its to decide.
- Item 192 owns the ordering input's label order (A4).
- Stage 33 D4's `rules.generated.md` gains `spline_offset`'s row.

## Decisions & Trade-offs

Implemented per Assumptions A1-A10 with no deviation. Notes recorded during
implementation (2026-09-28):

- The re-measured margins (Implementation Step 1) matched the Assumptions'
  prototype-measured values exactly on the real branch: relabel_swap label 23
  `5.624555` mm, crop_at_border label 22 `18.025609` mm, displace label 22
  `14.615923` mm (`extract_feature_record` over the real changes, not the
  scratch clone). No adjustment to the module docstring's cited literals was
  needed.
- `default_config.yaml`'s new `spline_offset` block is commented, in
  `neighbour_contact`'s form, exactly as A5 requires; `mislabel.max_offset_mm`
  and `flag_offset_outliers` stay as retained, unread, commented-explained
  keys. `config_hash` was measured unchanged before and after
  (`a706a888da4283885a75267f33beffc7070b311dca2f276f785caf6ab61e6ef5` for both
  `reference_verse_v1.json` and `reference_default.json`), confirming A5.
- Regenerating `tests/synth.corpus` changed only `tests/corpus/manifest.json`
  (`displace`'s entry, byte-identical to A6's description); every fixture
  byte-matched the committed copy on two independent runs. `docs/aide/
  golden_evidence.generated.json` regenerated byte-identical, confirming A6.
  `docs/aide/corpus_sheet.png` moved, as expected.
- `aide check` reports 0 errors (10 pre-existing warnings, unrelated to this
  item). `aide scope 189` reports one file outside the spec's Authorised
  paths: `tests/test_035_failure_modes.py`, edited by the test-writer's
  reconciliation commit (`32bd207`) to re-point `test_ac19_mode1_
  misalignment_fires_mislabel` and `_MODE_RECORDS_AND_RULE_IDS`'s mode-1 row
  from `"mislabel"` to `"spline_offset"` -- exactly the reconciliation
  fence's "an offset finding's rule id changed from mislabel to
  spline_offset" pattern, but the file itself is missing from this spec's
  Authorised paths test list (only `tests/test_035_default_config.py` is
  named there; `test_035_failure_modes.py` is a distinct file from the same
  item-035 stage). This is a builder-visible spec omission, not a
  content contradiction between the spec and the test: the change itself is
  faithful to the fence and needed for the suite to stay green. Left for the
  orchestrator/spec-author to add `tests/test_035_failure_modes.py` to the
  Authorised paths list (a one-line addition) rather than for the builder to
  edit the spec's Authorised paths section, which is out of this role's
  edit scope (Decisions & Trade-offs only).
- **Left open:** which labels an `ordering` finding names for a non-adjacent
  permutation. For the swap 20↔24 it names the descent pairs (labels 21–23),
  not the moved labels. Naming the out-of-sequence labels is sub-type
  reporting, and item 192 owns it (A4).
- **Left open:** removing the unread `mislabel.max_offset_mm` and
  `flag_offset_outliers` keys from `default_config.yaml`. That is done with the
  next reference rebuild, which moves `config_hash` anyway (A5).
- **Left open:** the `displace` fixture's 1.62 mm margin above the 13.0 mm
  threshold (A6). Widening it is a fixture or threshold decision for the
  at-the-bar review or for Stage 21's real-GT re-calibration.
