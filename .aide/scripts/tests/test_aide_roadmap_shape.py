"""A roadmap stage section is the plan and nothing else — issue #483.

§1 → roadmap.md says what a stage section may hold, and `aide check` warns
on four signals of a section that holds more: a blockquote, a Goal of more
than one paragraph, a paragraph opening in bold that is not a template
label, and a deliverable bullet over `LONG_DELIVERABLE` characters. Which of
them is named depends on what the stage's status still lets its author fix:
all four on a 📋 stage, the blockquote alone on a 🚧, 🔍 or ⏸️ one, nothing
on a ✅ or ❌ one.

Document-tree tests: `roadmap_shape_findings` over text, and
`roadmap_shape_warnings` / `run_checks` over a tree. The same warning
against a real install is `tests/test_fixture_consumer.py`'s.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_roadmap_shape", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

TEMPLATE = _MODULE_PATH.parents[1] / "templates" / "roadmap.md"

#: A stage in the template's shape: every block, each as the rule asks.
CLEAN = """\
## Stage 1 — Rules

**Goal.** The rule engine fires on every case of the corpus, wrapped over
two lines of one paragraph.

**Deliverables.**

- A **rule record** with its evidence pointer, checked by a unit test.
- The rule runner, its report checked against a fixture corpus; wrapped
  onto a continuation line.

**Dependencies.** None. Independent of Stage 2 — may be queued in either
order.

**Human gate.** Which corpus is the reference.

**Validation / acceptance.**

- Every rule fires on its fixture.
- Target: the corpus runs in under a minute.
"""

BLOCKQUOTE = "> ⚠️ Annotated 2026-09-15 — read before the text below.\n\n"
SECOND_GOAL_PARAGRAPH = "\nA second paragraph that narrates a decision.\n"
BOLD_BLOCK = "**Scope decisions (maintainer, 2026-09-22).** Recorded here.\n\n"


def _with(*, quote: bool = False, goal: bool = False, bold: bool = False,
          long: int = 0) -> str:
    """CLEAN with the named signals planted in it."""
    text = CLEAN
    if quote:
        text = text.replace("**Goal.**", BLOCKQUOTE + "**Goal.**", 1)
    if goal:
        text = text.replace("two lines of one paragraph.\n",
                            "two lines of one paragraph.\n" + SECOND_GOAL_PARAGRAPH, 1)
    if bold:
        text = text.replace("**Dependencies.**", BOLD_BLOCK + "**Dependencies.**", 1)
    if long:
        # Measured as the check measures it: the text after `- `, its
        # continuation line joined by one space.
        first = "A design narrated at length: "
        bullet = ("- " + first + "x" * (long - len(first) - len(" tail."))
                  + "\n  tail.\n")
        text = text.replace("- The rule runner", bullet + "- The rule runner", 1)
    return text


def _findings(roadmap: str, status: str | None = None, stage: int = 1):
    statuses = {} if status is None else {stage: status}
    return aide.roadmap_shape_findings(roadmap.splitlines(), statuses)


def _signal(finding: str) -> str:
    for key, needle in (("quote", "blockquote"), ("goal", "'s Goal runs"),
                        ("bold", "no template label"),
                        ("long", "deliverable bullet")):
        if needle in finding:
            return key
    raise AssertionError(f"unrecognised finding: {finding}")


# --------------------------------------------------------------------------- #
# the four signals, on a 📋 stage
# --------------------------------------------------------------------------- #
def test_the_template_shaped_stage_is_silent():
    assert _findings(CLEAN) == []


def test_the_installed_template_is_silent():
    """The template is what a roadmap starts as, every stage 📋 — it must not
    teach the shape the check names."""
    assert TEMPLATE.is_file()
    assert _findings(TEMPLATE.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("signal", ["quote", "goal", "bold", "long"])
def test_each_signal_alone_is_named_once_on_a_planned_stage(signal):
    kwargs = {signal: (aide.LONG_DELIVERABLE + 1) if signal == "long" else True}
    findings = _findings(_with(**kwargs), "planned")
    assert [_signal(f) for f in findings] == [signal], findings
    assert findings[0].startswith("roadmap.md:")
    assert "stage 1" in findings[0]
    assert findings[0].endswith("(conventions.md §1 → roadmap.md)")


def test_all_four_are_named_on_a_planned_stage_at_their_first_lines():
    text = _with(quote=True, goal=True, bold=True, long=aide.LONG_DELIVERABLE + 1)
    lines = text.splitlines()
    findings = _findings(text, "planned")
    assert sorted(_signal(f) for f in findings) == ["bold", "goal", "long", "quote"]
    for f in findings:
        lineno = int(f.split(":")[1])
        cited = lines[lineno - 1]
        expected = {"quote": ">", "goal": "**Goal.**",
                    "bold": "**Scope decisions", "long": "- A design"}[_signal(f)]
        assert cited.startswith(expected), (f, cited)


def test_a_stage_with_no_status_reads_as_planned():
    assert len(_findings(_with(bold=True))) == 1
    assert len(_findings(_with(bold=True), "planned")) == 1


# --------------------------------------------------------------------------- #
# scope by status
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", ["in-progress", "in-review", "deferred"])
def test_a_started_stage_is_named_for_its_blockquote_alone(status):
    text = _with(quote=True, goal=True, bold=True, long=aide.LONG_DELIVERABLE + 1)
    findings = _findings(text, status)
    assert [_signal(f) for f in findings] == ["quote"], findings
    assert "restores the stage as written" in findings[0]
    assert aide.STATUS_TO_ICON[status] in findings[0]


@pytest.mark.parametrize("status", ["in-progress", "in-review", "deferred"])
def test_a_started_stage_without_a_blockquote_is_silent(status):
    text = _with(goal=True, bold=True, long=aide.LONG_DELIVERABLE + 1)
    assert _findings(text, status) == []


@pytest.mark.parametrize("status", ["complete", "excluded"])
def test_a_settled_stage_is_silent(status):
    text = _with(quote=True, goal=True, bold=True, long=aide.LONG_DELIVERABLE + 1)
    assert _findings(text, status) == []


# --------------------------------------------------------------------------- #
# what is not read, and what is not a signal
# --------------------------------------------------------------------------- #
def test_a_fenced_code_block_is_never_read():
    fence = ("```text\n> not a quote\n**Not a block.** inside a fence\n```\n\n"
             "~~~\n> nor this\n~~~\n\n")
    text = CLEAN.replace("**Dependencies.**", fence + "**Dependencies.**", 1)
    assert _findings(text, "planned") == []


def test_an_html_comment_is_never_read():
    comment = ("<!-- an author's note\n> quoted inside it\n**Bold inside it.**\n"
               "-->\n\n<!-- > one-line comment -->\n\n")
    text = CLEAN.replace("**Dependencies.**", comment + "**Dependencies.**", 1)
    assert _findings(text, "planned") == []


def test_a_quote_after_a_closed_fence_is_still_read():
    """The fence closes: what follows it is prose again."""
    text = CLEAN.replace("**Dependencies.**",
                         "```\ncode\n```\n\n" + BLOCKQUOTE + "**Dependencies.**", 1)
    assert [_signal(f) for f in _findings(text, "planned")] == ["quote"]


def test_bold_inside_a_bullet_is_not_a_bold_block():
    text = CLEAN.replace("- A **rule record**",
                         "- **D0 — The rule record.** Its pointer\n"
                         "  **wrapped** in bold.\n- A **rule record**", 1)
    assert _findings(text, "planned") == []


def test_a_line_wrapped_onto_bold_is_not_a_bold_block():
    """Markdown reads it as the line above's continuation."""
    text = CLEAN.replace("two lines of one paragraph.\n",
                         "two lines of one paragraph, read\n"
                         "**together**, as one.\n", 1)
    assert _findings(text, "planned") == []


@pytest.mark.parametrize("label", [
    "**Goal**", "**Deliverables:**", "**dependencies.**", "**Human gate**",
    "**Validation/acceptance.**", "**Validation / Acceptance**"])
def test_a_template_label_is_read_with_or_without_its_dot(label):
    text = CLEAN.replace("**Dependencies.**", label + " text.\n\n**Dependencies.**", 1)
    assert [f for f in _findings(text, "planned") if _signal(f) == "bold"] == []


def test_a_bold_block_is_quoted_and_further_ones_counted():
    text = _with(bold=True).replace(
        "**Human gate.**", "**Another note.** More.\n\n**Human gate.**", 1)
    [finding] = _findings(text, "planned")
    assert "'**Scope decisions (maintainer, 2026-09-22).**'" in finding
    assert "2 blocks" in finding


def test_one_warning_per_stage_counts_its_blockquotes():
    text = _with(quote=True).replace(
        "**Dependencies.**", "> A second, separate annotation.\n\n**Dependencies.**", 1)
    [finding] = _findings(text, "deferred")
    assert "holds 2 blockquotes" in finding


def test_guidance_after_the_goal_is_not_a_second_paragraph():
    text = CLEAN.replace("two lines of one paragraph.\n",
                         "two lines of one paragraph.\n\n_Italic guidance,\n"
                         "wrapped over two lines._\n", 1)
    assert _findings(text, "planned") == []


def test_a_blockquote_inside_the_goal_is_named_once_not_as_a_paragraph():
    text = CLEAN.replace("two lines of one paragraph.\n",
                         "two lines of one paragraph.\n\n> A dated note.\n", 1)
    assert [_signal(f) for f in _findings(text, "planned")] == ["quote"]


def test_text_between_stages_is_no_stage_section():
    """A `#` heading ends the stage section above it, as every reader reads
    one: a blockquote under it belongs to no stage."""
    text = CLEAN + "\n# Stages scoped later\n\n> Why the next stages exist.\n"
    assert _findings(text, "planned") == []


# --------------------------------------------------------------------------- #
# the deliverable length boundary
# --------------------------------------------------------------------------- #
def test_the_threshold_is_exclusive_and_continuation_lines_count():
    at = _with(long=aide.LONG_DELIVERABLE)
    over = _with(long=aide.LONG_DELIVERABLE + 1)
    assert _findings(at, "planned") == []
    [finding] = _findings(over, "planned")
    assert f"of {aide.LONG_DELIVERABLE + 1} characters" in finding
    # The planted bullet's last line is its continuation: without it the
    # bullet is under the threshold, so the count above includes it.
    head = next(line for line in over.splitlines() if line.startswith("- A design"))
    assert len(head) < aide.LONG_DELIVERABLE


def test_the_threshold_is_the_one_the_rule_and_help_state():
    """`aide check -h` and §1 → roadmap.md state the number, not the name:
    moving `LONG_DELIVERABLE` alone would leave both saying 800."""
    assert aide.LONG_DELIVERABLE == 800
    section = (_MODULE_PATH.parents[1] / "conventions" / "1-format-contract"
               / "roadmap.md").read_text(encoding="utf-8")
    core = section.split("#### Rationale", 1)[0]
    assert f"about {aide.LONG_DELIVERABLE} characters" in " ".join(core.split())


def test_a_nested_bullet_belongs_to_its_top_level_bullet():
    nested = "  - " + "y" * (aide.LONG_DELIVERABLE - 5) + "\n"
    text = CLEAN.replace("- The rule runner", "- Parent.\n" + nested + "- The rule runner", 1)
    [finding] = _findings(text, "planned")
    assert _signal(finding) == "long"


def test_a_long_acceptance_bullet_is_not_a_deliverable():
    text = CLEAN.replace("- Every rule fires on its fixture.",
                         "- " + "z" * (aide.LONG_DELIVERABLE + 50), 1)
    assert _findings(text, "planned") == []


def test_several_long_bullets_share_one_warning():
    text = _with(long=aide.LONG_DELIVERABLE + 1).replace(
        "- The rule runner", "- " + "w" * (aide.LONG_DELIVERABLE + 5) + "\n- The rule runner", 1)
    [finding] = _findings(text, "planned")
    assert "2 deliverable bullets over" in finding


# --------------------------------------------------------------------------- #
# the maintenance stage follows the same rules
# --------------------------------------------------------------------------- #
MAINTENANCE = """\
## Stage 4 — Maintenance

**Goal.** Repair shipped work by closing insight-derived entries.

**Deliverables.** Added to `progress.md` by each maintenance queue.

**Dependencies.** None.
"""


def test_the_maintenance_stage_template_shape_is_silent():
    assert _findings(MAINTENANCE, "planned", 4) == []
    assert _findings(MAINTENANCE, "in-progress", 4) == []


def test_the_maintenance_stage_is_named_like_any_other():
    text = MAINTENANCE.replace(
        "**Deliverables.**", "**Why it is a stage.** Because.\n\n**Deliverables.**")
    assert [_signal(f) for f in _findings(text, "planned", 4)] == ["bold"]
    assert _findings(text, "in-progress", 4) == []
    quoted = MAINTENANCE.replace("**Goal.**", BLOCKQUOTE + "**Goal.**")
    assert [_signal(f) for f in _findings(quoted, "in-progress", 4)] == ["quote"]


# --------------------------------------------------------------------------- #
# the status, read from progress.md
# --------------------------------------------------------------------------- #
PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | {row} |

## Stage 1 — Rules — {header}

**Deliverables.**
- 📋 Bounds. *(Item 027)*
"""


@pytest.mark.parametrize("row, header, expected", [
    ("✅", "✅", "complete"),
    ("⏸️", "📋", "deferred"),
    ("📋", "🚧", "in-progress"),     # a started header wins over a 📋 row
    ("❌", "📋", "excluded"),
    ("📋", "📋", "planned"),
])
def test_the_status_is_the_summary_row_or_a_started_header(row, header, expected):
    text = PROGRESS.format(row=row, header=header)
    assert aide.roadmap_stage_statuses(text.splitlines()) == {1: expected}


def test_a_stage_progress_does_not_show_is_absent():
    assert aide.roadmap_stage_statuses([]) == {}


def _repo(tmp_path: Path, roadmap: str, progress: str | None) -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(
        '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n', encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    (ddir / "roadmap.md").write_text(roadmap, encoding="utf-8")
    if progress is not None:
        (ddir / "progress.md").write_text(progress, encoding="utf-8")
    return repo


def test_the_warnings_follow_the_stage_status_in_progress(tmp_path: Path):
    roadmap = _with(quote=True, bold=True)
    repo = _repo(tmp_path, roadmap, PROGRESS.format(row="⏸️", header="⏸️"))
    ddir = repo / "docs" / "aide"
    assert [_signal(f) for f in aide.roadmap_shape_warnings(ddir)] == ["quote"]
    (ddir / "progress.md").write_text(PROGRESS.format(row="✅", header="✅"),
                                      encoding="utf-8")
    assert aide.roadmap_shape_warnings(ddir) == []
    (ddir / "progress.md").unlink()
    assert sorted(_signal(f) for f in aide.roadmap_shape_warnings(ddir)) == \
        ["bold", "quote"]


def test_a_missing_roadmap_is_silent(tmp_path: Path):
    repo = _repo(tmp_path, CLEAN, None)
    (repo / "docs" / "aide" / "roadmap.md").unlink()
    assert aide.roadmap_shape_warnings(repo / "docs" / "aide") == []


def test_check_reports_them_as_warnings_and_never_errors(tmp_path: Path):
    roadmap = _with(quote=True, goal=True, bold=True, long=aide.LONG_DELIVERABLE + 1)
    repo = _repo(tmp_path, roadmap, PROGRESS.format(row="📋", header="📋"))
    errors, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    shape = [w for w in warnings if w.endswith("(conventions.md §1 → roadmap.md)")]
    assert sorted(_signal(w) for w in shape) == ["bold", "goal", "long", "quote"]
    assert not any("roadmap.md:" in e for e in errors), errors
