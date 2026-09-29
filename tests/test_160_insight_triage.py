"""Tests for item 160 -- insight triage to a known state.

Covers Acceptance Criterion AC6: every re-home destination in item 160's
disposition table resolves in ``docs/aide/roadmap.md``. AC1-AC5, AC7 and AC8
(and their adversarial predicate tests) were retired on 2026-09-29: they read
the live docs/aide/insights.md, which conventions §6 forbids (engine
2.10.0+); the triage is a diff-time claim the validator checked at merge.
AC9-AC12 are diff-time or recorded-measurement claims checked by the
validator on the branch, and AC13 is covered by
`tests/test_aide_check_no_errors.py`.

See ``docs/aide/items/160-insight-triage-to-a-known.md`` for the full
disposition table (S1-S29, Q1-Q6) this module transcribes once as
``_ROWS``.

Adversarial / edge cases (Testing Strategy): AC6's roadmap resolver is
scoped to the ``## Stage 32 -- `` section; a ``- **D3 -- `` bullet that
exists only under a different stage's heading must not satisfy it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP_MD = REPO_ROOT / "docs" / "aide" / "roadmap.md"

TICKED = "ticked"
REHOMED = "re-homed"
LEFT_OPEN = "left-open"


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
