"""Tests for item 186 -- the expected level sequence admits per-section
vertebra counts.

Covers Acceptance Criteria AC1-AC16 per the item spec's Testing Strategy: one
test per AC. AC1 and AC2 share a module-scoped fixture that builds the T12
map and its record once. AC13 loops over the nine (t, l) combinations inside
its one test. AC15 loops over its five inputs inside its one test.

Plus exactly the five named adversarial cases the Testing Strategy names:
``thoracic-reading-out-of-range``, ``supplied-overrides-observed``,
``supplied-unknown-section``, ``coccyx-outside-sequence`` and
``unaccepted-transitional-t13``.
"""

from __future__ import annotations

import pytest

from segfacet import failure_modes
from segfacet.config import bundled_default_config
from segfacet.features.centroids import LabelCentroid
from segfacet.features.relationships import compute_spine_relationships
from segfacet.heuristics import run_rules
from segfacet.io import FacetInputError
from segfacet.labels import (
    SACRUM,
    SectionCounts,
    expected_level_sequence,
    resolve_section_counts,
)
from segfacet.pipeline import extract_feature_record

from synthetic import make_labelmap


# =========================================================================== #
# Helpers
# =========================================================================== #


def _centroid(level_name: str, mm: tuple) -> LabelCentroid:
    """Build a minimal LabelCentroid for testing relationships (no NIfTI needed)."""
    return LabelCentroid(
        label=0,
        level_name=level_name,
        centroid_voxel=(0.0, 0.0, 0.0),
        centroid_mm=mm,
    )


def _relationships(levels, **kwargs):
    """Relationships of the given head-to-tail level names (spec's phrase)."""
    centroids = [
        _centroid(name, (0.0, 0.0, float(i) * 10.0)) for i, name in enumerate(levels)
    ]
    return compute_spine_relationships(centroids, **kwargs)


# The T12 map: six separated, non-touching blocks labelled 19-24 (T12, L1-L5
# under LabelConvention.default()), no label 28 (T13). Blocks are 2 voxels
# thick along z with a 2-voxel gap so they never touch.
_T12_MAP_BLOCKS = {
    19: ((0, 4), (0, 4), (0, 2)),   # T12
    20: ((0, 4), (0, 4), (4, 6)),   # L1
    21: ((0, 4), (0, 4), (8, 10)),  # L2
    22: ((0, 4), (0, 4), (12, 14)),  # L3
    23: ((0, 4), (0, 4), (16, 18)),  # L4
    24: ((0, 4), (0, 4), (20, 22)),  # L5
}


@pytest.fixture(scope="module")
def t12_map_record():
    """extract_feature_record for the T12 map, computed once for AC1 and AC2."""
    seg_img = make_labelmap(shape=(4, 4, 24), blocks=_T12_MAP_BLOCKS)
    return extract_feature_record(seg_img, bundled_default_config())


# =========================================================================== #
# AC1: the T12 map reports no missing level
# =========================================================================== #


def test_ac1_t12_map_no_missing_level(t12_map_record):
    assert t12_map_record["relationships"]["missing_levels"] == []


# =========================================================================== #
# AC2: the T12 map produces no missing-level finding
# =========================================================================== #


def test_ac2_t12_map_no_coverage_finding(t12_map_record):
    findings = run_rules(t12_map_record, bundled_default_config())
    assert not any(f.rule_id == "coverage" for f in findings)


# =========================================================================== #
# AC3: a skipped L3 is still reported
# =========================================================================== #


def test_ac3_skipped_l3_still_reported():
    result = _relationships(["T12", "L1", "L2", "L4", "L5"])
    assert result.missing_levels == ["L3"]


# =========================================================================== #
# AC4: an 11-level thoracic reading is accepted with C7 in view
# =========================================================================== #


def test_ac4_eleven_level_thoracic_accepted_with_c7():
    levels = ["C7"] + [f"T{i}" for i in range(1, 12)] + ["L1"]
    result = _relationships(levels)
    assert result.missing_levels == []


# =========================================================================== #
# AC5: the 11-level reading is refused without C7
# =========================================================================== #


def test_ac5_eleven_level_reading_refused_without_c7():
    levels = [f"T{i}" for i in range(1, 12)] + ["L1"]
    result = _relationships(levels)
    assert result.missing_levels == ["T12"]


# =========================================================================== #
# AC6: the refused reading is returned as unaccepted
# =========================================================================== #


def test_ac6_refused_reading_returned_as_unaccepted():
    levels = [f"T{i}" for i in range(1, 12)] + ["L1"]
    resolved = resolve_section_counts(levels)
    assert resolved.unaccepted == {"thoracic": 11}


# =========================================================================== #
# AC7: a supplied 13-level thoracic count makes an absent T13 missing
# =========================================================================== #


def test_ac7_supplied_thirteen_level_count_makes_t13_missing():
    levels = ["T12", "L1", "L2", "L3", "L4", "L5"]
    result = _relationships(levels, section_counts={"thoracic": 13})
    assert result.missing_levels == ["T13"]


# =========================================================================== #
# AC8: a supplied count needs no field-of-view evidence
# =========================================================================== #


def test_ac8_supplied_count_needs_no_fov_evidence():
    levels = [f"T{i}" for i in range(1, 12)] + ["L1"]
    result = _relationships(levels, section_counts={"thoracic": 11})
    assert result.missing_levels == []


# =========================================================================== #
# AC9: a 4-level lumbar reading is accepted with the last thoracic level in view
# =========================================================================== #


def test_ac9_four_level_lumbar_accepted_with_t12_in_view():
    levels = ["T12", "L1", "L2", "L3", "L4", "S1"]
    result = _relationships(levels)
    assert result.missing_levels == []


# =========================================================================== #
# AC10: the 4-level lumbar reading is refused without it
# =========================================================================== #


def test_ac10_four_level_lumbar_refused_without_t12():
    levels = ["L1", "L2", "L3", "L4", "S1"]
    result = _relationships(levels)
    assert result.missing_levels == ["L5"]


# =========================================================================== #
# AC11: a 6-level lumbar reading is accepted
# =========================================================================== #


def test_ac11_six_level_lumbar_accepted():
    levels = ["T12"] + [f"L{i}" for i in range(1, 7)] + ["S1"]
    result = _relationships(levels)
    assert result.missing_levels == []


# =========================================================================== #
# AC12: a mixed combination resolves from the labels
# =========================================================================== #


def test_ac12_mixed_combination_resolves_from_labels():
    levels = ["C7"] + [f"T{i}" for i in range(1, 14)] + ["L1", "L2", "L3", "L4", "S1"]
    resolved = resolve_section_counts(levels)
    assert resolved.counts == (7, 13, 4)


# =========================================================================== #
# AC13: the expected sequence for every valid combination
# =========================================================================== #


def test_ac13_expected_sequence_for_every_valid_combination():
    for t in range(11, 14):
        for l in range(4, 7):
            expected = (
                tuple(f"C{i}" for i in range(1, 8))
                + tuple(f"T{i}" for i in range(1, t + 1))
                + tuple(f"L{i}" for i in range(1, l + 1))
                + (SACRUM,)
            )
            assert expected_level_sequence(SectionCounts(7, t, l)) == expected


# =========================================================================== #
# AC14: the sacrum is not split into levels
# =========================================================================== #


def test_ac14_sacrum_not_split_into_levels():
    result = _relationships(["L5", "S1", "S3"])
    assert result.missing_levels == []


# =========================================================================== #
# AC15: an out-of-range supplied count is refused
# =========================================================================== #


@pytest.mark.parametrize(
    "section_counts",
    [
        {"thoracic": 10},
        {"thoracic": 14},
        {"lumbar": 3},
        {"lumbar": 7},
        {"cervical": 6},
    ],
)
def test_ac15_out_of_range_supplied_count_refused(section_counts):
    centroids = [_centroid("L1", (0.0, 0.0, 0.0))]
    with pytest.raises(FacetInputError):
        compute_spine_relationships(centroids, section_counts=section_counts)


# =========================================================================== #
# AC16: split_own_label no longer fires coverage
# =========================================================================== #


def test_ac16_split_own_label_no_longer_fires_coverage():
    matches = [
        c
        for c in failure_modes.SPECIFICATION[3].corpus_cases
        if c.case_id == "split_own_label"
    ]
    assert len(matches) == 1, matches
    case = matches[0]
    assert set(failure_modes.measured_firing(case)) == {"bounds"}


# =========================================================================== #
# Named case: thoracic-reading-out-of-range
# =========================================================================== #


def test_thoracic_reading_out_of_range():
    """Guards an implementation that accepts any highest index as the count,
    which would make a real two-level gap vanish."""
    levels = ["C7"] + [f"T{i}" for i in range(1, 11)] + ["L1"]
    result = _relationships(levels)
    assert result.missing_levels == ["T11", "T12"]


# =========================================================================== #
# Named case: supplied-overrides-observed
# =========================================================================== #


def test_supplied_overrides_observed():
    """Guards an accepted observation silently overriding prior knowledge."""
    levels = ["C7"] + [f"T{i}" for i in range(1, 12)] + ["L1"]
    result = _relationships(levels, section_counts={"thoracic": 12})
    assert result.missing_levels == ["T12"]


# =========================================================================== #
# Named case: supplied-unknown-section
# =========================================================================== #


def test_supplied_unknown_section():
    """Guards a typo'd key being ignored, which would leave the default in
    force with no signal."""
    centroids = [_centroid("L1", (0.0, 0.0, 0.0))]
    with pytest.raises(FacetInputError):
        compute_spine_relationships(centroids, section_counts={"sacral": 1})


# =========================================================================== #
# Named case: coccyx-outside-sequence
# =========================================================================== #


def test_coccyx_outside_sequence():
    """Guards a walk that still follows CANONICAL_ORDER's tail and reports
    the sacrum missing between L5 and Cocc (A3)."""
    result = _relationships(["L4", "L5", "Cocc"])
    assert result.missing_levels == []


# =========================================================================== #
# Named case: unaccepted-transitional-t13
# =========================================================================== #


def test_unaccepted_transitional_t13():
    """Guards a present T13 being accepted with no field-of-view evidence.
    Item 192's transitional sub-type depends on that refusal."""
    levels = ["T13", "L1", "L2", "L3", "L4"]
    resolved = resolve_section_counts(levels)
    assert resolved.counts == (7, 12, 5)
    assert resolved.unaccepted == {"thoracic": 13}
