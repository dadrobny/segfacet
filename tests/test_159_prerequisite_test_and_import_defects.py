"""Tests for item 159 -- the prerequisite test-and-import defects Stage 32
edits (roadmap Stage 31 D5, the test-and-import part of the queue line).

Covers AC1-AC11 from ``docs/aide/items/159-the-prerequisite-test-and-import-defects.md``:

- AC1/AC2: ``segfacet.failure_modes`` / ``segfacet.traceability`` import light
  (no ``numpy``/``scipy``/``nibabel`` root in ``sys.modules``), measured in a
  fresh subprocess.
- AC3/AC4: ``segfacet``'s lazy re-exports keep the public surface and identity
  guarantees, and an unknown attribute still raises ``AttributeError``.
- AC5/AC6: the ``test_143`` AC16 record check, reconciled by this item to a
  frozen required-path set, survives a new corpus case and still catches a
  dropped record row.
- AC7-AC9: ``test_146``/``test_150`` no longer pin the live warning-class set,
  but ``test_150`` still catches an unfilled template slot.
- AC10: no non-docstring string constant under ``tests/**/*.py`` names the
  deleted ``aide/queue-018`` branch.
- AC11: the already-fixed tests this item's spec lists as "kept, not deleted"
  are still defined, by AST.

This module writes nothing under ``src/``; AC1-AC4 run against whatever
``src/segfacet/__init__.py`` currently is, so AC1-AC4 are expected to fail
until the builder lands the lazy re-exports (item 159 spec, Implementation
Steps 1) -- that is the point of writing them first.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Set, Tuple

import pytest

from run_process import run_utf8

import test_143_s_axis_correction as t143

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AIDE_SCRIPT = _REPO_ROOT / ".aide" / "scripts" / "aide.py"
_TESTS_DIR = _REPO_ROOT / "tests"

_HEAVY_ROOTS = {"numpy", "scipy", "nibabel"}


# =========================================================================== #
# AC1/AC2: failure_modes / traceability import light
# =========================================================================== #


def _heavy_roots_after_import(module_name: str) -> Set[str]:
    """The subset of ``{numpy, scipy, nibabel}`` present as a root of some
    ``sys.modules`` key after ``import <module_name>`` in a fresh
    subprocess."""
    proc = run_utf8(
        [
            sys.executable,
            "-c",
            f"import sys, json\nimport {module_name}\nprint(json.dumps(sorted(sys.modules)))",
        ],
        cwd=_REPO_ROOT,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout, f"expected stdout importing {module_name!r}"
    loaded = json.loads(proc.stdout)
    assert loaded, f"expected a non-empty sys.modules listing importing {module_name!r}"
    return {m.split(".")[0] for m in loaded} & _HEAVY_ROOTS


def test_ac1_failure_modes_imports_light():
    assert _heavy_roots_after_import("segfacet.failure_modes") == set()


def test_ac2_traceability_imports_light():
    assert _heavy_roots_after_import("segfacet.traceability") == set()


def test_adv_heavy_roots_helper_flags_a_genuinely_heavy_import():
    """Negative control for AC1/AC2's shared helper: without it, a helper
    that always returns an empty set would pass both checks above while
    checking nothing. ``segfacet.features.fragmentation`` is one of the two
    sources the spec names as heavy (A1/A2), so it must still report at
    least one heavy root."""
    heavy = _heavy_roots_after_import("segfacet.features.fragmentation")
    assert heavy, "expected segfacet.features.fragmentation to load a heavy module"


# =========================================================================== #
# AC3/AC4: public surface, identity, unknown-attribute
# =========================================================================== #


def test_ac3_public_surface_and_identity():
    import segfacet
    import segfacet.verdict as verdict_mod
    import segfacet.empty as empty_mod
    import segfacet.report as report_mod
    import segfacet.human_report as human_report_mod
    import segfacet.feature_report as feature_report_mod
    import segfacet.features.fragmentation as fragmentation_mod

    assert set(segfacet.__all__) == {
        "__version__",
        "Severity",
        "Reason",
        "Verdict",
        "CheckResult",
        "check_empty",
        "serialize_report",
        "serialize_report_json",
        "render_human_report",
        "render_feature_table",
        "build_features_block",
        "compute_fragmentation_index",
    }

    defining_module = {
        "Severity": verdict_mod,
        "Reason": verdict_mod,
        "Verdict": verdict_mod,
        "CheckResult": empty_mod,
        "check_empty": empty_mod,
        "serialize_report": report_mod,
        "serialize_report_json": report_mod,
        "render_human_report": human_report_mod,
        "render_feature_table": human_report_mod,
        "build_features_block": feature_report_mod,
        "compute_fragmentation_index": fragmentation_mod,
    }
    for name, module in defining_module.items():
        assert getattr(segfacet, name) is getattr(module, name), name


def test_ac3_fresh_subprocess_from_import_succeeds():
    """Covers PEP 562's ``from``-import path specifically (Testing
    Strategy): a fresh subprocess ``from segfacet import ...`` the two
    lazily-resolved names plus one eager name, and must exit 0."""
    proc = run_utf8(
        [
            sys.executable,
            "-c",
            "from segfacet import check_empty, CheckResult, compute_fragmentation_index",
        ],
        cwd=_REPO_ROOT,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr


def test_ac4_unknown_attribute_raises_naming_it():
    import segfacet

    with pytest.raises(AttributeError, match="no_such_attribute_159"):
        getattr(segfacet, "no_such_attribute_159")


# =========================================================================== #
# AC5/AC6: the reconciled test_143 AC16 record check
# =========================================================================== #


def test_ac5_record_check_survives_a_new_corpus_case(tmp_path):
    extra_case = {
        "scan_fixture": "synthetic_159_extra_scan.nii.gz",
        "seg_fixture": "synthetic_159_extra_seg.nii.gz",
    }
    injected_paths = {
        f"tests/corpus/{extra_case['scan_fixture']}",
        f"tests/corpus/{extra_case['seg_fixture']}",
    }

    # Precondition: the injected fixture paths are genuinely absent from the
    # record, so this test cannot pass on a no-op injection.
    rows, header = t143._load_record_rows()
    path_col = t143._find_column(header, "path", "artifact")
    row_paths = {t143._normalise_cell_path(row[path_col]) for row in rows}
    assert injected_paths.isdisjoint(row_paths), (
        "the injected fixture paths are already present in the record -- "
        "this test's own precondition failed"
    )

    geo_copy = tmp_path / "manifest.json"
    intensity_copy = tmp_path / "intensity_manifest.json"
    for src, dest in (
        (_REPO_ROOT / "tests" / "corpus" / "manifest.json", geo_copy),
        (_REPO_ROOT / "tests" / "corpus" / "intensity" / "manifest.json", intensity_copy),
    ):
        manifest = json.loads(src.read_text(encoding="utf-8"))
        manifest["cases"] = list(manifest["cases"]) + [extra_case]
        dest.write_text(json.dumps(manifest), encoding="utf-8")

    # The check passes when driven against the extended copies -- it no
    # longer derives its required set from manifest content.
    t143._check_record_covers_required(
        geo_manifest_path=geo_copy, intensity_manifest_path=intensity_copy
    )
    # It even passes when the manifest paths do not exist on disk at all: a
    # regression that reintroduced live derivation would raise
    # FileNotFoundError here, so this call is the stronger proof.
    t143._check_record_covers_required(
        geo_manifest_path=tmp_path / "does-not-exist.json",
        intensity_manifest_path=tmp_path / "also-does-not-exist.json",
    )


def test_ac6_record_check_keeps_its_force(tmp_path):
    rows, header = t143._load_record_rows()
    path_col = t143._find_column(header, "path", "artifact")
    removed_row = rows[0]
    removed_path = t143._normalise_cell_path(removed_row[path_col])

    # Precondition: the row picked for removal really is one of the 27
    # required paths.
    assert removed_path in t143._required_artifact_paths(), (
        f"test precondition failed: {removed_path!r} is not a required path"
    )

    text = t143._RECORD_DOC_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    pipe_indices = [i for i, ln in enumerate(lines) if ln.strip().startswith("|")]
    data_indices = pipe_indices[2:]
    assert len(data_indices) == len(rows), (
        "raw table line count does not match parsed row count -- cannot "
        "safely align the row to remove"
    )
    removed_index = data_indices[0]
    assert removed_path in lines[removed_index], (
        "alignment assumption between the parsed row order and the raw "
        "table lines does not hold -- test precondition failed"
    )

    modified_lines = lines[:removed_index] + lines[removed_index + 1 :]
    modified_record = tmp_path / "record.md"
    modified_record.write_text("\n".join(modified_lines) + "\n", encoding="utf-8")

    with pytest.raises(AssertionError):
        t143._check_record_covers_required(record_path=modified_record)


# =========================================================================== #
# AC7-AC9: test_146/test_150 no longer pin the live warning-class set, but
# test_150 still catches an unfilled template slot
# =========================================================================== #

_TEST_146_PATH = _TESTS_DIR / "test_146_ninth_mode_and_first_proposed.py"
_TEST_150_PATH = _TESTS_DIR / "test_150_maintainer_sign_off.py"

_UNRECOGNISED_WARNING = (
    "progress.md: 2 deliverable bullets with identical prose, attributed to item 999"
)
_UNFILLED_SLOT_WARNING = "progress.md:9: unfilled template slot {{example}}"


def _load_module_from_path(path: Path, unique_name: str):
    spec = importlib.util.spec_from_file_location(unique_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


class _InjectingAide:
    """Wraps a real, freshly-loaded ``aide.py`` module so ``run_checks``
    returns the live result plus one extra warning (spec A9) -- the seam
    AC7-AC9 drive by monkeypatching a test module's ``_aide_module``."""

    def __init__(self, real_aide, extra_warning: str):
        self._real = real_aide
        self._extra_warning = extra_warning
        self.calls = 0
        self.last_warnings: List[str] = []

    def load_config(self, repo_root):
        return self._real.load_config(repo_root)

    def run_checks(self, repo_root, config, branches=None):
        self.calls += 1
        errors, warnings = self._real.run_checks(repo_root, config, branches)
        self.last_warnings = list(warnings) + [self._extra_warning]
        return errors, self.last_warnings


def test_ac7_test_146_no_longer_pins_the_warning_class_set(monkeypatch):
    module = _load_module_from_path(_TEST_146_PATH, "_test_146_for_159_ac7")
    real_aide = _load_module_from_path(_AIDE_SCRIPT, "_aide_cli_159_ac7_real")
    injector = _InjectingAide(real_aide, _UNRECOGNISED_WARNING)
    monkeypatch.setattr(module, "_aide_module", lambda: injector)

    module.test_ac36_aide_check_reports_no_error_and_no_new_warning_class()

    # Guard against vacuity: the wrapper was actually called, and the
    # injected, unclassifiable warning really is in what it returned.
    assert injector.calls == 1, "the injected wrapper's run_checks was never called"
    assert _UNRECOGNISED_WARNING in injector.last_warnings


def test_ac8_test_150_no_longer_pins_the_warning_class_set(monkeypatch):
    module = _load_module_from_path(_TEST_150_PATH, "_test_150_for_159_ac8")
    real_aide = _load_module_from_path(_AIDE_SCRIPT, "_aide_cli_159_ac8_real")
    injector = _InjectingAide(real_aide, _UNRECOGNISED_WARNING)
    monkeypatch.setattr(module, "_aide_module", lambda: injector)

    module.test_ac4_aide_check_reports_no_error_and_no_unfilled_slot()

    assert injector.calls == 1, "the injected wrapper's run_checks was never called"
    assert _UNRECOGNISED_WARNING in injector.last_warnings


def test_ac9_test_150_still_catches_an_unfilled_slot(monkeypatch):
    module = _load_module_from_path(_TEST_150_PATH, "_test_150_for_159_ac9")
    real_aide = _load_module_from_path(_AIDE_SCRIPT, "_aide_cli_159_ac9_real")
    injector = _InjectingAide(real_aide, _UNFILLED_SLOT_WARNING)
    monkeypatch.setattr(module, "_aide_module", lambda: injector)

    with pytest.raises(AssertionError):
        module.test_ac4_aide_check_reports_no_error_and_no_unfilled_slot()

    assert injector.calls == 1, "the injected wrapper's run_checks was never called"
    assert _UNFILLED_SLOT_WARNING in injector.last_warnings


# =========================================================================== #
# AC10: no non-docstring reference to the deleted aide/queue-018 branch
# =========================================================================== #

# Built by concatenation so this module's own source never carries the full
# needle as one string constant (AC10: "the module that holds it does not
# match itself").
_QUEUE_018_NEEDLE = "aide/" + "queue-018"


def _docstring_constant_ids(tree: ast.AST) -> Set[int]:
    """``id()`` of every ``Constant`` node that is a module/class/function
    docstring (the first statement of that body, an ``Expr`` wrapping a
    string ``Constant``)."""
    ids: Set[int] = set()

    def _mark(node) -> None:
        body = getattr(node, "body", None)
        if body:
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                ids.add(id(first.value))

    _mark(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            _mark(node)
    return ids


def _non_docstring_string_constants_containing(tree: ast.AST, needle: str) -> List[str]:
    docstring_ids = _docstring_constant_ids(tree)
    hits: List[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
            and needle in node.value
        ):
            hits.append(node.value)
    return hits


def test_ac10_no_non_docstring_reference_to_the_deleted_queue_018_branch():
    offenders = []
    for path in sorted(_TESTS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits = _non_docstring_string_constants_containing(tree, _QUEUE_018_NEEDLE)
        if hits:
            offenders.append((path.relative_to(_REPO_ROOT).as_posix(), hits))
    assert offenders == [], offenders


def test_adv_ac10_scanner_flags_a_planted_non_docstring_reference():
    """Negative control: a planted snippet using the retired branch as a
    plain (non-docstring) string constant is flagged. The snippet's source
    text is itself built by concatenation, so this file never carries the
    full needle as a single constant either."""
    snippet_src = 'subprocess.run(["git", "diff", "aide/' + 'queue-018"])\n'
    tree = ast.parse(snippet_src)
    hits = _non_docstring_string_constants_containing(tree, _QUEUE_018_NEEDLE)
    assert hits == [_QUEUE_018_NEEDLE]


def test_adv_ac10_scanner_ignores_a_docstring_reference():
    """A module docstring naming the retired branch as provenance (as
    several committed modules legitimately do) must not be flagged."""
    snippet_src = '"""mentions aide/' + 'queue-018 as history."""\n'
    tree = ast.parse(snippet_src)
    hits = _non_docstring_string_constants_containing(tree, _QUEUE_018_NEEDLE)
    assert hits == []


# =========================================================================== #
# AC11: the already-fixed tests were kept, not deleted
# =========================================================================== #

_AC11_EXPECTED_NAMES: Tuple[Tuple[Path, str], ...] = (
    (
        _TESTS_DIR / "test_147_specification_is_the_record.py",
        "test_ac3_mode_anchor_paths_stays_under_its_own_metric_label",
    ),
    (
        _TESTS_DIR / "test_147_specification_is_the_record.py",
        "test_ac9_every_mechanism_names_a_token_that_resolves_live",
    ),
    (
        _TESTS_DIR / "test_136_rule_mode_declarations.py",
        "test_ac8_surplus_declared_mode_is_reported_naming_both",
    ),
    (
        _TESTS_DIR / "test_145_eight_hypothesised_modes.py",
        "test_ac23_fresh_matches_committed_structurally_and_carries_every_signed_off_id",
    ),
    (
        _TESTS_DIR / "test_146_ninth_mode_and_first_proposed.py",
        "test_ac30_proposed_entry_acquiring_a_declaring_rule_is_reported",
    ),
    (_TESTS_DIR / "test_148_per_path_mode_attribution.py", "_status_report_module"),
    (
        _TESTS_DIR / "test_103_feature_catalogue.py",
        "test_ac13_rule_mode_map_effect_on_failure_modes",
    ),
)


def _module_level_function_names(path: Path) -> Set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


@pytest.mark.parametrize(
    "path,name",
    _AC11_EXPECTED_NAMES,
    ids=[f"{p.name}::{n}" for p, n in _AC11_EXPECTED_NAMES],
)
def test_ac11_already_fixed_test_was_kept(path, name):
    assert name in _module_level_function_names(path), (path.as_posix(), name)


def test_adv_ac11_presence_check_reports_a_genuinely_absent_name():
    """Negative control: a name that is not defined is reported absent --
    otherwise the AST presence check above could pass regardless of what it
    is asked about."""
    names = _module_level_function_names(
        _TESTS_DIR / "test_147_specification_is_the_record.py"
    )
    assert "test_ac_does_not_exist_159" not in names
