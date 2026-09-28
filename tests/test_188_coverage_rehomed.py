"""Tests for item 188 -- ``coverage`` re-homed from mode 6 to mode 10.

``coverage`` reads ``relationships.missing_levels[]`` and
``relationships.present_levels[]`` -- lists of labels. It sees a missing
*label* in the sequence and cannot see whether a vertebra is there, so it
serves mode 10 ("skipped level label"), not mode 6 ("vertebra not
segmented"). ``remove_level`` (mode 6's corpus case) still fires it, now as a
recorded co-detection that does not validate mode 6. Mode 6's own rule, over
the inter-centroid spacing, is decided in a later per-mode queue and is not
in scope here.

Covers Acceptance Criteria AC1-AC10, one direct test each, plus the one named
adversarial case the Testing Strategy lists (``declared-set-reads-the-
registry``) -- no others.
"""

from __future__ import annotations

import pytest

from segfacet.heuristics.coverage import CoverageRule
from segfacet.heuristics.rule import Rule, RuleModeDeclaration, _RULES, iter_rule_declarations, register_rule


def _coverage_detector_ids():
    """"Its detector ids", as AC1's terms define them: the sorted tuple of
    ``detector_id`` over the coverage rule's own declared detectors -- read
    from the live declaration, never a literal tuple, per the Testing
    Strategy note on AC2."""
    return tuple(sorted(d.detector_id for d in CoverageRule.mode_declaration.detectors))


def _declared_set(mode_id: int) -> set:
    """"The declared set of mode N", as the terms section defines it: the
    ``rule_id``s over the live registry whose declaration is not ``None`` and
    lists N in ``modes``."""
    return {
        rule_id
        for rule_id, declaration in iter_rule_declarations()
        if declaration is not None and mode_id in declaration.modes
    }


@pytest.fixture
def isolated_registry():
    """Snapshot/restore the rule registry -- the house pattern
    ``tests/test_136_rule_mode_declarations.py``'s ``isolated_registry`` uses
    -- so the stub rule the named adversarial case registers cannot leak into
    another test's clean-tree assertions."""
    snapshot = dict(_RULES)
    yield
    _RULES.clear()
    _RULES.update(snapshot)


# =========================================================================== #
# AC1: coverage declares mode 10 alone
# =========================================================================== #


def test_ac1_coverage_declares_mode_10_alone():
    assert CoverageRule.mode_declaration.modes == (10,)


# =========================================================================== #
# AC2: mode 10 carries the coverage edge at needs-real-data
# =========================================================================== #


def test_ac2_mode_10_carries_the_coverage_edge_at_needs_real_data():
    import segfacet.failure_modes as fm

    edges = [
        edge for edge in fm.SPECIFICATION[10].intended_rules if edge.rule_id == "coverage"
    ]
    assert edges == [
        fm.IntendedRule(
            rule_id="coverage",
            detector_ids=_coverage_detector_ids(),
            evidence_rung="needs-real-data",
        )
    ]


# =========================================================================== #
# AC3: mode 6 carries no edge
# =========================================================================== #


def test_ac3_mode_6_carries_no_edge():
    import segfacet.failure_modes as fm

    assert fm.SPECIFICATION[6].intended_rules == ()


# =========================================================================== #
# AC4: every coverage detector serves mode 10 alone
# =========================================================================== #


def test_ac4_every_coverage_detector_serves_mode_10_alone():
    import segfacet.failure_modes as fm

    detector_ids = _coverage_detector_ids()
    assert detector_ids, "expected coverage to declare at least one detector"
    for detector_id in detector_ids:
        assert fm.modes_for_detector("coverage", detector_id) == (10,), detector_id


# =========================================================================== #
# AC5: no registered rule declares mode 6
# =========================================================================== #


def test_ac5_no_registered_rule_declares_mode_6():
    assert _declared_set(6) == set()


# =========================================================================== #
# AC6: both remove_level cases stay attributed to mode 6
# =========================================================================== #


def test_ac6_both_remove_level_cases_stay_attributed_to_mode_6():
    import segfacet.failure_modes as fm

    case_ids = {c.case_id for c in fm.SPECIFICATION[6].corpus_cases}
    assert case_ids == {"remove_level", "remove_level_relabel"}


# =========================================================================== #
# AC7: mode 6's derived status records that no rule detects it
# =========================================================================== #


def test_ac7_mode_6_derives_specified():
    import segfacet.failure_modes as fm

    assert fm.derive_status(fm.SPECIFICATION[6]) == "specified"


# =========================================================================== #
# AC8: mode 6's derived rung is absent
# =========================================================================== #


def test_ac8_mode_6_derived_rung_is_none():
    import segfacet.failure_modes as fm

    assert fm.derive_mode_rung(fm.SPECIFICATION[6]) is None


# =========================================================================== #
# AC9: mode 10 derives implemented
# =========================================================================== #


def test_ac9_mode_10_derives_implemented():
    import segfacet.failure_modes as fm

    assert fm.derive_status(fm.SPECIFICATION[10]) == "implemented"


# =========================================================================== #
# AC10: mode 10's derived rung is needs-real-data
# =========================================================================== #


def test_ac10_mode_10_derived_rung_is_needs_real_data():
    import segfacet.failure_modes as fm

    assert fm.derive_mode_rung(fm.SPECIFICATION[10]) == "needs-real-data"


# =========================================================================== #
# Named adversarial case: declared-set-reads-the-registry
# =========================================================================== #


def test_declared_set_reads_the_registry(isolated_registry):
    """Guards AC5 passing for the wrong reason: with a stub rule declaring
    ``modes=(6,)`` registered in an isolated registry, "the declared set of
    mode 6" must read that stub back -- proving the computation reads the
    live registry rather than something that cannot see a declaration, such
    as mode 6's own (empty) ``intended_rules``."""

    class _Item188StubRule(Rule):
        rule_id = "__item188_stub_declares_mode_6__"
        mode_declaration = RuleModeDeclaration(modes=(6,), evidence=("stub, for a test",))

        def evaluate(self, record, config):
            return []

    register_rule(_Item188StubRule)
    assert _declared_set(6) == {"__item188_stub_declares_mode_6__"}
