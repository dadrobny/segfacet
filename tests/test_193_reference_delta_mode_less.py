"""Tests for item 193 -- ``reference_delta`` and ``intensity_reference_delta``
claim no mode as their own.

Both rules threshold a label's deviation from its level's cohort reference
distribution: general outlier detectors, no failure mode's own signal. They
become mode-less (``mode_less_reason``, the state ``border`` and
``spline_offset`` already use), and ``catalogue.path_classification_conflicts``
gains a check for a declared mode with no ``signal``-classified
``consumed_paths`` entry -- the state the pre-item ``intensity_reference_delta``
declaration was already in for mode 16, invisible to every existing check.

Covers Acceptance Criteria AC1-AC8, one test each, plus the one named
adversarial case from the Testing Strategy: ``empty-classification-reported-
once``.
"""

from __future__ import annotations

import dataclasses

import segfacet.catalogue as catalogue_module
import segfacet.failure_modes as failure_modes_module
import segfacet.heuristics.rule as rule_mod
import segfacet.traceability as traceability
from segfacet.heuristics.rule import declaration_for


# =========================================================================== #
# AC1: reference_delta is mode-less
# =========================================================================== #


def test_ac1_reference_delta_is_mode_less():
    decl = declaration_for("reference_delta")
    assert decl is not None
    assert decl.mode_less_reason != ""


# =========================================================================== #
# AC2: intensity_reference_delta is mode-less
# =========================================================================== #


def test_ac2_intensity_reference_delta_is_mode_less():
    decl = declaration_for("intensity_reference_delta")
    assert decl is not None
    assert decl.mode_less_reason != ""


# =========================================================================== #
# AC3: no specification edge names either rule
# =========================================================================== #


def test_ac3_no_specification_edge_names_either_rule():
    named_rule_ids = {
        edge.rule_id
        for mode in failure_modes_module.SPECIFICATION.values()
        for edge in mode.intended_rules
    }
    assert named_rule_ids & {"reference_delta", "intensity_reference_delta"} == set()


# =========================================================================== #
# AC4: neither rule counts toward bar condition 4 for any mode
# =========================================================================== #


def test_ac4_neither_rule_counts_toward_bar_condition_4():
    cat = catalogue_module.build_catalogue(strict=True)
    checked = 0
    for mode_id in failure_modes_module.SPECIFICATION:
        conditions = traceability.bar_conditions(mode_id, catalogue=cat)
        condition_4 = next(c for c in conditions if c.number == 4)
        checked += 1
        for subject in condition_4.subjects:
            assert not subject.startswith("reference_delta/"), (mode_id, subject)
            assert not subject.startswith("intensity_reference_delta/"), (mode_id, subject)
    assert checked, "expected at least one specified mode to check bar condition 4 on"


# =========================================================================== #
# AC5: a mode claim with no signal path is reported
# =========================================================================== #


def test_ac5_mode_claim_with_no_signal_path_is_reported(monkeypatch):
    live_conflicts = catalogue_module.path_classification_conflicts()

    rule = rule_mod._RULES["intensity_reference_delta"]
    live_decl = rule.mode_declaration
    planted = dataclasses.replace(
        live_decl, modes=(16,), evidence=("planted",), mode_less_reason=""
    )
    monkeypatch.setattr(rule, "mode_declaration", planted)

    new_conflicts = set(catalogue_module.path_classification_conflicts()) - set(live_conflicts)
    assert len(new_conflicts) == 1, new_conflicts
    (message,) = new_conflicts
    assert "intensity_reference_delta" in message


# =========================================================================== #
# AC6: the live registry reports nothing
# =========================================================================== #


def test_ac6_live_registry_reports_nothing():
    assert catalogue_module.path_classification_conflicts() == ()


# =========================================================================== #
# AC7: the rule-exercise direction stays complete
# =========================================================================== #


def test_ac7_rule_exercise_direction_stays_complete():
    matrix = traceability.matrix_to_dict(traceability.build_matrix())
    assert matrix["directions"]["rule_exercise"]["holes"] == []


# =========================================================================== #
# AC8: every authored unexercised-rule reason is the reason the matrix
# reports
# =========================================================================== #


def test_ac8_authored_unexercised_rule_reasons_match_the_matrix():
    assert traceability.UNEXERCISED_RULE_REASONS, (
        "expected a non-empty authored unexercised-rule reason map"
    )
    matrix = traceability.matrix_to_dict(traceability.build_matrix())
    rules = matrix["exercise"]["rules"]
    for rule_id, reason in traceability.UNEXERCISED_RULE_REASONS.items():
        assert rules[rule_id]["reason"] == reason, (rule_id, rules[rule_id])


# =========================================================================== #
# Named adversarial case: empty-classification-reported-once
# =========================================================================== #


def test_adv_empty_classification_reported_once(monkeypatch):
    """The new check (AC5) must not double-report the empty-classification
    state the existing check already covers: with the planted declaration's
    ``consumed_paths`` also emptied, exactly one message declares a failure
    mode claim, and it is the empty-classification message, not the new
    check's.

    Emptying ``consumed_paths`` also makes
    ``catalogue.path_classification_conflicts()`` report every catalogue-
    attributed leaf path as uncovered (completeness messages, one per path).
    Those are expected and are not counted here: the property this case
    guards is that the two checks that decide whether a rule declares a mode
    do not both fire, not how many completeness messages accompany that.
    *(item 193, 2026-09-28)*"""
    live_conflicts = catalogue_module.path_classification_conflicts()

    rule = rule_mod._RULES["intensity_reference_delta"]
    live_decl = rule.mode_declaration
    planted = dataclasses.replace(
        live_decl,
        modes=(16,),
        evidence=("planted",),
        mode_less_reason="",
        consumed_paths=(),
    )
    monkeypatch.setattr(rule, "mode_declaration", planted)

    new_conflicts = set(catalogue_module.path_classification_conflicts()) - set(live_conflicts)
    mode_claims = [c for c in new_conflicts if "declares failure mode(s)" in c]
    assert len(mode_claims) == 1, mode_claims
    assert "classification is empty" in mode_claims[0]
    assert not any("is classified 'signal'" in c for c in new_conflicts)
