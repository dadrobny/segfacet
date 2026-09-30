"""Tests for item 187 -- ``neighbour_contact`` becomes a rule of its own,
serving mode 3 (split vertebra segment).

Covers Acceptance Criteria AC1-AC15 per the item spec's Testing Strategy: one
test per AC, each recomputed live from the committed fixture's own array and
header, the live rule registry, ``SPECIFICATION`` or ``bar_conditions`` --
never a hand-built copy of a case.

Plus exactly the seven adversarial cases the Testing Strategy names:
``largest-component-not-read``, ``label-scope-not-read``,
``just-above-threshold-fires``, ``absence-tolerant``,
``threshold-margin-on-the-committed-corpora``, ``absolute-fields-unchanged``
and ``spacing-read-from-header``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np
import pytest

from segfacet import failure_modes, traceability
from segfacet.config import bundled_default_config
from segfacet.features.components import compute_components
from segfacet.heuristics.fragmentation import FragmentationRule
from segfacet.heuristics.neighbour_contact import (
    DEFAULT_CONTACT_FRACTION,
    NeighbourContactRule,
)
from segfacet.heuristics import iter_rules
from segfacet.heuristics.runner import run_rules
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest
from segfacet.synth.intensity import load_intensity_manifest
from segfacet.synth.regression import (
    intensity_pipeline_findings,
    loaded_intensity_case,
    loaded_seg_image,
    pipeline_findings,
    reconstructed_findings,
)

from synthetic import LABEL_DTYPE, affine_from_spacing


# =========================================================================== #
# Helpers
# =========================================================================== #


def _split_case_dict():
    """The one committed geometric manifest case whose ``perturbation ==
    "split"``."""
    matches = [c for c in load_manifest()["cases"] if c["perturbation"] == "split"]
    assert len(matches) == 1, matches
    return matches[0]


def _recompute_contacts(data: np.ndarray, zooms, label: int):
    """A parallel recomputation of A2's face-contact/surface definitions for
    every connected component of *label*, in ``component_sizes`` order
    (descending voxel count, ties broken by ascending component id) --
    independent of ``segfacet.features.components`` (a fresh pad/shift face
    count, not a call to the feature under test).

    Returns a list of ``(neighbour_label, contact_area_mm2, surface_area_mm2,
    contact_fraction)`` tuples, one per component, in that order.
    """
    import scipy.ndimage as ndi

    face_area = {
        0: float(zooms[1]) * float(zooms[2]),
        1: float(zooms[0]) * float(zooms[2]),
        2: float(zooms[0]) * float(zooms[1]),
    }
    padded = np.pad(data, 1, mode="constant", constant_values=0)
    neighbour_arrays = []
    for axis in range(3):
        pos = [slice(1, -1)] * 3
        pos[axis] = slice(2, None)
        neg = [slice(1, -1)] * 3
        neg[axis] = slice(0, -2)
        neighbour_arrays.append((padded[tuple(pos)], face_area[axis]))
        neighbour_arrays.append((padded[tuple(neg)], face_area[axis]))

    mask = data == label
    labelled, n_components = ndi.label(mask)
    sizes = ndi.sum(mask, labelled, index=np.arange(1, n_components + 1))
    counts_by_id = [(int(i), float(sizes[i - 1])) for i in range(1, n_components + 1)]
    ordered_ids = [
        cid for cid, _count in sorted(counts_by_id, key=lambda pair: (-pair[1], pair[0]))
    ]

    results = []
    for comp_id in ordered_ids:
        comp_mask = labelled == comp_id
        area_by_other: dict = {}
        surface = 0.0
        for neighbour_vals, area in neighbour_arrays:
            selected = neighbour_vals[comp_mask]
            for other_label in np.unique(selected):
                other_label = int(other_label)
                count = int(np.count_nonzero(selected == other_label))
                if other_label == label:
                    continue
                surface += count * area
                if other_label != 0:
                    area_by_other[other_label] = area_by_other.get(other_label, 0.0) + count * area
        if area_by_other:
            neighbour = max(area_by_other, key=lambda k: (area_by_other[k], -k))
            contact = area_by_other[neighbour]
        else:
            neighbour, contact = 0, 0.0
        fraction = contact / surface if surface else 0.0
        results.append((neighbour, contact, surface, fraction))
    return results


@pytest.fixture(scope="module")
def split_case_image():
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    data = np.asanyarray(seg_img.dataobj)
    zooms = seg_img.header.get_zooms()
    return seg_img, data, zooms


@pytest.fixture(scope="module")
def all_corpus_findings():
    """Every ``(corpus, case_id, Finding)`` triple across both committed
    manifests, driven exactly once through the same entry points
    ``failure_modes.measured_firing`` dispatches to."""
    triples = []

    for case in load_manifest().get("cases", []):
        detection = case.get("detection")
        if detection == "pipeline":
            findings = pipeline_findings(case)
        elif detection == "reconstructed_record":
            findings = reconstructed_findings(case)
        else:
            raise AssertionError(
                f"geometric case {case.get('case_id')!r}: unrecognised detection {detection!r}"
            )
        for finding in findings:
            triples.append(("geometric", case["case_id"], finding))

    for case in load_intensity_manifest().get("cases", []):
        detection = case.get("detection")
        if detection != "intensity_pipeline":
            raise AssertionError(
                f"intensity case {case.get('case_id')!r}: unrecognised detection {detection!r}"
            )
        for finding in intensity_pipeline_findings(case):
            triples.append(("intensity", case["case_id"], finding))

    assert triples, "expected at least one finding across both committed manifests"
    return triples


# =========================================================================== #
# AC1: each component's contact fraction is measured
# =========================================================================== #


def test_ac1_each_component_contact_fraction_is_measured(split_case_image):
    seg_img, data, zooms = split_case_image
    expected = _recompute_contacts(data, zooms, 24)

    config = bundled_default_config()
    info = compute_components(seg_img, 24, config)
    assert len(info.component_contacts) == len(expected), info.component_contacts

    for i, (_neighbour, _contact, _surface, expected_fraction) in enumerate(expected):
        assert info.component_contacts[i].contact_fraction == pytest.approx(
            expected_fraction, abs=1e-12
        )


# =========================================================================== #
# AC2: each component's record names the neighbour it touches
# =========================================================================== #


def test_ac2_each_component_names_its_neighbour(split_case_image):
    seg_img, data, zooms = split_case_image
    expected = _recompute_contacts(data, zooms, 24)

    config = bundled_default_config()
    info = compute_components(seg_img, 24, config)
    assert len(info.component_contacts) == len(expected), info.component_contacts

    for i, (expected_neighbour, _contact, _surface, _fraction) in enumerate(expected):
        assert info.component_contacts[i].neighbour_label == expected_neighbour


# =========================================================================== #
# AC3: a small component with most of its surface in contact scores higher
# =========================================================================== #


def test_ac3_small_component_scores_higher_at_equal_contact_area():
    # label 2 is a one-voxel wall; label 1 has a large 10x10x10 cube on one
    # side of the wall and a separate 1x10x10 slab on the other side, so the
    # slab and the cube are two components of label 1, each with one face on
    # the wall. Both contact areas are 100.0 mm^2 at 1mm isotropic spacing;
    # the small slab's surface is 240 mm^2, the cube's is 600 mm^2, so the
    # fractions differ though the areas match.
    shape = (12, 10, 10)
    data = np.zeros(shape, dtype=LABEL_DTYPE)
    data[0, :, :] = 1  # the slab, 1x10x10 (100 voxels)
    data[1, :, :] = 2  # the wall
    data[2:12, :, :] = 1  # the cube, 10x10x10 (1000 voxels)
    img = nib.Nifti1Image(data, affine_from_spacing((1.0, 1.0, 1.0)))

    config = bundled_default_config()
    info = compute_components(img, 1, config)
    assert info.component_count == 2, info.component_sizes
    # component_sizes is descending by voxel count: the cube (1000) first,
    # then the slab (100).
    cube_contact, slab_contact = info.component_contacts
    assert cube_contact.contact_area_mm2 == pytest.approx(100.0)
    assert slab_contact.contact_area_mm2 == pytest.approx(100.0)
    assert slab_contact.contact_fraction > cube_contact.contact_fraction


# =========================================================================== #
# AC4: an unfragmented label carries a label-level contact fraction
# =========================================================================== #


def test_ac4_unfragmented_label_carries_label_level_fraction(split_case_image):
    seg_img, data, zooms = split_case_image
    expected = _recompute_contacts(data, zooms, 23)
    assert len(expected) == 1, expected
    _neighbour, _contact, _surface, expected_fraction = expected[0]

    config = bundled_default_config()
    info = compute_components(seg_img, 23, config)
    assert info.component_count == 1
    assert info.label_contact_fraction == pytest.approx(expected_fraction, abs=1e-12)


# =========================================================================== #
# AC5: the rule count is 11
# =========================================================================== #


def test_ac5_rule_count_is_eleven():
    # Item 189 (2026-09-28): the new spline_offset rule brings the registry
    # from eleven to twelve. Item 207 (2026-09-30): fused_label makes thirteen.
    assert len(list(iter_rules())) == 14  # item 208 (2026-09-30): 13 -> 14


# =========================================================================== #
# AC6: the rule declares one detector on the relative measure
# =========================================================================== #


def test_ac6_one_detector_on_the_relative_measure():
    detectors = NeighbourContactRule.mode_declaration.detectors
    assert len(detectors) == 1, detectors
    assert detectors[0].detector_id == "stray_contact"
    assert detectors[0].signal_paths == (
        "per_label.{label}.components.component_contacts[].contact_fraction",
    )


# =========================================================================== #
# AC7: the detector serves mode 3 and no other mode
# =========================================================================== #


def test_ac7_detector_serves_mode_2_and_no_other():
    assert failure_modes.modes_for_detector("neighbour_contact", "stray_contact") == (2,)  # item 205 (2026-09-30): moved from mode 3


# =========================================================================== #
# AC8: fragmentation declares no mode 3
# =========================================================================== #


def test_ac8_fragmentation_declares_no_mode_3():
    assert 3 not in FragmentationRule.mode_declaration.modes


# =========================================================================== #
# AC9: the rule fires on the split case
# =========================================================================== #


def test_ac9_rule_fires_on_the_split_case():
    case = _split_case_dict()
    findings = pipeline_findings(case)
    matches = [f for f in findings if f.rule_id == "neighbour_contact"]
    assert len(matches) == 1, findings
    assert matches[0].detector_id == "stray_contact"
    assert matches[0].labels == frozenset({24})


# =========================================================================== #
# AC10: the rule fires on no other corpus case
# =========================================================================== #


def test_ac10_rule_fires_on_no_other_case(all_corpus_findings):
    firing_cases = {
        (corpus, case_id)
        for corpus, case_id, finding in all_corpus_findings
        if finding.rule_id == "neighbour_contact"
    }
    assert firing_cases == {("geometric", "split")}


# =========================================================================== #
# AC11: the split case's measured firing is the new rule alone
# =========================================================================== #


def test_ac11_split_measured_firing_is_the_new_rule_alone():
    cases = [c for c in failure_modes.SPECIFICATION[2].corpus_cases if c.case_id == "split"]  # item 205 (2026-09-30): moved from mode 3
    assert len(cases) == 1, cases
    case = cases[0]
    assert set(failure_modes.measured_firing(case)) == {"neighbour_contact"}


# =========================================================================== #
# AC12: the committed manifest designates the new rule for the split case
# =========================================================================== #


def test_ac12_manifest_designates_the_new_rule():
    case = _split_case_dict()
    assert case["expected_rule_ids"] == ["neighbour_contact"]


# =========================================================================== #
# AC13: mode 3 still meets the bar's conditions 1-5
# =========================================================================== #


def test_ac13_mode_2_meets_all_five_bar_conditions():
    bar = traceability.bar_conditions(2)  # item 205 (2026-09-30): moved from mode 3
    assert tuple(c.met for c in bar) == (True, True, True, True, True)


# =========================================================================== #
# AC14: mode 3's deciding detector is the new rule's
# =========================================================================== #


def test_ac14_deciding_detector_is_the_new_rule():
    bar = traceability.bar_conditions(2)  # item 205 (2026-09-30): moved from mode 3
    condition_4 = [c for c in bar if c.number == 4]
    assert len(condition_4) == 1, condition_4
    # Item 207 (2026-09-30): fused_label/fused_label joins mode 2's deciding
    # detectors.
    assert condition_4[0].subjects == (
        "fused_label/fused_label",
        "neighbour_contact/stray_contact",
    )


# =========================================================================== #
# AC15: the threshold is on the relative measure, fired strictly above
# =========================================================================== #


def test_ac15_threshold_fires_strictly_above():
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    config = bundled_default_config()
    record = extract_feature_record(seg_img, config)

    fraction = record["per_label"]["24"]["components"]["component_contacts"][1][
        "contact_fraction"
    ]
    config.rules.setdefault("neighbour_contact", {}).setdefault("params", {})[
        "contact_fraction_threshold"
    ] = fraction

    findings = run_rules(record, config)
    assert not any(f.rule_id == "neighbour_contact" for f in findings)


# =========================================================================== #
# Named adversarial case: largest-component-not-read
# =========================================================================== #


def test_largest_component_not_read():
    record = {
        "per_label": {
            22: {
                "label": 22,
                "level_name": "L3",
                "components": {
                    "component_contacts": [
                        {
                            "neighbour_label": 21,
                            "contact_area_mm2": 900.0,
                            "surface_area_mm2": 1000.0,
                            "contact_fraction": 0.9,
                        },
                        {
                            "neighbour_label": 0,
                            "contact_area_mm2": 0.0,
                            "surface_area_mm2": 100.0,
                            "contact_fraction": 0.0,
                        },
                    ],
                    "label_contact_fraction": 0.9,
                },
            },
        },
        "relationships": {},
        "overlaps": {},
    }
    findings = NeighbourContactRule().evaluate(record, bundled_default_config())
    assert findings == []


# =========================================================================== #
# Named adversarial case: label-scope-not-read
# =========================================================================== #


def test_label_scope_not_read():
    record = {
        "per_label": {
            23: {
                "label": 23,
                "level_name": "L4",
                "components": {
                    "component_contacts": [
                        {
                            "neighbour_label": 24,
                            "contact_area_mm2": 806.0,
                            "surface_area_mm2": 2430.0,
                            "contact_fraction": 0.0,
                        },
                    ],
                    "label_contact_fraction": 0.9,
                },
            },
        },
        "relationships": {},
        "overlaps": {},
    }
    findings = NeighbourContactRule().evaluate(record, bundled_default_config())
    assert findings == []


# =========================================================================== #
# Named adversarial case: just-above-threshold-fires
# =========================================================================== #


def test_just_above_threshold_fires():
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    config = bundled_default_config()
    record = extract_feature_record(seg_img, config)

    fraction = record["per_label"]["24"]["components"]["component_contacts"][1][
        "contact_fraction"
    ]
    config.rules.setdefault("neighbour_contact", {}).setdefault("params", {})[
        "contact_fraction_threshold"
    ] = fraction - 1e-9

    findings = run_rules(record, config)
    matches = [f for f in findings if f.rule_id == "neighbour_contact"]
    assert len(matches) == 1, findings


# =========================================================================== #
# Named adversarial case: absence-tolerant
# =========================================================================== #


def test_absence_tolerant():
    record = {
        "per_label": {
            22: {
                "label": 22,
                "level_name": "L3",
                "components": {
                    "fragmentation_index": 1.0,
                    "largest_component_fraction": 1.0,
                    "component_count": 1,
                    "component_sizes": [1000],
                    # Deliberately no component_contacts / label_contact_fraction --
                    # a legacy, pre-item-187 record shape (A7).
                },
            },
        },
        "relationships": {},
        "overlaps": {},
    }
    findings = NeighbourContactRule().evaluate(record, bundled_default_config())
    assert findings == []


# =========================================================================== #
# Named adversarial case: threshold-margin-on-the-committed-corpora
# =========================================================================== #


def test_threshold_margin_on_the_committed_corpora():
    config = bundled_default_config()
    firing_values = []
    non_firing_values = []

    for case in load_manifest().get("cases", []):
        seg_img = loaded_seg_image(case)
        data = np.asanyarray(seg_img.dataobj)
        for label in sorted(int(v) for v in np.unique(data) if v != 0):
            info = compute_components(seg_img, label, config)
            for contact in info.component_contacts[1:]:
                if contact.contact_fraction > 0.0:
                    firing_values.append(contact.contact_fraction)
                else:
                    non_firing_values.append(contact.contact_fraction)

    for case in load_intensity_manifest().get("cases", []):
        seg_img, _scan_img = loaded_intensity_case(case)
        data = np.asanyarray(seg_img.dataobj)
        for label in sorted(int(v) for v in np.unique(data) if v != 0):
            info = compute_components(seg_img, label, config)
            for contact in info.component_contacts[1:]:
                if contact.contact_fraction > 0.0:
                    firing_values.append(contact.contact_fraction)
                else:
                    non_firing_values.append(contact.contact_fraction)

    assert firing_values, "expected at least one firing stray fraction"
    assert non_firing_values, "expected at least one non-firing stray fraction"

    for value in firing_values:
        assert value - DEFAULT_CONTACT_FRACTION >= 0.1, value
    for value in non_firing_values:
        assert DEFAULT_CONTACT_FRACTION - value >= 0.1, value


# =========================================================================== #
# Named adversarial case: absolute-fields-unchanged
# =========================================================================== #


def test_absolute_fields_unchanged(split_case_image):
    seg_img, data, _zooms = split_case_image
    config = bundled_default_config()

    for label in sorted(int(v) for v in np.unique(data) if v != 0):
        info = compute_components(seg_img, label, config)
        stray_contacts = info.component_contacts[1:]
        expected = max(
            (c.contact_area_mm2 for c in stray_contacts), default=0.0
        )
        assert info.stray_contact_area_mm2 == pytest.approx(expected), label


# =========================================================================== #
# Named adversarial case: spacing-read-from-header
# =========================================================================== #


def test_spacing_read_from_header():
    # The same AC3 map, rebuilt at anisotropic spacing (1.0, 2.0, 3.0):
    # the wall's face is on axis 0, so its area is spacing[1] * spacing[2] =
    # 6.0 mm^2 per voxel; the cube's contact face is 10x10 voxels (100
    # faces), the slab's is also 10x10 (100 faces).
    shape = (12, 10, 10)
    data = np.zeros(shape, dtype=LABEL_DTYPE)
    data[0, :, :] = 1  # the slab, 1x10x10 (100 voxels)
    data[1, :, :] = 2  # the wall
    data[2:12, :, :] = 1  # the cube, 10x10x10 (1000 voxels)
    spacing = (1.0, 2.0, 3.0)
    img = nib.Nifti1Image(data, affine_from_spacing(spacing))

    config = bundled_default_config()
    info = compute_components(img, 1, config)
    assert info.component_count == 2

    face_area_x = spacing[1] * spacing[2]
    expected_contact = 100 * face_area_x
    for contact in info.component_contacts:
        assert contact.contact_area_mm2 == pytest.approx(expected_contact)

    # Recompute each component's own surface area independently, by its own
    # box dimensions in voxels (a x b x c along x, y, z): the cube is
    # 10x10x10, the slab is 1x10x10 -- component_sizes orders the (larger)
    # cube first, then the slab (A1).
    area_yz = spacing[1] * spacing[2]
    area_xz = spacing[0] * spacing[2]
    area_xy = spacing[0] * spacing[1]

    def _box_surface(a, b, c):
        return 2 * (b * c * area_yz) + 2 * (a * c * area_xz) + 2 * (a * b * area_xy)

    cube_surface = _box_surface(10, 10, 10)
    slab_surface = _box_surface(1, 10, 10)

    cube_contact, slab_contact = info.component_contacts
    assert cube_contact.surface_area_mm2 == pytest.approx(cube_surface)
    assert slab_contact.surface_area_mm2 == pytest.approx(slab_surface)
    assert cube_contact.contact_fraction == pytest.approx(expected_contact / cube_surface)
    assert slab_contact.contact_fraction == pytest.approx(expected_contact / slab_surface)
