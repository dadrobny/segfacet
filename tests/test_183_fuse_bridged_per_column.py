"""Tests for item 183 -- ``FusePerturbation(bridged=True)``
(``src/segfacet/synth/component_shape.py``) decides which end of a label
pair faces which **per column**, not once for the whole array. Item 176's
bridge picked a single global direction from the two labels' mean
stacking-axis index; a column whose pair sits in the opposite order (a
"reversed" column) or has one label on both sides of the other (a
"sandwiched" column) was left unfilled by that global rule.

Covers Acceptance Criteria AC1-AC2 per the item spec's Testing Strategy: one
test per AC, each on a small constructed two-label array with an identity
(RAS) affine. AC3 (committed corpus regenerates byte-identically) is the
existing ``tests/test_040_synthetic_corpus.py::
test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`` and
gets no new test here.

Plus exactly the one adversarial case the Testing Strategy names:
``no-fill-between-same-label``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet.synth.axes import si_axis
from segfacet.synth.component_shape import FusePerturbation

TARGET = 22
NEIGHBOUR = 23


def _build(column: list) -> nib.Nifti1Image:
    """A ``(1, 1, len(column))`` label map with an identity affine, whose
    sole axis-2 column holds *column* (an int list) as its values."""
    data = np.array(column, dtype=np.int16).reshape(1, 1, len(column))
    img = nib.Nifti1Image(data, np.eye(4), dtype=data.dtype)
    assert si_axis(img.affine) == 2
    return img


def _bridged_column(img: nib.Nifti1Image) -> np.ndarray:
    result = FusePerturbation(target_label=TARGET, neighbour_label=NEIGHBOUR, bridged=True).apply(
        img, seed=0
    )
    out = np.asanyarray(result.labelmap.dataobj)
    return out[0, 0, :]


# =========================================================================== #
# AC1: a reversed column is bridged in its own order
# =========================================================================== #


def test_ac1_reversed_column_bridged_in_its_own_order():
    # Global order (from mean index over the whole array): neighbour (23)
    # below target (22). One column reverses that: 22 then background then
    # 23.
    column = [TARGET, 0, 0, NEIGHBOUR]
    other_column = [NEIGHBOUR, NEIGHBOUR, TARGET, TARGET]
    data = np.array([column, other_column], dtype=np.int16).reshape(2, 1, 4)
    img = nib.Nifti1Image(data, np.eye(4), dtype=data.dtype)
    assert si_axis(img.affine) == 2

    # Premise: this column's own order is the opposite of the order the
    # two labels' global mean axis-2 index gives, and it has a background
    # voxel between the pair.
    mean_target = float(np.nonzero(data == TARGET)[2].mean())
    mean_neighbour = float(np.nonzero(data == NEIGHBOUR)[2].mean())
    global_neighbour_is_low = mean_neighbour < mean_target
    col = np.array(column)
    n_idx = np.nonzero(col == NEIGHBOUR)[0]
    t_idx = np.nonzero(col == TARGET)[0]
    assert n_idx.min() > t_idx.max(), "reversed column's own order must be target-then-neighbour"
    column_neighbour_is_low = n_idx.min() < t_idx.max()
    assert column_neighbour_is_low != global_neighbour_is_low, (
        "column's order must be opposite of the global order"
    )
    between = col[int(t_idx.max()) + 1 : int(n_idx.min())]
    assert np.count_nonzero(between == 0) > 0

    result = FusePerturbation(target_label=TARGET, neighbour_label=NEIGHBOUR, bridged=True).apply(
        img, seed=0
    )
    out = np.asanyarray(result.labelmap.dataobj)
    out_col = out[0, 0, :]

    expected = (
        set(int(i) for i in np.nonzero(col == TARGET)[0])
        | set(int(i) for i in np.nonzero(col == NEIGHBOUR)[0])
        | set(
            int(i)
            for i in range(int(t_idx.max()) + 1, int(n_idx.min()))
            if col[i] == 0
        )
    )
    actual = set(int(i) for i in np.nonzero(out_col == TARGET)[0])
    assert actual == expected


# =========================================================================== #
# AC2: a sandwiched column is bridged on both sides
# =========================================================================== #


def test_ac2_sandwiched_column_bridged_on_both_sides():
    column = [TARGET, 0, NEIGHBOUR, 0, TARGET]
    col = np.array(column)

    # Premise: this column really does hold target on both sides of
    # neighbour, with background in each gap.
    t_idx = np.nonzero(col == TARGET)[0]
    n_idx = np.nonzero(col == NEIGHBOUR)[0]
    assert t_idx.size == 2 and n_idx.size == 1
    assert t_idx.min() < n_idx.min() < t_idx.max()
    assert col[n_idx.min() - 1] == 0
    assert col[n_idx.min() + 1] == 0

    img = _build(column)
    out_col = _bridged_column(img)

    gap_positions = set()
    for lo, hi in ((t_idx.min(), n_idx.min()), (n_idx.min(), t_idx.max())):
        gap_positions |= {i for i in range(int(lo) + 1, int(hi)) if col[i] == 0}

    expected = (
        set(int(i) for i in np.nonzero(col == TARGET)[0])
        | set(int(i) for i in np.nonzero(col == NEIGHBOUR)[0])
        | gap_positions
    )
    actual = set(int(i) for i in np.nonzero(out_col == TARGET)[0])
    assert actual == expected


# =========================================================================== #
# Named adversarial case: no-fill-between-same-label
# =========================================================================== #


def test_no_fill_between_same_label():
    """Guards a per-column rule that fills from a column's first pair voxel
    to its last, which would pass AC1 and AC2 and also fill a hole inside
    one body: the first background run here sits between two target voxels
    and must stay 0."""
    column = [TARGET, 0, TARGET, 0, NEIGHBOUR]
    col = np.array(column)

    img = _build(column)
    out_col = _bridged_column(img)

    # First background run (index 1) is bounded by target on both sides --
    # never filled.
    assert out_col[1] == 0
    # Second background run (index 3) is bounded by target then neighbour --
    # filled.
    assert out_col[3] == TARGET
