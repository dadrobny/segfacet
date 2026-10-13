"""Item 221: the held-out spline offset withholds every interior outlier.

Covers AC1-AC3 and AC5-AC7 (AC4 was withdrawn on 2026-10-13 and has no
test), plus the Testing Strategy's four named cases. The item-120
computation is written out here from ``fit_centroid_spline`` and
``compute_spline_offsets``; it never calls the item's own helpers.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

import segfacet.backend as backend_mod
import segfacet.features.spline_offset as so
from segfacet.features.centroids import compute_centroid
from segfacet.features.spline import fit_centroid_spline
from segfacet.features.spline_offset import (
    compute_leave_one_out_spline_offsets,
    compute_spline_offsets,
)
from segfacet.synth.clean_gt import build_clean_spine

_REPO_ROOT = Path(__file__).resolve().parents[1]
_EIGHT = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")


def _spine(levels=_EIGHT):
    spine = build_clean_spine(levels=levels, spacing=(1.0, 1.0, 1.0), curve_amplitude_mm=6.0)
    return [compute_centroid(spine.seg_img, lbl) for lbl in spine.labels]


def _displaced(centroids, shifts):
    out = list(centroids)
    for k, m in shifts.items():
        mm = list(out[k].centroid_mm)
        mm[0] += m
        out[k] = dataclasses.replace(out[k], centroid_mm=tuple(mm))
    return out


def _item120(centroids, withheld):
    """The item-120 computation for withheld set *withheld*."""
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


_TWO_OPPOSITE = {2: 15.0, 5: -15.0}


def test_ac1_displaced_levels_outread_every_clean_level():
    r = compute_leave_one_out_spline_offsets(_displaced(_spine(), _TWO_OPPOSITE))
    clean = max(r[k].offset_mm for k in (0, 1, 3, 4, 6, 7))
    assert min(r[2].offset_mm, r[5].offset_mm) > clean


def test_ac2_single_outlier_reads_as_before():
    c = _displaced(_spine(), {3: 15.0})
    assert _dominant(c) == 3
    assert compute_leave_one_out_spline_offsets(c) == _item120(c, {3})


def test_ac3_withheld_set_is_the_two_displaced_levels():
    withheld, _ = _withhold(_displaced(_spine(), _TWO_OPPOSITE))
    assert withheld == frozenset({2, 5})


def test_ac5_cutoff_is_ten_mm():
    assert so._OUTLIER_CUTOFF_MM == 10.0


def test_ac6_terminal_level_is_never_withheld():
    c = _displaced(_spine(), {0: 18.0})
    withheld, _ = _withhold(c)
    assert withheld == frozenset()
    dominant = _dominant(c)
    assert compute_leave_one_out_spline_offsets(c) == _item120(c, {dominant})


def test_ac7_reverified_verse19_ceiling_is_recorded():
    import importlib.util
    import sys

    from segfacet.reference.artifact import bundled_production_reference_path, load_artifact

    module_path = _REPO_ROOT / "scripts" / "rebuild_verse_reference.py"
    spec = importlib.util.spec_from_file_location("rebuild_verse_reference", module_path)
    tool = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tool
    spec.loader.exec_module(tool)

    p99 = tool._p99_by_level(load_artifact(bundled_production_reference_path()))
    qualifying = [e["p99"] for e in p99.values() if e["count"] >= 10]
    assert qualifying
    expected = round(max(qualifying), 6)

    text = (_REPO_ROOT / "docs" / "reference-build.md").read_text(encoding="utf-8")
    sections = [s for s in text.split("\n## ")[1:] if s.startswith("Rebuild record — ")]
    mine = [s for s in sections if "item 221" in s]
    assert mine
    match = re.search(r"P = ([0-9]+(?:\.[0-9]+)?) mm", mine[0])
    assert match
    assert float(match.group(1)) == expected


def test_emptied_set_returns_first_pass():
    c = _displaced(_spine(), {2: 15.0, 3: 15.0})
    withheld, records = _withhold(c)
    assert withheld == frozenset()
    assert compute_leave_one_out_spline_offsets(c) == _item120(c, {_dominant(c)})
    assert records == _item120(c, {_dominant(c)})


_ADD_STEP_SETS = [(6.0, frozenset({1, 5, 6})), (10.0, frozenset({5})), (13.0, frozenset())]
# Each interior index is added at most once (6), and every index that enters
# the set is removed at most once (initial <= 6, added <= 6), plus the first
# held-out call: 1 + 6 + 12.
_MAX_HELD_OUT_CALLS = 19


@pytest.mark.parametrize(("cutoff", "expected"), _ADD_STEP_SETS)
def test_add_step_bounded(monkeypatch, cutoff, expected):
    monkeypatch.setattr(so, "_OUTLIER_CUTOFF_MM", cutoff)
    calls = []
    real = so._held_out_records
    monkeypatch.setattr(so, "_held_out_records", lambda *a, **k: calls.append(1) or real(*a, **k))
    withheld, records = _withhold(_displaced(_spine(), {2: 15.0, 4: -15.0}))
    assert withheld == expected
    assert len(records) == 8
    assert len(calls) <= _MAX_HELD_OUT_CALLS


def test_five_levels_every_interior_withheld():
    c = _displaced(_spine(("L1", "L2", "L3", "L4", "L5")), {1: 15.0, 2: -15.0, 3: 15.0})
    withheld, records = _withhold(c)
    assert withheld == frozenset({1, 2, 3})
    assert len(records) == 5
    assert all(r.offset_mm == r.offset_mm and abs(r.offset_mm) != float("inf") for r in records)


def test_withheld_set_is_interior_indices(monkeypatch):
    monkeypatch.setattr(so, "_OUTLIER_CUTOFF_MM", 6.0)
    c = _displaced(_spine(), {2: 15.0, 4: -15.0})
    withheld, _ = _withhold(c)
    assert withheld == frozenset({1, 5, 6})
    assert not withheld & {0, len(c) - 1}
