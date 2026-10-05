"""Tests for `## Human gates` — a decision only a person can make, blocking work.

Kept separate from acceptance boxes deliberately: conventions.md §1 defines
those as observable checks *of the built thing*, which a steering decision is
not. Same reasoning that gave Outcome targets their own table.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_gates", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


def _progress(rows: str, stage_status: str = "🚧") -> str:
    return f"""\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | {stage_status} |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | {stage_status} |

## Human gates

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
{rows}

## Stage 1 — Rules — {stage_status}

**Deliverables.**
- 📋 A. *(Item 027)*
- 📋 B. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""


AWAITING = "| Golden retirement approved | 028 | ⏳ Awaiting | — |"
APPROVED = "| Golden retirement approved | 028 | ✅ Approved (2026-08-18) | ok |"
ALL = "| Real segmenter output arrived | all | ⏳ Awaiting | — |"
STAGE = "| Stage-1 direction approved | stage 1 | ⏳ Awaiting | — |"


def _lines(rows: str):
    return _progress(rows).splitlines()


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #
def test_parses_a_gate_row():
    g = aide.human_gates(_lines(AWAITING))[0]
    assert g.text == "Golden retirement approved"
    assert g.blocks == [28] and g.blocks_all is False and g.kind == "awaiting"


def test_bare_numbers_in_blocks_are_parsed():
    """A column headed "Blocks" invites bare numbers. The shared extractor keys
    off the word "Item", so without normalisation this parses as nothing — and
    a gate blocking nothing is a gate that silently does not work."""
    rows = "| G | 106, 110–112 | ⏳ Awaiting | — |"
    assert aide.human_gates(_lines(rows))[0].blocks == [106, 110, 111, 112]


def test_item_reference_form_also_parsed():
    rows = "| G | Items 106, 108 | ⏳ Awaiting | — |"
    assert aide.human_gates(_lines(rows))[0].blocks == [106, 108]


def test_all_is_recognised():
    g = aide.human_gates(_lines(ALL))[0]
    assert g.blocks_all is True and g.blocks == [] and g.stage is None


def test_stage_reach_is_recognised():
    g = aide.human_gates(_lines(STAGE))[0]
    assert g.stage == "1" and g.blocks == [] and g.blocks_all is False


def test_stage_reach_resolves_through_progress_deliverables():
    """A stage gate follows the roadmap: its reach is whatever items that
    stage's deliverables reference, now — not a list frozen when it was
    written, and not whichever queue happens to be live."""
    blocked, everything = aide.gate_blocked_items(_lines(STAGE))
    assert blocked == {27, 28} and everything == []


def test_stage_reach_of_an_unknown_stage_holds_nothing():
    rows = "| G | stage 99 | ⏳ Awaiting | — |"
    blocked, _ = aide.gate_blocked_items(_lines(rows))
    assert blocked == set()


def test_no_table_is_no_gates():
    text = _progress(AWAITING).replace("## Human gates", "## Something else")
    assert aide.human_gates(text.splitlines()) == []


def test_header_and_separator_rows_are_skipped():
    assert len(aide.human_gates(_lines(AWAITING))) == 1


def test_table_ends_at_the_next_heading():
    """A deliverable bullet after the table must not be read as a gate row."""
    assert len(aide.human_gates(_lines(f"{AWAITING}\n{ALL}"))) == 2


# --------------------------------------------------------------------------- #
# resolution semantics
# --------------------------------------------------------------------------- #
def test_approved_gate_is_resolved():
    assert aide.blocking_gates(_lines(APPROVED)) == []


def test_declined_keeps_blocking():
    """A refusal is *resolved* — a person decided — but the decision was "no",
    so releasing the work would run exactly what was refused. Only approval
    opens a gate; the remedy for a decline is to re-plan."""
    rows = "| G | 028 | ❌ Declined (2026-08-18) | keep v0 |"
    pending = aide.blocking_gates(_lines(rows))
    assert len(pending) == 1 and pending[0].kind == "declined"
    blocked, _ = aide.gate_blocked_items(_lines(rows))
    assert blocked == {28}


def test_declined_warning_says_it_still_blocks():
    rows = "| G | 028 | ❌ Declined (2026-08-18) | keep v0 |"
    w = aide.gate_warnings(_lines(rows))[0]
    assert "DECLINED" in w and "still blocks" in w


def _declined(blocks: str) -> str:
    return f"| G | {blocks} | ❌ Declined (2026-09-30) | re-asked as a new gate |"


def _stage_one_spent(rows: str, extra=()):
    """Stage 1 with 027 ✅ and 028 ❌, plus *extra* stages as for
    ``_lines_with_stages``."""
    lines = _lines_with_stages(rows, *extra)
    text = "\n".join(lines).replace("- 📋 A. *(Item 027)*", "- ✅ A. *(Item 027)*") \
        .replace("- 📋 B. *(Item 028)*", "- ❌ B. *(Item 028)*")
    return text.splitlines()


@pytest.mark.parametrize("blocks, extra", [
    ("—", ()),                                   # the issue's repro: names nothing
    ("-", ()),
    ("", ()),
    ("027, 028", ()),                            # items all ✅ or ❌
    ("stage 1", ()),                             # every bullet ✅ or ❌
    ("stage 1–2", ("2:X. *(Item 040)*",)),       # stage 2 withdrawn by its ❌ row
])
def test_a_declined_gate_whose_reach_is_spent_is_silent(blocks, extra):
    """Issue #396: a declined gate whose reach holds nothing open was
    re-planned already — "drop those items or change what the gate asks" has
    nothing to apply to, and no verb closes it, so the warning fired forever.
    Enforcement is untouched: the gate is still a blocking gate."""
    lines = _stage_one_spent(_declined(blocks), extra)
    if extra:
        lines = _withdraw_stage_2(lines)
    assert aide.gate_warnings(lines) == []
    assert len(aide.blocking_gates(lines)) == 1


@pytest.mark.parametrize("blocks, extra", [
    ("027, 028, 029", ()),                       # 029 has no bullet: open
    ("stage 1–2", ("2:X. Nothing queued yet.",)),  # a stage with nothing queued
    ("stage 1–3", ()),                           # stages 2 and 3 not written yet
    ("stage 1+", ()),                            # arms every later stage
    ("all", ()),                                 # holds everything
    ("stage 1–2", ("2:X. *(Item 040)*", "3:Y. *(Item 040)*")),  # 040 still in scope
])
def test_a_declined_gate_that_could_still_hold_work_warns(blocks, extra):
    """Err toward the warning wherever the reach could still hold work: an
    item with no bullet yet, a stage written but unqueued or not written at
    all, and the two forms that cover work nobody has written yet."""
    lines = _stage_one_spent(_declined(blocks), extra)
    if blocks == "stage 1–2" and len(extra) == 2:
        lines = _withdraw_stage_2(lines)
    (w,) = aide.gate_warnings(lines)
    assert "DECLINED" in w and "still blocks" in w


def _withdraw_stage_2(lines):
    return "\n".join(lines).replace(
        "| 1 | Rules | G1 | 🚧 |",
        "| 1 | Rules | G1 | 🚧 |\n| 2 | S2 | G1 | ❌ |").splitlines()


def test_a_declined_range_over_a_withdrawn_stage_with_no_section_is_silent():
    """A stage withdrawn by its ❌ summary row before anyone wrote its section
    holds nothing, and no item can be queued into a withdrawn stage."""
    lines = _withdraw_stage_2(_stage_one_spent(_declined("stage 1–2")))
    assert aide.gate_warnings(lines) == []


def test_a_declined_gate_over_a_withdrawn_stage_holding_live_work_warns():
    """Withdrawal spends a 📋 item only (`spent_by_withdrawal`): a 🚧 one there
    is live work its owner has not dropped, which the gate still holds."""
    lines = _withdraw_stage_2(_stage_one_spent(
        _declined("stage 1–2"), ("2:X. *(Item 040)*",)))
    lines = "\n".join(lines).replace("- 📋 X. *(Item 040)*",
                                      "- 🚧 X. *(Item 040)*").splitlines()
    (w,) = aide.gate_warnings(lines)
    assert "still blocks stage 1–2" in w


@pytest.mark.parametrize("cell", ["stage 3a", "TBD", "stage 1, 2", "everything"])
def test_a_declined_gate_whose_blocks_cell_reads_as_nothing_is_a_typo(cell):
    """Only a deliberately empty cell is a gate holding nothing: a cell with
    words in it that no reader parses must not lose the one signal that it is
    a typo by going silent with the decline."""
    (w,) = aide.gate_warnings(_stage_one_spent(_declined(cell)))
    assert "DECLINED" in w and f"Blocks cell '{cell}' names no item" in w


def test_a_declined_range_with_a_gap_in_it_still_warns():
    """Stage 3 exists and stage 2 does not: the count of stages written
    matches the range's length, and the missing one is still open."""
    lines = _stage_one_spent(_declined("stage 1–2"), ("3:Y. *(Item 050)*",))
    (w,) = aide.gate_warnings(lines)
    assert "still blocks stage 1–2" in w


def test_a_declined_range_over_a_stage_with_no_bullets_still_warns():
    text = "\n".join(_stage_one_spent(_declined("stage 1–2"))) + (
        "\n## Stage 2 — Empty — 📋\n\n**Deliverables.**\n\n_None yet._\n")
    (w,) = aide.gate_warnings(text.splitlines())
    assert "still blocks stage 1–2" in w


def test_a_declined_stage_gate_whose_item_is_open_elsewhere_still_warns():
    """Every bullet of stage 1 is ✅ or ❌, but 028 is 🚧 in stage 3: the gate
    still holds 028 (`gate_stage_items`), so it is not spent."""
    lines = "\n".join(_stage_one_spent(_declined("stage 1"),
                                       ("3:B again. *(Item 028)*",))).replace(
        "- 📋 B again.", "- 🚧 B again.").splitlines()
    (w,) = aide.gate_warnings(lines)
    assert "still blocks stage 1 — holding 1 item(s): 028" in w


def test_a_declined_item_gate_with_one_open_item_still_warns():
    lines = _stage_one_spent(_declined("027, 028")).copy()
    lines = "\n".join(lines).replace("- ✅ A. *(Item 027)*",
                                     "- 🚧 A. *(Item 027)*").splitlines()
    (w,) = aide.gate_warnings(lines)
    assert "still blocks items 027, 028" in w


def test_a_declined_stage_gate_with_one_open_bullet_still_warns():
    """A 📋 bullet with no item marker is not held by the gate today, but the
    stage is not done, and an item queued for it would be."""
    lines = "\n".join(_stage_one_spent(_declined("stage 1"))).replace(
        "- ❌ B. *(Item 028)*", "- ❌ B. *(Item 028)*\n- 📋 C. Not queued yet."
    ).splitlines()
    (w,) = aide.gate_warnings(lines)
    assert "still blocks stage 1" in w


def test_unrecognised_status_stays_unresolved():
    """A typo in the mark must not silently open a gate."""
    rows = "| G | 028 | approved-ish | — |"
    pending = aide.blocking_gates(_lines(rows))
    assert len(pending) == 1 and pending[0].kind is None


def test_gate_blocked_items_splits_named_from_block_everything():
    blocked, everything = aide.gate_blocked_items(_lines(f"{AWAITING}\n{ALL}"))
    assert blocked == {28}
    assert len(everything) == 1


def test_approved_gate_blocks_nothing():
    blocked, everything = aide.gate_blocked_items(_lines(APPROVED))
    assert blocked == set() and everything == []


# --------------------------------------------------------------------------- #
# warnings
# --------------------------------------------------------------------------- #
def test_awaiting_gate_warns_with_its_reach():
    w = aide.gate_warnings(_lines(AWAITING))
    assert len(w) == 1 and "items 028" in w[0]


def test_all_warning_says_all_items():
    assert "all items" in aide.gate_warnings(_lines(ALL))[0]


def test_stage_warning_names_the_stage():
    assert "stage 1" in aide.gate_warnings(_lines(STAGE))[0]


def test_unrecognised_status_warns_about_the_vocabulary():
    rows = "| G | 028 | approved-ish | — |"
    assert "unrecognised status" in aide.gate_warnings(_lines(rows))[0]


def test_resolved_gates_are_silent():
    assert aide.gate_warnings(_lines(APPROVED)) == []


def test_gate_naming_nothing_is_called_out():
    """A gate that blocks nothing is inert; say so rather than look busy."""
    rows = "| G | — | ⏳ Awaiting | — |"
    assert "nothing named" in aide.gate_warnings(_lines(rows))[0]


def test_an_awaiting_gate_quotes_a_blocks_cell_that_names_no_reach():
    """A typo'd cell is quoted, as a declined gate's is; an empty one is not."""
    typo = aide.gate_warnings(_lines("| G | stage 3a | ⏳ Awaiting | — |"))[0]
    empty = aide.gate_warnings(_lines("| G | — | ⏳ Awaiting | — |"))[0]
    assert "Blocks cell 'stage 3a' names no item" in typo
    assert "Blocks cell names no item" in empty


def test_stage_warning_resolves_how_much_the_gate_holds():
    """The reach is computed at check time either way; throwing it away made a
    mis-scoped `stage N` gate invisible until a runner stalled on it — the
    observed case held the very item meant to produce the gate's evidence."""
    w = aide.gate_warnings(_lines(STAGE))[0]
    assert "holding 2 item(s): 027, 028" in w


def test_declined_stage_warning_also_resolves_the_reach():
    rows = "| G | stage 1 | ❌ Declined (2026-08-18) | keep v0 |"
    w = aide.gate_warnings(_lines(rows))[0]
    assert "still blocks" in w and "holding 2 item(s): 027, 028" in w


def test_item_list_warning_needs_no_resolution():
    """An item-list reach already names its items; no breadth suffix is added."""
    w = aide.gate_warnings(_lines(AWAITING))[0]
    assert "items 028" in w and "holding" not in w


def test_breadth_counts_only_items_the_gate_still_holds():
    """A ✅ item has merged and a ❌ one is out — 'holding' either would
    overstate the reach against the enforcement the message mirrors (claim
    blocks neither)."""
    lines = _progress(STAGE).replace("- 📋 A. *(Item 027)*",
                                     "- ✅ A. *(Item 027)*").splitlines()
    w = aide.gate_warnings(lines)[0]
    assert "holding 1 item(s): 028" in w and "027" not in w


def test_breadth_of_an_all_merged_stage_falls_back_to_the_bare_reach():
    lines = _progress(STAGE).replace("📋", "✅").splitlines()
    w = next(x for x in aide.gate_warnings(lines) if "awaiting" in x)
    assert "stage 1" in w and "holding" not in w


@pytest.mark.parametrize("status", ["⏳ Awaiting", "❌ Declined (2026-10-05)"])
def test_breadth_leaves_out_a_planned_item_only_a_withdrawn_stage_holds(status):
    """Issue #409: 040 is 📋 only in stage 2, which its ❌ summary row
    withdraws, so `claim` never offers it — the breadth reads "held" as the
    declined gate's silence does (`spent_by_withdrawal`), on both warnings."""
    lines = _withdraw_stage_2(_lines_with_stages(
        f"| G | stage 1–2 | {status} | — |", "2:X. *(Item 040)*"))
    (w,) = aide.gate_warnings(lines)
    assert "stage 1–2 — holding 2 item(s): 027, 028" in w and "040" not in w


def test_breadth_still_counts_live_work_in_a_withdrawn_stage():
    """Withdrawal spends a 📋 item only: a 🚧 one there is held until its
    owner drops it."""
    lines = _withdraw_stage_2(_lines_with_stages(
        "| G | stage 1–2 | ⏳ Awaiting | — |", "2:X. *(Item 040)*"))
    lines = "\n".join(lines).replace("- 📋 X. *(Item 040)*",
                                      "- 🚧 X. *(Item 040)*").splitlines()
    (w,) = aide.gate_warnings(lines)
    assert "holding 3 item(s): 027, 028, 040" in w


# --------------------------------------------------------------------------- #
# set_gate_status
# --------------------------------------------------------------------------- #
def test_approve_writes_mark_date_and_note():
    out = aide.set_gate_status(_progress(AWAITING), 1, "approved",
                               "reviewed with maintainer", today="2026-08-18")
    row = next(l for l in out.splitlines() if "Golden retirement" in l and "|" in l)
    assert "✅ Approved (2026-08-18)" in row
    assert "reviewed with maintainer" in row
    assert aide.blocking_gates(out.splitlines()) == []


def test_decline_is_recorded_distinctly():
    out = aide.set_gate_status(_progress(AWAITING), 1, "declined", "not now",
                               today="2026-08-18")
    assert "❌ Declined (2026-08-18)" in out
    assert aide.human_gates(out.splitlines())[0].kind == "declined"


def test_out_of_range_index_raises():
    import pytest
    with pytest.raises(ValueError, match="out of range"):
        aide.set_gate_status(_progress(AWAITING), 5, "approved")


def test_missing_table_raises():
    import pytest
    text = _progress(AWAITING).replace("## Human gates", "## Other")
    with pytest.raises(ValueError, match="no '## Human gates' table"):
        aide.set_gate_status(text, 1, "approved")


def test_other_rows_are_untouched():
    out = aide.set_gate_status(_progress(f"{AWAITING}\n{ALL}"), 1, "approved",
                               today="2026-08-18")
    gates = aide.human_gates(out.splitlines())
    assert gates[0].kind == "approved"
    assert gates[1].kind == "awaiting" and gates[1].blocks_all is True


def test_gate_table_does_not_disturb_the_stage_rollup():
    """The gates table sits in progress.md beside the tables the rollup reads;
    it must not be mistaken for one of them."""
    text = _progress(AWAITING)
    statuses = aide._parse_item_status(text.splitlines())[2]
    assert statuses.get(27) == "planned" and statuses.get(28) == "planned"


# --------------------------------------------------------------------------- #
# end to end — claim refuses, gate verb resolves, claim proceeds
# --------------------------------------------------------------------------- #
AIDE_TOML = '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n\n[git]\nmode = "local"\nmain_branch = "main"\nbranch_prefix = "aide/"\n'
QUEUE = "# Demo — Work Queue 003\n\n### Item 027: Alpha\nA.\n\n### Item 028: Beta\nB.\n"


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _repo(tmp_path: Path, rows: str) -> Path:
    repo = tmp_path / "repo"
    d = repo / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (d / "progress.md").write_text(_progress(rows), encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(QUEUE, encoding="utf-8")
    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "t@e.com"], repo)
    _run(["git", "config", "user.name", "T"], repo)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "init"], repo)
    return repo


def test_claim_skips_a_gated_item_and_offers_the_next(tmp_path: Path, capsys):
    """Item-scoped by default: the queue keeps producing work. Only the items
    a gate names wait for it."""
    repo = _repo(tmp_path, AWAITING)          # blocks 028 only
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert "item 027" in capsys.readouterr().out


def test_all_gate_stops_everything(tmp_path: Path, capsys):
    """A decision that could invalidate downstream work must not have the loop
    racing ahead of it."""
    repo = _repo(tmp_path, ALL)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "held by an unresolved human gate" in out
    assert "blocks everything" in out
    assert "item 027" not in out


def test_gate_list_numbers_the_rows(tmp_path: Path, capsys):
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    assert aide.main(["--repo", str(repo), "gate", "list"]) == 0
    out = capsys.readouterr().out
    assert "1. ⏳" in out and "2. ⏳" in out
    assert "2 gate(s), 2 still blocking" in out


def test_approving_an_all_gate_releases_the_queue(tmp_path: Path, capsys):
    repo = _repo(tmp_path, ALL)
    assert aide.main(["--repo", str(repo), "gate", "approve", "1",
                      "--evidence", "data landed", "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert "item 027" in capsys.readouterr().out


def test_gate_check_reports_the_outstanding_gate(tmp_path: Path):
    repo = _repo(tmp_path, AWAITING)
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert any("awaiting a decision" in w for w in warnings)


def test_gate_out_of_range_is_an_error_not_a_noop(tmp_path: Path, capsys):
    repo = _repo(tmp_path, AWAITING)
    assert aide.main(["--repo", str(repo), "gate", "approve", "9", "--no-commit"]) == 2
    assert "out of range" in capsys.readouterr().err


def test_a_queue_branch_does_not_make_an_item_unclaimable(tmp_path: Path, capsys):
    """`aide/queue-027` is a queue branch, not a claim on item 027. The old
    unanchored search read the trailing digits as an item number and marked it
    permanently claimed — the 1.5.0 bug class, at the one call site that sweep
    missed."""
    repo = _repo(tmp_path, "| G | 999 | ⏳ Awaiting | — |")   # gate blocks nothing real
    _run(["git", "switch", "-c", "aide/queue-027"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert "item 027" in capsys.readouterr().out


def test_a_real_claim_branch_still_marks_its_item_claimed(tmp_path: Path, capsys):
    repo = _repo(tmp_path, "| G | 999 | ⏳ Awaiting | — |")
    _run(["git", "switch", "-c", "aide/027-alpha"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "item 028" in out and "item 027" not in out


def test_gate_approve_without_a_number_reports_rather_than_crashing(tmp_path: Path, capsys):
    repo = _repo(tmp_path, AWAITING)
    assert aide.main(["--repo", str(repo), "gate", "approve", "--no-commit"]) == 2
    assert "needs a gate number" in capsys.readouterr().err


def test_none_left_is_not_blamed_on_an_unrelated_gate(tmp_path: Path, capsys):
    """A gate holding items that are not in play is not why this run found no
    work. Blaming it is a false explanation — worse than none, and exactly the
    'true about one ground, read as true of the repo' failure gates exist to
    remove."""
    repo = _repo(tmp_path, "| Unrelated | 999 | ⏳ Awaiting | — |")
    # Both queue items already claimed, so the empty result has nothing to do
    # with the gate.
    _run(["git", "switch", "-c", "aide/027-alpha"], repo)
    _run(["git", "switch", "-c", "aide/028-beta"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "none left" in out
    assert "human gate" not in out


def test_none_left_names_only_the_gates_that_apply(tmp_path: Path, capsys):
    repo = _repo(tmp_path, "| Unrelated | 999 | ⏳ Awaiting | — |\n"
                           "| Relevant | 027, 028 | ⏳ Awaiting | — |")
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "Relevant" in out and "Unrelated" not in out
    assert "items 027, 028" in out


# --------------------------------------------------------------------------- #
# early ready — the fact the queue-end step keys on (issue #331)
# --------------------------------------------------------------------------- #
def _early_repo(tmp_path: Path, rows: str, *, done=(), deps=None) -> Path:
    """`_repo`, with the named deliverables ✅ and item specs naming *deps*."""
    repo = _repo(tmp_path, rows)
    ppath = repo / "docs" / "aide" / "progress.md"
    text = ppath.read_text(encoding="utf-8")
    for letter, num in (("A", 27), ("B", 28)):
        if num in done:
            text = text.replace(f"- 📋 {letter}. *(Item {num:03d})*",
                                f"- ✅ {letter}. *(Item {num:03d})*")
    ppath.write_text(text, encoding="utf-8")
    items = repo / "docs" / "aide" / "items"
    items.mkdir(exist_ok=True)
    for num, dep in (deps or {}).items():
        (items / f"{num:03d}-x.md").write_text(
            f"# Item {num:03d} — X\n\n## Dependencies\n- Item {dep:03d}.\n\n"
            f"## End\n", encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "state", "--allow-empty"], repo)
    return repo


def _early_line(out: str) -> str:
    return [l for l in out.splitlines() if l.startswith("early ready:")][-1]


def test_early_ready_is_yes_when_every_open_item_waits_on_a_gate(
        tmp_path: Path, capsys):
    """027 landed, 028 held by a gate: only a person stands between the queue
    and its end, and there is built work for CI to check meanwhile."""
    repo = _early_repo(tmp_path, AWAITING, done=(27,))
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[-1] == _early_line(out)
    assert _early_line(out).startswith("early ready: yes — ")


def test_an_item_waiting_only_on_a_gated_item_is_held_by_the_gate(
        tmp_path: Path, capsys):
    """028 is not named by the gate, but it waits on 027, which is — so the
    gate is what holds it too."""
    repo = _early_repo(tmp_path, "| G | 027 | ⏳ Awaiting | — |",
                       deps={28: 27})
    ppath = repo / "docs" / "aide" / "progress.md"
    # A third, landed item, so the ✅ clause is not what decides this case.
    ppath.write_text(ppath.read_text(encoding="utf-8").replace(
        "- 📋 B. *(Item 028)*", "- 📋 B. *(Item 028)*\n- ✅ C. *(Item 026)*"),
        encoding="utf-8")
    qpath = repo / "docs" / "aide" / "queue" / "queue-003.md"
    qpath.write_text(QUEUE + "\n### Item 026: Gamma\nC.\n", encoding="utf-8")
    _run(["git", "commit", "-am", "third item"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert _early_line(capsys.readouterr().out).startswith("early ready: yes")


def test_a_queue_end_item_behind_a_gated_item_is_held_by_the_gate(
        tmp_path: Path, capsys):
    """Issue #347: 028 is `Validate stage 1`, with no spec to name 027 — it
    waits on 027 as its queue-mate, and 027 is gated, so the gate is what
    holds the queue's end too."""
    repo = _early_repo(tmp_path, "| G | 027 | ⏳ Awaiting | — |")
    ppath = repo / "docs" / "aide" / "progress.md"
    ppath.write_text(ppath.read_text(encoding="utf-8").replace(
        "- 📋 B. *(Item 028)*", "- 📋 B. *(Item 028)*\n- ✅ C. *(Item 026)*"),
        encoding="utf-8")
    qpath = repo / "docs" / "aide" / "queue" / "queue-003.md"
    qpath.write_text(QUEUE.replace("Item 028: Beta", "Item 028: Validate stage 1: X")
                     + "\n### Item 026: Gamma\nC.\n", encoding="utf-8")
    _run(["git", "commit", "-am", "queue-end item"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert _early_line(capsys.readouterr().out).startswith("early ready: yes")


def test_early_ready_is_no_before_any_item_has_landed(tmp_path: Path, capsys):
    """A queue held whole by its plan gate has nothing built: marking its PR
    ready would ask for a review of a plan as if it were a batch."""
    repo = _early_repo(tmp_path, ALL)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    line = _early_line(capsys.readouterr().out)
    assert line.startswith("early ready: no — ") and "✅" in line


def test_early_ready_is_no_while_an_open_item_is_claimed(tmp_path: Path, capsys):
    """027 in flight beside a gated 028: the queue is still being built."""
    repo = _early_repo(tmp_path, AWAITING)
    _run(["git", "switch", "-c", "aide/027-alpha"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "held by an unresolved human gate" in out
    assert _early_line(out) == ("early ready: no — 027 is claimed, so work is "
                                "still in flight")


def test_early_ready_is_no_when_no_gate_explains_the_hold(tmp_path: Path, capsys):
    """Both items claimed, no gate: the per-item report carries the fact too."""
    repo = _early_repo(tmp_path, "| Unrelated | 999 | ⏳ Awaiting | — |")
    _run(["git", "switch", "-c", "aide/027-alpha"], repo)
    _run(["git", "switch", "-c", "aide/028-beta"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert _early_line(capsys.readouterr().out) == (
        "early ready: no — no gate holds an open item")


def _queue_repo(tmp_path: Path, rows: str, items, deps=None) -> Path:
    """A queue listing *items* — ``(number, icon)`` in queue order — under
    *rows*, with item specs whose Dependencies name *deps* (number -> list)."""
    repo = _repo(tmp_path, rows)
    d = repo / "docs" / "aide"
    bullets = "\n".join(f"- {icon} X{n}. *(Item {n:03d})*" for n, icon in items)
    text = (d / "progress.md").read_text(encoding="utf-8").replace(
        "- 📋 A. *(Item 027)*\n- 📋 B. *(Item 028)*", bullets)
    (d / "progress.md").write_text(text, encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(
        "# Demo — Work Queue 003\n\n" + "".join(
            f"### Item {n:03d}: X{n}\nX.\n\n" for n, _ in items), encoding="utf-8")
    (d / "items").mkdir(exist_ok=True)
    for n, ds in (deps or {}).items():
        named = "\n".join(f"- Item {x:03d}." for x in ds)
        (d / "items" / f"{n:03d}-x.md").write_text(
            f"# Item {n:03d} — X\n\n## Dependencies\n{named}\n\n## End\n",
            encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "queue"], repo)
    return repo


def _claim_out(repo: Path, capsys) -> str:
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    return capsys.readouterr().out


def test_a_chain_listed_before_the_gated_item_it_hangs_off_is_held(
        tmp_path: Path, capsys):
    """027 waits on 028, which waits on 029, which the gate holds — each
    dependent listed before its dependency, so one pass in queue order is not
    enough and the fixed point has to be reached."""
    repo = _queue_repo(tmp_path, "| G | 029 | ⏳ Awaiting | — |",
                       [(26, "✅"), (27, "📋"), (28, "📋"), (29, "📋")],
                       deps={27: [28], 28: [29]})
    assert _early_line(_claim_out(repo, capsys)).startswith("early ready: yes")


def test_a_landed_dependency_does_not_loosen_a_held_item(tmp_path: Path, capsys):
    """028 names 026 (✅) and 027 (gated): only 027 still blocks it."""
    repo = _queue_repo(tmp_path, "| G | 027 | ⏳ Awaiting | — |",
                       [(26, "✅"), (27, "📋"), (28, "📋")], deps={28: [26, 27]})
    assert _early_line(_claim_out(repo, capsys)).startswith("early ready: yes")


def test_a_claimed_gated_item_is_work_in_flight(tmp_path: Path, capsys):
    """A branch on 028 means someone is building it, gate or no gate."""
    repo = _early_repo(tmp_path, AWAITING, done=(27,))
    _run(["git", "switch", "-c", "aide/028-beta"], repo)
    assert _early_line(_claim_out(repo, capsys)) == (
        "early ready: no — 028 is claimed, so work is still in flight")


def test_a_declined_gate_is_no_early_ready(tmp_path: Path, capsys):
    """Declined is a decision already made against the plan, not one pending:
    the held item is re-planned, so the queue is not about to end."""
    repo = _early_repo(tmp_path, "| G | 028 | ❌ Declined (2026-08-18) | keep v0 |",
                       done=(27,))
    out = _claim_out(repo, capsys)
    assert "held by an unresolved human gate" in out
    assert _early_line(out) == ("early ready: no — gate 1 is declined, so the "
                                "plan is re-planned, not shipped")


def test_an_all_gate_over_a_queue_with_nothing_open_says_so(tmp_path: Path, capsys):
    """027 landed, 028 in review, an `all` gate awaiting: nothing is open to
    wait on the gate, so the yes is worded for that rather than claiming
    every open item waits on it."""
    repo = _queue_repo(tmp_path, ALL, [(27, "✅"), (28, "🔍")])
    assert _early_line(_claim_out(repo, capsys)) == (
        "early ready: yes — nothing is left open, a human gate holds the "
        "queue's end, and 1 item(s) are ✅")


def test_an_unpublished_claim_behind_a_gate_exits_1_with_no_early_line(
        tmp_path: Path, capsys):
    """A broken state is not hidden behind a gate: 027's claim never reached
    origin, and the gate report must not read as a normal hold."""
    repo = _repo(tmp_path, AWAITING)
    toml = repo / "aide.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace(
        'mode = "local"', 'mode = "auto-merge"'), encoding="utf-8")
    _run(["git", "commit", "-am", "auto-merge"], repo)
    remote = tmp_path / "origin.git"
    _run(["git", "init", "--bare", "-b", "main", str(remote)], tmp_path)
    _run(["git", "remote", "add", "origin", str(remote)], repo)
    _run(["git", "push", "-u", "origin", "main"], repo)
    _run(["git", "branch", "aide/027-alpha"], repo)       # never pushed
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 1
    out = capsys.readouterr().out
    assert "held by an unresolved human gate" in out
    assert "WHICH ORIGIN HAS NEVER SEEN" in out
    assert "git push -u origin <branch>" in out
    assert "early ready:" not in out


def test_a_note_containing_a_pipe_is_refused():
    """`|` would add a column; a wrong-arity row is skipped by the parser, so a
    still-blocking gate would silently disappear."""
    import pytest
    with pytest.raises(ValueError, match="may not contain"):
        aide.set_gate_status(_progress(AWAITING), 1, "approved", "a | b")


MALFORMED = "| G | 028 | ⏳ Awaiting | note with | a pipe |"


def test_a_malformed_row_is_an_error_instead_of_vanishing():
    """The most dangerous failure this feature can have is a gate that stops
    being read: "a person must decide" silently becomes "nothing is blocking".
    Issue #202: the same rule as every other read table — an error, since the
    row's cells cannot be trusted to say what it blocked."""
    lines = _lines(MALFORMED)
    lineno = lines.index(MALFORMED) + 1
    errors = aide.unreadable_row_errors(lines)
    assert len(errors) == 1
    assert errors[0].startswith(
        f"progress.md:{lineno}: human-gate row has 5 cells, not 4")
    assert "holds every item" in errors[0]
    assert not any("cells, not 4" in w for w in aide.gate_warnings(lines))


def test_a_well_formed_table_produces_no_arity_error():
    assert aide.unreadable_row_errors(_lines(AWAITING)) == []


def test_claim_holds_every_item_behind_an_unreadable_gate_row(tmp_path: Path, capsys):
    """Fail closed, like an unrecognised status: what the row blocks is
    unknown, so any item released could be the one it was written to hold. A
    defect rather than a normal hold, so the exit is 1 and the row is named."""
    repo = _repo(tmp_path, MALFORMED)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 1
    out = capsys.readouterr().out
    assert "item 027" not in out
    assert "human-gate row aide cannot read" in out
    assert "has 5 cells, not 4" in out
    assert "early ready:" not in out


def test_an_unreadable_gate_row_holds_everything_beside_a_readable_gate(
        tmp_path: Path, capsys):
    """A readable gate holding only 028 must not let 027 through while another
    row in the table is unreadable — that row could be the one naming 027."""
    repo = _repo(tmp_path, f"{AWAITING}\n{MALFORMED}")
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 1
    assert "item 027" not in capsys.readouterr().out


def test_gate_list_names_an_unreadable_row_instead_of_reporting_no_table(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, MALFORMED)
    assert aide.main(["--repo", str(repo), "gate", "list"]) == 0
    out = capsys.readouterr().out
    assert "nothing gated" not in out
    assert "has 5 cells, not 4" in out
    assert "0 gate(s), 0 still blocking, 1 unreadable row(s)" in out


def test_a_note_with_a_line_break_is_refused():
    """A newline splits the row across lines, breaking its shape exactly as a
    `|` does — same silent-disappearance risk."""
    import pytest
    with pytest.raises(ValueError, match="line break"):
        aide.set_gate_status(_progress(AWAITING), 1, "approved", "line one\nline two")


def test_a_stage_gate_naming_a_missing_stage_says_it_holds_nothing():
    """Otherwise a typo'd stage number reads as a guarded stage while blocking
    nothing at all — the failure the warning exists to surface."""
    rows = "| G | stage 99 | ⏳ Awaiting | — |"
    w = aide.gate_warnings(_lines(rows))[0]
    assert "holds NOTHING" in w and "check the stage number" in w


def test_a_stage_gate_with_real_items_reports_its_stage_plainly():
    assert "stage 1" in aide.gate_warnings(_lines(STAGE))[0]
    assert "holds NOTHING" not in aide.gate_warnings(_lines(STAGE))[0]


def _lines_with_planned_empty_stage(rows: str):
    """Lines of a document carrying a `📋` Stage 2 whose deliverables name no
    item — the state every stage is in before anything has been queued for it."""
    return (_progress(rows) + """
## Stage 2 — Later — 📋

**Deliverables.**
- 📋 C. Nothing queued for this yet.

**Acceptance.**
- [ ] Later works.
""").splitlines()


def test_a_gate_on_a_real_but_unqueued_stage_is_not_called_a_typo():
    """The primary documented use — raise the gate at planning time, before the
    stage has items. Reporting that as a mistyped stage number is the check
    firing on the feature's own happy path, which teaches the reader to ignore
    it."""
    rows = "| External data approved | stage 2 | ⏳ Awaiting | — |"
    w = aide.gate_warnings(_lines_with_planned_empty_stage(rows))[0]
    assert "holds NOTHING" not in w
    assert "check the stage number" not in w


def test_that_gate_still_says_it_holds_nothing_today():
    """Neutral, but not silent: the gate blocks no item right now and the
    reader should not read `stage 2` as work already held."""
    rows = "| External data approved | stage 2 | ⏳ Awaiting | — |"
    w = aide.gate_warnings(_lines_with_planned_empty_stage(rows))[0]
    assert "no items queued yet" in w
    assert "stage 2" in w


def test_a_missing_stage_is_still_reported_as_a_typo_alongside_a_real_one():
    """Both cases in one document: the check must not have been broadened into
    treating every empty reach as benign."""
    rows = ("| Real one | stage 2 | ⏳ Awaiting | — |\n"
            "| Typo one | stage 99 | ⏳ Awaiting | — |")
    w = aide.gate_warnings(_lines_with_planned_empty_stage(rows))
    assert "no items queued yet" in w[0] and "holds NOTHING" not in w[0]
    assert "holds NOTHING" in w[1] and "check the stage number" in w[1]


def test_zero_padding_does_not_turn_a_real_stage_into_a_typo():
    """`stage_section` matches numerically, so `stage 02` must find `Stage 2` —
    otherwise the padding alone decides whether the author is told they made a
    typo."""
    rows = "| External data approved | stage 02 | ⏳ Awaiting | — |"
    w = aide.gate_warnings(_lines_with_planned_empty_stage(rows))[0]
    assert "holds NOTHING" not in w
    assert "no items queued yet" in w


def test_stage_section_separates_absent_from_empty():
    """The distinction the warning rests on, asserted directly: both stages
    yield no item numbers, and only one of them exists."""
    lines = _lines_with_planned_empty_stage("| G | stage 2 | ⏳ Awaiting | — |")
    assert aide.stage_item_numbers(lines, "2") == []
    assert aide.stage_item_numbers(lines, "99") == []
    assert aide.stage_section(lines, "2") is not None
    assert aide.stage_section(lines, "99") is None


# --------------------------------------------------------------------------- #
# `stage N+` and `stage N–M` — a reach over a run of stages (issue #304)
# --------------------------------------------------------------------------- #
def _lines_with_stages(rows: str, *extra: str):
    """Stage 1 (items 027, 028) plus one extra stage section per *extra*,
    each ``"<number>:<bullet>"``."""
    text = _progress(rows)
    for spec in extra:
        num, bullet = spec.split(":", 1)
        text += (f"\n## Stage {num} — S{num} — 📋\n\n**Deliverables.**\n"
                 f"- 📋 {bullet}\n\n**Acceptance.**\n- [ ] S{num} works.\n")
    return text.splitlines()


def _gate(blocks: str):
    return aide.human_gates(_lines(f"| G | {blocks} | ⏳ Awaiting | — |"))[0]


@pytest.mark.parametrize("cell, rng, reach", [
    ("stage 2+", (2, None), "stage 2+"),
    ("Stages 02 +", (2, None), "stage 2+"),
    ("stage 2–4", (2, 4), "stage 2–4"),
    ("stage 2-4", (2, 4), "stage 2–4"),
    ("STAGES 002 - 04", (2, 4), "stage 2–4"),
    ("stage 3–3", (3, 3), "stage 3"),
    ("stage 03-3", (3, 3), "stage 3"),
    ("stage 4–2", (4, 2), "stage 4–2"),
    ("stage 2", (2, 2), "stage 2"),
])
def test_stage_range_forms_parse_and_print_normalised(cell, rng, reach):
    g = _gate(cell)
    assert g.stage_range == rng and g.reach == reach
    assert g.blocks == [] and g.blocks_all is False


@pytest.mark.parametrize("cell", ["stage 6+", "stage 6-8", "stage 8-6", "stages 6–8"])
def test_a_stage_range_is_never_read_as_item_numbers(cell):
    """`stage 6-8` must not fall through to the item reader and become items
    6–8, nor a reversed range become items 8 and 6."""
    assert _gate(cell).blocks == []


def test_an_open_stage_reach_holds_its_stage_and_every_later_one():
    rows = "| G | stage 2+ | ⏳ Awaiting | — |"
    lines = _lines_with_stages(rows, "2:B. *(Item 040)*", "5:C. *(Item 050)*")
    blocked, everything = aide.gate_blocked_items(lines)
    assert blocked == {40, 50} and everything == []


def test_after_is_by_stage_number_not_document_order():
    """Stage 5 written above stage 2 is still after it; stage 1 written last
    is still before it."""
    text = _progress("| G | stage 2+ | ⏳ Awaiting | — |")
    head, stage1 = text.split("## Stage 1 — Rules", 1)
    lines = (head + "## Stage 5 — S5 — 📋\n\n**Deliverables.**\n- 📋 C. *(Item 050)*\n\n"
             + "## Stage 2 — S2 — 📋\n\n**Deliverables.**\n- 📋 B. *(Item 040)*\n\n"
             + "## Stage 1 — Rules" + stage1).splitlines()
    assert aide.gate_blocked_items(lines)[0] == {40, 50}


def test_a_closed_stage_range_holds_inside_and_releases_outside():
    rows = "| G | stage 1–2 | ⏳ Awaiting | — |"
    lines = _lines_with_stages(rows, "2:B. *(Item 040)*", "3:C. *(Item 050)*")
    assert aide.gate_blocked_items(lines)[0] == {27, 28, 40}


def test_a_reversed_stage_range_holds_nothing():
    lines = _lines_with_stages("| G | stage 2–1 | ⏳ Awaiting | — |", "2:B. *(Item 040)*")
    assert aide.gate_blocked_items(lines)[0] == set()


def test_check_names_a_reversed_range_and_how_to_write_it():
    lines = _lines_with_stages("| G | stage 2–1 | ⏳ Awaiting | — |", "2:B. *(Item 040)*")
    (w,) = aide.gate_warnings(lines)
    assert "reversed range" in w and "holds NOTHING" in w and "stage 1–2" in w


def test_check_names_a_reversed_range_on_a_declined_gate_too():
    (w,) = aide.gate_warnings(_lines("| G | stage 2–1 | ❌ Declined (2026-09-28) | no |"))
    assert "reversed range" in w


def test_an_open_reach_with_no_stage_yet_is_armed_not_a_typo():
    """`stage 9+` before stage 9 is written is the form's purpose."""
    (w,) = aide.gate_warnings(_lines("| G | stage 9+ | ⏳ Awaiting | — |"))
    assert "holds NOTHING" not in w and "check the stage" not in w
    assert "will block" in w and "stage 9+" in w


def test_an_open_reach_over_unqueued_stages_is_armed():
    lines = _lines_with_stages("| G | stage 2+ | ⏳ Awaiting | — |",
                               "2:B. Nothing queued yet.")
    (w,) = aide.gate_warnings(lines)
    assert "no items queued yet" in w and "holds NOTHING" not in w


def test_a_closed_range_naming_no_stage_is_the_typo_warning():
    (w,) = aide.gate_warnings(_lines("| G | stage 7–9 | ⏳ Awaiting | — |"))
    assert "holds NOTHING" in w and "check the stage numbers" in w


def test_a_closed_range_over_real_unqueued_stages_is_armed():
    lines = _lines_with_stages("| G | stage 2–4 | ⏳ Awaiting | — |",
                               "3:B. Nothing queued yet.")
    (w,) = aide.gate_warnings(lines)
    assert "no items queued yet" in w and "holds NOTHING" not in w


def test_check_counts_what_a_stage_range_holds():
    lines = _lines_with_stages("| G | stage 1+ | ⏳ Awaiting | — |", "4:B. *(Item 040)*")
    (w,) = aide.gate_warnings(lines)
    assert "stage 1+ — holding 3 item(s): 027, 028, 040" in w


def test_the_claim_stall_names_a_stage_range_reach(tmp_path: Path, capsys):
    repo = _repo(tmp_path, "| Milestone | stage 1+ | ⏳ Awaiting | — |")
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "blocks stage 1+ — holding 027, 028" in out


def test_a_malformed_row_with_an_empty_first_cell_is_still_reported():
    """`set("") <= set("-: ")` is true, so an empty first cell used to read as a
    separator row and the malformed-row warning never fired — the vanishing
    gate the report exists to catch, hiding inside the report itself."""
    rows = "| | 028 | ⏳ Awaiting | note with | a pipe |"
    assert any("cells, not 4" in e for e in aide.unreadable_row_errors(_lines(rows)))


def test_an_unnamed_but_well_formed_gate_still_blocks():
    """Failing safe: a row with no gate text is odd, but it must not silently
    stop blocking — that is the direction that loses work."""
    rows = "|  | 028 | ⏳ Awaiting | — |"
    blocked, _ = aide.gate_blocked_items(_lines(rows))
    assert blocked == {28}


def test_the_real_separator_row_is_still_ignored():
    assert aide.unreadable_row_errors(_lines(AWAITING)) == []
    assert len(aide.human_gates(_lines(AWAITING))) == 1


def test_resolving_a_gate_does_not_prepend_a_bom(tmp_path: Path):
    """Read tolerantly, write clean — `utf-8-sig` writes the BOM it strips."""
    repo = _repo(tmp_path, "| Pick a schema | Stage 1 | ⏳ Awaiting | |")
    ppath = repo / "docs" / "aide" / "progress.md"
    assert not ppath.read_bytes().startswith(b"\xef\xbb\xbf")
    assert aide.main(["--repo", str(repo), "gate", "approve", "1",
                      "--evidence", "chose X", "--no-commit"]) == 0
    assert not ppath.read_bytes().startswith(b"\xef\xbb\xbf")


def test_a_bom_already_in_the_file_is_stripped_not_preserved(tmp_path: Path):
    """The tolerant read is what removes it; the clean write keeps it removed."""
    repo = _repo(tmp_path, "| Pick a schema | Stage 1 | ⏳ Awaiting | |")
    ppath = repo / "docs" / "aide" / "progress.md"
    ppath.write_bytes(b"\xef\xbb\xbf" + ppath.read_bytes())
    assert aide.main(["--repo", str(repo), "gate", "approve", "1",
                      "--no-commit"]) == 0
    assert not ppath.read_bytes().startswith(b"\xef\xbb\xbf")


# --------------------------------------------------------------------------- #
# gate IDs — the durable handle (issue #293)
# --------------------------------------------------------------------------- #
def _ids(rows: str):
    return aide.gate_ids(aide.human_gates(_lines(rows)))


def test_every_named_gate_has_an_id_of_the_documented_shape():
    [gid] = _ids(AWAITING)
    assert aide.is_gate_id(gid) and len(gid) == len("gate-") + aide.GATE_ID_MIN_HEX


def test_resolving_a_gate_does_not_move_its_id():
    """Status and evidence are what `approve` writes — hashing them would make
    the ID move on the one edit every gate receives."""
    assert _ids(AWAITING) == _ids(APPROVED)


def test_re_planning_the_reach_does_not_move_the_id():
    assert _ids(AWAITING) == _ids("| Golden retirement approved | stage 1 | ⏳ Awaiting | — |")


def test_renumbering_the_rows_does_not_move_the_id():
    """The #293 incident: a merge put another gate above this one."""
    before = _ids(AWAITING)[0]
    after = _ids(f"{ALL}\n{AWAITING}")[1]
    assert before == after


def test_rewrapping_the_gate_cell_is_the_same_gate():
    assert _ids(AWAITING) == _ids("| Golden  retirement approved | 028 | ⏳ Awaiting | — |")


def test_rewording_the_gate_cell_is_a_different_gate():
    assert _ids(AWAITING) != _ids("| Golden retirement signed off | 028 | ⏳ Awaiting | — |")


def test_an_empty_gate_cell_has_no_id():
    assert _ids("| | 028 | ⏳ Awaiting | — |") == [None]


def test_ids_lengthen_only_to_tell_different_gates_apart(monkeypatch):
    """Two Gate cells sharing four hex digits get five; a third that shares
    nothing with them keeps four."""
    gates = [aide.HumanGate(i, t, [], None, False, "awaiting")
             for i, t in enumerate("abc", start=1)]
    fake = {"a": "abcd1" + "0" * 59, "b": "abcd2" + "0" * 59, "c": "ef01" + "0" * 60}
    monkeypatch.setattr(aide, "gate_hash", lambda g: fake[g.text])
    assert aide.gate_ids(gates) == ["gate-abcd1", "gate-abcd2", "gate-ef01"]


def test_two_rows_asking_the_same_question_share_an_id():
    ids = _ids(f"{AWAITING}\n| Golden retirement approved | 027 | ⏳ Awaiting | — |")
    assert ids[0] == ids[1]


def test_index_for_ref_takes_a_position_or_an_id():
    gates = aide.human_gates(_lines(f"{AWAITING}\n{ALL}"))
    ids = aide.gate_ids(gates)
    assert aide.gate_index_for_ref("2", gates) == 2
    assert aide.gate_index_for_ref(ids[1], gates) == 2
    # A longer prefix of the same hash is the same ID.
    full = "gate-" + aide.gate_hash(gates[1])
    assert aide.gate_index_for_ref(full, gates) == 2


def test_index_for_ref_refuses_a_dangling_a_duplicate_and_a_malformed_ref():
    import pytest
    gates = aide.human_gates(_lines(f"{AWAITING}\n| Golden retirement approved | 027 | ⏳ Awaiting | — |"))
    with pytest.raises(ValueError, match="reworded"):
        aide.gate_index_for_ref("gate-0000", gates)
    with pytest.raises(ValueError, match="same question"):
        aide.gate_index_for_ref(aide.gate_ids(gates)[0], gates)
    with pytest.raises(ValueError, match="neither a gate number nor a gate ID"):
        aide.gate_index_for_ref("golden", gates)


def test_gate_list_prints_each_id(tmp_path: Path, capsys):
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    assert aide.main(["--repo", str(repo), "gate", "list"]) == 0
    out = capsys.readouterr().out
    for gid in _ids(f"{AWAITING}\n{ALL}"):
        assert gid in out


def test_approve_by_id_resolves_the_row_it_names(tmp_path: Path, capsys):
    """The ID survives the renumbering a position does not: approving the
    second row by ID writes that row and no other."""
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    gid = _ids(ALL)[0]
    assert aide.main(["--repo", str(repo), "gate", "approve", gid,
                      "--evidence", "data landed", "--no-commit"]) == 0
    assert f"{gid}: approved" in capsys.readouterr().out
    gates = aide.human_gates((repo / "docs/aide/progress.md")
                             .read_text(encoding="utf-8").splitlines())
    assert [g.kind for g in gates] == ["awaiting", "approved"]


def test_approve_by_an_unknown_id_is_an_error_not_a_noop(tmp_path: Path, capsys):
    repo = _repo(tmp_path, AWAITING)
    before = (repo / "docs/aide/progress.md").read_text(encoding="utf-8")
    assert aide.main(["--repo", str(repo), "gate", "approve", "gate-0000",
                      "--no-commit"]) == 2
    assert "no gate gate-0000" in capsys.readouterr().err
    assert (repo / "docs/aide/progress.md").read_text(encoding="utf-8") == before


def test_the_commit_names_the_gate_by_its_id(tmp_path: Path, capsys):
    repo = _repo(tmp_path, AWAITING)
    assert aide.main(["--repo", str(repo), "gate", "approve", "1"]) == 0
    subject = _run(["git", "log", "-1", "--format=%s"], repo).stdout.strip()
    assert subject == f"docs: human {_ids(AWAITING)[0]} approved"


def test_warnings_and_claim_name_the_id(tmp_path: Path, capsys):
    gid = _ids(ALL)[0]
    assert any(gid in w for w in aide.gate_warnings(_lines(ALL)))
    repo = _repo(tmp_path, ALL)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert gid in capsys.readouterr().out


def _cite(repo: Path, text: str) -> None:
    (repo / "docs/aide/items").mkdir(exist_ok=True)
    (repo / "docs/aide/items/027-alpha.md").write_text(text, encoding="utf-8")


def test_check_accepts_a_citation_that_resolves(tmp_path: Path):
    repo = _repo(tmp_path, AWAITING)
    _cite(repo, f"Blocked on {_ids(AWAITING)[0]} until sign-off.\n")
    errors, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert not [e for e in errors if "gate-" in e]
    assert not [w for w in warnings if "by position" in w]


def test_check_errors_on_a_citation_naming_no_gate(tmp_path: Path):
    """The row went, or its question was reworded: the citation names a
    decision no reader can find, which is the silent failure #293 reports."""
    repo = _repo(tmp_path, AWAITING)
    _cite(repo, "Blocked on gate-0000 until sign-off.\n")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert any("items/027-alpha.md:1: gate-0000 names no human gate" in e
               for e in errors)


def test_check_warns_on_a_positional_citation_and_names_the_id(tmp_path: Path):
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    _cite(repo, "Waits on human gate 2.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    [w] = [w for w in warnings if "by position" in w]
    assert "`human gate 2`" in w and _ids(ALL)[0] in w


def test_positional_reading_needs_a_gates_section(tmp_path: Path):
    """With no `## Human gates` table, "gate 3" is some other gate."""
    repo = _repo(tmp_path, AWAITING)
    p = repo / "docs/aide/progress.md"
    text = p.read_text(encoding="utf-8")
    head, _, tail = text.partition("## Human gates")
    p.write_text(head + "## Stage 1" + tail.split("## Stage 1", 1)[1], encoding="utf-8")
    _cite(repo, "Passes quality gate 3.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert not [w for w in warnings if "by position" in w]


def test_a_hyphenated_word_or_a_version_is_not_a_citation():
    line = "the logic-gate-cafe module; gate-beefy; gate 1.2; gate-3fa1x"
    assert not list(aide._GATE_ID_CITATION_RE.finditer(line))
    assert not list(aide._GATE_POSITION_RE.finditer(line))


def _settle(repo: Path, icon: str) -> None:
    """Both of queue-003's items at *icon* in progress.md."""
    p = repo / "docs/aide/progress.md"
    p.write_text(p.read_text(encoding="utf-8").replace("- 📋 ", f"- {icon} "),
                 encoding="utf-8")


def _cite_in_queue(repo: Path, text: str) -> None:
    (repo / "docs/aide/queue/queue-003.md").write_text(QUEUE + text, encoding="utf-8")


@pytest.mark.parametrize("icon", ["✅", "❌", "⏸️", "withdrawn"])
def test_a_record_spec_and_a_done_queue_are_not_warned_about_positions(
        tmp_path: Path, icon: str):
    """§1 never rewrites a merged spec or a finished queue, so the warning
    could never clear (issue #338). `withdrawn` leaves both items 📋 under a
    ❌ Stage summary row: never offered, so records too (issue #393)."""
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    if icon == "withdrawn":
        (repo / "docs/aide/progress.md").write_text(
            _progress(f"{AWAITING}\n{ALL}", "❌"), encoding="utf-8")
    else:
        _settle(repo, icon)
    _cite(repo, "Waits on human gate 2.\n")
    _cite_in_queue(repo, "Waits on gate 1.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert not [w for w in warnings if "by position" in w]


def test_a_live_spec_and_an_open_queue_still_warn_about_positions(tmp_path: Path):
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    _cite(repo, "Waits on human gate 2.\n")
    _cite_in_queue(repo, "Waits on gate 1.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert sorted(w.split(":")[0] for w in warnings if "by position" in w) == [
        "docs/aide/items/027-alpha.md", "docs/aide/queue/queue-003.md"]


def test_a_record_is_still_held_to_gate_ids_that_resolve(tmp_path: Path):
    repo = _repo(tmp_path, AWAITING)
    _settle(repo, "✅")
    _cite(repo, "Blocked on gate-0000 until sign-off.\n")
    _cite_in_queue(repo, "Blocked on gate-0000.\n")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert sorted(e.split(":")[0] for e in errors if "names no human gate" in e) == [
        "docs/aide/items/027-alpha.md", "docs/aide/queue/queue-003.md"]


def test_a_zero_padded_number_is_not_a_gate_position(tmp_path: Path):
    """`gates 041/042` in dependency prose is two item numbers: a gate
    position is never padded (issue #335)."""
    repo = _repo(tmp_path, f"{AWAITING}\n{ALL}")
    _cite(repo, "Depends on 037–039, gates 041/042.\n"
                "Waits on human gate 2.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    [w] = [w for w in warnings if "by position" in w]
    assert w.startswith("docs/aide/items/027-alpha.md:2:")


def test_an_empty_gates_table_reads_no_positions(tmp_path: Path):
    """The progress template ships the section with no rows, so a consumer
    that never raised a gate keeps it — and its "quality gate 2" is not one."""
    repo = _repo(tmp_path, "")
    _cite(repo, "Passes quality gate 2.\n")
    _, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert not [w for w in warnings if "by position" in w]


def test_check_warns_on_an_ambiguous_gate_id(tmp_path: Path, monkeypatch):
    rows = f"{AWAITING}\n{ALL}"
    fake = {"Golden retirement approved": "abcd1" + "0" * 59,
            "Real segmenter output arrived": "abcd2" + "0" * 59}
    monkeypatch.setattr(aide, "gate_hash", lambda g: fake.get(g.text))
    repo = _repo(tmp_path, rows)
    _cite(repo, "Blocked on gate-abcd.\n")
    errors, warnings = aide.run_checks(repo, aide.load_config(repo))
    assert not [e for e in errors if "gate-abcd" in e]
    [w] = [w for w in warnings if "matches more than one human gate" in w]
    assert "gate-abcd1" in w and "gate-abcd2" in w


def test_a_path_a_file_name_or_an_anchor_is_not_a_citation(tmp_path: Path):
    """Each of these would be an error blocking a merge if read as a citation."""
    repo = _repo(tmp_path, AWAITING)
    _cite(repo, "See [it](roadmap.md#gate-2026), notes/gate-0001.md, "
                "https://x.example/gate-cafe, https://x.example/?id=gate-beef "
                "and gate-face/index.\n")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert not [e for e in errors if "names no human gate" in e]
    # A citation at the end of a sentence, or in backticks, still is one.
    assert [m.group("id") for m in aide._GATE_ID_CITATION_RE.finditer(
        "Held by gate-0000. And `gate-0001`, too.")] == ["gate-0000", "gate-0001"]


def test_tests_dir_is_not_swept_for_gate_ids(tmp_path: Path):
    repo = _repo(tmp_path, AWAITING)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_logic.py").write_text(
        'def test_x():\n    assert "gate-0000"\n', encoding="utf-8")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert not [e for e in errors if "gate-0000" in e]


def test_a_citation_of_an_unreadable_row_says_so(tmp_path: Path):
    repo = _repo(tmp_path, "| Golden retirement approved | 028 | ⏳ Awaiting | a | b |")
    _cite(repo, f"Blocked on {_ids(AWAITING)[0]}.\n")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    [e] = [e for e in errors if "names no human gate" in e]
    assert "unreadable gate rows" in e


def test_approve_by_id_without_a_gates_table_names_the_missing_table(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, AWAITING)
    p = repo / "docs/aide/progress.md"
    text = p.read_text(encoding="utf-8")
    head, _, tail = text.partition("## Human gates")
    p.write_text(head + "## Stage 1" + tail.split("## Stage 1", 1)[1], encoding="utf-8")
    assert aide.main(["--repo", str(repo), "gate", "approve", "gate-0000",
                      "--no-commit"]) == 2
    assert "no '## Human gates' table" in capsys.readouterr().err


def test_no_shipped_template_carries_a_gate_citation():
    """A template's guidance survives into a consumer's document unless its
    author deletes it, and every document built from one sits in docs_dir —
    so a `gate-<hex>` example there is a dangling citation, an `aide check`
    error, in every consumer, gate or no gate. Examples use `gate-<hex>`."""
    templates = _MODULE_PATH.parents[1] / "templates"
    found = [(p.name, m.group("id"))
             for p in sorted(templates.glob("*.md"))
             for m in aide._GATE_ID_CITATION_RE.finditer(p.read_text(encoding="utf-8"))]
    assert found == []
