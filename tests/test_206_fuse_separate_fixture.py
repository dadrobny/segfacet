"""Tests for item 206 -- the ``fuse_separate`` corpus case: one label (22) over
two full, separate vertebrae (L3 and L4, the disc gap left unlabelled), with L5
renumbered 23 so the label sequence stays continuous. Attributed to mode 2.

Covers Acceptance Criteria AC1-AC3: one test per AC. AC2/AC3 load the
committed fixtures through the committed manifest's ``seg_fixture`` paths
(never a fresh ``build_corpus()``), so they pin the committed bytes.

Plus exactly the two adversarial cases the Testing Strategy names:
``bridged-renumber-false-raises`` and ``default-unbridged-form-unchanged``.
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.ndimage as ndi

import segfacet.synth  # noqa: F401 -- triggers self-registration of the operators
from segfacet import failure_modes
from segfacet.io import FacetInputError
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.component_shape import FusePerturbation
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image


def _committed_array(case_id: str) -> np.ndarray:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return np.asanyarray(loaded_seg_image(matches[0]).dataobj)


def test_ac1_fuse_separate_is_attributed_to_mode_2_alone():
    modes = {
        mode_id
        for mode_id, mode in failure_modes.SPECIFICATION.items()
        if any(c.case_id == "fuse_separate" for c in mode.corpus_cases)
    }
    assert modes == {2}


def test_ac2_label_22_is_exactly_the_two_full_bodies():
    fixture = _committed_array("fuse_separate")
    clean = _committed_array("clean_control")
    assert int(np.count_nonzero(clean == 22)) > 0
    assert int(np.count_nonzero(clean == 23)) > 0

    labelled, n = ndi.label(fixture == 22)
    assert n == 2
    components = {
        frozenset(np.flatnonzero(labelled == i).tolist()) for i in range(1, n + 1)
    }
    expected = {
        frozenset(np.flatnonzero(clean == 22).tolist()),
        frozenset(np.flatnonzero(clean == 23).tolist()),
    }
    assert components == expected


def test_ac3_every_other_voxel_is_the_clean_map_with_l5_renumbered():
    fixture = _committed_array("fuse_separate")
    clean = _committed_array("clean_control")
    assert int(np.count_nonzero(clean == 24)) > 0

    outside = (clean != 22) & (clean != 23)
    renumbered = np.where(clean == 24, 23, clean)
    assert np.array_equal(fixture[outside], renumbered[outside])


def test_bridged_renumber_false_raises():
    """Guards the combination silently yielding a label map the bridged
    ``Expectation`` ("fires nothing") no longer describes."""
    with pytest.raises(FacetInputError):
        FusePerturbation(
            target_label=22, neighbour_label=23, bridged=True, renumber=False
        ).apply(build_clean_spine().seg_img, 0)


def test_default_unbridged_form_unchanged():
    """Guards the ``renumber=None`` default renumbering the supplementary
    ladder's unbridged form."""
    result = FusePerturbation(target_label=22, neighbour_label=23).apply(
        build_clean_spine().seg_img, 0
    )
    out = np.asanyarray(result.labelmap.dataobj)
    assert int(np.count_nonzero(out == 24)) > 0
    assert result.expectation.expected_rule_ids == frozenset(
        {"coverage", "fragmentation"}
    )
