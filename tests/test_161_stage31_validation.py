"""Tests for item 161 -- Stage 31 validation: the in-suite assertable subset.

Item 161 closes Stage 31 by replaying its five roadmap acceptance criteria
end to end from a clean clone (a fresh checkout with its own venv, the named
checks from items 152-155/160 re-run by node id, the eval harness re-run,
the triage counts re-measured, `aide check`, the full suite). Per the item
spec's Assumption A2 and Testing Strategy, every one of those is a **replay**
obligation discharged and recorded in `progress.md` and the item's Decisions
log -- not something this module can assert without duplicating a merged
test's tree-wide scan under a second name that could drift from the first.

This module covers exactly the two criteria the spec designates **in-suite**:

    AC14 -- every Stage 31 acceptance box is attested with evidence or
            annotated with a reason.
    AC15 -- the parser sees exactly the roadmap's Stage 31 acceptance
            bullets (no box the roadmap doesn't mirror, no roadmap bullet
            the progress-file boxes don't mirror).

AC1-AC13 and AC16-AC19 are replay-only and belong to the item's Decisions
log and Validation section, not here -- with one exception added
2026-09-17: Stage 31 criterion 2's module-prose half (Assumption A4,
reading R2) is pinned by a tree-wide scan of `src/segfacet/**/*.py` below,
because no merged test scans module prose for a numbered-§6 claim.

Per Assumption A2, AC14 is expected to fail (before this item's bookkeeping
step runs `aide progress accept`/`amend`/`retract`, or hand-annotates a
criterion that does not hold) -- at commit time Stage 31 carries four
unannotated boxes and one already-annotated one. That is not a defect in
this test: it is the honest state of a section not yet bookkept, and the
whole reason AC14 belongs in-suite instead of being folded into a "the
stage is done" claim this module cannot re-derive.

Discipline followed (Testing Strategy):

- Parsing goes entirely through `.aide/scripts/aide.py`'s own
  `stage_section` / `acceptance_boxes` / `roadmap_acceptance_bullets`,
  loaded in-process (the `test_150_maintainer_sign_off.py` idiom). The one
  helper this module writes is continuation-line gathering -- turning a
  checkbox's line index into the *text* AC14 inspects -- since neither of
  those functions returns box text, only line indices.
- No count of `aide check` warnings, triage entries, harness constants or
  the engine version is pinned here: those are dated measurements that
  legitimately move and live in `progress.md`'s evidence and Decisions.
- No insight entry is pinned.
- No git history, clone, network access or environment profile is needed.
- Every adversarial case is an in-memory `progress.md`/`roadmap.md` text
  passed to the same in-process helpers; none writes a file.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import List

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_DOCS_AIDE_DIR = _REPO_ROOT / "docs" / "aide"
_PROGRESS_PATH = _DOCS_AIDE_DIR / "progress.md"
_ROADMAP_PATH = _DOCS_AIDE_DIR / "roadmap.md"
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"

_STAGE = "31"

#: Mirrors `.aide/scripts/aide.py`'s own `_ACCEPT_TRAIL_RE` shape: an
#: indented dated correction line under an acceptance box. A box's
#: continuation text stops here -- a trail line's own `*(...)*` (an engine
#: version, a re-verification note) is never the box's attestation.
_TRAIL_LINE_RE = re.compile(r"^\s+[-*]\s+\*\*\d{4}-\d{2}-\d{2}\*\*\s*→")

#: A non-empty `*(...)*` annotation. `.+` (not `.*`) is what makes `*()*`
#: fail to match -- AC14 requires the annotation carry content.
_ANNOTATION_RE = re.compile(r"\*\(.+\)\*", re.DOTALL)


def _aide_module():
    spec = importlib.util.spec_from_file_location("_aide_cli_161", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _box_text(lines: List[str], box: int, sub_end: int) -> str:
    """The checkbox line at *box* plus its indented continuation lines.

    Per the item spec's AC14: continuation gathering stops at a trail line,
    a blank line, the next box, or the section end. *sub_end* is already
    bounded to the next box's line index (or the section end) by the
    caller, so "the next box" needs no separate check here.
    """
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


def _annotation_violations(lines: List[str], start: int, end: int, aide) -> List[str]:
    """Checkbox lines (stripped, for the failure message) with no non-empty
    `*(...)*` annotation anywhere in their gathered box text."""
    boxes = aide.acceptance_boxes(lines, start, end)
    violations = []
    for k, box in enumerate(boxes):
        sub_end = boxes[k + 1] if k + 1 < len(boxes) else end
        text = _box_text(lines, box, sub_end)
        if not _ANNOTATION_RE.search(text):
            violations.append(lines[box].strip())
    return violations


def _spliced_trail_violations(lines: List[str], start: int, end: int, aide) -> List[str]:
    """Checkbox lines (stripped) whose block carries a trail line followed by
    a further indented, non-trail line before the block ends.

    A correctly-wrapped box's own continuation lines all sit *before* its
    first trail line; `_box_text` stops gathering there by design (a trail
    line's own annotation is never the box's attestation). But that means a
    splice that reorders a wrapped box -- first line, trail line, *then* the
    continuation `aide progress amend` displaced below it -- would silently
    lose that continuation from `_box_text`'s gathered text with no signal:
    the trail-line-then-continuation shape reads as if the box had no
    continuation at all. This walks each box's full block (not stopping at
    the first trail line) and flags one where an indented, non-trail line
    follows a trail line -- the splice's structural signature.
    """
    boxes = aide.acceptance_boxes(lines, start, end)
    violations = []
    for k, box in enumerate(boxes):
        sub_end = boxes[k + 1] if k + 1 < len(boxes) else end
        seen_trail = False
        for i in range(box + 1, sub_end):
            line = lines[i]
            if not line.strip():
                break
            if not line[:1].isspace():
                break
            if _TRAIL_LINE_RE.match(line):
                seen_trail = True
                continue
            if seen_trail:
                violations.append(lines[box].strip())
                break
    return violations


# =========================================================================== #
# AC14: every Stage 31 acceptance box is attested with evidence or annotated
# with a reason.
# =========================================================================== #


def test_ac14_every_stage31_box_is_attested_or_annotated():
    aide = _aide_module()
    lines = _PROGRESS_PATH.read_text(encoding="utf-8").splitlines()
    section = aide.stage_section(lines, _STAGE)
    assert section is not None, "no Stage 31 section found in progress.md"
    start, end, _stage_num = section
    boxes = aide.acceptance_boxes(lines, start, end)
    assert boxes, "Stage 31 section carries no acceptance boxes"

    violations = _annotation_violations(lines, start, end, aide)
    assert violations == [], (
        "Stage 31 acceptance box(es) with no evidence/reason annotation "
        f"(A2: expected to fail until item 161's bookkeeping step runs): {violations}"
    )


def test_adv_ac14_ticked_box_with_no_annotation_is_flagged():
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] Some criterion with no annotation.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations, "expected the annotation-less ticked box to be flagged"


def test_adv_ac14_unticked_box_with_no_annotation_is_flagged():
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some criterion with no annotation.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations, "expected the annotation-less unticked box to be flagged"


def test_adv_ac14_wrapped_box_annotated_at_end_of_first_line_is_not_flagged():
    """The shape `aide progress accept --evidence` writes (A6): the
    annotation lands on the box's first physical line, mid-criterion, with
    the criterion's own wording continuing on the indented line below."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] The installed engine version equals the framework's at the "
        "time *(accepted 2026-09-17: AC2, clone abc123.)*\n"
        "  the stage's queue was planned, or the gap and its reason are "
        "recorded.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations == []


def test_adv_ac14_wrapped_box_annotated_on_last_continuation_line_is_not_flagged():
    """The AC16 hand-annotation shape: a criterion that does not hold stays
    unticked, and the reason lands at the end of the box's *last*
    continuation line, not its first."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some long criterion\n"
        "  spanning two lines, not attested. "
        "*(not attested 2026-09-17, item 161: AC5 counted 42 hits.)*\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations == []


def test_adv_ac14_retracted_box_keeps_its_original_annotation_and_is_not_flagged():
    """A retraction unticks the box, appends a `retracted: ` trail line, and
    leaves the box's original annotation untouched (A6). Continuation
    gathering must stop at the trail line without losing the annotation
    that sits on the box's own line above it."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] No consumer distinguishes a clean control from a "
        "condition-only case. *(accepted 2026-09-16: AC12 verified.)*\n"
        "  - **2026-09-17** → retracted: AC10 failed in the clone.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations == []


def test_adv_ac14_annotation_inside_a_trail_line_does_not_count():
    """A trail line's own `*(...)*` (an engine version, a re-verification
    note) is never the box's own attestation. A box whose only annotation
    sits inside a trail line must still be flagged."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some criterion with no annotation of its own.\n"
        "  - **2026-09-17** → retracted: AC10 failed *(engine 1.53.0)*.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations, "expected the box to be flagged despite the trail's own annotation"


def test_adv_wrapped_box_continuation_before_trail_line_is_gathered():
    """Correctly-ordered shape: the continuation line sits before the trail
    line. `_box_text` must still include it, and the structural splice check
    must find nothing wrong with this box."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some long criterion\n"
        "  spanning two lines, not attested. *(not attested 2026-09-17, item 161.)*\n"
        "  - **2026-09-17** → retracted: AC10 failed in the clone.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    boxes = aide.acceptance_boxes(lines, start, end)
    assert boxes, "expected at least one acceptance box in the synthetic section"
    text = _box_text(lines, boxes[0], end)
    assert "spanning two lines" in text, (
        "expected the pre-trail continuation line to be part of the gathered box text"
    )
    violations = _spliced_trail_violations(lines, start, end, aide)
    assert violations == []


def test_adv_spliced_trail_before_continuation_is_flagged():
    """The defective shape a hand-edit/`amend` can produce: the checkbox's
    first line, then a trail line, then an indented continuation line that
    belongs to the box's own criterion text -- displaced *below* the trail
    line instead of staying above it. `_box_text` would silently drop that
    continuation (it stops gathering at the first trail line), so this must
    be caught structurally instead."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some long criterion, not attested. *(not attested 2026-09-17.)*\n"
        "  - **2026-09-17** → retracted: AC10 failed in the clone.\n"
        "  spanning two lines that got spliced below the trail line.\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _spliced_trail_violations(lines, start, end, aide)
    assert violations, "expected the trail-then-continuation splice to be flagged"


def test_adv_box_with_no_trail_line_has_no_splice_violation():
    """A box with no trail line at all (the common case) must never be
    flagged by the splice check -- it has nothing to splice."""
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] Criterion one. *(evidence one.)*\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _spliced_trail_violations(lines, start, end, aide)
    assert violations == []


def test_live_stage31_section_has_no_spliced_trail_lines():
    """Structural regression guard: a future `aide progress amend` on Stage
    31 must not reproduce the trail-line/continuation splice fixed by this
    item (criterion 4's box). Runs against the live progress.md, not a
    fixture, so it reds the suite the moment the shape reappears."""
    aide = _aide_module()
    lines = _PROGRESS_PATH.read_text(encoding="utf-8").splitlines()
    section = aide.stage_section(lines, _STAGE)
    assert section is not None, "no Stage 31 section found in progress.md"
    start, end, _stage_num = section
    boxes = aide.acceptance_boxes(lines, start, end)
    assert boxes, "Stage 31 section carries no acceptance boxes"

    violations = _spliced_trail_violations(lines, start, end, aide)
    assert violations == [], (
        f"Stage 31 acceptance box(es) with a trail line spliced before a "
        f"later continuation line: {violations}"
    )


def test_adv_ac14_empty_annotation_is_flagged():
    aide = _aide_module()
    lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [ ] Some criterion. *()*\n"
    ).splitlines()
    start, end, _ = aide.stage_section(lines, _STAGE)
    violations = _annotation_violations(lines, start, end, aide)
    assert violations, "expected the empty annotation *()* to be flagged"


# =========================================================================== #
# AC15: the parser sees exactly the roadmap's criteria.
# =========================================================================== #


def test_ac15_box_count_equals_roadmap_bullet_count():
    aide = _aide_module()
    progress_lines = _PROGRESS_PATH.read_text(encoding="utf-8").splitlines()
    section = aide.stage_section(progress_lines, _STAGE)
    assert section is not None, "no Stage 31 section found in progress.md"
    start, end, _ = section
    boxes = aide.acceptance_boxes(progress_lines, start, end)
    assert boxes, "Stage 31 section carries no acceptance boxes"

    roadmap_lines = _ROADMAP_PATH.read_text(encoding="utf-8").splitlines()
    bullets = aide.roadmap_acceptance_bullets(roadmap_lines, _STAGE)
    assert bullets is not None, (
        "no Validation / acceptance block for Stage 31 found in roadmap.md"
    )
    assert bullets, "Stage 31's Validation / acceptance block carries no bullets"

    assert len(boxes) == len(bullets), (
        f"progress.md Stage 31 has {len(boxes)} acceptance box(es); "
        f"roadmap.md's Validation / acceptance block has {len(bullets)}"
    )


_SYNTHETIC_ROADMAP_STAGE31 = (
    "## Stage 31 — Post-Sign-Off Maintenance (G7, G8)\n"
    "\n"
    "**Validation / acceptance.**\n"
    "\n"
    "- The installed engine version equals the framework's.\n"
    "- vision.md names the specification.\n"
    "- No module references the legacy map.\n"
    "- No consumer distinguishes by failure_mode == 0 alone.\n"
    "- Every open defect/gap insight is ticked, re-homed, or left open.\n"
    "\n"
    "---\n"
    "\n"
    "## Stage 32 — Selected-Mode Refinement (G2, G7, G8)\n"
)


def test_adv_ac15_matching_five_and_five_counts_are_equal():
    aide = _aide_module()
    roadmap_lines = _SYNTHETIC_ROADMAP_STAGE31.splitlines()
    bullets = aide.roadmap_acceptance_bullets(roadmap_lines, _STAGE)
    assert bullets is not None
    assert len(bullets) == 5

    progress_lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] Criterion one. *(evidence one.)*\n"
        "- [x] Criterion two. *(evidence two.)*\n"
        "- [x] Criterion three. *(evidence three.)*\n"
        "- [x] Criterion four. *(evidence four.)*\n"
        "- [x] Criterion five. *(evidence five.)*\n"
    ).splitlines()
    start, end, _ = aide.stage_section(progress_lines, _STAGE)
    boxes = aide.acceptance_boxes(progress_lines, start, end)
    assert len(boxes) == len(bullets) == 5


def test_adv_ac15_a_sixth_box_makes_the_count_mismatch_fail():
    aide = _aide_module()
    roadmap_lines = _SYNTHETIC_ROADMAP_STAGE31.splitlines()
    bullets = aide.roadmap_acceptance_bullets(roadmap_lines, _STAGE)
    assert bullets is not None
    assert len(bullets) == 5

    progress_lines = (
        "## Stage 31 — Post-Sign-Off Maintenance (G7, G8) — 🚧\n"
        "\n"
        "**Acceptance.**\n"
        "\n"
        "- [x] Criterion one. *(evidence one.)*\n"
        "- [x] Criterion two. *(evidence two.)*\n"
        "- [x] Criterion three. *(evidence three.)*\n"
        "- [x] Criterion four. *(evidence four.)*\n"
        "- [x] Criterion five. *(evidence five.)*\n"
        "- [x] An unexpected sixth criterion. *(evidence six.)*\n"
    ).splitlines()
    start, end, _ = aide.stage_section(progress_lines, _STAGE)
    boxes = aide.acceptance_boxes(progress_lines, start, end)
    assert len(boxes) == 6
    assert len(boxes) != len(bullets)


# --------------------------------------------------------------------------- #
# Stage 31 criterion 2, module-prose half (Assumption A4, reading R2)
# --------------------------------------------------------------------------- #

_SRC_DIR = _REPO_ROOT / "src" / "segfacet"

#: Item 161's scan: prose attributing a numbered mode to vision.md §6, which
#: asserts §6 carries a numbered mode list (v4 §6 carries none).
_NUMBERED_SECTION6_RE = re.compile(
    r"§6('s)? (failure[ -])?modes? [0-9]+|§6's (eight )?numbered|numbered eight"
)

#: The one exemption: a line that names v3 explicitly, i.e. reads as history.
_V3_HISTORY_RE = re.compile(r"\bv3\b")


def _numbered_section6_claims(text: str) -> List[int]:
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if _NUMBERED_SECTION6_RE.search(line) and not _V3_HISTORY_RE.search(line)
    ]


def test_criterion2_no_module_attributes_a_numbered_mode_to_section6():
    sources = sorted(_SRC_DIR.rglob("*.py"))
    assert len(sources) > 20, _SRC_DIR.as_posix()
    violations = [
        f"{path.relative_to(_REPO_ROOT).as_posix()}:{number}"
        for path in sources
        for number in _numbered_section6_claims(path.read_text(encoding="utf-8"))
    ]
    assert violations == [], (
        "module prose attributes a numbered failure mode to vision.md §6; "
        "cite failure_modes.SPECIFICATION instead: " + ", ".join(violations)
    )


def test_adv_criterion2_matcher_flags_a_section6_mode_number():
    text = (
        '"""Overlap rule.\n'
        "\n"
        "Implements an overlap rule targeting §6 failure mode 8.\n"
        "# §6 modes 2, 3 (item 136)\n"
        "dispositioned mode-less because §6's eight numbered modes name none\n"
        "targeting failure mode 15 in failure_modes.SPECIFICATION\n"
        "Mode 9 is not one of v3 vision.md §6's numbered eight.\n"
    )
    assert _numbered_section6_claims(text) == [3, 4, 5]
