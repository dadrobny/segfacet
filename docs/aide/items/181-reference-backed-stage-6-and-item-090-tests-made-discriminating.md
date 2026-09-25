<!-- aide-template: item 2 -->
# Item 181 — Reference-backed Stage 6 and item-090 tests made discriminating

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 181
> **Objectives:** G3
> **Suggested branch:** `aide/181-reference-backed-stage-6-and`

---

## Description

Three reference-backed tests pass on the lordotic corpus base whether or not
the perturbation they test did anything (`insights.md`, the two `defect`
entries of item 175, 2026-09-24):

- `tests/test_049_acceptance_stage6.py::test_ac11_size_distorting_perturbation_flags_label_22_out_of_range`
  (parametrised over `inject_islands` and `crop_at_border`) asserts that label
  22's `out_of_range_features` is non-empty against
  `bundled_default_reference()`. The unperturbed `clean_control` already reads
  `['physical_volume_mm3']` there, because clean_control's L3 volume
  (19437 mm³) sits 0.7 mm³ above that reference's p99 (19436.3 mm³).
- Its sibling `test_ac11_size_distorting_perturbation_fires_reference_delta_finding_on_label_22`
  asserts that a `reference_delta` finding names label 22 against the same
  reference, and `clean_control` fires one too.
- `tests/test_090_reference_derived_defaults.py::test_ac14_mode6_crop_at_border_fires_bounds_on_label_22_against_verse_v1`
  asserts that `bounds` fires on label 22 of `crop_at_border` against
  `bundled_production_reference()`. On `clean_control` it fires on every
  label, label 22 included.

This item gives each of the two `test_049` tests a **control arm**: the same
predicate, evaluated on `clean_control` against the same reference, must be
false. `clean_control` is the manifest's `identity` perturbation of the same
base, so the control arm is the perturbation replaced by the identity. The
two tests switch to the reference against which that holds,
`_build_bracketing_reference()`, which the module already builds for its AC10
tests (A2).

`test_090`'s AC14 test is **retired**, because no bounds predicate on label 22
separates the two arms against verse-v1 on this base (A3). The reason is
recorded in the test module, where the test was.

**Not in scope.** No production code changes. `reference_default.json` and
`reference_verse_v1.json` are not regenerated or rescaled. No corpus fixture
is added or changed. The other tests in both modules are not touched. The
determinism and non-mutation tests in `test_049` still use
`bundled_default_reference()`, and neither claims a detection. `test_090`'s
AC13 fragmentation tests are already discriminating: measured 2026-09-25,
`clean_control` fires no `fragmentation` finding against
`bundled_default_reference()`, while `fragment` and `inject_islands` both
fire on label 22.

## Acceptance Criteria

Both criteria are about the two rewritten tests in
`tests/test_049_acceptance_stage6.py`. Each test is the AC's test, and it
keeps its current name and its parametrisation over
`("inject_islands", "crop_at_border")`. `R` is the reference returned by
`_build_bracketing_reference()`, and `run(c)` is
`run_qc_with_reference(loaded_seg_image(<manifest case c>), bundled_default_config(), R)`.

- [ ] **AC1: The out-of-range predicate separates each perturbed case from
  `clean_control`.** Let `P(c)` be
  `run(c)[2]["per_label"]["22"]["out_of_range_features"] != []`. For each
  `case_id` in `("inject_islands", "crop_at_border")`,
  `[P("clean_control"), P(case_id)] == [False, True]`, with both arms
  evaluated against the same `R`.
- [ ] **AC2: The `reference_delta`-finding predicate separates each perturbed
  case from `clean_control`.** Let `Q(c)` be
  `any(f.rule_id == "reference_delta" and 22 in f.labels for f in run(c)[0].findings)`.
  For each `case_id` in `("inject_islands", "crop_at_border")`,
  `[Q("clean_control"), Q(case_id)] == [False, True]`, with both arms
  evaluated against the same `R`.

The `test_090` AC14 retirement carries no criterion. Deleting a test adds no
test, and the Validation section replays the measured premise it rests on
(A3).

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1:** The queue's "unperturbed case" and "perturbation replaced by the
  identity" both mean the committed `clean_control` case. Measured
  2026-09-25 in `tests/corpus/manifest.json`: `clean_control` has
  `perturbation == "identity"`, and its `base`
  (`{"curve_amplitude_mm": 0.0, "levels": ["L1".."L5"], "spacing": [1.0, 1.0, 1.0]}`)
  equals the `base` of both `inject_islands` and `crop_at_border`. Each AC
  test checks this as a precondition (Testing Strategy), so a later corpus
  change that gives the arms different bases cannot turn the control arm into
  a base comparison unnoticed.
- **A2:** The two `test_049` tests are rewritten against
  `_build_bracketing_reference()`, not `bundled_default_reference()`. Measured
  2026-09-25, against the bracketing reference: `clean_control` reads `[]` on
  every label and fires no `reference_delta` or `bounds` finding, which the
  module's AC10 tests already pin. `inject_islands` reads `['extent_y_mm']`
  on label 22 and fires `reference_delta` `out_of_range` on it.
  `crop_at_border` reads `['extent_y_mm', 'physical_volume_mm3', 'spline_offset_mm']`
  on label 22 and fires `reference_delta` on it. Two alternatives were
  rejected. The first was keeping `bundled_default_reference()` with a
  feature-level discriminator (`extent_y_mm` is out of range for both
  perturbed cases and not for the control). AC1 could use it, but AC2 would
  have to parse feature names out of finding reasons, and the bundled
  reference places `clean_control` on its own p99 boundary, 0.7 mm³ away. The
  second was regenerating `reference_default.json` so that it brackets
  `clean_control`. That changes a committed artifact which
  `test_090`'s AC12 pins, and the item's job is the tests, not the reference.
- **A3:** `test_090`'s AC14 is retired rather than rewritten, because it
  cannot be made discriminating on this base against verse-v1. Measured
  2026-09-25, `bounds` against `bundled_production_reference()` fires on
  label 22 for the same four metrics on both arms. The values:

  | Metric | `clean_control` | `crop_at_border` | verse-v1 L3 p1 |
  |---|---|---|---|
  | volume (mm³) | 19437 | 16771 | 44980.05 |
  | extent_x (mm) | 31 | 31 | 68.63 |
  | extent_y (mm) | 28 | 23 | 42.67 |
  | extent_z (mm) | 28 | 28 | 44.63 |

  No rescaling of the synthetic box base moves `clean_control` into all four
  L3 bands. The smallest per-axis scale that reaches every extent's p1
  (×2.21, ×1.52, ×1.59) multiplies the volume by about 5.4, to roughly
  104,500 mm³, which is above the p99 of 90,790 mm³. A real L3 fills about
  13 % of its bounding box, and the synthetic box fills about 80 %.
  Rewriting the test against the bracketing reference would separate the
  arms. Measured: `crop_at_border` fires `bounds` on label 22 for volume
  16771 < p1 19346.8 and extent_y 23 < p1 28, and `clean_control` fires none.
  But that asserts reference-mode `bounds` sensitivity on a synthetic
  reference. It does not assert item 090's claim that the real-grounded
  default still catches the crop, and no consumer in this batch needs it, so
  it is not added (posture `prototype`).
- **A4:** "The reason recorded" means that the retirement reason is recorded
  in `test_090`'s module docstring, on the AC14 line of its AC list, and in a
  comment left in place of the deleted test. Both name this item and the
  measured premise from A3. Item 090's merged spec is not amended, because it
  is the record of what that item was built from.

## Implementation Steps

This item changes nothing under `source_dir`. Every edit is under
`tests_dir`, so all of it is the **test-writer's** work. The builder's step
is to confirm that no `src/segfacet/` change is needed, and to record that
in Decisions.

1. **`tests/test_049_acceptance_stage6.py`, AC1.** Rewrite
   `test_ac11_size_distorting_perturbation_flags_label_22_out_of_range`. Get
   `R` from `_build_bracketing_reference()`, which already exists in the
   module, and evaluate `clean_control` and `case_id` through the existing
   `_case`, `loaded_seg_image` and `run_qc_with_reference`, both against that
   one `R`. Assert the A1 precondition, then assert the AC1 equality.
2. **Same module, AC2.** Rewrite
   `test_ac11_size_distorting_perturbation_fires_reference_delta_finding_on_label_22`
   the same way, using the existing `_ref_findings` helper for `Q`.
3. **Share `R` across the two tests' parametrisations** through one
   module-scoped fixture, for example `bracketing_reference`, that returns
   `_build_bracketing_reference()`. The AC10 and adversarial tests keep their
   own calls unchanged.
4. **Update `test_049`'s module docstring.** The AC11 bullet names the
   bracketing reference and the `clean_control` control arm, citing this
   item.
5. **`tests/test_090_reference_derived_defaults.py`.** Delete
   `test_ac14_mode6_crop_at_border_fires_bounds_on_label_22_against_verse_v1`.
   Leave a comment under the AC14 section banner that records the retirement
   with A3's premise, meaning that both arms fire `bounds` on the same four
   label-22 metrics against verse-v1, and cites this item and the
   2026-09-24 insight. Rewrite the AC14 line of the module docstring to say
   the criterion is retired, and why. Remove any import that the deletion
   leaves unused, and nothing else.

No new helper, no new module, no new dependency.

## Authorised paths

**May change:**

- `tests/test_049_acceptance_stage6.py` — the two AC11 tests rewritten with a control arm, a shared fixture, and the docstring
- `tests/test_090_reference_derived_defaults.py` — the AC14 test retired, and its reason recorded

**Asserts against:**

- `tests/corpus/manifest.json` — AC1 and AC2 read the three cases' `perturbation` and `base` for the A1 precondition
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — the control arm of AC1 and AC2
- `tests/corpus/fixtures/inject_islands_seg.nii.gz` — the perturbed arm of AC1 and AC2
- `tests/corpus/fixtures/crop_at_border_seg.nii.gz` — the perturbed arm of AC1 and AC2

## Testing Strategy

There is no new test module. The AC tests **are** the two rewritten tests in
`tests/test_049_acceptance_stage6.py`, AC1 →
`test_ac11_size_distorting_perturbation_flags_label_22_out_of_range` and AC2
→ `test_ac11_size_distorting_perturbation_fires_reference_delta_finding_on_label_22`,
each parametrised over `("inject_islands", "crop_at_border")`.

Each AC test, before its equality:

- asserts the **A1 precondition**,
  `_case("clean_control")["perturbation"] == "identity"` and
  `_case("clean_control")["base"] == _case(case_id)["base"]`. This guards
  against a corpus change that gives the two arms different bases. The
  control arm would then measure a base difference instead of the
  perturbation, and would still pass;
- evaluates **both arms against the one `R` object**, so that the separation
  cannot come from two differently built references;
- asserts the list equality `[P("clean_control"), P(case_id)] == [False, True]`
  (for AC2, `Q`) as **one** assertion. This guards against a control arm that
  is computed and never compared, which is the vacuity this item removes.

**Adversarial cases:** none beyond the precondition above. The control arm is
the adversarial case the queue asked for, since it is the perturbation
replaced by the identity.

**Existing tests to reconcile:** these are the three tests named in the
Description and nothing else. No production default or behaviour changes. A
grep of `tests/` and `src/` on 2026-09-25 found the three test names only in
their own modules. `tests/test_126_golden_retirement.py` names
`test_090`'s `test_ac15_all_committed_goldens_still_check_true`, which is not
touched.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

1. Run `.venv/bin/python -m pytest tests/test_049_acceptance_stage6.py tests/test_090_reference_derived_defaults.py -n auto`
   (on Windows, `.venv/Scripts/python`). It must be green with no new skip.
2. **Replay A3's retirement premise.** In a scratch script, for
   `clean_control` and `crop_at_border`, run
   `run_qc_with_reference(loaded_seg_image(case), bundled_default_config(), bundled_production_reference())`
   and list the `bounds` findings whose `labels` contain 22. Both cases must
   show the same four metrics (volume, extent_x, extent_y, extent_z), each
   below its verse-v1 L3 p1. If they differ, the retirement's premise has
   failed. Hand back, because AC14 could then be rewritten rather than
   retired.
3. **Observe the control arm biting.** Temporarily replace `case_id` with
   `"clean_control"` in one rewritten test's perturbed arm, in a scratch copy
   and not on the branch. The test must fail.

No `[validation]` profile is needed.

## Dependencies

None.

**Downstream:** Stage 33 D3 (queue-025) gates the `bounds`/`reference_delta`
size features on the border condition. `crop_at_border` exhibits the FOV
truncation condition, so that change may silence its label-22 size features
in AC1 and AC2. `extent_y_mm` and `physical_volume_mm3` would go, and
`spline_offset_mm` would remain. The item that lands the gating owns
reconciling these two tests, and lists `tests/test_049_acceptance_stage6.py`
under its May change.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether item 090's claim, that the real-grounded `bounds`
  default still catches a FOV crop, is reinstated at all. It needs a fixture
  whose clean arm sits inside the verse-v1 L3 bands, and no synthetic box can
  do that (A3). A real-GT perturbation corpus (roadmap Stage 21) is where
  such a fixture would come from. This item retires the claim and does not
  re-home it.
- **Left open:** whether `reference_default.json`'s synthetic cohort should
  bracket `clean_control` with margin. Today clean_control's L3 volume sits
  0.7 mm³ above the p99. This item stops depending on it (A2), and changing
  a committed reference is a separate decision from making tests
  discriminating.
