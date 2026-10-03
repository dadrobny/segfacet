"""Item 201 -- severity-ladder constants re-measured on the lordotic base.

AC4, AC5 and AC6 are covered by existing tests that iterate the live
registries (``tests/test_154_ladder_remeasurement.py``: ``test_ac10_*``,
``test_ac8_*``, ``test_ac9_*``); they are not repeated here.
"""

from __future__ import annotations

import pytest

import segfacet.synth  # noqa: F401 -- registers every perturbation operator
from segfacet.eval import severity_ladder as sl


@pytest.fixture(scope="module")
def verdict():
    return sl.score_harness(sl.run_severity_harness())


def test_ac1_split_operators_are_scored(verdict):
    assert {"split", "split_own_label"} <= set(verdict.per_ladder)


def test_ac2_split_ladder_passes(verdict):
    assert "split" in verdict.per_ladder
    assert verdict.per_ladder["split"].failures == ()


def test_ac3_split_own_label_ladder_passes(verdict):
    assert "split_own_label" in verdict.per_ladder
    assert verdict.per_ladder["split_own_label"].failures == ()


def test_ac7_mode_1_disposition_follows_the_ladders_homes():
    expected = tuple(op for op, spec in sl.SEVERITY_LADDERS.items() if spec.failure_mode == 1)
    assert expected
    assert sl.MODE_LADDER_DISPOSITIONS[1].ladders == expected
