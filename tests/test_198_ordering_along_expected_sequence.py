"""Tests for item 198 -- ``mislabel``'s ``ordering`` detector judges order
along ``CANONICAL_ORDER``.

Covers Acceptance Criteria AC1-AC4 from
``docs/aide/items/198-mislabel-s-ordering-detector-judges.md``, one test each,
plus its two named adversarial cases: ``t13-below-l1-still-fires`` and
``cocc-above-s2-still-fires``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np

from segfacet.config import bundled_default_config
from segfacet.heuristics import run_rules
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image, pipeline_findings

_MANIFEST = load_manifest()
_CFG = bundled_default_config()


def _case(case_id: str) -> dict:
    return next(c for c in _MANIFEST["cases"] if c["case_id"] == case_id)


_CLEAN_MAP = loaded_seg_image(_case("clean_control"))


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


def rec(img: nib.Nifti1Image) -> dict:
    return extract_feature_record(img, _CFG)


def mis(img: nib.Nifti1Image) -> set:
    return {
        (f.detector_id, f.labels)
        for f in run_rules(rec(img), _CFG)
        if f.rule_id == "mislabel"
    }


# T13, L1, L2, L3, L4 head-to-tail.
_T13_MAP = relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})
# L4, L5, S1, S2, Cocc head-to-tail.
_COCC_MAP = relabel({20: 23, 21: 24, 22: 26, 23: 29, 24: 27})


# =========================================================================== #
# AC1-AC4
# =========================================================================== #


def test_ac1_correctly_placed_t13_fires_no_ordering_finding():
    assert mis(_T13_MAP) == set()


def test_ac2_correctly_placed_coccyx_fires_no_ordering_finding():
    assert mis(_COCC_MAP) == set()


def test_ac3_relabel_swap_still_fires():
    findings = pipeline_findings(_case("relabel_swap"), _CFG)
    assert {
        (f.detector_id, f.labels) for f in findings if f.rule_id == "mislabel"
    } == {("ordering", frozenset({21, 22}))}


def test_ac4_record_reports_the_two_controls_as_monotonic():
    assert [
        rec(m)["stage3"]["monotonic_consistency"]["non_monotonic_pairs"]
        for m in (_T13_MAP, _COCC_MAP)
    ] == [[], []]


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_t13_below_l1_still_fires():
    # L1, T13, L2, L3, L4 head-to-tail.
    img = relabel({21: 28, 22: 21, 23: 22, 24: 23})
    assert mis(img) == {("ordering", frozenset({20, 28}))}


def test_cocc_above_s2_still_fires():
    # L4, L5, S1, Cocc, S2 head-to-tail.
    img = relabel({20: 23, 21: 24, 22: 26, 23: 27, 24: 29})
    assert mis(img) == {("ordering", frozenset({27, 29}))}
