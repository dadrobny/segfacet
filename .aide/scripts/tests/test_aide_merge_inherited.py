"""`aide merge` separates a failure the item caused from one it inherited
(issue #275, §4).

Four layers, in the order the code has them: reading a JUnit report into
failure ids; deciding whether a command's failures are comparable at all; the
result store under git's own directory; and the verb, driven through `main()`
in a `git.mode = "local"` repository. The verb's suite runs are replaced by a
fake that reads the failing ids from a tracked `FAILS` file, so each tree
carries its own answer and the base run is exercised by what is checked out
when it runs — no pytest is spawned here. `tests/test_fixture_consumer.py`
runs the real pytest against an installed engine.

A fifth layer closes the module: `aide test` recording the validator's run in
the same store, with who ran it, where and at which commit, and `aide merge`
taking that run in place of its own where the tree it lands is the tree that
ran — and not otherwise.

Asserted on cells, files and exit codes; prose only where
`test_aide_help_pins.py` names a test here as the guard of a sentence.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_inherited", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
tests_dir = "tests"

[git]
mode = "local"
main_branch = "main"
branch_prefix = "aide/"
"""

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 🚧 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 🚧 |

## Stage 1 — Rules — 🚧

**Deliverables.**
- 📋 Bounds. *(Item 001)*
- 📋 Limits. *(Item 002)*

**Acceptance.**
- [ ] Rules fire.
"""

QUEUE = """\
# Demo — Work Queue 001

### Item 001: Bounds
Bounds.

### Item 002: Limits
Limits.
"""

INSIGHTS = """\
# Insight Inbox

_Entries below, newest last._
"""

LEGACY = "tests/test_legacy.py::test_old"


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _commit(repo: Path, message: str) -> None:
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", message], repo)


def _init_repo(path: Path, fails: str = LEGACY + "\n",
               toml: str = AIDE_TOML) -> Path:
    path.mkdir(parents=True)
    (path / "aide.toml").write_text(toml, encoding="utf-8")
    d = path / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir(parents=True)
    (d / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (d / "queue" / "queue-001.md").write_text(QUEUE, encoding="utf-8")
    (d / "insights.md").write_text(INSIGHTS, encoding="utf-8")
    (path / "FAILS").write_text(fails, encoding="utf-8")
    (path / "src").mkdir()
    (path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    _run(["git", "init", "-b", "main"], path)
    _run(["git", "config", "user.email", "t@example.com"], path)
    _run(["git", "config", "user.name", "Tester"], path)
    _commit(path, "init")
    return path


def _work(repo: Path, name: str, extra_failure: str = "") -> None:
    (repo / "src" / f"{name}.py").write_text("y = 2\n", encoding="utf-8")
    if extra_failure:
        with (repo / "FAILS").open("a", encoding="utf-8") as fh:
            fh.write(extra_failure + "\n")
    _commit(repo, f"work {name}")


class FakeSuite:
    """`run_test_suite`, answering from the tree that is checked out.

    The failing ids are the lines of the tracked `FAILS` file, so a run at
    the base and a run after the merge read different answers exactly when the
    item changed that file. Records every call, with the branch it ran on.
    """

    def __init__(self, repo: Path):
        self.repo = repo
        self.calls = []
        self.raise_on_detached = None

    def __call__(self, repo_root, argv, identify):
        head = subprocess.run(["git", "symbolic-ref", "-q", "--short", "HEAD"],
                              cwd=str(repo_root), stdout=subprocess.PIPE,
                              encoding="utf-8").stdout.strip()
        self.calls.append((head or "(detached)", identify, list(argv)))
        if self.raise_on_detached is not None and not head:
            raise self.raise_on_detached
        ids = tuple(sorted(l.strip() for l in (Path(repo_root) / "FAILS")
                           .read_text(encoding="utf-8").splitlines() if l.strip()))
        code = 1 if ids else 0
        if not identify:
            return aide.SuiteRun(code, 3.4, None, "failures were not identified")
        return aide.SuiteRun(code, 3.4, ids)


@pytest.fixture
def fake(monkeypatch, tmp_path):
    suite = FakeSuite(tmp_path)
    monkeypatch.setattr(aide, "run_test_suite", suite)
    return suite


def _merge(repo: Path, number: int, *extra: str) -> int:
    return aide.main(["--repo", str(repo), "merge", str(number), *extra])


def _claim(repo: Path) -> None:
    assert aide.main(["--repo", str(repo), "claim"]) == 0


def _rows(repo: Path) -> list:
    text = (repo / "docs" / "aide" / "ledger.md").read_text(encoding="utf-8")
    return [dict(zip(aide.LEDGER_COLUMNS, cells))
            for _, cells in aide.ledger_rows(text)]


def _status(repo: Path, number: int) -> str:
    text = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    return aide._parse_item_status(text.splitlines())[2].get(number, "planned")


def _branches(repo: Path) -> list:
    out = _run(["git", "branch", "--format=%(refname:short)"], repo).stdout
    return [l.strip() for l in out.splitlines() if l.strip()]


def _current(repo: Path) -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip()


def _open_defects(repo: Path) -> list:
    text = (repo / "docs" / "aide" / "insights.md").read_text(encoding="utf-8")
    return [e for e in aide.parse_insights(text)
            if e.type == "defect" and not e.ticked]


# --------------------------------------------------------------------------- #
# the report — JUnit XML into failure ids
# --------------------------------------------------------------------------- #
REPORT = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="1" failures="1" tests="4">
<testcase classname="tests.test_a.TestX" name="test_one[1.5]" time="0.1">
  <failure message="assert 0">boom</failure></testcase>
<testcase classname="tests.test_a" name="test_two" time="0.1"/>
<testcase classname="tests.test_a" name="test_three" time="0.1">
  <skipped message="later"/></testcase>
<testcase classname="tests.test_a" name="test_four" time="0.1">
  <error message="teardown">boom</error></testcase>
<testcase classname="" name="tests.test_broken" time="0.0">
  <error message="collection failure">ImportError</error></testcase>
</testsuite></testsuites>
"""


def test_a_report_names_every_failure_and_error_including_collection(tmp_path: Path):
    ids = aide.junit_failure_ids(REPORT)
    assert ids == ("tests.test_a.TestX::test_one[1.5]", "tests.test_a::test_four",
                   "tests.test_broken")


def test_a_report_read_in_its_checkout_gives_pytest_node_ids(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    for name in ("test_a.py", "test_broken.py"):
        (tmp_path / "tests" / name).write_text("", encoding="utf-8")
    assert aide.junit_failure_ids(REPORT, tmp_path) == (
        "tests/test_a.py::TestX::test_one[1.5]", "tests/test_a.py::test_four",
        "tests/test_broken.py")


def test_an_unreadable_report_is_no_answer_rather_than_a_green_one():
    assert aide.junit_failure_ids("<not xml") is None
    assert aide.junit_failure_ids("<html><body/></html>") is None
    assert aide.junit_failure_ids("<testsuite/>") == ()


# --------------------------------------------------------------------------- #
# which commands can be compared
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("argv,flag", [
    (["py", "-m", "pytest", "-x"], "-x"),
    (["py", "-m", "pytest", "-qx"], "-qx"),
    (["py", "-m", "pytest", "--maxfail=2"], "--maxfail=2"),
    (["py", "-m", "pytest", "--maxfail", "2"], "--maxfail"),
    (["py", "-m", "pytest", "--lf"], "--lf"),
    (["py", "-m", "pytest", "--failed-first"], "--failed-first"),
    (["py", "-m", "pytest", "--sw"], "--sw"),
    (["py", "-m", "pytest", "-rxs", "-q"], None),
    (["py", "-m", "pytest", "-k", "x", "-p", "no:xdist"], None),
    (["py", "-m", "pytest", "-q", "tests"], None),
])
def test_an_order_dependent_flag_is_found_and_a_value_is_not_one(argv, flag):
    assert aide.order_dependent_flag(argv) == flag


def test_only_pytest_run_as_a_module_is_comparable():
    assert aide.failure_identity_refusal(["/v/bin/python", "-m", "pytest"]) is None
    assert "not `<python> -m pytest`" in aide.failure_identity_refusal(["make", "test"])
    assert "not `<python> -m pytest`" in aide.failure_identity_refusal(
        ["python", "-m", "unittest"])
    assert "--lf" in aide.failure_identity_refusal(["python", "-m", "pytest", "--lf"])


# --------------------------------------------------------------------------- #
# the store — keyed by tree and command, clean trees only, pruned
# --------------------------------------------------------------------------- #
def test_the_key_moves_with_the_tree_and_with_the_command():
    a = aide.suite_result_key("t1", ["python", "-m", "pytest"])
    assert a == aide.suite_result_key("t1", ["python", "-m", "pytest"])
    assert a != aide.suite_result_key("t2", ["python", "-m", "pytest"])
    assert a != aide.suite_result_key("t1", ["python", "-m", "pytest", "-q"])


def test_a_stored_result_is_read_back_and_nothing_else_is(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    argv = ["python", "-m", "pytest"]
    run = aide.SuiteRun(1, 12.5, ("a::b",))
    path = aide.write_suite_result(repo, "t1", argv, run, now=1000.0)
    assert path is not None and path.parent == aide.suite_results_dir(repo)
    assert ".git" in path.parts                 # never in the work tree
    back = aide.read_suite_result(repo, "t1", argv, now=1000.0)
    assert back == aide.SuiteRun(1, 12.5, ("a::b",), reused=True)
    assert aide.read_suite_result(repo, "t1", argv + ["-q"], now=1000.0) is None
    assert aide.read_suite_result(repo, "t2", argv, now=1000.0) is None
    # Aged out: a miss, not a stale answer.
    late = 1000.0 + aide.SUITE_RESULT_MAX_AGE + 1
    assert aide.read_suite_result(repo, "t1", argv, now=late) is None
    # A run that could not name its failures is recorded but never reused.
    aide.write_suite_result(repo, "t3", argv, aide.SuiteRun(2, 1.0, None, "x"),
                            now=1000.0)
    assert aide.read_suite_result(repo, "t3", argv, now=1000.0) is None


def test_a_write_prunes_what_has_aged_out(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    argv = ["python", "-m", "pytest"]
    old = aide.write_suite_result(repo, "t1", argv, aide.SuiteRun(0, 1.0, ()),
                                  now=1000.0)
    junk = old.parent / "junk.json"
    junk.write_text("not json", encoding="utf-8")
    later = 1000.0 + aide.SUITE_RESULT_MAX_AGE + 5
    aide.write_suite_result(repo, "t2", argv, aide.SuiteRun(0, 1.0, ()), now=later)
    assert not old.exists()
    assert junk.exists()        # its mtime is now: unreadable, but not old
    assert aide.read_suite_result(repo, "t2", argv, now=later) is not None


def test_only_a_run_over_a_clean_tree_is_stored(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo")
    argv = ["python", "-m", "pytest"]
    folder = aide.suite_results_dir(repo)
    (repo / "src" / "a.py").write_text("x = 'edited'\n", encoding="utf-8")
    aide.recorded_suite_run(repo, argv, identify=True)
    assert not folder.exists() or not list(folder.glob("*.json"))
    _run(["git", "checkout", "--", "src/a.py"], repo)
    aide.recorded_suite_run(repo, argv, identify=True)
    (stored,) = folder.glob("*.json")
    assert json.loads(stored.read_text(encoding="utf-8"))["failures"] == [LEGACY]


# --------------------------------------------------------------------------- #
# where the base stood, for a merge an earlier run made
# --------------------------------------------------------------------------- #
def test_a_landed_merge_commit_names_its_first_parent(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/001-bounds"], repo)
    _work(repo, "b")
    tip = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "switch", "main"], repo)
    _work(repo, "moved")
    before = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "merge", "--no-ff", "--no-edit", "aide/001-bounds"], repo)
    _work(repo, "fix")          # a fix commit after the red run
    assert aide.landed_pre_merge_base(repo, "main", "aide/001-bounds", tip) == before


def test_a_landed_fast_forward_is_read_from_the_reflog(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    before = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "switch", "-c", "aide/001-bounds"], repo)
    _work(repo, "b")
    tip = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "switch", "main"], repo)
    _run(["git", "merge", "--no-edit", "aide/001-bounds"], repo)
    assert aide.landed_pre_merge_base(repo, "main", "aide/001-bounds", tip) == before


def test_a_fast_forward_the_reflog_does_not_record_is_not_guessed(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/001-bounds"], repo)
    _work(repo, "b")
    tip = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    _run(["git", "switch", "main"], repo)
    _run(["git", "merge", "--ff-only", "aide/001-bounds"], repo)
    _run(["git", "reflog", "expire", "--expire=all", "--all"], repo)
    assert aide.landed_pre_merge_base(repo, "main", "aide/001-bounds", tip) is None


# --------------------------------------------------------------------------- #
# the ledger — two more columns, and a fourteen-cell row still reads
# --------------------------------------------------------------------------- #
def test_a_fourteen_cell_row_and_a_sixteen_cell_row_both_read(tmp_path: Path):
    d = tmp_path / "docs"
    d.mkdir()
    old = ["001", "001", "1", "normal", "merged", "2", "1", "2", "2", "1",
           "0", "0", "2.6.1", "2026-09-20"]
    padded = old + ["", ""]
    new = old[:12] + ["2.7.0", "2026-09-25", "41", "3"]
    (d / "ledger.md").write_text(
        "# Run Ledger\n\n" + "\n".join(aide.ledger_row(r)
                                       for r in (old, padded, new)) + "\n",
        encoding="utf-8")
    assert aide.ledger_warnings(d) == []
    rows = [dict(zip(aide.LEDGER_COLUMNS, c))
            for _, c in aide.ledger_rows((d / "ledger.md").read_text(encoding="utf-8"))]
    assert rows[0].get("Suite s", "") == "" and rows[2]["Suite s"] == "41"
    # Fifteen cells is neither shape, and an integer column still holds integers.
    (d / "ledger.md").write_text(
        aide.ledger_row(old + ["4"]) + "\n"
        + aide.ledger_row(old[:12] + ["2.7.0", "2026-09-25", "slow", ""]) + "\n",
        encoding="utf-8")
    first, second = aide.ledger_warnings(d)
    assert "15 cell(s)" in first and "Suite s cell 'slow'" in second


def test_abandon_leaves_both_suite_cells_blank(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "1",
                      "--rounds", "5"]) == 0
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("", "")


# --------------------------------------------------------------------------- #
# aide merge — the gate, driven through the verb
# --------------------------------------------------------------------------- #
def test_a_green_run_records_its_time_and_zero_inherited(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _merge(repo, 1) == 0
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("3", "0")
    assert [c[0] for c in fake.calls] == ["main"]     # no base run for a green one


def test_no_test_leaves_both_suite_cells_blank(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    assert _merge(repo, 1, "--no-test") == 0
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("", "")
    assert fake.calls == []


def test_failures_the_base_already_had_are_admitted_and_recorded(
        tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    capsys.readouterr()

    assert _merge(repo, 1) == 0

    out = capsys.readouterr().out
    assert "inherited" in out and LEGACY in out
    assert _status(repo, 1) == "complete"
    assert _current(repo) == "main"
    # The base ran detached, in this checkout, and HEAD came back.
    assert [c[0] for c in fake.calls] == ["main", "(detached)"]
    (row,) = _rows(repo)
    assert row["Inherited"] == "1"
    (entry,) = _open_defects(repo)
    assert f"`{LEGACY}`" in entry.raw and entry.item == 1
    # Row, entry and tick are one commit.
    shown = _run(["git", "show", "--name-only", "--format=", "HEAD"], repo).stdout
    for rel in ("docs/aide/ledger.md", "docs/aide/insights.md",
                "docs/aide/progress.md"):
        assert rel in shown


def test_a_second_item_over_the_same_red_base_adds_no_second_entry(
        tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    assert _merge(repo, 1) == 0
    _claim(repo)
    _work(repo, "c")
    assert _merge(repo, 2) == 0
    assert len(_open_defects(repo)) == 1
    assert [r["Inherited"] for r in _rows(repo)] == ["1", "1"]


def test_a_failure_the_base_does_not_have_is_refused_and_listed_apart(
        tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b", extra_failure="tests/test_b.py::test_new")
    capsys.readouterr()

    assert _merge(repo, 1) == 1

    err = capsys.readouterr().err
    caused, _, inherited = err.partition("inherited:")
    assert "1 failure(s) are this item's" in caused
    assert "tests/test_b.py::test_new" in caused and LEGACY not in caused
    assert LEGACY in inherited
    assert _status(repo, 1) != "complete"
    assert _current(repo) == "main"
    assert "aide/001-bounds" in _branches(repo)
    assert not (repo / "docs" / "aide" / "ledger.md").exists()
    assert _open_defects(repo) == []


def test_a_retry_reuses_the_base_run_it_stored(tmp_path: Path, fake, capsys):
    """The first run is refused; the retry after a fix re-runs only the
    post-merge tree, reading the base's result back from the store."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b", extra_failure="tests/test_b.py::test_new")
    assert _merge(repo, 1) == 1
    (repo / "FAILS").write_text(LEGACY + "\n", encoding="utf-8")
    _commit(repo, "fix the item's own failure")
    fake.calls.clear()
    capsys.readouterr()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]
    assert "a stored result for that tree, not re-run" in capsys.readouterr().out
    assert _status(repo, 1) == "complete"


def test_a_retried_fast_forward_finds_its_base_in_the_reflog(
        tmp_path: Path, fake, monkeypatch):
    """Nothing stored this time: the retry has to find the base itself."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b", extra_failure="tests/test_b.py::test_new")
    assert _merge(repo, 1) == 1
    folder = aide.suite_results_dir(repo)
    for stored in folder.glob("*.json"):
        stored.unlink()
    (repo / "FAILS").write_text(LEGACY + "\n", encoding="utf-8")
    _commit(repo, "fix the item's own failure")
    fake.calls.clear()

    assert _merge(repo, 1) == 0
    assert [c[0] for c in fake.calls] == ["main", "(detached)"]
    assert _current(repo) == "main"


@pytest.mark.parametrize("command", ["python -m pytest -x", "make test"])
def test_a_command_that_cannot_be_compared_keeps_the_plain_gate(
        tmp_path: Path, fake, capsys, command):
    toml = AIDE_TOML + f'\n[python]\ntest_command = "{command}"\n'
    repo = _init_repo(tmp_path / "repo", toml=toml)
    _claim(repo)
    _work(repo, "b")
    capsys.readouterr()

    assert _merge(repo, 1) == 1

    assert "not compared with the base" in capsys.readouterr().err
    assert [(c[0], c[1]) for c in fake.calls] == [("main", False)]
    assert _status(repo, 1) != "complete"


def test_a_signal_during_the_base_run_leaves_the_base_checked_out(
        tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    fake.raise_on_detached = aide._Terminated(15)

    with pytest.raises(aide._Terminated):
        _merge(repo, 1)

    assert _current(repo) == "main"
    assert "aide/001-bounds" in _branches(repo)
    assert _status(repo, 1) != "complete"


def test_a_signal_just_after_the_base_checkout_still_switches_back(
        tmp_path: Path, fake, monkeypatch):
    """The detaching switch is inside the restoring `try`: a signal landing
    before the suite starts still puts the base branch back."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    real_git = aide.git

    def git(args, repo_root, check=True):
        res = real_git(args, repo_root, check)
        if args[:2] == ["switch", "--detach"]:
            raise aide._Terminated(15)
        return res

    monkeypatch.setattr(aide, "git", git)
    with pytest.raises(aide._Terminated):
        _merge(repo, 1)
    monkeypatch.setattr(aide, "git", real_git)

    assert _current(repo) == "main"
    assert "aide/001-bounds" in _branches(repo)
    assert _status(repo, 1) != "complete"


def test_a_failed_switch_back_stops_before_the_tick(
        tmp_path: Path, fake, monkeypatch):
    """Nothing is committed onto a detached HEAD: a base branch that cannot be
    checked out again after the base run stops the merge, and says how."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    head = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    real_git = aide.git

    def git(args, repo_root, check=True):
        if args[:2] == ["switch", "--discard-changes"]:
            return subprocess.CompletedProcess(args, 128, "", "index.lock exists")
        return real_git(args, repo_root, check)

    monkeypatch.setattr(aide, "git", git)
    with pytest.raises(RuntimeError, match="git switch main"):
        _merge(repo, 1)
    monkeypatch.setattr(aide, "git", real_git)

    assert _current(repo) == "HEAD"
    assert "aide/001-bounds" in _branches(repo)
    assert _run(["git", "rev-parse", "HEAD"], repo).stdout.strip() != head
    _run(["git", "switch", "main"], repo)
    assert _status(repo, 1) != "complete"


def test_the_claim_branch_is_deleted_inside_the_restoring_window(
        tmp_path: Path, monkeypatch):
    """A signal landing just after `git branch -d` must still restore the
    branch: the handler is installed, and the tip read, before the deletion."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    real_git = aide.git

    def git(args, repo_root, check=True):
        res = real_git(args, repo_root, check)
        if args[:2] == ["branch", "-d"]:
            raise aide._Terminated(15)
        return res

    monkeypatch.setattr(aide, "git", git)
    with pytest.raises(aide._Terminated):
        _merge(repo, 1, "--no-test")
    monkeypatch.setattr(aide, "git", real_git)

    assert "aide/001-bounds" in _branches(repo)
    assert aide._recorded_branch_base(repo, "aide/001-bounds") == "main"


# --------------------------------------------------------------------------- #
# the inbox entry
# --------------------------------------------------------------------------- #
def test_the_entry_skips_ids_an_open_entry_names_and_caps_its_list():
    ids = [f"tests/test_m.py::test_{i:02d}" for i in range(24)]
    text = (INSIGHTS + "- [ ] defect — `tests/test_m.py::test_00` is red "
            "*(item 004, 2026-09-01)*\n"
            "- [x] defect — tests/test_m.py::test_01 was red "
            "*(item 004, 2026-09-01)* → item 005\n")
    entry = aide.inherited_failures_entry(text, ids, 7, "main", "2026-09-25")
    assert "test_00`" not in entry                  # an open entry names it
    assert "`tests/test_m.py::test_01`" in entry    # a closed one does not count
    assert "(+3 more)" in entry and entry.startswith("- [ ] defect — 23 tests")
    assert entry.count("`tests/test_m.py::") == 20
    (parsed,) = aide.parse_insights(entry)
    assert parsed.type == "defect" and parsed.item == 7
    assert parsed.date == "2026-09-25"


def test_an_id_inside_a_longer_one_is_not_taken_as_named():
    text = INSIGHTS + "- [ ] defect — `a.py::test_bc` *(2026-09-01)*\n"
    entry = aide.inherited_failures_entry(text, ["a.py::test_b"], 1, "main",
                                          "2026-09-25")
    assert entry is not None and "`a.py::test_b`" in entry
    assert aide.inherited_failures_entry(text, ["a.py::test_bc"], 1, "main",
                                         "2026-09-25") is None


# --------------------------------------------------------------------------- #
# the runner — only pytest's tests-failed exit carries a whole report
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("code", [2, 3, 4, 5])
def test_a_pytest_exit_other_than_one_names_no_failures(tmp_path: Path,
                                                        monkeypatch, code):
    seen = []

    def run(argv, cwd=None, **_):
        seen.append(list(argv))
        report = next(a for a in argv if a.startswith("--junitxml="))
        Path(report.split("=", 1)[1]).write_text(REPORT, encoding="utf-8")
        return subprocess.CompletedProcess(argv, code)

    monkeypatch.setattr(aide.subprocess, "run", run)
    result = aide.run_test_suite(tmp_path, ["py", "-m", "pytest"], identify=True)
    assert result.returncode == code and result.failures is None
    assert f"exited {code}" in result.unidentified
    # The run is complete past a module that fails to import.
    assert "--continue-on-collection-errors" in seen[0]


def test_a_tests_failed_exit_reads_the_report(tmp_path: Path, monkeypatch):
    def run(argv, cwd=None, **_):
        report = next(a for a in argv if a.startswith("--junitxml="))
        Path(report.split("=", 1)[1]).write_text(REPORT, encoding="utf-8")
        return subprocess.CompletedProcess(argv, 1)

    monkeypatch.setattr(aide.subprocess, "run", run)
    result = aide.run_test_suite(tmp_path, ["py", "-m", "pytest"], identify=True)
    assert result.failures == aide.junit_failure_ids(REPORT, tmp_path)


def test_a_green_run_nothing_could_compare_leaves_inherited_blank(
        tmp_path: Path, fake):
    toml = AIDE_TOML + '\n[python]\ntest_command = "make test"\n'
    repo = _init_repo(tmp_path / "repo", fails="", toml=toml)
    _claim(repo)
    _work(repo, "b")
    assert _merge(repo, 1) == 0
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("3", "")


# --------------------------------------------------------------------------- #
# aide test — the validator's run, recorded; aide merge taking it (PR B)
# --------------------------------------------------------------------------- #
def _test(repo: Path) -> int:
    return aide.main(["--repo", str(repo), "test"])


def _records(repo: Path) -> list:
    folder = aide.suite_results_dir(repo)
    if folder is None or not folder.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(folder.glob("*.json"))]


def _in_review(repo: Path) -> None:
    assert aide.main(["--repo", str(repo), "progress", "set", "001",
                      "in-review"]) == 0


def test_aide_test_records_its_run_with_the_branch_and_commit(
        tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    head = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()

    assert _test(repo) == 1                 # the command's own exit code

    (record,) = _records(repo)
    assert (record["by"], record["branch"], record["commit"]) == (
        "aide test", "aide/001-bounds", head)
    assert record["failures"] == [LEGACY] and record["returncode"] == 1
    assert [c[0] for c in fake.calls] == ["aide/001-bounds"]
    assert "NOT recorded" not in capsys.readouterr().err


def test_aide_test_over_a_dirty_tree_records_nothing_and_says_so(
        tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    (repo / "src" / "a.py").write_text("x = 'edited'\n", encoding="utf-8")
    capsys.readouterr()

    assert _test(repo) == 0

    assert _records(repo) == []
    assert "NOT recorded" in capsys.readouterr().err


def test_a_fast_forward_merge_takes_the_validated_run(
        tmp_path: Path, fake, capsys):
    """The validator's bookkeeping commit sits between its run and the merge:
    only progress.md changed, so the run still stands for the tree."""
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0
    _in_review(repo)
    fake.calls.clear()
    capsys.readouterr()

    assert _merge(repo, 1) == 0

    assert fake.calls == []                  # no second suite run
    assert "reusing that run" in capsys.readouterr().out
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("3 (reused)", "0")
    assert aide.ledger_warnings(repo / "docs" / "aide") == []
    assert _status(repo, 1) == "complete"


def test_a_merge_over_a_moved_base_runs_the_suite(tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0
    _run(["git", "switch", "main"], repo)
    _work(repo, "elsewhere")
    _run(["git", "switch", "aide/001-bounds"], repo)
    fake.calls.clear()
    capsys.readouterr()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]
    assert "the base had moved" in capsys.readouterr().out
    (row,) = _rows(repo)
    assert row["Suite s"] == "3"


def test_a_run_from_before_a_code_change_is_not_taken(
        tmp_path: Path, fake, capsys):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0
    _work(repo, "c")                         # a fix after the recorded run
    fake.calls.clear()
    capsys.readouterr()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]
    assert "src/c.py" in capsys.readouterr().out
    assert _rows(repo)[0]["Suite s"] == "3"


def test_a_run_recorded_on_another_branch_is_not_taken(tmp_path: Path, fake):
    """Same tree, same command — but recorded before this claim existed."""
    repo = _init_repo(tmp_path / "repo", fails="")
    assert _test(repo) == 0                  # on main, before the claim
    _claim(repo)                             # no commits: the tip is main's
    fake.calls.clear()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]
    assert _rows(repo)[0]["Suite s"] == "3"


def test_an_aged_out_run_is_not_taken(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0
    (path,) = aide.suite_results_dir(repo).glob("*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    record["timestamp"] -= aide.SUITE_RESULT_MAX_AGE + 60
    path.write_text(json.dumps(record), encoding="utf-8")
    fake.calls.clear()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]


def test_a_red_validated_run_still_meets_the_base(tmp_path: Path, fake, capsys):
    """Taken, not trusted: its failures go to the base exactly as a run the
    merge made would, and are admitted only as a subset."""
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 1
    _in_review(repo)
    fake.calls.clear()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["(detached)"]   # the base run only
    (row,) = _rows(repo)
    assert (row["Suite s"], row["Inherited"]) == ("3 (reused)", "1")
    assert len(_open_defects(repo)) == 1


def test_a_red_validated_run_with_a_new_failure_is_refused(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo")
    _claim(repo)
    _work(repo, "b", extra_failure="tests/test_b.py::test_new")
    assert _test(repo) == 1
    fake.calls.clear()

    assert _merge(repo, 1) == 1

    assert [c[0] for c in fake.calls] == ["(detached)"]
    assert _status(repo, 1) != "complete"
    assert "aide/001-bounds" in _branches(repo)


def test_no_test_takes_no_recorded_run_either(tmp_path: Path, fake):
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0

    assert _merge(repo, 1, "--no-test") == 0

    assert _rows(repo)[0]["Suite s"] == ""


def test_a_reused_suite_cell_reads_and_nothing_else_does(tmp_path: Path):
    d = tmp_path / "docs"
    d.mkdir()
    base = ["001", "001", "1", "normal", "merged", "2", "1", "2", "2", "1",
            "0", "0", "2.8.0", "2026-09-25"]
    (d / "ledger.md").write_text(
        aide.ledger_row(base + ["41 (reused)", "0"]) + "\n"
        + aide.ledger_row(base + ["41 (maybe)", "0"]) + "\n"
        + aide.ledger_row(base[:5] + ["2 (reused)"] + base[6:] + ["", ""]) + "\n",
        encoding="utf-8")
    first, second = aide.ledger_warnings(d)
    assert "Suite s cell '41 (maybe)'" in first
    assert "ACs cell '2 (reused)'" in second


def test_a_run_recorded_in_another_checkout_is_not_taken(tmp_path: Path, fake):
    """The store is shared by every worktree; their untracked inputs are not."""
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)
    _work(repo, "b")
    assert _test(repo) == 0
    (path,) = aide.suite_results_dir(repo).glob("*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    record["checkout"] = str(tmp_path / "another-worktree")
    path.write_text(json.dumps(record), encoding="utf-8")
    fake.calls.clear()

    assert _merge(repo, 1) == 0

    assert [c[0] for c in fake.calls] == ["main"]


def test_a_run_whose_head_moved_is_not_recorded(tmp_path: Path, monkeypatch,
                                                capsys):
    """A commit landing mid-run leaves a result that is of neither commit."""
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)

    def run(repo_root, argv, identify):
        _work(Path(repo_root), "mid-run")
        return aide.SuiteRun(0, 1.0, ())

    monkeypatch.setattr(aide, "run_test_suite", run)
    capsys.readouterr()

    assert _test(repo) == 0

    assert _records(repo) == []
    assert "NOT recorded" in capsys.readouterr().err


def test_a_run_whose_tree_changed_is_not_recorded(tmp_path: Path, monkeypatch,
                                                  capsys):
    """A tracked file edited mid-run leaves a result that is of no commit."""
    repo = _init_repo(tmp_path / "repo", fails="")
    _claim(repo)

    def run(repo_root, argv, identify):
        (Path(repo_root) / "src" / "a.py").write_text("x = 2\n",
                                                      encoding="utf-8")
        return aide.SuiteRun(0, 1.0, ())

    monkeypatch.setattr(aide, "run_test_suite", run)
    capsys.readouterr()

    assert _test(repo) == 0

    assert _records(repo) == []
    assert "NOT recorded" in capsys.readouterr().err


def test_a_base_run_that_dirties_the_tree_is_not_recorded(tmp_path: Path,
                                                          monkeypatch):
    """The store's clean-tree rule is the store's, not `aide test`'s alone."""
    repo = _init_repo(tmp_path / "repo", fails="")

    def run(repo_root, argv, identify):
        (Path(repo_root) / "src" / "a.py").write_text("x = 2\n",
                                                      encoding="utf-8")
        return aide.SuiteRun(0, 1.0, ())

    monkeypatch.setattr(aide, "run_test_suite", run)

    _, tree = aide.recorded_suite_run(repo, ["pytest"], True,
                                      by=aide.SUITE_RECORDED_BY_MERGE)

    assert tree is None
    assert _records(repo) == []
