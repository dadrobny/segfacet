"""Tests for item 170 -- session-scoped ``aide check`` and
specification-regeneration fixtures.

Covers Acceptance Criteria AC1-AC7 from
``docs/aide/items/170-session-scoped-aide-check-and-regeneration-fixtures.md``,
one test each, plus the five named adversarial cases from its Testing
Strategy: ``aide-check-representative``, ``run-to-run-representative``,
``fresh-vs-committed-representative``, ``untouched-representative`` and
``ast-checker-negative-control``.

AC2-AC4 run on stubs under ``tmp_path`` and never trigger a real
``aide check`` or regeneration. AC1/AC5/AC6/AC7 read ``tests/conftest.py``
and the list-M/list-R modules by AST -- every module they read is under this
item's own "May change" authorised paths.

Other test modules are loaded by path with
``importlib.util.spec_from_file_location``, under a module name unique to
this file, the way ``test_159_prerequisite_test_and_import_defects.py``
does, so pytest does not collect them twice.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

import session_artifacts

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TESTS_DIR = _REPO_ROOT / "tests"
_CONFTEST_PATH = _TESTS_DIR / "conftest.py"

_SESSION_FIXTURE_NAMES = (
    "aide_check_result",
    "regenerated_failure_modes",
    "regenerated_traceability",
)

#: List M (item 170 spec): module -> migrated function names.
_LIST_M = {
    "test_aide_check_no_errors.py": ["test_aide_check_reports_no_errors"],
    "test_146_ninth_mode_and_first_proposed.py": [
        "test_ac36_aide_check_reports_no_error_and_no_new_warning_class",
    ],
    "test_150_maintainer_sign_off.py": [
        "test_ac4_aide_check_reports_no_error_and_no_unfilled_slot",
        "test_ac4_gate_warnings_feed_run_checks",
        "test_ac11_artifacts_are_byte_identical_to_a_fresh_regeneration",
        "test_ac11_two_successive_regenerations_agree_byte_for_byte",
    ],
    "test_159_prerequisite_test_and_import_defects.py": [
        "test_ac7_test_146_no_longer_pins_the_warning_class_set",
        "test_ac8_test_150_no_longer_pins_the_warning_class_set",
        "test_ac9_test_150_still_catches_an_unfilled_slot",
    ],
    "test_144_failure_mode_specification.py": [
        "test_ac17_redirected_run_leaves_committed_artifacts_untouched",
        "test_ac18_artifacts_are_byte_reproducible_run_to_run",
        "test_adv_main_called_twice_is_deterministic",
    ],
    "test_145_eight_hypothesised_modes.py": [
        "test_ac23_regeneration_is_byte_reproducible_run_to_run",
    ],
    "test_147_specification_is_the_record.py": [
        "test_ac23_new_fields_reach_both_artifacts",
        "test_ac24_all_three_artifact_pairs_regenerate_byte_identically",
    ],
    "test_157_case_id_rename.py": [
        "test_ac16_failure_mode_specification_artifacts_regenerate_identically",
        "test_ac17_traceability_matrix_artifacts_regenerate_identically",
    ],
    "test_138_traceability_matrix.py": [
        "test_ac2_main_redirects_writes_and_leaves_committed_artifacts_unchanged",
        "test_ac3_artifacts_are_byte_reproducible_run_to_run",
    ],
    "test_143_s_axis_correction.py": [
        "test_ac11_traceability_matrix_regenerates_byte_identically",
        "test_ac12_traceability_matrix_json_matches_committed",
        "test_ac15_traceability_matrix_markdown_matches_committed_byte_for_byte",
    ],
    "test_148_per_path_mode_attribution.py": [
        "test_ac18_traceability_untouched_and_paths_derived_from_consuming_rules",
    ],
    "test_149_conformance_report.py": [
        "test_ac20_both_artifacts_regenerate_byte_identically_run_to_run",
        "test_ac20_fresh_matches_committed_byte_for_byte",
    ],
}

# test_ac33_downstream_artifacts_regenerate_byte_identically_run_to_run and
# test_ac24_all_three_artifact_pairs_regenerate_byte_identically also carry a
# `catalogue.main(...)` call of their own (spec: "the catalogue.main half
# stays in the test") -- exempt by receiver name, not by omission from list M.
_LIST_M["test_146_ninth_mode_and_first_proposed.py"] += [
    "test_ac32_specification_artifacts_regenerate_byte_identically_run_to_run",
    "test_ac33_downstream_artifacts_regenerate_byte_identically_run_to_run",
    "test_ac33_traceability_matrix_matches_committed_structurally",
]

#: List R (item 170 spec): module -> removed function names.
_LIST_R = {
    "test_128_relocation_checks.py": [
        "test_ac23_aide_check_emits_no_gitattributes_lint_warning",
    ],
    "test_134_decision_table_evidence_companion.py": [
        "test_ac7_aide_check_names_neither_new_path",
    ],
    "test_146_ninth_mode_and_first_proposed.py": [
        "test_ac36_no_warning_names_a_path_this_item_writes",
        "test_adv_unclassified_warning_would_be_caught",
    ],
    "test_149_conformance_report.py": [
        "test_ac22_aide_check_reports_no_gitattributes_warning_for_these_paths",
    ],
}

#: The seven modules AC7 sweeps for a module-wide `run_checks` call.
_AC7_MODULES = (
    "test_aide_check_no_errors.py",
    "test_128_relocation_checks.py",
    "test_134_decision_table_evidence_companion.py",
    "test_146_ninth_mode_and_first_proposed.py",
    "test_149_conformance_report.py",
    "test_150_maintainer_sign_off.py",
    "test_159_prerequisite_test_and_import_defects.py",
)


def _load_module_from_path(path: Path, unique_name: str):
    spec = importlib.util.spec_from_file_location(unique_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _top_level_functions(tree: ast.Module) -> dict:
    """Module-level function definitions only -- not nested in a class or
    another function (AC5/AC6 both key on "defined at module level")."""
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _calls_a_regenerator_main(func_node: ast.AST) -> bool:
    """True iff *func_node* contains an ``ast.Call`` whose ``func`` is an
    ``ast.Attribute`` with ``attr == "main"``, unless the receiver is the
    bare name ``catalogue`` (AC5)."""
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "main"):
            continue
        receiver = func.value
        if isinstance(receiver, ast.Name) and receiver.id == "catalogue":
            continue
        return True
    return False


def _contains_run_checks_call(tree: ast.AST) -> bool:
    """True iff *tree* contains an ``ast.Call`` anywhere -- helpers and
    class methods included -- whose ``func`` is an ``ast.Attribute`` with
    ``attr == "run_checks"`` (AC7)."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run_checks"
        ):
            return True
    return False


# =========================================================================== #
# AC1: the three fixtures are session-scoped
# =========================================================================== #


def test_ac1_the_three_fixtures_are_session_scoped():
    tree = _parse(_CONFTEST_PATH)
    top_level = _top_level_functions(tree)
    for name in _SESSION_FIXTURE_NAMES:
        assert name in top_level, f"conftest.py defines no module-level {name}"
        func = top_level[name]
        matched = False
        for deco in func.decorator_list:
            # `@pytest.fixture(scope="session")`
            if not (isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute)):
                continue
            if not (deco.func.attr == "fixture"):
                continue
            for kw in deco.keywords:
                if kw.arg == "scope" and isinstance(kw.value, ast.Constant):
                    if kw.value.value == "session":
                        matched = True
        assert matched, f"{name} is not a @pytest.fixture(scope=\"session\")"


# =========================================================================== #
# AC2: the aide check helper returns the run as immutable tuples
# =========================================================================== #


def test_ac2_aide_check_helper_returns_immutable_tuples(tmp_path):
    stub = tmp_path / "aide_stub.py"
    stub.write_text(
        "def find_repo_root(path):\n"
        "    return path\n"
        "\n"
        "def load_config(repo_root):\n"
        "    return {}\n"
        "\n"
        "def run_checks(repo_root, config, branches=None):\n"
        "    return (['e1'], ['w1', 'w2'])\n",
        encoding="utf-8",
    )

    result = session_artifacts.load_aide_check_result(stub)

    expected = session_artifacts.AideCheckResult(errors=("e1",), warnings=("w1", "w2"))
    assert result == expected
    assert isinstance(result.errors, tuple)
    assert isinstance(result.warnings, tuple)
    # Tuple-to-list equality is False in Python, so this also pins the type.
    assert result.errors != ["e1"]


# =========================================================================== #
# AC3: the regeneration helper returns exactly what its two runs produced
# =========================================================================== #


def _make_stub_main(committed_json: Path, committed_md: Path):
    calls = []

    def stub_main(argv):
        json_dest = Path(argv[argv.index("--json") + 1])
        md_dest = Path(argv[argv.index("--md") + 1])
        calls.append((json_dest, md_dest))
        json_dest.write_bytes(b"fresh json %d" % len(calls))
        md_dest.write_bytes(b"fresh md %d" % len(calls))
        committed_json.write_bytes(b"overwritten json %d" % len(calls))
        committed_md.write_bytes(b"overwritten md %d" % len(calls))
        return 0 if len(calls) == 1 else 7

    return stub_main, calls


def test_ac3_regeneration_helper_returns_exactly_what_the_two_runs_produced(tmp_path):
    committed_json = tmp_path / "committed.json"
    committed_md = tmp_path / "committed.md"
    committed_json.write_bytes(b"before json")
    committed_md.write_bytes(b"before md")

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    stub_main, calls = _make_stub_main(committed_json, committed_md)

    result = session_artifacts.regenerate(stub_main, committed_json, committed_md, out_dir)

    assert len(calls) == 2
    expected = session_artifacts.Regeneration(
        json_a=calls[0][0],
        md_a=calls[0][1],
        json_b=calls[1][0],
        md_b=calls[1][1],
        exit_codes=(0, 7),
        committed_json_before=b"before json",
        committed_md_before=b"before md",
    )
    assert result == expected


# =========================================================================== #
# AC4: the two runs write to four distinct paths
# =========================================================================== #


def test_ac4_the_two_runs_write_to_four_distinct_paths(tmp_path):
    committed_json = tmp_path / "committed.json"
    committed_md = tmp_path / "committed.md"
    committed_json.write_bytes(b"before json")
    committed_md.write_bytes(b"before md")

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    stub_main, _calls = _make_stub_main(committed_json, committed_md)

    result = session_artifacts.regenerate(stub_main, committed_json, committed_md, out_dir)

    members = {result.json_a, result.md_a, result.json_b, result.md_b}
    assert len(members) == 4
    for path in members:
        assert out_dir in path.parents


# =========================================================================== #
# AC5: no migrated test regenerates
# =========================================================================== #


def test_ac5_no_migrated_test_regenerates():
    checked = 0
    for module_name, function_names in _LIST_M.items():
        tree = _parse(_TESTS_DIR / module_name)
        top_level = _top_level_functions(tree)
        for function_name in function_names:
            assert function_name in top_level, (module_name, function_name)
            func = top_level[function_name]
            assert not _calls_a_regenerator_main(func), (
                f"{module_name}::{function_name} still calls a regenerator's main()"
            )
            checked += 1
    assert checked == sum(len(v) for v in _LIST_M.values())


# =========================================================================== #
# AC6: the warning-set pins are gone
# =========================================================================== #


def test_ac6_the_warning_set_pins_are_gone():
    checked = 0
    for module_name, function_names in _LIST_R.items():
        tree = _parse(_TESTS_DIR / module_name)
        top_level = _top_level_functions(tree)
        for function_name in function_names:
            assert function_name not in top_level, (
                f"{module_name} still defines {function_name} at module level"
            )
            checked += 1
    assert checked == sum(len(v) for v in _LIST_R.values())


# =========================================================================== #
# AC7: no aide check run is left in the touched modules
# =========================================================================== #


def test_ac7_no_aide_check_run_is_left_in_the_touched_modules():
    checked = 0
    for module_name in _AC7_MODULES:
        tree = _parse(_TESTS_DIR / module_name)
        assert not _contains_run_checks_call(tree), (
            f"{module_name} still contains a run_checks(...) call"
        )
        checked += 1
    assert checked == len(_AC7_MODULES)


# =========================================================================== #
# Adversarial: aide-check-representative
# =========================================================================== #


def test_adv_aide_check_representative_still_fails_on_the_defect_it_guards():
    module = _load_module_from_path(
        _TESTS_DIR / "test_aide_check_no_errors.py", "_test_170_aide_check_no_errors"
    )
    planted = session_artifacts.AideCheckResult(errors=("planted error",), warnings=())
    # The defect is really present before we trust the raise below (§6).
    assert planted.errors != ()

    with pytest.raises(AssertionError):
        module.test_aide_check_reports_no_errors(planted)


# =========================================================================== #
# Adversarial: run-to-run-representative
# =========================================================================== #


def test_adv_run_to_run_representative_still_fails_on_the_defect_it_guards(tmp_path):
    module = _load_module_from_path(
        _TESTS_DIR / "test_144_failure_mode_specification.py",
        "_test_170_failure_mode_specification",
    )
    import segfacet.failure_modes as fm

    committed_json_bytes = fm.JSON_PATH.read_bytes()
    committed_md_bytes = fm.MD_PATH.read_bytes()

    json_a = tmp_path / "a.json"
    md_a = tmp_path / "a.md"
    json_a.write_bytes(committed_json_bytes)
    md_a.write_bytes(committed_md_bytes)

    json_b = tmp_path / "b.json"
    md_b = tmp_path / "b.md"
    json_b.write_bytes(committed_json_bytes[:-1] + b"\x00")  # one byte changed
    md_b.write_bytes(committed_md_bytes)

    # The defect is really present before we trust the raise below (§6).
    assert json_a.read_bytes() != json_b.read_bytes()

    planted = session_artifacts.Regeneration(
        json_a=json_a,
        md_a=md_a,
        json_b=json_b,
        md_b=md_b,
        exit_codes=(0, 0),
        committed_json_before=committed_json_bytes,
        committed_md_before=committed_md_bytes,
    )

    with pytest.raises(AssertionError):
        module.test_ac18_artifacts_are_byte_reproducible_run_to_run(planted)


# =========================================================================== #
# Adversarial: fresh-vs-committed-representative
# =========================================================================== #


def test_adv_fresh_vs_committed_representative_still_fails_on_the_defect_it_guards(
    tmp_path,
):
    module = _load_module_from_path(
        _TESTS_DIR / "test_157_case_id_rename.py", "_test_170_case_id_rename"
    )
    import json as json_module

    import segfacet.traceability as traceability

    committed_json_bytes = traceability.JSON_PATH.read_bytes()
    committed_md_bytes = traceability.MD_PATH.read_bytes()

    payload = json_module.loads(committed_json_bytes.decode("utf-8"))
    assert isinstance(payload.get("note"), str) and payload["note"], (
        "expected a non-empty string 'note' leaf to mutate"
    )
    payload["note"] = payload["note"] + " (mutated by test_170)"

    json_a = tmp_path / "a.json"
    md_a = tmp_path / "a.md"
    json_a.write_text(json_module.dumps(payload, sort_keys=True), encoding="utf-8")
    md_a.write_bytes(committed_md_bytes)

    # The defect is really present before we trust the raise below (§6).
    assert json_a.read_bytes() != committed_json_bytes

    planted = session_artifacts.Regeneration(
        json_a=json_a,
        md_a=md_a,
        json_b=json_a,
        md_b=md_a,
        exit_codes=(0, 0),
        committed_json_before=committed_json_bytes,
        committed_md_before=committed_md_bytes,
    )

    with pytest.raises(AssertionError):
        module.test_ac17_traceability_matrix_artifacts_regenerate_identically(planted)


# =========================================================================== #
# Adversarial: untouched-representative
# =========================================================================== #


def test_adv_untouched_representative_still_fails_on_the_defect_it_guards(tmp_path):
    module = _load_module_from_path(
        _TESTS_DIR / "test_138_traceability_matrix.py", "_test_170_traceability_matrix"
    )
    import segfacet.traceability as traceability

    live_json_bytes = traceability.JSON_PATH.read_bytes()
    live_md_bytes = traceability.MD_PATH.read_bytes()

    json_a = tmp_path / "a.json"
    md_a = tmp_path / "a.md"
    json_a.write_bytes(live_json_bytes)
    md_a.write_bytes(live_md_bytes)

    planted_before = live_json_bytes + b"x"
    # The defect is really present before we trust the raise below (§6):
    # the planted "before" no longer equals what the live file reads now.
    assert planted_before != traceability.JSON_PATH.read_bytes()

    planted = session_artifacts.Regeneration(
        json_a=json_a,
        md_a=md_a,
        json_b=json_a,
        md_b=md_a,
        exit_codes=(0, 0),
        committed_json_before=planted_before,
        committed_md_before=live_md_bytes,
    )

    with pytest.raises(AssertionError):
        module.test_ac2_main_redirects_writes_and_leaves_committed_artifacts_unchanged(
            planted
        )


# =========================================================================== #
# Adversarial: ast-checker-negative-control
# =========================================================================== #


def test_adv_ast_checker_negative_control_flags_and_clears_correctly():
    # Flags a migrated-test regeneration call.
    regenerates = ast.parse("def test_x(): fm.main([])").body[0]
    assert _calls_a_regenerator_main(regenerates)

    # Flags a run_checks call nested in a class method.
    nested_run_checks = ast.parse(
        "class W:\n def run_checks(self):\n  return self._real.run_checks()\n"
    )
    assert _contains_run_checks_call(nested_run_checks)

    # Does not flag a catalogue.main(...) call -- the exempted receiver.
    catalogue_call = ast.parse("def test_x(): catalogue.main([])").body[0]
    assert not _calls_a_regenerator_main(catalogue_call)

    # Reports a function name that is not defined as absent.
    tree = ast.parse("def test_x(): pass")
    top_level = _top_level_functions(tree)
    assert "test_y" not in top_level
