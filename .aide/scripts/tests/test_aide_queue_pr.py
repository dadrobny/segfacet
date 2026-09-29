"""Tests for the queue PR's CI state in `aide status` and for `aide queue pr`
and `aide queue ready` (issue #330) — see aide.py `checks_state`,
`_branch_pr_facts`, `_queue_branch_ci`, `_queue_pr` and `_queue_ready`.

Throwaway repositories under ``tmp_path``, each queue branch started with
`aide queue start` so its recorded base is the one a real run leaves, and a
bare origin where the mode reaches for one. The forge is never reached: `_gh`
is the engine's one call into `gh`, and each test puts a stand-in in its
place that answers `pr list` from a table and records every call — so the
tests are offline and the same on every platform, and a refusal is seen to
ask the forge to change nothing.
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
_spec = importlib.util.spec_from_file_location("aide_cli_queue_pr", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

Q1, Q2 = "aide/queue-001", "aide/queue-002"

AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"

[git]
mode = "{mode}"
main_branch = "main"
branch_prefix = "aide/"

[loop]
max_open_queues = 2
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
{trail}- 📋 Beta. *(Item 002)*
"""

REOPENED = "  - **2026-09-29** → reopened: CI failed on the queue PR\n"


def _git(args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _init(tmp_path: Path, mode: str = "pr", origin: bool = True) -> Path:
    repo = tmp_path / "r"
    repo.mkdir(parents=True)
    _git(["init", "-b", "main"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "Tester"], repo)
    (repo / "aide.toml").write_text(AIDE_TOML.format(mode=mode), encoding="utf-8")
    ddir = repo / "docs" / "aide"
    (ddir / "queue").mkdir(parents=True)
    (ddir / "progress.md").write_text(PROGRESS.format(icon="📋", trail=""),
                                      encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", "init"], repo)
    if origin:
        bare = tmp_path / "origin.git"
        _git(["init", "--bare", "-b", "main", str(bare)], tmp_path)
        _git(["remote", "add", "origin", str(bare)], repo)
        _git(["push", "-u", "origin", "main"], repo)
    return repo


def _commit(repo: Path, message: str) -> None:
    _git(["add", "-A"], repo)
    _git(["commit", "-m", message], repo)


def _plan(repo: Path, number: int, items: str = "### Item 001: Alpha\n") -> None:
    """Commit queue file *number* on the checked-out branch — the planner's work."""
    path = repo / "docs" / "aide" / "queue" / f"queue-{number:03d}.md"
    path.write_text(f"# Demo — Work Queue {number:03d}\n\n{items}",
                    encoding="utf-8")
    _commit(repo, f"docs(aide): add work queue {number:03d}")


def _progress(repo: Path, icon: str, trail: str) -> None:
    (repo / "docs" / "aide" / "progress.md").write_text(
        PROGRESS.format(icon=icon, trail=trail), encoding="utf-8")
    _commit(repo, "progress")


def _start(repo: Path, number: int, *extra: str) -> None:
    assert aide.main(["--repo", str(repo), "queue", "start", str(number),
                      *extra]) == 0


def _run(repo: Path, *argv: str) -> int:
    return aide.main(["--repo", str(repo), "queue", *argv])


def _on_origin(repo: Path, branch: str) -> Optional[str]:
    out = _git(["ls-remote", "origin", f"refs/heads/{branch}"], repo).stdout
    return out.split()[0] if out.strip() else None


def _head(repo: Path, ref: str = "HEAD") -> str:
    return _git(["rev-parse", ref], repo).stdout.strip()


def _forge(monkeypatch, prs: Optional[Dict[str, List[dict]]] = None,
           why: Optional[str] = None, fail: Optional[str] = None,
           no_checks: Optional[str] = None) -> List[List[str]]:
    """Stand in for `gh`. *prs* answers `pr list --head`; *why* fails every
    call; *fail* fails only the call whose second word it names (`create`,
    `ready`); *no_checks* fails only a list that asks for the check rollup.
    Returns every call made."""
    calls: List[List[str]] = []

    def fake(repo_root, args):
        calls.append(list(args))
        if why is not None:
            return None, why
        if (no_checks is not None and "--json" in args
                and "statusCheckRollup" in args[args.index("--json") + 1]):
            return None, no_checks
        if fail is not None and len(args) > 1 and args[1] == fail:
            return None, f"gh exited 1: {fail} refused"
        if args[:2] == ["pr", "list"] and "--head" in args:
            return json.dumps((prs or {}).get(args[args.index("--head") + 1],
                                              [])), None
        if args[:2] == ["pr", "create"]:
            return "https://example.test/pull/9\n", None
        return "", None

    monkeypatch.setattr(aide, "_gh", fake)
    return calls


def _writes(calls: List[List[str]]) -> List[List[str]]:
    """The calls that would change the forge — everything but `pr list`."""
    return [c for c in calls if c[:2] != ["pr", "list"]]


def _body(tmp_path: Path) -> str:
    path = tmp_path / "body.md"
    path.write_text("Plan for queue 001.\n", encoding="utf-8")
    return str(path)


def _status_stack(repo: Path, capsys) -> List[dict]:
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    stack: List[dict] = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("stack ") and ": " in line:
            name, *fields = line.partition(": ")[2].split()
            stack.append({"name": name, "failing": [], "why": None,
                          **dict(f.split("=", 1) for f in fields)})
        elif line.startswith("failing check: "):
            stack[-1]["failing"].append(line.partition(": ")[2])
        elif line.startswith("checks unknown: "):
            stack[-1]["why"] = line.partition(": ")[2]
        elif line.startswith("pending check: "):
            stack[-1].setdefault("running", []).append(line.partition(": ")[2])
        elif line.startswith("ci fix rounds: "):
            stack[-1]["rounds"] = int(line.partition(": ")[2])
        elif line.startswith("awaiting review: "):
            stack and stack[-1].setdefault("awaiting", line.split()[2])
    return stack


def _run_check(name: str, status: str, conclusion: str = "") -> dict:
    return {"__typename": "CheckRun", "name": name, "status": status,
            "conclusion": conclusion}


def _context(name: str, state: str) -> dict:
    return {"__typename": "StatusContext", "context": name, "state": state}


# --------------------------------------------------------------------------- #
# checks_state — the rollup, read
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("rollup,expected", [
    (None, ("none", [], None)),
    ([], ("none", [], None)),
    ([_run_check("docs", "COMPLETED", "SKIPPED"),
      _run_check("lint", "COMPLETED", "NEUTRAL")], ("none", [], None)),
    ([_run_check("build", "IN_PROGRESS")], ("pending", [], None)),
    ([_run_check("build", "QUEUED"), _run_check("lint", "COMPLETED", "SUCCESS")],
     ("pending", [], None)),
    ([_context("ci/legacy", "PENDING")], ("pending", [], None)),
    ([_run_check("build", "COMPLETED", "SUCCESS"), _context("ci/legacy", "SUCCESS"),
      _run_check("docs", "COMPLETED", "SKIPPED")], ("success", [], None)),
    ([_run_check("build", "COMPLETED", "FAILURE"), _run_check("lint", "IN_PROGRESS"),
      _context("ci/legacy", "ERROR"), _run_check("e2e", "COMPLETED", "CANCELLED"),
      _run_check("docs", "COMPLETED", "SUCCESS")],
     ("failure", ["build", "ci/legacy", "e2e"], None)),
    ([_run_check("slow", "COMPLETED", "TIMED_OUT")], ("failure", ["slow"], None)),
    ([_run_check("old", "COMPLETED", "STALE")], ("failure", ["old"], None)),
    ([_run_check("test", "COMPLETED", "FAILURE"), _run_check("lint", "COMPLETED", "FAILURE"),
      _run_check("test", "COMPLETED", "FAILURE")], ("failure", ["test", "lint"], None)),
], ids=["no-rollup", "empty", "only-skipped-and-neutral", "check-run-running",
        "one-running-one-passed", "status-context-pending", "all-passed",
        "a-failure-wins-and-names-each", "timed-out-fails", "stale-fails",
        "a-matrix-name-is-named-once"])
def test_the_rollup_reads_as_one_ci_state(rollup, expected):
    assert aide.checks_state(rollup) == expected


@pytest.mark.parametrize("rollup", [
    "not a list",
    [42],
    [_run_check("odd", "COMPLETED", "SOMETHING_NEW")],
], ids=["not-a-list", "not-an-object", "unrecognised-value"])
def test_a_rollup_status_cannot_read_is_unknown_with_a_reason(rollup):
    checks, failing, why = aide.checks_state(rollup)
    assert (checks, failing) == ("unknown", []) and why


# --------------------------------------------------------------------------- #
# status — checks= on the stack line, and a draft being fixed
# --------------------------------------------------------------------------- #
def test_status_reports_each_prs_checks_and_names_the_failing_ones(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _start(repo, 2, "--base", Q1)
    _plan(repo, 2, "### Item 002: Beta\n")
    calls = _forge(monkeypatch, {
        Q1: [{"number": 7, "state": "OPEN", "isDraft": False,
              "statusCheckRollup": [_run_check("build", "COMPLETED", "FAILURE"),
                                    _context("ci/legacy", "ERROR"),
                                    _run_check("lint", "COMPLETED", "SUCCESS")]}],
        Q2: [{"number": 8, "state": "OPEN", "isDraft": True,
              "statusCheckRollup": []}]})
    stack = _status_stack(repo, capsys)
    assert [(s["name"], s["pr"], s["checks"]) for s in stack] == [
        (Q1, "#7/open", "failure"), (Q2, "#8/draft", "none")]
    assert stack[0]["failing"] == ["build", "ci/legacy"]
    assert stack[1]["failing"] == []
    # The rollup rides the call that finds the PR: no second spawn per branch.
    asked = [c for c in calls if "--head" in c]
    assert len(asked) == 2
    assert all("statusCheckRollup" in c[c.index("--json") + 1].split(",")
               for c in asked)


def test_status_reads_pending_and_success(tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup":
                               [_run_check("build", "IN_PROGRESS")]}]})
    assert _status_stack(repo, capsys)[0]["checks"] == "pending"
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup":
                               [_run_check("build", "COMPLETED", "SUCCESS")]}]})
    assert _status_stack(repo, capsys)[0]["checks"] == "success"


def test_checks_are_unknown_with_the_reason_where_the_forge_cannot_be_asked(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _forge(monkeypatch, why="gh is not on PATH")
    (q1,) = _status_stack(repo, capsys)
    assert (q1["pr"], q1["checks"]) == ("unknown", "unknown")
    assert "gh is not on PATH" in q1["why"]


def test_checks_are_unknown_where_the_rollup_cannot_be_read(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup":
                               [_run_check("odd", "COMPLETED", "NEW_THING")]}]})
    (q1,) = _status_stack(repo, capsys)
    assert (q1["pr"], q1["checks"]) == ("#7/open", "unknown")
    assert "NEW_THING" in q1["why"]


def test_checks_are_a_dash_with_no_pr_and_in_local_mode(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _forge(monkeypatch, {})
    assert _status_stack(repo, capsys)[0]["checks"] == "-"

    local = _init(tmp_path / "local", mode="local", origin=False)
    _start(local, 1)
    calls = _forge(monkeypatch, why="must not be asked")
    (q1,) = _status_stack(local, capsys)
    assert (q1["pr"], q1["checks"]) == ("-", "-")
    assert calls == [c for c in calls if "--head" not in c]


def test_a_draft_with_a_reopened_item_still_open_reads_fixing(
        tmp_path: Path, monkeypatch, capsys):
    """The CI fix round (issue #332) turns the PR back to draft and reopens
    the item; the draft must not read like one never marked ready."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    draft = {Q1: [{"number": 7, "state": "OPEN", "isDraft": True}]}
    _forge(monkeypatch, draft)
    assert _status_stack(repo, capsys)[0]["pr"] == "#7/draft"

    _progress(repo, "📋", REOPENED)
    (q1,) = _status_stack(repo, capsys)
    assert q1["pr"] == "#7/draft(fixing)"
    assert q1["awaiting"] == "no"

    # Completed again: the round is over, and it reads as a plain draft.
    _progress(repo, "✅", REOPENED)
    assert _status_stack(repo, capsys)[0]["pr"] == "#7/draft"


def test_fixing_is_read_from_each_branch_and_only_for_its_own_queues(
        tmp_path: Path, monkeypatch, capsys):
    """Queue 002 on top: the reopened item is queue 001's, so only queue
    001's draft reads fixing — and it does while queue 002 is checked out,
    because each branch's own progress.md answers for it."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _start(repo, 2, "--base", Q1)
    _plan(repo, 2, "### Item 002: Beta\n")
    _progress(repo, "📋", REOPENED)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": True}],
                         Q2: [{"number": 8, "state": "OPEN", "isDraft": True}]})
    assert [s["pr"] for s in _status_stack(repo, capsys)] == [
        "#7/draft", "#8/draft"]
    _git(["switch", Q1], repo)
    _progress(repo, "📋", REOPENED)
    _git(["switch", Q2], repo)
    assert [s["pr"] for s in _status_stack(repo, capsys)] == [
        "#7/draft(fixing)", "#8/draft"]


def test_an_open_pr_with_a_reopened_item_is_not_marked_fixing(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _progress(repo, "📋", REOPENED)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": False}]})
    assert _status_stack(repo, capsys)[0]["pr"] == "#7/open"


# --------------------------------------------------------------------------- #
# issue #332 — the CI fix round's count
# --------------------------------------------------------------------------- #
ROUND_2 = ("  - **2026-09-20** → reopened: CI build: test_001 [CI round 1]\n"
           "  - **2026-09-29** → reopened: CI build: test_001 [CI round 2]\n")


def test_a_failure_with_legs_still_running_names_each_as_pending(
        tmp_path: Path, monkeypatch, capsys):
    """Failure still wins (#330), but a red answer with a leg still running
    is not settled (#332): each running check is named below the failing."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup": [
        _run_check("build (ubuntu)", "COMPLETED", "FAILURE"),
        _run_check("build (windows)", "IN_PROGRESS"),
        _context("ci/legacy", "PENDING"),
        _run_check("lint", "COMPLETED", "SUCCESS")]}]})
    (q1,) = _status_stack(repo, capsys)
    assert (q1["checks"], q1["failing"], q1["running"]) == (
        "failure", ["build (ubuntu)"], ["build (windows)", "ci/legacy"])
    # Settled: no pending line at all.
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup": [
        _run_check("build (ubuntu)", "COMPLETED", "FAILURE"),
        _run_check("build (windows)", "COMPLETED", "SUCCESS")]}]})
    assert "running" not in _status_stack(repo, capsys)[0]
    # Plain pending names nothing: only a red answer needs settling.
    assert aide.running_checks([_run_check("x", "QUEUED"),
                                _run_check("x", "IN_PROGRESS")]) == ["x"]


def test_a_draft_or_failing_pr_names_the_ci_fix_rounds_begun(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _progress(repo, "✅", ROUND_2)
    red = [_run_check("build", "COMPLETED", "FAILURE")]
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                               "statusCheckRollup": red}]})
    (q1,) = _status_stack(repo, capsys)
    assert (q1["checks"], q1["failing"], q1["rounds"]) == ("failure", ["build"], 2)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": True}]})
    (q1,) = _status_stack(repo, capsys)
    assert (q1["pr"], q1["rounds"]) == ("#7/draft", 2)
    # Green: nothing for a runner to count, and no git spawn to pay for it.
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "statusCheckRollup":
                               [_run_check("build", "COMPLETED", "SUCCESS")]}]})
    assert "rounds" not in _status_stack(repo, capsys)[0]
    # No CI reopening at all: a red PR prints no count line.
    _progress(repo, "✅", REOPENED)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                               "statusCheckRollup": red}]})
    assert "rounds" not in _status_stack(repo, capsys)[0]


def _two_queue_branch(repo: Path) -> None:
    """Queue 001's branch also carries queue 002 (a maintenance queue and the
    stage queue after it): items 001 and 002, both merged."""
    _start(repo, 1)
    _plan(repo, 1)
    _plan(repo, 2, "### Item 002: Beta\n")
    (repo / "docs" / "aide" / "progress.md").write_text(
        PROGRESS.format(icon="✅", trail=ROUND_2).replace(
            "- 📋 Beta. *(Item 002)*", "- ✅ Beta. *(Item 002)*"),
        encoding="utf-8")
    _commit(repo, "both merged, item 001 after two CI rounds")


def test_a_ci_reopening_on_a_queue_branch_counts_every_queue_it_carries(
        tmp_path: Path):
    """Item 002 is queue 002's, and queue 001's item carries round 2: one PR,
    one CI, one count — so 002's reopening begins round 3."""
    repo = _init(tmp_path)
    _two_queue_branch(repo)
    assert aide.main(["--repo", str(repo), "progress", "reopen", "2",
                      "--reason", "CI lint: step ruff", "--date", "2026-09-30",
                      "--no-commit"]) == 0
    text = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "  - **2026-09-30** → reopened: CI lint: step ruff [CI round 3]" in text


# --------------------------------------------------------------------------- #
# queue pr — the draft PR against the recorded base
# --------------------------------------------------------------------------- #
def test_pr_pushes_first_and_opens_a_draft_against_the_recorded_base(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    assert _on_origin(repo, Q1) != _head(repo)
    calls = _forge(monkeypatch, {})
    assert _run(repo, "pr", "--body-file", _body(tmp_path)) == 0
    assert _on_origin(repo, Q1) == _head(repo)
    (create,) = _writes(calls)
    assert create[:3] == ["pr", "create", "--draft"]
    opts = dict(zip(create[3::2], create[4::2]))
    assert opts["--base"] == "main" and opts["--head"] == Q1
    assert opts["--title"] == "aide: work queue 001"
    assert Path(opts["--body-file"]).read_text(encoding="utf-8") == \
        "Plan for queue 001.\n"


def test_pr_on_a_stacked_queue_targets_the_queue_below(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _start(repo, 2, "--base", Q1)
    _plan(repo, 2, "### Item 002: Beta\n")
    calls = _forge(monkeypatch, {})
    assert _run(repo, "pr", "--body", "Stacked on queue 001.") == 0
    (create,) = _writes(calls)
    opts = dict(zip(create[3::2], create[4::2]))
    assert (opts["--base"], opts["--head"]) == (Q1, Q2)
    assert opts["--title"] == "aide: work queue 002"
    assert opts["--body"] == "Stacked on queue 001."


def test_pr_titles_a_maintenance_and_stage_pair_by_both_numbers(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _plan(repo, 2, "### Item 002: Beta\n")
    calls = _forge(monkeypatch, {})
    assert _run(repo, "pr", "--body", "Maintenance 001, stage 002.") == 0
    (create,) = _writes(calls)
    assert create[create.index("--title") + 1] == "aide: work queues 001-002"


def test_pr_names_the_open_pr_and_opens_nothing(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    for existing in ({"number": 7, "state": "OPEN", "isDraft": True},
                     {"number": 7, "state": "OPEN", "isDraft": False}):
        calls = _forge(monkeypatch, {Q1: [existing]})
        assert _run(repo, "pr", "--body", "x") == 0
        assert _writes(calls) == []


@pytest.mark.parametrize("state", ["CLOSED", "MERGED"])
def test_pr_opens_no_second_pr_over_a_closed_or_merged_one(
        tmp_path: Path, monkeypatch, state: str):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": state}]})
    assert _run(repo, "pr", "--body", "x") == 1
    assert _writes(calls) == []


def test_pr_refuses_a_branch_with_nothing_ahead_of_its_base(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    calls = _forge(monkeypatch, {})
    assert _run(repo, "pr", "--body", "x") == 1
    assert calls == []


def test_pr_refuses_where_the_forge_cannot_be_asked(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, why="gh is not on PATH")
    assert _run(repo, "pr", "--body", "x") == 1
    assert _writes(calls) == []
    assert _on_origin(repo, Q1) != _head(repo)


def test_pr_that_the_forge_refuses_exits_1(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _forge(monkeypatch, {}, fail="create")
    assert _run(repo, "pr", "--body", "x") == 1


@pytest.mark.parametrize("argv", [
    ["pr"],
    ["pr", "--body", "x", "--body-file", "body.md"],
    ["pr", "--body-file", "no-such-file.md"],
], ids=["no-body", "both-bodies", "missing-body-file"])
def test_pr_takes_exactly_one_body(tmp_path: Path, monkeypatch, argv):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {})
    assert _run(repo, *argv) == 2
    assert calls == []


# --------------------------------------------------------------------------- #
# queue ready — mark ready, or back to draft
# --------------------------------------------------------------------------- #
def test_ready_pushes_first_then_marks_the_draft_ready(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _git(["push"], repo)
    (repo / "built.txt").write_text("the last item\n", encoding="utf-8")
    _commit(repo, "the last item's merge")
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": True}]})
    assert _run(repo, "ready") == 0
    assert _on_origin(repo, Q1) == _head(repo)
    assert _writes(calls) == [["pr", "ready", "7"]]


def test_ready_leaves_a_ready_pr_alone_and_exits_0(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": False}]})
    assert _run(repo, "ready") == 0
    assert _writes(calls) == []
    # Still pushed: CI sees the tree the queue built.
    assert _on_origin(repo, Q1) == _head(repo)


def test_ready_names_its_queue_from_another_branch(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _git(["switch", "main"], repo)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": True}]})
    assert _run(repo, "ready", "1") == 0
    assert _writes(calls) == [["pr", "ready", "7"]]
    assert _on_origin(repo, Q1) == _head(repo, Q1)


def test_undo_turns_a_ready_pr_back_to_draft_and_pushes_nothing(
        tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    before = _on_origin(repo, Q1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": False}]})
    assert _run(repo, "ready", "--undo") == 0
    assert _writes(calls) == [["pr", "ready", "7", "--undo"]]
    assert _on_origin(repo, Q1) == before


def test_undo_leaves_a_draft_alone_and_exits_0(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": True}]})
    assert _run(repo, "ready", "--undo") == 0
    assert _writes(calls) == []


@pytest.mark.parametrize("undo", [[], ["--undo"]], ids=["ready", "undo"])
@pytest.mark.parametrize("prs", [
    [],
    [{"number": 7, "state": "CLOSED"}],
    [{"number": 7, "state": "MERGED"}],
], ids=["no-pr", "closed", "merged"])
def test_ready_refuses_a_branch_with_no_pr_to_mark(
        tmp_path: Path, monkeypatch, prs, undo):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    before = _on_origin(repo, Q1)
    calls = _forge(monkeypatch, {Q1: prs})
    assert _run(repo, "ready", *undo) == 1
    assert _writes(calls) == []
    assert _on_origin(repo, Q1) == before


def test_ready_refuses_where_the_forge_cannot_be_asked(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, why="gh is not on PATH")
    assert _run(repo, "ready") == 1
    assert _writes(calls) == []


def test_ready_that_the_forge_refuses_exits_1(tmp_path: Path, monkeypatch):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": True}]},
           fail="ready")
    assert _run(repo, "ready") == 1


# --------------------------------------------------------------------------- #
# the refusals both verbs share
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("argv", [["pr", "--body", "x"], ["ready"],
                                  ["ready", "--undo"]],
                         ids=["pr", "ready", "undo"])
def test_off_a_queue_branch_both_refuse_and_ask_nothing(
        tmp_path: Path, monkeypatch, argv):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _git(["switch", "main"], repo)
    calls = _forge(monkeypatch, {})
    assert _run(repo, *argv) == 1
    # A specs-queue branch is not one either: its queue branch carries the PR.
    assert aide.main(["--repo", str(repo), "queue", "start", "1", "--specs"]) == 0
    assert _run(repo, *argv) == 1
    # Nor is a queue number with no branch here.
    assert _run(repo, argv[0], "5", *argv[1:]) == 1
    assert calls == []


@pytest.mark.parametrize("argv", [["pr", "--body", "x"], ["ready"]],
                         ids=["pr", "ready"])
def test_local_mode_and_no_origin_both_refuse_and_ask_nothing(
        tmp_path: Path, monkeypatch, argv):
    local = _init(tmp_path / "a", mode="local", origin=False)
    _start(local, 1)
    _plan(local, 1)
    # `queue start` pushes off local mode, so the branch is started local
    # and the mode moved after — a checkout whose origin was since removed.
    no_origin = _init(tmp_path / "b", mode="local", origin=False)
    _start(no_origin, 1)
    _plan(no_origin, 1)
    (no_origin / "aide.toml").write_text(AIDE_TOML.format(mode="pr"),
                                         encoding="utf-8")
    calls = _forge(monkeypatch, {})
    assert _run(local, *argv) == 1
    assert _run(no_origin, *argv) == 1
    assert calls == []


# --------------------------------------------------------------------------- #
# review round 1 (PR #337)
# --------------------------------------------------------------------------- #
def test_a_forge_that_will_not_report_checks_still_answers_pr(
        tmp_path: Path, monkeypatch, capsys):
    """A token that may not read checks fails the rich query: `pr=` is read
    without the rollup, as before #330, and only `checks=` is unknown."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN"}]},
                   no_checks="gh exited 1: Resource not accessible by integration")
    (q1,) = _status_stack(repo, capsys)
    assert (q1["pr"], q1["checks"]) == ("#7/open", "unknown")
    assert "Resource not accessible" in q1["why"]
    assert q1["awaiting"] == "yes"
    listed = [c for c in calls if "--head" in c]
    assert [("statusCheckRollup" in c[c.index("--json") + 1]) for c in listed] \
        == [True, False]


def test_checks_read_none_right_after_ready_before_ci_registers(
        tmp_path: Path, monkeypatch, capsys):
    """Nothing tells "not started yet" from "no CI": the forge reports an
    empty rollup for both, so the first read after `ready` is none."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": True,
                               "statusCheckRollup": []}]})
    assert _run(repo, "ready") == 0
    _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN", "isDraft": False,
                               "statusCheckRollup": []}]})
    (q1,) = _status_stack(repo, capsys)
    assert (q1["pr"], q1["checks"]) == ("#7/open", "none")


@pytest.mark.parametrize("argv,flag", [
    (["pr", "--body", "x", "--dry-run"], "--dry-run"),
    (["pr", "--body", "x", "--base", "main"], "--base"),
    (["pr", "--body", "x", "--undo"], "--undo"),
    (["pr", "--body", "x", "--through", "2"], "--through"),
    (["ready", "--dry-run"], "--dry-run"),
    (["ready", "--date", "2026-09-29"], "--date"),
    (["ready", "--body", "x"], "--body"),
    (["ready", "--body-file", "body.md"], "--body-file"),
    (["ready", "--undo", "--specs"], "--specs"),
    (["ready", "--no-commit"], "--no-commit"),
], ids=["pr-dry-run", "pr-base", "pr-undo", "pr-through", "ready-dry-run",
        "ready-date", "ready-body", "ready-body-file", "undo-specs",
        "ready-no-commit"])
def test_an_option_the_action_does_not_read_is_refused(
        tmp_path: Path, monkeypatch, capsys, argv, flag):
    """`ready --dry-run` must not push and flip: refused before anything."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    before = _on_origin(repo, Q1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": True}]})
    capsys.readouterr()
    assert _run(repo, *argv) == 2
    assert calls == [] and _on_origin(repo, Q1) == before
    assert flag in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["start", "2", "--undo"],
    ["start", "2", "--body", "x"],
    ["tidy", "1", "--body-file", "body.md"],
    ["gate", "1", "--undo"],
    ["restack", "--body", "x"],
], ids=["start-undo", "start-body", "tidy-body-file", "gate-undo", "restack-body"])
def test_the_older_actions_refuse_the_pr_options(tmp_path: Path, monkeypatch, argv):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    head = _head(repo)
    assert _run(repo, *argv) == 2
    assert _head(repo) == head
    assert _git(["branch", "--list", Q2], repo).stdout.strip() == ""


def test_pr_refuses_a_branch_with_no_recorded_base_and_says_so(
        tmp_path: Path, monkeypatch, capsys):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _git(["config", "--unset", f"branch.{Q1}.aide-base"], repo)
    calls = _forge(monkeypatch, {})
    capsys.readouterr()
    assert _run(repo, "pr", "--body", "x") == 1
    assert "no recorded base" in capsys.readouterr().err
    assert calls == []


@pytest.mark.parametrize("argv,prs", [
    (["pr", "--body", "x"], []),
    (["ready"], [{"number": 7, "state": "OPEN", "isDraft": True}]),
], ids=["pr", "ready"])
def test_a_failed_push_refuses_and_changes_nothing_on_the_forge(
        tmp_path: Path, monkeypatch, capsys, argv, prs):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    _git(["remote", "set-url", "origin", str(tmp_path / "gone.git")], repo)
    calls = _forge(monkeypatch, {Q1: prs})
    capsys.readouterr()
    assert _run(repo, *argv) == 1
    assert "FAILED" in capsys.readouterr().err
    assert _writes(calls) == []


@pytest.mark.parametrize("argv,draft,said", [
    (["pr", "--body", "x"], True, "already has PR #7/draft"),
    (["ready"], False, "PR #7"),
    (["ready", "--undo"], True, "PR #7"),
], ids=["pr-names-it", "already-ready", "already-a-draft"])
def test_the_idempotent_outcomes_name_the_pr(
        tmp_path: Path, monkeypatch, capsys, argv, draft, said):
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    calls = _forge(monkeypatch, {Q1: [{"number": 7, "state": "OPEN",
                                       "isDraft": draft}]})
    capsys.readouterr()
    assert _run(repo, *argv) == 0
    out = capsys.readouterr().out
    assert said in out and "already" in out
    assert _writes(calls) == []


# --------------------------------------------------------------------------- #
# review round 2 (PR #337)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("argv,prs", [
    (["pr", "--body", "x"], []),
    (["ready"], [{"number": 7, "state": "OPEN", "isDraft": True}]),
], ids=["pr", "ready"])
def test_a_commit_count_git_cannot_read_refuses_and_changes_nothing(
        tmp_path: Path, monkeypatch, capsys, argv, prs):
    """Every `rev-list --count` fails: `queue pr`'s count ahead of its base
    and the push-first count both refuse rather than read "not ahead"."""
    repo = _init(tmp_path)
    _start(repo, 1)
    _plan(repo, 1)
    before = _on_origin(repo, Q1)
    real = aide.git

    def failing(args, repo_root, check=True):
        if args[:2] == ["rev-list", "--count"]:
            return subprocess.CompletedProcess(["git", *args], 128, "",
                                               "fatal: bad revision")
        return real(args, repo_root, check=check)

    monkeypatch.setattr(aide, "git", failing)
    calls = _forge(monkeypatch, {Q1: prs})
    capsys.readouterr()
    assert _run(repo, *argv) == 1
    assert "could not count" in capsys.readouterr().err
    assert _writes(calls) == []
    assert _on_origin(repo, Q1) == before


def test_a_gh_missing_from_path_is_asked_once_not_retried(
        tmp_path: Path, monkeypatch):
    calls = _forge(monkeypatch, why="gh is not on PATH")
    got, why = aide._branch_pr_facts(tmp_path, Q1)
    assert (got, why) == (None, "gh is not on PATH")
    assert len(calls) == 1
