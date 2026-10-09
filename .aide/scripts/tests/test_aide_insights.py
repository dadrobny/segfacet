"""Tests for `aide insights` — add / list / tick / archive over the inbox.

The inbox is the one living document whose contract is *immutability of the
claim*, so the assertions here are mostly about what the verbs must NOT do:
never reword a captured line, never move an open entry out of the live file,
never renumber silently. The pure helpers are exercised directly; the command
layer is driven through `aide.main` in a real git repo, the way a consumer runs
it.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_insights", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


@pytest.fixture(autouse=True)
def _documents_not_the_machine(monkeypatch):
    """`aide check` also errors on what aide.toml needs of this machine and it
    lacks (issue #354) — a repository, `origin`, a runnable test command.
    These tests judge documents in scratch directories, so that half is
    taken out of them; `test_aide_env_report.py` holds it."""
    monkeypatch.setattr(aide, "dependency_errors", lambda repo_root, config: [])

AIDE_TOML = ('[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n\n'
             '[git]\nmode = "local"\nmain_branch = "main"\nbranch_prefix = "aide/"\n')

INBOX = """\
# Insight Inbox

_Entries below, newest last._

- [x] framework — insights.md has no verb *(item 117, 2026-03-04)* → aide-loop #52
  - **2026-03-05** → accepted into wave 3
- [ ] defect — the reach check calls its own happy path a typo *(2026-05-11)*
- [x] knowledge — utf-8-sig is the right default for hand-edited files *(2026-07-02)* → conventions.md
- [ ] gap — nothing exercises an installed engine *(item 118, 2026-08-15)*
"""


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _repo(tmp_path: Path, inbox: str = INBOX) -> Path:
    repo = tmp_path / "repo"
    d = repo / "docs" / "aide"
    d.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (d / "insights.md").write_text(inbox, encoding="utf-8")
    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "t@e.com"], repo)
    _run(["git", "config", "user.name", "T"], repo)
    # Local, before the first commit: the index holds the bytes the files
    # have, whatever the runner's global `core.autocrlf` says (§6 — a test
    # that lost the global config mid-run saw every tracked file "modified").
    _run(["git", "config", "core.autocrlf", "false"], repo)
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "init"], repo)
    return repo


def _inbox(repo: Path) -> str:
    return (repo / "docs" / "aide" / "insights.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# parse_insights
# --------------------------------------------------------------------------- #
def test_parse_reads_every_field():
    entries = aide.parse_insights(INBOX)
    assert [e.ordinal for e in entries] == [1, 2, 3, 4]
    first = entries[0]
    assert (first.ticked, first.type, first.date, first.item) == (
        True, "framework", "2026-03-04", 117)
    assert first.pointer == "aide-loop #52"
    assert first.trail == ["  - **2026-03-05** → accepted into wave 3"]
    assert entries[1].ticked is False and entries[1].item is None


def test_a_trail_line_is_not_mistaken_for_an_entry():
    """Indentation is the only thing separating the two shapes."""
    entries = aide.parse_insights(INBOX)
    assert len(entries) == 4
    assert all("**2026-03-05**" not in e.text for e in entries)


def test_malformed_entry_still_occupies_an_ordinal():
    """Otherwise `list`'s numbers stop matching the file after the first typo."""
    text = INBOX + "- this is not an entry\n- [ ] defect — no provenance at all\n"
    entries = aide.parse_insights(text)
    assert [e.ordinal for e in entries] == [1, 2, 3, 4, 5, 6]
    assert entries[4].type is None and entries[5].type is None


def test_a_claim_containing_parentheses_parses():
    text = "- [ ] gap — the venv (the one aide env builds) is never checked *(2026-08-01)*\n"
    entry = aide.parse_insights(text)[0]
    assert entry.type == "gap" and entry.date == "2026-08-01"
    assert "(the one aide env builds)" in entry.text


# --------------------------------------------------------------------------- #
# tick_insight_text
# --------------------------------------------------------------------------- #
def test_tick_flips_the_box_and_records_where_it_landed():
    out, msg = aide.tick_insight_text(INBOX, 2, "item 121", "2026-08-24")
    line = out.splitlines()[6]
    assert line.startswith("- [x] defect — the reach check calls its own happy path a typo")
    assert line.endswith("*(2026-05-11)* → item 121")
    assert "ticked" in msg


def test_tick_never_touches_the_claim():
    out, _ = aide.tick_insight_text(INBOX, 4, "item 122", "2026-08-24")
    assert "nothing exercises an installed engine *(item 118, 2026-08-15)*" in out
    # And no other entry moved.
    assert aide.parse_insights(out)[1].raw == aide.parse_insights(INBOX)[1].raw


def test_ticking_an_already_ticked_entry_appends_a_dated_trail_line():
    """The second routing is bookkeeping, and bookkeeping is appendable."""
    out, msg = aide.tick_insight_text(INBOX, 1, "resolved in engine 1.17.0", "2026-08-24")
    lines = out.splitlines()
    assert lines[5] == "  - **2026-03-05** → accepted into wave 3"
    assert lines[6] == "  - **2026-08-24** → resolved in engine 1.17.0"
    assert "already ticked" in msg
    # The entry line itself is byte-identical.
    assert lines[4] == INBOX.splitlines()[4]


def test_trail_line_is_appended_newest_last():
    once, _ = aide.tick_insight_text(INBOX, 1, "first", "2026-08-24")
    twice, _ = aide.tick_insight_text(once, 1, "second", "2026-08-25")
    trail = aide.parse_insights(twice)[0].trail
    assert [t.split("→ ")[1] for t in trail] == [
        "accepted into wave 3", "first", "second"]


def test_ticking_an_entry_that_already_has_a_pointer_keeps_it():
    text = "- [ ] gap — a claim routed by hand *(2026-08-01)* → docs/notes.md\n"
    out, msg = aide.tick_insight_text(text, 1, "item 130", "2026-08-24")
    assert out.splitlines()[0].endswith("*(2026-08-01)* → docs/notes.md")
    assert out.splitlines()[0].startswith("- [x]")
    assert out.splitlines()[1] == "  - **2026-08-24** → item 130"
    assert "kept" in msg


def test_tick_rejects_an_ordinal_that_does_not_exist():
    try:
        aide.tick_insight_text(INBOX, 9, "item 121", "2026-08-24")
    except ValueError as exc:
        assert "no entry 9" in str(exc) and "insights list" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_tick_refuses_a_pointer_containing_a_line_break():
    """A break would split one claim into two and renumber everything below."""
    for bad in ("item 121\nnot a claim", "item 121\r- [ ] forged", "a\rb"):
        try:
            aide.tick_insight_text(INBOX, 2, bad, "2026-08-24")
        except ValueError as exc:
            assert "line break" in str(exc)
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")


def test_a_rejected_pointer_leaves_the_file_untouched(tmp_path: Path):
    repo = _repo(tmp_path)
    before = _inbox(repo)
    assert aide.main(["--repo", str(repo), "insights", "tick", "2",
                      "--pointer", "item 121\n- [ ] forged entry",
                      "--no-commit"]) == 1
    assert _inbox(repo) == before
    assert len(aide.parse_insights(_inbox(repo))) == 4


def test_tick_refuses_a_malformed_entry_rather_than_guessing():
    text = "- [ ] defect no separator and no provenance\n"
    try:
        aide.tick_insight_text(text, 1, "item 121", "2026-08-24")
    except ValueError as exc:
        assert "does not parse" in str(exc)
    else:
        raise AssertionError("expected ValueError")


# --------------------------------------------------------------------------- #
# archive_insight_text
# --------------------------------------------------------------------------- #
def test_archive_moves_only_closed_entries_older_than_the_date():
    remaining, moved, _undatable = aide.archive_insight_text(INBOX, "2026-06-01")
    assert list(moved) == ["2026-Q1"]
    assert len(aide.parse_insights(remaining)) == 3
    assert "insights.md has no verb" not in remaining


def test_archive_never_moves_an_open_entry_however_old():
    """The open backlog is the working set; archiving it hides what list exists for."""
    remaining, moved, _undatable = aide.archive_insight_text(INBOX, "2027-01-01")
    kept = aide.parse_insights(remaining)
    assert all(not e.ticked for e in kept)
    assert [e.date for e in kept] == ["2026-05-11", "2026-08-15"]
    assert sum(len(v) for v in moved.values()) == 3  # two entries + one trail line


def test_archive_carries_the_status_trail_with_its_entry():
    _, moved, _undatable = aide.archive_insight_text(INBOX, "2026-06-01")
    assert moved["2026-Q1"] == [
        "- [x] framework — insights.md has no verb *(item 117, 2026-03-04)* → aide-loop #52",
        "  - **2026-03-05** → accepted into wave 3",
    ]


def test_archive_moves_lines_byte_for_byte():
    original = INBOX.splitlines()
    _, moved, _undatable = aide.archive_insight_text(INBOX, "2026-08-01")
    for lines in moved.values():
        for line in lines:
            assert line in original


def test_archive_groups_by_the_entry_quarter():
    _, moved, _undatable = aide.archive_insight_text(INBOX, "2026-08-01")
    assert sorted(moved) == ["2026-Q1", "2026-Q3"]


def test_archive_leaves_no_blank_gap_behind():
    text = "# I\n\n- [x] gap — a *(2026-01-01)*\n\n- [ ] gap — b *(2026-01-02)*\n"
    remaining, _, _undatable = aide.archive_insight_text(text, "2026-01-02")
    assert "\n\n\n" not in remaining
    assert remaining == "# I\n\n- [ ] gap — b *(2026-01-02)*\n"


def test_archive_of_nothing_is_a_no_op():
    remaining, moved, _undatable = aide.archive_insight_text(INBOX, "2026-01-01")
    assert moved == {} and remaining == INBOX


def test_quarter_boundaries():
    assert aide.insight_quarter("2026-01-01") == "2026-Q1"
    assert aide.insight_quarter("2026-03-31") == "2026-Q1"
    assert aide.insight_quarter("2026-04-01") == "2026-Q2"
    assert aide.insight_quarter("2026-12-31") == "2026-Q4"


# --------------------------------------------------------------------------- #
# the command layer
# --------------------------------------------------------------------------- #
def test_list_prints_every_entry_with_its_number(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "1." in out and "4." in out
    assert "4 entries, 2 open" in out


def test_list_open_hides_the_closed_history(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list", "--open"]) == 0
    out = capsys.readouterr().out
    assert "insights.md has no verb" not in out
    assert "the reach check calls its own happy path a typo" in out
    assert "2 shown by the filters given" in out


def test_list_filters_by_type(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list", "--type", "gap"]) == 0
    out = capsys.readouterr().out
    assert "nothing exercises an installed engine" in out
    assert "utf-8-sig" not in out


def test_list_keeps_the_whole_provenance(tmp_path: Path, capsys):
    """Dropping the item ref sends the reader back to the file being replaced."""
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "*(item 117, 2026-03-04)*" in out
    assert "→ aide-loop #52" in out
    assert "*(2026-05-11)*" in out          # no item ref to invent


def test_list_renders_a_malformed_entry_verbatim(tmp_path: Path, capsys):
    """Its fields were never parsed, so none may be shown as if they had been."""
    repo = _repo(tmp_path, INBOX + "- [ ] nonsense\n")
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "    5. ?? - [ ] nonsense" in out


def test_list_rejects_an_unknown_type(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list", "--type", "bug"]) == 2


def test_list_omits_trails_unless_asked(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    assert "accepted into wave 3" not in capsys.readouterr().out
    assert aide.main(["--repo", str(repo), "insights", "list", "--trail"]) == 0
    assert "accepted into wave 3" in capsys.readouterr().out


def test_list_names_malformed_entries_without_hiding_them(tmp_path: Path, capsys):
    repo = _repo(tmp_path, INBOX + "- [ ] nonsense\n")
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "1 malformed" in out and "aide check" in out


def test_tick_writes_and_commits(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "tick", "2",
                      "--pointer", "item 121", "--date", "2026-08-24"]) == 0
    assert "*(2026-05-11)* → item 121" in _inbox(repo)
    log = _run(["git", "log", "-1", "--pretty=%s"], repo).stdout
    iid = aide.insight_ids(aide.parse_insights(INBOX))[1]
    assert f"triage insight {iid}" in log
    assert _run(["git", "status", "--porcelain"], repo).stdout.strip() == ""


def test_tick_no_commit_leaves_the_edit_uncommitted(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "tick", "2",
                      "--pointer", "item 121", "--no-commit"]) == 0
    assert "insights.md" in _run(["git", "status", "--porcelain"], repo).stdout


def test_tick_without_a_pointer_is_refused(tmp_path: Path):
    """A tick that records only 'triage happened' loses what triage decided."""
    repo = _repo(tmp_path)
    before = _inbox(repo)
    assert aide.main(["--repo", str(repo), "insights", "tick", "2", "--no-commit"]) == 2
    assert aide.main(["--repo", str(repo), "insights", "tick", "2",
                      "--pointer", "   ", "--no-commit"]) == 2
    assert _inbox(repo) == before


def test_tick_without_a_number_is_refused(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "tick",
                      "--pointer", "x", "--no-commit"]) == 2


def test_tick_of_a_missing_ordinal_exits_1_and_writes_nothing(tmp_path: Path):
    repo = _repo(tmp_path)
    before = _inbox(repo)
    assert aide.main(["--repo", str(repo), "insights", "tick", "99",
                      "--pointer", "x", "--no-commit"]) == 1
    assert _inbox(repo) == before


def test_archive_is_a_dry_run_by_default(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = _inbox(repo)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-06-01"]) == 0
    assert "dry run" in capsys.readouterr().out
    assert _inbox(repo) == before
    assert not (repo / "docs" / "aide" / "insights").exists()


def test_archive_yes_moves_entries_into_a_quarter_file(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", "--yes", "--no-commit"]) == 0
    q1 = (repo / "docs" / "aide" / "insights" / "archive-2026-Q1.md").read_text(encoding="utf-8")
    q3 = (repo / "docs" / "aide" / "insights" / "archive-2026-Q3.md").read_text(encoding="utf-8")
    assert q1.startswith("# Insight Archive — 2026-Q1")
    assert "insights.md has no verb" in q1
    assert "utf-8-sig" in q3
    live = _inbox(repo)
    assert len(aide.parse_insights(live)) == 2
    assert all(not e.ticked for e in aide.parse_insights(live))


def test_archive_says_the_numbers_have_shifted(tmp_path: Path, capsys):
    """A stale number from a pre-archive `list` is the one way to mis-tick."""
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", "--yes", "--no-commit"]) == 0
    assert "shifted" in capsys.readouterr().out


def test_archive_appends_to_an_existing_quarter_file(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-06-01", "--yes", "--no-commit"]) == 0
    inbox = repo / "docs" / "aide" / "insights.md"
    inbox.write_text(_inbox(repo) + "- [x] gap — later *(2026-02-02)* → x\n",
                     encoding="utf-8")
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-06-01", "--yes", "--no-commit"]) == 0
    q1 = (repo / "docs" / "aide" / "insights" / "archive-2026-Q1.md").read_text(encoding="utf-8")
    assert q1.count("# Insight Archive") == 1
    assert "insights.md has no verb" in q1 and "later" in q1


def test_archive_commits_both_sides_of_the_move(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", "--yes"]) == 0
    assert _run(["git", "status", "--porcelain"], repo).stdout.strip() == ""
    files = _run(["git", "show", "--name-only", "--pretty=", "HEAD"], repo).stdout
    assert "docs/aide/insights.md" in files
    assert "docs/aide/insights/archive-2026-Q1.md" in files


def test_archive_requires_a_well_formed_date(tmp_path: Path):
    repo = _repo(tmp_path)
    for bad in ([], ["--before", "2026-8-1"], ["--before", "yesterday"]):
        assert aide.main(["--repo", str(repo), "insights", "archive", *bad]) == 2


def test_a_missing_inbox_is_reported_not_crashed(tmp_path: Path):
    repo = _repo(tmp_path)
    (repo / "docs" / "aide" / "insights.md").unlink()
    assert aide.main(["--repo", str(repo), "insights", "tick", "1",
                      "--pointer", "x"]) == 2


# --------------------------------------------------------------------------- #
# the two scoping decisions this verb forced
# --------------------------------------------------------------------------- #
def test_archive_paths_are_always_authorised_for_scope():
    """`aide insights archive` is loop bookkeeping, like `aide progress set`."""
    authorised = aide.AuthorisedPaths(may_change=["core/scripts/aide.py"],
                                      asserts_against=[])
    always = tuple(f"docs/aide/{n}" for n in aide._ALWAYS_AUTHORISED)
    unauthorised, _ = aide.scope_findings(
        ["docs/aide/insights.md", "docs/aide/insights/archive-2026-Q3.md",
         "core/scripts/aide.py"], authorised, always)
    assert unauthorised == []


def test_the_archive_wildcard_cannot_reach_further_than_one_file_shape():
    """The one pattern in _ALWAYS_AUTHORISED must not be a subtree hole."""
    authorised = aide.AuthorisedPaths(may_change=[], asserts_against=[])
    always = tuple(f"docs/aide/{n}" for n in aide._ALWAYS_AUTHORISED)
    unauthorised, _ = aide.scope_findings(
        ["docs/aide/insights/archive-2026-Q3/leaked.md",
         "docs/aide/insights/notes.md",
         "docs/aide/items/042-x.md"], authorised, always)
    assert sorted(unauthorised) == ["docs/aide/insights/archive-2026-Q3/leaked.md",
                                    "docs/aide/insights/notes.md",
                                    "docs/aide/items/042-x.md"]


def test_an_archive_is_frozen_and_not_shape_checked(tmp_path: Path):
    """Warning on an immutable claim would name a defect no one may fix."""
    d = tmp_path / "docs" / "aide"
    (d / "insights").mkdir(parents=True)
    (d / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    (d / "insights" / "archive-2026-Q1.md").write_text(
        "# Insight Archive — 2026-Q1\n\n- [x] this shape is long gone\n", encoding="utf-8")
    assert aide.insight_warnings(d) == []


def test_an_unfilled_slot_is_still_an_error_inside_an_archive(tmp_path: Path):
    """Frozen against shape warnings, not against a genuine template residue."""
    d = tmp_path / "docs" / "aide"
    (d / "insights").mkdir(parents=True)
    (d / "insights" / "archive-2026-Q1.md").write_text(
        "# Insight Archive\n\n- [x] gap — {{unfilled}} *(2026-01-01)*\n", encoding="utf-8")
    errors = aide.template_residue_errors(d)
    assert any("archive-2026-Q1.md" in e for e in errors)


# --------------------------------------------------------------------------- #
# provenance — what may stand between "*(" and the date (issue #76)
#
# The reported failure: the shape accepted `item NNN` alone, so two provenances
# the loop produces routinely — `queue-NNN` from planning done before any item
# exists, and `items NNN-NNN` from a finding spanning several — warned forever
# AND could not be archived, because the same pattern is what yields the date
# `archive --before` cuts on. Neither was fixable in place: §1 makes the claim
# immutable, and collapsing a range to one item destroys the provenance the
# marker records. The date is now the only load-bearing part.
# --------------------------------------------------------------------------- #
WIDE = """\
# Insight Inbox

_Entries below, newest last._

- [x] gap — queue planning found no home for this *(queue-014, 2026-07-26)*
- [x] defect — the three specs disagree on the same path *(items 099-101, 2026-07-27)*
- [x] knowledge — provenance can be anything honest *(the 2026 offsite, 2026-07-28)*
- [ ] framework — a bare date is still fine *(2026-07-29)*
"""


def test_a_queue_or_range_provenance_parses_and_keeps_its_date():
    """The date is what `archive` cuts on, so every accepted form must yield one."""
    entries = aide.parse_insights(WIDE)
    assert [e.date for e in entries] == [
        "2026-07-26", "2026-07-27", "2026-07-28", "2026-07-29"]
    assert [e.source for e in entries] == [
        "queue-014", "items 099-101", "the 2026 offsite", None]


def test_only_a_single_item_provenance_yields_an_item_number():
    """A range and a queue name no one item; inventing one would be a guess."""
    assert [e.item for e in aide.parse_insights(WIDE)] == [None, None, None, None]
    assert aide.parse_insights(
        "- [ ] gap — x *(item 099, 2026-07-26)*\n")[0].item == 99


def test_the_claim_survives_a_widened_provenance():
    """Text is still cut at the provenance, not at the first parenthesis."""
    entries = aide.parse_insights(WIDE)
    assert entries[1].text == "the three specs disagree on the same path"
    assert entries[0].ticked is True and entries[3].ticked is False


def test_check_no_longer_warns_on_a_queue_or_multi_item_capture(tmp_path: Path):
    """The reported entries, verbatim: three permanent warnings, now none."""
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "insights.md").write_text(WIDE, encoding="utf-8")
    assert aide.insight_warnings(d) == []


def test_the_date_stays_strict_where_the_provenance_relaxed(tmp_path: Path):
    """Relaxing the slug must not relax the one field every verb depends on."""
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "insights.md").write_text(
        "# I\n\n"
        "- [ ] gap — no date at all *(queue-014)*\n"
        "- [ ] gap — not ISO *(item 099, 26-07-26)*\n"
        "- [ ] gap — a provenance may not span lines *(queue-014,\n"
        "- [ ] nonsense — not a known type *(2026-07-26)*\n",
        encoding="utf-8")
    warnings = aide.insight_warnings(d)
    assert len(warnings) == 4
    assert all("YYYY-MM-DD" in w for w in warnings)


def test_archive_moves_a_queue_or_multi_item_entry():
    """The half of #76 that outlived the warning: pinned in the live file forever."""
    remaining, moved, undatable = aide.archive_insight_text(WIDE, "2026-08-01")
    assert sum(len(v) for v in moved.values()) == 3
    assert undatable == []
    kept = aide.parse_insights(remaining)
    assert [e.text.strip() for e in kept] == ["a bare date is still fine"]


def test_list_reprints_a_range_or_queue_provenance_verbatim(tmp_path: Path, capsys):
    """Re-deriving the provenance from an item number can print back only one form."""
    repo = _repo(tmp_path, WIDE)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "*(queue-014, 2026-07-26)*" in out
    assert "*(items 099-101, 2026-07-27)*" in out
    assert "*(2026-07-29)*" in out


def test_tick_works_on_a_widened_provenance(tmp_path: Path):
    """`tick` refuses what does not parse, so widening must reach it too."""
    repo = _repo(tmp_path, WIDE.replace("- [x] gap —", "- [ ] gap —", 1))
    assert aide.main(["--repo", str(repo), "insights", "tick", "1",
                      "--pointer", "aide-loop #76"]) == 0
    assert "*(queue-014, 2026-07-26)* → aide-loop #76" in _inbox(repo)


# --------------------------------------------------------------------------- #
# an entry no cut can reach is reported, not silently skipped (issue #76)
# --------------------------------------------------------------------------- #
UNDATABLE = """\
# Insight Inbox

- [x] gap — dated and closed *(2026-01-01)*
- [x] this one never parsed at all
"""


def test_archive_returns_the_closed_entries_it_could_not_date():
    _, _, undatable = aide.archive_insight_text(UNDATABLE, "2026-06-01")
    assert [e.ordinal for e in undatable] == [2]


def test_an_open_undated_entry_is_not_reported_as_unarchivable():
    """An open entry never moves anyway; naming it would be noise, not a finding."""
    _, _, undatable = aide.archive_insight_text(
        UNDATABLE.replace("- [x] this one", "- [ ] this one"), "2026-06-01")
    assert undatable == []


def test_archive_names_the_entry_it_had_to_leave_behind(tmp_path: Path, capsys):
    repo = _repo(tmp_path, UNDATABLE)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-06-01"]) == 0
    err = capsys.readouterr().err
    assert "entry 2" in err and "insights.md:4" in err
    assert "1 closed entry could not be dated" in err


def test_the_report_survives_a_run_where_nothing_moved(tmp_path: Path, capsys):
    """The run that most needs it: the live file will not shrink and says why."""
    repo = _repo(tmp_path, UNDATABLE)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2020-01-01"]) == 0
    captured = capsys.readouterr()
    assert "nothing closed before 2020-01-01" in captured.out
    assert "could not be dated" in captured.err


# --------------------------------------------------------------------------- #
# which marker is the provenance, when a line carries more than one
#
# A free-form provenance means an aside inside the claim can wear the marker's
# shape. Position alone cannot decide it: the first match takes the claim's
# aside, the last takes the pointer's. The rule is the marker that leaves a
# well-formed tail — nothing, or the `→` pointer.
# --------------------------------------------------------------------------- #
def test_an_aside_inside_the_claim_does_not_steal_the_provenance():
    """Taking the aside's date would file the entry in the wrong quarter, silently."""
    line = ("- [ ] defect — config default is *(prod, 2020-01-01)* not "
            "*(item 099, 2026-07-26)*\n")
    e = aide.parse_insights(line)[0]
    assert (e.source, e.date, e.item) == ("item 099", "2026-07-26", 99)
    assert e.text == "config default is *(prod, 2020-01-01)* not"


def test_an_aside_inside_the_pointer_does_not_steal_it_either():
    """The symmetric case, which taking the *last* marker would get wrong."""
    line = "- [x] gap — a *(item 099, 2026-07-26)* → see *(note, 2026-08-01)*\n"
    e = aide.parse_insights(line)[0]
    assert (e.source, e.date) == ("item 099", "2026-07-26")
    assert e.pointer == "see *(note, 2026-08-01)*"


def test_an_aside_that_would_be_archived_to_the_wrong_quarter_is_not():
    """The consequence the parse rule exists to prevent, through the verb itself."""
    text = ("- [x] defect — was *(prod, 2020-01-01)* now *(item 099, 2026-07-26)*\n")
    _, moved, _u = aide.archive_insight_text(text, "2026-08-01")
    assert list(moved) == ["2026-Q3"]          # not 2020-Q1


def test_a_hand_written_tail_still_parses_as_it_always_did():
    """Entries predating `tick` carry tails that are neither empty nor a pointer."""
    e = aide.parse_insights("- [x] gap — a *(2026-01-01)* — landed in X\n")[0]
    assert (e.date, e.pointer) == ("2026-01-01", None)


def test_a_blank_provenance_is_still_a_shape_warning(tmp_path: Path):
    """Free-form is not empty: a stray comma says nothing and should be fixed."""
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "insights.md").write_text(
        "# I\n\n- [ ] gap — a stray comma *(   , 2026-01-01)*\n", encoding="utf-8")
    assert len(aide.insight_warnings(d)) == 1
    assert aide.parse_insights("- [ ] gap — a *(   , 2026-01-01)*\n")[0].date is None


def test_the_patterns_do_not_backtrack_catastrophically():
    """Both are run over every bullet in the file, malformed ones included."""
    import time
    evil = "- [ ] gap — " + "a(" * 4000 + " *(item 1, 2026-01-01)*"
    start = time.time()
    aide.parse_insights(evil)
    assert time.time() - start < 1.0


# --------------------------------------------------------------------------- #
# the engine version an insight was observed under (issue #97)
#
# The reported failure: an entry records where a finding came from and when,
# never *which engine it was seen on* — and the value is sitting on disk as
# `.aide/VERSION` at capture time. The date cannot proxy for it, so eight
# framework issues that landed upstream across an engine restructure could not
# be placed on either side of it, and every older-engine claim was re-verified
# by hand. The version is conventional, not grammatical: what the CLI must do
# is accept it, parse it, and print it back — never warn about it.
# --------------------------------------------------------------------------- #
VERSIONED = """\
# Insight Inbox

_Entries below, newest last._

- [ ] framework — the reach check has no engine version *(item 042, 2026-08-29, engine 1.22.0)*
- [x] defect — captured before the convention existed *(item 041, 2026-08-01)*
- [ ] knowledge — a bare date takes one too *(2026-08-29, engine 1.22.0)*
"""


def test_a_versioned_entry_passes_the_shape_check_clean(tmp_path: Path):
    """A warning on a captured line can never be cleared, so this is the
    load-bearing assertion of the pair: the new component must not produce
    permanent noise on a well-formed entry."""
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "insights.md").write_text(VERSIONED, encoding="utf-8")
    assert aide.insight_warnings(d) == []


def test_the_version_is_parsed_out_and_does_not_disturb_the_other_fields():
    """`note` is a field of its own; the date, provenance and item number are
    read exactly as they were before it existed."""
    entries = aide.parse_insights(VERSIONED)
    assert [e.note for e in entries] == ["engine 1.22.0", None, "engine 1.22.0"]
    assert [e.date for e in entries] == ["2026-08-29", "2026-08-01", "2026-08-29"]
    assert [e.source for e in entries] == ["item 042", "item 041", None]
    assert [e.item for e in entries] == [42, 41, None]
    assert entries[0].text == "the reach check has no engine version"


def test_the_version_is_free_form_not_a_grammar():
    """Enumerating the accepted spelling would reject an honest capture
    permanently — the claim line is immutable. Same argument as the provenance
    (issue #76), and sharper here, since entries predate the convention."""
    e = aide.parse_insights(
        "- [ ] gap — a *(item 1, 2026-01-01, engine 1.22.0-rc1 on windows)*\n")[0]
    assert (e.date, e.note) == ("2026-01-01", "engine 1.22.0-rc1 on windows")


def test_an_entry_captured_without_a_version_is_untouched():
    """The convention is never retrofitted, so the un-versioned entry must keep
    parsing exactly as it did — `note` is None, not an invented value."""
    entries = aide.parse_insights(INBOX)
    assert [e.note for e in entries] == [None, None, None, None]


def test_list_reprints_the_engine_version(tmp_path: Path, capsys):
    """Triage reads the listing, not the file (the feedback-loop skill says so),
    so a version the listing drops is a version triage cannot carry into the
    issue it files."""
    repo = _repo(tmp_path, VERSIONED)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    assert "*(item 042, 2026-08-29, engine 1.22.0)*" in out
    assert "*(2026-08-29, engine 1.22.0)*" in out
    assert "*(item 041, 2026-08-01)*" in out


def test_tick_and_archive_reach_a_versioned_entry(tmp_path: Path):
    """The date is still what `archive` cuts on, and `tick` still refuses only
    what does not parse — widening the marker must cost neither verb its entry."""
    repo = _repo(tmp_path, VERSIONED)
    assert aide.main(["--repo", str(repo), "insights", "tick", "1",
                      "--pointer", "aide-loop #97"]) == 0
    assert ("*(item 042, 2026-08-29, engine 1.22.0)* → aide-loop #97"
            in _inbox(repo))
    _, moved, undatable = aide.archive_insight_text(VERSIONED, "2026-08-15")
    assert list(moved) == ["2026-Q3"] and undatable == []


def test_the_date_stays_strict_with_a_version_after_it(tmp_path: Path):
    """The one field every verb depends on did not relax on its right either."""
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "insights.md").write_text(
        "# I\n\n"
        "- [ ] gap — no date, only a version *(item 1, engine 1.22.0)*\n"
        "- [ ] gap — not ISO *(item 1, 26-08-29, engine 1.22.0)*\n"
        "- [ ] gap — an empty trailer says nothing *(item 1, 2026-08-29,  )*\n",
        encoding="utf-8")
    assert len(aide.insight_warnings(d)) == 3


# --------------------------------------------------------------------------- #
# the engine guarantees the inbox exists (issue #85)
# --------------------------------------------------------------------------- #
_TEMPLATE = Path(__file__).resolve().parents[2] / "templates" / "insights.md"

#: The least progress.md `check` passes on, so the verb reaches its exit code
#: for the document set's own reasons and not for a fixture's.
_PROGRESS = "# P\n\n| 1 | S | G | 📋 |\n\n| G1 | O | 📋 |\n\n## Stage 1 — S — 📋\n"


def _loop_repo_without_inbox(tmp_path: Path) -> Path:
    repo = _repo(tmp_path)
    (repo / "docs" / "aide" / "progress.md").write_text(_PROGRESS, encoding="utf-8")
    (repo / "docs" / "aide" / "insights.md").unlink()
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "a document set with no inbox yet"], repo)
    return repo


def _cli_only_repo(tmp_path: Path) -> Path:
    """A repo that adopted the CLI and not the loop: aide.toml, no docs_dir."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    return repo


def _clean(repo: Path) -> bool:
    return _run(["git", "status", "--porcelain"], repo).stdout.strip() == ""


def _status(repo: Path) -> list:
    return _run(["git", "status", "--porcelain"], repo).stdout.splitlines()


def _staged(repo: Path) -> list:
    return _run(["git", "diff", "--cached", "--name-only"], repo).stdout.split()


def _assert_untracked_only(repo: Path, rel: str = "docs/aide/insights.md") -> None:
    """*rel* is untracked and nothing at all is staged — asserted on the file's
    own status line, not on the whole porcelain list, which may carry lines
    that are the runner's business (line endings) and not this test's."""
    status = _status(repo)
    assert f"?? {rel}" in status, status
    assert _staged(repo) == [], _staged(repo)


def _files_in_head(repo: Path) -> list:
    """What HEAD's commit touches — posix paths, one per line as git prints
    them (never whitespace-split: a path may carry a space)."""
    out = _run(["git", "-c", "core.quotepath=false", "show", "--name-only",
                "--format=", "HEAD"], repo).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def _head(repo: Path) -> str:
    return _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()


def _without_git_identity(repo: Path, monkeypatch, tmp_path: Path) -> None:
    """A fresh clone before `git config user.name`: the commit is refused."""
    for key in ("user.name", "user.email"):
        _run(["git", "config", "--unset", key], repo)
    nowhere = tmp_path / "no-such-gitconfig"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(nowhere))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(nowhere))
    monkeypatch.setenv("HOME", str(tmp_path / "no-such-home"))
    for var in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME",
                "GIT_COMMITTER_EMAIL", "EMAIL"):
        monkeypatch.delenv(var, raising=False)


def test_the_template_is_where_the_engine_looks_for_it():
    """Every test below compares against this file; if the layout moves, this
    is the one that fails with a reason instead of the rest with a mystery."""
    assert _TEMPLATE.is_file()
    assert aide._TEMPLATES_DIR == _TEMPLATE.parent
    assert b"insight" in _TEMPLATE.read_bytes().lower()


def test_check_creates_a_missing_inbox_byte_for_byte(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert (repo / "docs" / "aide" / "insights.md").read_bytes() == _TEMPLATE.read_bytes()


def test_check_commits_the_inbox_it_created_and_nothing_else(tmp_path: Path):
    """`aide sync` refuses a dirty tree; a creation left untracked would stall
    the next preflight of the loop it exists to serve. The commit's CONTENTS
    are the assertion — "a commit happened" and "tree clean" were both true
    of a commit that had swept a builder's staged work in with the inbox."""
    repo = _loop_repo_without_inbox(tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert _clean(repo)
    subject = _run(["git", "log", "-1", "--format=%s"], repo).stdout.strip()
    assert subject.startswith("docs(aide):")
    assert _files_in_head(repo) == ["docs/aide/insights.md"]


def test_the_inbox_commit_leaves_staged_work_staged_and_out_of_it(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    (repo / "feature.py").write_text("x = 1\n", encoding="utf-8")
    _run(["git", "add", "feature.py"], repo)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert _files_in_head(repo) == ["docs/aide/insights.md"]
    assert _staged(repo) == ["feature.py"]
    assert not any("insights.md" in line for line in _status(repo))


def test_a_commit_git_refuses_leaves_the_inbox_untracked_not_staged(
        tmp_path: Path, monkeypatch, capsys):
    """A staged-but-uncommitted inbox stalls `aide sync` exactly as an
    untracked one does, with no message saying why. Untracked, plus a notice
    that names the refusal, is the honest degradation."""
    repo = _loop_repo_without_inbox(tmp_path)
    before = _head(repo)
    _without_git_identity(repo, monkeypatch, tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert _head(repo) == before
    _assert_untracked_only(repo)
    out = capsys.readouterr().out
    notice = [l for l in out.splitlines() if l.startswith("notice:")]
    assert len(notice) == 1 and "NOT committed" in notice[0]


def test_git_off_path_degrades_to_created_not_committed(
        tmp_path: Path, monkeypatch, capsys):
    """`check` ran in a repo with no usable `git` before 1.26.0 and must still:
    the creation happens, the commit is a reason in the notice, no traceback."""
    repo = _loop_repo_without_inbox(tmp_path)
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert (repo / "docs" / "aide" / "insights.md").read_bytes() == _TEMPLATE.read_bytes()
    notice = [l for l in capsys.readouterr().out.splitlines() if l.startswith("notice:")]
    assert len(notice) == 1 and "NOT committed" in notice[0]
    monkeypatch.undo()
    _assert_untracked_only(repo)


def test_a_detached_head_gets_the_file_and_no_dangling_commit(
        tmp_path: Path, monkeypatch, capsys):
    repo = _loop_repo_without_inbox(tmp_path)
    before = _head(repo)
    _run(["git", "checkout", "--quiet", "--detach"], repo)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert _head(repo) == before
    _assert_untracked_only(repo)
    notice = [l for l in capsys.readouterr().out.splitlines() if l.startswith("notice:")]
    assert len(notice) == 1 and "detached" in notice[0]


def test_check_says_it_created_the_inbox(tmp_path: Path, capsys):
    repo = _loop_repo_without_inbox(tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    out = capsys.readouterr().out
    notice = [l for l in out.splitlines() if l.startswith("notice:")]
    assert len(notice) == 1 and "docs/aide/insights.md" in notice[0]
    assert "aide check: OK" in out


def test_check_is_silent_about_the_inbox_once_it_exists(tmp_path: Path, capsys):
    repo = _loop_repo_without_inbox(tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert "notice:" not in capsys.readouterr().out


def test_check_never_overwrites_an_existing_inbox_even_a_malformed_one(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    inbox = repo / "docs" / "aide" / "insights.md"
    inbox.write_bytes(b"- [ ] not a shape the parser knows\n")
    assert aide.main(["--repo", str(repo), "check"]) == 0  # a shape *warning*
    assert inbox.read_bytes() == b"- [ ] not a shape the parser knows\n"


def test_check_creates_nothing_in_a_repo_with_no_document_set(tmp_path: Path):
    repo = _cli_only_repo(tmp_path)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert not (repo / "docs").exists()


def test_the_helper_reports_what_it_did(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    config = aide.load_config(repo)
    created = aide.ensure_insights_inbox(repo, config, verb="test")
    assert created == repo / "docs" / "aide" / "insights.md"
    assert aide.ensure_insights_inbox(repo, config, verb="test") is None
    assert aide.ensure_insights_inbox(_cli_only_repo(tmp_path / "other"),
                                      config, verb="test") is None


def test_a_missing_template_is_reported_not_crashed(tmp_path: Path, monkeypatch, capsys):
    """An install that lost `.aide/templates/` is incomplete, not broken here:
    the gate still runs, still exits on the document set's merits, and says
    which file it could not create and why."""
    repo = _loop_repo_without_inbox(tmp_path)
    monkeypatch.setattr(aide, "_TEMPLATES_DIR", tmp_path / "nowhere")
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert not (repo / "docs" / "aide" / "insights.md").exists()
    err = capsys.readouterr().err
    assert "insights.md" in err and "install" in err


def test_list_on_a_missing_inbox_creates_it_and_reports_an_empty_backlog(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    inbox = repo / "docs" / "aide" / "insights.md"
    inbox.unlink()
    _run(["git", "commit", "-am", "drop the inbox"], repo)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    assert inbox.read_bytes() == _TEMPLATE.read_bytes()
    assert _clean(repo)
    out = capsys.readouterr().out
    assert "notice:" in out and "0 entries, 0 open" in out


def test_list_no_commit_leaves_the_created_inbox_uncommitted(tmp_path: Path):
    repo = _repo(tmp_path)
    inbox = repo / "docs" / "aide" / "insights.md"
    inbox.unlink()
    _run(["git", "commit", "-am", "drop the inbox"], repo)
    assert aide.main(["--repo", str(repo), "insights", "list", "--no-commit"]) == 0
    assert inbox.is_file() and not _clean(repo)


def test_list_with_no_document_set_creates_nothing(tmp_path: Path):
    repo = _cli_only_repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 2
    assert not (repo / "docs").exists()


def test_tick_and_archive_on_a_missing_inbox_point_at_check(tmp_path: Path, capsys):
    """Neither can act on a file that is not there, and the way to get one is
    a verb now — not the hand copy the old message prescribed."""
    repo = _repo(tmp_path)
    (repo / "docs" / "aide" / "insights.md").unlink()
    for verb in (["tick", "1", "--pointer", "x"], ["archive", "--before", "2026-01-01"]):
        assert aide.main(["--repo", str(repo), "insights", *verb]) == 2
        err = capsys.readouterr().err
        assert "aide check" in err and "templates" not in err
    assert not (repo / "docs" / "aide" / "insights.md").exists()


def test_a_docs_dir_with_a_space_is_recognised_in_its_own_commit(
        tmp_path: Path, capsys):
    """The committed-path check tokenised `git show` output on whitespace, so
    `my docs/aide/insights.md` never matched itself and the notice said "NOT
    committed" about a file that was in the commit."""
    repo = _repo(tmp_path)
    ddir = repo / "my docs" / "aide"
    ddir.mkdir(parents=True)
    (ddir / "progress.md").write_text(_PROGRESS, encoding="utf-8")
    toml = AIDE_TOML.replace('docs_dir = "docs/aide"', 'docs_dir = "my docs/aide"')
    assert "my docs" in toml  # the substitution took
    (repo / "aide.toml").write_text(toml, encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "a docs_dir with a space"], repo)
    assert aide.main(["--repo", str(repo), "check"]) == 0
    inbox = ddir / "insights.md"
    assert inbox.read_bytes() == _TEMPLATE.read_bytes()
    assert _files_in_head(repo) == [inbox.relative_to(repo).as_posix()]
    notice = [l for l in capsys.readouterr().out.splitlines() if l.startswith("notice:")]
    assert len(notice) == 1 and "and committed it" in notice[0]


def test_the_shared_committer_is_loud_when_git_cannot_run(
        tmp_path: Path, monkeypatch, capsys):
    """A git that cannot be run is a reason, printed by the committer itself
    and never a traceback; `tick` then exits 1 with the inbox as it was, so a
    re-run makes the tick rather than reading it as made (issue #309)."""
    repo = _repo(tmp_path)
    empty = tmp_path / "empty-path"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    why = aide._commit_docs_files(repo, aide.load_config(repo), "m",
                                  ["docs/aide/insights.md"])
    assert why and "git could not be run" in why
    assert "could not commit docs/aide/insights.md" in capsys.readouterr().err
    # Through the verb, git's absence is met before the commit: one sentence
    # naming it, the edit put back first (issue #352).
    assert aide.main(["--repo", str(repo), "insights", "tick", "2",
                      "--pointer", "item 003"]) == 1
    err = capsys.readouterr().err
    assert "aide insights: git is not on PATH" in err and "Traceback" not in err
    monkeypatch.undo()
    assert "- [x] defect" not in _inbox(repo)  # the edit was put back ...
    assert "insights.md" not in _status(repo)  # ... byte for byte
    assert _staged(repo) == []


# --------------------------------------------------------------------------- #
# insights resolve — the parser, the union, and the refusals
# --------------------------------------------------------------------------- #
_HEAD = "# Insight Inbox\n\n_Entries below, newest last._\n\n"
_A = "- [ ] framework — a is a *(item 1, 2026-01-01)*"
_B = "- [ ] defect — b is b *(2026-01-02)*"
_C = "- [ ] gap — c from ours *(2026-02-01)*"
_D = "- [ ] knowledge — d from theirs *(2026-02-02)*"
_SHARED = _HEAD + _A + "\n" + _B + "\n"


def _conflicted(ours: str, theirs: str, common: str = _SHARED) -> str:
    return (f"{common}<<<<<<< HEAD\n{ours}=======\n{theirs}"
            f">>>>>>> other-branch\n")


def _resolve(text, base=None, date="2026-03-01"):
    return aide.resolve_insights_text(text, date, base)


def test_resolve_keeps_every_entry_id():
    """The ID survives the merge a position does not: theirs lands after ours."""
    text = _conflicted(_C + "\n", _D + "\n")
    ours, theirs, _ = aide.split_conflict_sides(text)
    before = set(aide.insight_ids(aide.parse_insights(ours))
                 + aide.insight_ids(aide.parse_insights(theirs)))
    merged, _, refusals = _resolve(text)
    assert refusals == []
    assert set(aide.insight_ids(aide.parse_insights(merged))) == before


def test_split_reconstructs_each_side_as_a_whole_document():
    """Positional ordinals are the identity every insight verb takes, so a side
    read as a hunk alone has no idea which entry it starts at."""
    ours, theirs, blocks = aide.split_conflict_sides(
        _conflicted(_C + "\n", _D + "\n"))
    assert blocks == 1
    assert ours == _SHARED + _C + "\n"
    assert theirs == _SHARED + _D + "\n"


def test_split_discards_the_diff3_merge_base_section():
    """Under `merge.conflictStyle = diff3` the base belongs to neither side;
    appending it to both would duplicate every entry the merge base had."""
    text = (f"{_SHARED}<<<<<<< HEAD\n{_C}\n||||||| merged common ancestors\n"
            f"{_A}\n=======\n{_D}\n>>>>>>> other-branch\n")
    ours, theirs, _ = aide.split_conflict_sides(text)
    assert ours == _SHARED + _C + "\n"
    assert theirs == _SHARED + _D + "\n"


def test_split_handles_more_than_one_conflict_block():
    text = (f"{_HEAD}<<<<<<< HEAD\n{_A}\n=======\n{_B}\n>>>>>>> o\n"
            f"<<<<<<< HEAD\n{_C}\n=======\n{_D}\n>>>>>>> o\n")
    ours, theirs, blocks = aide.split_conflict_sides(text)
    assert blocks == 2
    assert ours == _HEAD + _A + "\n" + _C + "\n"
    assert theirs == _HEAD + _B + "\n" + _D + "\n"


@pytest.mark.parametrize("text, needle", [
    (f"{_SHARED}<<<<<<< HEAD\n{_C}\n", "never closed"),
    (f"{_SHARED}<<<<<<< HEAD\n<<<<<<< HEAD\n{_C}\n=======\n{_D}\n>>>>>>> o\n",
     "do not nest"),
    (f"{_SHARED}{_C}\n>>>>>>> other\n", "outside a conflict block"),
])
def test_a_malformed_block_is_a_refusal_not_a_repair(text, needle):
    """A file whose markers do not nest is not one this verb can reason about."""
    merged, _, refusals = _resolve(text)
    assert merged == text
    assert len(refusals) == 1 and needle in refusals[0]


def test_a_file_with_no_markers_is_returned_untouched():
    merged, notes, refusals = _resolve(_SHARED)
    assert (merged, notes, refusals) == (_SHARED, [], [])


def test_the_union_appends_each_sides_new_entries_after_the_shared_history():
    merged, notes, refusals = _resolve(_conflicted(_C + "\n", _D + "\n"))
    assert refusals == []
    assert merged == _SHARED + _C + "\n" + _D + "\n"
    assert "1 added on HEAD, 1 added on the other side" in notes[0]


def test_the_union_never_rewrites_a_claim_and_never_renumbers():
    """§1's immutability rule, through a merge: every claim line survives
    byte-for-byte and positional ordinals stay what each side captured."""
    merged, _, _ = _resolve(_conflicted(_C + "\n", _D + "\n"))
    entries = aide.parse_insights(merged)
    assert [e.raw for e in entries] == [_A, _B, _C, _D]
    assert [e.ordinal for e in entries] == [1, 2, 3, 4]


def test_a_tick_on_one_side_survives_and_the_other_sides_entry_is_not_appended():
    ticked = _A.replace("- [ ]", "- [x]") + " → item 007"
    merged, notes, refusals = _resolve(_conflicted(
        f"{ticked}\n{_B}\n{_C}\n", f"{_A}\n{_B}\n{_D}\n", _HEAD))
    assert refusals == []
    assert merged == _HEAD + ticked + "\n" + _B + "\n" + _C + "\n" + _D + "\n"
    assert "1 merged in place" in notes[0]


def test_both_sides_trail_lines_are_kept_in_date_order():
    ticked = _A.replace("- [ ]", "- [x]") + " → item 007"
    merged, _, _ = _resolve(_conflicted(
        f"{ticked}\n  - **2026-02-09** → ours\n{_B}\n",
        f"{ticked}\n  - **2026-01-09** → theirs\n{_B}\n", _HEAD))
    assert merged.splitlines()[4:7] == [
        ticked, "  - **2026-01-09** → theirs", "  - **2026-02-09** → ours"]


def test_two_ticks_with_two_pointers_keep_both_and_flag_it_for_a_human():
    """The one case a machine may not decide, so it decides nothing: the claim
    line keeps the first pointer and the second becomes a dated trail line."""
    ours = _A.replace("- [ ]", "- [x]") + " → item 007"
    theirs = _A.replace("- [ ]", "- [x]") + " → aide-loop #52"
    merged, notes, refusals = _resolve(
        _conflicted(f"{ours}\n{_B}\n", f"{theirs}\n{_B}\n", _HEAD))
    assert refusals == []          # it still resolves ...
    assert merged.splitlines()[4] == ours
    assert merged.splitlines()[5] == (
        "  - **2026-03-01** → aide-loop #52 "
        "(second pointer, from the other side of the merge)")
    assert any("a different pointer on each side" in n
               and "a human must decide" in n
               for n in notes)    # ... and says a human must look


def test_an_archive_on_one_side_is_refused_by_the_prefix_check_alone():
    """The open point issue #158 left: an archive cuts closed entries out of
    the middle and renumbers what remains, so the two sides share no prefix."""
    merged, _, refusals = _resolve(_conflicted(
        f"{_B}\n{_C}\n", f"{_A}\n{_B}\n{_D}\n", _HEAD))
    assert merged == _conflicted(f"{_B}\n{_C}\n", f"{_A}\n{_B}\n{_D}\n", _HEAD)
    assert len(refusals) == 1
    assert "reordered or an archive cut entries out" in refusals[0]


def test_a_reworded_claim_at_the_tail_is_refused_only_against_the_merge_base():
    """Two sides alone cannot tell a rewording from a second capture — both are
    "one new line each". The base can, and a stalled merge has one."""
    reworded = "- [ ] framework — a is A *(item 1, 2026-01-01)*"
    text = _conflicted(f"{_A}\n", f"{reworded}\n", _HEAD)
    assert _resolve(text)[2] == []                      # no base: indistinguishable
    merged, _, refusals = _resolve(text, base=_HEAD + _A + "\n")
    assert merged == text
    assert len(refusals) == 1 and "reworded" in refusals[0]


def test_the_merge_base_names_the_side_that_rewrote_the_shared_history():
    text = _conflicted(f"{_B}\n{_C}\n", f"{_A}\n{_B}\n{_D}\n", _HEAD)
    refusal = _resolve(text, base=_HEAD + _A + "\n" + _B + "\n")[2][0]
    assert refusal.startswith("HEAD rewrote the 2 entries")


def test_a_conflict_reaching_the_header_is_refused():
    """Not an append: the two sides disagree above the first entry."""
    text = ("# Insight Inbox\n<<<<<<< HEAD\n_Ours._\n=======\n_Theirs._\n"
            f">>>>>>> o\n\n{_A}\n")
    merged, _, refusals = _resolve(text)
    assert merged == text
    assert len(refusals) == 1 and "above the first entry" in refusals[0]


def test_a_blank_separated_file_keeps_its_separator_across_the_join():
    merged, _, refusals = _resolve(_conflicted(
        f"{_C}\n", f"{_D}\n", _HEAD + _A + "\n\n" + _B + "\n\n"))
    assert refusals == []
    assert merged == _HEAD + f"{_A}\n\n{_B}\n\n{_C}\n\n{_D}\n"


# --------------------------------------------------------------------------- #
# conflict_marker_errors — the `aide check` lint
# --------------------------------------------------------------------------- #
def test_check_reports_a_conflict_marker_as_an_error_naming_the_verb(tmp_path: Path):
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True)
    (ddir / "insights.md").write_text(_conflicted(_C + "\n", _D + "\n"),
                                      encoding="utf-8")
    errors = aide.conflict_marker_errors(ddir)
    assert len(errors) == 2                     # <<<<<<< and >>>>>>>, not =======
    assert errors[0].startswith("insights.md:7:")
    assert all("insights resolve" in e for e in errors)


def test_the_lint_does_not_fire_on_a_setext_heading_underline(tmp_path: Path):
    """`=======` is a heading underline as often as it is a conflict marker, and
    a lint that fires on a heading is one a reader learns to skim."""
    ddir = tmp_path / "docs" / "aide"
    ddir.mkdir(parents=True)
    (ddir / "insights.md").write_text("Insight Inbox\n=======\n\n" + _A + "\n",
                                      encoding="utf-8")
    assert aide.conflict_marker_errors(ddir) == []


def test_run_checks_fails_on_a_committed_conflict_marker(tmp_path: Path):
    """An error, not a warning: every ordinal below the marker is wrong, so
    `list`, `tick` and `archive` are all reading a file that lies."""
    repo = _repo(tmp_path, _conflicted(_C + "\n", _D + "\n"))
    (repo / "docs" / "aide" / "progress.md").write_text(_PROGRESS, encoding="utf-8")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert [e for e in errors if "conflict marker" in e]
    assert aide.main(["--repo", str(repo), "check"]) == 1


# --------------------------------------------------------------------------- #
# the command layer
# --------------------------------------------------------------------------- #
def test_resolve_says_so_and_exits_clean_when_there_is_nothing_to_resolve(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "resolve"]) == 0
    assert "no conflict markers" in capsys.readouterr().out
    assert _inbox(repo) == INBOX


def test_dry_run_prints_the_union_and_writes_nothing(tmp_path: Path, capsys):
    text = _conflicted(_C + "\n", _D + "\n")
    repo = _repo(tmp_path, text)
    assert aide.main(["--repo", str(repo), "insights", "resolve", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "1 added on HEAD, 1 added on the other side" in out and "dry run" in out
    assert _inbox(repo) == text


def test_a_refusal_leaves_the_markers_exactly_where_they_were(tmp_path: Path, capsys):
    """Nothing partially written: the only safe thing to do with a claim the
    code cannot align is leave it in front of a human."""
    text = _conflicted(f"{_B}\n{_C}\n", f"{_A}\n{_B}\n{_D}\n", _HEAD)
    repo = _repo(tmp_path, text)
    assert aide.main(["--repo", str(repo), "insights", "resolve"]) == 1
    assert _inbox(repo) == text
    err = capsys.readouterr().err
    assert "archive cut entries out" in err and "left exactly as it is" in err


def test_a_pointer_is_never_dropped_when_only_one_tick_carries_one():
    """A hand-flipped `[x]` with no pointer met a `tick`-written one on the
    other side. Preferring our side unconditionally threw the routing record
    away — and the routing record is the whole reason a tick is worth merging."""
    bare = _A.replace("- [ ]", "- [x]")                  # ticked, no pointer
    routed = bare + " → item 007"
    merged, notes, refusals = _resolve(
        _conflicted(f"{bare}\n{_B}\n", f"{routed}\n{_B}\n", _HEAD))
    assert refusals == []
    assert merged.splitlines()[4] == routed
    # One tick, one pointer — nothing for a human to arbitrate.
    assert not any("different pointers" in n for n in notes)


def test_a_shared_entry_neither_side_touched_is_not_counted_as_merged():
    """Only a *last* entry lacks a trailing blank, so in a blank-separated file
    the two sides disagree about an untouched entry purely by where it sits."""
    ours = f"{_A}\n\n{_B}\n"
    theirs = f"{_A}\n\n{_B}\n\n{_D}\n"
    merged, notes, refusals = _resolve(_conflicted(ours, theirs, _HEAD))
    assert refusals == []
    assert "0 merged in place" in notes[0]
    # And the separator survives the join rather than being eaten with it.
    assert merged == _HEAD + f"{_A}\n\n{_B}\n\n{_D}\n"


def test_a_pointer_on_an_unticked_side_is_kept_too():
    """A hand-written routing note is a routing record like any other. Guarding
    the second-pointer branch on the other side having *ticked* dropped it."""
    ours = _A + " → see issue #12"                    # unticked, hand pointer
    theirs = _A.replace("- [ ]", "- [x]") + " → item 007"
    merged, notes, refusals = _resolve(
        _conflicted(f"{ours}\n{_B}\n", f"{theirs}\n{_B}\n", _HEAD))
    assert refusals == []
    assert merged.splitlines()[4] == theirs            # the tick wins the line
    assert "see issue #12" in merged                   # ... and nothing is lost
    assert any("a different pointer on each side" in n for n in notes)


def test_a_line_under_a_shared_entry_on_the_other_side_is_not_discarded():
    """`rest` came from our side alone, so anything sitting under the entry on
    the other side vanished — and the run still reported a clean merge."""
    stray = "  (a note that is neither a claim nor a trail line)"
    merged, _, refusals = _resolve(_conflicted(
        f"{_A}\n{_B}\n{_C}\n", f"{_A}\n{stray}\n{_B}\n{_D}\n", _HEAD))
    assert refusals == []
    assert stray in merged.splitlines()


def test_one_stray_blank_does_not_re_space_every_other_entry():
    """The separator is each entry's own. A whole-file "this file uses blanks"
    boolean reformatted entries neither side had touched."""
    ours = f"{_A}\n{_B}\n\n{_C}\n"        # one blank, after B only
    theirs = f"{_A}\n{_B}\n\n{_D}\n"
    merged, _, refusals = _resolve(_conflicted(ours, theirs, _HEAD))
    assert refusals == []
    assert merged == _HEAD + f"{_A}\n{_B}\n\n{_C}\n\n{_D}\n"


# --------------------------------------------------------------------------- #
# --trail: a dated line under an entry that stays open (issue #236)
# --------------------------------------------------------------------------- #
def test_tick_trail_appends_a_dated_line_and_leaves_the_box_open():
    """§1 → insights-triage: a duplicate, or a reason an entry stays open, is
    a trail line under an UNTICKED entry — the edit the verb exists to own."""
    out, msg = aide.tick_insight_text(INBOX, 2, "duplicate of entry 4",
                                      "2026-09-17", trail_only=True)
    lines = out.splitlines()
    assert lines[6] == INBOX.splitlines()[6]          # still `- [ ]`, byte for byte
    assert lines[7] == "  - **2026-09-17** → duplicate of entry 4"
    assert "left open" in msg
    entry = aide.parse_insights(out)[1]
    assert not entry.ticked
    assert entry.trail == ["  - **2026-09-17** → duplicate of entry 4"]


def test_tick_trail_on_an_open_entry_is_appendable_newest_last():
    once, _ = aide.tick_insight_text(INBOX, 2, "first", "2026-09-17", trail_only=True)
    twice, _ = aide.tick_insight_text(once, 2, "second", "2026-09-18", trail_only=True)
    entry = aide.parse_insights(twice)[1]
    assert not entry.ticked
    assert [t.split("→ ")[1] for t in entry.trail] == ["first", "second"]


def test_tick_trail_on_a_ticked_entry_is_the_ordinary_second_update():
    with_flag, _ = aide.tick_insight_text(INBOX, 1, "later", "2026-08-24", trail_only=True)
    without, _ = aide.tick_insight_text(INBOX, 1, "later", "2026-08-24")
    assert with_flag == without


def test_tick_trail_refuses_a_malformed_entry_rather_than_guessing():
    text = INBOX + "- [ ] not a typed entry at all\n"
    with pytest.raises(ValueError, match="does not parse"):
        aide.tick_insight_text(text, 5, "x", "2026-09-17", trail_only=True)


def test_tick_trail_from_the_cli_writes_and_commits(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "tick", "2", "--trail",
                      "--pointer", "duplicate of entry 4", "--date", "2026-09-17"]) == 0
    inbox = _inbox(repo)
    assert ("- [ ] defect — the reach check calls its own happy path a typo *(2026-05-11)*\n"
            "  - **2026-09-17** → duplicate of entry 4\n") in inbox
    assert _run(["git", "status", "--porcelain"], repo).stdout.strip() == ""


# --------------------------------------------------------------------------- #
# insight IDs — the durable handle (issue #276)
#
# A position is stable only until an archive or a merge; the ID is computed
# from what never changes — the capture date and the claim text — so a
# citation written today still resolves after both.
# --------------------------------------------------------------------------- #
def _sha(claim: str) -> str:
    import hashlib
    return hashlib.sha256(claim.encode("utf-8")).hexdigest()


def _colliding_claims(n: int = aide.INSIGHT_ID_MIN_HEX) -> "tuple[str, str]":
    """Two different claims whose hashes share their first *n* hex digits."""
    seen = {}
    i = 0
    while True:
        claim = f"claim number {i}"
        key = _sha(claim)[:n]
        if key in seen:
            return seen[key], claim
        seen[key] = claim
        i += 1


def test_an_id_is_the_capture_date_and_four_hex_of_the_claim():
    entries = aide.parse_insights(INBOX)
    ids = aide.insight_ids(entries)
    claim = "the reach check calls its own happy path a typo"
    assert ids[1] == f"2026-05-11-{_sha(claim)[:4]}"
    assert all(i is not None and aide.is_insight_id(i) for i in ids)


def test_the_id_is_blind_to_everything_triage_writes():
    """Checkbox, pointer and trail are bookkeeping; only the claim is hashed."""
    before = aide.insight_ids(aide.parse_insights(INBOX))
    ticked, _ = aide.tick_insight_text(INBOX, 2, "item 121", "2026-08-24")
    trailed, _ = aide.tick_insight_text(ticked, 2, "later", "2026-08-25")
    assert aide.insight_ids(aide.parse_insights(trailed)) == before


def test_the_id_survives_a_rewrap_but_not_a_reword():
    one = aide.parse_insights("- [ ] gap — a  claim\twith gaps *(2026-01-01)*\n")
    two = aide.parse_insights("- [ ] gap — a claim with gaps *(2026-01-01)*\n")
    three = aide.parse_insights("- [ ] gap — a claim with holes *(2026-01-01)*\n")
    assert aide.insight_ids(one) == aide.insight_ids(two)
    assert aide.insight_ids(one) != aide.insight_ids(three)


def test_a_malformed_or_undated_line_has_no_id():
    entries = aide.parse_insights("- [ ] nonsense\n")
    assert aide.insight_ids(entries) == [None]


def test_the_same_claim_captured_twice_shares_one_id():
    text = ("- [ ] gap — one claim *(item 001, 2026-01-01)*\n"
            "- [ ] gap — one claim *(item 002, 2026-01-01)*\n")
    a, b = aide.insight_ids(aide.parse_insights(text))
    assert a == b


def test_two_different_claims_sharing_four_hex_are_printed_longer():
    first, second = _colliding_claims()
    text = (f"- [ ] gap — {first} *(2026-01-01)*\n"
            f"- [ ] gap — {second} *(2026-01-01)*\n"
            f"- [ ] gap — {second} *(2026-01-02)*\n")
    entries = aide.parse_insights(text)
    a, b, c = aide.insight_ids(entries)
    assert len(a) > len("2026-01-01-") + 4 and len(b) > len("2026-01-01-") + 4
    assert a != b
    assert c == f"2026-01-02-{_sha(second)[:4]}"   # another date: no collision
    # The short form both share is ambiguous, and each long form resolves.
    short = f"2026-01-01-{_sha(first)[:4]}"
    assert len(aide.resolve_insight_ref(short, entries)) == 2
    assert aide.resolve_insight_ref(a, entries) == [0]
    assert aide.resolve_insight_ref(b, entries) == [1]


def test_any_longer_prefix_of_the_same_hash_is_the_same_id():
    entries = aide.parse_insights(INBOX)
    claim = "the reach check calls its own happy path a typo"
    assert aide.resolve_insight_ref(f"2026-05-11-{_sha(claim)[:10]}", entries) == [1]
    assert aide.resolve_insight_ref(f"2026-05-12-{_sha(claim)[:4]}", entries) == []


def test_list_prints_each_entry_with_its_id(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    out = capsys.readouterr().out
    for iid in aide.insight_ids(aide.parse_insights(INBOX)):
        assert iid in out


def test_tick_by_id_ticks_that_entry_and_the_commit_names_the_id(tmp_path: Path):
    repo = _repo(tmp_path)
    iid = aide.insight_ids(aide.parse_insights(INBOX))[3]
    assert aide.main(["--repo", str(repo), "insights", "tick", iid,
                      "--pointer", "item 121", "--date", "2026-08-24"]) == 0
    assert "*(item 118, 2026-08-15)* → item 121" in _inbox(repo)
    log = _run(["git", "log", "-1", "--pretty=%s"], repo).stdout
    assert f"triage insight {iid}" in log


def test_tick_by_id_refuses_what_it_cannot_name_exactly(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    before = _inbox(repo)
    for ref in ("2026-05-11-ffff", "not-an-id"):
        assert aide.main(["--repo", str(repo), "insights", "tick", ref,
                          "--pointer", "x", "--no-commit"]) == 1
    assert _inbox(repo) == before


def test_an_archived_entry_keeps_its_id_and_list_finds_it(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    iid = aide.insight_ids(aide.parse_insights(INBOX))[0]
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", "--yes", "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "insights", "list", iid]) == 0
    out = capsys.readouterr().out
    assert "insights.md has no verb" in out and "archive-2026-Q1.md" in out
    # Frozen: an archived entry is named, never ticked.
    assert aide.main(["--repo", str(repo), "insights", "tick", iid,
                      "--pointer", "x", "--no-commit"]) == 1
    assert "archived" in capsys.readouterr().err


def test_list_one_by_position_prints_that_entry_with_its_trail(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list", "1"]) == 0
    out = capsys.readouterr().out
    assert "insights.md has no verb" in out and "accepted into wave 3" in out
    assert "utf-8-sig" not in out


# --------------------------------------------------------------------------- #
# aide check — insight citations in durable artefacts (issue #276)
# --------------------------------------------------------------------------- #
def _cite(repo: Path, rel: str, body: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _findings(repo: Path):
    config = aide.load_config(repo)
    return aide.insight_reference_findings(repo, config, aide.docs_dir(repo, config))


def test_a_dangling_insight_id_is_an_error_in_docs_and_in_tests(tmp_path: Path):
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md", "Chartered by insight 2026-05-11-ffff.\n")
    _cite(repo, "tests/test_x.py", "# corrects inbox entry `2026-05-11-ffff`\n")
    errors, _ = _findings(repo)
    assert len(errors) == 2
    assert any(e.startswith("docs/aide/items/007-x.md:1:") for e in errors)
    assert any(e.startswith("tests/test_x.py:1:") for e in errors)


def test_a_citation_that_resolves_is_clean_even_once_archived(tmp_path: Path):
    repo = _repo(tmp_path)
    iid = aide.insight_ids(aide.parse_insights(INBOX))[0]
    _cite(repo, "docs/aide/items/007-x.md", f"Chartered by insight {iid}.\n")
    assert _findings(repo) == ([], [])
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", "--yes", "--no-commit"]) == 0
    assert _findings(repo) == ([], [])


def test_a_date_shaped_token_without_the_word_is_not_a_citation(tmp_path: Path):
    """An error here blocks `merge`; a timestamp or a slug must never trip it."""
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md",
          "Log: run-2026-05-11-1530.log, and 2026-05-11-beef on its own.\n")
    _cite(repo, "tests/test_x.py", 'STAMP = "2026-05-11-1530"\n')
    assert _findings(repo) == ([], [])


def test_a_bare_entry_before_a_date_shaped_token_is_not_a_citation(tmp_path: Path):
    """"entry" alone is an audit or ledger entry too; it reads as an insight
    citation only on a line that says insight or inbox, as the positional
    form does — else a timestamp blocks `merge`."""
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md",
          "The audit entry 2026-05-11-1530 recorded a timeout.\n")
    _cite(repo, "tests/test_x.py", "# ledger entries 2026-05-11-1530\n")
    assert _findings(repo) == ([], [])
    _cite(repo, "docs/aide/items/008-y.md",
          "The inbox entry 2026-05-11-1530 is gone.\n")
    errors, _ = _findings(repo)
    assert [e.split(":")[0] for e in errors] == ["docs/aide/items/008-y.md"]


def test_a_year_after_insights_is_not_a_position(tmp_path: Path):
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md",
          "See the insights 2026 dashboard.\n"
          "Fixes insight #2026.\n")
    _, warnings = _findings(repo)
    assert [w.split(":")[1] for w in warnings] == ["2"]


def test_a_year_shaped_position_the_inbox_holds_still_warns(tmp_path: Path):
    """The year skip is for numbers no entry could have: an inbox of 1900+
    entries is cited by position like any other."""
    inbox = "".join(f"- [ ] gap — claim {i} *(2026-01-01)*\n" for i in range(1, 1901))
    repo = _repo(tmp_path, inbox)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 1900.\n")
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and "insight 1900" in warnings[0]


def test_the_inbox_and_its_archives_are_not_swept(tmp_path: Path):
    """A claim is immutable, so a finding on one could never be cleared."""
    repo = _repo(tmp_path, INBOX + "- [ ] gap — see insight 2026-01-01-ffff and entry 3 *(2026-08-20)*\n")
    _cite(repo, "docs/aide/insights/archive-2026-Q1.md",
          "# Insight Archive\n\n- [x] gap — insight 28, insight 2026-01-01-ffff *(2026-01-01)* → x\n")
    assert _findings(repo) == ([], [])


def test_a_short_id_two_claims_share_is_a_warning(tmp_path: Path):
    first, second = _colliding_claims()
    repo = _repo(tmp_path, f"- [ ] gap — {first} *(2026-01-01)*\n"
                           f"- [ ] gap — {second} *(2026-01-01)*\n")
    _cite(repo, "docs/aide/queue/queue-001.md",
          f"Routes insight 2026-01-01-{_sha(first)[:4]}.\n")
    errors, warnings = _findings(repo)
    assert errors == [] and len(warnings) == 1 and "more than one claim" in warnings[0]
    entries = aide.parse_insights(_inbox(repo))
    assert all(iid in warnings[0] for iid in aide.insight_ids(entries))


def test_a_positional_citation_is_a_warning_naming_the_id(tmp_path: Path):
    repo = _repo(tmp_path)
    iid = aide.insight_ids(aide.parse_insights(INBOX))[1]
    _cite(repo, "docs/aide/items/007-x.md",
          "Fixes insight 2.\n"
          "The lint the inbox entry #2 describes.\n"
          "See insights.md entry 2.\n"
          "Ledger entry 2 is a different thing.\n"
          "Released in insight 1.2 and entry 1.2.\n")
    errors, warnings = _findings(repo)
    assert errors == []
    assert [w.split(":")[1] for w in warnings] == ["1", "2", "3"]
    assert all(iid in w for w in warnings)


def test_a_positional_citation_in_a_test_is_a_warning_too(tmp_path: Path):
    """A test comment or assertion message naming "insight 2" goes stale on
    the same archive a spec does (issue #295)."""
    repo = _repo(tmp_path)
    iid = aide.insight_ids(aide.parse_insights(INBOX))[1]
    _cite(repo, "tests/test_x.py",
          "# corrects insight 2\n"
          'assert ok, "the ledger entry 2 is fine"\n'
          'assert ok, "see inbox entry #2"\n')
    errors, warnings = _findings(repo)
    assert errors == []
    assert [w.split(":")[:2] for w in warnings] == [["tests/test_x.py", "1"],
                                                    ["tests/test_x.py", "3"]]
    assert all("by position" in w and iid in w for w in warnings)


# --------------------------------------------------------------------------- #
# records are not swept for positions (issue #338)
# --------------------------------------------------------------------------- #
_RECORD_QUEUE = "# Demo — Work Queue 001\n\n### Item 007: X\nFixes insight 2.\n"


def _progress_007(repo: Path, icon: str) -> None:
    _cite(repo, "docs/aide/progress.md",
          f"# Demo — Progress\n\n## Stage 1 — Rules — 🚧\n\n**Deliverables.**\n"
          f"- {icon} X. *(Item 007)*\n")


@pytest.mark.parametrize("icon", ["✅", "❌", "⏸️"])
def test_a_record_spec_and_a_done_queue_are_not_warned_about_positions(
        tmp_path: Path, icon: str):
    """§1 never rewrites a merged spec, so a warning asking it to cite by ID
    could never clear — and its "today" hint names whatever an archive since
    moved there, which on a record written before it is a wrong answer."""
    repo = _repo(tmp_path)
    _progress_007(repo, icon)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    _cite(repo, "docs/aide/queue/queue-001.md", _RECORD_QUEUE)
    assert _findings(repo) == ([], [])


def test_a_withdrawn_stages_planned_item_is_a_record_too(tmp_path: Path):
    """007 is 📋 in stage 2, whose summary row is ❌: `claim` never offers it,
    so its spec and the queue left with it are records (issue #393)."""
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/progress.md",
          "# Demo — Progress\n\n## Stage summary\n\n"
          "| Stage | Title | Objectives | Status |\n|---|---|---|---|\n"
          "| 1 | Rules | G1 | 🚧 |\n| 2 | Later | G1 | ❌ |\n\n"
          "## Stage 1 — Rules — 🚧\n\n**Deliverables.**\n- ✅ Y. *(Item 008)*\n\n"
          "## Stage 2 — Later\n\n**Deliverables.**\n- 📋 X. *(Item 007)*\n")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    _cite(repo, "docs/aide/queue/queue-001.md", _RECORD_QUEUE)
    assert _findings(repo) == ([], [])


def test_a_queue_with_one_open_item_or_none_named_is_not_a_record(tmp_path: Path):
    """A queue is a record only once every item it names is settled: one 📋
    item beside a ✅ one keeps it live, and so does naming none yet."""
    ddir = tmp_path / "docs" / "aide"
    (ddir / "queue").mkdir(parents=True)
    (ddir / "items").mkdir()
    mixed = ddir / "queue" / "queue-001.md"
    mixed.write_text("# Queue 001\n\n### Item 007: A\n\n### Item 008: B\n",
                     encoding="utf-8")
    empty = ddir / "queue" / "queue-002.md"
    empty.write_text("# Queue 002\n\nBeing wired.\n", encoding="utf-8")
    done = ddir / "queue" / "queue-003.md"
    done.write_text("# Queue 003\n\n### Item 007: A\n", encoding="utf-8")
    spec = ddir / "items" / "007-a.md"
    spec.write_text("# Item 007 — A\n", encoding="utf-8")
    live = ddir / "items" / "008-b.md"
    live.write_text("# Item 008 — B\n", encoding="utf-8")
    records = aide.record_documents(ddir, {7: "complete", 8: "planned"})
    assert records == {done, spec}


@pytest.mark.parametrize("icon", ["📋", "🚧", "🔍"])
def test_a_live_spec_and_an_open_queue_still_warn_about_positions(
        tmp_path: Path, icon: str):
    repo = _repo(tmp_path)
    _progress_007(repo, icon)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    _cite(repo, "docs/aide/queue/queue-001.md", _RECORD_QUEUE)
    _, warnings = _findings(repo)
    assert sorted(w.split(":")[0] for w in warnings) == [
        "docs/aide/items/007-x.md", "docs/aide/queue/queue-001.md"]


def test_a_record_is_still_held_to_ids_that_resolve(tmp_path: Path):
    """Only the position warning is scoped: an ID naming nothing is a citation
    no reader can follow, in a record as anywhere."""
    repo = _repo(tmp_path)
    _progress_007(repo, "✅")
    _cite(repo, "docs/aide/items/007-x.md", "Chartered by insight 2026-05-11-ffff.\n")
    _cite(repo, "docs/aide/queue/queue-001.md",
          _RECORD_QUEUE + "See insight 2026-05-11-ffff.\n")
    errors, warnings = _findings(repo)
    assert warnings == []
    assert sorted(e.split(":")[0] for e in errors) == [
        "docs/aide/items/007-x.md", "docs/aide/queue/queue-001.md"]


def test_progress_and_tests_are_swept_whatever_the_items_status(tmp_path: Path):
    repo = _repo(tmp_path)
    _progress_007(repo, "✅")
    _cite(repo, "docs/aide/progress.md",
          (repo / "docs/aide/progress.md").read_text(encoding="utf-8")
          + "\nNote: insight 2 is the reason.\n")
    _cite(repo, "tests/test_x.py", "# corrects insight 2\n")
    _, warnings = _findings(repo)
    assert sorted(w.split(":")[0] for w in warnings) == [
        "docs/aide/progress.md", "tests/test_x.py"]


def test_a_zero_padded_number_is_not_an_insight_position(tmp_path: Path):
    """A position is never padded; `037` is the item-number shape (issue
    #335)."""
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md",
          "The inbox work: insight 037 and inbox entry 041.\n"
          "Fixes insight 2.\n")
    _, warnings = _findings(repo)
    assert [w.split(":")[1] for w in warnings] == ["2"]


def test_a_template_marker_is_not_an_insight_position(tmp_path: Path):
    """``aide-template: insights 2`` is the inbox template's version, so a
    spec or a test quoting the marker cites nothing (issue #439)."""
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md",
          "The inbox opens `<!-- aide-template: insights 2 -->`.\n"
          "<!-- AIDE-TEMPLATE:insights 2 --> and insight 2 on one line.\n")
    _cite(repo, "tests/test_x.py",
          'assert "<!-- aide-template: insights 2 -->" in text\n')
    _, warnings = _findings(repo)
    assert [w.split(":")[:2] for w in warnings] == [["docs/aide/items/007-x.md", "2"]]
    assert "insight 2" in warnings[0]


def test_the_archive_listing_skips_a_template_marker_too():
    """One detector serves `check` and `insights archive` (issue #439)."""
    line = "<!-- aide-template: insights 2 --> fixes insight 3"
    assert [m.group("n") for m in aide._positional_citations(line, lambda: 10)] == ["3"]


# --------------------------------------------------------------------------- #
# insights archive — the citations it renumbers, listed before it moves
# (issue #295)
# --------------------------------------------------------------------------- #
def test_the_position_map_names_what_moves_and_what_shifts():
    remaining, _, _ = aide.archive_insight_text(INBOX, "2026-08-01")
    # Entries 1 and 3 are closed and old; 2 and 4 stay, as 1 and 2.
    assert aide.archive_position_map(INBOX, remaining) == {
        1: None, 2: 1, 3: None, 4: 2}
    remaining, _, _ = aide.archive_insight_text(INBOX, "2026-06-01")
    # Only entry 1 moves; nothing above it, so every later one shifts by one.
    assert aide.archive_position_map(INBOX, remaining) == {1: None, 2: 1, 3: 2, 4: 3}


def test_an_entry_above_the_first_moved_one_keeps_its_number():
    inbox = INBOX + "- [x] gap — late and closed *(2026-01-02)* → x\n"
    remaining, _, _ = aide.archive_insight_text(inbox, "2026-01-03")
    assert aide.archive_position_map(inbox, remaining) == {5: None}


def _archive_citing(tmp_path: Path, capsys, *extra: str):
    repo = _repo(tmp_path)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\nSee insight 4.\n")
    _cite(repo, "tests/test_x.py", "# the claim inbox entry #3 made\n")
    ids = aide.insight_ids(aide.parse_insights(INBOX))
    capsys.readouterr()
    code = aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01", *extra])
    return repo, ids, code, capsys.readouterr().out


def test_a_dry_run_archive_lists_each_positional_citation_with_its_id_before(
        tmp_path: Path, capsys):
    repo, ids, code, out = _archive_citing(tmp_path, capsys)
    assert code == 0
    listed = [ln for ln in out.splitlines() if ln.startswith("  ") and "`" in ln]
    assert [ln.split(":")[0].strip() for ln in listed] == [
        "docs/aide/items/007-x.md", "docs/aide/items/007-x.md", "tests/test_x.py"]
    assert ids[1] in listed[0] and "entry 1 after" in listed[0]
    assert ids[3] in listed[1] and "entry 2 after" in listed[1]
    assert ids[2] in listed[2] and "archived" in listed[2]
    assert _inbox(repo) == INBOX                        # still a dry run


def test_an_archive_that_moves_lists_them_and_still_proceeds(tmp_path: Path, capsys):
    repo, ids, code, out = _archive_citing(tmp_path, capsys, "--yes", "--no-commit")
    assert code == 0
    assert ids[1] in out and ids[3] in out and ids[2] in out
    assert len(aide.parse_insights(_inbox(repo))) == 2   # the move happened


def test_an_archive_still_lists_a_records_positional_citation(tmp_path: Path, capsys):
    """`aide check` leaves a record's positions alone (issue #338), but the
    archive run is the one that changes what the number reads as — the
    listing is what preserves it."""
    repo = _repo(tmp_path)
    _progress_007(repo, "✅")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    ids = aide.insight_ids(aide.parse_insights(INBOX))
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-08-01"]) == 0
    out = capsys.readouterr().out
    assert "docs/aide/items/007-x.md:1:" in out and ids[1] in out


def test_an_archive_lists_no_citation_whose_number_it_leaves_alone(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, INBOX + "- [x] gap — late and closed *(2026-01-02)* → x\n")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-01-03"]) == 0
    assert "by position" not in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# insights add — capture through the CLI (issue #363)
#
# Capture was a hand edit, and in an unattended run every hand edit of the
# inbox stopped on a permission prompt. The verb writes §1's shape itself —
# the date and the engine filled in — so these tests are about the line it
# writes reading back exactly as given, and about the refusals writing nothing.
# --------------------------------------------------------------------------- #
import datetime as _dt  # noqa: E402


def _today() -> str:
    return _dt.date.today().isoformat()


def _engine() -> str:
    return aide.installed_engine_version()


def _add(repo: Path, *args: str) -> int:
    return aide.main(["--repo", str(repo), "insights", "add", *args])


def _inbox_bytes(repo: Path) -> bytes:
    return (repo / "docs" / "aide" / "insights.md").read_bytes()


def test_add_appends_the_section_shape_with_the_date_and_engine_filled_in(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    head = _head(repo)
    assert _add(repo, "defect", "`aide scope` misses renamed files",
                "--provenance", "item 042") == 0
    line = _inbox(repo).splitlines()[-1]
    assert line == (f"- [ ] defect — `aide scope` misses renamed files "
                    f"*(item 042, {_today()}, engine {_engine()})*")
    entry = aide.parse_insights(_inbox(repo))[-1]
    assert (entry.type, entry.text, entry.source, entry.date, entry.note,
            entry.pointer, entry.item) == (
        "defect", "`aide scope` misses renamed files", "item 042", _today(),
        f"engine {_engine()}", None, 42)
    # Appended, nothing else touched.
    assert _inbox(repo) == INBOX + line + "\n"
    # Committed, one commit on top, naming the ID it printed.
    iid = aide.insight_ids(aide.parse_insights(_inbox(repo)))[-1]
    assert f"captured insight {iid}" in capsys.readouterr().out
    assert _run(["git", "rev-parse", "HEAD~1"], repo).stdout.strip() == head
    assert _run(["git", "log", "-1", "--pretty=%s"], repo).stdout.strip() == (
        f"docs(aide): capture insight {iid}")
    assert _clean(repo)


def test_add_without_provenance_leaves_it_out_with_its_comma(tmp_path: Path):
    repo = _repo(tmp_path)
    assert _add(repo, "gap", "nothing exercises a Windows install") == 0
    line = _inbox(repo).splitlines()[-1]
    assert line == (f"- [ ] gap — nothing exercises a Windows install "
                    f"*({_today()}, engine {_engine()})*")
    assert aide.parse_insights(_inbox(repo))[-1].source is None
    assert aide.insight_warnings(repo / "docs" / "aide") == []


def test_add_without_an_engine_version_leaves_the_note_out(tmp_path: Path,
                                                           monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(aide, "_VERSION_FILE", tmp_path / "no-such-VERSION")
    assert _add(repo, "knowledge", "a fact", "--no-commit") == 0
    assert _inbox(repo).splitlines()[-1] == f"- [ ] knowledge — a fact *({_today()})*"


def test_the_id_add_prints_is_the_one_list_prints_even_when_lengthened(
        tmp_path: Path, capsys):
    first, second = _colliding_claims()
    repo = _repo(tmp_path, f"# Insight Inbox\n\n- [ ] gap — {first} *({_today()})*\n")
    assert _add(repo, "gap", second, "--no-commit") == 0
    printed = capsys.readouterr().out
    ids = aide.insight_ids(aide.parse_insights(_inbox(repo)))
    assert len(ids[-1]) > len(_today()) + 1 + aide.INSIGHT_ID_MIN_HEX
    assert f"captured insight {ids[-1]} " in printed
    assert aide.main(["--repo", str(repo), "insights", "list"]) == 0
    assert ids[-1] in capsys.readouterr().out


@pytest.mark.parametrize("argv", [
    ["bogus", "a claim"],                                  # unknown type
    ["Defect", "a claim"],                                 # types are lowercase
    ["gap"],                                               # no claim
    ["gap", "   "],                                        # empty claim
    ["gap", "two\nlines"],                                 # a line break
    ["gap", "two lines"],                             # one splitlines breaks on
    ["gap", "a claim", "--provenance", "item\n042"],       # a break in provenance
    ["gap", "a claim", "--provenance", "item 042)"],       # closes the marker
    ["gap", "x *(prod, 2020-01-01)* → y"],                 # reads as marker + pointer
    ["gap", "a claim", "--date", "2020-01-01"],            # capture is dated today
], ids=["unknown-type", "capitalised-type", "no-claim", "blank-claim",
        "newline", "line-separator", "provenance-newline", "provenance-paren",
        "aside-and-pointer", "date"])
def test_add_refuses_with_exit_2_and_writes_nothing(tmp_path: Path, argv, capsys):
    repo = _repo(tmp_path)
    before, head = _inbox_bytes(repo), _head(repo)
    assert _add(repo, *argv) == 2
    assert _inbox_bytes(repo) == before and _head(repo) == head
    err = capsys.readouterr().err.strip()
    assert err.startswith("aide insights add:") and len(err.splitlines()) == 1


def test_a_refused_add_creates_no_inbox_either(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    assert _add(repo, "bogus", "a claim") == 2
    assert not (repo / "docs" / "aide" / "insights.md").exists()


def test_an_aside_the_parser_reads_past_is_not_refused(tmp_path: Path):
    """The refusal is exactly as wide as the reader: an aside that parses back
    as part of the claim is captured as written."""
    repo = _repo(tmp_path)
    claim = "the default is *(prod, 2020-01-01)* not staging"
    assert _add(repo, "gap", claim, "--no-commit") == 0
    assert aide.parse_insights(_inbox(repo))[-1].text == claim


def test_the_verbs_line_is_the_line_a_hand_would_write():
    """A hand-appended line of the same shape is the same entry: check, list
    and the ID read the line, not how it got there."""
    line, problem = aide.insight_capture_line("gap", "  a claim ", "item 007",
                                              "2026-09-30", "engine 2.28.0")
    assert problem is None
    assert line == "- [ ] gap — a claim *(item 007, 2026-09-30, engine 2.28.0)*"
    by_hand = aide.parse_insights(
        "- [ ] gap — a claim *(item 007, 2026-09-30, engine 2.28.0)*\n")
    assert aide.insight_ids(aide.parse_insights(line + "\n")) == aide.insight_ids(by_hand)


def test_add_creates_a_missing_inbox_and_appends_to_it(tmp_path: Path):
    repo = _loop_repo_without_inbox(tmp_path)
    assert _add(repo, "gap", "a claim") == 0
    template = (aide._TEMPLATES_DIR / "insights.md").read_bytes()
    data = _inbox_bytes(repo)
    assert data.startswith(template)
    assert aide.parse_insights(_inbox(repo))[-1].text == "a claim"
    assert _clean(repo)


def test_add_no_commit_leaves_the_capture_uncommitted(tmp_path: Path):
    repo = _repo(tmp_path)
    head = _head(repo)
    assert _add(repo, "gap", "a claim", "--no-commit") == 0
    assert _head(repo) == head
    assert "insights.md" in _run(["git", "status", "--porcelain"], repo).stdout


def test_a_capture_git_will_not_commit_is_put_back_and_exits_1(
        tmp_path: Path, monkeypatch, capsys):
    """What `tick` does (issue #309): an edit left written but uncommitted
    reads as already made to the re-run. And no ID is printed: the entry it
    would name has just been removed again."""
    repo = _repo(tmp_path)
    before, head = _inbox_bytes(repo), _head(repo)
    _without_git_identity(repo, monkeypatch, tmp_path)
    capsys.readouterr()
    assert _add(repo, "gap", "a claim") == 1
    assert _inbox_bytes(repo) == before and _head(repo) == head
    assert "captured insight" not in capsys.readouterr().out


def test_the_id_add_prints_is_lengthened_against_an_archived_claim(
        tmp_path: Path, capsys):
    """The clash is with an archived entry of the same day: an ID computed
    over the live inbox alone would print four hex digits, and `check` would
    then call the citation ambiguous."""
    first, second = _colliding_claims()
    repo = _repo(tmp_path, "# Insight Inbox\n\n")
    quarter = aide.insight_quarter(_today())
    _cite(repo, f"docs/aide/insights/archive-{quarter}.md",
          f"# Insight Archive\n\n- [x] gap — {first} *({_today()})* → x\n")
    assert _add(repo, "gap", second, "--no-commit") == 0
    printed = capsys.readouterr().out
    pool = aide.load_insight_pool(repo / "docs" / "aide")
    ids = aide.insight_ids([e for _, e in pool])
    mine = ids[[e.text for _, e in pool].index(second)]
    assert len(mine) > len(_today()) + 1 + aide.INSIGHT_ID_MIN_HEX
    assert f"captured insight {mine} " in printed
    _cite(repo, "docs/aide/items/007-x.md", f"Fixes insight {mine}.\n")
    assert _findings(repo) == ([], [])


def test_add_never_glues_onto_a_last_line_with_no_newline(tmp_path: Path):
    repo = _repo(tmp_path, INBOX.rstrip("\n"))
    assert _add(repo, "gap", "a claim", "--no-commit") == 0
    lines = _inbox(repo).splitlines()
    assert lines[-2] == INBOX.rstrip("\n").splitlines()[-1]
    assert aide.parse_insights(lines[-1] + "\n")[0].text == "a claim"
    assert _inbox(repo).endswith("\n") and "\n\n" not in _inbox(repo)[len(INBOX) - 2:]


def test_add_keeps_a_bom_and_crlf_line_endings(tmp_path: Path):
    repo = _repo(tmp_path)
    path = repo / "docs" / "aide" / "insights.md"
    original = b"\xef\xbb\xbf" + INBOX.replace("\n", "\r\n").encode("utf-8")
    path.write_bytes(original)
    assert _add(repo, "gap", "a claim", "--no-commit") == 0
    data = path.read_bytes()
    assert data.startswith(original)
    assert data[len(original):].endswith(b")*\r\n")
    assert b"\n" not in data[len(original):-2]


def test_add_refuses_a_conflicted_inbox(tmp_path: Path):
    repo = _repo(tmp_path, INBOX + "<<<<<<< HEAD\n- [ ] gap — a *(2026-08-20)*\n"
                                   "=======\n- [ ] gap — b *(2026-08-20)*\n"
                                   ">>>>>>> other\n")
    before = _inbox_bytes(repo)
    assert _add(repo, "gap", "a claim", "--no-commit") == 2
    assert _inbox_bytes(repo) == before


def test_only_add_takes_a_claim(tmp_path: Path):
    repo = _repo(tmp_path)
    assert aide.main(["--repo", str(repo), "insights", "list", "1", "extra"]) == 2


# --------------------------------------------------------------------------- #
# a positional citation names what it meant when written (issue #361)
#
# Before, the hint named the entry the position holds *today*; after an
# archive that is a different claim, and following it rewrote the citation.
# --------------------------------------------------------------------------- #
_FIVE = """\
# Insight Inbox

- [x] gap — claim one *(2026-01-01)* → a
- [x] gap — claim two *(2026-01-02)* → a
- [x] gap — claim three *(2026-01-03)* → a
- [x] gap — claim four *(2026-01-04)* → a
- [ ] gap — claim five *(2026-01-10)*
"""


def _commit_all(repo: Path, message: str = "cite") -> None:
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", message], repo)


def _archived_after_citing(tmp_path: Path, citation: str) -> Path:
    """The issue's repro: five entries, 1-4 ticked; a committed citation;
    then an archive that leaves the fifth entry at position 1."""
    repo = _repo(tmp_path, _FIVE)
    _cite(repo, "docs/aide/items/007-x.md", citation)
    _commit_all(repo)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-01-05", "--yes"]) == 0
    return repo


def test_a_committed_citation_names_the_entry_it_meant_not_todays_holder(
        tmp_path: Path):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _archived_after_citing(tmp_path, "Fixes insight 1.\n")
    _, warnings = _findings(repo)
    assert len(warnings) == 1
    assert f"entry 1 was insight {ids[0]} when " in warnings[0]
    assert ids[4] not in warnings[0]          # today's holder of position 1
    # The ID it names is one check accepts: it resolves in the archive.
    _cite(repo, "docs/aide/items/007-x.md", f"Fixes insight {ids[0]}.\n")
    assert _findings(repo) == ([], [])


def test_the_issue_repro_entry_4_names_the_archived_fourth_entry(tmp_path: Path):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _archived_after_citing(tmp_path, "Mirrors the inbox entry 4.\n")
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and f"insight {ids[3]}" in warnings[0]
    assert "moved it since" in warnings[0]


def test_a_committed_citation_nothing_moved_says_it_still_is(tmp_path: Path):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _repo(tmp_path, _FIVE)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 5.\n")
    _commit_all(repo)
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and f"insight {ids[4]}" in warnings[0]
    assert "and still is" in warnings[0]


def test_an_uncommitted_citation_names_todays_holder(tmp_path: Path):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _archived_after_citing(tmp_path, "Nothing cited here yet.\n")
    with open(repo / "docs" / "aide" / "items" / "007-x.md", "a",
              encoding="utf-8") as fh:
        fh.write("Fixes insight 1.\n")
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and warnings[0].startswith("docs/aide/items/007-x.md:2:")
    assert "not committed" in warnings[0] and f"insight {ids[4]}" in warnings[0]


def test_a_position_beyond_the_inbox_at_its_commit_named_no_entry(tmp_path: Path):
    repo = _repo(tmp_path, _FIVE)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 7.\n")
    _commit_all(repo)
    # The inbox grows to seven entries afterwards; position 7 was never
    # an entry when the line was written.
    with open(repo / "docs" / "aide" / "insights.md", "a", encoding="utf-8") as fh:
        fh.write("- [ ] gap — six *(2026-02-01)*\n- [ ] gap — seven *(2026-02-02)*\n")
    _commit_all(repo, "two more captures")
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and "held no entry 7" in warnings[0]
    seven = aide.insight_ids(aide.parse_insights(_inbox(repo)))[6]
    assert seven not in warnings[0]


def test_without_git_history_todays_holder_is_the_labelled_fallback(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "docs" / "aide").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (repo / "docs" / "aide" / "insights.md").write_text(_FIVE, encoding="utf-8")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    _, warnings = _findings(repo)
    assert len(warnings) == 1
    assert "today's holder; history unavailable" in warnings[0]
    assert f"insight {ids[1]}" in warnings[0]


def test_history_costs_one_blame_per_file_and_one_show_per_commit(
        tmp_path: Path, monkeypatch):
    repo = _archived_after_citing(
        tmp_path, "Fixes insight 1.\nAnd insight 2.\nAnd inbox entry 3.\n")
    _cite(repo, "docs/aide/queue/queue-001.md",
          "# Q\n\n### Item 007: X\nRoutes insight 4.\n")
    _commit_all(repo, "a queue citing, in a commit of its own")
    calls = []
    real = aide.git

    def counting(args, root, check=True):
        calls.append(args[0])
        return real(args, root, check=check)

    monkeypatch.setattr(aide, "git", counting)
    _, warnings = _findings(repo)
    assert len(warnings) == 4
    assert calls.count("blame") == 2
    assert calls.count("show") == 2           # two distinct commits wrote them


def test_a_bom_on_the_inbox_then_does_not_shift_its_positions(tmp_path: Path):
    """`git show` output is decoded as utf-8, not utf-8-sig: a BOM left on
    would make the first entry no `- ` line and move every position by one."""
    # The first entry on the first line, where the BOM lands.
    bommed = "\ufeff" + _FIVE.split("\n\n", 1)[1]
    repo = _repo(tmp_path)
    (repo / "docs" / "aide" / "insights.md").write_bytes(bommed.encode("utf-8"))
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 1 and insight 5.\n")
    _commit_all(repo)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-01-05", "--yes"]) == 0
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    _, warnings = _findings(repo)
    assert len(warnings) == 2
    assert f"entry 1 was insight {ids[0]} when " in warnings[0]
    assert f"entry 5 was insight {ids[4]} when " in warnings[1]


def test_history_is_read_when_repo_root_is_below_the_git_top_level(tmp_path: Path):
    """`<sha>:<path>` is read from git's top level; the inbox path is
    repo_root's, so it is asked for as `<sha>:./<path>`."""
    top = tmp_path / "mono"
    top.mkdir()
    _run(["git", "init", "-b", "main"], top)
    _run(["git", "config", "user.email", "t@e.com"], top)
    _run(["git", "config", "user.name", "T"], top)
    _run(["git", "config", "core.autocrlf", "false"], top)
    repo = top / "sub"
    (repo / "docs" / "aide").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (repo / "docs" / "aide" / "insights.md").write_text(_FIVE, encoding="utf-8")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 1.\n")
    _commit_all(top)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-01-05", "--yes"]) == 0
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and f"entry 1 was insight {ids[0]} when " in warnings[0]


def test_an_inbox_that_cannot_be_read_then_is_the_labelled_fallback(tmp_path: Path):
    """A failed `git show` — here the inbox was never committed — says nothing
    about the past: not "named no entry", but today's holder, labelled."""
    repo = _repo(tmp_path, _FIVE)
    _run(["git", "rm", "-q", "--cached", "docs/aide/insights.md"], repo)
    _run(["git", "commit", "-q", "-m", "untrack the inbox"], repo)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    _run(["git", "add", "docs/aide/items/007-x.md"], repo)
    _run(["git", "commit", "-q", "-m", "cite"], repo)
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    _, warnings = _findings(repo)
    assert len(warnings) == 1
    assert "named no entry" not in warnings[0]
    assert "history unavailable" in warnings[0] and f"insight {ids[1]}" in warnings[0]


def test_a_line_blamed_on_a_shallow_clones_boundary_is_the_labelled_fallback(
        tmp_path: Path):
    """blame stops at the commit the clone was cut at, and `git show` of it is
    today's inbox — a confident, wrong answer unless the boundary is read."""
    src = _archived_after_citing(tmp_path, "Fixes insight 1.\n")
    clone = tmp_path / "clone"
    _run(["git", "clone", "-q", "--depth", "1", src.resolve().as_uri(),
          str(clone)], tmp_path)
    assert _run(["git", "rev-parse", "--is-shallow-repository"],
                clone).stdout.strip() == "true"
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    _, warnings = _findings(clone)
    assert len(warnings) == 1
    assert "history unavailable" in warnings[0]
    assert f"insight {ids[4]}" in warnings[0] and " was insight " not in warnings[0]


def test_a_root_commit_is_history_not_a_boundary(tmp_path: Path):
    """blame marks a true root commit `boundary` too; only a shallow cut hides
    history. A citation written in a repository's first commit resolves."""
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = tmp_path / "repo"
    (repo / "docs" / "aide" / "items").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (repo / "docs" / "aide" / "insights.md").write_text(_FIVE, encoding="utf-8")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 1.\n")
    _run(["git", "init", "-b", "main"], repo)
    _run(["git", "config", "user.email", "t@e.com"], repo)
    _run(["git", "config", "user.name", "T"], repo)
    _run(["git", "config", "core.autocrlf", "false"], repo)
    _commit_all(repo, "root")
    _, warnings = _findings(repo)
    assert len(warnings) == 1 and f"entry 1 was insight {ids[0]} when " in warnings[0]


@pytest.mark.parametrize("brk", ["\x0c", "\x0b", "\x85", "\u2028", "\r"])
def test_blame_is_asked_for_gits_line_not_splitlines(tmp_path: Path, brk):
    """git counts lines by \\n alone; a form feed, a U+2028 or a lone \\r
    before a citation puts `splitlines`' number past git's, and the blame of
    the wrong line names the wrong commit."""
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _repo(tmp_path, _FIVE)
    cite = repo / "docs" / "aide" / "items" / "007-x.md"
    cite.parent.mkdir(parents=True, exist_ok=True)
    cite.write_bytes(f"x{brk}y\nFixes insight 1.\nlast\n".encode("utf-8"))
    _commit_all(repo)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", "2026-01-05", "--yes"]) == 0
    # git's line 3, splitlines' line 4, is edited and left uncommitted.
    cite.write_bytes(f"x{brk}y\nFixes insight 1.\nlast, edited\n".encode("utf-8"))
    _, warnings = _findings(repo)
    assert len(warnings) == 1
    assert f"entry 1 was insight {ids[0]} when " in warnings[0]


def test_git_line_numbers_count_newlines_only():
    assert aide._git_line_numbers("a\nb\r\nc\x0cd\ne") == [1, 2, 3, 3, 4]


# --------------------------------------------------------------------------- #
# the archive listing names what a citation meant when written (issue #419)
#
# `insights archive` named the ID a position holds in *today's* inbox. For a
# citation written before an earlier archive that is a different claim; it now
# resolves through `_CitationHistory.resolve`, the lookup `aide check`'s hint
# formats, so the two surfaces cannot name different IDs for one citation.
# --------------------------------------------------------------------------- #
def _archive_out(repo: Path, before: str, capsys, *extra: str) -> list:
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", before, *extra]) == 0
    return [ln for ln in capsys.readouterr().out.splitlines()
            if ln.startswith("  ") and "`" in ln]


def _cited_then_archived(tmp_path: Path, citation: str, first: str) -> Path:
    """_FIVE, a committed citation, then an archive that renumbers it."""
    repo = _repo(tmp_path, _FIVE)
    _cite(repo, "docs/aide/items/007-x.md", citation)
    _commit_all(repo)
    assert aide.main(["--repo", str(repo), "insights", "archive",
                      "--before", first, "--yes"]) == 0
    return repo


def test_the_archive_listing_names_what_a_citation_meant_at_its_commit(
        tmp_path: Path, capsys):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    # "insight 3" is claim three; the first archive takes claim one, so
    # claim three is entry 2 and claim four holds entry 3.
    repo = _cited_then_archived(tmp_path, "Fixes insight 3.\n", "2026-01-02")
    sha = _run(["git", "log", "-1", "--format=%h", "--", "docs/aide/items"],
               repo).stdout.strip()
    # The second takes claim two: claim three moves from entry 2 to entry 1.
    (line,) = _archive_out(repo, "2026-01-03", capsys)
    assert line.startswith("  docs/aide/items/007-x.md:1: `insight 3` meant "
                           f"insight {ids[2]} when {sha[:7]} wrote this line")
    assert line.endswith("— entry 1 after the move")
    assert ids[3] not in line                 # today's holder of entry 3


def test_the_archive_listing_and_check_name_one_id(tmp_path: Path, capsys):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _cited_then_archived(tmp_path, "Fixes insight 3.\n", "2026-01-02")
    _, warnings = _findings(repo)
    (line,) = _archive_out(repo, "2026-01-03", capsys)
    assert len(warnings) == 1 and f"insight {ids[2]} when " in warnings[0]
    assert f"insight {ids[2]} when " in line


def test_the_archive_listing_says_a_meant_entry_is_already_archived(
        tmp_path: Path, capsys):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    # Claim one is archived by the first move; position 1 is claim two's,
    # which the second move archives.
    repo = _cited_then_archived(tmp_path, "Fixes insight 1.\n", "2026-01-02")
    (line,) = _archive_out(repo, "2026-01-03", capsys)
    assert f"meant insight {ids[0]} when " in line
    assert line.endswith("— already archived")
    assert ids[1] not in line


def test_an_uncommitted_citation_in_the_archive_listing_is_todays_holder(
        tmp_path: Path, capsys):
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _cited_then_archived(tmp_path, "Nothing yet.\n", "2026-01-02")
    with open(repo / "docs" / "aide" / "items" / "007-x.md", "a",
              encoding="utf-8") as fh:
        fh.write("Fixes insight 3.\n")
    (line,) = _archive_out(repo, "2026-01-03", capsys)
    assert line == ("  docs/aide/items/007-x.md:2: `insight 3` is insight "
                    f"{ids[3]} (not committed, so written against today's "
                    "inbox) — entry 2 after the move")


def test_without_history_the_archive_listing_labels_todays_holder(
        tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    (repo / "docs" / "aide").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (repo / "docs" / "aide" / "insights.md").write_text(_FIVE, encoding="utf-8")
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 2.\n")
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    (line,) = _archive_out(repo, "2026-01-02", capsys)
    assert line == ("  docs/aide/items/007-x.md:1: `insight 2` is insight "
                    f"{ids[1]} (today's holder; history unavailable) — entry 1 "
                    "after the move")


def test_the_archive_listing_says_a_position_named_no_entry_then(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, _FIVE)
    _cite(repo, "docs/aide/items/007-x.md", "Fixes insight 6.\n")
    _commit_all(repo)
    with open(repo / "docs" / "aide" / "insights.md", "a", encoding="utf-8") as fh:
        fh.write("- [x] gap — six *(2026-01-06)* → a\n")
    _commit_all(repo, "a sixth capture")
    six = aide.insight_ids(aide.parse_insights(_inbox(repo)))[5]
    (line,) = _archive_out(repo, "2026-01-02", capsys)
    assert "`insight 6` named no entry when " in line
    assert "find the claim meant with `aide insights list`" in line
    assert six not in line


def test_one_resolution_feeds_the_hint_and_the_listing(tmp_path: Path):
    """`hint` is a formatter over `resolve`: the meaning carries the ID it
    names and the pool index the listing reads the entry's fate from."""
    ids = aide.insight_ids(aide.parse_insights(_FIVE))
    repo = _cited_then_archived(tmp_path, "Fixes insight 3.\n", "2026-01-02")
    ddir = repo / "docs" / "aide"
    pool = aide.load_insight_pool(ddir)
    pids = aide.insight_ids([e for _, e in pool])
    history = aide._CitationHistory(repo, ddir)
    path = ddir / "items" / "007-x.md"
    history.want(path, 1)
    r = history.resolve(path, 1, 3, pool, pids)
    assert r.how == aide.CitationMeaning.COMMITTED
    assert r.iid == ids[2] and pool[r.index][0] == "insights.md"
    assert r.today == ids[3]
    assert history.hint(path, 1, 3, pool, pids) == (
        f"; entry 3 was insight {ids[2]} {r.when} — cite that; an archive or a "
        f"merge has moved it since")
