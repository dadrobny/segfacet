"""Tests for item 237 -- dead code and stale comments left by items 210, 223
and 227.

Covers Acceptance Criteria AC1-AC3: the dead ``coverage`` helper is gone, every
rule attribution is tagged ``observed`` or ``static``, and a static read is
attributed to exactly the path it names.
"""

from __future__ import annotations

import pytest

import segfacet.heuristics.coverage as coverage_module
from segfacet.catalogue import build_catalogue
from segfacet.heuristics.rule import Rule, _RULES


@pytest.fixture(scope="module")
def strict_catalogue():
    return build_catalogue(strict=True)


def test_ac1_dead_coverage_helper_is_gone():
    assert not hasattr(coverage_module, "_find_entry_by_level_name")


def test_ac2_every_rule_attribution_is_observed_or_static(strict_catalogue):
    tags = {
        evidence
        for entry in strict_catalogue.entries
        for _rule_id, evidence in entry.rule_evidence
    }
    assert tags, "precondition: the catalogue carries rule attributions"
    assert tags <= {"observed", "static"}


def test_ac3_static_read_attributed_to_exactly_the_path_it_names(strict_catalogue):
    value_paths = [e.path for e in strict_catalogue.entries if e.path.endswith(".value")]
    assert len(value_paths) > 1, "precondition: `.value` is not a unique last segment"

    class _VolumeRule(Rule):
        rule_id = "__item237_volume__"

        def evaluate(self, record, config):
            k = repr(config)
            _ = (
                record.get("reference_delta", {})
                .get("per_label", {})
                .get(k, {})
                .get("features", {})
                .get("physical_volume_mm3", {})
                .get("value")
            )
            return []

    snapshot = dict(_RULES)
    try:
        _RULES[_VolumeRule.rule_id] = _VolumeRule()
        cat = build_catalogue(strict=False)
    finally:
        _RULES.clear()
        _RULES.update(snapshot)
    paths = {
        e.path for e in cat.entries if (_VolumeRule.rule_id, "static") in e.rule_evidence
    }
    assert paths == {"reference_delta.{label}.features.physical_volume_mm3.value"}
