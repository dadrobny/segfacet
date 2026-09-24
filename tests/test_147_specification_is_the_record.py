"""Tests for item 147 -- collapsing the five partial sources onto the
failure-mode specification (``segfacet.failure_modes``).

Re-pointed at the signed-off catalogue (item 150, 2026-09-14, revised
2026-09-15), which re-organised the taxonomy under this item's tests:
sixteen modes in a one-tier hierarchy plus one ``ConditionSpec`` (FOV
truncation), ids re-assigned, and vision.md §6's list demoted from "the
names" to provenance (``VISION_SEED_DISPOSITION``). Every AC below is
unchanged in what it claims; the ids, counts and section headings it claims
it about are the signed-off ones. The three AC whose subject moved carry the
reason at their own section heading: AC5 (§6 titles are provenance, not
names), AC8 (the rung-less entries are the six ``proposed`` modes, not the
single mode 10) and AC10 (the corrected label-sequence sentence is mode
9's).

AC -> test map (house style, items 144-146):

- AC1:  test_ac1_one_source_for_mode_names_in_production_code,
        test_adv_ac1_walker_flags_a_planted_mode_name_literal
- AC2:  test_ac2_one_source_for_rung_vocabulary,
        test_adv_ac2_walker_flags_a_planted_mode_rungs_shaped_dict
- AC3:  test_ac3_mode_anchor_paths_stays_under_its_own_metric_label,
        test_adv_ac3_walker_flags_a_planted_real_reference
- AC4:  retired (item 152, 2026-09-16 correction) -- duplicated item 152's
        AC3 under stale substring semantics that the correction narrowed
        away from. See `tests/test_152_retire_vision_seed.py`
- AC5:  retired (item 152, 2026-09-16) with `vision_seed_conflicts()` --
        vision.md v4 carries no numbered §6 list left to parse. See
        `tests/test_152_retire_vision_seed.py`
- AC6:  test_ac6_matrix_titles_come_from_the_specification
- AC7:  test_ac7_mode_rungs_are_derived_from_the_specification
- AC8:  test_ac8_absent_rung_renders_explicitly_for_every_edgeless_mode
- AC9:  test_ac9_every_mechanism_names_a_token_that_resolves_live
- AC10: test_ac10_label_sequence_corrected_sentence_is_measured,
        test_adv_ac10_stale_false_claim_fails_the_tree_wide_check
- AC11: test_ac11_sequence_rule_caps_nothing
- AC12: test_ac12_declared_mode_outside_specification_is_reported
- AC13: test_ac13_intended_rule_whose_rule_declares_no_such_mode_is_reported
- AC14: test_ac14_corpus_case_the_specification_does_not_carry_is_reported
- AC15: test_ac15_corpus_case_disagreeing_with_specification_is_reported
- AC16: test_ac16_corpus_case_designating_unregistered_rule_id_is_reported
- AC17: test_ac17_both_checks_clean_and_deterministic_on_shipped_tree
- AC18: test_ac18_rule_mode_declaration_rejects_a_bare_string
- AC19: test_ac19_rule_mode_declaration_rejects_a_list
- AC20: test_ac20_reserved_corpus_evidence_tag_is_gone_from_the_tree,
        test_adv_ac20_corpus_tag_no_longer_binds_special_behaviour
- AC21: test_ac21_failure_mode_names_is_derived_from_the_specification,
        test_adv_ac21_missing_key_zero_fails_the_check
- AC22: test_ac22_committed_corpora_agree_with_the_derived_name_map
- AC23: test_ac23_new_fields_reach_both_artifacts,
        test_adv_ac23_empty_short_name_renders_explicitly
- AC24: test_ac24_all_three_artifact_pairs_regenerate_byte_identically
- AC25: test_ac25_matrix_note_names_the_specification_not_a_retired_constant
- AC26: test_ac26_every_corpus_case_agrees_and_status_derives_correctly
- AC27: test_ac27_aide_check_reports_no_error_and_no_new_warning_class

Adversarial / edge-case scenarios (see individual tests above, named
``test_adv_*``) plus:

- test_adv_ac18_evidence_tuple_element_type_still_enforced (a valid tuple
  construction is unaffected by the new type checks).
- Every AC12-AC16 test additionally calls ``monkeypatch.undo()`` mid-test and
  re-asserts the checker's baseline output, proving each conflict retracts
  when its patch is retracted -- the checks are live, not constants.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src" / "segfacet"
_TESTS_ROOT = _REPO_ROOT / "tests"

_COMMITTED_FM_JSON = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
_COMMITTED_FM_MD = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"
_COMMITTED_TRACE_JSON = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.json"
_COMMITTED_TRACE_MD = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.md"
_COMMITTED_CAT_JSON = _REPO_ROOT / "docs" / "aide" / "feature_catalogue.generated.json"
_COMMITTED_CAT_MD = _REPO_ROOT / "docs" / "aide" / "feature_catalogue.generated.md"


# =========================================================================== #
# House fixtures / helpers
# =========================================================================== #


@pytest.fixture
def isolated_registry():
    """Snapshot/restore the rule registry (the house pattern from
    ``test_136``/``test_137``/``test_138``/``test_144``/``test_146``)."""
    from segfacet.heuristics.rule import _RULES

    snapshot = dict(_RULES)
    yield
    _RULES.clear()
    _RULES.update(snapshot)


def _all_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def _all_test_py_files():
    return sorted(_TESTS_ROOT.rglob("*.py"))


def _rel(path: Path, root: Path = _REPO_ROOT) -> str:
    return path.relative_to(root).as_posix()


def _collect_string_literals(source: str) -> set:
    """Every ``ast.Constant`` string value anywhere in *source* (module,
    class and function bodies alike)."""
    tree = ast.parse(source)
    literals = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)
    return literals


@pytest.fixture(scope="module")
def src_literals_by_file():
    """AST-parse every ``src/segfacet/*.py`` file once into its string
    literal set (AC1/AC2's shared, module-scoped fixture)."""
    result = {}
    for path in _all_src_py_files():
        result[path] = _collect_string_literals(path.read_text(encoding="utf-8"))
    return result


def _offending_files(literals_by_file: dict, needles: set) -> set:
    offenders = set()
    for path, literals in literals_by_file.items():
        if literals & needles:
            offenders.add(_rel(path))
    return offenders


@pytest.fixture(scope="module")
def matrix():
    """One unpatched ``build_matrix()`` call, shared by AC6/AC7/AC8 (the
    Testing Strategy's shared fixture)."""
    import segfacet.traceability as traceability

    return traceability.build_matrix()


@pytest.fixture(scope="module")
def measured():
    """``segfacet.failure_modes.measured_firing`` cached per case_id (the
    item 145/146 pattern) -- AC26's cost control."""
    import segfacet.failure_modes as fm

    cache: dict = {}

    def _get(case):
        if case.case_id not in cache:
            cache[case.case_id] = fm.measured_firing(case)
        return cache[case.case_id]

    return _get


def _mode_section(markdown: str, mode_id: int) -> str:
    """The rendered section for *mode_id*. A top-level mode's heading reads
    ``## Mode 9: ...``; a sub-mode's reads ``## Mode 3 (1.2, sub-mode of
    1): ...`` (item 150's one-tier hierarchy), so both spellings are
    matched, and a section runs to the next ``## `` heading of any kind --
    the conditions section and the vision-seed-disposition section are
    ``## `` headings too."""
    match = re.search(
        rf"^## Mode {mode_id}(?::| \().*?(?=^## |\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"expected a '## Mode {mode_id}' section"
    return match.group(0)


def _table_header_cells(markdown: str) -> list:
    header_line = next(
        (line for line in markdown.splitlines() if line.startswith("| Mode ")),
        None,
    )
    assert header_line is not None, "expected a '| Mode ...' table header row"
    return [c.strip() for c in header_line.strip("|").split("|")]


def _row_for_mode(markdown: str, mode: int):
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] == str(mode):
            return cells
    return None


def _references_name(tree: ast.AST, name: str) -> bool:
    """True if *tree* contains an actual code reference to *name* -- an AST
    ``Name``/``Attribute`` use or an ``ImportFrom`` import -- never a comment
    (outside the AST entirely) or a string that merely mentions the name."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            return True
        if isinstance(node, ast.Attribute) and node.attr == name:
            return True
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == name or alias.asname == name:
                    return True
    return False


def _docstring_constant_ids(tree: ast.AST) -> set:
    """``id()`` of every ``ast.Constant`` string node sitting in docstring
    position (module, class or function body's first statement)."""
    ids = set()

    def _mark(node):
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            ids.add(id(body[0].value))

    _mark(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            _mark(node)
    return ids


# =========================================================================== #
# AC1: one source for mode names in production code
# =========================================================================== #


def test_ac1_one_source_for_mode_names_in_production_code(src_literals_by_file):
    import segfacet.failure_modes as fm

    needles = set()
    for mode in fm.SPECIFICATION.values():
        needles.add(mode.name)
        needles.add(mode.short_name)

    offenders = _offending_files(src_literals_by_file, needles)
    assert offenders == {
        "src/segfacet/failure_modes.py",
        "src/segfacet/synth/intensity.py",
        # Item 153 re-keyed the Stage-18/29 eval harness off the frozen
        # pre-sign-off name map onto metric/operator names, with the
        # specification's mode ids carried in a nullable field derived from
        # SPECIFICATION/CONDITIONS -- so `eval/per_mode.py` is no longer a
        # second source of mode-name literals and drops out of this set.
    }, offenders


def test_adv_ac1_walker_flags_a_planted_mode_name_literal(tmp_path):
    """Positive control: the same string-literal walker used above must
    flag a planted violation, so a clean AC1 result is not vacuous."""
    import segfacet.failure_modes as fm

    name = next(iter(fm.SPECIFICATION.values())).name
    planted = tmp_path / "planted_offender.py"
    planted.write_text(f"_PLANTED_MODE_NAME = {name!r}\n", encoding="utf-8")

    literals = _collect_string_literals(planted.read_text(encoding="utf-8"))
    assert name in literals, "walker failed to catch a planted mode-name literal"


# =========================================================================== #
# AC2: one source for the rung vocabulary
# =========================================================================== #


def test_ac2_one_source_for_rung_vocabulary(src_literals_by_file):
    import segfacet.failure_modes as fm
    import segfacet.traceability as traceability

    needles = set(fm.EVIDENCE_RUNGS)
    offenders = _offending_files(src_literals_by_file, needles)
    assert offenders == {"src/segfacet/failure_modes.py"}, offenders

    for name in ("MODE_RUNGS", "ModeRung", "RUNGS", "RUNG_LABELS"):
        assert not hasattr(traceability, name), name


def test_adv_ac2_walker_flags_a_planted_mode_rungs_shaped_dict(tmp_path):
    """Positive control: a planted ``MODE_RUNGS``-shaped dict literal (one
    rung-vocabulary string inside it) is caught by the same walker."""
    import segfacet.failure_modes as fm

    rung = fm.EVIDENCE_RUNGS[0]
    planted = tmp_path / "planted_mode_rungs.py"
    planted.write_text(
        "MODE_RUNGS = {\n"
        f"    1: {{'rung': {rung!r}, 'mechanism': 'planted, for a test.'}},\n"
        "}\n",
        encoding="utf-8",
    )

    literals = _collect_string_literals(planted.read_text(encoding="utf-8"))
    assert rung in literals, "walker failed to catch a planted rung literal"


# =========================================================================== #
# AC3: MODE_ANCHOR_PATHS stays, under its metric label
# =========================================================================== #


def test_ac3_mode_anchor_paths_stays_under_its_own_metric_label(matrix):
    import segfacet.failure_modes as fm
    import segfacet.feature_docs as feature_docs_module
    import segfacet.traceability as traceability

    # The signed-off key set (item 150, 2026-09-15 revision): the Stage-18
    # metric anchors cover modes 1, 4, 6, 8, 9 and 15 -- mode 1 carries two
    # paths (offset and fragmentation index), and the FOV-truncation anchor
    # lives in `CONDITION_ANCHOR_PATHS` since that mode became a condition.
    assert set(feature_docs_module.MODE_ANCHOR_PATHS.keys()) == {1, 4, 6, 8, 9, 15}
    assert set(feature_docs_module.MODE_ANCHOR_PATHS) <= set(fm.SPECIFICATION)
    assert set(feature_docs_module.CONDITION_ANCHOR_PATHS) <= set(fm.CONDITIONS)

    checked_any = False
    for mode in fm.SPECIFICATION.values():
        for feature in mode.candidate_features:
            if feature.role == "stage18-metric-anchor":
                checked_any = True
                anchors = feature_docs_module.MODE_ANCHOR_PATHS.get(mode.id, ())
                assert feature.path in anchors, (mode.id, feature.path, anchors)
    assert checked_any, "expected >=1 stage18-metric-anchor candidate feature"

    referencing = set()
    for path in _all_src_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _references_name(tree, "MODE_ANCHOR_PATHS"):
            referencing.add(_rel(path, root=_SRC_ROOT))
    assert referencing == {
        "feature_docs.py",
        "catalogue.py",
        "traceability.py",
        "failure_modes.py",
    }, referencing

    md = traceability.render_markdown(matrix)
    headers = _table_header_cells(md)
    anchor_headers = [h for h in headers if "anchor" in h.lower()]
    assert anchor_headers, headers
    read_path_headers = [h for h in headers if "read" in h.lower() and "path" in h.lower()]
    assert set(anchor_headers).isdisjoint(read_path_headers), headers


def test_adv_ac3_walker_flags_a_planted_real_reference(tmp_path):
    """Positive control: the same reference walker used above must flag a
    planted real use (an Attribute read), so a clean AC3 result is not
    vacuous -- and must not flag a planted comment-only mention."""
    planted_real = tmp_path / "planted_real_reference.py"
    planted_real.write_text(
        "import segfacet.feature_docs as feature_docs_module\n"
        "\n"
        "anchors = feature_docs_module.MODE_ANCHOR_PATHS\n",
        encoding="utf-8",
    )
    tree = ast.parse(planted_real.read_text(encoding="utf-8"))
    assert _references_name(tree, "MODE_ANCHOR_PATHS")

    planted_comment = tmp_path / "planted_comment_mention.py"
    planted_comment.write_text(
        "# see feature_docs.MODE_ANCHOR_PATHS for the per-mode metric path\n"
        "x = 1\n",
        encoding="utf-8",
    )
    tree_comment = ast.parse(planted_comment.read_text(encoding="utf-8"))
    assert not _references_name(tree_comment, "MODE_ANCHOR_PATHS")


# =========================================================================== #
# AC4: the vision §6 parse has one home
#
# Retired (item 152, 2026-09-16 correction), not re-pointed: AC4's surviving
# claim ("no module under src/segfacet/ holds a non-docstring string constant
# naming vision.md") is exactly item 152's AC3, and the item-152 correction
# narrowed that predicate from a substring match to a path-shaped match
# (`test_152_retire_vision_seed.py::_names_vision_md_as_a_path`) precisely
# because the substring form this test used (`_references_vision_md`) trips
# on the AC10/AC11 provenance literals `failure_modes.py` is required to
# carry (e.g. "## Provenance: vision.md v3 section 6 seed titles"). Keeping
# a second copy here under the old substring semantics would make this test
# red the moment item 152 lands, over text the correction explicitly
# exempts. See
# `tests/test_152_retire_vision_seed.py::test_ac3_no_production_module_names_vision_md_as_a_path`
# for the one surviving copy of this check.
# =========================================================================== #


# =========================================================================== #
# AC5: the vision §6 seed list is provenance, and every title disposes
#
# Re-targeted at the item-150 sign-off (2026-09-14). AC5's original claim --
# "modes 1-8's `name` fields equal vision.md §6's numbered list" -- was
# retired with the taxonomy: §6's titles are the SEED the catalogue started
# from and provide no ids (one title retired, one re-homed as a condition,
# one split, ids re-assigned). The claim kept in that direction is
# `VISION_SEED_DISPOSITION` / `vision_seed_conflicts()`: every §6 title has a
# disposition, and every disposition resolves.
# =========================================================================== #


# test_ac5_every_vision_seed_title_disposes_and_resolves and
# test_adv_ac5_unresolvable_disposition_is_reported retired (item 152,
# 2026-09-16), with `vision_seed_conflicts()`/`vision_seed_titles()`:
# vision.md v4's §6 carries no numbered list left to parse, so there is no
# live title set for a disposition to resolve against. The frozen-provenance
# and every-disposition-resolves claims they made, positive control
# included, are
# `tests/test_152_retire_vision_seed.py::test_ac6_provenance_map_is_frozen_at_its_v3_value`
# and its AC7 pair.


# =========================================================================== #
# AC6: the matrix's mode titles come from the specification
# =========================================================================== #


def test_ac6_matrix_titles_come_from_the_specification(matrix):
    import segfacet.failure_modes as fm

    records_by_mode = {m.mode: m for m in matrix.modes}
    assert set(records_by_mode) == set(fm.SPECIFICATION)
    for mode_id, mode in fm.SPECIFICATION.items():
        assert records_by_mode[mode_id].title == mode.name, mode_id
    for mode_id in (9, 10):
        assert records_by_mode[mode_id].title, mode_id


# =========================================================================== #
# AC7: MODE_RUNGS is retired and the matrix's rungs are derived
# =========================================================================== #


def test_ac7_mode_rungs_are_derived_from_the_specification(matrix):
    import segfacet.failure_modes as fm

    records_by_mode = {m.mode: m for m in matrix.modes}
    for mode_id, mode in fm.SPECIFICATION.items():
        expected = fm.derive_mode_rung(mode) or ""
        assert records_by_mode[mode_id].rung == expected, mode_id
    assert records_by_mode[9].rung != ""


# =========================================================================== #
# AC8: a mode with no edges renders its absent rung explicitly
#
# The catalogue's rung-less entries are its `proposed` ones: modes 5
# (holes), 7 (hallucinated vertebra), 10 (skipped level label), 11
# (unprompted numbering variant), 12 (shifted label sequence), 13 (collapsed
# labels) and 14 (duplicated label) since the item-150 sign-off's 2026-09-15
# revision, which narrowed mode 10 to the label alone. AC8 was written when
# that was the single mode 10.
# =========================================================================== #


def test_ac8_absent_rung_renders_explicitly_for_every_edgeless_mode(matrix):
    import segfacet.failure_modes as fm
    import segfacet.traceability as traceability

    edgeless = [mode for mode in fm.SPECIFICATION.values() if not mode.intended_rules]
    assert {mode.id for mode in edgeless} == {5, 7, 10, 11, 12, 13, 14}, [
        mode.id for mode in edgeless
    ]

    records_by_mode = {m.mode: m for m in matrix.modes}
    d = traceability.matrix_to_dict(matrix)
    md = traceability.render_markdown(matrix)

    for mode in edgeless:
        assert fm.derive_mode_rung(mode) is None, mode.id
        assert records_by_mode[mode.id].rung == "", mode.id
        assert d["modes"][str(mode.id)]["rung"] is None, mode.id
        row = _row_for_mode(md, mode.id)
        assert row is not None, f"expected a rendered row for mode {mode.id}"
        assert any("(none)" in cell for cell in row), row

    # ... and a mode that does carry edges renders a rung, so the assertion
    # above is not passing on a table that renders "(none)" everywhere.
    with_edges = next(mode for mode in fm.SPECIFICATION.values() if mode.intended_rules)
    assert records_by_mode[with_edges.id].rung != "", with_edges.id


# =========================================================================== #
# AC9: every mode's mechanism sentence names something that resolves live
# =========================================================================== #


def _token_in_mechanism(token: str, mechanism: str) -> bool:
    return re.search(r"\b" + re.escape(token) + r"\b", mechanism) is not None


@pytest.mark.parametrize("mode_id", range(1, 17))
def test_ac9_every_mechanism_names_a_token_that_resolves_live(mode_id):
    import segfacet.failure_modes as fm
    import segfacet.feature_docs as feature_docs_module

    mode = fm.SPECIFICATION[mode_id]
    assert mode.mechanism, mode_id

    anchors = set(feature_docs_module.MODE_ANCHOR_PATHS.get(mode_id, ()))
    candidate_feature_paths = {feature.path for feature in mode.candidate_features}
    candidates = set(anchors)
    candidates |= candidate_feature_paths
    candidates |= {case.case_id for case in mode.corpus_cases}
    candidates |= {rule.rule_id for rule in mode.intended_rules}
    assert candidates, (mode_id, "expected >=1 live-resolving candidate token")

    # Anchor / candidate-feature paths (dotted -- plain substring is
    # specific enough, matching item 138's AC31 precedent); case/rule ids
    # (bare identifiers -- word boundary, so a one-character-off near-miss
    # does not count).
    path_like = anchors | candidate_feature_paths
    resolved = any(path in mode.mechanism for path in path_like) or any(
        _token_in_mechanism(token, mode.mechanism)
        for token in (candidates - path_like)
    )
    assert resolved, (mode_id, mode.mechanism, candidates)


# =========================================================================== #
# AC10: the corrected label-sequence sentence, measured
#
# Item 147 settled the correction on the then-mode 7 ("non-continuous label
# sequence"); the item-150 sign-off re-homed that mode as mode 6
# ("Implausible label sequence"), and its 2026-09-15 revision split that into
# three, the sequence rule and `sequence_break` landing on mode 9
# ("Out-of-order label sequence"), carrying the sentence with it. The claim
# is unchanged: `rank(v) == v - 1` is false, and the sentence that replaced
# it must name what makes it false.
# =========================================================================== #


def test_ac10_label_sequence_corrected_sentence_is_measured():
    import segfacet.failure_modes as fm
    from segfacet.labels import CANONICAL_ORDER, DEFAULT_LABEL_MAP

    rank_of = {name: index for index, name in enumerate(CANONICAL_ORDER)}
    value_of = {name: value for value, name in DEFAULT_LABEL_MAP.items()}

    for lumbar in ("L1", "L2", "L3", "L4", "L5"):
        assert rank_of[lumbar] == value_of[lumbar], lumbar
    assert rank_of["T12"] == value_of["T12"] - 1

    example = ["L1", "T12", "L2", "L5"]
    ranks = [rank_of[name] for name in example]
    descents = sum(1 for a, b in zip(ranks, ranks[1:]) if b < a)
    assert descents == 1, ranks

    # Scoped to the sources this item collapses onto the specification
    # (spec AC10) -- src/segfacet/eval/severity_ladder.py (item 141, Stage
    # 21) carries the same false claim but is out of this item's authorised
    # paths; that is a recorded, separate defect (insights.md, item 147,
    # 2026-09-04), not this AC's to absorb.
    _AC10_SWEPT_PATHS = (
        _SRC_ROOT / "failure_modes.py",
        _SRC_ROOT / "traceability.py",
        _SRC_ROOT / "synth" / "perturbation.py",
    )
    swept_paths = list(_AC10_SWEPT_PATHS) + sorted((_SRC_ROOT / "heuristics").rglob("*.py"))
    assert swept_paths, "expected >=1 path to sweep"
    offending = [
        _rel(path)
        for path in swept_paths
        if "rank(v) == v - 1" in path.read_text(encoding="utf-8")
    ]
    assert offending == [], offending

    mechanism = fm.SPECIFICATION[9].mechanism
    assert mechanism, "expected a non-empty mode-9 mechanism sentence"
    for token in ("CANONICAL_ORDER", "T13"):
        assert token in mechanism, (token, mechanism)
    assert "rank(v) == v - 1" not in mechanism, mechanism


def test_adv_ac10_stale_false_claim_fails_the_tree_wide_check(tmp_path):
    """Positive control: a planted label-sequence reason containing the false claim
    is caught by the same tree-wide scan AC10 relies on."""
    planted = tmp_path / "planted_label_sequence_reason.py"
    planted.write_text(
        'reason = "single rank descent (rank(v) == v - 1 under the default)."\n',
        encoding="utf-8",
    )
    assert "rank(v) == v - 1" in planted.read_text(encoding="utf-8")


# =========================================================================== #
# AC11: the sequence rule caps nothing, measured
# =========================================================================== #


def _sequence_record(out_of_order):
    return {
        "relationships": {
            "present_levels": [],
            "missing_levels": [],
            "is_continuous": len(out_of_order) == 0,
            "out_of_order_labels": list(out_of_order),
        },
        "per_label": {},
        "overlaps": {},
    }


def test_ac11_sequence_rule_caps_nothing():
    from segfacet.config import default_config
    from segfacet.heuristics.sequence import SequenceRule

    rule = SequenceRule()
    config = default_config()

    one_descent = rule.evaluate(_sequence_record(["T12"]), config)
    assert len(one_descent) == 1, one_descent

    two_descent = rule.evaluate(_sequence_record(["T12", "L6"]), config)
    assert len(two_descent) == 1, two_descent


# =========================================================================== #
# AC12-AC16: adversarial conformance-check shapes
# =========================================================================== #


def test_ac12_declared_mode_outside_specification_is_reported(isolated_registry, monkeypatch):
    import segfacet.catalogue as catalogue
    import segfacet.heuristics.rule as rule_mod
    from segfacet.heuristics.rule import _RULES

    baseline = catalogue.rule_declaration_conflicts()

    rule = _RULES["bounds"]
    replacement = rule_mod.RuleModeDeclaration(
        modes=(999,), evidence=("test-evidence-item147",)
    )
    monkeypatch.setattr(rule, "mode_declaration", replacement)

    conflicts = catalogue.rule_declaration_conflicts()
    assert any("bounds" in msg and "999" in msg for msg in conflicts), conflicts

    monkeypatch.undo()
    retracted = catalogue.rule_declaration_conflicts()
    assert retracted == baseline, retracted


def test_ac13_intended_rule_whose_rule_declares_no_such_mode_is_reported(monkeypatch):
    import segfacet.failure_modes as fm

    baseline = fm.specification_conflicts()

    # Case 1: redirected to a registered rule that does not declare mode 1.
    bad_edge = fm.IntendedRule(
        rule_id="coverage", detector_ids=(), evidence_rung="needs-real-data"
    )
    patched_mode = dataclasses.replace(fm.SPECIFICATION[1], intended_rules=(bad_edge,))
    patched_map = dict(fm.SPECIFICATION)
    patched_map[1] = patched_mode
    monkeypatch.setattr(fm, "SPECIFICATION", patched_map)

    conflicts = fm.specification_conflicts()
    assert any("coverage" in msg and "1" in msg for msg in conflicts), conflicts

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline

    # Case 2: redirected to a rule_id no rule registers.
    unregistered_edge = fm.IntendedRule(
        rule_id="__item147_no_such_rule__", detector_ids=(), evidence_rung="needs-real-data"
    )
    patched_mode_2 = dataclasses.replace(
        fm.SPECIFICATION[1], intended_rules=(unregistered_edge,)
    )
    patched_map_2 = dict(fm.SPECIFICATION)
    patched_map_2[1] = patched_mode_2
    monkeypatch.setattr(fm, "SPECIFICATION", patched_map_2)

    conflicts_2 = fm.specification_conflicts()
    assert any(
        "__item147_no_such_rule__" in msg and "1" in msg for msg in conflicts_2
    ), conflicts_2

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline


def test_ac14_corpus_case_the_specification_does_not_carry_is_reported(monkeypatch):
    import segfacet.failure_modes as fm
    import segfacet.synth.corpus as corpus_module
    from segfacet.synth.perturbation import CASE_KIND_FAILURE

    baseline = fm.specification_conflicts()

    manifest = copy.deepcopy(corpus_module.load_manifest())
    assert manifest["cases"], "expected a non-empty geometric manifest"
    target = manifest["cases"][0]
    original_mode = target["failure_mode"]
    # Point the case at a mode whose corpus_cases do not carry this case_id.
    other_mode = next(m for m in fm.SPECIFICATION if m != original_mode and m != 0)
    target["failure_mode"] = other_mode
    target["condition"] = ""
    target["kind"] = CASE_KIND_FAILURE

    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: manifest)

    conflicts = fm.specification_conflicts()
    assert any(
        target["case_id"] in msg and str(other_mode) in msg for msg in conflicts
    ), conflicts

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline


def test_ac14_intensity_manifest_is_covered_by_the_same_check(monkeypatch):
    import segfacet.failure_modes as fm
    import segfacet.synth.intensity as intensity_module
    from segfacet.synth.perturbation import CASE_KIND_FAILURE, corpus_case_kind

    baseline = fm.specification_conflicts()

    manifest = copy.deepcopy(intensity_module.load_intensity_manifest())
    assert manifest["cases"], "expected a non-empty intensity manifest"
    target = next(c for c in manifest["cases"] if corpus_case_kind(c) == CASE_KIND_FAILURE)
    original_mode = target["failure_mode"]
    other_mode = next(
        m for m in fm.SPECIFICATION if m not in (0, original_mode)
    )
    target["failure_mode"] = other_mode

    monkeypatch.setattr(
        intensity_module, "load_intensity_manifest", lambda *a, **k: manifest
    )

    conflicts = fm.specification_conflicts()
    assert any(
        target["case_id"] in msg and str(other_mode) in msg for msg in conflicts
    ), conflicts

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline


def test_ac15_geometric_case_expectation_disagreement_is_reported(monkeypatch):
    import segfacet.failure_modes as fm
    import segfacet.synth.corpus as corpus_module
    from segfacet.synth.perturbation import CASE_KIND_FAILURE, corpus_case_kind

    baseline = fm.specification_conflicts()

    manifest = copy.deepcopy(corpus_module.load_manifest())
    target = next(
        c
        for c in manifest["cases"]
        if corpus_case_kind(c) == CASE_KIND_FAILURE and c.get("expected_rule_ids")
    )
    target["expected_rule_ids"] = list(target["expected_rule_ids"]) + [
        "__item147_extra_rule_id__"
    ]

    monkeypatch.setattr(corpus_module, "load_manifest", lambda *a, **k: manifest)

    conflicts = fm.specification_conflicts()
    assert any(
        target["case_id"] in msg and "__item147_extra_rule_id__" in msg
        for msg in conflicts
    ), conflicts

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline


def test_ac15_intensity_case_expectation_disagreement_is_reported(monkeypatch):
    import segfacet.failure_modes as fm
    import segfacet.synth.intensity as intensity_module
    from segfacet.synth.perturbation import CASE_KIND_FAILURE, corpus_case_kind

    baseline = fm.specification_conflicts()

    manifest = copy.deepcopy(intensity_module.load_intensity_manifest())
    target = next(c for c in manifest["cases"] if corpus_case_kind(c) == CASE_KIND_FAILURE)
    target["expected_firing"] = list(target["expected_firing"]) + [
        "__item147_extra_rule_id__"
    ]

    monkeypatch.setattr(
        intensity_module, "load_intensity_manifest", lambda *a, **k: manifest
    )

    conflicts = fm.specification_conflicts()
    assert any(
        target["case_id"] in msg and "__item147_extra_rule_id__" in msg
        for msg in conflicts
    ), conflicts

    monkeypatch.undo()
    assert fm.specification_conflicts() == baseline


def test_ac16_corpus_case_designating_unregistered_rule_id_is_reported(monkeypatch):
    import segfacet.catalogue as catalogue

    baseline = catalogue.rule_declaration_conflicts()

    real_map = catalogue.scan_synth_rule_mode_map()
    patched_map = dict(real_map)
    patched_map["__item147_unregistered_rule__"] = (1,)
    monkeypatch.setattr(
        catalogue, "_scan_synth_rule_mode_map", lambda: patched_map
    )

    conflicts = catalogue.rule_declaration_conflicts()
    assert any(
        "__item147_unregistered_rule__" in msg for msg in conflicts
    ), conflicts

    monkeypatch.undo()
    assert catalogue.rule_declaration_conflicts() == baseline


# =========================================================================== #
# AC17: both checks are clean on the shipped tree
# =========================================================================== #


def test_ac17_both_checks_clean_and_deterministic_on_shipped_tree():
    import segfacet.catalogue as catalogue
    import segfacet.failure_modes as fm

    assert fm.specification_conflicts() == ()
    assert fm.specification_conflicts() == fm.specification_conflicts()

    assert catalogue.rule_declaration_conflicts() == ()
    assert catalogue.rule_declaration_conflicts() == catalogue.rule_declaration_conflicts()


# =========================================================================== #
# AC18/AC19: RuleModeDeclaration rejects a bare string / a list
# =========================================================================== #


def test_ac18_rule_mode_declaration_rejects_a_bare_string():
    from segfacet.heuristics.rule import RuleModeDeclaration

    # Old code (item 136) does not raise here at all -- a bare str is itself
    # iterable-of-non-empty-strings (its characters); "evidence" + "tuple"
    # together pin the new outer check's message, not the retired weakness.
    with pytest.raises(ValueError, match="evidence") as excinfo:
        RuleModeDeclaration(modes=(1,), evidence="corpus-derived")
    assert "tuple" in str(excinfo.value).lower(), excinfo.value

    # Old code *does* raise here (character-wise type mismatch), but with a
    # message that never says "tuple" -- pin the new check's message shape,
    # not the pre-existing per-element loop's.
    with pytest.raises(ValueError, match="modes") as excinfo:
        RuleModeDeclaration(modes="12", evidence=("test-evidence",))
    assert "tuple" in str(excinfo.value).lower(), excinfo.value


def test_ac19_rule_mode_declaration_rejects_a_list():
    from segfacet.heuristics.rule import RuleModeDeclaration

    with pytest.raises(ValueError, match="evidence"):
        RuleModeDeclaration(modes=(1,), evidence=["test-evidence"])

    with pytest.raises(ValueError, match="modes"):
        RuleModeDeclaration(modes=[1], evidence=("test-evidence",))


def test_adv_ac18_evidence_tuple_element_type_still_enforced():
    from segfacet.heuristics.rule import RuleModeDeclaration

    # The control: a valid tuple construction is unaffected by the new checks.
    valid = RuleModeDeclaration(modes=(1, 2), evidence=("free-form-note",))
    assert valid.modes == (1, 2)
    assert valid.evidence == ("free-form-note",)


# =========================================================================== #
# AC20: the reserved "corpus" evidence tag is gone from the tree
# =========================================================================== #


def _rule_mode_declaration_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name == "RuleModeDeclaration":
            yield node


def _evidence_elements(call: ast.Call):
    for kw in call.keywords:
        if kw.arg == "evidence" and isinstance(kw.value, (ast.Tuple, ast.List)):
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    yield elt.value


def test_ac20_reserved_corpus_evidence_tag_is_gone_from_the_tree():
    offenders = []
    calls_seen = 0
    for path in _all_src_py_files() + _all_test_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for call in _rule_mode_declaration_calls(tree):
            calls_seen += 1
            if "corpus" in set(_evidence_elements(call)):
                offenders.append(_rel(path))
    # Non-vacuity guard: an empty `offenders` list only means "no declaration
    # passes 'corpus'" if the walker actually found declarations to inspect.
    # Renaming ``RuleModeDeclaration``, or moving the shipped declarations out
    # of ``src/segfacet/`` and ``tests/``, would otherwise turn this check into
    # a silent pass rather than a failure naming what moved. Measured on this
    # tree, 2026-09-04: 42 calls across both trees.
    assert calls_seen >= 10, (
        f"expected the AST walker to find the shipped RuleModeDeclaration "
        f"calls across src/segfacet/ and tests/, found {calls_seen}"
    )
    assert offenders == [], offenders

    membership_offenders = []
    scanned = 0
    for path in _all_src_py_files():
        scanned += 1
        text = path.read_text(encoding="utf-8")
        if re.search(r'"corpus"\s+(?:not\s+)?in\s+\S*evidence', text):
            membership_offenders.append(_rel(path))
    assert scanned, "expected >=1 src/segfacet/ module to scan"
    assert membership_offenders == [], membership_offenders


def test_adv_ac20_corpus_tag_no_longer_binds_special_behaviour(isolated_registry, monkeypatch):
    """evidence=("corpus",) is now an ordinary tag: the declaration ->
    corpus conflict direction fires identically whether or not it is
    present, since the retired branch no longer gates on it.

    The reserved literal is built at runtime (never a source-level
    ``ast.Constant`` reading "corpus"), so this test does not itself trip
    AC20's tree-wide AST sweep above -- that sweep is a static-literal
    scan, not a runtime-value ban, and this is the one legitimate place a
    live ``"corpus"``-valued declaration must still be constructible."""
    import segfacet.catalogue as catalogue
    import segfacet.heuristics.rule as rule_mod
    from segfacet.heuristics.rule import _RULES

    rule = _RULES["sequence"]
    original = rule.mode_declaration
    reserved_tag = "cor" + "pus"

    monkeypatch.setattr(
        rule,
        "mode_declaration",
        rule_mod.RuleModeDeclaration(modes=original.modes, evidence=(reserved_tag,)),
    )
    with_corpus_tag = catalogue.rule_declaration_conflicts()

    monkeypatch.setattr(
        rule,
        "mode_declaration",
        rule_mod.RuleModeDeclaration(modes=original.modes, evidence=("unrelated-tag",)),
    )
    without_corpus_tag = catalogue.rule_declaration_conflicts()

    assert with_corpus_tag == without_corpus_tag, (with_corpus_tag, without_corpus_tag)


# =========================================================================== #
# AC21: FAILURE_MODE_NAMES is derived from the specification
# =========================================================================== #


def test_ac21_failure_mode_names_is_derived_from_the_specification():
    import segfacet.failure_modes as fm
    import segfacet.synth.perturbation as perturbation

    assert set(perturbation.FAILURE_MODE_NAMES) - {0} == set(fm.SPECIFICATION)
    assert perturbation.FAILURE_MODE_NAMES[0] == fm.CLEAN_CONTROL_NAME
    for mode_id, mode in fm.SPECIFICATION.items():
        assert perturbation.FAILURE_MODE_NAMES[mode_id] == mode.short_name, mode_id


def test_adv_ac21_missing_key_zero_fails_the_check():
    """Positive control: a FAILURE_MODE_NAMES-shaped mapping missing key 0
    fails the exact AC21 assertion this item pins."""
    import segfacet.failure_modes as fm

    names_missing_zero = {mode_id: mode.short_name for mode_id, mode in fm.SPECIFICATION.items()}
    assert 0 not in names_missing_zero
    with pytest.raises(KeyError):
        assert names_missing_zero[0] == fm.CLEAN_CONTROL_NAME


# =========================================================================== #
# AC22: the committed corpora do not move
# =========================================================================== #


def test_ac22_committed_corpora_agree_with_the_derived_name_map():
    import segfacet.failure_modes as fm
    import segfacet.synth.corpus as corpus_module
    import segfacet.synth.intensity as intensity_module

    derived = fm.failure_mode_names()
    assert derived, "expected a non-empty derived name map"

    geometric_cases = corpus_module.load_manifest()["cases"]
    assert geometric_cases, "expected a non-empty geometric manifest"
    condition_cases = 0
    for case in geometric_cases:
        # A case carrying `failure_mode == 0` **and** a `condition` is a
        # condition fixture, not a clean control (item 150:
        # `crop_at_border` became the FOV-truncation condition's
        # case). Its `failure_mode_name` is the condition's `short_name`;
        # `failure_mode_names()[0]` -- the clean-control name -- belongs
        # only to a case with no condition.
        condition_id = case.get("condition") or ""
        if condition_id:
            assert case["failure_mode"] == 0, case["case_id"]
            assert condition_id in fm.CONDITIONS, (case["case_id"], condition_id)
            assert (
                case["failure_mode_name"] == fm.CONDITIONS[condition_id].short_name
            ), case["case_id"]
            condition_cases += 1
            continue
        assert case["failure_mode_name"] == derived[case["failure_mode"]], case["case_id"]
    assert condition_cases, "expected >=1 condition case in the geometric manifest"

    intensity_cases = intensity_module.load_intensity_manifest()["cases"]
    assert intensity_cases, "expected a non-empty intensity manifest"
    for case in intensity_cases:
        assert case["failure_mode_name"] == derived[case["failure_mode"]], case["case_id"]


# =========================================================================== #
# AC23: the specification's new fields reach both artifacts
# =========================================================================== #


def test_ac23_new_fields_reach_both_artifacts(regenerated_failure_modes):
    import segfacet.failure_modes as fm

    payload = json.loads(regenerated_failure_modes.json_a.read_text(encoding="utf-8"))
    assert payload["modes"], "expected a non-empty rendered mode list"
    assert len(payload["modes"]) == len(fm.SPECIFICATION)
    for mode_record in payload["modes"]:
        assert "short_name" in mode_record, mode_record["id"]
        assert "mechanism" in mode_record, mode_record["id"]

    md_text = regenerated_failure_modes.md_a.read_text(encoding="utf-8")
    for mode_id, mode in fm.SPECIFICATION.items():
        section = _mode_section(md_text, mode_id)
        assert mode.short_name in section, mode_id
        assert mode.mechanism in section, mode_id


def test_adv_ac23_empty_short_name_renders_explicitly(monkeypatch):
    import segfacet.failure_modes as fm

    patched_mode = dataclasses.replace(fm.SPECIFICATION[3], short_name="")
    patched_map = dict(fm.SPECIFICATION)
    patched_map[3] = patched_mode
    monkeypatch.setattr(fm, "SPECIFICATION", patched_map)

    md = fm.render_markdown()
    section = _mode_section(md, 3)
    assert "(none)" in section, section


# =========================================================================== #
# AC24: all three generated artifact pairs regenerate byte-identically
# =========================================================================== #


def _assert_lf_only_single_trailing_newline(raw: bytes):
    """*raw* must be undecoded bytes -- ``Path.read_text()`` applies
    universal-newline translation and would mask a genuine CRLF."""
    text = raw.decode("utf-8")
    assert "\r" not in text
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_ac24_all_three_artifact_pairs_regenerate_byte_identically(
    tmp_path, regenerated_failure_modes, regenerated_traceability
):
    import segfacet.catalogue as catalogue
    import segfacet.failure_modes as fm
    from segfacet.synth.golden import assert_matches_committed_artifact

    # -- failure_modes.generated.{json,md} --------------------------------- #
    fm_json_a, fm_md_a = regenerated_failure_modes.json_a, regenerated_failure_modes.md_a
    assert fm_json_a.read_bytes() == regenerated_failure_modes.json_b.read_bytes()
    assert fm_md_a.read_bytes() == regenerated_failure_modes.md_b.read_bytes()
    _assert_lf_only_single_trailing_newline(fm_json_a.read_bytes())
    _assert_lf_only_single_trailing_newline(fm_md_a.read_bytes())
    assert_matches_committed_artifact(fm_json_a, _COMMITTED_FM_JSON)
    # Markdown: structural section comparison (no ground for byte-exact
    # comparison exists in tests/committed_artifact_guard.py, and this item
    # adds none) -- extracted mode headings must agree. A sub-mode's heading
    # carries its path and parent ("## Mode 3 (1.2, sub-mode of 1): ...")
    # since item 150, so both spellings are captured; capturing only the
    # top-level spelling would silently compare six of the ten.
    _HEADING_RE = r"^## Mode (\d+)((?: \([^)]*\))?): (.+)$"
    fresh_headings = {
        mode_id: (suffix, title)
        for mode_id, suffix, title in re.findall(
            _HEADING_RE, fm_md_a.read_text(encoding="utf-8"), flags=re.MULTILINE
        )
    }
    committed_headings = {
        mode_id: (suffix, title)
        for mode_id, suffix, title in re.findall(
            _HEADING_RE, _COMMITTED_FM_MD.read_text(encoding="utf-8"), flags=re.MULTILINE
        )
    }
    assert len(fresh_headings) == len(fm.SPECIFICATION), sorted(fresh_headings)
    assert fresh_headings == committed_headings

    # -- traceability_matrix.generated.{json,md} ---------------------------- #
    trace_json_a, trace_md_a = regenerated_traceability.json_a, regenerated_traceability.md_a
    assert trace_json_a.read_bytes() == regenerated_traceability.json_b.read_bytes()
    assert trace_md_a.read_bytes() == regenerated_traceability.md_b.read_bytes()
    _assert_lf_only_single_trailing_newline(trace_json_a.read_bytes())
    _assert_lf_only_single_trailing_newline(trace_md_a.read_bytes())
    assert_matches_committed_artifact(trace_json_a, _COMMITTED_TRACE_JSON)
    # Markdown: the item 146 precedent (decode-wrapped full-text compare).
    fresh_md_bytes = trace_md_a.read_bytes()
    committed_md_bytes = _COMMITTED_TRACE_MD.read_bytes()
    assert fresh_md_bytes, "expected non-empty traceability markdown"
    assert fresh_md_bytes.decode("utf-8") == committed_md_bytes.decode("utf-8")

    # -- feature_catalogue.generated.{json,md} ------------------------------ #
    cat_json_a, cat_md_a = tmp_path / "cat_a.json", tmp_path / "cat_a.md"
    cat_json_b, cat_md_b = tmp_path / "cat_b.json", tmp_path / "cat_b.md"
    catalogue.main(["--json", str(cat_json_a), "--md", str(cat_md_a)])
    catalogue.main(["--json", str(cat_json_b), "--md", str(cat_md_b)])
    assert cat_json_a.read_bytes() == cat_json_b.read_bytes()
    assert cat_md_a.read_bytes() == cat_md_b.read_bytes()
    _assert_lf_only_single_trailing_newline(cat_json_a.read_bytes())
    _assert_lf_only_single_trailing_newline(cat_md_a.read_bytes())
    assert_matches_committed_artifact(cat_json_a, _COMMITTED_CAT_JSON)
    fresh_cat_md_bytes = cat_md_a.read_bytes()
    committed_cat_md_bytes = _COMMITTED_CAT_MD.read_bytes()
    assert fresh_cat_md_bytes, "expected non-empty catalogue markdown"
    assert fresh_cat_md_bytes.decode("utf-8") == committed_cat_md_bytes.decode("utf-8")


# =========================================================================== #
# AC25: the matrix no longer advertises a retired constant
# =========================================================================== #


def test_ac25_matrix_note_names_the_specification_not_a_retired_constant(matrix):
    assert "failure_modes.py" in matrix.note, matrix.note
    assert "MODE_RUNGS" not in matrix.note, matrix.note
    assert '"corpus"' not in matrix.note, matrix.note
    assert "'corpus'" not in matrix.note, matrix.note


# =========================================================================== #
# AC26: no rule firing moves
# =========================================================================== #


#: The lifecycle status every catalogue entry derives from live state as
#: signed off (item 150, 2026-09-14, revised 2026-09-15). Authored status is
#: "specified" or "proposed"; everything here is computed from the rule
#: registry and the committed corpora on every read, so a rule that stops
#: firing, a corpus case whose measurement moves, or a declaration that is
#: dropped moves one of these values and fails this test. "implemented" (not
#: "validated") is the honest value for a mode whose only corpus evidence is
#: a co-detection by a rule the mode does not own, a case recording "not
#: detected today" with an empty expected set, or no corpus case at all.
_EXPECTED_DERIVED_STATUS = {
    1: "validated",     # fragment fires fragmentation's Fragmentation: detector
    2: "implemented",   # fuse_adjacent fires coverage/fragmentation, neither mode 2's own
    3: "validated",     # item 167: split fires fragmentation via the new
                         # neighbour_contact edge (stray_contact_area_mm2 /
                         # stray_contact_label), 2026-09-20
    4: "validated",
    5: "proposed",
    6: "validated",     # remove_level fires coverage (remove_level_relabel expects {})
    7: "proposed",
    8: "implemented",   # no corpus case
    9: "validated",
    10: "proposed",      # skipped level label: no rule, no case
    11: "proposed",
    12: "proposed",
    13: "proposed",
    14: "proposed",
    15: "validated",
    16: "validated",
}


def test_ac26_every_corpus_case_agrees_and_status_derives_correctly(measured):
    import segfacet.failure_modes as fm

    assert set(_EXPECTED_DERIVED_STATUS) == set(fm.SPECIFICATION), (
        set(_EXPECTED_DERIVED_STATUS) ^ set(fm.SPECIFICATION)
    )

    for mode_id, mode in fm.SPECIFICATION.items():
        for case in mode.corpus_cases:
            assert fm.case_agrees(case), (mode_id, case.case_id)
        assert fm.derive_status(mode) == _EXPECTED_DERIVED_STATUS[mode_id], (
            mode_id,
            fm.derive_status(mode),
        )

    # The conditions' corpus cases are measured by the same harness and must
    # agree too -- a condition case is never a silent hole (item 150).
    checked_condition_cases = 0
    for condition in fm.iter_conditions():
        for case in condition.corpus_cases:
            assert fm.case_agrees(case), (condition.id, case.case_id)
            checked_condition_cases += 1
    assert checked_condition_cases, "expected >=1 condition corpus case"


# =========================================================================== #
# AC27's `aide check` warning-baseline test was retired on 2026-09-16: it
# pinned the loop's own `aide check` warning set in the standing suite, a
# diff-time claim that belongs on the branch, not here
# (.aide/conventions/6-test-hygiene.md §6). The error half now lives in
# tests/test_aide_check_no_errors.py; the `.gitattributes`-warning guard it
# also carried is covered by
# tests/test_128_relocation_checks.py::test_ac14_git_check_attr_reports_text_set_and_eol_lf
# (re-pointed by item 170: the sweep this comment used to name was removed
# as a warning-set pin, per §6 and the 2026-09-16 retirement).
# =========================================================================== #
