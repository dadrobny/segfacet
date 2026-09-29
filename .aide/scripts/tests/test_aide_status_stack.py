"""Tests for `aide status`'s stack report and its two facts (issue #303) —
see aide.py `queue_stack_facts`, `_branch_pr_facts` and `_gh`.

Throwaway repositories under ``tmp_path``, stacks built with `aide queue
start` so every base and start record is one a real run leaves. The forge is
never reached: `_gh` is the engine's one call into `gh`, and each test puts a
stand-in in its place — which is also what keeps these tests offline and the
same on every platform. `_gh` itself is exercised apart, with nothing on PATH
and with a program that exits non-zero.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_status_stack", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

Q1, Q2, Q3 = "aide/queue-001", "aide/queue-002", "aide/queue-003"

AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"

[git]
mode = "{mode}"
main_branch = "main"
branch_prefix = "aide/"

[loop]
max_open_queues = {cap}
"""

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | One | G1 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 📋 |

## Stage 1 — One — 📋

**Deliverables.**
- {icon} Alpha. *(Item 001)*
"""

QUEUE = "# Demo — Work Queue 001\n\n### Item 001: Alpha\nWork.\n"


def _git(args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _init(tmp_path: Path, mode: str = "pr", cap: int = 3,
          icon: str = "📋") -> Path:
    """A repo with one queue file whose one item is *icon*; off `local` mode,
    a bare origin with main pushed."""
    repo = tmp_path / "r"
    repo.mkdir()
    _git(["init", "-b", "main"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "Tester"], repo)
    (repo / "aide.toml").write_text(AIDE_TOML.format(mode=mode, cap=cap),
                                    encoding="utf-8")
    ddir = repo / "docs" / "aide"
    (ddir / "queue").mkdir(parents=True)
    (ddir / "progress.md").write_text(PROGRESS.format(icon=icon), encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    (ddir / "queue" / "queue-001.md").write_text(QUEUE, encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "init"], repo)
    if mode != "local":
        origin = tmp_path / "origin.git"
        _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
        _git(["remote", "add", "origin", str(origin)], repo)
        _git(["push", "-u", "origin", "main"], repo)
    return repo


def _start(repo: Path, number: int, *extra: str) -> int:
    return aide.main(["--repo", str(repo), "queue", "start", str(number), *extra])


def _work(repo: Path, name: str) -> None:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", f"work {name}"], repo)


def _stack(repo: Path, depth: int = 2) -> None:
    """main <- queue-001 <- queue-002 [<- queue-003], each with a commit."""
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    for n in range(2, depth + 1):
        assert _start(repo, n, "--base", f"aide/queue-{n - 1:03d}") == 0
        _work(repo, f"q{n}.txt")


def _forge(monkeypatch, prs: Optional[Dict[str, List[dict]]] = None,
           why: Optional[str] = None) -> List[List[str]]:
    """Stand in for `gh`: *prs* maps a head branch to its PRs, *why* makes
    every call fail with that reason. Returns the calls made."""
    calls: List[List[str]] = []

    def fake(repo_root, args):
        calls.append(list(args))
        if why is not None:
            return None, why
        if "--head" in args:
            head = args[args.index("--head") + 1]
            return json.dumps((prs or {}).get(head, [])), None
        return "", None

    monkeypatch.setattr(aide, "_gh", fake)
    return calls


def _status(repo: Path, capsys) -> dict:
    """Run status and read the stack lines and the two facts by their grammar."""
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    facts: dict = {"stack": [], "out": out}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("stack ") and ":" in line:
            _, _, rest = line.partition(": ")
            name, *fields = rest.split()
            facts["stack"].append({"name": name, **dict(
                f.split("=", 1) for f in fields)})
        elif line.startswith("stack: "):
            facts["size"] = line.split()[1]
        elif line.startswith("runnable: "):
            facts["runnable"] = line.split()[1]
        elif line.startswith("awaiting review: "):
            facts["awaiting"] = line.split()[2]
        elif line.startswith("open PRs:"):
            facts["open_prs"] = line
    return facts


# --------------------------------------------------------------------------- #
# the stack, bottom first
# --------------------------------------------------------------------------- #
def test_a_one_queue_stack_reports_its_base_and_pr(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo, depth=1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN"}]})
    f = _status(repo, capsys)
    assert f["size"] == "1/3"
    assert f["stack"] == [{"name": Q1, "base": "main", "pr": "#7/open",
                           "checks": "none", "lower": "-", "orphaned": "no"}]
    assert f["awaiting"] == "yes"


def test_a_two_queue_stack_is_printed_bottom_first(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo, depth=3)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN"}],
                         Q2: [{"number": 8, "state": "OPEN"}]})
    f = _status(repo, capsys)
    assert [s["name"] for s in f["stack"]] == [Q1, Q2, Q3]
    assert [s["base"] for s in f["stack"]] == ["main", Q1, Q2]
    assert [s["pr"] for s in f["stack"]] == ["#7/open", "#8/open", "none"]
    assert [s["lower"] for s in f["stack"]] == ["-", "current", "current"]
    assert all(s["orphaned"] == "no" for s in f["stack"])


def test_a_lower_with_commits_the_upper_lacks_reads_moved_until_restacked(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path, mode="local")
    _stack(repo)
    _git(["switch", Q1], repo)
    _work(repo, "review.txt")
    _forge(monkeypatch)
    assert _status(repo, capsys)["stack"][1]["lower"] == "moved"
    assert aide.main(["--repo", str(repo), "queue", "restack"]) == 0
    assert _status(repo, capsys)["stack"][1]["lower"] == "current"


def test_a_lower_moved_on_origin_reads_moved(tmp_path: Path, monkeypatch, capsys):
    """A reviewer's edit pushed to the lower's PR is seen once fetched,
    before any restack brings the local branch level."""
    repo = _init(tmp_path)
    _stack(repo)
    _git(["push", "origin", Q1, Q2], repo)
    human = tmp_path / "human"
    _git(["clone", "--branch", Q1, str(tmp_path / "origin.git"), str(human)], tmp_path)
    _git(["config", "user.email", "h@example.com"], human)
    _git(["config", "user.name", "Human"], human)
    _work(human, "review.txt")
    _git(["push", "origin", Q1], human)
    _git(["fetch", "origin"], repo)
    _forge(monkeypatch)
    assert _status(repo, capsys)["stack"][1]["lower"] == "moved"


def test_a_landed_lower_reads_landed_and_never_orphans(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    _git(["switch", "main"], repo)
    _git(["merge", "--squash", Q1], repo)
    _git(["commit", "-m", "squash q1"], repo)
    # Even a PR the forge reports closed: git says its work is in main.
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "CLOSED"}]})
    f = _status(repo, capsys)
    assert [s["name"] for s in f["stack"]] == [Q2]
    assert f["stack"][0]["lower"] == "landed"
    assert f["stack"][0]["orphaned"] == "no"


def test_a_branch_with_no_recorded_base_reads_unknown(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    _git(["config", "--unset", f"branch.{Q2}.aide-base"], repo)
    _forge(monkeypatch)
    q2 = next(s for s in _status(repo, capsys)["stack"] if s["name"] == Q2)
    assert (q2["base"], q2["lower"], q2["orphaned"]) == ("?", "unknown", "unknown")


# --------------------------------------------------------------------------- #
# orphaned — a PR below closed without merging
# --------------------------------------------------------------------------- #
def test_a_closed_lower_orphans_every_branch_above_and_stops_the_loop(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo, depth=3)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "CLOSED"}],
                         Q2: [{"number": 8, "state": "OPEN"}]})
    f = _status(repo, capsys)
    assert [s["orphaned"] for s in f["stack"]] == ["no", "yes", "yes"]
    assert f["stack"][0]["pr"] == "#7/closed"
    assert f["runnable"] == "no"
    assert f["awaiting"] == "yes"


def test_a_closed_and_deleted_lower_still_orphans_the_branch_above(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    _git(["branch", "-D", Q1], repo)
    _git(["push", "origin", "--delete", Q1], repo)
    _git(["fetch", "--prune", "origin"], repo)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "CLOSED"}]})
    f = _status(repo, capsys)
    assert f["stack"] == [{"name": Q2, "base": Q1, "pr": "none",
                           "checks": "-", "lower": "gone", "orphaned": "yes"}]
    assert any(Q1 in c for c in calls)
    assert f["runnable"] == "no"


def test_a_reopened_pr_is_answered_by_its_open_one(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "CLOSED"},
                              {"number": 9, "state": "OPEN"},
                              {"number": 5, "state": "MERGED"}]})
    f = _status(repo, capsys)
    assert f["stack"][0]["pr"] == "#9/open"
    assert f["stack"][1]["orphaned"] == "no"


def test_a_merged_pr_alone_reads_merged_and_orphans_nothing(
        tmp_path: Path, monkeypatch, capsys):
    """Merged on the forge, not yet pulled: git still counts the branch."""
    repo = _init(tmp_path)
    _stack(repo)
    _forge(monkeypatch, {Q1: [{"number": 5, "state": "MERGED"}]})
    f = _status(repo, capsys)
    assert f["stack"][0]["pr"] == "#5/merged"
    assert f["stack"][1]["orphaned"] == "no"
    assert f["awaiting"] == "no"


def test_a_draft_reads_draft_and_awaits_no_review_until_marked_ready(
        tmp_path: Path, monkeypatch, capsys):
    """GitHub reports a draft as OPEN; the loop keeps its queue PR in draft
    while it builds, so only a ready one is a batch awaiting review."""
    repo = _init(tmp_path, cap=2)
    _stack(repo)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": True}],
                         Q2: [{"number": 8, "state": "OPEN", "isDraft": True}]})
    f = _status(repo, capsys)
    assert [s["pr"] for s in f["stack"]] == ["#7/draft", "#8/draft"]
    assert (f["runnable"], f["awaiting"]) == ("yes", "no")
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": False}],
                         Q2: [{"number": 8, "state": "OPEN", "isDraft": True}]})
    f = _status(repo, capsys)
    assert [s["pr"] for s in f["stack"]] == ["#7/open", "#8/draft"]
    assert f["awaiting"] == "yes"


def test_a_draft_is_preferred_over_a_closed_pr_and_orphans_nothing(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "CLOSED"},
                              {"number": 6, "state": "OPEN", "isDraft": True}]})
    f = _status(repo, capsys)
    assert f["stack"][0]["pr"] == "#6/draft"
    assert f["stack"][1]["orphaned"] == "no"


def test_a_ready_pr_outranks_a_newer_draft_on_the_same_branch(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo, depth=1)
    _forge(monkeypatch, {Q1: [{"number": 3, "state": "OPEN", "isDraft": False},
                              {"number": 6, "state": "OPEN", "isDraft": True}]})
    f = _status(repo, capsys)
    assert f["stack"][0]["pr"] == "#3/open"
    assert f["awaiting"] == "yes"


def test_the_forge_is_asked_whether_a_pr_is_a_draft(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo, depth=1)
    calls = _forge(monkeypatch, {})
    _status(repo, capsys)
    asked = next(c for c in calls if "--head" in c)
    assert "isDraft" in asked[asked.index("--json") + 1].split(",")


# --------------------------------------------------------------------------- #
# runnable and awaiting review — two facts, and a repo can be both
# --------------------------------------------------------------------------- #
def test_live_work_is_runnable_while_prs_await_review(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path, cap=2)
    _stack(repo)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN"}]})
    f = _status(repo, capsys)
    assert (f["runnable"], f["awaiting"]) == ("yes", "yes")


@pytest.mark.parametrize("cap,runnable", [(2, "no"), (3, "yes")])
def test_with_no_live_work_runnable_is_room_below_the_cap(
        tmp_path: Path, monkeypatch, capsys, cap: int, runnable: str):
    repo = _init(tmp_path, cap=cap, icon="✅")
    _stack(repo)
    _forge(monkeypatch)
    f = _status(repo, capsys)
    assert f["runnable"] == runnable
    assert f["awaiting"] == "no"


def test_an_item_awaiting_review_is_not_live_work(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path, cap=1, icon="🔍")
    _stack(repo, depth=1)
    _forge(monkeypatch)
    assert _status(repo, capsys)["runnable"] == "no"


def test_could_not_look_is_unknown_and_never_none(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _stack(repo)
    calls = _forge(monkeypatch, why="gh is not on PATH")
    f = _status(repo, capsys)
    assert [s["pr"] for s in f["stack"]] == ["unknown", "unknown"]
    assert f["stack"][1]["orphaned"] == "unknown"
    assert f["awaiting"] == "unknown"
    assert "could not look" in f["open_prs"] and "gh is not on PATH" in f["open_prs"]
    # One failure is the answer for the rest: it is not asked again.
    assert len(calls) == 1


def test_an_empty_stack_awaits_no_review_without_asking(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    calls = _forge(monkeypatch, why="offline")
    f = _status(repo, capsys)
    assert f["size"] == "0/3" and f["stack"] == []
    assert f["awaiting"] == "no"
    assert all("--head" not in c for c in calls)


def test_local_mode_asks_no_forge_about_the_stack(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path, mode="local")
    _stack(repo)
    calls = _forge(monkeypatch, why="must not be asked")
    f = _status(repo, capsys)
    assert [(s["pr"], s["orphaned"]) for s in f["stack"]] == [("-", "-")] * 2
    assert f["awaiting"] == "no"
    assert all("--head" not in c for c in calls)


# --------------------------------------------------------------------------- #
# the forge call itself
# --------------------------------------------------------------------------- #
def test_gh_missing_from_path_is_a_reason(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(aide.shutil, "which", lambda name: None)
    out, why = aide._gh(tmp_path, ["pr", "list"])
    assert out is None and "not on PATH" in why


def test_gh_exiting_non_zero_is_a_reason_naming_the_exit(tmp_path: Path, monkeypatch):
    """A real process that fails the way an unauthenticated `gh` does."""
    monkeypatch.setattr(aide.shutil, "which", lambda name: sys.executable)
    out, why = aide._gh(tmp_path, ["-c", "import sys; sys.stderr.write('auth "
                                   "required\\n'); sys.exit(4)"])
    assert out is None
    assert "exited 4" in why and "auth required" in why


def test_a_forge_answer_status_cannot_read_is_could_not_look(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(aide, "_gh", lambda repo_root, args: ("not json", None))
    got, why = aide._branch_pr_facts(tmp_path, Q1)
    assert got is None and why
