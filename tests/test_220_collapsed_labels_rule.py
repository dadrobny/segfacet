"""Tests for item 220 -- a collapsed label set no longer passes silently
(the ``collapsed_labels`` rule, failure mode 13).

Covers Acceptance Criteria AC1-AC12, plus exactly the five adversarial cases
the Testing Strategy names: ``border-touching-pair-survives-the-runner``,
``triple-coincidence-one-finding-per-pair``, ``non-adjacent-pair-is-judged``,
``malformed-centroid-skipped-not-raised`` and ``unknown-severity-raises``.

Every fixture fact a test relies on (a centroid distance, the label pair
``stage3_unavailable`` names) is recomputed from the extracted record and
asserted as a precondition.
"""

from __future__ import annotations

import copy
import dataclasses
import math
import re

import pytest

import segfacet.heuristics  # noqa: F401 -- registers every rule
from segfacet import traceability
from segfacet.catalogue import build_catalogue, iter_leaf_paths
from segfacet.config import bundled_default_config
from segfacet.failure_modes import SPECIFICATION, derive_status
from segfacet.heuristics.fov import border_touching_labels
from segfacet.heuristics.rule import get_rule, iter_rules
from segfacet.heuristics.runner import run_rules
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image

from synthetic import make_labelmap
from test_129_coincident_centroids_and_held_out_floor import (
    _coincident_label_map,
    _triple_coincident_label_map,
)

_RULE_ID = "collapsed_labels"

# Mode 13's definition as shipped before item 220 (base-branch source).
_SHIPPED_MODE_13_DEFINITION = (
    "Decidable on centroids alone: two or more labels' centroids lie "
    "closer together than a fraction of the expected inter-vertebral "
    "spacing, so distinct levels are placed on (nearly) the same "
    "vertebra. When centroids coincide exactly the Stage 3 spline fit "
    "cannot be computed, the record carries a stage3_unavailable reason "
    "instead of a stage3 block, every stage3-reading rule "
    "short-circuits and no finding of any kind is raised: the case "
    "passes silently (carried defect, item 129, 2026-08-31)."
)


# =========================================================================== #
# Helpers
# =========================================================================== #


def _near_label_map(close_a: int, close_b: int, far: int):
    """Labels ``close_a`` / ``close_b`` interleave in x (0.8 mm between their
    centroids, no other coordinate differs); ``far`` sits 15 mm away in z."""
    blocks = {
        close_b: ((3, 11), (5, 15), (10, 30)),
        close_a: ((5, 8), (5, 15), (10, 30)),
        far: ((5, 15), (5, 15), (32, 38)),
    }
    return make_labelmap(shape=(20, 20, 40), blocks=blocks, spacing=(1.0, 1.0, 1.0))


def _centroids(record):
    out = {}
    for key, entry in record["per_label"].items():
        out[int(key)] = entry["centroid"]["centroid_mm"]
    return out


def _close_pairs(record, limit_mm):
    cents = _centroids(record)
    labels = sorted(cents)
    return {
        frozenset((a, b)): math.dist(cents[a], cents[b])
        for i, a in enumerate(labels)
        for b in labels[i + 1:]
        if math.dist(cents[a], cents[b]) < limit_mm
    }


def _near_record(close_a=21, close_b=22, far=23):
    record = extract_feature_record(
        _near_label_map(close_a, close_b, far), bundled_default_config()
    )
    assert "stage3_unavailable" not in record
    pairs = _close_pairs(record, 2.0)
    assert list(pairs) == [frozenset((close_a, close_b))], pairs
    assert 0.0 < pairs[frozenset((close_a, close_b))] < 2.0
    return record, pairs[frozenset((close_a, close_b))]


def _coincident_record():
    record = extract_feature_record(_coincident_label_map(), bundled_default_config())
    assert isinstance(record["stage3_unavailable"], dict)
    return record


def _with_rule_config(config, rule_id, entry):
    rules = dict(config.rules)
    rules[rule_id] = {**rules.get(rule_id, {}), **entry}
    return dataclasses.replace(config, rules=rules)


def _only_collapsed_labels_config():
    config = bundled_default_config()
    for rule in iter_rules():
        if rule.rule_id != _RULE_ID:
            config = _with_rule_config(config, rule.rule_id, {"enabled": False})
    return config


def _rule_ids(findings):
    return {f.rule_id for f in findings}


@pytest.fixture(scope="module")
def raw_matrix():
    return traceability.build_matrix()


# =========================================================================== #
# AC1-AC3: the coincident case
# =========================================================================== #


def test_ac1_exact_coincidence_fires_once_on_the_named_pair():
    record = _coincident_record()
    findings = get_rule(_RULE_ID).evaluate(record, bundled_default_config())
    assert {(f.detector_id, f.labels) for f in findings} == {
        ("coincident_centroids", frozenset(record["stage3_unavailable"]["labels"]))
    }
    assert len(findings) == 1


def test_ac2_coincident_finding_names_the_reason():
    record = _coincident_record()
    (finding,) = get_rule(_RULE_ID).evaluate(record, bundled_default_config())
    assert record["stage3_unavailable"]["reason"] in finding.reason
    assert record["stage3_unavailable"]["detail"] in finding.reason


def test_ac3_collapsed_case_is_not_a_pass():
    config = _only_collapsed_labels_config()
    without_rule = _with_rule_config(config, _RULE_ID, {"enabled": False})
    baseline, _ = run_qc(_coincident_label_map(), without_rule)
    assert baseline.verdict.overall.label == "pass"
    result, _ = run_qc(_coincident_label_map(), config)
    assert result.verdict.overall.label == "flagged-for-review"


# =========================================================================== #
# AC4-AC5: the near-coincident case
# =========================================================================== #


def test_ac4_near_coincident_pair_fires():
    record, _ = _near_record()
    findings = get_rule(_RULE_ID).evaluate(record, bundled_default_config())
    assert len(findings) == 1
    assert findings[0].detector_id == "near_coincident_centroids"
    assert findings[0].labels == frozenset({21, 22})


def test_ac5_tolerance_is_the_config_parameter():
    record, distance = _near_record()
    rule = get_rule(_RULE_ID)
    key = "max_centroid_distance_mm"
    halved = _with_rule_config(
        bundled_default_config(), _RULE_ID, {"params": {key: distance / 2}}
    )
    assert rule.evaluate(record, halved) == []
    exact = _with_rule_config(
        bundled_default_config(), _RULE_ID, {"params": {key: distance}}
    )
    findings = rule.evaluate(record, exact)
    assert [(f.detector_id, f.labels) for f in findings] == [
        ("near_coincident_centroids", frozenset({21, 22}))
    ]


# =========================================================================== #
# AC6-AC7: nothing else fires
# =========================================================================== #


def test_ac6_stage3_present_and_no_close_pair_fires_nothing():
    case = next(c for c in load_manifest()["cases"] if c["case_id"] == "clean_control")
    record = extract_feature_record(loaded_seg_image(case), bundled_default_config())
    assert "stage3_unavailable" not in record
    assert get_rule(_RULE_ID).evaluate(record, bundled_default_config()) == []


def test_ac7_no_committed_corpus_case_fires_the_rule(raw_matrix):
    cases = raw_matrix.conformance.cases
    assert cases, "expected a non-empty conformance report"
    for case in cases:
        assert _RULE_ID not in case.measured_firing, (case.corpus, case.case_id)


# =========================================================================== #
# AC8-AC10: the failure-mode specification
# =========================================================================== #


def test_ac8_rule_declares_mode_13_and_specification_carries_the_edge():
    declaration = get_rule(_RULE_ID).mode_declaration
    assert declaration.modes == (13,)
    edges = SPECIFICATION[13].intended_rules
    assert len(edges) == 1
    assert edges[0].rule_id == _RULE_ID
    assert edges[0].evidence_rung == "needs-real-data"
    assert edges[0].detector_ids == tuple(d.detector_id for d in declaration.detectors)


def test_ac9_mode_13_derives_implemented():
    assert derive_status(SPECIFICATION[13]) == "implemented"


def test_ac10_definition_is_appended_to_not_rewritten():
    definition = SPECIFICATION[13].definition
    assert definition.startswith(_SHIPPED_MODE_13_DEFINITION)
    tail = definition[len(_SHIPPED_MODE_13_DEFINITION):]
    assert _RULE_ID in tail
    assert re.search(r"\d{4}-\d{2}-\d{2}", tail)


# =========================================================================== #
# AC11-AC12: the catalogue
# =========================================================================== #


def _stage3_unavailable_entries():
    return [
        e for e in build_catalogue(strict=True).entries
        if e.path.startswith("stage3_unavailable.")
    ]


def test_ac11_catalogue_lists_stage3_unavailable():
    expected = {
        p for p in iter_leaf_paths(_coincident_record())
        if p.startswith("stage3_unavailable.")
    }
    assert expected, "the coincident record yielded no stage3_unavailable leaf"
    assert {e.path for e in _stage3_unavailable_entries()} == expected


def test_ac12_every_stage3_unavailable_entry_is_documented():
    entries = _stage3_unavailable_entries()
    assert entries
    for entry in entries:
        assert entry.documented is True, entry.path
        assert entry.measures, entry.path
        assert entry.computation, entry.path


# =========================================================================== #
# Adversarial cases named by the Testing Strategy
# =========================================================================== #


def test_border_touching_pair_survives_the_runner():
    blocks = {
        21: ((0, 10), (5, 15), (10, 30)),
        22: ((3, 7), (5, 15), (10, 30)),
    }
    img = make_labelmap(shape=(20, 20, 40), blocks=blocks, spacing=(1.0, 1.0, 1.0))
    record = extract_feature_record(img, bundled_default_config())
    assert 21 in border_touching_labels(record)
    assert isinstance(record["stage3_unavailable"], dict)
    findings = run_rules(record, bundled_default_config())
    assert any(
        f.rule_id == _RULE_ID and f.labels == frozenset({21, 22}) for f in findings
    )


def test_triple_coincidence_one_finding_per_pair():
    record = extract_feature_record(
        _triple_coincident_label_map(), bundled_default_config()
    )
    named = frozenset(record["stage3_unavailable"]["labels"])
    findings = get_rule(_RULE_ID).evaluate(record, bundled_default_config())
    assert len(findings) == 3
    assert len({f.labels for f in findings}) == 3
    by_detector = {}
    for f in findings:
        by_detector.setdefault(f.detector_id, []).append(f.labels)
    assert by_detector["coincident_centroids"] == [named]
    assert len(by_detector["near_coincident_centroids"]) == 2
    assert named not in by_detector["near_coincident_centroids"]


def test_non_adjacent_pair_is_judged():
    record, _ = _near_record(close_a=21, close_b=23, far=22)
    findings = get_rule(_RULE_ID).evaluate(record, bundled_default_config())
    assert [(f.detector_id, f.labels) for f in findings] == [
        ("near_coincident_centroids", frozenset({21, 23}))
    ]


def test_malformed_centroid_skipped_not_raised():
    record, _ = _near_record()
    broken = copy.deepcopy(record)
    far_key = next(k for k in broken["per_label"] if int(k) == 23)
    del broken["per_label"][far_key]["centroid"]
    findings = get_rule(_RULE_ID).evaluate(broken, bundled_default_config())
    assert [(f.detector_id, f.labels) for f in findings] == [
        ("near_coincident_centroids", frozenset({21, 22}))
    ]


def test_unknown_severity_raises():
    record = _coincident_record()
    config = _with_rule_config(
        bundled_default_config(), _RULE_ID, {"params": {"severity": "not-a-severity"}}
    )
    with pytest.raises(ValueError):
        get_rule(_RULE_ID).evaluate(record, config)
