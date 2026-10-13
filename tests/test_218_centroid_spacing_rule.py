"""Tests for item 218 -- one ``centroid_spacing`` rule for modes 2 and 6.

One test per Acceptance Criterion (``test_ac1`` .. ``test_ac9``), read live off
the committed manifests, the pipeline and ``failure_modes``, plus exactly the
six adversarial cases the Testing Strategy names: ``distant-relabel-silent``,
``fused-label-not-reported-as-missing``, ``end-gap-judged-on-one-neighbour``,
``two-labels-not-judged``, ``missing-path-u-not-judged`` and
``gap-threshold-read-from-own-section``.
"""

from __future__ import annotations

import copy
import math

import nibabel as nib
import numpy as np

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.heuristics.centroid_spacing import CentroidSpacingRule
from segfacet.heuristics.rule import iter_rules
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import load_intensity_manifest
from segfacet.synth.regression import (
    intensity_pipeline_findings,
    loaded_seg_image,
    pipeline_findings,
    pipeline_verdict_label,
)


def _case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _record(case_id: str) -> dict:
    return extract_feature_record(
        loaded_seg_image(_case(case_id)), bundled_default_config()
    )


def _clean_record() -> dict:
    return extract_feature_record(
        build_clean_spine().seg_img, bundled_default_config()
    )


def _evaluate(record: dict) -> list:
    return CentroidSpacingRule().evaluate(record, bundled_default_config())


def _label_entry(record: dict, label: int) -> dict:
    keys = [k for k in record["per_label"] if int(k) == label]
    assert len(keys) == 1, (label, list(record["per_label"]))
    return record["per_label"][keys[0]]


def _centroid(record: dict, label: int) -> np.ndarray:
    return np.asarray(_label_entry(record, label)["centroid"]["centroid_mm"][:3], float)


def _triples(findings, case_id: str) -> set:
    return {
        (case_id, f.detector_id, f.labels)
        for f in findings
        if f.rule_id == "centroid_spacing"
    }


# =========================================================================== #
# AC1-AC9
# =========================================================================== #


def test_ac1_the_rule_fires_exactly_where_both_detectors_are_expected():
    fired = set()
    n_cases = 0
    for case in load_manifest()["cases"]:
        n_cases += 1
        fired |= _triples(pipeline_findings(case), case["case_id"])
    for case in load_intensity_manifest()["cases"]:
        n_cases += 1
        fired |= _triples(intensity_pipeline_findings(case), case["case_id"])
    assert n_cases > 0
    assert fired == {
        ("fuse_adjacent", "fused_label", frozenset({22})),
        ("fuse_separate", "fused_label", frozenset({22})),
        ("remove_level", "missing_level", frozenset({21, 23})),
        ("remove_level_relabel", "missing_level", frozenset({21, 22})),
    }


def test_ac2_missing_level_is_attributed_to_mode_6():
    assert failure_modes.modes_for_detector("centroid_spacing", "missing_level") == (6,)


def test_ac3_fused_label_stays_attributed_to_mode_2():
    assert failure_modes.modes_for_detector("centroid_spacing", "fused_label") == (2,)


def test_ac4_the_rule_declares_modes_2_and_6():
    rules = [r for r in iter_rules() if r.rule_id == "centroid_spacing"]
    assert len(rules) == 1, rules
    assert rules[0].mode_declaration.modes == (2, 6)


def test_ac5_no_rule_is_registered_as_fused_label():
    rule_ids = [r.rule_id for r in iter_rules()]
    assert rule_ids
    assert "fused_label" not in rule_ids


def test_ac6_mode_6_derives_validated():
    assert (
        failure_modes.derive_status(failure_modes.SPECIFICATION[6]) == "validated"
    )


def test_ac7_remove_level_designates_the_rule():
    assert _case("remove_level")["expected_rule_ids"] == ["centroid_spacing"]


def test_ac8_remove_level_relabel_designates_the_rule():
    assert _case("remove_level_relabel")["expected_rule_ids"] == ["centroid_spacing"]


def test_ac9_remove_level_relabel_no_longer_passes():
    assert (
        pipeline_verdict_label(_case("remove_level_relabel")) == "flagged-for-review"
    )


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_distant_relabel_silent():
    img = build_clean_spine().seg_img
    data = np.asarray(img.dataobj).copy()
    is20, is23 = data == 20, data == 23
    assert is20.any() and is23.any()
    data[is20], data[is23] = 23, 20
    swapped = nib.Nifti1Image(data, img.affine, img.header)

    case_result, _block = run_qc(swapped, bundled_default_config())
    assert [f for f in case_result.findings if f.rule_id == "centroid_spacing"] == []


def test_fused_label_not_reported_as_missing():
    record = copy.deepcopy(_record("fuse_separate"))
    c21, c23 = _centroid(record, 21), _centroid(record, 23)
    pitch = float(math.dist(_centroid(record, 20), c21))
    direction = (c23 - c21) / np.linalg.norm(c23 - c21)
    _label_entry(record, 22)["centroid"]["centroid_mm"] = list(c21 + pitch * direction)

    findings = _evaluate(record)
    assert [f.labels for f in findings if f.detector_id == "fused_label"] == [
        frozenset({22})
    ]
    assert [f for f in findings if f.detector_id == "missing_level"] == []


def test_end_gap_judged_on_one_neighbour():
    record = copy.deepcopy(_clean_record())
    c23, c24 = _centroid(record, 23), _centroid(record, 24)
    _label_entry(record, 24)["centroid"]["centroid_mm"] = list(c24 + (c24 - c23))

    findings = _evaluate(record)
    assert len(findings) == 1, findings
    assert findings[0].detector_id == "missing_level"
    assert findings[0].labels == frozenset({23, 24})


def test_two_labels_not_judged():
    record = copy.deepcopy(_clean_record())
    keep = sorted(int(k) for k in record["per_label"])[:2]
    assert len(keep) == 2, keep
    record["per_label"] = {
        k: v for k, v in record["per_label"].items() if int(k) in keep
    }
    assert _evaluate(record) == []


def test_missing_path_u_not_judged():
    record = copy.deepcopy(_record("remove_level_relabel"))
    curve = _label_entry(record, 22)["curve"]
    assert "path_u" in curve, list(curve)
    del curve["path_u"]
    assert _evaluate(record) == []


def test_gap_threshold_read_from_own_section():
    case = _case("remove_level_relabel")
    config = bundled_default_config()
    control, _block = run_qc(loaded_seg_image(case), config)
    assert [f.detector_id for f in control.findings if f.rule_id == "centroid_spacing"] == [
        "missing_level"
    ]

    config.rules.setdefault("centroid_spacing", {}).setdefault("params", {})[
        "gap_ratio_threshold"
    ] = 1000.0
    case_result, _block = run_qc(loaded_seg_image(case), config)
    assert [f for f in case_result.findings if f.detector_id == "missing_level"] == []
