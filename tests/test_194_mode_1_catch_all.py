"""Tests for item 194 -- mode 1 (segmentation accuracy) is attributed only as
the catch-all: a corpus case, or a detector's edge, is attributed to mode 1
only when no other mode applies, and never beside another mode. Also the
review's vocabulary -- mode 2 is one label over parts of several vertebrae,
mode 3 is one vertebra under more than one label -- lands in
``SPECIFICATION[2].definition`` / ``SPECIFICATION[3].definition``.

Covers Acceptance Criteria AC1-AC6 per the item spec's Testing Strategy: one
test per AC, each recomputed from ``segfacet.failure_modes.SPECIFICATION``
(via ``iter_modes()``/``iter_conditions()``, never a hand-typed mode list) or
from the committed corpus manifests via the same harness functions the
manifests' own ``detection`` field names -- never a literal of what a case's
findings "should" be. Plus exactly the three adversarial cases the Testing
Strategy names: ``planted-shared-mode-1-edge``, ``planted-double-carried-case``
and ``served-modes-see-a-shared-detector``.

AC1 and AC3 are written over helpers that take an iterable of ``ModeSpec``
(and, for AC3, the conditions too), so the adversarial cases can pass a
planted tuple without touching the shipped ``SPECIFICATION``. AC2 shares one
module-scoped fixture that drives every committed corpus case's findings at
most once (the expensive part of this module) and dispatches on each
manifest case's own ``detection`` field, exactly as the item spec's "a case's
served modes" term defines it.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, FrozenSet, Iterable, Tuple

import pytest

import segfacet.failure_modes as fm

_S = (
    "The catch-all for accuracy defects: a corpus case, or a detector's "
    "edge, is attributed to this mode only when no other mode applies, and "
    "never beside another mode."
)


# =========================================================================== #
# Shared helpers (AC1/AC3's "written over a helper" requirement, and the two
# corresponding adversarial cases reuse them unchanged).
# =========================================================================== #


def _detector_groups(
    modes: Iterable[fm.ModeSpec],
) -> Dict[Tuple[str, str], FrozenSet[int]]:
    """The item spec's "detector groups": maps each ``(rule_id, detector_id)``
    pair to the set of mode ids whose ``IntendedRule`` edges name that
    ``rule_id`` and carry that ``detector_id``, computed over *modes* --
    never the module-level ``SPECIFICATION`` directly -- so a caller can pass
    a planted tuple."""
    groups: Dict[Tuple[str, str], set] = {}
    for mode in modes:
        for edge in mode.intended_rules:
            for detector_id in edge.detector_ids:
                groups.setdefault((edge.rule_id, detector_id), set()).add(mode.id)
    return {key: frozenset(ids) for key, ids in groups.items()}


def _groups_containing_mode_1(
    modes: Iterable[fm.ModeSpec],
) -> Dict[Tuple[str, str], FrozenSet[int]]:
    """AC1's helper: the subset of :func:`_detector_groups` whose group
    contains mode 1. A conforming specification maps every key here to
    ``frozenset({1})``."""
    return {key: ids for key, ids in _detector_groups(modes).items() if 1 in ids}


def _mode_1_shared_case_ids(
    modes: Iterable[fm.ModeSpec], conditions: Iterable[fm.ConditionSpec]
) -> FrozenSet[str]:
    """AC3's helper: the ``case_id``s in the mode-1 entry's ``corpus_cases``
    (found by scanning *modes* for ``id == 1``) that also appear in some
    other *modes* entry's ``corpus_cases`` or some *conditions* entry's
    ``corpus_cases``. Empty on a conforming specification."""
    modes = tuple(modes)
    mode_1 = next(mode for mode in modes if mode.id == 1)
    mode_1_ids = {case.case_id for case in mode_1.corpus_cases}

    other_ids = set()
    for mode in modes:
        if mode.id == 1:
            continue
        other_ids.update(case.case_id for case in mode.corpus_cases)
    for condition in conditions:
        other_ids.update(case.case_id for case in condition.corpus_cases)

    return frozenset(mode_1_ids & other_ids)


# =========================================================================== #
# AC2's module-scoped drive fixture -- one measurement pass over every
# committed corpus case, dispatching on the manifest case's own `detection`
# field (Testing Strategy).
# =========================================================================== #


@pytest.fixture(scope="module")
def served_modes_by_case():
    """``{case_id: served_modes}`` for every case in both committed corpus
    manifests, plus the total number of cases processed (so the consuming
    test can assert every case was checked, not just that the dict is
    non-empty)."""
    from segfacet.synth import corpus as corpus_module
    from segfacet.synth import intensity as intensity_module
    from segfacet.synth.regression import (
        intensity_pipeline_findings,
        pipeline_findings,
        reconstructed_findings,
    )

    served: Dict[str, set] = {}
    processed = 0

    for case in corpus_module.load_manifest()["cases"]:
        detection = case["detection"]
        if detection == "pipeline":
            findings = pipeline_findings(case)
        elif detection == "reconstructed_record":
            findings = reconstructed_findings(case)
        else:
            raise AssertionError(
                f"unrecognised detection {detection!r} for "
                f"case_id={case['case_id']!r} (geometric manifest)"
            )
        modes = set()
        for finding in findings:
            modes.update(fm.modes_for_detector(finding.rule_id, finding.detector_id))
        served[case["case_id"]] = modes
        processed += 1

    for case in intensity_module.load_intensity_manifest()["cases"]:
        detection = case["detection"]
        if detection != "intensity_pipeline":
            raise AssertionError(
                f"unrecognised detection {detection!r} for "
                f"case_id={case['case_id']!r} (intensity manifest)"
            )
        findings = intensity_pipeline_findings(case)
        modes = set()
        for finding in findings:
            modes.update(fm.modes_for_detector(finding.rule_id, finding.detector_id))
        served[case["case_id"]] = modes
        processed += 1

    return served, processed


# =========================================================================== #
# AC1: no detector serves mode 1 beside another mode
# =========================================================================== #


def test_ac1_no_detector_serves_mode_1_beside_another_mode():
    containing_1 = _groups_containing_mode_1(fm.iter_modes())
    assert containing_1, "expected >=1 detector group containing mode 1"
    assert all(ids == frozenset({1}) for ids in containing_1.values()), containing_1


# =========================================================================== #
# AC2: no committed case is served by mode 1 beside another mode
# =========================================================================== #


def test_ac2_no_committed_case_served_by_mode_1_beside_another_mode(
    served_modes_by_case,
):
    from segfacet.synth import corpus as corpus_module
    from segfacet.synth import intensity as intensity_module

    served, processed = served_modes_by_case
    expected_total = len(corpus_module.load_manifest()["cases"]) + len(
        intensity_module.load_intensity_manifest()["cases"]
    )
    assert processed == expected_total, (processed, expected_total)
    assert served, "expected >=1 case in the committed corpora"

    for case_id, modes in served.items():
        if 1 in modes:
            assert modes == {1}, (case_id, modes)


# =========================================================================== #
# AC3: no case is carried by mode 1 and by another entry
# =========================================================================== #


def test_ac3_no_case_carried_by_mode_1_and_another_entry():
    shared = _mode_1_shared_case_ids(fm.iter_modes(), fm.iter_conditions())
    assert shared == frozenset()


# =========================================================================== #
# AC4: the rendering states mode 1's catch-all rule
# =========================================================================== #


def test_ac4_rendering_states_mode_1s_catch_all_rule():
    lines = fm.render_markdown().splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## Mode 1:")]
    assert starts, "expected a '## Mode 1:' heading in render_markdown()"
    start = starts[0]

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    section = "\n".join(lines[start:end])
    assert _S in section


# =========================================================================== #
# AC5/AC6: modes 2 and 3's definitions use the vertebra wording
# =========================================================================== #


def test_ac5_mode_2_definition_uses_the_vertebra_wording():
    expected = (
        "One label covers substantial parts of two or more adjacent "
        "ground-truth vertebrae:"
    )
    assert fm.SPECIFICATION[2].definition.startswith(expected)


def test_ac6_mode_3_definition_uses_the_vertebra_wording():
    expected = "One ground-truth vertebra is covered by more than one label:"
    assert fm.SPECIFICATION[3].definition.startswith(expected)


# =========================================================================== #
# Adversarial / edge cases -- and no others.
# =========================================================================== #


def test_adv_planted_shared_mode_1_edge_is_reported():
    """``planted-shared-mode-1-edge``: mode 1 re-planted with the same
    ``bounds``/``metric_out_of_range`` edge modes 2, 3 and 4 already carry
    makes AC1's helper report exactly ``{("bounds", "metric_out_of_range")}``
    -- it guards a predicate that only iterates mode 1's own edges, or reads
    the unpatched ``SPECIFICATION``, and so can never see a sharing
    detector."""
    planted = fm.IntendedRule(
        rule_id="bounds",
        detector_ids=("metric_out_of_range",),
        evidence_rung="needs-real-data",
    )
    modes = tuple(
        dataclasses.replace(mode, intended_rules=(planted,))
        if mode.id == 1
        else mode
        for mode in fm.iter_modes()
    )

    containing_1 = _groups_containing_mode_1(modes)
    assert set(containing_1) == {("bounds", "metric_out_of_range")}
    assert containing_1[("bounds", "metric_out_of_range")] != frozenset({1})


def test_adv_planted_double_carried_case_is_reported():
    """``planted-double-carried-case``: mode 1 planted with ``split``'s
    ``CorpusCaseExpectation`` (taken from ``SPECIFICATION[3].corpus_cases``)
    makes AC3's helper report exactly ``{"split"}`` -- it guards a
    disjointness check that compares mode 1 against itself, or against
    conditions only."""
    split_case = next(
        case
        for case in fm.SPECIFICATION[3].corpus_cases
        if case.case_id == "split"
    )
    modes = tuple(
        dataclasses.replace(mode, corpus_cases=mode.corpus_cases + (split_case,))
        if mode.id == 1
        else mode
        for mode in fm.iter_modes()
    )

    shared = _mode_1_shared_case_ids(modes, fm.iter_conditions())
    assert shared == {"split"}


def test_adv_served_modes_see_a_shared_detector(monkeypatch):
    """``served-modes-see-a-shared-detector``: with ``SPECIFICATION``
    monkeypatched so mode 1 carries the planted ``bounds`` edge above, the
    served modes of ``split_own_label`` equal ``{1, 2, 3, 4}`` (measured on
    the pre-item tree). Guards AC2 computing served modes at rule
    granularity or from the manifest's ``failure_mode``, either of which
    passes whatever the edges say."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.regression import pipeline_findings

    planted = fm.IntendedRule(
        rule_id="bounds",
        detector_ids=("metric_out_of_range",),
        evidence_rung="needs-real-data",
    )
    planted_mode_1 = dataclasses.replace(fm.SPECIFICATION[1], intended_rules=(planted,))
    patched = dict(fm.SPECIFICATION)
    patched[1] = planted_mode_1
    monkeypatch.setattr(fm, "SPECIFICATION", patched)

    case = next(
        c for c in load_manifest()["cases"] if c["case_id"] == "split_own_label"
    )
    findings = pipeline_findings(case)
    assert findings, "fixture assumption: split_own_label fires >=1 finding"

    served = set()
    for finding in findings:
        served.update(fm.modes_for_detector(finding.rule_id, finding.detector_id))
    assert served == {1, 2, 3, 4}
