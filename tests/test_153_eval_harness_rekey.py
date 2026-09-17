"""Tests for item 153 -- re-keying the Stage-18/29 per-mode eval harness
(``segfacet.eval.per_mode``, ``severity_ladder``, ``per_mode_cohort``, and the
comparison-report schema) off the pre-sign-off legacy ids 1-8 onto metric
names / operator names, with the item-150 specification's mode ids carried
in a nullable ``failure_mode`` field.

One test per AC, named ``test_acN_*``, per the item spec's Testing Strategy.
AC23, AC37, AC38 run the real harness/CLI. ``run_severity_harness()`` is
computed once at module scope and shared across AC23/AC24/AC30 (expensive).

Every home (metric->mode, ladder->mode) this file asserts is **recomputed
live** from ``segfacet.failure_modes.SPECIFICATION``/``CONDITIONS`` and
``tests/corpus/manifest.json`` via the item spec's rule (a) / rule (b) --
never a hard-coded corpus case id, and never a copy-pasted table -- so a
change to the specification or the corpus is caught here, not silently
assumed.

Note on the legacy-name token: this file must itself never contain the
literal string naming the retired legacy map (AC1/AC2 would otherwise flag
this very file), so every reference to it below is built by concatenation.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import jsonschema
import pytest

import segfacet.failure_modes as fm
from segfacet.io import FacetInputError
from segfacet.synth.corpus import load_manifest
from segfacet.synth.regression import loaded_seg_image
from segfacet.config import bundled_default_config
from segfacet.pipeline import extract_feature_record

import segfacet.eval.per_mode as per_mode
import segfacet.eval.severity_ladder as severity_ladder
import segfacet.eval.per_mode_cohort as per_mode_cohort
import segfacet.eval.report as report

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src" / "segfacet"
_TESTS_ROOT = _REPO_ROOT / "tests"

# Built by concatenation -- see module docstring.
_LEGACY_NAME_TOKEN = "LEGACY_STAGE18_MODE" + "_NAMES"

_METRIC_NAMES = (
    "unanchored_foreground_fraction",
    "min_dominant_component_fraction",
    "rogue_island_count",
    "mislabelled_volume_fraction",
    "missing_level_count",
    "fov_clipped_label_count",
    "out_of_order_label_count",
    "overlapping_voxel_count",
)
_OPERATORS = (
    "displace",
    "fragment",
    "inject_islands",
    "relabel_swap",
    "remove_level",
    "crop_at_border",
    "sequence_break",
    "force_overlap",
)
_RECORDED_REHOMING = {
    "unanchored_foreground_fraction": 1,
    "min_dominant_component_fraction": 1,
    "rogue_island_count": 4,
    "mislabelled_volume_fraction": 8,
    "missing_level_count": 6,
    "fov_clipped_label_count": None,
    "out_of_order_label_count": 9,
    "overlapping_voxel_count": 15,
}


# =========================================================================== #
# Rule (a) / rule (b) derivation -- recomputed live, never hard-coded
# =========================================================================== #


def _manifest_case_id_for_perturbation(perturbation: str) -> str:
    cases = load_manifest()["cases"]
    matches = [c["case_id"] for c in cases if c.get("perturbation") == perturbation]
    assert len(matches) == 1, (perturbation, matches)
    return matches[0]


def _rule_a_home(metric_name: str, specification) -> Optional[int]:
    """The mode *m* whose ``candidate_features`` cites exactly
    ``eval.per_mode.<metric_name>``, or ``None`` if no mode cites it.

    Raises ``AssertionError`` (a report, not a silent resolution) if more
    than one mode cites it.
    """
    path = f"eval.per_mode.{metric_name}"
    homes = [
        m
        for m, mode in specification.items()
        if any(cf.path == path for cf in mode.candidate_features)
    ]
    assert len(homes) <= 1, f"{metric_name} cited by >1 mode: {homes}"
    return homes[0] if homes else None


def _rule_b_home(operator: str, specification, conditions):
    """``(mode_id_or_None, condition_id_or_None)`` for *operator*'s manifest
    case, per rule (b)."""
    case_id = _manifest_case_id_for_perturbation(operator)
    mode_hits = [
        m
        for m, mode in specification.items()
        if any(cc.case_id == case_id for cc in mode.corpus_cases)
    ]
    condition_hits = [
        c
        for c, cond in conditions.items()
        if any(cc.case_id == case_id for cc in cond.corpus_cases)
    ]
    assert len(mode_hits) <= 1, f"{operator} case {case_id!r} owned by >1 mode: {mode_hits}"
    assert len(condition_hits) <= 1, (
        f"{operator} case {case_id!r} owned by >1 condition: {condition_hits}"
    )
    if mode_hits:
        return mode_hits[0], None
    if condition_hits:
        return None, condition_hits[0]
    return None, None


def _metric_to_operator() -> dict:
    """``{designated_metric: operator}`` for the eight primary ladders,
    read live from ``SEVERITY_LADDERS`` (AC18 guarantees this covers every
    registry key exactly once)."""
    return {
        ladder.designated_metric: ladder.operator
        for ladder in severity_ladder.SEVERITY_LADDERS.values()
    }


def _derived_home(metric_name: str) -> Optional[int]:
    """The home rule (a), else rule (b), computes live for *metric_name*."""
    a_home = _rule_a_home(metric_name, fm.SPECIFICATION)
    if a_home is not None:
        return a_home
    operator = _metric_to_operator()[metric_name]
    mode_home, _condition = _rule_b_home(operator, fm.SPECIFICATION, fm.CONDITIONS)
    return mode_home


# =========================================================================== #
# Legacy map retired
# =========================================================================== #


def test_ac1_legacy_map_is_gone():
    assert hasattr(per_mode, _LEGACY_NAME_TOKEN) is False


def _files_containing_token(root: Path, token: str) -> list:
    hits = []
    for pattern in ("*.py", "*.json"):
        for path in sorted(root.rglob(pattern)):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if token in text:
                hits.append(path)
    return hits


def test_ac2_no_source_or_test_names_the_legacy_map():
    hits = _files_containing_token(_SRC_ROOT, _LEGACY_NAME_TOKEN)
    hits += _files_containing_token(_TESTS_ROOT, _LEGACY_NAME_TOKEN)
    assert hits == [], [p.as_posix() for p in hits]


def test_adv_ac2_planted_file_is_flagged(tmp_path):
    planted = tmp_path / "planted_offender.py"
    planted.write_text(f'X = "{_LEGACY_NAME_TOKEN}"\n', encoding="utf-8")
    hits = _files_containing_token(tmp_path, _LEGACY_NAME_TOKEN)
    assert hits == [planted]


def _string_literals(path: Path) -> set:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def test_ac3_no_hand_typed_mode_names_in_the_harness():
    needles = set()
    for mode in fm.SPECIFICATION.values():
        needles.add(mode.name)
        needles.add(mode.short_name)

    offenders = set()
    for rel in (
        "eval/per_mode.py",
        "eval/severity_ladder.py",
        "eval/per_mode_cohort.py",
    ):
        path = _SRC_ROOT / rel
        if _string_literals(path) & needles:
            offenders.add(rel)
    assert offenders == set(), offenders


def test_ac4_no_section_6_numbering_wording():
    offenders = []
    for rel in (
        "eval/per_mode.py",
        "eval/severity_ladder.py",
        "eval/per_mode_cohort.py",
        "eval/__init__.py",
        "eval/per_mode_comparison_schema_v0.json",
        "eval/eval_report_schema_v0.json",
    ):
        text = (_SRC_ROOT / rel).read_text(encoding="utf-8")
        if any(needle in text for needle in ("§6", "Section 6", "Section-6")):
            offenders.append(rel)
    assert offenders == [], offenders


# =========================================================================== #
# AC5-AC13: the metric registry
# =========================================================================== #


def test_ac5_homes_are_derived_from_the_specification():
    for metric_name, spec in per_mode.PER_MODE_METRIC_SPECS.items():
        assert spec.failure_mode == _derived_home(metric_name), metric_name


def test_adv_ac5_wrong_home_is_detected():
    """A monkeypatched registry entry with a wrong home disagrees with the
    live derivation (a false 'homes are derived' claim must fail, not pass
    silently)."""
    real = per_mode.PER_MODE_METRIC_SPECS["unanchored_foreground_fraction"]
    wrong = dataclasses.replace(real, failure_mode=99)
    assert wrong.failure_mode != _derived_home("unanchored_foreground_fraction")


def test_adv_ac5_ambiguous_citation_is_not_derivable():
    path = "eval.per_mode.unanchored_foreground_fraction"
    fake_specification = {
        1: SimpleNamespace(candidate_features=[SimpleNamespace(path=path)]),
        2: SimpleNamespace(candidate_features=[SimpleNamespace(path=path)]),
    }
    with pytest.raises(AssertionError):
        _rule_a_home("unanchored_foreground_fraction", fake_specification)


def test_ac6_the_recorded_rehoming_table_holds():
    actual = {name: spec.failure_mode for name, spec in per_mode.PER_MODE_METRIC_SPECS.items()}
    assert actual == _RECORDED_REHOMING


def test_ac7_the_registry_is_keyed_by_metric_name():
    assert list(per_mode.PER_MODE_METRIC_SPECS) == list(_METRIC_NAMES)


@pytest.mark.parametrize("key", _METRIC_NAMES)
def test_ac8_each_key_matches_its_entry(key):
    assert per_mode.PER_MODE_METRIC_SPECS[key].metric_name == key


def test_ac9_mode_names_come_from_the_specification():
    for spec in per_mode.PER_MODE_METRIC_SPECS.values():
        if spec.failure_mode is not None:
            assert spec.failure_mode_name == fm.SPECIFICATION[spec.failure_mode].name
        else:
            assert spec.failure_mode_name is None


def test_ac10_the_disposition_follows_the_home():
    for spec in per_mode.PER_MODE_METRIC_SPECS.values():
        if spec.failure_mode is not None:
            assert spec.mode_disposition == "measures-mode"
        else:
            assert spec.mode_disposition == "measures-no-mode"


def test_ac11_the_condition_is_recorded():
    case_id = _manifest_case_id_for_perturbation("crop_at_border")
    expected = [
        c for c, cond in fm.CONDITIONS.items() if any(cc.case_id == case_id for cc in cond.corpus_cases)
    ]
    assert len(expected) == 1
    assert expected[0] == "fov_truncation"
    assert per_mode.PER_MODE_METRIC_SPECS["fov_clipped_label_count"].condition == expected[0]


def test_ac12_only_that_entry_has_a_condition():
    for name, spec in per_mode.PER_MODE_METRIC_SPECS.items():
        if name == "fov_clipped_label_count":
            continue
        assert spec.condition is None, name


def _assert_citation_resolves(mode_id, cf, registry) -> None:
    assert cf.path.startswith("eval.per_mode.")
    name = cf.path[len("eval.per_mode.") :]
    assert name in registry, name
    assert registry[name].failure_mode == mode_id


def test_ac13_specification_citations_resolve_to_the_registry():
    for mode_id, mode in fm.SPECIFICATION.items():
        for cf in mode.candidate_features:
            if cf.path.startswith("eval.per_mode."):
                _assert_citation_resolves(mode_id, cf, per_mode.PER_MODE_METRIC_SPECS)


def test_adv_ac13_unregistered_metric_path_is_reported():
    fake_cf = SimpleNamespace(path="eval.per_mode.does_not_exist_anywhere")
    with pytest.raises(AssertionError):
        _assert_citation_resolves(1, fake_cf, per_mode.PER_MODE_METRIC_SPECS)


# =========================================================================== #
# AC14-AC16: emitted per-case records
# =========================================================================== #

_MANIFEST_CASES = {c["case_id"]: c for c in load_manifest()["cases"]}
_CONFIG = bundled_default_config()
_CLEAN_RECORD = extract_feature_record(
    loaded_seg_image(_MANIFEST_CASES["clean_control"]), _CONFIG
)


def test_ac14_the_per_case_record_carries_the_disposition():
    import numpy as np

    gt = np.asanyarray(loaded_seg_image(_MANIFEST_CASES["clean_control"]).dataobj)
    result = per_mode.compute_per_mode_metrics(_CLEAN_RECORD, candidate=gt, gt=gt)
    for entry in result.to_dict()["per_mode"]:
        registry_entry = per_mode.PER_MODE_METRIC_SPECS[entry["metric_name"]]
        assert entry["failure_mode"] == registry_entry.failure_mode
        assert entry["failure_mode_name"] == registry_entry.failure_mode_name
        assert entry["mode_disposition"] == registry_entry.mode_disposition
        assert entry["condition"] == registry_entry.condition


def test_ac15_lookup_by_metric_name():
    import numpy as np

    gt = np.asanyarray(loaded_seg_image(_MANIFEST_CASES["clean_control"]).dataobj)
    result = per_mode.compute_per_mode_metrics(_CLEAN_RECORD, candidate=gt, gt=gt)
    for name in _METRIC_NAMES:
        assert result.by_metric(name).metric_name == name
    with pytest.raises(KeyError):
        result.by_metric("does_not_exist")


def test_ac16_degradation_details_name_no_legacy_id():
    import re

    result = per_mode.compute_per_mode_metrics({}, candidate=None, gt=None)
    checked = 0
    for entry in result.per_mode:
        if entry.value is None:
            checked += 1
            assert entry.detail, entry.metric_name
            assert entry.metric_name in entry.detail, entry.metric_name
            assert re.search(r"\bmode [0-9]", entry.detail) is None, entry.detail
    assert checked > 0


# =========================================================================== #
# AC17-AC25: ladders
# =========================================================================== #


def test_ac17_ladders_are_keyed_by_operator():
    assert set(severity_ladder.SEVERITY_LADDERS) == set(_OPERATORS)
    for key, spec in severity_ladder.SEVERITY_LADDERS.items():
        assert spec.operator == key


def test_ac18_designated_metrics_cover_the_registry():
    designated = [
        spec.designated_metric for spec in severity_ladder.SEVERITY_LADDERS.values()
    ]
    assert len(designated) == len(set(designated))
    assert set(designated) == set(per_mode.PER_MODE_METRIC_SPECS)


def test_ac19_ladder_homes_are_derived_from_the_specification():
    all_ladders = list(severity_ladder.SEVERITY_LADDERS.values()) + list(
        severity_ladder.SUPPLEMENTARY_LADDERS
    )
    for spec in all_ladders:
        mode_home, condition_home = _rule_b_home(spec.operator, fm.SPECIFICATION, fm.CONDITIONS)
        assert spec.failure_mode == mode_home, spec.operator
        assert spec.condition == condition_home, spec.operator

    # Measured 2026-09-16 (item spec Description/AC19).
    assert severity_ladder.SEVERITY_LADDERS["relabel_swap"].failure_mode == 9
    assert severity_ladder.SEVERITY_LADDERS["crop_at_border"].failure_mode is None
    assert severity_ladder.SEVERITY_LADDERS["crop_at_border"].condition == "fov_truncation"
    fuse = next(s for s in severity_ladder.SUPPLEMENTARY_LADDERS if s.operator == "fuse")
    assert fuse.failure_mode == 2


def test_ac20_margins_are_keyed_by_operator():
    assert set(severity_ladder.RECORDED_MARGINS) == set(severity_ladder.SEVERITY_LADDERS)


def test_ac21_couplings_name_a_ladder_and_a_foreign_metric():
    for coupling in severity_ladder.KNOWN_CROSS_MODE_COUPLINGS:
        assert coupling.ladder_operator in severity_ladder.SEVERITY_LADDERS
        assert coupling.foreign_metric in per_mode.PER_MODE_METRIC_SPECS
        designated = severity_ladder.SEVERITY_LADDERS[coupling.ladder_operator].designated_metric
        assert coupling.foreign_metric != designated


def test_ac22_the_degenerate_set_follows_the_severity_kind():
    expected = {
        k for k, s in severity_ladder.SEVERITY_LADDERS.items() if s.severity_kind == "degenerate"
    }
    assert severity_ladder.DEGENERATE_LADDERS == expected


# --------------------------------------------------------------------------- #
# Shared, module-scoped harness run (AC23/AC24/AC30 -- expensive)
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def harness_result():
    return severity_ladder.run_severity_harness()


@pytest.fixture(scope="module")
def harness_verdict(harness_result):
    return severity_ladder.score_harness(harness_result)


def test_ac23_the_rekeyed_ratchet_still_passes(harness_verdict):
    assert harness_verdict.passed is True


def test_ac24_verdict_responses_are_keyed_by_metric(harness_verdict):
    registry_keys = set(per_mode.PER_MODE_METRIC_SPECS)
    assert set(harness_verdict.per_ladder) == set(severity_ladder.SEVERITY_LADDERS)
    for verdict in harness_verdict.per_ladder.values():
        assert set(verdict.responses) == registry_keys


def test_ac25_unknown_assignments_are_rejected(harness_result):
    valid = next(iter(per_mode.PER_MODE_METRIC_SPECS))
    op = next(iter(severity_ladder.SEVERITY_LADDERS))
    for bad_value in (1, "1", "does_not_exist"):
        with pytest.raises(FacetInputError):
            severity_ladder.score_harness(harness_result, assignment={op: bad_value})
    # Non-vacuity: a genuinely valid assignment does not raise.
    severity_ladder.score_harness(harness_result, assignment={op: valid})


# =========================================================================== #
# AC26-AC34: cohort summary, comparison, schema
# =========================================================================== #


def _fake_cohort(per_mode_metrics_list):
    cases = [
        SimpleNamespace(case_id=f"case{i}", per_mode=pm)
        for i, pm in enumerate(per_mode_metrics_list)
    ]
    return SimpleNamespace(cases=cases)


def _computed_metrics():
    import numpy as np

    gt = np.asanyarray(loaded_seg_image(_MANIFEST_CASES["clean_control"]).dataobj)
    return per_mode.compute_per_mode_metrics(_CLEAN_RECORD, candidate=gt, gt=gt)


def test_ac26_cohort_aggregates_follow_the_registry():
    cohort = _fake_cohort([_computed_metrics()])
    summary = per_mode_cohort.summarise_run_per_mode(cohort, run_id="r")
    assert [a.metric_name for a in summary.per_mode] == list(per_mode.PER_MODE_METRIC_SPECS)
    for agg in summary.per_mode:
        registry_entry = per_mode.PER_MODE_METRIC_SPECS[agg.metric_name]
        assert agg.failure_mode == registry_entry.failure_mode
        assert agg.mode_disposition == registry_entry.mode_disposition


def test_ac27_scale_specs_are_keyed_by_metric():
    assert set(per_mode_cohort.MODE_SCALE_SPECS) == set(per_mode.PER_MODE_METRIC_SPECS)


def _build_summary(run_id: str, means: dict):
    aggs = []
    for name, spec in per_mode.PER_MODE_METRIC_SPECS.items():
        mean = means.get(name, spec.baseline)
        aggs.append(
            per_mode_cohort.ModeAggregate(
                failure_mode=spec.failure_mode,
                failure_mode_name=spec.failure_mode_name,
                metric_name=spec.metric_name,
                direction=spec.direction,
                baseline=spec.baseline,
                mode_disposition=spec.mode_disposition,
                condition=spec.condition,
                n_cases=1,
                n_with_value=1,
                mean=mean,
                minimum=mean,
                maximum=mean,
                total=mean,
                detection_rate=None,
                n_detection_cases=0,
            )
        )
    return per_mode_cohort.RunPerModeSummary(
        run_id=run_id,
        case_ids=("c1",),
        n_cases=1,
        per_mode=tuple(aggs),
        mean_dice=None,
        volume_weighted_dice=None,
    )


def _comparisons():
    """The comparisons this test module produces (AC28/AC30's "every
    RunComparison produced by compare_runs in the test module")."""
    run_a = _build_summary("a", {})
    run_b = _build_summary(
        "b",
        {
            "unanchored_foreground_fraction": 0.5,
            "fov_clipped_label_count": 3.0,
        },
    )
    return [per_mode_cohort.compare_runs(run_a, run_b)]


def test_ac28_the_attributed_mode_is_looked_up_not_stored_separately():
    for comparison in _comparisons():
        if comparison.attributed_metric_name is None:
            assert comparison.attributed_mode is None
        else:
            expected = per_mode.PER_MODE_METRIC_SPECS[comparison.attributed_metric_name].failure_mode
            assert comparison.attributed_mode == expected


def test_ac29_exclusions_are_named_by_metric():
    for comparison in _comparisons():
        d = comparison.to_dict()
        assert "excluded_metric_names" in d
        assert "excluded_modes" not in d
        assert d["excluded_metric_names"] == list(comparison.excluded_metric_names)
        assert d["excluded_metric_names"] == [
            name for name in per_mode.PER_MODE_METRIC_SPECS if name in d["excluded_metric_names"]
        ]


def _bad_mode_values(obj, keys=("failure_mode", "attributed_mode")):
    bad = []

    def _walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in keys and v is not None and v not in fm.SPECIFICATION:
                    bad.append((k, v))
                _walk(v)
        elif isinstance(o, (list, tuple)):
            for item in o:
                _walk(item)

    _walk(obj)
    return bad


def test_ac30_every_emitted_mode_id_is_valid(harness_result, harness_verdict):
    metrics_dict = _computed_metrics().to_dict()
    summary = per_mode_cohort.summarise_run_per_mode(_fake_cohort([_computed_metrics()]), run_id="r")
    comparisons = [c.to_dict() for c in _comparisons()]

    for payload in (
        metrics_dict,
        harness_result.to_dict(),
        harness_verdict.to_dict(),
        summary.to_dict(),
        *comparisons,
    ):
        assert _bad_mode_values(payload) == []


def test_adv_ac30_walker_flags_a_planted_bad_value():
    planted = {"a": {"b": {"failure_mode": 99}}}
    bad = _bad_mode_values(planted)
    assert bad == [("failure_mode", 99)]


def test_ac31_pre_rekey_blocks_are_rejected():
    pre_item_block = {
        "run_id": "old",
        "case_ids": ["c1"],
        "n_cases": 1,
        "mean_dice": None,
        "volume_weighted_dice": None,
        "per_mode": [
            {
                "failure_mode": m,
                "failure_mode_name": "x",
                "metric_name": name,
                "direction": "increases",
                "baseline": 0.0,
                "n_cases": 1,
                "n_with_value": 1,
                "mean": 0.0,
                "minimum": 0.0,
                "maximum": 0.0,
                "total": 0.0,
                "detection_rate": None,
                "n_detection_cases": 0,
                # deliberately no "mode_disposition" -- the pre-item shape
            }
            for m, name in zip(range(1, 9), _METRIC_NAMES)
        ],
    }
    with pytest.raises(FacetInputError):
        per_mode_cohort.RunPerModeSummary.from_dict(pre_item_block)


def test_adv_ac31_compare_runs_cli_exits_1_no_traceback_on_pre_rekey_report(tmp_path, capsys):
    from segfacet import cli

    pre_item_report = {
        "schema_version": "0.1",
        "provenance": {},
        "metrics": {},
        "per_mode_magnitude": {
            "run_id": "old",
            "case_ids": ["c1"],
            "n_cases": 1,
            "mean_dice": None,
            "volume_weighted_dice": None,
            "per_mode": [
                {
                    "failure_mode": m,
                    "failure_mode_name": "x",
                    "metric_name": name,
                    "direction": "increases",
                    "baseline": 0.0,
                    "n_cases": 1,
                    "n_with_value": 1,
                    "mean": 0.0,
                    "minimum": 0.0,
                    "maximum": 0.0,
                    "total": 0.0,
                    "detection_rate": None,
                    "n_detection_cases": 0,
                }
                for m, name in zip(range(1, 9), _METRIC_NAMES)
            ],
        },
    }
    run_a = tmp_path / "a.json"
    run_b = tmp_path / "b.json"
    run_a.write_text(json.dumps(pre_item_report), encoding="utf-8")
    run_b.write_text(json.dumps(pre_item_report), encoding="utf-8")
    out_dir = tmp_path / "out"

    code = cli.main(
        [
            "compare-runs",
            "--run-a",
            str(run_a),
            "--run-b",
            str(run_b),
            "--out",
            str(out_dir),
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert not out_dir.exists() or not any(out_dir.iterdir())


def _comparison_schema() -> dict:
    return json.loads(
        (_SRC_ROOT / "eval" / "per_mode_comparison_schema_v0.json").read_text(encoding="utf-8")
    )


def test_ac32_comparison_reports_validate():
    comparison = _comparisons()[0]
    provenance = SimpleNamespace(to_dict=lambda: {})
    built = report.build_run_comparison_report(comparison, provenance, provenance)
    jsonschema.validate(built, _comparison_schema())


def test_ac33_the_comparison_schema_declares_metric_name_exclusions():
    schema = _comparison_schema()
    required = schema["definitions"]["comparison"]["required"]
    assert "excluded_metric_names" in required
    assert "excluded_modes" not in required


def test_ac34_the_comparison_schema_version_is_bumped():
    schema = _comparison_schema()
    assert schema["properties"]["schema_version"]["const"] == "0.2"
    assert report.PER_MODE_COMPARISON_SCHEMA_VERSION == "0.2"


def test_adv_ac32_excluded_modes_shape_fails_validation():
    comparison = _comparisons()[0]
    provenance = SimpleNamespace(to_dict=lambda: {})
    built = report.build_run_comparison_report(comparison, provenance, provenance)
    built["comparison"].pop("excluded_metric_names", None)
    built["comparison"]["excluded_modes"] = [3]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(built, _comparison_schema())


# =========================================================================== #
# AC35-AC36: human-readable text
# =========================================================================== #


def test_ac35_no_mode_metrics_are_named_as_such_in_comparison_text():
    comparison = _comparisons()[0]
    text = report.render_run_comparison(comparison)
    assert "no failure mode (fov_truncation condition) (fov_clipped_label_count)" in text


def test_ac36_the_evaluation_text_names_each_rehomed_mode():
    summary = _build_summary("r", {})
    metrics = SimpleNamespace(
        false_positive_rate=None,
        sensitivity=None,
        specificity=None,
        per_mode=(),
        dice_vs_flag=SimpleNamespace(method="pearson", coefficient=None, n=0),
        feature_divergence_vs_flag=SimpleNamespace(method="pearson", coefficient=None, n=0),
    )
    provenance = SimpleNamespace(
        cohort_id="c",
        cohort_size=1,
        config_version="v",
        build_date="2026-09-16",
    )
    text = report.render_evaluation_report(metrics, provenance, per_mode_summary=summary)
    for mode_id in (1, 4, 6, 8, 9, 15):
        assert fm.SPECIFICATION[mode_id].name in text, mode_id


# =========================================================================== #
# AC37-AC38: end to end
# =========================================================================== #


def test_ac37_evaluate_per_mode_still_runs(tmp_path):
    import test_101_compare_runs_cli as t101cli

    manifest_path = t101cli._write_manifest(tmp_path, t101cli._COHORT_CASES)
    out_dir = tmp_path / "out"
    code = t101cli._run_evaluate(manifest_path, out_dir, per_mode=True)
    assert code == 0

    report_json = json.loads((out_dir / "eval_report.json").read_text(encoding="utf-8"))
    metric_names = [
        e["metric_name"] for e in report_json["per_mode_magnitude"]["per_mode"]
    ]
    assert metric_names == list(per_mode.PER_MODE_METRIC_SPECS)


def test_ac38_compare_runs_still_runs(tmp_path):
    import test_101_compare_runs_cli as t101cli

    manifest_path = t101cli._write_manifest(tmp_path, t101cli._COHORT_CASES, name="cohort_a.json")
    other_manifest_path = t101cli._write_manifest(
        tmp_path, t101cli._COHORT_CASES, name="cohort_b.json"
    )
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    assert t101cli._run_evaluate(manifest_path, out_a, per_mode=True, run_id="run_a") == 0
    assert t101cli._run_evaluate(other_manifest_path, out_b, per_mode=True, run_id="run_b") == 0

    from segfacet import cli

    out_cmp = tmp_path / "out_cmp"
    code = cli.main(
        [
            "compare-runs",
            "--run-a",
            str(out_a / "eval_report.json"),
            "--run-b",
            str(out_b / "eval_report.json"),
            "--out",
            str(out_cmp),
        ]
    )
    assert code == 0
    written = json.loads((out_cmp / "per_mode_comparison.json").read_text(encoding="utf-8"))
    jsonschema.validate(written, _comparison_schema())


# =========================================================================== #
# Determinism
# =========================================================================== #


def test_determinism_registry_iteration_order_is_stable():
    import importlib

    import segfacet.eval.per_mode as pm1
    import segfacet.eval.severity_ladder as sl1

    pm2 = importlib.reload(pm1)
    sl2 = importlib.reload(sl1)
    try:
        assert list(pm2.PER_MODE_METRIC_SPECS) == list(per_mode.PER_MODE_METRIC_SPECS)
        assert list(sl2.SEVERITY_LADDERS) == list(severity_ladder.SEVERITY_LADDERS)
        assert list(sl2.RECORDED_MARGINS) == list(severity_ladder.RECORDED_MARGINS)
    finally:
        importlib.reload(pm1)
        importlib.reload(sl1)
