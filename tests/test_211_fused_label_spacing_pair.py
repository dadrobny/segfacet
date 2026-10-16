"""Item 211: ``fused_label`` (a detector of ``centroid_spacing``) judges the pair of adjacent spacings together.

Acceptance criteria are ``test_ac1`` / ``test_ac2``; the named adversarial cases
are ``split-proportion-invariant``, ``missing-vertebra-not-fused`` and
``none-key-not-judged``.
"""

from __future__ import annotations

import copy
import math

import numpy as np
import pytest

from segfacet.config import bundled_default_config
# item 218 (2026-10-13): FusedLabelRule is now CentroidSpacingRule.
from segfacet.heuristics.centroid_spacing import CentroidSpacingRule
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
    return CentroidSpacingRule().evaluate(record, config or bundled_default_config())


def _centroid(record: dict, label: int) -> np.ndarray:
    (key,) = [k for k in record["per_label"] if int(k) == label]
    return np.asarray(record["per_label"][key]["centroid"]["centroid_mm"][:3], float)


def _pitch(record: dict) -> float:
    """The 20 -> 21 centroid spacing (item 218: read off the centroids)."""
    return float(math.dist(_centroid(record, 20), _centroid(record, 21)))


def _with_pair(record: dict, first: float, second: float) -> dict:
    # Item 218 (2026-10-13): the rule no longer reads pairs.adjacent.spacings_mm,
    # so the (first, second) pair is set on the centroids. Label 22 sits `first`
    # beyond label 21 and label 23 `second` beyond label 22, along the 21 -> 23
    # direction; path_u is left as it is.
    out = copy.deepcopy(record)
    c21, c23 = _centroid(out, 21), _centroid(out, 23)
    d = (c23 - c21) / np.linalg.norm(c23 - c21)
    for label, offset in ((22, first), (23, first + second)):
        (key,) = [k for k in out["per_label"] if int(k) == label]
        out["per_label"][key]["centroid"]["centroid_mm"] = list(c21 + offset * d)
    return out


def _fused_labels(findings: list) -> list:
    # Item 218 (2026-10-13): the rule also carries missing_level, which reads
    # the (2/3, 4/3) edit's gap beside label 21 as 1.5x; only fused_label is
    # judged here.
    return [f.labels for f in findings if f.detector_id == "fused_label"]


def test_ac1_one_normal_and_one_doubled_adjacent_spacing_fires():
    record = _record("fuse_separate")
    assert _fused_labels(_evaluate(record)) == [frozenset({22})]

    p = _pitch(record)
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
    p = _pitch(record)
    findings = _evaluate(_with_pair(record, a * p, b * p))
    assert _fused_labels(findings) == ([frozenset({22})] if fires else [])


def test_missing_vertebra_not_fused():
    record = _record("remove_level_relabel")
    p = _pitch(record)
    widened = _with_pair(record, 2 * p, 2 * p)

    # Item 218 (2026-10-13): missing_level now fires on this case, so the
    # fused_label detector is judged on its own findings.
    def fused(rec, config=None):
        return [
            f for f in _evaluate(rec, config) if f.detector_id == "fused_label"
        ]

    assert fused(record) == []
    assert fused(widened) == []

    config = bundled_default_config()
    config.rules.setdefault("centroid_spacing", {}).setdefault("params", {})[
        "size_ratio_threshold"
    ] = 0.9
    for rec in (record, widened):
        findings = fused(rec, config)
        assert any(22 in f.labels for f in findings), findings


def test_none_key_not_judged():
    record = copy.deepcopy(_record("fuse_separate"))
    assert "20" in record["per_label"], list(record["per_label"])
    record["per_label"][None] = record["per_label"].pop("20")
    assert _evaluate(record) == []
