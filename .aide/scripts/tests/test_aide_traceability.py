"""``aide scope``'s traceability warning and ``aide claim``'s interface-pin
line (issues #242 part two and #243).

The parsers and the matcher are pure; the end-to-end tests build a throwaway
repository under ``tmp_path`` the way ``test_aide_scope.py`` does.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_traceability", _MODULE_PATH)
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

SPEC = """\
# Item 042 — Demo item

> **Created:** 2026-09-01 · status tracked in progress.md
> **Stage:** 1 — Rules

## Acceptance Criteria

- [ ] **AC1: parses.** The parser reads a row.
- [ ] **AC2: rejects.** A malformed row is refused.

## Assumptions

- None.

## Authorised paths

**May change:**

- `src/demo/rules.py` — the rule
- `tests/test_rules.py` — its tests

## Testing Strategy

Module `tests/test_rules.py`. Beyond one test per AC:

- `empty-input: the walker yields nothing rather than raising`
- **trailing-comma**: a row ending in a comma is one field short
- existing tests to reconcile: none
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
- ✅ The parser. *(Item 041)*
- ⏸️ The exporter. *(Item 040)*
- ❌ The importer. *(Item 039)*
- 📋 The walker. *(Item 042)*

**Acceptance.**
- [ ] All land.
"""

QUEUE = """\
# Demo — Work Queue 001

### Item 042: The walker
Walks rows.
"""

SPEC_WITH_PINS = SPEC.replace("- None.\n", """\
- **A1:** item 041's `parse_row` returns a dict keyed by column name.
- **A2 (engine 1.56.0):** `aide check` warns on a missing Assumptions block.
- **A3:** item 041's dict is ordered — re-checked 2026-09-10, agrees.
- **A4:** item 040's export format is CSV.
- **A5:** item 039's importer accepts a path; to be re-checked before tests.
- Whitespace is stripped (clarify default).
""") + """
## Dependencies

- Item 041 (the parser), Item 040 (the exporter), Item 039 (the importer).

**Downstream:** item 043 reads the walk.
"""


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _init_repo(path: Path, spec: str = SPEC) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], path)
    _run(["git", "config", "user.email", "t@example.com"], path)
    _run(["git", "config", "user.name", "Tester"], path)
    (path / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    ddir = path / "docs" / "aide"
    (ddir / "items").mkdir(parents=True)
    (ddir / "queue").mkdir()
    (ddir / "items" / "042-demo-item.md").write_text(spec, encoding="utf-8")
    (ddir / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (ddir / "queue" / "queue-001.md").write_text(QUEUE, encoding="utf-8")
    (path / "src" / "demo").mkdir(parents=True)
    (path / "src" / "demo" / "rules.py").write_text("x = 1\n", encoding="utf-8")
    (path / "tests").mkdir()
    (path / "tests" / "test_rules.py").write_text(
        "def test_legacy():\n    assert True\n", encoding="utf-8")
    _run(["git", "add", "-A"], path)
    _run(["git", "commit", "-m", "init"], path)
    return path


def _work(repo: Path, test_source: str) -> None:
    _run(["git", "switch", "-c", "aide/042-demo-item"], repo)
    # A `def test_…` outside tests_dir: the tests_dir filter must be
    # load-bearing, so this one is never reported.
    (repo / "src" / "demo" / "rules.py").write_text(
        "x = 2\n\ndef test_helper_in_source():\n    pass\n", encoding="utf-8")
    (repo / "tests" / "test_rules.py").write_text(test_source, encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "work"], repo)


# --------------------------------------------------------------------------- #
# the parsers
# --------------------------------------------------------------------------- #
def test_acceptance_numbers_come_from_the_criteria_section_only():
    assert aide.spec_acceptance_numbers(SPEC) == [1, 2]
    assert aide.spec_acceptance_numbers("# Item\n\nAC7 is mentioned in prose.\n") == []


def test_labels_are_the_first_word_of_a_bullet_closed_by_a_colon():
    """Backticks and bold around the token are decoration; a multi-word
    opener ("existing tests to reconcile:") is prose, not a case."""
    assert aide.testing_strategy_labels(SPEC) == ["empty-input", "trailing-comma"]


def test_labels_ignore_a_module_path_and_stop_at_the_next_heading():
    text = "## Testing Strategy\n\n- tests/test_x.py: the module\n\n## Dependencies\n\n- boundary: no\n"
    assert aide.testing_strategy_labels(text) == []


def test_a_prose_line_or_a_fenced_block_is_not_a_label():
    """`Note: …` in prose would trace every `test_notes_*`; a fenced block is
    code. Only a bullet's first word is a case."""
    text = ("## Testing strategy\n\nNote: the parser is shared.\n\n```\nfoo: bar\n```\n"
            "\n- boundary: the last row\n")
    assert aide.testing_strategy_labels(text) == ["boundary"]


def test_a_fence_is_stripped_from_the_section_only():
    """A bullet inside a fence is code (both spellings, indented too); a fence
    left open in an EARLIER section must not swallow this one."""
    text = ("## Implementation Steps\n\n```python\nopen and never closed\n\n"
            "## Testing Strategy\n\n- real: the row\n\n    ```\n    - fake: x\n    ```\n"
            "~~~\n- fake2: y\n~~~\n- also: z\n\n## Dependencies\n\n```\n")
    assert aide.testing_strategy_labels(text) == ["real", "also"]


def test_headings_match_case_insensitively():
    assert aide.spec_acceptance_numbers("## Acceptance criteria\n\n- [ ] AC4: x\n") == [4]


def test_under_dir_accepts_every_spelling_of_tests_dir():
    for spelling in ("tests", "tests/", "./tests", "tests\\unit", "."):
        assert aide._under_dir("tests/unit/test_a.py", spelling), spelling
    assert not aide._under_dir("src/tests_helpers.py", "tests")
    assert not aide._under_dir("tests/test_a.py", "tests/unit")


def test_an_absolute_tests_dir_inside_the_repo_is_relativised(tmp_path: Path):
    config = {"project": {"tests_dir": str(tmp_path / "tests")}}
    assert aide._tests_dir_rel(tmp_path, config) == "tests"
    config = {"project": {"tests_dir": str(tmp_path.parent / "elsewhere")}}
    assert aide._tests_dir_rel(tmp_path, config) is None


def test_a_bom_at_the_base_does_not_hide_the_existing_tests():
    assert aide._test_function_names("\ufeffdef test_legacy():\n    pass\n") == ["test_legacy"]


# --------------------------------------------------------------------------- #
# the matcher
# --------------------------------------------------------------------------- #
def test_a_test_naming_an_ac_or_a_label_is_traced():
    added = [("tests/test_rules.py", "test_ac1_parses"),
             ("tests/test_rules.py", "test_AC2_rejects_garbage"),
             ("tests/test_rules.py", "test_empty_input_yields_nothing"),
             ("tests/test_rules.py", "test_trailing_comma")]
    assert aide.traceability_warnings(added, [1, 2], ["empty-input", "trailing-comma"], "s.md") == []


def test_a_test_naming_neither_is_one_warning_naming_the_test():
    got = aide.traceability_warnings([("tests/test_rules.py", "test_parses_a_row")],
                                     [1, 2], ["empty-input"], "docs/aide/items/042.md")
    assert len(got) == 1
    assert "tests/test_rules.py::test_parses_a_row" in got[0]
    assert "docs/aide/items/042.md" in got[0]


def test_the_ac_token_is_bounded_on_both_sides():
    """`ac30` is not AC3, and `mac3` is not AC3 either."""
    got = aide.traceability_warnings([("t.py", "test_ac30"), ("t.py", "test_mac3")], [3], [], "s")
    assert len(got) == 2


# --------------------------------------------------------------------------- #
# scope, end to end
# --------------------------------------------------------------------------- #
def test_scope_warns_on_a_test_naming_neither(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _work(repo, "def test_legacy():\n    assert True\n\ndef test_parses():\n    assert True\n")
    rc = aide.main(["--repo", str(repo), "scope"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "warning: tests/test_rules.py::test_parses names no AC number" in out
    assert "1 traceability warning(s)" in out


def test_scope_is_silent_when_every_added_test_is_traced(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _work(repo, "def test_legacy():\n    assert True\n\n"
                "def test_ac1_parses():\n    assert True\n\n"
                "def test_empty_input():\n    assert True\n")
    rc = aide.main(["--repo", str(repo), "scope"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "warning" not in out


def test_scope_ignores_an_edited_existing_test(tmp_path: Path, capsys):
    """`test_legacy` existed at the base and names nothing: an edit to it is a
    reconcile, not an addition, so it draws no warning."""
    repo = _init_repo(tmp_path / "repo")
    _work(repo, "def test_legacy():\n    assert 1 == 1\n")
    rc = aide.main(["--repo", str(repo), "scope"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "warning" not in out


def test_a_renamed_test_file_is_read_under_its_old_name(tmp_path: Path, capsys):
    """`git diff --name-only` lists only the new path of a rename; without the
    rename map every pre-existing test in the moved file would be "added"."""
    repo = _init_repo(tmp_path / "repo",
                      spec=SPEC.replace("`tests/test_rules.py`", "`tests/*.py`"))
    _run(["git", "switch", "-c", "aide/042-demo-item"], repo)
    _run(["git", "mv", "tests/test_rules.py", "tests/test_walker.py"], repo)
    _run(["git", "commit", "-m", "rename"], repo)
    rc = aide.main(["--repo", str(repo), "scope"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "warning" not in out, out


def test_a_spec_without_criteria_is_one_notice_not_n_warnings(tmp_path: Path, capsys):
    spec = SPEC.replace("## Acceptance Criteria", "## Criteria")
    repo = _init_repo(tmp_path / "repo", spec=spec)
    _work(repo, "def test_a():\n    pass\n\ndef test_b():\n    pass\n")
    assert aide.main(["--repo", str(repo), "scope"]) == 0
    out = capsys.readouterr().out
    assert "notice:" in out and "traceability not checked" in out
    assert "warning" not in out


def test_the_warning_never_turns_a_pass_into_a_fail(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _work(repo, "def test_a():\n    pass\n\ndef test_b():\n    pass\n")
    assert aide.main(["--repo", str(repo), "scope"]) == 0
    assert capsys.readouterr().out.count("warning:") == 2


# --------------------------------------------------------------------------- #
# claim: the interface-pin line
# --------------------------------------------------------------------------- #
def test_interface_pins_skip_the_three_shapes_that_are_not_the_signal():
    """A2 is engine-marked, A3 carries a dated re-check; A5's "to be
    re-checked" is a request, not a record, and stays."""
    status = {41: "complete", 40: "deferred", 39: "excluded"}
    got = aide.interface_pins(SPEC_WITH_PINS, [41, 40, 39], status)
    assert [(label, dep) for _, label, dep, _ in got] == [("A1", 41), ("A4", 40), ("A5", 39)]
    assert [st for _, _, _, st in got] == ["complete", "deferred", "excluded"]


def test_a_recorded_re_check_in_prose_is_skipped_too():
    text = ("## Assumptions\n\n- **A7:** item 041's shape; re-checked against the "
            "real code in 1.36.0 and agrees.\n")
    assert aide.interface_pins(text, [41], {}) == []


def test_one_bullet_naming_two_dependencies_counts_once_and_two_unlabelled_count_twice():
    text = "## Assumptions\n\n- **A1:** items 041, 040's rows are dicts.\n"
    got = aide.interface_pins(text, [41, 40], {})
    assert [(i, dep) for i, _, dep, _ in got] == [(1, 41), (1, 40)]
    text = "## Assumptions\n\n- item 041 is a dict.\n- item 040 is CSV.\n"
    got = aide.interface_pins(text, [41, 40], {})
    assert [(i, label) for i, label, _, _ in got] == [(1, "assumption #1"), (2, "assumption #2")]


def test_interface_pins_are_empty_without_a_dependency():
    assert aide.interface_pins(SPEC_WITH_PINS, [], {}) == []


def test_claim_names_the_assumptions_that_pin_a_dependency(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo", spec=SPEC_WITH_PINS)
    rc = aide.main(["--repo", str(repo), "claim"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "claimed item 042" in out
    assert "3 assumption(s)" in out
    assert "A1 (item 041)" in out
    assert "A4 (item 040, no code to check against)" in out
    assert "A5 (item 039, no code to check against)" in out


def test_claim_says_nothing_about_pins_when_there_are_none(tmp_path: Path, capsys):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim", "--dry-run"]) == 0
    assert "pin a dependency" not in capsys.readouterr().out
