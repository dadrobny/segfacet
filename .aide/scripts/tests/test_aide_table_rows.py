"""Issue #202: a `progress.md` table row its reader cannot use is an error.

Every reader of the four tables the engine reads — stage summary, objective
coverage, Outcome targets, human gates — reads a row only when its cells parse,
and skips the rest. What happened next used to depend on the table: a warning
for gates, and nothing at all for the other three, where the row that vanished
was often exactly the one a check exists to catch. Each case below is the
issue's measurement: a document whose check errors, then the same document
with that row mis-shaped — the error the row carried is gone, and the
unreadable-row error stands in its place, so the check still fails.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_table_rows", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


SUMMARY_ROW = "| 1 | Rule Engine | G2 | ✅ |"
OBJECTIVE_ROW = "| G2 Rules | Stage 1 | ✅ |"
TARGET_ROW = "| Held-out FPR <= 0.10 | G2 | Stage 1 | ❌ Not met | FPR 0.975 |"
GATE_ROW = "| Schema approved | all | ⏳ Awaiting | — |"
ENV_ROW = "| GPU path | torch | Stage 1 *(Item 002)* | ❓ Unverified | — |"


def _progress(summary=SUMMARY_ROW, objective=OBJECTIVE_ROW, target=TARGET_ROW,
              gate=GATE_ROW, env=ENV_ROW, deliverable="📋") -> str:
    return f"""\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 0 | Scaffolding | (foundation) | ✅ |
{summary}

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Setup | Stage 0 | ✅ |
{objective}

## Environment-Gated Capability Verification

| Capability | Package / Tool | Introduced by | Status | Notes |
|------------|-----------------|----------------|--------|-------|
{env}

## Outcome targets

| Target | Objective | Attempted by | Status | Evidence / follow-up |
|--------|-----------|--------------|--------|----------------------|
{target}

## Human gates

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
{gate}

## Stage 0 — Scaffolding — ✅

**Deliverables.**
- ✅ Package. *(Item 001)*

**Acceptance.**
- [x] It builds.

## Stage 1 — Rule Engine — ✅

**Deliverables.**
- ✅ Core. *(Item 002)*
- {deliverable} Bounds. *(Item 003)*

**Acceptance.**
- [ ] Rules fire.
"""


def _check(tmp_path: Path, progress: str):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "aide.toml").write_text(
        '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n', encoding="utf-8")
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "progress.md").write_text(progress, encoding="utf-8")
    return aide.run_checks(tmp_path, aide.load_config(tmp_path), branches=[])


def _line_of(text: str, row: str) -> int:
    return text.splitlines().index(row) + 1


# Per table: the document state under which its row makes the check raise an
# error, that error, and a mis-shaping of the row — a stray `|` in a cell, the
# usual cause — that used to take the error away without a word.
_OVER_CLAIM = "objective G2 marked ✅ but outcome target"
CASES = {
    "stage summary": (
        dict(), "summary marked ✅ but has non-complete deliverables",
        "summary", "| 1 | Rule | Engine | G2 | ✅ |", "has 5 cells, not 4"),
    "objective coverage": (
        dict(deliverable="✅"), _OVER_CLAIM,
        "objective", "| G2 Rules | Stage 1 | a | b | ✅ |", "has 5 cells, not 3"),
    "Outcome targets": (
        dict(deliverable="✅"), _OVER_CLAIM,
        "target", TARGET_ROW.replace("FPR 0.975", "FPR | 0.975"), "has 6 cells, not 5"),
}


@pytest.mark.parametrize("table", sorted(CASES))
def test_a_mis_shaped_row_trades_its_error_for_an_unreadable_row_error(
        tmp_path: Path, table: str):
    state, carried, slot, broken_row, problem = CASES[table]

    errors, _ = _check(tmp_path / "whole", _progress(**state))
    assert any(carried in e for e in errors), errors       # the baseline errors
    assert not any("is not read" in e for e in errors), errors

    doc = _progress(**{**state, slot: broken_row})
    errors, _ = _check(tmp_path / "broken", doc)
    assert not any(carried in e for e in errors), errors   # the row took it away
    lineno = _line_of(doc, broken_row)
    assert any(e.startswith(f"progress.md:{lineno}: {table} row {problem}")
               and "A '|' inside a cell is the usual cause." in e
               for e in errors), errors


def test_a_mis_shaped_gate_row_is_an_error_under_the_same_rule(tmp_path: Path):
    """The gates case, decided by the same rule rather than separately (#202):
    it used to be a warning, which never moves the exit code."""
    doc = _progress(deliverable="✅", gate="| Schema | all | ⏳ Awaiting | a | b |")
    errors, warnings = _check(tmp_path, doc)
    lineno = _line_of(doc, "| Schema | all | ⏳ Awaiting | a | b |")
    assert any(e.startswith(f"progress.md:{lineno}: human-gate row has 5 cells, not 4")
               for e in errors), errors
    assert not any("cells, not 4" in w for w in warnings)


@pytest.mark.parametrize("kwargs, problem", [
    (dict(summary="| 1a | Rule Engine | G2 | ✅ |"),
     "stage summary row has a Stage cell that is not an integer"),
    (dict(summary="| 1 | Rule Engine | G2 | done |"),
     "stage summary row has no status icon in its Status cell"),
    (dict(objective="| Rules | Stage 1 | ✅ |"),
     "objective coverage row has an Objective cell that does not start with a G<n> code"),
    (dict(objective="| G2 Rules | Stage 1 | done |"),
     "objective coverage row has no status icon in its Status cell"),
    (dict(target="|  | G2 | Stage 1 | ❌ Not met | FPR 0.975 |"),
     "Outcome targets row has an empty Target cell"),
])
def test_a_right_width_row_its_reader_still_cannot_use_is_named(kwargs, problem):
    """Width is the usual cause, not the only one: every reader also refuses a
    row whose key or Status cell it cannot read, and the error follows the
    reader rather than a column count. No `|` hint — it would mislead here."""
    errors = aide.unreadable_row_errors(_progress(**kwargs).splitlines())
    assert len(errors) == 1 and problem in errors[0], errors
    assert "usual cause" not in errors[0]


def test_the_well_formed_document_has_no_unreadable_row():
    assert aide.unreadable_row_errors(_progress().splitlines()) == []


def test_a_renamed_header_is_reported_and_says_what_a_header_reads():
    """A header is recognised by its first cell alone, so a retitled one is
    reported — fail closed — with the hint that explains it."""
    doc = _progress().replace("| Stage | Title |", "| # | Title |")
    errors = aide.unreadable_row_errors(doc.splitlines())
    assert len(errors) == 1, errors
    assert "above the separator — a header row's first cell reads 'Stage'" in errors[0]
    assert "usual cause" not in errors[0]


HEADERLESS_GATES = """\
## Human gates

| Schema approved | all | ⏳ Awaiting | — |
|------|--------|--------|---------------------|
"""


def test_a_headerless_tables_only_row_is_data_not_its_header():
    """Markdown's rule — the row above the separator is the header — would read
    a hand-raised `all` gate, written without the header, as furniture and drop
    it unreported. The first-cell rule reads it as the gate it is."""
    lines = (_progress(gate="").replace(
        "## Human gates\n\n| Gate | Blocks | Status | Decision / evidence |\n"
        "|------|--------|--------|---------------------|\n", HEADERLESS_GATES)
    ).splitlines()
    gates = aide.human_gates(lines)
    assert [g.blocks_all for g in gates] == [True]
    assert aide.unreadable_row_errors(lines) == []


def test_a_gate_titled_with_a_dash_is_read_not_taken_for_a_separator():
    """A separator is a row of delimiter cells — every cell, not the first."""
    lines = _progress(gate="| - | all | ⏳ Awaiting | — |").splitlines()
    assert [g.blocks_all for g in aide.human_gates(lines)] == [True]


def test_a_summary_under_another_heading_is_still_checked_row_by_row(tmp_path: Path):
    """The summary reader finds its rows by shape anywhere in the file, so the
    check has to find the table the same way when the template's heading is
    missing — otherwise a stray `|` under `## Stages` is #202 all over again."""
    broken = "| 1 | Rule | Engine | G2 | ✅ |"
    doc = _progress(summary=broken).replace("## Stage summary", "## Stages")
    errors, _ = _check(tmp_path, doc)
    assert any(e.startswith(f"progress.md:{_line_of(doc, broken)}: stage summary "
                            f"row has 5 cells, not 4") for e in errors), errors


def test_a_summary_away_from_its_present_but_empty_heading_is_checked(tmp_path: Path):
    """The heading can be there with the table under another one; the reader
    still finds the table by shape, so the check falls back to finding it the
    same way whenever the heading's section holds no readable row."""
    broken = "| 1 | Rule | Engine | G2 | ✅ |"
    doc = _progress(summary=broken).replace(
        "## Stage summary\n", "## Stage summary\n\nSee below.\n\n## Stages\n")
    errors, _ = _check(tmp_path, doc)
    assert any(e.startswith(f"progress.md:{_line_of(doc, broken)}: stage summary "
                            f"row has 5 cells, not 4") for e in errors), errors


def test_a_table_whose_every_row_is_unreadable_is_not_also_missing(tmp_path: Path):
    """The rows are reported one by one; "missing Stage summary table" on top
    would send the author looking for a table that is there."""
    doc = _progress(summary="| 1 | Rule Engine | G2 | done |").replace(
        "| 0 | Scaffolding | (foundation) | ✅ |", "| 0 | Scaffolding | — | done |")
    errors, _ = _check(tmp_path, doc)
    assert sum("stage summary row has no status icon" in e for e in errors) == 2, errors
    assert not any("missing Stage summary table" in e for e in errors), errors


def test_a_summary_written_without_leading_pipes_is_missing(tmp_path: Path):
    """Valid markdown, but no reader or writer of the table has ever taken a
    row without its leading `|` — its statuses were never checked — so the
    table is reported missing rather than passing as present."""
    doc = _progress().replace("| 0 | Scaffolding | (foundation) | ✅ |",
                              "0 | Scaffolding | (foundation) | ✅").replace(
        SUMMARY_ROW, "1 | Rule Engine | G2 | ✅")
    errors, _ = _check(tmp_path, doc)
    assert "progress.md: missing Stage summary table" in errors


def test_a_second_table_under_the_gates_heading_fails_closed():
    """Every `|` line under `## Human gates` is read as the gates table, so a
    side table there is reported — and holds claims — rather than a scope
    narrow enough to spare it being one a broken gates table could slip past."""
    lines = _progress().replace(
        GATE_ROW + "\n", GATE_ROW + "\n\n| Who | Role |\n|---|---|\n| Ana | lead |\n"
    ).splitlines()
    assert [n for n, _ in aide.unreadable_gate_rows(lines)] == [
        lines.index("| Who | Role |") + 1, lines.index("| Ana | lead |") + 1]


def test_with_the_heading_present_an_authors_own_table_is_left_alone():
    """Under the template heading the check reads that section only: a table of
    the author's own in a stage section is not a summary table to report on."""
    doc = _progress() + (
        "\n| Step | Owner | Notes | Status |\n|---|---|---|---|\n"
        "| 1 | Ana | first | ✅ |\n| Wrap-up | Ana | — | — |\n")
    assert aide.unreadable_row_errors(doc.splitlines()) == []


def test_a_target_naming_no_objective_is_read_and_gates_none():
    """A measured runtime or cost target may belong to no objective — a real
    consumer writes `—` there — so the row is read, gates nothing, and stays
    listed by `aide status`; it is not an unreadable row."""
    lines = _progress(target=TARGET_ROW.replace("| G2 |", "| — |")).splitlines()
    assert aide.unreadable_row_errors(lines) == []
    assert [t.objectives for t in aide.outcome_targets(lines)] == [[]]


def test_a_target_status_with_no_mark_stays_a_warning(tmp_path: Path):
    """The target reader reads such a row — its Status is table-local and
    warned on as unrecognised — so it is not an unreadable row."""
    doc = _progress(target=TARGET_ROW.replace("❌ Not met", "pending"))
    errors, warnings = _check(tmp_path, doc)
    assert not any("is not read" in e for e in errors), errors
    assert any("unrecognised Status" in w for w in warnings), warnings


def test_a_mis_shaped_environment_gated_row_is_no_error(tmp_path: Path):
    """The fifth table is read (issue #207) but gates no check, so its
    unusable row is a warning — `test_aide_capabilities.py` holds that half."""
    doc = _progress(env="| GPU | torch | Stage 1 | ❓ Unverified | a | b |")
    assert aide.unreadable_row_errors(doc.splitlines()) == []
    assert len(aide.unreadable_row_warnings(doc.splitlines())) == 1


def test_a_row_under_another_heading_is_not_the_tables_business():
    """The lint reads each table's own section and stops at the next heading,
    exactly as the readers do — a 5-cell row in the stage sections is prose."""
    doc = _progress() + "\n| a | b | c | d | e |\n"
    assert aide.unreadable_row_errors(doc.splitlines()) == []
