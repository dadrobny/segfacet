"""Tests for item 145 -- authoring vision.md section 6's eight hypothesised
failure modes into item 144's specification module (``segfacet.failure_modes``)
and regenerating ``docs/aide/failure_modes.generated.{json,md}``.

Covers Acceptance Criteria AC1-AC24 per the item spec's Testing Strategy, plus
the listed adversarial / edge cases. Every factual AC recomputes its fact from
the primary source -- the live rule registry, ``MODE_ANCHOR_PATHS``, the
parsed ``vision.md``, or a fresh drive of the committed corpus fixtures --
and compares; none is met by a length floor, a token-presence check alone, or
a flag derived from the declarations themselves.

Corpus-driven tests (AC8-AC18, AC20, AC21) share two module-scoped fixtures
(``corpus``, ``measured``) that each drive a committed case through the
pipeline / ``measured_firing`` at most once and cache the result by
``case_id`` -- the expensive part of this module.

AC23 -- reconciled (item 149, 2026-09-04): ``docs/aide/failure_modes.generated.
{json,md}`` now carry a ``tests/committed_artifact_guard.py`` ``ALLOWLIST``
entry under the sixth ``GROUNDS`` member, ``"no-float-leaf"``, added by item
149 in ``tests/committed_artifact_guard.py`` directly (not by this module).
This module's own fresh-vs-committed comparison still goes through
``json.loads()``/``specification_to_dict()`` and a plain ``render_markdown()``
string equality rather than a ``read_bytes()`` comparison of the two
committed paths -- that pattern was never contingent on the allowlist ground
existing, so it is unchanged; item 149's own module,
``tests/test_149_conformance_report.py``, is what exercises the new
byte-exact/allowlisted path. The byte-exact comparison here stays run-to-run
only (two ``tmp_path`` renders), matching item 144's own AC18 pattern.

Reconciled (item 150, 2026-09-14) against the **signed-off taxonomy**. The
maintainer accepted the catalogue with changes and re-organised it, so the
"eight hypothesised modes" this module was written against no longer exist as
a group: ids were re-assigned into a one-tier hierarchy of ten modes, the old
mode 6 (partial vertebra at the image border) became the ``fov_truncation``
**condition** with no failure mode at all, and two entries (7 and 8) are
``proposed`` -- listed, defined, with no declaring rule and no corpus case.
vision.md section 6 is now **provenance**: its eight titles are the seed the
catalogue started from, mapped through ``VISION_SEED_DISPOSITION``, and mode
``name`` fields deliberately no longer equal them.

Every AC below is re-pointed at its counterpart in the signed-off catalogue,
with the same rigour: nothing is met by a length floor or by re-deriving the
production function it checks, the adversarial tests still run the *same*
predicate over a broken copy, and the per-mode groups are those the sign-off
created (``_MODE_IDS`` / ``_PROPOSED_MODE_IDS`` / ``_GEOMETRIC_CORPUS_MODE_IDS``)
rather than the retired seed of eight.

Reconciled again (item 150, 2026-09-15) against the **revised** sign-off:
every sub-mode that paired two converse defects was split, so the catalogue
carries sixteen modes. Fused (2) / split (3), islands (4) / holes (5),
not segmented (6) / hallucinated (7), collapsed (13) / duplicated (14); the
implausible label sequence became out-of-order (9, severity ``fail``),
missing interior level (10) and unprompted numbering variant (11); shifted
label sequence is 12, overlap 15, implausible tissue 16. The maintainer
then narrowed mode 10 to the label alone ("skipped level label", proposed,
severity ``fail``, no rule and no case) and widened mode 6 to own a missed
vertebra, so ``coverage`` and ``remove_level`` now sit at mode 6,
which derives ``validated``. ``fragment``
and ``fragmentation``'s Fragmentation: detector sit at the parent, mode 1,
which therefore derives ``validated``. The groups below are re-pinned to
those ids; each test keeps its claim.
"""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_COMMITTED_JSON = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
_COMMITTED_MD = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"
_MANIFEST_PATH = _REPO_ROOT / "tests" / "corpus" / "manifest.json"

#: Every mode id the item-150 sign-off assigned, ascending. Pinned literally:
#: these tests are what assert *which* entries the catalogue carries, so
#: deriving them from ``SPECIFICATION`` would assert nothing.
_MODE_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

#: The entries authored ``"proposed"``: listed and deliberately unimplemented,
#: so they carry no intended-rule edge, no corpus case and no declaring rule.
_PROPOSED_MODE_IDS = (5, 7, 10, 11, 12, 13, 14)

#: The modes whose corpus cases live in the **geometric** manifest
#: (``tests/corpus/manifest.json``), which is the only one the ``corpus``
#: fixture and ``_manifest_case`` resolve against. Modes 3 and 8 are
#: specified but carry no case; mode 16's three cases are in the intensity
#: corpus; the proposed entries (mode 10 among them since the maintainer
#: narrowed it to a skipped label) carry none.
_GEOMETRIC_CORPUS_MODE_IDS = (1, 2, 4, 6, 9, 15)

#: The condition the sign-off retired failure mode 6 into.
_FOV_CONDITION_ID = "fov_truncation"

#: The lifecycle status each shipped entry derives from live state under the
#: signed-off catalogue (a declaring rule, every corpus case agreeing, and at
#: least one case demonstrating one of the mode's *own* intended rules).
_EXPECTED_DERIVED_STATUS = {
    1: "validated",
    2: "implemented",
    3: "implemented",
    4: "validated",
    5: "proposed",
    6: "validated",
    7: "proposed",
    8: "implemented",
    9: "validated",
    10: "proposed",
    11: "proposed",
    12: "proposed",
    13: "proposed",
    14: "proposed",
    15: "validated",
    16: "validated",
}

_TOUCH_FACES = (
    "touches_superior",
    "touches_inferior",
    "touches_left",
    "touches_right",
    "touches_anterior",
    "touches_posterior",
)


# =========================================================================== #
# House fixtures / helpers
# =========================================================================== #


def _manifest_cases() -> list:
    payload = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    cases = payload["cases"]
    assert cases, "expected a non-empty corpus manifest"
    return cases


def _manifest_case(case_id: str) -> dict:
    for case in _manifest_cases():
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"case_id {case_id!r} not found in the committed manifest")


@pytest.fixture(scope="module")
def corpus():
    """One measurement pass per committed corpus case: a callable
    ``get(case_id) -> (detection, findings, record)``, each case_id computed
    at most once and cached for the whole module (Testing Strategy)."""
    from segfacet.config import bundled_default_config
    from segfacet.pipeline import extract_feature_record
    from segfacet.synth.regression import (
        loaded_seg_image,
        pipeline_findings,
        reconstructed_findings,
    )

    config = bundled_default_config()
    cache: dict = {}

    def _get(case_id: str):
        if case_id in cache:
            return cache[case_id]
        case = _manifest_case(case_id)
        detection = case["detection"]
        record = extract_feature_record(loaded_seg_image(case), config)
        if detection == "pipeline":
            findings = tuple(pipeline_findings(case, config))
        elif detection == "reconstructed_record":
            findings = tuple(reconstructed_findings(case, config))
        else:
            raise AssertionError(
                f"unrecognised detection {detection!r} for case_id={case_id!r}"
            )
        cache[case_id] = (detection, findings, record)
        return cache[case_id]

    return _get


@pytest.fixture(scope="module")
def measured():
    """``segfacet.failure_modes.measured_firing`` cached per case_id (Testing
    Strategy) -- the real, public production function under test."""
    import segfacet.failure_modes as fm

    cache: dict = {}

    def _get(case):
        if case.case_id not in cache:
            cache[case.case_id] = fm.measured_firing(case)
        return cache[case.case_id]

    return _get


def _mode(fm, mode_id: int):
    mode = next((m for m in fm.iter_modes() if m.id == mode_id), None)
    assert mode is not None, mode_id
    return mode


def _case(mode, case_id: str):
    case = next((c for c in mode.corpus_cases if c.case_id == case_id), None)
    assert case is not None, (mode.id, case_id)
    return case


def _condition(fm, condition_id: str):
    condition = next(
        (c for c in fm.iter_conditions() if c.id == condition_id), None
    )
    assert condition is not None, condition_id
    return condition


def _live_declared_rule_ids(mode_id: int) -> set:
    """The rule ids the **live** registry declares for *mode_id*, recomputed
    from `iter_rule_declarations()` on every call."""
    from segfacet.heuristics.rule import iter_rule_declarations

    return {
        rule_id
        for rule_id, declaration in iter_rule_declarations()
        if declaration is not None and mode_id in declaration.modes
    }


def _ac5_edge_set_matches_registry(mode) -> bool:
    """AC5's predicate, as one function. Shared by the parametrised AC5 test
    and by the adversarial test that feeds it a deliberately-broken mode --
    otherwise the adversarial test re-implements the comparison inline and
    can pass whatever the checker does."""
    return {edge.rule_id for edge in mode.intended_rules} == _live_declared_rule_ids(mode.id)


def _ac19_names_a_sibling(mode, all_ids: set) -> bool:
    """AC19's predicate, as one function (same reason as
    :func:`_ac5_edge_set_matches_registry`)."""
    tokens = {int(token) for token in re.findall(r"\d+", mode.discriminator)}
    return bool(tokens & (all_ids - {mode.id}))


def _pick_mode_with_unique_strongest_edge(fm):
    """The first shipped mode whose derived rung comes from exactly one
    strongest edge -- picked live, never hardcoded to a particular mode id
    (AC7's precondition)."""
    for mode in fm.iter_modes():
        if not mode.intended_rules:
            continue
        strengths = [fm.EVIDENCE_RUNGS.index(e.evidence_rung) for e in mode.intended_rules]
        if strengths.count(min(strengths)) == 1:
            return mode
    return None


# =========================================================================== #
# AC1: every signed-off mode is present, and the one condition beside them
# =========================================================================== #


def test_ac1_all_signed_off_modes_present():
    """Rescoped twice: item 146 added modes 9 and 10 beside the eight seed
    entries, and the item-150 sign-off re-organised the whole catalogue and
    re-assigned ids; its 2026-09-15 revision split every paired sub-mode.
    What ``iter_modes()`` yields is now exactly the sixteen signed-off ids,
    ascending."""
    import segfacet.failure_modes as fm

    ids = tuple(mode.id for mode in fm.iter_modes())
    assert ids == _MODE_IDS
    assert ids == tuple(sorted(fm.SPECIFICATION))


def test_ac1_fov_truncation_is_a_condition_and_not_a_mode():
    """The sign-off retired failure mode 6 into a **condition**: a state of
    the case that gates other rules and is deliberately not a defect of the
    segmentation. It must appear in ``iter_conditions()`` and nowhere in
    ``iter_modes()``."""
    import segfacet.failure_modes as fm

    condition_ids = {condition.id for condition in fm.iter_conditions()}
    assert _FOV_CONDITION_ID in condition_ids, condition_ids

    condition = _condition(fm, _FOV_CONDITION_ID)
    assert condition.corpus_cases, "expected the condition to carry its fixture"
    # No mode may claim the condition's own fixture case.
    for mode in fm.iter_modes():
        assert "crop_at_border" not in {c.case_id for c in mode.corpus_cases}, mode.id


# =========================================================================== #
# AC2: every schema field is populated for every shipped entry
# =========================================================================== #


@pytest.mark.parametrize("mode_id", _MODE_IDS)
def test_ac2_every_field_populated(mode_id):
    """Re-pointed at the signed-off catalogue: ``parent`` is legitimately
    ``None`` on a top-level mode, and ``intended_rules`` / ``corpus_cases``
    are legitimately empty on a ``proposed`` entry (5, 7, 10-14), and
    ``corpus_cases`` on a specified mode with no fixture of its own (3, 8).
    ``scope`` (added 2026-09-15) must be a ``SCOPES`` member on every
    shipped entry. Those absences are the
    subject of ``test_ac2_proposed_entries_carry_no_edges_and_no_cases``
    below rather than swept under a blanket "nothing is empty", which would
    have made this test unsatisfiable rather than informative."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, mode_id)
    for field_name in (
        "name",
        "short_name",
        "definition",
        "discriminator",
        "mechanism",
        "observability",
        "severity",
        "status",
        "provenance",
    ):
        value = getattr(mode, field_name)
        assert isinstance(value, str) and value, (mode_id, field_name)
    for field_name in ("candidate_features", "intended_rules", "corpus_cases"):
        assert isinstance(getattr(mode, field_name), tuple), (mode_id, field_name)
    assert mode.candidate_features, mode_id
    assert mode.parent is None or mode.parent in fm.SPECIFICATION, mode_id
    assert mode.scope in fm.SCOPES, (mode_id, mode.scope)


def test_ac2_proposed_entries_carry_no_edges_and_no_cases():
    """``proposed`` means listed, defined, deliberately unimplemented. The
    partition is read off the authored ``status`` field, so it keeps holding
    as entries are re-authored, and the id tuple is pinned separately so a
    silently-widened ``proposed`` set is caught."""
    import segfacet.failure_modes as fm

    proposed = tuple(m.id for m in fm.iter_modes() if m.status == "proposed")
    assert proposed == _PROPOSED_MODE_IDS, proposed
    for mode_id in proposed:
        mode = _mode(fm, mode_id)
        assert mode.intended_rules == (), mode_id
        assert mode.corpus_cases == (), mode_id
    for mode in fm.iter_modes():
        if mode.status == "proposed":
            continue
        assert mode.status == "specified", (mode.id, mode.status)
        assert mode.intended_rules, mode.id


def test_ac2_condition_fields_are_populated():
    """The condition carries the same kind of authored record a mode does,
    plus the two rule lists that are its reason for existing."""
    import segfacet.failure_modes as fm

    condition = _condition(fm, _FOV_CONDITION_ID)
    for field_name in ("id", "name", "short_name", "definition", "mechanism"):
        value = getattr(condition, field_name)
        assert isinstance(value, str) and value, field_name
    assert condition.candidate_features
    assert condition.recording_rules
    assert condition.exempting_rules
    assert condition.corpus_cases


# =========================================================================== #
# AC3: every vision.md section 6 seed title is accounted for by a disposition
# =========================================================================== #


# test_ac3_every_vision_seed_title_has_a_resolving_disposition retired (item
# 152, 2026-09-16): it called `fm.vision_seed_titles()` and
# `fm.vision_seed_conflicts()`, both retired because vision.md v4's §6
# carries no numbered list left to parse. The frozen-provenance and
# every-disposition-resolves claims it made are
# `tests/test_152_retire_vision_seed.py::test_ac6_provenance_map_is_frozen_at_its_v3_value`
# and its AC7 pair.


def test_ac3_retired_seed_title_is_carried_by_no_mode():
    """The one seed title the sign-off retired ("label not aligned with the
    vertebra it names") must not survive as a mode ``name`` -- otherwise the
    disposition says retired while the catalogue still ships it."""
    import segfacet.failure_modes as fm

    retired = [
        title
        for title, disposition in fm.VISION_SEED_DISPOSITION.items()
        if disposition == "retired"
    ]
    assert retired, "expected the sign-off to have retired at least one seed title"
    names = {mode.name for mode in fm.iter_modes()}
    for title in retired:
        assert title not in names, title


# =========================================================================== #
# AC4: the Stage-18 metric anchor path is carried, and only as that
# =========================================================================== #


@pytest.mark.parametrize("mode_id", _MODE_IDS)
def test_ac4_stage18_anchor_paths_carried_and_only_that(mode_id):
    """Re-pointed: since the item-150 sign-off only some modes are anchored
    in a Stage-18 metric, so ``MODE_ANCHOR_PATHS`` is keyed by a subset of
    the ids and a missing key means "no anchor", not a failure. The claim
    that survives is the exact agreement of the two sides, in both
    directions -- a mode carries anchor-role features iff it is a key, and
    the paths match."""
    import segfacet.failure_modes as fm
    import segfacet.feature_docs as feature_docs

    mode = _mode(fm, mode_id)
    anchor_paths = {
        feature.path
        for feature in mode.candidate_features
        if feature.role == "stage18-metric-anchor"
    }
    assert anchor_paths == set(feature_docs.MODE_ANCHOR_PATHS.get(mode_id, ()))


def test_ac4_mode_anchor_paths_keys_are_all_shipped_modes():
    """The other direction, once: no ``MODE_ANCHOR_PATHS`` key may name a
    mode id the catalogue does not carry (the sign-off re-assigned ids, so
    a stale key is exactly the drift this catches), and at least one mode
    is anchored -- otherwise the parametrised test above passes vacuously
    on sixteen empty sets."""
    import segfacet.failure_modes as fm
    import segfacet.feature_docs as feature_docs

    assert feature_docs.MODE_ANCHOR_PATHS, "expected a non-empty anchor map"
    assert set(feature_docs.MODE_ANCHOR_PATHS) <= set(fm.SPECIFICATION), (
        sorted(set(feature_docs.MODE_ANCHOR_PATHS) - set(fm.SPECIFICATION))
    )


def test_ac4_condition_anchor_paths_are_the_conditions_own_features():
    """The condition's Stage-18 anchor lives in its own map
    (``CONDITION_ANCHOR_PATHS``), and every path there must be one the
    condition itself lists."""
    import segfacet.failure_modes as fm
    import segfacet.feature_docs as feature_docs

    anchors = feature_docs.CONDITION_ANCHOR_PATHS
    assert anchors, "expected a non-empty condition anchor map"
    assert set(anchors) <= {c.id for c in fm.iter_conditions()}, sorted(anchors)
    for condition_id, paths in sorted(anchors.items()):
        condition = _condition(fm, condition_id)
        assert paths, condition_id
        for path in paths:
            assert path in condition.candidate_features, (condition_id, path)


# =========================================================================== #
# AC5: the edge set equals what the live registry declares
# =========================================================================== #


@pytest.mark.parametrize("mode_id", _MODE_IDS)
def test_ac5_edge_set_equals_live_registry_declared_set(mode_id):
    """Unchanged in substance. The one reconciliation the sign-off forces:
    a ``proposed`` entry has an empty edge set *and* an empty declared set,
    so the "at least one registered rule declares it" precondition now
    applies to the specified entries only -- and is asserted for them, so
    the equality is never satisfied by two empty sets where it should not
    be."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, mode_id)
    declared = _live_declared_rule_ids(mode_id)
    if mode_id in _PROPOSED_MODE_IDS:
        assert declared == set(), (mode_id, declared)
    else:
        assert declared, f"expected >=1 registered rule to declare mode {mode_id}"
    assert _ac5_edge_set_matches_registry(mode), (
        mode_id,
        {edge.rule_id for edge in mode.intended_rules},
        declared,
    )


def test_ac5_fov_truncation_is_recorded_by_border_which_declares_no_mode():
    """Re-targeted from "mode 6's edge set is exactly {border}". The
    sign-off made ``border`` **mode-less**: it records the FOV-truncation
    condition and declares no failure mode at all, carrying a
    ``mode_less_reason`` in place of ``modes``. So the claim moves from a
    mode's ``intended_rules`` to the condition's ``recording_rules``, and
    gains its complement -- ``border`` appears in no mode's edge set."""
    import segfacet.failure_modes as fm
    from segfacet.heuristics.rule import iter_rule_declarations

    condition = _condition(fm, _FOV_CONDITION_ID)
    assert condition.recording_rules == ("border",), condition.recording_rules
    assert "mislabel" not in condition.recording_rules

    declarations = dict(iter_rule_declarations())
    border = declarations["border"]
    assert border is not None, "expected border to carry a RuleModeDeclaration"
    assert border.modes == (), border.modes
    assert border.mode_less_reason.strip(), border

    for mode in fm.iter_modes():
        assert "border" not in {edge.rule_id for edge in mode.intended_rules}, mode.id


def test_ac5_condition_exempting_rules_are_registered_and_distinct():
    """The exemptions the condition grants are rules that exist, and are not
    the rule that records it -- otherwise "recording" and "exempting" would
    be one undifferentiated list."""
    import segfacet.failure_modes as fm
    from segfacet.heuristics.rule import iter_rule_declarations

    condition = _condition(fm, _FOV_CONDITION_ID)
    registered = {rule_id for rule_id, _declaration in iter_rule_declarations()}
    assert condition.exempting_rules, condition.id
    for rule_id in condition.recording_rules + condition.exempting_rules:
        assert rule_id in registered, (rule_id, sorted(registered))
    assert not set(condition.recording_rules) & set(condition.exempting_rules)


# =========================================================================== #
# AC6: every mode's rung is the strongest of its own edges
# =========================================================================== #


@pytest.mark.parametrize("mode_id", _MODE_IDS)
def test_ac6_mode_rung_is_the_strongest_of_its_own_edges(mode_id):
    """Unchanged in substance; a ``proposed`` entry has no edge at all, and
    ``derive_mode_rung`` returns ``None`` for it rather than computing a
    ``min()`` over the empty set."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, mode_id)
    if not mode.intended_rules:
        assert mode_id in _PROPOSED_MODE_IDS, mode_id
        assert fm.derive_mode_rung(mode) is None
        return
    strongest = min(
        (edge.evidence_rung for edge in mode.intended_rules),
        key=lambda rung: fm.EVIDENCE_RUNGS.index(rung),
    )
    assert fm.derive_mode_rung(mode) == strongest


# =========================================================================== #
# AC7: a deliberately weakened edge rung changes the derived mode rung
# =========================================================================== #


def test_ac7_weakening_the_single_strongest_edge_changes_derived_rung():
    import segfacet.failure_modes as fm

    mode = _pick_mode_with_unique_strongest_edge(fm)
    assert mode is not None, "expected >=1 shipped mode with a unique strongest edge"
    before = fm.derive_mode_rung(mode)

    edges = mode.intended_rules
    strengths = [fm.EVIDENCE_RUNGS.index(e.evidence_rung) for e in edges]
    strongest_index = strengths.index(min(strengths))
    weaker_rung = fm.EVIDENCE_RUNGS[strengths[strongest_index] + 1]

    weakened_edges = tuple(
        dataclasses.replace(edge, evidence_rung=weaker_rung) if i == strongest_index else edge
        for i, edge in enumerate(edges)
    )
    weakened_copy = dataclasses.replace(mode, intended_rules=weakened_edges)

    after = fm.derive_mode_rung(weakened_copy)
    assert after != before, (before, after)
    assert after == weaker_rung

    # The shipped SPECIFICATION entry itself is never mutated.
    shipped_again = fm.SPECIFICATION[mode.id]
    assert fm.derive_mode_rung(shipped_again) == before


# =========================================================================== #
# AC8: every synthetic-demonstrable edge is actually demonstrated
# =========================================================================== #


def test_ac8_every_synthetic_demonstrable_edge_is_demonstrated(measured):
    """Rescoped (item 146, 2026-09-03): resolves each case through
    ``_manifest_case``, which reads the **geometric** manifest and would
    raise on the intensity cases -- so only the modes whose cases live in
    that manifest are iterated (``_GEOMETRIC_CORPUS_MODE_IDS``; the
    intensity mode's own equivalent is item 146's AC20)."""
    import segfacet.failure_modes as fm

    checked = False
    for mode in fm.iter_modes():
        if mode.id not in _GEOMETRIC_CORPUS_MODE_IDS:
            continue
        pipeline_cases = [
            case
            for case in mode.corpus_cases
            if _manifest_case(case.case_id)["detection"] == "pipeline"
        ]
        for edge in mode.intended_rules:
            if edge.evidence_rung != "synthetic-demonstrable":
                continue
            checked = True
            fired = set()
            for case in pipeline_cases:
                fired |= set(measured(case))
            assert edge.rule_id in fired, (mode.id, edge.rule_id, fired)
    assert checked, "expected >=1 synthetic-demonstrable edge in the specification"


# =========================================================================== #
# AC9: the three analytic-only edges are needs-real-data and undemonstrated
# =========================================================================== #


def test_ac9_the_three_analytic_only_edges_are_needs_real_data_and_undemonstrated(measured):
    import segfacet.failure_modes as fm

    targets = {(1, "reference_delta"), (2, "reference_delta"), (2, "bounds")}
    seen = set()
    for mode in fm.iter_modes():
        for edge in mode.intended_rules:
            key = (mode.id, edge.rule_id)
            if key not in targets:
                continue
            seen.add(key)
            assert edge.evidence_rung == "needs-real-data", key
            fired = set()
            for case in mode.corpus_cases:
                fired |= set(measured(case))
            assert edge.rule_id not in fired, (key, fired)
    assert seen == targets, seen


# =========================================================================== #
# AC10a/AC10b: the `sequence` edge's divergence -- needs-real-data rung on
# an edge whose own corpus case measurably fires. Re-homed by the item-150
# sign-off from mode 7 onto the label-sequence mode -- since the 2026-09-15
# revision mode 9 ("out-of-order label sequence"); "shifted label sequence"
# is mode 12, a `proposed` entry with no rule at all.
# =========================================================================== #


def test_ac10a_sequence_edge_is_needs_real_data_while_its_case_measurably_fires(measured):
    """The divergence is a property of the **edge**, and it survives the
    re-homing intact: ``sequence`` sits at ``needs-real-data`` although
    ``sequence_break`` demonstrably fires it, because a multi-relabel
    scramble is not expressible by the fixture generator.

    What no longer follows is the mode-level assertion this test also made:
    mode 9 carries a ``synthetic-demonstrable`` edge (``mislabel``'s
    ordering detector) beside this one, so its derived rung is the stronger
    of the two, not this edge's. That is asserted here rather than dropped,
    so the divergence stays visible.
    """
    import segfacet.failure_modes as fm

    mode = _mode(fm, 9)
    sequence_edges = [edge for edge in mode.intended_rules if edge.rule_id == "sequence"]
    assert len(sequence_edges) == 1, mode.intended_rules
    assert sequence_edges[0].evidence_rung == "needs-real-data"
    assert fm.derive_mode_rung(mode) == "synthetic-demonstrable"

    case = _case(mode, "sequence_break")
    assert "sequence" in measured(case)


def test_ac10a_shifted_label_sequence_mode_is_proposed_with_no_rule(measured):
    """The shifted-label-sequence mode (12 since the 2026-09-15 revision): a
    whole-sequence offset is internally valid, so no label-map rule can fire
    on it -- the entry is ``proposed``, observability
    ``needs-external-classifier``, with no edge, no case and no declaring
    rule."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, 12)
    assert mode.name == "Shifted label sequence", mode.name
    assert mode.status == "proposed"
    assert fm.derive_status(mode) == "proposed"
    assert mode.observability == "needs-external-classifier"
    assert mode.intended_rules == ()
    assert mode.corpus_cases == ()
    assert _live_declared_rule_ids(12) == set()


def test_ac10b_sequence_case_records_the_single_rank_descent_correction():
    """Reconciled (item 147, 2026-09-04): the false claim this test pinned
    (``rank(v) == v - 1`` as a general per-pair cap) is corrected in
    ``SPECIFICATION[7].mechanism`` -- item 147's own AC10 test recomputes
    the corrected claim live from ``segfacet.labels.CANONICAL_ORDER`` /
    ``DEFAULT_LABEL_MAP``. What survives here is the narrower, still-true
    assertion: the corrected sentence lives in ``mechanism`` (not
    ``case.reason``, which now carries only the measured detection fact),
    names the live tokens this item's mechanism must resolve against, and
    the retired false claim is gone from both fields."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, 9)
    case = _case(mode, "sequence_break")
    assert case.reason.strip()
    assert "rank(v) == v - 1" not in case.reason, case.reason

    mechanism = mode.mechanism
    assert mechanism.strip()
    assert "rank(v) == v - 1" not in mechanism, mechanism
    for token in ("CANONICAL_ORDER", "T13"):
        assert token in mechanism, (token, mechanism)
    lowered = mechanism.lower()
    # The levels the corrected sentence has to resolve against: T13 is
    # ranked between T12 and L1, which is what makes the relabel a single
    # rank descent. ("l5" was in this list while the sentence also carried
    # vision §6's "L1 -> T12 -> L2 -> L5" example; the sign-off's mechanism
    # names the three corpus cases' own levels instead.)
    for token in ("t12", "l1", "l2"):
        assert token in lowered, (token, mechanism)


# =========================================================================== #
# AC11/AC12: the overlapping-segments mode's structural unobservability holds
# live. Re-numbered from 8 to 9 by the item-150 sign-off and to 15 by its
# 2026-09-15 revision; the corpus case id
# `force_overlap` is unchanged (the `modeN_` prefixes are historical).
# =========================================================================== #


def test_ac11_overlap_mode_structural_unobservability_holds_live():
    import segfacet.failure_modes as fm
    from segfacet.synth.regression import pipeline_findings, reconstructed_findings

    mode = _mode(fm, 15)
    assert fm.derive_mode_rung(mode) == "structurally-unobservable"

    case = _manifest_case("force_overlap")
    assert case["detection"] == "reconstructed_record"

    plain = pipeline_findings(case)
    assert not any(f.rule_id == "overlap" for f in plain), plain

    reconstructed = reconstructed_findings(case)
    assert reconstructed, "expected >=1 finding from the reconstructed record"
    reconstructed_ids = tuple(sorted({f.rule_id for f in reconstructed}))
    assert reconstructed_ids == ("overlap",), reconstructed_ids


def test_ac12_overlap_mode_records_the_single_channel_mechanism():
    import segfacet.failure_modes as fm

    mode = _mode(fm, 15)
    case = _case(mode, "force_overlap")
    assert case.reason.strip()
    lowered = case.reason.lower()
    assert "single" in lowered and "channel" in lowered, case.reason
    assert "voxel" in lowered, case.reason
    assert "one label" in lowered or "exactly one" in lowered, case.reason
    assert "overlap" in lowered, case.reason


# =========================================================================== #
# AC13: every expected firing set equals a fresh measurement
# =========================================================================== #


def test_ac13_every_expected_firing_equals_a_fresh_measurement(measured):
    """Every authored ``expected_firing`` set, on every mode **and** on the
    condition, equals a fresh drive of the committed corpus.

    Two reconciliations the item-150 sign-off forces, both narrowing rather
    than relaxing what is checked:

    * ``assert got`` is gone as a blanket precondition. ``remove_level_relabel``
      is authored with an **empty** expected set on purpose -- it records "not
      detected today" for the hypothesised spacing-gap signal -- so requiring
      a non-empty measurement would assert the opposite of what the entry
      says. The empty-expected cases are instead asserted to measure nothing,
      and at least one is required to exist, so the case class stays covered.
    * "every mode derives validated" moves to
      ``test_ac13_derived_status_is_the_signed_off_ladder`` below. Under the
      sign-off's semantics an agreeing case validates only if it fires one of
      the mode's **own** intended rules, so a co-detection (mode 2) agrees
      without validating, and an empty set (``remove_level_relabel`` on
      mode 6) validates nothing on its own.

    The floor is the thirteen committed corpus cases the 2026-09-15
    catalogue carries (ten geometric, the condition's among them, and three
    intensity); several specified and every proposed mode carries none, so
    "one case per mode id" is no longer the floor.
    """
    import segfacet.failure_modes as fm

    checked_cases = 0
    empty_expected = 0
    for owner in list(fm.iter_modes()) + list(fm.iter_conditions()):
        for case in owner.corpus_cases:
            checked_cases += 1
            got = set(measured(case))
            assert set(case.expected_firing) == got, (owner.id, case.case_id, got)
            assert fm.case_agrees(case) is True, (owner.id, case.case_id)
            if not case.expected_firing:
                empty_expected += 1
                assert got == set(), (owner.id, case.case_id, got)
    assert checked_cases >= 13, checked_cases
    assert empty_expected >= 1, "expected >=1 'not detected today' corpus case"


def test_ac13_derived_status_is_the_signed_off_ladder():
    """The lifecycle each entry derives from live state, pinned as the
    sign-off left it. ``"validated"`` needs a declaring rule, every corpus
    case agreeing, **and** at least one case with a non-empty expected set
    naming one of the mode's own intended rules -- which is why fused (2,
    co-detections only) and the proxy-only modes with no case (3, 8) sit at
    ``"implemented"`` while every case they carry agrees perfectly, and why
    vertebra not segmented (6) validates on ``remove_level``'s
    ``coverage`` finding despite also carrying the empty "not detected today"
    ``remove_level_relabel`` case."""
    import segfacet.failure_modes as fm

    derived = {mode.id: fm.derive_status(mode) for mode in fm.iter_modes()}
    assert derived == _EXPECTED_DERIVED_STATUS, derived
    # Not a single-valued map: the pin above would be far weaker if every
    # entry derived the same thing.
    assert len(set(derived.values())) >= 3, derived


def test_ac13_co_detection_alone_does_not_validate():
    """The mechanism behind mode 2's ``"implemented"``: its one corpus case
    (``fuse_adjacent``) agrees exactly, but everything it fires belongs to
    another mode's detector (mode 1's fragmentation, mode 6's coverage).
    Re-pointed from mode 1, which the 2026-09-15 revision made validated by
    homing ``fragment`` there. Asserted through the production
    derivation, with the disjointness recomputed rather than transcribed."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, 2)
    assert mode.corpus_cases
    own_rules = {edge.rule_id for edge in mode.intended_rules}
    assert own_rules, mode.id
    for case in mode.corpus_cases:
        assert fm.case_agrees(case) is True, case.case_id
        assert not own_rules & set(case.expected_firing), (case.case_id, own_rules)
    assert fm.derive_status(mode) == "implemented"


# =========================================================================== #
# AC14: crop_at_border expects {border, mislabel} with a reason.
# Re-homed by the item-150 sign-off: the case belongs to the fov_truncation
# CONDITION, not to a failure mode. The expectation itself is unchanged.
# =========================================================================== #


def test_ac14_fov_truncation_case_expects_border_and_mislabel_with_reason():
    import segfacet.failure_modes as fm

    condition = _condition(fm, _FOV_CONDITION_ID)
    case = _case(condition, "crop_at_border")
    assert case.expected_firing == ("border", "mislabel")
    assert case.reason.strip()
    lowered = case.reason.lower()
    assert "crop" in lowered or "border" in lowered, case.reason
    assert "centroid" in lowered, case.reason
    assert "curve" in lowered or "spline" in lowered, case.reason
    # `mislabel` co-fires but records nothing about this condition: it is one
    # of the rules the condition *exempts*, never one that records it.
    assert "mislabel" not in condition.recording_rules
    assert "mislabel" in condition.exempting_rules


def test_ac14_condition_case_is_carried_by_the_manifest_as_a_condition():
    """The manifest side of the re-homing: the case carries
    ``failure_mode == 0`` (no mode) **and** a non-empty ``condition``, which
    is what tells the conformance check to compare it against a
    ``ConditionSpec`` instead of treating it as a clean control."""
    import segfacet.failure_modes as fm

    case = _manifest_case("crop_at_border")
    assert case["failure_mode"] == 0, case
    assert case["condition"] == _FOV_CONDITION_ID, case
    assert case["expected_rule_ids"], case

    condition = _condition(fm, _FOV_CONDITION_ID)
    expectation = _case(condition, "crop_at_border")
    assert set(case["expected_rule_ids"]) <= set(expectation.expected_firing)

    # Every other manifest case names no condition, so the key is a real
    # discriminator rather than a field that is always set.
    conditioned = [c["case_id"] for c in _manifest_cases() if c.get("condition")]
    assert conditioned == ["crop_at_border"], conditioned


# =========================================================================== #
# AC15: the condition's displacement claim is a live measurement, not prose
# =========================================================================== #


def test_ac15_fov_truncation_displacement_claim_holds_live(corpus):
    """Re-targeted at the ``fov_truncation`` condition.

    The authored reason used to quote a displacement in millimetres, and
    this test recomputed that number and compared it. The sign-off's reason
    states the *causal* claim instead ("the crop displaces the centroid off
    the fitted spinal curve") and quotes no figure, so there is no number
    left to compare -- and asserting on a number the record no longer
    carries would be asserting on nothing.

    What is checked instead is the claim itself, end to end and entirely
    from live measurement: the single label ``border`` names is the same
    label that carries a non-terminal, strictly positive spline offset, and
    that same label is the one ``mislabel``'s co-detection names. If the
    crop stopped displacing the centroid, or displaced a different label's,
    this fails.
    """
    import segfacet.failure_modes as fm

    condition = _condition(fm, _FOV_CONDITION_ID)
    case = _case(condition, "crop_at_border")
    assert set(case.expected_firing) == {"border", "mislabel"}

    _detection, findings, record = corpus("crop_at_border")
    border_findings = [f for f in findings if f.rule_id == "border"]
    assert border_findings, "expected >=1 border finding on crop_at_border"
    labels = set()
    for finding in border_findings:
        labels |= set(finding.labels)
    assert len(labels) == 1, labels
    label = next(iter(labels))

    stage3 = record.get("stage3")
    assert stage3, "expected a non-empty stage3 block on a multi-label fixture"
    offsets = stage3.get("per_label_offsets")
    assert offsets, "expected a non-empty stage3.per_label_offsets[] block"
    matching = [o for o in offsets if o["label"] == label and not o.get("is_terminal")]
    assert matching, (label, offsets)
    measured_offset = matching[0]["offset_mm"]
    assert measured_offset > 0.0, (label, measured_offset)

    # The other label offsets on the same case are all smaller: the crop is
    # what displaced this one, not a property of the fixture's whole spline.
    others = [
        entry["offset_mm"]
        for entry in offsets
        if entry["label"] != label and not entry.get("is_terminal")
    ]
    assert others, offsets
    assert measured_offset > max(others), (measured_offset, others)

    mislabel_findings = [f for f in findings if f.rule_id == "mislabel"]
    assert mislabel_findings, "expected mislabel to co-fire on the condition's case"
    assert any(label in set(f.labels) for f in mislabel_findings), (
        label,
        [f.labels for f in mislabel_findings],
    )

    # The condition's own mechanism names the exempting seam this rests on.
    assert "is_terminal" in condition.mechanism, condition.mechanism


# =========================================================================== #
# AC16: the accuracy / FOV-truncation discriminator holds on the corpus.
# Renamed for the item-150 sign-off: the second side is no longer mode 6 but
# the `fov_truncation` condition. The fixtures and the claim are unchanged --
# "the missing part lies beyond an image face" is exactly what separates them.
# =========================================================================== #


def test_ac16_accuracy_vs_fov_truncation_discriminator_holds_on_corpus(corpus):
    _detection6, _findings6, mode6_record = corpus("crop_at_border")
    mode6_touches = any(
        entry["geometry"][face]
        for entry in mode6_record["per_label"].values()
        for face in _TOUCH_FACES
    )
    assert mode6_touches is True

    _detection1, _findings1, mode1_record = corpus("displace")
    mode1_touches = any(
        entry["geometry"][face]
        for entry in mode1_record["per_label"].values()
        for face in _TOUCH_FACES
    )
    assert mode1_touches is False


# =========================================================================== #
# AC17: the fragment / island discriminator holds on the corpus. Since the
# 2026-09-15 revision the two fixtures sit in different modes again:
# `fragment` (a vertebra cut into large same-label pieces) at the
# parent, mode 1, and `inject_islands` at mode 4 (islands) -- mode 4's
# discriminator sends "the vertebra itself cut into large same-label pieces"
# to mode 1. The component-fraction split below is what separates them.
# =========================================================================== #


def test_ac17_fragment_vs_island_discriminator_holds_on_corpus(corpus):
    mode3_case = _manifest_case("inject_islands")
    mode3_labels = mode3_case["expected_labels"]
    assert mode3_labels, mode3_case
    mode3_label = str(mode3_labels[0])
    _detection3, _findings3, mode3_record = corpus("inject_islands")
    fraction3 = mode3_record["per_label"][mode3_label]["components"]["largest_component_fraction"]
    assert fraction3 >= 0.9, fraction3

    mode2_case = _manifest_case("fragment")
    mode2_labels = mode2_case["expected_labels"]
    assert mode2_labels, mode2_case
    mode2_label = str(mode2_labels[0])
    _detection2, _findings2, mode2_record = corpus("fragment")
    fraction2 = mode2_record["per_label"][mode2_label]["components"]["largest_component_fraction"]
    assert fraction2 <= 0.6, fraction2


# =========================================================================== #
# AC18: the two `mislabel` detectors are told apart by their leading tag.
# The sign-off split them across the catalogue: the spline-offset detector
# (`displace`) serves NO failure mode -- a spline offset is an
# anatomy-classification signal -- while the ordering detector
# (`relabel_swap`) serves mode 9. Distinguishing them therefore matters
# more after the sign-off, not less.
# =========================================================================== #


def test_ac18_mislabel_detector_leading_tags_differ(corpus):
    from segfacet.heuristics.mislabel import _MISALIGN_TAG, _MISLABEL_TAG

    assert _MISALIGN_TAG != _MISLABEL_TAG

    _detection1, findings1, _record1 = corpus("displace")
    mode1_mislabel = [f for f in findings1 if f.rule_id == "mislabel"]
    assert mode1_mislabel, "expected mislabel to fire on displace"

    _detection4, findings4, _record4 = corpus("relabel_swap")
    mode4_mislabel = [f for f in findings4 if f.rule_id == "mislabel"]
    assert mode4_mislabel, "expected mislabel to fire on relabel_swap"

    assert any(f.reason.startswith(_MISALIGN_TAG) for f in mode1_mislabel), [
        f.reason for f in mode1_mislabel
    ]
    assert any(f.reason.startswith(_MISLABEL_TAG) for f in mode4_mislabel), [
        f.reason for f in mode4_mislabel
    ]
    assert not any(f.reason.startswith(_MISLABEL_TAG) for f in mode1_mislabel), [
        f.reason for f in mode1_mislabel
    ]
    assert not any(f.reason.startswith(_MISALIGN_TAG) for f in mode4_mislabel), [
        f.reason for f in mode4_mislabel
    ]

    # The catalogue side of the same split: the ordering detector is mode 9's
    # declared detector, and no mode declares the spline-offset one.
    import segfacet.failure_modes as fm

    mislabel_edges = [
        edge
        for mode in fm.iter_modes()
        for edge in mode.intended_rules
        if edge.rule_id == "mislabel"
    ]
    assert len(mislabel_edges) == 1, mislabel_edges
    assert mislabel_edges[0].detector_ids == ("ordering",), mislabel_edges[0].detector_ids
    assert "spline_offset" not in mislabel_edges[0].detector_ids


# =========================================================================== #
# AC19: every discriminator names at least one sibling mode
# =========================================================================== #


def test_ac19_every_discriminator_names_a_sibling_mode():
    import segfacet.failure_modes as fm

    all_ids = {mode.id for mode in fm.iter_modes()}
    assert all_ids, "expected >=1 mode"
    for mode in fm.iter_modes():
        assert _ac19_names_a_sibling(mode, all_ids), (mode.id, mode.discriminator)


@pytest.mark.parametrize(
    "mode_id, sibling_id",
    # Re-derived against the 2026-09-15 tree: every split sub-mode names its
    # converse, so the set is a pin on the new discriminators rather than a
    # carry-over of the old ids.
    [
        (1, 2),   # accuracy catch-all vs fused segments
        (2, 3),   # fused vs its converse, split
        (3, 2),   # and back
        (4, 5),   # islands vs its topological converse, holes
        (5, 4),   # and back
        (6, 7),   # not segmented vs its converse, hallucinated
        (7, 6),   # and back
        (8, 9),   # identity catch-all vs an out-of-order sequence
        (9, 10),  # out of order vs a skipped level label
        (10, 6),  # a skipped label vs the unsegmented vertebra (spatial gap)
        (10, 9),  # a skipped label vs levels out of order
        (10, 12), # a skipped label vs a gapless whole-sequence offset
        (10, 2),  # a skipped label vs the level absorbed by a neighbour
        (10, 8),  # it always contains a mode-8 mislabelling
        (11, 9),  # numbering variant vs a variant that breaks order
        (12, 8),  # whole-sequence shift vs only some labels wrong
        (13, 14), # collapsed vs its converse, duplicated
        (14, 13), # and back
        (15, 14), # overlap needs a second label's mask, unlike modes 1-14
        (16, 15), # needs the paired scan, unlike modes 1-15
    ],
)
def test_ac19_named_discriminator_pairs(mode_id, sibling_id):
    import segfacet.failure_modes as fm

    mode = _mode(fm, mode_id)
    tokens = {int(t) for t in re.findall(r"\d+", mode.discriminator)}
    assert sibling_id in tokens, (mode_id, mode.discriminator)


# =========================================================================== #
# AC20: detector names the detector that actually fired
# =========================================================================== #


def test_ac20_detector_names_the_detector_that_actually_fired(corpus):
    """Rescoped (item 146): the ``corpus`` fixture reads the **geometric**
    manifest and would raise on the intensity cases, so only the modes whose
    cases live there are iterated.

    Reconciled for item 164: ``detector`` was a prose string naming several
    detectors of one rule separated by ``" / "``; ``detector_ids`` is the
    tuple that replaces it, so the fired detector is found by membership
    rather than a prefix join.

    "an edge that fired nothing carries an empty detector" is no longer
    true in that direction: an edge may name detectors that fire on none
    of its mode's cases (mode 6's ``coverage`` edge also names the opt-in
    span/count detectors, which ship **disabled**). The contrapositive is what survives and is asserted -- an edge
    whose ``detector_ids`` is empty fired nothing -- which still catches an
    unnamed detector that does fire.
    """
    import segfacet.failure_modes as fm

    checked_fired = 0
    checked_unfired = 0
    for mode in fm.iter_modes():
        if mode.id not in _GEOMETRIC_CORPUS_MODE_IDS:
            continue
        fired_findings = []
        for case in mode.corpus_cases:
            _detection, findings, _record = corpus(case.case_id)
            fired_findings.extend(findings)
        fired_rule_ids = {f.rule_id for f in fired_findings}
        for edge in mode.intended_rules:
            if edge.rule_id in fired_rule_ids:
                checked_fired += 1
                assert edge.detector_ids, (mode.id, edge.rule_id)
                matching = [f for f in fired_findings if f.rule_id == edge.rule_id]
                assert any(
                    f.detector_id in edge.detector_ids for f in matching
                ), (
                    mode.id,
                    edge.rule_id,
                    edge.detector_ids,
                    [f.reason for f in matching],
                )
            else:
                # A named-but-unfired detector is legitimate since the
                # sign-off (an edge may name opt-in checks that ship
                # disabled), so nothing is asserted about the
                # name here -- the surviving direction is its own test,
                # `test_ac20_an_empty_detector_never_belongs_to_a_rule_that_fired`.
                checked_unfired += 1
    assert checked_fired, "expected >=1 edge whose rule_id fired on its own mode's case"
    assert checked_unfired, "expected >=1 analytic-only edge that fired nothing"


def test_ac20_no_edge_is_authored_without_a_detector_id():
    """Reconciled for item 164 (2026-09-20). Retires the premise of the
    predecessor this replaces (``test_ac20_an_empty_detector_never_belongs_to_a_rule_that_fired``):
    step 7 of item 164 gives each of the ten ``detector=""`` edges its rule's
    full detector set, so no edge is left with an empty ``detector_ids`` and
    a corpus-driven "checked >= 1" guard would reach zero. See AC5/AC7."""
    import segfacet.failure_modes as fm

    checked = 0
    for mode in fm.iter_modes():
        if mode.id not in _GEOMETRIC_CORPUS_MODE_IDS:
            continue
        for edge in mode.intended_rules:
            assert edge.detector_ids, (mode.id, edge.rule_id)
            checked += 1
    assert checked, "expected >=1 intended-rule edge across the geometric-corpus modes"


# =========================================================================== #
# AC21: severity is grounded in what the mode's case measurably produces
# =========================================================================== #


def test_ac21_severity_is_never_below_what_the_modes_own_rules_produce(corpus):
    """Rescoped (item 146): geometric-corpus modes only, as above.

    Reconciled for the item-150 sign-off. "The authored severity is one the
    mode's own rules measurably produce" no longer holds in that exact form,
    for two reasons the sign-off created deliberately:

    * Mode 2 carries a corpus case on which its own intended rules
      (``bounds`` / ``reference_delta``) fire on **nothing**, so there is no
      measured severity to be a member of.
    * Mode 9 is authored ``fail`` -- "an out-of-order sequence means at
      least one label is certainly wrong and should fail the case" -- while
      its two detectors currently raise ``flagged-for-review``. That is
      the sign-off's intent running ahead of the rules, and it is pinned
      explicitly by ``test_ac21_sequence_mode_severity_leads_its_rules``.

    What replaces equality is the ordering claim, which is the one that
    actually protects the catalogue: a mode's authored severity is never
    *below* what its own rules measurably raise. Authoring
    ``flagged-for-review`` on a mode whose rules fail the case still fails
    here.
    """
    import segfacet.failure_modes as fm
    from segfacet.verdict import Severity

    by_label = {severity.label: severity for severity in Severity}
    checked = 0
    for mode in fm.iter_modes():
        if mode.id not in _GEOMETRIC_CORPUS_MODE_IDS:
            continue
        rule_ids = {edge.rule_id for edge in mode.intended_rules}
        measured_severities = set()
        for case in mode.corpus_cases:
            _detection, findings, _record = corpus(case.case_id)
            measured_severities |= {
                f.severity for f in findings if f.rule_id in rule_ids
            }
        if not measured_severities:
            # A mode whose own rules fire on nothing in the corpus: nothing
            # to compare, and its emptiness is the subject of AC9.
            continue
        checked += 1
        authored = by_label[mode.severity]
        assert authored >= max(measured_severities), (
            mode.id,
            mode.severity,
            sorted(s.label for s in measured_severities),
        )
    assert checked, "expected >=1 mode whose own rules fire on its own corpus case"


def test_ac21_sequence_mode_severity_leads_its_rules(corpus):
    """The deliberate divergence, pinned so it cannot drift silently in
    either direction: exactly two entries are authored ``fail`` -- mode 9
    (out-of-order label sequence) and mode 10 (skipped level label, which
    "always contains at least one mode-8 mislabelling, so it fails like mode
    9"). For mode 9, every finding its own rules raise today is
    ``flagged-for-review``; if a rule is escalated to fail, or the mode is
    re-authored down, this test is the one that says so. Mode 10 is
    ``proposed`` with no rule and no case, so its severity leads *no*
    measurement at all: that is asserted as such (no edge, no case, no
    declaring rule) rather than passed by comparing an empty set."""
    import segfacet.failure_modes as fm

    failing = [mode.id for mode in fm.iter_modes() if mode.severity == "fail"]
    assert failing == [9, 10], failing

    mode = _mode(fm, 9)
    rule_ids = {edge.rule_id for edge in mode.intended_rules}
    assert rule_ids, mode.id
    measured_severities = set()
    for case in mode.corpus_cases:
        _detection, findings, _record = corpus(case.case_id)
        measured_severities |= {
            f.severity.label for f in findings if f.rule_id in rule_ids
        }
    assert measured_severities == {"flagged-for-review"}, measured_severities

    skipped = _mode(fm, 10)
    assert skipped.status == "proposed", skipped.status
    assert skipped.intended_rules == (), skipped.intended_rules
    assert skipped.corpus_cases == (), skipped.corpus_cases
    assert _live_declared_rule_ids(10) == set()


# =========================================================================== #
# AC22: implemented derives on "a registered rule whose modes contains id"
# =========================================================================== #


@pytest.mark.parametrize("mode_id", _MODE_IDS)
def test_ac22_implemented_derives_on_registered_rule_containment(mode_id):
    """With its corpus cases stripped, every mode a registered rule declares
    falls back to exactly ``"implemented"`` -- the containment reading,
    unchanged. A ``proposed`` entry has no declaring rule, so it falls back
    to its authored status instead; the expected value is pinned per id
    rather than recomputed from ``_live_declared_rule_ids``, which would
    re-implement the function under test."""
    import segfacet.failure_modes as fm

    expected = "proposed" if mode_id in _PROPOSED_MODE_IDS else "implemented"
    mode = _mode(fm, mode_id)
    probe = dataclasses.replace(mode, corpus_cases=())
    assert fm.derive_status(probe) == expected


# =========================================================================== #
# AC23: both generated artifacts carry every signed-off mode and are
# byte-reproducible (run-to-run); fresh matches committed structurally
# =========================================================================== #


def test_ac23_regeneration_is_byte_reproducible_run_to_run(tmp_path):
    import segfacet.failure_modes as fm

    json_a, md_a = tmp_path / "a.json", tmp_path / "a.md"
    json_b, md_b = tmp_path / "b.json", tmp_path / "b.md"

    fm.main(["--json", str(json_a), "--md", str(md_a)])
    fm.main(["--json", str(json_b), "--md", str(md_b)])

    bytes_a_json, bytes_b_json = json_a.read_bytes(), json_b.read_bytes()
    bytes_a_md, bytes_b_md = md_a.read_bytes(), md_b.read_bytes()
    assert bytes_a_json, "expected non-empty JSON"
    assert bytes_a_md, "expected non-empty markdown"
    assert bytes_a_json == bytes_b_json
    assert bytes_a_md == bytes_b_md


def test_ac23_fresh_matches_committed_structurally_and_carries_every_signed_off_id():
    """Reconciled (item 149, 2026-09-04): an ``ALLOWLIST`` ground
    (``"no-float-leaf"``) now exists for these two committed paths, added in
    ``tests/committed_artifact_guard.py`` directly. This test's own
    fresh-vs-committed comparison is unchanged by that -- it still compares
    structurally rather than via ``read_bytes()``, the same pattern item
    144's AC18 uses."""
    import segfacet.failure_modes as fm

    committed_payload = json.loads(_COMMITTED_JSON.read_text(encoding="utf-8"))
    assert committed_payload, "expected a non-empty committed JSON payload"
    fresh_payload = fm.specification_to_dict()
    normalised_fresh = json.loads(json.dumps(fresh_payload, sort_keys=True))
    assert normalised_fresh == committed_payload

    committed_ids = {mode_record["id"] for mode_record in committed_payload["modes"]}
    # Item 146 relaxed this to a subset check because it was adding modes 9
    # and 10 to an artifact this module claimed carried eight. The item-150
    # sign-off (revised 2026-09-15) closed the catalogue at sixteen and
    # assigned the ids here, so
    # equality is the honest claim again -- and it is the one that catches a
    # mode silently added to or dropped from the committed rendering.
    assert committed_ids == set(_MODE_IDS), committed_ids

    committed_conditions = {c["id"] for c in committed_payload["conditions"]}
    assert _FOV_CONDITION_ID in committed_conditions, committed_conditions
    assert committed_payload["vision_seed_disposition"] == dict(
        fm.VISION_SEED_DISPOSITION
    )

    committed_md = _COMMITTED_MD.read_text(encoding="utf-8")
    assert committed_md.strip(), "expected non-empty committed markdown"
    fresh_md = fm.render_markdown()
    assert fresh_md == committed_md
    # A sub-mode's heading carries its path and parent between the id and
    # the name ("## Mode 2 (1.1, sub-mode of 1): ..."), so match the heading
    # rather than the old "Mode N:" literal, which only top-level entries
    # would satisfy.
    headings = {int(m) for m in re.findall(r"^## Mode (\d+)\b", fresh_md, re.MULTILINE)}
    assert headings == set(_MODE_IDS), headings
    assert f"## Condition {_FOV_CONDITION_ID}:" in fresh_md


# =========================================================================== #
# AC24's `aide check` warning-baseline tests were retired on 2026-09-16: they
# pinned the loop's own `aide check` warning set in the standing suite, a
# diff-time claim that belongs on the branch, not here
# (.aide/conventions/6-test-hygiene.md §6). The error half now lives in
# tests/test_aide_check_no_errors.py.
# =========================================================================== #


# =========================================================================== #
# Adversarial / edge cases
# =========================================================================== #


def test_adv_narrowing_an_expected_firing_set_drops_validated_to_implemented(measured):
    """Re-targeted: the ``{border, mislabel}`` case this used to narrow now
    belongs to the ``fov_truncation`` condition, which has no lifecycle
    status to drop. The claim -- an ``expected_firing`` set that understates
    what the case measurably fires stops the mode validating -- is asserted
    on mode 9, the sign-off's validated out-of-order sequence mode, with the
    narrowing derived from a live measurement rather than transcribed."""
    import segfacet.failure_modes as fm

    mode = _mode(fm, 9)
    assert fm.derive_status(mode) == "validated"

    case = _case(mode, "relabel_swap")
    fired = set(measured(case))
    assert fired, "adversarial precondition: the case must actually fire something"

    narrowed_case = dataclasses.replace(case, expected_firing=())
    probe = dataclasses.replace(
        mode,
        corpus_cases=tuple(
            narrowed_case if c.case_id == case.case_id else c
            for c in mode.corpus_cases
        ),
    )
    assert fm.derive_status(probe) == "implemented"

    # The shipped mode itself is untouched.
    assert fm.derive_status(fm.SPECIFICATION[9]) == "validated"


def test_adv_condition_case_narrowed_expectation_is_a_disagreement(measured):
    """The condition's half of the same claim. A condition derives no
    status, so what must catch a narrowed expectation there is
    ``case_agrees`` -- and, through it, ``specification_conflicts()``'s
    condition branch."""
    import segfacet.failure_modes as fm

    condition = _condition(fm, _FOV_CONDITION_ID)
    case = _case(condition, "crop_at_border")
    assert "mislabel" in measured(case), (
        "adversarial precondition: crop_at_border must actually fire mislabel too"
    )
    assert fm.case_agrees(case) is True

    narrowed_case = dataclasses.replace(case, expected_firing=("border",))
    assert fm.case_agrees(narrowed_case) is False


def test_adv_intended_rule_for_a_rule_not_declaring_the_mode_fails_ac5_check():
    """Runs the **same** predicate the AC5 test runs
    (:func:`_ac5_edge_set_matches_registry`) over a deliberately-broken copy,
    so this asserts the checker rejects it rather than re-deriving the
    comparison inline (which would pass no matter what AC5 checked)."""
    import segfacet.failure_modes as fm

    mode = fm.SPECIFICATION[1]
    assert _ac5_edge_set_matches_registry(mode), "precondition: mode 1 is clean today"
    assert "border" not in _live_declared_rule_ids(1), (
        "adversarial precondition: 'border' must not declare mode 1"
    )

    bad_edge = fm.IntendedRule(rule_id="border", detector_ids=(), evidence_rung="needs-real-data")
    bad_mode = dataclasses.replace(mode, intended_rules=mode.intended_rules + (bad_edge,))
    assert not _ac5_edge_set_matches_registry(bad_mode)


def test_adv_discriminator_naming_no_sibling_fails_ac19_check():
    """Same shape as the AC5 adversarial above: the AC19 predicate itself is
    run over a broken copy, not re-derived here."""
    import segfacet.failure_modes as fm

    mode = fm.SPECIFICATION[1]
    all_ids = {m.id for m in fm.iter_modes()}
    assert _ac19_names_a_sibling(mode, all_ids), "precondition: mode 1 is clean today"

    bad_mode = dataclasses.replace(mode, discriminator="Names no other mode at all.")
    assert not _ac19_names_a_sibling(bad_mode, all_ids)


def test_adv_all_expected_firing_tuples_are_ascending():
    import segfacet.failure_modes as fm

    checked = 0
    for mode in fm.iter_modes():
        for case in mode.corpus_cases:
            checked += 1
            assert case.expected_firing == tuple(sorted(case.expected_firing)), (
                mode.id,
                case.case_id,
                case.expected_firing,
            )
    assert checked >= 8, checked


def test_adv_every_specified_mode_is_declared_and_no_proposed_one_is():
    """Negative control for AC22's containment reading: the live registry
    declares every ``specified`` id somewhere (so AC22's quantifier is not
    vacuous), and declares **no** ``proposed`` id (so the fallback branch
    AC22 asserts for 5, 7 and 10-14 is reached for the stated reason and
    not by accident). It also pins the other direction: no rule declares a
    mode id the catalogue does not carry."""
    import segfacet.failure_modes as fm
    from segfacet.heuristics.rule import iter_rule_declarations

    declared_ids: set = set()
    for _rule_id, declaration in iter_rule_declarations():
        if declaration is not None:
            declared_ids |= set(declaration.modes)
    assert declared_ids, "expected the registry to declare at least one mode"

    for mode in fm.iter_modes():
        if mode.id in _PROPOSED_MODE_IDS:
            assert mode.id not in declared_ids, (mode.id, sorted(declared_ids))
        else:
            assert mode.id in declared_ids, (mode.id, sorted(declared_ids))

    assert declared_ids <= set(_MODE_IDS), sorted(declared_ids - set(_MODE_IDS))
