"""Tests for item 154 -- re-measuring the severity-ladder harness's carried-
over ratchet constants, settling item 153's four open questions, and
correcting two documentation claims (``segfacet.eval.severity_ladder``,
``segfacet.feature_docs``, ``segfacet.failure_modes``).

Covers Acceptance Criteria AC1-AC22:

- AC1:  every ``KNOWN_CROSS_MODE_COUPLINGS`` entry carries a ``provenance``.
- AC2:  every ``RECORDED_MARGINS`` key has a matching provenance.
- AC3:  every provenance names the ``"geometric"`` corpus.
- AC4:  every provenance's ``base_params`` matches the harness base.
- AC5:  the harness base matches the geometric corpus's own default base.
- AC6:  every provenance is dated on or after 2026-09-16 and not in the
        future.
- AC7:  the re-measured ratchet passes.
- AC8:  the coupling set is exactly what is measured at the threshold.
- AC9:  each coupling's ``recorded_response`` is a fresh, tight-tolerance
        transcription (rounded up).
- AC10: each ``RECORDED_MARGINS`` value is a fresh, tight-tolerance
        transcription (rounded down).
- AC11: no coupling names its own ladder's designated metric.
- AC12: excluding same-home foreign metrics from the margin computation
        changes no measured margin on this base (A2's finding).
- AC13: exactly one ``MODE_LADDER_DISPOSITIONS`` entry, for mode 1.
- AC14: its ``ladders`` tuple is derived from the per-mode metric homes.
- AC15: its disposition is ``"re-derived"``, a member of
        ``MODE_LADDER_DISPOSITION_VALUES``.
- AC16: the false ``rank(v) == v - 1`` literal is gone from ``src/``.
- AC17: the corrected rank premise's two-descent finding is measured, not
        asserted by fiat.
- AC18: the "structural" wording is withdrawn from the ``sequence_break``
        ladder's rationale and the module docstring.
- AC19: mode 1's re-anchor leaves at least one anchor path.
- AC20: every one of mode 1's anchor paths is consumed as ``"signal"`` by at
        least one of mode 1's intended rules.
- AC21: mode 1's ``"stage18-metric-anchor"``-role candidate features exactly
        match ``MODE_ANCHOR_PATHS[1]``.
- AC22: importing ``severity_ladder``/``per_mode``/``feature_docs`` in a
        fresh subprocess opens nothing under a ``tests`` path component.

Adversarial / edge-case scenarios (mirrors the item spec's Testing
Strategy):

- AC1:  building ``CrossModeCoupling`` with no ``provenance`` raises
        ``TypeError``.
- AC6:  a date before the carry-over cutoff, and a non-ISO date string, both
        fail the check.
- AC9/AC10: a coupling/margin recorded outside the tight tolerance, in
        either direction, fails the check -- proving it is not vacuous.
- AC12: a synthetic responses table where a same-home metric carries the
        largest foreign response makes the two margin computations differ.
- AC14: re-homing a metric to mode 1 (monkeypatched) changes the derived
        ladder tuple.
- AC16: a planted file containing the needle is flagged by the same
        scanner.
- AC17: the independent descent counter returns 0 for a strictly-increasing
        sequence and 1 for a sequence with one out-of-order label.
- AC20: the same check applied to the *dropped* anchor path
        (``stage3.per_label_offsets[].offset_mm``) fails: its only
        consumer, ``mislabel``, declares it ``"bookkeeping"``, and
        ``mislabel`` is not one of mode 1's intended rules.
- AC21: a ``ModeSpec`` copy whose anchor-role candidate feature is not in
        ``MODE_ANCHOR_PATHS[1]`` raises ``ValueError``.
- AC22: a positive-control child that opens a path under ``tests/`` after
        installing the audit hook is reported by the same scanner.

Cost control: the harness (AC7-AC12) is built once in a module-scoped
fixture. ``segfacet.eval.severity_ladder``'s new names (``MeasurementProvenance``,
``MODE_LADDER_DISPOSITIONS``, ...) are read through a lazily-imported ``sl``
fixture (mirrors ``tests/test_100_severity_ladder.py``'s ``_sl()``/``harness``
convention) so this module still collects before the builder step lands them.
"""

from __future__ import annotations

import dataclasses
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

import segfacet.heuristics.rule as rule_mod  # noqa: F401 -- import order registers every concrete rule
import segfacet.synth  # noqa: F401 -- registers every perturbation operator
import segfacet.failure_modes as failure_modes
import segfacet.feature_docs as feature_docs
from segfacet.config import bundled_default_config
from segfacet.eval.per_mode import PER_MODE_METRIC_SPECS, compute_per_mode_metrics
from segfacet.heuristics.rule import iter_rule_declarations
from segfacet.labels import CANONICAL_ORDER, DEFAULT_LABEL_MAP
from segfacet.pipeline import extract_feature_record
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.perturbation import get_perturbation
from run_process import run_utf8

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src" / "segfacet"


def _sl():
    """Local import of ``segfacet.eval.severity_ladder`` -- kept out of the
    module-level import block (mirrors ``tests/test_100_severity_ladder.py``'s
    ``_sl()``) so this file still collects before item 154's builder step
    lands ``MeasurementProvenance``/``MODE_LADDER_DISPOSITIONS``/etc."""
    import segfacet.eval.severity_ladder as severity_ladder

    return severity_ladder


@pytest.fixture(scope="module")
def sl():
    return _sl()


@pytest.fixture(scope="module")
def harness_run(sl):
    harness = sl.run_severity_harness()
    verdict = sl.score_harness(harness)
    return harness, verdict


@pytest.fixture
def all_provenances(sl):
    """Every provenance record, per the item spec's Acceptance Criteria
    preamble: each ``KNOWN_CROSS_MODE_COUPLINGS`` entry's ``provenance``,
    each ``RECORDED_MARGIN_PROVENANCE`` value, and each
    ``MODE_LADDER_DISPOSITIONS`` value's ``provenance``."""
    provenances = [c.provenance for c in sl.KNOWN_CROSS_MODE_COUPLINGS]
    provenances += list(sl.RECORDED_MARGIN_PROVENANCE.values())
    provenances += [d.provenance for d in sl.MODE_LADDER_DISPOSITIONS.values()]
    assert provenances, "expected at least one provenance record to check"
    return provenances


def _normalise_base_params(params):
    """Coerce every sequence value to a ``tuple`` so a list vs. tuple
    representation of the same base params compares equal."""
    return {
        key: (tuple(value) if isinstance(value, (list, tuple)) else value)
        for key, value in dict(params).items()
    }


def _rank(label_value: int) -> int:
    return CANONICAL_ORDER.index(DEFAULT_LABEL_MAP[label_value])


def _count_descents(values):
    """Count entries whose canonical rank falls below the running maximum
    rank seen so far, in ascending-label order -- the independent
    measure AC17 compares the production ``out_of_order_label_count``
    against."""
    count = 0
    running_max = None
    for value in values:
        rank = _rank(value)
        if running_max is not None and rank < running_max:
            count += 1
        else:
            running_max = rank
    return count


# =========================================================================== #
# Provenance (AC1-AC6)
# =========================================================================== #


def test_ac1_couplings_carry_provenance(sl):
    for coupling in sl.KNOWN_CROSS_MODE_COUPLINGS:
        assert isinstance(coupling.provenance, sl.MeasurementProvenance), coupling


def test_adv_ac1_coupling_without_provenance_raises_typeerror(sl):
    with pytest.raises(TypeError):
        sl.CrossModeCoupling(
            ladder_operator="displace",
            foreign_metric="min_dominant_component_fraction",
            recorded_response=1.0,
            cause="adversarial: no provenance supplied",
        )


def test_ac2_every_margin_has_provenance(sl):
    assert set(sl.RECORDED_MARGIN_PROVENANCE) == set(sl.RECORDED_MARGINS)
    for value in sl.RECORDED_MARGIN_PROVENANCE.values():
        assert isinstance(value, sl.MeasurementProvenance), value


def test_ac3_every_provenance_names_the_geometric_corpus(all_provenances):
    for provenance in all_provenances:
        assert provenance.corpus == "geometric", provenance


def test_ac4_every_provenance_base_params_is_the_harness_base(all_provenances, sl):
    expected = _normalise_base_params(sl._BASE_PARAMS)
    for provenance in all_provenances:
        assert _normalise_base_params(provenance.base_params) == expected, provenance


def test_ac5_harness_base_is_the_geometric_corpus_default(sl):
    from segfacet.synth.corpus import _DEFAULT_BASE_PARAMS

    assert _normalise_base_params(sl._BASE_PARAMS) == _normalise_base_params(
        _DEFAULT_BASE_PARAMS
    )


def test_ac6_every_measurement_dated_after_the_carry_over(all_provenances):
    lower_bound = date(2026, 9, 16)
    today = date.today()
    for provenance in all_provenances:
        measured = date.fromisoformat(provenance.measured_on)
        assert lower_bound <= measured <= today, provenance


def test_adv_ac6_dates_outside_the_window_fail_the_check():
    lower_bound = date(2026, 9, 16)
    too_early = date.fromisoformat("2026-09-15")
    assert not (lower_bound <= too_early)
    with pytest.raises(ValueError):
        date.fromisoformat("16/09/2026")


# =========================================================================== #
# Re-measured values (AC7-AC11)
# =========================================================================== #


def test_ac7_the_re_measured_ratchet_passes(harness_run):
    _, verdict = harness_run
    assert verdict.passed is True


def test_ac8_coupling_set_is_what_is_measured(harness_run, sl):
    _, verdict = harness_run
    measured_pairs = set()
    for operator, ladder_verdict in verdict.per_ladder.items():
        designated = sl.SEVERITY_LADDERS[operator].designated_metric
        for metric, response in ladder_verdict.responses.items():
            if metric != designated and response >= sl.COUPLING_THRESHOLD:
                measured_pairs.add((operator, metric))
    recorded_pairs = {
        (c.ladder_operator, c.foreign_metric) for c in sl.KNOWN_CROSS_MODE_COUPLINGS
    }
    assert recorded_pairs == measured_pairs


def test_ac9_each_coupling_value_is_a_fresh_transcription(harness_run, sl):
    _, verdict = harness_run
    for coupling in sl.KNOWN_CROSS_MODE_COUPLINGS:
        measured = verdict.per_ladder[coupling.ladder_operator].responses[
            coupling.foreign_metric
        ]
        assert measured <= coupling.recorded_response, coupling
        gap = coupling.recorded_response - measured
        tolerance = 10 ** (math.floor(math.log10(measured)) - 3)
        assert gap < tolerance, (coupling, measured, gap, tolerance)


def test_adv_ac9_out_of_tolerance_couplings_fail_the_check(harness_run, sl):
    _, verdict = harness_run
    coupling = sl.KNOWN_CROSS_MODE_COUPLINGS[0]
    measured = verdict.per_ladder[coupling.ladder_operator].responses[
        coupling.foreign_metric
    ]
    tolerance = 10 ** (math.floor(math.log10(measured)) - 3)

    too_high = dataclasses.replace(coupling, recorded_response=measured + tolerance * 2)
    assert not (too_high.recorded_response - measured < tolerance)

    too_low = dataclasses.replace(coupling, recorded_response=measured - tolerance)
    assert not (measured <= too_low.recorded_response)


def test_ac10_each_margin_is_a_fresh_transcription(harness_run, sl):
    _, verdict = harness_run
    for operator in sl.SEVERITY_LADDERS:
        measured = verdict.per_ladder[operator].margin
        recorded = sl.RECORDED_MARGINS[operator]
        if recorded == math.inf:
            assert measured == math.inf, operator
        else:
            assert measured != math.inf, operator
            assert recorded <= measured, operator
            tolerance = 10 ** (math.floor(math.log10(measured)) - 3)
            assert measured - recorded < tolerance, (operator, measured, recorded, tolerance)


def test_adv_ac10_margin_transcription_positive_controls(harness_run, sl):
    _, verdict = harness_run
    finite_operators = [op for op in sl.SEVERITY_LADDERS if sl.RECORDED_MARGINS[op] != math.inf]
    assert finite_operators, "expected at least one finite recorded margin"
    operator = finite_operators[0]
    measured = verdict.per_ladder[operator].margin

    # A finite margin recorded above its measurement fails "recorded <= measured".
    recorded_too_high = measured * 1.1 + 1.0
    assert not (recorded_too_high <= measured)

    # A margin recorded inf against a finite measurement fails the exactness check.
    recorded_as_inf = math.inf
    assert (measured == math.inf) != (recorded_as_inf == math.inf)


def test_ac11_couplings_are_not_self_couplings(sl):
    for coupling in sl.KNOWN_CROSS_MODE_COUPLINGS:
        designated = sl.SEVERITY_LADDERS[coupling.ladder_operator].designated_metric
        assert coupling.foreign_metric != designated, coupling


# =========================================================================== #
# Foreign-set decision (AC12)
# =========================================================================== #


def _naive_margin(designated, responses):
    others = [value for metric, value in responses.items() if metric != designated]
    largest = max(others) if others else 0.0
    return math.inf if largest == 0.0 else 1.0 / largest


def _margin_excluding_same_home(designated, responses, home_of):
    designated_home = home_of(designated)
    foreign = [
        value
        for metric, value in responses.items()
        if metric != designated and home_of(metric) != designated_home
    ]
    largest = max(foreign) if foreign else 0.0
    return math.inf if largest == 0.0 else 1.0 / largest


def test_ac12_excluding_same_home_metrics_changes_no_margin(harness_run, sl):
    _, verdict = harness_run

    def home_of(metric_name):
        spec = PER_MODE_METRIC_SPECS[metric_name]
        return (spec.failure_mode, spec.condition)

    for operator, ladder_verdict in verdict.per_ladder.items():
        designated = sl.SEVERITY_LADDERS[operator].designated_metric
        alt_margin = _margin_excluding_same_home(designated, ladder_verdict.responses, home_of)
        if ladder_verdict.margin == math.inf:
            assert alt_margin == math.inf, operator
        else:
            assert alt_margin == pytest.approx(ladder_verdict.margin, rel=1e-12), operator


def test_adv_ac12_same_home_dominance_makes_the_two_margins_differ():
    """A synthetic responses table where a same-home metric ('same_home')
    carries the largest foreign response: the naive margin (over every
    foreign metric) and the same-home-excluded margin disagree, proving
    AC12's check is not vacuously true."""
    responses = {"designated": 1.0, "same_home": 0.9, "foreign": 0.2}
    homes = {"designated": (1, None), "same_home": (1, None), "foreign": (2, None)}

    naive = _naive_margin("designated", responses)
    excluding_same_home = _margin_excluding_same_home(
        "designated", responses, lambda m: homes[m]
    )
    assert naive != pytest.approx(excluding_same_home)


# =========================================================================== #
# Mode 1's ladder disposition (item 141) (AC13-AC15)
# =========================================================================== #


def test_ac13_one_disposition_for_mode1(sl):
    assert set(sl.MODE_LADDER_DISPOSITIONS) == {1}


def test_ac14_disposition_ladders_are_derived_from_the_homes(sl):
    expected = tuple(
        operator
        for operator in sl.SEVERITY_LADDERS
        if PER_MODE_METRIC_SPECS[sl.SEVERITY_LADDERS[operator].designated_metric].failure_mode
        == 1
    )
    assert sl.MODE_LADDER_DISPOSITIONS[1].ladders == expected


def test_adv_ac14_rehoming_a_metric_changes_the_derived_tuple(monkeypatch, sl):
    import segfacet.eval.per_mode as per_mode

    patched_specs = dict(per_mode.PER_MODE_METRIC_SPECS)
    patched_specs["rogue_island_count"] = dataclasses.replace(
        patched_specs["rogue_island_count"], failure_mode=1
    )
    monkeypatch.setattr(per_mode, "PER_MODE_METRIC_SPECS", patched_specs)

    rehomed_ladders = tuple(
        operator
        for operator in sl.SEVERITY_LADDERS
        if patched_specs[sl.SEVERITY_LADDERS[operator].designated_metric].failure_mode == 1
    )
    assert rehomed_ladders != sl.MODE_LADDER_DISPOSITIONS[1].ladders


def test_ac15_the_disposition_is_re_derived(sl):
    assert sl.MODE_LADDER_DISPOSITION_VALUES == ("re-derived", "no-ladder")
    assert sl.MODE_LADDER_DISPOSITIONS[1].disposition == "re-derived"
    assert sl.MODE_LADDER_DISPOSITIONS[1].disposition in sl.MODE_LADDER_DISPOSITION_VALUES


# =========================================================================== #
# The rank premise (AC16-AC18)
# =========================================================================== #


def _files_containing(root: Path, needle: str):
    return [path for path in sorted(root.rglob("*.py")) if needle in path.read_text(encoding="utf-8")]


def test_ac16_false_rank_premise_literal_is_gone_from_production():
    # Built by concatenation so this test file's own source never matches
    # the scanner it defines (AC16's own instruction).
    needle = "rank(v)" + " == v - 1"
    hits = _files_containing(_SRC_DIR, needle)
    assert hits == [], [path.as_posix() for path in hits]


def test_adv_ac16_scanner_flags_a_planted_file(tmp_path):
    needle = "rank(v)" + " == v - 1"
    planted = tmp_path / "planted_false_premise.py"
    planted.write_text(f"# {needle}\n", encoding="utf-8")
    hits = _files_containing(tmp_path, needle)
    assert hits == [planted]


def test_ac17_the_two_descent_finding_is_measured(sl):
    base = build_clean_spine(**sl._BASE_PARAMS)
    img = base.seg_img
    for target_label, new_label in ((24, 28), (23, 27), (22, 29)):
        operator = get_perturbation("sequence_break")(target_label=target_label, new_label=new_label)
        img = operator.apply(img, 0).labelmap

    final_arr = np.asanyarray(img.dataobj)
    present_values = sorted(int(v) for v in np.unique(final_arr) if v != 0)
    assert present_values, "expected at least one present label after the relabels"

    independent_count = _count_descents(present_values)

    record = extract_feature_record(img, bundled_default_config())
    metrics = compute_per_mode_metrics(record)
    measured = metrics.by_metric("out_of_order_label_count").value
    assert measured is not None, "expected out_of_order_label_count to be computable"

    assert measured == pytest.approx(independent_count)
    assert independent_count >= 2, present_values


def test_adv_ac17_descent_counter_positive_and_negative_controls():
    assert _count_descents([20, 21, 22, 23, 24]) == 0
    assert _count_descents([20, 21, 22, 23, 28]) == 1


def test_ac18_the_structural_claim_is_withdrawn(sl):
    assert "structural" not in sl.SEVERITY_LADDERS["sequence_break"].rationale.lower()
    assert "structural" not in (sl.__doc__ or "").lower()


# =========================================================================== #
# Mode 1's anchor (AC19-AC21)
# =========================================================================== #


def test_ac19_the_anchor_is_non_empty():
    assert len(feature_docs.MODE_ANCHOR_PATHS[1]) >= 1


def test_ac20_mode1_rules_consume_its_anchor():
    declarations = dict(iter_rule_declarations())
    intended_rule_ids = {rule.rule_id for rule in failure_modes.SPECIFICATION[1].intended_rules}
    anchor_paths = feature_docs.MODE_ANCHOR_PATHS[1]
    assert anchor_paths, "expected mode 1 to carry at least one anchor path"

    for path in anchor_paths:
        consumers = []
        for rule_id in intended_rule_ids:
            declaration = declarations.get(rule_id)
            if declaration is None:
                continue
            consumers.extend(
                consumed
                for consumed in declaration.consumed_paths
                if consumed.path == path and consumed.role == "signal"
            )
        assert consumers, (path, sorted(intended_rule_ids))


def test_adv_ac20_dropped_offset_path_is_not_a_mode1_signal():
    """The path this item drops from ``MODE_ANCHOR_PATHS[1]``: its only
    consumer, ``mislabel``, declares it ``"bookkeeping"``, and ``mislabel``
    is not among mode 1's intended rules -- so the AC20 check would fail if
    this path were still listed as mode 1's anchor."""
    declarations = dict(iter_rule_declarations())
    intended_rule_ids = {rule.rule_id for rule in failure_modes.SPECIFICATION[1].intended_rules}
    assert "mislabel" not in intended_rule_ids

    offset_path = "stage3.per_label_offsets[].offset_mm"
    mislabel_declaration = declarations["mislabel"]
    matches = [cp for cp in mislabel_declaration.consumed_paths if cp.path == offset_path]
    assert len(matches) == 1
    assert matches[0].role == "bookkeeping"


def test_ac21_candidate_feature_anchor_roles_mirror_the_anchor_map():
    anchor_role_paths = {
        feature.path
        for feature in failure_modes.SPECIFICATION[1].candidate_features
        if feature.role == "stage18-metric-anchor"
    }
    assert anchor_role_paths == set(feature_docs.MODE_ANCHOR_PATHS[1])


def test_adv_ac21_mismatched_anchor_role_raises_valueerror():
    mode1 = failure_modes.SPECIFICATION[1]
    bogus_feature = failure_modes.CandidateFeature(
        path="per_label.{label}.geometry.physical_volume_mm3",
        role="stage18-metric-anchor",
    )
    with pytest.raises(ValueError):
        dataclasses.replace(mode1, candidate_features=(bogus_feature,))


# =========================================================================== #
# Import hygiene (AC22)
# =========================================================================== #

_AUDIT_CHILD_TEMPLATE = """
import sys
import json

opened = []


def _hook(name, args):
    if name == "open":
        opened.append(str(args[0]))


sys.addaudithook(_hook)
import {module}

print(json.dumps(opened))
"""

_AUDIT_POSITIVE_CONTROL_CHILD = """
import sys
import json

opened = []


def _hook(name, args):
    if name == "open":
        opened.append(str(args[0]))


sys.addaudithook(_hook)
try:
    open("tests/__item154_audit_probe__.txt")
except OSError:
    pass

print(json.dumps(opened))
"""


def _paths_under_tests(opened):
    return [path for path in opened if "tests" in Path(path).parts]


@pytest.mark.parametrize(
    "module_name",
    ["segfacet.eval.severity_ladder", "segfacet.eval.per_mode", "segfacet.feature_docs"],
)
def test_ac22_import_reads_no_test_tree_path(module_name):
    code = _AUDIT_CHILD_TEMPLATE.format(module=module_name)
    result = run_utf8([sys.executable, "-c", code], cwd=_REPO_ROOT, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout, f"expected stdout from the {module_name} import subprocess"
    opened = json.loads(result.stdout)
    assert _paths_under_tests(opened) == [], (module_name, opened)


def test_adv_ac22_scanner_flags_a_planted_tests_open():
    result = run_utf8([sys.executable, "-c", _AUDIT_POSITIVE_CONTROL_CHILD], cwd=_REPO_ROOT, timeout=60)
    assert result.returncode == 0, result.stderr
    assert result.stdout, "expected stdout from the positive-control subprocess"
    opened = json.loads(result.stdout)
    assert _paths_under_tests(opened) != [], opened
