"""Tests for item 168 -- maintainer sign-off of modes 3 and 4.

Roadmap Stage 32's fully-specified bar has six conditions
(``segfacet.traceability.bar_conditions``, item 165); condition 6 -- the
maintainer's sign-off -- is a person's decision, not derivable from the code.
This item ships the mechanism only: ``segfacet.failure_modes.ModeSignOff``,
``SIGN_OFF_OUTCOMES``, ``MODE_SIGN_OFFS`` (shipped **empty**) and
``mode_sign_off``, plus a per-mode ``sign_off`` JSON key and Markdown bullet,
and raises the human gate that reaches this item and item 169.

**No test in this module asserts that a sign-off happened, that its outcome
was approval, or that mode 3 or mode 4 is signed** (item spec, AC9-AC12
preamble). AC9 and AC12 hold vacuously while ``MODE_SIGN_OFFS`` is empty --
that is the honest, expected state, not a defect. AC11 is what keeps that
emptiness a measured claim rather than an unexamined default, and the two
named adversarial cases below -- ``at-the-bar-claim-over-a-failing-mode`` and
``resolution-coherence-is-not-vacuous`` -- prove AC9's and AC12's/AC11's
predicates can actually fail, by perturbing local copies. Neither ever writes
into ``MODE_SIGN_OFFS`` (a ``MappingProxyType``, read-only by design) or into
``docs/aide/progress.md``.

Shape: one module-scoped fixture builds ``build_catalogue(strict=True)`` once
and feeds every ``bar_conditions(...)`` call, the idiom
``tests/test_165_mode_4_at_the_bar.py`` established. ``progress.md`` is parsed
by loading ``.aide/scripts/aide.py`` in process and calling its
``human_gates()`` / ``_split_row``, the idiom ``tests/test_150_maintainer_sign_off.py``
established -- never a hand-written Markdown table parser, and never a write
to ``progress.md``.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_PROGRESS_MD = _REPO_ROOT / "docs" / "aide" / "progress.md"

#: The literal the gate row's Gate cell must contain (item spec A3/A4). Must
#: NOT collide with item 150's "Stage 30 failure-mode specification sign-off"
#: gate -- that is asserted by test_150/test_151, not re-asserted here.
_GATE_TEXT = "Stage 32 selected-mode sign-off"


# =========================================================================== #
# Shared helpers
# =========================================================================== #


def _aide_module():
    """Import ``.aide/scripts/aide.py`` in-process (§6: never shell out to
    the CLI and re-parse its stdout)."""
    spec = importlib.util.spec_from_file_location("_aide_cli_168", _AIDE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _progress_lines():
    return _PROGRESS_MD.read_text(encoding="utf-8").splitlines()


def _sign_off_gate(aide, lines):
    """``(1-based index, HumanGate)`` for the one Stage-32 sign-off row.

    Fails loudly on "not found" and on "found more than one" (§6: assert a
    derived value is recognisable before asserting anything about it).
    """
    matches = [
        (n, gate)
        for n, gate in enumerate(aide.human_gates(lines), start=1)
        if _GATE_TEXT in gate.text
    ]
    assert len(matches) == 1, (
        f"expected exactly one '## Human gates' row whose Gate cell contains "
        f"{_GATE_TEXT!r}; found {len(matches)}: {[n for n, _ in matches]}"
    )
    return matches[0]


def _with_status_cell(aide, lines, gate, status_cell):
    """A copy of *lines* with only *gate*'s Status cell replaced. In memory
    only -- ``progress.md`` is never written by this module."""
    variant = list(lines)
    i = gate.lineno - 1
    cells = aide._split_row(variant[i])
    assert len(cells) == 4, f"gate row is not four cells: {cells!r}"
    cells[2] = status_cell
    variant[i] = "| " + " | ".join(cells) + " |"
    return variant


def _mode_sections(markdown_text):
    """The per-``## Mode N`` body text, one entry per mode, split on the
    heading the catalogue's 16 modes each open with."""
    parts = re.split(r"\n(?=## Mode \d)", markdown_text)
    sections = [p for p in parts if p.startswith("## Mode ")]
    assert len(sections) == 16, f"expected 16 mode sections, found {len(sections)}"
    return sections


@pytest.fixture(scope="module")
def cached_catalogue():
    from segfacet.catalogue import build_catalogue

    return build_catalogue(strict=True)


def _all_conditions_met(catalogue, mode_id):
    import segfacet.traceability as traceability

    conditions = traceability.bar_conditions(mode_id, catalogue=catalogue)
    return all(c.met for c in conditions)


def _first_non_qualifying_mode(fm, catalogue):
    """The first mode id, in ascending order, whose ``bar_conditions`` are
    NOT all met -- recomputed live rather than a pinned literal, so the
    adversarial fixture below tracks the specification instead of going
    stale against it."""
    count = 0
    for mode_id in sorted(fm.SPECIFICATION):
        count += 1
        if not _all_conditions_met(catalogue, mode_id):
            return mode_id
    assert False, (
        f"expected at least one of the {count} catalogued modes to fail "
        "bar_conditions -- if every mode now clears all five, this fixture "
        "needs a different source of a non-qualifying mode"
    )


# =========================================================================== #
# AC1-AC8 -- the mechanism (satisfiable now, independent of any decision)
# =========================================================================== #


def test_ac1_sign_off_record_field_order():
    import segfacet.failure_modes as fm

    names = tuple(f.name for f in dataclasses.fields(fm.ModeSignOff))
    assert names == ("mode_id", "date", "outcome", "note")
    assert dataclasses.is_dataclass(fm.ModeSignOff)
    assert fm.ModeSignOff.__dataclass_params__.frozen is True


def _valid_sign_off_kwargs(fm):
    return {
        "mode_id": 4,
        "date": "2026-09-20",
        "outcome": fm.SIGN_OFF_OUTCOMES[0],
        "note": "measured on this tree",
    }


def test_ac2_each_field_is_validated_at_construction():
    import segfacet.failure_modes as fm

    # Baseline must itself construct cleanly, or the table below proves nothing.
    fm.ModeSignOff(**_valid_sign_off_kwargs(fm))

    invalid_cases = [
        ("mode_id", 0),
        ("mode_id", -1),
        ("mode_id", True),
        ("mode_id", "4"),
        ("date", "2026-9-20"),
        ("date", "20260920"),
        ("date", "09-20-2026"),
        ("date", ""),
        ("outcome", "approved"),
        ("outcome", ""),
        ("outcome", None),
        ("note", ""),
        ("note", None),
        ("note", 123),
    ]
    count = 0
    for field, bad_value in invalid_cases:
        count += 1
        kwargs = _valid_sign_off_kwargs(fm)
        kwargs[field] = bad_value
        with pytest.raises(ValueError, match=field) as excinfo:
            fm.ModeSignOff(**kwargs)
        assert field in str(excinfo.value), (
            f"ValueError for bad {field}={bad_value!r} does not name the "
            f"offending field: {excinfo.value}"
        )
    assert count == len(invalid_cases)


def test_ac3_outcome_vocabulary_is_closed_and_two_valued():
    import segfacet.failure_modes as fm

    assert fm.SIGN_OFF_OUTCOMES == ("at-the-bar", "intermediate-state")


def test_ac4_mapping_is_read_only():
    from types import MappingProxyType

    import segfacet.failure_modes as fm

    assert isinstance(fm.MODE_SIGN_OFFS, MappingProxyType)
    with pytest.raises(TypeError):
        fm.MODE_SIGN_OFFS[1] = fm.ModeSignOff(
            mode_id=1, date="2026-09-20", outcome=fm.SIGN_OFF_OUTCOMES[0], note="x"
        )


def test_ac5_mapping_keys_agree_with_their_records_and_the_specification():
    import segfacet.failure_modes as fm

    count = 0
    for key in fm.MODE_SIGN_OFFS:
        count += 1
        assert key in fm.SPECIFICATION, f"key {key} is not a catalogued mode id"
        assert fm.MODE_SIGN_OFFS[key].mode_id == key, (
            f"MODE_SIGN_OFFS[{key}].mode_id == {fm.MODE_SIGN_OFFS[key].mode_id}, "
            f"not the mapping's own key"
        )
    # MODE_SIGN_OFFS ships empty (item spec A2); count == 0 here is the
    # expected, honest state -- the invariant itself is exercised adversarially
    # below (sign-off-for-an-unknown-mode / key-disagrees-with-its-record).
    assert count == len(fm.MODE_SIGN_OFFS)


def test_ac6_unsigned_mode_reads_as_unsigned():
    import segfacet.failure_modes as fm

    count = 0
    for mode_id in fm.SPECIFICATION:
        count += 1
        assert fm.mode_sign_off(mode_id) == fm.MODE_SIGN_OFFS.get(mode_id)
    assert count == 16


def test_ac7_serialisation_carries_one_sign_off_key_per_mode():
    import segfacet.failure_modes as fm

    payload = fm.specification_to_dict()
    modes = payload["modes"]
    assert len(modes) == 16
    count = 0
    for record in modes:
        count += 1
        record_sign_off = fm.mode_sign_off(record["id"])
        if record_sign_off is None:
            assert record["sign_off"] is None
        else:
            assert record["sign_off"] == {
                "date": record_sign_off.date,
                "outcome": record_sign_off.outcome,
                "note": record_sign_off.note,
            }
    assert count == 16


def test_ac8_rendering_carries_one_sign_off_bullet_per_mode():
    import segfacet.failure_modes as fm

    markdown_text = fm.render_markdown()
    sections = _mode_sections(markdown_text)
    count = 0
    for section, mode_id in zip(sections, sorted(fm.SPECIFICATION)):
        count += 1
        bullets = [
            line for line in section.splitlines() if line.startswith("- Maintainer sign-off: ")
        ]
        assert len(bullets) == 1, (
            f"mode {mode_id} section carries {len(bullets)} sign-off bullets, "
            f"expected exactly one: {bullets}"
        )
        remainder = bullets[0][len("- Maintainer sign-off: "):]
        record = fm.mode_sign_off(mode_id)
        if record is None:
            assert remainder == "(none recorded)"
        else:
            assert remainder == f"{record.date} -- {record.outcome} -- {fm._md_escape(record.note)}"
    assert count == 16


# =========================================================================== #
# AC9-AC12 -- the gate, and invariants that hold in both halves
# =========================================================================== #


def test_ac9_at_the_bar_claims_are_cross_checked_against_live_state(cached_catalogue):
    import segfacet.failure_modes as fm

    at_the_bar_entries = [
        entry for entry in fm.MODE_SIGN_OFFS.values() if entry.outcome == "at-the-bar"
    ]
    # Vacuously true while MODE_SIGN_OFFS ships empty (item spec, AC9-AC12
    # preamble) -- the predicate's ability to fail is proved by the
    # at-the-bar-claim-over-a-failing-mode case below, not here.
    count = 0
    for entry in at_the_bar_entries:
        count += 1
        assert _all_conditions_met(cached_catalogue, entry.mode_id), (
            f"mode {entry.mode_id} is recorded 'at-the-bar' but does not "
            "clear all five live bar_conditions"
        )
    assert count == len(at_the_bar_entries)


def test_ac10_human_gate_exists_is_unique_and_reaches_168_and_169():
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    assert gate.blocks == [168, 169], f"expected blocks == [168, 169]; parsed {gate.blocks!r}"
    assert gate.stage is None, f"gate blocks named items, not a stage; parsed stage={gate.stage!r}"
    assert gate.blocks_all is False, "gate is not a programme-level stop"


def test_ac11_a_record_exists_iff_the_gate_is_resolved():
    import segfacet.failure_modes as fm

    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)

    assert bool(fm.MODE_SIGN_OFFS) == (gate.kind != "awaiting"), (
        f"bool(MODE_SIGN_OFFS)={bool(fm.MODE_SIGN_OFFS)!r} disagrees with "
        f"gate.kind={gate.kind!r}"
    )


def test_ac12_a_recorded_sign_off_carries_the_resolved_gates_own_date():
    import segfacet.failure_modes as fm

    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)
    status_cell = aide._split_row(lines[gate.lineno - 1])[2]
    match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", status_cell)

    # Vacuously true while MODE_SIGN_OFFS ships empty and the gate stays
    # unresolved (no ISO date to compare against); the adversarial cases
    # above/below exercise AC9's and AC11's ability to fail instead.
    count = 0
    for entry in fm.MODE_SIGN_OFFS.values():
        count += 1
        assert match is not None, (
            "a sign-off record exists but the gate's Status cell carries no "
            f"ISO date to compare it against: {status_cell!r}"
        )
        assert entry.date == match.group(1)
    assert count == len(fm.MODE_SIGN_OFFS)


# =========================================================================== #
# Named adversarial cases (Testing Strategy) -- and no others.
# =========================================================================== #


def test_sign_off_for_an_unknown_mode():
    import segfacet.failure_modes as fm

    unknown_id = max(fm.SPECIFICATION) + 1000
    assert unknown_id not in fm.SPECIFICATION
    bad_mapping = {
        unknown_id: fm.ModeSignOff(
            mode_id=unknown_id,
            date="2026-09-20",
            outcome=fm.SIGN_OFF_OUTCOMES[0],
            note="typo'd mode id",
        )
    }
    with pytest.raises(ValueError, match=str(unknown_id)):
        fm._validate_sign_offs(bad_mapping)


def test_key_disagrees_with_its_record():
    import segfacet.failure_modes as fm

    mode_ids = sorted(fm.SPECIFICATION)
    key = mode_ids[0]
    other_mode_id = mode_ids[1]
    assert key != other_mode_id
    bad_mapping = {
        key: fm.ModeSignOff(
            mode_id=other_mode_id,
            date="2026-09-20",
            outcome=fm.SIGN_OFF_OUTCOMES[0],
            note="signed for a different mode",
        )
    }
    with pytest.raises(ValueError, match=f"{key}") as excinfo:
        fm._validate_sign_offs(bad_mapping)
    assert str(other_mode_id) in str(excinfo.value), (
        "the error must name both the mapping's key and the record's own "
        f"mode_id: {excinfo.value}"
    )


def test_at_the_bar_claim_over_a_failing_mode(cached_catalogue):
    """AC9's predicate, re-run over a constructed at-the-bar claim for a mode
    that does not clear bar_conditions, must fail -- otherwise AC9 passes
    vacuously on the empty shipped mapping and certifies nothing at all."""
    import segfacet.failure_modes as fm

    failing_mode_id = _first_non_qualifying_mode(fm, cached_catalogue)
    assert not _all_conditions_met(cached_catalogue, failing_mode_id), (
        f"mode {failing_mode_id} was selected as non-qualifying but now "
        "clears all five bar_conditions -- fixture is stale"
    )

    claim = fm.ModeSignOff(
        mode_id=failing_mode_id,
        date="2026-09-20",
        outcome="at-the-bar",
        note="constructed for the adversarial test only, not shipped",
    )
    assert claim.mode_id not in fm.MODE_SIGN_OFFS, (
        "the constructed claim must never be looked up through the shipped "
        "MODE_SIGN_OFFS -- this test proves the predicate on a local copy"
    )

    # AC9's predicate, applied to the local claim.
    assert claim.outcome == "at-the-bar"
    assert _all_conditions_met(cached_catalogue, claim.mode_id) is False


def test_resolution_coherence_is_not_vacuous():
    """AC11's if-and-only-if, re-run with the two sides forced to disagree in
    each direction, must fail both times -- otherwise it is satisfied by
    both sides agreeing by accident and asserts nothing at all.

    Each direction flips ONE side away from whatever is live (the gate was
    ``⏳`` with an empty mapping until 2026-09-22 and ``✅ Approved`` with two
    records after), so the test is derived from live state, never from a
    literal of it.
    """
    import segfacet.failure_modes as fm

    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)
    live_resolved = gate.kind != "awaiting"

    # Direction 1: the gate flipped to the opposite kind, shipped mapping live.
    flipped_cell = "⏳ Awaiting" if live_resolved else "✅ Approved (2026-09-21)"
    flipped_lines = _with_status_cell(aide, lines, gate, flipped_cell)
    _, flipped_gate = _sign_off_gate(aide, flipped_lines)
    assert (flipped_gate.kind != "awaiting") is not live_resolved, (
        f"the flipped Status cell {flipped_cell!r} did not change the gate's "
        f"kind away from the live {gate.kind!r}"
    )
    assert bool(fm.MODE_SIGN_OFFS) != (flipped_gate.kind != "awaiting"), (
        "AC11's predicate must fail once the gate's resolution is flipped "
        "while MODE_SIGN_OFFS stays as shipped"
    )

    # Direction 2: the mapping flipped (local only, never MODE_SIGN_OFFS)
    # against the live gate.
    if fm.MODE_SIGN_OFFS:
        flipped_mapping = {}
    else:
        fake_mode_id = sorted(fm.SPECIFICATION)[0]
        flipped_mapping = {
            fake_mode_id: fm.ModeSignOff(
                mode_id=fake_mode_id,
                date="2026-09-20",
                outcome=fm.SIGN_OFF_OUTCOMES[0],
                note="local-only, never assigned into MODE_SIGN_OFFS",
            )
        }
    assert bool(flipped_mapping) is not bool(fm.MODE_SIGN_OFFS)
    assert bool(flipped_mapping) != live_resolved, (
        "AC11's predicate must fail for a mapping whose emptiness is flipped "
        "against the live gate"
    )


def test_unsigned_never_renders_as_a_blank_record():
    import segfacet.failure_modes as fm

    payload = fm.specification_to_dict()
    markdown_text = fm.render_markdown()
    sections = _mode_sections(markdown_text)

    count = 0
    for record, section in zip(payload["modes"], sections):
        count += 1
        sign_off = record["sign_off"]
        if sign_off is None:
            bullets = [
                line
                for line in section.splitlines()
                if line.startswith("- Maintainer sign-off: ")
            ]
            assert len(bullets) == 1
            assert bullets[0] == "- Maintainer sign-off: (none recorded)"
        else:
            assert sign_off["date"] != ""
            assert sign_off["outcome"] != ""
            assert sign_off["date"] is not None
            assert sign_off["outcome"] is not None
    assert count == 16


def test_gate_row_is_four_cells():
    aide = _aide_module()
    lines = _progress_lines()
    _index, gate = _sign_off_gate(aide, lines)
    cells = aide._split_row(lines[gate.lineno - 1])
    assert len(cells) == 4, f"gate row split into {len(cells)} cells, expected 4: {cells!r}"
