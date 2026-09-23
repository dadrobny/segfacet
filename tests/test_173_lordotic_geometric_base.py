"""Tests for item 173 -- the lordotic geometric base.

Covers Acceptance Criteria AC1-AC7: the per-level sagittal tilt, the 33 mm
S-I pitch, the integrated A-P path, zero lateral curve, and the equality of
``build_clean_spine()``'s default output (array + affine) with the committed
``clean_control`` fixture, on both the geometric and intensity corpora.

Adversarial cases (Testing Strategy):

- ``tilt-oracle-responds``: the AC1 tilt-measurement helper responds to an
  externally-imposed rotation rather than returning a fixed table.
- ``coarse-spacing-margin``: at 20 mm spacing the mm-only margin still
  reaches a full voxel, so no ``touches_*`` flag fires.
- ``partial-lumbar-span-keeps-level-tilts``: a level's tilt is looked up by
  name, not by position within the span.
- ``non-lumbar-span-is-untilted``: a span outside the lumbar table stays flat.
- ``single-steepest-body-fits``: the steepest single-level span still fits
  its own worst-case half-extent with no neighbour to widen the grid.

Fixture paths are resolved through the corpora's own ``load_manifest`` /
``load_intensity_manifest`` plus their ``CORPUS_DIR`` / ``INTENSITY_CORPUS_DIR``
-- never a hardcoded path (Testing Strategy). The maintainer's per-level tilt
table is a literal here, not read from the module under test (Testing
Strategy: "Reading it from clean_gt would let a wrong constant pass").
"""

from __future__ import annotations

import math

import nibabel as nib
import numpy as np
import pytest
from nibabel.affines import apply_affine
from scipy import ndimage

from segfacet.config import bundled_default_config
from segfacet.pipeline import extract_feature_record
from segfacet.synth import build_clean_spine
from segfacet.synth.corpus import CORPUS_DIR, load_manifest
from segfacet.synth.intensity import INTENSITY_CORPUS_DIR, load_intensity_manifest

# The maintainer's decision (docs/aide/insights.md, 2026-09-22), written
# literally per the Testing Strategy -- never read from clean_gt.
_MAINTAINER_TILTS_DEG = {20: -8.0, 21: 0.0, 22: 8.0, 23: 18.0, 24: 35.0}
_LEVELS_ASCENDING = (20, 21, 22, 23, 24)


def _clean_control_seg_path():
    manifest = load_manifest()
    case = next(c for c in manifest["cases"] if c["case_id"] == "clean_control")
    return CORPUS_DIR / case["seg_fixture"]


def _intensity_clean_hu_seg_path():
    manifest = load_intensity_manifest()
    case = next(c for c in manifest["cases"] if c["case_id"] == "clean_hu")
    return INTENSITY_CORPUS_DIR / case["seg_fixture"]


def _voxel_centres_mm(img: "nib.Nifti1Image", label: int) -> np.ndarray:
    """Voxel centres (mm) of *label*'s mask, deduplicated."""
    data = np.asanyarray(img.dataobj)
    ijk = np.argwhere(data == label)
    xyz = apply_affine(img.affine, ijk)
    return np.unique(xyz, axis=0)


def _measure_tilt_deg(img: "nib.Nifti1Image", label: int) -> float:
    """AC1's minimum-area-bounding-rectangle tilt search, over (y, z).

    A plain loop over 901 angles in (-45, 45] at 0.1deg steps, per the
    Testing Strategy -- a test-local helper, never production code.
    """
    xyz = _voxel_centres_mm(img, label)
    y = xyz[:, 1]
    z = xyz[:, 2]
    y_bar = y.mean()
    z_bar = z.mean()
    dy = y - y_bar
    dz = z - z_bar

    best_theta = None
    best_area = math.inf
    steps = round((45.0 - (-45.0)) / 0.1)
    for i in range(steps + 1):
        theta_deg = -45.0 + i * 0.1
        if theta_deg <= -45.0:
            continue
        theta = math.radians(theta_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        u = dy * cos_t - dz * sin_t
        v = dy * sin_t + dz * cos_t
        area = (u.max() - u.min()) * (v.max() - v.min())
        if area < best_area:
            best_area = area
            best_theta = theta_deg
    assert best_theta is not None
    return best_theta


def _centroid_mm(img: "nib.Nifti1Image", label: int) -> np.ndarray:
    xyz = _voxel_centres_mm(img, label)
    return xyz.mean(axis=0)


# =========================================================================== #
# AC1: Each body carries its level's sagittal tilt
# =========================================================================== #


def test_ac1_each_body_carries_its_levels_sagittal_tilt():
    """AC1: measured tilt for labels 20-24 is within 1.0deg of the maintainer's
    table."""
    img = nib.load(str(_clean_control_seg_path()))
    for label, expected_deg in _MAINTAINER_TILTS_DEG.items():
        measured = _measure_tilt_deg(img, label)
        assert abs(measured - expected_deg) <= 1.0, (label, measured, expected_deg)


# =========================================================================== #
# AC2: Consecutive bodies sit 33 mm apart along S-I
# =========================================================================== #


def test_ac2_consecutive_bodies_sit_33mm_apart_along_si():
    """AC2: S-I centroid step between consecutive labels is 33.0 +/- 1.0 mm."""
    img = nib.load(str(_clean_control_seg_path()))
    for lower, higher in zip(_LEVELS_ASCENDING, _LEVELS_ASCENDING[1:]):
        z_lower = _centroid_mm(img, lower)[2]
        z_higher = _centroid_mm(img, higher)[2]
        step = z_lower - z_higher
        assert abs(step - 33.0) <= 1.0, (lower, higher, step)


# =========================================================================== #
# AC3: The A-P path is the integral of the tilts
# =========================================================================== #


def test_ac3_ap_path_is_the_integral_of_the_tilts():
    """AC3: dAP == dS * tan(mean(tilt_a, tilt_b)) within 0.5 mm, using AC1's
    literal tilts."""
    img = nib.load(str(_clean_control_seg_path()))
    for a, b in zip(_LEVELS_ASCENDING, _LEVELS_ASCENDING[1:]):
        centroid_a = _centroid_mm(img, a)
        centroid_b = _centroid_mm(img, b)
        delta = centroid_b - centroid_a
        delta_s = delta[2]
        delta_ap = delta[1]
        mean_tilt = (_MAINTAINER_TILTS_DEG[a] + _MAINTAINER_TILTS_DEG[b]) / 2.0
        expected_ap = delta_s * math.tan(math.radians(mean_tilt))
        assert abs(delta_ap - expected_ap) <= 0.5, (a, b, delta_ap, expected_ap)


# =========================================================================== #
# AC4: There is no lateral curve
# =========================================================================== #


def test_ac4_there_is_no_lateral_curve():
    """AC4: the L-R centroid spread over labels 20-24 is at most 0.5 mm."""
    img = nib.load(str(_clean_control_seg_path()))
    lr_centroids = [_centroid_mm(img, label)[0] for label in _LEVELS_ASCENDING]
    spread = max(lr_centroids) - min(lr_centroids)
    assert spread <= 0.5


# =========================================================================== #
# AC5: The default build is the committed clean control
# =========================================================================== #


def test_ac5_default_build_array_equals_committed_clean_control():
    """AC5: build_clean_spine()'s seg_img array equals the committed fixture's."""
    built = build_clean_spine()
    committed = nib.load(str(_clean_control_seg_path()))
    assert np.array_equal(
        np.asanyarray(built.seg_img.dataobj), np.asanyarray(committed.dataobj)
    )


# =========================================================================== #
# AC6: The default build's affine is the committed clean control's
# =========================================================================== #


def test_ac6_default_build_affine_equals_committed_clean_control():
    """AC6: build_clean_spine().seg_img.affine equals the committed fixture's."""
    built = build_clean_spine()
    committed = nib.load(str(_clean_control_seg_path()))
    assert np.array_equal(built.seg_img.affine, committed.affine)


# =========================================================================== #
# AC7: Both corpora sit on the same base
# =========================================================================== #


def test_ac7_both_corpora_sit_on_the_same_base():
    """AC7: the intensity corpus's clean_hu seg fixture array equals the
    geometric corpus's clean_control array."""
    geometric = nib.load(str(_clean_control_seg_path()))
    intensity = nib.load(str(_intensity_clean_hu_seg_path()))
    assert np.array_equal(
        np.asanyarray(intensity.dataobj), np.asanyarray(geometric.dataobj)
    )


# =========================================================================== #
# Adversarial case: tilt-oracle-responds
# =========================================================================== #


def test_tilt_oracle_responds_to_an_imposed_rotation():
    """The AC1 helper responds to an externally-imposed +20deg rotation of
    label 21's mask, rather than returning the expected table whatever the
    mask holds. The "wrong" angle is derived from the live measurement
    (item 171), not a literal."""
    img = nib.load(str(_clean_control_seg_path()))
    data = np.asanyarray(img.dataobj)
    baseline_tilt = _measure_tilt_deg(img, 21)

    mask = (data == 21).astype(np.uint8)
    rotated_mask = ndimage.rotate(mask, 20.0, axes=(1, 2), order=0, reshape=True)

    # Rebuild a label map holding only the rotated mask as label 21, on its
    # own (possibly resized) grid, sharing the original affine's rotation
    # and spacing.
    rotated_data = np.zeros(rotated_mask.shape, dtype=data.dtype)
    rotated_data[rotated_mask != 0] = 21
    rotated_img = nib.Nifti1Image(rotated_data, img.affine)

    rotated_tilt = _measure_tilt_deg(rotated_img, 21)
    assert abs(abs(rotated_tilt - baseline_tilt) - 20.0) <= 1.0


# =========================================================================== #
# Adversarial case: coarse-spacing-margin
# =========================================================================== #


def test_coarse_spacing_margin_touches_no_face():
    """At 20 mm spacing every label's touches_* flag stays false -- the
    margin does not collapse to zero voxels at coarse spacing."""
    clean = build_clean_spine(levels=("L1", "L2", "L3"), spacing=(20.0, 20.0, 20.0))
    record = extract_feature_record(clean.seg_img, bundled_default_config())
    per_label = record["per_label"]
    assert set(per_label.keys()) != set()
    touch_keys = (
        "touches_inferior",
        "touches_superior",
        "touches_left",
        "touches_right",
        "touches_anterior",
        "touches_posterior",
    )
    for label_key, label_record in per_label.items():
        geometry = label_record["geometry"]
        for key in touch_keys:
            assert geometry[key] is False, (label_key, key)


# =========================================================================== #
# Adversarial case: partial-lumbar-span-keeps-level-tilts
# =========================================================================== #


def test_partial_lumbar_span_keeps_level_tilts():
    """L3-L5 built alone still measure 8/18/35deg -- the tilt is looked up by
    level name, not by position within the span."""
    clean = build_clean_spine(levels=("L3", "L4", "L5"))
    labels_by_level = dict(zip(clean.level_names, clean.labels))
    expected = {"L3": 8.0, "L4": 18.0, "L5": 35.0}
    for level, expected_deg in expected.items():
        measured = _measure_tilt_deg(clean.seg_img, labels_by_level[level])
        assert abs(measured - expected_deg) <= 1.0, (level, measured, expected_deg)


# =========================================================================== #
# Adversarial case: non-lumbar-span-is-untilted
# =========================================================================== #


def test_non_lumbar_span_is_untilted():
    """A thoracic span (T5-T10) stays untilted and keeps the 33 mm pitch --
    the lookup does not fall back to the lumbar table for an unnamed level."""
    clean = build_clean_spine(levels=("T5", "T6", "T7", "T8", "T9", "T10"))
    for label in clean.labels:
        measured = _measure_tilt_deg(clean.seg_img, label)
        assert abs(measured - 0.0) <= 1.0, (label, measured)

    for lower, higher in zip(clean.labels, clean.labels[1:]):
        z_lower = _centroid_mm(clean.seg_img, lower)[2]
        z_higher = _centroid_mm(clean.seg_img, higher)[2]
        step = z_lower - z_higher
        assert abs(step - 33.0) <= 1.0, (lower, higher, step)


# =========================================================================== #
# Adversarial case: single-steepest-body-fits
# =========================================================================== #


def test_single_steepest_body_fits():
    """L5 alone (the steepest tilt, no neighbour to widen the grid) yields
    one component and no touches_* flag set."""
    clean = build_clean_spine(levels=("L5",))
    record = extract_feature_record(clean.seg_img, bundled_default_config())
    per_label = record["per_label"]
    assert len(per_label) == 1
    label_record = next(iter(per_label.values()))
    assert label_record["components"]["component_count"] == 1
    touch_keys = (
        "touches_inferior",
        "touches_superior",
        "touches_left",
        "touches_right",
        "touches_anterior",
        "touches_posterior",
    )
    geometry = label_record["geometry"]
    for key in touch_keys:
        assert geometry[key] is False, key
