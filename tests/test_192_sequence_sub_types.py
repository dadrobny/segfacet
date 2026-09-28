"""Tests for item 192 -- ``sequence`` reports which sub-type it saw.

The rule stops reading ``relationships.out_of_order_labels[]`` (integer-label
order, item 186's defect) and instead orders each kept ``per_label`` entry
head-to-tail by its centroid, ranks that order by ``CANONICAL_ORDER``, and
reports one of four sub-types: ``swap``, ``shift`` (mode 9), ``skip``
(mode 10) and ``transitional`` (mode 11).

Covers Acceptance Criteria AC1-AC10 from
``docs/aide/items/192-sequence-reports-which-sub-type.md``, one test each,
plus exactly the four surviving named adversarial cases from its Testing
Strategy (as corrected 2026-09-28):
``lumbar-reading-uncorroborated``, ``sacral-labels-share-one-rank``,
``no-centroid-no-finding``, ``full-reversal-reads-as-flipped`` and
``ascending-fixture-fires-no-sequence``. ``non-adjacent-swap-names-moved-labels``
was withdrawn by the same correction.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np

from segfacet.config import bundled_default_config
from segfacet.heuristics import get_rule, run_rules
from segfacet.pipeline import extract_feature_record
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image, pipeline_findings
from synthetic import anisotropic_case, labelled_blocks_case

_MANIFEST = load_manifest()
_CFG = bundled_default_config()


def _case(case_id: str) -> dict:
    return next(c for c in _MANIFEST["cases"] if c["case_id"] == case_id)


_CLEAN_MAP = loaded_seg_image(_case("clean_control"))


def relabel(mapping: dict) -> nib.Nifti1Image:
    """The clean map with every voxel value ``a`` in *mapping* replaced by
    ``mapping[a]`` (each replacement read from the original data), on the
    same affine and header."""
    data = np.asarray(_CLEAN_MAP.dataobj)
    original = data.copy()
    out = data.copy()
    for src, dst in mapping.items():
        out[original == src] = dst
    return nib.Nifti1Image(out, _CLEAN_MAP.affine, _CLEAN_MAP.header, dtype=out.dtype)


def seq(img: nib.Nifti1Image) -> set:
    record = extract_feature_record(img, _CFG)
    return {
        (f.detector_id, f.labels)
        for f in run_rules(record, _CFG)
        if f.rule_id == "sequence"
    }


# =========================================================================== #
# AC1-AC10
# =========================================================================== #


def test_ac1_swap_reported_as_swap():
    assert seq(loaded_seg_image(_case("relabel_swap"))) == {
        ("swap", frozenset({21, 22}))
    }


def test_ac2_moved_label_reported_as_shift():
    assert seq(relabel({20: 21, 21: 22, 22: 20})) == {("shift", frozenset({20}))}


def test_ac3_skipped_level_reported_as_skip():
    assert seq(relabel({20: 19, 21: 20, 22: 21})) == {("skip", frozenset())}


def test_ac4_uncorroborated_t13_reported_as_transitional():
    assert seq(relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})) == {
        ("transitional", frozenset({28}))
    }


def test_ac5_uncorroborated_short_thoracic_is_transitional_not_skip():
    assert seq(relabel({20: 17, 21: 18, 22: 20, 23: 21, 24: 22})) == {
        ("transitional", frozenset({18}))
    }


def test_ac6_correct_coccyx_below_sacrum_fires_nothing():
    assert seq(relabel({20: 23, 21: 24, 22: 26, 23: 29, 24: 27})) == set()


def test_ac7_sequence_break_finding_names_its_sub_type():
    findings = pipeline_findings(_case("sequence_break"))
    reduced = {
        (f.detector_id, f.labels) for f in findings if f.rule_id == "sequence"
    }
    assert reduced == {("shift", frozenset({28}))}


def test_ac8_rule_declares_modes_9_10_11_and_no_other():
    assert get_rule("sequence").mode_declaration.modes == (9, 10, 11)


def test_ac9_each_sub_type_serves_its_own_mode():
    from segfacet import failure_modes

    assert {
        d: failure_modes.modes_for_detector("sequence", d)
        for d in ("shift", "skip", "swap", "transitional")
    } == {"shift": (9,), "skip": (10,), "swap": (9,), "transitional": (11,)}


def test_ac10_swap_on_displaced_reading_label_still_fires():
    record = extract_feature_record(relabel({20: 21, 21: 20}), _CFG)
    findings = run_rules(record, _CFG)
    reduced = {
        (f.rule_id, f.detector_id, f.labels)
        for f in findings
        if f.rule_id in {"sequence", "spline_offset"}
    }
    assert reduced == {
        ("sequence", "swap", frozenset({20, 21})),
        ("spline_offset", "spline_offset", frozenset({21})),
    }


# =========================================================================== #
# Named adversarial cases (Testing Strategy, corrected 2026-09-28)
# =========================================================================== #


def test_lumbar_reading_uncorroborated():
    assert seq(relabel({24: 26})) == {("transitional", frozenset({23}))}


def test_sacral_labels_share_one_rank():
    assert seq(relabel({23: 29, 24: 26})) == {("skip", frozenset())}


def test_no_centroid_no_finding():
    record = {
        "relationships": {
            "present_levels": ["L1", "T12"],
            "is_continuous": False,
            "out_of_order_labels": ["T12"],
        },
        "per_label": {
            "19": {"label": 19, "level_name": "T12"},
            "20": {"label": 20, "level_name": "L1"},
        },
    }
    assert get_rule("sequence").evaluate(record, _CFG) == []


def test_full_reversal_reads_as_flipped():
    assert seq(relabel({20: 24, 21: 23, 23: 21, 24: 20})) == set()


def test_ascending_fixture_fires_no_sequence():
    for case in (labelled_blocks_case(), anisotropic_case()):
        record = extract_feature_record(case.seg_img, _CFG)
        findings = run_rules(record, _CFG)
        assert not any(f.rule_id == "sequence" for f in findings)
