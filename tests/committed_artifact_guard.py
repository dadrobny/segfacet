"""Static classifier + allowlist for byte-exact fresh-vs-committed comparisons
under ``tests/`` (item 127).

``segfacet.synth.golden.assert_matches_committed_artifact`` is the one path a
test should take to compare freshly-generated output against a committed
artifact (numeric-tolerance leaves, everything else exact -- item 078). This
module is the enforcing half: :func:`classify_module` walks a test module's
AST for a byte-exact (``==``/``!=``) comparison where exactly one operand
resolves to a **committed** path (a repo-relative file this repo ships, not
something the test itself wrote under ``tmp_path`` this run) and the other
operand does not resolve to that *same* committed path, then reports it as a
:class:`Violation` unless the committed path is covered by :data:`ALLOWLIST`.
:func:`violation_message` renders the failure, naming
``assert_matches_committed_artifact`` as the fix.

Standing rule: the emission-clamp requirement
----------------------------------------------
An artifact that reports a raw float measurement alongside its own
"meaningfully nonzero" threshold must clamp sub-threshold values to a fixed
sentinel at the serialisation boundary before it can be byte-compared --
quantisation alone (``float(f"{v:.6g}")``) cannot stabilise cancellation-scale
numerical residue, which is still noise at six significant digits (measured
2026-08-30, PR #56). ``segfacet.observed_range.emission_range`` is the shipped
example: a covered-but-not-informative population emits
``(0.0, 0.0, 0.0, 0.0)`` while ``PopulationRange`` keeps the raw measurement
for every caller that classifies on it. Five other grounds make byte
comparison legitimate -- see :data:`GROUNDS` -- and every :data:`ALLOWLIST`
entry names its ground and carries a one-line reason.

Standing rule: the no-float-leaf ground
-----------------------------------------
Item 149 adds a sixth ground, ``"no-float-leaf"``: an artifact whose payload
tree (walked to every leaf, JSON object values included) carries **zero**
``float`` instances is byte-safe to compare fresh-vs-committed
unconditionally -- there is no floating-point representation or platform
arithmetic residue for a byte comparison to be fragile against, only integers,
strings, booleans and ``null``. This ground is discharged by a dedicated test
that walks the payload and asserts the float count is zero, never by an
assertion in the reason string (the guard itself performs no float walk --
it is a static AST classifier, same as every other ground): see
``tests/test_149_conformance_report.py``'s
``test_ac21_traceability_matrix_has_no_float_leaf`` and
``test_ac21_failure_modes_specification_has_no_float_leaf``, which the
:data:`ALLOWLIST` entries below name directly.

Standing rule: the consumer-survey requirement
------------------------------------------------
A spec that changes a feature the reference artifact aggregates must survey
its consumers **mechanically** -- ``grep -l build_and_write_default tests/``
-- never by hand-listing. Item 123's recalibration is the precedent: the same
four-line fresh-vs-committed comparison existed in four unrelated modules, and
hand-listing found only three of them.

``src/segfacet/reference/reference_default.json`` is deliberately absent from
:data:`ALLOWLIST`: 454 of its 1133 float leaves (measured 2026-08-31) are
full-precision computed statistics, exactly the shape item 078 proved is not
byte-stable across NumPy versions, platform BLAS/SIMD and libm rounding. Every
comparison against it goes through ``assert_matches_committed_artifact``
instead (item 127's AC2/AC10 helper cases and AC16's synthetic violation both
exercise this exclusion directly).

Precise, not exhaustive
------------------------
:func:`classify_module` resolves an operand to a committed path only through:
a string literal passed to ``Path(...)``; a module-level or function-local
name bound to a chain of ``.resolve()``/``.parent``/``.parents[N]`` (``N`` a
non-negative int literal) starting at ``Path(__file__)`` (a
"``_REPO_ROOT``-style" root) -- including a name reached in two hops, one
name bound to the chain and a second bound to ``.parent`` on the first name
(``_TESTS_DIR = Path(__file__).resolve().parent`` then
``_REPO_ROOT = _TESTS_DIR.parent``) -- optionally further joined with literal
string segments via ``/``; a local variable assigned from one of those in the
same function; and the recognised read shapes ``.read_bytes()``,
``.read_text(...)`` and ``hashlib.sha256(<path>.read_bytes()).hexdigest()`` --
including a local variable that was itself assigned from one of those read
shapes earlier in the same function (the "unchanged fence" idiom: read once,
do something, read again, compare to the stored value). A one-step root
(``Path(__file__).resolve().parent`` or ``.parents[0]``, named or not) is
deliberately not "the repo root" -- see :func:`_is_file_root_chain`.

Still skipped in silence:
- a ``pathlib.Path(__file__)`` root (the attribute-call form): ``(pathlib.Path(__file__).parent.parent / ARTIFACT).read_bytes()``
- a bare function argument used as a root: ``(arg / ARTIFACT).read_bytes()``
- the result of an arbitrary call used as a root: ``(arg() / ARTIFACT).read_bytes()``
- a ``parents`` index that is not a non-negative int literal: ``(Path(__file__).resolve().parents[n] / ARTIFACT).read_bytes()``
- a value reached through json.loads: ``(Path(json.loads(arg)) / ARTIFACT).read_bytes()``
- a comprehension variable: ``Path(next(p for p in [ARTIFACT])).read_bytes()``
- a path segment that is not a string literal (an f-string): ``(Path(__file__).resolve().parent.parent / f'{ARTIFACT}').read_bytes()``

A loop variable (bound by a ``for`` statement rather than a comprehension), a
path built from ``tmp_path``, and every placement shape described below are
also skipped, but do not fit this list's one-expression-per-line form. A
reported :class:`Violation` is therefore authoritative; a clean
:func:`iter_violations` run is not a proof of absence.

Certain *placements* of an otherwise-recognised comparison are never
classified regardless of operand shape: a comparison inside a class method, a
module-level (not function-body) comparison, a module in a subdirectory of
``tests/`` (:func:`iter_violations` is non-recursive), and an ``in``/``is``/
chained comparison (only a single ``==``/``!=`` between exactly two operands
is recognised).
"""

from __future__ import annotations

import ast
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Allowlist
# --------------------------------------------------------------------------- #

#: Closed vocabulary of grounds on which a byte-exact fresh-vs-committed
#: comparison is legitimate. Adding a member is a deliberate edit an author
#: must justify -- that is the point.
GROUNDS: Tuple[str, ...] = (
    "exact-parameter-floats",
    "emission-clamped",
    "hand-written-literals",
    "binary-fixture",
    "integrity-pin",
    "no-float-leaf",
)


@dataclass(frozen=True)
class AllowlistEntry:
    """One legitimate byte-exact fresh-vs-committed comparison.

    ``path`` is a repo-relative path or glob (matched against a resolved
    committed path with :func:`fnmatch.fnmatch`); ``ground`` is a member of
    :data:`GROUNDS`; ``reason`` is a non-empty single-line justification.
    """

    path: str
    ground: str
    reason: str


#: Every entry below is measured against the post-item-126 inventory
#: (2026-08-31): the nine snapshots from the retired corpus golden-snapshot
#: store (see item 126 / ``docs/aide/golden-decision-table.md``'s Retirement
#: execution log) and the two
#: ``tests/golden/0NN_*.json`` snapshots item 126 retired are absent here, and
#: ``tests/golden/report_format_contract.json`` -- the surviving fixture -- is
#: keyed by the same ``tests/golden/*.json`` glob its ``.gitattributes`` pin
#: uses, not by its own filename. ``src/segfacet/reference/reference_default.json``
#: is deliberately absent -- see the module docstring. ``docs/aide/golden-
#: decision-table.md`` is read-only prose, never regenerated and compared
#: fresh-vs-committed, so it stays out of this allowlist even though it is
#: byte-read and LF-pinned (``tests/test_111_golden_guard.py``'s
#: ``_KNOWN_BYTE_EXACT_FIXTURE_FAMILIES`` covers that separately).
ALLOWLIST: Tuple[AllowlistEntry, ...] = (
    AllowlistEntry(
        path="tests/corpus/manifest.json",
        ground="exact-parameter-floats",
        reason="36 float leaves, all declared generator parameters or exact "
        "binary values (6.0, 1.0); no computed measurement.",
    ),
    AllowlistEntry(
        path="tests/corpus/intensity/manifest.json",
        ground="exact-parameter-floats",
        reason="Same generator, 16 float leaves, all exact.",
    ),
    AllowlistEntry(
        path="tests/corpus/094_pre_migration_snapshot.json",
        ground="exact-parameter-floats",
        reason="285 float leaves, all affine/spacing components that are "
        "exact binary values; the array payloads are carried as digests, "
        "not floats.",
    ),
    AllowlistEntry(
        path="tests/corpus/fixtures/*.nii.gz",
        ground="binary-fixture",
        reason="Integer label and scan volumes; gzip of an exact byte "
        "payload, pinned binary in .gitattributes.",
    ),
    AllowlistEntry(
        path="tests/corpus/intensity/fixtures/*.nii.gz",
        ground="binary-fixture",
        reason="Same, for the intensity corpus.",
    ),
    AllowlistEntry(
        path="docs/aide/feature_catalogue.generated.json",
        ground="emission-clamped",
        reason="Observed-range floats are quantised to six significant "
        "figures and sub-floor noise is clamped to 0.0 at emission "
        "(segfacet.observed_range.emission_range, item 124).",
    ),
    AllowlistEntry(
        path="docs/aide/feature_catalogue.generated.md",
        ground="emission-clamped",
        reason="The rendered form of the same clamped values.",
    ),
    AllowlistEntry(
        path="tests/golden/*.json",
        ground="hand-written-literals",
        reason="Item 126's feature-value-free format fixture "
        "(report_format_contract.json): every number is a literal "
        "serialised straight through, so the comparison is a formatting "
        "guarantee, not a measurement.",
    ),
    AllowlistEntry(
        path="src/segfacet/reference/reference_verse_v1.json",
        ground="integrity-pin",
        reason="A released production artifact compared against a recorded "
        "digest; there is no freshly computed side, so a change must be "
        "deliberate.",
    ),
    AllowlistEntry(
        path="docs/aide/traceability_matrix.generated.json",
        ground="no-float-leaf",
        reason="Zero float leaves, discharged by test_149_conformance_report."
        "py::test_ac21_traceability_matrix_has_no_float_leaf.",
    ),
    AllowlistEntry(
        path="docs/aide/traceability_matrix.generated.md",
        ground="no-float-leaf",
        reason="The rendered form of the same float-free payload, same "
        "discharging test.",
    ),
    AllowlistEntry(
        path="docs/aide/failure_modes.generated.json",
        ground="no-float-leaf",
        reason="Zero float leaves, discharged by test_149_conformance_report."
        "py::test_ac21_failure_modes_specification_has_no_float_leaf.",
    ),
    AllowlistEntry(
        path="docs/aide/failure_modes.generated.md",
        ground="no-float-leaf",
        reason="The rendered form of the same float-free payload, same "
        "discharging test.",
    ),
)


def _matches_allowlist(committed_path: str) -> bool:
    return any(fnmatch.fnmatch(committed_path, entry.path) for entry in ALLOWLIST)


# --------------------------------------------------------------------------- #
# Violations
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Violation:
    """One off-allowlist byte-exact fresh-vs-committed comparison."""

    module: str
    line: int
    committed_path: str


def violation_message(violations) -> str:
    """Render *violations* as a failure message naming the fix
    (``assert_matches_committed_artifact``) and, per violation, the module,
    line and committed path."""
    lines = [
        "byte-exact comparison(s) against a committed artifact outside the "
        "allowlist -- use segfacet.synth.golden.assert_matches_committed_artifact "
        "instead (see tests/committed_artifact_guard.py):",
    ]
    for v in violations:
        lines.append(f"  {v.module}:{v.line} -- committed artifact {v.committed_path!r}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# AST resolution -- see the module docstring's "Precise, not exhaustive"
# --------------------------------------------------------------------------- #


def _is_name(node, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _file_root_parent_count(node, depths: Optional[Dict[str, int]] = None) -> Optional[int]:
    """If *node* is a chain of ``.resolve()``/``.parent``/``.parents[N]``
    starting at ``Path(__file__)``, return how many ``.parent`` steps it
    takes (0 for ``Path(__file__)`` itself); otherwise ``None``.

    *depths* maps a name already known to carry such a chain (bound earlier
    at module level or, for a function-local pre-scan, earlier in the same
    function) to its depth, so a name may stand in anywhere a literal chain
    could -- ``parents[N]`` counts as N+1 ``.parent`` steps on top of its
    inner chain's depth.
    """
    if depths is None:
        depths = {}
    if isinstance(node, ast.Name):
        return depths.get(node.id)
    if isinstance(node, ast.Call) and _is_name(node.func, "Path") and len(node.args) == 1:
        arg = node.args[0]
        if isinstance(arg, ast.Name) and arg.id == "__file__":
            return 0
        return None
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "resolve"
        and not node.args
    ):
        return _file_root_parent_count(node.func.value, depths)
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        inner = _file_root_parent_count(node.value, depths)
        return None if inner is None else inner + 1
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
    ):
        index_node = node.slice
        if not (isinstance(index_node, ast.Constant) and type(index_node.value) is int and index_node.value >= 0):
            return None
        inner = _file_root_parent_count(node.value.value, depths)
        return None if inner is None else inner + index_node.value + 1
    return None


def _is_file_root_chain(node, depths: Optional[Dict[str, int]] = None) -> bool:
    """True iff *node* is a ``Path(__file__)``-based chain (directly, via
    ``parents[N]``, or via a name carrying one of these -- see *depths* on
    :func:`_file_root_parent_count`) reaching at least two ``.parent`` steps
    up, e.g. ``Path(__file__).resolve().parent.parent``.

    A *single* ``.parent`` (a module's own containing directory, e.g.
    ``tests/`` for a module directly under it) is deliberately not treated as
    "the repo root" -- this classifier has no notion of a module's real
    on-disk depth (see the module docstring), so a one-parent chain used to
    join further literal segments (e.g. ``Path(__file__).parent / "golden" /
    "x.json"``) would otherwise resolve to a path relative to the *module's*
    directory rather than the repo root, and silently mismatch every
    repo-relative allowlist entry.
    """
    count = _file_root_parent_count(node, depths)
    return count is not None and count >= 2


def _resolve_expr(node, known: Dict[str, str], depths: Optional[Dict[str, int]] = None) -> Optional[str]:
    """Resolve *node* to a repo-relative path string, or ``None`` if it is
    not one of the recognised shapes (see the module docstring)."""
    if depths is None:
        depths = {}
    if _is_file_root_chain(node, depths):
        return ""
    if isinstance(node, ast.Name):
        return known.get(node.id)
    if isinstance(node, ast.Call) and _is_name(node.func, "Path") and len(node.args) == 1:
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _resolve_expr(node.left, known, depths)
        if left is None:
            return None
        if not (isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)):
            return None
        segment = node.right.value
        return segment if left == "" else f"{left.rstrip('/')}/{segment}"
    return None


def _extract_path_expr_from_read(node) -> Optional[ast.expr]:
    """If *node* is one of the recognised committed-artifact read shapes
    (``.read_bytes()``, ``.read_text(...)``,
    ``hashlib.sha256(<path>.read_bytes()).hexdigest()``), return the AST
    expression for the path it reads. Otherwise ``None``."""
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in ("read_bytes", "read_text"):
        return func.value
    if isinstance(func, ast.Attribute) and func.attr == "hexdigest" and not node.args:
        inner = func.value
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "sha256"
            and isinstance(inner.func.value, ast.Name)
            and inner.func.value.id == "hashlib"
            and len(inner.args) == 1
        ):
            return _extract_path_expr_from_read(inner.args[0])
    return None


def _walk_stmts(stmts):
    """Yield every statement under *stmts*, recursing into ``body``,
    ``orelse`` and ``finalbody`` in source order."""
    for stmt in stmts:
        yield stmt
        for field in ("body", "orelse", "finalbody"):
            substmts = getattr(stmt, field, None)
            if substmts:
                yield from _walk_stmts(substmts)


def _module_level_paths(tree: ast.Module) -> Tuple[Dict[str, str], Dict[str, int]]:
    """Resolve every module-level single-name assignment. Returns
    ``(known, depths)``: ``known`` maps a name to the repo-relative path it
    resolves to (a ``Path(__file__)``-based root resolves to ``""``);
    ``depths`` additionally records the ``.parent`` depth of *every* such
    assignment whose value is a ``Path(__file__)`` chain (directly or via a
    name already in ``depths``), at any depth including one -- a one-step
    root has no entry in ``known`` (it is not the repo root) but must still
    be available for a later name to step off of, e.g. ``_REPO_ROOT =
    _TESTS_DIR.parent``.
    """
    known: Dict[str, str] = {}
    depths: Dict[str, int] = {}
    for stmt in tree.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
        ):
            name = stmt.targets[0].id
            count = _file_root_parent_count(stmt.value, depths)
            if count is not None:
                depths[name] = count
            resolved = _resolve_expr(stmt.value, known, depths)
            if resolved is not None:
                known[name] = resolved
    return known, depths


def _resolve_operand(
    operand: ast.expr,
    known: Dict[str, str],
    read_results: Dict[str, str],
    depths: Optional[Dict[str, int]] = None,
) -> Optional[str]:
    """Resolve one comparison operand to a committed path, if it is (or
    stands in for) a read of one."""
    path_expr = _extract_path_expr_from_read(operand)
    if path_expr is not None:
        return _resolve_expr(path_expr, known, depths)
    if isinstance(operand, ast.Name) and operand.id in read_results:
        return read_results[operand.id]
    return None


def _classify_function(
    func,
    module_known: Dict[str, str],
    module_path: str,
    module_depths: Optional[Dict[str, int]] = None,
) -> List[Violation]:
    local_known: Dict[str, str] = dict(module_known)
    local_depths: Dict[str, int] = dict(module_depths) if module_depths else {}
    local_reads: Dict[str, str] = {}

    for stmt in _walk_stmts(func.body):
        if not (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
        ):
            continue
        name = stmt.targets[0].id
        count = _file_root_parent_count(stmt.value, local_depths)
        if count is not None:
            local_depths[name] = count
        resolved = _resolve_expr(stmt.value, local_known, local_depths)
        if resolved is not None:
            local_known[name] = resolved
            continue
        path_expr = _extract_path_expr_from_read(stmt.value)
        if path_expr is not None:
            read_resolved = _resolve_expr(path_expr, local_known, local_depths)
            if read_resolved is not None:
                local_reads[name] = read_resolved

    violations: List[Violation] = []
    for stmt in _walk_stmts(func.body):
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
                continue
            if len(node.comparators) != 1:
                continue
            left = _resolve_operand(node.left, local_known, local_reads, local_depths)
            right = _resolve_operand(node.comparators[0], local_known, local_reads, local_depths)
            resolved = [r for r in (left, right) if r is not None]
            if len(resolved) != 1:
                # Zero operands resolve (fresh-vs-fresh, AC19) or both
                # resolve to (the same, AC18, or a different) committed
                # path -- neither is a fresh-vs-committed comparison.
                continue
            committed_path = resolved[0]
            if not _matches_allowlist(committed_path):
                violations.append(
                    Violation(module=module_path, line=node.lineno, committed_path=committed_path)
                )
    return violations


def classify_module(source: str, module_path: str) -> List[Violation]:
    """Classify one test module's *source* for byte-exact fresh-vs-committed
    comparisons whose committed artifact is not on :data:`ALLOWLIST`.

    *module_path* is a label for the module (used only in the returned
    :class:`Violation`\\ s), typically its repo-relative path. Invalid Python
    (or empty source) reports no violations rather than raising -- see the
    module docstring's "Precise, not exhaustive" section."""
    try:
        tree = ast.parse(source, filename=module_path)
    except SyntaxError:
        return []

    module_known, module_depths = _module_level_paths(tree)

    violations: List[Violation] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_classify_function(stmt, module_known, module_path, module_depths))
    return violations


def iter_violations(tests_dir) -> Iterator[Violation]:
    """Map :func:`classify_module` over every ``*.py`` file directly under
    *tests_dir* (non-recursive -- ``tests/`` carries no nested test
    packages), in sorted filename order."""
    tests_dir = Path(tests_dir)
    for path in sorted(tests_dir.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for violation in classify_module(source, path.as_posix()):
            yield violation
