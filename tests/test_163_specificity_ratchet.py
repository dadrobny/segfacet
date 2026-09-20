"""Tests for item 163 -- the specificity ratchet (no unintended rule may
fire, and no intended rule may go silent, without the change being authored
in ``segfacet.failure_modes.SPECIFICATION``/``CONDITIONS`` and the suite
failing on it).

Covers Acceptance Criteria AC1-AC6 per the item spec's Testing Strategy: AC1
and AC3 are single tests iterating the live case set (no literal case list,
no pinned count -- both re-derived, in-session, from
``segfacet.synth.corpus.load_manifest()`` /
``segfacet.synth.intensity.load_intensity_manifest()`` and from
``segfacet.failure_modes.SPECIFICATION``/``CONDITIONS``); AC2 is parametrised
one test per ``(corpus, case_id)`` pair, ids naming the case; AC4 and AC6
each drive the single geometric case ``fragment`` through
``segfacet.failure_modes.measured_firing`` (never a second
``build_matrix()`` -- A3, the 7-27s cost recorded in ``insights.md``,
2026-09-18) with the rule registry perturbed inside a snapshot-and-restore
fixture (item 162's ``_isolated_rule_registry`` idiom); AC5 asserts on the
message the shared comparison helper returns for AC4's violation. Plus
exactly the one adversarial case the Testing Strategy names,
``unspecified-case-is-not-exempt``.

Shape note (A3): one module-scoped ``build_matrix()`` fixture (the pattern
``tests/test_162_corpus_exercise_report.py`` and
``tests/test_149_conformance_report.py`` use) -- no second ``build_matrix()``
call anywhere in this module. The one adversarial fixture that needs a
freshly-derived conformance report under a patched ``SPECIFICATION`` calls
``segfacet.traceability._build_conformance`` directly instead: the private
function ``build_matrix()`` itself delegates to, so the path proved is the
ratchet's own without paying for the mode-record/exercise-report derivation
``build_matrix()`` layers on top.

A5 note: every case expectation constructed here (the AC4/AC6 probes) carries
a ``case_id`` read from a manifest that is never narrowed or monkeypatched --
``measured_firing`` raises on a case id absent from the manifest it resolves
against (item 162's recorded trap) rather than degrading, and this module's
one SPECIFICATION patch (the adversarial fixture) never touches either
manifest, so it cannot starve the intensity-manifest loader item 162's own
exercise fixtures separately depend on.
"""

from __future__ import annotations

import dataclasses as dc

import pytest


# =========================================================================== #
# build_matrix() fixture -- the one call site in this module (A3).
# =========================================================================== #


@pytest.fixture(scope="module")
def raw_matrix():
    import segfacet.traceability as traceability

    return traceability.build_matrix()


# =========================================================================== #
# House helpers
# =========================================================================== #


def _live_manifest_pairs() -> set:
    """``{(corpus, case_id)}`` across both committed manifests, read live --
    AC1's primary source, never a literal list."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.intensity import load_intensity_manifest

    pairs = {("geometric", c["case_id"]) for c in load_manifest()["cases"]}
    pairs |= {("intensity", c["case_id"]) for c in load_intensity_manifest()["cases"]}
    return pairs


#: Computed once at collection time so AC2 can parametrise one test per pair
#: with a readable id -- itself derived from the same live read AC1 asserts,
#: never a hand-typed case list.
_CASE_PAIRS = sorted(_live_manifest_pairs())


def _case_record(matrix, corpus: str, case_id: str):
    for record in matrix.conformance.cases:
        if record.corpus == corpus and record.case_id == case_id:
            return record
    raise AssertionError(f"no conformance record for {corpus}/{case_id}")


def _manifest_condition(corpus: str, case_id: str) -> str:
    """The manifest case's own ``condition`` field, read live -- what
    ``expected_source == 'specification-condition'`` is dispatched from."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.intensity import load_intensity_manifest

    cases = load_manifest()["cases"] if corpus == "geometric" else load_intensity_manifest()["cases"]
    for case in cases:
        if case["case_id"] == case_id:
            return case.get("condition") or ""
    raise AssertionError(f"no manifest case for {corpus}/{case_id}")


def _compare_firing(corpus: str, case_id: str, expected, measured):
    """The module's one shared comparison helper (Testing Strategy's
    "spine"): the unintended set, the missing set, and one message naming
    corpus, case id, expected and measured -- AC2, AC4, AC5 and AC6 all call
    this, so the guard and its proofs share one code path."""
    expected_set = set(expected)
    measured_set = set(measured)
    unintended = measured_set - expected_set
    missing = expected_set - measured_set
    message = (
        f"{corpus}/{case_id}: expected firing {sorted(expected_set)!r}, "
        f"measured firing {sorted(measured_set)!r} "
        f"(unintended={sorted(unintended)!r}, missing={sorted(missing)!r})"
    )
    return unintended, missing, message


def _recompute_expected(record, failure_modes_module):
    """AC3's recomputation, dispatched on ``record.expected_source`` --
    reads only ``segfacet.failure_modes.SPECIFICATION``/``CONDITIONS``,
    never the conformance record's own ``expected_firing``. Raises
    ``AssertionError`` for ``'unspecified'``: that source names no
    primary-source set to recompute, and is never exempt from the ratchet."""
    source = record.expected_source
    if source == "specification":
        for mode_spec in failure_modes_module.SPECIFICATION.values():
            for case in mode_spec.corpus_cases:
                if case.corpus == record.corpus and case.case_id == record.case_id:
                    return set(case.expected_firing)
        raise AssertionError(
            f"{record.corpus}/{record.case_id}: expected_source 'specification' "
            "names no SPECIFICATION corpus_cases entry"
        )
    if source == "specification-condition":
        condition_id = _manifest_condition(record.corpus, record.case_id)
        condition = failure_modes_module.CONDITIONS.get(condition_id)
        if condition is not None:
            for case in condition.corpus_cases:
                if case.case_id == record.case_id:
                    return set(case.expected_firing)
        raise AssertionError(
            f"{record.corpus}/{record.case_id}: expected_source "
            "'specification-condition' names no CONDITIONS corpus_cases entry "
            f"for condition {condition_id!r}"
        )
    if source == "manifest-clean-control":
        return set()
    raise AssertionError(
        f"{record.corpus}/{record.case_id}: expected_source {source!r} names no "
        "primary-source set to recompute -- never exempt from the ratchet."
    )


# =========================================================================== #
# AC1: every committed corpus case is driven, none exempt.
# =========================================================================== #


def test_ac1_every_committed_corpus_case_is_driven_none_exempt(raw_matrix):
    live_pairs = _live_manifest_pairs()
    assert live_pairs, "expected a non-empty union of committed manifest cases"
    driven_pairs = {(c.corpus, c.case_id) for c in raw_matrix.conformance.cases}
    assert driven_pairs == live_pairs, (driven_pairs, live_pairs)


# =========================================================================== #
# AC2: the ratchet -- one parametrised test per (corpus, case_id) pair.
# =========================================================================== #


@pytest.mark.parametrize(
    "corpus,case_id",
    _CASE_PAIRS,
    ids=[f"{corpus}-{case_id}" for corpus, case_id in _CASE_PAIRS],
)
def test_ac2_ratchet_measured_equals_expected(corpus, case_id, raw_matrix):
    record = _case_record(raw_matrix, corpus, case_id)
    unintended, missing, message = _compare_firing(
        record.corpus, record.case_id, record.expected_firing, record.measured_firing
    )
    assert not unintended and not missing, message


# =========================================================================== #
# AC3: the allowlist is the specification's, recomputed from the primary
# source.
# =========================================================================== #


def test_ac3_expected_firing_is_recomputed_from_the_specification(raw_matrix):
    import segfacet.failure_modes as failure_modes_module

    assert raw_matrix.conformance.cases, "expected a non-empty conformance report"
    for record in raw_matrix.conformance.cases:
        recomputed = _recompute_expected(record, failure_modes_module)
        assert set(record.expected_firing) == recomputed, record


# =========================================================================== #
# AC4/AC5: an unintended rule firing is caught, and the violation names the
# case and both sets.
# =========================================================================== #

_STUB_RULE_ID = "stub_unintended_163"


@pytest.fixture
def _isolated_rule_registry():
    from segfacet.heuristics.rule import _RULES

    snapshot = dict(_RULES)
    try:
        yield
    finally:
        _RULES.clear()
        _RULES.update(snapshot)


@pytest.fixture
def ac4_violation(_isolated_rule_registry, raw_matrix):
    """Registers a stub rule that fires on every record, then drives the
    geometric case ``fragment`` through ``measured_firing`` (not a second
    ``build_matrix()`` -- A3) and runs it through the shared comparison
    helper. Shared by AC4 (the unintended set) and AC5 (the message)."""
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.finding import Finding
    from segfacet.heuristics.rule import Rule, register_rule
    from segfacet.verdict import Severity

    class _StubAlwaysFires(Rule):
        rule_id = _STUB_RULE_ID

        def evaluate(self, record, config):
            return [Finding(rule_id=self.rule_id, severity=Severity.PASS, reason="stub always fires (item 163)")]

    register_rule(_StubAlwaysFires)

    expected_case = _case_record(raw_matrix, "geometric", "fragment")
    probe = failure_modes_module.CorpusCaseExpectation(
        case_id="fragment", corpus="geometric", expected_firing=(), reason=""
    )
    measured = failure_modes_module.measured_firing(probe)
    return _compare_firing("geometric", "fragment", expected_case.expected_firing, measured)


def test_ac4_unintended_rule_firing_is_caught(ac4_violation):
    unintended, _missing, message = ac4_violation
    assert unintended == {_STUB_RULE_ID}, message


def test_ac5_violation_names_case_and_both_sets(ac4_violation, raw_matrix):
    _unintended, _missing, message = ac4_violation
    expected_case = _case_record(raw_matrix, "geometric", "fragment")

    assert "geometric" in message, message
    assert "fragment" in message, message
    for rule_id in expected_case.expected_firing:
        assert rule_id in message, message
    assert _STUB_RULE_ID in message, message


# =========================================================================== #
# AC6: a rule that stops firing is caught.
# =========================================================================== #


@pytest.fixture
def ac6_violation(monkeypatch, raw_matrix):
    """Patches the already-registered ``fragmentation`` rule instance to emit
    no findings, then drives ``fragment`` through ``measured_firing`` (the
    same single-case, no-second-``build_matrix()`` discipline as AC4)."""
    import segfacet.failure_modes as failure_modes_module
    from segfacet.heuristics.rule import get_rule

    fragmentation_rule = get_rule("fragmentation")
    monkeypatch.setattr(fragmentation_rule, "evaluate", lambda record, config: [])

    expected_case = _case_record(raw_matrix, "geometric", "fragment")
    probe = failure_modes_module.CorpusCaseExpectation(
        case_id="fragment", corpus="geometric", expected_firing=(), reason=""
    )
    measured = failure_modes_module.measured_firing(probe)
    return _compare_firing("geometric", "fragment", expected_case.expected_firing, measured)


def test_ac6_rule_that_stops_firing_is_caught(ac6_violation):
    _unintended, missing, message = ac6_violation
    assert missing == {"fragmentation"}, message


# =========================================================================== #
# Adversarial case (Testing Strategy, beyond the AC tests):
# unspecified-case-is-not-exempt.
# =========================================================================== #


@pytest.fixture
def conformance_mode6_corpus_cases_emptied(monkeypatch):
    """Empties mode 6's own ``corpus_cases`` (item 149's
    ``matrix_mode6_corpus_cases_emptied`` idiom, a patched ``SPECIFICATION``)
    so the manifest case ``remove_level`` is orphaned: its conformance
    record's ``expected_source`` turns ``"unspecified"``. Calls
    ``traceability._build_conformance`` directly rather than
    ``build_matrix()`` -- the module's one production entry point this
    fixture needs, without paying for the mode-record/exercise derivation
    ``build_matrix()`` layers on top (A3's budget)."""
    import segfacet.failure_modes as failure_modes_module
    import segfacet.traceability as traceability

    original_mode6 = failure_modes_module.SPECIFICATION[6]
    case_ids = {c.case_id for c in original_mode6.corpus_cases}
    assert "remove_level" in case_ids, case_ids
    patched_map = dict(failure_modes_module.SPECIFICATION)
    patched_map[6] = dc.replace(original_mode6, corpus_cases=())
    monkeypatch.setattr(failure_modes_module, "SPECIFICATION", patched_map)

    return traceability._build_conformance(failure_modes_module)


def test_unspecified_case_is_not_exempt(conformance_mode6_corpus_cases_emptied):
    import segfacet.failure_modes as failure_modes_module

    report = conformance_mode6_corpus_cases_emptied
    orphaned = next(
        c for c in report.cases if c.corpus == "geometric" and c.case_id == "remove_level"
    )
    assert orphaned.expected_source == "unspecified", orphaned

    with pytest.raises(AssertionError):
        _recompute_expected(orphaned, failure_modes_module)
