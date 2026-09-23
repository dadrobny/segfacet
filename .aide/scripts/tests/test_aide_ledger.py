"""The run ledger — one row per item worked (issue #244, §1 → ``ledger.md``).

Three layers, in the order the code has them. The parsers (``parse_findings``,
``ledger_warnings``) are pure and tested as such; the derivation
(``ledger_cells``) needs a document tree and no git; and the two verbs that
write a row — ``merge`` and ``ledger abandon`` — need a repository, built under
``tmp_path`` in ``git.mode = "local"`` so nothing pushes or fetches, except the
one case that needs a bare remote to push to.

Asserted on cells and effects, never on prose, with one deliberate exception:
the sentences ``test_aide_help_pins.py`` pins are claims about behaviour, and
the tests it names as their guards are here.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_ledger", _MODULE_PATH)
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

[loop]
review = "background"
"""

#: The default a scaffolded `aide.toml` carries: no reviewer runs at all, so
#: the three finding cells carry the marker rather than a blank. The fixture
#: above runs *with* a reviewer, because every count a caller passes is a
#: count some reviewer produced; the marker cases switch it back.
REVIEW_OFF = 'review = "background"', 'review = "off"'

PROGRESS = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 2 | Rules | G1 | 🚧 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 2 | 🚧 |

## Stage 2 — Rules — 🚧

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

### Item 028: Validate stage 2
Pin what the stage produced.
"""

SPEC_027 = """\
# Item 027 — Bounds rules

> **Created:** 2026-09-17 · status tracked in progress.md
> **Stage:** 2 — Rules

## Acceptance Criteria

- [ ] **AC1: bounds.** The rule bounds the input.
- [ ] **AC2: refuses.** An unbounded input is refused.

## Authorised paths

**May change:**

- `src/demo/bounds.py` — the rule
- `tests/test_bounds.py` — its tests
"""

INSIGHTS = """\
# Insight Inbox

_Entries below, newest last._
"""

#: A closed `defect` entry routed to an item — how the engine learns that an
#: item is insight-derived (§1 → the maintenance queue).
ROUTED_DEFECT = ("- [x] defect — bounds are off by one *(item 019, 2026-09-01)* "
                 "→ item 027\n")


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8")


def _docs(path: Path, insights: str = INSIGHTS) -> Path:
    """The document tree alone — no git, which most of these need none of."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    d = path / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir(parents=True)
    (d / "progress.md").write_text(PROGRESS, encoding="utf-8")
    (d / "queue" / "queue-003.md").write_text(QUEUE, encoding="utf-8")
    (d / "items" / "027-bounds-rules.md").write_text(SPEC_027, encoding="utf-8")
    (d / "insights.md").write_text(insights, encoding="utf-8")
    return path


def _review_off(repo: Path) -> Path:
    """Switch the repo to `[loop] review = "off"` — the scaffolded default."""
    toml = repo / "aide.toml"
    toml.write_text(toml.read_text(encoding="utf-8").replace(*REVIEW_OFF),
                    encoding="utf-8")
    return repo


def _init_repo(path: Path, mode: str = "local", insights: str = INSIGHTS) -> Path:
    _docs(path, insights)
    if mode != "local":
        (path / "aide.toml").write_text(
            AIDE_TOML.replace('mode = "local"', f'mode = "{mode}"'),
            encoding="utf-8")
    _run(["git", "init", "-b", "main"], path)
    _run(["git", "config", "user.email", "t@example.com"], path)
    _run(["git", "config", "user.name", "Tester"], path)
    (path / "src" / "demo").mkdir(parents=True)
    (path / "src" / "demo" / "bounds.py").write_text("x = 1\n", encoding="utf-8")
    (path / "tests").mkdir()
    _run(["git", "add", "-A"], path)
    _run(["git", "commit", "-m", "init"], path)
    return path


def _do_the_work(repo: Path) -> None:
    """Exactly two files, one of them a new test — the counts to assert on."""
    (repo / "src" / "demo" / "bounds.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "tests" / "test_bounds.py").write_text(
        "def test_ac1_bounds():\n    assert True\n", encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "work"], repo)


def _cells(repo: Path, **kwargs) -> dict:
    config = aide.load_config(repo)
    row = aide.ledger_cells(repo, config, 27, kwargs.pop("outcome", "merged"),
                            **kwargs)
    return dict(zip(aide.LEDGER_COLUMNS, row))


def _rows(repo: Path) -> list:
    """The ledger's data rows, as `{column: cell}` dicts."""
    text = (repo / "docs" / "aide" / "ledger.md").read_text(encoding="utf-8")
    return [dict(zip(aide.LEDGER_COLUMNS, cells))
            for _, cells in aide.ledger_rows(text)]


def _mkbare(path: Path) -> Path:
    subprocess.run(["git", "init", "--bare", "-b", "main", str(path)],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return path


# --------------------------------------------------------------------------- #
# --findings: the one thing the caller types, so the one thing parsed strictly
# --------------------------------------------------------------------------- #
def test_findings_takes_any_subset_of_the_ranks_in_any_order():
    assert aide.parse_findings("blocking=1,minor=2,nit=0") == {
        "blocking": 1, "minor": 2, "nit": 0}
    assert aide.parse_findings("nit=3, blocking=0") == {"nit": 3, "blocking": 0}
    assert aide.parse_findings("MINOR=7") == {"minor": 7}


def test_findings_refuses_an_unknown_rank_a_duplicate_and_a_non_integer():
    """Each refusal names what was wrong: a rank silently dropped would record
    a blank where a count was passed, which is the one lie the blank-cell rule
    exists to prevent."""
    for value, wanted in (("critical=1", "unknown rank"),
                          ("minor=1,minor=2", "given twice"),
                          ("minor=two", "non-negative integer"),
                          ("minor=-1", "non-negative integer"),
                          ("minor", "not <rank>=<count>"),
                          ("minor=1,,nit=2", "empty entry")):
        try:
            aide.parse_findings(value)
        except ValueError as exc:
            assert wanted in str(exc), (value, str(exc))
        else:
            raise AssertionError(f"{value!r} was accepted")


def test_the_flag_turns_a_refusal_into_a_usage_error(capsys):
    """`merge --findings critical=1` must exit 2 with the flag named, before
    anything merges — a usage error, not a half-done run."""
    parser = aide.build_parser()
    try:
        parser.parse_args(["merge", "27", "--findings", "critical=1"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("an unknown rank was accepted")
    assert "--findings" in capsys.readouterr().err


def test_rounds_refuses_anything_but_a_non_negative_integer(capsys):
    parser = aide.build_parser()
    for value in ("-1", "two", "1.5"):
        try:
            parser.parse_args(["merge", "27", "--rounds", value])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"--rounds {value} was accepted")
        assert "--rounds" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# the row and the template — one shape, two files
# --------------------------------------------------------------------------- #
def test_the_template_header_row_is_the_column_order_the_engine_writes():
    """The template is the shape's executable statement (§1) and
    `LEDGER_COLUMNS` is what writes it, so the two are one claim. A column
    added to either alone puts every row one cell out."""
    text = (aide._TEMPLATES_DIR / "ledger.md").read_text(encoding="utf-8-sig")
    header = next(line for line in text.splitlines()
                  if line.strip().startswith("| Item"))
    assert aide._split_row(header) == list(aide.LEDGER_COLUMNS)


def test_the_templates_own_example_row_is_not_read_as_an_item():
    """The document is a byte-exact copy of the template, comment included,
    and that comment draws the row the verb is about to write. A reader that
    took every `|` line for data would report an item nobody worked."""
    text = (aide._TEMPLATES_DIR / "ledger.md").read_text(encoding="utf-8-sig")
    assert aide.ledger_rows(text) == []


def test_a_row_is_one_cell_per_column():
    cells = ["x"] * len(aide.LEDGER_COLUMNS)
    assert aide.ledger_row(cells).count("|") == len(aide.LEDGER_COLUMNS) + 1


# --------------------------------------------------------------------------- #
# derivation — everything but the two counts
# --------------------------------------------------------------------------- #
def test_the_documents_supply_every_cell_but_the_counts(tmp_path: Path):
    row = _cells(_docs(tmp_path / "repo"), rounds=2,
                 findings={"blocking": 1, "minor": 2, "nit": 0})
    assert row["Item"] == "027"
    assert row["Queue"] == "003"
    assert row["Stage"] == "2"
    assert row["Kind"] == "normal"
    assert row["Outcome"] == "merged"
    assert row["ACs"] == "2"
    assert row["Rounds"] == "2"
    assert (row["Blocking"], row["Minor"], row["Nit"]) == ("1", "2", "0")
    assert row["Engine"] == aide.installed_engine_version()
    assert row["Date"].count("-") == 2


def test_a_count_nobody_passed_is_a_blank_cell_never_a_zero(tmp_path: Path):
    """The help's claim, and §1's: an unrecorded run must not read as a cheap
    one. A rank the caller *did* pass as 0 is a measurement and stays a 0."""
    row = _cells(_docs(tmp_path / "repo"), rounds=None,
                 findings={"blocking": 0})
    assert row["Rounds"] == ""
    assert row["Blocking"] == "0"
    assert row["Minor"] == "" and row["Nit"] == ""


def test_a_cell_nothing_could_measure_is_blank_and_costs_only_itself(tmp_path: Path):
    """No spec, no queue entry, no branch: the row is still a row."""
    repo = _docs(tmp_path / "repo")
    (repo / "docs" / "aide" / "items" / "027-bounds-rules.md").unlink()
    (repo / "docs" / "aide" / "queue" / "queue-003.md").unlink()
    row = _cells(repo)
    assert row["Item"] == "027"
    assert (row["Stage"], row["ACs"], row["Queue"]) == ("", "", "")
    assert (row["Tests"], row["Files"]) == ("", "")
    assert row["Kind"] == "normal"


def test_a_spec_with_no_criteria_heading_blanks_only_that_cell(tmp_path: Path):
    repo = _docs(tmp_path / "repo")
    spec = repo / "docs" / "aide" / "items" / "027-bounds-rules.md"
    spec.write_text(spec.read_text(encoding="utf-8").replace(
        "## Acceptance Criteria", "## Criteria, informally"), encoding="utf-8")
    row = _cells(repo)
    assert row["ACs"] == ""
    assert row["Stage"] == "2"


def test_a_validate_stage_item_is_its_own_kind(tmp_path: Path):
    """Read off the title — the spec's, or the queue's where no spec exists
    yet. Such an item is test-heavy by design, so tests-per-criterion is not
    comparable with anything else's."""
    repo = _docs(tmp_path / "repo")
    config = aide.load_config(repo)
    assert aide.item_kind(repo, config, 28) == "validate-stage"
    assert aide.item_kind(repo, config, 27) == "normal"
    assert aide.item_kind(repo, config, 27, title="Validate stage 2") == "validate-stage"


def test_an_item_an_insight_was_routed_to_is_maintenance(tmp_path: Path):
    """§1 → the maintenance queue: a queued `defect`, `gap` or `automation`
    entry is ticked with the item number it became, so the inbox is where the
    engine can read that an item is insight-derived."""
    repo = _docs(tmp_path / "repo", insights=INSIGHTS + ROUTED_DEFECT)
    assert aide.item_kind(repo, aide.load_config(repo), 27) == "maintenance"


def test_the_provenance_of_an_entry_does_not_make_an_item_maintenance(tmp_path: Path):
    """`*(item 027, …)*` names the item an insight was captured IN — the
    opposite claim from "this item is that insight", and reading it as one
    would mark every item any role captured anything during."""
    captured = INSIGHTS + "- [ ] defect — bounds are off by one *(item 027, 2026-09-01)*\n"
    repo = _docs(tmp_path / "repo", insights=captured)
    assert aide.item_kind(repo, aide.load_config(repo), 27) == "normal"


def test_a_knowledge_entry_routed_to_an_item_is_not_maintenance(tmp_path: Path):
    """Only the three types that become a maintenance item count."""
    routed = INSIGHTS + "- [x] knowledge — the bound is documented *(2026-09-01)* → item 027\n"
    repo = _docs(tmp_path / "repo", insights=routed)
    assert aide.item_kind(repo, aide.load_config(repo), 27) == "normal"


def test_validate_stage_wins_over_an_insight_pointer(tmp_path: Path):
    routed = INSIGHTS + "- [x] gap — nothing pins the stage *(2026-09-01)* → item 028\n"
    repo = _docs(tmp_path / "repo", insights=routed)
    assert aide.item_kind(repo, aide.load_config(repo), 28) == "validate-stage"


# --------------------------------------------------------------------------- #
# the file — created from the template, appended to, never rewritten
# --------------------------------------------------------------------------- #
def test_the_first_row_creates_the_ledger_from_the_template(tmp_path: Path):
    repo = _docs(tmp_path / "repo")
    config = aide.load_config(repo)
    cells = aide.ledger_cells(repo, config, 27, "merged", rounds=1)
    rel = aide.append_ledger_row(repo, config, cells, "merge")
    assert rel == "docs/aide/ledger.md"
    template = (aide._TEMPLATES_DIR / "ledger.md").read_text(encoding="utf-8-sig")
    written = (repo / "docs" / "aide" / "ledger.md").read_text(encoding="utf-8-sig")
    assert written.startswith(template)
    assert written.splitlines()[-1] == aide.ledger_row(cells)


def test_a_second_row_is_appended_and_the_first_is_untouched(tmp_path: Path):
    repo = _docs(tmp_path / "repo")
    config = aide.load_config(repo)
    first = aide.ledger_cells(repo, config, 27, "merged", rounds=1)
    aide.append_ledger_row(repo, config, first, "merge")
    second = aide.ledger_cells(repo, config, 28, "abandoned", rounds=3)
    aide.append_ledger_row(repo, config, second, "ledger abandon")
    rows = _rows(repo)
    assert [r["Item"] for r in rows] == ["027", "028"]
    assert [r["Outcome"] for r in rows] == ["merged", "abandoned"]


def test_a_repo_with_no_document_set_gets_no_ledger(tmp_path: Path, capsys):
    """A project may adopt the CLI without the loop; there is nowhere to write
    and nothing to fail."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    config = aide.load_config(repo)
    assert aide.append_ledger_row(repo, config, ["x"], "merge") is None
    assert "no ledger row" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# aide check — a warning, never an error, and never a file it created
# --------------------------------------------------------------------------- #
def test_an_absent_or_readable_ledger_says_nothing(tmp_path: Path):
    repo = _docs(tmp_path / "repo")
    ddir = repo / "docs" / "aide"
    assert aide.ledger_warnings(ddir) == []
    config = aide.load_config(repo)
    aide.append_ledger_row(repo, config,
                           aide.ledger_cells(repo, config, 27, "merged"), "merge")
    assert aide.ledger_warnings(ddir) == []


def test_check_never_creates_the_ledger(tmp_path: Path):
    """Unlike the inbox: nothing appends here by hand, so a file with no rows
    would be a document the engine created for nobody."""
    repo = _docs(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert not (repo / "docs" / "aide" / "ledger.md").exists()


def test_a_row_no_reader_can_use_is_a_warning_and_never_an_error(tmp_path: Path, capsys):
    repo = _docs(tmp_path / "repo")
    ddir = repo / "docs" / "aide"
    good = aide.ledger_row(["027", "003", "2", "normal", "merged", "2", "1",
                            "2", "2", "1", "0", "", "1.58.0", "2026-09-17"])
    (ddir / "ledger.md").write_text(
        "# Run Ledger\n\n"
        "| " + " | ".join(aide.LEDGER_COLUMNS) + " |\n"
        "|" + "---|" * len(aide.LEDGER_COLUMNS) + "\n"
        + good + "\n"
        + "| 028 | 003 | 2 |\n"
        + aide.ledger_row(["stage two", "003", "2", "normal", "merged", "2", "1",
                           "2", "2", "1", "0", "0", "1.58.0", "2026-09-17"]) + "\n"
        + aide.ledger_row(["029", "003", "2", "normal", "merged", "two", "1",
                           "2", "2", "1", "0", "0", "1.58.0", "2026-09-17"]) + "\n",
        encoding="utf-8")
    warnings = aide.ledger_warnings(ddir)
    assert len(warnings) == 3, warnings
    assert "3 cell(s), not 14" in warnings[0]
    assert "Item cell 'stage two'" in warnings[1]
    assert "ACs cell 'two'" in warnings[2]
    # …and the whole check still passes: a record nobody can rewrite must not
    # be able to stop a run (§1 → `ledger.md`).
    errors, reported = aide.run_checks(repo, aide.load_config(repo))
    assert errors == []
    assert [w for w in reported if "ledger.md" in w] == warnings
    assert aide.main(["--repo", str(repo), "check"]) == 0


def test_an_outcome_outside_the_vocabulary_is_a_warning(tmp_path: Path):
    """The cell says how the item left the loop, and the two answers are the
    writing verbs'. A third is a row a reader cannot place."""
    repo = _docs(tmp_path / "repo")
    ddir = repo / "docs" / "aide"
    (ddir / "ledger.md").write_text(
        "# Run Ledger\n\n"
        + aide.ledger_row(["027", "003", "2", "normal", "shipped", "2", "1",
                           "2", "2", "1", "0", "0", "1.58.0", "2026-09-17"])
        + "\n", encoding="utf-8")
    (warning,) = aide.ledger_warnings(ddir)
    assert "Outcome cell 'shipped'" in warning


def test_a_ledger_from_an_older_template_is_reported_like_every_document(tmp_path: Path):
    repo = _docs(tmp_path / "repo")
    ddir = repo / "docs" / "aide"
    (ddir / "ledger.md").write_text(
        "<!-- aide-template: ledger 0 -->\n# Run Ledger\n", encoding="utf-8")
    warnings = aide.template_drift_warnings(ddir, {}, {"ledger": 1})
    assert any("ledger.md" in w and "ledger template 0" in w for w in warnings), warnings


# --------------------------------------------------------------------------- #
# aide merge — the row beside the tick, in the same commit
# --------------------------------------------------------------------------- #
def test_merge_writes_the_row_in_the_commit_that_ticks_the_item(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--rounds", "2", "--findings", "blocking=1,nit=0"]) == 0

    (row,) = _rows(repo)
    assert row["Item"] == "027" and row["Outcome"] == "merged"
    assert row["Rounds"] == "2"
    assert (row["Blocking"], row["Minor"], row["Nit"]) == ("1", "", "0")
    # The branch's own diff, taken before the merge deleted it: one test
    # function added, two files changed.
    assert (row["Tests"], row["Files"]) == ("1", "2")
    # One commit, so a run can never land the tick and lose the row.
    shown = _run(["git", "show", "--name-only", "--format=", "HEAD"], repo).stdout
    assert "docs/aide/ledger.md" in shown
    assert "docs/aide/progress.md" in shown


def test_merge_without_the_flags_writes_the_row_with_blank_counts(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)
    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test"]) == 0
    (row,) = _rows(repo)
    assert (row["Rounds"], row["Blocking"], row["Minor"], row["Nit"]) == \
        ("", "", "", "")


def test_a_ledger_that_cannot_be_written_does_not_fail_the_merge(
        tmp_path: Path, monkeypatch, capsys):
    """The row is worth a sentence, never an item: the merge has already
    landed by the time it is written."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)
    monkeypatch.setattr(aide, "_TEMPLATES_DIR", tmp_path / "no-templates")

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test"]) == 0

    assert not (repo / "docs" / "aide" / "ledger.md").exists()
    assert "install is incomplete" in capsys.readouterr().err
    assert aide._parse_item_status(
        (repo / "docs" / "aide" / "progress.md").read_text(
            encoding="utf-8").splitlines())[2][27] == "complete"


def test_pr_mode_writes_neither_the_tick_nor_a_row(tmp_path: Path):
    """The row follows the ✅, and under `pr` this verb writes neither: the
    merge is the human's."""
    remote = _mkbare(tmp_path / "remote.git")
    repo = _init_repo(tmp_path / "repo", mode="pr")
    _run(["git", "remote", "add", "origin", str(remote)], repo)
    _run(["git", "push", "-u", "origin", "main"], repo)
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--rounds", "1"]) == 0

    assert not (repo / "docs" / "aide" / "ledger.md").exists()


# --------------------------------------------------------------------------- #
# aide ledger abandon — the row for the item that never merges
# --------------------------------------------------------------------------- #
def test_abandon_records_the_round_count_and_leaves_progress_alone(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)
    before = (repo / "docs" / "aide" / "progress.md").read_text(encoding="utf-8")

    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3", "--findings", "blocking=2"]) == 0

    (row,) = _rows(repo)
    assert row["Outcome"] == "abandoned"
    assert (row["Rounds"], row["Blocking"], row["Minor"]) == ("3", "2", "")
    assert (row["Tests"], row["Files"]) == ("1", "2")
    assert (repo / "docs" / "aide" / "progress.md").read_text(
        encoding="utf-8") == before
    shown = _run(["git", "show", "--name-only", "--format=", "HEAD"], repo).stdout
    assert "docs/aide/ledger.md" in shown


def test_abandon_without_rounds_exits_two_and_writes_nothing(tmp_path: Path, capsys):
    """The round count is why the row exists."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27"]) == 2
    assert "--rounds is required" in capsys.readouterr().err
    assert not (repo / "docs" / "aide" / "ledger.md").exists()


def test_abandon_run_twice_records_the_item_once(tmp_path: Path, capsys):
    """A retried orchestrator step must not count one abandonment as two."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3"]) == 0
    before = (repo / "docs" / "aide" / "ledger.md").read_bytes()
    capsys.readouterr()
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3"]) == 0
    assert "already recorded as abandoned" in capsys.readouterr().out
    assert (repo / "docs" / "aide" / "ledger.md").read_bytes() == before
    assert len(_rows(repo)) == 1


def test_abandon_with_different_counts_is_a_second_abandonment(tmp_path: Path):
    """An item resumed after the cap and stopped again is a new fact."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3"]) == 0
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "2", "--findings", "minor=1"]) == 0
    rows = _rows(repo)
    assert [(r["Rounds"], r["Minor"]) for r in rows] == [("3", ""), ("2", "1")]


def test_abandon_with_no_branch_left_blanks_the_two_diff_cells(tmp_path: Path):
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3"]) == 0
    (row,) = _rows(repo)
    assert (row["Tests"], row["Files"]) == ("", "")
    assert row["ACs"] == "2"


def test_a_test_reconciled_in_another_items_file_is_not_counted(tmp_path: Path):
    """Issue #262: the tests `aide scope` reports as reconciled — traced to
    item 026's spec, in 026's own file — are 026's and not counted on 027's
    row; one in the same file that traces to nothing still is."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "docs" / "aide" / "items" / "026-walker.md").write_text(
        "# Item 026 — Walker\n\n## Acceptance Criteria\n\n- [ ] **AC9: walks.**\n",
        encoding="utf-8")
    (repo / "tests" / "test_026_walker.py").write_text(
        "def test_ac9_old():\n    assert True\n", encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "item 026"], repo)
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)
    (repo / "tests" / "test_026_walker.py").write_text(
        "def test_ac9_new():\n    assert True\n\n"
        "def test_unasked():\n    assert True\n", encoding="utf-8")
    _run(["git", "add", "-A"], repo)
    _run(["git", "commit", "-m", "reconcile 026"], repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--rounds", "1"]) == 0
    (row,) = _rows(repo)
    # test_ac1_bounds (027's own) + test_unasked; test_ac9_new is 026's.
    assert (row["Tests"], row["Files"]) == ("2", "3")


# --------------------------------------------------------------------------- #
# [loop] review — what the three finding cells say when nobody reviewed
# --------------------------------------------------------------------------- #
def test_merge_under_review_off_marks_the_finding_cells(tmp_path: Path):
    """No reviewer ran, so there were no findings to count — and `-` is what
    separates that from a run whose counts were never passed on."""
    repo = _review_off(_init_repo(tmp_path / "repo"))
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--rounds", "2"]) == 0

    (row,) = _rows(repo)
    assert (row["Blocking"], row["Minor"], row["Nit"]) == ("-", "-", "-")
    # Only the finding cells: the round count is the caller's either way.
    assert row["Rounds"] == "2"


def test_merge_under_review_on_leaves_the_finding_cells_blank(tmp_path: Path):
    """The other half of the same claim — without it the marker could be
    unconditional and every assertion above would still pass."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--rounds", "2"]) == 0

    (row,) = _rows(repo)
    assert (row["Blocking"], row["Minor"], row["Nit"]) == ("", "", "")


def test_findings_passed_under_review_off_win_over_the_mark(tmp_path: Path):
    """A count is a claim its caller made, and the engine records claims: a
    project that reviews outside the loop still gets its counts written."""
    repo = _review_off(_init_repo(tmp_path / "repo"))
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--findings", "minor=2"]) == 0

    (row,) = _rows(repo)
    assert row["Minor"] == "2"
    # Whole, not cell by cell: half a marked row would claim both things.
    assert (row["Blocking"], row["Nit"]) == ("", "")


def test_merge_with_review_on_and_no_findings_warns_and_still_lands(
        tmp_path: Path, capsys):
    """A reviewer ran and its triage reached no flag. The row is still worth
    writing and the item still lands, so this costs one line of stderr."""
    repo = _init_repo(tmp_path / "repo")
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test",
                      "--rounds", "1"]) == 0

    assert "no --findings was passed" in capsys.readouterr().err
    (row,) = _rows(repo)
    assert row["Outcome"] == "merged"


def test_merge_with_review_off_and_no_findings_does_not_warn(
        tmp_path: Path, capsys):
    """Nothing to pass, so nothing to warn about — a warning on every merge of
    every unreviewed project is a warning nobody reads."""
    repo = _review_off(_init_repo(tmp_path / "repo"))
    assert aide.main(["--repo", str(repo), "claim"]) == 0
    _do_the_work(repo)

    assert aide.main(["--repo", str(repo), "merge", "27", "--no-test"]) == 0

    assert "--findings" not in capsys.readouterr().err


def test_abandon_under_review_off_marks_the_finding_cells(tmp_path: Path):
    """Both writing verbs read the same setting; a row's cells must not depend
    on which verb ended the item."""
    repo = _review_off(_init_repo(tmp_path / "repo"))

    assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                      "--rounds", "3"]) == 0

    (row,) = _rows(repo)
    assert (row["Blocking"], row["Minor"], row["Nit"]) == ("-", "-", "-")
    assert row["Rounds"] == "3"


def test_a_marked_row_is_readable_and_a_junk_cell_still_is_not(tmp_path: Path):
    """`aide check` reports a cell no reader can use, and the marker the
    engine itself writes is not one — while anything else in those columns
    still is."""
    repo = _docs(tmp_path / "repo")
    ledger = repo / "docs" / "aide" / "ledger.md"
    header = (aide.ledger_row(list(aide.LEDGER_COLUMNS)) + "\n"
              + aide.ledger_row(["---"] * len(aide.LEDGER_COLUMNS)) + "\n")
    marked = dict(zip(aide.LEDGER_COLUMNS,
                      aide.ledger_cells(repo, aide.load_config(repo), 27,
                                        "merged", rounds=1, no_review=True)))
    junk = dict(marked, Minor="some")
    ledger.write_text(
        header
        + aide.ledger_row([marked[c] for c in aide.LEDGER_COLUMNS]) + "\n"
        + aide.ledger_row([junk[c] for c in aide.LEDGER_COLUMNS]) + "\n",
        encoding="utf-8")

    warnings = aide.ledger_warnings(repo / "docs" / "aide")
    assert len(warnings) == 1 and "Minor cell 'some'" in warnings[0]


def test_abandon_run_twice_under_review_off_still_records_the_item_once(
        tmp_path: Path):
    """The duplicate check compares the cells it is about to write, so it has
    to render them the same way the row did."""
    repo = _review_off(_init_repo(tmp_path / "repo"))
    for _ in range(2):
        assert aide.main(["--repo", str(repo), "ledger", "abandon", "27",
                          "--rounds", "3"]) == 0
    assert len(_rows(repo)) == 1
