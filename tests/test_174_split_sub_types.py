"""Tests for item 174 -- mode 3's two sub-types: ``split`` re-authored to a
20 % smallest-whole-slice cap (sub-type (a), part of a vertebra carries a
neighbouring vertebra's label), and the new ``split_own_label`` operator and
corpus case (sub-type (b), part of a vertebra carries a label of its own,
with every cranial label shifted up one level).

Covers Acceptance Criteria AC1-AC10 per the item spec's Testing Strategy: one
test per AC, each recomputed live from the array / registry / manifest /
``failure_modes`` / ``traceability`` rather than a pinned literal. AC1 and
AC2 recompute the cap from the input array themselves, never reading the
``_neighbour_facing_cap`` helper under test. AC4 builds its expected array
with plain NumPy from the two committed fixtures.

Plus exactly the six adversarial cases the Testing Strategy names:
``cap-faces-a-cranial-neighbour``, ``own-label-non-mutating``,
``own-label-top-label-refused``, ``own-label-shift-to-background-refused``,
``own-label-absent-target-refused`` and
``own-label-degenerate-fraction-refused``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes, traceability
from segfacet.io import FacetInputError
from segfacet.synth.axes import si_axis
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.component_shape import SplitOwnLabelPerturbation, SplitPerturbation
from segfacet.synth.corpus import CASE_RECIPE, CORPUS_DIR, _DEFAULT_BASE_PARAMS, load_manifest
from segfacet.synth.regression import pipeline_findings, verify_case


# =========================================================================== #
# Helpers
# =========================================================================== #


def _clean_seg_img():
    return build_clean_spine(**_DEFAULT_BASE_PARAMS).seg_img


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _committed_array(case_id: str) -> np.ndarray:
    case = _manifest_case(case_id)
    fixture_path = CORPUS_DIR / case["seg_fixture"]
    img = nib.load(str(fixture_path))
    return np.asanyarray(img.dataobj)


# =========================================================================== #
# AC1: the cap is everything of the target beyond one S-I cut, on the
# neighbour's side
# =========================================================================== #


def test_ac1_cap_is_everything_beyond_one_si_cut():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)

    result = SplitPerturbation(
        target_label=23, neighbour_label=24, donated_fraction=0.2
    ).apply(clean_img, seed=0)
    output_data = np.asanyarray(result.labelmap.dataobj)

    donated_mask = (input_data == 23) & (output_data == 24)
    assert int(np.count_nonzero(donated_mask)) > 0

    donated_coords = np.argwhere(donated_mask)
    donated_axis_indices = sorted({int(v) for v in donated_coords[:, axis]})
    assert donated_axis_indices == list(
        range(donated_axis_indices[0], donated_axis_indices[-1] + 1)
    ), "donated cap is not one contiguous run along the stacking axis"

    target_coords = np.argwhere(input_data == 23)
    neighbour_coords = np.argwhere(input_data == 24)
    target_axis_min = int(target_coords[:, axis].min())
    target_axis_max = int(target_coords[:, axis].max())
    target_mean = float(target_coords[:, axis].mean())
    neighbour_mean = float(neighbour_coords[:, axis].mean())

    if neighbour_mean > target_mean:
        extreme = target_axis_max
    else:
        extreme = target_axis_min
    assert extreme in donated_axis_indices

    run_set = set(donated_axis_indices)
    axis_index_grid = np.indices(input_data.shape)[axis]
    expected_mask = (input_data == 23) & np.isin(axis_index_grid, list(run_set))
    assert np.array_equal(donated_mask, expected_mask)


# =========================================================================== #
# AC2: the cap is the smallest whole-slice cap holding at least the fraction
# =========================================================================== #


def test_ac2_cap_is_the_smallest_whole_slice_cap_holding_the_fraction():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)

    result = SplitPerturbation(
        target_label=23, neighbour_label=24, donated_fraction=0.2
    ).apply(clean_img, seed=0)
    output_data = np.asanyarray(result.labelmap.dataobj)

    donated_mask = (input_data == 23) & (output_data == 24)
    donated_coords = np.argwhere(donated_mask)
    donated_axis_indices = [int(v) for v in donated_coords[:, axis]]

    target_coords = np.argwhere(input_data == 23)
    neighbour_coords = np.argwhere(input_data == 24)
    n = target_coords.shape[0]
    target_mean = float(target_coords[:, axis].mean())
    neighbour_mean = float(neighbour_coords[:, axis].mean())

    if neighbour_mean > target_mean:
        farthest_slice = min(donated_axis_indices)
    else:
        farthest_slice = max(donated_axis_indices)

    axis_index_grid = np.indices(input_data.shape)[axis]
    farthest_count = int(
        np.count_nonzero((input_data == 23) & (axis_index_grid == farthest_slice))
    )

    assert int(np.count_nonzero(donated_mask)) >= 0.2 * n
    assert int(np.count_nonzero(donated_mask)) - farthest_count < 0.2 * n


# =========================================================================== #
# AC3: the committed ``split`` fixture gives an L4 part to L5
# =========================================================================== #


def test_ac3_committed_split_gives_an_l4_part_to_l5():
    clean_control = _committed_array("clean_control")
    split = _committed_array("split")

    diff_mask = clean_control != split
    assert int(np.count_nonzero(diff_mask)) > 0
    expected_diff_mask = (clean_control == 23) & (split == 24)
    assert np.array_equal(diff_mask, expected_diff_mask)


# =========================================================================== #
# AC4: the committed ``split_own_label`` fixture is the same cap under its
# own label, with the cranial labels shifted
# =========================================================================== #


def test_ac4_split_own_label_is_the_cap_relabelled_with_cranial_shift():
    clean_control = _committed_array("clean_control")
    split = _committed_array("split")
    split_own_label = _committed_array("split_own_label")

    diff_mask = (clean_control == 23) & (split == 24)

    expected = np.array(clean_control, copy=True)
    shift_mask = (expected <= 23) & (expected != 0)
    expected[shift_mask] = expected[shift_mask] - 1
    expected[diff_mask] = 23

    assert np.array_equal(split_own_label, expected)


# =========================================================================== #
# AC5: ``split_own_label`` is deterministic under its seed
# =========================================================================== #


def test_ac5_split_own_label_deterministic_under_seed():
    clean_img = _clean_seg_img()
    op = SplitOwnLabelPerturbation()
    result_a = op.apply(clean_img, seed=3)
    result_b = op.apply(clean_img, seed=3)

    data_a = np.asanyarray(result_a.labelmap.dataobj)
    data_b = np.asanyarray(result_b.labelmap.dataobj)
    assert np.array_equal(data_a, data_b)
    assert result_a.expectation == result_b.expectation


# =========================================================================== #
# AC6: ``split_own_label`` is attributed to mode 3
# =========================================================================== #


def test_ac6_split_own_label_attributed_to_mode_3():
    case = _manifest_case("split_own_label")
    assert case["failure_mode"] == 3


# =========================================================================== #
# AC7: ``split_own_label``'s machine-readable record holds
# =========================================================================== #


def test_ac7_split_own_label_record_verifies():
    case = _manifest_case("split_own_label")
    assert verify_case(case) is True


# =========================================================================== #
# AC8: ``split_own_label`` fires ``bounds`` and ``coverage``
# =========================================================================== #


def test_ac8_split_own_label_fires_bounds_and_coverage():
    matches = [
        c
        for c in failure_modes.SPECIFICATION[3].corpus_cases
        if c.case_id == "split_own_label"
    ]
    assert len(matches) == 1, matches
    case = matches[0]
    assert set(failure_modes.measured_firing(case)) == {"bounds", "coverage"}


# =========================================================================== #
# AC9: ``split`` fires mode 3's own detector alone
# =========================================================================== #


def test_ac9_split_fires_neighbour_contact_alone():
    case = _manifest_case("split")
    findings = pipeline_findings(case)
    pairs = {(f.rule_id, f.detector_id) for f in findings}
    assert pairs == {("fragmentation", "neighbour_contact")}


# =========================================================================== #
# AC10: the exercise report records the new operator as used by its case
# =========================================================================== #


@pytest.fixture(scope="module")
def _matrix():
    """The one ``build_matrix()`` call in this module (Testing Strategy)."""
    return traceability.build_matrix()


def test_ac10_exercise_report_records_split_own_label_as_used(_matrix):
    matches = [o for o in _matrix.exercise.operators if o.name == "split_own_label"]
    assert len(matches) == 1, matches
    record = matches[0]
    assert record.state == "used"

    expected_cases = tuple(
        sorted(
            entry.case_id
            for entry in CASE_RECIPE
            if entry.perturbation == "split_own_label"
        )
    )
    assert expected_cases != ()
    assert record.cases == expected_cases


# =========================================================================== #
# Named adversarial case: cap-faces-a-cranial-neighbour
# =========================================================================== #


def test_cap_faces_a_cranial_neighbour():
    """AC1 and AC2 only exercise a caudal neighbour; this guards a cumulative
    count taken from the low end whatever side the neighbour is actually
    on."""
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)

    result = SplitPerturbation(
        target_label=23, neighbour_label=22, donated_fraction=0.2
    ).apply(clean_img, seed=0)
    output_data = np.asanyarray(result.labelmap.dataobj)

    donated_mask = (input_data == 23) & (output_data == 22)
    assert int(np.count_nonzero(donated_mask)) > 0
    donated_coords = np.argwhere(donated_mask)
    donated_axis_indices = sorted({int(v) for v in donated_coords[:, axis]})
    assert donated_axis_indices == list(
        range(donated_axis_indices[0], donated_axis_indices[-1] + 1)
    )

    target_coords = np.argwhere(input_data == 23)
    neighbour_coords = np.argwhere(input_data == 22)
    n = target_coords.shape[0]
    target_mean = float(target_coords[:, axis].mean())
    neighbour_mean = float(neighbour_coords[:, axis].mean())

    assert neighbour_mean < target_mean
    assert min(donated_axis_indices) == target_coords[:, axis].min()

    assert int(np.count_nonzero(donated_mask)) >= 0.2 * n
    axis_index_grid = np.indices(input_data.shape)[axis]
    farthest_slice = max(donated_axis_indices)
    farthest_count = int(
        np.count_nonzero((input_data == 23) & (axis_index_grid == farthest_slice))
    )
    assert int(np.count_nonzero(donated_mask)) - farthest_count < 0.2 * n


# =========================================================================== #
# Named adversarial case: own-label-non-mutating
# =========================================================================== #


def test_own_label_non_mutating():
    """A mutating operator would corrupt the shared clean base that
    ``build_corpus`` reuses for every later ``CASE_RECIPE`` entry."""
    clean_img = _clean_seg_img()
    before = np.array(np.asanyarray(clean_img.dataobj), copy=True)
    SplitOwnLabelPerturbation(target_label=23).apply(clean_img, seed=0)
    after = np.asanyarray(clean_img.dataobj)
    assert np.array_equal(before, after)


# =========================================================================== #
# Named adversarial case: own-label-top-label-refused
# =========================================================================== #


def test_own_label_top_label_refused():
    """A cap cut toward a neighbour that does not exist would take the wrong
    end or crash on an empty neighbour."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitOwnLabelPerturbation(target_label=24).apply(clean_img, seed=0)


# =========================================================================== #
# Named adversarial case: own-label-shift-to-background-refused
# =========================================================================== #


def test_own_label_shift_to_background_refused():
    """The shift would otherwise write label 1's voxels as 0, silently
    deleting a vertebra."""
    small_img = build_clean_spine(levels=("C1", "C2", "C3")).seg_img
    with pytest.raises(FacetInputError):
        SplitOwnLabelPerturbation(target_label=2).apply(small_img, seed=0)


# =========================================================================== #
# Named adversarial case: own-label-absent-target-refused
# =========================================================================== #


def test_own_label_absent_target_refused():
    """A silent fallback to the seeded choice would make a committed fixture
    depend on the seed rather than the recipe."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitOwnLabelPerturbation(target_label=999).apply(clean_img, seed=0)


# =========================================================================== #
# Named adversarial case: own-label-degenerate-fraction-refused
# =========================================================================== #


@pytest.mark.parametrize("donated_fraction", [0.0, 1.0])
def test_own_label_degenerate_fraction_refused(donated_fraction):
    """0.0 would round up to a one-slice cap under the at-least rule and pass
    as an identity fixture; 1.0 would consume the whole target."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitOwnLabelPerturbation(
            target_label=23, donated_fraction=donated_fraction
        ).apply(clean_img, seed=0)
