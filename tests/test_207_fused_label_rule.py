"""Tests for item 207 -- mode 2's ``fused_label`` rule: a label that is both
large against its adjacent labels and flanked by wide centroid spacing.

Covers Acceptance Criteria AC1-AC2: one test per AC, read live off the
committed manifests, the pipeline and ``failure_modes`` -- never a hand-built
record.

Plus exactly the four adversarial cases the Testing Strategy names:
``caudal-end-fuse-fires``, ``sacral-label-not-judged``,
``size-threshold-read-from-own-section`` and
``spacing-threshold-read-from-own-section``.
"""

from __future__ import annotations

import copy

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.heuristics.centroid_spacing import CentroidSpacingRule  # item 218 (2026-10-13): renamed from FusedLabelRule
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.component_shape import FusePerturbation
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import load_intensity_manifest
from segfacet.synth.regression import (
    intensity_pipeline_findings,
    loaded_seg_image,
    pipeline_findings,
)


def _fuse_separate_case() -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == "fuse_separate"]
    assert len(matches) == 1, matches
    return matches[0]


def _fused_label_findings(findings) -> list:
    # item 218 (2026-10-13): the rule is centroid_spacing, this detector fused_label.
    return [
        f
        for f in findings
        if f.rule_id == "centroid_spacing" and f.detector_id == "fused_label"
    ]


# =========================================================================== #
# AC1: fused_label fires on the two fused labels and nowhere else
# =========================================================================== #


def test_ac1_fused_label_fires_on_the_two_fused_labels_and_nowhere_else():
    fired = set()
    n_cases = 0
    for case in load_manifest()["cases"]:
        n_cases += 1
        for f in _fused_label_findings(pipeline_findings(case)):
            fired.update(("geometric", case["case_id"], label) for label in f.labels)
    for case in load_intensity_manifest()["cases"]:
        n_cases += 1
        for f in _fused_label_findings(intensity_pipeline_findings(case)):
            fired.update(("intensity", case["case_id"], label) for label in f.labels)
    assert n_cases > 0
    assert fired == {
        ("geometric", "fuse_adjacent", 22),
        ("geometric", "fuse_separate", 22),
    }


# =========================================================================== #
# AC2: the detector serves mode 2 alone
# =========================================================================== #


def test_ac2_the_detector_serves_mode_2_alone():
    # item 218 (2026-10-13): detector renamed fused_label -> centroid_spacing
    assert failure_modes.modes_for_detector("centroid_spacing", "fused_label") == (2,)


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_caudal_end_fuse_fires():
    result = FusePerturbation(target_label=23, neighbour_label=24, bridged=True).apply(
        build_clean_spine().seg_img, 0
    )
    case_result, _block = run_qc(result.labelmap, bundled_default_config())
    fired = _fused_label_findings(case_result.findings)
    assert len(fired) == 1, fired
    assert list(fired[0].labels) == [23]


def test_sacral_label_not_judged():
    config = bundled_default_config()
    record = extract_feature_record(loaded_seg_image(_fuse_separate_case()), config)

    control = CentroidSpacingRule().evaluate(record, config)
    assert len(control) == 1, control
    assert list(control[0].labels) == [22]

    sacral = copy.deepcopy(record)
    keys = [k for k in sacral["per_label"] if int(k) == 22]
    assert len(keys) == 1, keys
    sacral["per_label"][keys[0]]["level_name"] = "S1"
    assert CentroidSpacingRule().evaluate(sacral, config) == []


def test_size_threshold_read_from_own_section():
    config = bundled_default_config()
    config.rules.setdefault("centroid_spacing", {})  # item 218 (2026-10-13): renamed section
    config.rules["centroid_spacing"].setdefault("params", {})[
        "size_ratio_threshold"
    ] = 1000.0
    case_result, _block = run_qc(loaded_seg_image(_fuse_separate_case()), config)
    assert _fused_label_findings(case_result.findings) == []


def test_spacing_threshold_read_from_own_section():
    config = bundled_default_config()
    config.rules.setdefault("centroid_spacing", {})  # item 218 (2026-10-13): renamed section
    config.rules["centroid_spacing"].setdefault("params", {})[
        "spacing_ratio_threshold"
    ] = 1000.0
    case_result, _block = run_qc(loaded_seg_image(_fuse_separate_case()), config)
    assert _fused_label_findings(case_result.findings) == []
