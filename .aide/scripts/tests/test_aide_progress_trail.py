"""The trail under a progress.md table — issue #474.

`progress.md`'s Human gates, Environment-Gated Capability Verification and
Outcome targets tables had grown prose in their cells. Each cell is now a
label or a pointer, and the detail is a dated bullet line under its table,
keyed to its row: a gate by its `gate-<hex>` ID, a capability or a target
by its first cell. These tests hold the writers (`gate approve|decline
--evidence`, `gate reword`, `progress compact`), the readers (`gate list`,
`aide status`, every reader of a gate ID) and `aide check`'s long-cell
findings to that shape, and hold an old document to reading as it did.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_progress_trail", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


LONG = "x" * (aide.LONG_CELL + 1)
LONG_NOTE = ("Measured on the real host: " + "detail " * 30).strip()


def _progress(gates: str = "", capabilities: str = "", targets: str = "") -> str:
    return f"""\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 🚧 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 🚧 |

## Environment-Gated Capability Verification

| Capability | Package / Tool | Introduced by | Status | Notes |
|------------|-----------------|----------------|--------|-------|
{capabilities}

## Outcome targets

| Target | Objective | Attempted by | Status | Evidence / follow-up |
|--------|-----------|--------------|--------|----------------------|
{targets}

---

## Human gates

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
{gates}

---

## Stage 1 — Rules — 🚧

**Deliverables.**
- 📋 A. *(Item 027)*
- 🚧 B. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""


AWAITING = "| Golden retirement approved | 028 | ⏳ Awaiting | — |"
SECOND = "| Budget signed | 027 | ⏳ Awaiting | — |"
CAPABILITY = "| GPU inference | torch (`gpu` profile) | Stage 1 | ❓ Unverified | — |"
TARGET = "| FPR ≤ 0.10 — on held-out GT | G1 | Stage 1 | ❓ Unverified | — |"


def _lines(text: str):
    return text.splitlines()


def _gid(text: str, n: int = 0) -> str:
    return aide.gate_ids(aide.human_gates(_lines(text)))[n]


# --------------------------------------------------------------------------- #
# gate approve | decline --evidence
# --------------------------------------------------------------------------- #
def test_evidence_goes_on_a_trail_line_under_the_table():
    text = _progress(gates=f"{AWAITING}\n{SECOND}")
    gid = _gid(text)
    out = aide.set_gate_status(text, 1, "declined", "not before the audit",
                               today="2026-10-12")
    lines = _lines(out)
    row = next(l for l in lines if l.startswith("| Golden"))
    assert row == ("| Golden retirement approved | 028 | ❌ Declined "
                   "(2026-10-12) | see trail (2026-10-12) |")
    trail = f"- {gid} — ❌ Declined 2026-10-12: not before the audit"
    # Under the table, a blank line between, above the section's `---`.
    at = lines.index(trail)
    assert lines[at - 1] == "" and lines[at - 2].startswith("| Budget signed")
    assert lines[at + 1] == "" and lines[at + 2] == "---"
    assert aide.unreadable_row_errors(lines) == []


def test_a_second_decision_appends_and_keeps_the_first():
    text = _progress(gates=AWAITING)
    gid = _gid(text)
    once = aide.set_gate_status(text, 1, "declined", "no", today="2026-10-01")
    twice = aide.set_gate_status(once, 1, "approved", "yes now", today="2026-10-12")
    trail = [t.body for t in aide.table_trail(_lines(twice), aide._HUMAN_GATES)]
    assert trail == ["❌ Declined 2026-10-01: no", "✅ Approved 2026-10-12: yes now"]
    assert all(t.key == gid for t in aide.table_trail(_lines(twice), aide._HUMAN_GATES))


def test_text_the_cell_held_is_moved_to_the_trail_first_verbatim():
    held = "| Golden retirement approved | 028 | ⏳ Awaiting | Approve with the Stage 2 row. |"
    text = _progress(gates=held)
    gid = _gid(text)
    out = aide.set_gate_status(text, 1, "approved", "ok", today="2026-10-12")
    bodies = [t.body for t in aide.table_trail(_lines(out), aide._HUMAN_GATES)]
    assert bodies == ["Approve with the Stage 2 row.", "✅ Approved 2026-10-12: ok"]
    assert f"- {gid} — Approve with the Stage 2 row." in out


def test_without_evidence_the_cell_is_left_as_it_reads():
    held = "| Golden retirement approved | 028 | ⏳ Awaiting | a note |"
    out = aide.set_gate_status(_progress(gates=held), 1, "approved",
                               today="2026-10-12")
    assert "| ✅ Approved (2026-10-12) | a note |" in out
    assert aide.table_trail(_lines(out), aide._HUMAN_GATES) == []


def test_a_gate_with_no_id_keeps_its_note_in_its_cell():
    out = aide.set_gate_status(_progress(gates="| | 028 | ⏳ Awaiting | — |"), 1,
                               "approved", "fine", today="2026-10-12")
    assert "|  | 028 | ✅ Approved (2026-10-12) | fine |" in out


# --------------------------------------------------------------------------- #
# reading the trail: gate list, aide status
# --------------------------------------------------------------------------- #
def test_the_record_reads_the_trail_and_falls_back_to_the_cell():
    old = "| Budget signed | 027 | ✅ Approved (2026-09-01) | signed by finance |"
    text = _progress(gates=f"{AWAITING}\n{old}")
    gid = _gid(text)
    text = text.replace(f"{old}\n", f"{old}\n\n- {gid} — context: asked by legal\n")
    out = aide.set_gate_status(text, 1, "approved", "retired", today="2026-10-12")
    gates = aide.human_gates(_lines(out))
    record = aide.gate_trail_record(_lines(out), gates)
    assert record[0] == {"context": "asked by legal", "evidence": "retired"}
    assert record[1] == {"evidence": "signed by finance"}


def test_gate_list_prints_context_and_evidence(tmp_path: Path, capsys):
    repo = _repo(tmp_path, _progress(gates=f"{AWAITING}\n{SECOND}"))
    ppath = repo / "docs" / "aide" / "progress.md"
    gid = _gid(ppath.read_text(encoding="utf-8"))
    assert aide.main(["--repo", str(repo), "gate", "approve", gid,
                      "--evidence", "reviewed with the owner", "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "gate", "list"]) == 0
    out = capsys.readouterr().out
    assert "       evidence: reviewed with the owner" in out
    assert out.count("evidence:") == 1


def test_status_prints_a_declined_gate_s_evidence_from_the_trail(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, _progress(gates=AWAITING), git=True)
    gid = _gid((repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8"))
    assert aide.main(["--repo", str(repo), "gate", "decline", gid,
                      "--reason", "budget is not there", "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "status"]) == 0
    out = capsys.readouterr().out
    assert "    evidence: budget is not there" in out


def test_status_reads_an_old_row_s_evidence_from_its_cell(tmp_path: Path, capsys):
    old = "| Golden retirement approved | 028 | ❌ Declined (2026-09-01) | too risky |"
    repo = _repo(tmp_path, _progress(gates=old), git=True)
    assert aide.main(["--repo", str(repo), "status"]) == 0
    assert "    evidence: too risky" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# gate reword — and the old ID as an alias
# --------------------------------------------------------------------------- #
def test_reword_restates_the_question_and_keeps_the_old_id_resolving():
    text = _progress(gates=f"{AWAITING}\n{SECOND}")
    old_id = _gid(text)
    out, was, now = aide.reword_gate(text, 1, "Retire the golden files?",
                                     today="2026-10-12")
    assert was == old_id and now != old_id
    assert "| Retire the golden files? | 028 | ⏳ Awaiting | — |" in out
    assert (f"- {now} — reworded 2026-10-12, was: Golden retirement approved"
            in _lines(out))
    gates = aide.human_gates(_lines(out))
    assert aide.resolve_gate_ref(old_id, gates) == [0]
    assert aide.resolve_gate_ref(now, gates) == [0]
    assert aide.gate_index_for_ref(old_id, gates) == 1
    # The ID the row prints is the new one; the alias is only read.
    assert aide.gate_ids(gates)[0] == now


def test_two_rewords_in_a_row_still_lead_to_the_gate():
    text = _progress(gates=AWAITING)
    first = _gid(text)
    once, _, middle = aide.reword_gate(text, 1, "Retire the golden files?",
                                       today="2026-10-01")
    twice, _, last = aide.reword_gate(once, 1, "Retire golden files now?",
                                      today="2026-10-12")
    gates = aide.human_gates(_lines(twice))
    for ref in (first, middle, last):
        assert aide.resolve_gate_ref(ref, gates) == [0], ref


def test_the_alias_stands_only_while_its_trail_line_does():
    text = _progress(gates=AWAITING)
    old_id = _gid(text)
    out, _, now = aide.reword_gate(text, 1, "Retire the golden files?",
                                   today="2026-10-12")
    gone = "\n".join(l for l in _lines(out) if "reworded" not in l)
    assert aide.resolve_gate_ref(old_id, aide.human_gates(_lines(gone))) == []


def test_a_decision_line_written_under_the_old_id_still_reads_as_the_gate_s():
    text = _progress(gates=AWAITING)
    declined = aide.set_gate_status(text, 1, "declined", "first try",
                                    today="2026-10-01")
    # A decided gate refuses a reword; put it back to awaiting by hand, as a
    # person re-asking would, and reword it then.
    reopened = declined.replace("❌ Declined (2026-10-01)", "⏳ Awaiting")
    out, _, _ = aide.reword_gate(reopened, 1, "Retire the golden files?",
                                 today="2026-10-12")
    record = aide.gate_trail_record(_lines(out), aide.human_gates(_lines(out)))
    assert record[0]["evidence"] == "first try"


@pytest.mark.parametrize("question, why", [
    ("", "empty"),
    ("a | b", "may not contain '|'"),
    ("Golden retirement approved", "already asks that question"),
    ("Budget  signed", "another gate row already asks"),
])
def test_reword_refuses(question, why):
    with pytest.raises(ValueError, match=why):
        aide.reword_gate(_progress(gates=f"{AWAITING}\n{SECOND}"), 1, question)


def test_reword_refuses_a_decided_gate():
    decided = "| Golden retirement approved | 028 | ✅ Approved (2026-10-01) | — |"
    with pytest.raises(ValueError, match="decided gate's question is the record"):
        aide.reword_gate(_progress(gates=decided), 1, "Something else?")


def test_a_citation_of_the_old_id_passes_check_after_a_reword(tmp_path: Path):
    repo = _repo(tmp_path, _progress(gates=AWAITING))
    ddir = repo / "docs" / "aide"
    old_id = _gid((ddir / "progress.md").read_text(encoding="utf-8"))
    (ddir / "items").mkdir()
    (ddir / "items" / "028-retire.md").write_text(f"Held by {old_id}.\n",
                                                  encoding="utf-8")
    assert aide.main(["--repo", str(repo), "gate", "reword", old_id, "--text",
                      "Retire the golden files?", "--no-commit"]) == 0
    lines = (ddir / "progress.md").read_text(encoding="utf-8").splitlines()
    errors, _ = aide.gate_reference_findings(repo, aide.load_config(repo), ddir, lines)
    assert errors == []


def test_gate_reword_cli_refuses_writing_nothing(tmp_path: Path, capsys):
    decided = "| Budget signed | 027 | ❌ Declined (2026-10-01) | — |"
    repo = _repo(tmp_path, _progress(gates=f"{AWAITING}\n{decided}"))
    ppath = repo / "docs" / "aide" / "progress.md"
    before = ppath.read_bytes()
    for argv in (["gate", "reword", "1"],
                 ["gate", "reword", "1", "--text", "Q?", "--evidence", "e"],
                 ["gate", "approve", "1", "--text", "Q?"],
                 ["gate", "reword", "2", "--text", "Q?"],
                 ["gate", "reword", "1", "--text", "  "],
                 ["gate", "reword", "1", "--text", "a | b"],
                 ["gate", "reword", "1", "--text", "Budget signed"]):
        assert aide.main(["--repo", str(repo), *argv, "--no-commit"]) == 2, argv
        assert ppath.read_bytes() == before, argv


def test_gate_reword_commits_progress_alone(tmp_path: Path, capsys):
    repo = _repo(tmp_path, _progress(gates=AWAITING), git=True)
    old_id = _gid((repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8"))
    assert aide.main(["--repo", str(repo), "gate", "reword", old_id, "--text",
                      "Retire the golden files?"]) == 0
    assert _git_out(["status", "--porcelain"], repo) == ""
    assert _git_out(["show", "--name-only", "--format=%s", "HEAD"], repo).split() == [
        "docs:", "human", old_id, "reworded", "as",
        _gid((repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")),
        "docs/aide/progress.md"]


@pytest.mark.parametrize("breakage", ["cell shortened by hand", "row deleted"])
def test_a_dangling_trail_key_is_a_warning_never_an_error(tmp_path: Path,
                                                         breakage: str):
    """PR #478 review: the trail is append-only, so a key whose row went is
    reported, and is not a citation `check` errors on (which stalls merge)."""
    text = aide.set_gate_status(_progress(gates=f"{AWAITING}\n{SECOND}"), 1,
                                "approved", "fine", today="2026-10-12")
    gid = _gid(text)
    if breakage == "row deleted":
        text = "\n".join(l for l in text.splitlines()
                         if not l.startswith("| Golden")) + "\n"
    else:
        text = text.replace("| Golden retirement approved |", "| Golden retired |")
    repo = _repo(tmp_path, text)
    ddir = repo / "docs" / "aide"
    errors, warnings = aide.run_checks(repo, aide.load_config(repo), branches=[])
    assert errors == []
    assert [w for w in warnings if "trail line keyed" in w] == [
        w for w in warnings if f"trail line keyed {gid}" in w and "names no human gate row" in w]
    assert any(f"trail line keyed {gid}" in w for w in warnings)


def test_a_citation_in_a_trail_line_s_body_is_still_checked(tmp_path: Path):
    text = _progress(gates=AWAITING)
    gid = _gid(text)
    text = text.replace(f"{AWAITING}\n",
                        f"{AWAITING}\n\n- {gid} — context: see gate-dead\n")
    repo = _repo(tmp_path, text)
    ddir = repo / "docs" / "aide"
    errors, _ = aide.gate_reference_findings(
        repo, aide.load_config(repo), ddir, text.splitlines())
    assert len(errors) == 1 and "gate-dead names no human gate" in errors[0]


def test_reword_refuses_a_question_another_row_once_asked():
    """Otherwise the other row's old ID — its citations — would move here."""
    text = _progress(gates=f"{AWAITING}\n{SECOND}")
    once, _, _ = aide.reword_gate(text, 1, "Retire the golden files?",
                                  today="2026-10-12")
    with pytest.raises(ValueError, match="once asked that question"):
        aide.reword_gate(once, 2, "Golden retirement approved")
    # Its own old wording is its own alias, and may come back.
    back, _, _ = aide.reword_gate(once, 1, "Golden retirement approved",
                                  today="2026-10-13")
    assert "| Golden retirement approved | 028 |" in back


def test_a_status_cell_compact_moved_is_not_the_gate_s_evidence():
    status = "❌ Declined (2026-10-01, " + "after a long meeting " * 10 + ")"
    text = _progress(gates=f"| Golden retirement approved | 028 | {status} | too risky |")
    out, messages = aide.compact_progress(text)
    assert len(messages) == 1
    record = aide.gate_trail_record(out.splitlines(), aide.human_gates(out.splitlines()))
    assert record[0] == {"evidence": "too risky"}


@pytest.mark.parametrize("body", [
    "❌ Declined by David: " + ("far too risky " * 12).strip(),
    "✅ Approved by Dana 2026-01-01: sign-off",
])
def test_an_evidence_line_that_opens_with_its_mark_is_still_evidence(body):
    text = _progress(gates="| Golden retirement approved | 028 | ❌ Declined (2026-10-01) | see trail |")
    gates = aide.human_gates(text.splitlines())
    key = aide.gate_ids(gates)[0]
    row = "| Golden retirement approved | 028 | ❌ Declined (2026-10-01) | see trail |"
    lines = text.replace(row, f"{row}\n\n- {key} — {body}").splitlines()
    record = aide.gate_trail_record(lines, aide.human_gates(lines))
    assert record[0] == {"evidence": body}


@pytest.mark.parametrize("cell, short", [
    ("✅ Met 2026-02-02 — " + "detail " * 30, "✅ Met (2026-02-02)"),
    ("✅ Met (2026-02-02, " + "detail " * 30 + ")", "✅ Met (2026-02-02)"),
    ("❌ Not met, measured 0.90 " + "detail " * 30, "❌ Not met"),
])
def test_a_short_status_names_its_date_once(cell, short):
    assert aide._short_status(cell) == short


# --------------------------------------------------------------------------- #
# progress compact
# --------------------------------------------------------------------------- #
def _long_document() -> str:
    return _progress(
        gates=(f"| Golden retirement approved | 028 | ✅ Approved (2026-10-01) | {LONG_NOTE} |\n"
               f"| | 027 | ✅ Approved (2026-10-01) | {LONG_NOTE} |\n"
               f"{SECOND}"),
        capabilities=(f"| GPU inference | torch (`gpu` profile) | Stage 1 | "
                      f"✅ Verified (2026-08-29, this workstation: {LONG_NOTE}) | "
                      f"{LONG_NOTE} |"),
        targets=(f"| FPR ≤ 0.10 — on held-out GT | G1 | Stage 1 | "
                 f"❌ Not met, measured 0.90 after {LONG_NOTE} | short |"))


def test_compact_moves_long_cells_verbatim_and_leaves_pointers():
    text = _long_document()
    before = _lines(text)
    out, messages = aide.compact_progress(text)
    lines = _lines(out)
    assert len(messages) == 4
    assert "| GPU inference | torch (`gpu` profile) | Stage 1 | ✅ Verified (2026-08-29) | see trail |" in lines
    assert "| FPR ≤ 0.10 — on held-out GT | G1 | Stage 1 | ❌ Not met | short |" in lines
    assert "| Golden retirement approved | 028 | ✅ Approved (2026-10-01) | see trail |" in lines
    # The keys: a capability and a target by first cell, a gate by its ID.
    cap = aide.table_trail(lines, aide._CAPABILITIES)
    assert [(t.key, t.body) for t in cap] == [
        ("GPU inference", f"✅ Verified (2026-08-29, this workstation: {LONG_NOTE})"),
        ("GPU inference", LONG_NOTE)]
    tgt = aide.table_trail(lines, aide._OUTCOME_TARGETS)
    assert [t.key for t in tgt] == ["FPR ≤ 0.10 — on held-out GT"]
    gate = aide.table_trail(lines, aide._HUMAN_GATES)
    assert [t.key for t in gate] == [_gid(text)]
    # What every reader decides on is where it was.
    assert ([(g.text, g.kind) for g in aide.human_gates(lines)]
            == [(g.text, g.kind) for g in aide.human_gates(before)])
    assert aide.gate_ids(aide.human_gates(lines)) == aide.gate_ids(aide.human_gates(before))
    assert ([(c.text, c.kind, c.noted, c.profiles) for c in aide.gated_capabilities(lines)]
            == [(c.text, c.kind, c.noted, c.profiles) for c in aide.gated_capabilities(before)])
    assert ([(t.text, t.kind, t.objectives) for t in aide.outcome_targets(lines)]
            == [(t.text, t.kind, t.objectives) for t in aide.outcome_targets(before)])
    assert aide.unreadable_row_errors(lines) == []
    assert aide.unreadable_row_warnings(lines) == []


def test_compact_skips_a_gate_row_with_no_id_and_is_idempotent():
    out, _ = aide.compact_progress(_long_document())
    assert f"| | 027 | ✅ Approved (2026-10-01) | {LONG_NOTE} |" in out
    again, messages = aide.compact_progress(out)
    assert messages == [] and again == out


def test_compact_never_touches_an_identity_cell():
    long_gate = f"| {LONG} | 028 | ⏳ Awaiting | — |"
    text = _progress(gates=long_gate)
    assert aide.compact_progress(text) == (text, [])


def test_compact_cli_prints_what_moved_and_refuses_other_arguments(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, _long_document())
    ppath = repo / "docs" / "aide" / "progress.md"
    assert aide.main(["--repo", str(repo), "progress", "compact", "--stage",
                      "1"]) == 2
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "progress", "compact",
                      "--no-commit"]) == 0
    out = capsys.readouterr().out
    assert out.count("to the trail") == 4
    assert "moved its Notes cell" in out
    after = ppath.read_text(encoding="utf-8")
    assert aide.main(["--repo", str(repo), "progress", "compact",
                      "--no-commit"]) == 0
    assert "no change" in capsys.readouterr().out
    assert ppath.read_text(encoding="utf-8") == after


def test_compact_commits_progress_alone(tmp_path: Path, capsys):
    repo = _repo(tmp_path, _long_document(), git=True)
    (repo / "unrelated.txt").write_text("left alone\n", encoding="utf-8")
    assert aide.main(["--repo", str(repo), "progress", "compact"]) == 0
    assert _git_out(["status", "--porcelain"], repo) == "?? unrelated.txt"
    assert _git_out(["show", "--name-only", "--format=%s", "HEAD"], repo).splitlines() == [
        "progress(aide): compact long table cells into their trails", "",
        "docs/aide/progress.md"]


def test_a_compaction_whose_commit_fails_is_put_back(tmp_path: Path, capsys):
    """Issue #309's rule, as every recording verb keeps it: a commit that did
    not happen leaves progress.md as it was, exit 1, for the re-run."""
    repo = _repo(tmp_path, _long_document(), git=True)
    ppath = repo / "docs" / "aide" / "progress.md"
    before = ppath.read_bytes()
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert aide.main(["--repo", str(repo), "progress", "compact"]) == 1
    finally:
        lock.unlink()
    assert ppath.read_bytes() == before
    assert aide.main(["--repo", str(repo), "progress", "compact"]) == 0
    assert "see trail" in _git_out(["show", "HEAD:docs/aide/progress.md"], repo)


# --------------------------------------------------------------------------- #
# aide check: long cells
# --------------------------------------------------------------------------- #
def test_a_long_gate_question_in_a_live_row_warns_and_names_reword():
    text = _progress(gates=f"| {LONG} | 028 | ⏳ Awaiting | — |")
    gid = _gid(text)
    (w,) = aide.long_cell_warnings(_lines(text))
    assert f"aide gate reword {gid} --text" in w
    assert f"Gate cell is {len(LONG)} characters" in w


def test_a_settled_row_s_long_identity_cell_is_not_warned_on():
    text = _progress(
        gates=f"| {LONG} | 028 | ✅ Approved (2026-10-01) | — |",
        capabilities=f"| {LONG} | torch | Stage 1 | ✅ Verified (2026-10-01) | — |",
        targets=f"| {LONG} | G1 | Stage 1 | ✅ Met (2026-10-01) | — |")
    assert aide.long_cell_warnings(_lines(text)) == []


def test_a_long_label_in_a_live_capability_or_target_warns():
    text = _progress(
        capabilities=f"| {LONG} | torch | Stage 1 | ❓ Unverified | — |",
        targets=f"| {LONG} | G1 | Stage 1 | ❓ Unverified | — |")
    warnings = aide.long_cell_warnings(_lines(text))
    assert len(warnings) == 2
    assert all("trail line under the table keyed by the new label" in w
               for w in warnings)


def test_compactable_rows_are_one_warning_per_table_not_one_per_row():
    note = f"| Q{{n}} | 028 | ✅ Approved (2026-10-01) | {LONG_NOTE} |"
    text = _progress(gates="\n".join(note.format(n=n) for n in range(3)))
    (w,) = aide.long_cell_warnings(_lines(text))
    assert "human-gate table — 3 row(s)" in w and "aide progress compact" in w
    out, _ = aide.compact_progress(text)
    assert aide.long_cell_warnings(_lines(out)) == []


def test_a_short_document_draws_no_long_cell_finding():
    text = _progress(gates=AWAITING, capabilities=CAPABILITY, targets=TARGET)
    assert aide.long_cell_warnings(_lines(text)) == []


def test_a_first_cell_key_holding_a_dash_of_its_own_is_one_key():
    text = _progress(targets=TARGET).replace(
        f"{TARGET}\n", f"{TARGET}\n\n- FPR ≤ 0.10 — on held-out GT — measured "
        f"0.08 on 2026-10-12\n- an unkeyed note\n")
    (t,) = aide.table_trail(_lines(text), aide._OUTCOME_TARGETS)
    assert t.key == "FPR ≤ 0.10 — on held-out GT"
    assert t.body == "measured 0.08 on 2026-10-12"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
"""


def _run(cmd, cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def _git_out(args, repo: Path) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True,
                          capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


def _repo(tmp_path: Path, text: str, git: bool = False) -> Path:
    repo = tmp_path / "repo"
    d = repo / "docs" / "aide"
    d.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (d / "progress.md").write_text(text, encoding="utf-8")
    if git:
        _run(["git", "init", "-b", "main"], repo)
        _run(["git", "config", "user.email", "t@e.com"], repo)
        _run(["git", "config", "user.name", "T"], repo)
        _run(["git", "add", "-A"], repo)
        _run(["git", "commit", "-m", "init"], repo)
    return repo
