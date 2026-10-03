"""Tests for `aide queue start`'s cap and stack shape, and `aide queue gate`
(issue #302) — see aide.py `_queue_start`, `_unmerged_queue_branches`,
`_stack_top_refusal` and `_queue_gate`.

Throwaway repositories under ``tmp_path``; a bare repository stands in for
``origin`` where a branch only origin has is under test. Stacks are built the
way the loop builds them, with `aide queue start`, so every base and start
record is one a real run leaves.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_queue_stack", _MODULE_PATH)
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
{loop}
"""

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | One | G1 | 📋 |
| 2 | Two | G1 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1, Stage 2 | 📋 |

## Human gates

| Gate | Blocks | Status | Decision / evidence |
|------|--------|--------|---------------------|
| Budget signed off | stage 2 | ⏳ Awaiting | — |

## Stage 1 — One — 📋

**Deliverables.**
- 📋 Alpha. *(Item 001)*
- 📋 Beta. *(Item 002)*
- 📋 Gamma. *(Item 003)*

## Stage 2 — Two — 📋

**Deliverables.**
- 📋 Delta. *(Item 004)*
"""

#: queue number -> its items: queue 1 opens stage 1, queue 2 finishes it,
#: queue 3 opens stage 2.
QUEUES = {1: (1, 2), 2: (3,), 3: (4,)}


def _git(args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _queue_text(number: int, items) -> str:
    body = "".join(f"\n### Item {n:03d}: Item {n}\nWork.\n" for n in items)
    return f"# Demo — Work Queue {number:03d}\n{body}"


def _init(path: Path, loop: str = "", mode: str = "local",
          queues=(1, 2, 3)) -> Path:
    path.mkdir(parents=True)
    _git(["init", "-b", "main"], path)
    _git(["config", "user.email", "t@example.com"], path)
    _git(["config", "user.name", "Tester"], path)
    (path / "aide.toml").write_text(AIDE_TOML.format(mode=mode, loop=loop),
                                    encoding="utf-8")
    ddir = path / "docs" / "aide"
    (ddir / "queue").mkdir(parents=True)
    (ddir / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (ddir / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    for n in queues:
        (ddir / "queue" / f"queue-{n:03d}.md").write_text(
            _queue_text(n, QUEUES[n]), encoding="utf-8")
    _git(["add", "-A"], path)
    _git(["commit", "-m", "init"], path)
    return path


def _start(repo: Path, number: int, *extra: str) -> int:
    return aide.main(["--repo", str(repo), "queue", "start", str(number), *extra])


def _gate(repo: Path, number: int, *extra: str) -> int:
    return aide.main(["--repo", str(repo), "queue", "gate", str(number), *extra])


def _work(repo: Path, name: str) -> None:
    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    _git(["add", "-A"], repo)
    _git(["commit", "-m", f"work {name}"], repo)


def _branches(repo: Path) -> set:
    out = _git(["branch", "--format=%(refname:short)"], repo).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def _base(repo: Path, branch: str) -> str:
    return _git(["config", "--get", f"branch.{branch}.aide-base"], repo,
                check=False).stdout.strip()


def _progress(repo: Path) -> str:
    return (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")


def _head(repo: Path) -> str:
    return _git(["rev-parse", "HEAD"], repo).stdout.strip()


def _clean(repo: Path) -> bool:
    return _git(["status", "--porcelain"], repo).stdout.strip() == ""


# --------------------------------------------------------------------------- #
# [loop] max_open_queues — enforced by `queue start`
# --------------------------------------------------------------------------- #
def test_the_default_cap_refuses_a_second_queue_while_the_first_is_unmerged(
        tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    assert _start(repo, 2, "--base", Q1) == 3
    assert Q2 not in _branches(repo)
    err = capsys.readouterr().err
    assert Q1 in err and "max_open_queues" in err


def test_the_cap_is_checked_by_a_dry_run_too(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    assert _start(repo, 2, "--base", Q1, "--dry-run") == 3
    assert Q2 not in _branches(repo)


def test_below_the_cap_a_queue_stacks_on_the_top_and_records_it(tmp_path: Path):
    repo = _init(tmp_path / "r", loop="max_open_queues = 2")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    assert _start(repo, 2, "--base", Q1) == 0
    assert _base(repo, Q2) == Q1
    # Two unmerged now: the third is the cap's.
    assert _start(repo, 3, "--base", Q2) == 3


@pytest.mark.parametrize("how", ["squash", "merge-commit", "fast-forward"])
def test_a_queue_whose_work_landed_no_longer_counts(tmp_path: Path, how: str):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    _git(["switch", "main"], repo)
    if how == "squash":
        _git(["merge", "--squash", Q1], repo)
        _git(["commit", "-m", "squash q1"], repo)
    elif how == "merge-commit":
        _git(["merge", "--no-ff", "--no-edit", Q1], repo)
    else:
        _git(["merge", "--ff-only", Q1], repo)
    assert _start(repo, 2) == 0
    assert _base(repo, Q2) == "main"


def test_a_queue_git_cannot_judge_counts_as_unmerged(tmp_path: Path):
    """No start recorded, and the tip on main's first-parent history: a
    fast-forward landing and a queue with no commits yet look alike, so it is
    counted rather than guessed landed."""
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    _git(["config", "--unset", f"branch.{Q1}.aide-start"], repo)
    _git(["switch", "main"], repo)
    assert _start(repo, 2) == 3


def test_a_queue_only_origin_has_counts_as_unmerged(tmp_path: Path):
    """Another checkout started queue 1 and pushed it; this one has only
    fetched it."""
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    repo = _init(tmp_path / "r", mode="pr")
    _git(["remote", "add", "origin", str(origin)], repo)
    _git(["push", "-u", "origin", "main"], repo)
    other = tmp_path / "other"
    _git(["clone", str(origin), str(other)], tmp_path)
    _git(["config", "user.email", "o@example.com"], other)
    _git(["config", "user.name", "Other"], other)
    assert _start(other, 1) == 0
    _work(other, "q1.txt")
    _git(["push"], other)
    _git(["fetch", "origin"], repo)

    assert Q1 not in _branches(repo)
    assert _start(repo, 2) == 3


def test_a_specs_queue_branch_is_neither_counted_nor_capped(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1, "--specs") == 0
    _work(repo, "specs.txt")
    _git(["switch", "main"], repo)
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    _git(["switch", "main"], repo)
    assert _start(repo, 2, "--specs") == 0


def test_a_base_beside_the_stack_is_refused(tmp_path: Path, capsys):
    repo = _init(tmp_path / "r", loop="max_open_queues = 3")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    _git(["switch", "main"], repo)
    assert _start(repo, 2) == 1
    assert Q2 not in _branches(repo)
    assert f"--base {Q1}" in capsys.readouterr().err


def test_a_base_that_would_fork_the_stack_is_refused(tmp_path: Path):
    repo = _init(tmp_path / "r", loop="max_open_queues = 3")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    assert _start(repo, 2, "--base", Q1) == 0
    _work(repo, "q2.txt")
    assert _start(repo, 3, "--base", Q1) == 1
    assert Q3 not in _branches(repo)
    assert _start(repo, 3, "--base", Q2) == 0
    assert _base(repo, Q3) == Q2


@pytest.mark.parametrize("value", ["0", "-1", "true", "1.5", '"2"'])
def test_an_unusable_cap_refuses_the_start_and_fails_the_check(
        tmp_path: Path, value: str):
    repo = _init(tmp_path / "r", loop=f"max_open_queues = {value}")
    assert _start(repo, 1) == 1
    assert Q1 not in _branches(repo)
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert any("max_open_queues" in e for e in errors)


def test_the_check_accepts_both_keys_at_their_documented_values(tmp_path: Path):
    for n, value in enumerate(aide.PLAN_REVIEW_VALUES):
        repo = _init(tmp_path / f"r{n}",
                     loop=f'max_open_queues = 2\nplan_review = "{value}"')
        errors, _ = aide.run_checks(repo, aide.load_config(repo))
        assert not any("[loop]" in e for e in errors), errors


@pytest.mark.parametrize("mode", ["Local", "auto_merge", "offline", ""])
def test_a_git_mode_outside_the_three_fails_the_check(tmp_path: Path, mode: str):
    """Issue #352: every site compares against one of the three, so any other
    string ran as `auto-merge` — `"Local"` pushed from a checkout meant to be
    offline."""
    repo = _init(tmp_path / "r", mode=mode)
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert [e for e in errors if "[git] mode" in e] == [
        f"aide.toml [git] mode = {mode!r} is not one of 'auto-merge', 'pr', "
        f"'local' — any other value runs as 'auto-merge' (default "
        f"'auto-merge')"]


def test_the_check_accepts_the_three_git_modes(tmp_path: Path):
    for mode in aide.GIT_MODE_VALUES:
        repo = _init(tmp_path / mode, mode=mode)
        errors, _ = aide.run_checks(repo, aide.load_config(repo))
        assert not any("[git] mode" in e for e in errors), errors


# --------------------------------------------------------------------------- #
# [git] forge and [git] ci — declared, never inferred (issue #355)
# --------------------------------------------------------------------------- #
def _git_keys(repo: Path, keys: str) -> List[str]:
    """`aide check`'s errors naming ``[git]`` after *keys* join that table."""
    path = repo / "aide.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        'branch_prefix = "aide/"\n', f'branch_prefix = "aide/"\n{keys}\n'),
        encoding="utf-8")
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    return [e for e in errors if "[git]" in e]


def test_pr_mode_with_no_forge_fails_the_check(tmp_path: Path):
    """Under `pr` a person opens each item's PR on the forge, so the
    combination has no meaning."""
    repo = _init(tmp_path / "r", mode="pr")
    (error,) = _git_keys(repo, 'forge = "none"')
    assert error.startswith('aide.toml [git] mode = "pr" with forge = "none"')


def test_ci_on_a_pr_with_no_forge_fails_the_check(tmp_path: Path):
    repo = _init(tmp_path / "r", mode="auto-merge")
    (error,) = _git_keys(repo, 'forge = "none"\nci = "pr"')
    assert error.startswith('aide.toml [git] ci = "pr" with forge = "none"')


@pytest.mark.parametrize("keys, named", [
    ('forge = "gitlab"', "[git] forge = 'gitlab' is not one of 'github', 'none'"),
    ('forge = "GitHub"', "[git] forge = 'GitHub' is not one of"),
    ('ci = "push"', "[git] ci = 'push' is not one of 'pr', 'none'"),
    ('ci = ""', "[git] ci = '' is not one of"),
])
def test_a_forge_or_ci_outside_its_values_fails_the_check(
        tmp_path: Path, keys: str, named: str):
    repo = _init(tmp_path / "r", mode="auto-merge")
    (error,) = _git_keys(repo, keys)
    assert named in error


@pytest.mark.parametrize("mode, keys", [
    ("auto-merge", 'forge = "none"'),
    ("auto-merge", 'forge = "none"\nci = "none"'),
    ("local", 'forge = "none"'),
    ("pr", 'forge = "github"\nci = "none"'),
    ("auto-merge", 'forge = "github"\nci = "pr"'),
    ("pr", ""),
])
def test_the_check_accepts_every_meaningful_combination(
        tmp_path: Path, mode: str, keys: str):
    repo = _init(tmp_path / "r", mode=mode)
    assert _git_keys(repo, keys) == []


@pytest.mark.parametrize("git_table, forge, ci", [
    ({}, "github", "pr"),
    ({"forge": "none"}, "none", "none"),
    ({"forge": "none", "ci": "pr"}, "none", "none"),
    ({"ci": "none"}, "github", "none"),
    ({"forge": "gitlab", "ci": "push"}, "github", "pr"),
])
def test_ci_defaults_follow_the_forge(git_table, forge: str, ci: str):
    config = {"git": git_table}
    assert (aide.declared_forge(config), aide.declared_ci(config)) == (forge, ci)


# --------------------------------------------------------------------------- #
# [loop] plan_review — the gate `queue gate` raises
# --------------------------------------------------------------------------- #
def test_queue_raises_one_gate_over_the_queue_s_items_and_commits_it(
        tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    before = _head(repo)
    assert _gate(repo, 1) == 0
    text = _progress(repo)
    assert ("| Queue 001 plan reviewed before build | 001–002 | ⏳ Awaiting | — |"
            in text)
    gates = aide.human_gates(text.splitlines())
    gate = next(g for g in gates if g.text.startswith("Queue 001"))
    assert gate.blocks == [1, 2] and gate.kind == "awaiting"
    assert _head(repo) != before and _clean(repo)
    gid = aide.gate_ids(gates)[gates.index(gate)]
    assert gid in capsys.readouterr().out


def test_queue_through_raises_one_gate_over_both_queues(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert _gate(repo, 1, "--through", "2") == 0
    gate = next(g for g in aide.human_gates(_progress(repo).splitlines())
                if g.text == "Queues 001–002 plan reviewed before build")
    assert gate.blocks == [1, 2, 3]


def test_stage_raises_a_stage_gate_only_for_a_queue_that_opens_one(
        tmp_path: Path):
    repo = _init(tmp_path / "r", loop='plan_review = "stage"')
    assert _gate(repo, 1) == 0
    gate = next(g for g in aide.human_gates(_progress(repo).splitlines())
                if g.text == "Stage 1 plan reviewed before build")
    assert gate.stage == "1" and gate.kind == "awaiting"

    # Queue 2 is the rest of stage 1, which queue 1 already opened.
    head = _head(repo)
    text = _progress(repo)
    assert _gate(repo, 2) == 0
    assert _progress(repo) == text and _head(repo) == head

    # Queue 3 opens stage 2; the roadmap's own stage 2 gate is left alone.
    assert _gate(repo, 3) == 0
    gates = aide.human_gates(_progress(repo).splitlines())
    assert [g.text for g in gates if g.stage == "2"] == [
        "Budget signed off", "Stage 2 plan reviewed before build"]
    assert "| Budget signed off | stage 2 | ⏳ Awaiting | — |" in _progress(repo)


def test_none_raises_nothing_and_exits_zero(tmp_path: Path):
    repo = _init(tmp_path / "r", loop='plan_review = "none"')
    head, text = _head(repo), _progress(repo)
    assert _gate(repo, 1) == 0
    assert _progress(repo) == text and _head(repo) == head


@pytest.mark.parametrize("setting", ["queue", "stage"])
def test_a_second_run_raises_nothing_new(tmp_path: Path, setting: str):
    repo = _init(tmp_path / "r", loop=f'plan_review = "{setting}"')
    assert _gate(repo, 1) == 0
    head, text = _head(repo), _progress(repo)
    assert _gate(repo, 1) == 0
    assert _progress(repo) == text and _head(repo) == head


def test_an_approved_gate_is_not_raised_again(tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert _gate(repo, 1) == 0
    gates = aide.human_gates(_progress(repo).splitlines())
    gid = aide.gate_ids(gates)[-1]
    assert aide.main(["--repo", str(repo), "gate", "approve", gid]) == 0
    text = _progress(repo)
    assert _gate(repo, 1) == 0
    assert _progress(repo) == text


def test_a_progress_file_with_no_gates_section_gets_one(tmp_path: Path):
    repo = _init(tmp_path / "r")
    path = repo / "docs" / "aide" / "progress.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("## Human gates")
    path.write_text(text[:start] + text[text.index("## Stage 1 —"):],
                    encoding="utf-8")
    _git(["commit", "-am", "no gates section"], repo)
    assert _gate(repo, 1, "--no-commit") == 0
    gates = aide.human_gates(_progress(repo).splitlines())
    assert [g.text for g in gates] == ["Queue 001 plan reviewed before build"]
    assert not aide.unreadable_gate_rows(_progress(repo).splitlines())
    assert not _clean(repo)  # --no-commit


@pytest.mark.parametrize("argv,code", [
    (["queue", "gate", "9"], 1),                         # no such queue file
    (["queue", "gate", "1", "--through", "9"], 1),       # the range reaches one
    (["queue", "gate", "2", "--through", "1"], 2),       # a backwards range
    (["queue", "gate"], 2),                              # no number
])
def test_gate_refusals_and_usage(tmp_path: Path, argv, code):
    repo = _init(tmp_path / "r")
    text = _progress(repo)
    assert aide.main(["--repo", str(repo), *argv]) == code
    assert _progress(repo) == text


def test_a_queue_listing_no_items_is_refused(tmp_path: Path):
    repo = _init(tmp_path / "r")
    (repo / "docs" / "aide" / "queue" / "queue-004.md").write_text(
        "# Demo — Work Queue 004\n", encoding="utf-8")
    assert _gate(repo, 4, "--no-commit") == 1


def test_an_unusable_plan_review_refuses_and_fails_the_check(tmp_path: Path):
    repo = _init(tmp_path / "r", loop='plan_review = "sometimes"')
    text = _progress(repo)
    assert _gate(repo, 1) == 1
    assert _progress(repo) == text
    errors, _ = aide.run_checks(repo, aide.load_config(repo))
    assert any("plan_review" in e for e in errors)


def test_item_ranges_read_back_as_the_numbers_written():
    for nums in ([5], [5, 6], [5, 7, 8, 9], list(range(1, 120)), [3, 1, 2, 2]):
        cell = aide.item_ranges(nums)
        assert sorted(aide._blocked_item_numbers(cell)) == sorted(set(nums)), cell


# --------------------------------------------------------------------------- #
# review round 1 (PR #308) — the printed remedies clear the refusal, and
# every clause of the pinned exits has a guard
# --------------------------------------------------------------------------- #
def test_a_pr_merged_on_origin_clears_once_main_is_updated_from_origin(
        tmp_path: Path, capsys):
    """The refusal names the remedy that works: `restack` has no stack to read
    here and leaves main where it is, so only updating main clears it."""
    origin = tmp_path / "origin.git"
    _git(["init", "--bare", "-b", "main", str(origin)], tmp_path)
    repo = _init(tmp_path / "r", mode="pr")
    _git(["remote", "add", "origin", str(origin)], repo)
    _git(["push", "-u", "origin", "main"], repo)
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    _git(["push"], repo)
    human = tmp_path / "human"
    _git(["clone", str(origin), str(human)], tmp_path)
    _git(["config", "user.email", "h@example.com"], human)
    _git(["config", "user.name", "Human"], human)
    _git(["merge", "--squash", f"origin/{Q1}"], human)
    _git(["commit", "-m", "squash queue 1"], human)
    _git(["push", "origin", "main"], human)

    assert _start(repo, 2, "--dry-run") == 3
    err = capsys.readouterr().err
    assert "git pull" in err and "aide queue restack')" not in err
    _git(["switch", "main"], repo)
    _git(["pull"], repo)
    assert _start(repo, 2, "--dry-run") == 0


def test_a_landed_branch_git_cannot_judge_clears_once_gc_deletes_it(
        tmp_path: Path, capsys):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    _git(["config", "--unset", f"branch.{Q1}.aide-start"], repo)
    _git(["switch", "main"], repo)
    _git(["merge", "--ff-only", Q1], repo)
    assert _start(repo, 2, "--dry-run") == 3
    assert "aide gc --merged --yes" in capsys.readouterr().err
    assert aide.main(["--repo", str(repo), "gc", "--merged", "--yes"]) == 0
    assert Q1 not in _branches(repo)
    assert _start(repo, 2) == 0


def test_an_open_branch_git_cannot_judge_is_read_once_its_start_is_recorded(
        tmp_path: Path):
    repo = _init(tmp_path / "r")
    assert _start(repo, 1) == 0
    _git(["config", "--unset", f"branch.{Q1}.aide-start"], repo)
    _git(["switch", "main"], repo)
    config = aide.load_config(repo)
    assert aide._unmerged_queue_branches(repo, config) == {Q1: None}
    assert aide.main(["--repo", str(repo), "queue", "restack", "1",
                      "--base", "main"]) == 0
    assert aide._unmerged_queue_branches(repo, config) == {Q1: False}


@pytest.mark.parametrize("shape", ["beside", "fork"])
def test_a_dry_run_refuses_a_bad_stack_shape_and_creates_nothing(
        tmp_path: Path, shape: str):
    repo = _init(tmp_path / "r", loop="max_open_queues = 3")
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    assert _start(repo, 2, "--base", Q1) == 0
    _work(repo, "q2.txt")
    before = _branches(repo)
    extra = [] if shape == "beside" else ["--base", Q1]
    if shape == "beside":
        _git(["switch", "main"], repo)
    assert _start(repo, 3, *extra, "--dry-run") == 1
    assert _branches(repo) == before and Q3 not in before
    assert _base(repo, Q3) == ""


def test_gate_without_a_progress_file_is_refused(tmp_path: Path):
    repo = _init(tmp_path / "r")
    (repo / "docs" / "aide" / "progress.md").unlink()
    head = _head(repo)
    assert _gate(repo, 1) == 1
    assert not (repo / "docs" / "aide" / "progress.md").exists()
    assert _head(repo) == head


def test_gate_whose_commit_fails_changes_nothing_and_a_retry_commits(
        tmp_path: Path):
    """A held index lock is a commit failure on every platform — no hook,
    no executable bit, no shell. The failed run leaves progress.md exactly
    as it was (bytes, so CRLF would show), and the re-run after the lock is
    released raises and commits the gate rather than calling it raised."""
    repo = _init(tmp_path / "r")
    path = repo / "docs" / "aide" / "progress.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    # Repo-local, so a runner's global autocrlf cannot rewrite either side.
    _git(["config", "core.autocrlf", "false"], repo)
    _git(["commit", "-am", "crlf"], repo)
    before, head = path.read_bytes(), _head(repo)
    lock = repo / ".git" / "index.lock"
    lock.write_bytes(b"")
    try:
        assert _gate(repo, 1) == 1
        assert path.read_bytes() == before
        assert _head(repo) == head
    finally:
        lock.unlink()
    assert _clean(repo)

    assert _gate(repo, 1) == 0
    assert _head(repo) != head and _clean(repo)
    committed = _git(["show", "HEAD:docs/aide/progress.md"], repo).stdout
    assert "Queue 001 plan reviewed before build" in committed


def test_the_cap_refusal_in_local_mode_names_a_local_merge_and_it_clears(
        tmp_path: Path, capsys):
    """No origin, no PR: a queue lands when a person merges it into
    main_branch here, and `git pull` would fail for want of an upstream."""
    repo = _init(tmp_path / "r")          # mode = "local", no remote
    assert _start(repo, 1) == 0
    _work(repo, "q1.txt")
    assert _start(repo, 2, "--dry-run") == 3
    err = capsys.readouterr().err
    assert "git merge" in err and "git pull" not in err
    _git(["switch", "main"], repo)
    _git(["merge", "--no-ff", "--no-edit", Q1], repo)
    assert _start(repo, 2, "--dry-run") == 0
