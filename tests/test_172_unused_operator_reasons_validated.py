"""Tests for item 172 -- ``segfacet.traceability.operator_reason_conflicts()``,
which validates ``UNUSED_OPERATOR_REASONS`` entries that ``_build_exercise``
itself never checks: a key absent from ``perturbation_names()``, and a key
naming an operator that ``CASE_RECIPE`` actually uses.

Covers Acceptance Criteria AC1-AC4 per the item spec's Testing Strategy: one
test per AC, plus the one named adversarial case, ``both-kinds-at-once``.
None of these tests calls ``build_matrix()`` -- the function does not depend
on the matrix.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def _isolated_perturbation_registry():
    """Copied from ``test_162_corpus_exercise_report.py`` per the item spec's
    Testing Strategy -- not imported across test modules."""
    from segfacet.synth.perturbation import Perturbation, _PERTURBATIONS, register_perturbation

    snapshot = dict(_PERTURBATIONS)
    try:
        yield Perturbation, register_perturbation
    finally:
        _PERTURBATIONS.clear()
        _PERTURBATIONS.update(snapshot)


# AC1: an entry for an unregistered name is reported.
def test_ac1_unregistered_name_is_reported(monkeypatch):
    import segfacet.traceability as traceability
    from segfacet.synth.perturbation import perturbation_names

    unregistered_name = "unregistered_operator_172"
    assert unregistered_name not in perturbation_names()

    monkeypatch.setattr(
        traceability, "UNUSED_OPERATOR_REASONS", {unregistered_name: "stale reason"}
    )

    conflicts = traceability.operator_reason_conflicts()

    assert len(conflicts) == 1
    assert unregistered_name in conflicts[0]


# AC2: an entry for a used operator is reported.
def test_ac2_used_operator_is_reported(monkeypatch):
    import segfacet.traceability as traceability
    from segfacet.synth.corpus import CASE_RECIPE

    used_name = sorted(entry.perturbation for entry in CASE_RECIPE)[0]

    monkeypatch.setattr(
        traceability, "UNUSED_OPERATOR_REASONS", {used_name: "not actually unused"}
    )

    conflicts = traceability.operator_reason_conflicts()

    assert len(conflicts) == 1
    assert used_name in conflicts[0]


# AC3: an entry for a registered, unused operator is not reported.
def test_ac3_registered_unused_operator_is_not_reported(
    _isolated_perturbation_registry, monkeypatch
):
    import segfacet.traceability as traceability
    from segfacet.synth.corpus import CASE_RECIPE

    Perturbation, register_perturbation = _isolated_perturbation_registry

    class _Stub(Perturbation):
        name = "stub_unused_172"

        def apply(self, labelmap, seed):
            raise NotImplementedError

    register_perturbation(_Stub)
    assert not any(entry.perturbation == _Stub.name for entry in CASE_RECIPE)

    monkeypatch.setattr(
        traceability, "UNUSED_OPERATOR_REASONS", {_Stub.name: "kept for later (test)"}
    )

    assert traceability.operator_reason_conflicts() == ()


# AC4: the live tree reports no conflict.
def test_ac4_live_tree_reports_no_conflict():
    import segfacet.traceability as traceability

    assert traceability.operator_reason_conflicts() == ()


# Adversarial case: both-kinds-at-once.
def test_both_kinds_at_once(_isolated_perturbation_registry, monkeypatch):
    import segfacet.traceability as traceability
    from segfacet.synth.corpus import CASE_RECIPE
    from segfacet.synth.perturbation import perturbation_names

    Perturbation, register_perturbation = _isolated_perturbation_registry

    class _Stub(Perturbation):
        name = "stub_unused_172_both"

        def apply(self, labelmap, seed):
            raise NotImplementedError

    register_perturbation(_Stub)
    assert not any(entry.perturbation == _Stub.name for entry in CASE_RECIPE)

    unregistered_name = "unregistered_operator_172_both"
    assert unregistered_name not in perturbation_names()

    used_name = sorted(entry.perturbation for entry in CASE_RECIPE)[0]

    monkeypatch.setattr(
        traceability,
        "UNUSED_OPERATOR_REASONS",
        {
            unregistered_name: "stale reason",
            used_name: "not actually unused",
            _Stub.name: "kept for later (test)",
        },
    )

    conflicts = traceability.operator_reason_conflicts()

    assert len(conflicts) == 2
    joined = " ".join(conflicts)
    assert unregistered_name in joined
    assert used_name in joined
    assert _Stub.name not in joined
