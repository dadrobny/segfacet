"""Stage 19 end-to-end validation + steering review (item 106).

Replays the four things Stage 19 shipped -- through the shipped mechanisms, not
the unit suite each item already exercises -- and closes the stage's two
mechanically-verifiable roadmap acceptance criteria (G7/box1, G8/box2)
honestly. Box 3 (the golden-decision-table sign-off) is read as a **gate**
here and never written (item 105's alone).

This module adds no production code of its own; the sole production edit this
item is authorised to make -- ``src/segfacet/feature_docs.py``'s
``STATUS_OVERRIDES`` mapping, per the 2026-07-27 amendment -- happens (if at
all) during Validation step 4b, outside this test module. Every Block-F test
below is written to be **green whether or not** that map is populated (AC25's
"no minimum override count" rule), so this module collects and passes
independent of the steering review's outcome.

Six blocks, matching the item spec's Acceptance Criteria:

- **Block A** (AC1, AC3, AC4) -- retired by item 236 (2026-10-17), with the
  box-tick tests of AC19, AC20, AC22 and AC24: they pinned the Stage 19
  section's ticks, icons and annotation wording in ``progress.md``, which
  ``aide progress archive`` moves out (the 2026-09-16 precedent).
- **Block B** (AC5-AC10) -- regeneration replay: the documented zero-argument
  and explicit-argument ``segfacet.catalogue.main`` invocations, the committed
  artifacts vs. a live build, the four-way entry-count agreement, and the
  status report's render + placeholder-degrade paths.
- **Block C** (AC11-AC16) -- drift replay: item 104's helpers imported flat
  and green on the current tree; the hermetic undocumented-feature injection
  (through item 103's AC16 seam, nested to match AC13's exact path shape)
  proving both item 104's reporter and the shipped ``strict=True`` mechanism
  fail and name the path; the revert restoring green; the real-source
  rehearsal transcript check.
- **Block D** (AC17-AC20) -- G8 measurement: every committed entry's status is
  from the fixed vocabulary; the three-way moded/unwired/mode-unmapped
  partition is exhaustive, disjoint, and its ``retune``/``retire`` counts tie
  out to ``len(STATUS_OVERRIDES)``; the two tick-implies-evidence annotation
  checks.
- **Block E** (AC21-AC24) -- the fences: the Environment-Gated table doesn't
  move, the nine corpus goldens are still present and Stage 21's bullet is
  still ``\U0001F4CB``, the Objective-coverage/Outcome-targets tables don't
  move.
- **Block F** (AC25-AC31) -- the steering review's judgments: the
  ``### Stage-19 steering review`` transcript heading exists and is honest;
  every *shipped* override is well-formed (AC26) and names a real catalogue
  path (AC27), both checked as plain loops that pass vacuously on an empty
  map; the **unconditional** hermetic injection proving the override
  mechanism changes ``status`` and nothing else (AC28/AC29); AC30 is verified
  by re-running Block B's/Block C's own tests on whatever tree state exists at
  collection time (no duplicate assertions -- see the item spec's Testing
  Strategy). AC2/AC23/AC31 are validator git-diff obligations, not pytests
  here -- see the item spec's Decisions & Trade-offs (three prior
  Windows-only CI breaks from a byte-hash scope fence, `insights.md`).

Adversarial / edge-case scenarios included: every ``stage19_signoff_state()``
parse edge named in the spec (box absent, unticked-with-note, ticked-without-
note, uppercase ``X``, a note on a wrapped continuation line, a note naming
the wrong document); the AC3 biconditional fed three named mixed states; a
missing ``status``/``failure_modes`` field and an ``unwired``-with-modes
combination in the committed-artifact partition (a legitimate bucket-(ii)
member per AC18's own definition -- see the module comment on
``_status_partition``); the ``N == 0`` floor; the
undocumented-feature injection run twice with the revert re-checked each time;
a non-``CatalogueError`` stub propagating out of ``strict_build_message``;
``normalise_leaf_path`` invariance across three radiomics-style names and two
labels; and, for Block F, every override malformation named in the spec
(``unwired``/``keep`` status, empty/short/status-echoing rationale, a bare
string or 3-tuple value, a key absent from ``FEATURE_DOCS``, a key present in
``FEATURE_DOCS`` but absent from the committed artifact, an empty map passing
vacuously, the same override applied twice being idempotent, and an override
on a ``keep`` entry with non-empty ``consuming_rules`` leaving them untouched).
"""

from __future__ import annotations

import copy
import dataclasses
import functools
import json
import re
import sys
import types
from pathlib import Path

import pytest

import segfacet.catalogue as catalogue_module
import segfacet.feature_docs as feature_docs_module
from segfacet.catalogue import (
    CatalogueError,
    FeatureDocMissing,
    build_catalogue,
    catalogue_to_dict,
    iter_driver_records,
    iter_leaf_paths,
    normalise_leaf_path,
    render_markdown,
)
from segfacet.feature_docs import FEATURE_DOCS

# Item 104's own module-level helpers, imported flat -- the style
# tests/test_102_stage18_validation.py:49 already uses, never the
# ``tests.``-qualified form (insights.md: that broke full-suite collection
# once already this queue).
from test_104_feature_catalogue_drift import (
    covered_paths,
    documented_paths,
    drift_report,
    iter_committed_entries,
    load_committed_catalogue,
    strict_build_message,
)

# =========================================================================== #
# Path constants -- no absolute path literal anywhere (insights.md's item-099
# entry documents exactly this bug class going undetected through the whole
# loop: Linux-green, Windows-red, invisible to every gate in this loop).
# =========================================================================== #

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_DOCS_AIDE = _REPO_ROOT / "docs" / "aide"
_PROGRESS_PATH = _DOCS_AIDE / "progress.md"
_ITEM_106_SPEC_PATH = _DOCS_AIDE / "items" / "106-validate-stage19.md"
_DEFAULT_JSON = _DOCS_AIDE / "feature_catalogue.generated.json"
_DEFAULT_MD = _DOCS_AIDE / "feature_catalogue.generated.md"
_ASR_MODULE_PATH = _REPO_ROOT / "scripts" / "aide_status_report.py"


def _read_progress() -> str:
    return _PROGRESS_PATH.read_text(encoding="utf-8")


def _read_spec() -> str:
    return _ITEM_106_SPEC_PATH.read_text(encoding="utf-8")


# =========================================================================== #
# Block A helpers (AC1-AC4): parsing progress.md's Stage-19 section, never
# assuming its content.
# =========================================================================== #

# Retired by item 236 (2026-10-17): the Stage 19 section tests pinned box ticks, bullet icons and annotation wording in progress.md, loop attestation state that 'aide progress archive' moves out of progress.md; their synthetic companions had no other subject.
# Removed: _CHECKBOX_RE, _EVIDENCE_NOTE_RE, _stage19_section, _acceptance_items, _acceptance_item_matching, _is_checked, _has_golden_decision_table_note, _signoff_state_from_text, stage19_signoff_state, _deliverable_blocks, _deliverable_block_for_item, _stage19_heading_line, _stage_summary_row_19, _ac3_flags, _check_biconditional, _minimal_box3_fragment, _synthetic_progress_md, test_ac1_real_progress_md_reports_signed_off, test_adv_signoff_state_box_absent_fails_naming_heading_and_found_items, test_adv_signoff_state_unticked_with_note_is_pending, test_adv_signoff_state_ticked_without_note_is_pending, test_adv_signoff_state_uppercase_x_with_note_is_signed_off, test_adv_signoff_state_note_on_wrapped_continuation_line_is_signed_off, test_adv_signoff_state_note_naming_wrong_document_is_pending, test_ac3_biconditional_holds_on_real_progress_md, test_ac3_biconditional_passes_in_both_consistent_states, test_adv_ac3_stage_heading_ok_but_signoff_pending_fails_naming_stage_heading, test_adv_ac3_signoff_signed_but_stage_still_planned_fails_naming_stage_heading, test_adv_ac3_box1_ticked_while_box2_and_signoff_are_not_fails_naming_box1, test_ac4_deliverable_bullets_are_ticked_when_signed_off, test_ac19_checkbox2_carries_honest_partition_if_ticked, test_ac20_checkbox1_carries_generated_and_can_fail_evidence_if_ticked, test_ac22_annotations_state_stage19_decides_stage21_executes_if_ticked, test_ac24_no_annotation_asserts_real_data_coverage.


# =========================================================================== #
# AC1: the sign-off state is parsed, never assumed
# =========================================================================== #


# =========================================================================== #
# AC2: this item never writes the sign-off checkbox or the decision table --
# a validator git-diff obligation (`git diff <merge-base>..HEAD -- ...`), not
# a pytest here. See the item spec's Decisions & Trade-offs: items 099-101
# each shipped a byte-hash scope fence and each produced a Windows-only CI
# break invisible to every gate in this loop.
# =========================================================================== #


# =========================================================================== #
# AC3: the stage cannot close while sign-off is pending -- a biconditional
# valid in both states, never `if signed_off: assert ...`.
# =========================================================================== #


# =========================================================================== #
# AC4: a stage does not close over an unfinished deliverable
# =========================================================================== #


# =========================================================================== #
# Shared fixtures (Testing Strategy: module-scoped, built once)
# =========================================================================== #


@pytest.fixture(scope="module")
def full_catalogue():
    return build_catalogue()


@pytest.fixture(scope="module")
def empty_overrides_catalogue():
    """The catalogue as it would be with STATUS_OVERRIDES = {} -- the correct
    "un-overridden counterpart" baseline for AC28/AC29's hermetic single-key
    override, as opposed to `full_catalogue`, which reflects the real,
    currently-shipped (non-empty) STATUS_OVERRIDES map."""
    empty_map = types.MappingProxyType({})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(feature_docs_module, "STATUS_OVERRIDES", empty_map)
        if hasattr(catalogue_module, "STATUS_OVERRIDES"):
            mp.setattr(catalogue_module, "STATUS_OVERRIDES", empty_map)
        return catalogue_module.build_catalogue()


@pytest.fixture(scope="module")
def committed_json_doc():
    return load_committed_catalogue()


@pytest.fixture(scope="module")
def committed_entries(committed_json_doc):
    return iter_committed_entries(committed_json_doc)


@pytest.fixture(scope="module")
def asr():
    import importlib.util

    spec = importlib.util.spec_from_file_location("aide_status_report_106", _ASR_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _entry(cat, path):
    for entry in cat.entries:
        if entry.path == path:
            return entry
    raise AssertionError(f"no catalogue entry for path {path!r}")


# =========================================================================== #
# AC5: the documented zero-argument regeneration moves nothing
# =========================================================================== #


def test_ac5_zero_argument_regeneration_moves_nothing():
    original_json = _DEFAULT_JSON.read_bytes()
    original_md = _DEFAULT_MD.read_bytes()
    try:
        exit_code = catalogue_module.main([])
        assert exit_code == 0
        assert _DEFAULT_JSON.read_bytes() == original_json
        assert _DEFAULT_MD.read_bytes() == original_md
    finally:
        _DEFAULT_JSON.write_bytes(original_json)
        _DEFAULT_MD.write_bytes(original_md)


# =========================================================================== #
# AC6: the explicit-argument regeneration reproduces the same bytes
# =========================================================================== #


def test_ac6_explicit_argument_regeneration_matches_committed(tmp_path):
    json_dest = tmp_path / "c.json"
    md_dest = tmp_path / "c.md"
    exit_code = catalogue_module.main(["--json", str(json_dest), "--md", str(md_dest)])
    assert exit_code == 0
    assert json_dest.read_bytes() == _DEFAULT_JSON.read_bytes()
    assert md_dest.read_bytes() == _DEFAULT_MD.read_bytes()


# =========================================================================== #
# AC7: the committed artifacts equal a live build
# =========================================================================== #


def test_ac7_committed_artifacts_equal_live_build(full_catalogue):
    committed_json = json.loads(_DEFAULT_JSON.read_text(encoding="utf-8"))
    assert catalogue_to_dict(full_catalogue) == committed_json
    committed_md = _DEFAULT_MD.read_text(encoding="utf-8")
    assert render_markdown(full_catalogue) == committed_md


# =========================================================================== #
# AC8: one entry count, agreed by four independent surfaces
# =========================================================================== #

_N_HEADER_RE = re.compile(r"# Feature & Rule Catalogue \((\d+) entries\)")


def test_ac8_entry_count_agreed_by_four_surfaces(full_catalogue, committed_entries):
    md_text = _DEFAULT_MD.read_text(encoding="utf-8")
    header_match = _N_HEADER_RE.search(md_text)
    assert header_match, "committed markdown header doesn't match '(N entries)'"
    n_header = int(header_match.group(1))

    table_rows = [l for l in md_text.splitlines() if l.strip().startswith("|")]
    n_rows = len(table_rows) - 2  # header row + separator row

    n_committed = len(committed_entries)
    n_live = len(full_catalogue.entries)

    assert n_header == n_rows == n_committed == n_live, (
        n_header,
        n_rows,
        n_committed,
        n_live,
    )
    assert n_header > 0


def test_adv_empty_catalogue_fails_the_n_greater_than_zero_floor():
    def _check_n(header_n, row_n, committed_n, live_n):
        assert header_n == row_n == committed_n == live_n
        assert header_n > 0

    with pytest.raises(AssertionError):
        _check_n(0, 0, 0, 0)


# =========================================================================== #
# AC9: the status report renders the generated catalogue, no manual editing
# =========================================================================== #


def test_ac9_status_report_renders_generated_catalogue_no_manual_editing(asr, full_catalogue):
    groups = asr.load_feature_catalog(asr.FEATURE_CATALOGUE_PATH)
    assert groups
    total_items = sum(len(g.items) for g in groups)
    assert total_items == len(full_catalogue.entries)

    section = asr._render_feature_catalog_section(groups)
    assert section.count('<div class="feature-group">') == len(groups)
    for entry in full_catalogue.entries:
        assert entry.path in section

    model = asr.build_report_model()
    html = asr.render_html(model)
    assert '<section id="features"' in html


# =========================================================================== #
# AC10: hiding the artifact degrades to the placeholder, live
# =========================================================================== #


def test_ac10_hiding_artifact_degrades_to_placeholder_live(asr, tmp_path, monkeypatch):
    missing_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(asr, "FEATURE_CATALOGUE_PATH", missing_path)

    groups = asr.load_feature_catalog(asr.FEATURE_CATALOGUE_PATH)
    assert groups == ()

    section = asr._render_feature_catalog_section(groups)
    assert str(missing_path) in section  # names the (patched) expected path
    assert "python -m segfacet.catalogue" in section

    model = asr.ReportModel(generated_at="now")
    html = asr.render_html(model)
    assert str(missing_path) in html


def test_ac10_undoing_monkeypatch_restores_populated_section(asr):
    groups = asr.load_feature_catalog(asr.FEATURE_CATALOGUE_PATH)
    assert groups


# =========================================================================== #
# Block C helpers (AC11-AC16): item 104's own helpers, item 103's AC16
# injection seam, nested to match AC13's exact normalised path shape.
# =========================================================================== #

_STAGE19_PROBE_KEY = "zzz_stage19_probe"
_STAGE19_PROBE_PATH = "per_label.{label}.geometry.zzz_stage19_probe"


def _driver_records_with_geometry_probe(catalogue_mod):
    """Reuses tests/test_103_feature_catalogue.py's AC16 seam --
    monkeypatching ``segfacet.catalogue.iter_driver_records`` -- but injects a
    *nested* ``per_label.<label>.geometry`` field (rather than test_103's own
    top-level-key injection) so the realised path matches AC13's exact
    normalised shape, ``per_label.{label}.geometry.zzz_stage19_probe``."""
    real = catalogue_mod.iter_driver_records

    def _fake():
        first = True
        for driver_id, record in real():
            if first and record.get("per_label"):
                record = copy.deepcopy(dict(record))
                label_key = next(iter(record["per_label"]))
                per_label_entry = dict(record["per_label"][label_key])
                per_label_entry["geometry"] = dict(per_label_entry.get("geometry", {}))
                per_label_entry["geometry"][_STAGE19_PROBE_KEY] = 1.0
                record["per_label"] = dict(record["per_label"])
                record["per_label"][label_key] = per_label_entry
                first = False
            yield driver_id, record

    return _fake


def _injected_realised_set(catalogue_mod):
    realised = set()
    for _driver_id, record in catalogue_mod.iter_driver_records():
        realised |= catalogue_mod.iter_leaf_paths(record)
    return realised


@pytest.fixture(scope="module")
def pre_injection_state():
    return {
        "covered": covered_paths(),
        "feature_docs_snapshot": copy.deepcopy(dict(FEATURE_DOCS)),
        "committed_snapshot": copy.deepcopy(load_committed_catalogue()),
    }


# =========================================================================== #
# AC11: item 104's check is green on the current tree, through its own
# helpers.
# =========================================================================== #


def test_ac11_all_drift_directions_and_strict_mechanism_are_clean():
    realised = covered_paths()
    documented = documented_paths()
    primary = drift_report(
        realised=realised,
        documented=documented,
        realised_label="realised by the record but absent from FEATURE_DOCS",
        documented_label="documented in FEATURE_DOCS but no longer produced by the record",
    )
    doc = load_committed_catalogue()
    entries = iter_committed_entries(doc)
    committed_record_paths = frozenset(
        e["path"] for e in entries if e.get("origin") == "record"
    )
    artifact_message = drift_report(
        realised=realised,
        documented=committed_record_paths,
        realised_label="realised by the record but missing from the committed artifact",
        documented_label="a record-tier entry in the committed artifact but no longer realised",
    )
    assert primary is None
    assert artifact_message is None
    assert strict_build_message(functools.partial(build_catalogue, strict=True)) is None


# =========================================================================== #
# AC12: the covered path set is invariant to the radiomics backend
# =========================================================================== #


@pytest.mark.parametrize(
    "name",
    ["original_firstorder_Mean", "original_glcm_Contrast", "some_arbitrary_name_123"],
)
@pytest.mark.parametrize("label", [3, 17])
def test_ac12_normalise_leaf_path_collapses_extended_regardless_of_backend(label, name):
    raw = f"per_label.{label}.intensity.extended.{name}"
    assert normalise_leaf_path(raw) == "per_label.{label}.intensity.extended.{radiomic}"


# =========================================================================== #
# AC13: a deliberately undocumented realised feature fails the drift report
# =========================================================================== #


def test_ac13_injected_undocumented_feature_fails_drift_naming_exact_path(monkeypatch):
    monkeypatch.setattr(
        catalogue_module,
        "iter_driver_records",
        _driver_records_with_geometry_probe(catalogue_module),
    )
    injected_realised = _injected_realised_set(catalogue_module)

    message = drift_report(
        realised=injected_realised,
        documented=frozenset(FEATURE_DOCS),
        realised_label="realised by the record but absent from FEATURE_DOCS",
        documented_label="documented in FEATURE_DOCS but no longer produced by the record",
    )
    assert message is not None
    assert _STAGE19_PROBE_PATH in message
    assert "src/segfacet/feature_docs.py" in message
    assert "python -m segfacet.catalogue" in message

    only_realised = injected_realised - frozenset(FEATURE_DOCS)
    assert only_realised == {_STAGE19_PROBE_PATH}


# =========================================================================== #
# AC14: the same injection makes the shipped strict mechanism fail
# =========================================================================== #


def test_ac14_injected_undocumented_feature_fails_strict_mechanism_named(monkeypatch):
    monkeypatch.setattr(
        catalogue_module,
        "iter_driver_records",
        _driver_records_with_geometry_probe(catalogue_module),
    )
    message = strict_build_message(functools.partial(catalogue_module.build_catalogue, strict=True))
    assert message is not None
    assert "FeatureDocMissing" in message
    assert _STAGE19_PROBE_PATH in message


def test_adv_non_catalogue_error_propagates_out_of_strict_build_message():
    def _stub():
        raise ValueError("not a catalogue error -- re-asserted here for AC14")

    with pytest.raises(ValueError):
        strict_build_message(_stub)


# =========================================================================== #
# AC15: the injection reverts cleanly and green is restored
# =========================================================================== #


def test_ac15_injection_reverts_cleanly_and_green_restored(pre_injection_state):
    assert covered_paths() == pre_injection_state["covered"]
    assert dict(FEATURE_DOCS) == pre_injection_state["feature_docs_snapshot"]
    assert load_committed_catalogue() == pre_injection_state["committed_snapshot"]

    realised = covered_paths()
    documented = documented_paths()
    doc = load_committed_catalogue()
    entries = iter_committed_entries(doc)
    committed_record_paths = frozenset(
        e["path"] for e in entries if e.get("origin") == "record"
    )
    primary = drift_report(
        realised=realised,
        documented=documented,
        realised_label="realised by the record but absent from FEATURE_DOCS",
        documented_label="documented in FEATURE_DOCS but no longer produced by the record",
    )
    artifact_message = drift_report(
        realised=realised,
        documented=committed_record_paths,
        realised_label="realised by the record but missing from the committed artifact",
        documented_label="a record-tier entry in the committed artifact but no longer realised",
    )
    assert primary is None
    assert artifact_message is None
    assert strict_build_message(functools.partial(build_catalogue, strict=True)) is None


def test_adv_injection_revert_and_drift_recheck_idempotent_across_two_cycles():
    results = []
    for _ in range(2):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                catalogue_module,
                "iter_driver_records",
                _driver_records_with_geometry_probe(catalogue_module),
            )
            injected_realised = _injected_realised_set(catalogue_module)
            message = drift_report(
                realised=injected_realised,
                documented=frozenset(FEATURE_DOCS),
                realised_label="realised by the record but absent from FEATURE_DOCS",
                documented_label="documented in FEATURE_DOCS but no longer produced by the record",
            )
        post_revert = drift_report(
            realised=covered_paths(),
            documented=documented_paths(),
            realised_label="A",
            documented_label="B",
        )
        results.append((message, post_revert))

    assert results[0] == results[1]
    for message, post_revert in results:
        assert message is not None
        assert _STAGE19_PROBE_PATH in message
        assert post_revert is None


# =========================================================================== #
# AC16: the real-source rehearsal is executed and transcribed at its true
# strength.
# =========================================================================== #


def test_ac16_real_source_rehearsal_transcript_present_and_honest():
    text = _read_spec()
    heading = "### Real-source drift rehearsal"
    idx = text.find(heading)
    assert idx != -1, "spec is missing the '### Real-source drift rehearsal' heading"
    nxt_h3 = text.find("\n### ", idx + 1)
    nxt_h2 = text.find("\n## ", idx + 1)
    ends = [e for e in (nxt_h3, nxt_h2) if e != -1]
    section = text[idx : min(ends) if ends else len(text)]
    assert "zzz_drift_probe" in section or "not executed" in section


# =========================================================================== #
# Block D (AC17-AC20): the status/mode partition, measured on the committed
# artifact.
# =========================================================================== #

_STATUS_VOCABULARY = {"keep", "retune", "retire", "unwired"}


def test_ac17_every_committed_entry_status_in_fixed_vocabulary(committed_entries):
    for entry in committed_entries:
        status = entry.get("status") if isinstance(entry, dict) else None
        assert status in _STATUS_VOCABULARY, entry.get("path") if isinstance(entry, dict) else entry
    assert len(committed_entries) > 0


def _status_partition(entries):
    """AC18: partition *entries* into (moded, unwired, mode_unmapped), per the
    AC's own bucket definitions -- (i) moded: status != 'unwired' and
    failure_modes non-empty; (ii) unwired: status == 'unwired' (independent of
    failure_modes -- a path can be §6-mode-anchored via MODE_ANCHOR_PATHS with
    no rule/other consumer, e.g. the committed
    'stage3.monotonic_consistency.is_monotonic' entry, mode 4; that is a
    legitimate bucket-(ii) member, not a disjointness conflict); (iii)
    statused-but-mode-unmapped: status != 'unwired' and failure_modes empty.
    Fails with a named path on a missing field, never a KeyError."""
    moded, unwired, mode_unmapped = [], [], []
    for entry in entries:
        path = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(entry, dict) or "status" not in entry or "failure_modes" not in entry:
            pytest.fail(f"committed catalogue entry {path!r} missing 'status' or 'failure_modes'")
        status = entry["status"]
        if status not in _STATUS_VOCABULARY:
            pytest.fail(f"committed catalogue entry {path!r} has invalid status {status!r}")
        modes = entry["failure_modes"]
        if status == "unwired":
            unwired.append(entry)
        elif modes:
            moded.append(entry)
        else:
            mode_unmapped.append(entry)
    return moded, unwired, mode_unmapped


def test_ac18_status_mode_partition_exhaustive_disjoint_and_measured(committed_entries):
    moded, unwired, mode_unmapped = _status_partition(committed_entries)
    assert len(moded) + len(unwired) + len(mode_unmapped) == len(committed_entries)

    retune_count = sum(1 for e in committed_entries if e.get("status") == "retune")
    retire_count = sum(1 for e in committed_entries if e.get("status") == "retire")
    assert retune_count + retire_count == len(feature_docs_module.STATUS_OVERRIDES)


def test_adv_unwired_entry_with_nonempty_modes_is_bucketed_as_unwired_not_a_conflict():
    # Real committed data contains exactly this combination (a §6 mode can be
    # anchored via MODE_ANCHOR_PATHS on a path with no rule/other consumer --
    # see stage3.monotonic_consistency.is_monotonic, mode 4, status
    # "unwired"), so this is a legitimate bucket-(ii) member per AC18's own
    # definition, not a disjointness violation.
    entries = [{"path": "adv.unwired.with.modes", "status": "unwired", "failure_modes": [3]}]
    moded, unwired, mode_unmapped = _status_partition(entries)
    assert unwired == entries
    assert moded == []
    assert mode_unmapped == []


def test_adv_missing_status_field_fails_naming_path_not_keyerror():
    entries = [{"path": "adv.missing.status", "failure_modes": []}]
    with pytest.raises(pytest.fail.Exception) as excinfo:
        _status_partition(entries)
    assert "adv.missing.status" in str(excinfo.value)


def test_adv_missing_failure_modes_field_fails_naming_path_not_keyerror():
    entries = [{"path": "adv.missing.modes", "status": "keep"}]
    with pytest.raises(pytest.fail.Exception) as excinfo:
        _status_partition(entries)
    assert "adv.missing.modes" in str(excinfo.value)


# =========================================================================== #
# Block E (AC21-AC24): the fences
# =========================================================================== #


def _markdown_section(text: str, heading: str) -> str:
    idx = text.find(heading)
    assert idx != -1, f"heading {heading!r} not found in progress.md"
    nxt = text.find("\n## ", idx + 1)
    return text[idx : nxt if nxt != -1 else len(text)]


def _table_data_rows(section: str) -> list:
    lines = [l for l in section.splitlines() if l.strip().startswith("|")]
    return lines[2:]  # drop header row + separator row


def _row_cells(row_line: str) -> list:
    return [c.strip() for c in row_line.strip().strip("|").split("|")]


_ENV_TABLE_ROW_COUNT = 8
# Pinned at authoring time (item 106, pre-execution): (capability name prefix,
# status-cell icon) for every row of the Environment-Gated Capability
# Verification table. Compared as normalised text (read_text, never
# read_bytes) -- progress.md is not LF-pinned in .gitattributes, so a
# byte-level comparison would be a Windows-CRLF false positive (the same
# class of bug insights.md's item-100/101 entries describe).
_ENV_TABLE_STATUS_SNAPSHOT = (
    ("Real VerSe GT reference distributions", "✅"),
    ("Radiomics feature extraction", "✅"),
    ("Containerised pipeline (Docker build + run)", "✅"),
    # Re-pinned 2026-09-16 (engine 1.52.1): engine 1.51.0 accepts only
    # "✅ Verified" / "❓ Unverified" in the Status cell, so the row that read
    # "⏸️ Out of scope" now reads "❓ Unverified (out of scope since 2026-07-25)".
    ("XNAT Container Service command on a real server", "❓"),
    ("Real automatic-segmentation failure corpus", "❓"),
    ("GPU-accelerated feature extraction", "✅"),
    ("Real SPINEPS-output label-convention round-trip", "❓"),
    ("Real segmentation-tool run-vs-run per-mode comparison", "❓"),
)


def test_ac21_environment_gated_table_row_count_and_status_cells_unchanged():
    text = _read_progress()
    section = _markdown_section(text, "## Environment-Gated Capability Verification")
    rows = _table_data_rows(section)
    assert len(rows) == _ENV_TABLE_ROW_COUNT, len(rows)
    for row_line, (expected_name, expected_status_icon) in zip(rows, _ENV_TABLE_STATUS_SNAPSHOT):
        cells = _row_cells(row_line)
        assert cells[0].startswith(expected_name), cells[0]
        assert cells[3].startswith(expected_status_icon), cells[3]


def test_ac22_nine_goldens_match_corpus_case_ids(tmp_path):
    """Item 126 re-pointed this at a regeneration -- the committed
    corpus-golden snapshot store this used to glob was retired, see
    docs/aide/golden-decision-table.md's "## Retirement execution log". The
    harness (write_goldens) survives and is exercised here into a fresh
    caller-supplied directory instead."""
    from segfacet.synth.golden import write_goldens

    out_dir = tmp_path / "regen_ac22"
    write_goldens(out_dir)
    files = sorted(out_dir.glob("*.json"))
    stems = {f.stem for f in files}
    manifest = json.loads((_TESTS_DIR / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    case_ids = {c["case_id"] for c in manifest["cases"]}
    assert len(case_ids) >= 9  # the original nine, plus item 150's cases
    assert len(files) == len(case_ids)
    assert stems == case_ids


# =========================================================================== #
# Block F (AC25-AC31): the steering review's judgments. Every test below runs
# unconditionally -- an empty STATUS_OVERRIDES is the honest-review outcome
# and must be green end to end (AC25's "no minimum override count" rule).
# =========================================================================== #


def test_ac25_steering_review_heading_present_and_honest():
    text = _read_spec()
    decisions_heading = "## Decisions & Trade-offs"
    decisions_idx = text.find(decisions_heading)
    assert decisions_idx != -1, "spec is missing the '## Decisions & Trade-offs' heading"
    heading = "### Stage-19 steering review"
    idx = text.find(heading, decisions_idx)
    assert idx != -1, "spec is missing the '### Stage-19 steering review' heading"
    assert idx > decisions_idx
    nxt_h3 = text.find("\n### ", idx + 1)
    nxt_h2 = text.find("\n## ", idx + 1)
    ends = [e for e in (nxt_h3, nxt_h2) if e != -1]
    section = text[idx : min(ends) if ends else len(text)]

    overrides = feature_docs_module.STATUS_OVERRIDES
    if overrides:
        # Item 215 fence (e): the 106 record predates the taxonomy migration, so
        # each key is looked up as its pre-migration path, translated back
        # through the signed table.
        from feature_taxonomy_mapping import read_mapping

        new_to_old = {new: old for old, new, change, _by in read_mapping() if change in ("kept", "moved")}
        # Item 216: a survivor also stands for the row merged onto it, and the
        # 106 record transcribed the merged row's override (the survivor
        # pairs.adjacent.spacings_mm[] takes stage3.spacing_consistency.
        # spacings_mm[]'s), so that old path is accepted too.
        merged_old: dict = {}
        for old, new, change, _by in read_mapping():
            if change == "merged":
                merged_old.setdefault(new, []).append(old)
        report_only = re.compile(
            r"^reference_delta\.\{label\}\.features\."
            r"(?:extent_x_mm|extent_y_mm|extent_z_mm|spline_offset_mm)\.[a-z_]+$"
        )
        for key in overrides:
            p = new_to_old.get(key, key)
            if report_only.match(p):
                counterpart = re.sub(r"\.features\.[a-z_0-9]+\.", ".features.physical_volume_mm3.", key, count=1)
                assert overrides[key] == overrides[counterpart], (
                    f"override {key!r} differs from its physical_volume_mm3 counterpart {counterpart!r}"
                )
                p = new_to_old.get(counterpart, counterpart)
            assert any(c in section for c in [p, *merged_old.get(key, [])]), (
                f"override key {key!r} (pre-migration {p!r}) not transcribed in the steering-review section"
            )
    else:
        assert "no override recorded" in section


def _ac26_errors(status_overrides) -> list:
    """AC26: plain loop over *status_overrides*, vacuously true on an empty
    map -- no minimum override count is required."""
    errors = []
    for path, value in status_overrides.items():
        if not (isinstance(value, tuple) and len(value) == 2):
            errors.append(f"{path!r}: override value must be a 2-tuple (status, rationale); got {value!r}")
            continue
        status, rationale = value
        if status not in ("retune", "retire"):
            errors.append(f"{path!r}: status must be 'retune' or 'retire'; got {status!r}")
        if not isinstance(rationale, str):
            errors.append(f"{path!r}: rationale must be a str; got {rationale!r}")
            continue
        stripped = rationale.strip()
        if not stripped or len(stripped) < 20:
            errors.append(f"{path!r}: rationale {rationale!r} must be non-empty and >=20 chars")
        elif stripped == status or stripped.lower() in {"retune", "retire", "n/a", "tbd", "see review"}:
            errors.append(f"{path!r}: rationale {rationale!r} merely restates the status")
    return errors


def _ac27_errors(status_overrides, feature_docs_map, catalogue_paths, committed_paths) -> list:
    """AC27: plain loop over *status_overrides*, vacuously true on an empty
    map."""
    errors = []
    for path in status_overrides:
        if path not in feature_docs_map:
            errors.append(f"{path!r}: not present in FEATURE_DOCS")
            continue
        matches_live = [p for p in catalogue_paths if p == path]
        if len(matches_live) != 1:
            errors.append(
                f"{path!r}: matches {len(matches_live)} entries of build_catalogue() (expected exactly 1)"
            )
        matches_committed = [p for p in committed_paths if p == path]
        if len(matches_committed) != 1:
            errors.append(
                f"{path!r}: matches {len(matches_committed)} entries of the committed "
                "catalogue (expected exactly 1)"
            )
    return errors


def test_ac26_shipped_overrides_are_well_formed():
    assert _ac26_errors(feature_docs_module.STATUS_OVERRIDES) == []


def test_ac27_shipped_override_keys_name_real_catalogue_paths(full_catalogue, committed_entries):
    catalogue_paths = [e.path for e in full_catalogue.entries]
    committed_paths = [e["path"] for e in committed_entries]
    errors = _ac27_errors(
        feature_docs_module.STATUS_OVERRIDES,
        feature_docs_module.FEATURE_DOCS,
        catalogue_paths,
        committed_paths,
    )
    assert errors == []


def test_adv_ac26_ac27_empty_map_passes_vacuously():
    assert _ac26_errors({}) == []
    assert _ac27_errors({}, feature_docs_module.FEATURE_DOCS, [], []) == []


def test_adv_ac26_unwired_status_rejected():
    errors = _ac26_errors({"adv.unwired.status": ("unwired", "x" * 25)})
    assert any("adv.unwired.status" in e for e in errors)


def test_adv_ac26_keep_status_rejected():
    errors = _ac26_errors({"adv.keep.status": ("keep", "x" * 25)})
    assert any("adv.keep.status" in e for e in errors)


@pytest.mark.parametrize("rationale", ["", "   ", "retire", "TBD", "x" * 19])
def test_adv_ac26_bad_rationale_rejected(rationale):
    errors = _ac26_errors({"adv.bad.rationale": ("retire", rationale)})
    assert any("adv.bad.rationale" in e for e in errors)


def test_adv_ac26_bare_string_value_rejected():
    errors = _ac26_errors({"adv.bare.string": "retire"})
    assert any("adv.bare.string" in e for e in errors)


def test_adv_ac26_three_tuple_value_rejected():
    errors = _ac26_errors(
        {"adv.three.tuple": ("retire", "a rationale of at least twenty characters", "extra")}
    )
    assert any("adv.three.tuple" in e for e in errors)


def test_adv_ac27_key_absent_from_feature_docs():
    errors = _ac27_errors(
        {"not.a.real.path.at.all.item106": ("retire", "x" * 25)},
        feature_docs_module.FEATURE_DOCS,
        [],
        [],
    )
    assert any("not.a.real.path.at.all.item106" in e for e in errors)


def test_adv_ac27_key_present_in_feature_docs_absent_from_committed():
    real_path = next(iter(feature_docs_module.FEATURE_DOCS))
    errors = _ac27_errors(
        {real_path: ("retire", "x" * 25)},
        feature_docs_module.FEATURE_DOCS,
        [real_path],
        [],
    )
    assert any(real_path in e for e in errors)


def _first_keep_and_unwired_paths():
    cat = build_catalogue()
    keep_path = next(e.path for e in cat.entries if e.status == "keep")
    unwired_path = next(e.path for e in cat.entries if e.status == "unwired")
    return keep_path, unwired_path


_AC28_KEEP_PATH, _AC28_UNWIRED_PATH = _first_keep_and_unwired_paths()


@pytest.mark.parametrize("target_path", [_AC28_KEEP_PATH, _AC28_UNWIRED_PATH], ids=["keep", "unwired"])
def test_ac28_ac29_hermetic_override_changes_only_status(target_path, empty_overrides_catalogue):
    """AC28/AC29: runs unconditionally, regardless of what the live steering
    review decided -- it is the proof that build_catalogue() actually reads
    STATUS_OVERRIDES.

    The baseline for "every other entry equals its un-overridden counterpart"
    is the catalogue built with STATUS_OVERRIDES = {} (empty_overrides_catalogue),
    not full_catalogue -- full_catalogue reflects the real, currently-shipped
    overrides, so comparing against it would spuriously fail for every path
    that carries a real override other than target_path.
    """
    baseline_by_path = {e.path: e for e in empty_overrides_catalogue.entries}
    shipped_snapshot = dict(feature_docs_module.STATUS_OVERRIDES)
    rationale = "test-only AC28/AC29 probe rationale, at least twenty characters"
    override_map = types.MappingProxyType({target_path: ("retire", rationale)})

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(feature_docs_module, "STATUS_OVERRIDES", override_map)
        if hasattr(catalogue_module, "STATUS_OVERRIDES"):
            mp.setattr(catalogue_module, "STATUS_OVERRIDES", override_map)
        overridden = catalogue_module.build_catalogue()

    overridden_by_path = {e.path: e for e in overridden.entries}

    # (i) the assertion that fails if build_catalogue ignores the map.
    target_entry = overridden_by_path[target_path]
    assert target_entry.status == "retire"

    # (ii) every other field of that entry equals the un-overridden build's.
    baseline_entry = baseline_by_path[target_path]
    for field in dataclasses.fields(target_entry):
        if field.name == "status":
            continue
        assert getattr(target_entry, field.name) == getattr(baseline_entry, field.name), (
            target_path,
            field.name,
        )

    # (iii) every other entry compares equal field-for-field.
    assert overridden_by_path.keys() == baseline_by_path.keys()
    for path, entry in overridden_by_path.items():
        if path == target_path:
            continue
        assert entry == baseline_by_path[path], path

    assert dict(feature_docs_module.STATUS_OVERRIDES) == shipped_snapshot


def _first_keep_with_consuming_rules_path():
    cat = build_catalogue()
    return next(e.path for e in cat.entries if e.status == "keep" and e.consuming_rules)


_AC28_KEEP_WITH_RULES_PATH = _first_keep_with_consuming_rules_path()


def test_adv_override_on_keep_entry_with_consuming_rules_preserves_them(full_catalogue):
    baseline_by_path = {e.path: e for e in full_catalogue.entries}
    baseline_entry = baseline_by_path[_AC28_KEEP_WITH_RULES_PATH]
    assert baseline_entry.consuming_rules  # sanity: the fixture really has rules

    rationale = "adversarial probe: retirement must not erase the rule-read record"
    override_map = types.MappingProxyType({_AC28_KEEP_WITH_RULES_PATH: ("retire", rationale)})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(feature_docs_module, "STATUS_OVERRIDES", override_map)
        if hasattr(catalogue_module, "STATUS_OVERRIDES"):
            mp.setattr(catalogue_module, "STATUS_OVERRIDES", override_map)
        overridden = catalogue_module.build_catalogue()

    entry = next(e for e in overridden.entries if e.path == _AC28_KEEP_WITH_RULES_PATH)
    assert entry.status == "retire"
    assert entry.consuming_rules == baseline_entry.consuming_rules


def test_adv_same_override_applied_twice_is_idempotent():
    rationale = "idempotence probe rationale of at least twenty characters here"
    override_map = types.MappingProxyType({_AC28_KEEP_PATH: ("retire", rationale)})
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(feature_docs_module, "STATUS_OVERRIDES", override_map)
        if hasattr(catalogue_module, "STATUS_OVERRIDES"):
            mp.setattr(catalogue_module, "STATUS_OVERRIDES", override_map)
        first = catalogue_module.build_catalogue()
        second = catalogue_module.build_catalogue()
    assert first == second


def test_ac29_committed_artifacts_reflect_shipped_overrides_if_any(committed_entries):
    overrides = feature_docs_module.STATUS_OVERRIDES
    if not overrides:
        return
    committed_by_path = {e["path"]: e for e in committed_entries}
    md_text = _DEFAULT_MD.read_text(encoding="utf-8")
    for path, (status, _rationale) in overrides.items():
        entry = committed_by_path.get(path)
        assert entry is not None, path
        assert entry.get("status") == status, path
        row = next((l for l in md_text.splitlines() if l.strip().startswith(f"| {path} |")), None)
        assert row is not None, path
        assert row.rstrip().endswith(f"| {status} |"), row


# AC30: the post-override re-check reuses Block B's (AC5/AC6/AC7) and Block
# C's (AC11) own tests -- they run unconditionally against whatever tree
# state exists at test time, so re-evaluating them *is* AC30's evidence
# rather than a duplicate of it (Testing Strategy: "reuse Block B's and Block
# C's fixtures rather than duplicating them"). No separate test is added
# here; `git status --short docs/aide/` being empty when the item finishes is
# a Validation-step / validator observation, not a pytest assertion.

# AC31: the production-code widening is exactly one mapping -- a validator
# git-diff obligation (`git diff <merge-base>..HEAD -- src/segfacet/feature_docs.py`),
# not a pytest here. See AC2's note above and the item spec's Decisions &
# Trade-offs.
