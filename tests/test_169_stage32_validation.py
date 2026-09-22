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

Discipline followed (Testing Strategy):

- Stage-section and acceptance-box location goes entirely through
  ``.aide/scripts/aide.py``'s own ``stage_section`` / ``acceptance_boxes``,
  loaded in-process (the ``test_150`` / ``test_161`` idiom). The one helper
  this module writes for that is continuation-line gathering, since neither
  of those functions returns box or bullet *text*, only line indices.
- One module-scoped fixture builds ``catalogue.build_catalogue(strict=True)``
  once; one holds the per-mode ``bar_conditions`` results computed from it.
  No test body calls ``build_catalogue()`` or ``bar_conditions()`` a second
  time outside those fixtures.
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
from typing import Dict, List, Tuple

import pytest

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
# Shared fixtures (Testing Strategy: build once, reuse).
# =========================================================================== #


@pytest.fixture(scope="module")
def cached_catalogue():
    from segfacet.catalogue import build_catalogue

    return build_catalogue(strict=True)


@pytest.fixture(scope="module")
def bar_conditions_by_mode(cached_catalogue):
    import segfacet.failure_modes as fm
    import segfacet.traceability as traceability

    return {
        mode_id: traceability.bar_conditions(mode_id, catalogue=cached_catalogue)
        for mode_id in fm.SPECIFICATION
    }


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


def _render_ids(ids) -> str:
    return ", ".join(str(i) for i in sorted(ids))


def _modes_at_bar(bar_conditions_by_mode: Dict[int, Tuple], sign_offs) -> List[int]:
    """AC9's predicate: a mode id is "at the bar" iff every
    ``bar_conditions`` record is ``met`` **and** *sign_offs* carries a record
    for it with ``outcome == "at-the-bar"``. Takes *sign_offs* as an argument
    (rather than reading ``MODE_SIGN_OFFS`` directly) so an adversarial case
    can drive it over a local, constructed mapping without touching the
    shipped one."""
    result = []
    for mode_id, conditions in bar_conditions_by_mode.items():
        if not all(condition.met for condition in conditions):
            continue
        record = sign_offs.get(mode_id)
        if record is not None and record.outcome == "at-the-bar":
            result.append(mode_id)
    return sorted(result)


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
# AC8: the refined/bar/drafts clause equals the live partition.
# =========================================================================== #

_REFINED_BAR_DRAFTS_RE = re.compile(
    r"modes refined by stage 32: ([0-9, ]+); "
    r"at the fully-specified bar: ([0-9, ]+|none); "
    r"left as documented drafts: (\d+)"
)


def test_ac8_refined_bar_drafts_clause_equals_live_partition(bar_conditions_by_mode):
    import segfacet.failure_modes as fm

    aide = _aide_module()
    lines = _progress_lines()
    section = aide.stage_section(lines, _STAGE_20)
    assert section is not None, "no Stage 20 section found in progress.md"
    start, end, _stage_num = section
    text = "\n".join(lines[start:end])

    matches = list(_REFINED_BAR_DRAFTS_RE.finditer(text))
    assert matches, (
        "Stage 20's section carries no refined/bar/drafts clause yet "
        "(expected until item 169's bookkeeping step runs)"
    )
    match = matches[-1]
    refined_str, bar_str, drafts_str = match.group(1), match.group(2), match.group(3)

    expected_refined = _render_ids(fm.MODE_SIGN_OFFS)
    expected_bar_ids = _modes_at_bar(bar_conditions_by_mode, fm.MODE_SIGN_OFFS)
    expected_bar_str = _render_ids(expected_bar_ids) if expected_bar_ids else "none"
    expected_drafts = len(fm.SPECIFICATION) - len(fm.MODE_SIGN_OFFS)

    assert refined_str == expected_refined, (
        f"clause names refined modes {refined_str!r}; sorted(MODE_SIGN_OFFS) "
        f"renders as {expected_refined!r}"
    )
    assert bar_str == expected_bar_str, (
        f"clause names the at-the-bar set {bar_str!r}; live recomputation is "
        f"{expected_bar_str!r}"
    )
    assert int(drafts_str) == expected_drafts, (
        f"clause names {drafts_str} documented drafts; "
        f"len(SPECIFICATION) - len(MODE_SIGN_OFFS) == {expected_drafts}"
    )


def test_adv_refined_clause_names_a_wrong_mode_disagrees_with_live():
    """`refined-clause-names-a-wrong-mode`: a clause whose refined-modes list
    disagrees with `sorted(MODE_SIGN_OFFS)` fails -- guards a hand-written
    clause drifting from the mapping it claims to summarise. The wrong id is
    derived from live state (a mode id not in `MODE_SIGN_OFFS`), never a
    hardcoded literal, so the control cannot coincide with live state by
    accident."""
    import segfacet.failure_modes as fm

    live_ids = sorted(fm.MODE_SIGN_OFFS)
    assert live_ids, "MODE_SIGN_OFFS is empty; this fixture needs >=1 signed mode"
    unsigned_ids = [i for i in sorted(fm.SPECIFICATION) if i not in fm.MODE_SIGN_OFFS]
    assert unsigned_ids, "every mode is signed off; this fixture needs an unsigned one"
    wrong_ids = live_ids[:-1] + [unsigned_ids[0]]
    assert sorted(wrong_ids) != live_ids

    text = (
        f"modes refined by stage 32: {_render_ids(wrong_ids)}; "
        f"at the fully-specified bar: none; left as documented drafts: 0"
    )
    match = _REFINED_BAR_DRAFTS_RE.search(text)
    assert match is not None
    refined_str = match.group(1)
    assert refined_str != _render_ids(live_ids), (
        "expected the wrong-mode clause to disagree with the live "
        "MODE_SIGN_OFFS rendering"
    )


# =========================================================================== #
# AC9: no mode, recomputed live, meets all six bar conditions.
# =========================================================================== #


def test_ac9_no_mode_recomputed_live_meets_all_six_bar_conditions(bar_conditions_by_mode):
    import segfacet.failure_modes as fm

    at_bar = _modes_at_bar(bar_conditions_by_mode, fm.MODE_SIGN_OFFS)

    # Per-sign-off diagnostic (which of the two halves -- conditions 1-5,
    # outcome -- failed), folded into the failure message rather than
    # asserted separately: nothing beyond "the set is empty" is required.
    diagnostics = {}
    for mode_id, record in fm.MODE_SIGN_OFFS.items():
        conditions_met = all(c.met for c in bar_conditions_by_mode[mode_id])
        diagnostics[mode_id] = {
            "conditions_1_5_met": conditions_met,
            "outcome": record.outcome,
        }

    assert at_bar == [], (
        f"expected no mode to meet all six bar conditions live; found "
        f"{at_bar} (per-sign-off diagnostics: {diagnostics})"
    )


def test_adv_bar_predicate_is_not_vacuous(bar_conditions_by_mode):
    """`bar-predicate-is-not-vacuous`: over a constructed mapping in which
    one mode whose conditions 1-5 all hold carries `outcome="at-the-bar"`,
    AC9's predicate returns that mode -- guards a predicate that yields the
    empty set for the wrong reason, such as an outcome string that never
    matches."""
    import segfacet.failure_modes as fm

    qualifying = [
        mode_id
        for mode_id, conditions in bar_conditions_by_mode.items()
        if all(c.met for c in conditions)
    ]
    assert qualifying, (
        "expected >=1 mode to meet bar_conditions 1-5 live -- if none does, "
        "this fixture needs a different source of a qualifying mode"
    )
    mode_id = sorted(qualifying)[0]

    local_sign_offs = {
        mode_id: fm.ModeSignOff(
            mode_id=mode_id,
            date="2026-09-22",
            outcome="at-the-bar",
            note="constructed for the adversarial test only, not shipped",
        )
    }
    assert mode_id not in fm.MODE_SIGN_OFFS or fm.MODE_SIGN_OFFS[mode_id].outcome != (
        "at-the-bar"
    ), "the constructed claim must exercise the predicate, not just repeat live state"

    at_bar = _modes_at_bar(bar_conditions_by_mode, local_sign_offs)
    assert at_bar == [mode_id], (
        f"expected the predicate to return [{mode_id}] for a mode that "
        f"clears all five live conditions and carries a local 'at-the-bar' "
        f"claim; got {at_bar}"
    )


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
