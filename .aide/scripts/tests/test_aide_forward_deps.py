"""Tests for the forward stage-dependency warning — issue #282.

The recorded defect: a consumer's roadmap had a stage whose Dependencies read
`Depends on Stage N+2; … may be delivered after it`. Stages close in number
order, so that stage could not close in its turn, and a queue cut from it said
outright that it did not close the stage. §1 → roadmap.md now says a stage's
blocking Dependencies name only earlier-numbered stages, with a deferred (⏸️)
stage the one tolerated exception, and `aide check` warns on the rest.

Only the blocking slot is read: the template puts ordering without blocking in
a sentence after it (`None. Independent of Stage 17 — …`), and reading the
whole block would flag exactly the phrasing the template recommends.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_forward_deps", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


@pytest.mark.parametrize("text, expected", [
    # The consumer's line: the `;` ends the slot, the later stage is in it.
    ("Depends on Stage 5; the rest may be delivered after it.", [5]),
    # The template's own example: the ordering sentence names nothing.
    ("None. Independent of Stage 17 — may be queued in either order.", []),
    ("None", []),
    ("Stage 2.", [2]),
    ("Stages 3 and 4.", [3, 4]),
    ("Stages 3, 4", [3, 4]),
    ("Stage 3 and Stage 6", [3, 6]),
    ("Stages 3–5", [3, 5]),
    # A comma before the final conjunction does not drop the last stage.
    ("Depends on Stages 10, 11, and 12.", [10, 11, 12]),
    ("3, 4, and 5", [3, 4, 5]),
    # The template's ordering phrasings, written with no `None.` before them.
    ("independent of Stage 9; may be queued in either order.", []),
    ("Queue before Stage 9, whose retuning is safer once this exists.", []),
    ("Stage 2, independent of Stage 9", [2]),
    # "Queued after" states a block, not an ordering preference: still read.
    ("Blocked on Stage 5, queued after Stage 3 lands.", [5, 3]),
    # Bare numbers — the template slot says "blocking stage numbers".
    ("3, 4", [3, 4]),
    ("3 and 4", [3, 4]),
    # A spaced dash ends the slot, as a sentence end does.
    ("Stage 1 — queue before Stage 9, whose retuning is safer once this exists", [1]),
    ("Stage 1 - see Stage 9", [1]),
    # A number not after the word Stage is not a stage.
    ("Stage 1 and item 012", [1]),
    ("The v2 API", []),
    # Emphasis does not hide a stage.
    ("**Stage 4**", [4]),
])
def test_the_blocking_slot_is_read_and_nothing_after_it(text, expected):
    assert aide.blocking_dependency_stages(text) == expected


ROADMAP = """\
# R

## Stage 1 — Foundations

**Goal.** The base.

**Dependencies.** None.

## Stage 2 — Campaign

**Dependencies.** Depends on Stage 4; the rest may be delivered after it.

## Stage 3 — Hardening

**Dependencies.** Stage 1. Independent of Stage 4 — may be queued in either
order.

# Phase 2 — Later

## Stage 4 — Model

**Dependencies.** Stages 1 and 3.

## Stage 5 — Polish

**Dependencies.** Stage 5 and Stage 2.
"""


def _progress(stage2_icon: str, summary_icon: str = "📋") -> str:
    return (
        "# P\n\n"
        "| Stage | Title | Objectives | Status |\n"
        "|-------|-------|-----------|--------|\n"
        f"| 2 | Campaign | G1 | {summary_icon} |\n\n"
        f"## Stage 2 — Campaign — {stage2_icon}\n\n"
        "**Deliverables.**\n"
        "- 📋 The run. *(Item 001)*\n")


def _warnings(tmp_path: Path, roadmap=ROADMAP, progress=None):
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True, exist_ok=True)
    if roadmap is not None:
        (ddir / "roadmap.md").write_text(roadmap, encoding="utf-8")
    if progress is not None:
        (ddir / "progress.md").write_text(progress, encoding="utf-8")
    return aide.forward_dependency_warnings(ddir)


def test_a_forward_dependency_is_a_warning_naming_stage_and_later_stage(tmp_path: Path):
    """Stage 2 depends on Stage 4 — the consumer's `;` shape. Backward
    dependencies (4 on 1 and 3), `None`, an ordering sentence naming a later
    stage (3 on 4) and a self-reference (5 on 5) are all silent."""
    out = _warnings(tmp_path)
    assert len(out) == 1
    assert "stage 2's Dependencies name later stage 4" in out[0]
    assert "roadmap.md" in out[0] and "§1 → roadmap.md" in out[0]


def test_a_deferred_stage_is_exempt(tmp_path: Path):
    """⏸️ on the stage's header in progress.md is the one tolerated forward
    dependency, and so is ⏸️ on its summary row."""
    assert _warnings(tmp_path, progress=_progress("⏸️", "⏸️")) == []
    assert _warnings(tmp_path, progress=_progress("⏸️")) == []
    assert _warnings(tmp_path, progress=_progress("📋", "⏸️")) == []


@pytest.mark.parametrize("icon", ["📋", "🚧", "🔍", "✅"])
def test_any_other_status_is_not_exempt(tmp_path: Path, icon: str):
    """A stage still expected to close in its turn is still warned about."""
    out = _warnings(tmp_path, progress=_progress(icon, icon))
    assert len(out) == 1 and "stage 2's" in out[0]


def test_a_missing_progress_exempts_nothing_and_a_missing_roadmap_is_silent(
        tmp_path: Path):
    assert len(_warnings(tmp_path)) == 1
    assert _warnings(tmp_path / "other", roadmap=None,
                     progress=_progress("📋")) == []


def test_several_later_stages_are_named_together(tmp_path: Path):
    roadmap = ("# R\n\n## Stage 0 — Base\n\n"
               "**Dependencies.** Stages 2 and 3.\n")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "stage 0's Dependencies name later stages 2, 3" in out[0]


def test_a_wrapped_dependencies_line_is_read_whole(tmp_path: Path):
    """The slot continues over a wrapped line up to its sentence end."""
    roadmap = ("# R\n\n## Stage 1 — Base\n\n"
               "**Dependencies.** Stage 0 and\nStage 4.\n\n"
               "**Validation / acceptance.**\n\n- Stage 9 is not read here.\n")
    out = _warnings(tmp_path, roadmap=roadmap)
    assert len(out) == 1 and "later stage 4" in out[0]


def test_check_reports_it_as_a_warning_and_never_an_error(tmp_path: Path):
    """`run_checks` carries the lint, on the warnings side."""
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True)
    (ddir / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
    config = {"project": {"docs_dir": "docs/aide"}, "git": {}}
    errors, warnings = aide.run_checks(tmp_path, config, branches=[])
    assert any("stage 2's Dependencies name later stage 4" in w for w in warnings)
    assert not any("Dependencies name later" in e for e in errors)


# --------------------------------------------------------------------------- #
# A stage under way over a ⏸️ or withdrawn earlier dependency — issue #384
# --------------------------------------------------------------------------- #
# Since 2.32.0 §1 → roadmap.md meets a blocking dependency on an earlier stage
# only once that stage is ✅: a ⏸️ one waits on its owner, and (2.34.0) a
# withdrawn one is never met, so the dependent stage is re-planned. The
# queue-planner hands back on both; `aide check` now says so when a stage
# is under way regardless.

UNDER_WAY_ROADMAP = """\
# R

## Stage 1 — Base

**Dependencies.** None.

## Stage 2 — Build

**Dependencies.** Stage 1.
"""


def _two_stage_progress(dep_header: str, dep_summary: str,
                        dependent_bullet: str,
                        dependent_summary: str = "📋",
                        dependent_header: str = "",
                        dep_bullet: str = "") -> str:
    return (
        "# P\n\n"
        "| Stage | Title | Objectives | Status |\n"
        "|-------|-------|-----------|--------|\n"
        f"| 1 | Base | G1 | {dep_summary} |\n"
        f"| 2 | Build | G1 | {dependent_summary} |\n\n"
        f"## Stage 1 — Base — {dep_header}\n\n"
        "**Deliverables.**\n"
        f"- {dep_bullet or dep_header} The base. *(Item 001)*\n\n"
        f"## Stage 2 — Build{' — ' + dependent_header if dependent_header else ''}\n\n"
        "**Deliverables.**\n"
        f"- {dependent_bullet} The build. *(Item 002)*\n"
        "- 📋 The rest. *(Item 003)*\n")


def _queue(tmp_path: Path, *items: int) -> None:
    qdir = tmp_path / "docs" / "aide" / "queue"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "queue-001.md").write_text(
        "# Queue 001\n\n" + "".join(f"### Item {n:03d}: thing {n}\n\n"
                                    for n in items), encoding="utf-8")


@pytest.mark.parametrize("dep_header, dep_summary, word", [
    ("⏸️", "⏸️", "⏸️ deferred"),
    ("⏸️", "📋", "⏸️ deferred"),   # the header alone says ⏸️
    ("📋", "⏸️", "⏸️ deferred"),   # the summary row alone says ⏸️
    ("📋", "❌", "withdrawn"),
])
def test_a_started_stage_over_a_deferred_or_withdrawn_dependency_warns(
        tmp_path: Path, dep_header: str, dep_summary: str, word: str):
    out = _warnings(tmp_path, roadmap=UNDER_WAY_ROADMAP,
                    progress=_two_stage_progress(dep_header, dep_summary, "🚧",
                                                 dep_bullet="📋"))
    assert len(out) == 1
    assert "stage 2 is under way while stage 1" in out[0] and word in out[0]


def test_a_queued_stage_over_a_withdrawn_dependency_warns(tmp_path: Path):
    """Not yet started, but a 📋 item of it sits in an open queue."""
    _queue(tmp_path, 3)
    out = _warnings(tmp_path, roadmap=UNDER_WAY_ROADMAP,
                    progress=_two_stage_progress("📋", "❌", "📋"))
    assert len(out) == 1 and "stage 2 is under way" in out[0]


@pytest.mark.parametrize("dependent_bullet, dependent_summary", [
    ("📋", "📋"),   # waiting, queued nowhere: what the rule asks for
    ("✅", "✅"),   # nothing left to build over it
    ("⏸️", "⏸️"),   # the dependent is itself deferred
    ("🚧", "❌"),   # the dependent is withdrawn too
])
def test_a_stage_not_under_way_is_silent(tmp_path: Path, dependent_bullet: str,
                                          dependent_summary: str):
    progress = _two_stage_progress("📋", "❌", dependent_bullet,
                                   dependent_summary)
    if dependent_bullet == "✅":
        progress = progress.replace("- 📋 The rest.", "- ✅ The rest.")
    if dependent_bullet == "⏸️":
        progress = progress.replace("- 📋 The rest.", "- ⏸️ The rest.")
    assert _warnings(tmp_path, roadmap=UNDER_WAY_ROADMAP,
                     progress=progress) == []


@pytest.mark.parametrize("dependent_summary, dependent_header, queued", [
    ("⏸️", "", False),    # ⏸️ summary row over a 🚧 bullet
    ("📋", "⏸️", False),  # ⏸️ header over a 🚧 bullet
    ("⏸️", "", True),     # ⏸️ summary row, a 📋 item of it queued
])
def test_a_deferred_dependent_is_never_under_way(
        tmp_path: Path, dependent_summary: str, dependent_header: str,
        queued: bool):
    """The ⏸️ exemption reads the dependent's header and summary row, not
    only what its bullets roll up to."""
    if queued:
        _queue(tmp_path, 3)
    progress = _two_stage_progress("⏸️", "⏸️", "📋" if queued else "🚧",
                                   dependent_summary, dependent_header)
    assert _warnings(tmp_path, roadmap=UNDER_WAY_ROADMAP,
                     progress=progress) == []


@pytest.mark.parametrize("icon", ["📋", "🚧", "✅"])
def test_a_dependency_a_queue_can_still_meet_is_silent(tmp_path: Path, icon: str):
    """A 📋 or 🚧 earlier stage is the ordinary wait; a ✅ one is met."""
    assert _warnings(tmp_path, roadmap=UNDER_WAY_ROADMAP,
                     progress=_two_stage_progress(icon, icon, "🚧")) == []


def test_check_reports_an_unmet_earlier_dependency_as_a_warning(tmp_path: Path):
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True)
    (ddir / "roadmap.md").write_text(UNDER_WAY_ROADMAP, encoding="utf-8")
    (ddir / "progress.md").write_text(
        _two_stage_progress("⏸️", "⏸️", "🚧"), encoding="utf-8")
    config = {"project": {"docs_dir": "docs/aide"}, "git": {}}
    errors, warnings = aide.run_checks(tmp_path, config, branches=[])
    assert any("stage 2 is under way while stage 1" in w for w in warnings)
    assert not any("under way while" in e for e in errors)
