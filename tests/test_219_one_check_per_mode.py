"""Tests for item 219 -- one check per failure mode for label order and
label-set gaps.

Covers Acceptance Criteria AC1-AC13 from
``docs/aide/items/219-one-check-per-failure-mode-for-label-order-and-gaps.md``,
one test each, plus its two named adversarial cases:
``unrelated-pair-does-not-silence-transitional`` and
``pair-member-excluded-from-transitional``.
"""

from __future__ import annotations

import math

import segfacet.failure_modes as fm
from segfacet.config import bundled_default_config
from segfacet.feature_docs import STATUS_OVERRIDES
from segfacet.features.centroids import LabelCentroid
from segfacet.features.consistency import compute_monotonic_consistency
from segfacet.heuristics import get_rule, run_rules
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import load_intensity_manifest
from segfacet.synth.regression import intensity_pipeline_findings, pipeline_findings

_CFG = bundled_default_config()
_ORDER_RULES = {"mislabel", "sequence", "coverage"}
_LEVELS = ["T8", "T9", "T10", "T11", "T12", "L1", "L2", "L3", "L4", "L5"]


def _centroid(level_name: str, mm, label: int) -> LabelCentroid:
    return LabelCentroid(
        label=label,
        level_name=level_name,
        centroid_voxel=tuple(mm),
        centroid_mm=tuple(mm),
    )


def _spine_record(centroids) -> dict:
    """A spine record built from *centroids* (T8 -> L5 order); the pairs come
    from the producer, ``compute_monotonic_consistency``."""
    pairs = compute_monotonic_consistency(centroids, None).non_monotonic_pairs
    return {
        "per_label": {
            c.label: {
                "label": c.label,
                "level_name": c.level_name,
                "centroid": {"centroid_mm": list(c.centroid_mm)},
            }
            for c in centroids
        },
        "pairs": {"adjacent": {"non_monotonic_pairs": [list(p) for p in pairs]}},
    }


def _curved_spine() -> list:
    out = []
    for i, name in enumerate(_LEVELS):
        t = math.radians(-90 + 210 * i / 9)
        out.append(_centroid(name, (0.0, 60 * math.cos(t), 60 * math.sin(t)), i + 1))
    return out


def _reclined_spine() -> list:
    c, s = math.cos(math.radians(10)), math.sin(math.radians(10))
    out = []
    for i, name in enumerate(_LEVELS):
        t = math.radians(135 - 10 * i)
        y, z = 150 * math.cos(t), 150 * math.sin(t)
        out.append(_centroid(name, (0.0, y * c - z * s, y * s + z * c), 15 + i))
    return out


def _levels_record(levels_and_labels, pairs=None) -> dict:
    record = {
        "per_label": {
            label: {"label": label, "level_name": name}
            for name, label in levels_and_labels
        }
    }
    if pairs is not None:
        record["pairs"] = {"adjacent": {"non_monotonic_pairs": pairs}}
    return record


def _edge_pairs(mode_id: int) -> set:
    return {
        (edge.rule_id, detector_id)
        for edge in fm.SPECIFICATION[mode_id].intended_rules
        for detector_id in edge.detector_ids
    }


def _manifest_case(case_id: str) -> dict:
    return next(c for c in load_manifest()["cases"] if c["case_id"] == case_id)


# =========================================================================== #
# AC1-AC13
# =========================================================================== #


def test_ac1_mode_9_is_declared_against_one_detector():
    assert _edge_pairs(9) == {("mislabel", "ordering")}


def test_ac2_mode_10_is_declared_against_one_detector():
    assert _edge_pairs(10) == {("coverage", "missing_interior")}


def test_ac3_sequence_declares_only_transitional():
    declaration = get_rule("sequence").mode_declaration
    assert {d.detector_id for d in declaration.detectors} == {"transitional"}


def test_ac4_sequence_declares_mode_11_only():
    assert get_rule("sequence").mode_declaration.modes == (11,)


def test_ac5_count_shortfall_is_mode_less():
    detectors = {d.detector_id: d for d in get_rule("coverage").mode_declaration.detectors}
    assert detectors["count_shortfall"].mode_less_reason


def test_ac6_incomplete_span_is_mode_less():
    detectors = {d.detector_id: d for d in get_rule("coverage").mode_declaration.detectors}
    assert detectors["incomplete_span"].mode_less_reason


def test_ac7_sequence_opts_in_to_no_condition():
    assert get_rule("sequence").condition_opt_ins == ()


def test_ac8_a_curved_spine_fires_no_ordering_finding():
    findings = run_rules(_spine_record(_curved_spine()), _CFG)
    assert [f for f in findings if f.rule_id in _ORDER_RULES] == []


def test_ac9_a_reclined_spine_fires_no_ordering_finding():
    findings = run_rules(_spine_record(_reclined_spine()), _CFG)
    assert [f for f in findings if f.rule_id in _ORDER_RULES] == []


def test_ac10_the_order_rules_fire_exactly_where_expected():
    fired = set()
    for case in load_manifest()["cases"]:
        for f in pipeline_findings(case, _CFG):
            if f.rule_id in _ORDER_RULES:
                fired.add((case["case_id"], f.rule_id, f.detector_id, f.labels))
    for case in load_intensity_manifest()["cases"]:
        for f in intensity_pipeline_findings(case, _CFG):
            if f.rule_id in _ORDER_RULES:
                fired.add((case["case_id"], f.rule_id, f.detector_id, f.labels))
    assert fired == {
        ("relabel_swap", "mislabel", "ordering", frozenset({21, 22})),
        ("sequence_break", "mislabel", "ordering", frozenset({20, 28})),
        ("remove_level", "coverage", "missing_interior", frozenset()),
    }


def test_ac11_sequence_break_designates_mislabel():
    assert _manifest_case("sequence_break")["expected_rule_ids"] == ["mislabel"]


def test_ac12_sequence_break_names_the_ordering_pair():
    assert sorted(_manifest_case("sequence_break")["expected_labels"]) == [20, 28]


def test_ac13_the_override_carries_the_owners_line():
    assert STATUS_OVERRIDES["case.curve.is_monotonic"] == (
        "retune",
        "Should be wired into the sequence rule directly; "
        "sequence-related checks should typically verify order along the "
        "spline parameter, not only label order. "
        "2026-10-12: Done: order is judged along the label-free path by "
        "`mislabel`, items 210/219.",
    )


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_unrelated_pair_does_not_silence_transitional():
    record = _levels_record(
        [("T10", 17), ("T11", 18), ("L1", 20), ("L2", 21), ("L3", 22)],
        pairs=[["L2", "L3"]],
    )
    findings = get_rule("sequence").evaluate(record, _CFG)
    assert [(f.detector_id, f.labels) for f in findings] == [
        ("transitional", frozenset({18}))
    ]


def test_pair_member_excluded_from_transitional():
    record = _levels_record(
        [("L1", 20), ("L2", 21), ("L3", 22), ("L4", 23), ("T13", 28)],
        pairs=[["T13", "L1"]],
    )
    assert list(get_rule("sequence").evaluate(record, _CFG)) == []
