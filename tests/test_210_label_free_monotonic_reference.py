"""Tests for item 210 -- the monotonicity check's reference curve made
label-free and direction-robust.

Covers Acceptance Criteria AC1-AC5 from
``docs/aide/items/210-monotonic-reference-curve-label-free-direction-robust.md``,
one test each, plus its two named adversarial cases:
``displaced-far-lateral-not-misread`` and ``handler-still-detects-swap``.
"""

from __future__ import annotations

import math
from typing import List

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth.regression as regression
from segfacet.config import bundled_default_config
from segfacet.features.centroids import LabelCentroid
from segfacet.features.consistency import compute_monotonic_consistency
from segfacet.features.spline import fit_centroid_spline
from segfacet.heuristics.mislabel import MislabelRule
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest

_MANIFEST = load_manifest()
_CFG = bundled_default_config()


def _case(case_id: str) -> dict:
    return next(c for c in _MANIFEST["cases"] if c["case_id"] == case_id)


_CLEAN_CASE = _case("clean_control")
_CLEAN_MAP = regression.loaded_seg_image(_CLEAN_CASE)


def relabel(mapping: dict) -> nib.Nifti1Image:
    """The clean map with every voxel value ``a`` in *mapping* replaced by
    ``mapping[a]`` (each replacement read from the original data), on the
    same affine and header."""
    data = np.asarray(_CLEAN_MAP.dataobj)
    original = data.copy()
    out = data.copy()
    for src, dst in mapping.items():
        out[original == src] = dst
    return nib.Nifti1Image(out, _CLEAN_MAP.affine, _CLEAN_MAP.header, dtype=out.dtype)


def _centroid(level_name: str, mm, label: int) -> LabelCentroid:
    return LabelCentroid(
        label=label,
        level_name=level_name,
        centroid_voxel=tuple(mm),
        centroid_mm=tuple(mm),
    )


_LEVELS = ["T8", "T9", "T10", "T11", "T12", "L1", "L2", "L3", "L4", "L5"]


def _arc() -> List[LabelCentroid]:
    out = []
    for i, name in enumerate(_LEVELS):
        t = math.radians(-90 + 210 * i / 9)
        out.append(_centroid(name, (0.0, 60 * math.cos(t), 60 * math.sin(t)), i + 1))
    return out


ARC = _arc()
ARC_SWAP = list(ARC)
ARC_SWAP[3], ARC_SWAP[4] = ARC_SWAP[4], ARC_SWAP[3]

_T13_MAP = relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})

_HANDLER_CASE = dict(
    _CLEAN_CASE,
    detection="reconstructed_record",
    reconstruction="monotonic_true_spatial_order",
    expected_rule_ids=["mislabel"],
)


def via_handler(img, monkeypatch) -> set:
    monkeypatch.setattr(regression, "loaded_seg_image", lambda case, *a, **k: img)
    return {
        (f.rule_id, f.detector_id, f.labels)
        for f in regression.reconstructed_findings(_HANDLER_CASE, _CFG)
    }


# =========================================================================== #
# AC1-AC5
# =========================================================================== #


def test_ac1_sequence_break_names_the_misplaced_level():
    findings = regression.pipeline_findings(_case("sequence_break"), _CFG)
    assert {
        (f.detector_id, f.labels) for f in findings if f.rule_id == "mislabel"
    } == {("ordering", frozenset({20, 28}))}


def test_ac2_curve_whose_s_reverses_reads_monotone_when_correctly_labelled():
    result = compute_monotonic_consistency(ARC, fit_centroid_spline(ARC))
    assert result.non_monotonic_pairs == ()


def test_ac3_reconstruction_handler_agrees_with_pipeline(monkeypatch):
    expected = {
        (f.rule_id, f.detector_id, f.labels)
        for f in MislabelRule().evaluate(extract_feature_record(_T13_MAP, _CFG), _CFG)
    }
    assert via_handler(_T13_MAP, monkeypatch) == expected


def test_ac4_u_is_normalised_arc_length_along_the_path():
    result = compute_monotonic_consistency(ARC, fit_centroid_spline(ARC))
    assert result.u_values == pytest.approx([i / 9 for i in range(10)], abs=1e-9)


def test_ac5_check_reads_no_spline():
    result = compute_monotonic_consistency(ARC_SWAP, None)
    assert result.non_monotonic_pairs == (("T12", "T11"),)


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_displaced_far_lateral_not_misread():
    c = []
    for i, name in enumerate(_LEVELS):
        mm = (60.0, 0.0, -120.0) if i == 4 else (0.0, 0.0, -30.0 * i)
        c.append(_centroid(name, mm, i + 1))
    assert compute_monotonic_consistency(c, None).non_monotonic_pairs == ()


def test_handler_still_detects_swap(monkeypatch):
    got = via_handler(relabel({21: 22, 22: 21}), monkeypatch)
    assert got == {("mislabel", "ordering", frozenset({21, 22}))}
