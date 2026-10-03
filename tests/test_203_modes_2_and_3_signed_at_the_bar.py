"""Tests for item 203 -- modes 2 and 3 signed at the bar (gate-0133).

Criteria in force are AC4-AC6 (AC1-AC3 of the original scope are superseded).
The gate is selected from ``docs/aide/progress.md`` by its Gate-cell substring
through the CLI's own ``human_gates()``, loaded in process (the
``tests/test_168_maintainer_sign_off.py`` idiom). ``progress.md`` is never
written; the adversarial cases perturb an in-memory copy.
"""

from __future__ import annotations

import datetime
import importlib.util
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_PROGRESS_MD = _REPO_ROOT / "docs" / "aide" / "progress.md"

_GATE_TEXT = "Stage 33 at-the-bar sign-off of modes 2 and 3"
_MODES = (2, 3)
_DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")


def _aide_module():
    spec = importlib.util.spec_from_file_location("_aide_cli_203", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _progress_lines():
    return _PROGRESS_MD.read_text(encoding="utf-8").splitlines()


def _the_gate(aide, lines):
    """The one gate row whose Gate cell contains ``_GATE_TEXT``; asserts
    exactly one matches before anything is asserted about it."""
    matches = [g for g in aide.human_gates(lines) if _GATE_TEXT in g.text]
    assert len(matches) == 1, (
        f"expected exactly one gate row containing {_GATE_TEXT!r}; found {len(matches)}"
    )
    return matches[0]


def _status_cell(aide, lines, gate):
    return aide._split_row(lines[gate.lineno - 1])[2]


def _with_status_cell(aide, lines, gate, status_cell):
    """A copy of *lines* with only *gate*'s Status cell replaced (in memory)."""
    variant = list(lines)
    i = gate.lineno - 1
    cells = aide._split_row(variant[i])
    assert len(cells) == 4, f"gate row is not four cells: {cells!r}"
    cells[2] = status_cell
    variant[i] = "| " + " | ".join(cells) + " |"
    return variant


def _gate_is_approved(aide, lines):
    return _the_gate(aide, lines).kind == "approved"


def _dates_match_gate(aide, lines):
    """AC6's predicate: every mode's record date equals the gate's Status-cell date."""
    import segfacet.failure_modes as fm

    gate = _the_gate(aide, lines)
    match = _DATE_RE.search(_status_cell(aide, lines, gate))
    assert match is not None, "gate Status cell carries no ISO date"
    return [fm.mode_sign_off(m).date == match.group(1) for m in _MODES]


def test_ac4_modes_2_and_3_are_recorded_at_the_bar():
    import segfacet.failure_modes as fm

    for mode_id in _MODES:
        record = fm.mode_sign_off(mode_id)
        assert record is not None, f"mode {mode_id} has no sign-off record"
        assert record.outcome == "at-the-bar"


def test_ac5_the_gate_is_resolved_as_an_approval():
    assert _gate_is_approved(_aide_module(), _progress_lines())


def test_ac6_each_record_carries_the_gates_own_resolution_date():
    results = _dates_match_gate(_aide_module(), _progress_lines())
    assert results == [True, True]


def test_declined_gate_is_not_an_approval():
    aide = _aide_module()
    lines = _progress_lines()
    gate = _the_gate(aide, lines)
    match = _DATE_RE.search(_status_cell(aide, lines, gate))
    assert match is not None
    variant = _with_status_cell(aide, lines, gate, f"❌ Declined ({match.group(1)})")
    assert _the_gate(aide, variant).kind == "declined"
    assert not _gate_is_approved(aide, variant)


def test_date_off_by_one_is_caught():
    aide = _aide_module()
    lines = _progress_lines()
    gate = _the_gate(aide, lines)
    match = _DATE_RE.search(_status_cell(aide, lines, gate))
    assert match is not None
    shifted = datetime.date.fromisoformat(match.group(1)) + datetime.timedelta(days=1)
    assert shifted.isoformat() != match.group(1)
    variant = _with_status_cell(aide, lines, gate, f"✅ Approved ({shifted.isoformat()})")
    assert _dates_match_gate(aide, variant) == [False, False]
