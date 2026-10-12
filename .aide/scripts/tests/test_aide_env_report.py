"""`aide env`'s dependency report, and the half of it `aide check` errors on
(issue #354).

Nothing reported whether this machine could run what a project's
configuration asks for, so a missing requirement was found mid-run by
whichever verb met it first — worst, `auto-merge` with no `origin`: `merge`
did all of its local work, ticked ✅, then failed at the push on every retry.
These tests drive `main()` in-process over scratch repositories, and never
the forge: `_gh` is replaced wherever the configuration would ask it, so a
machine with a real `gh` neither waits on the network nor changes a verdict.
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
_spec = importlib.util.spec_from_file_location("aide_cli_env_report", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]

PYTHON = Path(sys.executable).as_posix()


def _git(args, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _repo(tmp_path: Path, *, mode: str = "local", origin: bool = False,
          test_command: str = "git --version", venv: str = "",
          gh: Optional[str] = None, python: str = PYTHON,
          init: bool = True) -> Path:
    """A repository whose every requirement is met unless a keyword says
    otherwise: `local`, no venv kept, a test command that is git, and the
    running interpreter as the one the engine prints."""
    repo = tmp_path / "repo"
    repo.mkdir()
    if init:
        _git(["init", "-q"], repo)
    if origin:
        # `git remote get-url` reads config: the URL need not answer.
        _git(["remote", "add", "origin", (tmp_path / "origin.git").as_posix()],
             repo)
    (repo / "aide.toml").write_text(
        f'[python]\ntest_command = "{test_command}"\nvenv = "{venv}"\n'
        f'[git]\nmode = "{mode}"\n', encoding="utf-8")
    (repo / ".aide").mkdir()
    tools = f"[tools]\npython = '{python}'\n"
    if gh is not None:
        tools += f"gh = '{gh}'\n"
    (repo / ".aide" / "local.toml").write_text(tools, encoding="utf-8")
    return repo


@pytest.fixture
def logged_in(monkeypatch):
    """A forge that confirms a login, and records that it was asked."""
    asked = []

    def gh(repo_root, args):
        asked.append(args)
        return "", None
    monkeypatch.setattr(aide, "_gh", gh)
    return asked


def _env(repo: Path, capsys) -> tuple:
    capsys.readouterr()
    code = aide.main(["--repo", str(repo), "env"])
    return code, capsys.readouterr().out


ORIGIN_REFUSAL = ('[git] mode = "auto-merge" in aide.toml needs a remote named '
                  'origin — add one')


# --------------------------------------------------------------------------- #
# env — origin and gh are needed under every mode but local
# --------------------------------------------------------------------------- #
def test_auto_merge_with_no_origin_is_refused_naming_the_setting(
        tmp_path: Path, capsys, logged_in):
    repo = _repo(tmp_path, mode="auto-merge", gh=PYTHON)
    code, out = _env(repo, capsys)
    assert code == 1
    assert f"aide env: {ORIGIN_REFUSAL}" in out
    assert 'or set [git] mode = "local"' in out
    assert "aide env: FAIL" in out


def test_local_needs_no_origin_and_never_asks_the_forge(
        tmp_path: Path, capsys, logged_in):
    repo = _repo(tmp_path, mode="local")
    code, out = _env(repo, capsys)
    assert code == 0, out
    assert "aide env: OK (no venv)" in out
    assert 'not needed under [git] mode = "local"' in out
    assert logged_in == []


def test_every_requirement_met_under_pr_exits_zero(
        tmp_path: Path, capsys, logged_in):
    repo = _repo(tmp_path, mode="pr", origin=True, gh=PYTHON)
    code, out = _env(repo, capsys)
    assert code == 0, out
    assert logged_in == [["auth", "status"]]
    assert "logged in" in out


@pytest.mark.parametrize("mode", ["pr", "auto-merge"])
def test_a_pushing_mode_without_gh_is_refused(tmp_path: Path, capsys,
                                              monkeypatch, mode: str):
    """Unless `[git] forge = "none"` declares no forge (#355), every mode
    but `local` asks for gh — `auto-merge` too, whose queue end opens a PR."""
    repo = _repo(tmp_path, mode=mode, origin=True)
    monkeypatch.setattr(aide, "resolve_tool", lambda name, root: (
        None if name == "gh" else _real_resolve(name, root)))
    code, out = _env(repo, capsys)
    assert code == 1
    assert (f'aide env: [git] mode = "{mode}" in aide.toml needs gh, which '
            f"opens and reads the queue's pull request") in out


_real_resolve = aide.resolve_tool


@pytest.mark.parametrize("mode", ["auto-merge", "local"])
def test_no_forge_needs_no_gh_and_leaves_its_line_out(
        tmp_path: Path, capsys, monkeypatch, logged_in, mode):
    """Issue #355: `auto-merge` pushing to a remote with no GitHub behind
    it — origin is still needed, gh is neither asked nor listed; under
    `local` the line is left out too, not listed as unneeded."""
    repo = _repo(tmp_path, mode=mode, origin=True)
    with (repo / "aide.toml").open("a", encoding="utf-8") as f:
        f.write('forge = "none"\n')
    monkeypatch.setattr(aide, "resolve_tool", lambda name, root: (
        None if name == "gh" else _real_resolve(name, root)))
    code, out = _env(repo, capsys)
    assert code == 0, out
    assert not any(line.split()[:1] == ["gh"] for line in out.splitlines())
    assert "needs gh" not in out
    assert logged_in == []


def test_a_gh_refusal_names_no_forge_as_a_way_out_except_under_pr(
        tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(aide, "resolve_tool", lambda name, root: (
        None if name == "gh" else _real_resolve(name, root)))
    (tmp_path / "a").mkdir()
    (tmp_path / "p").mkdir()
    auto = _repo(tmp_path / "a", mode="auto-merge", origin=True)
    assert 'or [git] forge = "none"' in _env(auto, capsys)[1]
    pr = _repo(tmp_path / "p", mode="pr", origin=True)
    assert "[git] forge" not in _env(pr, capsys)[1]


def test_pr_with_no_login_is_refused(tmp_path: Path, capsys, monkeypatch):
    repo = _repo(tmp_path, mode="pr", origin=True, gh=PYTHON)
    monkeypatch.setattr(aide, "_gh", lambda root, args: (None, "gh exited 1: "
                                                         "not logged in"))
    code, out = _env(repo, capsys)
    assert code == 1
    assert ('aide env: [git] mode = "pr" in aide.toml needs gh logged in'
            in out) and "gh auth login" in out


def test_a_repository_is_needed_always(tmp_path: Path, capsys):
    repo = _repo(tmp_path, init=False)
    code, out = _env(repo, capsys)
    assert code == 1
    assert f"aide env: {repo} is not inside a git repository" in out


def test_a_test_command_this_machine_lacks_is_refused(tmp_path: Path, capsys):
    repo = _repo(tmp_path, test_command="nosuchrunner-aide-354 --x")
    code, out = _env(repo, capsys)
    assert code == 1
    assert "aide env: the test command 'nosuchrunner-aide-354' is not on PATH" in out


def test_a_printed_interpreter_this_machine_lacks_is_a_note(
        tmp_path: Path, capsys, monkeypatch):
    """It decides only what a suggestion says, never what a verb runs (§4):
    a note, and `env` still exits 0."""
    repo = _repo(tmp_path, python="no-such-python-aide-354")
    monkeypatch.setattr(aide.shutil, "which", lambda name, *a, **k: (
        "/usr/bin/python3" if name == "python3" else _real_which(name, *a, **k)))
    code, out = _env(repo, capsys)
    assert code == 0, out
    assert ("aide env: note: the engine prints 'no-such-python-aide-354' in "
            "the commands it suggests") in out
    assert '[tools] python = "python3"' in out     # the machine has one
    assert sys.executable in out           # what the engine itself runs on


def test_with_no_python3_either_the_note_names_the_key(
        tmp_path: Path, capsys, monkeypatch):
    repo = _repo(tmp_path, python="no-such-python-aide-354")
    monkeypatch.setattr(aide.shutil, "which", lambda name, *a, **k: (
        None if name == "python3" else _real_which(name, *a, **k)))
    code, out = _env(repo, capsys)
    assert code == 0, out
    assert "put one on PATH, or name the interpreter to print" in out
    assert '"python3"' not in out


_real_which = aide.shutil.which


def test_the_git_line_names_the_merge_tree_features(tmp_path: Path, capsys,
                                                    monkeypatch):
    """Each feature against its own minimum: 2.39 has the first and not the
    second; 2.37 has neither; 2.40 has both."""
    repo = _repo(tmp_path)
    for version, write_tree, merge_base in (("2.39.1", "yes", "no"),
                                            ("2.37.0", "no", "no"),
                                            ("2.40.0", "yes", "yes")):
        monkeypatch.setattr(aide, "_version_text", lambda root, v=version: v)
        code, out = _env(repo, capsys)
        assert code == 0, out
        assert f", {version} — " in out
        assert f"merge-tree --write-tree (gc's landed check), 2.38+: {write_tree}" in out
        assert (f"merge-tree --merge-base (queue restack past a squash), "
                f"2.40+: {merge_base}") in out


# --------------------------------------------------------------------------- #
# venv = "" — a project that keeps no venv
# --------------------------------------------------------------------------- #
def test_an_empty_venv_setting_leaves_the_venv_line_out(tmp_path: Path, capsys):
    code, out = _env(_repo(tmp_path, venv=""), capsys)
    assert code == 0, out
    assert "  venv " not in out


def test_a_kept_venv_that_is_missing_is_refused(tmp_path: Path, capsys):
    repo = _repo(tmp_path, venv=".venv")
    code, out = _env(repo, capsys)
    assert code == 1
    assert "aide env: the venv is missing" in out
    assert '[python] venv = "" in aide.toml for a project with no venv' in out


def test_bootstrap_refuses_when_no_venv_is_kept(tmp_path: Path, capsys):
    repo = _repo(tmp_path, venv="")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "env", "--bootstrap"]) == 1
    assert 'aide env: [python] venv = "" in aide.toml' in capsys.readouterr().err
    assert not (repo / "bin").exists() and not (repo / "Scripts").exists()


def test_bootstrap_answers_for_the_venv_alone(tmp_path: Path, capsys,
                                              monkeypatch):
    """The validator bootstraps to get a suite runner: a requirement it does
    not need for that — here `origin` — must not read as a failed build."""
    repo = _repo(tmp_path, mode="auto-merge", venv=".venv")
    monkeypatch.setattr(aide, "_gh", lambda root, args: (None, "not asked here"))
    monkeypatch.setattr(aide, "env_report", lambda root, config: ("ok", "stub"))
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "env", "--bootstrap"]) == 0
    assert "aide env: OK (stub)" in capsys.readouterr().out
    assert aide.main(["--repo", str(repo), "env"]) == 1


def test_no_venv_kept_leaves_a_leading_python_unbound(tmp_path: Path):
    """`venv = ""` would otherwise name the repo root itself as the venv."""
    repo = _repo(tmp_path, venv="", test_command="python -m pytest")
    config = aide.load_config(repo)
    assert aide.resolve_test_command(repo, config)[0] == "python"


# --------------------------------------------------------------------------- #
# check — the offline half, as errors
# --------------------------------------------------------------------------- #
def test_check_errors_on_auto_merge_with_no_origin(tmp_path: Path, capsys):
    repo = _repo(tmp_path, mode="auto-merge")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 1
    assert f"error: this machine: {ORIGIN_REFUSAL}" in capsys.readouterr().out


def test_check_errors_outside_a_repository_and_on_a_missing_runner(
        tmp_path: Path, capsys):
    repo = _repo(tmp_path, init=False, test_command="nosuchrunner-aide-354")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 1
    out = capsys.readouterr().out
    assert f"error: this machine: {repo} is not inside a git repository" in out
    assert ("error: this machine: the test command 'nosuchrunner-aide-354' is "
            "not on PATH") in out


def test_check_leaves_gh_the_interpreter_and_the_venv_to_env(
        tmp_path: Path, capsys, monkeypatch):
    """No gh, an interpreter the machine lacks, a venv never built: all
    `env`'s to report, none an error of the check — and the forge is never
    asked."""
    repo = _repo(tmp_path, mode="pr", origin=True, venv=".venv",
                 python="no-such-python-aide-354")
    monkeypatch.setattr(aide, "_gh", lambda root, args: pytest.fail(
        "the check asked the forge"))
    monkeypatch.setattr(aide, "resolve_tool", lambda name, root: (
        None if name == "gh" else _real_resolve(name, root)))
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert "error:" not in capsys.readouterr().out


def test_check_without_an_aide_toml_judges_no_machine(tmp_path: Path, capsys):
    """A repo with no AIDE configuration gets the lints, and no error about
    defaults nobody committed."""
    repo = tmp_path / "repo"
    repo.mkdir()
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert "error:" not in capsys.readouterr().out


PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 📋 |

## Stage 1 — Rules — 📋

**Deliverables.**
- 📋 A. *(Item 027)*

**Acceptance.**
- [ ] Rules fire.
"""


def test_check_queue_never_fails_on_the_machine(tmp_path: Path, capsys):
    """`--queue` is a planner's or reviewer's judgement of documents: a
    machine error there would invite the `[git] mode` edit §4 forbids."""
    repo = _repo(tmp_path, mode="auto-merge")
    d = repo / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir()
    (d / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(
        "# Demo — Work Queue 003\n\n### Item 027: Thing\nDoes a thing.\n",
        encoding="utf-8")
    (d / "items" / "027-thing.md").write_text(
        "# Item 027 — Demo\n\n## Authorised paths\n\n**May change:**\n\n"
        "- `src/a.py` — work\n\n## Dependencies\n\nNone.\n", encoding="utf-8")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check", "--queue", "3"]) == 0, (
        capsys.readouterr().out)
    assert "this machine:" not in capsys.readouterr().out
    assert aide.main(["--repo", str(repo), "check"]) == 1      # plain: it is
    assert f"error: this machine: {ORIGIN_REFUSAL}" in capsys.readouterr().out


def test_check_under_local_with_no_origin_passes(tmp_path: Path, capsys):
    """Nothing stubbed: `local` needs no origin, so a machine without one
    meets it."""
    repo = _repo(tmp_path, mode="local")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert "error:" not in capsys.readouterr().out


def test_a_runner_path_that_is_not_executable_says_so(tmp_path: Path):
    repo = tmp_path / "r"
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "run").write_text("not a program\n", encoding="utf-8")
    assert "'tools/run' is not an executable file" in str(
        aide.RunnerMissing("tools/run", repo))
    assert "'tools/gone' does not exist" in str(
        aide.RunnerMissing("tools/gone", repo))


@pytest.mark.skipif(os.name == "nt", reason="an execute bit is POSIX")
def test_test_names_a_runner_file_with_no_execute_bit(tmp_path: Path, capsys):
    """Running it is a PermissionError, which ended `aide test` in a
    traceback; now the sentence `aide env` and `check` use."""
    repo = _repo(tmp_path, test_command="tools/run")
    (repo / "tools").mkdir()
    (repo / "tools" / "run").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "test"]) == 1
    err = capsys.readouterr().err
    assert "aide test: the test command 'tools/run' is not an executable file" in err
    assert "Traceback" not in err


def test_test_spawns_the_program_resolve_tool_found(tmp_path: Path, capsys,
                                                    monkeypatch):
    """The suite runs the path `aide env` reports, not the bare name: on
    Windows a list argv is searched for with `.exe` alone, so an `npm.cmd`
    shim was a `FileNotFoundError` for a program found (issue #449)."""
    repo = _repo(tmp_path, test_command="shimmed --flag")
    shim = str(tmp_path / "bin" / "shimmed.cmd")
    real_resolve = aide.resolve_tool
    monkeypatch.setattr(aide, "resolve_tool", lambda name, root, path=None: (
        shim if name == "shimmed" else real_resolve(name, root, path)))
    spawned = []
    real_run = subprocess.run

    def run(args, *a, **kw):
        if args and args[0] in (shim, "shimmed"):
            spawned.append(list(args))
            return subprocess.CompletedProcess(args, 0)
        return real_run(args, *a, **kw)
    monkeypatch.setattr(aide.subprocess, "run", run)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "test"]) == 0
    assert spawned and spawned[0][:2] == [shim, "--flag"]


@pytest.mark.skipif(os.name != "nt", reason="a .cmd shim is Windows")
def test_test_runs_a_cmd_shim_on_path(tmp_path: Path, capsys, monkeypatch):
    """The reported case itself: a test command whose program is a `.cmd`
    file found through PATHEXT, as `npm` is (issue #449)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "shimmed-aide-449.cmd").write_text("@exit /b 0\r\n",
                                                  encoding="utf-8")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    repo = _repo(tmp_path, test_command="shimmed-aide-449")
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "test"]) == 0
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.skipif(os.name == "nt", reason="an exec format error is POSIX")
def test_test_names_a_found_runner_that_cannot_start(tmp_path: Path, capsys):
    """Found, executable, and not a program the kernel can start: one
    sentence naming where it was found, where a traceback was (issue #449)."""
    repo = _repo(tmp_path, test_command="tools/run")
    (repo / "tools").mkdir()
    run = repo / "tools" / "run"
    run.write_bytes(b"\x00\x01not a program\n")
    run.chmod(0o755)
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "test"]) == 1
    err = capsys.readouterr().err
    assert (f"aide test: the test command 'tools/run' was found at {run} "
            "and cannot be run (") in err
    assert "fix [python] test_command in aide.toml" in err
    assert "Traceback" not in err
