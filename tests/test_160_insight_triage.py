"""Tests for item 160 -- insight triage to a known state.

Covers Acceptance Criteria AC1-AC8. AC9-AC12 are diff-time or
recorded-measurement claims and are checked by the validator on the branch,
not by this suite (`.aide/conventions/6-test-hygiene.md`: "A scope claim
about a diff belongs on the branch, not in the suite", and a count the
loop's own verbs move is never pinned). AC13 is covered by the existing
`tests/test_aide_check_no_errors.py`.

See ``docs/aide/items/160-insight-triage-to-a-known.md`` for the full
disposition table (S1-S29, Q1-Q6) this module transcribes once as
``_ROWS``, keyed by type + provenance + date + claim substring, never by
list number (`aide insights archive` renumbers).

Adversarial / edge cases (Testing Strategy):

- AC2/AC4/AC7 predicates are each exercised on synthetic, in-memory text
  first, with a planted positive and negative control, before being trusted
  against the real inbox.
- AC1's resolver is shown a synthetic duplicate (same key in two texts) so
  it reports two matches, not one.
- AC6's roadmap resolver is scoped to the ``## Stage 32 -- `` section; a
  ``- **D3 -- `` bullet that exists only under a different stage's heading
  must not satisfy it.
- AC8 is bounded by date, not by count: a synthetic unticked ``gap`` dated
  2026-09-15 (in scope) fails the predicate with no trail; the same entry
  dated 2026-09-18 (out of scope) is excluded from the check entirely.

This item touches no production code. Reading happens against
``docs/aide/insights.md`` plus every ``docs/aide/insights/archive-*.md`` (an
``aide insights archive`` sweep must not turn any test here red) and against
``docs/aide/roadmap.md`` (AC6). ``parse_insights`` is loaded in-process from
``.aide/scripts/aide.py`` via ``importlib``, the same pattern
``tests/test_aide_check_no_errors.py`` uses (A8) -- no subprocess, no
reimplementation of the parser.
"""

from __future__ import annotations

import datetime
import importlib.util
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AIDE_SCRIPT = REPO_ROOT / ".aide" / "scripts" / "aide.py"
INSIGHTS_MD = REPO_ROOT / "docs" / "aide" / "insights.md"
INSIGHTS_ARCHIVE_DIR = REPO_ROOT / "docs" / "aide" / "insights"
ROADMAP_MD = REPO_ROOT / "docs" / "aide" / "roadmap.md"

TICKED = "ticked"
REHOMED = "re-homed"
LEFT_OPEN = "left-open"

_LEFT_OPEN_TRAIL_RE = re.compile(r"^\s+- \*\*(\d{4}-\d{2}-\d{2})\*\* → left open: \S")
_REHOME_POINTER_RE = re.compile(r"^re-homed \((\d{4}-\d{2}-\d{2})\): ")
_AC8_DATE_BOUND = "2026-09-16"


# ---------------------------------------------------------------------------
# In-process access to the engine's own parser (A8) -- no subprocess, no
# reimplementation.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _aide_module():
    spec = importlib.util.spec_from_file_location("_aide_cli_160", AIDE_SCRIPT)
    aide = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aide)  # type: ignore[union-attr]
    return aide


def _parse(text: str):
    return _aide_module().parse_insights(text)


@lru_cache(maxsize=1)
def _all_entries() -> Tuple:
    """Every entry in the live inbox plus every archive file.

    An `aide insights archive` sweep moves entries between these two
    sources without changing their content, so every test here reads both
    (CLAUDE.md's documented gotcha) rather than pinning which file holds a
    given row.
    """
    entries = list(_parse(INSIGHTS_MD.read_text(encoding="utf-8")))
    for archive in sorted(INSIGHTS_ARCHIVE_DIR.glob("archive-*.md")):
        entries.extend(_parse(archive.read_text(encoding="utf-8")))
    return tuple(entries)


@lru_cache(maxsize=1)
def _roadmap_text() -> str:
    return ROADMAP_MD.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The frozen row tuple (Description's disposition table, transcribed once).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Row:
    row: str
    type: str
    source: Optional[str]
    date: str
    claim: str
    disposition: str
    # AC3: token(s) a ticked row's pointer/trail must contain.
    evidence: Tuple[str, ...] = ()
    # AC5/AC6: the roadmap destination token a re-homed row's pointer names.
    destination: str = ""
    # AC5: literal "mode N" / "modes N/M" substrings the pointer must contain.
    mode_pointer_tokens: Tuple[str, ...] = ()
    # AC6: bare mode ids ("13" covers the "13/14" pair) resolved in roadmap.md.
    mode_ids: Tuple[str, ...] = field(default_factory=tuple)


_ROWS: Tuple[Row, ...] = (
    Row("S1", "gap", None, "2026-09-01", "three of the five CI legs in",
        REHOMED, destination="roadmap.md Carried defects"),
    Row("S2", "gap", None, "2026-09-01",
        "re-extracts every case's features once per grid point",
        REHOMED, destination="roadmap.md Stage 21"),
    Row("S3", "gap", "stage 20 criterion 5", "2026-09-02",
        "acceptance criterion retracted:", REHOMED,
        destination="roadmap.md Stage 32 D3"),
    Row("S4", "gap", "stage 20 criterion 4", "2026-09-02",
        "acceptance criterion retracted:", REHOMED,
        destination="roadmap.md Stage 32 D0"),
    Row("S5", "gap", "stage 20 criterion 3", "2026-09-02",
        "acceptance criterion retracted:", REHOMED,
        destination="roadmap.md Stage 32 D0"),
    Row("S6", "gap", "stage 20 criterion 1", "2026-09-02",
        "acceptance criterion retracted:", REHOMED,
        destination="roadmap.md Stage 32 D3"),
    Row("S7", "gap", "item 143", "2026-09-03",
        "is now byte-compared fresh-vs-committed", TICKED, evidence=("item 158",)),
    Row("S8", "defect", "item 143", "2026-09-03",
        "test_ac16_record_covers_exactly_the_required_artifact_set", TICKED,
        evidence=("item 159",)),
    Row("S9", "defect", "item 144", "2026-09-03",
        "unconditionally imports", TICKED, evidence=("item 159",)),
    Row("S10", "gap", "item 144", "2026-09-03",
        "classifier resolves a module root only from a", TICKED,
        evidence=("item 158",)),
    Row("S11", "defect", "item 146", "2026-09-04",
        "test_ac23_fresh_matches_committed_structurally_and_carries_all_eight_ids",
        TICKED, evidence=("item 159",)),
    Row("S12", "defect", "item 146", "2026-09-04",
        "test_ac30_proposed_entry_acquiring_a_declaring_rule_is_reported",
        TICKED, evidence=("item 159",)),
    Row("S13", "defect", "item 146", "2026-09-04",
        "now carries mode 9 as a mode row whose", TICKED, evidence=("item 156",)),
    Row("S14", "defect", "item 146", "2026-09-04",
        "the two documents the contract was authored in still assert it verbatim",
        TICKED, evidence=("item 156",)),
    Row("S15", "defect", "item 147", "2026-09-04",
        "evidence-rungs paragraph calls mode 7's", TICKED, evidence=("7d800a2",)),
    Row("S16", "defect", "item 147", "2026-09-04",
        "relying on exactly the declared→corpus direction item 147 step 8 deletes",
        TICKED, evidence=("item 159",)),
    Row("S17", "defect", "item 147", "2026-09-04",
        "carries the same false mode-7 claim item 147 corrected", TICKED,
        evidence=("item 154",)),
    Row("S18", "defect", "item 147", "2026-09-04",
        "checks cannot pass as written against item 147's own spec", TICKED,
        evidence=("item 159",)),
    Row("S19", "gap", "item 147", "2026-09-04",
        "nothing reports a rule declaring a", TICKED, evidence=("item 156",)),
    Row("S20", "gap", "item 148", "2026-09-04",
        "classification (item 148) is an authored claim no shipped check can refute",
        LEFT_OPEN),
    Row("S21", "defect", "item 148", "2026-09-04",
        "omits two pins that break as a direct, mechanical consequence", TICKED,
        evidence=("tests/test_137_mode_less_rule_disposition.py",)),
    Row("S22", "defect", "item 148", "2026-09-04",
        "two committed tests fail against item 148's own spec, both test-side",
        TICKED, evidence=("item 159",)),
    Row("S23", "gap", "item 150", "2026-09-14",
        "the Stage-18/29 eval harness", TICKED, evidence=("item 153",)),
    Row("S24", "gap", "item 150", "2026-09-14",
        "numbered eight-item list no longer matches the catalogue", TICKED,
        evidence=("item 152",)),
    Row("S25", "gap", "item 150", "2026-09-14",
        "three detectors the sign-off asked for that no shipped rule provides",
        REHOMED, destination="roadmap.md Stage 32 Known inputs per mode",
        mode_pointer_tokens=("mode 6", "mode 11", "modes 13/14"),
        mode_ids=("6", "11", "13")),
    Row("S26", "gap", "item 150", "2026-09-14",
        "lumbosacral transitional-anatomy sub-type", REHOMED,
        destination="roadmap.md Stage 32 Known inputs per mode",
        mode_pointer_tokens=("mode 2",), mode_ids=("2",)),
    Row("S27", "gap", "item 150", "2026-09-14",
        "per-detector attribution is now a live need, not a nicety", REHOMED,
        destination="roadmap.md Stage 32 Known inputs per mode",
        mode_pointer_tokens=("mode 9",), mode_ids=("9",)),
    Row("S28", "gap", "item 150", "2026-09-14",
        "in a corpus manifest now means two things", TICKED,
        evidence=("item 155",)),
    Row("S29", "gap", "item 150", "2026-09-15",
        "detectors and fixtures the 2026-09-15 split asked for", REHOMED,
        destination="roadmap.md Stage 32 Known inputs per mode",
        mode_pointer_tokens=("mode 5", "mode 7", "mode 3"),
        mode_ids=("5", "7", "3")),
    Row("Q1", "defect", "item 152", "2026-09-16",
        "test_ac14_every_item_150_insight_is_well_formed_and_honestly_dated",
        TICKED, evidence=("ecdc81d",)),
    Row("Q2", "defect", "item 154", "2026-09-16", "declaring mode 1 by", LEFT_OPEN),
    Row("Q3", "gap", "item 155", "2026-09-16",
        "the eval harness groups corpus cases by", LEFT_OPEN),
    Row("Q4", "gap", "item 155", "2026-09-16",
        "would pass the scan undetected", LEFT_OPEN),
    Row("Q5", "gap", "item 158", "2026-09-17",
        "resolver has no branch for the os.path.dirname(os.path.abspath(__file__)) root idiom",
        LEFT_OPEN),
    Row("Q6", "defect", "item 158", "2026-09-17",
        "splits it into copies with byte-identical prose", TICKED,
        evidence=("item 159",)),
)

assert len(_ROWS) == 35, "the spec's S1-S29 + Q1-Q6 cohorts total 35 rows"

_TICKED_ROWS = tuple(r for r in _ROWS if r.disposition == TICKED)
_REHOMED_ROWS = tuple(r for r in _ROWS if r.disposition == REHOMED)
_LEFT_OPEN_ROWS = tuple(r for r in _ROWS if r.disposition == LEFT_OPEN)
assert len(_TICKED_ROWS) == 20 and len(_REHOMED_ROWS) == 10 and len(_LEFT_OPEN_ROWS) == 5


# ---------------------------------------------------------------------------
# Resolution helper (Testing Strategy).
# ---------------------------------------------------------------------------


def _resolve(entries, row: Row) -> List:
    return [
        e for e in entries
        if e.type == row.type and e.source == row.source and e.date == row.date
        and row.claim in e.text
    ]


def _resolve_one(row: Row):
    matches = _resolve(_all_entries(), row)
    assert len(matches) == 1, (
        f"row {row.row}: expected exactly one match across the inbox and "
        f"archives, found {len(matches)}"
    )
    return matches[0]


# ---------------------------------------------------------------------------
# AC1 -- every row resolves to exactly one entry.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", _ROWS, ids=lambda r: r.row)
def test_ac1_row_resolves_to_exactly_one_entry(row: Row) -> None:
    matches = _resolve(_all_entries(), row)
    assert len(matches) == 1, (
        f"row {row.row}: type={row.type!r} source={row.source!r} "
        f"date={row.date!r} claim={row.claim!r} matched {len(matches)} entries"
    )


def test_ac1_adversarial_duplicate_key_across_inbox_and_archive_is_two_matches() -> None:
    line = "- [ ] gap — a planted duplicate claim for the AC1 resolver *(2026-01-01)*"
    inbox_entries = _parse(line)
    archive_entries = _parse(line)
    combined = inbox_entries + archive_entries
    row = Row("X", "gap", None, "2026-01-01", "planted duplicate claim", LEFT_OPEN)
    matches = _resolve(combined, row)
    assert len(matches) == 2, "the same key in two texts must not collapse to one match"


# ---------------------------------------------------------------------------
# AC2 -- ticked rows are ticked with a pointer.
# ---------------------------------------------------------------------------


def _ac2_holds(entry) -> bool:
    if not entry.ticked:
        return False
    if entry.pointer and entry.pointer.strip():
        return True
    return any(" → " in t and t.split(" → ", 1)[1].strip() for t in entry.trail)


@pytest.mark.parametrize("row", _TICKED_ROWS, ids=lambda r: r.row)
def test_ac2_ticked_row_carries_a_pointer(row: Row) -> None:
    entry = _resolve_one(row)
    assert _ac2_holds(entry), f"row {row.row}: entry is not ticked with a pointer"


def test_ac2_adversarial_ticked_with_no_pointer_and_no_trail_fails() -> None:
    entries = _parse("- [x] defect — no pointer anywhere *(2026-01-01)*")
    assert not _ac2_holds(entries[0])


def test_ac2_adversarial_ticked_with_pointer_passes() -> None:
    entries = _parse("- [x] defect — has a pointer *(2026-01-01)* → somewhere")
    assert _ac2_holds(entries[0])


# ---------------------------------------------------------------------------
# AC3 -- a ticked row's pointer names its recorded evidence.
# ---------------------------------------------------------------------------


def _evidence_present(entry, token: str) -> bool:
    if entry.pointer and token in entry.pointer:
        return True
    return any(token in t for t in entry.trail)


@pytest.mark.parametrize("row", _TICKED_ROWS, ids=lambda r: r.row)
def test_ac3_ticked_row_pointer_names_its_evidence(row: Row) -> None:
    entry = _resolve_one(row)
    for token in row.evidence:
        assert _evidence_present(entry, token), (
            f"row {row.row}: neither the entry-line pointer nor any trail "
            f"line contains {token!r}"
        )


# ---------------------------------------------------------------------------
# AC4 -- re-homed rows are ticked with a dated re-home pointer.
# ---------------------------------------------------------------------------


def _valid_rehome_pointer(pointer: Optional[str]) -> bool:
    if not pointer:
        return False
    m = _REHOME_POINTER_RE.match(pointer)
    if not m:
        return False
    try:
        datetime.date.fromisoformat(m.group(1))
    except ValueError:
        return False
    return True


@pytest.mark.parametrize("row", _REHOMED_ROWS, ids=lambda r: r.row)
def test_ac4_rehomed_row_is_ticked_with_a_dated_rehome_pointer(row: Row) -> None:
    entry = _resolve_one(row)
    assert entry.ticked, f"row {row.row}: re-homed entry must be ticked"
    assert _valid_rehome_pointer(entry.pointer), (
        f"row {row.row}: pointer {entry.pointer!r} does not match "
        r"'^re-homed \(YYYY-MM-DD\): ' with a valid calendar date"
    )


def test_ac4_adversarial_rehome_pointer_with_no_date_fails() -> None:
    assert not _valid_rehome_pointer("re-homed: roadmap.md Stage 32 D0")


def test_ac4_adversarial_rehome_pointer_with_invalid_calendar_date_fails() -> None:
    # The regex alone would accept this; only date.fromisoformat rejects it.
    pointer = "re-homed (2026-13-40): roadmap.md Stage 32 D0"
    assert _REHOME_POINTER_RE.match(pointer) is not None
    assert not _valid_rehome_pointer(pointer)


def test_ac4_adversarial_well_formed_rehome_pointer_passes() -> None:
    assert _valid_rehome_pointer("re-homed (2026-09-17): roadmap.md Stage 21")


# ---------------------------------------------------------------------------
# AC5 -- a re-home pointer names its recorded destination (and mode ids).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", _REHOMED_ROWS, ids=lambda r: r.row)
def test_ac5_rehomed_pointer_names_its_destination(row: Row) -> None:
    entry = _resolve_one(row)
    assert entry.pointer and row.destination in entry.pointer, (
        f"row {row.row}: pointer {entry.pointer!r} does not contain "
        f"destination token {row.destination!r}"
    )
    for token in row.mode_pointer_tokens:
        assert token in entry.pointer, (
            f"row {row.row}: pointer {entry.pointer!r} does not contain "
            f"mode token {token!r}"
        )


# ---------------------------------------------------------------------------
# AC6 -- every re-home destination exists in roadmap.md.
# ---------------------------------------------------------------------------


def _stage32_section(roadmap_text: str) -> str:
    lines = roadmap_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## Stage 32 — "):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## ") or lines[j].startswith("# "):
            end = j
            break
    return "\n".join(lines[start:end])


def _destination_exists(roadmap_text: str, token: str) -> bool:
    lines = roadmap_text.splitlines()
    if token == "roadmap.md Carried defects":
        return any(l.startswith("# Carried defects") for l in lines)
    if token == "roadmap.md Stage 21":
        return any(l.startswith("## Stage 21 — ") for l in lines)
    if token in ("roadmap.md Stage 32 D0", "roadmap.md Stage 32 D3"):
        d = "D0" if token.endswith("D0") else "D3"
        section = _stage32_section(roadmap_text)
        return any(l.startswith(f"- **{d} — ") for l in section.splitlines())
    if token == "roadmap.md Stage 32 Known inputs per mode":
        section = _stage32_section(roadmap_text)
        return any(l.startswith("**Known inputs per mode") for l in section.splitlines())
    raise ValueError(f"unrecognised destination token: {token!r}")


def _mode_exists(roadmap_text: str, mode_id: str) -> bool:
    section = _stage32_section(roadmap_text)
    prefix = f"- *Modes {mode_id} " if mode_id == "13" else f"- *Mode {mode_id} "
    return any(l.startswith(prefix) for l in section.splitlines())


@pytest.mark.parametrize("row", _REHOMED_ROWS, ids=lambda r: r.row)
def test_ac6_rehome_destination_exists_in_roadmap(row: Row) -> None:
    text = _roadmap_text()
    assert _destination_exists(text, row.destination), (
        f"row {row.row}: destination {row.destination!r} does not resolve "
        f"in docs/aide/roadmap.md"
    )
    for mode_id in row.mode_ids:
        assert _mode_exists(text, mode_id), (
            f"row {row.row}: mode {mode_id!r} does not resolve inside "
            f"roadmap.md's Stage 32 section"
        )


def test_ac6_adversarial_missing_bullet_in_stage32_section_fails() -> None:
    roadmap = (
        "## Stage 31 — Something\n"
        "- **D3 — a bullet under the wrong stage.**\n"
        "\n"
        "## Stage 32 — Selected-Mode Refinement\n"
        "- **D0 — the only bullet here.**\n"
        "\n"
        "## Stage 33 — Next\n"
    )
    assert not _destination_exists(roadmap, "roadmap.md Stage 32 D3")


def test_ac6_adversarial_bullet_only_under_another_stage_does_not_satisfy_scoped_lookup() -> None:
    roadmap = (
        "## Stage 20 — Something\n"
        "- **D3 — this D3 belongs to Stage 20, not Stage 32.**\n"
        "\n"
        "## Stage 32 — Selected-Mode Refinement\n"
        "- **D0 — only D0 lives here.**\n"
    )
    assert not _destination_exists(roadmap, "roadmap.md Stage 32 D3")


def test_ac6_adversarial_mode_bullet_resolves_when_present() -> None:
    roadmap = (
        "## Stage 32 — Selected-Mode Refinement\n"
        "**Known inputs per mode** -- a menu.\n"
        "- *Mode 6 not segmented:* the spacing-gap signal.\n"
        "- *Modes 13 collapsed / 14 duplicated:* per-component centroids.\n"
    )
    assert _mode_exists(roadmap, "6")
    assert _mode_exists(roadmap, "13")
    assert not _mode_exists(roadmap, "9")


# ---------------------------------------------------------------------------
# AC7 -- left-open rows carry a dated reason.
# ---------------------------------------------------------------------------


def _left_open_trail_valid(entry) -> bool:
    for t in entry.trail:
        m = _LEFT_OPEN_TRAIL_RE.match(t)
        if not m:
            continue
        try:
            datetime.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        return True
    return False


@pytest.mark.parametrize("row", _LEFT_OPEN_ROWS, ids=lambda r: r.row)
def test_ac7_left_open_row_carries_a_dated_reason(row: Row) -> None:
    entry = _resolve_one(row)
    assert _left_open_trail_valid(entry), (
        f"row {row.row}: no trail line matches "
        r"'^\s+- \*\*YYYY-MM-DD\*\* → left open: <reason>'"
    )


def test_ac7_adversarial_empty_reason_fails() -> None:
    entries = _parse(
        "- [ ] gap — a claim *(2026-09-01)*\n"
        "  - **2026-09-17** → left open: "
    )
    assert not _left_open_trail_valid(entries[0])


def test_ac7_adversarial_zero_indent_trail_is_not_parsed_as_trail() -> None:
    entries = _parse(
        "- [ ] gap — a claim *(2026-09-01)*\n"
        "- **2026-09-17** → left open: a reason"
    )
    # The zero-indent line does not start with "- " prefixed by whitespace,
    # so parse_insights treats it as a new (malformed) entry, not a trail
    # line under the first.
    assert entries[0].trail == []
    assert not _left_open_trail_valid(entries[0])


def test_ac7_adversarial_well_formed_trail_line_passes() -> None:
    entries = _parse(
        "- [ ] gap — a claim *(2026-09-01)*\n"
        "  - **2026-09-17** → left open: a genuine reason"
    )
    assert _left_open_trail_valid(entries[0])


# ---------------------------------------------------------------------------
# AC8 -- no stage-start defect or gap entry is still untriaged.
# ---------------------------------------------------------------------------


def test_ac8_no_defect_or_gap_dated_on_or_before_bound_is_untriaged() -> None:
    offenders = [
        (e.ordinal, e.type, e.date, e.text[:80])
        for e in _all_entries()
        if e.type in ("defect", "gap")
        and not e.ticked
        and e.date is not None
        and e.date <= _AC8_DATE_BOUND
        and not _left_open_trail_valid(e)
    ]
    assert not offenders, (
        f"untriaged defect/gap entries dated on or before {_AC8_DATE_BOUND}: "
        f"{offenders}"
    )


def test_ac8_adversarial_untriaged_entry_in_scope_fails_the_predicate() -> None:
    entries = _parse("- [ ] gap — an untriaged claim with no trail *(2026-09-15)*")
    e = entries[0]
    in_scope_untriaged = (
        e.type in ("defect", "gap") and not e.ticked and e.date is not None
        and e.date <= _AC8_DATE_BOUND and not _left_open_trail_valid(e)
    )
    assert in_scope_untriaged


def test_ac8_adversarial_same_entry_dated_after_the_bound_is_excluded() -> None:
    entries = _parse("- [ ] gap — an untriaged claim with no trail *(2026-09-18)*")
    e = entries[0]
    in_scope = e.date is not None and e.date <= _AC8_DATE_BOUND
    assert not in_scope, "a capture dated after the bound must not be counted"
