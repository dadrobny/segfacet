"""Tests for item 195 -- ``force_overlap`` removed.

A single-channel integer label map cannot express an overlap (each voxel
carries exactly one label), so the committed ``force_overlap`` corpus case
was attributed to a mode its fixture does not express. This item removes the
operator, its corpus case and fixture, its severity ladder, margin and
coupling, and the operator-specific reconstruction technique that rebuilt
its two-mask stack -- while keeping the ``overlap`` rule, now declared to
need multi-channel input, and mode 15's mechanism rewritten to say so (item
195 spec, 2026-09-28).

Covers Acceptance Criteria AC1-AC12:

- AC1: no manifest case is ``force_overlap``.
- AC2: the operator registry has no ``force_overlap``.
- AC3: the ladder registry has no ``force_overlap``.
- AC4: margins are recorded for exactly the registered ladders.
- AC5: every recorded coupling names a registered ladder.
- AC6: the severity harness passes.
- AC7: responses are scored only for the laddered metrics.
- AC8: mode 15 carries no corpus case.
- AC9: the rule-exercise report records ``overlap`` with a derived reason.
- AC10: the ``overlap`` rule's declaration says it needs multi-channel input.
- AC11: mode 15's mechanism says the same.
- AC12: every committed geometric fixture is referenced by the manifest.

Named adversarial cases (item 195 spec's Testing Strategy), and no others:

- planted-stale-margin
- planted-stale-coupling
- second-unowned-metric
- planted-orphan-fixture
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

import segfacet.synth  # noqa: F401 -- triggers self-registration of every operator
from segfacet import failure_modes, traceability
from segfacet.eval import severity_ladder
from segfacet.heuristics.overlap import OverlapRule
from segfacet.synth import corpus
from segfacet.synth.perturbation import perturbation_names


# --------------------------------------------------------------------------- #
# Helpers taking the tables as arguments (Testing Strategy), so the
# adversarial cases below can pass planted ones instead of the live tables.
# --------------------------------------------------------------------------- #


def _margins_without_a_ladder(margins, ladders) -> set:
    """``margins`` keys that name no key of ``ladders`` (item 195, 2026-09-28)."""
    return set(margins) - set(ladders)


def _couplings_without_a_ladder(couplings, ladders) -> set:
    """``couplings`` ``ladder_operator`` values naming no key of ``ladders``
    (item 195, 2026-09-28)."""
    return {c.ladder_operator for c in couplings} - set(ladders)


def _fixture_mismatch(fixtures_dir: Path, manifest: dict) -> set:
    """Symmetric difference between the fixture file names on disk in
    *fixtures_dir* and the basenames every manifest case references via
    ``seg_fixture``/``scan_fixture`` (item 195, 2026-09-28). Symmetric so a
    one-directional (referenced-subset-of-disk-only) check cannot pass this
    helper by accident."""
    on_disk = {p.name for p in fixtures_dir.iterdir()}
    referenced = set()
    for case in manifest["cases"]:
        referenced.add(Path(case["seg_fixture"]).name)
        referenced.add(Path(case["scan_fixture"]).name)
    return on_disk ^ referenced


# --------------------------------------------------------------------------- #
# Module-scoped fixtures (AC6, AC7 and AC9 share one harness/matrix result).
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def harness_verdict():
    return severity_ladder.score_harness(severity_ladder.run_severity_harness())


@pytest.fixture(scope="module")
def matrix():
    return traceability.build_matrix()


# --------------------------------------------------------------------------- #
# AC1-AC3
# --------------------------------------------------------------------------- #


def test_ac1_no_manifest_case_is_force_overlap():
    manifest = corpus.load_manifest()
    case_ids = {case["case_id"] for case in manifest["cases"]}
    perturbations = {case["perturbation"] for case in manifest["cases"]}
    assert "force_overlap" not in case_ids
    assert "force_overlap" not in perturbations


def test_ac2_operator_registry_has_no_force_overlap():
    assert "force_overlap" not in perturbation_names()


def test_ac3_ladder_registry_has_no_force_overlap():
    assert "force_overlap" not in severity_ladder.SEVERITY_LADDERS


# --------------------------------------------------------------------------- #
# AC4-AC5
# --------------------------------------------------------------------------- #


def test_ac4_margins_recorded_for_exactly_the_registered_ladders():
    assert (
        _margins_without_a_ladder(
            severity_ladder.RECORDED_MARGINS, severity_ladder.SEVERITY_LADDERS
        )
        == set()
    )


def test_ac5_every_recorded_coupling_names_a_registered_ladder():
    assert (
        _couplings_without_a_ladder(
            severity_ladder.KNOWN_CROSS_MODE_COUPLINGS, severity_ladder.SEVERITY_LADDERS
        )
        == set()
    )


# --------------------------------------------------------------------------- #
# AC6-AC7
# --------------------------------------------------------------------------- #


def test_ac6_severity_harness_passes(harness_verdict):
    assert harness_verdict.passed is True


def test_ac7_responses_scored_only_for_the_laddered_metrics(harness_verdict):
    laddered = {
        spec.designated_metric for spec in severity_ladder.SEVERITY_LADDERS.values()
    }
    for verdict in harness_verdict.per_ladder.values():
        assert set(verdict.responses) == laddered


# --------------------------------------------------------------------------- #
# AC8-AC9
# --------------------------------------------------------------------------- #


def test_ac8_mode_15_carries_no_corpus_case():
    assert failure_modes.SPECIFICATION[15].corpus_cases == ()


def test_ac9_rule_exercise_report_records_overlap_with_a_derived_reason(matrix):
    record = next(r for r in matrix.exercise.rules if r.rule_id == "overlap")
    assert record.state == "unexercised"
    assert record.reason == failure_modes.derive_mode_rung(failure_modes.SPECIFICATION[15])
    assert record.reason_modes == (15,)


# --------------------------------------------------------------------------- #
# AC10-AC11
# --------------------------------------------------------------------------- #


def test_ac10_overlap_rule_declaration_says_multi_channel():
    assert any(
        "multi-channel" in evidence
        for evidence in OverlapRule.mode_declaration.evidence
    )


def test_ac11_mode_15_mechanism_says_multi_channel():
    assert "multi-channel" in failure_modes.SPECIFICATION[15].mechanism


# --------------------------------------------------------------------------- #
# AC12
# --------------------------------------------------------------------------- #


def test_ac12_every_committed_geometric_fixture_is_referenced():
    fixtures_dir = corpus.CORPUS_DIR / corpus.FIXTURES_DIRNAME
    manifest = corpus.load_manifest()
    assert _fixture_mismatch(fixtures_dir, manifest) == set()


# --------------------------------------------------------------------------- #
# Named adversarial cases
# --------------------------------------------------------------------------- #


def test_planted_stale_margin():
    """A stale ``RECORDED_MARGINS`` entry naming no registered ladder is
    caught -- guards a check that compares only the ladder side, or reads
    ``SEVERITY_LADDERS`` twice."""
    planted = dict(severity_ladder.RECORDED_MARGINS)
    planted["force_overlap"] = 1.741
    assert _margins_without_a_ladder(planted, severity_ladder.SEVERITY_LADDERS) == {
        "force_overlap"
    }


def test_planted_stale_coupling():
    """A stale ``CrossModeCoupling`` naming no registered ladder is caught --
    guards a check that iterates ladders instead of couplings."""
    provenance = severity_ladder.MeasurementProvenance(
        corpus="geometric",
        base_params={},
        measured_on="2026-09-28",
    )
    planted = severity_ladder.KNOWN_CROSS_MODE_COUPLINGS + (
        severity_ladder.CrossModeCoupling(
            ladder_operator="force_overlap",
            foreign_metric="unanchored_foreground_fraction",
            recorded_response=0.5742,
            cause="planted for test_planted_stale_coupling (item 195, 2026-09-28).",
            provenance=provenance,
        ),
    )
    assert _couplings_without_a_ladder(planted, severity_ladder.SEVERITY_LADDERS) == {
        "force_overlap"
    }


def test_second_unowned_metric(monkeypatch, harness_verdict):
    """With ``SEVERITY_LADDERS`` monkeypatched to drop ``inject_islands``,
    the harness still passes: every verdict carries the remaining six
    responses (never ``rogue_island_count``), and the six remaining margins
    equal those of the unpatched run. Guards a fix that special-cases the
    name ``overlapping_voxel_count`` instead of deriving the laddered set
    from ``SEVERITY_LADDERS``."""
    patched_ladders = MappingProxyType(
        {
            op: spec
            for op, spec in severity_ladder.SEVERITY_LADDERS.items()
            if op != "inject_islands"
        }
    )
    monkeypatch.setattr(severity_ladder, "SEVERITY_LADDERS", patched_ladders)

    patched_verdict = severity_ladder.score_harness(severity_ladder.run_severity_harness())

    assert patched_verdict.passed is True
    laddered = {spec.designated_metric for spec in patched_ladders.values()}
    for op, lv in patched_verdict.per_ladder.items():
        assert set(lv.responses) == laddered
        assert "rogue_island_count" not in lv.responses
        assert lv.margin == pytest.approx(harness_verdict.per_ladder[op].margin)


def test_planted_orphan_fixture(tmp_path):
    """A ``tmp_path`` fixtures directory holding the manifest's files plus
    one extra ``orphan_seg.nii.gz`` is caught -- guards a one-directional
    comparison (referenced subset-of on-disk only)."""
    manifest = corpus.load_manifest()
    referenced = set()
    for case in manifest["cases"]:
        referenced.add(Path(case["seg_fixture"]).name)
        referenced.add(Path(case["scan_fixture"]).name)
    for name in referenced:
        (tmp_path / name).touch()
    (tmp_path / "orphan_seg.nii.gz").touch()

    assert _fixture_mismatch(tmp_path, manifest) == {"orphan_seg.nii.gz"}
