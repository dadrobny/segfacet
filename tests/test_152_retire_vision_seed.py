"""Tests for item 152 -- retiring the vision.md section 6 seed-conformance
check.

Vision v4 (PR #77, gate 6 approved 2026-09-16, commit
``7d800a20c8cf779f2ef1b93d5ba65d48652e2b2e``) re-issues section 6 as
principles plus a pointer to ``segfacet.failure_modes.SPECIFICATION``, with
no numbered list. ``vision_seed_titles()`` and ``vision_seed_conflicts()``
are retired; ``VISION_SEED_DISPOSITION`` is kept as a frozen literal
recording what each of v3's eight seed titles became. These tests assert
against the post-merge tree (the item's first act is merging that commit)
and the retired-module state the builder produces from it.

AC -> test map:

- AC1:  test_ac1_section_six_carries_no_numbered_list
- AC2:  test_ac2_section_six_names_the_specification
- AC3:  test_ac3_no_production_module_names_vision_md_as_a_path,
        test_ac3_adv_flagged_planted_paths (parametrized),
        test_ac3_adv_not_flagged_planted_constants (parametrized)
- AC4:  test_ac4_retired_functions_are_gone_from_the_module,
        test_adv_ac4_walker_flags_a_stand_in_with_the_attributes
- AC5:  test_ac5_no_source_text_names_a_retired_function
- AC6:  test_ac6_provenance_map_is_frozen_at_its_v3_value
- AC7:  test_ac7_every_disposition_resolves,
        test_adv_ac7_unresolvable_dispositions_are_reported,
        test_adv_ac7_all_three_kinds_are_exercised_by_the_shipped_map
- AC8:  test_ac8_docstring_drops_the_stale_section_six_claims
- AC9:  test_ac9_note_does_not_use_the_word_seed
- AC10: test_ac10_rendering_section_six_heading_is_the_provenance_heading
- AC11: test_ac11_provenance_section_opens_with_its_explanatory_sentence
- AC12: test_ac12_committed_markdown_carries_the_provenance_heading
- AC13: test_ac13_committed_json_note_is_the_module_note
- AC14: test_ac14_committed_json_top_level_shape_is_unchanged
- AC15: test_ac15_committed_json_provenance_equals_the_frozen_literal
- AC16: test_ac16_no_other_test_module_parses_section_six_by_heading,
        test_adv_ac16_walker_flags_a_planted_heading_literal

Adversarial / edge-case scenarios: positive controls for every AST walker
(AC3, AC4, AC16) so a clean result is never vacuous, and AC7's resolver is
fed four kinds of unresolvable disposition (out-of-range mode id, unknown
condition, non-digit mode target, and an unrecognised kind entirely).
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src" / "segfacet"
_TESTS_ROOT = _REPO_ROOT / "tests"
_VISION_PATH = _REPO_ROOT / "docs" / "aide" / "vision.md"
_COMMITTED_FM_JSON = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
_COMMITTED_FM_MD = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"

_THIS_FILE = Path(__file__).resolve()

_FROZEN_DISPOSITION = {
    "Label not aligned with the anatomical vertebra it names": "retired",
    "Over-/under-segmentation — fused or fragmented vertebra segments": "mode:1",
    "Disconnected components / islands, especially tiny rogue segments": "mode:4",
    "Semantic mislabelling (wrong vertebra identification)": "mode:8",
    "Not all vertebrae in the image are segmented": "mode:6",
    "Partial vertebra at the image border whose appearance changes": (
        "condition:fov_truncation"
    ),
    "Non-continuous label sequence (e.g. L1 → T12 → L2 → L5)": "mode:9",
    "Overlapping segments": "mode:15",
}


# =========================================================================== #
# House fixtures / helpers
# =========================================================================== #


def _section_six_text() -> str:
    """The text of vision.md section 6: from the ``## 6.`` heading up to the
    next ``## <digit>`` heading, or end of file -- exactly the AC's own
    definition. Reads live, with no import of ``segfacet.failure_modes``."""
    text = _VISION_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"^(## 6\..*?)(?=^## \d|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "expected a '## 6.' heading in vision.md"
    return match.group(1)


def _all_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def _all_test_py_files():
    return sorted(_TESTS_ROOT.rglob("*.py"))


def _rel(path: Path, root: Path = _REPO_ROOT) -> str:
    return path.relative_to(root).as_posix()


def _docstring_constant_ids(tree: ast.AST) -> set:
    """``id()`` of every ``ast.Constant`` string node sitting in docstring
    position (module, class or function body's first statement) -- the same
    shape as ``test_147_specification_is_the_record._docstring_constant_ids``."""
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


def _non_docstring_str_constant_contains(tree: ast.AST, needle: str) -> bool:
    """True if *tree* holds a non-docstring string constant containing
    *needle* -- the shared AST-walk shape AC16 uses, matching
    ``test_147_specification_is_the_record._references_vision_md``.

    AC3 no longer uses this substring shape (corrected 2026-09-16): see
    ``_names_vision_md_as_a_path`` below.
    """
    docstring_ids = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
            and needle in node.value
        ):
            return True
    return False


# Corrected AC3 predicate (2026-09-16): a *path-shaped* constant, not any
# substring mention. Matches the whole constant "vision.md" or a constant
# ending in "/vision.md" or "\vision.md" -- case-sensitive, no stripping,
# applied to each Constant node's exact value (including the literal parts
# of an f-string's ``JoinedStr``, which ``ast.walk`` yields as ordinary
# ``Constant`` nodes).
_VISION_MD_PATH_RE = re.compile(r"(?:^|[/\\])vision\.md$")


def _names_vision_md_as_a_path(tree: ast.AST) -> bool:
    """True if *tree* holds a non-docstring string constant matching the
    corrected AC3 predicate: the constant names ``vision.md`` as a path,
    rather than merely mentioning it in prose."""
    docstring_ids = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
            and _VISION_MD_PATH_RE.search(node.value)
        ):
            return True
    return False


@pytest.fixture(scope="module")
def rendered_markdown():
    """One ``render_markdown()`` call, shared by AC10/AC11 -- rendering
    measures corpus firing and is slow."""
    import segfacet.failure_modes as fm

    return fm.render_markdown()


# =========================================================================== #
# AC1/AC2: section 6's live prose
# =========================================================================== #


def test_ac1_section_six_carries_no_numbered_list():
    section = _section_six_text()
    numbered_lines = re.findall(r"^\d+\.\s", section, flags=re.MULTILINE)
    assert numbered_lines == [], numbered_lines


def test_ac2_section_six_names_the_specification():
    section = _section_six_text()
    assert "segfacet.failure_modes.SPECIFICATION" in section


# =========================================================================== #
# AC3 (corrected 2026-09-16): no production module names vision.md as a path
# =========================================================================== #


def test_ac3_no_production_module_names_vision_md_as_a_path():
    offenders = set()
    for path in _all_src_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _names_vision_md_as_a_path(tree):
            offenders.add(_rel(path))
    assert offenders == set(), offenders


# Positive controls: every "flagged" case from the correction's own control
# list must trip the predicate, so a clean result on the real tree is not
# vacuous. Each is a distinct path-shaped spelling of a vision.md read.
_AC3_FLAGGED_SOURCES = {
    "open_call": 'text = open("docs/aide/vision.md").read()\n',
    "pathlib_join": (
        'from pathlib import Path\n'
        'p = Path(root) / "docs" / "aide" / "vision.md"\n'
    ),
    "os_path_join": 'import os\np = os.path.join(root, "vision.md")\n',
    "fstring_join": 'p = f"{root}/vision.md"\n',
    "windows_separator": 'p = "docs\\\\aide\\\\vision.md"\n',
}


@pytest.mark.parametrize(
    "source", _AC3_FLAGGED_SOURCES.values(), ids=_AC3_FLAGGED_SOURCES.keys()
)
def test_ac3_adv_flagged_planted_paths(tmp_path, source):
    planted = tmp_path / "planted_flagged.py"
    planted.write_text(source, encoding="utf-8")
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    assert _names_vision_md_as_a_path(tree), source


# Negative controls: prose *about* vision.md, including the exact AC10/AC11
# literals authored into failure_modes.py by this item, must not trip the
# predicate -- these are the shapes AC3's original substring form would have
# wrongly flagged (the contradiction this correction resolves).
_AC3_NOT_FLAGGED_SOURCES = {
    "ac10_heading_literal": (
        'HEADING = "## Provenance: vision.md v3 section 6 seed titles"\n'
    ),
    "ac11_sentence_literal": (
        "SENTENCE = (\n"
        '    "vision.md section 6 states the catalogue\'s principles and "\n'
        '    "points at this specification; the numbered list its v3 carried "\n'
        '    "seeded the catalogue, and what became of each title is "\n'
        '    "recorded below."\n'
        ")\n"
    ),
    "docstring_only_mention": '"""See docs/aide/vision.md."""\nx = 1\n',
    "comment_only_mention": "# see docs/aide/vision.md\ny = 1\n",
}


@pytest.mark.parametrize(
    "source",
    _AC3_NOT_FLAGGED_SOURCES.values(),
    ids=_AC3_NOT_FLAGGED_SOURCES.keys(),
)
def test_ac3_adv_not_flagged_planted_constants(tmp_path, source):
    planted = tmp_path / "planted_not_flagged.py"
    planted.write_text(source, encoding="utf-8")
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    assert not _names_vision_md_as_a_path(tree), source


# =========================================================================== #
# AC4: the two functions are retired
# =========================================================================== #


def test_ac4_retired_functions_are_gone_from_the_module():
    import segfacet.failure_modes as fm

    retired_names = {"vision_seed_titles", "vision_seed_conflicts"}
    present = {name for name in retired_names if hasattr(fm, name)}
    assert present == set(), present

    for name in retired_names:
        assert name not in fm.__all__, name


def test_adv_ac4_walker_flags_a_stand_in_with_the_attributes():
    """Positive control: the same ``hasattr`` check must flag a stand-in
    module that still carries the retired names, so a clean AC4 result on
    the real module is not vacuous."""
    import types

    stand_in = types.ModuleType("planted_stand_in")
    stand_in.vision_seed_titles = lambda: {}
    stand_in.vision_seed_conflicts = lambda: ()

    retired_names = {"vision_seed_titles", "vision_seed_conflicts"}
    present = {name for name in retired_names if hasattr(stand_in, name)}
    assert present == retired_names, present


# =========================================================================== #
# AC5: no source text names a retired function
# =========================================================================== #


def test_ac5_no_source_text_names_a_retired_function():
    needles = ("vision_seed_titles", "vision_seed_conflicts")
    offenders = set()
    for path in _all_src_py_files():
        text = path.read_text(encoding="utf-8")
        if any(needle in text for needle in needles):
            offenders.add(_rel(path))
    assert offenders == set(), offenders


# =========================================================================== #
# AC6: the provenance map is frozen at its v3 value
# =========================================================================== #


def test_ac6_provenance_map_is_frozen_at_its_v3_value():
    import segfacet.failure_modes as fm

    assert dict(fm.VISION_SEED_DISPOSITION) == _FROZEN_DISPOSITION


# =========================================================================== #
# AC7: every provenance disposition resolves
# =========================================================================== #


def _resolves(disposition: str, specification: dict, conditions: dict) -> bool:
    if disposition == "retired":
        return True
    kind, _sep, target = disposition.partition(":")
    if kind == "mode":
        return target.isdigit() and int(target) in specification
    if kind == "condition":
        return target in conditions
    return False


def test_ac7_every_disposition_resolves():
    import segfacet.failure_modes as fm

    unresolved = {
        value
        for value in fm.VISION_SEED_DISPOSITION.values()
        if not _resolves(value, fm.SPECIFICATION, fm.CONDITIONS)
    }
    assert unresolved == set(), unresolved


def test_adv_ac7_unresolvable_dispositions_are_reported():
    import segfacet.failure_modes as fm

    for bogus in ("mode:9999", "condition:no_such", "mode:abc", "bogus"):
        assert not _resolves(bogus, fm.SPECIFICATION, fm.CONDITIONS), bogus


def test_adv_ac7_all_three_kinds_are_exercised_by_the_shipped_map():
    """So AC7's `retired`/`mode`/`condition` branches cannot rot into dead
    code unnoticed on the shipped tree."""
    import segfacet.failure_modes as fm

    kinds = set()
    for value in fm.VISION_SEED_DISPOSITION.values():
        if value == "retired":
            kinds.add("retired")
        else:
            kinds.add(value.partition(":")[0])
    assert kinds == {"retired", "mode", "condition"}, kinds


# =========================================================================== #
# AC8/AC9: the module's prose drops the stale §6-as-seed-list claims
# =========================================================================== #


def test_ac8_docstring_drops_the_stale_section_six_claims():
    import segfacet.failure_modes as fm

    collapsed = re.sub(r"\s+", " ", fm.__doc__ or "")
    stale_phrases = [
        "is the **seed**, not the record",
        "re-issue through the create-vision entry point is owed",
        "still equal §6's list",
        "the only reader of that document",
        "reads ``vision.md``",
    ]
    present = [phrase for phrase in stale_phrases if phrase in collapsed]
    assert present == [], present


def test_ac9_note_does_not_use_the_word_seed():
    import segfacet.failure_modes as fm

    assert "seed" not in fm._NOTE.lower()


# =========================================================================== #
# AC10/AC11: the fresh rendering's provenance section
# =========================================================================== #


def test_ac10_rendering_section_six_heading_is_the_provenance_heading(rendered_markdown):
    section_six_headings = {
        line
        for line in rendered_markdown.splitlines()
        if line.startswith("## ") and "section 6" in line
    }
    assert section_six_headings == {
        "## Provenance: vision.md v3 section 6 seed titles"
    }, section_six_headings


def test_ac11_provenance_section_opens_with_its_explanatory_sentence(rendered_markdown):
    lines = rendered_markdown.splitlines()
    heading = "## Provenance: vision.md v3 section 6 seed titles"
    idx = lines.index(heading)
    following = [line for line in lines[idx + 1 :] if line.strip()]
    assert following, "expected a non-empty line after the provenance heading"
    assert following[0] == (
        "vision.md section 6 states the catalogue's principles and points at "
        "this specification; the numbered list its v3 carried seeded the "
        "catalogue, and what became of each title is recorded below."
    )


# =========================================================================== #
# AC12-AC15: the committed artifacts
# =========================================================================== #


def test_ac12_committed_markdown_carries_the_provenance_heading():
    lines = _COMMITTED_FM_MD.read_text(encoding="utf-8").splitlines()
    section_six_headings = {
        line for line in lines if line.startswith("## ") and "section 6" in line
    }
    assert section_six_headings == {
        "## Provenance: vision.md v3 section 6 seed titles"
    }, section_six_headings


def test_ac13_committed_json_note_is_the_module_note():
    import segfacet.failure_modes as fm

    payload = json.loads(_COMMITTED_FM_JSON.read_text(encoding="utf-8"))
    assert payload["note"] == fm._NOTE


def test_ac14_committed_json_top_level_shape_is_unchanged():
    payload = json.loads(_COMMITTED_FM_JSON.read_text(encoding="utf-8"))
    assert set(payload.keys()) == {
        "schema_version",
        "note",
        "modes",
        "conditions",
        "vision_seed_disposition",
    }


def test_ac15_committed_json_provenance_equals_the_frozen_literal():
    payload = json.loads(_COMMITTED_FM_JSON.read_text(encoding="utf-8"))
    assert payload["vision_seed_disposition"] == _FROZEN_DISPOSITION


# =========================================================================== #
# AC16: no test parses section 6 by its heading outside this module
# =========================================================================== #


def test_ac16_no_other_test_module_parses_section_six_by_heading():
    offenders = set()
    for path in _all_test_py_files():
        if path.resolve() == _THIS_FILE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _non_docstring_str_constant_contains(tree, "Segmentation Failure Modes"):
            offenders.add(_rel(path))
    assert offenders == set(), offenders


def test_adv_ac16_walker_flags_a_planted_heading_literal(tmp_path):
    planted = tmp_path / "planted_heading_needle.py"
    planted.write_text(
        'PATTERN = r"^## 6\\. Segmentation Failure Modes"\n',
        encoding="utf-8",
    )
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    assert _non_docstring_str_constant_contains(tree, "Segmentation Failure Modes")
