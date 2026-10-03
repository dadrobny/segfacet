"""Tests for item 208 -- mode 3's ``split_fragment`` rule: a label that both
touches a neighbouring label over more than a tenth of its surface and is less
than half the median volume of its neighbouring labels.

Covers Acceptance Criteria AC1-AC3: one test per AC, read live off the
committed manifests, the pipeline, ``failure_modes`` and ``traceability`` --
never a hand-built record.

Plus exactly the four adversarial cases the Testing Strategy names:
``remainder-beside-enlarged-receiver-silent``, ``coccygeal-label-not-judged``,
``contact-threshold-read-from-own-section`` and
``size-threshold-read-from-own-section``.
"""

from __future__ import annotations

import copy

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes, traceability
from segfacet.config import bundled_default_config
from segfacet.heuristics.split_fragment import SplitFragmentRule
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.component_shape import SplitPerturbation
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import load_intensity_manifest
from segfacet.synth.regression import (
    intensity_pipeline_findings,
    loaded_seg_image,
    pipeline_findings,
)


def _split_own_label_case() -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == "split_own_label"]
    assert len(matches) == 1, matches
    return matches[0]


def _split_fragment_findings(findings) -> list:
    return [f for f in findings if f.rule_id == "split_fragment"]


def _label_entry(record: dict, label: int) -> dict:
    keys = [k for k in record["per_label"] if int(k) == label]
    assert len(keys) == 1, keys
    return record["per_label"][keys[0]]


# =========================================================================== #
# AC1: split_fragment fires on the cap and nowhere else
# =========================================================================== #


def test_ac1_split_fragment_fires_on_the_cap_and_nowhere_else():
    fired = set()
    n_cases = 0
    for case in load_manifest()["cases"]:
        n_cases += 1
        for f in _split_fragment_findings(pipeline_findings(case)):
            fired.update(("geometric", case["case_id"], label) for label in f.labels)
    for case in load_intensity_manifest()["cases"]:
        n_cases += 1
        for f in _split_fragment_findings(intensity_pipeline_findings(case)):
            fired.update(("intensity", case["case_id"], label) for label in f.labels)
    assert n_cases > 0
    assert fired == {("geometric", "split_own_label", 23)}


# =========================================================================== #
# AC2: the detector serves mode 3 alone
# =========================================================================== #


def test_ac2_the_detector_serves_mode_3_alone():
    assert failure_modes.modes_for_detector("split_fragment", "split_fragment") == (3,)


# =========================================================================== #
# AC3: mode 3 meets bar conditions 1-5 live
# =========================================================================== #


def test_ac3_mode_3_meets_bar_conditions_1_to_5_live():
    conditions = traceability.bar_conditions(3)
    assert len(conditions) == 5, conditions
    assert tuple(c.met for c in conditions) == (True, True, True, True, True)


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_remainder_beside_enlarged_receiver_silent():
    result = SplitPerturbation(
        target_label=23, neighbour_label=24, donated_fraction=0.4
    ).apply(build_clean_spine().seg_img, 0)
    config = bundled_default_config()

    record = extract_feature_record(result.labelmap, config)
    contact = _label_entry(record, 23)["components"]["label_contact_fraction"]
    assert contact > 0.1, contact

    case_result, _block = run_qc(result.labelmap, config)
    assert _split_fragment_findings(case_result.findings) == []


def test_coccygeal_label_not_judged():
    config = bundled_default_config()
    record = extract_feature_record(loaded_seg_image(_split_own_label_case()), config)

    control = SplitFragmentRule().evaluate(record, config)
    assert len(control) == 1, control
    assert list(control[0].labels) == [23]

    coccyx = copy.deepcopy(record)
    _label_entry(coccyx, 23)["level_name"] = "Cocc"
    assert SplitFragmentRule().evaluate(coccyx, config) == []


def test_contact_threshold_read_from_own_section():
    config = bundled_default_config()
    config.rules.setdefault("split_fragment", {}).setdefault("params", {})[
        "contact_fraction_threshold"
    ] = 1000.0
    case_result, _block = run_qc(loaded_seg_image(_split_own_label_case()), config)
    assert _split_fragment_findings(case_result.findings) == []


def test_size_threshold_read_from_own_section():
    config = bundled_default_config()
    config.rules.setdefault("split_fragment", {}).setdefault("params", {})[
        "size_ratio_threshold"
    ] = 0.0
    case_result, _block = run_qc(loaded_seg_image(_split_own_label_case()), config)
    assert _split_fragment_findings(case_result.findings) == []
