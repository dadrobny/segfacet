"""Tests for item 164 -- first-class detector ids on rules and in the
failure-mode specification (``RuleDetector`` on ``RuleModeDeclaration``,
``Finding.detector_id``, ``IntendedRule.detector_ids``,
``segfacet.failure_modes.modes_for_detector``, and the two new
``segfacet.traceability`` directions ``edge_to_detector`` /
``detector_to_edge``).

Covers Acceptance Criteria AC1-AC14 per the item spec's Testing Strategy:
one test per AC (several iterating live registry/specification state per
AC1/AC4/AC5/AC6/AC10, two ``pytest.raises`` constructions per AC2/AC3,
single tests for AC7-AC9 and AC11-AC14), plus exactly the three named
adversarial cases: ``detector-id-collides-across-rules``,
``empty-detector-ids-on-an-edge-is-a-hole`` and
``mode-less-reason-is-what-excuses-a-detector``.

Shape (A7, A3 of item 163's precedent): one module-scoped ``build_matrix()``
fixture (``raw_matrix``) and one module-scoped fixture that collects every
``(corpus, case_id, Finding)`` triple across both committed manifests exactly
once (``all_corpus_findings``, AC10), through the same
``segfacet.synth.regression`` entry points
(``pipeline_findings``/``reconstructed_findings``/
``intensity_pipeline_findings``) that ``failure_modes.measured_firing``
itself dispatches to -- so the path AC10 proves is the one the specificity
ratchet measures, and no test body drives a case a second time. AC13, AC14
and the three named adversarial cases each perturb live state inside a
snapshot-and-restore, function-scoped fixture (item 162's
``_isolated_rule_registry`` idiom for a rule's ``mode_declaration``, item
149's patched-``SPECIFICATION`` idiom for the edges) and read the resulting
directions from a fresh ``build_matrix()`` built *inside* that fixture --
never inside a test body.

AC7 convention note: the item spec states the ``edge_to_detector`` holes are
``(mode_id, rule_id, detector_id)`` triples "for which detector_id is not
declared ... (or for which detector_ids is empty)". For a normal undeclared
id the triple's third element is that id (AC13's own wording is explicit
about this). For an edge whose ``detector_ids`` is empty there is no id to
name; this module recomputes that case's triple with ``""`` as the third
element -- the natural sentinel, and the one this module's own AC7 test
therefore requires of the implementation. The
``empty-detector-ids-on-an-edge-is-a-hole`` adversarial case deliberately
does *not* depend on that convention: it asserts only that a hole naming the
patched mode/rule appears, which holds regardless of the third element's
exact representation.
"""

from __future__ import annotations

import dataclasses as dc

import pytest


# =========================================================================== #
# build_matrix() fixture -- the one unpatched call site (A7/A3).
# =========================================================================== #


@pytest.fixture(scope="module")
def raw_matrix():
    import segfacet.traceability as traceability

    return traceability.build_matrix()


@pytest.fixture(scope="module")
def all_corpus_findings():
    """Every ``(corpus, case_id, Finding)`` triple across both committed
    manifests, driven exactly once (AC10, A7) through the same entry points
    ``failure_modes.measured_firing`` dispatches to."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth import intensity as intensity_module
    from segfacet.synth.regression import (
        intensity_pipeline_findings,
        pipeline_findings,
        reconstructed_findings,
    )

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

    for case in intensity_module.load_intensity_manifest().get("cases", []):
        detection = case.get("detection")
        if detection != "intensity_pipeline":
            raise AssertionError(
                f"intensity case {case.get('case_id')!r}: unrecognised detection {detection!r}"
            )
        for finding in intensity_pipeline_findings(case):
            triples.append(("intensity", case["case_id"], finding))

    return triples


# =========================================================================== #
# AC1: every registered rule declares at least one detector.
# =========================================================================== #


def test_ac1_every_registered_rule_declares_at_least_one_detector():
    from segfacet.heuristics.rule import iter_rules

    rules = list(iter_rules())
    assert rules, "expected at least one registered rule"

    all_ids = {rule.rule_id for rule in rules}
    with_detectors = {
        rule.rule_id
        for rule in rules
        if rule.mode_declaration is not None and rule.mode_declaration.detectors
    }
    assert with_detectors == all_ids


# =========================================================================== #
# AC2: a declaration rejects a malformed or duplicated detector id.
# =========================================================================== #


@pytest.mark.parametrize(
    "detector_ids",
    [
        pytest.param(("",), id="empty-id"),
        pytest.param(("Bad-ID",), id="invalid-pattern"),
        pytest.param(("dup", "dup"), id="duplicate-id"),
        pytest.param(("b", "a"), id="out-of-order"),
    ],
)
def test_ac2_rejects_malformed_or_duplicated_detector_id(detector_ids):
    from segfacet.heuristics.rule import RuleDetector, RuleModeDeclaration

    detectors = tuple(
        RuleDetector(detector_id=detector_id, description="test-only detector")
        for detector_id in detector_ids
    )
    with pytest.raises(ValueError) as exc_info:
        RuleModeDeclaration(mode_less_reason="test-only", detectors=detectors)
    message = str(exc_info.value)
    assert "'detectors'" in message
    offending = detector_ids[-1]
    assert offending in message


# =========================================================================== #
# AC3: a declaration rejects a signal_paths element the same declaration
# does not classify signal.
# =========================================================================== #


def test_ac3_rejects_signal_path_not_classified_signal_in_same_declaration():
    from segfacet.heuristics.rule import ConsumedPath, RuleDetector, RuleModeDeclaration

    offending_path = "per_label.{label}.geometry.extent_x_mm"
    consumed = (ConsumedPath(path=offending_path, role="bookkeeping", reason="test-only"),)
    detector = RuleDetector(
        detector_id="probe",
        description="test-only detector",
        signal_paths=(offending_path,),
    )
    with pytest.raises(ValueError) as exc_info:
        RuleModeDeclaration(
            modes=(1,),
            evidence=("test-only",),
            consumed_paths=consumed,
            detectors=(detector,),
        )
    message = str(exc_info.value)
    assert "probe" in message
    assert offending_path in message


# =========================================================================== #
# AC4: every signal path of a rule is claimed by at least one of its
# detectors.
# =========================================================================== #


def test_ac4_signal_paths_equal_union_of_detector_signal_paths():
    from segfacet.heuristics.rule import iter_rules

    rules = list(iter_rules())
    assert rules, "expected at least one registered rule"

    saw_nonempty_signal_set = False
    for rule in rules:
        decl = rule.mode_declaration
        assert decl is not None, rule.rule_id
        signal_paths = {cp.path for cp in decl.consumed_paths if cp.role == "signal"}
        detector_union = set()
        for detector in decl.detectors:
            detector_union |= set(detector.signal_paths)
        assert detector_union == signal_paths, rule.rule_id
        if signal_paths:
            saw_nonempty_signal_set = True

    assert saw_nonempty_signal_set, "expected at least one rule with signal paths"


# =========================================================================== #
# AC5: every specification edge names only declared detector ids, and names
# at least one.
# =========================================================================== #


def test_ac5_every_edge_names_only_declared_and_nonempty_detector_ids():
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import iter_rules

    declared_by_rule = {
        rule.rule_id: {d.detector_id for d in (rule.mode_declaration.detectors if rule.mode_declaration else ())}
        for rule in iter_rules()
    }

    checked_any_edge = False
    for mode in failure_modes_module.SPECIFICATION.values():
        for edge in mode.intended_rules:
            checked_any_edge = True
            assert edge.detector_ids, (mode.id, edge.rule_id)
            declared = declared_by_rule.get(edge.rule_id, set())
            assert set(edge.detector_ids) <= declared, (mode.id, edge.rule_id, edge.detector_ids, declared)
    assert checked_any_edge, "expected at least one specification edge"


# =========================================================================== #
# AC6: a detector's modes are derived from the specification, not authored.
# =========================================================================== #


def test_ac6_modes_for_detector_recomputed_from_specification():
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import iter_rules

    checked_any_detector = False
    for rule in iter_rules():
        decl = rule.mode_declaration
        if decl is None:
            continue
        for detector in decl.detectors:
            checked_any_detector = True
            expected = tuple(
                sorted(
                    mode_id
                    for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items()
                    for edge in mode_spec.intended_rules
                    if edge.rule_id == rule.rule_id and detector.detector_id in edge.detector_ids
                )
            )
            actual = failure_modes_module.modes_for_detector(rule.rule_id, detector.detector_id)
            assert actual == expected, (rule.rule_id, detector.detector_id, actual, expected)

    assert checked_any_detector, "expected at least one declared detector"


# =========================================================================== #
# AC7: the edge -> detector direction's holes are exactly the edges naming
# an undeclared id (or an empty detector_ids tuple).
# =========================================================================== #


def test_ac7_edge_to_detector_holes_match_recomputation(raw_matrix):
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import iter_rules

    declared_by_rule = {
        rule.rule_id: {d.detector_id for d in (rule.mode_declaration.detectors if rule.mode_declaration else ())}
        for rule in iter_rules()
    }

    expected_holes = []
    for mode_id, mode_spec in failure_modes_module.SPECIFICATION.items():
        for edge in mode_spec.intended_rules:
            declared = declared_by_rule.get(edge.rule_id, set())
            if not edge.detector_ids:
                expected_holes.append((mode_id, edge.rule_id, ""))
                continue
            for detector_id in edge.detector_ids:
                if detector_id not in declared:
                    expected_holes.append((mode_id, edge.rule_id, detector_id))
    expected_holes = tuple(sorted(expected_holes))

    direction = raw_matrix.edge_to_detector
    assert direction.holes == expected_holes
    assert direction.complete == (not expected_holes)


# =========================================================================== #
# AC8: the detector -> edge direction's holes are exactly the declared
# detectors no edge names and no mode_less_reason excuses.
# =========================================================================== #


def test_ac8_detector_to_edge_holes_match_recomputation(raw_matrix):
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import iter_rules

    named_by_edge = set()
    for mode_spec in failure_modes_module.SPECIFICATION.values():
        for edge in mode_spec.intended_rules:
            for detector_id in edge.detector_ids:
                named_by_edge.add((edge.rule_id, detector_id))

    expected_holes = []
    for rule in iter_rules():
        decl = rule.mode_declaration
        if decl is None:
            continue
        for detector in decl.detectors:
            if detector.mode_less_reason:
                continue
            if (rule.rule_id, detector.detector_id) not in named_by_edge:
                expected_holes.append((rule.rule_id, detector.detector_id))
    expected_holes = tuple(sorted(expected_holes))

    direction = raw_matrix.detector_to_edge
    assert direction.holes == expected_holes
    assert direction.complete == (not expected_holes)
    # Non-vacuous on this tree (item spec: three detectors carry a
    # mode_less_reason and are excluded by it rather than by having no edge).
    assert any(
        detector.mode_less_reason
        for rule in iter_rules()
        if rule.mode_declaration is not None
        for detector in rule.mode_declaration.detectors
    )


# =========================================================================== #
# AC9: both new directions reach the committed matrix artifact.
# =========================================================================== #


def test_ac9_committed_matrix_carries_both_new_directions(raw_matrix):
    import json
    from pathlib import Path

    import segfacet.traceability as traceability

    repo_root = Path(__file__).resolve().parent.parent
    committed_path = repo_root / "docs" / "aide" / "traceability_matrix.generated.json"
    payload = json.loads(committed_path.read_text(encoding="utf-8"))

    directions = payload["directions"]
    assert set(directions) == {
        "mode_to_rule",
        "rule_to_mode",
        "rule_exercise",
        "operator_exercise",
        "edge_to_detector",
        "detector_to_edge",
    }

    fresh_directions = traceability.matrix_to_dict(raw_matrix)["directions"]
    for key in ("edge_to_detector", "detector_to_edge"):
        assert directions[key]["complete"] == fresh_directions[key]["complete"], key
        assert directions[key]["holes"] == fresh_directions[key]["holes"], key


# =========================================================================== #
# AC10: every finding a committed corpus case produces carries a detector id
# its own rule declares.
# =========================================================================== #


def test_ac10_every_corpus_finding_detector_id_is_declared_by_its_rule(all_corpus_findings):
    from segfacet.heuristics.rule import iter_rules

    declared_by_rule = {
        rule.rule_id: {d.detector_id for d in (rule.mode_declaration.detectors if rule.mode_declaration else ())}
        for rule in iter_rules()
    }

    assert all_corpus_findings, "expected at least one finding across both committed manifests"
    for corpus, case_id, finding in all_corpus_findings:
        assert finding.detector_id, (corpus, case_id, finding.rule_id)
        assert finding.detector_id in declared_by_rule.get(finding.rule_id, set()), (
            corpus,
            case_id,
            finding.rule_id,
            finding.detector_id,
        )


# =========================================================================== #
# AC11: detector_id round-trips losslessly.
# =========================================================================== #


def test_ac11_detector_id_round_trips_losslessly():
    from segfacet.heuristics.finding import Finding
    from segfacet.verdict import Severity

    finding = Finding(rule_id="fragmentation", severity=Severity.FLAG, reason="x", detector_id="components")
    assert Finding.from_dict(finding.to_dict()) == finding

    d_no_key = {"rule_id": "fragmentation", "severity": "flagged-for-review", "reason": "x", "labels": []}
    assert "detector_id" not in d_no_key
    assert Finding.from_dict(d_no_key).detector_id == ""


# =========================================================================== #
# AC12: the report schema admits detector_id and requires nothing new.
# =========================================================================== #


def test_ac12_report_schema_finding_definition_admits_detector_id():
    from segfacet.report import _SCHEMA

    ref = _SCHEMA["properties"]["findings"]["items"]["$ref"]
    def_name = ref.rsplit("/", 1)[-1]
    finding_def = _SCHEMA["definitions"][def_name]

    assert finding_def["properties"]["detector_id"]["type"] == "string"
    assert finding_def["additionalProperties"] is False
    assert set(finding_def["required"]) == {"rule_id", "severity", "reason", "labels"}


# =========================================================================== #
# AC13: an edge naming an undeclared detector id is caught.
# =========================================================================== #


@pytest.fixture
def matrix_with_undeclared_edge_detector(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    original = failure_modes_module.SPECIFICATION
    mode_id, mode_spec = next((mid, ms) for mid, ms in original.items() if ms.intended_rules)
    edge0 = mode_spec.intended_rules[0]
    bogus_id = "zzz_undeclared_164"
    patched_edge = dc.replace(edge0, detector_ids=(bogus_id,))
    patched_mode = dc.replace(mode_spec, intended_rules=(patched_edge,) + mode_spec.intended_rules[1:])
    patched_spec = dict(original)
    patched_spec[mode_id] = patched_mode
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_spec)

    matrix = traceability.build_matrix()
    return matrix, mode_id, edge0.rule_id, bogus_id


def test_ac13_edge_naming_undeclared_detector_id_is_caught(matrix_with_undeclared_edge_detector):
    matrix, mode_id, rule_id, bogus_id = matrix_with_undeclared_edge_detector
    direction = matrix.edge_to_detector
    assert direction.complete is False
    assert direction.holes == ((mode_id, rule_id, bogus_id),)


# =========================================================================== #
# AC14: a declared detector no edge names is caught.
# =========================================================================== #


@pytest.fixture
def matrix_with_unwired_detector(monkeypatch):
    import segfacet.traceability as traceability
    from segfacet.heuristics.rule import RuleDetector, iter_rules

    target = next(rule for rule in iter_rules() if rule.mode_declaration is not None)
    new_id = "zzz_unwired_164"
    new_detector = RuleDetector(detector_id=new_id, description="test-only unwired detector")
    widened = tuple(
        sorted(target.mode_declaration.detectors + (new_detector,), key=lambda d: d.detector_id)
    )
    new_declaration = dc.replace(target.mode_declaration, detectors=widened)
    monkeypatch.setattr(target, "mode_declaration", new_declaration)

    matrix = traceability.build_matrix()
    return matrix, target.rule_id, new_id


def test_ac14_declared_detector_no_edge_names_is_caught(matrix_with_unwired_detector):
    matrix, rule_id, detector_id = matrix_with_unwired_detector
    direction = matrix.detector_to_edge
    assert direction.complete is False
    assert direction.holes == ((rule_id, detector_id),)


# =========================================================================== #
# Named adversarial case: detector-id-collides-across-rules
# =========================================================================== #


@pytest.fixture
def matrix_after_rename_and_colliding_edge(monkeypatch):
    """``reference_delta`` and ``intensity_reference_delta`` both declare
    ``out_of_range``. Rename ``intensity_reference_delta``'s own detector
    away, then add an edge naming ``intensity_reference_delta``/
    ``out_of_range`` -- an id that rule no longer declares, but that
    ``reference_delta`` still does. A join keyed on the bare slug (ignoring
    which rule declared it) would resolve this edge against
    ``reference_delta``'s declaration instead of reporting a hole; the
    per-rule join this item ships must not."""
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import iter_rules
    import segfacet.traceability as traceability

    declared_by_rule = {
        rule.rule_id: {d.detector_id for d in (rule.mode_declaration.detectors if rule.mode_declaration else ())}
        for rule in iter_rules()
    }
    assert "out_of_range" in declared_by_rule.get("reference_delta", set())
    assert "out_of_range" in declared_by_rule.get("intensity_reference_delta", set())

    target = next(rule for rule in iter_rules() if rule.rule_id == "intensity_reference_delta")
    old_detectors = target.mode_declaration.detectors
    renamed_detectors = tuple(
        sorted(
            (
                dc.replace(d, detector_id="out_of_range_renamed_164") if d.detector_id == "out_of_range" else d
                for d in old_detectors
            ),
            key=lambda d: d.detector_id,
        )
    )
    assert renamed_detectors != old_detectors
    new_declaration = dc.replace(target.mode_declaration, detectors=renamed_detectors)
    monkeypatch.setattr(target, "mode_declaration", new_declaration)

    original_spec = failure_modes_module.SPECIFICATION
    mode_id, mode_spec = next(
        (mid, ms)
        for mid, ms in original_spec.items()
        if not any(edge.rule_id == "intensity_reference_delta" for edge in ms.intended_rules)
    )
    colliding_edge = failure_modes_module.IntendedRule(
        rule_id="intensity_reference_delta",
        detector_ids=("out_of_range",),
        evidence_rung="needs-real-data",
    )
    patched_mode = dc.replace(mode_spec, intended_rules=mode_spec.intended_rules + (colliding_edge,))
    patched_spec = dict(original_spec)
    patched_spec[mode_id] = patched_mode
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_spec)

    matrix = traceability.build_matrix()
    return matrix, mode_id


def test_detector_id_collides_across_rules(matrix_after_rename_and_colliding_edge):
    matrix, mode_id = matrix_after_rename_and_colliding_edge
    direction = matrix.edge_to_detector
    assert direction.complete is False
    assert (mode_id, "intensity_reference_delta", "out_of_range") in direction.holes


# =========================================================================== #
# Named adversarial case: empty-detector-ids-on-an-edge-is-a-hole
# =========================================================================== #


@pytest.fixture
def matrix_with_empty_edge_detector_ids(monkeypatch):
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    original = failure_modes_module.SPECIFICATION
    mode_id, mode_spec = next((mid, ms) for mid, ms in original.items() if ms.intended_rules)
    edge0 = mode_spec.intended_rules[0]
    emptied_edge = dc.replace(edge0, detector_ids=())
    patched_mode = dc.replace(mode_spec, intended_rules=(emptied_edge,) + mode_spec.intended_rules[1:])
    patched_spec = dict(original)
    patched_spec[mode_id] = patched_mode
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_spec)

    matrix = traceability.build_matrix()
    return matrix, mode_id, edge0.rule_id


def test_empty_detector_ids_on_an_edge_is_a_hole(matrix_with_empty_edge_detector_ids):
    matrix, mode_id, rule_id = matrix_with_empty_edge_detector_ids
    direction = matrix.edge_to_detector
    assert direction.complete is False
    assert any(hole[0] == mode_id and hole[1] == rule_id for hole in direction.holes)


# =========================================================================== #
# Named adversarial case: mode-less-reason-is-what-excuses-a-detector
# =========================================================================== #


@pytest.fixture
def matrix_with_spline_offset_reason_dropped(monkeypatch):
    import segfacet.traceability as traceability
    from segfacet.heuristics.rule import iter_rules

    target = next(rule for rule in iter_rules() if rule.rule_id == "mislabel")
    detectors = target.mode_declaration.detectors
    offset_detector = next(d for d in detectors if d.mode_less_reason)

    new_detectors = tuple(
        dc.replace(d, mode_less_reason="") if d.detector_id == offset_detector.detector_id else d
        for d in detectors
    )
    new_declaration = dc.replace(target.mode_declaration, detectors=new_detectors)
    monkeypatch.setattr(target, "mode_declaration", new_declaration)

    matrix = traceability.build_matrix()
    return matrix, target.rule_id, offset_detector.detector_id


def test_mode_less_reason_is_what_excuses_a_detector(matrix_with_spline_offset_reason_dropped):
    matrix, rule_id, detector_id = matrix_with_spline_offset_reason_dropped
    direction = matrix.detector_to_edge
    assert direction.complete is False
    assert (rule_id, detector_id) in direction.holes
