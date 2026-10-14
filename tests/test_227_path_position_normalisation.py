"""Item 227: path positions stay in [0, 1] whatever ``sum()`` rounding does.

Python 3.12 made ``sum()`` of floats compensated, so ``_path_positions`` could
normalise by a total one ulp below its own final accumulated length. CI runs
3.11, where the defect cannot occur, so the tests patch the module-global
``sum`` to ``math.fsum`` (an exactly rounded sum that overshoots the same way).
"""

import math

from segfacet.features import consistency
from segfacet.features.centroids import LabelCentroid

OVERSHOOT_SPINE = [
    (0.0, 0.0, 0.0),
    (2.0665311091502883, 1.5477264176418153, 28.411431616616902),
    (0.6200316109080684, 1.6153747458534662, 56.510114365625185),
    (2.322823145116704, 0.4352511023270309, 86.0420534486723),
    (2.8231153818468915, 2.8839284134990417, 116.1357905650201),
]

BACKWARD_OVERSHOOT_SPINE = [
    (-1.5098163182215227, -3.9720566376064594, 84.46705062824944),
    (0.0, 0.0, 0.0),
    (0.40939765999365907, -2.1731235016702133, 22.465964361582984),
    (-1.867495223422111, -2.765824254685681, 51.82482120939568),
    (-0.05574349640587961, -5.663996879209332, 114.24421384989117),
]


def _centroids(points):
    return [
        LabelCentroid(
            label=i + 1,
            level_name=f"L{i + 1}",
            centroid_voxel=p,
            centroid_mm=p,
        )
        for i, p in enumerate(points)
    ]


def _patched(monkeypatch):
    monkeypatch.setattr(consistency, "sum", math.fsum, raising=False)


def test_ac1_path_positions_in_unit_range_with_compensated_sum(monkeypatch):
    _patched(monkeypatch)
    u = consistency._path_positions(_centroids(OVERSHOOT_SPINE))
    assert len(u) == len(OVERSHOOT_SPINE)
    assert all(0.0 <= v <= 1.0 for v in u)


def test_ac2_path_positions_independent_of_sum_rounding(monkeypatch):
    cents = _centroids(OVERSHOOT_SPINE)
    unpatched = consistency._path_positions(cents)
    _patched(monkeypatch)
    patched = consistency._path_positions(cents)
    assert len(unpatched) == len(OVERSHOOT_SPINE)
    assert patched == unpatched


def test_backward_branch(monkeypatch):
    _patched(monkeypatch)
    u = consistency._path_positions(_centroids(BACKWARD_OVERSHOOT_SPINE))
    assert len(u) == len(BACKWARD_OVERSHOOT_SPINE)
    assert all(0.0 <= v <= 1.0 for v in u)


def test_zero_length_path():
    p = (1.0, 2.0, 3.0)
    assert consistency._path_positions(_centroids([p, p, p])) == [0.0, 0.0, 0.0]
