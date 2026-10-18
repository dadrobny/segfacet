"""Tests for item 230 -- a per-label, several-modes-per-case expectation in the
evaluation harness (``segfacet.eval.label_outcome`` plus its wiring into
``segfacet.eval.harness`` and ``segfacet.eval.metrics``).

One test per AC, named ``test_acN_*``, and one per adversarial case the item
spec's Testing Strategy names, named for its label. The detector/mode pairs
are read live from the registered rules and ``failure_modes.modes_for_detector``
-- never a hard-coded mode table -- and the harness scenarios recompute their
expected values from the live ``run_qc`` result.

This module deliberately uses none of the OS-sensitivity signals
``tests/test_213_windows_ci_subset.py`` classifies (no CLI import, no
subprocess, no byte reads, no path text).
"""

from __future__ import annotations

import dataclasses
import functools
from types import SimpleNamespace

import numpy as np
import pytest

from segfacet.config import bundled_default_config
from segfacet.eval.harness import EvaluationCase, evaluate_case, evaluate_cohort
from segfacet.eval.label_outcome import (
    classify_label_outcomes,
    compute_label_metrics,
    label_mode_expectation,
)
from segfacet.eval.metrics import compute_cohort_metrics
from segfacet.eval.report import EvaluationProvenance, build_evaluation_report
from segfacet.failure_modes import SPECIFICATION, modes_for_detector
from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import iter_rule_declarations
from segfacet.io import FacetInputError
from segfacet.pipeline import run_qc
from segfacet.synth.corpus import build_corpus
from segfacet.verdict import Severity

_MODES = sorted(SPECIFICATION)
_UNKNOWN_MODE = max(SPECIFICATION) + 1000


# =========================================================================== #
# Fixtures read from the producers' own code
# =========================================================================== #


def _detectors():
    """Every registered ``(rule_id, detector_id, served_modes)``."""
    out = []
    for rule_id, declaration in iter_rule_declarations():
        if declaration is None:
            continue
        for detector in declaration.detectors:
            served = modes_for_detector(rule_id, detector.detector_id)
            out.append((rule_id, detector.detector_id, served))
    return out


def _multi_mode_detector():
    found = [d for d in _detectors() if len(d[2]) >= 2]
    assert found, "no registered detector serves several modes"
    return found[0]


def _single_mode_detector():
    found = [d for d in _detectors() if len(d[2]) == 1]
    assert found, "no registered detector serves exactly one mode"
    return found[0]


def _finding(detector, labels, severity=Severity.FLAG):
    rule_id, detector_id, _served = detector
    return Finding(
        rule_id=rule_id,
        severity=severity,
        reason="test finding",
        labels=frozenset(labels),
        detector_id=detector_id,
    )


def _result(*findings):
    return SimpleNamespace(findings=list(findings))


def _by_pair(outcomes):
    return {(o.label, o.failure_mode): o for o in outcomes}


def _wrong_mode(detector):
    served = detector[2]
    others = [m for m in _MODES if m not in served]
    assert others, "detector serves every mode"
    return others[0]


@functools.lru_cache(maxsize=1)
def _scenario():
    """A corpus case with two labelled counted findings at two different
    modes plus one further label present in the segmentation:
    ``(case, (l1, m1), (l2, m2), clean_label)``."""
    config = bundled_default_config()
    for case in build_corpus():
        result, _block = run_qc(case.seg_img, config)
        pairs = sorted(
            {
                (label, mode)
                for f in result.findings
                if f.severity >= Severity.FLAG
                for mode in modes_for_detector(f.rule_id, f.detector_id)
                for label in f.labels
            }
        )
        if not pairs:
            continue
        first = pairs[0]
        second = [p for p in pairs if p[0] != first[0] and p[1] != first[1]]
        present = [int(v) for v in np.unique(np.asarray(case.seg_img.dataobj)) if v > 0]
        spare = [v for v in present if v not in (first[0], *[p[0] for p in second[:1]])]
        if second and spare:
            return case, first, second[0], spare[0]
    raise AssertionError("no corpus case yields two labelled pairs at two modes")


@functools.lru_cache(maxsize=1)
def _cohort():
    case, (l1, m1), (l2, m2), lc = _scenario()
    expectations = (
        label_mode_expectation([(l1, m1), (l2, m2), (lc, 0)]),
        label_mode_expectation([(l1, m1), (lc, 0)]),
    )
    cases = [
        EvaluationCase(case_id=f"label-case-{i}", gt=case.seg_img, expected=expected)
        for i, expected in enumerate(expectations)
    ]
    return evaluate_cohort(cases, bundled_default_config())


@functools.lru_cache(maxsize=1)
def _one_mode_cohort():
    cases = [
        EvaluationCase(
            case_id=case.case_id,
            gt=case.seg_img,
            expected=case.expectation.to_dict(),
        )
        for case in build_corpus()[:2]
    ]
    return evaluate_cohort(cases, bundled_default_config())


# =========================================================================== #
# Acceptance criteria
# =========================================================================== #


def test_ac1_helper_pairs_sorted_distinct_int_lists():
    ma, mb = _MODES[0], _MODES[1]
    pairs = [(5, mb), (3, 0), (5, mb), (4, ma)]
    got = label_mode_expectation(pairs)["label_modes"]
    assert got == sorted([list(p) for p in set(pairs)])
    assert len(got) == 3
    assert all(isinstance(p, list) and len(p) == 2 for p in got)
    assert all(type(v) is int for p in got for v in p)


def test_ac2_helper_verdict():
    all_clean = label_mode_expectation([(1, 0), (2, 0)])["expected_verdict"]
    with_failure = label_mode_expectation([(1, 0), (2, _MODES[0])])["expected_verdict"]
    assert all_clean == Severity.PASS.label
    assert with_failure == Severity.FLAG.label
    assert all_clean != with_failure


def test_ac3_unknown_mode_refused():
    expected = {"label_modes": [[1, _UNKNOWN_MODE]]}
    with pytest.raises(FacetInputError, match=str(_UNKNOWN_MODE)):
        classify_label_outcomes(expected, _result())


def test_ac4_clean_and_failed_label_refused():
    expected = {"label_modes": [[4177, 0], [4177, _MODES[0]]]}
    with pytest.raises(FacetInputError, match="4177"):
        classify_label_outcomes(expected, _result())


def _mixed_scoring_case():
    multi = _multi_mode_detector()
    single = _single_mode_detector()
    findings = (
        _finding(multi, {1}),
        _finding(single, {2}),
        _finding(multi, {5}, severity=Severity.PASS),
        _finding(multi, set()),
    )
    pairs = [
        (1, multi[2][0]),
        (2, _wrong_mode(single)),
        (3, _MODES[0]),
        (5, multi[2][0]),
        (6, 0),
        (7, 0),
    ]
    return findings, pairs


def test_ac5_detection_per_failure_pair():
    findings, pairs = _mixed_scoring_case()
    outcomes = classify_label_outcomes(label_mode_expectation(pairs), _result(*findings))
    got = _by_pair(outcomes)
    counted = [f for f in findings if f.severity >= Severity.FLAG]
    expected = {
        (label, mode): any(
            label in f.labels and mode in modes_for_detector(f.rule_id, f.detector_id)
            for f in counted
        )
        for label, mode in pairs
        if mode != 0
    }
    assert {True, False} <= set(expected.values())
    assert {k: got[k].detected for k in expected} == expected


def test_ac6_flagging_per_pair():
    findings, pairs = _mixed_scoring_case()
    outcomes = classify_label_outcomes(label_mode_expectation(pairs), _result(*findings))
    got = _by_pair(outcomes)
    counted = [f for f in findings if f.severity >= Severity.FLAG]
    expected = {
        (label, mode): any(label in f.labels for f in counted) for label, mode in pairs
    }
    assert {True, False} <= set(expected.values())
    assert {k: got[k].flagged for k in expected} == expected


def test_ac7_harness_scores_several_mode_case_per_label():
    case, (l1, m1), (l2, m2), lc = _scenario()
    expected = label_mode_expectation([(l1, m1), (l2, m2), (lc, 0)])
    config = bundled_default_config()
    record = evaluate_case(
        EvaluationCase(case_id="ac7", gt=case.seg_img, expected=expected), config
    )
    case_result, _block = run_qc(case.seg_img, config)
    want = classify_label_outcomes(expected, case_result, positive_severity=Severity.FLAG)
    assert len(want) == 3
    assert record.label_outcomes == want
    keys = [(o.label, o.failure_mode) for o in record.label_outcomes]
    assert keys == sorted(keys)


def test_ac8_one_mode_record_keeps_its_key_set():
    record = _one_mode_cohort().cases[0]
    assert set(record.to_dict()) == {
        "case_id",
        "outcome",
        "overlap",
        "feature_match",
        "candidate_present",
        "subject",
        "metadata",
        "per_mode",
    }


def test_ac9_per_mode_label_sensitivity():
    records = _cohort().cases
    metrics = compute_cohort_metrics(_cohort())
    pairs = [o for r in records for o in r.label_outcomes if o.failure_mode != 0]
    modes = sorted({o.failure_mode for o in pairs})
    assert len(modes) >= 2
    per_mode = metrics.label_metrics.per_mode
    assert [e.failure_mode for e in per_mode] == modes
    for entry in per_mode:
        of_mode = [o for o in pairs if o.failure_mode == entry.failure_mode]
        detected = [o for o in of_mode if o.detected]
        assert entry.n_labels == len(of_mode)
        assert entry.n_detected == len(detected)
        assert entry.sensitivity == len(detected) / len(of_mode)


def test_ac10_clean_label_false_positives():
    records = _cohort().cases
    label_metrics = compute_cohort_metrics(_cohort()).label_metrics
    clean = [o for r in records for o in r.label_outcomes if o.failure_mode == 0]
    flagged = [o for o in clean if o.flagged]
    assert clean
    assert label_metrics.n_clean_labels == len(clean)
    assert label_metrics.n_clean_labels_flagged == len(flagged)
    assert label_metrics.clean_label_false_positive_rate == len(flagged) / len(clean)


def test_ac11_one_mode_cohort_metrics_keep_their_key_set():
    metrics = compute_cohort_metrics(_one_mode_cohort())
    assert set(metrics.to_dict()) == {
        "counts",
        "false_positive_rate",
        "sensitivity",
        "specificity",
        "per_mode",
        "dice_vs_flag",
        "feature_divergence_vs_flag",
        "n_cases",
    }


def test_ac12_report_carries_label_metrics():
    metrics = compute_cohort_metrics(_cohort())
    provenance = EvaluationProvenance(
        cohort_id="ac12",
        cohort_size=metrics.n_cases,
        config_version=bundled_default_config().schema_version,
        build_date="2026-10-18",
    )
    report = build_evaluation_report(metrics, provenance)
    assert metrics.to_dict()["label_metrics"] is not None
    assert report["metrics"]["label_metrics"] == metrics.to_dict()["label_metrics"]


# =========================================================================== #
# Adversarial cases named by the Testing Strategy
# =========================================================================== #


def test_case_level_finding():
    multi = _multi_mode_detector()
    outcomes = classify_label_outcomes(
        label_mode_expectation([(1, 0), (2, 0)]), _result(_finding(multi, set()))
    )
    assert len(outcomes) == 2
    assert [o.flagged for o in outcomes] == [False, False]


def test_unreviewed_label():
    multi = _multi_mode_detector()
    expected = label_mode_expectation([(1, 0)])
    with_stray = classify_label_outcomes(expected, _result(_finding(multi, {9})))
    without = classify_label_outcomes(expected, _result())
    assert [(o.label, o.failure_mode) for o in with_stray] == [(1, 0)]
    assert with_stray == without
    stray_metrics = compute_label_metrics([SimpleNamespace(label_outcomes=with_stray)])
    assert stray_metrics.n_clean_labels == 1
    assert stray_metrics.n_clean_labels_flagged == 0
    assert stray_metrics == compute_label_metrics(
        [SimpleNamespace(label_outcomes=without)]
    )


def test_wrong_mode_detector():
    single = _single_mode_detector()
    mode = _wrong_mode(single)
    (outcome,) = classify_label_outcomes(
        label_mode_expectation([(3, mode)]), _result(_finding(single, {3}))
    )
    assert outcome.flagged is True
    assert outcome.detected is False


def test_multi_mode_detector():
    multi = _multi_mode_detector()
    pairs = [(3, mode) for mode in multi[2]]
    outcomes = classify_label_outcomes(
        label_mode_expectation(pairs), _result(_finding(multi, {3}))
    )
    assert len(outcomes) == len(multi[2]) >= 2
    assert [o.detected for o in outcomes] == [True] * len(outcomes)


def test_duplicate_pair():
    mode = _MODES[0]
    expected = label_mode_expectation([(3, mode), (3, mode)])
    assert expected["label_modes"] == [[3, mode]]
    outcomes = classify_label_outcomes(
        {"label_modes": [[3, mode], [3, mode]]}, _result()
    )
    assert len(outcomes) == 1
    metrics = compute_label_metrics([SimpleNamespace(label_outcomes=outcomes)])
    assert [(e.failure_mode, e.n_labels) for e in metrics.per_mode] == [(mode, 1)]


def test_severity_threshold():
    multi = _multi_mode_detector()
    expected = label_mode_expectation([(3, 0)])
    result = _result(_finding(multi, {3}, severity=Severity.FLAG))
    (at_flag,) = classify_label_outcomes(expected, result)
    (at_fail,) = classify_label_outcomes(
        expected, result, positive_severity=Severity.FAIL
    )
    assert at_flag.flagged is True
    assert at_fail.flagged is False


def test_helper_validates():
    with pytest.raises(FacetInputError):
        label_mode_expectation([(1, _UNKNOWN_MODE)])


def test_duck_typed_records():
    records = [
        SimpleNamespace(
            **{
                f.name: getattr(r, f.name)
                for f in dataclasses.fields(r)
                if f.name != "label_outcomes"
            }
        )
        for r in _one_mode_cohort().cases
    ]
    assert all(not hasattr(r, "label_outcomes") for r in records)
    metrics = compute_cohort_metrics(SimpleNamespace(cases=records))
    assert metrics.label_metrics is None
