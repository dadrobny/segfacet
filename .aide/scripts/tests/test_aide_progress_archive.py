"""`aide progress archive` / `unarchive` — issue #475.

A settled stage's section moves out of progress.md to
`progress/stage-N.md`, and its summary row's Title cell links there. Readers
skip the archived section, so these tests hold the four places skipping it
would break to the archive instead: item status (every reader of an item's
status reads the archived bullets too), the rollups (an archived stage rolls
up to its summary row), `aide check`'s structural findings (an archived stage
is not a missing section; progress.md and the archive disagreeing is an
error), and the writers (none writes into the archive; each refuses naming
`unarchive`). And the eligibility rule, condition by condition.

Document-tree tests, bar the few that commit or read branches — the commit,
its put-back, and the claim-branch condition — which build a repository.
`tests/test_fixture_consumer.py` drives both verbs against a real install.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_progress_archive",
                                               _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


GATES = """\
## Human gates

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
| Ship the report format | stage 3 | ⏳ Awaiting | — |

---

"""

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | ✅ |
| 2 | Checks | G1 | ✅ |
| 3 | Reports | G2 | 🚧 |
| 4 | Maintenance | — | ✅ |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1, 2 | ✅ |
| G2 Reports | Stage 2, 3 | 🚧 |

{gates}## Stage 1 — Rules — ✅

**Deliverables.**
- ✅ Bounds. *(Item 001)*
- ✅ Limits. *(Item 002)*

**Acceptance.**
- [x] Rules fire.

---

## Stage 2 — Checks — ✅

**Deliverables.**
- ✅ Lint. *(Item 003)*
- ❌ Fuzz. *(Item 004)*
  - **2026-09-01** → dropped: not needed

**Acceptance.**
- [x] Checks run.
  - **2026-09-02** → re-run on the CI host

---

## Stage 3 — Reports — 🚧

**Deliverables.**
- ✅ Summary. *(Item 005)*
- 📋 Charts. *(Item 006)*

**Acceptance.**
- [ ] Reports render.

---

## Stage 4 — Maintenance — ✅

**Deliverables.**
- ✅ Fix 007. *(Item 007)*
"""

QUEUE_1 = """\
# Queue 001

> **Status:** ✅ Completed (2026-09-04).

### Item 001 — Bounds
### Item 002 — Limits
### Item 003 — Lint
### Item 004 — Fuzz
"""

QUEUE_2 = """\
# Queue 002

> **Status:** 🚧 Live

### Item 005 — Summary
### Item 006 — Charts
"""

AIDE_TOML = '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n'


def _progress(gates: str = GATES) -> str:
    return PROGRESS.format(gates=gates)


def _repo(tmp_path: Path, progress: str = "", queues: bool = True,
          specs: bool = False) -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    (ddir / "queue").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(progress or _progress(), encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    if queues:
        (ddir / "queue" / "queue-001.md").write_text(QUEUE_1, encoding="utf-8")
        (ddir / "queue" / "queue-002.md").write_text(QUEUE_2, encoding="utf-8")
    if specs:
        # Built from an older item template: drift `aide check` reports on a
        # live spec and never on a record's (issue #338).
        (ddir / "items").mkdir()
        for n in range(1, 8):
            (ddir / "items" / f"{n:03d}-x.md").write_text(
                f"<!-- aide-template: item 1 -->\n# Item {n:03d} — X\n\n"
                f"> **Stage:** 1\n", encoding="utf-8")
    return repo


def _ddir(repo: Path) -> Path:
    return repo / "docs" / "aide"


def _read(repo: Path, rel: str = "progress.md") -> str:
    return (_ddir(repo) / rel).read_text(encoding="utf-8")


def _archive(repo: Path, *argv: str) -> int:
    return aide.main(["--repo", str(repo), "progress", "archive", *argv,
                      "--no-commit"])


def _unarchive(repo: Path, *argv: str) -> int:
    return aide.main(["--repo", str(repo), "progress", "unarchive", *argv,
                      "--no-commit"])


def _check(repo: Path):
    return aide.run_checks(repo, aide.load_config(repo), branches=[])


# --------------------------------------------------------------------------- #
# the move itself
# --------------------------------------------------------------------------- #
def test_archive_moves_the_section_verbatim_and_links_the_summary_row():
    text = _progress()
    updated, archived = aide.archive_stage_text(text, "2")
    assert "## Stage 2" not in updated
    assert "| 2 | [Checks](progress/stage-2.md) | G1 | ✅ |" in updated
    alines = archived.splitlines()
    assert alines[0] == aide._archive_header(2)
    assert "../progress.md" in alines[0]
    assert "aide progress unarchive --stage 2" in alines[0]
    section = text[text.index("## Stage 2"):text.index("## Stage 3")]
    body = section.rstrip().removesuffix("---").rstrip()
    assert archived == aide._archive_header(2) + "\n\n" + body + "\n"
    assert "  - **2026-09-01** → dropped: not needed" in archived


@pytest.mark.parametrize("stage", ["1", "2", "3", "4"])
def test_unarchive_puts_back_exactly_what_archive_took(stage):
    """First, middle and last section: the round trip is byte-identical."""
    text = _progress()
    updated, archived = aide.archive_stage_text(text, stage)
    assert aide.unarchive_stage_text(updated, archived, int(stage)) == text


def test_two_stages_archived_come_back_in_number_order():
    text = _progress()
    once, a1 = aide.archive_stage_text(text, "1")
    twice, a2 = aide.archive_stage_text(once, "2")
    back = aide.unarchive_stage_text(twice, a2, 2)
    assert aide.unarchive_stage_text(back, a1, 1) == text


# --------------------------------------------------------------------------- #
# readers: item status, rollups, check
# --------------------------------------------------------------------------- #
def test_item_status_reads_the_archived_bullets_and_a_slice_does_not(tmp_path):
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    plain = _read(repo).splitlines()
    assert 3 not in aide._parse_item_status(plain)[2]
    lines = aide.read_progress_lines(_ddir(repo) / "progress.md")
    status = aide._parse_item_status(lines)[2]
    assert status[3] == "complete" and status[4] == "excluded"
    # A slice is one stage's section, and gains no other file's items.
    start, end, _ = aide.stage_section(lines, "1")
    assert set(aide._parse_item_status(lines[start:end])[2]) == {1, 2}


def test_an_archived_stage_rolls_up_to_its_summary_row(tmp_path):
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    lines = _read(repo).splitlines()
    assert aide.stage_rollups(lines)["2"] == "complete"
    # G2 names archived stage 2 ✅ and live stage 3 🚧: still 🚧, and the
    # writer, which reads the same rollup, leaves it there.
    out, messages = aide.rollup_progress(_read(repo))
    assert messages == [] and "| G2 Reports | Stage 2, 3 | 🚧 |" in out


def test_rollup_of_an_archived_stage_writes_the_objective_rows_naming_it(tmp_path):
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "1") == 0
    assert _archive(repo, "--stage", "2") == 0
    path = _ddir(repo) / "progress.md"
    path.write_text(_read(repo).replace("| G1 Rules | Stage 1, 2 | ✅ |",
                                        "| G1 Rules | Stage 1, 2 | 🚧 |"),
                    encoding="utf-8")
    out, messages = aide.rollup_progress(_read(repo), 2)
    assert messages == ["objective G1 🚧 → ✅ complete"]
    assert "| G1 Rules | Stage 1, 2 | ✅ |" in out


def test_check_reads_an_archived_tree_as_it_read_the_live_one(tmp_path):
    """The audit's 8 → 96 warnings: archiving changes no finding. Read
    without the archive, the shipped items were 📋 — their specs drifted and
    their completed queue was open — and the archived stages had no section."""
    repo = _repo(tmp_path, _progress(gates=""), specs=True)
    before = _check(repo)
    assert any(w.startswith("items/006-x.md") for w in before[1])  # live
    assert _archive(repo) == 0
    assert (_ddir(repo) / "progress" / "stage-1.md").is_file()
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()
    assert _check(repo) == before


def test_every_stage_archived_still_passes_the_section_check(tmp_path):
    text = _progress(gates="")
    for n in ("1", "2", "3", "4"):
        text, archived = aide.archive_stage_text(text, n)
        repo_dir = tmp_path / "repo" / "docs" / "aide" / "progress"
        repo_dir.mkdir(parents=True, exist_ok=True)
        (repo_dir / f"stage-{n}.md").write_text(archived, encoding="utf-8")
    ddir = tmp_path / "repo" / "docs" / "aide"
    (tmp_path / "repo" / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(text, encoding="utf-8")
    errors, warnings = _check(tmp_path / "repo")
    assert not any("no '## Stage N' sections" in e for e in errors)
    assert not any("has no '## Stage" in w for w in warnings)
    assert not any("names no stage" in w for w in warnings)


@pytest.mark.parametrize("damage, finding", [
    (lambda d: (d / "progress" / "stage-2.md").unlink(),
     "stage 2: its Stage summary row links to progress/stage-2.md, which "
     "does not exist"),
    (lambda d: (d / "progress.md").write_text(
        (d / "progress.md").read_text(encoding="utf-8").replace(
            "[Checks](progress/stage-2.md)", "Checks"), encoding="utf-8"),
     "stage 2: archived in progress/stage-2.md, but its Stage summary row's "
     "Title cell does not link to it"),
    (lambda d: (d / "progress.md").write_text(
        (d / "progress.md").read_text(encoding="utf-8").replace(
            "| 2 | [Checks](progress/stage-2.md) | G1 | ✅ |\n", ""),
        encoding="utf-8"),
     "progress/stage-2.md: archives stage 2, which has no row in the Stage "
     "summary table"),
    (lambda d: (d / "progress" / "stage-2.md").write_text(
        "> archived\n", encoding="utf-8"),
     "progress/stage-2.md: holds no '## Stage 2' section"),
    (lambda d: (d / "progress.md").write_text(
        (d / "progress.md").read_text(encoding="utf-8")
        + "\n## Stage 2 — Checks — ✅\n", encoding="utf-8"),
     "stage 2: archived in progress/stage-2.md and still a '## Stage 2' "
     "section of progress.md"),
])
def test_progress_and_its_archive_disagreeing_is_an_error(tmp_path, damage,
                                                          finding):
    repo = _repo(tmp_path, _progress(gates=""))
    assert _archive(repo, "--stage", "2") == 0
    assert _check(repo)[0] == []
    damage(_ddir(repo))
    errors, _ = _check(repo)
    assert any(e.startswith(finding) for e in errors), errors


def test_an_archive_file_is_a_record(tmp_path):
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    assert _ddir(repo) / "progress" / "stage-2.md" in aide._docs_records(
        _ddir(repo))
    # The settled queue whose items are all archived is a record too.
    assert _ddir(repo) / "queue" / "queue-001.md" in aide._docs_records(
        _ddir(repo))


# --------------------------------------------------------------------------- #
# eligibility
# --------------------------------------------------------------------------- #
def _refusal(text: str, stage: str, tmp_path: Path, queues: bool = True):
    repo = _repo(tmp_path, text, queues=queues)
    lines = aide.read_progress_lines(_ddir(repo) / "progress.md")
    return aide.archive_refusal(_ddir(repo), lines, stage, None)


def test_a_settled_stage_with_nothing_holding_it_is_eligible(tmp_path):
    assert _refusal(_progress(), "1", tmp_path) is None
    assert _refusal(_progress(), "2", tmp_path / "b") is None


@pytest.mark.parametrize("edit, stage, why", [
    (lambda t: t, "3", "its Stage summary row is 🚧, not ✅ or ❌"),
    (lambda t: t, "4", "it is the maintenance stage"),
    (lambda t: t, "9", "progress.md has no '## Stage 9' section"),
    (lambda t: t.replace("- ✅ Limits. *(Item 002)*", "- ⏸️ Limits. *(Item 002)*"),
     "1", "it still has 1 deliverable bullet that is not ✅ or ❌"),
    (lambda t: t.replace("- [x] Rules fire.", "- [ ] Rules fire."),
     "1", "it still has an unticked acceptance box"),
    (lambda t: t.replace("| stage 3 | ⏳ Awaiting |", "| stage 1+ | ⏳ Awaiting |"),
     "2", "human gate gate-"),
    (lambda t: t.replace("| stage 3 | ⏳ Awaiting |", "| stage 1–2 | ❌ Declined (2026-09-03) |"),
     "1", "and is ❌ Declined"),
    (lambda t: t.replace("- 📋 Charts. *(Item 006)*",
                         "- 📋 Charts. *(Item 006)*\n- ✅ Bounds again. *(Item 001)*"),
     "1", "item 001 also has a bullet outside it"),
])
def test_each_eligibility_condition_refuses_on_its_own(tmp_path, edit, stage, why):
    found = _refusal(edit(_progress()), stage, tmp_path)
    assert found is not None and why in found, found


def test_an_unreadable_gate_row_holds_every_stage(tmp_path):
    """What the row reaches is unknown, so it may be any stage: held, as
    `claim` holds every item while one stands."""
    text = _progress().replace("| stage 3 | ⏳ Awaiting | — |",
                               "| stage 3 | ⏳ Awaiting |")   # a cell short
    assert aide.unreadable_gate_rows(text.splitlines())
    for stage in ("1", "2"):
        found = _refusal(text, stage, tmp_path / stage)
        assert found is not None and "Human gates row no reader can use" in (
            found), found


def test_an_approved_gate_reaching_the_stage_does_not_hold_it(tmp_path):
    text = _progress().replace("| stage 3 | ⏳ Awaiting |",
                               "| stage 1+ | ✅ Approved (2026-09-03) |")
    assert _refusal(text, "1", tmp_path) is None


@pytest.mark.parametrize("reach, stage", [
    ("stage 1–2", "3"),     # the range ends below it
    ("stage 2-3", "1"),     # it starts above it (a hyphen reads as a range)
    ("stage 3", "2"),
])
def test_a_gate_whose_reach_misses_the_stage_does_not_hold_it(
        tmp_path, reach, stage):
    text = _progress().replace("| stage 3 | ⏳ Awaiting |",
                               f"| {reach} | ⏳ Awaiting |")
    text = text.replace("| 3 | Reports | G2 | 🚧 |", "| 3 | Reports | G2 | ✅ |")
    text = text.replace("- 📋 Charts. *(Item 006)*", "- ✅ Charts. *(Item 006)*")
    text = text.replace("- [ ] Reports render.", "- [x] Reports render.")
    assert _refusal(text, stage, tmp_path, queues=False) is None


def test_an_item_with_a_bullet_already_in_the_archive_holds_the_stage(tmp_path):
    """The archive half of the split-item rule: 003's other bullet sits in
    archived stage 2, not in progress.md."""
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    path = _ddir(repo) / "progress.md"
    path.write_text(_read(repo).replace(
        "- ✅ Limits. *(Item 002)*",
        "- ✅ Limits. *(Item 002)*\n- ✅ Lint again. *(Item 003)*"),
        encoding="utf-8")
    lines = aide.read_progress_lines(path)
    why = aide.archive_refusal(_ddir(repo), lines, "1", None)
    assert why is not None and "item 003 also has a bullet outside it" in why


def test_a_stage_whose_archive_file_exists_already_is_refused(tmp_path, capsys):
    """One stage in two places, which `check` errors on: archiving over the
    stale file would lose whichever copy was the record."""
    repo = _repo(tmp_path)
    folder = _ddir(repo) / "progress"
    folder.mkdir()
    (folder / "stage-1.md").write_text("an older copy\n", encoding="utf-8")
    before = _read(repo)
    assert _archive(repo, "--stage", "1") == 1
    err = capsys.readouterr().err
    assert "progress/stage-1.md already exists beside its section" in err
    assert (folder / "stage-1.md").read_text(encoding="utf-8") == "an older copy\n"
    assert _read(repo) == before
    assert _archive(repo) == 0            # stage 2 alone, stage 1 kept
    assert "stage 1: kept — progress/stage-1.md already exists" in (
        capsys.readouterr().out)
    assert (folder / "stage-1.md").read_text(encoding="utf-8") == "an older copy\n"


def test_an_open_queue_listing_its_items_holds_the_stage(tmp_path):
    repo = _repo(tmp_path)
    (_ddir(repo) / "queue" / "queue-003.md").write_text(
        "# Queue 003\n\n### Item 002 — Limits\n### Item 008 — New\n",
        encoding="utf-8")
    lines = aide.read_progress_lines(_ddir(repo) / "progress.md")
    why = aide.archive_refusal(_ddir(repo), lines, "1", None)
    assert why == "queue-003.md, which lists its items, is still open"


def _git(args, repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                          text=True, encoding="utf-8", check=True)


def _committed_repo(tmp_path: Path, progress: str = "") -> Path:
    repo = _repo(tmp_path, progress)
    (repo / "aide.toml").write_text(
        AIDE_TOML + '\n[git]\nmode = "local"\nmain_branch = "main"\n',
        encoding="utf-8")
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "user.name", "t"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "core.autocrlf", "false"], repo)
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "init"], repo)
    return repo


def test_an_unmerged_claim_branch_of_its_items_holds_the_stage(tmp_path, capsys):
    repo = _committed_repo(tmp_path)
    _git(["switch", "-qc", "aide/002-limits"], repo)
    (repo / "work.txt").write_text("unlanded\n", encoding="utf-8")
    _git(["add", "work.txt"], repo)
    _git(["commit", "-qm", "work"], repo)
    _git(["switch", "-q", "main"], repo)
    assert _archive(repo, "--stage", "1") == 1
    err = capsys.readouterr().err
    assert "claim branch aide/002-limits of item 002 is not merged" in err
    assert not (_ddir(repo) / "progress").exists()
    # Landed, it holds nothing.
    _git(["merge", "-q", "--no-edit", "aide/002-limits"], repo)
    assert _archive(repo, "--stage", "1") == 0


def test_an_unmerged_queue_branch_of_its_queue_holds_the_stage(tmp_path, capsys):
    repo = _committed_repo(tmp_path)
    _git(["switch", "-qc", "aide/queue-001"], repo)
    (repo / "plan.txt").write_text("unlanded\n", encoding="utf-8")
    _git(["add", "plan.txt"], repo)
    _git(["commit", "-qm", "plan"], repo)
    _git(["switch", "-q", "main"], repo)
    assert _archive(repo, "--stage", "1") == 1
    err = capsys.readouterr().err
    assert "aide/queue-001, the branch of queue-001.md" in err
    assert "is not merged" in err
    # Landed by a merge commit, its work is in main and it holds nothing.
    _git(["merge", "-q", "--no-ff", "--no-edit", "aide/queue-001"], repo)
    assert _archive(repo, "--stage", "1") == 0


def test_a_queue_branch_git_cannot_judge_holds_the_stage_and_names_both_remedies(
        tmp_path, capsys):
    """A queue branch at main's tip with no start recorded: git cannot tell a
    fast-forward landing from a branch with no commits yet, so it holds the
    stage, and the refusal names the way out either way."""
    repo = _committed_repo(tmp_path)
    _git(["branch", "aide/queue-001"], repo)
    assert _archive(repo, "--stage", "1") == 1
    err = capsys.readouterr().err
    assert "git cannot tell whether aide/queue-001" in err
    assert "'aide gc --merged --yes'" in err
    assert "'aide queue restack 001 --base main'" in err


# --------------------------------------------------------------------------- #
# the verbs
# --------------------------------------------------------------------------- #
def test_archive_with_no_stage_takes_every_eligible_one_and_names_the_rest(
        tmp_path, capsys):
    repo = _repo(tmp_path)
    assert _archive(repo) == 0
    out = capsys.readouterr().out
    assert "stage 1: archived to progress/stage-1.md" in out
    assert "stage 2: archived to progress/stage-2.md" in out
    assert "stage 4: kept — it is the maintenance stage" in out
    assert "stage 3" not in out           # 🚧: not a settled stage
    assert sorted(aide.archived_stage_files(_ddir(repo))) == [1, 2]
    before = _read(repo)
    assert _archive(repo) == 0             # nothing left: no change
    assert "no stage is eligible" in capsys.readouterr().out
    assert _read(repo) == before


def test_archive_of_an_ineligible_stage_writes_nothing(tmp_path, capsys):
    repo = _repo(tmp_path)
    before = _read(repo)
    assert _archive(repo, "--stage", "3") == 1
    err = capsys.readouterr().err
    assert "stage 3 is not archived — its Stage summary row is 🚧" in err
    assert _read(repo) == before and not (_ddir(repo) / "progress").exists()


def test_unarchive_moves_the_stage_back_and_removes_the_file(tmp_path, capsys):
    repo = _repo(tmp_path)
    before = _read(repo)
    assert _archive(repo, "--stage", "2") == 0
    assert _unarchive(repo, "--stage", "2") == 0
    assert "stage 2: moved back to progress.md" in capsys.readouterr().out
    assert _read(repo) == before
    assert not (_ddir(repo) / "progress").exists()


def test_unarchive_refuses_a_stage_that_is_not_archived(tmp_path, capsys):
    repo = _repo(tmp_path)
    assert _unarchive(repo, "--stage", "2") == 1
    assert "stage 2 is not archived" in capsys.readouterr().err


def test_unarchive_refuses_a_stage_progress_md_still_has(tmp_path, capsys):
    repo = _repo(tmp_path)
    folder = _ddir(repo) / "progress"
    folder.mkdir()
    (folder / "stage-2.md").write_text("## Stage 2 — Checks — ✅\n",
                                       encoding="utf-8")
    before = _read(repo)
    assert _unarchive(repo, "--stage", "2") == 1
    assert "already has a '## Stage 2' section" in capsys.readouterr().err
    assert _read(repo) == before and (folder / "stage-2.md").is_file()


@pytest.mark.parametrize("verb, argv", [
    ("archive", ["2"]), ("archive", ["--stage", "2", "--item", "3"]),
    ("archive", ["--reason", "why"]), ("archive", ["--all"]),
    ("unarchive", []), ("unarchive", ["--stage", "2", "--text", "x"]),
    ("unarchive", ["2"]),
])
def test_both_verbs_refuse_any_argument_but_stage_and_no_commit(
        tmp_path, capsys, verb, argv):
    repo = _repo(tmp_path)
    before = _read(repo)
    run = _archive if verb == "archive" else _unarchive
    assert run(repo, *argv) == 2
    assert f"usage: aide progress {verb}" in capsys.readouterr().err
    assert _read(repo) == before


# --------------------------------------------------------------------------- #
# writers refuse the archive
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("argv", [
    ["set", "3", "done"],
    ["set", "4", "restored", "--reason", "wanted"],
    ["reopen", "3", "--reason", "broken"],
    ["reword", "--item", "3", "--text", "Lint everything"],
    ["accept", "2", "--criterion", "1"],
    ["amend", "2", "--criterion", "1", "--evidence", "more"],
    ["retract", "2", "--criterion", "1", "--reason", "no"],
    ["reword", "2", "--criterion", "1", "--text", "Checks pass"],
    ["set", "--stage", "2", "--deliverable", "1", "deferred", "--reason", "x"],
])
def test_no_writer_reaches_into_the_archive(tmp_path, capsys, argv):
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    capsys.readouterr()
    before = (_read(repo), _read(repo, "progress/stage-2.md"))
    assert aide.main(["--repo", str(repo), "progress", *argv,
                      "--no-commit"]) == 1
    err = capsys.readouterr().err
    assert "progress/stage-2.md" in err
    assert "`aide progress unarchive --stage 2`" in err
    assert (_read(repo), _read(repo, "progress/stage-2.md")) == before


def test_a_back_fill_into_an_archived_stage_is_refused(tmp_path, capsys):
    """An item no bullet names, whose spec's stage is archived: the self-heal
    would insert its bullet into the archive."""
    repo = _repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    (_ddir(repo) / "items").mkdir()
    (_ddir(repo) / "items" / "009-late.md").write_text(
        "# Item 009 — Late\n\n> **Stage:** 2\n", encoding="utf-8")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "progress", "set", "9", "done",
                      "--no-commit"]) == 1
    assert "`aide progress unarchive --stage 2`" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# the commit
# --------------------------------------------------------------------------- #
def test_archive_and_unarchive_commit_both_files(tmp_path):
    repo = _committed_repo(tmp_path)
    argv = ["--repo", str(repo), "progress"]
    assert aide.main([*argv, "archive", "--stage", "2"]) == 0
    assert _git(["log", "-1", "--format=%s"], repo).stdout.strip() == (
        "progress(aide): archive stage 2")
    assert _git(["status", "--porcelain"], repo).stdout == ""
    shown = _git(["show", "--name-only", "--format=", "HEAD"], repo).stdout
    assert sorted(shown.split()) == ["docs/aide/progress.md",
                                     "docs/aide/progress/stage-2.md"]
    assert aide.main([*argv, "unarchive", "--stage", "2"]) == 0
    assert _git(["log", "-1", "--format=%s"], repo).stdout.strip() == (
        "progress(aide): unarchive stage 2")
    assert _git(["status", "--porcelain"], repo).stdout == ""
    assert _git(["diff", "HEAD~2", "--stat"], repo).stdout == ""


def test_an_unarchive_whose_commit_fails_is_put_back(tmp_path):
    repo = _committed_repo(tmp_path)
    argv = ["--repo", str(repo), "progress"]
    assert aide.main([*argv, "archive", "--stage", "2"]) == 0
    before = (_read(repo), _read(repo, "progress/stage-2.md"))
    head = _git(["rev-parse", "HEAD"], repo).stdout
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert aide.main([*argv, "unarchive", "--stage", "2"]) == 1
    finally:
        lock.unlink()
    assert (_read(repo), _read(repo, "progress/stage-2.md")) == before
    assert _git(["rev-parse", "HEAD"], repo).stdout == head


def test_an_archive_whose_commit_fails_is_put_back(tmp_path):
    repo = _committed_repo(tmp_path)
    before = _read(repo)
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert aide.main(["--repo", str(repo), "progress", "archive"]) == 1
    finally:
        lock.unlink()
    assert _read(repo) == before
    assert not (_ddir(repo) / "progress").exists()   # the folder it made too
    assert _git(["status", "--porcelain"], repo).stdout == ""


@pytest.mark.parametrize("staged", [False, True], ids=["untracked", "staged"])
def test_an_uncommitted_archive_is_unarchived_and_committed(tmp_path, staged):
    """`archive --no-commit` leaves stage-2.md uncommitted — untracked, or
    only staged: the committing unarchive removes it and commits progress.md
    alone, rather than failing on a pathspec git does not know, on every
    re-run, and leaves no staged add of the file behind."""
    repo = _committed_repo(tmp_path)
    original = _read(repo)
    assert _archive(repo, "--stage", "2") == 0
    # progress.md committed by hand, the new file forgotten.
    _git(["commit", "-qm", "half", "--", "docs/aide/progress.md"], repo)
    if staged:
        _git(["add", "--", "docs/aide/progress/stage-2.md"], repo)
    head = _git(["rev-parse", "HEAD"], repo).stdout
    assert aide.main(["--repo", str(repo), "progress", "unarchive",
                      "--stage", "2"]) == 0
    assert _git(["rev-parse", "HEAD~1"], repo).stdout == head
    assert _git(["log", "-1", "--format=%s"], repo).stdout.strip() == (
        "progress(aide): unarchive stage 2")
    assert _git(["status", "--porcelain"], repo).stdout == ""
    assert _read(repo) == original
    assert not (_ddir(repo) / "progress").exists()


def _tree(repo: Path):
    """Every markdown file under docs/aide — so every file `archive` and
    `unarchive` write — with its text, and HEAD."""
    ddir = _ddir(repo)
    files = sorted(p.relative_to(ddir).as_posix() for p in ddir.rglob("*.md"))
    return ({f: _read(repo, f) for f in files},
            _git(["rev-parse", "HEAD"], repo).stdout)


def test_both_verbs_refuse_on_a_claim_branch(tmp_path, capsys):
    """Issue #481: the files they write are in no item's Authorised paths,
    so on a claim branch the move would be a diff `aide scope` reports.
    Each refuses there, exit 1 and writing nothing, and runs on main."""
    repo = _committed_repo(tmp_path)
    argv = ["--repo", str(repo), "progress"]
    _git(["switch", "-qc", "aide/009-late"], repo)
    before = _tree(repo)
    assert aide.main([*argv, "archive", "--stage", "2"]) == 1
    assert _tree(repo) == before
    assert not (_ddir(repo) / "progress").exists()
    _git(["switch", "-q", "main"], repo)
    assert aide.main([*argv, "archive", "--stage", "2"]) == 0
    _git(["switch", "-q", "aide/009-late"], repo)
    _git(["merge", "-q", "--ff-only", "main"], repo)
    before = _tree(repo)
    assert aide.main([*argv, "unarchive", "--stage", "2"]) == 1
    assert _tree(repo) == before
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()
    _git(["switch", "-q", "main"], repo)
    assert aide.main([*argv, "unarchive", "--stage", "2"]) == 0
    assert not (_ddir(repo) / "progress").exists()


def test_both_verbs_run_on_a_queue_branch(tmp_path):
    repo = _committed_repo(tmp_path)
    argv = ["--repo", str(repo), "progress"]
    _git(["switch", "-qc", "aide/queue-002"], repo)
    assert aide.main([*argv, "archive", "--stage", "2"]) == 0
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()
    assert aide.main([*argv, "unarchive", "--stage", "2"]) == 0
    assert not (_ddir(repo) / "progress").exists()
    assert _git(["status", "--porcelain"], repo).stdout == ""


@pytest.mark.parametrize("branch, prefix, refused", [
    ("aide/009-late", "aide/", True),
    ("work/009-late", "work/", True),
    ("aide/009-late", "work/", False),
    ("aide/queue-002", "aide/", False),
    ("aide/specs-queue-002", "aide/", False),
    ("main", "aide/", False),
    ("feature", "aide/", False),
    (None, "aide/", False),
], ids=["claim", "custom-prefix-claim", "other-prefix", "queue",
        "specs-queue", "main", "other-branch", "detached"])
def test_the_gate_refuses_a_claim_branch_alone(tmp_path, branch, prefix,
                                               refused):
    """Issue #481: the gate reads a claim branch the way `claim` and `scope`
    do — after the configured prefix, and never a queue branch."""
    repo = _committed_repo(tmp_path)
    if branch is None:
        _git(["switch", "-q", "--detach"], repo)
    elif branch != "main":
        _git(["switch", "-qc", branch], repo)
    config = {"git": {"branch_prefix": prefix, "main_branch": "main"}}
    why = aide._archive_claim_branch_refusal(repo, config, "tag")
    assert (why is not None) is refused
    if refused:
        assert why.startswith(f"tag: {branch} is a claim branch")


def test_the_gate_passes_outside_a_repository(tmp_path):
    config = {"git": {"branch_prefix": "aide/", "main_branch": "main"}}
    assert aide._archive_claim_branch_refusal(tmp_path, config, "t") is None


def test_merge_refuses_an_item_of_an_archived_stage(tmp_path, capsys):
    repo = _committed_repo(tmp_path)
    assert aide.main(["--repo", str(repo), "progress", "archive",
                      "--stage", "2"]) == 0
    _git(["switch", "-qc", "aide/003-lint"], repo)
    _git(["switch", "-q", "main"], repo)
    capsys.readouterr()
    head = _git(["rev-parse", "HEAD"], repo).stdout
    assert aide.main(["--repo", str(repo), "merge", "3", "--base", "main",
                      "--no-test"]) == 1
    err = capsys.readouterr().err
    assert "`aide progress unarchive --stage 2`" in err
    assert "nothing was merged or pushed" in err
    assert _git(["rev-parse", "HEAD"], repo).stdout == head


# --------------------------------------------------------------------------- #
# every reader of item status, after an archive — one guard per read site
# --------------------------------------------------------------------------- #
#: Item 006 waits on 003 (✅) and 004 (❌), both in stage 2; its A1 pins
#: 004's interface, and 004 left the way without landing.
SPEC_006 = """\
# Item 006 — Charts

> **Stage:** 3 — Reports

## Dependencies

- Item 003 (lint) and Item 004 (fuzz).

## Assumptions

- **A1:** item 004's corpus is a directory of files.
"""


def _archived(tmp_path: Path, files: Optional[Dict[str, str]] = None,
              gates: str = "") -> Path:
    """Stages 1 and 2 archived and committed; by default no gate holds
    stage 3. *files* are written under docs_dir first."""
    repo = _committed_repo(tmp_path, _progress(gates=gates))
    for rel, text in (files or {}).items():
        path = _ddir(repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-qm", "specs", "--allow-empty"], repo)
    assert aide.main(["--repo", str(repo), "progress", "archive"]) == 0
    assert sorted(aide.archived_stage_files(_ddir(repo))) == [1, 2]
    return repo


def test_claim_offers_an_item_whose_dependencies_are_archived(tmp_path, capsys):
    """`_open_queue_texts` reads queue-001 as settled, `_pick_item` reads
    006's dependencies as having left the way, and `_interface_pin_report`
    reads 004 as ❌ — no code to check against."""
    repo = _archived(tmp_path, {"items/006-charts.md": SPEC_006})
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    out = capsys.readouterr().out
    assert _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.startswith(
        "aide/006-")
    assert "A1 (item 004, no code to check against)" in out


def test_claim_held_by_a_gate_reports_no_archived_item_as_waiting(
        tmp_path, capsys):
    """The stage 3 gate holds 006: the report (`_report_nothing_claimable`)
    names the gate, and no archived item as open work."""
    repo = _archived(tmp_path, {"items/006-charts.md": SPEC_006}, gates=GATES)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("none left"), out
    assert "Ship the report format" in out
    assert not any(f"item {n:03d}" in out for n in (1, 2, 3, 4)), out


def test_status_reads_an_archived_queue_as_done(tmp_path, capsys):
    repo = _archived(tmp_path)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "status"]) == 0
    out = capsys.readouterr().out
    assert "queue-001.md: done" in out
    assert "queue-002.md: open (live) — 1/2 items open (006)" in out


def test_gc_deletes_the_landed_branch_of_an_archived_item(tmp_path):
    repo = _archived(tmp_path)
    _git(["branch", "aide/003-lint"], repo)
    assert aide.main(["--repo", str(repo), "gc", "--yes"]) == 0
    assert "aide/003-lint" not in _git(["branch"], repo).stdout


def test_check_queue_discounts_archived_items_on_both_sides(tmp_path):
    """001 and 002 both claim one path; both are archived ✅, so the overlap
    is between two records and never reported (`queue_spec_findings`)."""
    spec = ("# Item {n} — X\n\n> **Stage:** 1\n\n## Authorised paths\n\n"
            "**May change:**\n\n- `src/rules.py` — the rules\n")
    repo = _archived(tmp_path, {"items/001-x.md": spec.format(n="001"),
                                "items/002-x.md": spec.format(n="002")})
    findings, _ = aide.queue_spec_findings(repo, aide.load_config(repo), 1)
    assert findings == []


def test_queue_end_findings_read_an_archived_queue_as_spent(tmp_path):
    """002 is queue-001's queue-end item, ✅ in archived stage 1: spent, so
    not idle over a stage the queue no longer closes in progress.md."""
    queue = QUEUE_1.replace("### Item 002 — Limits",
                            "### Item 002: Validate stage 1: Rules")
    repo = _archived(tmp_path, {"queue/queue-001.md": queue})
    assert aide.queue_end_findings(repo, aide.load_config(repo), 1) == []


def test_claim_on_an_archived_queue_finds_nothing_open(tmp_path, capsys):
    """`_report_nothing_claimable` over the named queue: every item is
    archived ✅ or ❌, so the report is the bare exhaustion."""
    repo = _archived(tmp_path)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "claim", "--dry-run",
                      "--queue", "1"]) == 0
    assert capsys.readouterr().out.strip() == "none left"


def test_the_landed_review_reader_sees_archived_items(tmp_path):
    repo = _archived(tmp_path)
    status = aide._progress_item_status(repo, aide.load_config(repo))
    assert status[3] == "complete" and status[4] == "excluded"


def test_an_item_archived_and_planned_in_a_withdrawn_stage_is_not_withdrawn(
        tmp_path):
    """A hand edit no verb makes, read as `withdrawn_stage_items` reads a
    bullet in a live stage: an item with a bullet outside the withdrawn
    stage — here in the archive — is not withdrawn whole."""
    repo = _repo(tmp_path, _progress(gates=""))
    assert _archive(repo, "--stage", "2") == 0
    path = _ddir(repo) / "progress.md"
    path.write_text(_read(repo).replace("| 3 | Reports | G2 | 🚧 |",
                                        "| 3 | Reports | G2 | ❌ |").replace(
        "- 📋 Charts. *(Item 006)*", "- 📋 Charts. *(Item 006)*\n"
        "- 📋 Lint again. *(Item 003)*"), encoding="utf-8")
    lines = aide.read_progress_lines(path)
    assert 3 not in aide.withdrawn_stage_items(lines)
    assert 6 in aide.withdrawn_stage_items(lines)


def test_claim_names_no_archived_item_among_withdrawn_queued_work(
        tmp_path, capsys):
    """Stage 3 withdrawn, with 006 📋 there and a hand-made 📋 copy of 003,
    whose ✅ bullet is archived: no queue is open, and the refusal names
    006 alone (`_withdrawn_queued_lines`)."""
    repo = _archived(tmp_path)
    path = _ddir(repo) / "progress.md"
    path.write_text(_read(repo).replace("| 3 | Reports | G2 | 🚧 |",
                                        "| 3 | Reports | G2 | ❌ |").replace(
        "- 📋 Charts. *(Item 006)*", "- 📋 Charts. *(Item 006)*\n"
        "- 📋 Lint again. *(Item 003)*"), encoding="utf-8")
    _git(["commit", "-qam", "stage 3 withdrawn"], repo)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 1
    err = capsys.readouterr().err
    assert "  006 item 6 — in withdrawn stage 3" in err, err
    assert "003" not in err, err



# --------------------------------------------------------------------------- #
# roadmap.md's half — issue #476
# --------------------------------------------------------------------------- #
VISION = """\
# Demo — Vision

## Objectives

| Code | Objective |
|------|-----------|
| G1 | Rules |
| G2 | Reports |
"""

ROADMAP = """\
<!-- aide-template: roadmap 3 -->
# Demo — Development Roadmap

> **Status:** Draft v1

---

## Strategy

### Objective → stage coverage

| Objective | Delivered by |
|-----------|--------------|
| G1 Rules | Stage 1, 2 |
| G2 Reports | Stage 2, 3 |

### Stage dependency graph

```
1 ─► 2 ─► 3
```

---

## Stage 1 — Rules

**Goal.** Rules fire.

**Deliverables.**

- Bounds and limits.

**Dependencies.** None.

**Validation / acceptance.**

- Rules fire.

---

## Stage 2 — Checks

**Goal.** Checks run.

> Annotated later: a note the freeze kept out of reach.

**Deliverables.**

- Lint and fuzz.

**Dependencies.** Stage 1.

**Validation / acceptance.**

- Checks run.

---

## Stage 3 — Reports

**Goal.** Reports render.

**Deliverables.**

- Summary and charts.

**Dependencies.** Stage 2.

**Validation / acceptance.**

- Reports render.

---

## Stage 4 — Maintenance

**Goal.** Repairs shipped work.

**Deliverables.** Added to `progress.md` by each maintenance queue.

**Dependencies.** None.

---

# Backlog

- An idea.
"""


def _road_repo(tmp_path: Path, roadmap: str = ROADMAP, **kw) -> Path:
    repo = _repo(tmp_path, **kw)
    (_ddir(repo) / "roadmap.md").write_text(roadmap, encoding="utf-8")
    (_ddir(repo) / "vision.md").write_text(VISION, encoding="utf-8")
    return repo


def test_archive_roadmap_text_leaves_a_stub_and_moves_the_section():
    updated, archived = aide.archive_roadmap_text(ROADMAP, 2)
    stub = "## Stage 2 — Checks\n\nArchived in [roadmap/stage-2.md](roadmap/stage-2.md).\n\n---\n\n## Stage 3"
    assert stub in updated
    assert "Annotated later" not in updated
    alines = archived.splitlines()
    assert alines[0] == aide._roadmap_archive_header(2)
    assert "../roadmap.md" in alines[0]
    section = ROADMAP[ROADMAP.index("## Stage 2"):ROADMAP.index("## Stage 3")]
    body = section.rstrip().removesuffix("---").rstrip()
    assert archived == aide._roadmap_archive_header(2) + "\n\n" + body + "\n"
    stub_bytes = len(("## Stage 2 — Checks\n\n"
                      + aide.roadmap_stub_line(2) + "\n").encode("utf-8"))
    assert stub_bytes < 100
    assert aide.roadmap_stub_stages(updated.splitlines()) == {2}
    assert aide.roadmap_whole_stages(updated.splitlines()) == {1, 3, 4}


@pytest.mark.parametrize("stage", [1, 2, 3, 4])
def test_unarchive_roadmap_text_puts_back_exactly_what_archive_took(stage):
    """First, middle and last stage, the last before the Backlog heading."""
    updated, archived = aide.archive_roadmap_text(ROADMAP, stage)
    assert aide.unarchive_roadmap_text(updated, archived, stage) == ROADMAP


def test_archive_moves_the_roadmap_section_with_the_progress_section(
        tmp_path, capsys):
    repo = _road_repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    out = capsys.readouterr().out
    assert "stage 2: archived to progress/stage-2.md" in out
    assert "stage 2: roadmap.md's section archived to roadmap/stage-2.md" in out
    road = _read(repo, "roadmap.md")
    assert "Archived in [roadmap/stage-2.md](roadmap/stage-2.md)." in road
    assert "Lint and fuzz" not in road
    assert "Lint and fuzz" in _read(repo, "roadmap/stage-2.md")


def test_archive_with_no_stage_moves_every_eligible_roadmap_section(
        tmp_path):
    repo = _road_repo(tmp_path)
    assert _archive(repo) == 0
    assert sorted(aide.roadmap_archived_files(_ddir(repo))) == [1, 2]
    rlines = _read(repo, "roadmap.md").splitlines()
    assert aide.roadmap_stub_stages(rlines) == {1, 2}
    assert aide.roadmap_whole_stages(rlines) == {3, 4}


def test_check_reads_a_stubbed_roadmap_as_it_read_the_whole_one(tmp_path):
    """No roadmap reader in `aide check` changes its findings over a stub:
    shape, coverage, dependencies, the maintenance rules, the acceptance
    mirror. Stage 2's blockquote was never named (✅), and stage 3's
    dependency on stage 2 needs only its number."""
    repo = _road_repo(tmp_path, progress=_progress(gates=""))
    before = _check(repo)
    assert not any(w.startswith("roadmap.md") for w in before[1]), before
    assert _archive(repo) == 0
    assert _check(repo) == before


def test_a_stage_archived_without_its_roadmap_section_is_caught_up(
        tmp_path, capsys):
    """A stage archived by 2.50.x: progress.md's half only. `check` warns,
    and `archive` — with or without --stage — moves the roadmap half alone."""
    repo = _road_repo(tmp_path)
    road = _read(repo, "roadmap.md")
    (_ddir(repo) / "roadmap.md").unlink()
    assert _archive(repo) == 0                 # stages 1 and 2, no roadmap
    (_ddir(repo) / "roadmap.md").write_text(road, encoding="utf-8")
    progress = _read(repo)
    _errors, warnings = _check(repo)
    for n in (1, 2):
        assert any(w.startswith(
            f"stage {n}: archived in progress/stage-{n}.md while its "
            f"roadmap.md section is whole") for w in warnings), warnings
    capsys.readouterr()
    assert _archive(repo, "--stage", "1") == 0
    out = capsys.readouterr().out
    assert "stage 1: roadmap.md's section archived to roadmap/stage-1.md" in out
    assert "progress/stage-1.md" not in out
    assert _archive(repo) == 0
    assert sorted(aide.roadmap_archived_files(_ddir(repo))) == [1, 2]
    assert _read(repo) == progress             # progress.md untouched
    assert not any("section is whole" in w for w in _check(repo)[1])
    assert _archive(repo) == 0
    assert "no stage is eligible" in capsys.readouterr().out


def test_a_roadmap_with_no_section_for_the_stage_lets_progress_move_alone(
        tmp_path, capsys):
    road = ROADMAP.replace(
        ROADMAP[ROADMAP.index("## Stage 2"):ROADMAP.index("## Stage 3")], "")
    repo = _road_repo(tmp_path, roadmap=road)
    assert _archive(repo, "--stage", "2") == 0
    out = capsys.readouterr().out
    assert "stage 2: archived to progress/stage-2.md" in out
    assert ("stage 2: roadmap.md has no '## Stage 2' section, so "
            "progress.md's alone moved") in out
    assert _read(repo, "roadmap.md") == road
    assert not (_ddir(repo) / "roadmap").exists()


@pytest.mark.parametrize("damage, why", [
    (lambda d: (d / "roadmap").mkdir() or (d / "roadmap" / "stage-2.md")
     .write_text("## Stage 2 — Checks\n", encoding="utf-8"),
     "roadmap/stage-2.md already exists while its progress.md section is "
     "live"),
    (lambda d: (d / "roadmap.md").write_text(
        aide.archive_roadmap_text((d / "roadmap.md").read_text(
            encoding="utf-8"), 2)[0], encoding="utf-8"),
     "roadmap.md's '## Stage 2' section is an archive stub with no "
     "roadmap/stage-2.md behind it"),
])
def test_a_roadmap_half_already_moved_holds_the_stage(tmp_path, capsys,
                                                      damage, why):
    repo = _road_repo(tmp_path)
    damage(_ddir(repo))
    before = (_read(repo), _read(repo, "roadmap.md"))
    assert _archive(repo, "--stage", "2") == 1
    assert why in capsys.readouterr().err
    assert (_read(repo), _read(repo, "roadmap.md")) == before
    assert not (_ddir(repo) / "progress").exists()


def _stub_without_file(d: Path) -> None:
    (d / "roadmap" / "stage-2.md").unlink()


def _file_beside_whole(d: Path) -> None:
    (d / "roadmap.md").write_text(ROADMAP, encoding="utf-8")


def _file_without_stub(d: Path) -> None:
    (d / "roadmap.md").write_text(ROADMAP.replace(
        ROADMAP[ROADMAP.index("## Stage 2"):ROADMAP.index("## Stage 3")], ""),
        encoding="utf-8")


def _file_without_section(d: Path) -> None:
    (d / "roadmap" / "stage-2.md").write_text("> archived\n", encoding="utf-8")


def _progress_moved_back(d: Path) -> None:
    text = (d / "progress.md").read_text(encoding="utf-8")
    archived = (d / "progress" / "stage-2.md").read_text(encoding="utf-8")
    (d / "progress.md").write_text(
        aide.unarchive_stage_text(text, archived, 2), encoding="utf-8")
    (d / "progress" / "stage-2.md").unlink()


def _stub_retitled(d: Path) -> None:
    road = (d / "roadmap.md").read_text(encoding="utf-8")
    (d / "roadmap.md").write_text(road.replace(
        "## Stage 2 — Checks\n", "## Stage 2 — Maintenance\n"),
        encoding="utf-8")


def _stub_with_text(d: Path) -> None:
    road = (d / "roadmap.md").read_text(encoding="utf-8")
    (d / "roadmap.md").write_text(road.replace(
        "Archived in [roadmap/stage-2.md](roadmap/stage-2.md).\n",
        "Archived in [roadmap/stage-2.md](roadmap/stage-2.md).\n\n"
        "> Annotated after archiving.\n"), encoding="utf-8")


@pytest.mark.parametrize("damage, finding", [
    (_stub_with_text,
     "stage 2's stub holds text besides its heading and its line linking to "
     "roadmap/stage-2.md"),
    (_stub_retitled,
     "roadmap.md: stage 2's stub is headed '## Stage 2 — Maintenance', but "
     "roadmap/stage-2.md holds '## Stage 2 — Checks'"),
    (_stub_without_file,
     "roadmap.md: stage 2's section is a stub linking to roadmap/stage-2.md, "
     "which does not exist"),
    (_file_beside_whole,
     "stage 2: archived in roadmap/stage-2.md and still a whole '## Stage 2' "
     "section of roadmap.md"),
    (_file_without_stub,
     "roadmap/stage-2.md: archives stage 2, which roadmap.md has no "
     "'## Stage 2' stub for"),
    (_file_without_section,
     "roadmap/stage-2.md: holds no '## Stage 2' section"),
    (_progress_moved_back,
     "stage 2: its roadmap.md section is archived in roadmap/stage-2.md while "
     "its progress.md section is live"),
], ids=["stub-with-text", "stub-retitled", "stub-without-file", "file-beside-whole", "file-without-stub",
        "file-without-section", "progress-live"])
def test_roadmap_and_its_archive_disagreeing_is_an_error(tmp_path, damage,
                                                         finding):
    repo = _road_repo(tmp_path, progress=_progress(gates=""))
    assert _archive(repo, "--stage", "2") == 0
    assert _check(repo)[0] == []
    damage(_ddir(repo))
    errors, _ = _check(repo)
    assert any(finding in e for e in errors), errors


def test_a_roadmap_archive_file_is_a_record(tmp_path):
    repo = _road_repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    assert _ddir(repo) / "roadmap" / "stage-2.md" in aide._docs_records(
        _ddir(repo))


def test_unarchive_moves_both_halves_back(tmp_path, capsys):
    repo = _road_repo(tmp_path)
    before = (_read(repo), _read(repo, "roadmap.md"))
    assert _archive(repo, "--stage", "2") == 0
    capsys.readouterr()
    assert _unarchive(repo, "--stage", "2") == 0
    out = capsys.readouterr().out
    assert "stage 2: moved back to progress.md from progress/stage-2.md" in out
    assert "stage 2: moved back to roadmap.md from roadmap/stage-2.md" in out
    assert (_read(repo), _read(repo, "roadmap.md")) == before
    assert not (_ddir(repo) / "progress").exists()
    assert not (_ddir(repo) / "roadmap").exists()


def test_unarchive_moves_back_whichever_half_is_archived(tmp_path, capsys):
    """progress.md's half alone (archived by 2.50.x), and roadmap.md's half
    alone — the disagreement `check` errors on, whose remedy this is."""
    repo = _road_repo(tmp_path)
    road = _read(repo, "roadmap.md")
    (_ddir(repo) / "roadmap.md").unlink()
    assert _archive(repo, "--stage", "2") == 0
    (_ddir(repo) / "roadmap.md").write_text(road, encoding="utf-8")
    assert _unarchive(repo, "--stage", "2") == 0
    assert _read(repo, "roadmap.md") == road
    assert not (_ddir(repo) / "progress").exists()

    assert _archive(repo, "--stage", "2") == 0
    _progress_moved_back(_ddir(repo))
    progress = _read(repo)
    capsys.readouterr()
    assert _unarchive(repo, "--stage", "2") == 0
    out = capsys.readouterr().out
    assert "moved back to roadmap.md" in out
    assert "moved back to progress.md" not in out
    assert (_read(repo), _read(repo, "roadmap.md")) == (progress, road)


def test_unarchive_refuses_a_roadmap_with_no_stub_to_replace(tmp_path, capsys):
    repo = _road_repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    _file_beside_whole(_ddir(repo))
    before = (_read(repo), _read(repo, "roadmap.md"))
    capsys.readouterr()
    assert _unarchive(repo, "--stage", "2") == 1
    assert ("roadmap.md already has a '## Stage 2' section beside "
            "roadmap/stage-2.md" in capsys.readouterr().err)
    assert (_read(repo), _read(repo, "roadmap.md")) == before
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()


def test_archive_and_unarchive_commit_the_roadmap_half_too(tmp_path):
    repo = _repo(tmp_path)
    (_ddir(repo) / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
    (repo / "aide.toml").write_text(
        AIDE_TOML + '\n[git]\nmode = "local"\nmain_branch = "main"\n',
        encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"],
                 ["config", "user.email", "t@example.com"],
                 ["config", "core.autocrlf", "false"], ["add", "-A"],
                 ["commit", "-qm", "init"]):
        _git(args, repo)
    argv = ["--repo", str(repo), "progress"]
    assert aide.main([*argv, "archive", "--stage", "2"]) == 0
    assert _git(["status", "--porcelain"], repo).stdout == ""
    shown = _git(["show", "--name-only", "--format=", "HEAD"], repo).stdout
    assert sorted(shown.split()) == ["docs/aide/progress.md",
                                     "docs/aide/progress/stage-2.md",
                                     "docs/aide/roadmap.md",
                                     "docs/aide/roadmap/stage-2.md"]
    assert aide.main([*argv, "unarchive", "--stage", "2"]) == 0
    assert _git(["status", "--porcelain"], repo).stdout == ""
    assert _git(["diff", "HEAD~2", "--stat"], repo).stdout == ""


def test_a_failed_archive_commit_puts_the_roadmap_back(tmp_path):
    repo = _repo(tmp_path)
    (_ddir(repo) / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
    (repo / "aide.toml").write_text(
        AIDE_TOML + '\n[git]\nmode = "local"\nmain_branch = "main"\n',
        encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"],
                 ["config", "user.email", "t@example.com"],
                 ["config", "core.autocrlf", "false"], ["add", "-A"],
                 ["commit", "-qm", "init"]):
        _git(args, repo)
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert aide.main(["--repo", str(repo), "progress", "archive"]) == 1
    finally:
        lock.unlink()
    assert _read(repo, "roadmap.md") == ROADMAP
    assert not (_ddir(repo) / "roadmap").exists()
    assert _git(["status", "--porcelain"], repo).stdout == ""


def test_unarchive_refuses_a_roadmap_with_no_section_for_the_stage(
        tmp_path, capsys):
    repo = _road_repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    _file_without_stub(_ddir(repo))
    before = (_read(repo), _read(repo, "roadmap.md"))
    capsys.readouterr()
    assert _unarchive(repo, "--stage", "2") == 1
    assert ("roadmap.md has no '## Stage 2' stub to put the section back in "
            "place of" in capsys.readouterr().err)
    assert (_read(repo), _read(repo, "roadmap.md")) == before
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()
    assert (_ddir(repo) / "roadmap" / "stage-2.md").is_file()


def test_unarchive_refuses_when_there_is_no_roadmap_md(tmp_path, capsys):
    repo = _road_repo(tmp_path)
    assert _archive(repo, "--stage", "2") == 0
    (_ddir(repo) / "roadmap.md").unlink()
    before = _read(repo)
    capsys.readouterr()
    assert _unarchive(repo, "--stage", "2") == 1
    assert ("there is no roadmap.md to move roadmap/stage-2.md back into"
            in capsys.readouterr().err)
    assert _read(repo) == before
    assert (_ddir(repo) / "progress" / "stage-2.md").is_file()
    assert (_ddir(repo) / "roadmap" / "stage-2.md").is_file()


def test_an_archived_stage_naming_a_later_stage_is_no_longer_warned_on(
        tmp_path):
    """The one roadmap reader whose findings a stub changes: the stub has no
    Dependencies slot, so a settled stage whose slot named a later stage is
    warned on while whole and silent once archived. Intended — the stage has
    closed, so there is no closure left for the later stage to stand in the
    way of — and the archive file keeps the slot as written."""
    road = ROADMAP.replace("**Dependencies.** Stage 1.",
                        "**Dependencies.** Stage 3.", 1)
    repo = _road_repo(tmp_path, roadmap=road, progress=_progress(gates=""))
    forward = "roadmap.md: stage 2's Dependencies name later stage 3"
    assert any(w.startswith(forward) for w in _check(repo)[1])
    assert _archive(repo, "--stage", "2") == 0
    assert not any(w.startswith(forward) for w in _check(repo)[1])
    assert "**Dependencies.** Stage 3." in _read(repo, "roadmap/stage-2.md")


# --------------------------------------------------------------------------- #
# relative links in a moved section — issue #476
# --------------------------------------------------------------------------- #
LINKED = [
    'See [the vision](vision.md) and ![a chart](img/a.png "Chart").',
    '- [x] Specified in [item 150](items/150-x.md#decisions "Decisions").',
    "[web](https://x.org/a.md) [top](#goal) [abs](/docs/a.md) "
    "<https://auto.org/b.md> [mail](mailto:a@b.org)",
    "Written as code: `[x](vision.md)`, outside it [y](queue/queue-001.md).",
    "```",
    "[fenced](vision.md)",
    "```",
    "~~~~",
    "[tilde](vision.md)",
    "~~~~",
    '[ref]: items/001-x.md "Item 1"',
    "[parent](../README.md)",
]

UP = [
    'See [the vision](../vision.md) and ![a chart](../img/a.png "Chart").',
    '- [x] Specified in [item 150](../items/150-x.md#decisions "Decisions").',
    "[web](https://x.org/a.md) [top](#goal) [abs](/docs/a.md) "
    "<https://auto.org/b.md> [mail](mailto:a@b.org)",
    "Written as code: `[x](vision.md)`, outside it [y](../queue/queue-001.md).",
    "```",
    "[fenced](vision.md)",
    "```",
    "~~~~",
    "[tilde](vision.md)",
    "~~~~",
    '[ref]: ../items/001-x.md "Item 1"',
    "[parent](../../README.md)",
]


def test_rebase_links_moves_only_relative_targets_outside_code():
    assert aide.rebase_links(LINKED, True) == UP
    assert aide.rebase_links(UP, False) == LINKED
    # Down strips exactly one ../ and leaves a target without one as it is.
    assert aide.rebase_links(["[a](x.md) [b](../../y.md)"], False) == [
        "[a](x.md) [b](../y.md)"]


def test_archive_rebases_relative_links_in_both_sections(tmp_path):
    progress = _progress(gates="").replace(
        "- [x] Checks run.\n", "- [x] Checks run, per [the roadmap](roadmap.md).\n")
    road = ROADMAP.replace(
        "## Stage 2 — Checks\n", "## Stage 2 — Checks ([spec](items/003-x.md))\n"
    ).replace("- Lint and fuzz.", "- Lint and fuzz, see [vision](vision.md).")
    p_updated, p_archived = aide.archive_stage_text(progress, "2")
    assert "per [the roadmap](../roadmap.md)." in p_archived
    assert p_archived.splitlines()[0] == aide._archive_header(2)
    assert aide.unarchive_stage_text(p_updated, p_archived, 2) == progress
    r_updated, r_archived = aide.archive_roadmap_text(road, 2)
    assert "see [vision](../vision.md)." in r_archived
    assert "## Stage 2 — Checks ([spec](../items/003-x.md))" in r_archived
    assert "## Stage 2 — Checks ([spec](items/003-x.md))\n" in r_updated
    assert r_archived.splitlines()[0] == aide._roadmap_archive_header(2)
    assert aide.unarchive_roadmap_text(r_updated, r_archived, 2) == road
    # Through the verb: the stub's heading still matches its file's, as
    # unarchive would put it back, and the archived items still read.
    repo = _road_repo(tmp_path, roadmap=road, progress=progress)
    assert _archive(repo, "--stage", "2") == 0
    assert _check(repo)[0] == []
    lines = aide.read_progress_lines(_ddir(repo) / "progress.md")
    assert aide._parse_item_status(lines)[2][3] == "complete"
