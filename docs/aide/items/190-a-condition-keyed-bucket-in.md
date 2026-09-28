<!-- aide-template: item 2 -->
# Item 190 — A condition-keyed bucket in the eval harness

> **Created:** 2026-09-28 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-025.md`](../queue/queue-025.md) · Item 190
> **Objectives:** G7
> **Suggested branch:** `aide/190-a-condition-keyed-bucket-in`

---

## Description

This item implements the last bullet of roadmap Stage 33 D3. It closes the
`docs/aide/insights.md` `gap` entry dated 2026-09-16 (item 155), which is
already ticked with the pointer "→ item 190".

**The defect.** `segfacet.eval.metrics._compute_per_mode` groups the
expected-failure records by `CaseOutcome.failure_mode`. A condition case (a
case whose manifest `kind` is `condition`) carries `failure_mode == 0`, the
clean control's key. So every condition case lands in the mode-0 bucket. That
bucket then goes out under a name that is wrong either way:

- With `failure_modes=FAILURE_MODE_NAMES`, it carries the clean-control name.
- With `failure_modes=None`, it carries whichever record came first.

Measured on the committed geometric corpus on 2026-09-28 (scratch probe over
`evaluate_cohort` and `compute_cohort_metrics`, bundled default config):

| call | mode-0 entry | `n_cases` | name |
|---|---|---|---|
| `failure_modes=FAILURE_MODE_NAMES` | `failure_mode=0` | 3 (`displace`, `crop_at_border`, `crop_fov_si`) | `clean control (no failure)` |
| `failure_modes=None` | `failure_mode=0` | 3 (same) | `displaced vertebra (condition, not a failure mode)` |

The corpus has held two conditions since item 189: `fov_truncation` and
`displaced_vertebra`. So the harness now needs to tell them apart.

**What this item changes.**

- `CaseOutcome` gains a `condition` field, read from the expected side's
  `condition` key. Both corpus manifests and `Expectation.to_dict()` already
  carry that key.
- `PerModeSensitivity` gains a `condition` field.
- `_compute_per_mode` sends every expected-failure record with a condition to
  a bucket of its own, keyed by the condition id. A condition entry carries
  `failure_mode=None`, and its name comes from its records. The mode-0 bucket
  then holds only records that carry no condition.
- The existing tests that pin the old mode-0 bucket are reconciled (Testing
  Strategy).

**Not in scope.**

- The condition-gating of rules is item 191's.
- The detection-rate join in `per_mode_cohort.summarise_run_per_mode` is
  unchanged (Left open).
- There is no change to `eval/report.py`, `eval/calibrate.py`,
  `eval_report_schema_v0.json`, any corpus manifest or fixture, or any
  generated artifact (A6).

## Acceptance Criteria

Terms used below:

- **"The manifest"** is `segfacet.synth.corpus.load_manifest()["cases"]`.
- **"The corpus cohort"** is `evaluate_cohort` over the manifest, built the
  way `tests/test_116_ras_native_corpus.py::_build_corpus_cohort` builds it:
  - the ground truth (GT) is `crop_to_grid(clean_control image, candidate)`;
  - the candidate is each case's own seg fixture, and `clean_control` uses its
    GT as its candidate;
  - `expected` is the manifest case dict;
  - the config is `bundled_default_config()`.
- **"Metrics(X)"** is `compute_cohort_metrics(corpus cohort, failure_modes=X)`.
- **An expected-failure manifest case** is one whose `expected_verdict` is not
  `"pass"`.
- **A case's kind** is `segfacet.synth.perturbation.corpus_case_kind(case)`.
- **The key of an entry** is the pair `(entry.failure_mode, entry.condition)`.

The criteria:

- [ ] **AC1: `CaseOutcome` carries the case's condition.** For every manifest
  case, `classify_outcome(case, actual).condition` equals
  `case["condition"] or None`. Here `actual` is any object with a `.verdict`
  whose `.overall` is a `Severity`, and with an empty `.findings`.
- [ ] **AC2: the explicit-mode layout ends in one entry per condition.** The
  key sequence of `Metrics(FAILURE_MODE_NAMES).per_mode` equals two lists
  joined in order:
  - `[(m, None) for m in FAILURE_MODE_NAMES]`;
  - `[(None, c) for c in C]`, where `C` is the sorted set of `condition`
    values over the expected-failure manifest cases whose kind is
    `condition`.
- [ ] **AC3: the observed-mode layout.** The key sequence of
  `Metrics(None).per_mode` equals two lists joined in order:
  - `[(m, None) for m in M]`, where `M` is the ascending list of distinct
    `failure_mode` values over the expected-failure manifest cases whose kind
    is `failure`;
  - `[(None, c) for c in C]`, with `C` as in AC2.
- [ ] **AC4: each condition case is reported under its condition's name.**
  Take each entry `e` of `Metrics(FAILURE_MODE_NAMES).per_mode` whose
  `condition` is not `None`. Its `e.failure_mode_name` equals
  `segfacet.failure_modes.CONDITIONS[e.condition].short_name`.
- [ ] **AC5: each condition bucket holds exactly its condition's cases.** Take
  each such entry `e` of `Metrics(FAILURE_MODE_NAMES).per_mode`. Its
  `e.n_cases` equals the number of expected-failure manifest cases whose
  `condition` equals `e.condition`.
- [ ] **AC6: the clean control's bucket holds only clean controls.** Take the
  entry of `Metrics(FAILURE_MODE_NAMES).per_mode` whose key is `(0, None)`.
  Its `n_cases` equals the number of expected-failure manifest cases whose
  kind is `clean_control`.

## Assumptions

- **A1: the new `PerModeSensitivity` field.** `PerModeSensitivity` gains
  `condition: Optional[str] = None` as its **last** field, with that default.
  A condition entry has `failure_mode=None`, and every other entry has
  `condition=None`.
  - *Why `None` and not 0.* 0 is the clean control, so keeping 0 would repeat
    the double meaning that item 155 removed from the manifest.
    `per_mode_cohort.summarise_run_per_mode` indexes entries by `failure_mode`
    and skips `None` (`per_mode_cohort.py`, the `detection_by_mode` loop), so a
    condition entry can never overwrite a mode entry there.
  - *Why last, with a default.* `tests/test_055_calibrate.py` and
    `tests/test_101_per_mode_cohort.py` build `PerModeSensitivity` by keyword
    without the field.
- **A2: the new `CaseOutcome` field.** `CaseOutcome` gains
  `condition: Optional[str] = None` as its last field, with that default.
  - `classify_outcome` fills it with `expected.get("condition") or None`.
    So an absent key and the manifests' `""` for a non-condition case both
    become `None`.
  - The `CaseOutcome(**fields)` factories in `test_054`, `test_055` and
    `test_056` build the record without the field.
- **A3: routing.** A record whose `outcome.condition` is not `None` goes to its
  condition's bucket, whatever its `failure_mode`.
  - `case_kind` already refuses a non-zero mode combined with a condition. So
    no corpus record could belong to both kinds of bucket.
  - `_compute_per_mode` reads the field with
    `getattr(record.outcome, "condition", None)`. This keeps its duck-typed
    record contract.
  - The routing makes no `failure_mode` comparison with 0.
    `tests/test_155_corpus_case_kind.py::test_ac12_...` scans `src/segfacet`
    and `tests` for that shape.
- **A4: when condition entries are reported, and where.** Condition entries
  are reported for every condition observed among the expected-failure
  records. They come in ascending condition-id order, **after** every other
  entry, including a trailing no-mode-metadata `failure_mode=None` entry when
  the `failure_modes=None` path emits one.
  - An explicit `failure_modes` sequence or mapping still yields exactly one
    entry per requested mode. The condition entries follow those entries,
    because a condition is never requested by a mode integer.
  - A requested name never applies to a condition entry.
  - **Consequence for calibration.** `CalibrationObjective.evaluate` checks
    every entry with `n_cases > 0`. So a condition bucket now counts towards
    feasibility under an explicit mode list too. Before, the mode-0 bucket was
    dropped unless 0 was requested.
  - This was measured on 2026-09-28 against
    `tests/test_057_acceptance_stage7.py`'s AC13 grid
    (`reference_delta.max_robust_z` ∈ {3.0, 3.5}). At both values,
    `fov_truncation` scored 2 of 2 and `displaced_vertebra` 1 of 1 by the
    designated rule. So feasibility is unchanged.
- **A5: condition entry names.** A condition entry's `failure_mode_name` is
  its first record's `outcome.failure_mode_name`, the same way an unrequested
  mode entry gets its name.
  - `metrics.py` stays decoupled from the taxonomy (its module docstring), so
    it imports nothing from `segfacet.failure_modes`.
  - The manifests write `CONDITIONS[id].short_name` into a condition case's
    `failure_mode_name`. Measured 2026-09-28: `fov_truncation` →
    `FOV truncation (condition, not a failure mode)`, and
    `displaced_vertebra` →
    `displaced vertebra (condition, not a failure mode)`. AC4 checks this end
    to end.
- **A6: no report, schema or artifact change.**
  - `eval_report_schema_v0.json` does not enumerate the fields of a
    `per_mode` entry (its `metrics` description). So the additive `condition`
    key needs no schema edit.
  - `eval/report.py`'s text rendering labels an entry by `failure_mode_name`
    first, so a condition entry prints its condition's name.
  - No generated artifact calls `compute_cohort_metrics`. Only `cli.py` and
    `eval/calibrate.py` do, under `src/`.
- **A7: the displaced-vertebra condition (item 189, merged ✅).** It is read as
  it stands on the base branch. This item needs only the manifest `displace`
  entry's `condition == "displaced_vertebra"` and its `failure_mode_name`,
  both measured above. This records a defensible default, not a pin on an
  unbuilt interface.

## Implementation Steps

1. **`src/segfacet/eval/outcome.py`.**
   - Add `condition: Optional[str] = None` as the last field of `CaseOutcome`,
     and document it in the class docstring.
   - Make `_extract_expected` also return `expected.get("condition") or None`.
   - Have `classify_outcome` pass that value into `CaseOutcome`.
   - Add `condition` to the module docstring's list of expected keys that
     default when absent.
2. **`src/segfacet/eval/metrics.py`.**
   - Add `condition: Optional[str] = None` as the last field of
     `PerModeSensitivity`, and document it.
   - Give `_per_mode_entry` a `condition` keyword, passed through to the
     constructor.
   - In `_compute_per_mode`, split the expected-failure records into two
     groups. Records with `getattr(record.outcome, "condition", None)` set go
     into an `observed_conditions` dict keyed by condition id. The rest stay in
     `observed`, keyed by `failure_mode` as today.
   - Build the mode entries with the existing `_requested_modes` and
     `_per_mode_entry`, unchanged. Then append one
     `_per_mode_entry(None, None, records, condition=cid)` per `cid` in
     `sorted(observed_conditions)` (A4, A5).
   - Update the module docstring's per-mode paragraph and
     `compute_cohort_metrics`'s `failure_modes` parameter text to say where
     condition entries go.
3. No other `src/` file changes, and no dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/eval/outcome.py` — `CaseOutcome.condition` and its extraction
  (AC1)
- `src/segfacet/eval/metrics.py` — `PerModeSensitivity.condition` and the
  condition buckets (AC2–AC6)
- `tests/test_190_condition_keyed_eval_bucket.py` — this item's tests
- `tests/test_052_outcome.py` — the field-set pin gains `condition`
- `tests/test_054_metrics.py` — the field-set pin gains `condition`
- `tests/test_116_ras_native_corpus.py` — AC8 re-pointed at the
  `fov_truncation` bucket
- `tests/test_120_leave_one_out_offset.py` — AC24's per-mode map loses its
  mode-0 row
- `tests/test_091_stage14_acceptance.py` — the sensitivity guard re-keyed off
  mode 0 onto `fov_truncation`

**Asserts against:**

- `tests/corpus/manifest.json` — AC1–AC6 recompute each expected value from
  `load_manifest()`
- `src/segfacet/failure_modes.py` — AC4 reads `CONDITIONS[...].short_name`

## Testing Strategy

**New module: `tests/test_190_condition_keyed_eval_bucket.py`.** It has one
test per AC. Build the corpus cohort once per module, in a module-scoped
fixture or with `functools.lru_cache` as `test_057_acceptance_stage7.py`
does, because the cohort runs the pipeline over 14 cases.

- Count manifest kinds with `corpus_case_kind(case)`. Never write a
  `case["failure_mode"] == 0` comparison outside an `assert`:
  `test_155`'s AC12 scans `tests/` for that shape.
- Every expected value is recomputed from the manifest and from `CONDITIONS`.
  Values measured on 2026-09-28, for the builder's orientation only (the tests
  must not pin them):

| quantity | value |
|---|---|
| expected-failure records | 11 |
| `C` | `["displaced_vertebra", "fov_truncation"]` |
| `M` | `[1, 3, 4, 6, 9, 15]` |
| `fov_truncation` entry | `n_cases` 2 (`crop_at_border`, `crop_fov_si`), sensitivity 1.0 |
| `displaced_vertebra` entry | `n_cases` 1 (`displace`), sensitivity 1.0 |
| `(0, None)` entry under `FAILURE_MODE_NAMES` | `n_cases` 0, sensitivity `None` |
| `len(per_mode)` under `FAILURE_MODE_NAMES` | 17 → 19 |
| `len(per_mode)` under `None` | 7 → 8 |

**Adversarial cases.** Write these, and no others:

- **absent-condition-key.** `classify_outcome({"expected_verdict": "pass"},
  actual).condition is None`. This guards against a `KeyError`, or a `""`
  bucket, for the hand-built and eval-cohort-manifest expectations that carry
  no `condition` key. `test_057_acceptance_stage7`'s graded cohort is one.
- **non-vacuous clean-control bucket.** Hand-build a cohort from `CaseOutcome`
  records, with no pipeline:
  - one expected-failure record with `failure_mode=0` and `condition=None`;
  - one expected-failure record with `failure_mode=0` and
    `condition="fov_truncation"`.

  `compute_cohort_metrics(cohort)` then has a `(0, None)` entry with
  `n_cases == 1` and a `(None, "fov_truncation")` entry with `n_cases == 1`.
  This guards AC6 being met only because the corpus holds no expected-failure
  clean control, where it reads 0 == 0.
- **conservation.** The sum of `n_cases` over `Metrics(FAILURE_MODE_NAMES)
  .per_mode` equals the number of expected-failure manifest cases. This guards
  a condition record being counted in both its condition bucket and the mode-0
  bucket, or being dropped.

**Existing tests to reconcile.** The values below were measured by scratch
probe on 2026-09-28 and are exact.

- **`tests/test_052_outcome.py::test_ac1_case_outcome_is_frozen_dataclass_with_fields`.**
  Add `"condition"` to the pinned field set.
- **`tests/test_054_metrics.py::test_ac1_dataclasses_are_frozen_with_documented_fields`.**
  Add `"condition"` to `PerModeSensitivity`'s pinned field set.
- **`tests/test_116_ras_native_corpus.py::test_ac8_mode6_crop_at_border_sensitivity_is_restored_to_one`.**
  - Replace the selector `next(m for m in metrics.per_mode if
    m.failure_mode == 0)` with `m.condition == "fov_truncation"`.
  - Remove the line `assert crop_case["failure_mode"] == 0`, and keep
    `assert crop_case["condition"] == "fov_truncation"`.
  - The entry now reads `n_cases == 2` and `sensitivity == 1.0`, so the
    existing `n_cases > 0` and `sensitivity == 1.0` asserts hold.
  - Update the docstring: the case now has a bucket of its own.
  - The test name may stay.
- **`tests/test_120_leave_one_out_offset.py::test_ac24_corpus_pipeline_detection_is_nine_of_ten`.**
  - Remove `0: 1.0` from `expected_sensitivity`, because the `(0, None)`
    entry now has `n_cases == 0`.
  - Add one lookup by `m.condition` for each condition:
    `{"fov_truncation": 1.0, "displaced_vertebra": 1.0}`, each with
    `n_cases > 0`.
  - `sum(m.n_cases ...) == 11` still holds, and so do mode 6 (`n_cases == 1`)
    and mode 10 (0). Overall sensitivity stays `10/11`.
  - The docstring still files `displace` under mode 1. Correct it in the same
    edit, because since item 189 `displace` is a condition case.
- **`tests/test_091_stage14_acceptance.py`.** This file keys its sensitivity
  guard on mode 0. After this item, the `(0, None)` entry has `n_cases == 0`,
  so `per_mode_sensitivity` drops it, and `achieved[0]` raises `KeyError` in
  AC7 and AC11.
  - Re-key `per_mode_sensitivity`'s dict on
    `m.condition if m.condition is not None else m.failure_mode`.
  - Set `_BASELINE_MODES = ("fov_truncation", 1, 4, 6, 9)`.
  - Change `_PIPELINE_DETECTABLE_OPERATORS`' `("crop_at_border", 0)` row to
    `("crop_at_border", "fov_truncation")`.
  - Replace the key `0` with `"fov_truncation"` in:
    - `test_ac6_sensitivity_baseline_matches_item_057`'s literal, which
      becomes `{"fov_truncation": 1.0, 1: 1.0, 4: 1.0, 6: 1.0, 9: 1.0}`;
    - all five `test_ac8_sensitivity_regressed_truth_table` parameters;
    - `test_ac10_sensitivity_regressed_deterministic_and_non_mutating`'s
      `achieved` literal.
  - Update `sensitivity_baseline`'s docstring to match.
  - Measured results:
    - The corpus reads `fov_truncation` 1.0 (2 cases).
    - The perturbed stand-in reads `fov_truncation` 1.0: its `crop_at_border`
      expectation carries `condition="fov_truncation"`.
    - Under the over-loosened config (AC9), both `fov_truncation` cases lose
      their designated rules (`border` and `bounds` are disabled). The bucket
      reads 0.0 (0 of 2), so the guard still reports a regression.

**Checked and unaffected** (read, or probed on 2026-09-28; no edit):

- `test_057_acceptance_stage7.py`: its modes are 1, 3, 4, 6, 9 and 15, and
  its AC13 calibration stays feasible (A4).
- `test_056_eval_report.py` and `test_055_calibrate.py`: hand-built, with no
  condition.
- `test_054`'s other tests: hand-built, with no condition.
- `test_101_per_mode_cohort.py` and `test_102_stage18_validation.py`: the
  detection join is by a non-`None` `failure_mode`, and no metric is homed on
  mode 0.
- `test_084_stage12_acceptance.py`: an all-pass cohort, so `per_mode == []`.

## Dependencies

- Item 189: added the `displaced_vertebra` condition and moved `displace`
  onto it, which gives the corpus the second condition this item buckets (✅).

**Downstream:**

- Item 191 re-authors `crop_fov_si`'s and `crop_at_border`'s expected sets.
  That can change the `fov_truncation` bucket's designated-rule counts, which
  the reconciled `test_091`, `test_116` and `test_120` pins read.
- Item 195 removes `force_overlap`. That drops mode 15 from AC3's `M` and
  from `test_120`'s map.

## Decisions & Trade-offs

Implemented per the spec's Implementation Steps with no deviation:
`CaseOutcome.condition` and `PerModeSensitivity.condition` were added as the
last field with `Optional[str] = None`, `_extract_expected` now returns
`expected.get("condition") or None`, and `_compute_per_mode` splits records
into `observed` (keyed by `failure_mode`, unchanged) and
`observed_conditions` (keyed by condition id, read via
`getattr(record.outcome, "condition", None)`), appending one
`_per_mode_entry(None, None, records, condition=cid)` per `cid` in
`sorted(observed_conditions)` after the requested-mode entries.

- **Left open:** the detection-rate join for a condition-homed magnitude
  metric. `per_mode_cohort.summarise_run_per_mode` joins sensitivity entries
  by `failure_mode` only. So `fov_clipped_label_count` (homed on
  `fov_truncation`, with `failure_mode` None) still reports no detection
  rate, even though a `fov_truncation` bucket now exists to join against. No
  consumer in this batch reads that column. It waits for the item that first
  needs a condition's detection rate beside its magnitude.
