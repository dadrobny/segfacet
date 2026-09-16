"""Tests for item 156 -- the three unclosed conformance seams in the checks
that guard ``segfacet.failure_modes.SPECIFICATION``.

Covers Acceptance Criteria AC1-AC14:

- AC1: ``catalogue.rule_declaration_conflicts()``'s new declaration ->
  specification direction agrees with the specification's own edges on the
  shipped tree, computed live from both sides.
- AC2-AC6: the new direction fires under the queue's own perturbations
  (``reference_delta`` widened to ``(1, 2, 3, 4, 6, 8)`` and to the queue's
  ``(1, 2, 5)`` control, ``fragmentation`` widened to ``(1, 2, 4)`` to show
  the check is unconditional on corpus evidence, and ``bounds`` widened to an
  out-of-key-set mode to show that direction still reports exactly once).
- AC7-AC10: ``traceability.build_matrix()``'s
  ``corpus_designated_unregistered_rule_ids`` is derived from the two
  committed manifests (geometric ``expected_rule_ids`` + intensity
  ``expected_firing``), not from the AST scan.
- AC11/AC12: no production source or generated artifact asserts the retired
  "mode -> rule is complete, always" contract, and the phrase matcher that
  checks this actually detects each forbidden phrasing (case-insensitively,
  and across a line wrap) -- exercised against both planted positive hits and
  a planted negative control that must not match.
- AC13: every ``proposed`` mode is a mode -> rule hole.
- AC14: met by the existing, unmodified
  ``tests/test_149_conformance_report.py::test_ac20_fresh_matches_committed_byte_for_byte``
  (spec Testing Strategy); no new test duplicates that byte comparison here.

Adversarial / edge-case scenarios included: a rule declaring a known mode
*and* an unknown mode (only the unknown one is reported, and the mirrored
known one gets nothing new); ``rule_declaration_conflicts()`` is pure and
repeatable across two calls; a monkeypatch's ``.undo()`` restores the
baseline exactly; a stub rule declaring a ``proposed`` mode with no
``IntendedRule`` edge is reported by rule id and mode.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from pathlib import Path

import pytest

import segfacet.catalogue as catalogue_module
import segfacet.failure_modes as failure_modes_module
import segfacet.traceability as traceability
from segfacet.heuristics.rule import Rule, RuleModeDeclaration, _RULES, iter_rule_declarations, iter_rules, register_rule
from segfacet.synth import corpus as corpus_module
from segfacet.synth import intensity as intensity_module
from segfacet.synth import perturbation as perturbation_module

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_registry():
    """Snapshot/restore the rule registry (the house pattern, e.g.
    ``tests/test_136_rule_mode_declarations.py``), so a stub rule registered
    for the mode-13 adversarial test cannot leak into another test's
    clean-tree assertions."""
    snapshot = dict(_RULES)
    yield
    _RULES.clear()
    _RULES.update(snapshot)


@pytest.fixture(scope="module")
def raw_matrix():
    """One unpatched ``build_matrix()`` call, shared by AC7 and AC13 --
    ``build_matrix()`` builds the catalogue and runs every corpus case, so
    it is slow enough to be worth sharing (Testing Strategy)."""
    return traceability.build_matrix()


# =========================================================================== #
# AC1: declarations mirror the specification's edges on the shipped tree
# =========================================================================== #


def test_ac1_declarations_mirror_specification_edges_on_shipped_tree():
    known_modes = set(failure_modes_module.SPECIFICATION.keys())

    declared_pairs = set()
    for rule_id, decl in iter_rule_declarations():
        if decl is None:
            continue
        for mode in decl.modes:
            if mode in known_modes:
                declared_pairs.add((rule_id, mode))

    spec_pairs = set()
    for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items():
        for edge in mode_spec.intended_rules:
            spec_pairs.add((edge.rule_id, mode_id))

    only_declared = sorted(declared_pairs - spec_pairs)
    only_spec = sorted(spec_pairs - declared_pairs)
    assert declared_pairs == spec_pairs, (
        f"declared but not in specification: {only_declared}; "
        f"in specification but not declared: {only_spec}"
    )


# =========================================================================== #
# AC2-AC6: the new declaration -> specification direction
# =========================================================================== #


def test_ac2_unmirrored_declaration_on_specified_mode_is_reported(monkeypatch):
    baseline = catalogue_module.rule_declaration_conflicts()

    rule = _RULES["reference_delta"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 2, 3, 4, 6, 8))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    new_messages = set(catalogue_module.rule_declaration_conflicts()) - set(baseline)
    assert len(new_messages) == 1, new_messages
    (message,) = new_messages
    assert "reference_delta" in message
    assert re.search(r"\b6\b", message), message


def test_ac3_queue_control_1_2_5_is_reported(monkeypatch):
    rule = _RULES["reference_delta"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 2, 5))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    messages = catalogue_module.rule_declaration_conflicts()
    assert any(
        "reference_delta" in msg and re.search(r"\b5\b", msg) for msg in messages
    ), messages


def test_ac4_check_is_unconditional_on_corpus_evidence(monkeypatch):
    rule = _RULES["fragmentation"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 2, 4))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    messages = catalogue_module.rule_declaration_conflicts()
    assert any(
        "fragmentation" in msg and re.search(r"\b2\b", msg) for msg in messages
    ), messages


def test_ac5_new_message_is_not_read_as_a_rule_to_mode_hole(monkeypatch):
    rule = _RULES["reference_delta"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 2, 3, 4, 6, 8))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    matrix = traceability.build_matrix()
    assert matrix.rule_to_mode.holes == ()


def test_ac6_mode_outside_key_set_reported_exactly_once(monkeypatch):
    rule = _RULES["bounds"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(999,))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    matching = [
        msg
        for msg in catalogue_module.rule_declaration_conflicts()
        if "bounds" in msg and re.search(r"\b999\b", msg)
    ]
    assert len(matching) == 1, matching


# =========================================================================== #
# AC7-AC10: corpus_designated_unregistered_rule_ids is read from both
# committed manifests, not the AST scan
# =========================================================================== #


def test_ac7_shipped_tree_designates_no_unregistered_rule(raw_matrix):
    registered_ids = {r.rule_id for r in iter_rules()}

    geometric_ids = set()
    geometric_cases = corpus_module.load_manifest().get("cases", [])
    assert geometric_cases, "fixture assumption: the geometric manifest has cases"
    for case in geometric_cases:
        geometric_ids.update(case.get("expected_rule_ids", []))

    intensity_ids = set()
    intensity_cases = intensity_module.load_intensity_manifest().get("cases", [])
    assert intensity_cases, "fixture assumption: the intensity manifest has cases"
    for case in intensity_cases:
        intensity_ids.update(case.get("expected_firing", []))

    expected = tuple(sorted((geometric_ids | intensity_ids) - registered_ids))
    assert raw_matrix.corpus_designated_unregistered_rule_ids == expected


def test_ac8_intensity_case_naming_unregistered_rule_is_reported(monkeypatch):
    real_manifest = intensity_module.load_intensity_manifest()
    patched = copy.deepcopy(real_manifest)

    target = None
    for case in patched.get("cases", []):
        if case.get("case_id") == "implausible_metal":
            target = case
            break
    assert target is not None, (
        "fixture assumption: the intensity manifest has an 'implausible_metal' case"
    )
    target["expected_firing"].append("__item156_unregistered__")

    monkeypatch.setattr(intensity_module, "load_intensity_manifest", lambda *a, **k: patched)

    matrix = traceability.build_matrix()
    assert "__item156_unregistered__" in matrix.corpus_designated_unregistered_rule_ids


def test_ac9_geometric_case_naming_unregistered_rule_is_reported(monkeypatch):
    real_manifest = corpus_module.load_manifest()
    patched = copy.deepcopy(real_manifest)

    target = None
    for case in patched.get("cases", []):
        if perturbation_module.corpus_case_kind(case) == perturbation_module.CASE_KIND_FAILURE:
            target = case
            break
    assert target is not None, (
        "fixture assumption: the geometric manifest has at least one failure case"
    )
    target["expected_rule_ids"].append("__item156_unregistered__")

    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: patched)

    matrix = traceability.build_matrix()
    assert "__item156_unregistered__" in matrix.corpus_designated_unregistered_rule_ids


def test_ac10_matrix_field_is_not_derived_from_the_ast_scan(monkeypatch):
    real_map = catalogue_module.scan_synth_rule_mode_map()

    def _patched():
        mapping = dict(real_map)
        mapping["__item156_scan_only__"] = (6,)
        return mapping

    monkeypatch.setattr(catalogue_module, "scan_synth_rule_mode_map", _patched)
    monkeypatch.setattr(catalogue_module, "_scan_synth_rule_mode_map", _patched)

    matrix = traceability.build_matrix()
    assert "__item156_scan_only__" not in matrix.corpus_designated_unregistered_rule_ids


# =========================================================================== #
# AC11/AC12: the retired "complete, always" contract, and its phrase matcher
# =========================================================================== #

_FORBIDDEN = ("complete, always", "complete-always", "always complete", "yes, always")


def _complete_always_hits(text: str) -> list:
    """A4's phrase matcher: case-insensitive, with every run of whitespace
    (including newlines and indentation) collapsed to one space first."""
    normalised = re.sub(r"\s+", " ", text.lower())
    return [phrase for phrase in _FORBIDDEN if phrase in normalised]


def test_ac11_no_complete_always_phrasing_in_source_or_generated_artifacts():
    py_files = sorted((_REPO_ROOT / "src" / "segfacet").rglob("*.py"))
    generated_files = sorted((_REPO_ROOT / "docs" / "aide").glob("*.generated.*"))

    # An empty walk must not pass vacuously.
    assert py_files, "expected at least one *.py file under src/segfacet"
    assert generated_files, "expected at least one docs/aide/*.generated.* file"

    offenders = []
    for path in py_files + generated_files:
        text = path.read_text(encoding="utf-8")
        hits = _complete_always_hits(text)
        if hits:
            offenders.append((path.relative_to(_REPO_ROOT).as_posix(), hits))

    assert offenders == [], offenders


@pytest.mark.parametrize("phrase", _FORBIDDEN)
def test_ac12_matcher_detects_each_forbidden_phrase(phrase):
    hits = _complete_always_hits(f"prose before {phrase} prose after")
    assert phrase in hits, hits


@pytest.mark.parametrize("phrase", _FORBIDDEN)
def test_ac12_matcher_detects_upper_case_variant(phrase):
    hits = _complete_always_hits(phrase.upper())
    assert phrase in hits, hits


def test_ac12_matcher_detects_phrase_split_across_a_line_break():
    hits = _complete_always_hits("complete,\n    always")
    assert "complete, always" in hits, hits


def test_ac12_matcher_negative_control_similar_but_not_forbidden_wording():
    """Planted negative control: prose that uses the individual words but
    never the forbidden run, and must not trip the matcher -- otherwise AC11
    would be pinning something other than the contract it names."""
    benign = (
        "Both directions are scored. A proposed mode is a legitimate hole, "
        "not complete, and it is never always true that mode-to-rule holds."
    )
    assert _complete_always_hits(benign) == []


# =========================================================================== #
# AC13: every proposed mode is a mode -> rule hole
# =========================================================================== #


def test_ac13_every_proposed_mode_is_a_mode_to_rule_hole(raw_matrix):
    proposed_modes = [
        mode_id
        for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items()
        if failure_modes_module.derive_status(mode_spec) == "proposed"
    ]
    assert proposed_modes, "fixture assumption: at least one proposed mode exists"

    for mode_id in proposed_modes:
        assert str(mode_id) in raw_matrix.mode_to_rule.holes, (mode_id, raw_matrix.mode_to_rule.holes)


# =========================================================================== #
# Adversarial / edge cases
# =========================================================================== #


def test_adv_known_and_unknown_mode_only_the_unknown_one_is_reported(monkeypatch):
    """``bounds`` already declares (and mirrors) mode 1. Widening it to
    ``(1, 999)`` must add only the "outside the key set" message for 999 --
    mode 1 is already mirrored, so it must gain nothing new."""
    baseline = catalogue_module.rule_declaration_conflicts()

    rule = _RULES["bounds"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 999))
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    new_messages = set(catalogue_module.rule_declaration_conflicts()) - set(baseline)
    assert len(new_messages) == 1, new_messages
    (message,) = new_messages
    assert "bounds" in message
    assert "outside" in message
    assert re.search(r"\b999\b", message), message
    assert not re.search(r"\b1\b", message), message


def test_adv_rule_declaration_conflicts_is_pure_and_repeatable():
    first = catalogue_module.rule_declaration_conflicts()
    second = catalogue_module.rule_declaration_conflicts()
    assert first == second


def test_adv_monkeypatch_undo_restores_the_baseline_exactly(monkeypatch):
    baseline = catalogue_module.rule_declaration_conflicts()

    rule = _RULES["reference_delta"]
    replacement = dataclasses.replace(rule.mode_declaration, modes=(1, 2, 3, 4, 6, 8))
    monkeypatch.setattr(rule, "mode_declaration", replacement)
    assert catalogue_module.rule_declaration_conflicts() != baseline

    monkeypatch.undo()
    assert catalogue_module.rule_declaration_conflicts() == baseline


def test_adv_stub_rule_declaring_a_proposed_mode_is_reported(isolated_registry):
    """A stub rule registered under ``isolated_registry`` declares mode 13
    (a ``proposed`` mode, per AC13, with no ``IntendedRule`` edge for any
    rule) -- the new direction must name the stub and the mode."""

    class _Item156StubRule(Rule):
        rule_id = "__item156_stub__"
        mode_declaration = RuleModeDeclaration(
            modes=(13,),
            evidence=("item156-adversarial-stub",),
        )

        def evaluate(self, record, config):
            return []

    register_rule(_Item156StubRule)

    messages = catalogue_module.rule_declaration_conflicts()
    assert any(
        "__item156_stub__" in msg and re.search(r"\b13\b", msg) for msg in messages
    ), messages
