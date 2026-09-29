<!-- aide-template: item 3 -->
# Item 198 — `mislabel`'s `ordering` detector judges order along the expected sequence

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-026.md`](../queue/queue-026.md) · Item 198
> **Objectives:** G2, G8
> **Suggested branch:** `aide/198-mislabel-s-ordering-detector-judges`

---

## Description

This item closes the `defect` entry in `docs/aide/insights.md` dated
2026-09-28 (item 192, id `2026-09-28-d6ed`), recorded in item 192's A11.

**The defect.** `mislabel`'s `ordering` detector fires on
`stage3.monotonic_consistency.non_monotonic_pairs[]`.
`segfacet.pipeline.extract_feature_record` builds that field by passing
`compute_monotonic_consistency` the centroids in ascending integer-label
order. TPTBox integer values are not anatomical order: T13 is 28, after
L1–L6 (20–25), and `Cocc` is 27, before S2–S6 (29–33). So a correctly
labelled T13 or coccyx reads as out of order. Measured on 2026-09-29 on the
clean control:

- relabelled T13, L1–L4 head-to-tail (T13 correctly above L1), the detector
  fires on (20, 21), (21, 22) and (22, 23);
- relabelled L4, L5, S1, S2, `Cocc` head-to-tail (the coccyx correctly last),
  it fires on (27, 29).

**The fix, in the feature.** The pipeline hands
`compute_monotonic_consistency` the centroids in anatomical order: sorted by
their level name's `segfacet.labels.CANONICAL_ORDER` index. That order agrees
with item 186's expected sequence for every level the sequence contains (A2).
The rule is not changed. Every other Stage 3 feature, and `relationships`,
keeps reading the ascending-integer sequence (A1, A3).

**What moves on the corpus** (A5, measured). `sequence_break`, whose tail L5
is relabelled T13, gains three `mislabel` `ordering` findings. Its T13 now
sits below L4 in the order judged, which is a real ordering break. The
findings name the lumbar pairs rather than T13, which is an older limit of the
traversal direction (A8, Left open). Nothing else fires differently in either
corpus, and no verdict moves.

**Not in scope.**

- `compute_monotonic_consistency` itself, and item 132's traversal-direction
  convention in `segfacet.features.consistency` (A8).
- `relationships.is_continuous` / `out_of_order_labels[]`, which still walk
  integer order (item 192's Left open).
- The spline fit and every other Stage 3 feature. They keep the
  ascending-integer input.
- `tests/corpus/manifest.json`, the corpus fixtures, the severity ladders and
  every config key.

## Acceptance Criteria

Terms used below:

- **`cfg`** is `segfacet.config.bundled_default_config()`.
- **"The manifest"** is `segfacet.synth.corpus.load_manifest()`, and **"the
  `X` case"** is its entry whose `case_id == "X"`.
- **"The clean map"** is
  `segfacet.synth.regression.loaded_seg_image(<the clean_control case>)`:
  labels 20–24 (L1–L5), with L1 the most superior.
- **`relabel(M)`** is the clean map with every voxel value `a` in `M` replaced
  by `M[a]`, each replacement read from the original data, on the same affine
  and header. This is item 192's helper.
- **`T13_MAP`** is `relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})`: T13,
  L1, L2, L3, L4 head-to-tail.
- **`COCC_MAP`** is `relabel({20: 23, 21: 24, 22: 26, 23: 29, 24: 27})`: L4, L5,
  S1, S2, `Cocc` head-to-tail.
- **`rec(X)`** is `segfacet.pipeline.extract_feature_record(X, cfg)`.
- **`mis(X)`** is
  `{(f.detector_id, f.labels) for f in segfacet.heuristics.run_rules(rec(X), cfg) if f.rule_id == "mislabel"}`.

- [ ] **AC1: a correctly placed T13 fires no `ordering` finding.**
  `mis(T13_MAP) == set()`.
- [ ] **AC2: a correctly placed coccyx fires no `ordering` finding.**
  `mis(COCC_MAP) == set()`.
- [ ] **AC3: `relabel_swap` still fires.** The findings of
  `segfacet.synth.regression.pipeline_findings(<the relabel_swap case>, cfg)`
  with `rule_id == "mislabel"`, reduced to `(detector_id, labels)`, are
  `{("ordering", frozenset({21, 22}))}`.
- [ ] **AC4: the record reports the two controls as monotonic.**
  `[rec(m)["stage3"]["monotonic_consistency"]["non_monotonic_pairs"] for m in (T13_MAP, COCC_MAP)] == [[], []]`.

Why each is written:

- AC1 and AC2 are the queue's "both relabelled controls fire no `ordering`
  finding". Today AC1's map fires three findings and AC2's one.
- AC3 is the queue's "`relabel_swap` still fires". A fix that silences the
  detector passes AC1 and AC2, and fails here.
- AC4 pins where the fix lives. The features block is written into every JSON
  report. A rule-side filter would pass AC1 and AC2 while that block still
  reports false ordering breaks.
- The queue's "every corpus case's expected set is re-measured, and the
  specificity ratchet is green" is not restated. Step 3 re-authors
  `sequence_break`'s expected set, and `tests/test_163_specificity_ratchet.py`
  fails unless each authored set equals its measured firing.

None of these closes a Stage 33 acceptance criterion. This is a maintenance
item.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on 2026-09-29 with `.venv/bin/python`, with
Implementation Step 1 prototyped in-process. The prototype replaced
`segfacet.features.consistency.compute_monotonic_consistency` with a wrapper
that reorders and refits, which the pipeline's deferred import picks up. It
also added step 2's two consumed paths and step 3's expected set, both by
`dataclasses.replace`. The working checkout was not edited, so the editable
install's shadowing (`CLAUDE.md`, Gotchas) does not apply. The builder
re-measures each value on the real change.

- **A1 (defensible default: the feature, not the rule).** The queue leaves
  the choice to this spec.
  - The rule cannot re-judge the order. `u_values[]` carries no labels, and
    `non_monotonic_pairs[]` holds only integer-adjacent pairs. A rule-side
    fix would have to re-implement item 132's traversal logic inside a rule.
    It would also leave the report's `stage3.monotonic_consistency` claiming
    breaks that are not there (AC4).
  - So the pipeline changes the order it hands `compute_monotonic_consistency`.
    `segfacet.features.consistency` is unchanged. Its contract already says
    the supplied order is the "anatomical order" under test.
  - The spline fit and every other Stage 3 extractor keep the
    ascending-integer sequence. Reordering that sequence would move the fit
    and every Stage 3 feature, which is why item 192 left this open.
- **A2 (defensible default: the order judged).**
  - Sort key: `(CANONICAL_ORDER index of level_name, label)`. A name not in
    `CANONICAL_ORDER` (only possible under a custom convention, as
    `"unknown"`) sorts after every canonical name, then by ascending label. A
    map of only unknown names therefore keeps ascending-integer order.
  - Item 186's `expected_level_sequence` is a subsequence of `CANONICAL_ORDER`,
    so the key orders every level the expected sequence contains exactly as
    that sequence does. `Cocc`, which the expected sequence omits, is last.
  - S1–S6 keep their `CANONICAL_ORDER` order. They are not collapsed onto one
    rank as item 192's A5 does for `sequence`. The monotonic walk needs a total
    order over the labels present, and an S2 above an S1 is judged as a break
    (Left open).
  - The key built from `CANONICAL_ORDER` is the public tuple.
    `segfacet.labels._order_key` / `_CANONICAL_RANK` are private and are not
    imported.
- **A3 (what moves in the record).**
  - Only `stage3.monotonic_consistency` changes: `is_monotonic`,
    `non_monotonic_pairs[]` and `u_values[]`. `u_values[]` is now listed in
    the anatomical order.
  - It changes only when the anatomical order differs from ascending integer
    order: a T13 (28) with any label 20–27 present, or a `Cocc` (27) with any
    of S2–S6 (29–33) present. Every other map gets the same label sequence
    and the same fit, so its record is unchanged.
  - Unchanged: `stage3.spline_offsets`, `orientations`, `tangent_orientations`,
    `curvature`, `spacing_consistency`, `per_label_neighbourhood`, and
    `relationships`.
- **A4 (defensible default: the fit handed over).**
  `compute_monotonic_consistency(centroids, fit)` reuses `fit` as its
  reference curve when the supplied order is already the traversal order.
  That is correct only if `fit` was fitted in the supplied order.
  - When the anatomical order equals ascending integer order, the pipeline
    passes the in-sample `fit` unchanged, with no extra fit (item 130's one
    fit).
  - Otherwise it passes
    `fit_centroid_spline(<anatomical>, degree=fit.degree, smoothing=fit.smoothing)`,
    the same inheritance `consistency.py` already uses for its own refit.
  - Without this, `T13_MAP` would reuse a curve fitted through L1–L4 then T13,
    which doubles back.
- **A5 (measured: what moves on the corpus).**
  - Geometric corpus, plain pipeline: only `sequence_break` changes. It gains,
    in report order before its unchanged `sequence` `shift` finding on [28]:
    - `mislabel`, `ordering`, `flagged-for-review`, labels [20, 21],
      `"Vertebra ordering inconsistent with label: labels 20 (L1) and 21 (L2) are out of expected order along the spine (spline parameter does not advance)."`
    - the same on [21, 22],
      `"... labels 21 (L2) and 22 (L3) are out of expected order ..."`
    - the same on [22, 23],
      `"... labels 22 (L3) and 23 (L4) are out of expected order ..."`
    - (the elided middles are the first reason's text verbatim.)
    - Its verdict stays `flagged-for-review`.
  - `sequence_break`'s `stage3.monotonic_consistency` becomes
    `is_monotonic` `False`, `non_monotonic_pairs` `[["L1", "L2"], ["L2", "L3"], ["L3", "L4"]]`,
    `u_values` `[5.611895432316293e-07, 0.9999994401419617, 0.754943198372328, 0.5169111036217682, 0.26901327963669636]`
    (T13, L1, L2, L3, L4).
  - Every other case, and every intensity case, fires exactly as before:
    `relabel_swap` keeps `mislabel` `ordering` on (21, 22) beside `sequence`
    `swap`.
  - The in-memory `SequenceBreakPerturbation().apply(build_clean_spine().seg_img, seed=0)`
    that `tests/test_039_identity_ordering_alignment_perturbations.py` uses
    fires the same four `(rule_id, labels)` pairs.
  - `segfacet.eval.severity_ladder.run_severity_harness()` is identical
    (serialised and compared).
  - `docs/aide/golden_evidence.generated.json` regenerates byte-identical.
  - `tests/corpus/manifest.json` does not move. `sequence_break`'s
    `expected_rule_ids` `["sequence"]` stays a subset of what fires, which is
    how `failure_modes._corpus_case_conflicts` compares the geometric manifest.
  - `tests.synthetic.labelled_blocks_case()` and `anisotropic_case()` fire only
    `bounds`, as before.
- **A6 (measured: `mislabel`'s declaration).**
  - `catalogue.build_catalogue()` observes `mislabel` reading
    `per_label.{label}.label` and `per_label.{label}.level_name`. The reads
    come from `_label_for_level`, now that the catalogue's `sequence_break`
    record carries pairs. Without a declaration,
    `path_classification_conflicts()` reports both.
  - Declaring both as `bookkeeping` makes `path_classification_conflicts()`
    and `rule_declaration_conflicts()` both `()`.
  - Regenerated against the committed artifacts, with steps 1–3 applied:
    - catalogue: those two entries gain `mislabel` in `consuming_rules`, a
      `("mislabel", "bookkeeping")` role and `("mislabel", "observed")`
      evidence. No `mode_evidence`, `failure_modes` or observed range moves.
    - matrix: `exercise.rules.mislabel.exercised_by` gains
      `["geometric", "sequence_break"]`; `features.by_rule.mislabel` goes
      2 → 4; `mislabel`'s `feature_path_count` goes 2 → 4 and its path list
      gains the two paths.
    - matrix, unchanged: conformance stays 17 agreeing, 0 disagreeing.
      `features.read_by_rule` and `read_by_no_rule` are unchanged, because
      `sequence` already read both paths. Mode 9 stays `validated`.
    - specification rendering: mode 9's `sequence_break` case gains
      `mislabel` in `expected_firing`.
  - No derived status or rung count moves. No `progress.md` amendment is due.
- **A7 (defensible default: the specification).**
  - `sequence_break`'s `expected_firing` becomes `("mislabel", "sequence")`.
    Its `reason` is rewritten to the measured firing of A5. It must stay
    non-empty and must not contain `rank(v) == v - 1`
    (`tests/test_145_eight_hypothesised_modes.py` AC10b).
  - Mode 9's `mechanism` gains one sentence (step 3). It keeps every token
    it has now. It names no path that no mode-9 rule reads
    (`tests/test_138_traceability_matrix.py` AC31).
  - No edge, rung, status or detector id changes.
- **A8 (measured, out of scope: the traversal direction names the wrong
  pairs).** In `sequence_break` the misplaced T13 is first in the anatomical
  order.
  - Item 132's `_traversal_order` takes its direction from the supplied
    sequence's first-to-last net advance. So it walks the curve upward, and
    the four lumbar levels read as descending. T13, the level that is actually
    misplaced, is never named.
  - A direction chosen by fewer inversions, as item 192's A4 correction does
    for `sequence`, would name (T13, L1), labels {20, 28}. That changes item
    132's convention and every map with a misplaced endpoint, so it is not
    done here (Left open, and one `insights.md` line).
- **A9:** no human gate, and no environment-gated capability.

## Implementation Steps

1. **`src/segfacet/pipeline.py`**, in `extract_feature_record`'s Stage 3 branch.
   - Import `CANONICAL_ORDER` from `segfacet.labels` inside the function
     (house style: deferred imports).
   - Build `anatomical_centroids`: `ordered_centroids` stably sorted by A2's key.
   - Choose the fit per A4. Compare the two orders by their label sequences,
     not by `LabelCentroid` equality. Use the already-imported
     `fit_centroid_spline`.
   - Pass `compute_monotonic_consistency(anatomical_centroids, <that fit>)`.
     Every other Stage 3 call keeps `ordered_centroids` and `fit`.
   - Extend the existing "Ascending-label order is the single consistent
     ordered centroid sequence" comment. Monotonic consistency is the one
     exception, and the comment says why: TPTBox integers are not anatomical
     order, and the item-198 date and A4's fit rule go with it.
2. **`src/segfacet/heuristics/mislabel.py`.**
   - Add two `ConsumedPath` entries, role `bookkeeping`, between `per_label`
     and the signal path so the tuple stays ascending:
     - `per_label.{label}.label`, reason: it is the integer id a resolved pair
       reports in `labels`;
     - `per_label.{label}.level_name`, reason: it is matched against a
       pair's level names by `_label_for_level`.
   - `per_label` stays `consumed_paths[0]`: `tests/test_148_per_path_mode_attribution.py`
     drops `consumed_paths[0]` as its adversarial probe.
   - Add a dated item-198 paragraph to the module docstring: the pairs are
     judged in `CANONICAL_ORDER` order, so a correctly placed T13 or `Cocc`
     no longer reads as out of order.
   - Nothing inside `evaluate` names `mode_declaration`, `consumed_paths` or
     `ConsumedPath` (`test_148`'s banned-name check). `evaluate`'s logic is not
     changed.
3. **`src/segfacet/failure_modes.py`** (A7).
   - `_MODE_9`'s `sequence_break` `CorpusCaseExpectation`:
     `expected_firing=("mislabel", "sequence")`, and a `reason` stating A5's
     measured firing, dated 2026-09-29, item 198.
   - `_MODE_9.mechanism`: after the sentence ending "(relabel_swap exchanges
     L2 and L3).", add one saying that since item 198 the pairs are judged
     in CANONICAL_ORDER order, so a correctly placed T13 or Cocc no longer
     fires, and that sequence_break fires ordering beside shift.
4. **`src/segfacet/feature_docs.py`**, two `FeatureDoc`s only.
   - `stage3.monotonic_consistency.non_monotonic_pairs[]`'s `computation`
     says the consecutive pairs are taken in `CANONICAL_ORDER` order (item
     198).
   - `stage3.monotonic_consistency.u_values[]`'s `measures` says "in
     `CANONICAL_ORDER` order" instead of "in input order".
   - No anchor or `MODE_ANCHOR_PATHS` entry changes.
5. **Regenerate** each module's `main` twice into temp paths, byte-compare the
   two runs, then write the committed copy:
   - `segfacet.failure_modes` → `docs/aide/failure_modes.generated.{json,md}`;
   - `segfacet.traceability` → `docs/aide/traceability_matrix.generated.{json,md}`;
   - `segfacet.catalogue` → `docs/aide/feature_catalogue.generated.{json,md}`;
   - `segfacet.golden_evidence`, into temp only. It must equal the committed
     file (A5). If it does not, hand back.
6. **Reconcile** the tests listed under Testing Strategy, each edit with a
   dated item-198 comment.
7. Run `python .aide/scripts/aide.py scope 198` and
   `python .aide/scripts/aide.py check`. Both must report no error.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/pipeline.py` — monotonic consistency judged in anatomical order (step 1).
- `src/segfacet/heuristics/mislabel.py` — two bookkeeping paths and a docstring paragraph (step 2).
- `src/segfacet/failure_modes.py` — `sequence_break`'s expected set and reason, one mode-9 mechanism sentence (step 3).
- `src/segfacet/feature_docs.py` — two `FeatureDoc` texts (step 4).
- `docs/aide/failure_modes.generated.json` — regenerated (step 5).
- `docs/aide/failure_modes.generated.md` — regenerated.
- `docs/aide/traceability_matrix.generated.json` — regenerated.
- `docs/aide/traceability_matrix.generated.md` — regenerated.
- `docs/aide/feature_catalogue.generated.json` — regenerated.
- `docs/aide/feature_catalogue.generated.md` — regenerated.
- `tests/test_198_ordering_along_expected_sequence.py` — **new**: this item's test module.
- `tests/test_039_identity_ordering_alignment_perturbations.py` — AC17's firing set (Testing Strategy).
- `tests/test_098_stray_components.py` — `sequence_break`'s entry of `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`.
- `tests/test_116_ras_native_corpus.py` — item 198's added pairs stripped in AC7.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `_PRE_129_FINDINGS["sequence_break"]`.
- `tests/test_132_monotonicity_against_traversal_order.py` — `_PRE_ITEM_U_VALUES["sequence_break"]`.

**The reconciliation fence.** Every edit to an existing test is a moved
literal: a firing set, a finding list, a u-value row, or a stripped-pair
table. Each carries a dated item-198 comment. No test is retired, skipped,
`xfail`-marked or loosened. **A red test in a file not listed here is a
hand-back to spec-author.**

**Asserts against:**

- `src/segfacet/features/consistency.py` — `compute_monotonic_consistency` reused unchanged (A1).
- `src/segfacet/labels.py` — `CANONICAL_ORDER` read, unchanged (A2).
- `tests/corpus/manifest.json` — must not move (A5).
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC1, AC2 and AC4 relabel it.
- `tests/corpus/fixtures/relabel_swap_seg.nii.gz` — AC3 reads it.
- `tests/corpus/fixtures/sequence_break_seg.nii.gz` — the reconciled literals read it.
- `docs/aide/golden_evidence.generated.json` — must not move (A5).
- `tests/test_163_specificity_ratchet.py` — red unless step 3 re-authors `sequence_break`.
- `tests/test_148_per_path_mode_attribution.py` — AC4's declared-equals-consumed check is red unless step 2 declares both paths. AC16's row is a containment check and holds.

## Testing Strategy

The test module is `tests/test_198_ordering_along_expected_sequence.py`, one
test per AC. `relabel` is a module helper built as item 192's is: NumPy on
`loaded_seg_image`'s data, `nibabel.Nifti1Image(data, img.affine, img.header)`,
each replacement read from the original array. Every value below was measured
by the prototype of Assumptions (2026-09-29).

Named adversarial cases, and no others:

- **t13-below-l1-still-fires:** `mis(relabel({21: 28, 22: 21, 23: 22, 24: 23})) == {("ordering", frozenset({20, 28}))}`
  (L1, T13, L2, L3, L4 head-to-tail). It guards a fix that drops every pair
  naming T13 instead of re-ordering: a T13 below L1 is a real break.
- **cocc-above-s2-still-fires:** `mis(relabel({20: 23, 21: 24, 22: 26, 23: 27, 24: 29})) == {("ordering", frozenset({27, 29}))}`
  (L4, L5, S1, `Cocc`, S2 head-to-tail). It guards the same shortcut for the
  coccyx.

**Existing tests to reconcile** (measured on the prototype, 2026-09-29):

- **`tests/test_039_identity_ordering_alignment_perturbations.py`**
  `test_ac17_sequence_break_only_fired_rule_is_sequence_no_coverage`
  (line 494). The loop asserting `f.rule_id == "sequence"` for every finding
  becomes `{f.rule_id for f in findings} == {"mislabel", "sequence"}`. The
  `assert findings` and no-`coverage` assertions stay, and the docstring says
  why `mislabel` fires. AC16, AC18 and
  `test_adv_sequence_break_interior_target_still_fires_sequence_with_coverage_cofire`
  hold unedited: they use `any(...)` or the verdict.
- **`tests/test_098_stray_components.py`** `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["sequence_break"]`
  (line 999). Insert before the `sequence` finding, in this order, the three
  dicts of A5, each with keys `rule_id` `"mislabel"`, `detector_id`
  `"ordering"`, `severity` `"flagged-for-review"`, `labels` `[20, 21]` /
  `[21, 22]` / `[22, 23]`, and `reason` the exact string. Verdict stays
  `flagged-for-review`. The importers read the reconciled constant unedited:
  `test_089`, `test_090`, `test_094`, `test_102`, `test_108`, `test_123`,
  `test_132` and `test_143`. A red one among them is a hand-back.
- **`tests/test_116_ras_native_corpus.py`**
  `test_ac7_case_identity_preserved_vs_merge_base` (line 416). It runs here,
  because commit `aeb2f55` is present.
  - Beside `_ITEM_192_ADDED_SEQUENCE_PAIRS`, add
    `_ITEM_198_ADDED_MISLABEL_PAIRS = {"sequence_break": (("mislabel", (20, 21)), ("mislabel", (21, 22)), ("mislabel", (22, 23)))}`.
  - For that case, assert each pair is in `fresh_pairs`, then strip it, as the
    item-192 pairs are handled.
  - Correct the comment saying `sequence_break` "needs no stripping".
- **`tests/test_129_coincident_centroids_and_held_out_floor.py`**
  `_PRE_129_FINDINGS["sequence_break"]` (line 733) becomes
  `{("mislabel", (20, 21)), ("mislabel", (21, 22)), ("mislabel", (22, 23)), ("sequence", (28,))}`.
  `tests/test_131_tangent_direction_normalisation.py` calls the reconciled
  check unedited.
- **`tests/test_132_monotonicity_against_traversal_order.py`**
  `_PRE_ITEM_U_VALUES["sequence_break"]` (line 198) becomes
  `[0.000000561, 0.999999440, 0.754943198, 0.516911104, 0.269013280]`
  (A5, in T13, L1–L4 order; the table's `abs=1e-9` tolerance holds).

**Checked and unaffected** (read on 2026-09-29):

- `tests/test_041_regression_suite.py` AC9–AC11 and `tests/test_171_literal_negative_controls.py`
  derive from the live firing set, and `sequence_break`'s designated rule
  stays `sequence`.
- `tests/test_145_eight_hypothesised_modes.py` asserts only
  `"sequence" in measured(case)` and AC10b's reason and mechanism tokens.
- `tests/test_135_stage29_validation.py` and `tests/test_125_stage28_validation.py`
  pin `relabel_swap` and `clean_control`'s pairs, which do not move.
- `tests/test_036_clean_gt.py` AC11 calls `compute_monotonic_consistency`
  directly.
- `tests/test_192_sequence_sub_types.py` reads only `sequence` findings.
- `tests/test_131_tangent_direction_normalisation.py` and
  `tests/test_143_s_axis_correction.py` pin `sequence_break`'s curvature and
  offsets, which do not move (A3).

## Validation

Replay `sequence_break` through the CLI, without a reference, for the reason
`CLAUDE.md` gives:

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/sequence_break_seg.nii.gz --out <tmp> --no-reference
```

- `<tmp>/segfacet_report.json` holds the four findings of A5, verdict
  `flagged-for-review`.
- Its `features.stage3.monotonic_consistency` equals A5's values.

No environment profile is needed.

## Dependencies

None. `CANONICAL_ORDER` predates this queue, and the items this spec reads
from (186, 192) are merged. It pins no interface of an unbuilt item.

**Downstream:** items 201 (severity-ladder constants re-measured) and 202
(`docs/aide/rules.generated.md`) read `mislabel`'s declaration and the corpus
firing this item changes. A5 measured the ladders unchanged.

## Decisions & Trade-offs

- **Implemented as specified (2026-09-29).** `pipeline.py` sorts the
  centroids by `(CANONICAL_ORDER index, label)` and refits (inheriting degree
  and smoothing) only when that differs from ascending-integer order;
  `compute_monotonic_consistency` is untouched. Re-measured on the real
  change: `sequence_break`'s `monotonic_consistency` equals A5's values, and
  `golden_evidence.generated.json` regenerates byte-identical. The test
  reconciliations of step 6 were already present on the branch from the
  test-writer, so this step made no test edit.

- **Left open:** the traversal direction names the wrong pairs when an
  endpoint of the judged order is misplaced (A8). `sequence_break`'s
  `mislabel` findings name L1–L4 rather than T13. Fixing it changes item
  132's direction convention in `segfacet.features.consistency`, which reaches
  every map with a misplaced endpoint, not only the TPTBox integer quirk this
  item removes.
- **Left open:** whether S1–S6 share one rank in the monotonic walk, as item
  192 decided for `sequence` (A2). No corpus case has two sacral labels, so
  nothing measures the difference yet.
