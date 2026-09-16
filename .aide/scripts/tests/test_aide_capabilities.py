"""Issue #207: the Environment-Gated Capability Verification table has a reader.

§1 → environment-gated capabilities stated rules about the table that no tool
checked. It now has two readers, both surfacing state and neither gating
anything: `aide status` lists every row not yet ✅ Verified with the
`[validation]` profile the row names — evaluated only under `--profiles`, and
only for a ❓ Unverified row — and `aide check` warns, never errors, on the
rows. The status tests drive the verb through `main`, the path a consumer
runs; the last two hold `evaluate_profile` to its timeout and to an
interpreter that cannot start.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_capabilities", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


ROW = "| GPU path | `torch` (`gpu` profile) | Stage 1 *(Item 002)* | ❓ Unverified | — |"


def _progress(*rows: str, stage_one: str = "✅") -> str:
    body = "\n".join(rows)
    return f"""\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | {stage_one} |
| 2 | Models | G1 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1 | 🚧 |

## Environment-Gated Capability Verification

| Capability | Package / Tool | Introduced by | Status | Notes |
|------------|-----------------|----------------|--------|-------|
{body}

## Stage 1 — Rules — {stage_one}

**Deliverables.**
- {stage_one} Core. *(Item 002)*

**Acceptance.**
- [ ] Rules fire.

## Stage 2 — Models — 📋

**Deliverables.**
- 📋 Model. *(Item 003)*

**Acceptance.**
- [ ] It trains.
"""


def _repo(tmp_path: Path, progress: str, validation: str = 'gpu = "True"') -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "aide.toml").write_text(
        '[project]\nname = "Demo"\ndocs_dir = "docs/aide"\n\n'
        f"[validation]\n{validation}\n", encoding="utf-8")
    d = tmp_path / "docs" / "aide"
    d.mkdir(parents=True)
    (d / "progress.md").write_text(progress, encoding="utf-8")
    (d / "insights.md").write_text("# Insight Inbox\n", encoding="utf-8")
    return tmp_path


def _check(tmp_path: Path, progress: str, validation: str = 'gpu = "True"'):
    repo = _repo(tmp_path, progress, validation)
    return aide.run_checks(repo, aide.load_config(repo), branches=[])


# --------------------------------------------------------------------------- #
# the reader
# --------------------------------------------------------------------------- #
def test_a_row_is_read_with_its_profile_stages_status_and_notes():
    [c] = aide.gated_capabilities(_progress(ROW).splitlines())
    assert (c.text, c.profiles, c.stages, c.kind, c.noted) == (
        "GPU path", ["gpu"], [1], "unverified", False)


@pytest.mark.parametrize("cell, profiles", [
    ("`torch` with a visible GPU (`gpu` profile)", ["gpu"]),
    ("weights tree (profile `weights`)", ["weights"]),
    ("`spineps` @ `60cc736`, `TPTBox` @ `e71e3e2` (`spineps` profile)", ["spineps"]),
    ("`cupy` (extra: `segqc[gpu]`)", []),  # a backticked extra is not a profile
    ("`a` profile, `b` profile, `a` profile", ["a", "b"]),
])
def test_the_profile_link_is_read_from_the_package_cell(cell, profiles):
    row = f"| Cap | {cell} | Stage 1 | ❓ Unverified | — |"
    [c] = aide.gated_capabilities(_progress(row).splitlines())
    assert c.profiles == profiles


@pytest.mark.parametrize("cell, stages", [
    ("Stage 3 / 4", [3, 4]),
    ("Stage 6*(Items 044, 045)*; closed by Stage 12 *(Item 084)*", [6]),
    ("Stages 5, 7*(Items 041, 053, 057)*; to be closed by Stage 16", [5, 7]),
    ("Stage 17 (Item 097)", [17]),
    ("Stages 2–4", [2, 3, 4]),
    ("Item 002", []),
])
def test_the_introducing_stages_are_the_first_stage_run(cell, stages):
    """The shapes both local consumers write: a later "closed by Stage N"
    names a different stage, and item numbers are never stages."""
    row = f"| Cap | tool | {cell} | ❓ Unverified | — |"
    [c] = aide.gated_capabilities(_progress(row).splitlines())
    assert c.stages == stages


# --------------------------------------------------------------------------- #
# aide check — warnings, and never an error
# --------------------------------------------------------------------------- #
def test_a_mis_shaped_capability_row_is_a_warning_not_an_error(tmp_path: Path):
    """Unlike the four tables #202 made errors: this one gates nothing, so a
    dropped row carries no over-claim away."""
    broken = "| GPU | torch | Stage 1 | ❓ Unverified | a | b |"
    doc = _progress(broken)
    errors, warnings = _check(tmp_path, doc)
    lineno = doc.splitlines().index(broken) + 1
    assert not any("capability row" in e for e in errors), errors
    assert any(w.startswith(f"progress.md:{lineno}: capability row has 6 cells, not 5")
               for w in warnings), warnings
    assert aide.unreadable_row_errors(doc.splitlines()) == []


def test_an_empty_capability_cell_is_an_unusable_row():
    doc = _progress("|  | torch | Stage 1 | ❓ Unverified | why |")
    [w] = aide.unreadable_row_warnings(doc.splitlines())
    assert "capability row has an empty Capability cell" in w
    assert "usual cause" not in w
    assert aide.gated_capabilities(doc.splitlines()) == []


def test_an_unrecognised_capability_status_is_a_warning(tmp_path: Path):
    errors, warnings = _check(
        tmp_path, _progress(ROW.replace("❓ Unverified", "⏸️ Out of scope")))
    assert not errors, errors
    assert any("capability 'GPU path' has an unrecognised Status" in w
               for w in warnings), warnings


def test_an_undefined_profile_is_a_warning(tmp_path: Path):
    errors, warnings = _check(tmp_path, _progress(ROW), validation='cpu = "True"')
    assert not errors, errors
    assert any("names profile 'gpu', which [validation] in aide.toml does not "
               "define" in w for w in warnings), warnings


def test_a_closed_stage_row_with_no_reason_is_a_warning(tmp_path: Path):
    errors, warnings = _check(tmp_path, _progress(ROW))
    assert not errors, errors
    assert any("capability 'GPU path' is still ❓ Unverified under stage 1, which "
               "is ✅, and its Notes cell records no reason" in w
               for w in warnings), warnings


@pytest.mark.parametrize("change", [
    dict(row=ROW.replace("| — |", "| gpu profile unsatisfied on the build host |")),
    dict(row=ROW, stage_one="🚧"),
    dict(row=ROW.replace("❓ Unverified", "✅ Verified (2026-09-01, CI)")),
    dict(row=ROW.replace("Stage 1", "Stage 2")),
])
def test_a_reason_an_open_stage_or_a_verified_row_is_not_that_warning(
        tmp_path: Path, change):
    doc = _progress(change["row"], stage_one=change.get("stage_one", "✅"))
    _, warnings = _check(tmp_path, doc)
    assert not any("records no reason" in w for w in warnings), warnings


# --------------------------------------------------------------------------- #
# aide status — every row not yet verified; profiles only with --profiles
# --------------------------------------------------------------------------- #
STATUS_ROWS = (
    ROW,
    "| Weights | tree (`weights` profile) | Stage 2 | ❓ Unverified | unset |",
    "| Docker | docker (`docker` profile) | Stage 2 | ⏸️ Out of scope | — |",
    "| Excluded | tool (`gpu` profile) | Stage 2 | ⏸️ Out of scope | — |",
    "| Radiomics | `pyradiomics` (`gpu` profile) | Stage 1 | ✅ Verified (2026-09-01, CI) | — |",
)


def _status(tmp_path: Path, capsys, *flags: str) -> str:
    repo = _repo(tmp_path, _progress(*STATUS_ROWS),
                 validation='gpu = "True"\nweights = "False"')
    assert aide.main(["--repo", str(repo), "status", "--no-fetch", *flags]) == 0
    return capsys.readouterr().out


def test_status_lists_unverified_capabilities_without_evaluating_profiles(
        tmp_path: Path, monkeypatch, capsys):
    """A profile is project code that may import a GPU stack; `status` is the
    loop's resume check, so it names the profile and runs nothing."""
    monkeypatch.setattr(aide, "evaluate_profile",
                        lambda *a, **k: pytest.fail("evaluated without --profiles"))
    out = _status(tmp_path, capsys)
    assert "capability: GPU path [stage 1] — ❓ unverified; profile 'gpu'\n" in out
    assert "capability: Weights [stage 2] — ❓ unverified; profile 'weights'\n" in out
    assert ("capability: Docker [stage 2] — ⚠ unrecognised status; profile "
            "'docker' is not defined in [validation]") in out
    assert "Radiomics" not in out


def test_status_profiles_evaluates_the_profiles_of_unverified_rows(
        tmp_path: Path, capsys):
    out = _status(tmp_path, capsys, "--profiles")
    assert ("capability: GPU path [stage 1] — ❓ unverified; profile 'gpu' is "
            "satisfied here — the gated path can be run and the row verified") in out
    assert ("capability: Weights [stage 2] — ❓ unverified; profile 'weights' is "
            "not satisfied here") in out
    # An Out of scope row is not one to be told it can be verified now.
    assert "capability: Excluded [stage 2] — ⚠ unrecognised status; profile 'gpu'\n" in out
    assert "Radiomics" not in out


def test_status_evaluates_each_profile_once(tmp_path: Path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(aide, "evaluate_profile",
                        lambda root, config, expr: calls.append(expr) or (True, ""))
    rows = (ROW, ROW.replace("GPU path", "GPU training"))
    repo = _repo(tmp_path, _progress(*rows))
    assert aide.main(["--repo", str(repo), "status", "--no-fetch", "--profiles"]) == 0
    assert calls == ["True"]
    assert capsys.readouterr().out.count("profile 'gpu' is satisfied here") == 2


# --------------------------------------------------------------------------- #
# evaluate_profile — the expression, bounded, and never a pass by accident
# --------------------------------------------------------------------------- #
def test_a_profile_that_outlives_its_timeout_is_not_satisfied(tmp_path: Path):
    repo = _repo(tmp_path, _progress(ROW))
    satisfied, detail = aide.evaluate_profile(
        repo, aide.load_config(repo), "__import__('time').sleep(30)", timeout=0.5)
    assert (satisfied, detail) == (False, "timed out after 0.5s")


def test_a_profile_whose_interpreter_cannot_start_is_not_satisfied(
        tmp_path: Path, monkeypatch):
    """A venv interpreter that exists but cannot be executed — a stale tree,
    a non-executable file — reports, rather than crashing `status`."""
    repo = _repo(tmp_path, _progress(ROW))
    broken = tmp_path / "not-an-interpreter.txt"
    broken.write_text("not a program\n", encoding="utf-8")
    monkeypatch.setattr(aide, "venv_python", lambda root, config: broken)
    satisfied, detail = aide.evaluate_profile(repo, aide.load_config(repo), "True")
    assert satisfied is False
    assert detail.startswith("interpreter ") and "cannot be run" in detail
