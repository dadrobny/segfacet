"""Tests for item 157 -- dropping the ``modeN_`` corpus case-id prefixes.

Covers Acceptance Criteria AC1-AC19 (AC20, the full-suite run, is the
validator's job, not a test in this module). See
``docs/aide/items/157-drop-the-moden-corpus-case-id-prefixes.md`` for the
full rationale: eight geometric corpus case ids lose their stale ``modeN_``
prefix (the manifest's ``failure_mode`` field is the authority, not the
prefix), and ``segfacet.synth.corpus.RENAMED_CASE_IDS`` records the old->new
mapping as a frozen historical record for the handful of tests that must
still reach a pre-rename artifact (a pinned git blob, a retired file, a
dated comparison record).

Adversarial / edge cases (Testing Strategy):

- AC9/AC11 scans are exercised against synthetic positive and negative
  controls first, to prove the token boundaries and AST shapes are what the
  ACs claim, before asserting the real tree is clean.
- A8 (id/perturbation-name collisions): every new id resolves to exactly one
  manifest case; ``remove_level`` never resolves to
  ``remove_level_relabel_seg.nii.gz``; the inverse mapping is total and
  injective.
- AC12 skips cleanly (rather than failing) when ``git`` is unavailable, per
  the AC's own text.
- AC14 searches the live inbox *and* every archive file (CLAUDE.md's
  documented gotcha: an archive sweep must not red this suite).
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Dict

import pytest

from run_process import run_utf8

from segfacet.synth.corpus import CASE_RECIPE, RENAMED_CASE_IDS, load_manifest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_THIS_FILE = Path(__file__).resolve()
_CORPUS_SOURCE = _REPO_ROOT / "src" / "segfacet" / "synth" / "corpus.py"
_GEOMETRIC_MANIFEST = _REPO_ROOT / "tests" / "corpus" / "manifest.json"
_INTENSITY_MANIFEST = _REPO_ROOT / "tests" / "corpus" / "intensity" / "manifest.json"
_CORPUS_DIR = _REPO_ROOT / "tests" / "corpus"
_FIXTURES_DIR = _CORPUS_DIR / "fixtures"
_DECISION_TABLE = _REPO_ROOT / "docs" / "aide" / "golden-decision-table.md"
_INSIGHTS_MD = _REPO_ROOT / "docs" / "aide" / "insights.md"
_INSIGHTS_ARCHIVE_DIR = _REPO_ROOT / "docs" / "aide" / "insights"

_EXPECTED_MAPPING: Dict[str, str] = {
    "mode1_displace": "displace",
    "mode2_fragment": "fragment",
    "mode3_inject_islands": "inject_islands",
    "mode4_relabel_swap": "relabel_swap",
    "mode5_remove_level": "remove_level",
    "mode6_crop_at_border": "crop_at_border",
    "mode7_sequence_break": "sequence_break",
    "mode8_force_overlap": "force_overlap",
}

# AC9's two exempt files -- the mapping's own home, and this test module,
# which necessarily writes every old id as a literal (spec, AC9).
_AC9_EXEMPT = {
    "src/segfacet/synth/corpus.py",
    "tests/test_157_case_id_rename.py",
}

_AC9_GENERATED_DOCS = (
    "docs/aide/failure_modes.generated.json",
    "docs/aide/failure_modes.generated.md",
    "docs/aide/traceability_matrix.generated.json",
    "docs/aide/traceability_matrix.generated.md",
    "docs/aide/golden_evidence.generated.json",
)


def _token_regex(ids) -> "re.Pattern":
    """AC9's own regex, built only from *ids* -- never a hand-typed list or
    a ``mode[1-8]_...`` pattern (Testing Strategy)."""
    alternatives = "|".join(re.escape(old) for old in ids)
    return re.compile(rf"(?<![A-Za-z0-9_])(?:{alternatives})(?![A-Za-z0-9])")


def _tracked_files():
    """Every tracked file, via ``git ls-files``; falls back to a tree walk
    (skipping ``__pycache__``) when git is unavailable (Testing Strategy)."""
    try:
        result = run_utf8(["git", "ls-files"], cwd=str(_REPO_ROOT), timeout=60)
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is not None and result.returncode == 0 and result.stdout:
        return [line for line in result.stdout.splitlines() if line.strip()]
    paths = []
    for path in _REPO_ROOT.rglob("*"):
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if path.is_file():
            paths.append(path.relative_to(_REPO_ROOT).as_posix())
    return paths


# =========================================================================== #
# AC1: the mapping is recorded exactly
# =========================================================================== #


def test_ac1_renamed_case_ids_equals_expected_mapping():
    assert RENAMED_CASE_IDS == _EXPECTED_MAPPING


# =========================================================================== #
# AC2: the mapping is a source literal (no I/O, no path touched under tests/)
# =========================================================================== #


def test_ac2_renamed_case_ids_is_a_dict_literal_of_string_constants():
    tree = ast.parse(_CORPUS_SOURCE.read_text(encoding="utf-8"), filename=str(_CORPUS_SOURCE))
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "RENAMED_CASE_IDS" for t in node.targets
        ):
            found = node.value
            break
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "RENAMED_CASE_IDS":
            found = node.value
            break
    assert found is not None, "no module-level assignment to RENAMED_CASE_IDS found"
    assert isinstance(found, ast.Dict), "RENAMED_CASE_IDS is not a dict literal"
    for key_node, value_node in zip(found.keys, found.values):
        assert isinstance(key_node, ast.Constant) and isinstance(key_node.value, str), (
            f"RENAMED_CASE_IDS key {key_node!r} is not a string constant"
        )
        assert isinstance(value_node, ast.Constant) and isinstance(value_node.value, str), (
            f"RENAMED_CASE_IDS value {value_node!r} is not a string constant"
        )


# =========================================================================== #
# AC3/AC4: every new id is live, no old id is live
# =========================================================================== #


def test_ac3_every_new_id_is_exactly_one_live_case():
    recipe_ids = [entry.case_id for entry in CASE_RECIPE]
    for new_id in RENAMED_CASE_IDS.values():
        assert recipe_ids.count(new_id) == 1, (
            f"{new_id!r} does not resolve to exactly one CASE_RECIPE entry: "
            f"count={recipe_ids.count(new_id)}"
        )


def test_ac4_no_old_id_is_a_live_case():
    recipe_ids = {entry.case_id for entry in CASE_RECIPE}
    for old_id in RENAMED_CASE_IDS:
        assert old_id not in recipe_ids, f"{old_id!r} is still a live CASE_RECIPE case_id"


# =========================================================================== #
# AC5: no committed manifest id carries a mode prefix
# =========================================================================== #


_MODE_PREFIX_RE = re.compile(r"^mode\d+_")


@pytest.mark.parametrize("manifest_path", [_GEOMETRIC_MANIFEST, _INTENSITY_MANIFEST])
def test_ac5_no_manifest_case_id_carries_a_mode_prefix(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = manifest["cases"]
    assert cases, f"expected at least one case in {manifest_path}"
    offenders = [c["case_id"] for c in cases if _MODE_PREFIX_RE.match(c["case_id"])]
    assert offenders == [], f"{manifest_path}: mode-prefixed case ids survive: {offenders}"


# =========================================================================== #
# AC6: no corpus file/dir name carries a mode prefix
# =========================================================================== #


def test_ac6_no_corpus_path_name_carries_a_mode_prefix():
    offenders = [
        p.relative_to(_REPO_ROOT).as_posix()
        for p in _CORPUS_DIR.rglob("*")
        if _MODE_PREFIX_RE.match(p.name)
    ]
    assert offenders == [], f"mode-prefixed names still exist under tests/corpus/: {offenders}"


# =========================================================================== #
# AC7: every geometric seg fixture resolves by its case id
# =========================================================================== #


def test_ac7_every_seg_fixture_resolves_by_case_id():
    manifest = load_manifest()
    cases = manifest["cases"]
    assert cases, "expected at least one manifest case"
    for case in cases:
        expected = f"fixtures/{case['case_id']}_seg.nii.gz"
        assert case["seg_fixture"] == expected, (
            f"{case['case_id']!r}: seg_fixture {case['seg_fixture']!r} != {expected!r}"
        )
        seg_path = _CORPUS_DIR / case["seg_fixture"]
        assert seg_path.is_file(), f"missing seg fixture: {seg_path}"


# =========================================================================== #
# AC8: every specification corpus reference resolves
# =========================================================================== #


def test_ac8_every_corpus_case_expectation_resolves_to_a_committed_manifest_case():
    import segfacet.failure_modes as failure_modes

    geo_ids = {c["case_id"] for c in json.loads(_GEOMETRIC_MANIFEST.read_text(encoding="utf-8"))["cases"]}
    intensity_ids = {c["case_id"] for c in json.loads(_INTENSITY_MANIFEST.read_text(encoding="utf-8"))["cases"]}
    by_corpus = {"geometric": geo_ids, "intensity": intensity_ids}

    checked = 0
    for mode in failure_modes.SPECIFICATION.values():
        for case in mode.corpus_cases:
            assert case.corpus in by_corpus, f"unknown corpus {case.corpus!r} on case {case.case_id!r}"
            assert case.case_id in by_corpus[case.corpus], (
                f"{case.case_id!r} ({case.corpus}) is not a case in the committed "
                f"{case.corpus} manifest"
            )
            checked += 1
    for condition in failure_modes.CONDITIONS.values():
        for case in condition.corpus_cases:
            assert case.corpus in by_corpus, f"unknown corpus {case.corpus!r} on case {case.case_id!r}"
            assert case.case_id in by_corpus[case.corpus], (
                f"{case.case_id!r} ({case.corpus}) is not a case in the committed "
                f"{case.corpus} manifest"
            )
            checked += 1
    assert checked > 0, "expected at least one CorpusCaseExpectation reachable from the specification"


# =========================================================================== #
# AC9: no live surface names an old id (scan) -- synthetic controls first
# =========================================================================== #


def test_ac9_scan_adversarial_controls_prove_the_token_boundary():
    """Before trusting the tree-wide sweep below, prove its regex matches
    the exact shape AC9 claims and nothing looser."""
    pattern = _token_regex(RENAMED_CASE_IDS)
    positive = "tests/corpus/golden/mode1_displace.json"
    assert pattern.search(positive) is not None, (
        f"expected {positive!r} to match the AC9 token regex"
    )
    negatives = (
        "test_ac1_mode4_relabel_swap_is_non_monotonic",
        "mode4_sequence_break",
        "mode5_sequence_break",
    )
    for negative in negatives:
        assert pattern.search(negative) is None, (
            f"{negative!r} unexpectedly matched the AC9 token regex -- a "
            "loose mode[1-8]_... pattern would trip on this, exactly what "
            "AC9's exact-token requirement guards against"
        )


def test_ac9_no_live_surface_names_an_old_id():
    pattern = _token_regex(RENAMED_CASE_IDS)
    candidates = set()
    for rel in _tracked_files():
        if rel in _AC9_EXEMPT:
            continue
        suffix = Path(rel).suffix
        under_scanned_dir = (
            rel.startswith("src/segfacet/") or rel.startswith("scripts/") or rel.startswith("tests/")
        )
        if (under_scanned_dir and suffix in (".py", ".json", ".md")) or rel in _AC9_GENERATED_DOCS:
            candidates.add(rel)
    assert candidates, "expected a non-empty scan set -- the enumeration is broken"

    offenders = []
    for rel in sorted(candidates):
        full = _REPO_ROOT / rel
        if not full.is_file():
            continue
        text = full.read_text(encoding="utf-8", errors="strict")
        match = pattern.search(text)
        if match is not None:
            offenders.append((rel, match.group(0)))
    assert offenders == [], f"old case ids still appear in live surfaces: {offenders}"


# =========================================================================== #
# AC10: the decision table's keep rows name only live ids
# =========================================================================== #


def _decision_table_text() -> str:
    return _DECISION_TABLE.read_bytes().decode("utf-8")


def test_ac10_decision_table_keep_rows_and_divergences_name_no_old_id():
    import test_105_golden_decision_table as t105

    text = _decision_table_text()
    sections = t105._split_sections(text)
    _, rows = t105._parse_first_pipe_table(
        sections["Section 1 — Committed test fixtures"], where="Section 1"
    )
    keep_rows = [r for r in rows if r.get("disposition") == "keep"]
    assert keep_rows, "expected at least one 'keep' row in Section 1"

    divergences_body = sections.get("Divergences from the roadmap's working assumption")
    assert divergences_body is not None, "Divergences section not found"

    pattern = _token_regex(RENAMED_CASE_IDS)
    for row in keep_rows:
        for cell in row.values():
            assert pattern.search(cell) is None, (
                f"keep row cell still names an old id: {cell!r}"
            )
    assert pattern.search(divergences_body) is None, (
        "the Divergences section still names an old id"
    )


# =========================================================================== #
# AC11: nothing parses a mode out of a case id (AST scan)
# =========================================================================== #


def _is_case_id_expr(node) -> bool:
    if isinstance(node, ast.Name) and node.id == "case_id":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "case_id":
        return True
    if isinstance(node, ast.Subscript):
        sl = node.slice
        if isinstance(sl, ast.Constant) and sl.value == "case_id":
            return True
    return False


_RE_MODE_FUNCS = {"match", "search", "fullmatch", "findall", "split", "sub"}
_STR_MODE_PREFIX_METHODS = {"startswith", "removeprefix", "find", "index"}
_STR_SPLIT_METHODS = {"split", "rsplit", "partition", "rpartition"}


def _case_id_mode_parse_violations(tree: ast.AST):
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and _is_case_id_expr(node.value):
            violations.append(node)
            continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            recv, attr = node.func.value, node.func.attr
            if attr in _STR_SPLIT_METHODS and _is_case_id_expr(recv):
                violations.append(node)
                continue
            if attr in _STR_MODE_PREFIX_METHODS and _is_case_id_expr(recv):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(
                    node.args[0].value, str
                ) and node.args[0].value.startswith("mode"):
                    violations.append(node)
                    continue
            if (
                isinstance(recv, ast.Name)
                and recv.id == "re"
                and attr in _RE_MODE_FUNCS
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and "mode" in node.args[0].value
            ):
                for other in node.args[1:]:
                    if _is_case_id_expr(other):
                        violations.append(node)
                        break
    return violations


@pytest.mark.parametrize(
    "snippet",
    [
        "case_id[4]",
        'case["case_id"].split("_")',
        'c.case_id.startswith("mode")',
        'import re\nre.match(r"mode(\\d+)_", case_id)',
    ],
)
def test_ac11_ast_scan_positive_controls_are_reported(snippet):
    tree = ast.parse(snippet)
    assert _case_id_mode_parse_violations(tree), f"expected a violation for: {snippet!r}"


@pytest.mark.parametrize(
    "snippet",
    [
        'case.case_id.startswith("sub-verse")',
        'c["case_id"] == "displace"',
    ],
)
def test_ac11_ast_scan_negative_controls_are_not_reported(snippet):
    tree = ast.parse(snippet)
    assert _case_id_mode_parse_violations(tree) == [], f"unexpected violation for: {snippet!r}"


def test_ac11_no_real_module_parses_a_mode_out_of_a_case_id():
    offenders = []
    for rel in _tracked_files():
        if not rel.endswith(".py"):
            continue
        if not (
            rel.startswith("src/segfacet/") or rel.startswith("scripts/") or rel.startswith("tests/")
        ):
            continue
        full = _REPO_ROOT / rel
        if not full.is_file():
            continue
        try:
            tree = ast.parse(full.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError:
            continue
        if _case_id_mode_parse_violations(tree):
            offenders.append(rel)
    assert offenders == [], f"these modules parse a mode out of a case id: {offenders}"


# =========================================================================== #
# AC12: the renamed fixtures stay pinned binary
# =========================================================================== #


@pytest.mark.parametrize("new_id", sorted(RENAMED_CASE_IDS.values()))
def test_ac12_renamed_fixture_is_pinned_binary(new_id):
    rel = f"tests/corpus/fixtures/{new_id}_seg.nii.gz"
    try:
        result = run_utf8(["git", "check-attr", "binary", "--", rel], cwd=str(_REPO_ROOT), timeout=30)
    except (OSError, subprocess.SubprocessError):
        pytest.skip("git is unavailable to the runner")
    if result.returncode != 0:
        pytest.skip(f"git check-attr failed for {rel!r}: {result.stderr}")
    assert result.stdout is not None, "expected decoded stdout from git check-attr"
    assert "binary: set" in result.stdout, (
        f"{rel!r} is not pinned binary: {result.stdout!r}"
    )


# =========================================================================== #
# AC13: the generator documents the mapping
# =========================================================================== #


def _pair_pattern(old: str, new: str) -> "re.Pattern[str]":
    # Matches the docstring's own ``old`` -> ``new`` shape, both ids as
    # whole double-backtick-quoted tokens, old strictly before new -- not a
    # bare substring check, since every new id is a suffix of its old id
    # (e.g. "mode1_displace" -> "displace") and so "new in line" is always
    # true whenever "old in line" is.
    return re.compile(rf"``{re.escape(old)}``\s*->\s*``{re.escape(new)}``")


def test_ac13_generator_docstring_documents_every_pair():
    import segfacet.synth.corpus as corpus_module

    doc = corpus_module.__doc__ or ""
    lines = doc.splitlines()
    for old, new in RENAMED_CASE_IDS.items():
        pattern = _pair_pattern(old, new)
        matching = [ln for ln in lines if pattern.search(ln)]
        assert matching, (
            f"no docstring line documents the pair ``{old}`` -> ``{new}``"
        )


def test_ac13_pair_pattern_rejects_old_id_named_alone():
    # Negative control: a line naming only the old id (no "-> ``new``")
    # must not satisfy the pattern -- proves the check above can fail.
    old, new = next(iter(RENAMED_CASE_IDS.items()))
    pattern = _pair_pattern(old, new)
    assert not pattern.search(f"* ``{old}`` was renamed.")
    assert pattern.search(f"* ``{old}`` -> ``{new}``")


# =========================================================================== #
# AC14: the mapping is captured as one knowledge insight
# =========================================================================== #


def _captured_insight_lines():
    lines = _INSIGHTS_MD.read_text(encoding="utf-8").splitlines()
    if _INSIGHTS_ARCHIVE_DIR.is_dir():
        for archive in sorted(_INSIGHTS_ARCHIVE_DIR.glob("archive-*.md")):
            lines.extend(archive.read_text(encoding="utf-8").splitlines())
    return lines


def test_ac14_mapping_captured_as_exactly_one_knowledge_insight():
    lines = _captured_insight_lines()
    matches = [
        line
        for line in lines
        if (line.startswith("- [ ] knowledge —") or line.startswith("- [x] knowledge —"))
        and "item 157" in line
        and all(old in line for old in RENAMED_CASE_IDS)
        and all(new in line for new in RENAMED_CASE_IDS.values())
    ]
    assert len(matches) == 1, (
        f"expected exactly one knowledge insight for item 157's mapping, found {len(matches)}: {matches}"
    )


# =========================================================================== #
# AC15: the geometric corpus regenerates identically
# =========================================================================== #


def test_ac15_geometric_corpus_regenerates_identically(tmp_path):
    from test_040_synthetic_corpus import (
        test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed as _ac16,
    )

    # Reuses test_040's existing byte-identity helper rather than adding a
    # second fresh-vs-committed byte comparison of its own (Testing
    # Strategy) -- covers manifest.json, every fixtures/<case_id>_seg.nii.gz
    # and base_scan.nii.gz.
    _ac16(tmp_path)


# =========================================================================== #
# AC16/AC17/AC18: the generated artifacts regenerate identically
# =========================================================================== #


def test_ac16_failure_mode_specification_artifacts_regenerate_identically(
    regenerated_failure_modes,
):
    from segfacet.synth.golden import assert_matches_committed_artifact

    committed_json = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
    committed_md = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"
    assert_matches_committed_artifact(regenerated_failure_modes.json_a, committed_json)
    # Markdown: no numeric-tolerance ground exists for a whole-document
    # compare, and none is added here -- decode-then-compare as fully
    # rendered text (same shape as test_147's AC24).
    assert (
        regenerated_failure_modes.md_a.read_bytes().decode("utf-8")
        == committed_md.read_bytes().decode("utf-8")
    )


def test_ac17_traceability_matrix_artifacts_regenerate_identically(
    regenerated_traceability,
):
    from segfacet.synth.golden import assert_matches_committed_artifact

    committed_json = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.json"
    committed_md = _REPO_ROOT / "docs" / "aide" / "traceability_matrix.generated.md"
    assert_matches_committed_artifact(regenerated_traceability.json_a, committed_json)
    assert (
        regenerated_traceability.md_a.read_bytes().decode("utf-8")
        == committed_md.read_bytes().decode("utf-8")
    )


def test_ac18_golden_evidence_companion_regenerates_identically(tmp_path):
    import segfacet.golden_evidence as golden_evidence
    from segfacet.synth.golden import assert_matches_committed_artifact

    out_path = tmp_path / "golden_evidence.generated.json"
    golden_evidence.main(["--out", str(out_path)])

    committed = _REPO_ROOT / "docs" / "aide" / "golden_evidence.generated.json"
    assert_matches_committed_artifact(out_path, committed)


# =========================================================================== #
# AC19: historical lookups still resolve through the mapping
# =========================================================================== #


def test_ac19_decision_table_has_exactly_one_retired_row_per_old_id():
    import test_105_golden_decision_table as t105

    text = _decision_table_text()
    sections = t105._split_sections(text)
    _, rows = t105._parse_first_pipe_table(
        sections["Section 1 — Committed test fixtures"], where="Section 1"
    )
    for new_id, old_id in {v: k for k, v in RENAMED_CASE_IDS.items()}.items():
        expected_fixture = f"tests/corpus/golden/{old_id}.json"
        matches = [r for r in rows if r.get("fixture") == expected_fixture]
        assert len(matches) == 1, (
            f"expected exactly one Section-1 row for {expected_fixture!r}, "
            f"got {len(matches)}"
        )
        assert matches[0]["disposition"] == "retire", matches[0]


# =========================================================================== #
# Edge cases (A8): id/perturbation-name collisions
# =========================================================================== #


def test_a8_each_new_id_resolves_to_exactly_one_manifest_case():
    manifest = load_manifest()
    ids = [c["case_id"] for c in manifest["cases"]]
    for new_id in RENAMED_CASE_IDS.values():
        assert ids.count(new_id) == 1, (
            f"{new_id!r} does not resolve to exactly one manifest case: count={ids.count(new_id)}"
        )


def test_a8_remove_level_never_resolves_to_remove_level_relabel():
    manifest = load_manifest()
    case = next(c for c in manifest["cases"] if c["case_id"] == "remove_level")
    assert case["seg_fixture"] == "fixtures/remove_level_seg.nii.gz"
    assert case["seg_fixture"] != "fixtures/remove_level_relabel_seg.nii.gz"


def test_a8_inverse_mapping_is_total_and_injective():
    values = list(RENAMED_CASE_IDS.values())
    assert len(values) == len(set(values)), (
        f"RENAMED_CASE_IDS is not injective -- two old ids map to the same new id: {values}"
    )
    inverse = {new: old for old, new in RENAMED_CASE_IDS.items()}
    assert len(inverse) == len(RENAMED_CASE_IDS)
    for old, new in RENAMED_CASE_IDS.items():
        assert inverse[new] == old
