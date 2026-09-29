"""Tests for the coverage-completeness warnings — issue #289.

`aide check` said that each coverage table *existed* and never that it was
*complete*. Found in the #285 audit, three omissions each passed clean:

1. a `progress.md` stage section with no Stage summary row;
2. a `vision.md` G-code with no row in `roadmap.md`'s coverage table;
3. a `roadmap.md` coverage row naming a stage with no `## Stage N` section.

§1 → `progress.md` and §1 → `roadmap.md` now say each table is complete, and
`coverage_completeness_warnings` warns on each case. Stage numbers are read
from a coverage row's Delivered-by cell by `named_stage_numbers` — the reading
the Dependencies slot takes — never by a bare number in the cell's prose.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_coverage", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


VISION = """\
# D — Vision

| Code | Objective | Measure |
|------|-----------|---------|
| G1 | Ship | It runs |
| G2 | Measure | A number |
| G3 | *Removed from scope* — Deploy | Not pursued |
"""

ROADMAP = """\
# D — Roadmap

### Objective → stage coverage

| Objective | Delivered by |
|-----------|--------------|
| G1 Ship | Stage 0 |
| G2 Measure | Stages 1, 2 (extended by 3–4) |
| *(out of scope 2026-07-25)* G3 Deploy | Stage 2 shipped the artefacts |

## Stage 0 — Base

**Dependencies.** None.

## Stage 1 — Grow

**Dependencies.** Stage 0.

## Stage 2 — Ship

**Dependencies.** Stage 1.
"""

PROGRESS = """\
# D — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 0 | Base | G1 | ✅ |
| 1 | Grow | G2 | ⏸️ |
| 2 | Ship | G2 | ❌ |

## Stage 0 — Base — ✅

**Deliverables.**
- ✅ Base. *(Item 001)*

## Stage 1 — Grow — ⏸️

**Deliverables.**
- ⏸️ Grow. *(Item 002)*

## Stage 2 — Ship — ❌

**Deliverables.**
- 📋 Ship. *(Item 003)*
"""


def _warnings(tmp_path: Path, vision=VISION, roadmap=ROADMAP, progress=PROGRESS):
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True, exist_ok=True)
    for name, text in (("vision.md", vision), ("roadmap.md", roadmap),
                       ("progress.md", progress)):
        path = ddir / name
        if text is None:
            if path.exists():
                path.unlink()
        else:
            path.write_text(text, encoding="utf-8")
    return aide.coverage_completeness_warnings(ddir)


def test_complete_tables_are_silent(tmp_path: Path):
    """The prose around a Delivered-by cell's stages (`extended by 3–4`) is
    not read, and a row whose first cell opens with a parenthetical note
    still maps its G-code."""
    assert _warnings(tmp_path) == []


# --------------------------------------------------------------------------- #
# 1. a progress.md stage section with no Stage summary row
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("dropped", ["| 0 | Base | G1 | ✅ |\n",
                                     "| 1 | Grow | G2 | ⏸️ |\n",
                                     "| 2 | Ship | G2 | ❌ |\n"])
def test_a_stage_section_with_no_summary_row_is_named(tmp_path: Path, dropped):
    """A ⏸️ or ❌ stage needs its row as much as any other: the summary row is
    where the deferral or the exclusion is read from."""
    stage = dropped.split("|")[1].strip()
    out = _warnings(tmp_path, progress=PROGRESS.replace(dropped, ""))
    assert len(out) == 1, out
    assert out[0].startswith(f"progress.md: stage {stage} has a '## Stage {stage}' "
                             f"section but no Stage summary row")
    assert out[0].endswith("§1 → progress.md")


def test_a_stage_number_is_matched_by_value(tmp_path: Path):
    progress = PROGRESS.replace("| 1 | Grow |", "| 01 | Grow |")
    assert _warnings(tmp_path, progress=progress) == []


def test_an_unreadable_summary_row_still_counts_for_its_stage(tmp_path: Path):
    """A row its reader cannot use is `unreadable_row_errors`'s to report,
    once: its stage is not named a second time as having no row."""
    progress = PROGRESS.replace("| 1 | Grow | G2 | ⏸️ |", "| 1 | Grow | a|b | ⏸️ |")
    assert _warnings(tmp_path, progress=progress) == []


def test_a_missing_summary_table_is_not_reported_again(tmp_path: Path):
    """`run_checks` already errors on the missing table."""
    progress = PROGRESS.split("## Stage summary")[0] + PROGRESS.split("❌ |\n", 1)[1]
    assert "| Stage |" not in progress
    assert _warnings(tmp_path, progress=progress) == []


# --------------------------------------------------------------------------- #
# 2. a vision.md G-code with no roadmap coverage row
# --------------------------------------------------------------------------- #
def test_a_vision_g_code_with_no_coverage_row_is_named(tmp_path: Path):
    roadmap = ROADMAP.replace("| G2 Measure | Stages 1, 2 (extended by 3–4) |\n", "")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1, out
    assert out[0].startswith("roadmap.md: vision objective G2 has no row in the "
                             "objective → stage coverage table")
    assert out[0].endswith("§1 → roadmap.md")


def test_a_withdrawn_objective_still_needs_its_row(tmp_path: Path):
    """The vision still lists G3, so the roadmap must still map it."""
    roadmap = ROADMAP.replace(
        "| *(out of scope 2026-07-25)* G3 Deploy | Stage 2 shipped the artefacts |\n", "")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "vision objective G3 has no row" in out[0]


@pytest.mark.parametrize("first_cell", ["G02 Measure", "**G2** Measure",
                                        "G1, G2 Both", "G1 and G2 Both",
                                        "G1 or G2 Either", "G1/G2 Both",
                                        "(note) G2 Measure"])
def test_a_coverage_row_is_read_by_the_codes_opening_its_first_cell(
        tmp_path: Path, first_cell):
    roadmap = ROADMAP.replace("| G2 Measure |", f"| {first_cell} |")
    assert _warnings(tmp_path, roadmap=roadmap) == []


@pytest.mark.parametrize("first_cell, expected", [
    ("G2 and G7 Something", [2, 7]),
    ("G2 or G7 Something", [2, 7]),
    ("G2, and G7", [2, 7]),
    ("G2 & G7", [2, 7]),
    ("G2 AND G7", [2, 7]),
    ("G2 Or G7", [2, 7]),
    ("G2, OR G7", [2, 7]),
    ("G2 and g7", [2]),
    # A conjunction joins codes only: the word after it must be one.
    ("G2 and more", [2]),
    ("G2 or Gx", [2]),
    ("G2 and G7x", [2]),
    ("Measure, as G2", []),
])
def test_the_codes_run_joins_g_codes_and_nothing_else(first_cell, expected):
    assert aide._coverage_row_codes([first_cell, "Stage 3"]) == expected


def test_a_g_code_later_in_the_first_cell_is_not_a_coverage_row(tmp_path: Path):
    roadmap = ROADMAP.replace("| G2 Measure |", "| Measure, as G2 |")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "vision objective G2 has no row" in out[0]


def test_a_missing_table_on_either_side_is_not_reported_again(tmp_path: Path):
    """`root_document_warnings` names a vision or roadmap with no G-code rows."""
    assert _warnings(tmp_path, vision="# V\n\nNo table.\n") == []
    roadmap = "# R\n\n## Stage 0 — Base\n\n## Stage 1 — Grow\n\n## Stage 2 — Ship\n"
    assert _warnings(tmp_path, roadmap=roadmap) == []


def test_missing_files_are_silent(tmp_path: Path):
    assert _warnings(tmp_path, vision=None) == []
    assert _warnings(tmp_path / "b", roadmap=None) == []
    assert _warnings(tmp_path / "c", progress=None) == []
    assert _warnings(tmp_path / "d", vision=None, roadmap=None, progress=None) == []


# --------------------------------------------------------------------------- #
# 3. a roadmap coverage row naming a stage with no ## Stage N section
# --------------------------------------------------------------------------- #
def test_a_named_stage_with_no_section_is_named(tmp_path: Path):
    """The roadmap-side counterpart of #285's Objective row naming no stage
    with a section — per stage, so one real stage beside it does not hide
    the missing one."""
    roadmap = ROADMAP.replace("Stages 1, 2 (extended", "Stages 1, 2, 7 (extended")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1, out
    assert out[0].startswith("roadmap.md: the coverage row for G2 names stage 7, "
                             "which has no '## Stage N' section in roadmap.md")
    assert out[0].endswith("§1 → roadmap.md")


def test_several_missing_stages_share_one_warning(tmp_path: Path):
    roadmap = ROADMAP.replace("| G1 Ship | Stage 0 |",
                              "| G1 Ship | Stage 0 (then **Stage 8**; and Stages 9–11) |")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "G1 names stages 8, 9, 11, which have no" in out[0]


def test_a_stage_held_only_as_a_placeholder_bullet_has_no_section(tmp_path: Path):
    """The consumer shape: `## Stages 22–25 — placeholders` with a bullet per
    stage lays none of them out, so a row naming one is named."""
    roadmap = (ROADMAP.replace("| G2 Measure | Stages 1, 2 (extended by 3–4) |",
                               "| G2 Measure | Stages 1, 2 (normative model: Stage 3) |")
               + "\n## Stages 3–4 — placeholders\n\n- **Stage 3 — Model.** Later.\n")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "G2 names stage 3," in out[0]


@pytest.mark.parametrize("cell", ["Stage 00", "0", "0, 1", "**Stage 1**",
                                  "Stage 2 (item 017, v9, extended by 5–6)",
                                  "—"])
def test_the_delivered_by_cell_is_read_as_the_dependencies_slot_is(
        tmp_path: Path, cell):
    """By value; after the word Stage or Stages, or a cell of bare numbers;
    never a bare number in prose, and a cell naming nothing names nothing."""
    roadmap = ROADMAP.replace("| G1 Ship | Stage 0 |", f"| G1 Ship | {cell} |")
    assert _warnings(tmp_path, roadmap=roadmap) == []


def test_a_bare_number_cell_naming_a_missing_stage_is_read(tmp_path: Path):
    roadmap = ROADMAP.replace("| G1 Ship | Stage 0 |", "| G1 Ship | 0, 5 |")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "G1 names stage 5," in out[0]


def test_a_roadmap_with_no_stage_sections_is_not_reported_again(tmp_path: Path):
    """`root_document_warnings` names a roadmap with no stage sections; every
    coverage row would otherwise repeat it."""
    roadmap = ROADMAP.split("## Stage 0")[0]
    assert _warnings(tmp_path, roadmap=roadmap) == []


# --------------------------------------------------------------------------- #
# the reader, and the check
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("text, expected", [
    ("Stage 1", [1]),
    ("Stages 4, 5, 18, 28 (specification: **Stage 30**; real failures: Stage 16)",
     [4, 5, 18, 28, 30, 16]),
    ("Stage 1 (extended by 2–4); cohort characterisation: Stage 18", [1, 18]),
    ("Stage 8 (labelled at review), Stage 10 (enforced at routing)", [8, 10]),
    ("Stages 19–21, 29", [19, 21, 29]),
    ("3, 4", [3, 4]),
    ("The v2 API", []),
])
def test_named_stage_numbers_reads_stages_and_not_prose(text, expected):
    assert aide.named_stage_numbers(text) == expected


def test_check_reports_each_case_as_a_warning_and_never_an_error(tmp_path: Path):
    """`run_checks` carries all three, on the warnings side."""
    ddir = tmp_path / "docs" / "aide"
    _warnings(tmp_path,
              roadmap=ROADMAP.replace("| G1 Ship | Stage 0 |\n", "")
                             .replace("Stages 1, 2 (", "Stages 1, 2, 7 ("),
              progress=PROGRESS.replace("| 1 | Grow | G2 | ⏸️ |\n", ""))
    assert ddir.is_dir()
    config = {"project": {"docs_dir": "docs/aide"}, "git": {}}
    errors, warnings = aide.run_checks(tmp_path, config, branches=[])
    for needle in ("stage 1 has a '## Stage 1' section but no Stage summary row",
                   "vision objective G1 has no row",
                   "the coverage row for G2 names stage 7"):
        assert any(needle in w for w in warnings), (needle, warnings)
        assert not any(needle in e for e in errors), (needle, errors)
