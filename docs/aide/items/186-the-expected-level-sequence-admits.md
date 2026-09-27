<!-- aide-template: item 2 -->
# Item 186 — The expected level sequence admits per-section vertebra counts

> **Created:** 2026-09-27 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 186
> **Objectives:** G2
> **Suggested branch:** `aide/186-the-expected-level-sequence-admits`

---

## Description

This item implements roadmap Stage 33 D3's bullet "the expected level sequence
admits per-section vertebra counts". It fixes the `defect` entry in
`docs/aide/insights.md` dated 2026-09-22 (queue-022 review), and follows the
maintainer feedback of 2026-09-25 recorded in `queue-025.md`.

**The defect.** `segfacet.features.relationships.compute_spine_relationships`
computes `missing_levels` as every entry of `segfacet.labels.CANONICAL_ORDER`
between the first and last present level that is not present. `CANONICAL_ORDER`
places the transitional T13 between T12 and L1, L6 between L5 and S1, and lists
the sacrum as six levels S1–S6. So a label map holding T12 and L1 reports T13
missing, and `coverage`'s always-on `missing_interior` detector fires on it.
That map is the common thoraco-lumbar case. The committed corpus case
`split_own_label` (labels T12, L1–L5) fires `coverage` for exactly this
reason.

**The fix: `missing_levels` walks an expected sequence built from section
counts.**

- **Sections.** Cervical has 7 vertebrae. Thoracic has 11, 12 or 13. Lumbar has
  4, 5 or 6. Any combination is valid, and the default is (7, 12, 5).
- **The expected sequence** for counts (c, t, l) is C1–C7, T1–T*t*, L1–L*l*,
  then one sacral element, in that head-to-tail order. The sacrum is not split
  into levels, so any present label S1–S6 stands for it. The coccyx is not in
  the sequence (A3).
- **A non-default count is read from the labels and accepted only when the scan
  shows the whole section, plus the first vertebra on either side of it.**
  - A thoracic reading exists when L1 is present. It is the highest thoracic
    index present. A reading of 11 or 13 is accepted only when C7 is present.
  - A lumbar reading exists when a sacral label is present. It is the highest
    lumbar index present. A reading of 4 or 6 is accepted only when the last
    thoracic level, T*t* for the thoracic count in effect, is present.
  - A reading that is not accepted leaves that section at its default. It is
    returned as *unaccepted* for item 192's transitional sub-type to report.
- **A supplied count** replaces that section's reading, with no field-of-view
  requirement. It enters as a keyword argument of
  `compute_spine_relationships`.

**What this item changes.** `segfacet/labels.py` gains the section model and
two pure functions (A1). `compute_spine_relationships` walks the resolved
sequence for `missing_levels`. `split_own_label`'s expected set in
`segfacet/failure_modes.py` loses `coverage`. The feature catalogue's
description of `missing_levels` is corrected. Three pairs of generated documents
are regenerated.

**Not in scope.**

- `CANONICAL_ORDER` is unchanged. It stays the ranking every sort and the
  `is_continuous` check use (A4).
- No rule changes. `coverage.py`, `fov.py` and `sequence.py` are not edited.
  `coverage` still reads `relationships.missing_levels`, and it is re-homed by
  item 188.
- No change to `present_levels`, `is_continuous`, `out_of_order_labels` or
  `neighbour_spacings_mm`, and no new field in the serialised record or report
  schema (A2).
- No pipeline, CLI or config channel for supplied counts (Decisions, Left open).
- No corpus fixture or manifest change. `split_own_label`'s manifest entry
  already designates only `bounds`.

## Acceptance Criteria

Terms used below:

- **"The T12 map"** is a label map built with `tests.synthetic.make_labelmap`
  holding six separated, non-touching blocks labelled 19–24 (T12, L1–L5 under
  `LabelConvention.default()`) and no label 28 (T13).
- **"Relationships of levels X"** means
  `compute_spine_relationships(centroids)` where `centroids` holds one
  `LabelCentroid` per named level, with distinct `centroid_mm` coordinates,
  given in head-to-tail order. `section_counts=` is passed only where the
  criterion says so.
- **"Resolved counts of levels X"** means
  `segfacet.labels.resolve_section_counts(X)`, with `supplied=` only where the
  criterion says so.

- [ ] **AC1: the T12 map reports no missing level.**
  `extract_feature_record(t12_map, bundled_default_config())["relationships"]["missing_levels"] == []`.
- [ ] **AC2: the T12 map produces no missing-level finding.** For that record,
  `run_rules(record, bundled_default_config())` returns no finding with
  `rule_id == "coverage"`. *(closes Stage 33 criterion 4)*
- [ ] **AC3: a skipped L3 is still reported.** Relationships of levels T12, L1,
  L2, L4, L5 give `missing_levels == ["L3"]`.
- [ ] **AC4: an 11-level thoracic reading is accepted with C7 in view.**
  Relationships of levels C7, T1–T11, L1 give `missing_levels == []`.
- [ ] **AC5: the 11-level reading is refused without C7.** Relationships of
  levels T1–T11, L1 give `missing_levels == ["T12"]`.
- [ ] **AC6: the refused reading is returned as unaccepted.** Resolved counts of
  levels T1–T11, L1 have `unaccepted == {"thoracic": 11}`.
- [ ] **AC7: a supplied 13-level thoracic count makes an absent T13 missing.**
  Relationships of levels T12, L1–L5 with `section_counts={"thoracic": 13}` give
  `missing_levels == ["T13"]`.
- [ ] **AC8: a supplied count needs no field-of-view evidence.** Relationships
  of levels T1–T11, L1 with `section_counts={"thoracic": 11}` give
  `missing_levels == []`.
- [ ] **AC9: a 4-level lumbar reading is accepted with the last thoracic level
  in view.** Relationships of levels T12, L1–L4, S1 give `missing_levels == []`.
- [ ] **AC10: the 4-level lumbar reading is refused without it.** Relationships
  of levels L1–L4, S1 give `missing_levels == ["L5"]`.
- [ ] **AC11: a 6-level lumbar reading is accepted.** Relationships of levels
  T12, L1–L6, S1 give `missing_levels == []`.
- [ ] **AC12: a mixed combination resolves from the labels.** Resolved counts of
  levels C7, T1–T13, L1–L4, S1 have `counts == (7, 13, 4)`.
- [ ] **AC13: the expected sequence for every valid combination.** For every
  `t` in 11–13 and `l` in 4–6,
  `expected_level_sequence(SectionCounts(7, t, l))` equals
  `("C1", …, "C7", "T1", …, f"T{t}", "L1", …, f"L{l}", SACRUM)`, built in the
  test from `t` and `l`.
- [ ] **AC14: the sacrum is not split into levels.** Relationships of levels L5,
  S1, S3 give `missing_levels == []`.
- [ ] **AC15: an out-of-range supplied count is refused.** For each of
  `{"thoracic": 10}`, `{"thoracic": 14}`, `{"lumbar": 3}`, `{"lumbar": 7}` and
  `{"cervical": 6}`, `compute_spine_relationships(centroids, section_counts=…)`
  raises `FacetInputError`.
- [ ] **AC16: `split_own_label` no longer fires `coverage`.** For `c`, the
  `split_own_label` entry of `failure_modes.SPECIFICATION[3].corpus_cases`,
  `set(failure_modes.measured_firing(c)) == {"bounds"}`.

Why each is written: AC1–AC5, AC7–AC11 and AC14 are the queue line's
*Testable* sentence and the section rules, one case each. AC6 and AC12 pin
`resolve_section_counts`, which item 192 reads (A1). AC13 is the sequence
item 192 checks order against. AC15 guards the one input this item adds.
AC16 is the queue's stated consequence for the corpus. That `split_own_label`'s
authored expected set equals its measured firing is the existing specificity
ratchet's job (`tests/test_163_specificity_ratchet.py`), so it is not
restated here.

## Assumptions

- **A1 (the interface item 192 reads).** In `segfacet.labels`, added to
  `__all__`:
  - `SectionCounts(NamedTuple)` with fields `cervical`, `thoracic`, `lumbar`,
    in that order, so it compares equal to a plain `(7, 13, 4)`.
  - `DEFAULT_SECTION_COUNTS = SectionCounts(7, 12, 5)`.
  - `SECTION_COUNT_RANGES = {"cervical": (7, 7), "thoracic": (11, 13), "lumbar": (4, 6)}`,
    inclusive bounds.
  - `SACRUM = "S"`, the one sacral element of the sequence.
  - `expected_level_sequence(counts=DEFAULT_SECTION_COUNTS) -> Tuple[str, ...]`.
    It raises `FacetInputError` for a count outside its range.
  - `resolve_section_counts(present_levels, supplied=None) -> ResolvedSectionCounts`,
    a `NamedTuple` of `counts: SectionCounts` and `unaccepted: Dict[str, int]`.
    `present_levels` is any iterable of level names. `supplied` is a partial
    mapping keyed by section name. An unknown key, or a value outside its range,
    raises `FacetInputError`. A supplied section never appears in
    `unaccepted`.

  Item 192 is the consumer. It checks label order against
  `expected_level_sequence(resolve_section_counts(...).counts)` and reports
  `unaccepted` as its transitional sub-type. How item 192 learns a supplied
  count is its own decision (Left open below).
- **A2 (defensible default: nothing new is serialised).** The resolved counts
  and the unaccepted readings are not added to the `relationships` block. Doing
  so would move `report_schema_v0.json`, the feature catalogue and
  `tests/golden/report_format_contract.json`, and no consumer in this queue
  reads them from the record. Item 192 can resolve them from
  `relationships.present_levels[]` through A1's function.
- **A3 (defensible default: the coccyx is outside the expected sequence).** The
  queue line gives the sequence as C1–C7, T1–T*n*, L1–L*m*, S. `Cocc` is
  therefore neither walked nor counted toward the span, and it is never reported
  missing. The sacral element is the sequence's last entry, so it is never
  interior and never reported missing either. Every name `missing_levels` can
  hold is a `CANONICAL_ORDER` name, which `coverage`'s canonical sort and
  `human_report.py` already rank.
- **A4 (defensible default: "the order must be monotonic" is the sequence's
  order, not a new check here).** The expected sequence is built head-to-tail,
  section by section, which AC13 pins. Whether the *present* labels follow it is
  `sequence`'s question, which item 192 re-bases on this sequence. So
  `is_continuous` and `out_of_order_labels` are unchanged, and so is the
  `CANONICAL_ORDER` ranking they use. The item 147/145/138 tests that require
  the tokens `CANONICAL_ORDER` and `T13` in mode 9's mechanism stay satisfied.
- **A5 (defensible default: "in the field of view" means "labelled").** The
  relationships extractor sees centroids only, with no image geometry. A level
  that carries a label is in the field of view. So C7 and L1 both present means
  every thoracic level lies inside the scan. A partly truncated C7 still has T1
  below it. No border flag is read.
- **A6 (defensible default: how a reading is taken).** A section's reading is
  the highest index present in it, taken only when the section's caudal
  neighbour (L1 for thoracic, a sacral label for lumbar) is present. So the
  labels show where the section ends. A reading outside the section's range
  (T10 highest with L1 present, say) is no reading. The section keeps its
  default, and its absent levels are reported missing. The thoracic count is
  resolved first, because the lumbar acceptance test names T*t*.
- **A7 (measured on this branch, 2026-09-27, with a scratch probe of A1 and A6
  over both committed corpora).** Only `split_own_label` changes. Its present
  levels are T12, L1–L5. `missing_levels` goes from `["T13"]` to `[]`, so its
  measured firing goes from `("bounds", "coverage")` to `("bounds",)`.
  `sequence_break` (T13, L1–L4) keeps `[]`. Its thoracic reading of 13 is
  unaccepted, because C7 is absent. `remove_level` keeps `["L3"]`, and every
  other geometric and intensity case keeps `[]`. The builder re-measures each of
  these.
- **A8 (predicted, re-measured by the builder).**
  - `docs/aide/golden_evidence.generated.json` regenerates byte-identical, since
    every case's leaf-path counts are 96/26, `remove_level`'s included.
  - The feature catalogue's `failure_modes` for `relationships.*` paths are
    unchanged. `coverage` maps to `(6,)` there, and `split_own_label`'s
    co-detection never entered that map. Only the `missing_levels` entry's
    `measures` and `computation` text moves.
  - `tests/corpus/manifest.json` and every fixture are untouched.
- **A9: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/labels.py`**: add A1's names after `CANONICAL_ORDER`, with a
   module-docstring paragraph that credits item 186. Generate the sequence from
   the counts (`f"T{i}"` for `i` in `1..t`). A level name maps to a sequence
   element by identity, except `S1`–`S6`, which map to `SACRUM`. Validation
   raises the module's existing `FacetInputError`. No dependency is added.
2. **`src/segfacet/features/relationships.py`**:
   - `compute_spine_relationships(centroids, convention=None, *, section_counts=None)`.
   - Replace the `CANONICAL_ORDER[lo : hi + 1]` walk with:
     1. resolve the counts with `resolve_section_counts(present_levels, section_counts)`;
     2. build `expected_level_sequence(resolved.counts)`;
     3. map each present level to its sequence element and drop those not in the
        sequence;
     4. report the unpresent elements between the first and last present element,
        in sequence order, when at least two distinct elements are present.
   - `present_levels`, the spacings and the continuity walk keep using
     `CANONICAL_ORDER`, unchanged.
   - Update the module and dataclass docstrings: `missing_levels` is the
     expected-sequence gap, with item 186 credited.
3. **`src/segfacet/feature_docs.py`**: rewrite the
   `relationships.missing_levels[]` `FeatureDoc`. Its `measures` becomes
   expected-sequence levels absent within the present span. Its `computation`
   states the section counts, the default, when a non-default count is accepted,
   and that the sacrum is one element.
4. **`src/segfacet/failure_modes.py`**: set mode 3's `split_own_label`
   `expected_firing` to `("bounds",)`. Rewrite its `reason`: drop the `coverage`
   sentence and say `coverage` no longer fires, since T12→L1 is continuous under
   the default thoracic count (item 186, measured live via
   `segfacet.synth.regression.pipeline_findings`). Keep the `bounds` and
   `neighbour_contact` sentences, re-measured. Edit no other field of any mode.
5. **Regenerate** with each module's `main`, twice into temp directories, and
   byte-compare the two runs before writing:
   - `python -m segfacet.failure_modes` writes `docs/aide/failure_modes.generated.json`
     and `.md` (the reason text);
   - `python -m segfacet.traceability` writes `docs/aide/traceability_matrix.generated.json`
     and `.md` (the case row, and `coverage`'s `exercised_by` losing
     `geometric/split_own_label`);
   - `python -m segfacet.catalogue` writes `docs/aide/feature_catalogue.generated.json`
     and `.md`. The diff must be the `missing_levels` entry's text only (A8).
   - `python -m segfacet.golden_evidence`, into temp only. It must equal the
     committed file byte for byte (A8). If it does not, hand back.
6. **Reconcile** `tests/test_174_split_sub_types.py::test_ac8_split_own_label_fires_bounds_and_coverage`.
   The expected set becomes `{"bounds"}`, with a dated item-186 comment. The
   name is kept (items 173–176 precedent), and its section banner states the new
   set.
7. Run `python .aide/scripts/aide.py scope 186` and confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/labels.py` — the section model, `expected_level_sequence`, `resolve_section_counts` (step 1).
- `src/segfacet/features/relationships.py` — the expected-sequence walk and the `section_counts` keyword (step 2).
- `src/segfacet/feature_docs.py` — the `missing_levels` `FeatureDoc` text (step 3).
- `src/segfacet/failure_modes.py` — `split_own_label`'s expected set and reason (step 4).
- `docs/aide/failure_modes.generated.json` — regenerated (step 5).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 5).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 5).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `tests/test_186_expected_level_sequence.py` — **new**: this item's test module.
- `tests/test_174_split_sub_types.py` — reconciliation of AC8 (step 6).

**The reconciliation fence.** Only `tests/test_174_split_sub_types.py`'s AC8
is reconciled, as a moved literal. It keeps its shape and gains a dated
item-186 comment. No test is retired, skipped, `xfail`-marked or loosened. A
red test in a file not listed here is a hand-back to spec-author, not an edit.

**Asserts against:**

- `src/segfacet/heuristics/coverage.py` — unchanged; AC2 runs it over the new `missing_levels`.
- `docs/aide/golden_evidence.generated.json` — predicted byte-identical (A8); `tests/test_134_*` recomputes it live.
- `tests/corpus/manifest.json` — `split_own_label`'s `expected_rule_ids` is already `["bounds"]`; AC16 resolves the case through it.

Some paths stay off **May change** on purpose, so `aide scope` refuses them:

- `src/segfacet/report_schema_v0.json` — nothing new is serialised (A2).
- `src/segfacet/feature_report.py` — the same.
- `tests/golden/report_format_contract.json` — the same.
- `src/segfacet/heuristics/fov.py` — its adjacency step is a later item's (Left open).
- `src/segfacet/heuristics/sequence.py` — item 192's.
- `src/segfacet/synth/clean_gt.py` — its span guard is left as is (Left open).

## Testing Strategy

The test module is `tests/test_186_expected_level_sequence.py`. There is one
test per AC. AC1 and AC2 share one module-scoped fixture that builds the T12
map and its record once. AC13 loops over the nine combinations inside its one
test. AC15 loops over its five inputs inside its one test.

Named adversarial cases, and no others:

- `thoracic-reading-out-of-range`: relationships of levels C7, T1–T10, L1 give
  `missing_levels == ["T11", "T12"]`. It guards an implementation that accepts
  any highest index as the count, which would make a real two-level gap vanish.
- `supplied-overrides-observed`: relationships of levels C7, T1–T11, L1 with
  `section_counts={"thoracic": 12}` give `missing_levels == ["T12"]`. It guards
  an accepted observation silently overriding prior knowledge.
- `supplied-unknown-section`: `section_counts={"sacral": 1}` raises
  `FacetInputError`. It guards a typo'd key being ignored, which would leave the
  default in force with no signal.
- `coccyx-outside-sequence`: relationships of levels L4, L5, Cocc give
  `missing_levels == []`. It guards a walk that still follows `CANONICAL_ORDER`'s
  tail and reports the sacrum missing between L5 and `Cocc` (A3).
- `unaccepted-transitional-t13`: resolved counts of levels T13, L1–L4 (the
  `sequence_break` shape, no C7) have `counts == (7, 12, 5)` and
  `unaccepted == {"thoracic": 13}`. It guards a present T13 being accepted with
  no field-of-view evidence. Item 192's transitional sub-type depends on that
  refusal.

**Existing tests to reconcile.** `tests/test_174_split_sub_types.py`'s AC8
pins `{"bounds", "coverage"}` (step 6). A grep of `tests_dir` for the old
behaviour found no other pin:

- `test_014`'s `test_ac2_cross_region_gap_detected` asserts `"L1" in` the
  missing list for T12, L2, and that still holds.
- `test_089` and `test_029` build their `relationships` blocks by hand.
- `test_036`'s transitional-crossing test pins `build_clean_spine`'s guard,
  which is unchanged.
- `test_097`'s L6/S1/S2 map reports no missing level before and after.

`tests/test_163_specificity_ratchet.py` must stay green, and it goes red if step
4 is skipped.

## Validation

Replay Stage 33 criterion 4 through the CLI on the committed T12 map:

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/split_own_label_seg.nii.gz --out <tmp> --no-reference
```

Pass `--no-reference` for the reason `CLAUDE.md` gives: the bundled VerSe
reference is not calibrated for the synthetic corpus. Inspect
`<tmp>/segfacet_report.json`:

- `features.relationships.present_levels` is T12, L1–L5;
- `features.relationships.missing_levels` is `[]`;
- no entry of `findings` has `rule_id == "coverage"`.

No environment profile is needed.

## Dependencies

None. Item 186 leads queue-025.

**Downstream:** item 192 checks `sequence` against this item's expected
sequence and reports its unaccepted readings (A1). Items 187 and 188 re-author
expected sets after this item has removed `split_own_label`'s `coverage`
firing.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** how a supplied section count reaches a case in production
  (an `extract_feature_record`/`run_qc` keyword, a CLI flag, or a per-case
  manifest field) and how item 192's rule learns it. No caller in this queue
  supplies counts, so this item stops at `compute_spine_relationships`'
  keyword.
- **Left open:** `coverage`'s opt-in `incomplete_span` check still resolves
  "the adjacent level" through `fov.py`'s `CANONICAL_ORDER` step. So beyond
  a non-truncated T12 it names T13, not L1. The check ships disabled, and
  `coverage` is re-homed by item 188.
- **Left open:** `synth/clean_gt.py` still refuses a T12→L1 span. Its docstring
  says that crossing "would (correctly) trip" `coverage`, and after this item
  that is no longer true. Nothing in this stage builds such a base.
