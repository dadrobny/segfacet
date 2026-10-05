"""Item 211: ``fused_label`` judges the pair of adjacent spacings together.

Acceptance criteria are ``test_ac1`` / ``test_ac2``; the named adversarial cases
are ``split-proportion-invariant``, ``missing-vertebra-not-fused`` and
``none-key-not-judged``.
"""

from __future__ import annotations

import copy

import pytest

from segfacet.config import bundled_default_config
from segfacet.heuristics.fused_label import FusedLabelRule
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image


def _record(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return extract_feature_record(
        loaded_seg_image(matches[0]), bundled_default_config()
    )


def _evaluate(record: dict, config=None) -> list:
    return FusedLabelRule().evaluate(record, config or bundled_default_config())


def _with_pair(record: dict, first: float, second: float) -> dict:
    out = copy.deepcopy(record)
    sp = out["stage3"]["spacing_consistency"]["spacings_mm"]
    sp[1], sp[2] = first, second
    return out


def _fused_labels(findings: list) -> list:
    return [f.labels for f in findings]


def test_ac1_one_normal_and_one_doubled_adjacent_spacing_fires():
    record = _record("fuse_separate")
    assert _fused_labels(_evaluate(record)) == [frozenset({22})]

    p = record["stage3"]["spacing_consistency"]["spacings_mm"][0]
    assert _fused_labels(_evaluate(_with_pair(record, p, 2 * p))) == [frozenset({22})]


def test_ac2_a_non_integer_per_label_key_is_not_judged():
    record = copy.deepcopy(_record("fuse_separate"))
    assert "20" in record["per_label"], list(record["per_label"])
    record["per_label"]["x"] = record["per_label"].pop("20")
    assert _evaluate(record) == []


@pytest.mark.parametrize(
    "a, b, fires",
    [
        (1, 2, True),
        (1.5, 1.5, True),
        (2, 1, True),
        (2 / 3, 4 / 3, False),
        (4 / 3, 2 / 3, False),
    ],
)
def test_split_proportion_invariant(a, b, fires):
    record = _record("fuse_separate")
    p = record["stage3"]["spacing_consistency"]["spacings_mm"][0]
    findings = _evaluate(_with_pair(record, a * p, b * p))
    assert _fused_labels(findings) == ([frozenset({22})] if fires else [])


def test_missing_vertebra_not_fused():
    record = _record("remove_level_relabel")
    p = record["stage3"]["spacing_consistency"]["spacings_mm"][0]
    widened = _with_pair(record, 2 * p, 2 * p)

    assert _evaluate(record) == []
    assert _evaluate(widened) == []

    config = bundled_default_config()
    config.rules.setdefault("fused_label", {}).setdefault("params", {})[
        "size_ratio_threshold"
    ] = 0.9
    for rec in (record, widened):
        findings = _evaluate(rec, config)
        assert any(22 in f.labels for f in findings), findings


def test_none_key_not_judged():
    record = copy.deepcopy(_record("fuse_separate"))
    assert "20" in record["per_label"], list(record["per_label"])
    record["per_label"][None] = record["per_label"].pop("20")
    assert _evaluate(record) == []
