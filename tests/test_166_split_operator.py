"""Tests for item 166 -- a ``split`` perturbation operator and mode 3's first
committed corpus case.

Mode 3 ("split vertebra segment") had no corpus case at all before this item
(``SPECIFICATION[3].corpus_cases == ()``). This item adds the ``split``
operator (donates a contiguous end-slab of one label's voxels to its
neighbour, along the affine-resolved stacking axis) and one committed
geometric corpus case built from it, with the case's ``expected_firing``
authored from the measured firing so item 163's specificity ratchet stays
green.

Covers Acceptance Criteria AC1-AC9 per the item spec's Testing Strategy: one
test per AC, each recomputed from the live array / registry / manifest /
``failure_modes`` rather than a pinned literal. Plus exactly the eight
adversarial cases the Testing Strategy names:
``non-mutating-apply``, ``explicit-non-adjacent-pair-refused``,
``absent-label-refused``, ``degenerate-fraction-refused``,
``target-stays-one-component``, ``expected-labels-equal-the-fired-labels``,
``bounds-stays-silent-on-the-donor`` and ``mode-3-intended-rules-unchanged``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes, traceability
from segfacet.catalogue import build_catalogue
from segfacet.config import bundled_default_config
from segfacet.features.components import compute_components
from segfacet.features.geometry import compute_label_geometry
from segfacet.heuristics.bounds import DEFAULT_BOUNDS
from segfacet.io import FacetInputError
from segfacet.synth import (
    FAILURE_MODE_NAMES,
    Perturbation,
    build_clean_spine,
    get_perturbation,
    perturbation_names,
)
from segfacet.synth.axes import si_axis
from segfacet.synth.component_shape import SplitPerturbation
from segfacet.synth.corpus import CORPUS_DIR, _DEFAULT_BASE_PARAMS, load_manifest
from segfacet.synth.regression import offending_labels_match


# =========================================================================== #
# Helpers
# =========================================================================== #


def _clean_seg_img():
    return build_clean_spine(**_DEFAULT_BASE_PARAMS).seg_img


def _split_case_dict():
    """The one committed manifest case whose ``perturbation == "split"``."""
    matches = [
        c for c in load_manifest()["cases"] if c["perturbation"] == "split"
    ]
    assert len(matches) == 1, matches
    return matches[0]


def _split_corpus_case_expectation():
    """The one ``CorpusCaseExpectation`` mode 3 carries for the split case."""
    matches = [
        c
        for c in failure_modes.SPECIFICATION[3].corpus_cases
        if c.case_id == "split"
    ]
    assert len(matches) == 1, matches
    return matches[0]


# =========================================================================== #
# AC1: registration
# =========================================================================== #


def test_ac1_operator_registered_under_split():
    assert "split" in perturbation_names()
    cls = get_perturbation("split")
    assert issubclass(cls, Perturbation)
    assert cls.name == "split"


# =========================================================================== #
# AC2: exactly the donated voxels change, and only from target to neighbour
# =========================================================================== #


def test_ac2_split_reassigns_target_voxels_and_changes_nothing_else():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    result = SplitPerturbation(target_label=22, neighbour_label=23).apply(
        clean_img, seed=0
    )
    output_data = np.asanyarray(result.labelmap.dataobj)

    changed_mask = input_data != output_data
    donated_mask = (input_data == 22) & (output_data == 23)
    assert np.array_equal(changed_mask, donated_mask)
    assert int(np.count_nonzero(donated_mask)) > 0


# =========================================================================== #
# AC3: the donated voxels form a contiguous end-slab on the neighbour's side
# of the affine-resolved stacking axis
# =========================================================================== #


def test_ac3_donated_slab_is_contiguous_on_the_neighbours_side():
    clean_img = _clean_seg_img()
    input_data = np.asanyarray(clean_img.dataobj)
    axis = si_axis(clean_img.affine)

    result = SplitPerturbation(target_label=22, neighbour_label=23).apply(
        clean_img, seed=0
    )
    output_data = np.asanyarray(result.labelmap.dataobj)

    donated_coords = np.argwhere((input_data == 22) & (output_data == 23))
    assert donated_coords.size > 0, "no donated voxels found"
    donated_axis_indices = sorted({int(v) for v in donated_coords[:, axis]})
    assert donated_axis_indices == list(
        range(donated_axis_indices[0], donated_axis_indices[-1] + 1)
    ), "donated slab is not contiguous along the stacking axis"

    target_coords = np.argwhere(input_data == 22)
    neighbour_coords = np.argwhere(input_data == 23)
    target_axis_min = int(target_coords[:, axis].min())
    target_axis_max = int(target_coords[:, axis].max())
    target_mean = float(target_coords[:, axis].mean())
    neighbour_mean = float(neighbour_coords[:, axis].mean())

    if neighbour_mean > target_mean:
        assert donated_axis_indices[-1] == target_axis_max, (
            "neighbour lies at higher stacking-axis indices, but the "
            "donated slab is not at the target's high end"
        )
    else:
        assert donated_axis_indices[0] == target_axis_min, (
            "neighbour lies at lower stacking-axis indices, but the "
            "donated slab is not at the target's low end"
        )


# =========================================================================== #
# AC4: deterministic under its seed
# =========================================================================== #


def test_ac4_operator_deterministic_under_seed():
    clean_img = _clean_seg_img()
    op = SplitPerturbation(target_label=22, neighbour_label=23)
    result_a = op.apply(clean_img, seed=0)
    result_b = op.apply(clean_img, seed=0)
    data_a = np.asanyarray(result_a.labelmap.dataobj)
    data_b = np.asanyarray(result_b.labelmap.dataobj)
    assert np.array_equal(data_a, data_b)


# =========================================================================== #
# AC5: no adjacent neighbour is refused
# =========================================================================== #


def test_ac5_no_adjacent_neighbour_refused():
    single_label_img = build_clean_spine(levels=["L1"]).seg_img
    with pytest.raises(FacetInputError):
        SplitPerturbation().apply(single_label_img, seed=0)


# =========================================================================== #
# AC6: the Expectation attributes the case to mode 3
# =========================================================================== #


def test_ac6_expectation_attributes_case_to_mode_3():
    clean_img = _clean_seg_img()
    result = SplitPerturbation(target_label=22, neighbour_label=23).apply(
        clean_img, seed=0
    )
    assert result.expectation.failure_mode == 3
    assert result.expectation.failure_mode_name == FAILURE_MODE_NAMES[3]


# =========================================================================== #
# AC7: the committed geometric corpus carries the case
# =========================================================================== #


def test_ac7_committed_geometric_corpus_carries_the_case():
    case = _split_case_dict()
    assert case["failure_mode"] == 3
    assert case["detection"] == "pipeline"
    fixture_path = CORPUS_DIR / case["seg_fixture"]
    assert fixture_path.is_file(), f"missing committed fixture: {fixture_path}"


# =========================================================================== #
# AC8: authored expected firing equals measured firing, and both are
# {"fragmentation"}
# =========================================================================== #


def test_ac8_authored_expected_firing_equals_measured_firing():
    case = _split_corpus_case_expectation()
    measured = set(failure_modes.measured_firing(case))
    assert measured == set(case.expected_firing) == {"fragmentation"}


# =========================================================================== #
# AC9: mode 3's recorded state against the fully-specified bar
# =========================================================================== #


def test_ac9_mode_3_recorded_state_against_the_fully_specified_bar():
    catalogue = build_catalogue(strict=True)
    bar = traceability.bar_conditions(3, catalogue=catalogue)
    assert tuple(c.met for c in bar) == (True, False, False, False, False)

    condition_1 = [c for c in bar if c.number == 1]
    assert len(condition_1) == 1, condition_1
    completeness_fields = {
        "definition",
        "discriminator",
        "scope",
        "observability",
        "severity",
        "candidate_features",
        "intended_rules",
        "corpus_cases",
    }
    assert set(condition_1[0].subjects) == completeness_fields


# =========================================================================== #
# Named adversarial case: non-mutating-apply
# =========================================================================== #


def test_non_mutating_apply():
    """A mutating operator corrupts the shared clean base that
    ``build_corpus`` reuses for every later ``CASE_RECIPE`` entry, silently
    changing other cases' committed fixtures."""
    clean_img = _clean_seg_img()
    before = np.array(np.asanyarray(clean_img.dataobj), copy=True)
    SplitPerturbation(target_label=22, neighbour_label=23).apply(clean_img, seed=0)
    after = np.asanyarray(clean_img.dataobj)
    assert np.array_equal(before, after)


# =========================================================================== #
# Named adversarial case: explicit-non-adjacent-pair-refused
# =========================================================================== #


def test_explicit_non_adjacent_pair_refused():
    """Without the adjacency guard a "split" onto a non-adjacent level
    produces a mode-14-shaped fixture filed under mode 3."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitPerturbation(target_label=22, neighbour_label=24).apply(
            clean_img, seed=0
        )


# =========================================================================== #
# Named adversarial case: absent-label-refused
# =========================================================================== #


def test_absent_label_refused():
    """Silently falling back to ``_choose_adjacent_pair`` would make the
    committed fixture depend on the seed instead of the recipe."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitPerturbation(target_label=999, neighbour_label=23).apply(
            clean_img, seed=0
        )


# =========================================================================== #
# Named adversarial case: degenerate-fraction-refused
# =========================================================================== #


@pytest.mark.parametrize("donated_fraction", [0.0, 1.0])
def test_degenerate_fraction_refused(donated_fraction):
    """A zero-donation split is an identity fixture that passes every
    structural check while expressing nothing; a full-donation split leaves
    the target no voxels."""
    clean_img = _clean_seg_img()
    with pytest.raises(FacetInputError):
        SplitPerturbation(
            target_label=22, neighbour_label=23, donated_fraction=donated_fraction
        ).apply(clean_img, seed=0)


# =========================================================================== #
# Named adversarial case: target-stays-one-component
# =========================================================================== #


def test_target_stays_one_component():
    """A slab cut that fragmented the donor too would fire fragmentation on
    both labels and stop the case being a split."""
    clean_img = _clean_seg_img()
    result = SplitPerturbation(target_label=22, neighbour_label=23).apply(
        clean_img, seed=0
    )
    config = bundled_default_config()
    info = compute_components(result.labelmap, 22, config)
    assert info.component_count == 1


# =========================================================================== #
# Named adversarial case: expected-labels-equal-the-fired-labels
# =========================================================================== #


def test_expected_labels_equal_the_fired_labels():
    """A4: the manifest's ``expected_labels`` is ``{23}`` (the neighbour
    alone), an exact equality the intuitive ``{22, 23}`` fails."""
    case = _split_case_dict()
    assert offending_labels_match(case) is True


# =========================================================================== #
# Named adversarial case: bounds-stays-silent-on-the-donor
# =========================================================================== #


def test_bounds_stays_silent_on_the_donor():
    """At a 0.5 donated fraction the donor's extent_z falls to 13 mm and
    bounds fires (A1), which would validate mode 3 through a proxy the
    bar's condition 4 excludes; the committed 0.4 fixture must stay inside
    the lumbar range on every geometry field bounds checks."""
    case = _split_case_dict()
    fixture_path = CORPUS_DIR / case["seg_fixture"]
    donor_img = nib.load(str(fixture_path))
    config = bundled_default_config()
    geometry = compute_label_geometry(donor_img, 22, config)

    lumbar = DEFAULT_BOUNDS["lumbar"]
    assert lumbar["min_volume_mm3"] <= geometry.physical_volume_mm3 <= lumbar["max_volume_mm3"]
    for axis_name in ("x", "y", "z"):
        extent = getattr(geometry, f"extent_{axis_name}_mm")
        assert (
            lumbar[f"min_extent_{axis_name}_mm"]
            <= extent
            <= lumbar[f"max_extent_{axis_name}_mm"]
        ), (axis_name, extent, lumbar)


# =========================================================================== #
# Named adversarial case: mode-3-intended-rules-unchanged
# =========================================================================== #


def test_mode_3_intended_rules_unchanged():
    """A6: if a later hand authored the co-detection as an edge instead,
    condition 4 and ``derive_status`` would both move on a proxy rule."""
    rule_ids = {edge.rule_id for edge in failure_modes.SPECIFICATION[3].intended_rules}
    assert rule_ids == {"bounds", "reference_delta"}
    assert "fragmentation" not in rule_ids
