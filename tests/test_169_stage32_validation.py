"""Tests for item 169 -- validate Stage 32 (selected-mode refinement) and
close Stage 20's deferred end-to-end validation deliverable.

Item 169's own Description explains the split: every stage-level claim
already has an in-suite check merged with the item that made it true
(``test_162``, ``test_163``, ``test_165``, ``test_168``, ``test_151``), and
the item's replay runs those by node id from a clean clone. This module
holds only what no merged test covers -- the live-state invariants behind
the numbers written into ``progress.md``, and the Stage 20 bullet sweep.

Per the item spec's Testing Strategy, this module carries exactly six AC
tests (AC6, AC7, AC8, AC9, AC10, AC13) plus the five named adversarial
cases below -- no others. AC1-AC5, AC11, AC12 and AC14-AC17 are Replay
criteria: executed by the builder and re-executed by the validator, their
evidence recorded in the item's Decisions log, not tested here.

Until the builder's bookkeeping step lands (``aide progress accept`` /
``amend`` on Stage 20's and Stage 32's criteria, and the hand-edit of Stage
20's item-141 bullet from `⏸` to `❌`), AC6, AC7, AC8, AC10 and AC13
are expected to fail: the clauses/annotations they check for do not exist
in ``progress.md`` yet. That is the honest state of a section not yet
bookkept, not a defect in this module -- the ``test_161`` AC14 precedent.

2026-10-02 (item 203): ``test_ac8_...``, ``test_adv_refined_clause_...``,
``test_ac9_...`` and ``test_adv_bar_predicate_...`` are retired, with their
helpers and fixtures. Modes 2 and 3 are now signed at the bar, so the dated
Stage 20 clause and the empty at-the-bar set they compared against live state
are false by design; evidence in ``progress.md`` is a dated measurement and is
not rewritten.

Discipline followed (Testing Strategy):

- Stage-section and acceptance-box location goes entirely through
  ``.aide/scripts/aide.py``'s own ``stage_section`` / ``acceptance_boxes``,
  loaded in-process (the ``test_150`` / ``test_161`` idiom). The one helper
  this module writes for that is continuation-line gathering, since neither
  of those functions returns box or bullet *text*, only line indices.
- No integer, mode id or rung name is written into this module as a literal
  expectation -- every comparison is derived from ``SPECIFICATION``,
  ``MODE_SIGN_OFFS``, ``derive_status``, ``derive_mode_rung`` and
  ``bar_conditions``, recomputed live.
- No ``aide check`` warning count, suite total, engine version or
  severity-ladder constant is pinned here -- those are dated measurements
  that legitimately move and live in ``progress.md``'s evidence and in the
  item's Decisions log.
- No ``insights.md`` entry is pinned.
- No git history, clone, network access or environment profile is needed.
- Every adversarial case is an in-memory ``progress.md`` text or a
  constructed sign-off mapping passed to the same in-process helpers; none
  writes a file or touches the shipped ``MODE_SIGN_OFFS``.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import List

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_PROGRESS_PATH = _REPO_ROOT / "docs" / "aide" / "progress.md"

_STAGE_20 = "20"
_STAGE_32 = "32"


def _aide_module():
    """Import ``.aide/scripts/aide.py`` in-process (§6: never shell out to
    the CLI and re-parse its stdout)."""
    spec = importlib.util.spec_from_file_location("_aide_cli_169", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _progress_lines() -> List[str]:
    return _PROGRESS_PATH.read_text(encoding="utf-8").splitlines()


# =========================================================================== #
# Continuation-line gathering (the one helper this module writes -- the
# test_161 idiom: stage_section/acceptance_boxes return line indices, not
# text).
# =========================================================================== #

#: Mirrors `.aide/scripts/aide.py`'s own dated-trail-line shape (test_161).
_TRAIL_LINE_RE = re.compile(r"^\s+[-*]\s+\*\*\d{4}-\d{2}-\d{2}\*\*\s*→")
_ANNOTATION_RE = re.compile(r"\*\(.+\)\*", re.DOTALL)


def _box_text(lines: List[str], box: int, sub_end: int) -> str:
    """The checkbox line at *box* plus its indented continuation lines,
    stopping at a trail line, a blank line, the next box, or the section
    end (test_161's ``_box_text``)."""
    parts = [lines[box]]
    for i in range(box + 1, sub_end):
        line = lines[i]
        if not line.strip():
            break
        if _TRAIL_LINE_RE.match(line):
            break
        if not line[:1].isspace():
            break
        parts.append(line)
    return "\n".join(parts)


#: A top-level Deliverables bullet: `- <icon> ...`. Sub-bullets (retraction
#: trail lines, etc.) are indented and never match `^- `.
_BULLET_LEAD_RE = re.compile(r"^- (\S+)")


def _bullet_start(lines: List[str], idx: int, section_start: int):
    """Walk back from *idx* to the nearest top-level bullet line owning it."""
    for i in range(idx, section_start - 1, -1):
        if lines[i].startswith("- "):
            return i
    return None


def _bullet_block(lines: List[str], bullet: int, section_end: int) -> str:
    """*bullet*'s own line plus its indented/hanging continuation lines,
    stopping at the next top-level bullet, a blank line, or a heading."""
    parts = [lines[bullet]]
    for i in range(bullet + 1, section_end):
        line = lines[i]
        if not line.strip():
            break
        if line.startswith("- ") or line.startswith("#") or line.startswith(">"):
            break
        parts.append(line)
    return "\n".join(parts)


def _deferred_bullets(lines: List[str], start: int, end: int) -> List[str]:
    """Top-level bullet lines in [start, end) leading with the deferred icon
    `⏸️`."""
    violations = []
    for i in range(start, end):
        match = _BULLET_LEAD_RE.match(lines[i])
        if match and match.group(1) == "⏸️":
            violations.append(lines[i].strip())
    return violations


# =========================================================================== #
# Live derivations (shared by AC6-AC9).
# =========================================================================== #


def _live_status_counts():
    import segfacet.failure_modes as fm

    counts = {"validated": 0, "implemented": 0, "specified": 0, "proposed": 0}
    for mode in fm.SPECIFICATION.values():
        counts[fm.derive_status(mode)] += 1
    return len(fm.SPECIFICATION), counts


def _live_rung_counts():
    import segfacet.failure_modes as fm

    counts = {
        "synthetic-demonstrable": 0,
        "needs-real-data": 0,
        "structurally-unobservable": 0,
        "none": 0,
    }
    for mode in fm.SPECIFICATION.values():
        rung = fm.derive_mode_rung(mode)
        counts[rung or "none"] += 1
    return counts


# =========================================================================== #
# AC6: the status-count clause equals the live derivation.
# =========================================================================== #

_STATUS_COUNTS_RE = re.compile(
    r"derived status counts over (\d+) modes: validated (\d+), implemented (\d+), "
    r"specified (\d+), proposed (\d+)"
)


def test_ac6_status_count_clause_equals_live_derivation():
    aide = _aide_module()
    lines = _progress_lines()
    section = aide.stage_section(lines, _STAGE_20)
    assert section is not None, "no Stage 20 section found in progress.md"
    start, end, _stage_num = section
    text = "\n".join(lines[start:end])

    matches = list(_STATUS_COUNTS_RE.finditer(text))
    assert matches, (
        "Stage 20's section carries no derived-status-counts clause yet "
        "(expected until item 169's bookkeeping step runs)"
    )
    match = matches[-1]
    n, validated, implemented, specified, proposed = (int(g) for g in match.groups())
    live_n, live_counts = _live_status_counts()
    assert n == live_n
    assert validated == live_counts["validated"]
    assert implemented == live_counts["implemented"]
    assert specified == live_counts["specified"]
    assert proposed == live_counts["proposed"]


def test_adv_status_clause_missing_yields_no_match():
    """`status-clause-missing`: a section carrying no status-count clause
    yields no match -- guards a parser that would read an absent note as
    agreement, letting an unwritten number pass as measured."""
    assert _STATUS_COUNTS_RE.search("no such clause anywhere in this text") is None


def test_adv_status_clause_off_by_one_disagrees_with_live():
    """`status-clause-off-by-one`: a clause whose `validated` count is the
    live value plus one fails -- guards the exact defect item 167's
    2026-09-20 correction found, a hardcoded literal that happened to equal
    live state at writing. Built from the live derivation, never a literal,
    so the control tracks the specification instead of coinciding with it by
    accident."""
    live_n, live_counts = _live_status_counts()
    text = (
        f"derived status counts over {live_n} modes: "
        f"validated {live_counts['validated'] + 1}, "
        f"implemented {live_counts['implemented']}, "
        f"specified {live_counts['specified']}, "
        f"proposed {live_counts['proposed']}"
    )
    match = _STATUS_COUNTS_RE.search(text)
    assert match is not None
    n, validated, implemented, specified, proposed = (int(g) for g in match.groups())
    assert n == live_n
    assert implemented == live_counts["implemented"]
    assert specified == live_counts["specified"]
    assert proposed == live_counts["proposed"]
    assert validated != live_counts["validated"], (
        "expected the off-by-one clause to disagree with the live validated count"
    )


# =========================================================================== #
# AC7: the rung-count clause equals the live derivation.
# =========================================================================== #

_RUNG_COUNTS_RE = re.compile(
    r"derived mode rung counts: synthetic-demonstrable (\d+), needs-real-data (\d+), "
    r"structurally-unobservable (\d+), none (\d+)"
)


def test_ac7_rung_count_clause_equals_live_derivation():
    aide = _aide_module()
    lines = _progress_lines()
    section = aide.stage_section(lines, _STAGE_20)
    assert section is not None, "no Stage 20 section found in progress.md"
    start, end, _stage_num = section
    text = "\n".join(lines[start:end])

    matches = list(_RUNG_COUNTS_RE.finditer(text))
    assert matches, (
        "Stage 20's section carries no derived-mode-rung-counts clause yet "
        "(expected until item 169's bookkeeping step runs)"
    )
    match = matches[-1]
    sd, nrd, su, none_ = (int(g) for g in match.groups())
    live_counts = _live_rung_counts()
    assert sd == live_counts["synthetic-demonstrable"]
    assert nrd == live_counts["needs-real-data"]
    assert su == live_counts["structurally-unobservable"]
    assert none_ == live_counts["none"]


# =========================================================================== #
# AC10: Stage 32's criterion-1 box is unticked with a dated, live-derived
# reason.
# =========================================================================== #


def test_ac10_stage32_criterion1_box_unticked_with_dated_reason():
    import segfacet.failure_modes as fm

    aide = _aide_module()
    lines = _progress_lines()
    section = aide.stage_section(lines, _STAGE_32)
    assert section is not None, "no Stage 32 section found in progress.md"
    start, end, _stage_num = section
    boxes = aide.acceptance_boxes(lines, start, end)
    assert boxes, "Stage 32 section carries no acceptance boxes"

    first_box = boxes[0]
    box_line = lines[first_box]
    assert re.match(r"^\s*[-*]\s*\[\s\]", box_line), (
        f"Stage 32's first acceptance box must stay unticked; it reads: {box_line!r}"
    )

    sub_end = boxes[1] if len(boxes) > 1 else end
    text = _box_text(lines, first_box, sub_end)
    annotations = _ANNOTATION_RE.findall(text)
    assert annotations, (
        f"Stage 32 criterion 1 carries no *(...)* annotation naming the "
        f"measured reason: {text!r}"
    )
    full_annotation = " ".join(annotations)

    assert "item 169" in full_annotation, full_annotation
    assert re.search(r"\d{4}-\d{2}-\d{2}", full_annotation), (
        f"criterion-1 annotation carries no ISO date: {full_annotation!r}"
    )

    non_bar_modes = sorted(
        mode_id
        for mode_id, record in fm.MODE_SIGN_OFFS.items()
        if record.outcome != "at-the-bar"
    )
    for mode_id in non_bar_modes:
        assert re.search(rf"\b{mode_id}\b", full_annotation), (
            f"mode {mode_id} carries a sign-off whose outcome != 'at-the-bar' "
            f"but is not named in Stage 32 criterion 1's annotation: "
            f"{full_annotation!r}"
        )


# =========================================================================== #
# AC13: no Stage 20 deliverable bullet is left deferred, and the item-141
# bullet reads excluded with a pointer to item 154.
# =========================================================================== #


def test_ac13_no_stage20_bullet_deferred_and_item141_points_to_154():
    aide = _aide_module()
    lines = _progress_lines()
    section = aide.stage_section(lines, _STAGE_20)
    assert section is not None, "no Stage 20 section found in progress.md"
    start, end, _stage_num = section

    deferred = _deferred_bullets(lines, start, end)
    assert deferred == [], (
        f"Stage 20 deliverable bullet(s) still lead with the deferred icon: {deferred}"
    )

    marker = "*(Item 141)*"
    hits = [i for i in range(start, end) if marker in lines[i]]
    assert len(hits) == 1, (
        f"expected exactly one Stage 20 deliverable carrying {marker!r}; "
        f"found {len(hits)}"
    )
    bullet = _bullet_start(lines, hits[0], start)
    assert bullet is not None, f"could not find the bullet owning {marker!r} in Stage 20"
    assert lines[bullet].startswith("- ❌"), (
        f"the item-141 Stage 20 deliverable must lead with the excluded icon; "
        f"it reads: {lines[bullet][:80]!r}"
    )

    block = _bullet_block(lines, bullet, end)
    assert "item 154" in block.lower(), (
        f"the item-141 bullet does not name item 154: {block!r}"
    )
    dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", block)
    assert dates, f"the item-141 bullet carries no ISO date: {block!r}"
    assert any(d >= "2026-09-22" for d in dates), (
        f"the item-141 bullet carries no ISO date on or after 2026-09-22: {dates}"
    )


def test_adv_deferred_bullet_anywhere_is_flagged():
    """`deferred-bullet-anywhere-is-flagged`: an in-memory Stage 20 section
    whose deferred bullet is some deliverable OTHER than item 141's is
    flagged -- guards a scan that checks only the item-141 line and would
    let another deferred bullet block the rollup unnoticed."""
    aide = _aide_module()
    section_text = (
        "## Stage 20 — Failure-Mode Traceability (G2, G7) — \U0001f6a7\n"
        "\n"
        "**Deliverables.**\n"
        "\n"
        "- ⏸️ Some other deliverable, not item 141's own. *(Item 999)*\n"
        "- ❌ The item-141 deliverable, resolved. *(Item 141)* item 154, 2026-09-22.\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] Some criterion. *(evidence.)*\n"
    ).splitlines()
    start, end, _stage_num = aide.stage_section(section_text, _STAGE_20)
    violations = _deferred_bullets(section_text, start, end)
    assert violations, "expected the non-item-141 deferred bullet to be flagged"
