<!-- aide-template: item 3 -->
# Item 230 — A per-label, several-modes-per-case expectation in the evaluation harness

> **Created:** 2026-10-18 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 35 — Programme Interface: the SegFACET Side
> **Queue:** [`../queue/queue-031.md`](../queue/queue-031.md) · Item 230
> **Objectives:** G2, G7
> **Suggested branch:** `aide/230-a-per-label-several-modes`

---

## Description

This is the harness half of Stage 35's third deliverable, the real-label
expectation. Item 231 is the reader half.

Today the evaluation harness (`segfacet.eval.harness.evaluate_case`) scores a
case against one expectation mapping in the
`segfacet.synth.perturbation.Expectation.to_dict()` shape: one
`failure_mode`, a set of designated rule ids and a set of expected labels.
`segfacet.eval.outcome.classify_outcome` reduces it to one case-level
confusion cell. That fits scripted perturbation, which breaks one thing per
case. It does not fit `spine-failure-lab`'s review-label table (`rl1`,
`docs/project/facet-interface.md` at `7436b0f`). There, each row names a
`label_id` and a `mode_id`. A case has several rows at different modes, and
mode 0 marks a level that was reviewed and found clean.

This item adds that expectation and scores the harness against it:

- **The expectation.** An `EvaluationCase.expected` mapping may carry a
  `label_modes` key: a sequence of `[label, mode]` pairs. Mode 0 means the
  label was reviewed and found clean. The new helper
  `segfacet.eval.label_outcome.label_mode_expectation(pairs)` builds that
  mapping, including the `expected_verdict` that `classify_outcome` still
  requires. Item 231 builds its expectations through this helper.
- **Per-label scoring.** A failure pair `(label, m)` with `m != 0` counts as
  **detected** when a finding on that label comes from a detector that serves
  mode `m`. A detector serves the modes
  `segfacet.failure_modes.modes_for_detector(rule_id, detector_id)` returns.
  Any pair counts as **flagged** when any finding falls on its label. For a
  clean pair (mode 0), flagged is a false positive. `evaluate_case` attaches
  the per-pair outcomes to the record as `label_outcomes`.
- **Cohort metrics.** `compute_cohort_metrics` gains a `label_metrics` block.
  It holds per-mode label sensitivity (detected failure pairs out of all
  failure pairs at each mode) and the clean-label false-positive count and
  rate.
- **The one-mode path is unchanged.** A case without `label_modes` is scored
  exactly as before. Its record and its cohort's metrics serialise with the
  key sets they had before this item.

**Not in scope.**

- Reading the `rl1` table, its vendored schema, the schema-tag refusal, and
  the role rule that keeps a test-role row out of calibration. All of that is
  item 231.
- A `segfacet evaluate` flag, and the human-readable report. The JSON
  evaluation report carries `label_metrics` through the existing metrics
  block, and nothing new is printed (Left open).
- Any change to `classify_outcome`, `CaseOutcome`, `Expectation` or the
  synthetic corpora. How a transitional L5 is scored is Stage 16's question
  (insight `2026-10-12-76ac`). This item scores whatever mode id it is given.

## Acceptance Criteria

Terms used below:

- **A counted finding** is a finding in the case result's `findings` whose
  `severity >= positive_severity`, the same threshold `classify_outcome`
  applies to the verdict.
- **A finding falls on label L** when `L in finding.labels`. A case-level
  finding (empty `labels`) falls on no label.
- **A finding serves mode m** when
  `m in failure_modes.modes_for_detector(finding.rule_id, finding.detector_id)`.

- [ ] **AC1: The helper's pairs.** `label_mode_expectation(pairs)["label_modes"]`
  equals the sorted list of the distinct `[label, mode]` pairs in `pairs`, each
  pair a two-element list of `int`.
- [ ] **AC2: The helper's verdict.** `label_mode_expectation(pairs)["expected_verdict"]`
  is `"pass"` when every pair's mode is 0, and `"flagged-for-review"` otherwise.
- [ ] **AC3: An unknown mode is refused.** `classify_label_outcomes` raises
  `FacetInputError` for an expectation with a pair whose mode is neither 0 nor a
  key of `failure_modes.SPECIFICATION`. The message names that mode id.
- [ ] **AC4: A label that is both clean and failed is refused.**
  `classify_label_outcomes` raises `FacetInputError` for an expectation that
  pairs one label with mode 0 and with a non-zero mode. The message names that
  label.
- [ ] **AC5: Detection per failure pair.** For each pair `(L, m)` with `m != 0`,
  the `LabelOutcome.detected` that `classify_label_outcomes` returns equals
  whether some counted finding falls on `L` and serves `m`.
- [ ] **AC6: Flagging per pair.** For each pair `(L, m)`, the
  `LabelOutcome.flagged` that `classify_label_outcomes` returns equals whether
  some counted finding falls on `L`.
- [ ] **AC7: The harness scores a several-mode case per label.** Take a case
  whose `expected` was built by `label_mode_expectation` with two labels at two
  different non-zero modes and one label at mode 0. `evaluate_case` returns a
  record whose `label_outcomes` equals
  `classify_label_outcomes(case.expected, case_result, positive_severity=...)`,
  where `case_result` comes from `run_qc` on the same subject. It has one entry
  per pair, ordered by `(label, failure_mode)`.
- [ ] **AC8: A one-mode record keeps its key set.** For a case whose `expected`
  has no `label_modes` key, `CaseEvaluation.to_dict()` has exactly the keys
  `{case_id, outcome, overlap, feature_match, candidate_present, subject,
  metadata, per_mode}`.
- [ ] **AC9: Per-mode label sensitivity.** For a cohort that includes per-label
  cases, `compute_cohort_metrics(...).label_metrics.per_mode` has one entry per
  distinct non-zero mode among the cohort's pairs, in ascending mode order.
  Each entry's `n_labels`, `n_detected` and `sensitivity` equal the count of
  that mode's pairs across all records, the count of those that are detected,
  and their ratio.
- [ ] **AC10: Clean-label false positives.** For the same cohort,
  `label_metrics.n_clean_labels` equals the number of mode-0 pairs across all
  records. `label_metrics.n_clean_labels_flagged` equals how many of those are
  flagged, and `label_metrics.clean_label_false_positive_rate` equals their
  ratio.
- [ ] **AC11: One-mode cohort metrics keep their key set.** For a cohort with no
  per-label case, `compute_cohort_metrics(...).to_dict()` has exactly the keys
  `{counts, false_positive_rate, sensitivity, specificity, per_mode,
  dice_vs_flag, feature_divergence_vs_flag, n_cases}`.
- [ ] **AC12: The evaluation report carries the label metrics.** For a cohort
  that includes a per-label case, `build_evaluation_report(metrics, provenance)
  ["metrics"]["label_metrics"]` equals `metrics.to_dict()["label_metrics"]`.

## Assumptions

`loop.clarify = "assume"`. Each entry records a default taken where the queue
line left a choice. None pins a dependency's interface, since this item has no
dependency. A7 is the interface this item **produces** for item 231.

- **A1: How a finding is attributed to a mode.** The queue line says "a finding
  on that label is attributed to that mode". Read literally, a finding is
  attributed to every mode its `(rule_id, detector_id)` serves under
  `failure_modes.modes_for_detector`, the specification's own derivation
  (item 164). So one `bounds` / `metric_out_of_range` finding, which serves
  modes 2, 3 and 4, detects any of those three on its label. A finding whose
  pair serves no mode (an empty `detector_id`, or a mode-less rule) detects
  nothing, but it still flags its label.
- **A2: A per-label case is still classified at case level.** `evaluate_case`
  still calls `classify_outcome` on every case, so a per-label case adds to
  the confusion counts with the `expected_verdict` from AC2. An all-clean
  reviewed case that flags is a case-level false positive, and that is the
  real-data FPR Stage 16 measures. Such a case carries no `failure_mode`, so
  as an expected failure it lands in the case-level `per_mode` list's
  existing trailing `None` bucket, the bucket that already holds any manifest
  case without a mode. The per-mode answer for these cases is
  `label_metrics`, not that bucket.
- **A3: An unreviewed label is ignored.** A finding on a label that no pair
  names adds nothing to `label_outcomes` or `label_metrics`. The table records
  only what a reviewer looked at, so an unnamed label is not known to be clean.
- **A4: Several modes on one label are allowed. Clean with failed is not.**
  The `rl1` field table does not limit a label to one row. A label with two
  non-zero modes therefore has two pairs, each scored on its own. A label
  paired with both 0 and a non-zero mode contradicts itself and is refused
  (AC4). Duplicate pairs are collapsed to one.
- **A5: The severity threshold is the case-level one.** Only findings at or
  above `positive_severity` count, so the per-label and case-level reductions
  agree when the threshold is raised to `Severity.FAIL`.
- **A6: An absent block is omitted, not null.** `CaseEvaluation.to_dict()`
  writes `label_outcomes` only when the field is set. `CohortMetrics.to_dict()`
  writes `label_metrics` only when the field is set. This keeps every
  synthetic-corpus record and report key-for-key what it was before (AC8,
  AC11), which is the queue line's "same metrics as before". The values the
  one-mode path computes are untouched, because `classify_outcome` and the
  existing aggregation are not changed. Their existing tests (listed under
  Testing Strategy) keep pinning them.
- **A7: The interface item 231 reads (producer side).** Item 231 builds each
  case's `EvaluationCase.expected` by calling
  `segfacet.eval.label_outcome.label_mode_expectation(pairs)`. `pairs` is an
  iterable of `(label_id, mode_id)` integer pairs, one per `rl1` row of the
  case, with mode 0 for a reviewed-clean label. The helper returns a plain
  `dict` with exactly two keys: `"expected_verdict"` (AC2) and
  `"label_modes"` (AC1). It raises `segfacet.io.FacetInputError` on an
  invalid pair (AC3, AC4). Item 231 reads nothing else of this item. In
  particular it reads no serialised layout: role and provenance travel in
  `EvaluationCase.metadata`, which the harness already carries through
  unchanged.

## Implementation Steps

1. **New module `src/segfacet/eval/label_outcome.py`.** Its docstring names
   item 230, its scope fence (no table reading, no CLI) and A1–A6. It holds:
   - `LabelOutcome`, a frozen dataclass with fields `label: int`,
     `failure_mode: int`, `flagged: bool` and `detected: Optional[bool]`.
     `detected` is `None` for a mode-0 pair.
   - `_validated_label_modes(raw) -> Tuple[Tuple[int, int], ...]`. It accepts
     any sequence of two-element sequences (JSON lists from a cohort manifest
     included) and requires `int` labels and modes, rejecting `bool`. It
     requires each mode to be 0 or a key of `failure_modes.SPECIFICATION`
     (AC3) and refuses a label paired with both 0 and a non-zero mode (AC4).
     It deduplicates and sorts the pairs. Errors are
     `segfacet.io.FacetInputError`.
   - `label_mode_expectation(pairs) -> dict`. It calls the validator and
     returns `{"expected_verdict": ..., "label_modes": [[l, m], ...]}` (AC1,
     AC2). The verdict strings are `Severity.PASS.label` and
     `Severity.FLAG.label`, never re-typed.
   - `classify_label_outcomes(expected, actual, *,
     positive_severity=Severity.FLAG) -> Optional[Tuple[LabelOutcome, ...]]`.
     It returns `None` when `expected` has no `label_modes` key. Otherwise it
     validates the pairs and scores each one against `actual.findings`, read
     duck-typed the way `outcome._extract_actual` reads them: `.rule_id`,
     `.detector_id` (default `""` through `getattr`), `.labels` and
     `.severity`. Detection calls `failure_modes.modes_for_detector`, imported
     inside the function (AC5, AC6).
   - `LabelModeSensitivity`, a frozen dataclass with fields `failure_mode`,
     `n_labels`, `n_detected` and `sensitivity: Optional[float]`.
     `LabelMetrics`, a frozen dataclass with fields
     `per_mode: Tuple[LabelModeSensitivity, ...]`, `n_clean_labels`,
     `n_clean_labels_flagged` and
     `clean_label_false_positive_rate: Optional[float]`.
   - `compute_label_metrics(records) -> Optional[LabelMetrics]`. It reads
     `getattr(record, "label_outcomes", None)`, because `compute_cohort_metrics`
     accepts duck-typed records and the existing tests pass records that lack
     the attribute. It returns `None` when no record carries outcomes.
     Otherwise it aggregates (AC9, AC10), using
     `segfacet.eval.metrics._safe_rate` for the ratios. To avoid a circular
     import, the helper is imported inside the function.
2. **`src/segfacet/eval/harness.py`.** Add the field
   `label_outcomes: Optional[Tuple[LabelOutcome, ...]] = None` last on
   `CaseEvaluation`. In `evaluate_case`, after `classify_outcome`, set it with
   `classify_label_outcomes(case.expected, case_result,
   positive_severity=positive_severity)`, which reuses the `case_result`
   already computed and needs no second pipeline pass (AC7).
   `CaseEvaluation.to_dict()` adds `"label_outcomes"` (each entry through the
   existing `_asdict_enum_safe`) only when the field is not `None` (AC8).
   Update the module docstring's public-API entry.
3. **`src/segfacet/eval/metrics.py`.** Add the field
   `label_metrics: Optional[LabelMetrics] = None` last on `CohortMetrics`, with
   a default so every existing keyword construction still works.
   `compute_cohort_metrics` fills it from `compute_label_metrics(records)`.
   `CohortMetrics.to_dict()` drops the `label_metrics` key when it is `None`
   (AC11). Update the docstrings.
4. **No change** to `outcome.py`, `report.py`, the bundled
   `eval_report_schema_v0.json` (its `metrics` block is
   `additionalProperties: true`, so AC12 needs nothing), `cohort.py`
   (`load_cohort_manifest` already copies `expected` verbatim, so a JSON
   manifest carrying `label_modes` already reaches the harness) or `cli.py`.
   `segfacet/eval/__init__.py` is not changed either. Item 231 imports from
   `segfacet.eval.label_outcome` directly. No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/eval/label_outcome.py` — the new expectation helper, per-label scorer and label metrics (AC1–AC6, AC9, AC10)
- `src/segfacet/eval/harness.py` — `CaseEvaluation.label_outcomes` and its wiring in `evaluate_case` (AC7, AC8)
- `src/segfacet/eval/metrics.py` — `CohortMetrics.label_metrics` and its omission when absent (AC9–AC11)
- `tests/test_230_label_mode_expectation.py` — the item's tests
- `tests/test_099_per_mode_metrics.py` — added by the 2026-10-18 correction: `test_ac25_eval_metrics_public_names_unchanged` pins `CohortMetrics`'s exact field set, reconciled to include `label_metrics` and nothing else

**Asserts against:**

- `src/segfacet/failure_modes.py` — AC3 reads `SPECIFICATION`'s keys, and AC5/AC9 recompute detection through `modes_for_detector`
- `src/segfacet/eval/eval_report_schema_v0.json` — AC12 builds a report that `build_evaluation_report` validates against it, unchanged

## Testing Strategy

Test module: `tests/test_230_label_mode_expectation.py`. It must not import
`segfacet.cli`, spawn a subprocess, read bytes, or handle path text
(`as_posix`, `os.sep`): those are the OS-sensitivity signals
`tests/test_213_windows_ci_subset.py` classifies, and `.github/workflows/ci.yml`
is not authorised here. Use `tmp_path` only if a JSON manifest is needed, and
read it back with `read_text` / `json.loads`.

Fixtures read the producers' own code:

- Build findings for AC5/AC6 as real `segfacet.heuristics.finding.Finding`
  objects. Take their `(rule_id, detector_id)` pairs from the registered rules
  (`segfacet.heuristics.rule.iter_rules()` and each rule's declaration's
  `detectors`), picking a detector by what
  `failure_modes.modes_for_detector` returns. Never hard-code a mode table.
  Wrap the findings in a minimal object exposing `.findings`.
- For AC7, use a `segfacet.synth.corpus.build_corpus()` case with at least one
  labelled finding under `bundled_default_config()`. Choose the pairs from the
  live `run_qc` result, and recompute the expected outcomes from that result,
  not from literals.
- For AC9–AC12, use a cohort built through `evaluate_cohort` over corpus cases
  with `label_mode_expectation` expectations. Recompute the counts from the
  returned records' `label_outcomes`.

Adversarial cases, each with the failure mode it guards:

- `case-level-finding`: a finding with empty `labels` leaves every clean pair
  `flagged is False`. This guards a case-level finding being counted as a
  false positive on every reviewed-clean label.
- `unreviewed-label`: a finding on a label that no pair names adds no
  `LabelOutcome` and moves no `label_metrics` count. This guards an unreviewed
  label being scored as clean (A3).
- `wrong-mode-detector`: a finding on a mode-`m` label from a detector that
  does not serve `m` gives `flagged is True` and `detected is False`. This
  guards detection by label alone.
- `multi-mode-detector`: a finding from a detector that serves several modes
  detects each of those modes on its label. This guards attribution to only
  the first mode a detector serves (A1).
- `duplicate-pair`: a pair given twice yields one `label_modes` entry and is
  counted once in `label_metrics`. This guards double-counting a label in
  sensitivity (A4).
- `severity-threshold`: at `positive_severity=Severity.FAIL`, a
  `Severity.FLAG` finding on a clean label leaves it `flagged is False`. This
  guards the per-label and case-level reductions disagreeing (A5).
- `helper-validates`: `label_mode_expectation` given an unknown mode raises
  `FacetInputError`. This guards item 231 building an expectation that fails
  only later, at scoring.
- `duck-typed-records`: `compute_cohort_metrics` over records lacking a
  `label_outcomes` attribute returns `label_metrics is None`. This guards the
  existing duck-typed callers (`tests/test_054_metrics.py`'s fakes) breaking
  (step 1).

**Existing tests to reconcile: none expected.** The sweep (`grep` over
`tests/` for `CaseOutcome`, `CohortMetrics(`, `CaseEvaluation(`, `to_dict()`
key sets and `dataclasses.fields`) found these pins, all on shapes this item
keeps:

- `tests/test_052_outcome.py` AC1 pins `CaseOutcome`'s exact field set.
  `CaseOutcome` is not changed.
- `tests/test_054_metrics.py` AC1 checks `CohortMetrics` fields as a
  superset (`>=`). A new field passes.
- `tests/test_055_calibrate.py` and `tests/test_101_per_mode_cohort.py`
  construct `CohortMetrics` by keyword. The new field has a default.
- `tests/test_112_overlap_short_circuit.py` builds its expected dict through
  `CaseEvaluation(...).to_dict()`, so it follows the omission rule
  automatically.

These tests, together with `tests/test_053_eval_harness.py`,
`tests/test_057_acceptance_stage7.py`, `tests/test_153_eval_harness_rekey.py`
and `tests/test_190_condition_keyed_eval_bucket.py`, are what keep the
one-mode metric values pinned. They must pass unchanged.

**Correction (2026-10-18), after validation round 1.** The "none expected"
claim above is wrong: the sweep missed an exact-equality pin.
`tests/test_099_per_mode_metrics.py::test_ac25_eval_metrics_public_names_unchanged`
asserts `{f.name for f in dataclasses.fields(CohortMetrics)} == {...}`, so the
new `label_metrics` field fails it. It is the one existing test to reconcile:
add `"label_metrics"` to that expected set and change nothing else in the
file (no other assertion, no other test). The file is added to **May change**
for this alone. The other pins listed above stand as written.

**Correction (2026-10-18), after validation round 1 — scenario fixture.** The
AC7 and AC9–AC12 fixtures above say the scenario comes from
`segfacet.synth.corpus.build_corpus()` cases. Round 1 showed no corpus case
under `bundled_default_config()` yields counted findings on two labels at two
different modes, so the multi-label, multi-mode scenario cannot be drawn from
the corpus. The test may instead construct its own label map — through
`tests/synthetic.py` and `segfacet.synth` helpers, combining two defects on
two different labels — and run it through `run_qc` / `evaluate_case` /
`evaluate_cohort` exactly as the corpus case would have been. The rule that
expected outcomes and counts are recomputed from the live results, never from
literals, is unchanged.

## Dependencies

None. Item 230 is independent of items 228 and 229.

**Downstream:** item 231 reads A7's helper to turn `rl1` rows into this
expectation. Item 235 replays the stage through it.

## Decisions & Trade-offs

- `label_outcome.py` imports nothing from `metrics.py` at module level
  (`_safe_rate` is imported inside `compute_label_metrics`), so `metrics.py`
  and `harness.py` can import the dataclasses at the top without a cycle.
- A non-sequence `label_modes` and a malformed pair both raise
  `FacetInputError`, as does a non-int (or bool) label or mode.

- **Left open:** whether `render_evaluation_report` prints `label_metrics`,
  and whether `segfacet evaluate` takes a review-label table directly. The
  JSON report already carries the block (AC12). How the table reaches the CLI
  is item 231's reader question, so this item does not guess at its shape.
