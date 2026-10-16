"""Item 222: a terminal vertebra is judged on a one-sided line reading.

Covers AC1-AC13 plus the Testing Strategy's three named cases. The line
reading ``L(p; a, b)`` and the item-120 computation are written out here in
numpy and from ``fit_centroid_spline`` / ``compute_spline_offsets``; no test
calls the item's own helpers except ``_withhold_outliers`` for the set ``S``.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import segfacet.backend as backend_mod
import segfacet.features.spline_offset as so
from segfacet.config import bundled_default_config
from segfacet.features.centroids import compute_centroid
from segfacet.features.spline import fit_centroid_spline
from segfacet.features.spline_offset import (
    compute_leave_one_out_spline_offsets,
    compute_spline_offsets,
)
from segfacet.heuristics.spline_offset import SplineOffsetRule
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.identity_ordering_alignment import DisplacePerturbation
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image

_EIGHT = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")
_TWO_OPPOSITE = {2: 15.0, 5: -15.0}


def _line(p, a, b):
    """The line reading L(p; a, b): distance from p to the line through a, b."""
    p, a, b = (np.asarray(x, dtype=float) for x in (p, a, b))
    t = (a - b) / np.linalg.norm(a - b)
    d = p - a
    return float(np.linalg.norm(d - (d @ t) * t))


def _centroids(levels=("L1", "L2", "L3", "L4", "L5"), **kw):
    spine = build_clean_spine(levels=levels, **kw)
    return [compute_centroid(spine.seg_img, lbl) for lbl in spine.labels]


def _eight():
    return _centroids(_EIGHT, spacing=(1.0, 1.0, 1.0), curve_amplitude_mm=6.0)


def _displaced(centroids, shifts):
    out = list(centroids)
    for k, m in shifts.items():
        mm = list(out[k].centroid_mm)
        mm[0] += m
        out[k] = dataclasses.replace(out[k], centroid_mm=tuple(mm))
    return out


def _mm(c):
    return c.centroid_mm


def _item120(centroids, withheld):
    """The item-120 computation for withheld set *withheld* (item 221's terms)."""
    n = len(centroids)
    ref = fit_centroid_spline(centroids)
    records = []
    for i in range(n):
        w = [1.0] * n
        for j in set(withheld) | {i}:
            w[j] = so._WITHHELD_WEIGHT
        refit = fit_centroid_spline(centroids, u=ref.u, weights=w)
        rec = compute_spline_offsets([centroids[i]], refit)[0]
        records.append(dataclasses.replace(rec, is_terminal=i in (0, n - 1)))
    return records


def _dominant(centroids):
    in_sample = compute_spline_offsets(centroids, fit_centroid_spline(centroids))
    return min(range(len(centroids)), key=lambda i: (-in_sample[i].offset_mm, centroids[i].label))


def _withhold(centroids):
    first = _item120(centroids, {_dominant(centroids)})
    return so._withhold_outliers(
        centroids, first, fit_centroid_spline(centroids), None, backend_mod.get_backend()
    )


def _terminal_record(offset_mm, terminal_offset_mm, is_terminal=True, label=24, level="L5"):
    curve = {
        "closest_u": 0.5,
        "offset_mm": offset_mm,
        "offset_voxel": offset_mm,
        "dx_mm": 3.0,
        "dy_mm": 1.0,
        "dz_mm": 0.5,
        "is_terminal": is_terminal,
        "terminal_offset_mm": terminal_offset_mm,
    }
    return {
        "per_label": {str(label): {"label": label, "level_name": level, "curve": curve}},
        "case": {"curve": {"is_monotonic": True}},
        "pairs": {"adjacent": {"non_monotonic_pairs": []}},
    }


def _evaluate(record):
    return SplineOffsetRule().evaluate(record, bundled_default_config())


def _displaced_terminal_findings(label):
    seg = build_clean_spine().seg_img
    result = DisplacePerturbation(target_label=label, displacement_mm=15.0, ap_angle_deg=20.0).apply(seg, 0)
    return run_qc(result.labelmap, bundled_default_config())[0].findings


def _corpus_findings(case_id):
    case = next(c for c in load_manifest()["cases"] if c["case_id"] == case_id)
    return run_qc(loaded_seg_image(case), bundled_default_config())[0].findings


def _has(findings, label):
    return any(f.rule_id == "spline_offset" and f.labels == frozenset({label}) for f in findings)


def test_ac1_clean_terminal_reads_line_through_two_nearest_neighbours():
    c = _centroids()
    r = compute_leave_one_out_spline_offsets(c)
    m = [_mm(x) for x in c]
    assert r[0].terminal_offset_mm == pytest.approx(_line(m[0], m[1], m[2]), abs=1e-9)
    assert r[4].terminal_offset_mm == pytest.approx(_line(m[4], m[3], m[2]), abs=1e-9)


def test_ac2_withheld_neighbour_is_skipped():
    c = _displaced(_eight(), _TWO_OPPOSITE)
    r = compute_leave_one_out_spline_offsets(c)
    m = [_mm(x) for x in c]
    assert r[0].terminal_offset_mm == pytest.approx(_line(m[0], m[1], m[3]), abs=1e-9)
    assert r[7].terminal_offset_mm == pytest.approx(_line(m[7], m[6], m[4]), abs=1e-9)


def test_ac3_interior_records_carry_no_terminal_reading():
    r = compute_leave_one_out_spline_offsets(_centroids())
    interior = [x for x in r if not x.is_terminal]
    assert len(interior) == 3
    assert all(x.terminal_offset_mm is None for x in interior)


def test_ac4_below_five_levels_no_terminal_reading():
    r = compute_leave_one_out_spline_offsets(_centroids(("L1", "L2", "L3", "L4")))
    assert len(r) == 4
    assert all(x.terminal_offset_mm is None for x in r)


def test_ac5_item_221_fields_are_unchanged():
    c = _displaced(_eight(), _TWO_OPPOSITE)
    withheld, _ = _withhold(c)
    assert withheld == frozenset({2, 5})
    expected = _item120(c, withheld)
    actual = compute_leave_one_out_spline_offsets(c)
    assert len(actual) == len(expected) == 8
    for i in range(8):
        assert dataclasses.replace(actual[i], terminal_offset_mm=None) == expected[i]


def test_ac6_record_stores_terminal_reading():
    per_label = extract_feature_record(build_clean_spine().seg_img, bundled_default_config())["per_label"]
    p = {n: per_label[str(n)]["centroid"]["centroid_mm"] for n in (20, 21, 22, 23, 24)}
    assert per_label["20"]["curve"]["terminal_offset_mm"] == pytest.approx(
        _line(p[20], p[21], p[22]), abs=1e-9
    )
    assert per_label["24"]["curve"]["terminal_offset_mm"] == pytest.approx(
        _line(p[24], p[23], p[22]), abs=1e-9
    )


def test_ac7_record_stores_nothing_for_interior_label():
    per_label = extract_feature_record(build_clean_spine().seg_img, bundled_default_config())["per_label"]
    for lbl in ("21", "22", "23"):
        assert "curve" in per_label[lbl]
        assert "terminal_offset_mm" not in per_label[lbl]["curve"]


def test_ac8_terminal_fires_at_threshold():
    findings = _evaluate(_terminal_record(0.5, 13.0))
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "spline_offset"
    assert f.detector_id == "spline_offset"
    assert f.labels == frozenset({24})
    assert f.reason.startswith("Vertebra misaligned from spinal curve:")


def test_ac9_terminal_not_judged_on_held_out_offset():
    assert not _evaluate(_terminal_record(40.0, 12.99))


def test_ac10_terminal_finding_names_no_axis():
    (f,) = _evaluate(_terminal_record(0.5, 13.0))
    assert "terminal" in f.reason
    assert "predominantly" not in f.reason


def test_ac11_displaced_terminal_is_flagged():
    assert _has(_displaced_terminal_findings(24), 24)


def test_ac12_sequence_break_fires_spline_offset_on_t13():
    assert _has(_corpus_findings("sequence_break"), 28)


def test_ac13_split_own_label_fires_spline_offset_on_l5():
    assert _has(_corpus_findings("split_own_label"), 24)


def test_interior_entry_ignores_terminal_value():
    assert not _evaluate(_terminal_record(1.0, 40.0, is_terminal=False))


def test_every_interior_withheld_leaves_no_terminal_reading():
    c = _displaced(_centroids(), {1: 15.0, 2: -15.0, 3: 15.0})
    withheld, _ = _withhold(c)
    assert withheld == frozenset({1, 2, 3})
    r = compute_leave_one_out_spline_offsets(c)
    assert len(r) == 5
    assert r[0].terminal_offset_mm is None
    assert r[4].terminal_offset_mm is None


def test_cranial_terminal_flagged():
    assert _has(_displaced_terminal_findings(20), 20)
