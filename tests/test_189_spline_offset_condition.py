"""Tests for item 189 -- ``mislabel``'s ``spline_offset`` detector moves to a
new mode-less ``spline_offset`` rule, becoming the recording rule of a new
case CONDITION, ``displaced_vertebra`` (``failure_modes.CONDITIONS``),
alongside ``fov_truncation``. ``mislabel`` keeps only its ``ordering``
detector (mode 9). ``displace`` moves from a mode-1 corpus case (a recorded
co-detection) to the new condition's own fixture, the way ``crop_at_border``
is ``fov_truncation``'s.

Covers Acceptance Criteria AC1-AC14 per the item spec's Testing Strategy: one
test per AC, each read live off the registry / catalogue / ``SPECIFICATION`` /
``CONDITIONS`` / the committed manifest -- never a hand-built copy.

Plus exactly the three adversarial cases the Testing Strategy names:
``every-displace-rung-silent-for-mislabel``, ``threshold-read-from-own-section``
and ``mode-less-detector-excused``.
"""

from __future__ import annotations

import nibabel as nib
import numpy as np

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes
from segfacet.catalogue import build_catalogue
from segfacet.config import bundled_default_config
from segfacet.eval.severity_ladder import LADDER_SEED, SEVERITY_LADDERS
from segfacet.heuristics import get_rule
from segfacet.heuristics.mislabel import MislabelRule
from segfacet.pipeline import extract_feature_record, run_qc
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.corpus import load_manifest
from segfacet.synth.perturbation import corpus_case_kind, get_perturbation
from segfacet.synth.regression import loaded_seg_image, pipeline_findings


# =========================================================================== #
# Helpers
# =========================================================================== #


def _manifest_cases():
    return load_manifest()["cases"]


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in _manifest_cases() if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


# =========================================================================== #
# AC1: mislabel declares the ordering detector alone
# =========================================================================== #


def test_ac1_mislabel_declares_ordering_detector_alone():
    assert tuple(
        d.detector_id for d in MislabelRule.mode_declaration.detectors
    ) == ("ordering",)


# =========================================================================== #
# AC2: mislabel reads no spline-offset path
# =========================================================================== #


def test_ac2_mislabel_reads_no_spline_offset_path():
    entries = build_catalogue(strict=True).entries
    checked = 0
    for entry in entries:
        if entry.path.startswith("stage3.per_label_offsets[]"):
            assert "mislabel" not in entry.consuming_rules, entry.path
            checked += 1
    assert checked > 0, "expected at least one stage3.per_label_offsets[] entry"


# =========================================================================== #
# AC3: the spline_offset rule declares no failure mode
# =========================================================================== #


def test_ac3_spline_offset_rule_declares_no_failure_mode():
    assert get_rule("spline_offset").mode_declaration.modes == ()


# =========================================================================== #
# AC4: the offset is the condition's signal
# =========================================================================== #


def test_ac4_offset_is_the_conditions_signal():
    entries = build_catalogue(strict=True).entries
    matches = [e for e in entries if e.path == "stage3.per_label_offsets[].offset_mm"]
    assert len(matches) == 1, matches
    assert matches[0].mode_roles == (("spline_offset", "condition-signal"),)


# =========================================================================== #
# AC5: the condition is recorded by spline_offset
# =========================================================================== #


def test_ac5_condition_is_recorded_by_spline_offset():
    assert failure_modes.CONDITIONS["displaced_vertebra"].recording_rules == (
        "spline_offset",
    )


# =========================================================================== #
# AC6: displace is a condition case
# =========================================================================== #


def test_ac6_displace_is_a_condition_case():
    case = _manifest_case("displace")
    assert corpus_case_kind(case) == "condition"


# =========================================================================== #
# AC7: displace is the condition's fixture
# =========================================================================== #


def test_ac7_displace_is_the_conditions_fixture():
    condition = failure_modes.CONDITIONS["displaced_vertebra"]
    assert {c.case_id for c in condition.corpus_cases} == {"displace"}


# =========================================================================== #
# AC8: no mode claims displace
# =========================================================================== #


def test_ac8_no_mode_claims_displace():
    for mode_spec in failure_modes.SPECIFICATION.values():
        assert all(c.case_id != "displace" for c in mode_spec.corpus_cases), mode_spec.id


# =========================================================================== #
# AC9: mislabel fires on no displaced-only case
# =========================================================================== #


def test_ac9_mislabel_fires_on_no_displaced_only_case():
    condition = failure_modes.CONDITIONS["displaced_vertebra"]
    assert condition.corpus_cases, "expected at least one condition case"
    for case in condition.corpus_cases:
        assert "mislabel" not in failure_modes.measured_firing(case), case.case_id


# =========================================================================== #
# AC10: the condition is recorded on displace
# =========================================================================== #


def test_ac10_condition_is_recorded_on_displace():
    case = _manifest_case("displace")
    findings = [f for f in pipeline_findings(case) if f.rule_id == "spline_offset"]
    assert len(findings) == 1, findings
    assert findings[0].detector_id == "spline_offset"
    assert findings[0].labels == frozenset({22})


# =========================================================================== #
# AC11: crop_at_border's firing is re-measured
# =========================================================================== #


def test_ac11_crop_at_border_firing_is_remeasured():
    # item 191 (2026-09-28): the runner gates spline_offset's finding on the
    # touching label -- it does not opt in to fov_truncation -- so the
    # measured set narrows to border alone.
    condition = failure_modes.CONDITIONS["fov_truncation"]
    matches = [c for c in condition.corpus_cases if c.case_id == "crop_at_border"]
    assert len(matches) == 1, matches
    assert set(failure_modes.measured_firing(matches[0])) == {"border"}


# =========================================================================== #
# AC12: the terminal-skip exemption moves with the detector
# =========================================================================== #


def test_ac12_terminal_skip_exemption_moves_with_detector():
    # item 191 (2026-09-28): exempting_rules renamed opting_in_rules; coverage
    # no longer belongs (its findings are case-level, so the gate never
    # reaches them -- A3), leaving only the recording rule, which now opts in.
    condition = failure_modes.CONDITIONS["fov_truncation"]
    assert set(condition.opting_in_rules) == {"border"}


# =========================================================================== #
# AC13: the ordering detector fires on a non-adjacent swap
# =========================================================================== #


def test_ac13_ordering_detector_fires_on_non_adjacent_swap():
    case = _manifest_case("clean_control")
    seg_img = loaded_seg_image(case)
    data = np.asanyarray(seg_img.dataobj)
    swapped = data.copy()
    swapped[data == 21] = 23
    swapped[data == 23] = 21
    swapped_img = nib.Nifti1Image(swapped, seg_img.affine, dtype=swapped.dtype)

    case_result, _block = run_qc(swapped_img, bundled_default_config())
    detector_ids = {
        f.detector_id for f in case_result.findings if f.rule_id == "mislabel"
    }
    assert detector_ids == {"ordering"}


# =========================================================================== #
# AC14: the recorded corpus margins are live
# =========================================================================== #


def test_ac14_recorded_corpus_margins_are_live():
    import segfacet.heuristics.spline_offset as spline_offset_module

    config = bundled_default_config()
    cases = _manifest_cases()

    non_firing_interior_offsets = []
    for case in cases:
        fires = any(f.rule_id == "spline_offset" for f in pipeline_findings(case))
        if fires:
            continue
        record = extract_feature_record(loaded_seg_image(case), config)
        for entry in record["stage3"]["per_label_offsets"]:
            if entry.get("is_terminal"):
                continue
            non_firing_interior_offsets.append(entry["offset_mm"])
    assert non_firing_interior_offsets, "expected >=1 non-firing interior offset"
    largest_non_firing = max(non_firing_interior_offsets)

    def _label_22_offset(case_id: str) -> float:
        record = extract_feature_record(
            loaded_seg_image(_manifest_case(case_id)), config
        )
        matches = [
            e for e in record["stage3"]["per_label_offsets"] if e["label"] == 22
        ]
        assert len(matches) == 1, matches
        assert not matches[0].get("is_terminal"), "expected label 22 to be interior"
        return matches[0]["offset_mm"]

    crop_offset = _label_22_offset("crop_at_border")
    displace_offset = _label_22_offset("displace")

    docstring = spline_offset_module.__doc__ or ""
    for value in (largest_non_firing, crop_offset, displace_offset):
        assert f"{value:.6f}" in docstring, (value, docstring)


# =========================================================================== #
# Named adversarial case: every-displace-rung-silent-for-mislabel
# =========================================================================== #


def test_every_displace_rung_silent_for_mislabel():
    spec = SEVERITY_LADDERS["displace"]
    config = bundled_default_config()
    for rung in spec.rungs:
        img = build_clean_spine().seg_img
        for op_name, kwargs in rung.steps:
            operator = get_perturbation(op_name)(**dict(kwargs))
            img = operator.apply(img, LADDER_SEED).labelmap
        case_result, _block = run_qc(img, config)
        assert not any(f.rule_id == "mislabel" for f in case_result.findings), rung.label


# =========================================================================== #
# Named adversarial case: threshold-read-from-own-section
# =========================================================================== #


def test_threshold_read_from_own_section():
    case = _manifest_case("displace")
    config = bundled_default_config()
    record = extract_feature_record(loaded_seg_image(case), config)
    matches = [e for e in record["stage3"]["per_label_offsets"] if e["label"] == 22]
    assert len(matches) == 1, matches
    offset_mm = matches[0]["offset_mm"]

    high_mislabel_config = bundled_default_config()
    high_mislabel_config.rules.setdefault("mislabel", {}).setdefault("params", {})[
        "max_offset_mm"
    ] = 1000.0
    findings = [
        f
        for f in run_qc(loaded_seg_image(case), high_mislabel_config)[0].findings
        if f.rule_id == "spline_offset"
    ]
    assert len(findings) == 1, findings

    just_below_config = bundled_default_config()
    just_below_config.rules.setdefault("spline_offset", {}).setdefault("params", {})[
        "max_offset_mm"
    ] = offset_mm + 1e-9
    findings = [
        f
        for f in run_qc(loaded_seg_image(case), just_below_config)[0].findings
        if f.rule_id == "spline_offset"
    ]
    assert findings == []


# =========================================================================== #
# Named adversarial case: mode-less-detector-excused
# =========================================================================== #


def test_mode_less_detector_excused():
    assert failure_modes.modes_for_detector("spline_offset", "spline_offset") == ()
    rule = get_rule("spline_offset")
    matches = [
        d for d in rule.mode_declaration.detectors if d.detector_id == "spline_offset"
    ]
    assert len(matches) == 1, matches
    assert matches[0].mode_less_reason
