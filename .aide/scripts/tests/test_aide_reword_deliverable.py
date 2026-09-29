"""Rewording a deliverable bullet's prose — `aide progress reword --item NNN`.

Issue #320: `aide check` reports the residue of the multi-item bullet split
(#131, #169) — two single-item bullets in one stage with identical prose — and
asks for each copy to be reworded, but no verb changed a bullet's words:
`reword` took an acceptance criterion only, and refuses over a ticked box. The
one repair was a hand edit of progress.md, which every role is steered away
from. The bullet form finds the bullet the way every progress verb does, by
its trailing marker, and rewrites the prose between icon and marker — over a
✅ bullet too, since a deliverable bullet carries no attestation and the ✅
copy is the one whose words lie.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_reword_deliverable", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


#: The issue's fixture: the shape a split of `*(Items 041, 042)*` leaves once
#: 041 has merged.
SPLIT = """\
## Stage 3 — Adapters — 🚧

**Deliverables.**
- ✅ Adapters for two datasets. *(Item 041)*
- 📋 Adapters for two datasets. *(Item 042)*

**Acceptance.**
- [ ] Both datasets load.
"""


# --------------------------------------------------------------------------- #
# the rewrite
# --------------------------------------------------------------------------- #
def test_a_done_bullet_is_reworded_and_keeps_its_icon_and_marker():
    """The ✅ copy is the one the criterion form's refusal would have left
    lying — so it is the one case the bullet form must not refuse."""
    out, old, line = aide.reword_deliverable(SPLIT, 41, "The first dataset's adapter.")
    assert old == "Adapters for two datasets."
    assert line == 4
    lines = out.splitlines()
    assert lines[3] == "- ✅ The first dataset's adapter. *(Item 041)*"
    assert lines[4] == "- 📋 Adapters for two datasets. *(Item 042)*"
    # Status is untouched, so nothing rolls up differently.
    assert aide._parse_item_status(lines)[2] == aide._parse_item_status(
        SPLIT.splitlines())[2]


def test_a_planned_bullet_is_reworded_and_its_twin_left_alone():
    out, _, line = aide.reword_deliverable(SPLIT, 42, "The second dataset's adapter.")
    assert line == 5
    lines = out.splitlines()
    assert lines[3] == "- ✅ Adapters for two datasets. *(Item 041)*"
    assert lines[4] == "- 📋 The second dataset's adapter. *(Item 042)*"
    assert out.endswith("\n")


def test_rewording_both_copies_clears_the_identical_prose_warning():
    assert aide.identical_deliverable_warnings(SPLIT.splitlines())
    out, _, _ = aide.reword_deliverable(SPLIT, 41, "The first dataset's adapter.")
    assert aide.identical_deliverable_warnings(out.splitlines()) == []


def test_the_warning_names_the_verb_that_clears_it():
    warning, = aide.identical_deliverable_warnings(SPLIT.splitlines())
    assert "aide progress reword --item NNN" in warning


def test_a_wrapped_bullet_is_written_back_on_one_line():
    """The prose spans every wrapped line up to the marker on the last one;
    the new prose replaces all of it, on the bullet's first line."""
    text = ("## Stage 1 — X — 📋\n"
            "- 📋 A sentence long enough that the author\n"
            "  wrapped it onto a second line and\n"
            "  a third. *(Item 007)*.\n"
            "- 📋 Next. *(Item 008)*\n")
    out, old, _ = aide.reword_deliverable(text, 7, "Short now.")
    assert old == ("A sentence long enough that the author wrapped it onto a "
                   "second line and a third.")
    assert out.splitlines() == [
        "## Stage 1 — X — 📋",
        "- 📋 Short now. *(Item 007)*.",
        "- 📋 Next. *(Item 008)*"]


def test_lines_under_the_bullet_are_left_as_they_were():
    """A trail line and a sub-line are not part of the bullet's span, so the
    rewrite cannot reach them."""
    text = ("## Stage 1 — X — 📋\n"
            "- 📋 Old words\n"
            "  wrapped. *(Item 007)*\n"
            "  - **2026-09-01** → reopened: the operator run never happened\n"
            "  - a note an author hung under it\n"
            "- 📋 Next. *(Item 008)*\n")
    out, _, _ = aide.reword_deliverable(text, 7, "New words.")
    assert out.splitlines() == [
        "## Stage 1 — X — 📋",
        "- 📋 New words. *(Item 007)*",
        "  - **2026-09-01** → reopened: the operator run never happened",
        "  - a note an author hung under it",
        "- 📋 Next. *(Item 008)*"]
    assert aide.reopened_items(out.splitlines())[0].item == 7


def test_the_same_prose_is_no_change():
    out, old, _ = aide.reword_deliverable(SPLIT, 42, "  Adapters for two datasets.  ")
    assert out == SPLIT and old == "Adapters for two datasets."


def test_a_multi_codepoint_icon_is_kept_whole():
    text = "## Stage 1 — X — ⏸️\n- ⏸️ Later. *(Item 007)*\n"
    out, _, _ = aide.reword_deliverable(text, 7, "Much later.")
    assert out == "## Stage 1 — X — ⏸️\n- ⏸️ Much later. *(Item 007)*\n"


# --------------------------------------------------------------------------- #
# the refusals — each one leaves the caller nothing to write
# --------------------------------------------------------------------------- #
def test_an_item_no_bullet_names_is_refused():
    with pytest.raises(ValueError, match="nothing to reword"):
        aide.reword_deliverable(SPLIT, 99, "x")


def test_a_mid_prose_mention_is_not_the_items_bullet():
    """Suffix means suffix (#99): a bullet that merely names 043 in its prose
    is 041's, and rewording 043 finds nothing."""
    text = "## Stage 1 — X — 📋\n- 📋 Absorbs *(Item 043)*'s scope. *(Item 041)*\n"
    with pytest.raises(ValueError, match="nothing to reword"):
        aide.reword_deliverable(text, 43, "x")


def test_an_item_two_bullets_name_is_refused():
    text = ("## Stage 1 — X — 📋\n- 📋 One. *(Item 007)*\n"
            "- 📋 Two. *(Item 007)*\n")
    with pytest.raises(ValueError, match=r"2 deliverable bullets.*progress\.md:2, progress\.md:3"):
        aide.reword_deliverable(text, 7, "x")


def test_a_shared_marker_is_refused_and_says_what_to_do():
    """Its prose is one sentence for every item it names: rewording it for one
    would reword it for all, so the refusal points at the split instead."""
    text = "## Stage 1 — X — 📋\n- 📋 Adapters. *(Items 041, 042)*\n"
    with pytest.raises(ValueError) as exc:
        aide.reword_deliverable(text, 42, "The second adapter.")
    message = str(exc.value)
    assert "shared marker *(Items 041, 042)*" in message
    assert "aide progress set" in message


@pytest.mark.parametrize("new_text, why", [
    ("", "empty"),
    ("   ", "empty"),
    ("one\ntwo", "line break"),
    ("✅ Done already.", "status icon"),
    ("⏸️ Later.", "status icon"),
    ("Adapters. *(Item 043)*", "item reference"),
    ("Adapters. *(Items 043, 044)*.", "item reference"),
])
def test_text_that_would_change_the_bullet_is_refused(new_text, why):
    with pytest.raises(ValueError, match=why):
        aide.reword_deliverable(SPLIT, 42, new_text)


# --------------------------------------------------------------------------- #
# the command — progress.md alone, and nothing at all on a refusal
# --------------------------------------------------------------------------- #
AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
"""

ROADMAP = """\
# R

## Stage 3 — Adapters

**Deliverables.**

- Adapters for two datasets.

**Validation / acceptance.**

- Both datasets load.
"""


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    ddir = repo / "docs" / "aide"
    ddir.mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (ddir / "progress.md").write_text(SPLIT, encoding="utf-8")
    (ddir / "roadmap.md").write_text(ROADMAP, encoding="utf-8")
    return repo


def _reword(repo: Path, *argv: str) -> int:
    return aide.main(["--repo", str(repo), "progress", "reword", *argv,
                      "--no-commit"])


def test_the_cli_writes_progress_alone_and_leaves_roadmap_alone(
        tmp_path: Path, capsys):
    """roadmap.md's deliverables carry no item marker — items are born after
    it — so there is no bullet of the item there to keep in step."""
    repo = _repo(tmp_path)
    ddir = repo / "docs" / "aide"
    assert _reword(repo, "--item", "042", "--text", "The second adapter.") == 0
    assert "- 📋 The second adapter. *(Item 042)*" in (
        ddir / "progress.md").read_text(encoding="utf-8")
    assert (ddir / "roadmap.md").read_text(encoding="utf-8") == ROADMAP
    assert "item 042: deliverable bullet reworded" in capsys.readouterr().out


def test_a_refusal_through_the_cli_writes_nothing(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    progress = repo / "docs" / "aide" / "progress.md"
    before = progress.read_bytes()
    assert _reword(repo, "--item", "099", "--text", "x") == 1
    assert "NOT changed" in capsys.readouterr().err
    assert progress.read_bytes() == before


@pytest.mark.parametrize("argv", [
    ("3", "--item", "042", "--text", "x"),          # a STAGE as well
    ("--item", "042"),                              # no --text
    ("--item", "042", "--text", "  "),              # an empty --text
    ("--item", "042", "--all", "--text", "x"),      # --all is never offered
])
def test_the_bullet_form_refuses_a_malformed_call_with_usage(tmp_path: Path, argv):
    repo = _repo(tmp_path)
    progress = repo / "docs" / "aide" / "progress.md"
    before = progress.read_bytes()
    assert _reword(repo, *argv) == 2
    assert progress.read_bytes() == before


def test_all_on_the_bullet_form_is_refused_in_its_own_words(tmp_path: Path, capsys):
    """`--all` beside `--item` names bullets, not criteria — the call named none."""
    repo = _repo(tmp_path)
    assert _reword(repo, "--item", "042", "--all", "--text", "x") == 2
    err = capsys.readouterr().err
    assert "one item at a time" in err and "criteria" not in err


def test_the_two_forms_are_mutually_exclusive(tmp_path: Path, capsys):
    repo = _repo(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _reword(repo, "3", "--criterion", "1", "--item", "042", "--text", "x")
    assert exc.value.code == 2
    assert "not allowed with argument" in capsys.readouterr().err


def test_item_belongs_to_reword_alone_and_every_other_action_needs_its_number(
        tmp_path: Path):
    repo = _repo(tmp_path)
    base = ["--repo", str(repo), "progress"]
    assert aide.main([*base, "set", "--item", "042", "--no-commit"]) == 2
    assert aide.main([*base, "set", "--no-commit"]) == 2
    assert aide.main([*base, "reopen", "--reason", "x", "--no-commit"]) == 2


def test_the_criterion_form_still_needs_a_stage(tmp_path: Path):
    assert _reword(_repo(tmp_path), "--criterion", "1", "--text", "x") == 2
