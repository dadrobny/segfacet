"""Tests for item 214 -- the feature-record taxonomy design note.

The deliverable is ``docs/feature-taxonomy.md``; these tests read its mapping
table and answers through ``tests/feature_taxonomy_mapping.py`` and the
sign-off gate row through ``.aide/scripts/aide.py``'s ``human_gates()``
(the idiom of ``tests/test_168_maintainer_sign_off.py``). Only AC8 asserts
what the design decides, and that is the maintainer's own 2026-10-05
decision; the design's adequacy is the gate's to judge. AC1 compares against
a frozen literal and reads no file a migration changes.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from feature_taxonomy_mapping import NOTE_PATH, answer_lines, read_mapping

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_PROGRESS_MD = _REPO_ROOT / "docs" / "aide" / "progress.md"

_GATE_TEXT = "Stage 27 feature-record taxonomy sign-off"

#: Frozen pre-migration path set: (count, SHA-256 of the sorted, newline-joined
#: list). Held here on purpose -- item 215 rewrites the catalogue.
_FROZEN_OLD_PATHS = (
    165,
    "488221662105adf220e4b35dbc541acda4b21f1f2ed994ac0098bf34bc067667",
)

_ANSWER_HEADINGS_KNOWN = (
    "### Identity fields stored in several containers",
    "### stage3 and image_features beside per_label",
    "### Image-axis-relative shape features",
    "### The reference-delta's feature selection",
)
_ANSWER_HEADINGS_INBOX = (
    "### Where per-component features live",
    "### Which path owns adjacent-pair spacing",
)

_SPACING_A = "relationships.neighbour_spacings_mm[]"
_SPACING_B = "stage3.spacing_consistency.spacings_mm[]"


def _aide_module():
    spec = importlib.util.spec_from_file_location("_aide_cli_214", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _old_paths_pair(rows):
    old = sorted(row[0] for row in rows)
    digest = hashlib.sha256("\n".join(old).encode("utf-8")).hexdigest()
    return (len(old), digest)


def _has_one_answer(heading, text=None):
    """True when exactly one non-empty ``**Answer:**`` line sits under it."""
    lines = answer_lines(heading, text)
    return len(lines) == 1 and bool(lines[0][len("**Answer:**"):].strip())


# --------------------------------------------------------------------------- #
# Acceptance criteria
# --------------------------------------------------------------------------- #


def test_ac1_old_paths_are_exactly_the_pre_migration_set():
    assert _old_paths_pair(read_mapping()) == _FROZEN_OLD_PATHS


def test_ac2_new_paths_that_store_a_value_are_unique():
    stored = [new for _, new, change, _ in read_mapping() if change in ("kept", "moved")]
    assert stored, "no kept/moved rows read"
    assert len(stored) == len(set(stored))


def test_ac3_every_merged_row_lands_on_a_stored_field():
    rows = read_mapping()
    stored = {new for _, new, change, _ in rows if change in ("kept", "moved")}
    merged = [new for _, new, change, _ in rows if change == "merged"]
    assert merged, "no merged rows read"
    assert all(new in stored for new in merged)


def test_ac4_row_is_kept_exactly_when_its_path_does_not_change():
    rows = read_mapping()
    assert rows
    for old, new, change, _ in rows:
        assert (change == "kept") == (new == old), old


def test_ac5_each_known_instance_has_a_recorded_answer():
    for heading in _ANSWER_HEADINGS_KNOWN:
        assert _has_one_answer(heading), heading


def test_ac6_each_inbox_question_has_a_recorded_answer():
    for heading in _ANSWER_HEADINGS_INBOX:
        assert _has_one_answer(heading), heading


def test_ac7_sign_off_gate_is_raised_over_215_216_217():
    aide = _aide_module()
    lines = _PROGRESS_MD.read_text(encoding="utf-8").splitlines()
    gates = [g for g in aide.human_gates(lines) if _GATE_TEXT in g.text]
    assert len(gates) == 1
    gate = gates[0]
    assert gate.blocks == [215, 216, 217]
    assert gate.stage is None
    assert gate.blocks_all is False


def test_ac8_one_stored_spacing_array_is_merged_into_the_other():
    by_old = {old: (new, change) for old, new, change, _ in read_mapping()}
    new_a, change_a = by_old[_SPACING_A]
    new_b, change_b = by_old[_SPACING_B]
    assert sorted([change_a, change_b]).count("merged") == 1
    assert new_a == new_b
    survivor = change_b if change_a == "merged" else change_a
    assert survivor in ("kept", "moved")


# --------------------------------------------------------------------------- #
# Named adversarial cases
# --------------------------------------------------------------------------- #


def test_section_bounded():
    text = "\n".join(
        [
            "## Answers",
            "",
            "| Old path | New path | Change | Moved by |",
            "|---|---|---|---|",
            "| `a.b` | `c.d` | moved | 215 |",
            "",
            "## Mapping table",
            "",
            "| Old path | New path | Change | Moved by |",
            "|---|---|---|---|",
            "",
        ]
    )
    assert read_mapping(text) == []


def test_duplicate_old_path_fails_ac1():
    rows = read_mapping()
    first_old = rows[0][0]
    rows.append((first_old, first_old + ".other", "moved", 215))
    assert _old_paths_pair(rows) != _FROZEN_OLD_PATHS


def test_heading_without_answer_fails_ac5():
    heading = _ANSWER_HEADINGS_KNOWN[0]
    lines = NOTE_PATH.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    drop = next(
        i for i in range(start + 1, len(lines)) if lines[i].startswith("**Answer:**")
    )
    del lines[drop]
    assert not _has_one_answer(heading, "\n".join(lines))
