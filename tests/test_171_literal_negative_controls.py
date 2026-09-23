"""Tests for item 171 -- literal negative controls rebuilt from live values.

Covers Acceptance Criteria AC1-AC6 from
``docs/aide/items/171-literal-negative-controls-rebuilt-from-live-values.md``,
one test each, plus the one named adversarial case from its Testing
Strategy: ``old-literal-form-fails-under-patch``, parametrised over the six
rebuilt hits (H1-H6).

Each AC monkeypatches the seam its target control reads (A4) so that the
seam reports the *old literal's* value, then calls the rebuilt control
(H1-H6, rebuilt in place in their own modules by this same item) and asserts
it still passes -- i.e. the rebuilt control is non-coincidental: it rejects
its perturbed input regardless of what live state happens to be.

The five target modules are loaded by path with
``importlib.util.spec_from_file_location``, under a module name unique to
this file, the way ``test_170_...``/``test_159_...`` do, so pytest does not
collect them twice.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TESTS_DIR = _REPO_ROOT / "tests"


def _load_module_from_path(path: Path, unique_name: str):
    spec = importlib.util.spec_from_file_location(unique_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _fake_finding(rule_id: str, labels=()):
    return SimpleNamespace(rule_id=rule_id, labels=tuple(labels))


# =========================================================================== #
# AC1: H1 (test_151) survives a mode count of 15.
# =========================================================================== #


def test_ac1_h1_survives_mode_count_of_15(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_151_stage30_validation.py", "_test_171_test_151"
    )
    _, live_counts = module._live_status_counts()

    monkeypatch.setattr(module, "_live_status_counts", lambda: (15, live_counts))
    # The defect is really present before we trust the pass below (§6).
    assert module._live_status_counts()[0] == 15

    module.test_adv_ac35_status_counts_parser_rejects_wrong_n()


# =========================================================================== #
# AC2: H2 (test_041) survives a live verdict of "pass".
# =========================================================================== #


def test_ac2_h2_survives_live_verdict_of_pass(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_041_regression_suite.py", "_test_171_test_041_ac9"
    )
    import segfacet.synth.regression as regression

    def _always_pass(case, config=None):
        return "pass"

    monkeypatch.setattr(module, "pipeline_verdict_label", _always_pass)
    monkeypatch.setattr(regression, "pipeline_verdict_label", _always_pass)
    case = module._case("sequence_break")
    # The defect is really present before we trust the pass below (§6).
    assert module.pipeline_verdict_label(case) == "pass"

    module.test_ac9_verdict_drift_is_caught()


# =========================================================================== #
# AC3: H3 (test_041) survives a live firing set of {"overlap"}.
# =========================================================================== #


def test_ac3_h3_survives_live_firing_set_of_overlap(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_041_regression_suite.py", "_test_171_test_041_ac10"
    )
    import segfacet.synth.regression as regression

    fake = (_fake_finding("overlap", (28,)),)

    def _fake_pipeline_findings(case, config=None):
        return fake

    monkeypatch.setattr(module, "pipeline_findings", _fake_pipeline_findings)
    monkeypatch.setattr(regression, "pipeline_findings", _fake_pipeline_findings)
    case = module._case("sequence_break")
    # The defect is really present before we trust the pass below (§6).
    assert {f.rule_id for f in module.pipeline_findings(case)} == {"overlap"}

    module.test_ac10_fired_rule_drift_is_caught()


# =========================================================================== #
# AC4: H4 (test_138) survives a live firing set equal to the old claim.
# =========================================================================== #


def test_ac4_h4_survives_live_firing_set_equal_to_old_claim(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_138_traceability_matrix.py", "_test_171_test_138"
    )
    import segfacet.synth.regression as regression

    fake = (
        _fake_finding("bounds"),
        _fake_finding("fragmentation"),
        _fake_finding("reference_delta"),
    )

    def _fake_pipeline_findings(case, config=None):
        return fake

    monkeypatch.setattr(regression, "pipeline_findings", _fake_pipeline_findings)
    # The defect is really present before we trust the pass below (§6).
    assert {f.rule_id for f in regression.pipeline_findings(None)} == {
        "bounds",
        "fragmentation",
        "reference_delta",
    }

    module.test_adv_ac31_measured_findings_claim_overclaiming_a_rule_is_detectable(monkeypatch)


# =========================================================================== #
# AC5: H5 (test_153) survives a derived home of 99.
# =========================================================================== #


def test_ac5_h5_survives_derived_home_of_99(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_153_eval_harness_rekey.py", "_test_171_test_153"
    )

    monkeypatch.setattr(module, "_derived_home", lambda metric_name: 99)
    # The defect is really present before we trust the pass below (§6).
    assert module._derived_home("unanchored_foreground_fraction") == 99

    module.test_adv_ac5_wrong_home_is_detected()


# =========================================================================== #
# AC6: H6 (test_154) survives rogue_island_count already living in mode 1.
# =========================================================================== #


def _patch_rogue_island_home_to_1(monkeypatch):
    """Shared by AC6 and the H6 branch of the adversarial case below: patch
    both PER_MODE_METRIC_SPECS and MODE_LADDER_DISPOSITIONS the way A4
    requires, and return the module handles used to build the patch."""
    import segfacet.eval.per_mode as per_mode
    import segfacet.eval.severity_ladder as severity_ladder

    patched_specs = dict(per_mode.PER_MODE_METRIC_SPECS)
    patched_specs["rogue_island_count"] = dataclasses.replace(
        patched_specs["rogue_island_count"], failure_mode=1
    )
    monkeypatch.setattr(per_mode, "PER_MODE_METRIC_SPECS", patched_specs)

    # MODE_LADDER_DISPOSITIONS[1].ladders is computed from the specs at
    # import (severity_ladder.py); recompute it the same way so the table
    # stays consistent with the patched specs (A4).
    recomputed_ladders = tuple(
        operator
        for operator in severity_ladder.SEVERITY_LADDERS
        if patched_specs[severity_ladder.SEVERITY_LADDERS[operator].designated_metric].failure_mode
        == 1
    )
    patched_dispositions = dict(severity_ladder.MODE_LADDER_DISPOSITIONS)
    patched_dispositions[1] = dataclasses.replace(
        patched_dispositions[1], ladders=recomputed_ladders
    )
    monkeypatch.setattr(severity_ladder, "MODE_LADDER_DISPOSITIONS", patched_dispositions)

    return per_mode, severity_ladder


def test_ac6_h6_survives_rogue_island_count_already_in_mode_1(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_154_ladder_remeasurement.py", "_test_171_test_154"
    )
    per_mode, severity_ladder = _patch_rogue_island_home_to_1(monkeypatch)

    # The defect is really present before we trust the pass below (§6):
    # every ladder designating rogue_island_count is now recorded under
    # mode 1's disposition.
    designating_ladders = tuple(
        operator
        for operator in severity_ladder.SEVERITY_LADDERS
        if severity_ladder.SEVERITY_LADDERS[operator].designated_metric == "rogue_island_count"
    )
    assert designating_ladders
    for operator in designating_ladders:
        assert operator in severity_ladder.MODE_LADDER_DISPOSITIONS[1].ladders

    module.test_adv_ac14_rehoming_a_metric_changes_the_derived_tuple(monkeypatch, severity_ladder)


# =========================================================================== #
# Adversarial: old-literal-form-fails-under-patch
# =========================================================================== #


def _h1_pre_item_body(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_151_stage30_validation.py", "_test_171_adv_test_151"
    )
    _, live_counts = module._live_status_counts()
    monkeypatch.setattr(module, "_live_status_counts", lambda: (15, live_counts))

    text = "derived status counts over 15 modes: validated 6, implemented 3, specified 0, proposed 7"
    match = module._STATUS_COUNTS_RE.search(text)
    assert match is not None
    n = int(match.group(1))
    live_n, _live_counts = module._live_status_counts()
    assert n != live_n


def _h2_pre_item_body(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_041_regression_suite.py", "_test_171_adv_test_041_ac9"
    )
    import segfacet.synth.regression as regression

    def _always_pass(case, config=None):
        return "pass"

    monkeypatch.setattr(module, "pipeline_verdict_label", _always_pass)
    monkeypatch.setattr(regression, "pipeline_verdict_label", _always_pass)

    case = module._case("sequence_break")
    assert case["detection"] == "pipeline"
    drifted = copy.deepcopy(case)
    drifted["expected_verdict"] = "pass"

    assert drifted["expected_verdict"] != module.pipeline_verdict_label(case)
    assert module.verify_case(drifted) is False


def _h3_pre_item_body(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_041_regression_suite.py", "_test_171_adv_test_041_ac10"
    )
    import segfacet.synth.regression as regression

    fake = (_fake_finding("overlap", (28,)),)

    def _fake_pipeline_findings(case, config=None):
        return fake

    monkeypatch.setattr(module, "pipeline_findings", _fake_pipeline_findings)
    monkeypatch.setattr(regression, "pipeline_findings", _fake_pipeline_findings)

    case = module._case("sequence_break")
    assert case["detection"] == "pipeline"
    drifted = copy.deepcopy(case)
    drifted["expected_rule_ids"] = ["overlap"]

    assert module.designated_rule_fired(drifted) is False


def _h4_pre_item_body(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_138_traceability_matrix.py", "_test_171_adv_test_138"
    )
    import segfacet.synth.regression as regression
    from segfacet.synth.corpus import load_manifest

    fake = (
        _fake_finding("bounds"),
        _fake_finding("fragmentation"),
        _fake_finding("reference_delta"),
    )

    def _fake_pipeline_findings(case, config=None):
        return fake

    monkeypatch.setattr(regression, "pipeline_findings", _fake_pipeline_findings)

    from segfacet.synth.regression import pipeline_findings  # picks up the patch above

    manifest = load_manifest()
    cases_by_id = {c["case_id"]: c for c in manifest.get("cases", [])}
    case = cases_by_id["fragment"]
    assert case.get("detection") == "pipeline"

    actual_rule_ids = {f.rule_id for f in pipeline_findings(case)}
    assert actual_rule_ids == {"fragmentation"}, actual_rule_ids

    overclaiming_mechanism = (
        "caught independently by bounds' magnitude thresholds, "
        "fragmentation's component-count checks, and reference_delta's "
        "cohort-relative scoring on fragment (measured: findings == "
        "['bounds', 'fragmentation', 'reference_delta'])."
    )
    claim = module._parse_measured_findings_claim(overclaiming_mechanism)
    assert claim == {"bounds", "fragmentation", "reference_delta"}
    assert claim != actual_rule_ids


def _h5_pre_item_body(monkeypatch):
    module = _load_module_from_path(
        _TESTS_DIR / "test_153_eval_harness_rekey.py", "_test_171_adv_test_153"
    )
    import segfacet.eval.per_mode as per_mode

    monkeypatch.setattr(module, "_derived_home", lambda metric_name: 99)

    real = per_mode.PER_MODE_METRIC_SPECS["unanchored_foreground_fraction"]
    wrong = dataclasses.replace(real, failure_mode=99)
    assert wrong.failure_mode != module._derived_home("unanchored_foreground_fraction")


def _h6_pre_item_body(monkeypatch):
    per_mode, severity_ladder = _patch_rogue_island_home_to_1(monkeypatch)

    patched_specs = per_mode.PER_MODE_METRIC_SPECS
    rehomed_ladders = tuple(
        operator
        for operator in severity_ladder.SEVERITY_LADDERS
        if patched_specs[severity_ladder.SEVERITY_LADDERS[operator].designated_metric].failure_mode
        == 1
    )
    assert rehomed_ladders != severity_ladder.MODE_LADDER_DISPOSITIONS[1].ladders


_PRE_ITEM_BODIES = {
    "H1": _h1_pre_item_body,
    "H2": _h2_pre_item_body,
    "H3": _h3_pre_item_body,
    "H4": _h4_pre_item_body,
    "H5": _h5_pre_item_body,
    "H6": _h6_pre_item_body,
}


@pytest.mark.parametrize("hit", sorted(_PRE_ITEM_BODIES))
def test_adv_old_literal_form_fails_under_patch(hit, monkeypatch):
    """Guards against a patch that does not reach the seam a rebuilt
    control reads: under each AC's own patch, the corresponding hit's
    pre-item body (wrong input + final rejection, literal preconditions
    dropped per A3) must still raise ``AssertionError``. A patch that
    missed its seam would let the old and rebuilt forms both pass, and
    AC1-AC6 would certify nothing."""
    with pytest.raises(AssertionError):
        _PRE_ITEM_BODIES[hit](monkeypatch)
