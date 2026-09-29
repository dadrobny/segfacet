"""Tests for `aide queue restack` (issue #301) — see aide.py `_queue_restack`.

Throwaway repositories under ``tmp_path``; a bare repository stands in for
``origin`` where the remote half is under test. Each test builds the stack the
way the loop does — `aide queue start M --base <prefix>queue-N` — so the base
records are the ones a real run leaves, never hand-written config.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_restack", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"

[git]
mode = "{mode}"
main_branch = "main"
branch_prefix = "aide/"

# A stack of three is what these tests build; the default cap of one would
# refuse the second `queue start` (issue #302).
[loop]
max_open_queues = 3
"""

#: Five lines a queue ticks one at a time — the shape `progress.md` has, and
#: the one where a squash merge meets the commits it squashed.
LEDGER = "".join(f"line {n}\n" for n in range(1, 6))

Q1, Q2, Q3 = "aide/queue-001", "aide/queue-002", "aide/queue-003"


def _git(args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _sha(repo: Path, ref: str) -> str:
    return _git(["rev-parse", ref], repo).stdout.strip()


def _head(repo: Path) -> str:
    return _git(["rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()


def _contains(repo: Path, ancestor: str, ref: str) -> bool:
    return _git(["merge-base", "--is-ancestor", ancestor, ref], repo,
                check=False).returncode == 0


def _base(repo: Path, branch: str) -> str:
    return _git(["config", "--get", f"branch.{branch}.aide-base"], repo,
                check=False).stdout.strip()


def _clean(repo: Path) -> bool:
    return _git(["status", "--porcelain"], repo).stdout.strip() == ""


def _init(path: Path, mode: str = "local") -> Path:
    path.mkdir(parents=True)
    _git(["init", "-b", "main"], path)
    _git(["config", "user.email", "t@example.com"], path)
    _git(["config", "user.name", "Tester"], path)
    (path / "aide.toml").write_text(AIDE_TOML.format(mode=mode), encoding="utf-8")
    ddir = path / "docs" / "aide"
    ddir.mkdir(parents=True)
    # An inbox already present, so `queue start` commits nothing of its own
    # and a branch's commits are exactly the ones a test makes.
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    (path / "ledger.txt").write_text(LEDGER, encoding="utf-8")
    _git(["add", "-A"], path)
    _git(["commit", "-m", "init"], path)
    return path


def _commit_file(repo: Path, name: str, text: str, message: str) -> None:
    (repo / name).write_text(text, encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", message], repo)


def _tick(repo: Path, n: int, mark: str = "done") -> None:
    """Edit line *n* of the shared file, as a queue ticks its own row."""
    text = (repo / "ledger.txt").read_text(encoding="utf-8")
    text = text.replace(f"line {n}\n", f"line {n} {mark}\n")
    _commit_file(repo, "ledger.txt", text, f"tick {n} {mark}")


def _restack(repo: Path, *extra: str) -> int:
    return aide.main(["--repo", str(repo), "queue", "restack", *extra])


def _start(repo: Path, number: int, base: str = "") -> None:
    extra = ["--base", base] if base else []
    assert aide.main(["--repo", str(repo), "queue", "start", str(number),
                      *extra]) == 0


def _stack(repo: Path) -> None:
    """main <- queue-001 (ticks line 2) <- queue-002 (ticks line 3)."""
    _start(repo, 1)
    _tick(repo, 2)
    _commit_file(repo, "q1.txt", "one\n", "q1 work")
    _start(repo, 2, Q1)
    _tick(repo, 3)


def _squash(repo: Path, branch: str) -> None:
    """Land *branch* as GitHub's "Squash and merge" does."""
    _git(["switch", "main"], repo)
    _git(["merge", "--squash", branch], repo)
    _git(["commit", "-m", f"squash {branch}"], repo)


# --------------------------------------------------------------------------- #
# a lower branch moved
# --------------------------------------------------------------------------- #
def test_a_moved_lower_branch_is_merged_forward_and_never_rebased(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    upper_before = _sha(repo, Q2)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2)
    assert _contains(repo, upper_before, Q2)  # merged onto, never rewritten
    assert _head(repo) == Q1 and _clean(repo)


def test_a_merge_propagates_up_a_stack_of_three(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _start(repo, 3, Q2)
    _commit_file(repo, "q3.txt", "three\n", "q3 work")
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2) and _contains(repo, Q2, Q3)
    assert _contains(repo, Q1, Q3)


def test_a_lone_queue_branch_on_main_is_left_alone(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _start(repo, 1)
    _tick(repo, 2)
    _git(["switch", "main"], repo)
    _commit_file(repo, "other.txt", "x\n", "unrelated work on main")
    before = _sha(repo, Q1)

    assert _restack(repo) == 0
    assert _sha(repo, Q1) == before
    assert "nothing to do" in capsys.readouterr().out


def test_a_second_run_with_nothing_moved_merges_nothing(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")
    assert _restack(repo) == 0
    tips = (_sha(repo, Q1), _sha(repo, Q2))
    capsys.readouterr()

    assert _restack(repo) == 0
    assert (_sha(repo, Q1), _sha(repo, Q2)) == tips
    assert "nothing to merge" in capsys.readouterr().out


def test_dry_run_prints_the_merges_and_changes_nothing(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")
    tips = (_sha(repo, Q1), _sha(repo, Q2))

    assert _restack(repo, "--dry-run") == 0
    out = capsys.readouterr().out
    assert f"would merge {Q1} into {Q2}" in out
    assert (_sha(repo, Q1), _sha(repo, Q2)) == tips
    assert _head(repo) == Q1


# --------------------------------------------------------------------------- #
# the bottom landed in main
# --------------------------------------------------------------------------- #
def test_a_squash_merged_bottom_hands_its_upper_to_main(tmp_path: Path):
    """Line 2 (the bottom's tick) and line 3 (the upper's) are adjacent, so
    git's own merge base makes this a conflict; the landed tip as the base
    does not. Both halves are asserted — the first is the finding."""
    repo = _init(tmp_path / "r")
    _stack(repo)
    bottom = _sha(repo, Q1)
    _squash(repo, Q1)
    plain = _git(["merge-tree", "--write-tree", Q2, "main"], repo, check=False)
    assert plain.returncode == 1, "the plain forward merge was expected to conflict"
    _git(["switch", Q2], repo)

    assert _restack(repo) == 0
    assert _contains(repo, "main", Q2)
    assert _base(repo, Q2) == "main"
    assert _sha(repo, Q1) == bottom  # the landed branch is left alone
    text = _git(["show", f"{Q2}:ledger.txt"], repo).stdout
    assert "line 2 done" in text and "line 3 done" in text
    assert _head(repo) == Q2 and _clean(repo)


def test_a_merge_commit_landed_bottom_hands_its_upper_to_main(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", "main"], repo)
    _commit_file(repo, "other.txt", "x\n", "unrelated work on main")
    _git(["merge", "--no-ff", "--no-edit", Q1], repo)

    assert _restack(repo) == 0
    assert _contains(repo, "main", Q2)
    assert _base(repo, Q2) == "main"
    assert _head(repo) == "main"


def test_a_lower_with_no_commits_of_its_own_is_not_read_as_landed(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _start(repo, 1)             # no commits: its tip is on main's history
    _start(repo, 2, Q1)
    _tick(repo, 3)
    _git(["switch", "main"], repo)
    _commit_file(repo, "other.txt", "x\n", "unrelated work on main")
    before = _sha(repo, Q2)

    assert _restack(repo) == 0
    assert _base(repo, Q2) == Q1
    assert _sha(repo, Q2) == before


def test_on_old_git_a_squash_merged_bottom_reads_as_still_open(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _squash(repo, Q1)
    monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 30))
    before = _sha(repo, Q2)

    assert _restack(repo) == 0
    assert _base(repo, Q2) == Q1
    assert _sha(repo, Q2) == before


def test_on_old_git_the_merge_runs_in_the_tree_and_head_comes_back(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")
    _git(["switch", "main"], repo)
    monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 30))

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2)
    assert _head(repo) == "main" and _clean(repo)


# --------------------------------------------------------------------------- #
# stops
# --------------------------------------------------------------------------- #
def _conflicting_stack(repo: Path) -> None:
    """queue-002 rewrites the line queue-001 then rewrites again."""
    _start(repo, 1)
    _tick(repo, 2)
    _start(repo, 2, Q1)
    text = (repo / "ledger.txt").read_text(encoding="utf-8")
    _commit_file(repo, "ledger.txt", text.replace("line 2 done", "line 2 upper"),
                 "upper rewrites line 2")
    _git(["switch", Q1], repo)
    text = (repo / "ledger.txt").read_text(encoding="utf-8")
    _commit_file(repo, "ledger.txt", text.replace("line 2 done", "line 2 lower"),
                 "lower rewrites line 2")


@pytest.mark.parametrize("old_git", [False, True], ids=["merge-tree", "in-tree"])
def test_a_conflict_stops_with_the_tree_clean_and_head_restored(
        tmp_path: Path, monkeypatch, capsys, old_git):
    repo = _init(tmp_path / "r")
    _conflicting_stack(repo)
    if old_git:
        monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 30))
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before
    assert _head(repo) == Q1 and _clean(repo)
    assert not (repo / ".git" / "MERGE_HEAD").exists()
    err = capsys.readouterr().err
    assert Q1 in err and Q2 in err


def test_an_unclean_tree_is_refused(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    (repo / "ledger.txt").write_text("dirty\n", encoding="utf-8")
    assert _restack(repo) == 1


def test_an_unrecorded_queue_branch_is_listed_and_never_chained(
        tmp_path: Path, capsys):
    """Legacy and other-machine branches carry no record; chaining them by
    number would merge unrelated queues."""
    repo = _init(tmp_path / "r")
    _git(["switch", "-c", Q1], repo)
    _tick(repo, 2)
    _git(["switch", "-c", Q2], repo)
    _tick(repo, 3)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "moved\n", "q1 moves")
    before = _sha(repo, Q2)

    assert _restack(repo) == 0
    assert _sha(repo, Q2) == before
    err = capsys.readouterr().err
    assert Q1 in err and Q2 in err and "--base" in err


def test_base_records_a_branch_s_base_and_restacks_it(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _git(["switch", "-c", Q1], repo)
    _tick(repo, 2)
    _git(["switch", "-c", Q2], repo)
    _tick(repo, 3)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "moved\n", "q1 moves")

    # Bottom up: the upper's base must itself be read before it is used.
    assert _restack(repo, "2", "--base", Q1) == 1
    assert _base(repo, Q2) == ""          # refused before anything is written
    assert _restack(repo, "1", "--base", "main") == 0
    assert _base(repo, Q1) == "main"
    assert _restack(repo, "2", "--base", Q1) == 0
    assert _base(repo, Q2) == Q1
    assert _contains(repo, Q1, Q2)


def test_a_recorded_base_this_checkout_lacks_refuses(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", "main"], repo)
    _git(["branch", "-D", Q1], repo)
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before
    assert Q1 in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["2"], ["--base", "main"]],
                         ids=["number-alone", "base-alone"])
def test_number_and_base_go_together(tmp_path: Path, argv):
    repo = _init(tmp_path / "r")
    assert _restack(repo, *argv) == 2


def test_start_and_tidy_still_need_a_number(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert aide.main(["--repo", str(repo), "queue", "start"]) == 2
    assert aide.main(["--repo", str(repo), "queue", "tidy"]) == 2


# --------------------------------------------------------------------------- #
# origin
# --------------------------------------------------------------------------- #
def _with_origin(tmp_path: Path) -> tuple:
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    repo = _init(tmp_path / "r", mode="pr")
    _git(["remote", "add", "origin", str(origin)], repo)
    _git(["push", "-u", "origin", "main"], repo)
    _stack(repo)                 # `queue start` pushes both branches
    _git(["push", "origin", Q1, Q2], repo)
    other = tmp_path / "other"
    _git(["clone", str(origin), str(other)], tmp_path)
    _git(["config", "user.email", "h@example.com"], other)
    _git(["config", "user.name", "Human"], other)
    return origin, repo, other


def test_review_edits_on_origin_are_fetched_merged_forward_and_pushed(
        tmp_path: Path):
    origin, repo, other = _with_origin(tmp_path)
    _git(["switch", Q1], other)
    _commit_file(other, "q1.txt", "one, reviewed\n", "review edit on the PR")
    _git(["push", "origin", Q1], other)
    edit = _sha(other, Q1)

    assert _restack(repo) == 0
    assert _sha(repo, Q1) == edit                 # fast-forwarded from origin
    assert _contains(repo, edit, Q2)
    assert _sha(origin, Q2) == _sha(repo, Q2)     # pushed, no force needed


def test_a_branch_diverged_from_origin_is_refused(tmp_path: Path):
    origin, repo, other = _with_origin(tmp_path)
    _git(["switch", Q1], other)
    _commit_file(other, "q1.txt", "theirs\n", "on origin")
    _git(["push", "origin", Q1], other)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "ours\n", "only here")
    tips = (_sha(repo, Q1), _sha(repo, Q2))

    assert _restack(repo) == 1
    assert (_sha(repo, Q1), _sha(repo, Q2)) == tips


def test_a_conflict_pushes_nothing(tmp_path: Path):
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    repo = _init(tmp_path / "r", mode="pr")
    _git(["remote", "add", "origin", str(origin)], repo)
    _git(["push", "-u", "origin", "main"], repo)
    _conflicting_stack(repo)
    on_origin = _sha(origin, Q2)

    assert _restack(repo) == 1
    assert _sha(origin, Q2) == on_origin


def test_a_stack_branch_ahead_of_origin_is_pushed_by_a_re_run(tmp_path: Path):
    """What a stopped run leaves behind: a merge made locally, not pushed."""
    origin, repo, _other = _with_origin(tmp_path)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")
    _git(["push", "origin", Q1], repo)
    _git(["switch", Q2], repo)
    _git(["merge", "--no-edit", Q1], repo)        # merged here, never pushed
    _git(["switch", Q1], repo)

    assert _restack(repo) == 0
    assert _sha(origin, Q2) == _sha(repo, Q2)


def test_local_mode_never_fetches_or_pushes(tmp_path: Path):
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    repo = _init(tmp_path / "r", mode="local")
    _git(["remote", "add", "origin", str(origin)], repo)
    _stack(repo)
    _git(["push", "origin", "main", Q1, Q2], repo)
    on_origin = _sha(origin, Q2)
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2)
    assert _sha(origin, Q2) == on_origin


def test_base_creates_a_branch_only_origin_has(tmp_path: Path):
    """The second machine: it fetched the stack and started none of it."""
    origin, _repo, other = _with_origin(tmp_path)
    assert Q1 not in _git(["branch"], other).stdout

    assert _restack(other, "1", "--base", "main") == 0
    assert _base(other, Q1) == "main"
    assert _restack(other, "2", "--base", Q1) == 0
    assert _base(other, Q2) == Q1
    assert _sha(other, Q2) == _sha(origin, Q2)


def test_a_cycle_of_recorded_bases_refuses(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["config", f"branch.{Q1}.aide-base", Q2], repo)
    tips = (_sha(repo, Q1), _sha(repo, Q2))

    assert _restack(repo) == 1
    assert (_sha(repo, Q1), _sha(repo, Q2)) == tips


def test_a_specs_queue_branch_is_never_part_of_a_stack(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert aide.main(["--repo", str(repo), "queue", "start", "1", "--specs"]) == 0
    _tick(repo, 2)
    _start(repo, 2, "aide/specs-queue-001")
    _tick(repo, 3)
    _git(["switch", "aide/specs-queue-001"], repo)
    _commit_file(repo, "specs.txt", "moved\n", "specs move")
    before = _sha(repo, Q2)

    assert _restack(repo) == 0
    assert _sha(repo, Q2) == before


def test_between_git_2_38_and_2_40_main_is_merged_over_git_s_own_base(
        tmp_path: Path, monkeypatch):
    """No `--merge-base`: the squashed bottom's adjacent tick meets itself."""
    repo = _init(tmp_path / "r")
    _stack(repo)
    _squash(repo, Q1)
    monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 39))
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before and _base(repo, Q2) == Q1


# --------------------------------------------------------------------------- #
# review round 1 (PR #306)
# --------------------------------------------------------------------------- #
def _old_git(monkeypatch, old: bool) -> None:
    if old:
        monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 30))


def _move_lower(repo: Path) -> None:
    _git(["switch", Q1], repo)
    _commit_file(repo, "q1.txt", "one, reviewed\n", "review edit")


def test_a_forced_base_whose_merge_conflicts_keeps_the_old_record(tmp_path: Path):
    """The record is a step after its merge, so a stop leaves the one found."""
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["switch", "main"], repo)
    _tick(repo, 3, "clashes")          # queue-002 ticked line 3 differently
    before = _sha(repo, Q2)

    assert _restack(repo, "2", "--base", "main") == 1
    assert _base(repo, Q2) == Q1
    assert _sha(repo, Q2) == before


def test_queue_start_records_the_commit_it_started_from(tmp_path: Path):
    repo = _init(tmp_path / "r")
    main = _sha(repo, "main")
    _start(repo, 1)
    assert _git(["config", "--get", f"branch.{Q1}.aide-start"],
                repo).stdout.strip() == main


def _land_by_fast_forward(repo: Path) -> None:
    """`local` mode's own landing: main fast-forwarded to the bottom."""
    _git(["switch", "main"], repo)
    _git(["merge", "--ff-only", Q1], repo)
    _commit_file(repo, "other.txt", "x\n", "main moves on")


def test_a_bottom_landed_by_fast_forward_past_its_start_hands_on_its_upper(
        tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _land_by_fast_forward(repo)

    assert _restack(repo) == 0
    assert _contains(repo, "main", Q2)
    assert _base(repo, Q2) == "main"


def test_a_fast_forwarded_bottom_with_no_start_record_is_a_stop_not_consistent(
        tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _git(["config", "--unset", f"branch.{Q1}.aide-start"], repo)
    _land_by_fast_forward(repo)
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before and _base(repo, Q2) == Q1
    out = capsys.readouterr()
    assert "consistent" not in out.out and "--base main" in out.err
    # The remedy it names for a landed lower:
    assert _restack(repo, "2", "--base", "main") == 0
    assert _contains(repo, "main", Q2) and _base(repo, Q2) == "main"


def test_an_empty_bottom_with_no_start_record_is_resolved_by_recording_it(
        tmp_path: Path):
    repo = _init(tmp_path / "r")
    _start(repo, 1)
    _start(repo, 2, Q1)
    _tick(repo, 3)
    _git(["config", "--unset", f"branch.{Q1}.aide-start"], repo)
    _git(["switch", "main"], repo)
    _commit_file(repo, "other.txt", "x\n", "main moves on")
    tips = (_sha(repo, Q1), _sha(repo, Q2))

    assert _restack(repo) == 1
    # The remedy it names for an open lower records the start, moves nothing.
    assert _restack(repo, "1", "--base", "main") == 0
    assert (_sha(repo, Q1), _sha(repo, Q2)) == tips
    assert _restack(repo) == 0
    assert _base(repo, Q2) == Q1


@pytest.mark.parametrize("old_git", [False, True], ids=["merge-tree", "in-tree"])
def test_a_signing_failure_stops_the_run_with_nothing_moved(
        tmp_path: Path, monkeypatch, old_git):
    """`commit.gpgSign` is honoured on both paths; a signer that cannot run
    must stop the merge, never let it through unsigned."""
    repo = _init(tmp_path / "r")
    _stack(repo)
    _move_lower(repo)
    _git(["config", "commit.gpgSign", "true"], repo)
    _git(["config", "gpg.program", str(tmp_path / "no-such-signer")], repo)
    _old_git(monkeypatch, old_git)
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before
    assert _head(repo) == Q1 and _clean(repo)


@pytest.mark.parametrize("old_git", [False, True], ids=["merge-tree", "in-tree"])
def test_no_commit_hook_runs_on_either_path(tmp_path: Path, monkeypatch, old_git):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _move_lower(repo)
    hooks = repo / ".git" / "hooks"
    for name in ("pre-merge-commit", "commit-msg"):
        (hooks / name).write_bytes(b"#!/bin/sh\nexit 1\n")
        (hooks / name).chmod(0o755)
    _old_git(monkeypatch, old_git)

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2)


def test_an_unrecorded_base_below_is_not_called_a_cycle(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _start(repo, 3, Q2)
    _git(["config", "--unset", f"branch.{Q1}.aide-base"], repo)

    assert _restack(repo) == 1
    err = capsys.readouterr().err
    assert "cycle" not in err and Q1 in err


def test_a_stack_branch_checked_out_in_another_worktree_refuses(tmp_path: Path):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _move_lower(repo)
    _git(["worktree", "add", str(tmp_path / "wt"), Q2], repo)
    before = _sha(repo, Q2)

    assert _restack(repo) == 1
    assert _sha(repo, Q2) == before


def test_a_failed_push_exits_one_with_the_merge_kept_local(tmp_path: Path):
    origin, repo, _other = _with_origin(tmp_path)
    on_origin = _sha(origin, Q2)
    _git(["config", "remote.origin.pushurl", str(tmp_path / "nowhere.git")], repo)
    _move_lower(repo)

    assert _restack(repo) == 1
    assert _contains(repo, Q1, Q2)
    assert _sha(origin, Q2) == on_origin


@pytest.mark.parametrize("old_git", [False, True], ids=["merge-tree", "in-tree"])
def test_a_detached_head_start_is_restored(tmp_path: Path, monkeypatch, old_git):
    repo = _init(tmp_path / "r")
    _stack(repo)
    _move_lower(repo)
    _git(["switch", "--detach", "main"], repo)
    at = _sha(repo, "HEAD")
    _old_git(monkeypatch, old_git)

    assert _restack(repo) == 0
    assert _contains(repo, Q1, Q2)
    assert _head(repo) == "HEAD" and _sha(repo, "HEAD") == at


# --------------------------------------------------------------------------- #
# review round 2 (PR #306) — a branch's own landing, whatever lies below it
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("starts", [True, False], ids=["starts", "no-starts"])
def test_a_middle_branch_landed_over_an_open_empty_bottom_hands_on_its_upper(
        tmp_path: Path, capsys, starts: bool):
    """main <- queue-001 (no commits) <- queue-002 <- queue-003; main is
    fast-forwarded to queue-002 and moves on. queue-002 has commits beyond
    its lower, so it landed however queue-001 is read; queue-001 is open,
    empty and wholly in main, and is left alone."""
    repo = _init(tmp_path / "r")
    _start(repo, 1)
    _start(repo, 2, Q1)
    _tick(repo, 2)
    _start(repo, 3, Q2)
    _tick(repo, 3)
    if not starts:
        for b in (Q1, Q2, Q3):
            _git(["config", "--unset", f"branch.{b}.aide-start"], repo)
    _git(["switch", "main"], repo)
    _git(["merge", "--ff-only", Q2], repo)
    _commit_file(repo, "hotfix.txt", "hotfix\n", "hotfix")
    bottom, middle = _sha(repo, Q1), _sha(repo, Q2)

    assert _restack(repo) == 0
    assert _contains(repo, "main", Q3)
    assert _base(repo, Q3) == "main" and _base(repo, Q2) == "main"
    assert (_sha(repo, Q1), _sha(repo, Q2)) == (bottom, middle)
    assert _base(repo, Q1) == "main"
    capsys.readouterr()
    assert _restack(repo) == 0
    assert "nothing" in capsys.readouterr().out


def test_two_lowers_squash_landed_before_any_restack(tmp_path: Path):
    """Lines 1 and 4 are apart, so git's own `merge --squash` of the second
    lower goes through, as a human's would; the top queue ticks line 5, next
    to line 4, which only the landed tip as merge base keeps clean."""
    repo = _init(tmp_path / "r")
    _start(repo, 1)
    _tick(repo, 1)
    _start(repo, 2, Q1)
    _tick(repo, 4)
    _start(repo, 3, Q2)
    _tick(repo, 5)
    _squash(repo, Q1)
    _squash(repo, Q2)

    assert _restack(repo) == 0
    assert _contains(repo, "main", Q3) and _base(repo, Q3) == "main"
    assert _base(repo, Q2) == "main"
    text = _git(["show", f"{Q3}:ledger.txt"], repo).stdout
    assert all(f"line {n} done" in text for n in (1, 4, 5))
