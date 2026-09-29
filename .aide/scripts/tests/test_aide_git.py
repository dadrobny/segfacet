"""Tests for the aide CLI git layer (claim, merge, env) — see aide.py.

The git-touching tests build throwaway repositories under ``tmp_path`` (a bare
repo stands in for ``origin`` where a remote is needed), so nothing touches the
real project or network.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_git", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"

[python]
venv = ".venv"
import_check = "demo_pkg"

[git]
mode = "{mode}"
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
- ✅ Core. *(Item 026)*
- 📋 Bounds. *(Item 027)*
- 📋 Coverage. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""

QUEUE = """\
# Demo — Work Queue 003

> **Status:** Live · **Created:** 2026-07-01

### Item 026: Rule engine core
Core.

### Item 027: Bounds rules
Bounds.

### Item 028: Coverage rules
Coverage.
"""


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _show_utf8(cwd: Path, rev_path: str) -> str:
    """`git show <rev>:<path>`, decoded as UTF-8 **strictly**.

    The documents this project reads are UTF-8 by definition (conventions.md
    §1), so anything reading one out of git says so rather than inheriting the
    platform's guess. Left decoding from bytes even though `_run` now names the
    codec itself: this one wants the *strict* decoder, so a byte that is not
    UTF-8 raises here instead of arriving as a replacement character that no
    status icon matches. That is the recorded §6 shape — the locale codec
    mangled the icons into characters `_parse_item_status` could not match,
    green on Linux and red only on the platform no local run sees.
    """
    out = subprocess.run(["git", "show", rev_path], cwd=str(cwd), check=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    return out.decode("utf-8")


def _init_repo(path: Path, mode: str = "local") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], path)
    _run(["git", "config", "user.email", "t@example.com"], path)
    _run(["git", "config", "user.name", "Tester"], path)
    (path / "aide.toml").write_text(AIDE_TOML.format(mode=mode), encoding="utf-8")
    d = path / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir(parents=True)
    (d / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(QUEUE, encoding="utf-8")
    _run(["git", "add", "-A"], path)
    _run(["git", "commit", "-m", "init"], path)
    return path


def _current_branch(path: Path) -> str:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path).stdout.strip()


# --------------------------------------------------------------------------- #
# pure helpers
# --------------------------------------------------------------------------- #
def test_slug():
    assert aide._slug("Level-aware min/max bounds rules (volume)") == "level-aware-min-max-bounds"
    assert aide._slug("") == "item"


def test_queue_titles():
    titles = aide._queue_titles(QUEUE)
    assert titles[27] == "Bounds rules"


def test_venv_python_path(tmp_path: Path):
    cfg = aide.DEFAULT_CONFIG
    p = aide.venv_python(tmp_path, cfg)
    if os.name == "nt":
        assert p.name == "python.exe" and p.parent.name == "Scripts"
    else:
        assert p.name == "python" and p.parent.name == "bin"


def test_env_status_missing(tmp_path: Path):
    (tmp_path / "aide.toml").write_text(AIDE_TOML.format(mode="local"), encoding="utf-8")
    cfg = aide.load_config(tmp_path)
    assert aide.env_status(tmp_path, cfg) == "missing"


def test_env_profile_satisfied_and_not(tmp_path: Path, capsys):
    (tmp_path / "aide.toml").write_text(
        AIDE_TOML.format(mode="local")
        + '\n[validation]\nyes = "1 + 1 == 2"\nno = "False"\n',
        encoding="utf-8",
    )
    assert aide.main(["--repo", str(tmp_path), "env", "--profile", "yes"]) == 0
    assert aide.main(["--repo", str(tmp_path), "env", "--profile", "no"]) == 1
    assert aide.main(["--repo", str(tmp_path), "env", "--profile", "nope"]) == 2
    err = capsys.readouterr().err
    assert "unknown profile 'nope'" in err


def test_pick_item_skips_done_and_claimed(tmp_path: Path):
    root = _init_repo(tmp_path / "r")
    cfg = aide.load_config(root)
    # 026 is done -> skip; 027 claimed -> skip; expect 028.
    pick = aide._pick_item(root, cfg, QUEUE, claim_branches=["aide/027-bounds"])
    assert pick is not None and pick[0] == 28


def test_pick_item_respects_dependency(tmp_path: Path):
    root = _init_repo(tmp_path / "r")
    # Give item 027 a spec that depends on 028 (still planned) -> 027 blocked, pick 028.
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\n- Item 028 provides X.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    pick = aide._pick_item(root, cfg, QUEUE, claim_branches=[])
    assert pick is not None and pick[0] == 28


def test_item_dependencies_expands_every_number_in_a_multi_item_list(tmp_path: Path):
    # Regression: a naive first-number-only regex left every item after the
    # first in "Items 026, 027, 028" unrecognised as a blocker.
    # _item_dependencies itself is status-agnostic — it reports every number
    # the section names; _pick_item is what discards already-✅ dependencies
    # (see test_pick_item_not_blocked_once_every_multi_item_dependency_is_done
    # below for that half of the behaviour).
    root = _init_repo(tmp_path / "r")
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\n"
        "- Items 026, 028 — both must land first.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    assert aide._item_dependencies(root, cfg, 27) == [26, 28]


def test_pick_item_not_blocked_once_every_multi_item_dependency_is_done(tmp_path: Path):
    # The practical regression: with 026 already ✅ (per PROGRESS) and 027
    # depending on "Items 026, 028", 027 must stay blocked while 028 is still
    # planned — a naive first-number-only parse would have reported 027 as
    # unblocked (it only ever saw 026, which is done) the moment 026 landed.
    root = _init_repo(tmp_path / "r")
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\n"
        "- Items 026, 028 — both must land first.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    pick = aide._pick_item(root, cfg, QUEUE, claim_branches=[])
    assert pick is not None and pick[0] == 28  # 027 is still blocked by open 028


def test_pick_item_waits_only_for_a_dependency_that_still_blocks(tmp_path: Path):
    """The parenthetical in `aide claim -h`: \u2705, \u274c or \u23f8\ufe0f have all left the way.

    `_pick_item` asks whether any dependency is in `BLOCKING_STATUSES`
    (planned, in-progress, in-review), so the three terminal-or-dormant icons
    are the complement of that set rather than a list kept in step with it by
    hand. \u23f8\ufe0f is the one worth exercising: it is not spent, and it still does
    not hold a dependent back \u2014 skipping the deferred item while blocking
    everything behind it is how a queue stops producing work.
    """
    root = _init_repo(tmp_path / "r")
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 \u2014 Bounds\n\n## Dependencies\n- Item 028 provides X.\n\n## End\n",
        encoding="utf-8")
    cfg = aide.load_config(root)
    ppath = root / "docs" / "aide" / "progress.md"

    ppath.write_text(PROGRESS, encoding="utf-8")
    assert aide._pick_item(root, cfg, QUEUE, claim_branches=[])[0] == 28

    for icon in ("\u2705", "\u274c", "\u23f8\ufe0f"):
        ppath.write_text(
            PROGRESS.replace("- \U0001f4cb Coverage. *(Item 028)*",
                             f"- {icon} Coverage. *(Item 028)*"),
            encoding="utf-8")
        pick = aide._pick_item(root, cfg, QUEUE, claim_branches=[])
        assert pick is not None and pick[0] == 27, (icon, pick)


def test_item_dependencies_is_case_insensitive(tmp_path: Path):
    root = _init_repo(tmp_path / "r")
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\n- lowercase item 028 still blocks.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    assert aide._item_dependencies(root, cfg, 27) == [28]


def test_item_dependencies_ignores_downstream_forward_reference(tmp_path: Path):
    # Regression: "**Downstream:** item 028 depends on this item" was
    # previously misread as item 027 depending ON 028 (backwards) — the exact
    # bug that let `aide claim` skip an unblocked item in favour of a wrong one.
    root = _init_repo(tmp_path / "r")
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\n"
        "- Item 026 provides X.\n\n"
        "**Downstream:** item 028 depends on this item's output.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    assert aide._item_dependencies(root, cfg, 27) == [26]


def test_pick_item_not_blocked_by_a_downstream_forward_reference(tmp_path: Path):
    root = _init_repo(tmp_path / "r")
    # 027 mentions 028 only as a downstream forward reference -> 027 must be
    # pickable even though 028 is still planned.
    (root / "docs" / "aide" / "items" / "027-bounds.md").write_text(
        "# Item 027 — Bounds\n\n## Dependencies\nNone.\n\n"
        "**Downstream:** item 028 depends on this item's output.\n\n## End\n",
        encoding="utf-8",
    )
    cfg = aide.load_config(root)
    pick = aide._pick_item(root, cfg, QUEUE, claim_branches=[])
    assert pick is not None and pick[0] == 27


# --------------------------------------------------------------------------- #
# claim
# --------------------------------------------------------------------------- #
def test_claim_local_creates_branch_no_push(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "claim"])
    assert rc == 0
    assert _current_branch(root) == "aide/027-bounds-rules"


def test_claim_dry_run_does_not_switch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "claim", "--dry-run"])
    assert rc == 0
    assert _current_branch(root) == "main"


# --------------------------------------------------------------------------- #
# merge
# --------------------------------------------------------------------------- #
def _make_item_branch(root: Path, branch: str, filename: str,
                      base: Optional[str] = "main") -> None:
    """A claim branch as `aide claim` would leave it — base recorded and all.

    Recording the base is not decoration: since issue #174 `merge` refuses a
    claim branch that has none, because `claim` writes one for every branch it
    creates, so a missing record means the record was LOST. A fixture that
    skipped it would be testing the refusal in every merge test rather than
    the merge. Pass ``base=None`` for a branch that genuinely has no record —
    as does an empty string, since a base recorded as "" is not a base.
    """
    _run(["git", "switch", "-c", branch], root)
    (root / filename).write_text("work\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", f"work on {branch}"], root)
    _run(["git", "switch", "main"], root)
    if base:
        aide._record_branch_base(root, branch, base)


def test_merge_local_merges_to_main(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    rc = aide.main(["--repo", str(root), "merge", "27", "--no-test"])
    assert rc == 0
    assert _current_branch(root) == "main"
    assert (root / "feature.txt").is_file()  # branch content is on main


def test_merge_pr_mode_pushes_and_stops(tmp_path: Path):
    # Bare remote so the push has somewhere to go; pr mode must NOT merge.
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="pr")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    rc = aide.main(["--repo", str(root), "merge", "27", "aide/027-bounds-rules", "--no-test"])
    assert rc == 0
    # pr mode does not merge: feature file absent on main.
    assert not (root / "feature.txt").is_file()
    # …but the branch was pushed to origin.
    refs = _run(["git", "ls-remote", "--heads", str(remote)], root).stdout
    assert "aide/027-bounds-rules" in refs


def test_merge_auto_merge_pushes_and_deletes_branch(tmp_path: Path):
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    _run(["git", "push", "-u", "origin", "aide/027-bounds-rules"], root)
    rc = aide.main(["--repo", str(root), "merge", "27", "--no-test"])
    assert rc == 0
    assert (root / "feature.txt").is_file()  # merged to main
    # Local claim branch deleted.
    branches = _run(["git", "branch"], root).stdout
    assert "aide/027-bounds-rules" not in branches
    # Remote claim branch deleted.
    refs = _run(["git", "ls-remote", "--heads", str(remote)], root).stdout
    assert "aide/027-bounds-rules" not in refs


def test_merge_missing_branch_errors(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "merge", "99", "--no-test"])
    assert rc == 1


# --------------------------------------------------------------------------- #
# claim scope (WI-2: derived queue state, opt-in cross-queue claiming)
# --------------------------------------------------------------------------- #
QUEUE_NEXT = """\
# Demo — Work Queue 004

> **Created:** 2026-07-02

### Item 029: Extra rules
Extra.
"""


def _add_next_queue_and_claim_all(root: Path) -> None:
    (root / "docs" / "aide" / "queue" / "queue-004.md").write_text(QUEUE_NEXT, encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "queue 004"], root)
    # Claim branches exist for every open item of queue-003.
    _run(["git", "branch", "aide/027-bounds-rules"], root)
    _run(["git", "branch", "aide/028-coverage-rules"], root)


def test_claim_creates_the_missing_inbox_on_the_way_through(tmp_path: Path,
                                                           capsys):
    """`aide claim -h`'s last sentence \u2014 the \u00a71 guarantee, kept on this path too.

    `/aide-run-queue` reaches its roles through `sync` and `claim`, never
    through `check`, so a loop that never ran `check` would otherwise have the
    roles copying the template by hand. The creation happens on the new branch,
    after the switch, so the inbox lands with the item rather than on its base.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    inbox = root / "docs" / "aide" / "insights.md"
    assert not inbox.exists()

    assert aide.main(["--repo", str(root), "claim"]) == 0
    assert inbox.is_file()
    assert "created docs/aide/insights.md" in capsys.readouterr().out


def test_claim_default_scope_stops_at_live_queue(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _add_next_queue_and_claim_all(root)
    rc = aide.main(["--repo", str(root), "claim", "--dry-run"])
    assert rc == 0
    assert "none left" in capsys.readouterr().out


def test_claim_all_open_scope_spans_queues(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _add_next_queue_and_claim_all(root)
    toml = (root / "aide.toml").read_text(encoding="utf-8")
    (root / "aide.toml").write_text(
        toml + '\n[loop]\nclaim_scope = "all-open"\n', encoding="utf-8")
    rc = aide.main(["--repo", str(root), "claim", "--dry-run"])
    assert rc == 0
    assert "would claim item 029" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# sync (WI-3: deterministic preflight)
# --------------------------------------------------------------------------- #
def test_sync_ok_on_clean_tree(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "sync"])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_sync_fails_on_dirty_tree(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    (root / "uncommitted.txt").write_text("wip\n", encoding="utf-8")
    rc = aide.main(["--repo", str(root), "sync"])
    assert rc == 1
    assert "not clean" in capsys.readouterr().err


def test_sync_item_switches_to_claim_branch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")  # ends on main
    rc = aide.main(["--repo", str(root), "sync", "--item", "27"])
    assert rc == 0
    assert _current_branch(root) == "aide/027-bounds-rules"


def test_sync_item_without_claim_branch_errors(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "sync", "--item", "28"])
    assert rc == 1
    assert "no claim branch" in capsys.readouterr().err


def test_sync_fast_forwards_main(tmp_path: Path):
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    # A second clone advances origin/main past our local main.
    other = tmp_path / "other"
    _run(["git", "clone", str(remote), str(other)], tmp_path)
    _run(["git", "config", "user.email", "t@example.com"], other)
    _run(["git", "config", "user.name", "Tester"], other)
    (other / "new.txt").write_text("x\n", encoding="utf-8")
    _run(["git", "add", "-A"], other)
    _run(["git", "commit", "-m", "remote work"], other)
    _run(["git", "push"], other)
    rc = aide.main(["--repo", str(root), "sync"])
    assert rc == 0
    assert (root / "new.txt").is_file()  # local main caught up


def _claim_with_unpushed_merge(tmp_path: Path):
    """A pushed claim branch holding a local merge commit origin has not seen.

    The consumer's shape (issue #235): an item's spec asked for a gate-approved
    commit from another branch to be merged into the claim branch as a real
    merge. Returns ``(root, remote, claim, merge_sha)``.
    """
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    claim = "aide/027-bounds-rules"
    _make_item_branch(root, claim, "feature.txt")            # ends on main
    _run(["git", "push", "origin", claim], root)             # no -u: no @{u}
    _run(["git", "switch", "-c", "gate/approved", "main"], root)
    (root / "approved.txt").write_text("approved\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "gate-approved work"], root)
    _run(["git", "switch", claim], root)
    _run(["git", "merge", "--no-ff", "-m", "merge gate/approved", "gate/approved"], root)
    sha = _run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    _run(["git", "switch", "main"], root)
    return root, remote, claim, sha


def test_sync_item_keeps_an_unpushed_merge_when_origin_has_not_moved(tmp_path: Path):
    """`pull --rebase` over a local merge commit linearises it silently —
    nothing reports it. `--ff-only` integrates nothing here and the merge
    survives, so the start point is safe and the verb says so."""
    root, _, claim, sha = _claim_with_unpushed_merge(tmp_path)
    rc = aide.main(["--repo", str(root), "sync", "--item", "27"])
    assert rc == 0
    assert _current_branch(root) == claim
    assert _run(["git", "rev-parse", "HEAD"], root).stdout.strip() == sha
    assert _run(["git", "rev-list", "--merges", f"origin/{claim}..HEAD"], root).stdout.strip()


def test_sync_item_refuses_to_rebase_an_unpushed_merge_over_a_moved_origin(
        tmp_path: Path, capsys):
    """The other half: origin/<claim> moved, so a rebase would replay both
    parents linearly and stop on the conflict the merge resolved — on a
    checkout other roles may share. Refuse before pulling, naming the fix."""
    root, remote, claim, sha = _claim_with_unpushed_merge(tmp_path)
    other = tmp_path / "other"
    _run(["git", "clone", "-b", claim, str(remote), str(other)], tmp_path)
    _run(["git", "config", "user.email", "t@example.com"], other)
    _run(["git", "config", "user.name", "Tester"], other)
    (other / "approved.txt").write_text("the other machine's version\n", encoding="utf-8")
    _run(["git", "add", "-A"], other)
    _run(["git", "commit", "-m", "remote work on the claim"], other)
    _run(["git", "push"], other)
    rc = aide.main(["--repo", str(root), "sync", "--item", "27"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "merge commit origin has not seen" in err
    assert f"git push origin {claim}" in err
    # Nothing was rewritten and nothing is mid-rebase.
    assert _run(["git", "rev-parse", "HEAD"], root).stdout.strip() == sha
    assert not (root / ".git" / "rebase-merge").exists()
    assert not (root / ".git" / "rebase-apply").exists()


# --------------------------------------------------------------------------- #
# gc (WI-3: claim-branch garbage collection)
# --------------------------------------------------------------------------- #
def _squash_merge(root: Path, branch: str, message: str) -> None:
    """Land *branch* on main the way GitHub's "Squash and merge" does.

    The shape `gc` reaches for `git branch -D` to cope with: the content is on
    main, but the branch tip is no ancestor of it, so `git branch --merged`
    cannot see it.
    """
    _run(["git", "switch", "main"], root)
    _run(["git", "merge", "--squash", branch], root)
    _run(["git", "commit", "-m", message], root)


def test_gc_dry_run_lists_a_landed_stale_branch(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    # Item 026 is ✅ in progress.md; its work landed, so the branch is stale.
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    rc = aide.main(["--repo", str(root), "gc"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "would delete aide/026-rule-engine-core" in out
    assert "dry run" in out
    branches = _run(["git", "branch"], root).stdout
    assert "aide/026-rule-engine-core" in branches  # nothing deleted


def test_gc_yes_deletes_local_and_remote(tmp_path: Path):
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _run(["git", "push", "-u", "origin", "aide/026-rule-engine-core"], root)
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    _run(["git", "push", "origin", "main"], root)
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    assert rc == 0
    branches = _run(["git", "branch"], root).stdout
    assert "aide/026-rule-engine-core" not in branches
    refs = _run(["git", "ls-remote", "--heads", str(remote)], root).stdout
    assert "aide/026-rule-engine-core" not in refs


# --------------------------------------------------------------------------- #
# gc — the ✅ ground asks git whether the work actually landed
# --------------------------------------------------------------------------- #
def test_gc_refuses_a_tick_whose_branch_has_unlanded_content(tmp_path: Path, capsys):
    """The defect: `progress.md` said ✅, git was never asked, and `-D` plus a
    remote delete discarded a commit that had never merged."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout
    assert "skipping aide/026-rule-engine-core" in out
    assert "main" in out  # the skip names the base it was measured against


def test_gc_abandon_deletes_an_unlanded_tick_on_purpose(tmp_path: Path):
    """Abandoning a claim is a real part of the lifecycle (conventions §2) — it
    just has to be asked for, not inferred from a document."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    rc = aide.main(["--repo", str(root), "gc", "--abandon", "--yes"])
    assert rc == 0
    assert "aide/026-rule-engine-core" not in _run(["git", "branch"], root).stdout


def test_gc_deletes_a_single_commit_squash_merge(tmp_path: Path):
    """No regression in the case `-D` exists to serve."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    assert "aide/026-rule-engine-core" not in _run(["git", "branch"], root).stdout


def test_gc_deletes_a_multi_commit_squash_merge(tmp_path: Path):
    """The shape `git cherry` gets wrong — it reports a false alarm — and the
    reason `merge-tree --write-tree` is the oracle rather than `cherry`."""
    root = _init_repo(tmp_path / "r", mode="local")
    _run(["git", "switch", "-c", "aide/026-rule-engine-core"], root)
    for n in ("one", "two"):
        (root / f"{n}.txt").write_text(f"{n}\n", encoding="utf-8")
        _run(["git", "add", "-A"], root)
        _run(["git", "commit", "-m", f"part {n}"], root)
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    assert "aide/026-rule-engine-core" not in _run(["git", "branch"], root).stdout


def test_gc_still_deletes_after_the_base_advances_with_unrelated_work(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    (root / "unrelated.txt").write_text("later\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "unrelated work"], root)
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    assert "aide/026-rule-engine-core" not in _run(["git", "branch"], root).stdout


def test_gc_refuses_the_tick_ground_on_git_too_old(tmp_path: Path, capsys, monkeypatch):
    """Old git becomes MORE conservative, never less: no second oracle, and
    nobody's `gc` stops working — it just declines this ground and says why."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    monkeypatch.setattr(aide, "_git_version", lambda _root: (2, 34))
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout
    assert "2.38" in out


# --------------------------------------------------------------------------- #
# gc — the preview is the set --yes acts on
# --------------------------------------------------------------------------- #
def _gc_lines(capsys) -> set:
    """Branch names the run reported as deletable, from either path."""
    out = capsys.readouterr().out
    prefixes = ("would delete ", "deleted ")
    return {line[len(pre):].split()[0]
            for line in out.splitlines() for pre in prefixes
            if line.startswith(pre)}


def test_gc_preview_and_yes_report_the_same_set(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")  # 📋, kept
    capsys.readouterr()
    aide.main(["--repo", str(root), "gc"])
    previewed = _gc_lines(capsys)
    aide.main(["--repo", str(root), "gc", "--yes"])
    assert _gc_lines(capsys) == previewed


def test_a_gc_skip_names_the_branch_where_it_lives_and_why(tmp_path: Path,
                                                          capsys):
    """The literal `aide gc -h` quotes, on both paths.

    A skip is the only thing a reader has instead of a deletion, so it has to
    say which branch, whether the local or the remote copy is meant, and what
    stopped it. The help quoted the line without `(local/remote)` until 1.49.4.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")

    for extra in ([], ["--yes"]):
        capsys.readouterr()
        assert aide.main(["--repo", str(root), "gc", *extra]) == 0
        skips = [l for l in capsys.readouterr().out.splitlines()
                 if l.startswith("skipping ")]
        assert skips == ["skipping aide/026-rule-engine-core (local): item 026 "
                         "is \u2705 but the branch has content not in main; "
                         "re-check it, or pass --abandon to delete it anyway"], skips


def test_a_gc_skip_says_so_when_the_landing_could_not_be_measured(
        tmp_path: Path, capsys, monkeypatch):
    """The fourth reason `aide gc -h` enumerates, and the one easiest to lose.

    "Could not be determined" and "has content not in main" are different
    statements, and this is the one destructive verb: saying the second about a
    ref the run never read would be a claim it cannot support. The oracle's own
    half is exercised unmocked; `cmd_gc`'s rendering of that answer needs the
    oracle forced, since a listed branch whose ref does not resolve is not a
    state git will let a fixture build.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    # Unmocked: a ref it cannot read is unmeasurable, never False.
    assert aide._branch_content_landed(root, "main", "origin/nope") is None

    monkeypatch.setattr(aide, "_branch_content_landed", lambda *a, **k: None)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "skipping aide/026-rule-engine-core (local):" in out
    assert "could not be determined" in out
    assert "has content not in" not in out
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout


def test_gc_preview_does_not_promise_to_delete_the_checked_out_branch(
        tmp_path: Path, capsys):
    """The preview used to list a branch `--yes` then silently skipped."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    _run(["git", "switch", "aide/026-rule-engine-core"], root)
    capsys.readouterr()
    aide.main(["--repo", str(root), "gc"])
    previewed = _gc_lines(capsys)
    assert previewed == set()
    aide.main(["--repo", str(root), "gc", "--yes"])
    assert _gc_lines(capsys) == previewed
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout


def test_gc_protects_a_branch_at_a_detached_head(tmp_path: Path, capsys):
    """`rev-parse --abbrev-ref HEAD` returns the literal 'HEAD' when detached,
    and no branch equals that — so the guard protected nothing."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    _run(["git", "checkout", "--detach", "aide/026-rule-engine-core"], root)
    capsys.readouterr()
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    assert rc == 0
    assert _gc_lines(capsys) == set()
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout


def test_gc_merged_now_sees_a_squash_merge(tmp_path: Path):
    """`--merged` is built on ancestry and missed every squash merge; the same
    oracle that guards the ✅ ground closes that too."""
    root = _init_repo(tmp_path / "r", mode="local")
    # Item 027 is 📋, so only the --merged ground can collect this.
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    _squash_merge(root, "aide/027-bounds-rules", "squash 027")
    assert aide.main(["--repo", str(root), "gc", "--merged", "--yes"]) == 0
    assert "aide/027-bounds-rules" not in _run(["git", "branch"], root).stdout


def test_gc_keeps_active_item_branch(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    # Item 027 is 📋 (not complete) — its claim branch must survive gc.
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    assert rc == 0
    branches = _run(["git", "branch"], root).stdout
    assert "aide/027-bounds-rules" in branches


def test_gc_merged_deletes_merged_branch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    # Branch for 📋 item merged into main (e.g. landed by hand): --merged collects it.
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    _run(["git", "merge", "--no-edit", "aide/027-bounds-rules"], root)
    rc = aide.main(["--repo", str(root), "gc", "--merged", "--yes"])
    assert rc == 0
    branches = _run(["git", "branch"], root).stdout
    assert "aide/027-bounds-rules" not in branches


# --------------------------------------------------------------------------- #
# branch parsing — queue numbers and item numbers share one namespace
# --------------------------------------------------------------------------- #
def test_branch_item_number_reads_a_claim_branch():
    assert aide._branch_item_number("aide/026-rule-engine-core", "aide/") == 26
    assert aide._branch_item_number("aide/007-x", "aide/") == 7
    assert aide._branch_item_number("aide/026", "aide/") == 26


def test_branch_item_number_rejects_a_queue_branch():
    """The defect this anchoring exists to prevent.

    `aide/queue-016` used to resolve to item 016 — an unrelated, long-finished
    work item — because the fallback searched anywhere in the branch name for a
    digit run. `gc` deletes a branch whose item is ✅ using `git branch -D` plus
    a remote delete, independently of `--merged`, so that misread could destroy
    an in-flight queue branch carrying unreviewed specs.
    """
    assert aide._branch_item_number("aide/queue-016", "aide/") is None
    assert aide._branch_item_number("aide/specs-queue-015", "aide/") is None
    assert aide._is_queue_branch("aide/queue-016", "aide/")
    assert aide._is_queue_branch("aide/specs-queue-015", "aide/")


def test_branch_item_number_rejects_an_unnumbered_branch():
    assert aide._branch_item_number("aide/fix-the-thing", "aide/") is None
    assert not aide._is_queue_branch("aide/fix-the-thing", "aide/")


def test_branch_item_number_honours_a_custom_prefix():
    assert aide._branch_item_number("wip/031-x", "wip/") == 31
    assert aide._branch_item_number("aide/031-x", "wip/") is None


# --------------------------------------------------------------------------- #
# branch construction — every name the engine produces, read back by the
# recogniser that must later parse it
# --------------------------------------------------------------------------- #
#: Prefixes chosen to break a careless implementation: the default; one with no
#: separator; one containing a digit (a prefix-swallowing `\d+` reads `2` as the
#: number); and one whose text ends in the queue token itself.
_PREFIXES = ["aide/", "wip/", "v2/", "aide", "team/queue-"]


@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize("number", [1, 16, 123, 1234])
def test_queue_branch_name_round_trips_through_its_recogniser(prefix, number):
    """The test #72 exists to make possible.

    Until 1.20.0 `<prefix>queue-NNN` had no constructor — an agent typed it out
    of a markdown file — so there was nothing to round-trip and the regex that
    parses it never saw a name until something had already gone wrong.
    """
    branch = aide.queue_branch_name(prefix, number)
    assert aide._is_queue_branch(branch, prefix)
    # And is never mistaken for the same-numbered item claim, which is the
    # misread that once let `gc` delete an in-flight queue branch.
    assert aide._branch_item_number(branch, prefix) is None


@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize("number", [1, 16, 123, 1234])
def test_specs_queue_branch_name_round_trips_through_its_recogniser(prefix, number):
    branch = aide.specs_queue_branch_name(prefix, number)
    assert aide._is_queue_branch(branch, prefix)
    assert aide._branch_item_number(branch, prefix) is None


@pytest.mark.parametrize("prefix", _PREFIXES)
@pytest.mark.parametrize("number", [1, 16, 123, 1234])
def test_claim_branch_name_round_trips_through_its_recogniser(prefix, number):
    branch = aide.claim_branch_name(prefix, number, "Rule engine core")
    assert aide._branch_item_number(branch, prefix) == number
    assert not aide._is_queue_branch(branch, prefix)


def test_branch_constructors_produce_the_documented_shapes():
    """Pins the literal text, so a refactor of the token cannot quietly
    re-shape every branch name the framework tells a human to expect."""
    assert aide.queue_branch_name("aide/", 16) == "aide/queue-016"
    assert aide.specs_queue_branch_name("aide/", 15) == "aide/specs-queue-015"
    assert aide.claim_branch_name("aide/", 26, "Rule engine core") == \
        "aide/026-rule-engine-core"


def test_queue_branch_recogniser_still_accepts_unpadded_digits():
    """Constructors always pad; a human or an older run may not have."""
    assert aide._is_queue_branch("aide/queue-16", "aide/")
    assert aide._is_queue_branch("aide/specs-queue-5", "aide/")


def test_a_slugged_queue_branch_is_still_not_recognised():
    """#55 (queue slugs) is deferred and this records the state, not a wish.

    With one constructor, changing the shape becomes a one-place edit whose
    failure this suite catches — rather than a mis-targeted merge in a live run.
    """
    assert not aide._is_queue_branch("aide/queue-016-stage-27", "aide/")


# --------------------------------------------------------------------------- #
# aide queue start
# --------------------------------------------------------------------------- #
def test_queue_start_creates_and_records_its_base(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "queue", "start", "16"])
    assert rc == 0
    assert _current_branch(root) == "aide/queue-016"
    assert aide._recorded_branch_base(root, "aide/queue-016") == "main"


def test_queue_start_specs_creates_the_specs_branch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "queue", "start", "15", "--specs"])
    assert rc == 0
    assert _current_branch(root) == "aide/specs-queue-015"


def test_queue_start_dry_run_creates_nothing(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "queue", "start", "16", "--dry-run"])
    assert rc == 0
    assert "aide/queue-016" in capsys.readouterr().out
    assert _current_branch(root) == "main"
    assert "aide/queue-016" not in _run(["git", "branch"], root).stdout


def test_queue_start_refuses_a_base_that_is_not_a_local_branch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "queue", "start", "16", "--base", "nope"])
    assert rc == 1
    assert _current_branch(root) == "main"


def test_queue_start_refuses_to_recreate_an_existing_branch(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "16"]) == 0
    _run(["git", "switch", "main"], root)
    assert aide.main(["--repo", str(root), "queue", "start", "16"]) == 1


def test_queue_start_branches_from_the_named_base_not_head(tmp_path: Path):
    """`switch -c` with no start point uses HEAD, which would let the branch's
    real origin disagree with the base it records."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/099-elsewhere", "stray.txt")
    _run(["git", "switch", "aide/099-elsewhere"], root)
    rc = aide.main(["--repo", str(root), "queue", "start", "16", "--base", "main"])
    assert rc == 0
    assert not (root / "stray.txt").is_file()


def test_a_claim_off_a_started_queue_branch_merges_back_into_it(tmp_path: Path):
    """The failure #72 measured: an unrecognised queue branch made `claim`
    fall back to `main_branch`, merging the item past the queue branch."""
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    branch = _current_branch(root)
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"


def test_gc_never_deletes_a_queue_branch_for_a_same_numbered_item(tmp_path: Path, capsys):
    """Item 026 is ✅, but `aide/queue-026` is not item 026's claim branch."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/queue-026", "queue.txt")
    rc = aide.main(["--repo", str(root), "gc", "--yes"])
    assert rc == 0
    branches = _run(["git", "branch"], root).stdout
    assert "aide/queue-026" in branches
    assert "deleted" not in capsys.readouterr().out


def test_check_does_not_report_a_queue_branch_as_a_stale_claim(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    cfg = aide.load_config(root)
    _, warnings = aide.run_checks(root, cfg, branches=["aide/queue-026"])
    assert not any("stale claim" in w for w in warnings)
    assert not any("unrecognised" in w for w in warnings)


def test_check_reports_a_prefixed_branch_it_cannot_parse(tmp_path: Path):
    """Anchoring must not turn a real stale claim into a silent skip."""
    root = _init_repo(tmp_path / "r", mode="local")
    cfg = aide.load_config(root)
    _, warnings = aide.run_checks(root, cfg, branches=["aide/rule-engine-core"])
    assert any("unrecognised branch aide/rule-engine-core" in w for w in warnings)


def test_unrecognised_branch_warning_names_the_remedy(tmp_path: Path):
    """A warning that explains the convention but not the fix sends the reader
    to raw git, which is what the CLI's own convention says to avoid."""
    root = _init_repo(tmp_path / "r", mode="local")
    cfg = aide.load_config(root)
    _, warnings = aide.run_checks(root, cfg, branches=["aide/rule-engine-core"])
    warning = next(w for w in warnings if "unrecognised branch" in w)
    assert "rename" in warning
    assert "aide gc --merged" in warning


# --------------------------------------------------------------------------- #
# gc signposting — an empty result is about a ground and a scope, not the repo
# --------------------------------------------------------------------------- #
def test_gc_empty_default_points_at_merged_when_it_would_find_something(
        tmp_path: Path, capsys):
    """The item ground structurally cannot see a queue branch; --merged can.

    Reporting a bare "nothing to clean" while `aide gc --merged` would offer
    three branches is a true statement about the ground checked read as a false
    one about the repository.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/queue-026", "queue.txt")
    _run(["git", "merge", "--no-edit", "aide/queue-026"], root)
    rc = aide.main(["--repo", str(root), "gc"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "nothing to clean" in out
    assert "aide gc --merged" in out


def test_gc_empty_result_stays_terse_when_there_is_nothing_to_add(
        tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "gc"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip() == "aide gc: nothing to clean"


def test_gc_states_its_scope_when_branches_sit_outside_the_prefix(
        tmp_path: Path, capsys):
    """gc only ever looks at branches under the prefix -- correctly, since it
    must not delete branches it does not own. The defect is that the
    restriction was silent, so "nothing to clean" read as "no cleanup exists"
    for a merged branch gc had never even considered."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "fix/33-signposting", "fix.txt")
    _run(["git", "merge", "--no-edit", "fix/33-signposting"], root)
    rc = aide.main(["--repo", str(root), "gc"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "nothing to clean" in out
    assert "1 local branch outside the 'aide/' scope was not considered" in out


def test_gc_does_not_probe_merged_when_the_flag_was_passed(tmp_path: Path, capsys):
    """With --merged already given, naming --merged again would be nonsense."""
    root = _init_repo(tmp_path / "r", mode="local")
    rc = aide.main(["--repo", str(root), "gc", "--merged"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "aide gc --merged" not in out


def _mkbare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-b", "main", str(path)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return path


# --------------------------------------------------------------------------- #
# 🔍 In Review — ✅ means "merged", in every git.mode
# --------------------------------------------------------------------------- #
def test_in_review_rolls_a_stage_up_to_in_progress_not_complete():
    """The whole point: an open PR must not roll a stage up to "shipped"."""
    assert aide.rollup_status(["in-review"]) == "in-progress"
    assert aide.rollup_status(["complete", "in-review"]) == "in-progress"
    assert aide.rollup_status(["complete"]) == "complete"


def test_in_review_outranks_in_progress_and_is_outranked_by_complete():
    assert aide.RANK["in-progress"] < aide.RANK["in-review"] < aide.RANK["complete"]


def test_in_review_keeps_its_queue_open():
    """A queue is not finished with an item whose review has not happened."""
    text = "### Item 026 — x\n"
    assert aide.queue_is_open(text, {26: "in-review"})
    assert not aide.queue_is_open(text, {26: "complete"})


def test_merge_records_the_tick_itself_in_local_mode(tmp_path: Path):
    """✅ is set by the process that did the merge, so it cannot outrun it."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    # The 🔍 tick is committed, not left in the tree: `merge` refuses to
    # `switch`/`pull`/`merge` from a dirty one (issue #133), so a run that
    # means to land must hand it a clean tree first.
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 0
    progress = (root / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "✅ Bounds rules" in progress or "27" in progress
    _, _, status = aide._parse_item_status(progress.splitlines())
    assert status[27] == "complete"


def test_pr_mode_merge_leaves_the_item_in_review(tmp_path: Path, capsys):
    """The designed state #71 names: pushed, awaiting a human — NOT ✅."""
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="pr")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27", "in-review",
                      "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 0
    progress = (root / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    _, _, status = aide._parse_item_status(progress.splitlines())
    assert status[27] == "in-review"


def test_gc_never_targets_an_item_awaiting_review(tmp_path: Path, capsys):
    """The load-bearing fix: `gc`'s ground is "the item is ✅", and a `pr`-mode
    item is no longer ✅ — so the exhaustion sweep cannot offer to delete the
    head branch of an open PR."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27", "in-review",
                      "--no-commit"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    assert "aide/027-bounds-rules" in _run(["git", "branch"], root).stdout
    assert "would delete" not in capsys.readouterr().out


def test_check_does_not_call_a_branch_awaiting_review_stale(tmp_path: Path, capsys):
    """A warning that fires on every run until a human merges is a warning
    that gets tuned out."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27", "in-review",
                      "--no-commit"]) == 0
    capsys.readouterr()
    aide.main(["--repo", str(root), "check"])
    assert "stale claim branch" not in capsys.readouterr().out


def test_status_does_not_recommend_gc_for_a_branch_awaiting_review(
        tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27", "in-review",
                      "--no-commit"]) == 0
    capsys.readouterr()
    aide.main(["--repo", str(root), "status"])
    out = capsys.readouterr().out
    assert "awaiting review" in out
    assert "run 'aide gc'" not in out


def test_sync_reports_a_review_item_whose_work_has_landed(tmp_path: Path, capsys):
    """🔍 needs a way home: in `pr` mode nothing in the loop observes the merge,
    so without this an item enters the state and never leaves it."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    _squash_merge(root, "aide/027-bounds-rules", "squash 027")
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "sync"]) == 0
    out = capsys.readouterr().out
    assert "item 027 is 🔍" in out
    assert "progress set 027 done" in out


def test_sync_is_silent_about_a_review_item_still_awaiting_its_merge(
        tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "sync"]) == 0
    assert "is 🔍 but its work is now in" not in capsys.readouterr().out


def test_status_names_a_review_item_whose_work_has_landed(tmp_path: Path, capsys):
    """`aide status -h` promises this of `status`, not only of `sync`.

    The sentence names both verbs, and the two call `_landed_review_items`
    from different places: `status` prints it near the end of its report, with
    the `aide sync: ` prefix stripped, so a regression in that one line would
    leave the sync test green and the help wrong.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    _squash_merge(root, "aide/027-bounds-rules", "squash 027")
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    assert "item 027 is \U0001f50d but its work is now in main" in out
    assert "progress set 027 done" in out


def _stacked_review_item_landed_in_its_queue(
        root: Path, recorded: Optional[str] = "aide/queue-003") -> None:
    """Item 027 claimed off `aide/queue-003`, 🔍, its PR merged into the queue.

    The work is in the queue branch and not in main — the shape stacked work
    has between an item's merge and its queue's (issue #213). Status is set on
    main, where the loop records it, and HEAD is left on main. *recorded* is
    the base the claim remembers; ``None`` is a checkout that never ran the
    `claim`, so has no record at all.
    """
    _run(["git", "branch", "aide/queue-003"], root)
    aide._record_branch_base(root, "aide/queue-003", "main")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt",
                      base=recorded)
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    _run(["git", "switch", "aide/queue-003"], root)
    _run(["git", "merge", "--squash", "aide/027-bounds-rules"], root)
    _run(["git", "commit", "-m", "squash 027 into the queue"], root)
    _run(["git", "switch", "main"], root)


def test_status_names_stacked_review_work_landed_in_its_recorded_base(
        tmp_path: Path, capsys):
    """Measured against `main_branch`, stacked work was never reported landed.

    Run from main, so the current branch's base is main too: the claim's own
    record is the only thing that can name the queue branch.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _stacked_review_item_landed_in_its_queue(root)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    assert ("item 027 is \U0001f50d but its work is now in aide/queue-003"
            in out)
    assert "progress set 027 done" in out


def test_status_measures_landed_work_against_an_explicit_base(
        tmp_path: Path, capsys):
    """`--base` reaches the landed line, not only the ahead/behind one.

    One command, one resolution. A checkout that never ran the `claim` has no
    record to find the queue branch by, and `--base` is the way to name it.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _stacked_review_item_landed_in_its_queue(root, recorded=None)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    assert "is \U0001f50d but its work is now in" not in capsys.readouterr().out
    assert aide.main(["--repo", str(root), "status", "--no-fetch",
                      "--base", "aide/queue-003"]) == 0
    assert ("item 027 is \U0001f50d but its work is now in aide/queue-003"
            in capsys.readouterr().out)


def test_status_still_reports_stacked_work_once_its_queue_landed_and_went(
        tmp_path: Path, capsys):
    """The recorded base can be deleted; main is still measured then.

    A landed queue branch is a `gc --merged` target. Measured only against its
    record, a 🔍 item of that queue compared with a ref that no longer exists
    — which `merge-tree` answers as it answers a conflict — and was never
    reported again, though its work was in main.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _stacked_review_item_landed_in_its_queue(root)
    _squash_merge(root, "aide/queue-003", "squash queue 003")
    _run(["git", "branch", "-D", "aide/queue-003"], root)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    assert ("item 027 is \U0001f50d but its work is now in main"
            in capsys.readouterr().out)


def test_status_sees_a_forge_merge_only_once_the_base_is_pulled(
        tmp_path: Path, capsys):
    """`status -h` says the landed line reads local bases, not origin/<base>.

    A squash merge on the forge reaches this checkout as `origin/main` after a
    fetch; local main does not move until it is pulled, and until then the
    item is not reported — documented, deliberately not changed.
    """
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="local")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    # The forge's merge: a squash on a throwaway branch, pushed to origin/main.
    _run(["git", "switch", "-c", "forge"], root)
    _run(["git", "merge", "--squash", "aide/027-bounds-rules"], root)
    _run(["git", "commit", "-m", "squash 027 on the forge"], root)
    _run(["git", "push", "origin", "forge:main"], root)
    _run(["git", "switch", "main"], root)
    _run(["git", "branch", "-D", "forge"], root)
    _run(["git", "fetch", "origin"], root)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    assert "is \U0001f50d but its work is now in" not in capsys.readouterr().out
    _run(["git", "merge", "--ff-only", "origin/main"], root)
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    assert ("item 027 is \U0001f50d but its work is now in main"
            in capsys.readouterr().out)


def test_sync_reports_stacked_review_work_landed_in_its_recorded_base(
        tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    _stacked_review_item_landed_in_its_queue(root)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "sync"]) == 0
    out = capsys.readouterr().out
    assert "item 027 is \U0001f50d but its work is now in aide/queue-003" in out
    assert "progress set 027 done" in out


# --------------------------------------------------------------------------- #
# The tick reaches origin — regression: it was committed after the only push
# --------------------------------------------------------------------------- #
def test_auto_merge_pushes_the_commit_that_records_the_tick(tmp_path: Path):
    """`aide merge` writes the ✅ itself, so that commit must ride the push.

    Recorded after it, the tick was stranded on local main: origin's
    progress.md under-reported, and on a queue's last item nothing in the CLI
    would ever push it (`aide sync` only fetches and pulls).
    """
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "progress", "set", "27",
                      "in-review"]) == 0
    _run(["git", "push"], root)
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 0
    ahead = _run(["git", "rev-list", "--count", "origin/main..main"], root).stdout.strip()
    assert ahead == "0", "the ✅ commit never reached origin"
    _, _, status = aide._parse_item_status(
        _show_utf8(root, "origin/main:docs/aide/progress.md").splitlines())
    assert status[27] == "complete"


def test_merge_after_a_no_commit_run_names_the_tick_it_is_blocked_on(
        tmp_path: Path, capsys):
    """`--no-commit` leaves the tick in the tree, and the NEXT merge — of any
    item — meets the dirty-tree precondition (issue #133).

    The refusal is right: git will not rebase over unstaged changes either. But
    the block outlives the item that caused it, so the message has to name the
    cause. A run that says only "uncommitted changes: docs/aide/progress.md"
    sends a human hunting for an edit nobody made.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test",
                      "--no-commit"]) == 0
    assert "progress.md" in _run(["git", "status", "--porcelain"], root).stdout

    # Item 028's own work, committed by path the way a careful consumer does —
    # so the stray tick is NOT swept into that commit by a `git add -A`.
    _run(["git", "switch", "-c", "aide/028-coverage-rules"], root)
    (root / "feature2.txt").write_text("work\n", encoding="utf-8")
    _run(["git", "add", "feature2.txt"], root)
    _run(["git", "commit", "-m", "work on 028"], root)
    _run(["git", "switch", "main"], root)
    # As `claim` would have left it — otherwise the base refusal (issue #174)
    # answers first and this test stops being about the dirty tree.
    aide._record_branch_base(root, "aide/028-coverage-rules", "main")
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "merge", "28", "--no-test"]) == 1
    err = capsys.readouterr().err
    assert "progress.md" in err and "--no-commit" in err
    # ...and committing it is all that was needed.
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "chore: the tick"], root)
    assert aide.main(["--repo", str(root), "merge", "28", "--no-test"]) == 0


@pytest.mark.parametrize("docs_rel", ["docs/aide", "docs/a spacé dir"])
def test_the_uncommitted_tick_is_recognised_whatever_the_layout(
        tmp_path: Path, docs_rel: str):
    """The diagnosis must not quietly fall back to the generic message.

    Two layouts break a naive string compare, and neither is documented as
    unsupported: `git status --porcelain` **quotes and escapes** a path with a
    space or a non-ASCII byte, and it reports every path relative to the git
    **top level** — which is not `repo_root` when `aide.toml` sits in a
    subdirectory of the repository.
    """
    top = tmp_path / "outer"
    top.mkdir()
    _run(["git", "init", "-b", "main"], top)
    _run(["git", "config", "user.email", "t@example.com"], top)
    _run(["git", "config", "user.name", "Tester"], top)
    root = top / "sub"                       # aide.toml BELOW the git top level
    root.mkdir()
    (root / "aide.toml").write_text(
        AIDE_TOML.format(mode="local").replace(
            'docs_dir = "docs/aide"', f'docs_dir = "{docs_rel}"'),
        encoding="utf-8")
    ddir = root / docs_rel
    ddir.mkdir(parents=True)
    (ddir / "progress.md").write_text(PROGRESS, encoding="utf-8")
    _run(["git", "add", "-A"], top)
    _run(["git", "commit", "-m", "init"], top)

    config = aide.load_config(root)
    tick = aide.docs_dir(root, config) / "progress.md"
    assert aide._unsafe_tree_state(root, tick) is None
    tick.write_text(PROGRESS.replace("📋 Bounds", "🔍 Bounds"), encoding="utf-8")
    state = aide._unsafe_tree_state(root, tick)
    assert state is not None and "uncommitted status tick" in state

    # An unrelated dirty file is still the generic refusal, not the tick's.
    (root / "stray.txt").write_text("x\n", encoding="utf-8")
    _run(["git", "add", "stray.txt"], root)
    other = aide._unsafe_tree_state(root, tick)
    assert other is not None and "uncommitted status tick" not in other


def test_merge_no_commit_leaves_the_tick_uncommitted(tmp_path: Path):
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test",
                      "--no-commit"]) == 0
    dirty = _run(["git", "status", "--porcelain"], root).stdout
    assert "progress.md" in dirty
    progress = (root / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    _, _, status = aide._parse_item_status(progress.splitlines())
    assert status[27] == "complete"  # written, just not committed


# --------------------------------------------------------------------------- #
# A dependency awaiting review has not landed, so it still blocks
# --------------------------------------------------------------------------- #
def test_claim_skips_an_item_whose_dependency_is_only_in_review(tmp_path: Path):
    """Claiming off a base that lacks the dependency's work branches from a
    tree missing the very thing the dependency provides."""
    root = _init_repo(tmp_path / "r", mode="local")
    idir = root / "docs" / "aide" / "items"
    (idir / "027-bounds-rules.md").write_text(
        "# Item 027 — Bounds rules\n\n## Dependencies\n- Item 026 provides the engine.\n",
        encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "spec"], root)
    # Downgrade 026 to 🔍 by hand: `progress set` never walks a status backwards.
    ppath = root / "docs" / "aide" / "progress.md"
    ppath.write_text(ppath.read_text(encoding="utf-8")
                     .replace("- ✅ Core. *(Item 026)*", "- 🔍 Core. *(Item 026)*"),
                     encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "026 in review"], root)

    rc = aide.main(["--repo", str(root), "claim"])
    on = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()
    assert on != "aide/027-bounds-rules", "claimed an item whose dependency is unmerged"
    # 028 has no dependencies, so claiming moves on to it rather than stalling.
    assert rc == 0 and on == "aide/028-coverage-rules"


# --------------------------------------------------------------------------- #
# gc reports what git did, not what was asked of it
# --------------------------------------------------------------------------- #
def test_gc_skips_a_branch_checked_out_in_another_worktree(tmp_path: Path, capsys):
    """`git branch -D` refuses a branch any worktree is sitting on, so the guard
    has to ask `git worktree list` — otherwise the preview promises a delete
    that then bounces off, which is the exact defect #70 was filed about."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/026-rule-engine-core", "core.txt")
    _squash_merge(root, "aide/026-rule-engine-core", "squash 026")
    _run(["git", "worktree", "add", str(tmp_path / "wt"),
          "aide/026-rule-engine-core"], root)
    capsys.readouterr()
    # The PREVIEW must not promise it either — that is #70's first acceptance
    # criterion, "identical on every path", and a worktree is one of the paths.
    assert aide.main(["--repo", str(root), "gc"]) == 0
    previewed = _gc_lines(capsys)
    assert previewed == set()
    assert aide.main(["--repo", str(root), "gc", "--yes"]) == 0
    assert _gc_lines(capsys) == previewed
    assert "aide/026-rule-engine-core" in _run(["git", "branch"], root).stdout


def test_queue_start_refuses_a_name_that_exists_only_on_origin(tmp_path: Path, capsys):
    """It used to create the branch locally and then raise an uncaught
    CalledProcessError from the failing push — a traceback in an unattended flow."""
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    _run(["git", "switch", "-c", "aide/queue-016"], root)
    _run(["git", "push", "-u", "origin", "aide/queue-016"], root)
    _run(["git", "switch", "main"], root)
    _run(["git", "branch", "-D", "aide/queue-016"], root)
    _run(["git", "fetch", "origin"], root)
    capsys.readouterr()
    rc = aide.main(["--repo", str(root), "queue", "start", "16"])
    assert rc == 1
    assert "already exists on origin" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# a failed push — issue #137: a sentence, and never a silent half-claim
# --------------------------------------------------------------------------- #
def test_claim_push_failure_is_a_sentence_not_a_traceback(tmp_path: Path, capsys):
    """`auto-merge` with no remote: the push cannot succeed, and used to raise.

    `git(..., check=True)` let every cause of a failed push out of `main()` as
    a `CalledProcessError` — a raw traceback in a flow meant to be unattended.
    """
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    rc = aide.main(["--repo", str(root), "claim"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "pushing aide/027-bounds-rules to origin FAILED" in err
    assert "claimed LOCALLY ONLY" in err
    # The branch is kept, not rolled back, and it is what we are standing on.
    assert _current_branch(root) == "aide/027-bounds-rules"


def test_a_failed_claim_does_not_come_back_as_none_left(tmp_path: Path, capsys):
    """The defect the traceback hid: the item then counted as claimed.

    `_pick_item` skips any item with a claim branch, so the run *after* the
    failure reported an exhausted queue and exited 0 — the loop's own "is
    there work left?" answering no, successfully, with nothing built.
    """
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    assert aide.main(["--repo", str(root), "claim"]) == 1        # 027, push fails
    assert aide.main(["--repo", str(root), "claim"]) == 1        # 028, push fails
    capsys.readouterr()

    rc = aide.main(["--repo", str(root), "claim"])
    out = capsys.readouterr().out
    assert rc == 1
    assert out.strip() != "none left"
    assert "2 item(s) still open" in out
    assert out.count("ORIGIN HAS NEVER SEEN") == 2
    assert "aide/027-bounds-rules" in out and "aide/028-coverage-rules" in out


def test_status_names_an_unpublished_claim(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    assert aide.main(["--repo", str(root), "claim"]) == 1
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "status", "--no-fetch"]) == 0
    out = capsys.readouterr().out
    assert "claim: aide/027-bounds-rules" in out
    assert "NOT on origin" in out


def test_a_published_claim_is_in_flight_not_a_failure(tmp_path: Path, capsys):
    """The control: a claim whose push landed is an ordinary hold, exit 0."""
    remote = _mkbare(tmp_path / "remote.git")
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    _run(["git", "remote", "add", "origin", str(remote)], root)
    _run(["git", "push", "-u", "origin", "main"], root)
    assert aide.main(["--repo", str(root), "claim"]) == 0        # takes 027
    assert aide.main(["--repo", str(root), "claim"]) == 0        # takes 028
    capsys.readouterr()

    rc = aide.main(["--repo", str(root), "claim"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "none left" in out
    assert "already in flight" in out
    assert "ORIGIN HAS NEVER SEEN" not in out


def test_local_mode_never_calls_a_claim_branch_unpublished(tmp_path: Path, capsys):
    """`local` mode is the one place an unpushed claim branch is the design."""
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "claim"]) == 0
    assert aide.main(["--repo", str(root), "claim"]) == 0
    capsys.readouterr()

    rc = aide.main(["--repo", str(root), "claim"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "already in flight" in out
    assert "ORIGIN HAS NEVER SEEN" not in out


def test_none_left_names_a_dependency_that_has_not_landed(tmp_path: Path, capsys):
    """The third reason a queue is open with nothing offerable."""
    root = _init_repo(tmp_path / "r", mode="local")
    items = root / "docs" / "aide" / "items"
    for num, dep in ((27, 28), (28, 27)):
        (items / f"{num:03d}-x.md").write_text(
            f"# Item {num:03d} — X\n\n## Dependencies\n- Item {dep:03d}.\n\n## End\n",
            encoding="utf-8")
    rc = aide.main(["--repo", str(root), "claim", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "027 Bounds rules — waiting on 028 (planned)" in out
    assert "028 Coverage rules — waiting on 027 (planned)" in out


def test_an_empty_queue_still_says_only_none_left(tmp_path: Path, capsys):
    """The genuinely exhausted case keeps its one-line answer.

    Open queue, nothing in it still 📋 — the state `/aide-run-queue` reads as
    "the queue is exhausted, stop". It must stay a bare `none left`, or the
    reason lines would be noise on every finished queue.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "progress", "set", "27", "in-progress"]) == 0
    assert aide.main(["--repo", str(root), "progress", "set", "28", "done"]) == 0
    capsys.readouterr()
    rc = aide.main(["--repo", str(root), "claim", "--dry-run"])
    assert rc == 0
    assert capsys.readouterr().out.strip().splitlines()[-1] == "none left"


def test_queue_start_push_failure_is_a_sentence(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    rc = aide.main(["--repo", str(root), "queue", "start", "4"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "pushing aide/queue-004 to origin FAILED" in err
    assert "exists locally, branched from main" in err
    assert _current_branch(root) == "aide/queue-004"


def test_merge_pr_mode_push_failure_leaves_the_item_unticked(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="pr")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    rc = aide.main(["--repo", str(root), "merge", "27", "aide/027-bounds-rules",
                    "--no-test"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "pushing aide/027-bounds-rules to origin FAILED" in err
    assert "is NOT ticked" in err
    # progress.md untouched: 027 is still 📋.
    progress = (root / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")
    assert "📋 Bounds. *(Item 027)*" in progress


def test_check_warns_about_an_unpublished_branch(tmp_path: Path, capsys):
    """The third reporting surface, beside `claim` and `status`.

    §2 already puts claim-branch/status agreement in `check`, and a branch
    origin has never seen is the same kind of disagreement: the document set
    says an item is taken, and no other checkout can see the claim.
    """
    root = _init_repo(tmp_path / "r", mode="auto-merge")
    assert aide.main(["--repo", str(root), "claim"]) == 1
    capsys.readouterr()
    aide.main(["--repo", str(root), "check"])
    out = capsys.readouterr().out
    assert "unpublished branch aide/027-bounds-rules" in out
    assert "git push -u origin aide/027-bounds-rules" in out


def test_check_is_silent_about_claim_branches_in_local_mode(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "claim"]) == 0
    capsys.readouterr()
    aide.main(["--repo", str(root), "check"])
    assert "unpublished branch" not in capsys.readouterr().out


def test_claim_offers_the_first_planned_item_the_queue_lists(tmp_path: Path,
                                                            capsys):
    """`aide claim -h` says "the first \U0001f4cb item the queue lists", and means it.

    `_pick_item` walks `queue_item_numbers`, which is document order — a queue
    is free to list its items out of numeric order, and the pick follows the
    list rather than sorting it. The help said "lowest-numbered" until 1.49.4,
    which is what this fixture falsifies.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    (root / "docs" / "aide" / "queue" / "queue-003.md").write_text(
        "# Demo — Work Queue 003\n\n"
        "> **Status:** Live · **Created:** 2026-07-01\n\n"
        "### Item 028: Coverage rules\nCoverage.\n\n"
        "### Item 027: Bounds rules\nBounds.\n",
        encoding="utf-8")
    assert aide.main(["--repo", str(root), "claim", "--dry-run"]) == 0
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith("would claim item 028"), first


def test_none_left_reports_in_the_queues_own_order(tmp_path: Path, capsys):
    """The report follows `_pick_item`'s walk, not the item numbers.

    A queue is free to list its items out of numeric order, and under
    `claim_scope = "all-open"` the walk crosses queues in turn — sorting
    numerically would describe a scan that never happened.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    (root / "docs" / "aide" / "queue" / "queue-003.md").write_text(
        "# Demo — Work Queue 003\n\n"
        "> **Status:** Live · **Created:** 2026-07-01\n\n"
        "### Item 026: Rule engine core\nCore.\n\n"
        "### Item 028: Coverage rules\nCoverage.\n\n"
        "### Item 027: Bounds rules\nBounds.\n",
        encoding="utf-8")
    items = root / "docs" / "aide" / "items"
    for num, dep in ((27, 28), (28, 27)):
        (items / f"{num:03d}-x.md").write_text(
            f"# Item {num:03d} — X\n\n## Dependencies\n- Item {dep:03d}.\n\n## End\n",
            encoding="utf-8")
    assert aide.main(["--repo", str(root), "claim", "--dry-run"]) == 0
    reported = [line.split()[0] for line in capsys.readouterr().out.splitlines()
                if line.startswith("  0")]
    assert reported == ["028", "027"]


# --------------------------------------------------------------------------- #
# a merge retry resolves to the base the first run had (issue #167)
# --------------------------------------------------------------------------- #
def test_restore_puts_back_the_recorded_base_with_the_ref(tmp_path: Path):
    """`git branch -d` takes `branch.<claim>.aide-base` with the ref. Restoring
    the ref alone made the retry *run*; it made it run against main_branch."""
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    branch = _current_branch(root)
    tip = _run(["git", "rev-parse", branch], root).stdout.strip()
    base = aide._recorded_branch_base(root, branch)
    assert base == "aide/queue-003"
    _run(["git", "switch", "aide/queue-003"], root)
    _run(["git", "branch", "-D", branch], root)
    assert aide._recorded_branch_base(root, branch) is None

    aide._restore_claim_branch(root, branch, tip, base)
    assert branch in aide._local_branches(root)
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"
    assert aide.resolve_base(root, aide.load_config(root), None, branch) == "aide/queue-003"


def test_merge_refuses_a_claim_branch_with_no_recorded_base(tmp_path: Path, capsys):
    """Issue #174, half 2 — and the assertion this file used to make the other
    way round (it pinned the fallback being *named*, which was not enough).

    `claim` records a base for every branch it makes, so a claim branch with
    none has lost its record — the way an interrupted merge loses it, with the
    ref. `resolve_base` cannot tell that from a branch this machine never
    claimed; `merge` can, so it stops instead of resolving to `main_branch` and
    fast-forwarding a queue's work onto main.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt", base=None)
    assert aide._recorded_branch_base(root, "aide/027-bounds-rules") is None

    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 1
    captured = capsys.readouterr()
    assert "no base is recorded" in captured.err
    assert "--base" in captured.err
    # Refused means refused: nothing merged, and the branch is untouched.
    assert not (root / "feature.txt").is_file()
    assert "aide/027-bounds-rules" in aide._local_branches(root)


def test_merge_names_an_explicit_base_and_proceeds_without_a_record(tmp_path: Path,
                                                                   capsys):
    """`--base` is the override the refusal points at, so the legitimate
    first-merge-onto-main shape still lands — it just says where."""
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt", base=None)
    assert aide.main(["--repo", str(root), "merge", "27", "--base", "main",
                      "--no-test"]) == 0
    out = capsys.readouterr().out
    assert "item 027 lands on main (from --base)" in out
    assert (root / "feature.txt").is_file()


def test_merge_names_a_recorded_base_as_recorded(tmp_path: Path, capsys):
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    (root / "work.txt").write_text("work\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "work"], root)
    capsys.readouterr()
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 0
    out = capsys.readouterr().out
    assert "item 027 lands on aide/queue-003 (recorded for" in out
    assert _current_branch(root) == "aide/queue-003"


# --------------------------------------------------------------------------- #
# env: an interpreter to build from, and an OK that means it (issue #166)
# --------------------------------------------------------------------------- #
def _env_toml(test_command: str, import_check: str = "", interpreter: str = "") -> str:
    return (f'[python]\nvenv = ".venv"\ntest_command = "{test_command}"\n'
            f'import_check = "{import_check}"\ninterpreter = "{interpreter}"\n')


def _toml_path(path: str) -> str:
    return path.replace("\\", "\\\\")


@pytest.fixture(scope="module")
def bare_venv(tmp_path_factory) -> Path:
    """A real venv with nothing in it — the shape a bootstrap leaves when its
    `pip install` aborts after the editable project and before the closure.
    `--without-pip` so the fixture costs one interpreter start, not ensurepip."""
    root = tmp_path_factory.mktemp("venv-repo")
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(root / ".venv")],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return root


def test_the_test_runner_module_is_read_only_from_the_python_m_shape():
    assert aide._test_runner_module({"python": {"test_command": "python -m pytest -q"}}) == "pytest"
    assert aide._test_runner_module({"python": {"test_command": "pytest -q"}}) is None
    assert aide._test_runner_module({"python": {"test_command": "make test"}}) is None
    assert aide._test_runner_module({"python": {}}) == "pytest"


def test_a_venv_with_no_test_runner_cannot_report_ok(bare_venv: Path, capsys):
    """The observed false green: `import spinelab` succeeded, `pytest` was not
    installed, and the validator trusting OK failed on the environment with
    the failure attributed to its item."""
    (bare_venv / "aide.toml").write_text(_env_toml("python -m pytest"), encoding="utf-8")
    status, detail = aide.env_report(bare_venv, aide.load_config(bare_venv))
    assert status == "stale" and "pytest" in detail
    assert aide.main(["--repo", str(bare_venv), "env"]) == 1
    assert "pytest" in capsys.readouterr().out


def test_a_stdlib_runner_in_a_bare_venv_is_ok(bare_venv: Path, capsys):
    (bare_venv / "aide.toml").write_text(_env_toml("python -m unittest"), encoding="utf-8")
    assert aide.env_status(bare_venv, aide.load_config(bare_venv)) == "ok"
    assert aide.main(["--repo", str(bare_venv), "env"]) == 0
    assert "venv is Python" in capsys.readouterr().out


def test_a_failed_bootstrap_record_makes_the_venv_stale(bare_venv: Path):
    (bare_venv / "aide.toml").write_text(_env_toml("python -m unittest"), encoding="utf-8")
    record = bare_venv / ".venv" / aide._BOOTSTRAP_RECORD
    record.write_text('{"exit": 1}', encoding="utf-8")
    try:
        status, detail = aide.env_report(bare_venv, aide.load_config(bare_venv))
    finally:
        record.unlink()
    assert status == "stale" and "did not finish" in detail


def test_the_configured_interpreter_is_compared_with_the_venvs_version(
        bare_venv: Path, tmp_path: Path):
    same = _toml_path(sys.executable)
    (bare_venv / "aide.toml").write_text(
        _env_toml("python -m unittest", interpreter=same), encoding="utf-8")
    status, detail = aide.env_report(bare_venv, aide.load_config(bare_venv))
    assert status == "ok" and sys.executable in detail

    # An "interpreter" that answers with a version no venv has — a command
    # line, so the two paths must survive a split.
    if " " in sys.executable or " " in str(tmp_path):
        pytest.skip("a command-line interpreter value splits on whitespace")
    other = tmp_path / "other.py"
    other.write_text("print('9.9')\n", encoding="utf-8")
    (bare_venv / "aide.toml").write_text(
        _env_toml("python -m unittest", interpreter=f"{same} {_toml_path(str(other))}"),
        encoding="utf-8")
    status, detail = aide.env_report(bare_venv, aide.load_config(bare_venv))
    assert status == "stale" and "9.9" in detail and "rebuild" in detail


def test_an_interpreter_this_machine_cannot_run_is_reported_not_fatal(bare_venv: Path):
    (bare_venv / "aide.toml").write_text(
        _env_toml("python -m unittest", interpreter="no-such-python-zz"), encoding="utf-8")
    status, detail = aide.env_report(bare_venv, aide.load_config(bare_venv))
    assert status == "ok" and "no-such-python-zz" in detail


def test_bootstrap_with_an_interpreter_this_machine_lacks_is_a_sentence(tmp_path: Path, capsys):
    (tmp_path / "aide.toml").write_text(
        _env_toml("python -m unittest", interpreter="no-such-python-zz"), encoding="utf-8")
    assert aide.main(["--repo", str(tmp_path), "env", "--bootstrap"]) == 1
    err = capsys.readouterr().err
    assert "no-such-python-zz" in err and "Traceback" not in err
    assert not (tmp_path / ".venv").exists()


def test_an_interpreter_path_with_a_space_is_one_command(tmp_path: Path):
    """Windows's default install is under `Program Files`; a split there made
    a valid key "cannot be run". A value naming an existing file is the whole
    command; anything else is a command line."""
    home = tmp_path / "My Python"
    home.mkdir()
    exe = home / ("python.exe" if os.name == "nt" else "python3")
    exe.write_text("", encoding="utf-8")
    assert aide._configured_interpreter({"python": {"interpreter": str(exe)}}) == [str(exe)]
    assert aide._configured_interpreter({"python": {"interpreter": "py -3.12"}}) == ["py", "-3.12"]
    quoted = f'"{exe}" -X utf8'
    assert aide._configured_interpreter({"python": {"interpreter": quoted}}) == [str(exe), "-X", "utf8"]
    assert aide._configured_interpreter({"python": {"interpreter": ""}}) == [sys.executable]


def test_a_merge_killed_mid_suite_puts_the_branch_and_its_base_back(
        tmp_path: Path, monkeypatch, capsys):
    """Issue #174, half 1 — the exit #167 could not see.

    `_restore_claim_branch` was called from exactly the two clean failure
    returns, so a run KILLED between the branch delete and the push restored
    nothing: the item was merged into its base, the branch was gone, and the
    next run's `resolve_base` fell back to main_branch. The post-merge suite is
    the long pole in that window, which is where Ctrl-C, a CI timeout and a
    runner's wall clock all land.

    The interrupt is aimed at the test command alone — `git` goes through the
    same `subprocess.run`, and stubbing it wholesale would kill the run before
    it ever deleted the branch, which is the state this is about.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    branch = _current_branch(root)
    (root / "work.txt").write_text("work\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "work"], root)
    _run(["git", "switch", "aide/queue-003"], root)
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"

    real_run = aide.subprocess.run
    test_cmd = aide.resolve_test_command(root, aide.load_config(root))

    def _killed_mid_suite(cmd, *a, **kw):
        # A prefix: under pytest the merge appends its report options (#275).
        if list(cmd)[:len(test_cmd)] == list(test_cmd):
            raise KeyboardInterrupt
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(aide.subprocess, "run", _killed_mid_suite)
    with pytest.raises(KeyboardInterrupt):
        aide.main(["--repo", str(root), "merge", "27"])

    assert branch in aide._local_branches(root)
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"
    # The whole point of recording it: the re-run lands where this run did.
    assert aide.resolve_base(root, aide.load_config(root), None, branch) == "aide/queue-003"
    assert "interrupted" in capsys.readouterr().err


def test_a_failure_in_the_window_restores_but_is_not_called_an_interrupt(
        tmp_path: Path, monkeypatch, capsys):
    """The restore is owed to any exception; the word "interrupted" is not.

    A test command that is not on PATH raises `FileNotFoundError` right here.
    Reporting that as an interrupt would send a human hunting for a signal
    nobody sent — the failure class the `--no-commit` message was fixed for in
    issue #133.
    """
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    branch = _current_branch(root)
    (root / "work.txt").write_text("work\n", encoding="utf-8")
    _run(["git", "add", "-A"], root)
    _run(["git", "commit", "-m", "work"], root)
    _run(["git", "switch", "aide/queue-003"], root)

    real_run = aide.subprocess.run
    test_cmd = aide.resolve_test_command(root, aide.load_config(root))

    def _no_such_command(cmd, *a, **kw):
        if list(cmd)[:len(test_cmd)] == list(test_cmd):
            raise FileNotFoundError(2, "No such file or directory", cmd[0])
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(aide.subprocess, "run", _no_such_command)
    with pytest.raises(FileNotFoundError):
        aide.main(["--repo", str(root), "merge", "27"])

    assert branch in aide._local_branches(root)
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"
    err = capsys.readouterr().err
    assert "FileNotFoundError" in err and "interrupted" not in err


def test_the_restore_window_ends_at_the_push_not_at_the_return(tmp_path: Path):
    """A merge that got all the way through must NOT get its branch back.

    The `except` arm covers the window; putting the branch back after the work
    has left the repository would leave a stale claim branch behind a ✅ item —
    the state deleting it before the tests exists to avoid (issue #125).
    """
    root = _init_repo(tmp_path / "r", mode="local")
    _make_item_branch(root, "aide/027-bounds-rules", "feature.txt")
    assert aide.main(["--repo", str(root), "merge", "27", "--no-test"]) == 0
    assert "aide/027-bounds-rules" not in aide._local_branches(root)


@pytest.mark.skipif(os.name == "nt", reason="POSIX signal delivery")
def test_a_terminating_signal_unwinds_instead_of_ending_the_process(tmp_path: Path):
    """SIGTERM is how the unattended cases in #174 arrive, and Python's default
    handler ends the process where it stands — no `finally`, no `except`. The
    context manager is what gives the restore above a stack to unwind."""
    import signal

    original = signal.getsignal(signal.SIGTERM)
    with aide._restore_on_signal():
        # Asserted BEFORE the signal is sent, deliberately: were the handler
        # not installed, the SIGTERM below would end the pytest process rather
        # than fail this test.
        assert signal.getsignal(signal.SIGTERM) is not original
        with pytest.raises(aide._Terminated):
            os.kill(os.getpid(), signal.SIGTERM)
    # And handed back, so nothing outside the merge window inherits it.
    assert signal.getsignal(signal.SIGTERM) is original


def test_restore_records_the_base_the_run_merged_into_not_the_old_record(tmp_path: Path):
    """A run given `--base` landed where the record did not say; its retry
    must land there again, and a `branch -d` that refused leaves the stale
    record in place to be corrected, not kept."""
    root = _init_repo(tmp_path / "r", mode="local")
    assert aide.main(["--repo", str(root), "queue", "start", "3"]) == 0
    assert aide.main(["--repo", str(root), "claim", "--queue", "3"]) == 0
    branch = _current_branch(root)
    tip = _run(["git", "rev-parse", branch], root).stdout.strip()
    assert aide._recorded_branch_base(root, branch) == "aide/queue-003"

    aide._restore_claim_branch(root, branch, tip, "main")      # branch still exists
    assert aide._recorded_branch_base(root, branch) == "main"
    assert aide.resolve_base(root, aide.load_config(root), None, branch) == "main"
