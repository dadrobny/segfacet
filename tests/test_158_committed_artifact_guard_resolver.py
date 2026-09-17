"""Tests for item 158 -- the committed-artifact guard's two blind spots.

``tests/committed_artifact_guard.py``'s resolver (item 127) only recognised a
committed-path root built as a literal chain of ``.parent`` attribute access
starting at ``Path(__file__)``. Two equivalent idioms silently resolved to
nothing and were skipped without a report: ``Path(__file__).resolve()
.parents[N]`` (an integer-literal ``Subscript`` on ``.parents``), and a
module-level or function-local name bound to a ``Path(__file__)`` chain and
then further ``.parent``-stepped by name (``_TESTS_DIR = ...; _REPO_ROOT =
_TESTS_DIR.parent``). This item teaches the resolver both shapes without
touching ``ALLOWLIST`` or ``GROUNDS``.

Every synthetic module below goes through
``committed_artifact_guard.classify_module`` with an in-memory source string
-- never written into the real ``tests/`` tree, where item 126/127's own
sweep would flag it and corrupt AC10's real-tree assertion. ``ARTIFACT`` here
is the committed path ``src/segfacet/reference/reference_default.json``,
deliberately off-allowlist (see the guard's module docstring), so a
recognised root chain that resolves to it always produces exactly one
``Violation``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import committed_artifact_guard as guard

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent

ARTIFACT = "src/segfacet/reference/reference_default.json"
MODULE_PATH = "tests/test_zz_synthetic_158.py"

_JOIN = '"src" / "segfacet" / "reference" / "reference_default.json"'


def _build_module(root_lines: str) -> str:
    """One synthetic module: *root_lines* binds the root, then a single test
    function compares a fresh read against ``<root expr> / ... / ARTIFACT``.
    ``root_lines`` must leave the root expression available as ``_ROOT``.
    """
    return (
        "from pathlib import Path\n"
        f"{root_lines}"
        "\n\n"
        "def test_x(tmp_path):\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (_ROOT / {_JOIN}).read_bytes()\n"
    )


def _one_violation(violations, committed_path=ARTIFACT):
    assert len(violations) == 1, violations
    assert violations[0].committed_path == committed_path, violations


# =========================================================================== #
# AC1: parents[1] resolves to the repo root
# =========================================================================== #


def test_ac1_parents_1_resolves_to_the_repo_root():
    source = _build_module("_ROOT = Path(__file__).resolve().parents[1]\n")
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


# =========================================================================== #
# AC2: parents[1] and .parent.parent classify identically
# =========================================================================== #


def test_ac2_parents_1_and_parent_parent_classify_identically():
    parents_source = _build_module("_ROOT = Path(__file__).resolve().parents[1]\n")
    dotted_source = _build_module(
        "_ROOT = Path(__file__).resolve().parent.parent\n"
    )
    parents_violations = guard.classify_module(parents_source, MODULE_PATH)
    dotted_violations = guard.classify_module(dotted_source, MODULE_PATH)
    assert parents_violations == dotted_violations
    _one_violation(parents_violations)


# =========================================================================== #
# AC3: parents[0] and a single .parent classify identically (both empty)
# =========================================================================== #


def test_ac3_parents_0_and_single_parent_classify_identically_and_empty():
    parents_source = _build_module("_ROOT = Path(__file__).resolve().parents[0]\n")
    dotted_source = _build_module("_ROOT = Path(__file__).resolve().parent\n")
    parents_violations = guard.classify_module(parents_source, MODULE_PATH)
    dotted_violations = guard.classify_module(dotted_source, MODULE_PATH)
    assert parents_violations == dotted_violations
    assert parents_violations == []


# =========================================================================== #
# AC4: parents[2] and three .parent steps classify identically
# =========================================================================== #


def test_ac4_parents_2_and_three_parent_steps_classify_identically():
    parents_source = _build_module("_ROOT = Path(__file__).resolve().parents[2]\n")
    dotted_source = _build_module(
        "_ROOT = Path(__file__).resolve().parent.parent.parent\n"
    )
    parents_violations = guard.classify_module(parents_source, MODULE_PATH)
    dotted_violations = guard.classify_module(dotted_source, MODULE_PATH)
    assert parents_violations == dotted_violations
    _one_violation(parents_violations)


# =========================================================================== #
# AC5: a parents index that is not a non-negative int literal resolves nothing
# =========================================================================== #


def test_ac5_negative_index_resolves_nothing():
    source = _build_module("_ROOT = Path(__file__).resolve().parents[-1]\n")
    assert guard.classify_module(source, MODULE_PATH) == []


def test_ac5_name_index_resolves_nothing():
    source = _build_module(
        "n = 1\n_ROOT = Path(__file__).resolve().parents[n]\n"
    )
    assert guard.classify_module(source, MODULE_PATH) == []


def test_ac5_bool_index_resolves_nothing():
    # A5: bool is not an int literal here even though `True == 1` and
    # `isinstance(True, int)` -- the resolver must reject it explicitly, not
    # accept it by falling through the int check.
    source = _build_module("_ROOT = Path(__file__).resolve().parents[True]\n")
    assert guard.classify_module(source, MODULE_PATH) == []


# =========================================================================== #
# AC6: a module-level two-hop root and the literal chain classify identically
# =========================================================================== #


def test_ac6_module_level_two_hop_root_matches_literal_chain():
    two_hop_source = _build_module(
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        "_ROOT = _TESTS_DIR.parent\n"
    )
    literal_source = _build_module(
        "_PAD = None\n"
        "_ROOT = Path(__file__).resolve().parent.parent\n"
    )
    assert len(two_hop_source.splitlines()) == len(literal_source.splitlines())
    two_hop_violations = guard.classify_module(two_hop_source, MODULE_PATH)
    literal_violations = guard.classify_module(literal_source, MODULE_PATH)
    assert two_hop_violations == literal_violations
    _one_violation(two_hop_violations)


# =========================================================================== #
# AC7: a name carrying a one-step root is still not the repo root
# =========================================================================== #


def test_ac7_one_step_named_root_is_still_not_the_repo_root():
    source = _build_module("_ROOT = Path(__file__).resolve().parent\n")
    # _ROOT here is a one-step root -- same as AC3's single-.parent case,
    # just reached through a name instead of used inline.
    assert guard.classify_module(source, MODULE_PATH) == []


# =========================================================================== #
# AC8: a function-local two-hop root and the literal chain classify identically
# =========================================================================== #


def _build_local_module(root_lines: str) -> str:
    return (
        "from pathlib import Path\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        f"{root_lines}"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (root / {_JOIN}).read_bytes()\n"
    )


def test_ac8_function_local_two_hop_root_matches_literal_chain():
    two_hop_source = _build_local_module(
        "    here = Path(__file__).resolve().parent\n"
        "    root = here.parent\n"
    )
    literal_source = _build_local_module(
        "    here = None\n"
        "    root = Path(__file__).resolve().parent.parent\n"
    )
    assert len(two_hop_source.splitlines()) == len(literal_source.splitlines())
    two_hop_violations = guard.classify_module(two_hop_source, MODULE_PATH)
    literal_violations = guard.classify_module(literal_source, MODULE_PATH)
    assert two_hop_violations == literal_violations
    _one_violation(two_hop_violations)


# =========================================================================== #
# AC9: every real test module classifies the same as its normalised source
# =========================================================================== #


class _NormaliseFileRootShapes(ast.NodeTransformer):
    """Expand ``<expr>.parents[N]`` (N a non-negative int literal) into N+1
    ``.parent`` steps, and inline a load of a module-level name bound to a
    ``Path(__file__)`` chain with that chain's (normalised) expression --
    both are the two shapes item 158 teaches the resolver, applied by an
    independent AST rewrite rather than by calling the resolver itself."""

    def __init__(self, module_level_chains):
        # name -> the (already-normalised) ast.expr it was assigned from
        self._chains = module_level_chains

    def visit_Subscript(self, node):
        node = self.generic_visit(node)
        value = node.value
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "parents"
            and isinstance(node.slice, ast.Constant)
            and type(node.slice.value) is int
            and node.slice.value >= 0
        ):
            n = node.slice.value
            expr = value.value
            for _ in range(n + 1):
                expr = ast.Attribute(value=expr, attr="parent", ctx=ast.Load())
            return ast.copy_location(expr, node)
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self._chains:
            return ast.copy_location(self._chains[node.id], node)
        return node


def _file_root_chain_source_only(node) -> bool:
    """Structural mirror of ``guard._file_root_parent_count`` that looks only
    at ``.resolve()``/``.parent``/``Path(__file__)`` -- used to decide which
    module-level names to inline, independent of the resolver under test."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Path":
        return len(node.args) == 1 and isinstance(node.args[0], ast.Name) and node.args[0].id == "__file__"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "resolve"
        and not node.args
    ):
        return _file_root_chain_source_only(node.func.value)
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        return _file_root_chain_source_only(node.value)
    return False


def _normalise_source(source: str) -> str:
    tree = ast.parse(source)
    # First expand parents[N] everywhere so a chain like `X.parents[0].parent`
    # is fully dotted before name inlining looks at module-level assignments.
    tree = _NormaliseFileRootShapes({}).visit(tree)
    ast.fix_missing_locations(tree)

    chains = {}
    for stmt in tree.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and _file_root_chain_source_only(stmt.value)
        ):
            chains[stmt.targets[0].id] = stmt.value

    if chains:
        tree = _NormaliseFileRootShapes(chains).visit(tree)
        ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def test_ac9_every_real_test_module_classifies_the_same_normalised(monkeypatch):
    monkeypatch.setattr(guard, "ALLOWLIST", ())

    changed_and_nonempty = 0
    for path in sorted(TESTS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        module_path = path.as_posix()

        original_violations = guard.classify_module(source, module_path)
        original_paths = sorted(v.committed_path for v in original_violations)

        try:
            normalised_source = _normalise_source(source)
        except SyntaxError:
            continue

        normalised_violations = guard.classify_module(normalised_source, module_path)
        normalised_paths = sorted(v.committed_path for v in normalised_violations)

        assert original_paths == normalised_paths, (
            f"{module_path}: original {original_paths} != normalised "
            f"{normalised_paths}"
        )

        if ast.dump(ast.parse(source)) != ast.dump(ast.parse(normalised_source)):
            if normalised_paths:
                changed_and_nonempty += 1

    # Non-vacuity, derived live (per the spec/testing strategy): at least one
    # real module must actually use one of the two idioms and see a
    # comparison as a result, or this equivalence would hold trivially
    # because no module ever exercised either shape.
    assert changed_and_nonempty >= 1, (
        "no real test module's normalisation both changed its AST and "
        "produced a non-empty violation list -- the AC9 equivalence would "
        "be vacuous"
    )


# =========================================================================== #
# AC10: the tests tree is guard-clean with the committed allowlist
# =========================================================================== #


def test_ac10_tests_tree_is_guard_clean_with_committed_allowlist():
    violations = list(guard.iter_violations(TESTS_DIR))
    assert violations == [], guard.violation_message(violations)


# =========================================================================== #
# AC11: the traceability-matrix comparison is visible, and its entry grounds it
# =========================================================================== #


def test_ac11_traceability_matrix_comparison_visible_when_ungrounded(monkeypatch):
    narrowed = tuple(
        e
        for e in guard.ALLOWLIST
        if not e.path.startswith("docs/aide/traceability_matrix.generated.")
    )
    assert len(narrowed) < len(guard.ALLOWLIST), (
        "fixture assumption violated: no traceability-matrix entry was "
        "removed from ALLOWLIST"
    )
    monkeypatch.setattr(guard, "ALLOWLIST", narrowed)

    violations = list(guard.iter_violations(TESTS_DIR))
    assert violations, "expected a non-empty violation list with the ground removed"
    for v in violations:
        assert v.committed_path.startswith("docs/aide/traceability_matrix.generated."), v


# =========================================================================== #
# AC12 / AC13: the "Still skipped in silence" docstring list is accurate
# =========================================================================== #

_STILL_SKIPPED_INTRO = "Still skipped in silence:"

_ENTRY_RE_TEMPLATE = "- {prose}: ``{expr}``"


def _parse_still_skipped_entries():
    doc = guard.__doc__ or ""
    lines = doc.splitlines()
    try:
        intro_idx = next(i for i, line in enumerate(lines) if line.strip() == _STILL_SKIPPED_INTRO)
    except StopIteration:
        raise AssertionError(
            f"module docstring has no {_STILL_SKIPPED_INTRO!r} line"
        )

    entries = []
    for line in lines[intro_idx + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        assert stripped.startswith("- ") and "``" in stripped, (
            f"malformed still-skipped entry: {line!r}"
        )
        prose, _, rest = stripped[2:].partition(":")
        # rest looks like " ``<expression>`` " (A6's fixed form)
        parts = rest.split("``")
        assert len(parts) >= 3, f"malformed still-skipped entry: {line!r}"
        expr = parts[1]
        entries.append((prose.strip(), expr))
    return entries


_A6_TEMPLATE = """import hashlib
import json
import pathlib
from pathlib import Path


def test_shape(tmp_path, arg):
    fresh = tmp_path / "fresh.json"
    assert fresh.read_bytes() == {expr}
"""


def _render_a6(expr: str) -> str:
    rendered_expr = expr.replace("ARTIFACT", '"src/segfacet/reference/reference_default.json"')
    return _A6_TEMPLATE.format(expr=rendered_expr)


def test_ac12_still_skipped_list_exists_and_is_nonempty():
    entries = _parse_still_skipped_entries()
    assert entries, "the still-skipped list must be non-empty (A3, A6)"


def test_ac12_every_still_skipped_shape_parses_and_is_actually_skipped():
    entries = _parse_still_skipped_entries()
    for prose, expr in entries:
        assert "ARTIFACT" in expr, f"entry {prose!r} does not use the ARTIFACT token: {expr!r}"
        rendered = _render_a6(expr)
        try:
            ast.parse(rendered)
        except SyntaxError as exc:
            raise AssertionError(
                f"still-skipped entry {prose!r} rendered invalid Python: "
                f"{rendered!r} ({exc})"
            )
        violations = guard.classify_module(rendered, MODULE_PATH)
        assert violations == [], (
            f"still-skipped entry {prose!r} ({expr!r}) is NOT actually "
            f"skipped -- the guard reported: {violations}"
        )


def test_ac12_still_skipped_covers_the_required_operand_shapes():
    entries = _parse_still_skipped_entries()
    exprs = " | ".join(expr for _, expr in entries)
    # A6 requires at least these operand shapes to be present, in some
    # wording the builder chose -- checked structurally, not by exact prose.
    assert "pathlib.Path(__file__)" in exprs, exprs
    assert "arg()" in exprs, exprs
    # A bare function-argument root, distinct from the arg() call shape.
    assert any(expr.strip().split(" ")[0] == "arg" or expr.strip() == "arg" or "arg /" in expr or "arg)" in expr for _, expr in entries), exprs
    assert "parents[" in exprs, exprs
    assert "json.loads" in exprs, exprs
    assert "f\"" in exprs or "f'" in exprs, exprs


def test_ac13_control_expression_in_a6_template_is_seen_as_a_violation():
    control_expr = "(Path(__file__).resolve().parent.parent / ARTIFACT).read_bytes()"
    rendered = _render_a6(control_expr)
    violations = guard.classify_module(rendered, MODULE_PATH)
    _one_violation(violations)


# =========================================================================== #
# Adversarial / edge cases
# =========================================================================== #


def test_adv_parents_1_directly_on_path_no_resolve_matches_ac1():
    source = _build_module("_ROOT = Path(__file__).parents[1]\n")
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


def test_adv_chained_root_parent_then_parents_0_has_depth_two():
    source = _build_module(
        "_ROOT = Path(__file__).resolve().parent.parents[0]\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


def test_adv_module_level_name_bound_to_parents_1_then_joined_resolves():
    source = (
        "from pathlib import Path\n"
        "_REPO_ROOT = Path(__file__).resolve().parents[1]\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        '    fresh = tmp_path / "fresh.json"\n'
        "    committed = _REPO_ROOT / \"docs\" / \"aide\" / \"x.json\"\n"
        "    assert fresh.read_bytes() == committed.read_bytes()\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations, committed_path="docs/aide/x.json")


def test_adv_classification_is_deterministic():
    source = _build_module("_ROOT = Path(__file__).resolve().parents[1]\n")
    first = guard.classify_module(source, MODULE_PATH)
    second = guard.classify_module(source, MODULE_PATH)
    assert first == second


def test_adv_loop_variable_still_skipped_in_silence():
    """Re-run of test_127's unresolvable-operand case in this module, to
    show the resolver's new parents[N]/name-carried-root handling has not
    accidentally widened what resolves: a loop variable stays unresolved."""
    source = (
        "def test_loop(paths, tmp_path):\n"
        "    for p in paths:\n"
        "        fresh = tmp_path / p.name\n"
        "        assert fresh.read_bytes() == p.read_bytes()\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    assert not violations


def test_adv_module_level_rebind_control_still_one_violation():
    """Positive control for the next test: without the rebind, a two-hop
    module-level root reached via a *second* name (``_REPO_ROOT``, not the
    ``_ROOT`` `_build_module` uses) still resolves to one violation."""
    source = (
        "from pathlib import Path\n"
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        "_REPO_ROOT = _TESTS_DIR.parent\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (_REPO_ROOT / {_JOIN}).read_bytes()\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


def test_adv_module_level_rebind_to_unrelated_path_does_not_leak_stale_depth():
    """bc8ac68's regression case: rebinding ``_TESTS_DIR`` to something that
    does not resolve (a plain string-literal ``Path(...)``) must drop its
    stale ``depths`` entry, so the later ``_REPO_ROOT = _TESTS_DIR.parent``
    does not inherit a depth that belongs to the discarded first binding."""
    source = (
        "from pathlib import Path\n"
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        '_TESTS_DIR = Path("/tmp/unrelated")\n'
        "_REPO_ROOT = _TESTS_DIR.parent\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (_REPO_ROOT / {_JOIN}).read_bytes()\n"
    )
    assert guard.classify_module(source, MODULE_PATH) == []


def test_adv_function_local_rebind_control_still_one_violation():
    """Positive control for the next test: without the rebind, a
    function-local ``root = _TESTS_DIR.parent`` off a module-level one-step
    root still resolves to one violation."""
    source = (
        "from pathlib import Path\n"
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        "    root = _TESTS_DIR.parent\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (root / {_JOIN}).read_bytes()\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)


def test_adv_function_local_rebind_to_unrelated_call_does_not_leak_stale_depth():
    """Function-local counterpart of the module-level regression above:
    rebinding ``_TESTS_DIR`` inside the function body to an arbitrary call
    result must drop the depth it inherited from the module-level scan, so
    ``root = _TESTS_DIR.parent`` does not resolve off the stale binding."""
    source = (
        "from pathlib import Path\n"
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        "\n\n"
        "def test_x(tmp_path):\n"
        "    _TESTS_DIR = some_unrelated_call()\n"
        "    root = _TESTS_DIR.parent\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (root / {_JOIN}).read_bytes()\n"
    )
    assert guard.classify_module(source, MODULE_PATH) == []


def test_adv_function_local_rebind_does_not_leak_into_a_later_function():
    """A function-local rebind must not poison a *sibling* function's use of
    the same module-level name: ``test_a`` rebinds and stops resolving,
    ``test_b`` never rebinds and must still report its violation."""
    source = (
        "from pathlib import Path\n"
        "_TESTS_DIR = Path(__file__).resolve().parent\n"
        "\n\n"
        "def test_a(tmp_path):\n"
        "    _TESTS_DIR = some_unrelated_call()\n"
        "    root = _TESTS_DIR.parent\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (root / {_JOIN}).read_bytes()\n"
        "\n\n"
        "def test_b(tmp_path):\n"
        "    root = _TESTS_DIR.parent\n"
        '    fresh = tmp_path / "fresh.json"\n'
        f"    assert fresh.read_bytes() == (root / {_JOIN}).read_bytes()\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    _one_violation(violations)
    assert violations[0].line > source.splitlines().index("def test_b(tmp_path):") + 1


def test_adv_unchanged_fence_still_not_a_violation():
    """Re-run of test_127's unchanged-fence idiom in this module, for the
    same reason: comparing the same committed path to itself twice within
    one run must still not be a violation after the resolver change."""
    source = (
        "from pathlib import Path\n"
        "\n"
        "def test_fence():\n"
        '    p = Path("src/segfacet/reference/reference_default.json")\n'
        "    before = p.read_bytes()\n"
        "    # ... some unrelated operation happens here ...\n"
        "    assert p.read_bytes() == before\n"
    )
    violations = guard.classify_module(source, MODULE_PATH)
    assert not violations
