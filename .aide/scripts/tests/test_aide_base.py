"""Tests for the base-ref layer — what a claim branches off and merges back to.

``main_branch`` stays the default everywhere; these cover the two ways a branch
can legitimately have a different base (an explicit ``--base``, and the base a
claim recorded when it branched off a queue branch) and the verbs that read it.

Repositories are built under ``tmp_path`` in ``git.mode = "local"`` so nothing
pushes, fetches, or touches the real project.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_base", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"

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
- 📋 Bounds. *(Item 027)*
- 📋 Coverage. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""

QUEUE = """\
# Demo — Work Queue 003

### Item 027: Bounds rules
Bounds.

### Item 028: Coverage rules
Coverage.
"""

SPEC_027 = """\
# Item 027 — Bounds rules

## Authorised paths

**May change:**

- `src/demo/bounds.py` — the rule
"""


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], path)
    _run(["git", "config", "user.email", "t@example.com"], path)
    _run(["git", "config", "user.name", "Tester"], path)
    (path / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    d = path / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir(parents=True)
    (d / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(QUEUE, encoding="utf-8")
    (d / "items" / "027-bounds-rules.md").write_text(SPEC_027, encoding="utf-8")
    # A loop repo has an inbox (1.26.0 guarantees it), so `claim` creates
    # nothing here and a scope count below is the test's own diff.
    (d / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    (path / "src" / "demo").mkdir(parents=True)
    (path / "src" / "demo" / "bounds.py").write_text("x = 1\n", encoding="utf-8")
    _run(["git", "add", "-A"], path)
    _run(["git", "commit", "-m", "init"], path)
    return path


def _branches(path: Path) -> list:
    out = _run(["git", "branch", "--format=%(refname:short)"], path).stdout
    return [b.strip() for b in out.splitlines() if b.strip()]


def _commit(path: Path, rel: str, text: str, message: str) -> None:
    target = path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    _run(["git", "add", "-A"], path)
    _run(["git", "commit", "-m", message], path)


# --------------------------------------------------------------------------- #
# resolve_base
# --------------------------------------------------------------------------- #
def test_resolve_base_defaults_to_main_branch(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    cfg = aide.load_config(repo)
    assert aide.resolve_base(repo, cfg) == "main"


def test_resolve_base_prefers_the_recorded_base(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    cfg = aide.load_config(repo)
    aide._record_branch_base(repo, "main", "aide/queue-003")
    assert aide.resolve_base(repo, cfg, branch="main") == "aide/queue-003"


def test_resolve_base_explicit_wins_over_recorded(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    cfg = aide.load_config(repo)
    aide._record_branch_base(repo, "main", "aide/queue-003")
    assert aide.resolve_base(repo, cfg, "release/1.x", branch="main") == "release/1.x"


def test_recorded_base_is_absent_by_default(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide._recorded_branch_base(repo, "main") is None


# --------------------------------------------------------------------------- #
# claim records a base
# --------------------------------------------------------------------------- #
def test_claim_from_main_records_main(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    branch = "aide/027-bounds-rules"
    assert branch in _branches(repo)
    assert aide._recorded_branch_base(repo, branch) == "main"


def test_claim_from_a_queue_branch_records_that_branch(tmp_path: Path, capsys):
    """`switch -c` already branches from whatever is checked out, so claiming
    from a queue branch branched correctly all along — only the merge target
    was hard-wired. The base is inferred here so no caller must pass a flag."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    assert aide._recorded_branch_base(repo, "aide/027-bounds-rules") == "aide/queue-003"
    assert "base aide/queue-003" in capsys.readouterr().out


def test_claim_does_not_infer_a_base_from_an_arbitrary_branch(tmp_path: Path):
    """Only a *recognised* queue branch is inferred from. Inferring from any
    checked-out branch would silently retarget a merge."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "spike/whatever"], repo)
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    assert aide._recorded_branch_base(repo, "aide/027-bounds-rules") == "main"


def test_claim_explicit_base_overrides_the_inference(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--base", "main"]) == 0
    assert aide._recorded_branch_base(repo, "aide/027-bounds-rules") == "main"


def test_claim_dry_run_names_the_base_and_creates_nothing(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert "base aide/queue-003" in capsys.readouterr().out
    assert "aide/027-bounds-rules" not in _branches(repo)



def test_claim_from_a_claim_branch_takes_its_recorded_base(tmp_path: Path,
                                                           capsys):
    """Issue #433: a validator ending PASS (awaiting gate-…) leaves HEAD on the
    item's claim branch. The next claim from there takes the base that branch
    recorded — the queue branch — never `main_branch`, and branches FROM it,
    so the left item's work does not come along."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "027's work")
    capsys.readouterr()

    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert capsys.readouterr().out.startswith(
        "would claim item 028 -> aide/028-coverage-rules (Coverage rules); "
        "base aide/queue-003")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    assert aide._recorded_branch_base(repo, "aide/028-coverage-rules") == "aide/queue-003"
    assert (repo / "src" / "demo" / "bounds.py").read_text(encoding="utf-8") == "x = 1\n"


def test_claim_from_a_claim_branch_with_no_recorded_base_is_refused(
        tmp_path: Path, capsys):
    """Issue #433: `main_branch` is the guess that misroutes, so a claim
    branch whose base this checkout never recorded is refused — --dry-run
    too — and `--base` decides."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/027-bounds-rules"], repo)
    for extra in (["--dry-run"], []):
        assert aide.main(["--repo", str(repo), "claim", *extra]) == 1
        err = capsys.readouterr().err
        assert "no recorded base" in err and "--base" in err
    assert "aide/028-coverage-rules" not in _branches(repo)
    assert aide.main(["--repo", str(repo), "claim", "--base", "main"]) == 0
    assert aide._recorded_branch_base(repo, "aide/028-coverage-rules") == "main"

# --------------------------------------------------------------------------- #
# merge honours the base
# --------------------------------------------------------------------------- #
def test_merge_lands_on_the_recorded_base_not_main(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test"]) == 0
    assert _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "aide/queue-003"
    assert "x = 2" in (repo / "src" / "demo" / "bounds.py").read_text(encoding="utf-8")

    _run(["git", "switch", "main"], repo)
    assert "x = 1" in (repo / "src" / "demo" / "bounds.py").read_text(encoding="utf-8")


def test_merge_base_flag_overrides_the_recorded_base(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "merge", "27", "--base", "main",
                      "--no-test"]) == 0
    _run(["git", "switch", "main"], repo)
    assert "x = 2" in (repo / "src" / "demo" / "bounds.py").read_text(encoding="utf-8")


def test_merge_without_a_recorded_base_still_lands_on_main(tmp_path: Path):
    """main_branch is the default and is never removed as one."""
    repo = _init_repo(tmp_path / "repo")
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test"]) == 0
    assert _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo).stdout.strip() == "main"


def test_merge_reports_a_base_that_does_not_exist(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    rc = aide.main(["--repo", str(repo), "merge", "27", "--base", "no/such",
                    "--no-test"])
    assert rc == 1
    assert "no such local branch" in capsys.readouterr().err


def test_merge_refuses_a_base_that_is_not_a_local_branch(tmp_path: Path, capsys):
    """`git switch` on a tag/commit/remote-tracking ref detaches HEAD, and a
    merge into a detached HEAD updates no branch while still reporting success
    — then the claim branch is deleted and the work survives only as an
    unreferenced commit. Resolving is not enough; it must be a branch."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "tag", "v1"], repo)
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    rc = aide.main(["--repo", str(repo), "merge", "27", "--base", "v1",
                    "--no-test"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "detach" in err
    assert "aide/027-bounds-rules" in _branches(repo), "claim branch must survive"


def test_claim_branches_from_the_base_not_from_head(tmp_path: Path):
    """`switch -c` with no start point uses HEAD, which would let the branch's
    real starting point disagree with the base it records — claiming with
    `--base main` from a queue branch would start from the queue branch and
    then merge all of it into main."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    _commit(repo, "queue_only.py", "q = 1\n", "queue-branch-only work")

    assert aide.main(["--repo", str(repo), "claim", "--base", "main"]) == 0
    assert not (repo / "queue_only.py").exists(), (
        "claim recorded main as the base, so it must branch from main")


@pytest.mark.parametrize("base", ["v1", "origin/main"])
def test_claim_refuses_a_base_that_is_not_a_local_branch(tmp_path: Path, capsys,
                                                         base: str):
    """A tag and a remote-tracking ref alike: claim writes to its base (§4,
    issue #407), and only a local branch moves forward."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "tag", "v1"], repo)
    _run(["git", "update-ref", "refs/remotes/origin/main", "main"], repo)
    rc = aide.main(["--repo", str(repo), "claim", "--base", base])
    assert rc == 1
    assert "not a local branch" in capsys.readouterr().err
    assert "aide/027-bounds-rules" not in _branches(repo)


def test_scope_uses_an_explicit_base_verbatim(tmp_path: Path, capsys):
    """An explicit --base is the caller's word: substituting origin/ for it
    would make `--base main` mean something they did not write."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/027-bounds-rules"], repo)
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "scope", "--base", "main"]) == 0
    assert "vs main" in capsys.readouterr().out


@pytest.mark.parametrize("form", ["origin", "commit"])
def test_a_measuring_verb_takes_a_base_that_is_not_a_local_branch(
        tmp_path: Path, capsys, form: str):
    """§4, issue #407: scope and status only measure, so a remote-tracking ref
    or a raw commit is a base they take — the one a PR-context CI job on a
    detached checkout has to pass. Neither refuses it the way claim does."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "update-ref", "refs/remotes/origin/main", "main"], repo)
    base = ("origin/main" if form == "origin" else
            _run(["git", "rev-parse", "main"], repo).stdout.strip())
    _run(["git", "switch", "-c", "aide/027-bounds-rules"], repo)
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "scope", "--base", base]) == 0
    assert f"vs {base}" in capsys.readouterr().out
    _commit(repo, "stray.md", "x\n", "stray")
    assert aide.main(["--repo", str(repo), "scope", "--base", base]) == 1
    assert "stray.md" in capsys.readouterr().out

    assert aide.main(["--repo", str(repo), "status", "--no-fetch",
                      "--base", base]) == 0
    assert "not a local branch" not in capsys.readouterr().err


def test_a_derived_base_prefers_its_origin_counterpart(tmp_path: Path):
    """The other half of the sentence above it, and of `aide scope -h`.

    An explicit `--base` is the caller's word and is used verbatim; the two
    *derived* answers — the recorded base, and `main_branch` — are nobody's
    word, so they resolve to `origin/<base>` when that ref exists. The footgun
    is a local `main` sitting behind the work: the merge-base with it is it,
    and every file the earlier items touched is then reported against this
    item's spec.
    """
    repo = _init_repo(tmp_path / "repo")
    cfg = aide.load_config(repo)
    assert aide._scope_base_ref(repo, cfg, None) == "main"

    # A remote pointing at the repository itself: no network, and the
    # remote-tracking ref is what the preference actually looks for.
    _run(["git", "remote", "add", "origin", str(repo)], repo)
    _run(["git", "update-ref", "refs/remotes/origin/main", "main"], repo)
    assert aide._scope_base_ref(repo, cfg, None) == "origin/main"
    assert aide._scope_base_ref(repo, cfg, "main") == "main"

    # BOTH derived answers, not just `main_branch`: on stacked work the base
    # is the queue branch a claim recorded, and that is the answer the footgun
    # actually bites — a local queue branch behind its origin copy makes every
    # sibling item already merged into it read as this item's own change.
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    _run(["git", "switch", "-c", "aide/027-bounds-rules"], repo)
    aide._record_branch_base(repo, "aide/027-bounds-rules", "aide/queue-003")
    assert aide._scope_base_ref(repo, cfg, None) == "aide/queue-003"
    _run(["git", "update-ref", "refs/remotes/origin/aide/queue-003", "main"], repo)
    assert aide._scope_base_ref(repo, cfg, None) == "origin/aide/queue-003"
    assert aide._scope_base_ref(repo, cfg, "aide/queue-003") == "aide/queue-003"


# --------------------------------------------------------------------------- #
# the base reaches the other verbs
# --------------------------------------------------------------------------- #
def test_scope_diffs_against_the_recorded_base(tmp_path: Path, capsys):
    """An item claimed from a queue branch has diverged from *that*. Diffing
    against main would report every sibling item already merged into the queue
    as this item's own out-of-scope change."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    _commit(repo, "unrelated/sibling.py", "s = 1\n", "an earlier item, on the queue branch")
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "this item's own work")

    assert aide.main(["--repo", str(repo), "scope"]) == 0
    out = capsys.readouterr().out
    assert "aide/queue-003" in out and "1 changed file(s)" in out


def test_scope_without_a_recorded_base_uses_main(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/027-bounds-rules"], repo)
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")

    assert aide.main(["--repo", str(repo), "scope"]) == 0
    assert "vs main" in capsys.readouterr().out


def test_gc_merged_is_measured_against_the_base(tmp_path: Path, capsys):
    """A branch merged into the queue branch is not merged into main, so a
    main-only --merged finds nothing where the cleanup actually is."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/queue-003"], repo)
    aide.main(["--repo", str(repo), "claim"])
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")
    _run(["git", "switch", "aide/queue-003"], repo)
    _run(["git", "merge", "--no-edit", "aide/027-bounds-rules"], repo)

    assert aide.main(["--repo", str(repo), "gc", "--merged"]) == 0
    assert "aide/027-bounds-rules" in capsys.readouterr().out

    assert aide.main(["--repo", str(repo), "gc", "--merged", "--base", "main"]) == 0
    assert "aide/027-bounds-rules" not in capsys.readouterr().out


def _queue_stack(repo: Path) -> None:
    """main -> aide/queue-001 -> aide/queue-002, each with a commit of its own,
    and main checked out: queue 001 is an ancestor of queue 002 and not of main."""
    _run(["git", "switch", "-c", "aide/queue-001"], repo)
    _commit(repo, "q1.txt", "1\n", "queue 1 work")
    _run(["git", "switch", "-c", "aide/queue-002"], repo)
    _commit(repo, "q2.txt", "2\n", "queue 2 work")
    _run(["git", "switch", "main"], repo)


def _local_branches(repo: Path) -> list:
    out = subprocess.run(["git", "branch", "--format=%(refname:short)"], cwd=repo,
                         capture_output=True, text=True, check=True).stdout
    return out.split()


def test_gc_merged_keeps_a_queue_branch_below_a_queue_base(tmp_path: Path, capsys):
    """Issue #403: under a queue base, the queue branch below it on the stack
    is merged into its successor, not into main, and its PR is its route
    there — skipped and said so, and neither it nor the base is deleted. A
    claim merged into that base is still collected."""
    repo = _init_repo(tmp_path / "repo")
    _queue_stack(repo)
    _run(["git", "switch", "-c", "aide/027-bounds-rules", "aide/queue-002"], repo)
    _commit(repo, "src/demo/bounds.py", "x = 2\n", "work")
    _run(["git", "switch", "aide/queue-002"], repo)
    _run(["git", "merge", "--no-edit", "aide/027-bounds-rules"], repo)
    _run(["git", "switch", "main"], repo)

    assert aide.main(["--repo", str(repo), "gc", "--merged",
                      "--base", "aide/queue-002"]) == 0
    out = capsys.readouterr().out
    assert "skipping aide/queue-001 (local)" in out
    assert "would delete aide/queue-001" not in out
    assert "aide/queue-002 (" not in out
    assert "would delete aide/027-bounds-rules" in out

    assert aide.main(["--repo", str(repo), "gc", "--merged", "--yes",
                      "--base", "aide/queue-002"]) == 0
    branches = _local_branches(repo)
    assert "aide/queue-001" in branches and "aide/queue-002" in branches
    assert "aide/027-bounds-rules" not in branches


def test_gc_merged_takes_a_queue_branch_merged_into_main(tmp_path: Path, capsys):
    """The main-base ground is unchanged: once main holds queue 001, it goes."""
    repo = _init_repo(tmp_path / "repo")
    _queue_stack(repo)
    _run(["git", "merge", "--ff-only", "aide/queue-001"], repo)

    assert aide.main(["--repo", str(repo), "gc", "--merged", "--yes",
                      "--base", "main"]) == 0
    branches = _local_branches(repo)
    assert "aide/queue-001" not in branches
    assert "aide/queue-002" in branches


@pytest.mark.parametrize("base_form", ["origin", "sha"])
def test_gc_merged_queue_base_by_another_name(tmp_path: Path, capsys,
                                              base_form):
    """The queue base given as its remote-tracking ref or as a raw commit:
    the queue and specs-queue branches below it are still skipped, and the
    base named as ``origin/<branch>`` is still the base — neither a target
    nor a skip line."""
    repo = _init_repo(tmp_path / "repo")
    _run(["git", "switch", "-c", "aide/specs-queue-001"], repo)
    _commit(repo, "s1.txt", "s\n", "specs work")
    _queue_stack(repo)
    _run(["git", "update-ref", "refs/remotes/origin/aide/queue-002",
          "aide/queue-002"], repo)
    base = ("origin/aide/queue-002" if base_form == "origin" else
            _run(["git", "rev-parse", "aide/queue-002"], repo).stdout.strip())

    assert aide.main(["--repo", str(repo), "gc", "--merged", "--yes",
                      "--base", base]) == 0
    out = capsys.readouterr().out
    assert "skipping aide/queue-001 (local)" in out
    assert "skipping aide/specs-queue-001 (local)" in out
    if base_form == "origin":
        assert "aide/queue-002 (" not in out
    branches = _local_branches(repo)
    assert {"aide/specs-queue-001", "aide/queue-001",
            "aide/queue-002"} <= set(branches)


def test_gc_merged_takes_a_queue_branch_under_origin_main(tmp_path: Path,
                                                         capsys):
    """``origin/<main_branch>`` is main_branch for the queue rule."""
    repo = _init_repo(tmp_path / "repo")
    _queue_stack(repo)
    _run(["git", "merge", "--ff-only", "aide/queue-001"], repo)
    _run(["git", "update-ref", "refs/remotes/origin/main", "main"], repo)

    assert aide.main(["--repo", str(repo), "gc", "--merged", "--yes",
                      "--base", "origin/main"]) == 0
    branches = _local_branches(repo)
    assert "aide/queue-001" not in branches
    assert "aide/queue-002" in branches


def test_status_accepts_a_base_and_still_reports(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "status", "--base", "main",
                      "--no-fetch"]) == 0
    assert "aide status" in capsys.readouterr().out
