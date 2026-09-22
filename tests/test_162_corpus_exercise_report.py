"""Tests for item 162 -- the per-rule and per-operator corpus-exercise
report (``segfacet.traceability`` gains an ``exercise`` block: every
registered rule is exercised by >=1 committed corpus case across both
manifests, or recorded unexercised with a reason derived from the signed-off
specification; every registered perturbation operator is used by >=1
``CASE_RECIPE`` entry, or recorded unused with a reason).

Covers Acceptance Criteria AC1-AC12 per the item spec's Testing Strategy: one
test per AC (several parametrised over the registered rules/operators),
building the matrix once through a module-scoped fixture and re-deriving
every asserted value in-session from the registry, the specification and
``CASE_RECIPE`` -- never a literal. Plus exactly the six adversarial cases the
Testing Strategy names: stub-rule-hole, stub-operator-hole,
recorded-unused-operator, demonstrable-rule-unexercised-is-a-hole,
intensity-corpus-is-read, frozen-and-uncached.

Field-name note (same discipline as ``test_149_conformance_report.py``): the
item spec pins the JSON's *content* precisely per-AC. This module reads
``payload["exercise"]["rules"]`` / ``["operators"]`` (each keyed by
rule_id/name), ``payload["directions"]["rule_exercise"]`` /
``["operator_exercise"]`` (``{complete, holes}``, the same shape the two
existing directions use), and per-record fields ``state``, ``exercised_by``,
``reason``, ``reason_modes`` (rules) / ``cases``, ``reason`` (operators).
"""

from __future__ import annotations

import dataclasses

import pytest


def _rule_records(payload: dict) -> dict:
    """Accept either a dict keyed by rule_id or a list of records, matching
    the container-shape leniency ``test_149``'s own helpers use."""
    rules = payload["exercise"]["rules"]
    if isinstance(rules, dict):
        return dict(rules)
    return {r["rule_id"]: r for r in rules}


def _operator_records(payload: dict) -> dict:
    operators = payload["exercise"]["operators"]
    if isinstance(operators, dict):
        return dict(operators)
    return {r["name"]: r for r in operators}


# =========================================================================== #
# build_matrix() fixtures -- one module-scoped unpatched pair, one
# function-scoped fixture per adversarial case.
# =========================================================================== #


@pytest.fixture(scope="module")
def raw_matrix():
    import segfacet.traceability as traceability

    return traceability.build_matrix()


@pytest.fixture(scope="module")
def matrix(raw_matrix):
    import segfacet.traceability as traceability

    return traceability.matrix_to_dict(raw_matrix)


#: A registered rule id that fires on no case and that no ``SPECIFICATION``
#: edge names -- the 2026-09-03 defect class this report exists to catch.
_STUB_HOLE_RULE_ID = "stub_hole_162"

#: A registered perturbation name that no ``CASE_RECIPE`` entry uses and
#: that carries no ``UNUSED_OPERATOR_REASONS`` entry.
_STUB_HOLE_PERTURBATION_NAME = "stub_hole_perturbation_162"


@pytest.fixture
def _isolated_rule_registry():
    from segfacet.heuristics.rule import Rule, _RULES, register_rule

    snapshot = dict(_RULES)
    try:
        yield Rule, register_rule
    finally:
        _RULES.clear()
        _RULES.update(snapshot)


@pytest.fixture
def _isolated_perturbation_registry():
    from segfacet.synth.perturbation import Perturbation, _PERTURBATIONS, register_perturbation

    snapshot = dict(_PERTURBATIONS)
    try:
        yield Perturbation, register_perturbation
    finally:
        _PERTURBATIONS.clear()
        _PERTURBATIONS.update(snapshot)


@pytest.fixture
def matrix_stub_rule_registered(_isolated_rule_registry):
    import segfacet.traceability as traceability

    Rule, register_rule = _isolated_rule_registry

    class _Stub(Rule):
        rule_id = _STUB_HOLE_RULE_ID

        def evaluate(self, record, config):
            return []

    register_rule(_Stub)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_stub_operator_registered(_isolated_perturbation_registry):
    import segfacet.traceability as traceability

    Perturbation, register_perturbation = _isolated_perturbation_registry

    class _Stub(Perturbation):
        name = _STUB_HOLE_PERTURBATION_NAME

        def apply(self, labelmap, seed):
            raise NotImplementedError

    register_perturbation(_Stub)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_recorded_unused_operator(_isolated_perturbation_registry, monkeypatch):
    import segfacet.traceability as traceability

    Perturbation, register_perturbation = _isolated_perturbation_registry

    class _Stub(Perturbation):
        name = _STUB_HOLE_PERTURBATION_NAME

        def apply(self, labelmap, seed):
            raise NotImplementedError

    register_perturbation(_Stub)
    monkeypatch.setattr(
        traceability,
        "UNUSED_OPERATOR_REASONS",
        {**traceability.UNUSED_OPERATOR_REASONS, _Stub.name: "kept for a mode with no fixture (test)"},
    )
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_demonstrable_rule_unexercised(monkeypatch):
    """``bounds`` is unexercised on the committed tree, named only at
    ``needs-real-data`` by modes 1-4. Patching mode 1's ``bounds`` edge alone
    to ``synthetic-demonstrable`` makes that the strongest rung across all of
    its edges -- and a ``synthetic-demonstrable``-only-derivable reason is,
    by the module's scope fence, no reason at all: a hole."""
    import dataclasses as dc

    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    original_map = failure_modes_module.SPECIFICATION
    mode1 = original_map[1]
    assert any(r.rule_id == "bounds" for r in mode1.intended_rules), mode1.intended_rules
    new_edges = tuple(
        dc.replace(edge, evidence_rung="synthetic-demonstrable") if edge.rule_id == "bounds" else edge
        for edge in mode1.intended_rules
    )
    assert new_edges != mode1.intended_rules, "fixture assumption violated"
    patched_map = dict(original_map)
    patched_map[1] = dc.replace(mode1, intended_rules=new_edges)
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_map)
    return traceability.matrix_to_dict(traceability.build_matrix())


@pytest.fixture
def matrix_intensity_corpus_not_read(monkeypatch):
    """Drop ``implausible_metal``, ``implausible_soft_tissue`` and
    ``degenerate_uniform`` from what the generator's intensity-manifest
    loader returns -- proving the rule direction reads the live intensity
    corpus rather than only ``tests/corpus/manifest.json``.

    Narrowing the loader alone collides with ``derive_status``'s pre-existing
    per-mode walk (``build_matrix`` -> ``derive_status`` -> ``_demonstrates``
    -> ``case_agrees`` -> ``measured_firing``): mode 16 declares exactly
    these three case ids as its own ``corpus_cases``, and
    ``measured_firing`` raises for a case id absent from the manifest it
    resolves against, rather than degrading. So the specification is
    narrowed the same way, everywhere it names one of the dropped ids -- a
    corpus without these cases is one whose specification would not declare
    them either. That narrowing is what ``_build_exercise`` (the module
    under test) reads to explain an unexercised rule, never what flips
    ``intensity`` to unexercised in the first place -- that is the loader
    patch above, read by ``_build_conformance``'s per-case measured firing.
    """
    import dataclasses as dc

    import segfacet.failure_modes as failure_modes_module
    from segfacet.synth import intensity as intensity_module
    import segfacet.traceability as traceability

    original_manifest = intensity_module.load_intensity_manifest()
    dropped = {"implausible_metal", "implausible_soft_tissue", "degenerate_uniform"}
    remaining_cases = [c for c in original_manifest["cases"] if c["case_id"] not in dropped]
    assert len(remaining_cases) == len(original_manifest["cases"]) - len(dropped)
    narrowed_manifest = {**original_manifest, "cases": remaining_cases}

    monkeypatch.setattr(intensity_module, "load_intensity_manifest", lambda *a, **k: narrowed_manifest)

    original_spec = failure_modes_module.SPECIFICATION
    patched_spec = dict(original_spec)
    narrowed_mode_ids = []
    for mode_id, mode_spec in original_spec.items():
        kept_cases = tuple(c for c in mode_spec.corpus_cases if c.case_id not in dropped)
        if kept_cases != mode_spec.corpus_cases:
            patched_spec[mode_id] = dc.replace(mode_spec, corpus_cases=kept_cases)
            narrowed_mode_ids.append(mode_id)
    # Only mode 16 declares any of the three dropped (intensity-only) case
    # ids -- if a future specification edit adds a second, this fixture's
    # assumption needs re-checking rather than silently narrowing it too.
    assert narrowed_mode_ids == [16], narrowed_mode_ids
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_spec)

    return traceability.matrix_to_dict(traceability.build_matrix())


# =========================================================================== #
# AC1: one exercise record per registered rule
# =========================================================================== #


def test_ac1_one_exercise_record_per_registered_rule(matrix):
    from segfacet.heuristics import iter_rules

    expected = sorted(rule.rule_id for rule in iter_rules())
    actual = sorted(_rule_records(matrix).keys())
    assert actual == expected, (actual, expected)


# =========================================================================== #
# AC2: one exercise record per registered operator
# =========================================================================== #


def test_ac2_one_exercise_record_per_registered_operator(matrix):
    from segfacet.synth.perturbation import perturbation_names

    expected = sorted(perturbation_names())
    actual = sorted(_operator_records(matrix).keys())
    assert actual == expected, (actual, expected)


# =========================================================================== #
# AC3: a rule's exercising cases are re-derived from the measured firing of
# both corpora
# =========================================================================== #


def test_ac3_rule_exercised_by_matches_measured_firing_across_both_corpora(raw_matrix, matrix):
    from segfacet.heuristics import iter_rules

    pairs_by_rule: dict = {}
    for case in raw_matrix.conformance.cases:
        for rule_id in case.measured_firing:
            pairs_by_rule.setdefault(rule_id, []).append((case.corpus, case.case_id))

    records = _rule_records(matrix)
    for rule in iter_rules():
        expected = sorted(pairs_by_rule.get(rule.rule_id, []))
        actual = sorted(tuple(pair) for pair in records[rule.rule_id]["exercised_by"])
        assert actual == expected, (rule.rule_id, actual, expected)


# =========================================================================== #
# AC4: a rule record is exercised or reasoned, never both and never neither
# =========================================================================== #


def test_ac4_rule_record_is_exercised_or_reasoned_never_both_never_neither(matrix):
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics import iter_rules

    allowed_reasons = tuple(
        r for r in failure_modes_module.EVIDENCE_RUNGS if r != "synthetic-demonstrable"
    )
    records = _rule_records(matrix)
    for rule in iter_rules():
        record = records[rule.rule_id]
        assert record["state"] in ("exercised", "unexercised"), record
        if record["state"] == "exercised":
            assert record["exercised_by"], record
            assert record["reason"] == "", record
        else:
            assert record["exercised_by"] == [], record
            assert record["reason"] == "" or record["reason"] in allowed_reasons, record


# =========================================================================== #
# AC5: an unexercised rule's reason is the strongest specification rung
# naming it, and its reason_modes are the modes that named it
# =========================================================================== #


def test_ac5_unexercised_reason_and_reason_modes_derived_from_specification(matrix):
    import segfacet.failure_modes as failure_modes_module

    specification = failure_modes_module.SPECIFICATION
    strength = {rung: idx for idx, rung in enumerate(failure_modes_module.EVIDENCE_RUNGS)}

    records = _rule_records(matrix)
    for rule_id, record in records.items():
        if record["state"] != "unexercised":
            continue
        edges = []
        for mode_id, mode_spec in specification.items():
            for edge in mode_spec.intended_rules:
                if edge.rule_id == rule_id:
                    edges.append((mode_id, edge.evidence_rung))
        if not edges:
            assert record["reason"] == "", record
            assert record["reason_modes"] == [], record
            continue
        rungs = [rung for _mode_id, rung in edges]
        strongest = min(rungs, key=strength.__getitem__)
        expected_reason_modes = sorted({mode_id for mode_id, _rung in edges})
        if strongest == "synthetic-demonstrable":
            assert record["reason"] == "", (rule_id, record)
        else:
            assert record["reason"] == strongest, (rule_id, record, strongest)
            assert sorted(record["reason_modes"]) == expected_reason_modes, (rule_id, record)


# =========================================================================== #
# AC6: the rule direction is complete exactly when no registered rule is
# both unexercised and unreasoned
# =========================================================================== #


def test_ac6_rule_direction_complete_iff_no_rule_unexercised_and_unreasoned(matrix):
    records = _rule_records(matrix)
    expected_holes = sorted(
        rule_id
        for rule_id, record in records.items()
        if record["state"] == "unexercised" and record["reason"] == ""
    )
    direction = matrix["directions"]["rule_exercise"]
    assert sorted(direction["holes"]) == expected_holes, direction
    assert direction["complete"] == (not expected_holes), direction


# =========================================================================== #
# AC7: an operator's cases are re-derived from CASE_RECIPE
# =========================================================================== #


def test_ac7_operator_cases_match_case_recipe(matrix):
    from segfacet.synth.corpus import CASE_RECIPE
    from segfacet.synth.perturbation import perturbation_names

    records = _operator_records(matrix)
    for name in perturbation_names():
        expected = sorted(entry.case_id for entry in CASE_RECIPE if entry.perturbation == name)
        actual = sorted(records[name]["cases"])
        assert actual == expected, (name, actual, expected)


# =========================================================================== #
# AC8: an operator record is used or reasoned, and the operator direction
# reports its holes
# =========================================================================== #


def test_ac8_operator_record_used_or_reasoned_and_direction_reports_holes(matrix):
    from segfacet.synth.perturbation import perturbation_names

    records = _operator_records(matrix)
    for name in perturbation_names():
        record = records[name]
        assert record["state"] in ("used", "unused"), record
        if record["state"] == "used":
            assert record["cases"], record
            assert record["reason"] == "", record
        else:
            assert record["cases"] == [], record

    expected_holes = sorted(
        name
        for name, record in records.items()
        if record["state"] == "unused" and record["reason"] == ""
    )
    direction = matrix["directions"]["operator_exercise"]
    assert sorted(direction["holes"]) == expected_holes, direction
    assert direction["complete"] == (not expected_holes), direction


# =========================================================================== #
# AC9: the committed JSON is byte-identical to a fresh build
# =========================================================================== #


def test_ac9_committed_json_byte_identical_to_fresh_build():
    import json

    import segfacet.traceability as traceability

    fresh_bytes = (
        json.dumps(
            traceability.matrix_to_dict(traceability.build_matrix()),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    committed_bytes = traceability.JSON_PATH.read_bytes()
    assert committed_bytes, "expected a non-empty committed JSON artifact"
    assert committed_bytes == fresh_bytes


# =========================================================================== #
# AC10: the committed Markdown is byte-identical to a fresh render
# =========================================================================== #


def test_ac10_committed_markdown_byte_identical_to_fresh_render():
    import segfacet.traceability as traceability

    fresh_bytes = traceability.render_markdown(traceability.build_matrix()).encode("utf-8")
    committed_bytes = traceability.MD_PATH.read_bytes()
    assert committed_bytes, "expected a non-empty committed markdown artifact"
    assert committed_bytes == fresh_bytes


# =========================================================================== #
# AC11: the Markdown carries every exercise record
# =========================================================================== #


def test_ac11_markdown_carries_every_exercise_record(matrix):
    import segfacet.traceability as traceability

    md_text = traceability.MD_PATH.read_text(encoding="utf-8")
    rule_section_start = md_text.index("## Rule corpus exercise")
    operator_section_start = md_text.index("## Operator corpus exercise")
    rule_section = md_text[rule_section_start:operator_section_start]
    operator_section = md_text[operator_section_start:]

    for rule_id, record in _rule_records(matrix).items():
        rows = [line for line in rule_section.splitlines() if line.startswith("|")]
        matching = [line for line in rows if line.strip("|").split("|")[0].strip() == rule_id]
        assert matching, (rule_id, "no row found in rule exercise section")
        row = matching[0]
        state_cell = [c.strip() for c in row.split("|")][2]
        assert state_cell == record["state"], (rule_id, row)
        if record["state"] == "exercised":
            for corpus, case_id in record["exercised_by"]:
                assert f"{corpus}/{case_id}" in row, (rule_id, corpus, case_id, row)
        elif record["reason"]:
            assert record["reason"] in row, (rule_id, row)

    for name, record in _operator_records(matrix).items():
        rows = [line for line in operator_section.splitlines() if line.startswith("|")]
        matching = [line for line in rows if line.strip("|").split("|")[0].strip() == name]
        assert matching, (name, "no row found in operator exercise section")
        row = matching[0]
        state_cell = [c.strip() for c in row.split("|")][2]
        assert state_cell == record["state"], (name, row)
        if record["state"] == "used":
            for case_id in record["cases"]:
                assert case_id in row, (name, case_id, row)
        elif record["reason"]:
            assert record["reason"] in row, (name, row)


# =========================================================================== #
# AC12: the exercise sections render after the rule-declaration table
# =========================================================================== #


def test_ac12_exercise_sections_render_after_rule_declaration_table(matrix):
    import segfacet.traceability as traceability
    from segfacet.heuristics import iter_rules

    md_text = traceability.MD_PATH.read_text(encoding="utf-8")
    rules_to_modes_idx = md_text.index("## Rules -> failure modes")
    rule_exercise_idx = md_text.index("## Rule corpus exercise")
    operator_exercise_idx = md_text.index("## Operator corpus exercise")

    assert rules_to_modes_idx < rule_exercise_idx < operator_exercise_idx

    for rule in iter_rules():
        rule_id = rule.rule_id
        first_row_index = None
        for line in md_text.splitlines(keepends=False):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] == rule_id:
                first_row_index = md_text.index(line)
                break
        assert first_row_index is not None, rule_id
        assert rules_to_modes_idx < first_row_index < rule_exercise_idx, (
            rule_id,
            "the first row naming this rule must be its declaration row, "
            "which stays ahead of the exercise sections",
        )


# =========================================================================== #
# Named adversarial case: stub-rule-hole
# =========================================================================== #


def test_stub_rule_hole(matrix_stub_rule_registered):
    records = _rule_records(matrix_stub_rule_registered)
    record = records[_STUB_HOLE_RULE_ID]
    assert record["state"] == "unexercised", record
    assert record["exercised_by"] == [], record
    assert record["reason"] == "", record

    direction = matrix_stub_rule_registered["directions"]["rule_exercise"]
    assert direction["complete"] is False, direction
    assert _STUB_HOLE_RULE_ID in direction["holes"], direction


# =========================================================================== #
# Named adversarial case: stub-operator-hole
# =========================================================================== #


def test_stub_operator_hole(matrix_stub_operator_registered):
    records = _operator_records(matrix_stub_operator_registered)
    record = records[_STUB_HOLE_PERTURBATION_NAME]
    assert record["state"] == "unused", record
    assert record["cases"] == [], record
    assert record["reason"] == "", record

    direction = matrix_stub_operator_registered["directions"]["operator_exercise"]
    assert direction["complete"] is False, direction
    assert _STUB_HOLE_PERTURBATION_NAME in direction["holes"], direction


# =========================================================================== #
# Named adversarial case: recorded-unused-operator
# =========================================================================== #


def test_recorded_unused_operator(matrix_recorded_unused_operator):
    records = _operator_records(matrix_recorded_unused_operator)
    record = records[_STUB_HOLE_PERTURBATION_NAME]
    assert record["state"] == "unused", record
    assert record["cases"] == [], record
    assert record["reason"] == "kept for a mode with no fixture (test)", record

    direction = matrix_recorded_unused_operator["directions"]["operator_exercise"]
    assert _STUB_HOLE_PERTURBATION_NAME not in direction["holes"], direction
    assert direction["complete"] is True, direction


# =========================================================================== #
# Named adversarial case: demonstrable-rule-unexercised-is-a-hole
# =========================================================================== #


def test_demonstrable_rule_unexercised_is_a_hole(matrix_demonstrable_rule_unexercised):
    records = _rule_records(matrix_demonstrable_rule_unexercised)
    record = records["bounds"]
    assert record["state"] == "unexercised", record
    assert record["reason"] == "", record
    assert record["reason_modes"] == [], record

    direction = matrix_demonstrable_rule_unexercised["directions"]["rule_exercise"]
    assert direction["complete"] is False, direction
    assert "bounds" in direction["holes"], direction


# =========================================================================== #
# Named adversarial case: intensity-corpus-is-read
# =========================================================================== #


def test_intensity_corpus_is_read(matrix, matrix_intensity_corpus_not_read):
    before = _rule_records(matrix)["intensity"]
    after = _rule_records(matrix_intensity_corpus_not_read)["intensity"]

    assert before["state"] == "exercised", before
    assert after["state"] == "unexercised", after
    assert after["exercised_by"] == [], after


# =========================================================================== #
# Named adversarial case: frozen-and-uncached
# =========================================================================== #


def test_frozen_and_uncached(raw_matrix):
    import segfacet.traceability as traceability

    matrix_two = traceability.build_matrix()
    d1 = traceability.matrix_to_dict(raw_matrix)
    d2 = traceability.matrix_to_dict(matrix_two)
    assert d1["exercise"] == d2["exercise"], (d1["exercise"], d2["exercise"])
    assert d1["directions"]["rule_exercise"] == d2["directions"]["rule_exercise"]
    assert d1["directions"]["operator_exercise"] == d2["directions"]["operator_exercise"]

    a_rule_record = raw_matrix.exercise.rules[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        a_rule_record.state = "used"  # type: ignore[misc]
    an_operator_record = raw_matrix.exercise.operators[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        an_operator_record.state = "unused"  # type: ignore[misc]

    d1["exercise"] = "deliberately corrupted by this test"
    d3 = traceability.matrix_to_dict(raw_matrix)
    assert d3["exercise"] != "deliberately corrupted by this test"
