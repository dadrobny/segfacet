"""Tests for item 204 -- validate Stage 33 (corpus and rule re-grounding).

Per the item spec's Testing Strategy this module carries exactly one AC test
(AC8) plus the one named adversarial case, ``skipped-level-is-seen``. Every
other criterion is a Replay criterion, executed from a fresh clone and
recorded in the item's Decisions log, not tested here.

The missing-level detector set is derived from the live rule registry and
``failure_modes.modes_for_detector`` (A3); no rule id or detector id is
written as a literal.
"""

from __future__ import annotations

import pytest

from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.heuristics import iter_rules, run_rules
from segfacet.pipeline import extract_feature_record

from synthetic import make_labelmap

# The two modes that describe an absent level (A3): 6 (vertebra not
# segmented) and 10 (skipped level label).
_ABSENT_LEVEL_MODES = {6, 10}

# Item 186's six-block T12 map: labels 19-24 (T12, L1-L5), no label 28 (T13).
_T12_MAP_BLOCKS = {
    19: ((0, 4), (0, 4), (0, 2)),   # T12
    20: ((0, 4), (0, 4), (4, 6)),   # L1
    21: ((0, 4), (0, 4), (8, 10)),  # L2
    22: ((0, 4), (0, 4), (12, 14)),  # L3
    23: ((0, 4), (0, 4), (16, 18)),  # L4
    24: ((0, 4), (0, 4), (20, 22)),  # L5
}


def _record(blocks):
    seg_img = make_labelmap(shape=(4, 4, 24), blocks=blocks)
    return extract_feature_record(seg_img, bundled_default_config())


def _missing_level_detectors():
    """Every registered ``(rule_id, detector_id)`` serving an absent-level mode."""
    return {
        (rule.rule_id, detector.detector_id)
        for rule in iter_rules()
        if rule.mode_declaration is not None
        for detector in rule.mode_declaration.detectors
        if _ABSENT_LEVEL_MODES.intersection(
            failure_modes.modes_for_detector(rule.rule_id, detector.detector_id)
        )
    }


def _missing_level_findings(record):
    detectors = _missing_level_detectors()
    assert detectors, "no registered detector serves an absent-level mode"
    findings = run_rules(record, bundled_default_config())
    return [f for f in findings if (f.rule_id, f.detector_id) in detectors]


@pytest.fixture(scope="module")
def t12_map_record():
    return _record(_T12_MAP_BLOCKS)


def test_ac8_t12_l1_map_no_missing_level_finding(t12_map_record):
    assert _missing_level_findings(t12_map_record) == []


def test_skipped_level_is_seen():
    """Guards a predicate that passes vacuously: one that reads the wrong
    attribute, takes ``None`` for ``detector_id``, or derives an empty set."""
    blocks = {label: box for label, box in _T12_MAP_BLOCKS.items() if label != 22}
    assert _missing_level_findings(_record(blocks))
