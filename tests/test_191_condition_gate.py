"""Tests for item 191 -- the condition gate over rule findings.

Today a condition (``segfacet.failure_modes.CONDITIONS``) is a record only:
each rule's own code decides whether it exempts a condition's labels.  This
item inverts that: the gate belongs to the condition and runs in one place,
``segfacet.heuristics.run_rules``. A finding that names a label in a
condition is dropped unless the rule that produced it opts in, via a new
``Rule.condition_opt_ins`` class attribute of ``ConditionOptIn`` entries;
``ConditionSpec.exempting_rules`` becomes ``ConditionSpec.opting_in_rules``,
the specification's record of which rules opt in.

Covers Acceptance Criteria AC1-AC12 from
``docs/aide/items/191-a-condition-flagged-label-is.md``, one test each, plus
exactly the six named adversarial cases from its Testing Strategy:
``any-member-label-gates``, ``case-level-finding-passes``,
``opt-in-is-per-condition``, ``record-not-mutated``,
``border-aware-span-control`` and ``opt-in-rejects-bare-string``.

AC1, AC6 and AC7 read firing through ``pipeline_findings`` and
``failure_modes.measured_firing``; AC2 and AC8 through
``run_qc_with_reference``. None re-implements the gate.
"""

from __future__ import annotations

import copy
import dataclasses

import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes
from segfacet.catalogue import build_catalogue
from segfacet.config import bundled_default_config
from segfacet.heuristics import Finding, Rule, iter_rules, run_rules
from segfacet.heuristics.rule import ConditionOptIn
from segfacet.pipeline import extract_feature_record, run_qc_with_reference
from segfacet.reference.artifact import bundled_production_reference
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image, pipeline_findings
from segfacet.verdict import Severity

_TOUCH_FLAGS = (
    "touches_superior",
    "touches_inferior",
    "touches_left",
    "touches_right",
    "touches_anterior",
    "touches_posterior",
)

_FOV_OPT_IN = ConditionOptIn(
    condition="fov_truncation",
    paths=("per_label.{label}.geometry.physical_volume_mm3",),
    reason="planted",
)


# =========================================================================== #
# Helpers
# =========================================================================== #


def _manifest_case(case_id: str) -> dict:
    matches = [c for c in load_manifest()["cases"] if c["case_id"] == case_id]
    assert len(matches) == 1, matches
    return matches[0]


def _rec(case_id: str, config) -> dict:
    return extract_feature_record(loaded_seg_image(_manifest_case(case_id)), config)


class _PlantedRule(Rule):
    """A planted rule on ``labels``, per the item spec's Testing Strategy
    term: ``evaluate`` returns exactly one ``Finding`` naming ``labels``."""

    rule_id = "planted"

    def __init__(self, labels, condition_opt_ins=()):
        self._labels = frozenset(labels)
        self.condition_opt_ins = condition_opt_ins

    def evaluate(self, record, config):
        return [
            Finding(
                rule_id="planted",
                severity=Severity.FLAG,
                reason="planted",
                labels=frozenset(self._labels),
            )
        ]


# =========================================================================== #
# AC1: the truncated remnant fires nothing
# =========================================================================== #


def test_ac1_truncated_remnant_fires_nothing():
    case = _manifest_case("crop_fov_si")
    findings = [f for f in pipeline_findings(case) if 24 in f.labels]
    assert findings == []


# =========================================================================== #
# AC2: the truncated remnant fires nothing against the reference
# =========================================================================== #


def test_ac2_truncated_remnant_fires_nothing_against_the_reference():
    case = _manifest_case("crop_fov_si")
    seg_img = loaded_seg_image(case)
    cfg = bundled_default_config()
    reference = bundled_production_reference()
    case_result, _features_block, _reference_delta = run_qc_with_reference(
        seg_img, cfg, reference
    )
    findings = [f for f in case_result.findings if 24 in f.labels]
    assert findings == []


# =========================================================================== #
# AC3: the same volume on an interior label still fires
# =========================================================================== #


def test_ac3_same_volume_on_interior_label_still_fires():
    cfg = bundled_default_config()
    record = copy.deepcopy(_rec("crop_fov_si", cfg))
    geometry = record["per_label"]["24"]["geometry"]
    for flag in _TOUCH_FLAGS:
        if flag in geometry:
            geometry[flag] = False

    pairs = {
        (f.rule_id, f.detector_id) for f in run_rules(record, cfg) if 24 in f.labels
    }
    assert pairs == {("bounds", "metric_out_of_range")}


# =========================================================================== #
# AC4: a rule that does not opt in is gated
# =========================================================================== #


def test_ac4_rule_that_does_not_opt_in_is_gated():
    cfg = bundled_default_config()
    rule = _PlantedRule(labels={24})
    assert run_rules(_rec("crop_fov_si", cfg), cfg, rules=[rule]) == []


# =========================================================================== #
# AC5: a rule that opts in still fires on a border-touching label
# =========================================================================== #


def test_ac5_rule_that_opts_in_still_fires_on_a_border_touching_label():
    cfg = bundled_default_config()
    rule = _PlantedRule(labels={24}, condition_opt_ins=(_FOV_OPT_IN,))
    record = _rec("crop_fov_si", cfg)
    expected = rule.evaluate(record, cfg)
    assert run_rules(record, cfg, rules=[rule]) == expected


# =========================================================================== #
# AC6: crop_at_border is recorded by border alone
# =========================================================================== #


def test_ac6_crop_at_border_is_recorded_by_border_alone():
    condition = failure_modes.CONDITIONS["fov_truncation"]
    matches = [c for c in condition.corpus_cases if c.case_id == "crop_at_border"]
    assert len(matches) == 1, matches
    assert set(failure_modes.measured_firing(matches[0])) == {"border"}


# =========================================================================== #
# AC7: crop_fov_si fires nothing
# =========================================================================== #


def test_ac7_crop_fov_si_fires_nothing():
    condition = failure_modes.CONDITIONS["fov_truncation"]
    matches = [c for c in condition.corpus_cases if c.case_id == "crop_fov_si"]
    assert len(matches) == 1, matches
    assert set(failure_modes.measured_firing(matches[0])) == set()


# =========================================================================== #
# AC8: a displaced label is gated too
# =========================================================================== #


def test_ac8_a_displaced_label_is_gated_too():
    case = _manifest_case("displace")
    seg_img = loaded_seg_image(case)
    cfg = bundled_default_config()
    reference = bundled_production_reference()
    case_result, _features_block, _reference_delta = run_qc_with_reference(
        seg_img, cfg, reference
    )
    rule_ids = {f.rule_id for f in case_result.findings if 22 in f.labels}
    assert rule_ids == {"spline_offset"}


# =========================================================================== #
# AC9: coverage's border-aware span holds under the gate
# =========================================================================== #


def test_ac9_coverages_border_aware_span_holds_under_the_gate():
    cfg = bundled_default_config()
    record = copy.deepcopy(_rec("clean_control", cfg))
    record["per_label"]["24"]["geometry"]["touches_inferior"] = True
    cfg9 = dataclasses.replace(
        cfg,
        rules={
            **cfg.rules,
            "coverage": {
                "enabled": True,
                "params": {"expected_levels": ["L1", "L2", "L3", "L4", "L5", "L6"]},
            },
        },
    )
    findings = [f for f in run_rules(record, cfg9) if f.rule_id == "coverage"]
    assert findings == []


# =========================================================================== #
# AC10: the specification records the registry's opt-ins
# =========================================================================== #


def test_ac10_specification_records_the_registrys_opt_ins():
    for condition_id, spec in failure_modes.CONDITIONS.items():
        expected = tuple(
            sorted(
                r.rule_id
                for r in iter_rules()
                if condition_id in {o.condition for o in r.condition_opt_ins}
            )
        )
        assert spec.opting_in_rules == expected, condition_id


# =========================================================================== #
# AC11: the exemption list is gone
# =========================================================================== #


def test_ac11_the_exemption_list_is_gone():
    field_names = {f.name for f in dataclasses.fields(failure_modes.ConditionSpec)}
    assert field_names & {"exempting_rules", "opting_in_rules"} == {"opting_in_rules"}


# =========================================================================== #
# AC12: an opt-in names features its rule reads
# =========================================================================== #


def test_ac12_an_opt_in_names_features_its_rule_reads():
    catalogue = build_catalogue(strict=True)
    entries_by_path: dict = {}
    for entry in catalogue.entries:
        entries_by_path.setdefault(entry.path, []).append(entry)

    checked_any = False
    for rule in iter_rules():
        for opt_in in rule.condition_opt_ins:
            for path in opt_in.paths:
                checked_any = True
                matches = [
                    e for e in entries_by_path.get(path, ()) if rule.rule_id in e.consuming_rules
                ]
                assert matches, (rule.rule_id, path)

    # AC12 must not pass on an empty registry walk.
    assert checked_any


# =========================================================================== #
# any-member-label-gates
# =========================================================================== #


def test_any_member_label_gates():
    cfg = bundled_default_config()
    rule = _PlantedRule(labels={23, 24})
    assert run_rules(_rec("crop_fov_si", cfg), cfg, rules=[rule]) == []


# =========================================================================== #
# case-level-finding-passes
# =========================================================================== #


def test_case_level_finding_passes():
    cfg = bundled_default_config()
    rule = _PlantedRule(labels=set())
    record = _rec("crop_fov_si", cfg)
    expected = rule.evaluate(record, cfg)
    assert run_rules(record, cfg, rules=[rule]) == expected


# =========================================================================== #
# opt-in-is-per-condition
# =========================================================================== #


def test_opt_in_is_per_condition():
    cfg = bundled_default_config()
    displaced_opt_in = ConditionOptIn(
        condition="displaced_vertebra",
        paths=("stage3.per_label_offsets[].offset_mm",),
        reason="planted",
    )
    rule = _PlantedRule(labels={24}, condition_opt_ins=(displaced_opt_in,))
    assert run_rules(_rec("crop_fov_si", cfg), cfg, rules=[rule]) == []


# =========================================================================== #
# record-not-mutated
# =========================================================================== #


def test_record_not_mutated():
    cfg = bundled_default_config()
    record = _rec("crop_fov_si", cfg)
    before = copy.deepcopy(record)
    run_rules(record, cfg)
    assert record == before


# =========================================================================== #
# border-aware-span-control
# =========================================================================== #


def test_border_aware_span_control():
    cfg = bundled_default_config()
    record = copy.deepcopy(_rec("clean_control", cfg))
    cfg9 = dataclasses.replace(
        cfg,
        rules={
            **cfg.rules,
            "coverage": {
                "enabled": True,
                "params": {"expected_levels": ["L1", "L2", "L3", "L4", "L5", "L6"]},
            },
        },
    )
    findings = [f for f in run_rules(record, cfg9) if f.rule_id == "coverage"]
    assert len(findings) == 1, findings
    assert findings[0].detector_id == "incomplete_span"
    assert "L6" in findings[0].reason


# =========================================================================== #
# opt-in-rejects-bare-string
# =========================================================================== #


def test_opt_in_rejects_bare_string():
    with pytest.raises(ValueError):
        ConditionOptIn(condition="fov_truncation", paths="per_label", reason="x")
