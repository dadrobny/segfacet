"""Tests for item 161 -- Stage 31 validation: the in-suite assertable subset.

Item 161 closes Stage 31 by replaying its five roadmap acceptance criteria
end to end from a clean clone (a fresh checkout with its own venv, the named
checks from items 152-155/160 re-run by node id, the eval harness re-run,
the triage counts re-measured, `aide check`, the full suite). Per the item
spec's Assumption A2 and Testing Strategy, every one of those is a **replay**
obligation discharged and recorded in `progress.md` and the item's Decisions
log -- not something this module can assert without duplicating a merged
test's tree-wide scan under a second name that could drift from the first.

AC14 (every Stage 31 acceptance box attested or annotated) and AC15 (the box
count equals the roadmap's bullet count) were the two criteria this module
once covered in-suite. Item 236 retired them on 2026-10-17, with their
synthetic companions: they pinned a stage section's boxes, annotations and
trail lines, bookkeeping that `aide progress archive` moves out of
`progress.md` and `roadmap.md` (the 2026-09-16 precedent).

AC1-AC13 and AC16-AC19 are replay-only and belong to the item's Decisions
log and Validation section, not here -- with one exception added
2026-09-17: Stage 31 criterion 2's module-prose half (Assumption A4,
reading R2) is pinned by a tree-wide scan of `src/segfacet/**/*.py` below,
because no merged test scans module prose for a numbered-§6 claim.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
# Retired by item 236 (2026-10-17): AC14 and AC15 pinned Stage 31's acceptance boxes, annotations and trail lines in progress.md and their count against roadmap.md, bookkeeping that 'aide progress archive' moves out of both documents; their synthetic companions and helpers had no other subject.
# Removed: _DOCS_AIDE_DIR, _PROGRESS_PATH, _ROADMAP_PATH, _AIDE_SCRIPT, _STAGE, _TRAIL_LINE_RE, _ANNOTATION_RE, _aide_module, _box_text, _annotation_violations, _spliced_trail_violations, test_ac14_every_stage31_box_is_attested_or_annotated, test_adv_ac14_ticked_box_with_no_annotation_is_flagged, test_adv_ac14_unticked_box_with_no_annotation_is_flagged, test_adv_ac14_wrapped_box_annotated_at_end_of_first_line_is_not_flagged, test_adv_ac14_wrapped_box_annotated_on_last_continuation_line_is_not_flagged, test_adv_ac14_retracted_box_keeps_its_original_annotation_and_is_not_flagged, test_adv_ac14_annotation_inside_a_trail_line_does_not_count, test_adv_wrapped_box_continuation_before_trail_line_is_gathered, test_adv_spliced_trail_before_continuation_is_flagged, test_adv_box_with_no_trail_line_has_no_splice_violation, test_live_stage31_section_has_no_spliced_trail_lines, test_adv_ac14_empty_annotation_is_flagged, test_ac15_box_count_equals_roadmap_bullet_count, _SYNTHETIC_ROADMAP_STAGE31, test_adv_ac15_matching_five_and_five_counts_are_equal, test_adv_ac15_a_sixth_box_makes_the_count_mismatch_fail.


# =========================================================================== #
# AC14: every Stage 31 acceptance box is attested with evidence or annotated
# with a reason.
# =========================================================================== #


# =========================================================================== #
# AC15: the parser sees exactly the roadmap's criteria.
# =========================================================================== #


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
