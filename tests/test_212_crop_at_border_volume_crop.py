"""Tests for item 212 -- ``crop_at_border`` re-authored as a true anterior crop.

Covers Acceptance Criteria AC1-AC10 from
``docs/aide/items/212-crop-at-border-re-authored-as-a-true-anterior-crop.md``,
one test each, plus the two named adversarial cases from its Testing
Strategy: ``anterior-face-resolved-from-affine`` and
``cranio-caudal-expectation-unchanged``.

AC2 and AC3 compute the affine-located sub-block with plain NumPy from the
two images' own affines, never through ``crop_to_grid`` or the operator's
internals. AC5 and AC7 compute the face-slice label set from the array with
``resolve_face``, never through ``touches_*`` or the manifest's
``expected_labels``, because those are what is being checked.
"""

from __future__ import annotations

import re
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
import segfacet.synth.corpus as corpus_module
from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.heuristics.spline_offset import _DEFAULT_MAX_OFFSET_MM
from segfacet.pipeline import extract_feature_record
from segfacet.synth.axes import resolve_face
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import CORPUS_DIR, load_manifest
from segfacet.synth.coverage_border_overlap import CropFovPerturbation
from segfacet.synth.regression import loaded_seg_image, pipeline_findings
from segfacet.traceability import build_matrix


# =========================================================================== #
# Helpers
# =========================================================================== #


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _committed_seg_img(case_id: str) -> nib.Nifti1Image:
    return nib.load(str(CORPUS_DIR / _manifest_case(case_id)["seg_fixture"]))


def _affine_located_subblock(a_img, b_img) -> np.ndarray:
    """Item 175's definition: the affine-located sub-block of *a_img* at
    *b_img*."""
    o = np.linalg.inv(a_img.affine) @ b_img.affine[:, 3]
    o_int = np.round(o[:3]).astype(int)
    assert np.allclose(o[:3], o_int, atol=1e-6), "offset is not integral"
    assert np.allclose(a_img.affine[:3, :3], b_img.affine[:3, :3])
    o0, o1, o2 = o_int
    s0, s1, s2 = b_img.shape
    a_data = np.asanyarray(a_img.dataobj)
    return a_data[o0 : o0 + s0, o1 : o1 + s1, o2 : o2 + s2]


def _anterior_face_labels(img) -> set:
    """The non-zero labels on the anterior face slice of *img*."""
    data = np.asanyarray(img.dataobj)
    axis, side = resolve_face(img.affine, "anterior")
    index = 0 if side == "low" else data.shape[axis] - 1
    face = np.take(data, index, axis=axis)
    return {int(v) for v in np.unique(face) if v != 0}


def _anterior_crop():
    return CropFovPerturbation(
        target_label=22, face="anterior", removed_fraction=0.005
    ).apply(build_clean_spine().seg_img, 0)


def _offset_threshold() -> float:
    return float(
        bundled_default_config().rule_param(
            "spline_offset", "max_offset_mm", default=_DEFAULT_MAX_OFFSET_MM
        )
    )


def _corpus_source() -> str:
    return Path(corpus_module.__file__).read_text(encoding="utf-8")


# =========================================================================== #
# AC1: the case names the volume-crop operator
# =========================================================================== #


def test_ac1_case_names_the_volume_crop_operator():
    case = _manifest_case("crop_at_border")
    assert case["perturbation"] == "crop_fov"
    assert case["perturbation_params"]["face"] == "anterior"
    assert case["perturbation_params"]["target_label"] == 22


# =========================================================================== #
# AC2: the committed case is a crop of the clean control
# =========================================================================== #


def test_ac2_committed_case_is_a_crop_of_the_clean_control():
    cc_img = _committed_seg_img("clean_control")
    case_img = _committed_seg_img("crop_at_border")

    expected = _affine_located_subblock(cc_img, case_img)
    actual = np.asanyarray(case_img.dataobj)
    assert np.array_equal(actual, expected)

    axis, _ = resolve_face(cc_img.affine, "anterior")
    for ax in range(3):
        if ax == axis:
            assert case_img.shape[ax] < cc_img.shape[ax]
        else:
            assert case_img.shape[ax] == cc_img.shape[ax]


# =========================================================================== #
# AC3: the cut is the shallowest that reaches label 22
# =========================================================================== #


def test_ac3_cut_is_the_shallowest_that_reaches_label_22():
    cc_img = _committed_seg_img("clean_control")
    case_img = _committed_seg_img("crop_at_border")
    cc_data = np.asanyarray(cc_img.dataobj)
    axis, _ = resolve_face(cc_img.affine, "anterior")

    o = np.linalg.inv(cc_img.affine) @ case_img.affine[:, 3]
    start = int(np.round(o[axis]))
    stop = start + case_img.shape[axis]
    removed = [i for i in range(cc_data.shape[axis]) if not start <= i < stop]
    assert removed, "the cut removed no slice"

    with_22 = [i for i in removed if np.any(np.take(cc_data, i, axis=axis) == 22)]
    assert len(with_22) == 1, with_22


# =========================================================================== #
# AC4: no interior label is displaced past the threshold
# =========================================================================== #


def test_ac4_no_interior_label_displaced_past_the_threshold():
    rec = extract_feature_record(
        loaded_seg_image(_manifest_case("crop_at_border")), bundled_default_config()
    )
    # Item 215: each offset is its label's ``curve`` block.
    entries = [e["curve"] for e in rec["per_label"].values() if "curve" in e]
    interior = [e for e in entries if not e["is_terminal"]]
    assert interior, entries
    threshold = _offset_threshold()
    for entry in interior:
        assert entry["offset_mm"] <= threshold, entry


# =========================================================================== #
# AC5: the case fires border on exactly the labels on its cut face
# =========================================================================== #


def test_ac5_case_fires_border_on_exactly_the_labels_on_its_cut_face():
    case = _manifest_case("crop_at_border")
    face_labels = _anterior_face_labels(_committed_seg_img("crop_at_border"))
    assert face_labels

    triples = {
        (f.rule_id, f.detector_id, frozenset(f.labels)) for f in pipeline_findings(case)
    }
    assert triples == {
        ("border", "unexpected_clip", frozenset({label})) for label in face_labels
    }


# =========================================================================== #
# AC6: the operator expects border at an in-plane face
# =========================================================================== #


def test_ac6_operator_expects_border_at_an_in_plane_face():
    r = _anterior_crop()
    assert r.expectation.expected_rule_ids == frozenset({"border"})
    assert r.expectation.expected_verdict == "flagged-for-review"


# =========================================================================== #
# AC7: the operator's expected labels are the labels on the cut face
# =========================================================================== #


def test_ac7_operators_expected_labels_are_the_labels_on_the_cut_face():
    r = _anterior_crop()
    assert set(r.expectation.expected_labels) == _anterior_face_labels(r.labelmap)


# =========================================================================== #
# AC8: the legacy operator is recorded unused, with a reason
# =========================================================================== #


def test_ac8_legacy_operator_is_recorded_unused_with_a_reason():
    matches = [
        o for o in build_matrix().exercise.operators if o.name == "crop_at_border"
    ]
    assert len(matches) == 1, matches
    assert matches[0].state == "unused"
    assert matches[0].reason


# =========================================================================== #
# AC9: each split recipe comment names the case's live mode
# =========================================================================== #


@pytest.mark.parametrize("case_id", ["split", "split_own_label"])
def test_ac9_split_recipe_comment_names_the_live_mode(case_id):
    modes = [
        m.id
        for m in failure_modes.SPECIFICATION.values()
        if any(c.case_id == case_id for c in m.corpus_cases)
    ]
    assert len(modes) == 1, modes

    chunks = _corpus_source().split("_RecipeEntry(")
    own = [i for i, c in enumerate(chunks) if c.lstrip().startswith(f'case_id="{case_id}"')]
    assert len(own) == 1, own
    comment_lines = [
        line.strip()
        for line in chunks[own[0] - 1].splitlines()
        if line.strip().startswith("#")
    ]
    assert comment_lines
    assert f"mode {modes[0]}" in "\n".join(comment_lines)


# =========================================================================== #
# AC10: no recipe comment carries sub-type lettering
# =========================================================================== #


def test_ac10_no_recipe_comment_carries_sub_type_lettering():
    source = _corpus_source()
    start = source.index("CASE_RECIPE:")
    end = source.index("\n]\n", start)
    assert end > start
    assert re.search(r"sub-type \([a-z]\)", source[start:end]) is None


# =========================================================================== #
# Named adversarial case: anterior-face-resolved-from-affine
# =========================================================================== #


def test_anterior_face_resolved_from_affine():
    """Guards a face slice hard-coded to the last index, which passes AC7 on
    the RAS base and names the wrong (empty) slice here."""
    reoriented = build_clean_spine().seg_img.as_reoriented(
        np.array([[0, 1], [1, -1], [2, 1]])
    )
    axis, side = resolve_face(reoriented.affine, "anterior")
    assert (axis, side) == (1, "low")

    r = CropFovPerturbation(
        target_label=22, face="anterior", removed_fraction=0.005
    ).apply(reoriented, 0)
    out_data = np.asanyarray(r.labelmap.dataobj)
    low_face = {int(v) for v in np.unique(out_data[:, 0, :]) if v != 0}
    assert low_face
    assert set(r.expectation.expected_labels) == low_face


# =========================================================================== #
# Named adversarial case: cranio-caudal-expectation-unchanged
# =========================================================================== #


def test_cranio_caudal_expectation_unchanged():
    """Guards the in-plane branch leaking to every face, which would make
    ``crop_fov_si`` expect ``border``."""
    r = CropFovPerturbation(
        target_label=24, face="inferior", removed_fraction=0.65
    ).apply(build_clean_spine().seg_img, 0)
    assert r.expectation.expected_rule_ids == frozenset()
    assert set(r.expectation.expected_labels) == set()
    assert r.expectation.expected_verdict == "pass"
