"""Tests for item 175 -- ``crop_fov`` as a real crop of the volume (S-I FOV
truncation), and the new ``crop_fov_si`` corpus case.

Covers Acceptance Criteria AC1-AC11 from
``docs/aide/items/175-crop-at-border-as-a-crop-of-the-volume.md``, one test
each, plus the six named adversarial cases from its Testing Strategy:
``crop-resolves-face-from-affine``, ``crop-output-not-a-view``,
``crop-degenerate-fraction-refused``, ``crop-whole-target-refused``,
``crop-absent-target-refused`` and ``grid-helper-refuses-non-subgrid``.

AC1, AC3, AC4 and AC8 compute the affine-located sub-block with plain NumPy
from the two images' own affines (the spec's own algorithm, ``o = inv(A.affine)
@ B.affine[:, 3]``), never through ``crop_to_grid`` or the operator's
internals. AC5-AC7 go through ``extract_feature_record`` on the committed
fixtures, loaded via ``loaded_seg_image`` per the Testing Strategy. Which end
of the stacking axis is "inferior" is always resolved live with
``segfacet.synth.axes.resolve_face``/``si_axis`` on the image's own affine,
never assumed (the item spec's "Stacking axis" note).
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.io import FacetInputError
from segfacet.pipeline import extract_feature_record
from segfacet.synth.axes import resolve_face, si_axis
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import CORPUS_DIR, crop_to_grid, load_manifest
from segfacet.synth.coverage_border_overlap import CropFovPerturbation
from segfacet.synth.regression import loaded_seg_image, pipeline_findings

_TOUCH_FLAGS = (
    "touches_inferior",
    "touches_superior",
    "touches_left",
    "touches_right",
    "touches_anterior",
    "touches_posterior",
)


# =========================================================================== #
# Helpers
# =========================================================================== #


def _default_base() -> nib.Nifti1Image:
    """"The default base" (item spec's term)."""
    return build_clean_spine().seg_img


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _committed_seg_img(case_id: str) -> nib.Nifti1Image:
    return nib.load(str(CORPUS_DIR / _manifest_case(case_id)["seg_fixture"]))


def _committed_scan_img(case_id: str) -> nib.Nifti1Image:
    return nib.load(str(CORPUS_DIR / _manifest_case(case_id)["scan_fixture"]))


def _affine_located_subblock(a_img, b_img) -> np.ndarray:
    """The item spec's own definition: the affine-located sub-block of
    *a_img* at *b_img*."""
    o = np.linalg.inv(a_img.affine) @ b_img.affine[:, 3]
    o_int = np.round(o[:3]).astype(int)
    assert np.allclose(o[:3], o_int, atol=1e-6), "offset is not integral"
    assert np.allclose(a_img.affine[:3, :3], b_img.affine[:3, :3])
    o0, o1, o2 = o_int
    s0, s1, s2 = b_img.shape
    a_data = np.asanyarray(a_img.dataobj)
    return a_data[o0 : o0 + s0, o1 : o1 + s1, o2 : o2 + s2]


# =========================================================================== #
# AC1: crop_fov is a crop, not a translation
# =========================================================================== #


def test_ac1_crop_fov_is_a_crop_not_a_translation():
    base_img = _default_base()
    result = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(base_img, 0)
    out_img = result.labelmap

    expected = _affine_located_subblock(base_img, out_img)
    actual = np.asanyarray(out_img.dataobj)
    assert np.array_equal(actual, expected)


# =========================================================================== #
# AC2: the target is cut by the requested face
# =========================================================================== #


def test_ac2_target_is_cut_by_the_requested_face():
    base_img = _default_base()
    result = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(base_img, 0)
    out_img = result.labelmap
    out_data = np.asanyarray(out_img.dataobj)

    axis, side = resolve_face(out_img.affine, "inferior")
    index = 0 if side == "low" else out_data.shape[axis] - 1
    face_slice = np.take(out_data, index, axis=axis)
    assert np.any(face_slice == 24)


# =========================================================================== #
# AC3: the cut is the smallest whole-slice cut removing at least the fraction
# =========================================================================== #


def test_ac3_smallest_whole_slice_cut_removing_at_least_the_fraction():
    base_img = _default_base()
    base_data = np.asanyarray(base_img.dataobj)
    axis, side = resolve_face(base_img.affine, "inferior")
    n = int(np.count_nonzero(base_data == 24))

    result = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(base_img, 0)
    out_data = np.asanyarray(result.labelmap.dataobj)

    r = n - int(np.count_nonzero(out_data == 24))
    assert r >= 0.65 * n

    cut = base_data.shape[axis] - out_data.shape[axis]
    assert cut >= 1
    nearest_kept_index = cut - 1 if side == "low" else base_data.shape[axis] - cut

    axis_grid = np.indices(base_data.shape)[axis]
    nearest_slice_count = int(
        np.count_nonzero((base_data == 24) & (axis_grid == nearest_kept_index))
    )
    assert r - nearest_slice_count < 0.65 * n


# =========================================================================== #
# AC4: the committed crop_fov_si fixture is a volume crop of clean_control
# =========================================================================== #


def test_ac4_committed_fixture_is_a_volume_crop_of_clean_control():
    cc_img = _committed_seg_img("clean_control")
    cf_img = _committed_seg_img("crop_fov_si")

    expected = _affine_located_subblock(cc_img, cf_img)
    actual = np.asanyarray(cf_img.dataobj)
    assert np.array_equal(actual, expected)

    axis = si_axis(cc_img.affine)
    assert cf_img.shape[axis] < cc_img.shape[axis]


# =========================================================================== #
# AC5: the truncated L5's volume
# =========================================================================== #


def test_ac5_truncated_l5_volume():
    config = bundled_default_config()
    cc_rec = extract_feature_record(loaded_seg_image(_manifest_case("clean_control")), config)
    cf_rec = extract_feature_record(loaded_seg_image(_manifest_case("crop_fov_si")), config)

    cc_volume = cc_rec["per_label"]["24"]["geometry"]["physical_volume_mm3"]
    cf_volume = cf_rec["per_label"]["24"]["geometry"]["physical_volume_mm3"]
    assert cf_volume <= 0.35 * cc_volume


# =========================================================================== #
# AC6: the truncated L5's S-I extent
# =========================================================================== #


def test_ac6_truncated_l5_si_extent():
    config = bundled_default_config()
    cc_rec = extract_feature_record(loaded_seg_image(_manifest_case("clean_control")), config)
    cf_rec = extract_feature_record(loaded_seg_image(_manifest_case("crop_fov_si")), config)

    cc_extent_z = cc_rec["per_label"]["24"]["geometry"]["extent_z_mm"]
    cf_extent_z = cf_rec["per_label"]["24"]["geometry"]["extent_z_mm"]
    assert cf_extent_z < cc_extent_z


# =========================================================================== #
# AC7: only the inferior face is touched
# =========================================================================== #


def test_ac7_only_the_inferior_face_is_touched():
    rec = extract_feature_record(
        loaded_seg_image(_manifest_case("crop_fov_si")), bundled_default_config()
    )
    touched = set()
    for label, entry in rec["per_label"].items():
        geometry = entry["geometry"]
        for flag in _TOUCH_FLAGS:
            if geometry[flag]:
                touched.add((label, flag))
    assert touched == {("24", "touches_inferior")}


# =========================================================================== #
# AC8: the case's scan is the base scan on the case's grid
# =========================================================================== #


def test_ac8_case_scan_is_the_base_scan_on_the_case_grid():
    seg_img = _committed_seg_img("crop_fov_si")
    scan_img = _committed_scan_img("crop_fov_si")

    assert scan_img.shape == seg_img.shape
    assert np.allclose(scan_img.affine, seg_img.affine)

    cc_scan_img = _committed_scan_img("clean_control")
    expected = _affine_located_subblock(cc_scan_img, scan_img)
    actual = np.asanyarray(scan_img.dataobj)
    assert np.array_equal(actual, expected)


# =========================================================================== #
# AC9: the case fires bounds on the remnant and nothing else
# =========================================================================== #


def test_ac9_case_fires_bounds_on_the_remnant_and_nothing_else():
    case = _manifest_case("crop_fov_si")
    findings = pipeline_findings(case)
    triples = {(f.rule_id, f.detector_id, frozenset(f.labels)) for f in findings}
    assert triples == {("bounds", "metric_out_of_range", frozenset({24}))}


# =========================================================================== #
# AC10: both crops are the condition's fixtures
# =========================================================================== #


def test_ac10_both_crops_are_the_conditions_fixtures():
    condition = failure_modes.CONDITIONS["fov_truncation"]
    spec_ids = {c.case_id for c in condition.corpus_cases}
    manifest_ids = {
        c["case_id"]
        for c in load_manifest()["cases"]
        if c["condition"] == "fov_truncation"
    }
    assert spec_ids == manifest_ids
    assert spec_ids == {"crop_at_border", "crop_fov_si"}


# =========================================================================== #
# AC11: a committed case still fires border
# =========================================================================== #


def test_ac11_a_committed_case_still_fires_border():
    condition = failure_modes.CONDITIONS["fov_truncation"]
    matches = [c for c in condition.corpus_cases if c.case_id == "crop_at_border"]
    assert len(matches) == 1, matches
    assert "border" in set(failure_modes.measured_firing(matches[0]))


# =========================================================================== #
# Named adversarial case: crop-resolves-face-from-affine
# =========================================================================== #


def test_crop_resolves_face_from_affine():
    """Guards a hard-coded low-end cut ([:, :, cut:], as in the prototype),
    which passes AC1-AC3 on the RAS base and fails here."""
    reoriented = build_clean_spine().seg_img.as_reoriented(
        np.array([[0, 1], [1, 1], [2, -1]])
    )
    assert nib.aff2axcodes(reoriented.affine) == ("R", "A", "I")

    result = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(reoriented, 0)
    out_img = result.labelmap

    expected = _affine_located_subblock(reoriented, out_img)
    actual = np.asanyarray(out_img.dataobj)
    assert np.array_equal(actual, expected)

    axis, side = resolve_face(out_img.affine, "inferior")
    assert side == "high"
    last_slice = np.take(actual, actual.shape[axis] - 1, axis=axis)
    assert np.any(last_slice == 24)


# =========================================================================== #
# Named adversarial case: crop-output-not-a-view
# =========================================================================== #


def test_crop_output_not_a_view():
    """Guards returning slicer's view, which would let a later edit of a
    case corrupt the base that build_corpus hands the next recipe entry."""
    base_img = _default_base()
    before = np.array(np.asanyarray(base_img.dataobj), copy=True)

    result = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(base_img, 0)
    out_data = np.asanyarray(result.labelmap.dataobj)
    out_data[0, 0, 0] = 999

    after = np.asanyarray(base_img.dataobj)
    assert np.array_equal(before, after)


# =========================================================================== #
# Named adversarial case: crop-degenerate-fraction-refused
# =========================================================================== #


@pytest.mark.parametrize("removed_fraction", [0.0, 1.0])
def test_crop_degenerate_fraction_refused(removed_fraction):
    """0.0 would round up to a one-slice cut under the at-least rule and
    pass as an identity "crop"; 1.0 would consume the whole target."""
    base_img = _default_base()
    with pytest.raises(FacetInputError):
        CropFovPerturbation(
            target_label=24, face="inferior", removed_fraction=removed_fraction
        ).apply(base_img, 0)


# =========================================================================== #
# Named adversarial case: crop-whole-target-refused
# =========================================================================== #


def test_crop_whole_target_refused():
    """Guards a returned map that silently lacks its target label.

    The fraction is derived live from the input array (spec correction,
    2026-09-24) rather than a literal: every slice but the farthest from
    the face holds fewer than ``fraction * n`` voxels, so the at-least walk
    must take every slice.
    """
    base_img = _default_base()
    base_data = np.asanyarray(base_img.dataobj)
    axis, side = resolve_face(base_img.affine, "inferior")

    axis_vals = np.argwhere(base_data == 24)[:, axis]
    distinct_indices = np.sort(np.unique(axis_vals))
    if side == "high":
        distinct_indices = distinct_indices[::-1]

    axis_grid = np.indices(base_data.shape)[axis]
    counts = [
        int(np.count_nonzero((base_data == 24) & (axis_grid == idx)))
        for idx in distinct_indices
    ]
    n = sum(counts)
    c_far = counts[-1]
    fraction = (n - c_far + 0.5) / n
    assert 0 < fraction < 1

    cumulative = 0
    slices_needed = 0
    for count in counts:
        cumulative += count
        slices_needed += 1
        if cumulative >= fraction * n:
            break
    # Reaching `fraction` needs every slice of label 24 -- the defect this
    # test guards would silently return a map missing the target altogether.
    assert slices_needed == len(distinct_indices)

    with pytest.raises(FacetInputError):
        CropFovPerturbation(
            target_label=24, face="inferior", removed_fraction=fraction
        ).apply(base_img, 0)


# =========================================================================== #
# Named adversarial case: crop-absent-target-refused
# =========================================================================== #


def test_crop_absent_target_refused():
    """Guards a silent fallback to the seeded choice."""
    base_img = _default_base()
    with pytest.raises(FacetInputError):
        CropFovPerturbation(
            target_label=999, face="inferior", removed_fraction=0.65
        ).apply(base_img, 0)


# =========================================================================== #
# Named adversarial case: grid-helper-refuses-non-subgrid
# =========================================================================== #


def test_grid_helper_refuses_non_subgrid():
    """Guards rounding a non-integral offset to a wrong slab, which would
    pair a case with a shifted ground truth in every re-derived cohort
    builder."""
    base_img = _default_base()
    voxel_step = base_img.affine[:3, 0]  # one voxel step along array axis 0
    shifted_affine = np.array(base_img.affine, copy=True)
    shifted_affine[:3, 3] = shifted_affine[:3, 3] + 0.5 * voxel_step

    grid_shape = (base_img.shape[0] - 1, base_img.shape[1], base_img.shape[2])
    grid_data = np.zeros(grid_shape, dtype=np.int16)
    grid_img = nib.Nifti1Image(grid_data, shifted_affine)

    with pytest.raises(FacetInputError):
        crop_to_grid(base_img, grid_img)
