"""Tests for item 150 -- maintainer sign-off of the failure-mode specification.

One focused test per acceptance criterion (AC1-AC15), grouped into the five
blocks the ACs form:

1. the gate           (AC1-AC4)
2. the sign-off record (AC5-AC7)
3. the walkthrough    (AC8-AC10)
4. the artifacts      (AC11-AC12)
5. housekeeping       (AC13-AC15)

**The gate block is expected to be red until the maintainer runs**
``python .aide/scripts/aide.py gate approve <n> --evidence "…"``. That redness
is the checkpoint working, not a defect to route around (item 150 spec, the
Acceptance Criteria preamble). Specifically:

* ``test_ac2_gate_status_cell_is_byte_equal_to_what_aide_gate_writes`` and
* ``test_ac3_gate_is_resolved_approved_and_no_longer_blocks``

both assert a resolved-and-approved gate; while the row reads ``⏳ Awaiting``
there is no ISO date in the Status cell to re-derive from and the gate is
(correctly) still blocking. Every other test in this module -- including every
adversarial variant of AC2/AC3/AC4, which are built in memory and never
written to ``progress.md`` -- is green now and stays green after approval.

No test here resolves the gate. ``aide gate approve`` / ``gate decline`` are
the maintainer's commands and only the maintainer's (``.aide/conventions.md``
§1 -> Human gates).

Reading idioms this module deliberately reuses rather than re-inventing:

* the in-process ``aide.py`` import of
  ``tests/test_114_documentation_corrections.py`` /
  ``tests/test_145_eight_hypothesised_modes.py`` -- never a subprocess shell-out
  to the CLI (``.aide/conventions.md`` §6);
* ``tests/test_145_eight_hypothesised_modes.py``'s ``_classify_warning``
  shape-classifier and its recorded baseline warning classes (AC4);
* ``segfacet.synth.golden.assert_matches_committed_artifact`` for the
  fresh-vs-committed JSON comparison (item 078/127). Both generated artifacts
  are allowlisted for byte comparison under the ``no-float-leaf`` ground in
  ``tests/committed_artifact_guard.py`` and pinned ``text eol=lf`` in
  ``.gitattributes`` (item 150 A8), which is what the ``\\r``-free /
  single-trailing-newline assertions below rest on.
"""

from __future__ import annotations

import dataclasses
import datetime
import importlib.util
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from segfacet.synth.golden import assert_matches_committed_artifact

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_PROGRESS_MD = _REPO_ROOT / "docs" / "aide" / "progress.md"
_INSIGHTS_MD = _REPO_ROOT / "docs" / "aide" / "insights.md"
_INSIGHTS_ARCHIVE_DIR = _REPO_ROOT / "docs" / "aide" / "insights"
_ENGINE_VERSION_FILE = _REPO_ROOT / ".aide" / "VERSION"
_SPEC_REL_PATH = "docs/aide/items/150-maintainer-sign-off-of-the-specification.md"
_SPEC_MD = _REPO_ROOT / "docs" / "aide" / "items" / (
    "150-maintainer-sign-off-of-the-specification.md"
)
_FAILURE_MODES_PY = _REPO_ROOT / "src" / "segfacet" / "failure_modes.py"
_COMMITTED_JSON = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
_COMMITTED_MD = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"

#: The literal the gate row's Gate cell must contain. Resolved by *text*, never
#: by the positional gate number, which shifts the moment a row is inserted
#: above it (item 150 A4).
_GATE_TEXT = "Stage 30 failure-mode specification sign-off"

#: The heading the walkthrough is transcribed under (item 150 step 10).
_TRANSCRIPT_HEADING = "### Stage-30 maintainer sign-off"

#: The earliest date on which the reviewed rendering existed -- the day item 149
#: landed (AC6).
_EARLIEST_SIGN_OFF_DATE = datetime.date(2026, 9, 4)


# =========================================================================== #
# Shared helpers
# =========================================================================== #


def _aide_module():
    """Import ``.aide/scripts/aide.py`` in-process.

    §6: a test asserting on ``aide check``'s output calls ``run_checks``
    directly rather than replaying the CLI's stdout across a subprocess
    boundary that adds an encoding and a re-parse.
    """
    spec = importlib.util.spec_from_file_location("_aide_cli_150", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _progress_lines():
    return _PROGRESS_MD.read_text(encoding="utf-8").splitlines()


def _sign_off_gate(aide, lines):
    """``(1-based index, HumanGate)`` for the one Stage-30 sign-off row.

    Fails loudly on "not found" and on "found more than one" rather than
    returning ``None`` for an assertion to pass over (§6: assert a derived
    value is recognisable *before* asserting anything about it).
    """
    matches = [
        (n, gate)
        for n, gate in enumerate(aide.human_gates(lines), start=1)
        if _GATE_TEXT in gate.text
    ]
    assert len(matches) == 1, (
        f"expected exactly one '## Human gates' row whose Gate cell contains "
        f"{_GATE_TEXT!r}; found {len(matches)}: "
        f"{[n for n, _ in matches]}"
    )
    return matches[0]


def _with_status_cell(aide, lines, gate, status_cell):
    """A copy of *lines* with only *gate*'s Status cell replaced.

    In memory only -- ``progress.md`` is never written by this module (AC3).
    """
    variant = list(lines)
    i = gate.lineno - 1
    cells = aide._split_row(variant[i])
    assert len(cells) == 4, f"gate row is not four cells: {cells!r}"
    cells[2] = status_cell
    variant[i] = "| " + " | ".join(cells) + " |"
    return variant


def _failure_modes():
    import segfacet.failure_modes as fm

    return fm


def _live_field_names(fm):
    """The union of the three authored dataclasses' field names, recomputed
    live rather than listed by hand (AC9/AC10)."""
    names = set()
    for cls in (fm.ModeSpec, fm.IntendedRule, fm.CorpusCaseExpectation):
        names.update(f.name for f in dataclasses.fields(cls))
    assert names, "the live field union came back empty -- plumbing failure"
    return names


# =========================================================================== #
# Block 1 -- the gate (AC1-AC4)
# =========================================================================== #


def test_ac1_gate_exists_is_unique_and_reaches_the_four_held_items():
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    assert gate.blocks == [139, 140, 141, 142], (
        "the gate's Blocks cell must reach exactly items 139, 140, 141, 142 "
        f"(measured equality, not containment); parsed {gate.blocks!r}"
    )
    assert gate.stage is None, (
        f"the gate blocks named items, not a stage; parsed stage={gate.stage!r}"
    )
    assert gate.blocks_all is False, (
        "the gate is not a programme-level stop; parsed blocks_all=True"
    )
    assert gate.kind in ("awaiting", "approved", "declined"), (
        "the Status cell must read one of ⏳ Awaiting / ✅ Approved / ❌ Declined "
        f"-- kind={gate.kind!r} is how the engine reports an unrecognised cell"
    )


#: Status cells that must NOT be accepted as "what ``aide gate`` writes" (AC2's
#: adversarial list): no date, wrong case, a non-ISO date shape.
_HAND_EDITED_STATUS_CELLS = (
    "✅ Approved",
    "✅ approved (2026-09-05)",
    "✅ Approved (05/09/2026)",
    "✅ Approved (2026-9-5)",
    "approved (2026-09-05)",
)

_PLACEHOLDER_DECISIONS = ("", "TBD", "n/a", "pending")

_ISO_DATE_IN_STATUS_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")


def _status_cell(aide, lines, gate):
    return aide._split_row(lines[gate.lineno - 1])[2]


def _decision_cell(aide, lines, gate):
    return aide._split_row(lines[gate.lineno - 1])[3]


def test_ac2_gate_status_cell_is_byte_equal_to_what_aide_gate_writes():
    """A hand-edited Status cell fails: the expected cell is re-derived by
    calling ``set_gate_status`` (so it tracks the engine's rendering) rather
    than pinned as a literal (item 150 A1).

    **Red until the maintainer approves the gate** -- an ``⏳ Awaiting`` cell
    carries no ISO date to re-derive from, and ``set_gate_status`` only writes
    ``approved`` / ``declined``.
    """
    aide = _aide_module()
    text = _PROGRESS_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    index, gate = _sign_off_gate(aide, lines)

    live_status = _status_cell(aide, lines, gate)
    match = _ISO_DATE_IN_STATUS_RE.search(live_status)
    assert match is not None, (
        "the gate's Status cell carries no ISO date in parentheses -- it reads "
        f"{live_status!r}. This is the expected state until the maintainer runs "
        "`aide gate approve <n> --evidence \"…\"`; no agent may resolve it."
    )
    d = match.group(1)
    assert gate.kind in ("approved", "declined"), (
        f"a dated Status cell must parse as approved or declined; kind={gate.kind!r}"
    )

    rewritten = aide.set_gate_status(text, index, gate.kind, today=d)
    rewritten_status = _status_cell(aide, rewritten.splitlines(), gate)
    assert rewritten_status == live_status, (
        "the live Status cell is not character-for-character what `aide gate` "
        f"writes: live={live_status!r} vs set_gate_status={rewritten_status!r}"
    )

    decision = _decision_cell(aide, lines, gate).strip()
    assert decision, "the gate's Decision cell is empty"
    assert "|" not in decision and "\n" not in decision and "\r" not in decision
    assert decision not in _PLACEHOLDER_DECISIONS, (
        f"the Decision cell is a placeholder: {decision!r}"
    )

    parsed = datetime.date.fromisoformat(d)
    assert parsed <= datetime.date.today(), (
        f"the gate's recorded date {d} is in the future"
    )


@pytest.mark.parametrize("bad_cell", _HAND_EDITED_STATUS_CELLS)
def test_adv_ac2_hand_edited_status_cells_are_not_what_aide_gate_writes(bad_cell):
    """AC2's adversarial half, and it is green regardless of the gate's state:
    each hand-edited shape must differ from what ``set_gate_status`` writes for
    the same date. Built in memory; ``progress.md`` is never written."""
    aide = _aide_module()
    text = _PROGRESS_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    index, gate = _sign_off_gate(aide, lines)

    # The date the engine would stamp for the hand edit's apparent date (or
    # today, when the hand edit carries none at all).
    match = _ISO_DATE_IN_STATUS_RE.search(bad_cell)
    day = match.group(1) if match else datetime.date.today().isoformat()
    engine_cell = _status_cell(
        aide,
        aide.set_gate_status(text, index, "approved", today=day).splitlines(),
        gate,
    )
    assert bad_cell != engine_cell, (
        f"{bad_cell!r} must not be accepted as the engine's own rendering "
        f"({engine_cell!r}) -- AC2 exists to catch exactly this hand edit"
    )


def test_ac3_gate_is_resolved_approved_and_no_longer_blocks():
    """**Red until the maintainer approves the gate** -- by design."""
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    assert gate.kind == "approved", (
        f"the Stage-30 sign-off gate reads kind={gate.kind!r}; it is not "
        "approved yet. Only the maintainer may resolve it "
        "(`aide gate approve <n> --evidence \"…\"`)."
    )
    blocking = [g for g in aide.blocking_gates(lines) if _GATE_TEXT in g.text]
    assert blocking == [], (
        "an approved gate must be absent from blocking_gates(); it is still listed"
    )


@pytest.mark.parametrize("status_cell", ["⏳ Awaiting", "❌ Declined (2026-09-14)"])
def test_adv_ac3_awaiting_and_declined_variants_still_block(status_cell):
    """The case a reader most often assumes is "resolved, therefore released":
    a **declined** gate still blocks (``blocking_gates``' own docstring). Both
    variants are built in memory; ``progress.md`` is not written."""
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    variant = _with_status_cell(aide, lines, gate, status_cell)
    blocking = [g for g in aide.blocking_gates(variant) if _GATE_TEXT in g.text]
    assert len(blocking) == 1, (
        f"with Status={status_cell!r} the Stage-30 gate must be back in "
        f"blocking_gates(); found {len(blocking)}"
    )


# --- AC4 -------------------------------------------------------------------- #

_BRANCH_STATE_WARNING_PREFIXES = ("stale claim branch", "unrecognised branch")

#: The recorded baseline warning classes -- identical to
#: ``tests/test_145_eight_hypothesised_modes.py``'s, and deliberately shared by
#: shape rather than by count (§6: never pin a count from a module that itself
#: trips the lint being counted).
_BASELINE_WARNING_CLASSES = (
    "assumptions-block",
    "awaiting-a-decision",
    "branch-state",
    "retracted-criterion",
)


def _classify_warning(message: str) -> str:
    """The ``test_145_eight_hypothesised_modes.py::_classify_warning`` shape
    idiom, reproduced verbatim: a genuinely new instance of a tolerated class
    still classifies as that class, while an unseen shape reports
    ``"unclassified"`` and fails the check."""
    if message.startswith(_BRANCH_STATE_WARNING_PREFIXES):
        return "branch-state"
    if re.search(r"criterion \d+ was retracted on \d{4}-\d{2}-\d{2}", message):
        return "retracted-criterion"
    if "assumptions" in message.lower():
        return "assumptions-block"
    if "awaiting a decision" in message.lower():
        return "awaiting-a-decision"
    return "unclassified"


def _human_gates_section(text: str) -> str:
    """The ``## Human gates`` section of progress.md, heading to next heading.
    Fails loudly if the heading is absent."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == "## Human gates"), None
    )
    assert start is not None, "progress.md has no '## Human gates' heading"
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if re.match(r"^#{1,6} ", lines[i])
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_ac4_aide_check_reports_no_error_and_no_unfilled_slot():
    aide = _aide_module()
    errors, warnings = aide.run_checks(_REPO_ROOT, aide.load_config(_REPO_ROOT))
    assert errors == [], errors
    # A plumbing failure must fail loudly rather than pass an empty loop
    # vacuously: this repo always reports the baseline warnings.
    assert warnings, "run_checks returned no warnings at all -- expected the baseline"

    assert not [w for w in warnings if "unfilled template slot" in w], (
        "aide check reports an unfilled template slot"
    )
    section = _human_gates_section(_PROGRESS_MD.read_text(encoding="utf-8"))
    assert "{{" not in section, (
        "the '## Human gates' section carries a doubled-brace template slot, "
        "which aide check's template_residue_errors reports as an error (D5)"
    )

    classes = {_classify_warning(w) for w in warnings}
    assert classes <= set(_BASELINE_WARNING_CLASSES), (
        "aide check reports a warning class outside the recorded baseline: "
        f"{sorted(classes - set(_BASELINE_WARNING_CLASSES))}"
    )


def test_ac4_gate_warnings_feed_run_checks():
    """The seam the adversarial test below rests on: every warning
    ``gate_warnings`` produces for the live progress.md is one ``run_checks``
    reports. Without this the in-memory variant test would assert about a
    function nothing calls."""
    aide = _aide_module()
    _errors, warnings = aide.run_checks(_REPO_ROOT, aide.load_config(_REPO_ROOT))
    gate_only = aide.gate_warnings(_progress_lines())
    assert set(gate_only) <= set(warnings), (
        "gate_warnings produced a warning run_checks does not report: "
        f"{sorted(set(gate_only) - set(warnings))}"
    )


def test_adv_ac4_awaiting_variant_produces_exactly_one_classified_gate_warning():
    """With this row's Status cell set to ``⏳ Awaiting`` in a temporary
    (in-memory) copy, the engine **reports** the gate rather than staying
    silent about it: exactly one warning names it, and it classifies as
    ``awaiting-a-decision``."""
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    variant = _with_status_cell(aide, lines, gate, "⏳ Awaiting")
    naming = [w for w in aide.gate_warnings(variant) if _GATE_TEXT in w]
    assert len(naming) == 1, (
        f"expected exactly one warning naming the Stage-30 gate; got {naming!r}"
    )
    assert _classify_warning(naming[0]) == "awaiting-a-decision", naming[0]


def test_adv_ac4_classifier_can_still_detect_an_unseen_shape():
    """Otherwise the baseline check above passes on anything."""
    assert _classify_warning("a brand new kind of warning nobody has seen") == (
        "unclassified"
    )
    assert _classify_warning(
        "progress.md:9: human gate 5 (x) is awaiting a decision — blocks 139"
    ) == "awaiting-a-decision"


# =========================================================================== #
# Block 2 -- the sign-off record (AC5-AC7)
# =========================================================================== #

#: An underlined (RST-style) section heading in the module docstring.
_DOC_SECTION_RE = re.compile(r"^(?P<title>\S.*)\n-{3,}[ \t]*$", re.M)

_SIGNED_OFF_RE = re.compile(r"^Signed off: (\d{4}-\d{2}-\d{2}) -- (.+)$", re.M)

_ITEM_144_PLACEHOLDER = "No maintainer sign-off is recorded yet."


def _docstring_section(doc: str, title: str) -> str:
    """The body of the underlined section *title*, up to the next underlined
    section or the end. Fails loudly when the section is absent -- an empty
    match must never pass silently (item 150 Testing Strategy)."""
    starts = [(m.group("title").strip(), m.end()) for m in _DOC_SECTION_RE.finditer(doc)]
    assert starts, "the module docstring carries no underlined sections at all"
    bounds = [m.start() for m in _DOC_SECTION_RE.finditer(doc)]
    for i, (found, body_start) in enumerate(starts):
        if found == title:
            body_end = bounds[i + 1] if i + 1 < len(bounds) else len(doc)
            body = doc[body_start:body_end]
            assert body.strip(), f"the {title!r} section body is empty"
            return body
    raise AssertionError(
        f"the module docstring has no {title!r} section; found "
        f"{[t for t, _ in starts]}"
    )


def _sign_off_match():
    fm = _failure_modes()
    doc = fm.__doc__
    assert doc, (
        "segfacet.failure_modes.__doc__ is empty -- the suite must not run "
        "under `python -OO`, which strips docstrings (item 150 A5)"
    )
    body = _docstring_section(doc, "Sign-off")
    matches = _SIGNED_OFF_RE.findall(body)
    assert len(matches) == 1, (
        "the 'Sign-off' section must carry exactly one anchored "
        f"'Signed off: YYYY-MM-DD -- …' line; found {len(matches)}"
    )
    return matches[0]


def test_ac5_module_records_a_sign_off_and_the_placeholder_is_gone():
    date_text, outcome = _sign_off_match()
    assert date_text and outcome.strip()

    source = _FAILURE_MODES_PY.read_text(encoding="utf-8")
    assert _ITEM_144_PLACEHOLDER not in source, (
        f"the item-144 placeholder sentence {_ITEM_144_PLACEHOLDER!r} still "
        "appears in src/segfacet/failure_modes.py"
    )

    # The edit is additive: item 146's record survives intact.
    doc = _failure_modes().__doc__
    assert "item 146" in doc, "the docstring lost item 146's record"
    paths = re.findall(r"src/segfacet/[\w/]+\.py", doc)
    assert paths, "the docstring names no src/segfacet/*.py path at all"
    resolvable = [p for p in paths if (_REPO_ROOT / p).is_file()]
    assert resolvable, (
        f"none of the docstring's src/segfacet paths resolve to a real file: {paths}"
    )


def _ac6_date_ok(day: datetime.date) -> bool:
    """AC6's predicate, applied both to the live value and to the adversarial
    ones -- so the test exercises the parser, not only today's answer."""
    return _EARLIEST_SIGN_OFF_DATE <= day <= datetime.date.today()


def test_ac6_recorded_date_is_real_and_within_bounds():
    date_text, _outcome = _sign_off_match()
    day = datetime.date.fromisoformat(date_text)
    assert day >= _EARLIEST_SIGN_OFF_DATE, (
        f"recorded sign-off date {day} is before {_EARLIEST_SIGN_OFF_DATE} -- "
        "the day item 149 landed, i.e. the earliest date on which the reviewed "
        "rendering existed"
    )
    assert day <= datetime.date.today(), (
        f"recorded sign-off date {day} is in the future (today is "
        f"{datetime.date.today()})"
    )
    assert _ac6_date_ok(day)


def test_adv_ac6_future_and_pre_history_dates_are_rejected():
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    assert not _ac6_date_ok(tomorrow), "a date one day in the future must fail"
    assert not _ac6_date_ok(datetime.date(2026, 9, 3)), (
        "2026-09-03 predates item 149 landing and must fail"
    )
    assert _ac6_date_ok(_EARLIEST_SIGN_OFF_DATE), "the lower bound is inclusive"


_DISPOSITION_LITERALS = ("accepted as rendered", "accepted with changes")

_PLACEHOLDER_OUTCOMES = (
    "TBD",
    "n/a",
    "see review",
    "pending",
    "signed off",
    "accepted as rendered",
    "accepted with changes",
    "",
)


def _ac7_outcome_ok(outcome: str) -> bool:
    """AC7's predicate, run over the live value *and* every placeholder."""
    text = outcome.strip()
    if not text or len(text) < 40:
        return False
    if text in _PLACEHOLDER_OUTCOMES:
        return False
    if sum(text.count(literal) > 0 for literal in _DISPOSITION_LITERALS) != 1:
        return False
    if _SPEC_REL_PATH not in text:
        return False
    return True


def test_ac7_recorded_outcome_is_substantive_and_points_at_the_transcript():
    _date_text, outcome = _sign_off_match()
    text = outcome.strip()
    assert text, "the outcome half of the sign-off line is empty"
    assert len(text) >= 40, f"the outcome is only {len(text)} characters: {text!r}"
    present = [lit for lit in _DISPOSITION_LITERALS if lit in text]
    assert len(present) == 1, (
        "the outcome must contain exactly one of the two disposition literals "
        f"{_DISPOSITION_LITERALS}; found {present}"
    )
    assert text not in _PLACEHOLDER_OUTCOMES, f"placeholder outcome: {text!r}"
    assert _SPEC_REL_PATH in text, (
        "the outcome must carry the transcript pointer "
        f"{_SPEC_REL_PATH!r} (the STATUS_OVERRIDES precedent)"
    )
    assert _SPEC_MD.is_file(), f"{_SPEC_REL_PATH} does not resolve to a real file"
    assert _ac7_outcome_ok(text)


@pytest.mark.parametrize("placeholder", _PLACEHOLDER_OUTCOMES)
def test_adv_ac7_placeholder_outcomes_are_rejected(placeholder):
    assert not _ac7_outcome_ok(placeholder), (
        f"{placeholder!r} must not pass AC7 -- a bare disposition literal with "
        "nothing else is not a recorded outcome"
    )


def test_adv_ac7_outcome_naming_both_dispositions_is_rejected():
    both = (
        "accepted as rendered and also accepted with changes, see "
        + _SPEC_REL_PATH
    )
    assert not _ac7_outcome_ok(both), (
        "an outcome naming both disposition literals is ambiguous and must fail"
    )


def test_adv_ac7_outcome_without_the_transcript_pointer_is_rejected():
    no_pointer = (
        "accepted with changes -- the maintainer re-organised the catalogue "
        "across all ten entries during the entry-by-entry read"
    )
    assert len(no_pointer) >= 40
    assert not _ac7_outcome_ok(no_pointer), (
        "an outcome that does not name the transcript's spec path must fail"
    )


# =========================================================================== #
# Block 3 -- the walkthrough (AC8-AC10)
# =========================================================================== #

_MODE_LINE_RE = re.compile(r"^- Mode (\d+) — (.*)$", re.M)

#: The disposition is read **positionally** -- the token immediately after
#: ``- Mode N — `` -- rather than by counting occurrences of the two literals
#: anywhere in the line. Prose legitimately reuses the other word (mode 9 and
#: mode 10 both read ``changed: …`` and then say "content confirmed as
#: rendered"), so an occurrence count would report two dispositions for a line
#: that carries exactly one. The slot holds exactly one token, and a line whose
#: slot holds neither literal fails -- which is what AC9 is for.
_DISPOSITION_SLOT_RE = re.compile(r"^(confirmed|changed)\b")


def _transcript_section(text: str) -> str:
    """The ``### Stage-30 maintainer sign-off`` section, up to the next ``###``
    or ``##`` heading. Fails loudly when the heading is absent."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == _TRANSCRIPT_HEADING),
        None,
    )
    assert start is not None, (
        f"{_SPEC_REL_PATH} carries no {_TRANSCRIPT_HEADING!r} heading"
    )
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if lines[i].startswith("### ") or lines[i].startswith("## ")
        ),
        len(lines),
    )
    section = "\n".join(lines[start + 1 : end])
    assert section.strip(), "the transcript section is empty"
    return section


def _transcript_mode_lines(section: str):
    """``{mode id: rest-of-line}`` for every ``- Mode N — `` line."""
    return {int(m.group(1)): m.group(2) for m in _MODE_LINE_RE.finditer(section)}


def _transcript_preamble(section: str) -> str:
    """Everything above the first ``- Mode `` line. Fails loudly if there is no
    ``- Mode `` line to be above."""
    first = _MODE_LINE_RE.search(section)
    assert first is not None, "the transcript carries no '- Mode N — ' line at all"
    preamble = section[: first.start()]
    assert preamble.strip(), "the transcript has no preamble above its entry lines"
    return preamble


def _spec_text():
    return _SPEC_MD.read_text(encoding="utf-8")


def test_ac8_walkthrough_covers_every_specification_entry():
    fm = _failure_modes()
    section = _transcript_section(_spec_text())
    ids = set(_transcript_mode_lines(section))
    expected = set(fm.SPECIFICATION)
    # Read from SPECIFICATION, never hardcoded as 10.
    assert expected, "SPECIFICATION came back empty -- plumbing failure"
    assert ids == expected, (
        f"the walkthrough's entry ids do not match SPECIFICATION exactly: "
        f"missing {sorted(expected - ids)}, extra {sorted(ids - expected)}"
    )


def test_adv_ac8_set_equality_fails_in_both_directions():
    """A transcript missing the last entry, and one carrying a line for an id
    the specification does not have, must both fail -- otherwise AC8's equality
    is asserting containment in one direction only."""
    fm = _failure_modes()
    expected = set(fm.SPECIFICATION)
    highest = max(expected)

    section = _transcript_section(_spec_text())
    lines = section.splitlines()

    missing = "\n".join(
        line for line in lines if not line.startswith(f"- Mode {highest} — ")
    )
    assert set(_transcript_mode_lines(missing)) != expected, (
        f"dropping mode {highest} must break the set equality"
    )

    extra = section + f"\n- Mode {highest + 1} — confirmed: a mode that does not exist.\n"
    assert set(_transcript_mode_lines(extra)) != expected, (
        f"an invented '- Mode {highest + 1} — ' line must break the set equality"
    )


def test_ac9_every_entry_carries_a_disposition_and_changed_lines_name_a_field():
    fm = _failure_modes()
    field_names = _live_field_names(fm)
    section = _transcript_section(_spec_text())
    mode_lines = _transcript_mode_lines(section)
    assert mode_lines, "no '- Mode N — ' lines parsed"

    for mode_id, rest in sorted(mode_lines.items()):
        slot = _DISPOSITION_SLOT_RE.match(rest)
        assert slot is not None, (
            f"mode {mode_id}'s line carries no disposition: it must open with "
            f"'confirmed' or 'changed'; got {rest[:60]!r}"
        )
        if slot.group(1) != "changed":
            continue
        named = sorted(
            name
            for name in field_names
            if re.search(rf"\b{re.escape(name)}\b", rest)
        )
        assert named, (
            f"mode {mode_id}'s line reads 'changed' but names no authored field "
            f"from the live ModeSpec / IntendedRule / CorpusCaseExpectation "
            f"union: {rest[:120]!r}"
        )


def test_adv_ac9_a_line_with_no_disposition_and_a_changed_line_naming_no_field_fail():
    fm = _failure_modes()
    field_names = _live_field_names(fm)

    assert _DISPOSITION_SLOT_RE.match("reviewed: nothing to say.") is None, (
        "a line whose disposition slot holds neither literal must not parse"
    )
    assert _DISPOSITION_SLOT_RE.match("changedly: not the literal") is None, (
        "the disposition must be a whole word, not a prefix"
    )

    bogus = "changed: the wording was tidied up a little."
    named = [
        name for name in field_names if re.search(rf"\b{re.escape(name)}\b", bogus)
    ]
    assert not named, (
        "a 'changed' line naming no dataclass field must be rejected; the "
        f"matcher found {named}"
    )

    # ...and the same matcher must accept a line that does name one, so the
    # check above is not passing because the matcher matches nothing ever.
    real = "changed: definition, discriminator, corpus_cases."
    assert [
        name for name in field_names if re.search(rf"\b{re.escape(name)}\b", real)
    ]


#: The eight review facets the queue line names, each mapped in the transcript
#: preamble onto the dataclass field it resolves to.
_FACETS = (
    "definition",
    "discriminator",
    "expected firing",
    "severity",
    "observability",
    "evidence rung",
    "status",
    "provenance",
)

_FACET_MAPPING_RE_TEMPLATE = r"{facet}\s*(?:→|->)\s*`(\w+)`"


def _facet_field_map(preamble: str):
    """``{facet: field name}`` read out of the preamble's mapping.

    Whitespace is collapsed first: the mapping is prose and wraps, so
    ``evidence rung →\\n`evidence_rung``` must read the same as the unwrapped
    form.
    """
    flat = re.sub(r"\s+", " ", preamble)
    out = {}
    for facet in _FACETS:
        m = re.search(
            _FACET_MAPPING_RE_TEMPLATE.format(facet=re.escape(facet)), flat
        )
        if m is not None:
            out[facet] = m.group(1)
    return out


def test_ac10_eight_facets_are_declared_and_each_resolves_onto_a_real_field():
    fm = _failure_modes()
    field_names = _live_field_names(fm)
    preamble = _transcript_preamble(_transcript_section(_spec_text()))
    flat = re.sub(r"\s+", " ", preamble)

    for facet in _FACETS:
        assert facet in flat, (
            f"the transcript preamble does not name the review facet {facet!r}"
        )

    mapping = _facet_field_map(preamble)
    missing = [facet for facet in _FACETS if facet not in mapping]
    assert not missing, (
        f"the preamble binds no dataclass field for these facets: {missing}"
    )
    for facet, field in sorted(mapping.items()):
        assert field in field_names, (
            f"facet {facet!r} is bound to {field!r}, which is not a field of "
            "ModeSpec / IntendedRule / CorpusCaseExpectation"
        )


def test_adv_ac10_a_facet_bound_to_a_nonexistent_field_is_caught():
    fm = _failure_modes()
    field_names = _live_field_names(fm)
    fake_preamble = "severity → `severity_level`; provenance → `provenance`."
    mapping = _facet_field_map(fake_preamble)
    assert mapping.get("severity") == "severity_level"
    assert "severity_level" not in field_names, (
        "adversarial precondition: `severity_level` must not be a real field"
    )


# =========================================================================== #
# Block 4 -- the artifacts (AC11-AC12)
# =========================================================================== #


def test_ac11_artifacts_are_byte_identical_to_a_fresh_regeneration(tmp_path):
    fm = _failure_modes()

    fresh_json = tmp_path / "a.json"
    fresh_md = tmp_path / "a.md"
    assert fm.main(["--json", str(fresh_json), "--md", str(fresh_md)]) == 0
    assert fresh_json.is_file() and fresh_md.is_file()

    assert_matches_committed_artifact(fresh_json, _COMMITTED_JSON)
    assert fresh_md.read_text(encoding="utf-8") == _COMMITTED_MD.read_text(
        encoding="utf-8"
    ), "docs/aide/failure_modes.generated.md is stale -- regenerate it"

    for path in (_COMMITTED_JSON, _COMMITTED_MD):
        raw = path.read_bytes()
        assert raw, f"{path.name} is empty"
        assert b"\r" not in raw, f"{path.name} carries a CR -- the eol=lf pin is lost"
        assert raw.endswith(b"\n"), f"{path.name} does not end with a newline"
        assert not raw.endswith(b"\n\n"), f"{path.name} ends with more than one newline"


def test_ac11_two_successive_regenerations_agree_byte_for_byte(tmp_path):
    """The run-to-run determinism half: two regenerations into *different*
    paths in one session must agree, independently of the committed copies."""
    fm = _failure_modes()
    first_json, first_md = tmp_path / "one.json", tmp_path / "one.md"
    second_json, second_md = tmp_path / "two.json", tmp_path / "two.md"
    assert fm.main(["--json", str(first_json), "--md", str(first_md)]) == 0
    assert fm.main(["--json", str(second_json), "--md", str(second_md)]) == 0

    assert first_json.read_bytes() == second_json.read_bytes()
    assert first_md.read_bytes() == second_md.read_bytes()
    assert first_json.read_bytes(), "the regeneration wrote an empty JSON"


def test_ac11_specification_to_dict_is_equal_but_not_identical_across_calls():
    """The module's own determinism/immutability contract: a fresh tree every
    call, so mutating the result never leaks into a later one."""
    fm = _failure_modes()
    first = fm.specification_to_dict()
    second = fm.specification_to_dict()
    assert first == second
    assert first is not second
    assert first["modes"] is not second["modes"]


#: Every authored string field the renderers emit for a mode, recomputed from
#: ``SPECIFICATION`` rather than read from a fixture (AC12). The spec's own AC12
#: list predates item 150's schema; this is the live emitted set, taken from
#: ``render_markdown`` / ``specification_to_dict``.
_AUTHORED_STRING_FIELDS = (
    "name",
    "short_name",
    "definition",
    "discriminator",
    "observability",
    "severity",
    "provenance",
    "mechanism",
)

#: The three fields ``render_markdown`` passes through ``_md_escape`` before
#: emitting; the rest are emitted raw.
_MD_ESCAPED_FIELDS = frozenset({"definition", "discriminator", "mechanism"})

_MD_MODE_HEADING_RE = re.compile(r"^## Mode (\d+)\b", re.M)


def _md_mode_sections(md_text: str):
    """``{mode id: section text}`` including each ``## Mode N`` heading line."""
    starts = [(int(m.group(1)), m.start()) for m in _MD_MODE_HEADING_RE.finditer(md_text)]
    assert starts, "the committed Markdown carries no '## Mode N' heading"
    out = {}
    for i, (mode_id, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(md_text)
        out[mode_id] = md_text[start:end]
    return out


def _ac12_compare(fm, md_sections, json_modes):
    """Run AC12's comparison, returning ``(comparisons, failures)``.

    Shared by the live test and its adversarial counterpart so the "the loop
    cannot pass vacuously" claim is checked against the *same* code.
    """
    comparisons = 0
    failures = []
    for mode_id, mode in sorted(fm.SPECIFICATION.items()):
        section = md_sections.get(mode_id)
        entry = json_modes.get(mode_id)
        if section is None:
            failures.append(f"mode {mode_id}: no '## Mode {mode_id}' section in the .md")
            continue
        if entry is None:
            failures.append(f"mode {mode_id}: no entry in the .json")
            continue
        per_mode = 0
        for field in _AUTHORED_STRING_FIELDS:
            value = getattr(mode, field)
            if not value:
                continue  # empty-string fields are skipped explicitly
            rendered = fm._md_escape(value) if field in _MD_ESCAPED_FIELDS else value
            if rendered not in section:
                failures.append(
                    f"mode {mode_id}: authored {field!r} is not in its "
                    f"'## Mode {mode_id}' section of the committed .md"
                )
            if entry.get(field) != value:
                failures.append(
                    f"mode {mode_id}: committed .json {field!r} is "
                    f"{entry.get(field)!r}, specification says {value!r}"
                )
            comparisons += 1
            per_mode += 1
        # `parent` is not a string field, so it is compared against the JSON's
        # own key rather than searched for in the prose.
        if entry.get("parent") != mode.parent:
            failures.append(
                f"mode {mode_id}: committed .json parent is {entry.get('parent')!r}, "
                f"specification says {mode.parent!r}"
            )
        if per_mode == 0:
            failures.append(f"mode {mode_id}: zero fields were compared")
    return comparisons, failures


def _committed_json_modes():
    import json

    payload = json.loads(_COMMITTED_JSON.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in payload["modes"]}


def test_ac12_every_authored_field_is_present_in_both_artifacts():
    fm = _failure_modes()
    md_sections = _md_mode_sections(_COMMITTED_MD.read_text(encoding="utf-8"))
    comparisons, failures = _ac12_compare(fm, md_sections, _committed_json_modes())
    assert not failures, "\n".join(failures)
    assert comparisons > 0, (
        "the comparison loop ran zero comparisons -- it cannot pass vacuously"
    )
    # Every mode must have contributed at least one comparison.
    assert comparisons >= len(fm.SPECIFICATION), (
        f"only {comparisons} comparisons across {len(fm.SPECIFICATION)} modes"
    )


def test_adv_ac12_a_stale_artifact_and_a_vacuous_loop_are_both_caught():
    fm = _failure_modes()
    md_sections = _md_mode_sections(_COMMITTED_MD.read_text(encoding="utf-8"))
    json_modes = _committed_json_modes()

    # (a) a stale committed .json for one mode must be reported.
    mode_id = sorted(fm.SPECIFICATION)[0]
    stale = dict(json_modes)
    stale[mode_id] = dict(stale[mode_id], definition="a stale definition")
    _comparisons, failures = _ac12_compare(fm, md_sections, stale)
    assert any("definition" in f for f in failures), failures

    # (b) a mode whose every authored string field is empty must report zero
    #     comparisons rather than passing silently. `ModeSpec.__post_init__`
    #     refuses to build such a mode -- which is the schema doing its job --
    #     so the degenerate entry is a plain stand-in carrying the same
    #     attribute names.
    blank = SimpleNamespace(parent=None, **{f: "" for f in _AUTHORED_STRING_FIELDS})
    probe = SimpleNamespace(
        SPECIFICATION={mode_id: blank}, _md_escape=fm._md_escape
    )
    section = {mode_id: f"## Mode {mode_id}\n"}
    entry = {mode_id: {"parent": None}}
    comparisons, failures = _ac12_compare(probe, section, entry)
    assert comparisons == 0
    assert any("zero fields were compared" in f for f in failures), failures

    # ...and one non-empty field is enough to lift it out of the vacuous case,
    # so the counter is measuring something real.
    one_field = SimpleNamespace(
        parent=None,
        **{f: ("" if f != "name" else f"Mode {mode_id}") for f in _AUTHORED_STRING_FIELDS},
    )
    probe.SPECIFICATION = {mode_id: one_field}
    comparisons, failures = _ac12_compare(
        probe,
        {mode_id: f"## Mode {mode_id}\n"},
        {mode_id: {"parent": None, "name": f"Mode {mode_id}"}},
    )
    assert comparisons == 1, comparisons
    assert not failures, failures


# =========================================================================== #
# Block 5 -- housekeeping (AC13-AC15)
# =========================================================================== #

#: The four Stage-20 deliverables this gate holds. **A dated claim** (D3): the
#: first item that lands any of 139-142 must list this test file under its
#: "Authorised paths -> May change" and update this test. Recorded here so that
#: item's author does not discover it as a red suite.
_HELD_ITEMS = (139, 140, 141, 142)


def _stage_20_section(text: str) -> list:
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("## Stage 20 —")), None
    )
    assert start is not None, "progress.md has no '## Stage 20 —' heading"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## Stage ")),
        len(lines),
    )
    return lines[start:end]


@pytest.mark.parametrize("item", _HELD_ITEMS)
def test_ac13_the_four_held_stage_20_items_are_still_deferred(item):
    """Located by the deliverable's own ``*(Item NNN)*`` marker and walked back
    to the bullet that owns it -- not by scanning the file for the icon."""
    section = _stage_20_section(_PROGRESS_MD.read_text(encoding="utf-8"))
    marker = f"*(Item {item})*"
    hits = [i for i, line in enumerate(section) if marker in line]
    assert len(hits) == 1, (
        f"expected exactly one Stage 20 deliverable carrying {marker}; found "
        f"{len(hits)}"
    )
    bullet_start = next(
        (i for i in range(hits[0], -1, -1) if section[i].startswith("- ")), None
    )
    assert bullet_start is not None, (
        f"could not find the bullet owning {marker} in Stage 20"
    )
    bullet = section[bullet_start]
    assert bullet.startswith("- ⏸️"), (
        f"the Stage 20 deliverable for item {item} must still carry ⏸️ as its "
        f"leading bullet icon; it reads: {bullet[:80]!r}"
    )


# --- AC14 ------------------------------------------------------------------- #

_INSIGHT_LINE_RE = re.compile(r"^- \[[ xX]\] ")

#: The §1 grammar, anchored, for a line whose provenance names item 150.
_ITEM_150_GRAMMAR_RE = re.compile(
    r"^- \[[ xX]\] (?:knowledge|defect|gap|automation|framework) — .+ "
    r"\*\(item 150, (\d{4}-\d{2}-\d{2}), engine (\d+\.\d+\.\d+)\)\*$"
)

#: Any line claiming item-150 provenance, well-formed or not -- so a malformed
#: one is caught rather than skipped by the strict grammar above.
_ITEM_150_CLAIM_RE = re.compile(r"\(item 150[,)]")

#: Non-``item 150`` insight lines across the inbox and every archive, measured
#: 2026-09-14 on ``aide/queue-020`` at this item's base. Asserted with ``>=``:
#: appending is allowed, rewording/reordering/deleting is not, and `aide
#: insights archive` only moves lines between the files this count spans, so
#: routine housekeeping cannot falsify it (CLAUDE.md's archive gotcha).
_NON_ITEM_150_INSIGHT_BASELINE = 209


def _insight_files():
    files = [_INSIGHTS_MD]
    files.extend(sorted(_INSIGHTS_ARCHIVE_DIR.glob("archive-*.md")))
    assert _INSIGHTS_MD.is_file(), "docs/aide/insights.md is missing"
    return files


def _insight_lines():
    out = []
    for path in _insight_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            if _INSIGHT_LINE_RE.match(line):
                out.append((path.name, line))
    assert out, "no insight lines parsed at all -- plumbing failure"
    return out


def test_ac14_every_item_150_insight_is_well_formed_and_honestly_dated():
    engine = _ENGINE_VERSION_FILE.read_text(encoding="utf-8").strip()
    assert engine, ".aide/VERSION is empty"
    today = datetime.date.today()

    claims = [
        (name, line)
        for name, line in _insight_lines()
        if _ITEM_150_CLAIM_RE.search(line)
    ]
    assert claims, (
        "no insights.md line carries item-150 provenance -- AC15's "
        "out-of-scope observations must be recorded there"
    )
    for name, line in claims:
        match = _ITEM_150_GRAMMAR_RE.match(line)
        assert match is not None, (
            f"{name}: an item-150 insight does not match the §1 grammar:\n{line}"
        )
        day = datetime.date.fromisoformat(match.group(1))
        assert day <= today, f"{name}: item-150 insight dated in the future ({day})"
        # An entry records the engine it was observed under and is immutable
        # (§1 → insights.md), so after an engine update it legitimately names
        # an older version. Re-pinned 2026-09-16 (1.37.0 → 1.52.1): the
        # recorded engine must not be newer than the installed one; equality
        # was the original pin and held only until the first update.
        recorded = tuple(int(part) for part in match.group(2).split("."))
        installed = tuple(int(part) for part in engine.split("."))
        assert recorded <= installed, (
            f"{name}: insight records engine {match.group(2)}, newer than "
            f".aide/VERSION's {engine}"
        )


def test_ac14_no_pre_existing_insight_line_was_removed():
    others = [
        line
        for _name, line in _insight_lines()
        if not _ITEM_150_CLAIM_RE.search(line)
    ]
    assert len(others) >= _NON_ITEM_150_INSIGHT_BASELINE, (
        f"only {len(others)} non-item-150 insight lines remain across the inbox "
        f"and archives; the baseline at this item's base is "
        f"{_NON_ITEM_150_INSIGHT_BASELINE}. A captured claim is immutable -- "
        "nothing may be reworded, reordered or deleted (§1)."
    )


def test_adv_ac14_a_malformed_item_150_line_is_caught():
    """The strict grammar must reject the shapes a careless append produces,
    while the claim matcher still spots them -- otherwise a malformed line is
    silently skipped instead of failing."""
    bad = (
        "- [ ] gap — missing the engine token *(item 150, 2026-09-14)*",
        "- [ ] musing — not a recognised class *(item 150, 2026-09-14, engine 1.37.0)*",
        "- [ ] gap — no date at all *(item 150, engine 1.37.0)*",
        "- [ ] gap — dash not em-dash *(item 150, 2026-09-14, engine 1.37.0)*".replace(
            "—", "-"
        ),
    )
    for line in bad:
        assert _ITEM_150_CLAIM_RE.search(line), line
        assert _ITEM_150_GRAMMAR_RE.match(line) is None, (
            f"the grammar must reject this malformed line: {line!r}"
        )

    good = (
        "- [ ] gap — a well-formed observation "
        "*(item 150, 2026-09-14, engine 1.37.0)*"
    )
    assert _ITEM_150_GRAMMAR_RE.match(good) is not None, (
        "the grammar must accept a well-formed line, or the rejections above "
        "prove nothing"
    )


# --- AC15 ------------------------------------------------------------------- #

_ZERO_CASE_SENTENCE = "no out-of-scope observation recorded"

_OBSERVATION_BULLET_RE = re.compile(
    r"^- ((?:knowledge|defect|gap|automation|framework) — .+)$", re.M
)


def test_ac15_the_zero_case_is_stated_not_left_silent():
    """Item 106's ``no override recorded`` discipline: a review that
    legitimately raises nothing passes, and a review that skipped the step does
    not."""
    preamble = _transcript_preamble(_transcript_section(_spec_text()))
    insights_text = "\n".join(
        path.read_text(encoding="utf-8") for path in _insight_files()
    )

    observations = [m.group(1) for m in _OBSERVATION_BULLET_RE.finditer(preamble)]
    verbatim = [obs for obs in observations if obs in insights_text]
    zero_case = _ZERO_CASE_SENTENCE in preamble

    assert verbatim or zero_case, (
        "the transcript preamble must either carry at least one out-of-scope "
        "observation whose text appears verbatim in insights.md (or an "
        f"archive), or state {_ZERO_CASE_SENTENCE!r}. It carries "
        f"{len(observations)} observation bullet(s), none of which appear "
        "verbatim in the insight files, and no zero-case sentence."
    )
    if observations and not zero_case:
        assert len(verbatim) == len(observations), (
            "every out-of-scope observation in the transcript must appear "
            "verbatim in insights.md (or an archive); these do not: "
            f"{[obs[:70] for obs in observations if obs not in insights_text]}"
        )


def test_adv_ac15_both_halves_absent_fails():
    """The predicate itself, run over a preamble that names no observation and
    states no zero case -- so AC15 cannot pass on silence."""
    silent = "**Date:** 2026-09-14. **Outcome:** accepted with changes.\n"
    observations = [m.group(1) for m in _OBSERVATION_BULLET_RE.finditer(silent)]
    assert not observations
    assert _ZERO_CASE_SENTENCE not in silent

    # ...and the zero-case half on its own is enough.
    stated = silent + f"\nThe review raised {_ZERO_CASE_SENTENCE}.\n"
    assert _ZERO_CASE_SENTENCE in stated
