"""Tests for item 167 -- mode 3's own feature (neighbour-label contact area
restricted to a label's non-largest connected components,
``ComponentsInfo.stray_contact_area_mm2`` / ``stray_contact_label``) and its
own detector (``fragmentation``'s new ``neighbour_contact`` detector, item
164's first-class detector-id machinery).

Covers Acceptance Criteria AC1-AC11 per the item spec's Testing Strategy: one
test per AC, each recomputed live from the committed fixture's own array and
header, the live rule registry, ``SPECIFICATION``, ``build_catalogue`` or
``bar_conditions`` -- never a hand-built copy of a case. AC1-AC3 recompute
the contact area independently of ``segfacet.features.components`` (a
padding/shift face-count, not a call to the feature under test) so the test
can actually fail if the implementation gets it wrong.

Plus exactly the nine adversarial cases the Testing Strategy names:
``threshold-margin-on-the-committed-corpora``, ``force-overlap-stays-silent``,
``fuse-adjacent-stays-silent``, ``inject-islands-stays-silent``,
``single-component-label-is-the-sentinel``, ``absence-tolerant-detector``,
``existing-detectors-unchanged``, ``record-is-not-mutated`` and
``spacing-is-read-from-the-header``, plus one more named by the item's
Correction (2026-09-20, C6): ``largest-component-tie-is-broken-by-
ascending-id``.
"""

from __future__ import annotations

import copy

import nibabel as nib
import numpy as np
import pytest
import scipy.ndimage as ndi

from segfacet import failure_modes, traceability
from segfacet.catalogue import build_catalogue
from segfacet.config import bundled_default_config
from segfacet.features.components import compute_components
from segfacet.heuristics.fragmentation import (
    DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2,
    FragmentationRule,
)
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


def _manifest_case(case_id):
    for case in load_manifest()["cases"]:
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"case_id {case_id!r} not found in the committed geometric manifest")


def _recompute_stray_contact(data: np.ndarray, zooms) -> dict:
    """A parallel recomputation, from the fixture's own array, of
    ``segfacet.features.components``'s neighbour-contact block -- not an
    independent derivation: it shares the same face-area axis map, the same
    pad-and-slice neighbour construction, and (below) the same documented
    tie-break as the production code, so it can confirm a refactor but
    cannot by itself catch a defect shared by both (item 167, Correction
    2026-09-20, C7). The from-first-principles evidence lives in the
    hand-computed literals in ``test_ac1``/``test_ac2``/
    ``test_spacing_is_read_from_the_header`` instead. The tie-break case
    itself -- two equal-size components, only one face-adjacent -- is
    covered by
    ``test_largest_component_tie_is_broken_by_ascending_id``, which uses
    literals only and does not call this helper.

    For every non-zero label in *data*, recomputes the maximum 6-neighbour
    face-contact area between any of that label's connected components
    **other than its largest** (components ordered by descending voxel
    count, ties broken by ascending component id) and any single other
    non-zero label (ties among equally-contacting labels broken by lowest
    label id).

    Returns ``{label: (area_mm2, other_label)}``, using ``0`` as the
    other-label sentinel when the maximum is ``0.0`` (single-component label,
    or a stray component touching nothing).
    """
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

    results = {}
    for label in sorted(int(v) for v in np.unique(data) if v != 0):
        mask = data == label
        labelled, n_components = ndi.label(mask)
        if n_components <= 1:
            results[label] = (0.0, 0)
            continue
        sizes = ndi.sum(mask, labelled, index=np.arange(1, n_components + 1))
        # Descending voxel count, ties broken by ascending component id --
        # the same explicit, stable ordering as
        # segfacet.features.components (item 167, C6/C7); the first is
        # "the largest" and is excluded below.
        counts_by_id = [(int(i), float(sizes[i - 1])) for i in range(1, n_components + 1)]
        component_ids_desc = [
            cid for cid, _count in sorted(counts_by_id, key=lambda pair: (-pair[1], pair[0]))
        ]

        best_area = 0.0
        best_other = 0
        for comp_id in component_ids_desc[1:]:
            comp_mask = labelled == comp_id
            area_by_other: dict = {}
            for neighbour_vals, area in neighbour_arrays:
                selected = neighbour_vals[comp_mask]
                for other_label in np.unique(selected):
                    other_label = int(other_label)
                    if other_label == 0 or other_label == label:
                        continue
                    count = int(np.count_nonzero(selected == other_label))
                    area_by_other[other_label] = area_by_other.get(other_label, 0.0) + count * area
            if area_by_other:
                # Among contacting labels of equal area, the lowest label id
                # wins (item 167, C6).
                local_other = max(area_by_other, key=lambda k: (area_by_other[k], -k))
                local_area = area_by_other[local_other]
                # Strict >: across components, the earlier (lower-id, per
                # the ordering above) component's contact wins an area tie
                # (item 167, C6).
                if local_area > best_area:
                    best_area, best_other = local_area, local_other
        results[label] = (best_area, best_other)
    return results


@pytest.fixture(scope="module")
def stray_contact_sweep():
    """``(corpus, case_id, label) -> stray_contact_area_mm2`` for every case
    of both committed manifests and every non-zero label, computed once
    through the feature under test (AC3, named case 1)."""
    config = bundled_default_config()
    triples = {}

    for case in load_manifest().get("cases", []):
        seg_img = loaded_seg_image(case)
        data = np.asanyarray(seg_img.dataobj)
        for label in sorted(int(v) for v in np.unique(data) if v != 0):
            info = compute_components(seg_img, label, config)
            triples[("geometric", case["case_id"], label)] = info.stray_contact_area_mm2

    for case in load_intensity_manifest().get("cases", []):
        seg_img, _scan_img = loaded_intensity_case(case)
        data = np.asanyarray(seg_img.dataobj)
        for label in sorted(int(v) for v in np.unique(data) if v != 0):
            info = compute_components(seg_img, label, config)
            triples[("intensity", case["case_id"], label)] = info.stray_contact_area_mm2

    assert triples, "expected a non-empty sweep over both committed manifests"
    return triples


@pytest.fixture(scope="module")
def all_corpus_findings():
    """Every ``(corpus, case_id, Finding)`` triple across both committed
    manifests, driven exactly once through the same entry points
    ``failure_modes.measured_firing`` dispatches to (item 164's pattern)."""
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
# AC1: the feature measures the split
# =========================================================================== #


def test_ac1_feature_measures_the_split():
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    data = np.asanyarray(seg_img.dataobj)
    zooms = seg_img.header.get_zooms()

    expected_area, _expected_other = _recompute_stray_contact(data, zooms)[23]
    assert expected_area > 0.0, "expected recomputation to find contact on label 23"

    config = bundled_default_config()
    info = compute_components(seg_img, 23, config)
    assert info.stray_contact_area_mm2 == pytest.approx(expected_area)
    # Measured 2026-09-20 (Correction C7): the committed split fixture's
    # own value, pinned as a from-first-principles literal alongside the
    # recomputation above -- neither is a mirror of the other.
    assert info.stray_contact_area_mm2 == pytest.approx(750.0)


# =========================================================================== #
# AC2: the feature names the label that claimed the part
# =========================================================================== #


def test_ac2_feature_names_the_claiming_label():
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    data = np.asanyarray(seg_img.dataobj)
    zooms = seg_img.header.get_zooms()

    expected_area, expected_other = _recompute_stray_contact(data, zooms)[23]
    assert expected_other != 0, "expected label 23's recomputed contact to name another label"

    config = bundled_default_config()
    info = compute_components(seg_img, 23, config)
    assert info.stray_contact_label == expected_other
    # Measured 2026-09-20 (Correction C7): the committed split fixture's
    # own value, pinned as a from-first-principles literal alongside the
    # recomputation above -- neither is a mirror of the other.
    assert info.stray_contact_label == 22

    # The background sentinel for a label with no stray contact (AC2's
    # second half): every other present label in the same fixture.
    other_labels = sorted(int(v) for v in np.unique(data) if v != 0 and int(v) != 23)
    assert other_labels, "expected at least one other label in the split fixture"
    saw_a_sentinel = False
    for label in other_labels:
        sibling_info = compute_components(seg_img, label, config)
        if sibling_info.stray_contact_area_mm2 == 0.0:
            assert sibling_info.stray_contact_label == 0
            saw_a_sentinel = True
    assert saw_a_sentinel, "expected at least one silent label to check the sentinel on"


# =========================================================================== #
# AC3: the feature is silent everywhere else in both committed corpora
# =========================================================================== #


def test_ac3_silent_everywhere_else_in_both_corpora(stray_contact_sweep):
    firing = {key for key, area in stray_contact_sweep.items() if area > 0.0}
    assert firing == {("geometric", "split", 23)}


# =========================================================================== #
# AC4: the detector is declared with a first-class id
# =========================================================================== #


def test_ac4_detector_declared_with_first_class_id():
    detectors = FragmentationRule.mode_declaration.detectors
    matches = [d for d in detectors if d.detector_id == "neighbour_contact"]
    assert len(matches) == 1, detectors
    assert matches[0].signal_paths == ("per_label.{label}.components.stray_contact_area_mm2",)


# =========================================================================== #
# AC5: the deciding detector serves mode 3 and no other mode
# =========================================================================== #


def test_ac5_detector_serves_mode_3_and_no_other():
    assert failure_modes.modes_for_detector("fragmentation", "neighbour_contact") == (3,)


# =========================================================================== #
# AC6: the detector fires on mode 3's corpus case
# =========================================================================== #


def test_ac6_detector_fires_on_the_split_case():
    case = _split_case_dict()
    findings = pipeline_findings(case)
    matches = [
        f for f in findings if (f.rule_id, f.detector_id) == ("fragmentation", "neighbour_contact")
    ]
    assert len(matches) == 1, findings
    assert matches[0].labels == frozenset({23})


# =========================================================================== #
# AC7: the detector fires on no other corpus case
# =========================================================================== #


def test_ac7_detector_fires_on_no_other_case(all_corpus_findings):
    firing_cases = {
        (corpus, case_id)
        for corpus, case_id, finding in all_corpus_findings
        if finding.rule_id == "fragmentation" and finding.detector_id == "neighbour_contact"
    }
    assert firing_cases == {("geometric", "split")}


# =========================================================================== #
# AC8: no committed case's expected firing moved
# =========================================================================== #


def test_ac8_split_case_expected_firing_unmoved():
    cases = failure_modes.SPECIFICATION[3].corpus_cases
    assert len(cases) == 1, cases
    case = cases[0]
    assert case.case_id == "split"
    assert case.expected_firing == ("fragmentation",)
    assert set(case.expected_firing) == set(failure_modes.measured_firing(case))


# =========================================================================== #
# AC9: the deciding detector's signal path is extracted and catalogued
# =========================================================================== #


def test_ac9_signal_path_extracted_and_catalogued():
    catalogue = build_catalogue(strict=True)
    target_path = "per_label.{label}.components.stray_contact_area_mm2"
    matches = [e for e in catalogue.entries if e.path == target_path]
    assert len(matches) == 1, [e.path for e in catalogue.entries if "stray_contact" in e.path]
    assert matches[0].observed.corpus.covered is True


# =========================================================================== #
# AC10: mode 3 owns the edge
# =========================================================================== #


def test_ac10_mode_3_owns_the_edge():
    edges = [
        edge
        for edge in failure_modes.SPECIFICATION[3].intended_rules
        if edge.rule_id == "fragmentation"
    ]
    assert len(edges) == 1, failure_modes.SPECIFICATION[3].intended_rules
    assert edges[0].detector_ids == ("neighbour_contact",)
    assert edges[0].evidence_rung == "synthetic-demonstrable"


# =========================================================================== #
# AC11: mode 3 stands at the fully-specified bar's conditions 1-5
# =========================================================================== #


def test_ac11_mode_3_meets_all_five_bar_conditions():
    catalogue = build_catalogue(strict=True)
    bar = traceability.bar_conditions(3, catalogue=catalogue)
    assert tuple(c.met for c in bar) == (True, True, True, True, True)

    condition_4 = [c for c in bar if c.number == 4]
    assert len(condition_4) == 1, condition_4
    assert condition_4[0].subjects == ("fragmentation/neighbour_contact",)


# =========================================================================== #
# Named adversarial case: threshold-margin-on-the-committed-corpora
# =========================================================================== #


def test_threshold_margin_on_the_committed_corpora(stray_contact_sweep):
    firing_values = [area for area in stray_contact_sweep.values() if area > 0.0]
    non_firing_values = [area for area in stray_contact_sweep.values() if area <= 0.0]
    assert firing_values, "expected at least one firing value in the sweep"
    assert non_firing_values, "expected at least one non-firing value in the sweep"

    for value in firing_values:
        assert value - DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2 >= 100.0, value
    for value in non_firing_values:
        assert DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2 - value >= 100.0, value


# =========================================================================== #
# Named adversarial case: force-overlap-stays-silent
# =========================================================================== #


def test_force_overlap_stays_silent():
    case = _manifest_case("force_overlap")
    seg_img = loaded_seg_image(case)
    config = bundled_default_config()
    for label in (20, 21):
        info = compute_components(seg_img, label, config)
        assert info.stray_contact_area_mm2 == 0.0, label


# =========================================================================== #
# Named adversarial case: fuse-adjacent-stays-silent
# =========================================================================== #


def test_fuse_adjacent_stays_silent():
    case = _manifest_case("fuse_adjacent")
    seg_img = loaded_seg_image(case)
    config = bundled_default_config()
    info = compute_components(seg_img, 22, config)
    assert info.component_count > 1, "expected label 22 to carry a detached component"
    assert info.stray_contact_area_mm2 == 0.0


# =========================================================================== #
# Named adversarial case: inject-islands-stays-silent
# =========================================================================== #


def test_inject_islands_stays_silent():
    case = _manifest_case("inject_islands")
    seg_img = loaded_seg_image(case)
    config = bundled_default_config()
    info = compute_components(seg_img, 22, config)
    assert info.component_count > 1, "expected label 22 to carry the injected island"
    assert info.stray_contact_area_mm2 == 0.0


# =========================================================================== #
# Named adversarial case: single-component-label-is-the-sentinel
# =========================================================================== #


def test_single_component_label_is_the_sentinel():
    data = np.zeros((6, 6, 6), dtype=LABEL_DTYPE)
    data[1:4, 1:4, 1:4] = 1
    img = nib.Nifti1Image(data, affine_from_spacing((1.0, 1.0, 1.0)))
    config = bundled_default_config()
    info = compute_components(img, 1, config)
    assert info.component_count == 1
    assert info.stray_contact_area_mm2 == 0.0
    assert info.stray_contact_label == 0


# =========================================================================== #
# Named adversarial case: absence-tolerant-detector
# =========================================================================== #


def test_absence_tolerant_detector():
    config = bundled_default_config()
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
                    # Deliberately no stray_contact_area_mm2 / stray_contact_label --
                    # a legacy, pre-item-167 record shape (A5).
                },
            },
        },
        "relationships": {},
        "overlaps": {},
    }
    findings = FragmentationRule().evaluate(record, config)
    assert isinstance(findings, list)
    assert not any(f.detector_id == "neighbour_contact" for f in findings)


# =========================================================================== #
# Named adversarial case: existing-detectors-unchanged
# =========================================================================== #


def test_existing_detectors_unchanged():
    case = _split_case_dict()
    findings = pipeline_findings(case)
    components_findings = [
        f for f in findings if (f.rule_id, f.detector_id) == ("fragmentation", "components")
    ]
    islands_findings = [
        f for f in findings if (f.rule_id, f.detector_id) == ("fragmentation", "islands")
    ]
    assert len(components_findings) == 1, findings
    assert islands_findings == []


# =========================================================================== #
# Named adversarial case: record-is-not-mutated
# =========================================================================== #


def test_record_is_not_mutated():
    config = bundled_default_config()
    case = _split_case_dict()
    seg_img = loaded_seg_image(case)
    record = extract_feature_record(seg_img, config)
    record_before = copy.deepcopy(record)

    FragmentationRule().evaluate(record, config)

    assert record == record_before
    fresh = extract_feature_record(seg_img, config)
    assert record == fresh


# =========================================================================== #
# Named adversarial case: spacing-is-read-from-the-header
# =========================================================================== #


def test_spacing_is_read_from_the_header():
    """The one test whose whole subject is the axis->face-area mapping, so
    it must not go through ``_recompute_stray_contact`` (item 167,
    Correction 2026-09-20, C7): that helper shares production's axis map,
    and a systematic defect in either would pass unnoticed if the other
    were compared against it. Asserts a hand-computed literal instead.

    The stray component (label 1, voxels at x=5) is a 1x3x3 slab whose
    9 voxels each face label 2 (at x=6) across the x axis (axis 0). Face
    area for an axis-0 contact is spacing[1] * spacing[2] = 1.0 * 3.0 mm,
    so the expected total is 9 faces * 1.0 mm * 3.0 mm = 27.0 mm^2.
    """
    spacing = (0.5, 1.0, 3.0)
    shape = (10, 3, 3)
    data = np.zeros(shape, dtype=LABEL_DTYPE)
    data[0:3, :, :] = 1  # label 1's dominant component, 27 voxels
    data[5, :, :] = 1  # label 1's stray component, 9 voxels, separated by a background gap
    data[6, :, :] = 2  # label 2, face-adjacent to the stray component only
    img = nib.Nifti1Image(data, affine_from_spacing(spacing))

    config = bundled_default_config()
    info = compute_components(img, 1, config)
    assert info.stray_contact_area_mm2 == pytest.approx(27.0)
    assert info.stray_contact_label == 2


# =========================================================================== #
# Named adversarial case: largest-component-tie-is-broken-by-ascending-id
# =========================================================================== #


def test_largest_component_tie_is_broken_by_ascending_id():
    """Item 167, Correction 2026-09-20, C6: two of label 1's components tie
    for largest (3 voxels each). The documented policy -- descending voxel
    count, ties broken by ascending component id -- excludes the *first*
    (lower-id) component as "the largest" and considers the second
    (higher-id) one, which is the one that actually touches label 2.

    Failure mode guarded: under the opposite (or an unstable) tie-break, the
    *contacting* (higher-id) component would be the one excluded instead,
    and ``stray_contact_area_mm2`` would silently read 0.0 -- the detector
    going quiet on exactly the split it exists to catch.

    Construction (isotropic 1mm spacing, so every face has area 1.0 mm^2):
    label 1 has two 3-voxel line components, separated by a background gap
    -- the first (positions 0-2, lower id) touches nothing; the second
    (positions 4-6, higher id) has its last voxel (position 6) face-adjacent
    to a single voxel of label 2 (position 7). One contacting face -> the
    hand-computed expected area is 1.0 mm^2, naming label 2.
    """
    shape = (9, 1, 1)
    data = np.zeros(shape, dtype=LABEL_DTYPE)
    data[0:3, 0, 0] = 1  # component A (lower id) -- 3 voxels, touches nothing
    data[4:7, 0, 0] = 1  # component B (higher id) -- 3 voxels, ties A's size
    data[7, 0, 0] = 2  # label 2, face-adjacent to component B's last voxel only
    img = nib.Nifti1Image(data, affine_from_spacing((1.0, 1.0, 1.0)))

    config = bundled_default_config()
    info = compute_components(img, 1, config)
    assert info.component_count == 2
    assert info.component_sizes == [3, 3]
    assert info.stray_contact_area_mm2 == pytest.approx(1.0)
    assert info.stray_contact_label == 2
