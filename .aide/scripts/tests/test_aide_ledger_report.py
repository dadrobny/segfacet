"""`aide ledger report` — the run ledger read back (issue #251, §1 → ``ledger.md``).

Two layers. ``ledger_report`` is pure — a function of the ledger's text — so
the readings are asserted on it directly; the verb is driven through ``main``
over a document tree with no git, since it reads one file and writes nothing.

Asserted on the returned numbers and on exit codes and effects, never on
prose. The sentences ``test_aide_help_pins.py`` pins from ``aide ledger -h``
are claims about behaviour, and the tests it names as their guards are here.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_ledger_report", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

_TEMPLATE = (_MODULE_PATH.parents[1] / "templates" / "ledger.md").read_text(
    encoding="utf-8")


def _row(item="001", queue="001", stage="2", kind="normal", outcome="merged",
         acs="3", tests="6", files="4", rounds="2", blocking="0", minor="1",
         nit="0", engine="2.26.0", date="2026-09-30", suite="41",
         inherited="0", width=16) -> str:
    cells = [item, queue, stage, kind, outcome, acs, tests, files, rounds,
             blocking, minor, nit, engine, date, suite, inherited][:width]
    return "| " + " | ".join(cells) + " |"


def _ledger(*rows: str) -> str:
    """The template as the engine creates it — example row in the header
    comment included — with *rows* appended."""
    return _TEMPLATE + "".join(r + "\n" for r in rows)


def _groups(report: dict) -> dict:
    return {(c["engine"], c["kind"]): c for c in report["cohorts"]}


def _repo(tmp_path: Path, ledger: str = None) -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text('[project]\ndocs_dir = "docs/aide"\n',
                                    encoding="utf-8")
    if ledger is not None:
        (ddir / "ledger.md").write_text(ledger, encoding="utf-8")
    return repo


# --------------------------------------------------------------------------- #
# grouping
# --------------------------------------------------------------------------- #
def test_rows_are_grouped_by_engine_cell_and_within_it_by_kind():
    report = aide.ledger_report(_ledger(
        _row(item="001", engine="2.1.0", kind="maintenance"),
        _row(item="002", engine="2.1.0", kind="normal"),
        _row(item="003", engine="2.1.0", kind="normal"),
        _row(item="004", engine="2.20.1", kind="validate-stage", stage="3"),
        _row(item="005", engine="2.3.0", kind="normal")))
    assert [(c["engine"], c["kind"], c["rows"]) for c in report["cohorts"]] == [
        ("2.1.0", "normal", 2), ("2.1.0", "maintenance", 1),
        ("2.3.0", "normal", 1), ("2.20.1", "validate-stage", 1)]
    assert _groups(report)[("2.20.1", "validate-stage")]["stages"] == ["3"]
    # The template's own example row, inside its header comment, is no item.
    assert report["rows"] == 5


def test_an_engine_cell_is_a_cohort_as_written():
    report = aide.ledger_report(_ledger(_row(engine=""), _row(engine="2.26.0")))
    assert {c["engine"] for c in report["cohorts"]} == {"", "2.26.0"}


def test_every_ratio_carries_its_n_and_counts_the_outcomes():
    report = aide.ledger_report(_ledger(
        _row(item="001", rounds="1", acs="2", tests="4", minor="2"),
        _row(item="002", rounds="3", acs="4", tests="2", minor="0",
             outcome="abandoned")))
    (g,) = report["cohorts"]
    assert (g["merged"], g["abandoned"]) == (1, 1)
    assert g["rounds"] == {"per_item": 2.0, "n": 2, "max": 3,
                           "histogram": {"1": 1, "3": 1}}
    assert g["tests_per_ac"] == {"value": 1.0, "n": 2}
    assert g["findings"]["minor"] == {"per_item": 1.0, "n": 2}


def test_rounds_are_a_distribution_and_not_a_share_at_the_cap():
    report = aide.ledger_report(_ledger(
        *(_row(item=f"{n:03d}", rounds=r) for n, r in
          enumerate(["1", "1", "2", "3", "5"], start=1))))
    (g,) = report["cohorts"]
    assert g["rounds"]["histogram"] == {"1": 2, "2": 1, "3": 1, "5": 1}
    assert "at_cap" not in g["rounds"]


# --------------------------------------------------------------------------- #
# the cell semantics §1 → ledger.md defines
# --------------------------------------------------------------------------- #
def test_a_blank_cell_joins_no_ratio_and_is_counted_unrecorded():
    report = aide.ledger_report(_ledger(
        _row(item="001", rounds="", blocking="", minor="", nit="", acs=""),
        _row(item="002", rounds="2", blocking="1", minor="0", nit="0")))
    (g,) = report["cohorts"]
    assert g["rounds"] == {"per_item": 2.0, "n": 1, "max": 2,
                           "histogram": {"2": 1}}
    assert g["findings"]["blocking"] == {"per_item": 1.0, "n": 1}
    assert g["tests_per_ac"]["n"] == 1
    assert g["unrecorded"]["Rounds"] == 1 and g["unrecorded"]["ACs"] == 1
    assert g["caller_blank"] == {"blank": 4, "cells": 8}


def test_a_no_review_finding_cell_joins_no_finding_ratio():
    report = aide.ledger_report(_ledger(
        _row(item="001", blocking="-", minor="-", nit="-"),
        _row(item="002", blocking="2", minor="0", nit="0")))
    (g,) = report["cohorts"]
    assert g["findings"]["blocking"] == {"per_item": 2.0, "n": 1}
    assert g["no_review"] == 1
    # Neither counted as blank: `-` is the engine's answer, not a gap.
    assert g["caller_blank"] == {"blank": 0, "cells": 5}


def test_a_merged_row_with_zero_tests_and_zero_files_is_unrecorded_not_zero():
    report = aide.ledger_report(_ledger(
        _row(item="001", tests="0", files="0", acs="5"),
        _row(item="002", tests="0", files="3", acs="2"),
        _row(item="003", tests="0", files="0", acs="4", outcome="abandoned")))
    (g,) = report["cohorts"]
    assert g["unknown_diff"] == 1
    assert (g["unrecorded"]["Tests"], g["unrecorded"]["Files"]) == (1, 1)
    # Items 002 and 003 are measurements of zero; 001 is lost data.
    assert g["tests_per_ac"] == {"value": 0.0, "n": 2}


def test_a_repeat_merged_row_with_a_zero_diff_is_left_out_and_the_earlier_counts():
    duplicate = _row(item="007", engine="2.20.1", tests="0", files="0",
                     rounds="2", suite="31")
    text = _ledger(
        _row(item="007", engine="2.20.1", tests="5", files="3", rounds="2",
             acs="5"),
        _row(item="008", engine="2.20.1", tests="4", files="2", acs="4"),
        duplicate)
    report = aide.ledger_report(text)
    (g,) = report["cohorts"]
    assert g["rows"] == 2
    assert report["counted_once"] == [text.splitlines().index(duplicate) + 1]
    # The earlier row's cells are the ones read: no diff is lost.
    assert g["unknown_diff"] == 0 and g["unrecorded"]["Tests"] == 0
    assert g["tests_per_ac"] == {"value": 1.0, "n": 2}


def test_a_reopened_item_merged_twice_keeps_both_rows():
    # A second merged row with a real diff is a reopen, whatever the engine.
    report = aide.ledger_report(_ledger(
        _row(item="007", engine="2.20.1"), _row(item="007", engine="2.20.1")))
    assert report["counted_once"] == [] and report["rows"] == 2
    # A lone merged 0/0 row, with no earlier merge of the item, is kept and
    # read as unrecorded; so is an abandoned row before a 0/0 merge.
    report = aide.ledger_report(_ledger(
        _row(item="007", outcome="abandoned"),
        _row(item="007", tests="0", files="0"),
        _row(item="009", queue="002"), _row(item="009", queue="003",
                                            tests="0", files="0")))
    assert report["counted_once"] == [] and report["rows"] == 4
    assert report["cohorts"][0]["unknown_diff"] == 2


def test_finding_ratios_are_withheld_from_a_group_before_1_59_0():
    report = aide.ledger_report(_ledger(
        _row(item="001", engine="1.58.0", blocking="", minor="", nit=""),
        _row(item="002", engine="1.59.0", blocking="1", minor="0", nit="0"),
        _row(item="003", engine="", blocking="1", minor="0", nit="0")))
    groups = _groups(report)
    old = groups[("1.58.0", "normal")]
    assert old["findings"] is None and old["no_review"] is None
    assert old["unrecorded"]["Blocking"] is None
    # Rounds still count, and the withheld cells are no blank.
    assert old["caller_blank"] == {"blank": 0, "cells": 1}
    assert old["rounds"]["n"] == 1
    assert groups[("1.59.0", "normal")]["findings"]["blocking"]["n"] == 1
    assert groups[("", "normal")]["findings"] is None


def test_the_1_59_0_boundary_compares_versions_not_strings():
    """"1.9.0" sorts after "1.59.0" as a string and "1.100.0" before it."""
    groups = _groups(aide.ledger_report(_ledger(
        _row(item="001", engine="1.9.0"), _row(item="002", engine="1.100.0"))))
    assert groups[("1.9.0", "normal")]["findings"] is None
    assert groups[("1.100.0", "normal")]["findings"]["blocking"]["n"] == 1


def test_a_row_with_no_criterion_joins_no_tests_per_criterion():
    (g,) = aide.ledger_report(_ledger(
        _row(item="001", acs="0", tests="2"),
        _row(item="002", acs="3", tests="6")))["cohorts"]
    assert g["tests_per_ac"] == {"value": 2.0, "n": 1}


# --------------------------------------------------------------------------- #
# row shapes
# --------------------------------------------------------------------------- #
def test_a_fourteen_cell_row_and_a_sixteen_cell_row_read_alike():
    report = aide.ledger_report(_ledger(
        _row(item="001", width=14), _row(item="002", width=16)))
    (g,) = report["cohorts"]
    assert g["rows"] == 2 and report["skipped"] == []
    assert g["rounds"]["n"] == 2 and g["tests_per_ac"]["n"] == 2


def test_a_row_with_another_cell_count_is_skipped_and_named():
    text = _ledger(_row(item="001"), _row(item="002", width=12))
    report = aide.ledger_report(text)
    assert report["rows"] == 1
    assert report["skipped"] == [text.splitlines().index(_row(item="002", width=12)) + 1]


def test_queue_keeps_that_queues_rows():
    report = aide.ledger_report(_ledger(
        _row(item="001", queue="021"), _row(item="002", queue="022"),
        _row(item="003", queue="")), queue=22)
    assert report["rows"] == 1
    assert report["cohorts"][0]["queues"] == ["022"]


def test_queue_leaves_another_queues_malformed_row_unnamed():
    report = aide.ledger_report(_ledger(
        _row(item="001", queue="022"), _row(item="002", queue="021", width=12)),
        queue=22)
    assert report["rows"] == 1 and report["skipped"] == []


# --------------------------------------------------------------------------- #
# the verb
# --------------------------------------------------------------------------- #
def test_report_prints_json_and_writes_nothing(tmp_path: Path, capsys):
    text = _ledger(_row(item="001", queue="004"), _row(item="002", queue="005"))
    repo = _repo(tmp_path, text)
    before = sorted(p.relative_to(repo) for p in repo.rglob("*"))

    assert aide.main(["--repo", str(repo), "ledger", "report", "--json",
                      "--queue", "4"]) == 0

    out = json.loads(capsys.readouterr().out)
    assert out["exists"] is True and out["queue"] == 4 and out["rows"] == 1
    assert (repo / "docs" / "aide" / "ledger.md").read_text(
        encoding="utf-8") == text
    assert sorted(p.relative_to(repo) for p in repo.rglob("*")) == before
    assert aide.main(["--repo", str(repo), "ledger", "report"]) == 0


def test_a_missing_ledger_is_reported_exits_0_and_is_never_created(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "ledger", "report"]) == 0
    assert aide.main(["--repo", str(repo), "ledger", "report", "--json"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out[out.index("{"):])["exists"] is False
    assert not (repo / "docs" / "aide" / "ledger.md").exists()


@pytest.mark.parametrize("argv", [
    ["report", "7"],
    ["report", "--rounds", "0"],
    ["report", "--findings", "nit=1"],
    ["report", "--no-commit"],
    ["abandon", "7", "--rounds", "1", "--json"],
    ["abandon", "7", "--rounds", "1", "--queue", "3"],
    ["abandon", "--rounds", "1"],
])
def test_an_option_the_action_does_not_read_is_a_usage_error(
        tmp_path: Path, argv):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "ledger", *argv]) == 2
    assert not (repo / "docs" / "aide" / "ledger.md").exists()
