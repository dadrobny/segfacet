"""Tests for item 190 -- a condition-keyed bucket in the eval harness's
per-mode aggregation.

Closes the ``docs/aide/insights.md`` ``gap`` entry dated 2026-09-16 (item
155): a condition case (manifest ``kind == "condition"``) carries
``failure_mode == 0``, the clean control's key, so ``_compute_per_mode``
used to fold every condition case into the mode-0 bucket under a name that
was wrong either way. This item gives ``CaseOutcome``/``PerModeSensitivity``
a ``condition`` field and routes every expected-failure record with a
condition to a bucket of its own, keyed by the condition id, leaving the
mode-0 bucket to hold only records that carry no condition.

Covers Acceptance Criteria AC1-AC6 (one test each) plus the three
adversarial cases the item spec's Testing Strategy names, and no others.
The corpus cohort (14 pipeline runs) is built once, via
``functools.lru_cache``, and reused across every AC test -- mirroring
``tests/test_057_acceptance_stage7.py``'s treatment of the same corpus.

Every expected value is recomputed from ``tests/corpus/manifest.json`` (via
``load_manifest()``) and from ``segfacet.failure_modes.CONDITIONS`` -- none
of the item spec's Testing Strategy table values are pinned here.

All tests are deterministic, CPU-only, and portable (no network, no
absolute paths, no services).
"""

from __future__ import annotations

import functools

from segfacet.aggregate import CaseResult
from segfacet.config import bundled_default_config
from segfacet.eval.harness import (
    CaseEvaluation,
    CohortEvaluation,
    EvaluationCase,
    evaluate_cohort,
)
from segfacet.eval.metrics import compute_cohort_metrics
from segfacet.eval.outcome import CaseOutcome, Outcome, classify_outcome
from segfacet.failure_modes import CONDITIONS
from segfacet.synth.corpus import crop_to_grid, load_manifest
from segfacet.synth.perturbation import (
    CASE_KIND_CLEAN_CONTROL,
    CASE_KIND_CONDITION,
    CASE_KIND_FAILURE,
    FAILURE_MODE_NAMES,
    corpus_case_kind,
)
from segfacet.synth.regression import loaded_seg_image
from segfacet.verdict import Verdict


# =========================================================================== #
# Shared fixtures/helpers
# =========================================================================== #


def _manifest_cases():
    return load_manifest()["cases"]


def _expected_failure_cases():
    """Manifest cases whose ``expected_verdict`` is not ``"pass"`` (the item
    spec's "expected-failure manifest case" term)."""
    return [c for c in _manifest_cases() if c["expected_verdict"] != "pass"]


@functools.lru_cache(maxsize=1)
def _corpus_metrics():
    """Build the corpus cohort once (14 pipeline runs) and compute both
    ``Metrics(FAILURE_MODE_NAMES)`` and ``Metrics(None)`` from it, exactly
    as ``tests/test_116_ras_native_corpus.py::_build_corpus_cohort`` builds
    the cohort."""
    manifest_cases = _manifest_cases()
    clean_case = next(c for c in manifest_cases if c["case_id"] == "clean_control")
    gt_img = loaded_seg_image(clean_case)

    eval_cases = []
    for case in manifest_cases:
        candidate_img = gt_img if case["case_id"] == "clean_control" else loaded_seg_image(case)
        eval_cases.append(
            EvaluationCase(
                case_id=case["case_id"],
                gt=crop_to_grid(gt_img, candidate_img),
                candidate=candidate_img,
                expected=case,
            )
        )
    cohort = evaluate_cohort(eval_cases, bundled_default_config())
    explicit = compute_cohort_metrics(cohort, failure_modes=FAILURE_MODE_NAMES)
    observed = compute_cohort_metrics(cohort)
    return explicit, observed


def _empty_actual():
    """An ``actual`` with an empty verdict and no findings -- the minimal
    shape ``classify_outcome`` accepts (item 052's Testing Strategy avoids a
    ``HeuristicConfig`` stub by building ``Verdict``/``CaseResult`` directly)."""
    verdict = Verdict.build(reasons=(), per_label={})
    return CaseResult(verdict=verdict, findings=())


def _hand_built_outcome(*, failure_mode, condition):
    """A minimal true-positive ``CaseOutcome`` with the given
    ``failure_mode``/``condition``, for the adversarial no-pipeline test."""
    return CaseOutcome(
        outcome=Outcome.TRUE_POSITIVE,
        expected_verdict="fail",
        actual_verdict="fail",
        expected_failure=True,
        actual_flagged=True,
        caught=True,
        failure_mode=failure_mode,
        failure_mode_name=None,
        expected_rule_ids=(),
        expected_labels=(),
        fired_rule_ids=(),
        designated_rule_fired=False,
        caught_by_designated_rule=True,
        condition=condition,
    )


def _hand_built_case(outcome, case_id):
    return CaseEvaluation(
        case_id=case_id,
        outcome=outcome,
        overlap=None,
        feature_match=None,
        candidate_present=False,
        subject="gt",
        metadata=None,
    )


# =========================================================================== #
# AC1: CaseOutcome carries the case's condition
# =========================================================================== #


def test_ac1_case_outcome_carries_condition():
    actual = _empty_actual()
    for case in _manifest_cases():
        outcome = classify_outcome(case, actual)
        assert outcome.condition == (case["condition"] or None)


# =========================================================================== #
# AC2: the explicit-mode layout ends in one entry per condition
# =========================================================================== #


def test_ac2_explicit_mode_layout_ends_in_one_entry_per_condition():
    explicit, _observed = _corpus_metrics()

    condition_ids = sorted(
        {
            c["condition"]
            for c in _expected_failure_cases()
            if corpus_case_kind(c) == CASE_KIND_CONDITION
        }
    )
    assert condition_ids

    expected_keys = [(m, None) for m in FAILURE_MODE_NAMES] + [
        (None, cid) for cid in condition_ids
    ]
    actual_keys = [(e.failure_mode, e.condition) for e in explicit.per_mode]
    assert actual_keys == expected_keys


# =========================================================================== #
# AC3: the observed-mode layout
# =========================================================================== #


def test_ac3_observed_mode_layout():
    _explicit, observed = _corpus_metrics()

    expected_failure_cases = _expected_failure_cases()
    modes = sorted(
        {
            c["failure_mode"]
            for c in expected_failure_cases
            if corpus_case_kind(c) == CASE_KIND_FAILURE
        }
    )
    condition_ids = sorted(
        {
            c["condition"]
            for c in expected_failure_cases
            if corpus_case_kind(c) == CASE_KIND_CONDITION
        }
    )
    assert modes
    assert condition_ids

    expected_keys = [(m, None) for m in modes] + [(None, cid) for cid in condition_ids]
    actual_keys = [(e.failure_mode, e.condition) for e in observed.per_mode]
    assert actual_keys == expected_keys


# =========================================================================== #
# AC4: each condition case is reported under its condition's name
# =========================================================================== #


def test_ac4_condition_entry_name_matches_conditions_catalogue():
    explicit, _observed = _corpus_metrics()
    condition_entries = [e for e in explicit.per_mode if e.condition is not None]
    assert condition_entries

    for entry in condition_entries:
        assert entry.failure_mode_name == CONDITIONS[entry.condition].short_name


# =========================================================================== #
# AC5: each condition bucket holds exactly its condition's cases
# =========================================================================== #


def test_ac5_condition_bucket_n_cases_matches_manifest_count():
    explicit, _observed = _corpus_metrics()
    condition_entries = [e for e in explicit.per_mode if e.condition is not None]
    assert condition_entries

    expected_failure_cases = _expected_failure_cases()
    for entry in condition_entries:
        expected_count = sum(
            1 for c in expected_failure_cases if c["condition"] == entry.condition
        )
        assert entry.n_cases == expected_count


# =========================================================================== #
# AC6: the clean control's bucket holds only clean controls
# =========================================================================== #


def test_ac6_clean_control_bucket_holds_only_clean_controls():
    explicit, _observed = _corpus_metrics()
    entry = next(
        (e for e in explicit.per_mode if (e.failure_mode, e.condition) == (0, None)), None
    )
    assert entry is not None

    expected_count = sum(
        1 for c in _expected_failure_cases() if corpus_case_kind(c) == CASE_KIND_CLEAN_CONTROL
    )
    assert entry.n_cases == expected_count


# =========================================================================== #
# Adversarial cases (named exactly as the Testing Strategy labels them)
# =========================================================================== #


def test_absent_condition_key():
    """Guards against a ``KeyError``, or a ``""`` bucket, for a hand-built
    or eval-cohort-manifest expectation that carries no ``condition`` key at
    all (as opposed to the corpus manifests' empty-string ``""``)."""
    outcome = classify_outcome({"expected_verdict": "pass"}, _empty_actual())
    assert outcome.condition is None


def test_non_vacuous_clean_control_bucket():
    """Guards AC6 being met only because the corpus holds no expected-
    failure clean control, where it reads ``0 == 0``: a hand-built cohort
    (no pipeline) with one mode-0/no-condition record and one mode-0/
    fov_truncation-condition record must split into two separate buckets."""
    cohort = CohortEvaluation(
        cases=(
            _hand_built_case(
                _hand_built_outcome(failure_mode=0, condition=None), "mode0-no-condition"
            ),
            _hand_built_case(
                _hand_built_outcome(failure_mode=0, condition="fov_truncation"),
                "mode0-fov-truncation",
            ),
        )
    )
    metrics = compute_cohort_metrics(cohort)

    mode0_entry = next(
        (e for e in metrics.per_mode if (e.failure_mode, e.condition) == (0, None)), None
    )
    condition_entry = next(
        (e for e in metrics.per_mode if (e.failure_mode, e.condition) == (None, "fov_truncation")),
        None,
    )
    assert mode0_entry is not None
    assert condition_entry is not None
    assert mode0_entry.n_cases == 1
    assert condition_entry.n_cases == 1


def test_conservation():
    """Guards a condition record being counted in both its condition bucket
    and the mode-0 bucket, or being dropped: the sum of ``n_cases`` over
    ``Metrics(FAILURE_MODE_NAMES).per_mode`` equals the number of expected-
    failure manifest cases."""
    explicit, _observed = _corpus_metrics()
    assert sum(e.n_cases for e in explicit.per_mode) == len(_expected_failure_cases())
