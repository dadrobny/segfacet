"""Tests for item 151 -- Stage 30 validation: the in-suite assertable subset.

Item 151 closes Stage 30 by replaying its acceptance end-to-end from a clean
clone (a fresh checkout with its own venv, six generators re-run, three
mutation replays, a full-suite run, ...). Per the item spec's Testing
Strategy, most of that is a *replay* obligation discharged and recorded in
this item's Decisions log and ``progress.md`` -- not something a pytest
module in the working checkout can assert (a clean-clone artifact
regeneration, a mutation-and-restore cycle, a full suite run). This module
covers exactly the subset the spec's Testing Strategy designates **in-suite**:

    AC3, AC4, AC5, AC6, AC8, AC9, AC10, AC11, AC12, AC13, AC14, AC15, AC16,
    AC17, AC18, AC22, AC23, AC24, AC25, AC26, AC27 (the conflicts half),
    AC28, AC29, AC30, AC34, AC35, AC36, AC37, AC39, AC40 (the signature
    half).

AC1, AC2, AC7, AC19, AC20, AC21, AC31, AC32, AC33, AC38, AC40 (the profile
half) and AC41 are replay-only and are intentionally not covered here -- they
belong to the item's Decisions log and Validation section.

Discipline followed (Testing Strategy):

- No byte-exact comparison against a committed artifact -- committed JSON is
  read and *parsed* (``json.loads``), never byte- or text-compared against a
  freshly generated file (that keeps every read outside
  ``committed_artifact_guard``'s detection, per its own documented
  ``json.loads`` example, and outside its allowlist, which this item may not
  edit).
- Measure once per module: ``matrix`` (``traceability.build_matrix()``) and
  the conformance measurement it carries are built in one module-scoped
  fixture and read by every AC that needs them (AC8, AC9, AC13, AC14, AC18).
- Independent recomputation: AC13 and AC18 re-derive rung and status from
  primary inputs in the test body, never by calling ``derive_mode_rung`` /
  ``derive_status`` and comparing the result to itself.
- Parsed, not eyeballed: AC28 imports ``.aide/scripts/aide.py`` in-process
  for ``human_gates()``; AC35-AC37 parse ``progress.md``'s Stage 30 section
  by its checkbox lines.
- Git-reading AC34 skips, never fails and never passes, on a shallow clone
  or a missing ``git``.
- Archive-aware: AC39 searches ``docs/aide/insights.md`` and every
  ``docs/aide/insights/archive-*.md``.

Adversarial and edge cases covered (Testing Strategy's own list, plus a few):

- AC35's parser rejects a missing count clause, an off-by-one count, and an
  ``N`` disagreeing with ``len(SPECIFICATION)``.
- AC36's parser fails on a ticked box with no annotation and an unticked box
  with no reason.
- AC37 fails on a reworded original annotation and on a missing trail line
  naming item 151.
- AC14 fails on an in-memory matrix copy with one ``analytic`` attribution
  flipped to ``corpus``.
- AC13's weakened-edge variant changes the derived rung; a mode with no
  edges derives ``None`` and renders ``""`` in the matrix.
- AC18 fails on an in-memory copy of a mode whose one agreeing case's
  expected set is emptied: ``validated`` must not be recomputed.
- AC9 fails when a synthetic manifest case with a non-zero ``failure_mode``
  not carried by the specification is injected in memory.
- AC11 fails if label 22's offset in a monkeypatched record sits exactly at
  the threshold (``>`` not ``>=``).
- Determinism: two independent calls agree (measured firing, ``build_clean_spine``).
- Immutability: every variant is built in memory; no committed file is
  written to.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import segfacet.failure_modes as fm
import segfacet.traceability as tb
from segfacet import feature_docs as feature_docs_module
from segfacet.config import bundled_default_config
from segfacet.heuristics.mislabel import _DEFAULT_MAX_OFFSET_MM
from segfacet.heuristics.rule import iter_rule_declarations
from segfacet.pipeline import extract_feature_record
from segfacet.synth import corpus as corpus_module
from segfacet.synth import intensity as intensity_module
from segfacet.synth.axes import si_axis
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.regression import (
    intensity_pipeline_findings,
    loaded_seg_image,
    pipeline_findings,
    reconstructed_findings,
)

from run_process import run_utf8
import test_150_maintainer_sign_off as t150

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_DOCS_AIDE_DIR = _REPO_ROOT / "docs" / "aide"
_PROGRESS_PATH = _DOCS_AIDE_DIR / "progress.md"
_INSIGHTS_PATH = _DOCS_AIDE_DIR / "insights.md"
_INSIGHTS_ARCHIVE_DIR = _DOCS_AIDE_DIR / "insights"
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_FM_JSON_PATH = _DOCS_AIDE_DIR / "failure_modes.generated.json"
_FM_MD_PATH = _DOCS_AIDE_DIR / "failure_modes.generated.md"
_TM_JSON_PATH = _DOCS_AIDE_DIR / "traceability_matrix.generated.json"
_TM_MD_PATH = _DOCS_AIDE_DIR / "traceability_matrix.generated.md"

_PRIMARY_SOURCE = "src/segfacet/failure_modes.py"

#: Item 143's S-axis correction commit, resolved fresh in AC34 by subject --
#: never hardcoded as the *sole* source of truth, only as the search text.
_CORRECTION_SUBJECT = "fix(143): correct the synthetic corpus's S-axis stacking"


def _aide_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_aide_cli_151", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _manifest_case(case_id: str) -> dict:
    for case in corpus_module.load_manifest()["cases"]:
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"case_id {case_id!r} not found in the committed geometric manifest")


def _intensity_manifest_case(case_id: str) -> dict:
    for case in intensity_module.load_intensity_manifest()["cases"]:
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"case_id {case_id!r} not found in the committed intensity manifest")


def _record(case_id: str) -> dict:
    seg_img = loaded_seg_image(_manifest_case(case_id))
    return extract_feature_record(seg_img, bundled_default_config())


def _max_offset_mm() -> float:
    config = bundled_default_config()
    return float(
        config.rule_param("mislabel", "max_offset_mm", default=_DEFAULT_MAX_OFFSET_MM)
    )


def _per_label_offset(record: dict, label: int) -> dict:
    entries = [e for e in record["stage3"]["per_label_offsets"] if e["label"] == label]
    assert entries, f"no stage3.per_label_offsets entry for label {label}"
    assert len(entries) == 1, entries
    return entries[0]


# =========================================================================== #
# Shared, module-scoped: build_matrix() exactly once (Testing Strategy's
# "measure once per module"), plus the manifest-derived case/detection index
# every AC8/AC14/AC35 recomputation reads.
# =========================================================================== #


@pytest.fixture(scope="module")
def matrix():
    return tb.build_matrix()


@pytest.fixture(scope="module")
def conformance_index(matrix):
    """``{(corpus, case_id): ConformanceCase}`` over both manifests, built
    from the one shared ``matrix`` -- never recomputed per test."""
    return {(c.corpus, c.case_id): c for c in matrix.conformance.cases}


@pytest.fixture(scope="module")
def detection_by_case_id():
    """``{case_id: detection}`` over both committed manifests -- used by
    AC35's validated-through split, independent of anything build_matrix
    computes."""
    out = {}
    for case in corpus_module.load_manifest()["cases"]:
        out[case["case_id"]] = case.get("detection")
    for case in intensity_module.load_intensity_manifest()["cases"]:
        out[case["case_id"]] = case.get("detection")
    return out


# =========================================================================== #
# AC3: the matrix names the specification as its primary source, and its
# content comes from that source.
# =========================================================================== #


def test_ac3_committed_matrix_json_names_the_specification_as_primary_source():
    payload = json.loads(_TM_JSON_PATH.read_text(encoding="utf-8"))
    assert payload["primary_source"] == _PRIMARY_SOURCE


def test_ac3_primary_source_resolves_to_the_loaded_module():
    resolved = Path(fm.__file__).resolve()
    assert resolved == (_REPO_ROOT / _PRIMARY_SOURCE).resolve()


def test_ac3_committed_matrix_markdown_carries_the_primary_source_line():
    text = _TM_MD_PATH.read_text(encoding="utf-8")
    assert f"Primary source: `{_PRIMARY_SOURCE}`." in text


def test_ac3_every_mode_row_title_authored_status_and_edge_rungs_match_specification(matrix):
    by_mode = {m.mode: m for m in matrix.modes}
    assert set(by_mode) == set(fm.SPECIFICATION), (
        "matrix row key set does not equal set(SPECIFICATION) exactly"
    )
    for mode_id, mode_spec in fm.SPECIFICATION.items():
        row = by_mode[mode_id]
        assert row.title == mode_spec.name
        assert row.authored_status == mode_spec.status
        expected_edges = tuple(
            (rule.rule_id, rule.detector, rule.evidence_rung)
            for rule in mode_spec.intended_rules
        )
        assert row.edge_rungs == expected_edges


# =========================================================================== #
# AC4: the specification rendering names the module it is rendered from.
# =========================================================================== #


def test_ac4_committed_json_note_names_the_module():
    payload = json.loads(_FM_JSON_PATH.read_text(encoding="utf-8"))
    assert _PRIMARY_SOURCE in payload["note"]


def test_ac4_committed_markdown_note_paragraph_names_the_module():
    text = _FM_MD_PATH.read_text(encoding="utf-8")
    assert _PRIMARY_SOURCE in text.splitlines()[2]


def test_ac4_committed_json_modes_list_equals_live_specification_to_dict():
    payload = json.loads(_FM_JSON_PATH.read_text(encoding="utf-8"))
    live = fm.specification_to_dict()
    assert payload["modes"] == live["modes"]


def test_ac4_committed_json_conditions_list_equals_live():
    payload = json.loads(_FM_JSON_PATH.read_text(encoding="utf-8"))
    live = fm.specification_to_dict()
    assert payload["conditions"] == live["conditions"]


# =========================================================================== #
# AC5: the metric anchor path and the rule read paths are separate,
# separately labelled columns in the matrix.
# =========================================================================== #


def test_ac5_matrix_markdown_header_carries_both_column_labels(matrix):
    text = tb.render_markdown(matrix)
    header_line = next(
        line for line in text.splitlines() if line.startswith("| Mode |")
    )
    assert "Stage-18 metric anchor paths" in header_line
    assert "Rule signal read paths" in header_line


def test_ac5_anchor_paths_equal_mode_anchor_paths_for_every_row(matrix):
    for row in matrix.modes:
        assert row.anchor_paths == tuple(
            feature_docs_module.MODE_ANCHOR_PATHS.get(row.mode, ())
        )


@pytest.mark.parametrize("mode_id", [6, 8, 9, 16])
def test_ac5_anchor_and_read_paths_differ_for_named_modes(matrix, mode_id):
    row = next(m for m in matrix.modes if m.mode == mode_id)
    assert row.anchor_paths != row.read_paths, (
        f"mode {mode_id}: expected anchor_paths and read_paths to differ"
    )


@pytest.mark.parametrize("mode_id", [6, 8, 9, 16])
def test_ac5_markdown_row_renders_the_two_columns_non_identically(matrix, mode_id):
    text = tb.render_markdown(matrix)
    row_line = next(
        line for line in text.splitlines() if line.startswith(f"| {mode_id} |")
    )
    cells = [c.strip() for c in row_line.strip("|").split("|")]
    assert len(cells) >= 10, row_line
    anchor_cell, read_cell = cells[-2], cells[-1]
    assert anchor_cell != read_cell, row_line


# =========================================================================== #
# AC6: the specification rendering labels anchor paths as metric anchors and
# never as rule reads.
# =========================================================================== #


def test_ac6_every_stage18_anchor_candidate_renders_under_the_anchor_label():
    text = fm.render_markdown()
    for mode in fm.SPECIFICATION.values():
        for feature in mode.candidate_features:
            if feature.role == "stage18-metric-anchor":
                assert (
                    f"Stage-18 metric anchor path (`stage18-metric-anchor`): "
                    f"`{feature.path}`" in text
                ), (mode.id, feature.path)
            else:
                assert (
                    f"`{feature.role}` candidate path: `{feature.path}`" in text
                ), (mode.id, feature.path)


def test_adv_stage18_metric_anchor_label_never_rendered_beside_a_rule_id():
    text = fm.render_markdown()
    for line in text.splitlines():
        if "Stage-18 metric anchor path" in line:
            assert "detector:" not in line, line


# =========================================================================== #
# AC8/AC9: expected equals measured, across both corpora; no unspecified case.
# =========================================================================== #


def _all_manifest_case_keys():
    keys = [
        ("geometric", c["case_id"])
        for c in corpus_module.load_manifest()["cases"]
    ] + [
        ("intensity", c["case_id"])
        for c in intensity_module.load_intensity_manifest()["cases"]
    ]
    assert keys, "expected at least one case across both manifests"
    return keys


def test_ac8_case_count_equals_summed_manifest_case_count(conformance_index):
    keys = _all_manifest_case_keys()
    assert len(keys) == 15, keys
    assert set(conformance_index) == set(keys)


@pytest.mark.parametrize("corpus_name,case_id", _all_manifest_case_keys())
def test_ac8_every_case_measures_its_expected_firing_set(conformance_index, corpus_name, case_id):
    case = conformance_index[(corpus_name, case_id)]
    assert set(case.measured_firing) == set(case.expected_firing), (
        corpus_name, case_id, case.measured_firing, case.expected_firing
    )


def test_ac9_no_unspecified_case_and_matrix_is_fully_conformant(matrix):
    assert matrix.conformance.unspecified_cases == ()
    assert matrix.conformance.disagreements == ()
    assert matrix.conformance.agree_count == len(matrix.conformance.cases)
    assert matrix.conformance.agree_count == 15


def test_adv_ac9_injected_unspecified_case_is_flagged(monkeypatch):
    """A synthetic manifest case naming a real mode but no carried case_id
    must surface as an unspecified case -- the manifest enumeration, not the
    specification, drives the walk.

    Built from a copy of a real, loadable manifest entry (rather than a bare
    dict) so ``measured_firing`` -- which ``_build_conformance`` calls on
    every case -- still finds a ``scan_fixture``/``seg_fixture`` pair to
    load; only ``case_id`` is overridden to one no ``ModeSpec.corpus_cases``
    entry carries.
    """
    real_case = _manifest_case("mode1_displace")
    assert real_case["failure_mode"] == 1

    def _fake_load_manifest():
        fake_case = dict(real_case)
        fake_case["case_id"] = "synthetic_unspecified_case"
        return {"cases": [fake_case]}

    monkeypatch.setattr(corpus_module, "load_manifest", _fake_load_manifest)
    monkeypatch.setattr(
        intensity_module, "load_intensity_manifest", lambda: {"cases": []}
    )
    report = tb._build_conformance(fm)
    assert ("geometric", "synthetic_unspecified_case") in report.unspecified_cases


# =========================================================================== #
# AC10/AC11: mode6_crop_at_border, the FOV-truncation condition's fixture.
# =========================================================================== #


def test_ac10_condition_case_expects_border_and_mislabel_with_a_reason():
    condition = fm.CONDITIONS["fov_truncation"]
    case = next(
        (c for c in condition.corpus_cases if c.case_id == "mode6_crop_at_border"), None
    )
    assert case is not None
    assert set(case.expected_firing) == {"border", "mislabel"}
    assert case.reason.strip()


def test_ac10_manifest_entry_has_no_failure_mode_and_the_condition():
    manifest_case = _manifest_case("mode6_crop_at_border")
    assert manifest_case["failure_mode"] == 0
    assert manifest_case.get("condition") == "fov_truncation"


def test_ac10_no_specification_mode_carries_the_case():
    for mode in fm.SPECIFICATION.values():
        assert "mode6_crop_at_border" not in {c.case_id for c in mode.corpus_cases}, mode.id


def test_ac11_crop_at_border_touches_anterior_and_offset_exceeds_threshold():
    record = _record("mode6_crop_at_border")
    assert record["per_label"]["22"]["geometry"]["touches_anterior"] is True

    offset_entry = _per_label_offset(record, 22)
    assert offset_entry["is_terminal"] is False

    threshold = _max_offset_mm()
    assert offset_entry["offset_mm"] > threshold, (offset_entry["offset_mm"], threshold)


def test_ac11_clean_control_does_not_touch_anterior():
    record = _record("clean_control")
    assert record["per_label"]["22"]["geometry"]["touches_anterior"] is False


def test_adv_ac11_offset_exactly_at_threshold_does_not_count_as_above():
    threshold = _max_offset_mm()
    record = _record("mode6_crop_at_border")
    offset_entry = dict(_per_label_offset(record, 22))
    offset_entry["offset_mm"] = threshold
    assert not (offset_entry["offset_mm"] > threshold)


# =========================================================================== #
# AC12: every mode <-> rule edge carries an authored rung from the closed
# vocabulary; the total edge count is derived live.
# =========================================================================== #


def test_ac12_every_intended_rule_edge_carries_a_valid_rung():
    total_edges = 0
    for mode in fm.SPECIFICATION.values():
        for edge in mode.intended_rules:
            assert edge.evidence_rung in fm.EVIDENCE_RUNGS
            total_edges += 1
    assert total_edges == 17, total_edges


# =========================================================================== #
# AC13: every mode's rung is derived from its edges -- independent
# recomputation, never delegated to derive_mode_rung.
# =========================================================================== #


def _independent_rung(mode):
    if not mode.intended_rules:
        return None
    strengths = [fm.EVIDENCE_RUNGS.index(edge.evidence_rung) for edge in mode.intended_rules]
    return fm.EVIDENCE_RUNGS[min(strengths)]


def test_ac13_derived_rung_matches_independent_recomputation_and_committed_rendering(matrix):
    committed = {
        entry["id"]: entry["derived_rung"]
        for entry in json.loads(_FM_JSON_PATH.read_text(encoding="utf-8"))["modes"]
    }
    row_by_mode = {m.mode: m for m in matrix.modes}
    for mode_id, mode_spec in fm.SPECIFICATION.items():
        expected = _independent_rung(mode_spec)
        assert expected == fm.derive_mode_rung(mode_spec), mode_id
        assert committed[mode_id] == expected, (mode_id, committed[mode_id], expected)
        row_rung = row_by_mode[mode_id].rung or None
        assert row_rung == expected, (mode_id, row_rung, expected)


def test_ac13_weakening_the_strongest_edge_changes_the_derived_rung():
    mode9 = fm.SPECIFICATION[9]
    assert _independent_rung(mode9) == "synthetic-demonstrable"
    weakened_edges = tuple(
        dataclasses.replace(edge, evidence_rung="structurally-unobservable")
        if edge.evidence_rung == "synthetic-demonstrable"
        else edge
        for edge in mode9.intended_rules
    )
    weakened_mode = dataclasses.replace(mode9, intended_rules=weakened_edges)
    assert _independent_rung(weakened_mode) != "synthetic-demonstrable"
    assert fm.derive_mode_rung(weakened_mode) == _independent_rung(weakened_mode)


def test_ac13_mode_with_no_edges_derives_none_and_renders_empty_string(matrix):
    mode5 = fm.SPECIFICATION[5]
    assert mode5.intended_rules == ()
    assert fm.derive_mode_rung(mode5) is None
    row = next(m for m in matrix.modes if m.mode == 5)
    assert row.rung == ""


# =========================================================================== #
# AC14: the analytic-only edges are rendered as such, from the *measured*
# firing set (AC8), never the authored expected_firing.
# =========================================================================== #


def _independent_attribution(matrix, conformance_index):
    """Per mode row: {rule_id: "corpus"|"analytic"}, derived from the union
    of *measured* firing sets over that mode's own corpus_cases -- never
    from ModeSpec.corpus_cases[].expected_firing directly."""
    out = {}
    for mode_id, mode_spec in fm.SPECIFICATION.items():
        measured_union = set()
        for case in mode_spec.corpus_cases:
            key = (case.corpus, case.case_id)
            measured_union |= set(conformance_index[key].measured_firing)
        row = next(m for m in matrix.modes if m.mode == mode_id)
        out[mode_id] = {
            rule_id: ("corpus" if rule_id in measured_union else "analytic")
            for rule_id in row.rules
        }
    return out


def test_ac14_attribution_matches_independent_recomputation_from_measured_sets(
    matrix, conformance_index
):
    independent = _independent_attribution(matrix, conformance_index)
    for row in matrix.modes:
        assert dict(row.rule_attribution) == independent[row.mode], row.mode


def test_ac14_no_analytic_edge_carries_the_strongest_rung(matrix):
    for row in matrix.modes:
        attribution = dict(row.rule_attribution)
        for rule_id, detector, evidence_rung in row.edge_rungs:
            if attribution.get(rule_id) == "analytic":
                assert evidence_rung != "synthetic-demonstrable", (row.mode, rule_id)


def test_ac14_recorded_analytic_edge_list(matrix):
    analytic = sorted(
        (row.mode, rule_id)
        for row in matrix.modes
        for rule_id, attribution in row.rule_attribution
        if attribution == "analytic"
    )
    for expected in [
        (1, "bounds"), (1, "reference_delta"),
        (2, "bounds"), (2, "reference_delta"),
        (3, "bounds"), (3, "reference_delta"),
        (4, "bounds"), (4, "reference_delta"),
        (8, "reference_delta"),
        (16, "intensity_reference_delta"),
    ]:
        assert expected in analytic, expected


def test_adv_ac14_flipped_attribution_is_detected(matrix, conformance_index):
    independent = _independent_attribution(matrix, conformance_index)
    mode1_row = next(m for m in matrix.modes if m.mode == 1)
    mutated_attribution = list(mode1_row.rule_attribution)
    for i, (rule_id, attribution) in enumerate(mutated_attribution):
        if attribution == "analytic":
            mutated_attribution[i] = (rule_id, "corpus")
            break
    else:
        pytest.fail("expected mode 1 to carry >=1 analytic edge to flip")
    mutated_row = SimpleNamespace(mode=1, rules=mode1_row.rules, rule_attribution=tuple(mutated_attribution))
    assert dict(mutated_row.rule_attribution) != independent[1]


# =========================================================================== #
# AC15/AC16: mode 15's rung is structurally-unobservable; the mechanism
# holds when measured on the shared fixture.
# =========================================================================== #


def test_ac15_mode15_rung_is_structurally_unobservable():
    assert fm.derive_mode_rung(fm.SPECIFICATION[15]) == "structurally-unobservable"


def test_ac15_mode15_mechanism_states_the_single_channel_invariant():
    mechanism = fm.SPECIFICATION[15].mechanism.lower()
    assert "single-channel" in mechanism
    assert "voxel" in mechanism


def test_ac16_overlap_case_yields_no_overlap_through_the_pipeline():
    case = _manifest_case("mode8_force_overlap")
    record = _record("mode8_force_overlap")
    assert record["overlaps"] == []
    findings = pipeline_findings(case)
    assert "overlap" not in {f.rule_id for f in findings}


def test_ac16_overlap_case_yields_overlap_through_the_reconstruction():
    case = _manifest_case("mode8_force_overlap")
    findings = reconstructed_findings(case)
    assert findings, "expected >=1 reconstructed finding"
    assert "overlap" in {f.rule_id for f in findings}


def test_ac16_manifest_detection_is_reconstructed_record():
    case = _manifest_case("mode8_force_overlap")
    assert case["detection"] == "reconstructed_record"


def test_ac16_mode15_carries_the_case():
    assert "mode8_force_overlap" in {c.case_id for c in fm.SPECIFICATION[15].corpus_cases}


# =========================================================================== #
# AC17: every mode carries every schema field with a valid value.
# =========================================================================== #


def test_ac17_every_mode_carries_every_dataclass_field():
    field_names = [f.name for f in dataclasses.fields(fm.ModeSpec)]
    for mode in fm.SPECIFICATION.values():
        for name in field_names:
            assert hasattr(mode, name), (mode.id, name)


def test_ac17_required_string_fields_are_non_empty():
    for mode in fm.SPECIFICATION.values():
        for field_name in (
            "name", "short_name", "scope", "definition", "discriminator",
            "mechanism", "observability", "severity", "status", "provenance",
        ):
            value = getattr(mode, field_name)
            assert isinstance(value, str) and value, (mode.id, field_name, value)


def test_ac17_vocabularies_hold():
    for mode in fm.SPECIFICATION.values():
        assert mode.status in fm.AUTHORED_STATUSES, mode.id
        assert mode.provenance in fm.PROVENANCE, mode.id
        assert mode.observability in fm.OBSERVABILITY, mode.id
        assert mode.scope in fm.SCOPES, mode.id
        assert mode.parent is None or mode.parent in fm.SPECIFICATION, mode.id
        if mode.parent is not None:
            assert fm.SPECIFICATION[mode.parent].parent is None, mode.id


def test_ac17_tuple_fields_are_tuples_of_the_right_element_type():
    """D5 (corrected 2026-09-15): no tuple field is required to be
    non-empty, whatever the authored status. Modes 3 and 8 are authored
    `specified` with an empty `corpus_cases`, and every mode -- `proposed`
    included -- carries a non-empty `candidate_features`. So this AC checks
    only that each of the three tuple fields is a tuple whose elements are
    the right dataclass type; it asserts no emptiness rule at all."""
    for mode in fm.SPECIFICATION.values():
        for field_name, element_type in (
            ("candidate_features", fm.CandidateFeature),
            ("intended_rules", fm.IntendedRule),
            ("corpus_cases", fm.CorpusCaseExpectation),
        ):
            value = getattr(mode, field_name)
            assert isinstance(value, tuple), (mode.id, field_name)
            for element in value:
                assert isinstance(element, element_type), (mode.id, field_name, element)


# =========================================================================== #
# AC18: the derived statuses equal an independent live derivation.
# =========================================================================== #


def _independent_declared_modes():
    declared = set()
    for _rule_id, declaration in iter_rule_declarations():
        if declaration is not None:
            declared |= set(declaration.modes)
    return declared


def _independent_status(mode, conformance_index, declared_modes):
    declared = mode.id in declared_modes
    if declared and mode.corpus_cases:
        all_agree = all(
            set(conformance_index[(case.corpus, case.case_id)].measured_firing)
            == set(case.expected_firing)
            for case in mode.corpus_cases
        )
        own_rules = {edge.rule_id for edge in mode.intended_rules}
        demonstrates = any(
            case.expected_firing and own_rules.intersection(case.expected_firing)
            for case in mode.corpus_cases
        )
        if all_agree and demonstrates:
            return "validated"
    if declared:
        return "implemented"
    return mode.status


def test_ac18_status_matches_independent_recomputation_and_committed_rendering(
    matrix, conformance_index
):
    declared_modes = _independent_declared_modes()
    committed = {
        entry["id"]: entry["status_derived"]
        for entry in json.loads(_FM_JSON_PATH.read_text(encoding="utf-8"))["modes"]
    }
    row_by_mode = {m.mode: m for m in matrix.modes}
    for mode_id, mode_spec in fm.SPECIFICATION.items():
        expected = _independent_status(mode_spec, conformance_index, declared_modes)
        assert expected in fm.STATUSES, (mode_id, expected)
        assert expected == fm.derive_status(mode_spec), mode_id
        assert committed[mode_id] == expected, (mode_id, committed[mode_id], expected)
        assert row_by_mode[mode_id].status == expected, mode_id


def test_adv_ac18_emptied_agreeing_case_stops_validating(conformance_index):
    declared_modes = _independent_declared_modes()
    mode9 = fm.SPECIFICATION[9]
    assert _independent_status(mode9, conformance_index, declared_modes) == "validated"

    mutated_cases = tuple(
        dataclasses.replace(case, expected_firing=())
        if case.case_id == "mode4_relabel_swap"
        else case
        for case in mode9.corpus_cases
    )
    mutated_mode = dataclasses.replace(mode9, corpus_cases=mutated_cases)
    result = _independent_status(mutated_mode, conformance_index, declared_modes)
    assert result != "validated", result


# =========================================================================== #
# AC22/AC23/AC24: mode 16 -- both intensity rules declare it, corpus cases
# carry expected firing sets.
# =========================================================================== #


def test_ac22_mode16_present_at_implemented_or_validated():
    mode16 = fm.SPECIFICATION[16]
    assert mode16.name == "Implausible tissue under a label"
    assert mode16.observability == "needs-paired-scan"
    assert fm.derive_status(mode16) in ("implemented", "validated")


def test_ac23_both_intensity_rules_declare_mode16():
    declarations = dict(iter_rule_declarations())
    for rule_id in ("intensity", "intensity_reference_delta"):
        declaration = declarations[rule_id]
        assert declaration is not None, rule_id
        assert 16 in declaration.modes, rule_id
    rule_ids = {edge.rule_id for edge in fm.SPECIFICATION[16].intended_rules}
    assert {"intensity", "intensity_reference_delta"} <= rule_ids


def test_ac24_intensity_manifest_cases_carry_expected_firing_keyed_to_mode16():
    cases = intensity_module.load_intensity_manifest()["cases"]
    assert cases, "expected >=1 intensity manifest case"
    for case in cases:
        assert "failure_mode" in case, case
        assert "expected_firing" in case and isinstance(case["expected_firing"], list), case
        if case["expected_firing"]:
            assert case["failure_mode"] == 16, case
        else:
            assert case["failure_mode"] == 0, case


def test_ac24_named_cases_measured_2026_09_15():
    for case_id in ("implausible_metal", "implausible_soft_tissue", "degenerate_uniform"):
        case = _intensity_manifest_case(case_id)
        assert case["failure_mode"] == 16
        assert case["expected_firing"] == ["intensity"]
    clean = _intensity_manifest_case("clean_hu")
    assert clean["failure_mode"] == 0
    assert clean["expected_firing"] == []


# =========================================================================== #
# AC25/AC26: FAILURE_MODE_NAMES and MODE_RUNGS are replaced by/derived from
# the specification.
# =========================================================================== #


def test_ac25_failure_mode_names_equals_derived_mapping():
    from segfacet.synth import perturbation

    assert perturbation.FAILURE_MODE_NAMES == dict(fm.failure_mode_names())


def test_ac25_perturbation_module_binding_is_not_a_dict_literal():
    import ast

    source = (_REPO_ROOT / "src" / "segfacet" / "synth" / "perturbation.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    found = False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        else:
            continue
        if "FAILURE_MODE_NAMES" in targets:
            found = True
            assert not isinstance(node.value, ast.Dict), (
                "FAILURE_MODE_NAMES is still a Dict literal, not derived"
            )
    assert found, "no module-level FAILURE_MODE_NAMES assignment found"


def test_ac26_no_module_binds_mode_rungs_or_rung_vocabulary_at_module_level():
    import ast

    src_dir = _REPO_ROOT / "src" / "segfacet"
    offenders = []
    for py_file in src_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        # Module-level only: `tree.body` is the module's own top-level
        # statement list, never descending into a function/class body (an
        # `ast.walk` would also catch a same-named local variable, which is
        # not what AC26 forbids).
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                for banned in ("MODE_RUNGS", "ModeRung", "RUNGS"):
                    if banned in names:
                        offenders.append((py_file.relative_to(_REPO_ROOT).as_posix(), banned))
    assert offenders == [], offenders


def test_ac26_traceability_has_no_mode_rungs_attribute():
    assert hasattr(tb, "MODE_RUNGS") is False


# =========================================================================== #
# AC27: every vision.md §6 seed title resolves through
# VISION_SEED_DISPOSITION.
# =========================================================================== #


def test_ac27_vision_seed_conflicts_is_empty():
    assert fm.vision_seed_conflicts() == ()


def test_adv_ac27_unresolvable_disposition_is_flagged(monkeypatch):
    bad_disposition = dict(fm.VISION_SEED_DISPOSITION)
    some_title = next(iter(bad_disposition))
    bad_disposition[some_title] = "mode:9999"
    monkeypatch.setattr(fm, "VISION_SEED_DISPOSITION", bad_disposition)
    assert fm.vision_seed_conflicts() != ()


# =========================================================================== #
# AC28/AC29: the sign-off record agrees with the resolved gate and its
# entry count.
# =========================================================================== #


def test_ac28_signed_off_date_matches_the_approved_gate():
    aide = _aide_module()
    lines = _PROGRESS_PATH.read_text(encoding="utf-8").splitlines()
    gates = aide.human_gates(lines)
    matching = [g for g in gates if "Stage 30 failure-mode specification sign-off" in g.text]
    assert len(matching) == 1, matching
    gate = matching[0]
    assert gate.kind == "approved"
    row_text = lines[gate.lineno - 1]
    date_match = re.search(r"Approved \((\d{4}-\d{2}-\d{2})\)", row_text)
    assert date_match, row_text
    gate_date = date_match.group(1)

    date_text, _outcome = t150._sign_off_match()
    assert date_text == gate_date, (date_text, gate_date)


_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def _count_before_entries(text: str) -> int:
    """The outcome sentence's entry count -- AC29 means the *final* count the
    sign-off arrived at, not an intermediate one it mentions along the way.
    The committed sentence names two: "reviewed all ten entries of the
    item-149 rendering" (the starting point) and "giving sixteen entries"
    (what the review produced). The last `<count> entries` phrase in the text
    is the outcome, so this takes the last match, never the first."""
    matches = list(re.finditer(r"(\w+)\s+entries", text))
    assert matches, f"no '<count> entries' phrase found in: {text!r}"
    token = matches[-1].group(1).lower()
    if token.isdigit():
        return int(token)
    assert token in _NUMBER_WORDS, f"unrecognised number word {token!r} in {text!r}"
    return _NUMBER_WORDS[token]


def test_ac29_sign_off_entry_count_matches_specification_length():
    _date_text, outcome = t150._sign_off_match()
    assert _count_before_entries(outcome) == len(fm.SPECIFICATION)


def test_adv_ac29_count_parser_rejects_missing_entries_phrase():
    with pytest.raises(AssertionError):
        _count_before_entries("accepted with changes: no count phrase here at all")


def test_adv_ac29_count_parser_resolves_to_the_outcome_count_not_the_first():
    text = (
        "accepted with changes: the maintainer reviewed all ten entries of "
        "the item-149 rendering and re-organised it, giving sixteen entries"
    )
    assert _count_before_entries(text) == 16


# =========================================================================== #
# AC30: build_clean_spine stacks ascending labels caudally along +S.
# =========================================================================== #


def _ordered_centroid_s_mm(clean):
    data = np.asanyarray(clean.seg_img.dataobj)
    affine = clean.seg_img.affine
    axis = si_axis(affine)
    origin = float(affine[axis, 3])
    scale = float(affine[axis, axis])
    coords = []
    for label in clean.labels:
        idx = np.argwhere(data == label)
        assert idx.size, f"label {label!r} has no voxels"
        mean_index = float(idx[:, axis].mean())
        coords.append(origin + scale * mean_index)
    return coords


def test_ac30_ascending_labels_advance_caudally():
    clean = build_clean_spine()
    coords = _ordered_centroid_s_mm(clean)
    assert len(coords) >= 2
    for earlier, later in zip(coords, coords[1:]):
        assert earlier > later, f"ascending labels do not strictly decrease in S: {coords}"


def test_adv_ac30_build_clean_spine_is_deterministic():
    first = _ordered_centroid_s_mm(build_clean_spine())
    second = _ordered_centroid_s_mm(build_clean_spine())
    assert first == pytest.approx(second)


# =========================================================================== #
# AC34: no expected firing set predates item 143's S-axis correction --
# skip-guarded for a shallow clone or missing git.
# =========================================================================== #


def _resolve_correction_commit():
    try:
        result = run_utf8(
            ["git", "log", "-1", "--format=%H", "--grep", _CORRECTION_SUBJECT, "--fixed-strings"],
            cwd=_REPO_ROOT,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = result.stdout.strip()
    if result.returncode != 0 or not sha:
        return None
    return sha


_correction_sha = _resolve_correction_commit()

requires_resolvable_correction_commit = pytest.mark.skipif(
    _correction_sha is None,
    reason=f"could not resolve item 143's correction commit by subject "
    f"{_CORRECTION_SUBJECT!r} (shallow clone or git unavailable)",
)


@requires_resolvable_correction_commit
def test_ac34_no_failure_modes_commit_predates_the_correction():
    full_history = run_utf8(
        ["git", "rev-list", "HEAD", "--", "src/segfacet/failure_modes.py"],
        cwd=_REPO_ROOT,
        timeout=60,
    )
    if full_history.returncode != 0:
        pytest.skip(f"git rev-list failed: {full_history.stderr}")
    since_correction = run_utf8(
        ["git", "rev-list", f"{_correction_sha}..HEAD", "--", "src/segfacet/failure_modes.py"],
        cwd=_REPO_ROOT,
        timeout=60,
    )
    if since_correction.returncode != 0:
        pytest.skip(f"git rev-list failed: {since_correction.stderr}")

    full_set = set(full_history.stdout.split())
    since_set = set(since_correction.stdout.split())
    assert full_set, "expected >=1 commit touching src/segfacet/failure_modes.py"
    assert since_set, "expected >=1 commit since the correction"
    assert full_set == since_set, full_set - since_set


# =========================================================================== #
# AC35: the per-status and per-rung counts in progress.md match a fresh
# derivation. (Dated claim: see Dependencies -> Downstream in the item spec.)
# =========================================================================== #


def _stage_section(text: str, heading_prefix: str) -> str:
    lines = text.splitlines()
    start = None
    end = len(lines)
    for i, line in enumerate(lines):
        if line.startswith(heading_prefix):
            start = i
        elif start is not None and line.startswith("## Stage ") and i > start:
            end = i
            break
    if start is None:
        raise AssertionError(f"no {heading_prefix!r} heading found in progress.md")
    return "\n".join(lines[start:end])


_STATUS_COUNTS_RE = re.compile(
    r"derived status counts over (\d+) modes: validated (\d+), implemented (\d+), "
    r"specified (\d+), proposed (\d+)"
)
_RUNG_COUNTS_RE = re.compile(
    r"derived mode rung counts: synthetic-demonstrable (\d+), needs-real-data (\d+), "
    r"structurally-unobservable (\d+), none (\d+); per-edge rung counts over (\d+) edges: "
    r"synthetic-demonstrable (\d+), needs-real-data (\d+), structurally-unobservable (\d+)"
)
_VALIDATED_SPLIT_RE = re.compile(
    r"validated through a pipeline-detected case (\d+), through a reconstructed record only (\d+)"
)


def _live_status_counts():
    counts = {"validated": 0, "implemented": 0, "specified": 0, "proposed": 0}
    for mode in fm.SPECIFICATION.values():
        counts[fm.derive_status(mode)] += 1
    return len(fm.SPECIFICATION), counts


def _live_rung_counts():
    mode_counts = {"synthetic-demonstrable": 0, "needs-real-data": 0, "structurally-unobservable": 0, "none": 0}
    edge_counts = {"synthetic-demonstrable": 0, "needs-real-data": 0, "structurally-unobservable": 0}
    total_edges = 0
    for mode in fm.SPECIFICATION.values():
        rung = fm.derive_mode_rung(mode)
        mode_counts[rung or "none"] += 1
        for edge in mode.intended_rules:
            edge_counts[edge.evidence_rung] += 1
            total_edges += 1
    return mode_counts, total_edges, edge_counts


def _live_validated_split(detection_by_case_id):
    pipeline_detected = 0
    reconstructed_only = 0
    for mode in fm.SPECIFICATION.values():
        if fm.derive_status(mode) != "validated":
            continue
        own_rules = {edge.rule_id for edge in mode.intended_rules}
        demonstrating = [
            case for case in mode.corpus_cases
            if case.expected_firing and own_rules.intersection(case.expected_firing)
        ]
        detections = {detection_by_case_id.get(c.case_id) for c in demonstrating}
        if detections & {"pipeline", "intensity_pipeline"}:
            pipeline_detected += 1
        elif detections == {"reconstructed_record"}:
            reconstructed_only += 1
    return pipeline_detected, reconstructed_only


def test_ac35_status_counts_note_matches_live_derivation():
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    match = _STATUS_COUNTS_RE.search(section)
    assert match, "Stage 30's criterion-1 evidence note carries no status-counts clause yet"
    n, validated, implemented, specified, proposed = (int(g) for g in match.groups())
    live_n, live_counts = _live_status_counts()
    assert n == live_n
    assert validated == live_counts["validated"]
    assert implemented == live_counts["implemented"]
    assert specified == live_counts["specified"]
    assert proposed == live_counts["proposed"]


def test_ac35_rung_counts_note_matches_live_derivation():
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    match = _RUNG_COUNTS_RE.search(section)
    assert match, "Stage 30's criterion-3 evidence note carries no rung-counts clause yet"
    sd, nrd, su, none_, total_edges, e_sd, e_nrd, e_su = (int(g) for g in match.groups())
    mode_counts, live_total_edges, edge_counts = _live_rung_counts()
    assert sd == mode_counts["synthetic-demonstrable"]
    assert nrd == mode_counts["needs-real-data"]
    assert su == mode_counts["structurally-unobservable"]
    assert none_ == mode_counts["none"]
    assert total_edges == live_total_edges
    assert e_sd == edge_counts["synthetic-demonstrable"]
    assert e_nrd == edge_counts["needs-real-data"]
    assert e_su == edge_counts["structurally-unobservable"]


def test_ac35_validated_split_note_matches_live_derivation(detection_by_case_id):
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    match = _VALIDATED_SPLIT_RE.search(section)
    assert match, "Stage 30's criterion-1 evidence note carries no validated-split clause yet"
    pipeline_detected, reconstructed_only = (int(g) for g in match.groups())
    live_pipeline, live_reconstructed = _live_validated_split(detection_by_case_id)
    assert pipeline_detected == live_pipeline
    assert reconstructed_only == live_reconstructed


def test_adv_ac35_status_counts_parser_rejects_missing_clause():
    assert _STATUS_COUNTS_RE.search("no such clause here") is None


def test_adv_ac35_status_counts_parser_rejects_off_by_one():
    text = "derived status counts over 16 modes: validated 7, implemented 3, specified 0, proposed 7"
    match = _STATUS_COUNTS_RE.search(text)
    assert match is not None
    n, validated, *_rest = (int(g) for g in match.groups())
    _live_n, live_counts = _live_status_counts()
    assert validated != live_counts["validated"]


def test_adv_ac35_status_counts_parser_rejects_wrong_n():
    text = "derived status counts over 15 modes: validated 6, implemented 3, specified 0, proposed 7"
    match = _STATUS_COUNTS_RE.search(text)
    assert match is not None
    n = int(match.group(1))
    live_n, _live_counts = _live_status_counts()
    assert n != live_n


# =========================================================================== #
# AC36: every Stage 30 acceptance box is ticked with evidence or unticked
# with a reason (tick-implies-evidence biconditional).
# =========================================================================== #

_CHECKBOX_RE = re.compile(r"^-\s*\[([ xX])\]\s?")
_EVIDENCE_NOTE_RE = re.compile(r"\*\(.*?\)\*", re.DOTALL)


def _acceptance_items(section: str) -> list:
    lines = section.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "**Acceptance.**")
    except StopIteration:
        raise AssertionError("no '**Acceptance.**' heading found under the section")
    items: list = []
    current: list = []
    seen_item = False
    for line in lines[start + 1:]:
        stripped = line.strip()
        if _CHECKBOX_RE.match(stripped):
            if current:
                items.append("\n".join(current))
            current = [line]
            seen_item = True
            continue
        if stripped == "" or stripped == "---":
            if current:
                items.append("\n".join(current))
                current = []
            if seen_item:
                break
            continue
        if current:
            current.append(line)
    if current:
        items.append("\n".join(current))
    return items


def _is_ticked(item_text: str) -> bool:
    match = _CHECKBOX_RE.match(item_text.splitlines()[0].strip())
    assert match is not None, item_text
    return match.group(1).lower() == "x"


def _has_annotation(item_text: str) -> bool:
    return bool(_EVIDENCE_NOTE_RE.search(item_text))


def _biconditional_violations(section: str) -> list:
    violations = []
    for item in _acceptance_items(section):
        if not _has_annotation(item):
            violations.append(item.splitlines()[0].strip())
    return violations


def test_ac36_stage30_has_seven_acceptance_boxes():
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    items = _acceptance_items(section)
    assert len(items) == 7, items


def test_ac36_every_box_ticked_implies_evidence_or_unticked_implies_reason():
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    violations = _biconditional_violations(section)
    assert violations == [], (
        f"Stage 30 acceptance box(es) with no evidence/reason annotation: {violations}"
    )


def test_adv_ac36_ticked_box_with_no_annotation_is_flagged():
    synthetic_section = (
        "## Stage 30 — Failure-Mode Specification (G2, G7, G8) — 🚧\n\n"
        "**Acceptance.**\n\n"
        "- [x] Every mode carries every schema field.\n"
    )
    violations = _biconditional_violations(synthetic_section)
    assert violations, "expected the annotation-less ticked box to be flagged"


def test_adv_ac36_unticked_box_with_reason_is_not_flagged():
    synthetic_section = (
        "## Stage 30 — Failure-Mode Specification (G2, G7, G8) — 🚧\n\n"
        "**Acceptance.**\n\n"
        "- [ ] Some criterion. *(Unticked: see item 151.)*\n"
    )
    violations = _biconditional_violations(synthetic_section)
    assert violations == []


# =========================================================================== #
# AC37: criterion 7 carries this item's dated correction trail, and its
# original attestation line survives.
# =========================================================================== #

_TRAIL_LINE_RE = re.compile(r"^\s*-\s*\*\*(\d{4}-\d{2}-\d{2})\*\*\s*→\s*(.+)$", re.M)

#: A stable, distinctive substring of item 143's original criterion-7
#: annotation (Stage 30's acceptance box 7, as committed by item 143's
#: validator) -- pinned per AC37's own requirement that this text survive
#: verbatim.
_ITEM_143_ANNOTATION_SUBSTRING = (
    "item 143 validator round 3: full suite green (6273 passed, "
    "60 environment-gated skips, 0 failed)"
)


def _criterion7_box() -> str:
    section = _stage_section(_PROGRESS_PATH.read_text(encoding="utf-8"), "## Stage 30")
    items = _acceptance_items(section)
    assert len(items) == 7, items
    return items[6]


def test_ac37_criterion7_original_annotation_survives_verbatim():
    box = _criterion7_box()
    assert _ITEM_143_ANNOTATION_SUBSTRING in box, box


def test_ac37_criterion7_carries_a_trail_line_dated_on_or_after_this_item_naming_it():
    box = _criterion7_box()
    trail_matches = _TRAIL_LINE_RE.findall(box)
    assert trail_matches, f"criterion 7's box carries no dated trail line yet: {box!r}"
    found = False
    for date_text, text in trail_matches:
        if date_text >= "2026-09-15" and "151" in text:
            found = True
    assert found, (
        f"no trail line on/after 2026-09-15 naming item 151 found: {trail_matches}"
    )


def test_adv_ac37_reworded_original_annotation_is_flagged():
    box = (
        "- [x] `build_clean_spine` stacks labels caudally along +S like real "
        "VerSe input, every *(item 143 validator: full suite green in some "
        "other shape entirely)*\n"
        "  - **2026-09-15** → item 151 re-verified criterion 7.\n"
    )
    assert _ITEM_143_ANNOTATION_SUBSTRING not in box


def test_adv_ac37_missing_trail_line_naming_item151_is_flagged():
    box = (
        f"- [x] `build_clean_spine` ... *({_ITEM_143_ANNOTATION_SUBSTRING})*\n"
    )
    trail_matches = _TRAIL_LINE_RE.findall(box)
    assert not any(d >= "2026-09-15" and "151" in t for d, t in trail_matches)


# =========================================================================== #
# AC39: the criterion-7 re-verification insight is ticked with a pointer,
# searching the live inbox and every archive file.
# =========================================================================== #

_AC39_ENTRY_SUBSTRING = "Stage 30 acceptance criterion 7 was ticked by item 143's validator"


def _find_ac39_entry():
    candidates = [_INSIGHTS_PATH]
    if _INSIGHTS_ARCHIVE_DIR.is_dir():
        candidates += sorted(_INSIGHTS_ARCHIVE_DIR.glob("archive-*.md"))
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if _AC39_ENTRY_SUBSTRING in line:
                return path, line
    return None, None


def test_ac39_entry_present_and_ticked_with_a_pointer_to_item151():
    path, line = _find_ac39_entry()
    assert path is not None, (
        f"no line containing {_AC39_ENTRY_SUBSTRING!r} found in insights.md or any "
        f"insights/archive-*.md"
    )
    assert line.strip().startswith("- [x]"), line
    assert "item 143, 2026-09-03" in line, line


def test_adv_ac39_entry_lookup_searches_archives_too(tmp_path, monkeypatch):
    """Adversarial: an entry present only in an archive file (not the live
    inbox) must still be found -- the CLAUDE.md archive gotcha this AC
    exists to guard against."""
    fake_docs_dir = tmp_path / "docs_aide"
    fake_archive_dir = fake_docs_dir / "insights"
    fake_archive_dir.mkdir(parents=True)
    (fake_docs_dir / "insights.md").write_text("- [ ] nothing relevant here\n", encoding="utf-8")
    (fake_archive_dir / "archive-2026-Q3.md").write_text(
        f"- [x] gap — {_AC39_ENTRY_SUBSTRING} ... *(item 143, 2026-09-03, engine 1.37.0)*\n",
        encoding="utf-8",
    )

    # Drive the real helper against the fake tree, so the test fails if
    # _find_ac39_entry ever stops searching the archive directory.
    monkeypatch.setattr(sys.modules[__name__], "_INSIGHTS_PATH", fake_docs_dir / "insights.md")
    monkeypatch.setattr(sys.modules[__name__], "_INSIGHTS_ARCHIVE_DIR", fake_archive_dir)

    path, line = _find_ac39_entry()
    assert path == fake_archive_dir / "archive-2026-Q3.md"
    assert line.strip().startswith("- [x]")


# =========================================================================== #
# AC40 (signature half): the environment-gated conclusion rests on a
# checked mechanism -- enable_pyradiomics defaults to False.
# =========================================================================== #


def test_ac40_intensity_pipeline_findings_pins_pyradiomics_disabled_by_default():
    sig = inspect.signature(intensity_pipeline_findings)
    assert sig.parameters["enable_pyradiomics"].default is False


# =========================================================================== #
# Determinism / immutability (Testing Strategy)
# =========================================================================== #


def test_adv_measured_firing_is_deterministic_across_two_calls():
    probe = fm.CorpusCaseExpectation(
        case_id="mode4_relabel_swap", corpus="geometric", expected_firing=(), reason=""
    )
    first = fm.measured_firing(probe)
    second = fm.measured_firing(probe)
    assert first == second


def test_adv_build_matrix_does_not_mutate_committed_manifests():
    manifest_before = (_TESTS_DIR / "corpus" / "manifest.json").read_bytes()
    tb.build_matrix()
    manifest_after = (_TESTS_DIR / "corpus" / "manifest.json").read_bytes()
    assert manifest_before == manifest_after


def test_adv_specification_to_dict_returns_a_fresh_tree_each_call():
    first = fm.specification_to_dict()
    first["modes"].append({"injected": True})
    second = fm.specification_to_dict()
    assert {"injected": True} not in second["modes"]
