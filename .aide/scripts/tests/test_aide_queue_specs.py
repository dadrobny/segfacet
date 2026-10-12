"""Tests for ``aide check --queue`` — a queue's specs checked against each other.

The window this guards is the one ``/aide-spec-queue`` creates: N specs authored
on one branch before any is built, where every cross-item conflict is possible
and cheap to fix, and nothing looked.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[1] / "aide.py"
_spec = importlib.util.spec_from_file_location("aide_cli_qspecs", _MODULE_PATH)
aide = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = aide
_spec.loader.exec_module(aide)  # type: ignore[union-attr]


AIDE_TOML = """\
[project]
name = "Demo"
docs_dir = "docs/aide"
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
- 📋 A. *(Item 027)*
- 📋 B. *(Item 028)*

**Acceptance.**
- [ ] Rules fire.
"""


def _spec_text(num: int, may=(), asserts=(), deps="None.") -> str:
    lines = [f"# Item {num:03d} — Demo", "", "## Authorised paths", ""]
    if may:
        lines += ["**May change:**", ""]
        lines += [f"- `{p}` — work" for p in may]
        lines.append("")
    if asserts:
        lines += ["**Asserts against:**", ""]
        lines += [f"- `{p}` — pinned" for p in asserts]
        lines.append("")
    lines += ["## Dependencies", "", deps, ""]
    return "\n".join(lines)


#: Item 027 merged (✅ means merged, in every git.mode), 028 still open.
PROGRESS_27_DONE = PROGRESS.replace("- 📋 A. *(Item 027)*", "- ✅ A. *(Item 027)*")

#: Item 027 deferred — recorded and deliberately not scheduled. It is NOT spent:
#: its edit is dormant, and `aide claim` steps over it rather than waiting.
PROGRESS_27_DEFERRED = PROGRESS.replace("- 📋 A. *(Item 027)*", "- ⏸️ A. *(Item 027)*")


def _make_repo(tmp_path: Path, specs: dict, queue_items=(27, 28),
               progress: str = PROGRESS) -> Path:
    repo = tmp_path / "repo"
    d = repo / "docs" / "aide"
    (d / "queue").mkdir(parents=True)
    (d / "items").mkdir(parents=True)
    (repo / "aide.toml").write_text(AIDE_TOML, encoding="utf-8")
    (d / "progress.md").write_text(progress, encoding="utf-8")
    body = "\n\n".join(f"### Item {n:03d}: Thing {n}\nDoes a thing."
                       for n in queue_items)
    (d / "queue" / "queue-003.md").write_text(f"# Demo — Work Queue 003\n\n{body}\n",
                                              encoding="utf-8")
    for num, text in specs.items():
        (d / "items" / f"{num:03d}-thing.md").write_text(text, encoding="utf-8")
    return repo


def _findings(repo: Path, queue: int = 3):
    cfg = aide.load_config(repo)
    return aide.queue_spec_findings(repo, cfg, queue)


# --------------------------------------------------------------------------- #
# patterns_overlap
# --------------------------------------------------------------------------- #
def test_overlap_identical_patterns():
    assert aide.patterns_overlap("src/a.py", "src/a.py")


def test_overlap_subtree_swallows_a_file():
    assert aide.patterns_overlap("src/**", "src/deep/a.py")
    assert aide.patterns_overlap("src/deep/a.py", "src/**")


def test_overlap_glob_covers_a_literal():
    assert aide.patterns_overlap("tests/golden/*.json", "tests/golden/a.json")


def test_no_overlap_between_unrelated_paths():
    assert not aide.patterns_overlap("src/a.py", "src/b.py")
    assert not aide.patterns_overlap("src/**", "tests/a.py")
    assert not aide.patterns_overlap("tests/golden/*.json", "tests/golden/deep/a.json")


def test_two_unrelated_globs_are_not_guessed_at():
    """Deciding that `src/*.py` and `src/a*` might one day both match `src/ab.py`
    would mean guessing at a future tree. The check reports what it can prove."""
    assert not aide.patterns_overlap("src/*.py", "src/a*")


# --------------------------------------------------------------------------- #
# row 1 — two specs claim the same file
# --------------------------------------------------------------------------- #
def test_reports_two_items_claiming_the_same_path(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/shared.py"]),
        28: _spec_text(28, may=["src/shared.py"]),
    })
    findings, _ = _findings(repo)
    kinds = [f.kind for f in findings]
    assert "may-change-overlap" in kinds
    hit = next(f for f in findings if f.kind == "may-change-overlap")
    assert hit.items == (27, 28) and hit.severity == "warning"


def test_subtree_claim_overlapping_a_sibling_file_is_reported(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/**"]),
        28: _spec_text(28, may=["src/one.py"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "may-change-overlap" for f in findings)


def test_disjoint_specs_produce_no_findings(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"]),
        28: _spec_text(28, may=["src/b.py"]),
    })
    findings, unspecced = _findings(repo)
    assert findings == [] and unspecced == []


# --------------------------------------------------------------------------- #
# rows 2+3 — one spec changes what another pins
# --------------------------------------------------------------------------- #
def test_changing_a_siblings_pinned_path_is_an_error(tmp_path: Path):
    """The recorded shape: item 101 was authorised to edit exactly the files
    items 099/100 had pinned as untouched forever."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/other.py"], asserts=["src/cli.py"]),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "changes-pinned-state")
    assert hit.severity == "error"
    assert hit.items == (27, 28)
    assert "027" in hit.message and "028" in hit.message


def test_a_live_recomputed_pin_is_caught_like_a_byte_hash(tmp_path: Path):
    """The instance a fragile-hash survey missed: item 105's AC7 recomputed its
    evidence live, so it was *more* coupled to the state item 106 changed."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/feature_docs.py"]),
        28: _spec_text(28, may=["docs/table.md"],
                       asserts=["src/feature_docs.py"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" for f in findings)


def test_a_declared_dependency_exempts_the_pinned_state_pair(tmp_path: Path):
    """The `Validate stage N` shape, reported inert 14 times on one consumer
    queue: item 028 exists to pin what item 027 produces, and says so under
    `## Dependencies`. It is built against a tree that already holds 027's
    edit, so 027 landing cannot break its pin."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"],
                       deps="Item 027 produces the artifacts this item pins."),
    })
    findings, _ = _findings(repo)
    assert findings == []


def test_the_dependency_exemption_is_directional(tmp_path: Path):
    """027 depending on 028 says 027 is built *last* — so its edit does land
    after 028's pin, which is the break the check exists to report."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"],
                       deps="Item 028 provides the schema."),
        28: _spec_text(28, asserts=["src/cli.py"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (27, 28)
               for f in findings)


def test_a_transitive_dependency_exempts_the_pair(tmp_path: Path):
    """029 → 028 → 027 orders 027 before 029 just as firmly as a direct edge.
    Only the far end of the chain is the pair being judged, and a validate item
    naming one sibling that names the rest is the ordinary way to write it."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 lands first."),
        29: _spec_text(29, asserts=["src/cli.py"], deps="Item 028 lands first."),
    }, queue_items=(27, 28, 29))
    findings, _ = _findings(repo)
    assert [f.kind for f in findings if f.kind == "changes-pinned-state"] == []


def test_an_undeclared_ordering_still_errors_next_to_a_declared_one(tmp_path: Path):
    """The exemption is per pair, not per item: 029 declares 028 and pins what
    both it and 027 change, and only the undeclared half is reported. That
    undeclared ordering is precisely what the check is for."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/b.py"]),
        29: _spec_text(29, asserts=["src/cli.py", "src/b.py"],
                       deps="Item 028 lands first."),
    }, queue_items=(27, 28, 29))
    findings, _ = _findings(repo)
    hits = [f for f in findings if f.kind == "changes-pinned-state"]
    assert [f.items for f in hits] == [(27, 29)]


def test_a_deferred_dependency_earns_no_exemption(tmp_path: Path):
    """The exemption rests on the dependency actually holding the dependent
    back. `aide claim` steps over a ⏸️ blocker, so 028 is claimable today and
    would pin a tree 027 has not touched — then 027 is undeferred and lands on
    top of the pin. Declaring the dependency does not make that safe."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"],
                       deps="Item 027 produces the artifacts this item pins."),
    }, progress=PROGRESS_27_DEFERRED)
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (27, 28)
               for f in findings)


def test_a_chain_through_a_deferred_link_earns_no_exemption(tmp_path: Path):
    """029 → 028 → 027 orders nothing if the middle link does not hold: 028 is
    ⏸️, so 029 is claimable before 027 lands. The filter is on the edges, which
    is what makes the transitive case come out right."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 lands first."),
        29: _spec_text(29, asserts=["src/cli.py"], deps="Item 028 lands first."),
    }, queue_items=(27, 28, 29),
       progress=PROGRESS.replace("- 📋 B. *(Item 028)*", "- ⏸️ B. *(Item 028)*"))
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (27, 29)
               for f in findings)


def test_a_chain_through_a_withdrawn_link_earns_no_exemption(tmp_path: Path):
    """The same chain with 028 📋 in a stage whose summary row is ❌: it has
    left the queue's way as a ❌ item has (issue #393), so 029 is claimable
    before 027 lands and the pair is judged."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 lands first."),
        29: _spec_text(29, asserts=["src/cli.py"], deps="Item 028 lands first."),
    }, queue_items=(27, 28, 29),
       progress=PROGRESS
       .replace("| 1 | Rules | G1 | 🚧 |",
                "| 1 | Rules | G1 | 🚧 |\n| 2 | Later | G1 | ❌ |")
       .replace("- 📋 B. *(Item 028)*\n", "")
       + "\n## Stage 2 — Later\n\n**Deliverables.**\n- 📋 B. *(Item 028)*\n")
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (27, 29)
               for f in findings)


def test_an_in_progress_dependency_still_exempts_the_pair(tmp_path: Path):
    """🚧 and 🔍 hold a dependent back exactly as 📋 does — the item is not in
    the base a dependent would branch from — so the ordering stands and the
    pair stays exempt. The filter is 'does this still block', not 'is this
    untouched'."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"], deps="Item 027 lands first."),
    }, progress=PROGRESS.replace("- 📋 A. *(Item 027)*", "- 🚧 A. *(Item 027)*"))
    findings, _ = _findings(repo)
    assert [f for f in findings if f.kind == "changes-pinned-state"] == []


def test_an_in_flight_pinning_item_keeps_its_exemption(tmp_path: Path):
    """The asymmetry is deliberate — do not "complete" it. Gating on the
    PINNING item's status would fire only outside this check's window (spec
    authoring, where nothing is built yet), and only in a state that already
    took an out-of-band claim. Meanwhile one deliverable bullet attributes its
    icon to every item in its trailing marker, so two items sharing a 🚧
    bullet would lose a legitimate exemption — errors invented on a normal
    in-flight queue, in exchange for a case `progress.md` cannot distinguish
    from that artifact."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"], deps="Item 027 lands first."),
    }, progress=PROGRESS.replace("- 📋 B. *(Item 028)*", "- 🚧 B. *(Item 028)*"))
    findings, _ = _findings(repo)
    assert [f for f in findings if f.kind == "changes-pinned-state"] == []


def test_the_pinned_state_message_names_the_dependency_remedy(tmp_path: Path):
    """A reader who hits the error needs the third way out — the two the
    message used to offer are both wrong for a validate item."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"]),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "changes-pinned-state")
    assert "## Dependencies" in hit.message


def test_a_later_item_retiring_the_earlier_items_test_is_exempt(tmp_path: Path):
    """The shape §1 → items prescribes for a sibling's schedule premise (issue
    #445): 027 pins the artifact 028 regenerates, 028 depends on 027 and lists
    027's test file under May change from the start, retiring the pin. The
    ordering runs the other way from the `Validate stage N` exemption, and the
    error used to stand with none of its remedies available until 027 merged."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["tests/test_027_topic.py"],
                       asserts=["docs/aide/artifact.json"]),
        28: _spec_text(28, may=["docs/aide/artifact.json",
                                "tests/test_027_topic.py"],
                       deps="Item 027 lands first; its pin is retired here."),
    })
    findings, _ = _findings(repo)
    assert [f for f in findings if f.kind == "changes-pinned-state"] == []


def test_a_later_changer_listing_none_of_the_pinners_tests_still_errors(
        tmp_path: Path):
    """The dependency alone retires nothing: 028 is built after 027 and so
    lands on top of 027's pin, and its spec says nothing about that test. The
    break is as undeclared as it was without the dependency."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["tests/test_027_topic.py"],
                       asserts=["docs/aide/artifact.json"]),
        28: _spec_text(28, may=["docs/aide/artifact.json",
                                "tests/test_028_topic.py"],
                       deps="Item 027 lands first."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (28, 27)
               for f in findings)


def test_listing_the_pinners_test_without_a_dependency_still_errors(
        tmp_path: Path):
    """The retirement needs the ordering too: with no declared dependency, 028
    may be built before 027 writes the test it lists, so nothing says which
    side lands first — the undeclared ordering this check exists to find."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["tests/test_027_topic.py"],
                       asserts=["docs/aide/artifact.json"]),
        28: _spec_text(28, may=["docs/aide/artifact.json",
                                "tests/test_027_topic.py"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (28, 27)
               for f in findings)


def test_sharing_a_non_test_path_with_the_pinner_retires_no_pin(tmp_path: Path):
    """Only a test file the pinner owns retires its pin. A second writer on one
    of the pinner's source files is a May change overlap, and the pin it breaks
    is still standing."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/gen.py", "tests/test_027_topic.py"],
                       asserts=["docs/aide/artifact.json"]),
        28: _spec_text(28, may=["docs/aide/artifact.json", "src/gen.py"],
                       deps="Item 027 lands first."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (28, 27)
               for f in findings)


def test_a_test_file_named_for_the_pinner_but_not_its_write_retires_nothing(
        tmp_path: Path):
    """The name alone is not ownership: 028 lists a `test_027_` file 027 never
    writes, so no test of 027's is retired and the pin still breaks."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["tests/test_027_topic.py"],
                       asserts=["docs/aide/artifact.json"]),
        28: _spec_text(28, may=["docs/aide/artifact.json",
                                "tests/test_027_other.py"],
                       deps="Item 027 lands first."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" and f.items == (28, 27)
               for f in findings)


def test_the_pinned_state_message_names_the_retirement_remedy(tmp_path: Path):
    """The prescribed shape has to be reachable from the error text: the
    fourth way out names the dependency and the pinner's test file under the
    changer's May change, and the section that prescribes it."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, asserts=["src/cli.py"]),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "changes-pinned-state")
    assert "to retire its pin" in hit.message
    assert "test_028_" in hit.message and "May change" in hit.message
    assert "item 028's own May change lists" in hit.message
    assert "§1 → items" in hit.message


def test_a_mutual_dependency_reports_the_cycle_without_hanging(tmp_path: Path):
    """The exemption walks the same edges the cycle check condemns, so it must
    survive a graph that has one — deriving the ordering must not hang on the
    very shape being reported."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"], deps="Item 028 lands first."),
        28: _spec_text(28, asserts=["src/cli.py"], deps="Item 027 lands first."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "dependency-cycle" for f in findings)


def test_built_after_closes_over_a_chain_and_over_a_cycle():
    assert aide._built_after({1: [2], 2: [3], 3: []}) == {1: {2, 3}, 2: {3}, 3: set()}
    # A cycle terminates, and no item is recorded as built after itself.
    assert aide._built_after({1: [2], 2: [1]}) == {1: {2}, 2: {1}}


def test_pinning_a_path_nobody_changes_is_fine(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"]),
        28: _spec_text(28, may=["src/b.py"], asserts=["src/untouched.py"]),
    })
    findings, _ = _findings(repo)
    assert findings == []


# --------------------------------------------------------------------------- #
# row 5 — the dependency graph
# --------------------------------------------------------------------------- #
def test_dependency_cycle_is_an_error(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 028 provides the API."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "dependency-cycle")
    assert hit.severity == "error"
    assert set(hit.items) == {27, 28}


def test_a_downstream_aside_does_not_create_a_cycle(tmp_path: Path):
    """`**Downstream` marks a forward reference, not a blocker — a plain
    'item NNN depends on this' aside used to register backwards."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"],
                       deps="None.\n\n**Downstream:** item 028 depends on this."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert not any(f.kind == "dependency-cycle" for f in findings)


def test_unknown_dependency_is_a_warning(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 999 provides it."),
        28: _spec_text(28, may=["src/b.py"]),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "unknown-dependency")
    assert hit.severity == "warning" and hit.items == (27, 999)


def test_dependency_on_a_real_earlier_item_is_not_flagged(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"]),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert findings == []


# --------------------------------------------------------------------------- #
# the ✅ discount — a merged item's claims are spent
# --------------------------------------------------------------------------- #
def test_a_completed_items_may_change_claim_is_spent(tmp_path: Path):
    """The recorded shape: item 118 (✅) claimed `spline.py`; item 119 exists to
    rewrite it. The conflict was real while both were live — once 118 merged,
    reporting it for the rest of the queue's life gives 119 an error it cannot
    clear without editing a completed item's spec."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/spline.py"]),
        28: _spec_text(28, may=["src/spline.py"]),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert findings == []


def test_a_completed_items_pin_is_retired(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/other.py"], asserts=["src/cli.py"]),
        28: _spec_text(28, may=["src/cli.py"]),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert findings == []


def test_a_completed_item_cannot_break_a_live_pin(tmp_path: Path):
    """The other side of the discount: what a merged item changed, it has
    already changed — the live spec's pin was authored against the result."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/other.py"], asserts=["src/cli.py"]),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert findings == []


def test_a_spent_item_is_discounted_on_both_sides_of_every_comparison(
        tmp_path: Path):
    """The sentence `aide check -h` states, exercised as one claim.

    Its two halves have a test each above — a spent item's pin is retired, and
    a spent item cannot break a live pin. Neither alone says "both sides", and
    "both sides" is what the help promises, so one item here is simultaneously
    the changer of what a live sibling pins and the pinner of what that sibling
    changes. Run for \u2705 and \u274c alike, because the help names both as spent.
    """
    for name, icon in (("merged", "\u2705"), ("excluded", "\u274c")):
        progress = PROGRESS.replace("- \U0001f4cb A. *(Item 027)*",
                                    f"- {icon} A. *(Item 027)*")
        repo = _make_repo(tmp_path / name, {
            27: _spec_text(27, may=["src/cli.py"], asserts=["src/rules.py"]),
            28: _spec_text(28, may=["src/rules.py"], asserts=["src/cli.py"]),
        }, progress=progress)
        findings, _ = _findings(repo)
        assert findings == [], (name, findings)


def test_conflicts_between_live_items_survive_the_discount(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/done.py"]),
        28: _spec_text(28, may=["src/shared.py"]),
        29: _spec_text(29, may=["src/shared.py"]),
    }, queue_items=(27, 28, 29),
       progress=PROGRESS_27_DONE.replace(
           "- 📋 B. *(Item 028)*", "- 📋 B. *(Item 028)*\n- 📋 C. *(Item 029)*"))
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "may-change-overlap")
    assert hit.items == (28, 29)


def test_a_cycle_among_completed_items_is_inert(tmp_path: Path):
    """A cycle every member of which merged has PROVED its order was
    satisfiable; reporting it as an error for the rest of the queue's life is
    exactly the unclearable-noise shape the discount removes."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 028 provides the API."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    }, progress=PROGRESS_27_DONE.replace("- 📋 B. *(Item 028)*",
                                         "- ✅ B. *(Item 028)*"))
    findings, _ = _findings(repo)
    assert not any(f.kind == "dependency-cycle" for f in findings)


def test_a_cycle_with_a_merged_member_is_broken_at_that_member(tmp_path: Path):
    """027 merged: 028's dependency on it is satisfied, and 027's own spec no
    longer waits on anything — nothing deadlocks."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 028 provides the API."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert not any(f.kind == "dependency-cycle" for f in findings)


def test_an_excluded_item_is_spent_too(tmp_path: Path):
    """❌ means dropped: claim never offers the item and an excluded dependency
    does not block, so its spec's claims and pins are as unclearable as a
    merged item's."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/shared.py"], asserts=["src/cli.py"]),
        28: _spec_text(28, may=["src/shared.py", "src/cli.py"]),
    }, progress=PROGRESS.replace("- 📋 A. *(Item 027)*", "- ❌ A. *(Item 027)*"))
    findings, _ = _findings(repo)
    assert findings == []


def test_a_deferred_item_stays_in_the_path_comparison(tmp_path: Path):
    """⏸️ is dormant, not dead — the deferred work returns, so a conflict with
    its claims is exactly what to surface while re-planning is still cheap."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/shared.py"]),
        28: _spec_text(28, may=["src/shared.py"]),
    }, progress=PROGRESS.replace("- 📋 A. *(Item 027)*", "- ⏸️ A. *(Item 027)*"))
    findings, _ = _findings(repo)
    assert any(f.kind == "may-change-overlap" for f in findings)


def test_a_deferred_item_drops_out_of_the_cycle_graph(tmp_path: Path):
    """A deferred dependency does not block `aide claim` (same status set as
    `_pick_item`), so a cycle through a deferred item cannot deadlock."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 028 provides the API."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    }, progress=PROGRESS.replace("- 📋 A. *(Item 027)*", "- ⏸️ A. *(Item 027)*"))
    findings, _ = _findings(repo)
    assert not any(f.kind == "dependency-cycle" for f in findings)


def test_a_spent_items_undeclared_scope_is_not_reported(tmp_path: Path):
    """The warning's remedy — add the section, get a human scope review — is
    unavailable once the item merged; reporting it forever is the unclearable
    noise this discount exists to remove. A LIVE undeclared spec still warns
    (pinned elsewhere in this file)."""
    repo = _make_repo(tmp_path, {
        27: "# Item 027 — Demo\n\n## Description\n\nNo authorised paths here.\n",
        28: _spec_text(28, may=["src/b.py"]),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert not any(f.kind == "undeclared-scope" for f in findings)


def test_a_spent_items_unknown_dependency_is_not_reported(tmp_path: Path):
    """'A typo here blocks the item forever' is false for an item that already
    merged — nothing is blocked, and the warning could never be cleared."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 999 provides it."),
        28: _spec_text(28, may=["src/b.py"]),
    }, progress=PROGRESS_27_DONE)
    findings, _ = _findings(repo)
    assert not any(f.kind == "unknown-dependency" for f in findings)


def test_a_cycle_among_live_items_is_still_an_error(tmp_path: Path):
    """The discount must remove only the inert reports — a live cycle is the
    deadlock the check exists to find."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"], deps="Item 028 provides the API."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "dependency-cycle" for f in findings)


# --------------------------------------------------------------------------- #
# a quoted gate reach is not a dependency
# --------------------------------------------------------------------------- #
def test_a_quoted_gate_blocks_list_creates_no_edges(tmp_path: Path):
    """Transcribing the gate row is the natural way to say which gate holds an
    item; the numbers in the quote are the gate's reach, not blockers. Read as
    edges they yielded cycles among items nobody ordered."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"],
                       deps="None. Waits on Gate 3 — `Blocks: items 028, 099.`"),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert not any(f.kind in ("dependency-cycle", "unknown-dependency")
                   for f in findings)


def test_numbers_before_a_blocks_quote_still_block(tmp_path: Path):
    """The exclusion is the line's remainder, not the line: a real dependency
    sharing a line with a gate quote must survive. The bold label is the other
    marked form a transcribed cell takes."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"],
                       deps="Item 028 provides the API. **Blocks**: item 999."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "dependency-cycle" for f in findings)
    assert not any(f.kind == "unknown-dependency" for f in findings)


def test_plain_prose_blocks_is_not_a_marker(tmp_path: Path):
    """Only a backticked or bold `Blocks:` label excludes. An English sentence
    carrying the word states real blockers, and an exclusion plain prose could
    trip would silently drop them — claim would then offer the item early."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"],
                       deps="Hard blocks: Item 028 must land first."),
        28: _spec_text(28, may=["src/b.py"], deps="Item 027 provides the schema."),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "dependency-cycle" for f in findings)


# --------------------------------------------------------------------------- #
# graceful degradation
# --------------------------------------------------------------------------- #
def test_undeclared_spec_is_reported_never_skipped(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: "# Item 027 — Demo\n\n## Description\n\nNo authorised paths here.\n",
        28: _spec_text(28, may=["src/b.py"]),
    })
    findings, _ = _findings(repo)
    hit = next(f for f in findings if f.kind == "undeclared-scope")
    assert hit.severity == "warning" and hit.items == (27,)
    assert "human scope review" in hit.message


def test_unspecced_items_are_counted_not_flagged(tmp_path: Path):
    """A queued item with no spec yet is the normal mid-queue state — that is
    what /aide-spec-queue exists to fill, not a conflict."""
    repo = _make_repo(tmp_path, {27: _spec_text(27, may=["src/a.py"])})
    findings, unspecced = _findings(repo)
    assert unspecced == [28]
    assert findings == []


def test_bookkeeping_files_are_not_an_overlap(tmp_path: Path):
    """Every item writes progress.md and insights.md — `aide scope` authorises
    both without them being listed. Two items 'conflicting' over progress.md is
    the claim protocol working, not a conflict. Observed as 4 of 16 warnings on
    a real consumer queue before this exclusion."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py", "docs/aide/progress.md",
                                "docs/aide/insights.md"]),
        28: _spec_text(28, may=["src/b.py", "docs/aide/progress.md",
                                "docs/aide/insights.md"]),
    })
    findings, _ = _findings(repo)
    assert findings == []


def test_pinning_a_bookkeeping_file_is_still_reported(tmp_path: Path):
    """The exclusion is for the overlap check only — pinning progress.md is a
    real assertion, and changing it under one is a real break."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["docs/aide/progress.md"]),
        28: _spec_text(28, may=["src/b.py"], asserts=["docs/aide/progress.md"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "changes-pinned-state" for f in findings)


def test_a_spec_that_only_pins_is_still_compared(tmp_path: Path):
    """An empty May change is not 'nothing declared'. A queue-end item
    changes only the bookkeeping every item may write, while pinning the tree
    it validates — treating that as undeclared would drop exactly the specs
    whose whole purpose is to assert, and miss siblings breaking their pins."""
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/a.py"]),
        28: _spec_text(28, asserts=["src/a.py"]),
    })
    findings, _ = _findings(repo)
    kinds = [f.kind for f in findings]
    assert "changes-pinned-state" in kinds
    assert "undeclared-scope" not in kinds


def test_a_section_with_both_lists_empty_is_undeclared(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27),
        28: _spec_text(28, may=["src/b.py"]),
    })
    findings, _ = _findings(repo)
    assert any(f.kind == "undeclared-scope" and f.items == (27,) for f in findings)


def test_report_without_queue_is_refused(tmp_path: Path, capsys):
    repo = _make_repo(tmp_path, {27: _spec_text(27, may=["src/a.py"])})
    rc = aide.main(["--repo", str(repo), "check", "--report",
                    str(tmp_path / "out.json")])
    assert rc == 2
    assert "--report needs --queue" in capsys.readouterr().err
    assert not (tmp_path / "out.json").exists()


def test_missing_queue_file_is_an_error(tmp_path: Path):
    repo = _make_repo(tmp_path, {27: _spec_text(27, may=["src/a.py"])})
    findings, _ = _findings(repo, queue=99)
    assert findings[0].kind == "missing-queue"


# --------------------------------------------------------------------------- #
# the command
# --------------------------------------------------------------------------- #
def test_check_queue_fails_on_an_error_finding(tmp_path: Path, capsys):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/other.py"], asserts=["src/cli.py"]),
    })
    rc = aide.main(["--repo", str(repo), "check", "--queue", "3"])
    assert rc == 1
    assert "Asserts against" in capsys.readouterr().out


def test_check_without_queue_is_unchanged(tmp_path: Path, capsys, monkeypatch):
    """The cross-spec checks are opt-in: a bare `aide check` must not start
    reporting them."""
    # Documents, not the machine: `aide check` also errors on what aide.toml
    # needs of this machine (issue #354), which a scratch directory lacks.
    monkeypatch.setattr(aide, "dependency_errors", lambda repo_root, config: [])
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/other.py"], asserts=["src/cli.py"]),
    })
    assert aide.main(["--repo", str(repo), "check"]) == 0
    assert "Asserts against" not in capsys.readouterr().out


def test_report_writes_the_json_seam(tmp_path: Path):
    repo = _make_repo(tmp_path, {
        27: _spec_text(27, may=["src/cli.py"]),
        28: _spec_text(28, may=["src/other.py"], asserts=["src/cli.py"]),
    })
    out = tmp_path / "status" / "queue-003.json"
    aide.main(["--repo", str(repo), "check", "--queue", "3", "--report", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["queue"] == 3
    assert payload["unspecced_items"] == []
    kinds = [f["kind"] for f in payload["findings"]]
    assert "changes-pinned-state" in kinds
    assert payload["findings"][0]["items"] == [27, 28]


# --------------------------------------------------------------------------- #
# the queue-end item — whether the queue needs one, reported both ways (#333)
# --------------------------------------------------------------------------- #
#: Stage 1 has two acceptance boxes, the first ticked; items 027 and 028 are
#: its deliverables, and a later stage 2 is untouched by queue 003.
PROGRESS_QE = """\
# Demo — Progress

## Stage summary

| Stage | Title | Objectives | Status |
|-------|-------|-----------|--------|
| 1 | Rules | G1 | 🚧 |
| 2 | Later | G1 | 📋 |

## Objective coverage

| Objective | Delivered by | Status |
|-----------|--------------|--------|
| G1 Rules | Stage 1, 2 | 🚧 |

## Stage 1 — Rules — 🚧

**Deliverables.**
- ✅ A. *(Item 026)*
- 📋 B. *(Item 027)*
- 📋 C. *(Item 028)*

**Acceptance.**
- [x] Rules load. *(accepted 2026-09-01 — test_026)*
- [ ] Rules fire.

## Stage 2 — Later — 📋

**Deliverables.**
- 📋 D. *(Item 040)*

**Acceptance.**
- [ ] Later works.
"""

_ANNOTATED_AC = ("## Acceptance Criteria\n\n"
                 "- [ ] **AC1: fires.** It fires. *(closes Stage 1 criterion 2)*\n\n")


def _qe_repo(tmp_path: Path, specs=None, queue_items=(27, 28), titles=None,
             progress: str = PROGRESS_QE, earlier=(26,)) -> Path:
    repo = _make_repo(tmp_path, specs or {}, queue_items=queue_items,
                      progress=progress)
    titles = titles or {}
    body = "\n\n".join(f"### Item {n:03d}: {titles.get(n, f'Thing {n}')}\n"
                       f"Does a thing." for n in queue_items)
    q = repo / "docs" / "aide" / "queue"
    (q / "queue-003.md").write_text(f"# Demo — Work Queue 003\n\n{body}\n",
                                    encoding="utf-8")
    early = "\n\n".join(f"### Item {n:03d}: Thing {n}\nDone." for n in earlier)
    (q / "queue-002.md").write_text(f"# Demo — Work Queue 002\n\n{early}\n",
                                    encoding="utf-8")
    return repo


def _qe(repo: Path, kind: str):
    cfg = aide.load_config(repo)
    return [f for f in aide.queue_end_findings(repo, cfg, 3) if f.kind == kind]


def test_a_stage_closing_queue_with_an_unannotated_criterion_needs_a_queue_end_item(
        tmp_path: Path):
    """No spec yet — the plan-time state — so the unticked criterion is
    annotated by nothing, and the queue's last item is a deliverable. The
    ticked criterion is not a reason: it is attested already."""
    repo = _qe_repo(tmp_path)
    hits = _qe(repo, "queue-end-needed")
    assert len(hits) == 1 and hits[0].severity == "warning"
    msg = hits[0].message
    assert "closes stage 1" in msg and "criterion 2 of stage 1" in msg
    assert "2 item(s) on the queue not yet specced" in msg
    assert "Validate stage 1" in msg
    assert "stage 2" not in msg


def test_a_queue_end_item_among_the_final_items_meets_the_need(tmp_path: Path):
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29),
                    titles={29: "Validate stage 1: Rules"},
                    progress=PROGRESS_QE.replace(
                        "- 📋 C. *(Item 028)*",
                        "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*"))
    assert _qe(repo, "queue-end-needed") == []
    assert _qe(repo, "queue-end-idle") == []


#: Items 027–029 open, 029 the stage's queue-end item.
_PROGRESS_QE_29 = PROGRESS_QE.replace(
    "- 📋 C. *(Item 028)*", "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*")


def test_an_open_queue_end_item_that_is_not_final_meets_the_need(tmp_path: Path):
    """Issue #347: an item added after planning is listed after `Validate
    stage 1`. `aide claim` holds the open queue-end item until 028 has left
    the way, so it still runs last and meets the need — the warning is about
    where the file lists it, not a missing item to plan."""
    repo = _qe_repo(tmp_path, queue_items=(27, 29, 28),
                    titles={29: "Validate stage 1: Rules"}, progress=_PROGRESS_QE_29)
    assert _qe(repo, "queue-end-needed") == []
    hits = _qe(repo, "queue-end-not-last")
    assert len(hits) == 1 and hits[0].severity == "warning"
    assert hits[0].items == (29, 28)
    assert "move it to the end of the queue" in hits[0].message


def test_an_item_depending_on_the_queue_end_item_is_not_out_of_place(
        tmp_path: Path):
    """028's spec names 029 as a dependency, so it belongs after it: claim
    does not hold 029 behind it, and the check does not ask to move 029."""
    repo = _qe_repo(tmp_path, queue_items=(27, 29, 28),
                    specs={28: "# Item 028 — Thing 28\n\n## Dependencies\n\n"
                               "- Item 029\n"},
                    titles={29: "Validate stage 1: Rules"}, progress=_PROGRESS_QE_29)
    assert _qe(repo, "queue-end-not-last") == []


def test_a_spent_queue_end_item_that_is_not_final_does_not_meet_the_need(
        tmp_path: Path):
    """A ✅ `Validate stage 1` listed before open work ran before that work:
    the need is still there, and a settled record is never out of place."""
    progress = _PROGRESS_QE_29.replace("- 📋 Stage validation.", "- ✅ Stage validation.")
    repo = _qe_repo(tmp_path, queue_items=(27, 29, 28),
                    titles={29: "Validate stage 1: Rules"}, progress=progress)
    assert len(_qe(repo, "queue-end-needed")) == 1
    assert _qe(repo, "queue-end-not-last") == []


def test_a_settled_record_never_puts_a_queue_end_item_out_of_place(tmp_path: Path):
    """Only open work after an open queue-end item counts (the #338
    convention): a ✅, ❌ or ⏸️ item listed after it is history, not a plan."""
    for k, icon in enumerate(("✅", "❌", "⏸️")):
        progress = _PROGRESS_QE_29.replace("- 📋 C. *(Item 028)*",
                                           f"- {icon} C. *(Item 028)*")
        repo = _qe_repo(tmp_path / f"s{k}",
                        queue_items=(27, 29, 28),
                        titles={29: "Validate stage 1: Rules"}, progress=progress)
        assert _qe(repo, "queue-end-not-last") == [], icon


def test_a_withdrawn_stages_planned_item_never_puts_a_queue_end_item_out_of_place(
        tmp_path: Path):
    """Issue #389: 040 sits in stage 2, withdrawn whole (❌ summary row).
    Claim never offers it 📋 and it holds nothing, so listing it after
    `Validate stage 1` is not out of place; started 🚧 there, it is live work
    and still is."""
    withdrawn = _PROGRESS_QE_29.replace("| 2 | Later | G1 | 📋 |",
                                        "| 2 | Later | G1 | ❌ |")
    repo = _qe_repo(tmp_path / "planned", queue_items=(27, 28, 29, 40),
                    titles={29: "Validate stage 1: Rules"}, progress=withdrawn)
    assert _qe(repo, "queue-end-not-last") == []
    started = withdrawn.replace("- 📋 D. *(Item 040)*", "- 🚧 D. *(Item 040)*")
    repo = _qe_repo(tmp_path / "started", queue_items=(27, 28, 29, 40),
                    titles={29: "Validate stage 1: Rules"}, progress=started)
    hits = _qe(repo, "queue-end-not-last")
    assert len(hits) == 1 and hits[0].items == (29, 40)


def test_two_trailing_queue_end_items_are_in_place(tmp_path: Path):
    """A queue may end on two queue-end items; neither is out of place for
    the other."""
    progress = _PROGRESS_QE_29.replace(
        "- 📋 D. *(Item 040)*", "- 📋 D. *(Item 040)*\n- 📋 Stage 2 check. *(Item 030)*")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29, 30), progress=progress,
                    titles={29: "Validate stage 1: Rules", 30: "Validate stage 2: Later"})
    assert _qe(repo, "queue-end-not-last") == []
    assert aide.queue_end_holds(repo, aide.load_config(repo),
                                (repo / "docs/aide/queue/queue-003.md")
                                .read_text(encoding="utf-8"),
                                aide._progress_item_status(repo, aide.load_config(repo))
                                ) == {29: [27, 28], 30: [27, 28]}


def test_every_criterion_annotated_or_ticked_is_no_need(tmp_path: Path):
    repo = _qe_repo(tmp_path, specs={
        27: "# Item 027 — B\n\n" + _ANNOTATED_AC,
        28: "# Item 028 — C\n\n## Acceptance Criteria\n\n- [ ] **AC1: c.** C.\n",
    })
    assert _qe(repo, "queue-end-needed") == []


def test_an_annotation_outside_acceptance_criteria_closes_nothing(tmp_path: Path):
    repo = _qe_repo(tmp_path, specs={
        27: "# Item 027 — B\n\n## Description\n\n(closes Stage 1 criterion 2)\n",
    })
    assert len(_qe(repo, "queue-end-needed")) == 1


def test_a_queue_end_items_own_annotation_does_not_retire_its_need(tmp_path: Path):
    """Otherwise the item's spec would be the reason the item is not needed."""
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29),
                    titles={29: "Validate stage 1: Rules"},
                    progress=PROGRESS_QE.replace(
                        "- 📋 C. *(Item 028)*",
                        "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*"),
                    specs={29: "# Item 029 — Validate stage 1: Rules\n\n" + _ANNOTATED_AC})
    assert _qe(repo, "queue-end-idle") == []


def test_a_queue_that_leaves_stage_work_to_a_later_queue_closes_nothing(
        tmp_path: Path):
    """Item 028 is listed on no queue yet, so queue 003 does not close stage 1."""
    repo = _qe_repo(tmp_path, queue_items=(27,))
    assert _qe(repo, "queue-end-needed") == []


def test_an_unreferenced_open_bullet_keeps_the_stage_open(tmp_path: Path):
    """A 📋 bullet with no item reference is work no queue has taken on."""
    unref = PROGRESS_QE.replace("- 📋 C. *(Item 028)*",
                                "- 📋 C. *(Item 028)*\n- 📋 Unqueued work.")
    assert _qe(_qe_repo(tmp_path, progress=unref), "queue-end-needed") == []


def test_a_deferred_bullet_never_holds_closure(tmp_path: Path):
    """⏸️ on an earlier queue, ⏸️ with no reference, and ⏸️ on this queue:
    none holds the stage open — deferred work is not what closes it, and a
    bullet that held closure would hold it for as long as nobody resumes it."""
    earlier = PROGRESS_QE.replace("- ✅ A. *(Item 026)*", "- ⏸️ A. *(Item 026)*")
    assert len(_qe(_qe_repo(tmp_path / "a", progress=earlier), "queue-end-needed")) == 1
    unref = PROGRESS_QE.replace("- 📋 C. *(Item 028)*",
                                "- 📋 C. *(Item 028)*\n- ⏸️ Later, maybe.")
    assert len(_qe(_qe_repo(tmp_path / "b", progress=unref), "queue-end-needed")) == 1
    here = PROGRESS_QE.replace("- 📋 C. *(Item 028)*", "- ⏸️ C. *(Item 028)*")
    assert len(_qe(_qe_repo(tmp_path / "c", progress=here), "queue-end-needed")) == 1


def test_an_excluded_bullet_is_skipped(tmp_path: Path):
    """An ❌ bullet whose item is on no queue at all does not hold closure."""
    dropped = PROGRESS_QE.replace("- 📋 C. *(Item 028)*",
                                  "- 📋 C. *(Item 028)*\n- ❌ Dropped. *(Item 099)*")
    assert len(_qe(_qe_repo(tmp_path, progress=dropped), "queue-end-needed")) == 1


def test_an_unverified_capability_row_is_a_need(tmp_path: Path):
    table = ("## Environment-Gated Capability Verification\n\n"
             "| Capability | Package / Tool | Introduced by | Status | Notes |\n"
             "|---|---|---|---|---|\n"
             "| GPU path | torch | Stage 1 *(Item 027)* | ❓ Unverified | — |\n\n")
    progress = PROGRESS_QE.replace("## Stage 1 — Rules", table + "## Stage 1 — Rules")
    progress = progress.replace("- [ ] Rules fire.", "- [x] Rules fire. *(accepted)*")
    msg = _qe(_qe_repo(tmp_path, progress=progress), "queue-end-needed")[0].message
    assert "'GPU path'" in msg and "criterion" not in msg


def test_an_item_declaring_an_environment_gated_capability_is_a_need(tmp_path: Path):
    progress = PROGRESS_QE.replace("- [ ] Rules fire.", "- [x] Rules fire. *(accepted)*")
    repo = _qe_repo(tmp_path, progress=progress, specs={
        27: "# Item 027 — B\n\n## Environment / Hardware Dependencies\n\n- torch\n"})
    msg = _qe(repo, "queue-end-needed")[0].message
    assert "item(s) 027 declaring an environment-gated capability" in msg


_ENV_SPEC = "# Item 026 — A\n\n## Environment / Hardware Dependencies\n\n- torch\n"
#: Every criterion ticked, so only the capability reasons can speak.
_PROGRESS_TICKED = PROGRESS_QE.replace("- [ ] Rules fire.", "- [x] Rules fire. *(accepted)*")


def _with_row(progress: str, introduced: str, status: str) -> str:
    table = ("## Environment-Gated Capability Verification\n\n"
             "| Capability | Package / Tool | Introduced by | Status | Notes |\n"
             "|---|---|---|---|---|\n"
             f"| GPU path | torch | {introduced} | {status} | — |\n\n")
    return progress.replace("## Stage 1 — Rules", table + "## Stage 1 — Rules")


def test_a_merged_env_item_with_no_row_is_still_a_need(tmp_path: Path):
    """Item 026 merged on an earlier queue and never wrote its row: that gap
    is exactly the queue-end item's work, so ✅ does not retire the need."""
    repo = _qe_repo(tmp_path, progress=_PROGRESS_TICKED, specs={26: _ENV_SPEC})
    msg = _qe(repo, "queue-end-needed")[0].message
    assert "item(s) 026 declaring an environment-gated capability" in msg


def test_a_merged_env_item_with_a_verified_row_is_no_need(tmp_path: Path):
    progress = _with_row(_PROGRESS_TICKED, "Stage 1 *(Item 026)*",
                         "✅ Verified (2026-09-01, CI)")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-needed") == []


def test_a_row_naming_another_item_does_not_cover_it(tmp_path: Path):
    progress = _with_row(_PROGRESS_TICKED, "Stage 1 *(Item 027)*",
                         "✅ Verified (2026-09-01, CI)")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert len(_qe(repo, "queue-end-needed")) == 1


def test_a_stage_only_row_covers_the_stages_env_items(tmp_path: Path):
    progress = _with_row(_PROGRESS_TICKED, "Stage 1", "✅ Verified (2026-09-01, CI)")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-needed") == []


def test_an_excluded_env_item_is_no_need(tmp_path: Path):
    progress = _PROGRESS_TICKED.replace("- ✅ A. *(Item 026)*", "- ❌ A. *(Item 026)*")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-needed") == []


def test_a_deferred_env_item_is_no_need(tmp_path: Path):
    """⏸️ is skipped like ❌: a deferred capability is not this stage's to verify."""
    progress = _PROGRESS_TICKED.replace("- ✅ A. *(Item 026)*", "- ⏸️ A. *(Item 026)*")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-needed") == []


def test_an_item_only_row_covers_its_item(tmp_path: Path):
    """The item reference is matched on its own: a cell naming only the item
    covers it, with no `Stage N` beside it."""
    progress = _with_row(_PROGRESS_TICKED, "*(Item 026)*", "✅ Verified (2026-09-01, CI)")
    repo = _qe_repo(tmp_path, progress=progress, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-needed") == []


def test_one_stage_only_row_covers_one_env_item(tmp_path: Path):
    """One row is one capability: two env items and one stage-only row leave
    the higher-numbered item uncovered."""
    progress = _with_row(_PROGRESS_TICKED, "Stage 1", "✅ Verified (2026-09-01, CI)")
    repo = _qe_repo(tmp_path, progress=progress, specs={
        26: _ENV_SPEC, 27: _ENV_SPEC.replace("026", "027")})
    msg = _qe(repo, "queue-end-needed")[0].message
    assert "item(s) 027 declaring" in msg and "026" not in msg


def test_an_env_item_outside_the_stage_is_not_its_need(tmp_path: Path):
    """Item 040 is stage 2's; its spec says nothing about stage 1."""
    repo = _qe_repo(tmp_path, progress=_PROGRESS_TICKED, specs={
        40: _ENV_SPEC.replace("026", "040")})
    assert _qe(repo, "queue-end-needed") == []


def test_a_planned_queue_end_item_stays_needed_once_the_env_item_merges(
        tmp_path: Path):
    """The mirror symptom: the env item ✅ with no row must not make the
    planned `Validate stage 1` read as idle."""
    progress = _PROGRESS_TICKED.replace(
        "- 📋 C. *(Item 028)*", "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29), progress=progress,
                    titles={29: "Validate stage 1: Rules"}, specs={26: _ENV_SPEC})
    assert _qe(repo, "queue-end-idle") == [] and _qe(repo, "queue-end-needed") == []


def test_a_queue_end_item_with_nothing_to_do_is_reported(tmp_path: Path):
    progress = PROGRESS_QE.replace("- [ ] Rules fire.", "- [x] Rules fire. *(accepted)*")
    progress = progress.replace(
        "- 📋 C. *(Item 028)*", "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29), progress=progress,
                    titles={29: "Validate stage 1: Rules"})
    hits = _qe(repo, "queue-end-idle")
    assert len(hits) == 1 and hits[0].items == (29,) and hits[0].severity == "warning"
    assert "stage 1 has nothing left for it" in hits[0].message


def test_a_spent_queue_end_item_is_never_reported_idle(tmp_path: Path):
    """Item 029 merged; 027 is still open so the queue is not spent. With
    every criterion ticked the stage has no need, and the merged item is a
    record, not a plan anyone can drop."""
    progress = _PROGRESS_TICKED.replace(
        "- 📋 C. *(Item 028)*", "- 📋 C. *(Item 028)*\n- ✅ Stage validation. *(Item 029)*")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29), progress=progress,
                    titles={29: "Validate stage 1: Rules"})
    assert _qe(repo, "queue-end-idle") == []
    live = progress.replace("- ✅ Stage validation.", "- 📋 Stage validation.")
    assert len(_qe(_qe_repo(tmp_path / "live", queue_items=(27, 28, 29), progress=live,
                            titles={29: "Validate stage 1: Rules"}),
                   "queue-end-idle")) == 1


def test_a_queue_end_item_a_fix_round_reopened_is_never_reported_idle(tmp_path: Path):
    """Issue #332: a CI finding that traces to no item goes to the queue-end
    item, reopened. Its first run ticked the stage's boxes, so it has no need
    left — and it is back for a fix, not a plan to drop before it is claimed."""
    progress = _PROGRESS_TICKED.replace(
        "- 📋 C. *(Item 028)*",
        "- 📋 C. *(Item 028)*\n- 📋 Stage validation. *(Item 029)*\n"
        "  - **2026-09-29** → reopened: CI build: the runner image [CI round 1]")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29), progress=progress,
                    titles={29: "Validate stage 1: Rules"})
    assert _qe(repo, "queue-end-idle") == []


def test_a_deferred_queue_end_item_is_never_reported_idle(tmp_path: Path):
    progress = _PROGRESS_TICKED.replace(
        "- 📋 C. *(Item 028)*", "- 📋 C. *(Item 028)*\n- ⏸️ Stage validation. *(Item 029)*")
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29), progress=progress,
                    titles={29: "Validate stage 1: Rules"})
    assert _qe(repo, "queue-end-idle") == []


def test_a_queue_whose_only_open_work_in_the_stage_is_deferred_closes_nothing(
        tmp_path: Path):
    """Agrees with `queue_is_open`: 027 merged, 028 deferred, so the queue is
    not open and the stage's remaining work is deferred — no need, no idle,
    and a ⏸️ bullet alone does not make the queue close the stage."""
    progress = PROGRESS_QE.replace("- 📋 B. *(Item 027)*", "- ✅ B. *(Item 027)*")
    progress = progress.replace("- 📋 C. *(Item 028)*", "- ⏸️ C. *(Item 028)*")
    repo = _qe_repo(tmp_path, progress=progress)
    assert _qe(repo, "queue-end-needed") == [] and _qe(repo, "queue-end-idle") == []
    cfg = aide.load_config(repo)
    qtext = (repo / "docs/aide/queue/queue-003.md").read_text(encoding="utf-8")
    assert not aide.queue_is_open(qtext, aide._progress_item_status(repo, cfg))
    # The `touches` half on its own: queue 003 is still open through stage
    # 2's item, and its only stage 1 reference is the deferred bullet.
    alone = _qe_repo(tmp_path / "alone", progress=progress, queue_items=(28, 40),
                     earlier=(26, 27))
    needs = [f.message for f in _qe(alone, "queue-end-needed")]
    assert any("closes stage 2" in m for m in needs)
    assert not any("closes stage 1" in m for m in needs)


def test_a_queue_end_item_for_a_stage_the_queue_does_not_close_is_reported(
        tmp_path: Path):
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29),
                    titles={29: "Validate stage 2: Later"})
    hits = _qe(repo, "queue-end-idle")
    assert any("does not close stage 2" in f.message for f in hits)
    assert len(_qe(repo, "queue-end-needed")) == 1


def test_a_queue_end_title_naming_no_stage_is_reported(tmp_path: Path):
    repo = _qe_repo(tmp_path, queue_items=(27, 28, 29),
                    titles={29: "Validate stage: all of it"})
    assert any("names no stage" in f.message for f in _qe(repo, "queue-end-idle"))


def test_a_spent_queue_is_reported_neither_way(tmp_path: Path):
    progress = PROGRESS_QE.replace("- 📋 B. *(Item 027)*", "- ✅ B. *(Item 027)*")
    progress = progress.replace("- 📋 C. *(Item 028)*", "- ✅ C. *(Item 028)*")
    repo = _qe_repo(tmp_path, progress=progress)
    assert _qe(repo, "queue-end-needed") == [] and _qe(repo, "queue-end-idle") == []


def test_the_need_reaches_check_as_a_warning_and_the_report(tmp_path: Path, capsys):
    """What the planner runs: `check --queue NNN`, before any spec exists —
    and the `--report` worklist the spec-reviewer reads once they do."""
    repo = _qe_repo(tmp_path)
    report = tmp_path / "report.json"
    aide.main(["--repo", str(repo), "check", "--queue", "3", "--report", str(report)])
    out = capsys.readouterr().out
    assert "warning: queue 003 closes stage 1 and needs a queue-end item" in out
    kinds = [f["kind"] for f in json.loads(report.read_text(encoding="utf-8"))["findings"]]
    assert kinds == ["queue-end-needed"]


def test_spec_closed_criteria_reads_the_annotation_and_a_list():
    text = ("## Acceptance Criteria\n\n- AC1 *(closes Stage 20 criterion 3)*\n"
            "- AC2 *(closes Stage 20 criteria 4, 5)*\n\n## Testing Strategy\n\n"
            "- x: *(closes Stage 20 criterion 9)*\n")
    assert aide.spec_closed_criteria(text) == {(20, 3), (20, 4), (20, 5)}


def test_queue_end_stages_reads_the_title():
    assert aide.queue_end_stages("Validate stage 32: Things") == [32]
    assert aide.queue_end_stages("Validate stage 31 and 32: Things") == [31, 32]
    assert aide.queue_end_stages("Validate stage: things") == []
    assert aide.queue_end_stages("Add a stage validator") is None
