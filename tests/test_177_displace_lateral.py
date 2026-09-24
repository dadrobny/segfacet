"""Tests for item 177 -- ``DisplacePerturbation`` gains an ``ap_angle_deg:
Optional[float] = None`` keyword (``src/segfacet/synth/identity_ordering_alignment.py``).
With a value, the translation is resolved anatomically: ``displacement_mm *
cos(theta)`` toward the **right** face and ``displacement_mm * sin(theta)``
toward the **anterior** face, each rounded to whole voxels on its own axis,
with nothing moved along the stacking axis. The default (``None``) stays
today's diagonal array-axis split, byte for byte, for the severity ladder.
The corpus ``displace`` case now applies the lateral form
(``target_label=22, displacement_mm=15.0, ap_angle_deg=20.0``), realising 14
voxels right and 5 voxels anterior.

Covers Acceptance Criteria AC1-AC5 per the item spec's Testing Strategy: one
test per AC. AC1/AC2 apply the lateral operator directly to
``build_clean_spine().seg_img``, resolving every axis and side from its
affine through ``segfacet.synth.axes`` -- never assumed. AC3 compares against
the committed ``clean_control``/``displace`` fixtures, resolved through
``load_manifest``/``loaded_seg_image``, never a hard-coded path. AC4 uses
``compute_centroid`` on both committed fixtures. AC5 uses
``failure_modes.measured_firing`` against the live ``SPECIFICATION``.

Plus exactly the five adversarial cases the Testing Strategy names:
``displace-lateral-resolves-axes``, ``displace-lateral-resolves-side``,
``displace-lateral-refuses-low-overflow``, ``displace-default-form-unchanged``
and ``displace-lateral-non-mutating``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes
from segfacet.features.centroids import compute_centroid
from segfacet.io import FacetInputError
from segfacet.synth.axes import non_stacking_axes, resolve_face, si_axis
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import load_manifest
from segfacet.synth.identity_ordering_alignment import DisplacePerturbation
from segfacet.synth.regression import loaded_seg_image


# =========================================================================== #
# Helpers
# =========================================================================== #


def _clean_seg_img():
    return build_clean_spine().seg_img


def _lateral_result(seg_img):
    return DisplacePerturbation(
        target_label=22, displacement_mm=15.0, ap_angle_deg=20.0
    ).apply(seg_img, seed=0)


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


# =========================================================================== #
# AC1: the target moves 14 right, 5 anterior, 0 along the stack
# =========================================================================== #


def test_ac1_target_moves_14_right_5_anterior_0_along_stack():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = _lateral_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    lr_axis, lr_side = resolve_face(clean_img.affine, "right")
    ap_axis, ap_side = resolve_face(clean_img.affine, "anterior")

    input_coords = np.argwhere(input_data == 22)
    assert input_coords.size > 0, "label 22 not present in the default base"

    expected_coords = input_coords.copy()
    expected_coords[:, lr_axis] += 14 if lr_side == "high" else -14
    expected_coords[:, ap_axis] += 5 if ap_side == "high" else -5

    expected = set(map(tuple, expected_coords))
    actual = set(map(tuple, np.argwhere(output_data == 22)))
    assert actual == expected


# =========================================================================== #
# AC2: nothing else moves
# =========================================================================== #


def test_ac2_nothing_else_moves():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = _lateral_result(clean_img)
    output_data = np.asanyarray(result.labelmap.dataobj)

    label22_mask = (input_data == 22) | (output_data == 22)
    untouched = ~label22_mask
    assert np.any(untouched), "the label-22 masks cover the whole volume"
    assert np.array_equal(output_data[untouched], input_data[untouched])


# =========================================================================== #
# AC3: the committed fixture is the lateral operator's output
# =========================================================================== #


def test_ac3_committed_fixture_is_the_lateral_operators_output():
    clean_case = _manifest_case("clean_control")
    displace_case = _manifest_case("displace")

    result = _lateral_result(loaded_seg_image(clean_case))
    actual = np.asanyarray(result.labelmap.dataobj)
    committed = np.asanyarray(loaded_seg_image(displace_case).dataobj)

    assert np.array_equal(actual, committed)


# =========================================================================== #
# AC4: the committed displacement is mostly left-right
# =========================================================================== #


def test_ac4_committed_displacement_is_mostly_left_right():
    clean_case = _manifest_case("clean_control")
    displace_case = _manifest_case("displace")

    clean_centroid = compute_centroid(loaded_seg_image(clean_case), 22).centroid_mm
    displace_centroid = compute_centroid(loaded_seg_image(displace_case), 22).centroid_mm

    delta = tuple(d - c for d, c in zip(displace_centroid, clean_centroid))
    assert delta == pytest.approx((14.0, 5.0, 0.0), abs=1e-9)


# =========================================================================== #
# AC5: the expected set equals the measured firing
# =========================================================================== #


def test_ac5_expected_set_equals_measured_firing():
    matches = [
        c for c in failure_modes.SPECIFICATION[1].corpus_cases if c.case_id == "displace"
    ]
    assert len(matches) == 1, matches
    case = matches[0]
    assert failure_modes.measured_firing(case) == case.expected_firing == ("mislabel",)


# =========================================================================== #
# Named adversarial case: displace-lateral-resolves-axes
# =========================================================================== #


def test_displace_lateral_resolves_axes():
    """Guards taking the L-R axis as ``non_stacking_axes(...)[0]``, which is
    L-R only on RAS: that passes AC1-AC4 and fails here."""
    ras_img = _clean_seg_img()
    ras_result = _lateral_result(ras_img)

    transform = np.array([[1, 1], [0, 1], [2, 1]])
    reoriented = ras_img.as_reoriented(transform)
    assert nib.aff2axcodes(reoriented.affine) == ("A", "R", "S")

    reoriented_result = _lateral_result(reoriented)

    expected_img = ras_result.labelmap.as_reoriented(transform)
    expected = np.asanyarray(expected_img.dataobj)
    actual = np.asanyarray(reoriented_result.labelmap.dataobj)
    assert np.array_equal(actual, expected)


# =========================================================================== #
# Named adversarial case: displace-lateral-resolves-side
# =========================================================================== #


def test_displace_lateral_resolves_side():
    """Guards a shift hard-coded toward the high index, as the diagonal
    branch does."""
    ras_img = _clean_seg_img()
    ras_result = _lateral_result(ras_img)

    transform = np.array([[0, -1], [1, 1], [2, 1]])
    reoriented = ras_img.as_reoriented(transform)
    assert nib.aff2axcodes(reoriented.affine) == ("L", "A", "S")

    reoriented_result = _lateral_result(reoriented)

    expected_img = ras_result.labelmap.as_reoriented(transform)
    expected = np.asanyarray(expected_img.dataobj)
    actual = np.asanyarray(reoriented_result.labelmap.dataobj)
    assert np.array_equal(actual, expected)


# =========================================================================== #
# Named adversarial case: displace-lateral-refuses-low-overflow
# =========================================================================== #


def test_displace_lateral_refuses_low_overflow():
    """Guards a fit check on the high end only, which would let the lateral
    branch write past index 0."""
    ras_img = _clean_seg_img()
    transform = np.array([[0, -1], [1, 1], [2, 1]])
    reoriented = ras_img.as_reoriented(transform)
    assert nib.aff2axcodes(reoriented.affine) == ("L", "A", "S")

    with pytest.raises(FacetInputError):
        DisplacePerturbation(
            target_label=22, displacement_mm=15.0, ap_angle_deg=0.0
        ).apply(reoriented, 0)


# =========================================================================== #
# Named adversarial case: displace-default-form-unchanged
# =========================================================================== #


def test_displace_default_form_unchanged():
    """Guards the lateral branch leaking into the default the severity
    ladder applies; ``tests/test_100_*`` pins the ladder's responses, not
    the operator's exact transform."""
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis_a, axis_b = non_stacking_axes(clean_img.affine)

    result = DisplacePerturbation(target_label=22).apply(clean_img, 0)
    output_data = np.asanyarray(result.labelmap.dataobj)

    label22_in = input_data == 22
    input_coords = np.argwhere(label22_in)
    assert input_coords.size > 0, "label 22 not present in the default base"

    expected_coords = input_coords.copy()
    expected_coords[:, axis_a] += 13
    expected_coords[:, axis_b] += 13
    expected = set(map(tuple, expected_coords))
    actual = set(map(tuple, np.argwhere(output_data == 22)))
    assert actual == expected

    untouched = ~(label22_in | (output_data == 22))
    assert np.any(untouched)
    assert np.array_equal(output_data[untouched], input_data[untouched])


# =========================================================================== #
# Named adversarial case: displace-lateral-non-mutating
# =========================================================================== #


def test_displace_lateral_non_mutating():
    """Guards writing the shift into the caller's array, which would corrupt
    the base that ``build_corpus`` hands the next recipe entry."""
    clean_img = _clean_seg_img()
    before = np.array(np.asanyarray(clean_img.dataobj), copy=True)

    _lateral_result(clean_img)

    after = np.asanyarray(clean_img.dataobj)
    assert np.array_equal(before, after)
