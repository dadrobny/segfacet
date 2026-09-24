"""Tests for item 176 -- ``FusePerturbation`` gains a ``bridged: bool = False``
keyword (``src/segfacet/synth/component_shape.py``). With ``bridged=True`` the
gap between an adjacent label pair is filled column-by-column along the
stacking axis, the neighbour is relabelled onto the target, and every label
caudal to the neighbour is renumbered one position up -- so the corpus case
``fuse_adjacent`` becomes one connected label over two bodies with a
continuous label sequence, firing nothing under the shipped rules. The
default (``bridged=False``) stays today's unbridged absorb, byte for byte,
for the severity ladder.

Covers Acceptance Criteria AC1-AC11 per the item spec's Testing Strategy: one
test per AC. AC1-AC6 apply the bridged operator directly to
``build_clean_spine().seg_img``; AC3/AC4 walk columns with plain NumPy,
deriving the stacking axis from ``si_axis`` and the facing side from the two
labels' live mean index on it, never calling the operator's internals. AC7
compares against the committed ``clean_control``/``fuse_adjacent`` fixtures,
resolved through ``load_manifest``/``loaded_seg_image``, never a hard-coded
path. AC9 uses ``extract_feature_record``; AC10/AC11 use
``failure_modes.measured_firing`` against the live ``SPECIFICATION``.

Plus exactly the five adversarial cases the Testing Strategy names:
``fuse-bridge-resolves-direction``, ``fuse-bridge-keeps-third-label``,
``fuse-bridged-refuses-cranial-neighbour``, ``fuse-default-form-unchanged``
and ``fuse-bridged-non-mutating``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest
import scipy.ndimage as ndi

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.io import FacetInputError
from segfacet.pipeline import extract_feature_record
from segfacet.synth.axes import si_axis
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.component_shape import FusePerturbation
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image


# =========================================================================== #
# Helpers
# =========================================================================== #


def _clean_seg_img():
    return build_clean_spine().seg_img


def _bridged_result(seg_img):
    return FusePerturbation(target_label=22, neighbour_label=23, bridged=True).apply(
        seg_img, seed=0
    )


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _facing_side(data: np.ndarray, axis: int) -> bool:
    """True iff label 23 (the neighbour) sits on the *low*-index side of
    label 22 (the target) along *axis*, derived live from their mean index --
    never assumed."""
    mean_target = float(np.nonzero(data == 22)[axis].mean())
    mean_neighbour = float(np.nonzero(data == 23)[axis].mean())
    return mean_neighbour < mean_target


def _column_gap(col: np.ndarray, neighbour_is_low: bool):
    """``(lo, hi)`` -- the exclusive-background index range strictly between
    the target's (22) and neighbour's (23) facing ends of one column, or
    ``None`` if the column does not hold both labels."""
    t_idx = np.nonzero(col == 22)[0]
    n_idx = np.nonzero(col == 23)[0]
    if t_idx.size == 0 or n_idx.size == 0:
        return None
    if neighbour_is_low:
        return int(n_idx.max()) + 1, int(t_idx.min())
    return int(t_idx.max()) + 1, int(n_idx.min())


# =========================================================================== #
# AC1: the fused label is one component
# =========================================================================== #


def test_ac1_fused_label_is_one_component():
    result = _bridged_result(_clean_seg_img())
    out = np.asanyarray(result.labelmap.dataobj)
    _labelled, num_components = ndi.label(out == 22)
    assert num_components == 1


# =========================================================================== #
# AC2: the fused label covers both bodies
# =========================================================================== #


def test_ac2_fused_label_covers_both_bodies():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = _bridged_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    both_mask = (input_data == 22) | (input_data == 23)
    assert int(np.count_nonzero(both_mask)) > 0
    assert np.all(output_data[both_mask] == 22)


# =========================================================================== #
# AC3: the bridge stays inside the gap
# =========================================================================== #


def test_ac3_bridge_stays_inside_the_gap():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)
    neighbour_is_low = _facing_side(input_data, axis)

    result = _bridged_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    moved_in = np.moveaxis(input_data, axis, -1)
    moved_out = np.moveaxis(output_data, axis, -1)
    bridge_mask = (moved_in == 0) & (moved_out != 0)
    n_bridged = int(np.count_nonzero(bridge_mask))
    assert n_bridged > 0, "no voxel was filled -- nothing to check"
    assert np.all(moved_out[bridge_mask] == 22)

    for idx in np.ndindex(moved_in.shape[:-1]):
        col_bridge = bridge_mask[idx]
        if not col_bridge.any():
            continue
        gap = _column_gap(moved_in[idx], neighbour_is_low)
        assert gap is not None, "bridged voxel in a column missing one of the pair"
        lo, hi = gap
        bridged_positions = set(int(p) for p in np.nonzero(col_bridge)[0])
        assert bridged_positions <= set(range(lo, hi))


# =========================================================================== #
# AC4: the bridge fills the gap
# =========================================================================== #


def test_ac4_bridge_fills_the_gap():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)
    neighbour_is_low = _facing_side(input_data, axis)

    result = _bridged_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    moved_in = np.moveaxis(input_data, axis, -1)
    moved_out = np.moveaxis(output_data, axis, -1)

    checked_gap_voxels = 0
    for idx in np.ndindex(moved_in.shape[:-1]):
        col_in = moved_in[idx]
        gap = _column_gap(col_in, neighbour_is_low)
        if gap is None:
            continue
        lo, hi = gap
        col_out = moved_out[idx]
        for pos in range(lo, hi):
            if col_in[pos] == 0:
                checked_gap_voxels += 1
                assert col_out[pos] == 22
    assert checked_gap_voxels > 0, "no column held a background gap -- nothing to check"


# =========================================================================== #
# AC5: the caudal label is renumbered
# =========================================================================== #


def test_ac5_caudal_label_is_renumbered():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = _bridged_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    assert int(np.count_nonzero(input_data == 24)) > 0
    assert np.array_equal(output_data == 23, input_data == 24)


# =========================================================================== #
# AC6: the cranial labels are unchanged
# =========================================================================== #


def test_ac6_cranial_labels_are_unchanged():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = _bridged_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    below_22 = sorted(int(v) for v in np.unique(input_data) if 0 < v < 22)
    assert below_22, "no input label below 22 -- nothing to check"
    for label in below_22:
        assert np.array_equal(output_data == label, input_data == label)


# =========================================================================== #
# AC7: the committed fixture is the operator's output
# =========================================================================== #


def test_ac7_committed_fixture_is_the_operators_output():
    clean_case = _manifest_case("clean_control")
    fuse_case = _manifest_case("fuse_adjacent")

    result = _bridged_result(loaded_seg_image(clean_case))
    actual = np.asanyarray(result.labelmap.dataobj)
    committed = np.asanyarray(loaded_seg_image(fuse_case).dataobj)

    assert np.array_equal(actual, committed)


# =========================================================================== #
# AC8: the committed fixture's labels are a continuous run
# =========================================================================== #


def test_ac8_committed_fixture_labels_are_a_continuous_run():
    fuse_case = _manifest_case("fuse_adjacent")
    data = np.asanyarray(loaded_seg_image(fuse_case).dataobj)
    s = sorted(int(v) for v in np.unique(data) if v != 0)
    assert s, "committed fixture has no foreground -- nothing to check"
    assert s == list(range(s[0], s[0] + len(s)))


# =========================================================================== #
# AC9: the pipeline measures one component
# =========================================================================== #


def test_ac9_pipeline_measures_one_component():
    fuse_case = _manifest_case("fuse_adjacent")
    record = extract_feature_record(loaded_seg_image(fuse_case), bundled_default_config())
    assert record["per_label"]["22"]["components"]["component_count"] == 1


# =========================================================================== #
# AC10: nothing fires
# =========================================================================== #


def test_ac10_nothing_fires():
    matches = [
        c for c in failure_modes.SPECIFICATION[2].corpus_cases if c.case_id == "fuse_adjacent"
    ]
    assert len(matches) == 1, matches
    assert failure_modes.measured_firing(matches[0]) == ()


# =========================================================================== #
# AC11: the authored expected set equals the measured firing
# =========================================================================== #


def test_ac11_expected_set_equals_measured_firing():
    matches = [
        c for c in failure_modes.SPECIFICATION[2].corpus_cases if c.case_id == "fuse_adjacent"
    ]
    assert len(matches) == 1, matches
    case = matches[0]
    assert case.expected_firing == failure_modes.measured_firing(case)


# =========================================================================== #
# Named adversarial case: fuse-bridge-resolves-direction
# =========================================================================== #


def test_fuse_bridge_resolves_direction():
    """Guards a hard-coded axis or side: the prototype's column walk assumed
    the neighbour lies at lower indices. That passes AC1-AC6 on the RAS base
    and fails here."""
    ras_img = _clean_seg_img()
    ras_result = _bridged_result(ras_img)

    transform = np.array([[0, 1], [1, 1], [2, -1]])
    reoriented = ras_img.as_reoriented(transform)
    assert nib.aff2axcodes(reoriented.affine) == ("R", "A", "I")

    rai_result = _bridged_result(reoriented)

    expected_img = ras_result.labelmap.as_reoriented(transform)
    expected = np.asanyarray(expected_img.dataobj)
    actual = np.asanyarray(rai_result.labelmap.dataobj)
    assert np.array_equal(actual, expected)


# =========================================================================== #
# Named adversarial case: fuse-bridge-keeps-third-label
# =========================================================================== #


def test_fuse_bridge_keeps_third_label():
    """Guards a bridge that fills the whole span regardless of content and
    silently overwrites another label."""
    clean_img = _clean_seg_img()
    axis = si_axis(clean_img.affine)
    data = np.array(np.asanyarray(clean_img.dataobj), copy=True)
    neighbour_is_low = _facing_side(data, axis)

    moved = np.moveaxis(data, axis, -1)
    other_axes = [a for a in range(data.ndim) if a != axis]

    chosen = None
    for other_idx in np.ndindex(moved.shape[:-1]):
        gap = _column_gap(moved[other_idx], neighbour_is_low)
        if gap is None:
            continue
        lo, hi = gap
        col = moved[other_idx]
        for pos in range(lo, hi):
            if col[pos] == 0:
                chosen = (other_idx, pos)
                break
        if chosen is not None:
            break
    assert chosen is not None, "no column has a background gap -- nothing to test"

    other_idx, pos = chosen
    orig_idx = [0] * data.ndim
    for a, v in zip(other_axes, other_idx):
        orig_idx[a] = v
    orig_idx[axis] = pos
    orig_idx = tuple(orig_idx)
    assert data[orig_idx] == 0

    data[orig_idx] = 20
    mutated_img = nib.Nifti1Image(data, clean_img.affine, dtype=data.dtype)

    result = _bridged_result(mutated_img)
    out = np.asanyarray(result.labelmap.dataobj)
    assert out[orig_idx] == 20


# =========================================================================== #
# Named adversarial case: fuse-bridged-refuses-cranial-neighbour
# =========================================================================== #


def test_fuse_bridged_refuses_cranial_neighbour():
    """Guards step 4's renumbering running with the neighbour cranial of the
    target, which would relabel the target itself and leave a hole."""
    with pytest.raises(FacetInputError):
        FusePerturbation(target_label=23, neighbour_label=22, bridged=True).apply(
            _clean_seg_img(), 0
        )


# =========================================================================== #
# Named adversarial case: fuse-default-form-unchanged
# =========================================================================== #


def test_fuse_default_form_unchanged():
    """Guards the bridged branch leaking into the default that the severity
    ladder applies."""
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)

    result = FusePerturbation(target_label=22, neighbour_label=23).apply(clean_img, 0)
    output_data = np.asanyarray(result.labelmap.dataobj)

    expected = np.array(input_data, copy=True)
    expected[expected == 23] = 22
    assert np.array_equal(output_data, expected)


# =========================================================================== #
# Named adversarial case: fuse-bridged-non-mutating
# =========================================================================== #


def test_fuse_bridged_non_mutating():
    """Guards writing through an ``np.moveaxis`` view of the caller's array,
    which would corrupt the base that ``build_corpus`` hands the next recipe
    entry."""
    clean_img = _clean_seg_img()
    before = np.array(np.asanyarray(clean_img.dataobj), copy=True)

    _bridged_result(clean_img)

    after = np.asanyarray(clean_img.dataobj)
    assert np.array_equal(before, after)
