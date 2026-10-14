"""Tests for item 223 -- path-aware rule-read attribution in the catalogue
(``segfacet.catalogue`` mechanism B).

Covers Acceptance Criteria AC1-AC3 (AC4 is carried by
``test_138_traceability_matrix.py``) and the Testing Strategy's three
adversarial cases (``unresolved-read-no-fallback``,
``seed-is-the-registered-class-only``, ``wildcard-is-one-segment``).
"""

from __future__ import annotations

import pytest

from segfacet.catalogue import build_catalogue
from segfacet.heuristics.rule import Rule, _RULES

_FEATURES = (
    "extent_x_mm",
    "extent_y_mm",
    "extent_z_mm",
    "physical_volume_mm3",
    "spline_offset_mm",
)


@pytest.fixture(scope="module")
def entries_by_path():
    return {e.path: e for e in build_catalogue(strict=True).entries}


@pytest.mark.parametrize("leaf", ("value", "percentile_rank"))
@pytest.mark.parametrize("feature", _FEATURES)
def test_ac1_reference_delta_out_of_range_reads_attributed(entries_by_path, feature, leaf):
    path = f"reference_delta.{{label}}.features.{feature}.{leaf}"
    assert path in entries_by_path, path
    assert "reference_delta" in entries_by_path[path].consuming_rules


def test_ac2_read_through_unrealised_block_stays_unattributed(entries_by_path):
    reference_paths = [p for p in entries_by_path if p.startswith("reference_delta.")]
    assert reference_paths, "precondition: reference_delta.* paths are catalogued"
    offenders = [
        p
        for p in reference_paths
        if "intensity_reference_delta" in entries_by_path[p].consuming_rules
    ]
    assert offenders == []


@pytest.mark.parametrize(
    "path",
    (
        "per_label.{label}.level_name",
        "per_label.{label}.geometry.touches_superior",
        "per_label.{label}.geometry.touches_inferior",
    ),
)
def test_ac3_imported_helper_reads_attributed_to_caller(entries_by_path, path):
    assert path in entries_by_path, path
    assert "coverage" in entries_by_path[path].consuming_rules


def _static_paths(rule_cls_by_id):
    """Register ad-hoc rules, build, and return {rule_id: static-attributed paths}."""
    snapshot = dict(_RULES)
    try:
        for rule_id, cls in rule_cls_by_id.items():
            _RULES[rule_id] = cls()
        cat = build_catalogue(strict=False)
    finally:
        _RULES.clear()
        _RULES.update(snapshot)
    return {
        rule_id: {
            e.path for e in cat.entries if (rule_id, "static") in e.rule_evidence
        }
        for rule_id in rule_cls_by_id
    }


def test_unresolved_read_no_fallback():
    class _LocalDictRule(Rule):
        rule_id = "__item223_local_dict__"

        def evaluate(self, record, config):
            local = {"lower_pct": 1.0}
            _ = local["lower_pct"]
            return []

    paths = _static_paths({_LocalDictRule.rule_id: _LocalDictRule})
    assert paths[_LocalDictRule.rule_id] == set()


def test_seed_is_the_registered_class_only():
    class _FirstRule(Rule):
        rule_id = "__item223_first__"

        def evaluate(self, record, config):
            return []

    class _SecondRule(Rule):
        rule_id = "__item223_second__"

        def evaluate(self, record, config):
            _ = record.get("reference_delta", {}).get("lower_pct")
            return []

    paths = _static_paths(
        {_FirstRule.rule_id: _FirstRule, _SecondRule.rule_id: _SecondRule}
    )
    assert "reference_delta.lower_pct" in paths[_SecondRule.rule_id], "precondition"
    assert not any(p.startswith("reference_delta") for p in paths[_FirstRule.rule_id])


def test_wildcard_is_one_segment():
    class _WildcardRule(Rule):
        rule_id = "__item223_wildcard__"

        def evaluate(self, record, config):
            k = repr(config)
            name = repr(record)
            block = record.get("reference_delta", {}).get("per_label", {})
            _ = block.get(k, {}).get("features", {}).get(name, {}).get("value")
            return []

    paths = _static_paths({_WildcardRule.rule_id: _WildcardRule})
    expected = {f"reference_delta.{{label}}.features.{f}.value" for f in _FEATURES}
    assert paths[_WildcardRule.rule_id] == expected
