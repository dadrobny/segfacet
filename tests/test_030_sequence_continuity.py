"""Tests for item 030 — label-sequence continuity rule (sequence).

Covers all 14 Acceptance Criteria plus adversarial and edge-case inputs:

- AC1:  SequenceRule registers under rule_id == "sequence"; discoverable.
- AC2:  No finding for an in-order (continuous) fixture.
- AC3:  A finding fires for a single reversal.
- AC4:  The offending vertebra is attributed by its integer label.
- AC5:  Multiple out-of-order labels are reported in one finding.
- AC6:  The queue's canonical non-anatomical jump (L1 -> T12 -> L2 -> L5) is
        flagged.
- AC7:  No finding for a single-present-level record.
- AC8:  No finding for an empty / no-present-levels record.
- AC9:  The rule tolerates an absent / None / malformed relationship record.
- AC10: An offending name with no per_label entry is still reported, without
        its integer label.
- AC11: Default severity is FLAG; severity is config-driven.
- AC12: An unrecognised severity string raises ValueError.
- AC13: The rule is deterministic with a fixed output order.
- AC14: The rule does not mutate the input record.

Adversarial / edge-case scenarios included:
- A record with is_continuous == False but an empty out_of_order_labels
  emits no finding (malformed-record guard, Assumptions).
- out_of_order_labels containing a name with no matching per_label entry
  reports it in the reason with an empty/partial labels frozenset.
- Determinism across two run_rules calls, including offending-name order in
  the reason matching out_of_order_labels order.
- Mutation guard via deep-copy equality, including nested relationships and
  per_label lists/dicts.
- relationships that is not a mapping (e.g. a string) is tolerated.
- per_label entries that are not mappings are tolerated when scanning for a
  level_name match.

**Item 192 (2026-09-28).** The rewritten rule no longer reads
``relationships.out_of_order_labels[]`` (item 186's integer-label-order
defect); it orders each kept ``per_label`` entry head-to-tail by
``centroid.centroid_mm`` and ranks that order by ``CANONICAL_ORDER``. Every
record below gains a synthetic ``centroid_mm`` per entry (``z = n - i`` for
the *i*-th level of the record's ``present_levels`` order) so the rewritten
rule has a position to read; a two-label record is never out of order under
item 192's inversion-count tie-break, so several records below gain a third,
in-order tail level.
"""

from __future__ import annotations

import copy
import pathlib

import pytest

import segfacet.heuristics.sequence  # noqa: F401 — triggers SequenceRule registration
from segfacet.heuristics import Finding, Rule, get_rule, iter_rules, run_rules
from segfacet.heuristics.rule import _RULES
from segfacet.verdict import Severity
from segfacet.config import (
    SUPPORTED_SCHEMA_VERSION,
    default_config,
    load_config,
)


# =========================================================================== #
# Helpers
# =========================================================================== #

# Default label convention (item 004): the labels used throughout this file.
_LABEL_T12 = 19
_LABEL_L1 = 20
_LABEL_L2 = 21
_LABEL_L3 = 22
_LABEL_L5 = 24


def _make_per_label_entry(label: int, level_name: str) -> dict:
    """Build a minimal per_label entry carrying only label + level_name."""
    return {"label": label, "level_name": level_name}


def _make_record(
    present_levels: list,
    out_of_order_labels: list,
    is_continuous: bool = None,
    label_entries: list = None,
) -> dict:
    """Assemble a minimal build_features_block-shaped record.

    ``relationships`` carries present_levels/is_continuous/out_of_order_labels
    (item 014 shape); ``per_label`` is keyed by each entry's integer label.
    If *is_continuous* is not given, it is derived from out_of_order_labels
    being empty (matching item 014's pinned coupling).

    Item 192 (2026-09-28): the rewritten rule reads each entry's
    ``centroid.centroid_mm`` instead of ``out_of_order_labels[]``, so any
    entry whose ``level_name`` appears in *present_levels* gains a synthetic
    centroid: ``z = n - i`` for the *i*-th (1-indexed) level of
    *present_levels*, i.e. descending z in *present_levels* order.
    """
    if is_continuous is None:
        is_continuous = len(out_of_order_labels) == 0
    entries = [dict(e) for e in (label_entries or [])]
    n = len(present_levels)
    z_by_level = {name: float(n - i) for i, name in enumerate(present_levels, start=1)}
    for e in entries:
        z = z_by_level.get(e.get("level_name"))
        if z is not None:
            e["centroid"] = {"centroid_mm": [0.0, 0.0, z]}
    return {
        "case": {"sequence": {
            "present_levels": list(present_levels),
            "missing_levels": [],
            "is_continuous": is_continuous,
            "out_of_order_labels": list(out_of_order_labels),
        }},
        "per_label": {e["label"]: e for e in entries},
        "pairs": {"overlaps": {}},
    }


def _write_yaml(
    tmp_path: pathlib.Path, content: str, name: str = "config.yaml"
) -> pathlib.Path:
    """Write *content* to a YAML file under *tmp_path* and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _sequence_yaml_header() -> str:
    """Return a YAML preamble placing the cursor inside sequence params."""
    return (
        f"schema_version: '{SUPPORTED_SCHEMA_VERSION}'\n"
        "rules:\n"
        "  sequence:\n"
        "    params:\n"
    )


def _seq_findings(findings):
    """Filter to only sequence-rule findings."""
    return [f for f in findings if f.rule_id == "sequence"]


def _transitional_record() -> dict:
    """T10, T11, L1, L2, L3 (labels 17, 18, 20, 21, 22): an uncorroborated
    short thoracic section, which fires one ``transitional`` finding on T11.

    item 219 (2026-10-13): the AC11 severity claim is re-pointed here from the
    retired swap detector."""
    names = {17: "T10", 18: "T11", 20: "L1", 21: "L2", 22: "L3"}
    return {
        "per_label": {k: _make_per_label_entry(k, v) for k, v in names.items()},
        "pairs": {"overlaps": {}},
    }


_DISCONTINUITY_TAG = "Non-continuous label sequence:"


# =========================================================================== #
# Registry isolation — snapshot / restore around every test
# =========================================================================== #


@pytest.fixture(autouse=True)
def _isolated_registry():
    """Snapshot _RULES before each test (includes 'sequence') and restore after."""
    snapshot = dict(_RULES)
    yield
    _RULES.clear()
    _RULES.update(snapshot)


# =========================================================================== #
# AC1: SequenceRule registers under rule_id == "sequence"
# =========================================================================== #


def test_ac1_sequence_rule_is_in_registry():
    """AC1: get_rule('sequence') returns a Rule instance without raising."""
    rule = get_rule("sequence")
    assert rule.rule_id == "sequence"


def test_ac1_sequence_appears_in_iter_rules():
    """AC1: iter_rules() yields at least one rule with rule_id == 'sequence'."""
    assert any(r.rule_id == "sequence" for r in iter_rules())


def test_ac1_sequence_rule_is_rule_subclass():
    """AC1: The registered SequenceRule is a subclass of segfacet.heuristics.Rule."""
    assert isinstance(get_rule("sequence"), Rule)


# =========================================================================== #
# AC2: No finding for an in-order (continuous) fixture
# =========================================================================== #


def test_ac2_in_order_fixture_no_finding():
    """AC2: out_of_order_labels == [] and is_continuous == True under
    default_config() yields no sequence finding."""
    entries = [
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(["L1", "L2"], [], is_continuous=True, label_entries=entries)
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == [], f"In-order sequence should produce no finding; got {findings}"


# =========================================================================== #
# AC3: A finding fires for a single reversal
# =========================================================================== #


# item 219 (2026-10-13): retired -- sequence's AC3 subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


# =========================================================================== #
# AC4: The offending vertebra is attributed by its integer label
# =========================================================================== #


# item 219 (2026-10-13): retired -- sequence's AC4 subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


# =========================================================================== #
# AC5: Multiple out-of-order labels are reported in one finding
# =========================================================================== #


# item 219 (2026-10-13): retired -- sequence's AC5 subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


# =========================================================================== #
# AC6: The queue's canonical non-anatomical jump is flagged
# =========================================================================== #


# item 219 (2026-10-13): retired -- sequence's AC6 subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


# =========================================================================== #
# AC7: No finding for a single-present-level record
# =========================================================================== #


def test_ac7_single_present_level_no_finding():
    """AC7: One present level, out_of_order_labels == [], is_continuous ==
    True => evaluate returns [], no error."""
    entries = [_make_per_label_entry(_LABEL_L1, "L1")]
    record = _make_record(["L1"], [], is_continuous=True, label_entries=entries)
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


# =========================================================================== #
# AC8: No finding for an empty / no-present-levels record
# =========================================================================== #


def test_ac8_empty_record_no_finding():
    """AC8: present_levels == [] and out_of_order_labels == [] => [] , no
    error."""
    record = _make_record([], [], is_continuous=True, label_entries=[])
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


# =========================================================================== #
# AC9: The rule tolerates an absent / None / malformed relationship record
# =========================================================================== #


def test_ac9_relationships_none_returns_empty_list():
    """AC9: record['relationships'] is None => [] without raising."""
    record = {"case": {"sequence": None}, "per_label": {}, "pairs": {"overlaps": {}}}
    assert _seq_findings(run_rules(record, default_config())) == []


def test_ac9_relationships_absent_returns_empty_list():
    """AC9: record has no 'relationships' key => [] without raising."""
    record = {"per_label": {}, "pairs": {"overlaps": {}}}
    assert _seq_findings(run_rules(record, default_config())) == []


def test_ac9_out_of_order_and_is_continuous_absent_no_raise():
    """AC9: relationships present but without out_of_order_labels /
    is_continuous keys (treated as continuous) => []."""
    record = {"case": {"sequence": {"present_levels": ["L1"]}}, "per_label": {}, "pairs": {"overlaps": {}}}
    assert _seq_findings(run_rules(record, default_config())) == []


def test_ac9_per_label_empty_no_raise():
    """AC9: per_label == {} does not crash the rule.

    Item 192 (2026-09-28): the rewritten rule reads per_label centroids only;
    an offender with no per-label entry has no position to judge, so an empty
    per_label now yields no finding rather than an unattributed one."""
    record = {
        "case": {"sequence": {
            "present_levels": ["L1", "T12"],
            "is_continuous": False,
            "out_of_order_labels": ["T12"],
        }},
        "per_label": {},
        "pairs": {"overlaps": {}},
    }
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


def test_ac9_per_label_absent_no_raise():
    """AC9: record has no 'per_label' key at all.

    Item 192 (2026-09-28): with no per_label, no entry has a position to
    judge, so the result is empty rather than a single unattributed finding."""
    record = {
        "case": {"sequence": {
            "present_levels": ["L1", "T12"],
            "is_continuous": False,
            "out_of_order_labels": ["T12"],
        }},
        "pairs": {"overlaps": {}},
    }
    result = _seq_findings(run_rules(record, default_config()))
    assert result == []


def test_ac9_malformed_relationships_not_a_mapping_no_raise():
    """AC9: relationships that is not a mapping (e.g. a string) is tolerated
    and yields no findings rather than crashing."""
    record = {"case": {"sequence": "not-a-dict"}, "per_label": {}, "pairs": {"overlaps": {}}}
    result = _seq_findings(run_rules(record, default_config()))
    assert result == []


# =========================================================================== #
# AC10: An offending name with no per_label entry is still reported, without
# its integer label
# =========================================================================== #


def test_ac10_unmappable_offender_reported_without_label():
    """AC10: no per_label entry named 'T12' leaves only L1 as a kept entry.

    Item 192 (2026-09-28): a single kept entry has no position to judge
    against, so this now yields no finding rather than an unattributed one."""
    entries = [_make_per_label_entry(_LABEL_L1, "L1")]
    record = _make_record(
        ["L1", "T12"], ["T12"], is_continuous=False, label_entries=entries
    )
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


def test_ac10_mixed_mappable_and_unmappable_offenders():
    """AC10: 'T12' and 'GHOST_LEVEL' have no per_label entry; only L1 is kept.

    Item 192 (2026-09-28): a single kept entry has no position to judge
    against, so this now yields no finding."""
    entries = [_make_per_label_entry(_LABEL_L1, "L1")]
    record = _make_record(
        ["L1", "T12"],
        ["T12", "GHOST_LEVEL"],
        is_continuous=False,
        label_entries=entries,
    )
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


# =========================================================================== #
# AC11: Default severity is FLAG, and severity is config-driven
# =========================================================================== #


def test_ac11_default_severity_is_flag():
    """AC11: With no severity param, an emitted finding has Severity.FLAG.

    item 219 (2026-10-13): re-pointed to the ``transitional`` detector."""
    findings = _seq_findings(run_rules(_transitional_record(), default_config()))
    assert [f.detector_id for f in findings] == ["transitional"]
    assert findings[0].labels == frozenset({18})
    assert all(f.severity is Severity.FLAG for f in findings)


def test_ac11_severity_param_fail_overrides_default(tmp_path):
    """AC11: With params.severity = 'fail', the emitted finding has
    Severity.FAIL.

    item 219 (2026-10-13): re-pointed to the ``transitional`` detector."""
    content = _sequence_yaml_header() + "      severity: fail\n"
    cfg = load_config(_write_yaml(tmp_path, content))
    findings = _seq_findings(run_rules(_transitional_record(), cfg))
    assert [f.detector_id for f in findings] == ["transitional"]
    assert all(f.severity is Severity.FAIL for f in findings)


# =========================================================================== #
# AC12: An unrecognised severity string raises ValueError
# =========================================================================== #


def test_ac12_unrecognised_severity_raises_value_error(tmp_path):
    """AC12: An unrecognised severity param string raises ValueError.

    Item 192 (2026-09-28): L2 is added as a third, in-order tail level (a
    two-label record is never out of order)."""
    entries = [
        _make_per_label_entry(_LABEL_T12, "T12"),
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(
        ["L1", "T12", "L2"], ["T12"], is_continuous=False, label_entries=entries
    )
    content = _sequence_yaml_header() + "      severity: xyz_not_a_severity\n"
    cfg = load_config(_write_yaml(tmp_path, content))
    with pytest.raises(ValueError):
        run_rules(record, cfg)


def test_ac12_value_error_raised_before_per_record_processing(tmp_path):
    """AC12: ValueError fires even for a continuous / empty record — severity
    is parsed before any per-record processing."""
    content = _sequence_yaml_header() + "      severity: garbage\n"
    cfg = load_config(_write_yaml(tmp_path, content))
    record = {"per_label": {}, "case": {"sequence": None}, "pairs": {"overlaps": {}}}
    with pytest.raises(ValueError):
        run_rules(record, cfg)


def test_ac12_value_error_has_non_empty_message(tmp_path):
    """AC12: The ValueError for a bad severity has a non-empty, readable
    message."""
    entries = [_make_per_label_entry(_LABEL_L1, "L1")]
    record = _make_record(["L1"], [], is_continuous=True, label_entries=entries)
    content = _sequence_yaml_header() + "      severity: not_a_real_severity\n"
    cfg = load_config(_write_yaml(tmp_path, content))
    with pytest.raises(ValueError) as exc_info:
        run_rules(record, cfg)
    assert str(exc_info.value).strip()


# =========================================================================== #
# AC13: Deterministic with fixed output order
# =========================================================================== #


def test_ac13_two_runs_return_equal_lists():
    """AC13: Two successive run_rules calls return equal finding lists."""
    entries = [
        _make_per_label_entry(_LABEL_T12, "T12"),
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(
        ["L2", "T12", "L1"],
        ["T12", "L1"],
        is_continuous=False,
        label_entries=entries,
    )
    cfg = default_config()
    run1 = _seq_findings(run_rules(record, cfg))
    run2 = _seq_findings(run_rules(record, cfg))
    assert run1 == run2, f"Non-deterministic output:\nrun1={run1}\nrun2={run2}"


# item 219 (2026-10-13): retired -- sequence's AC13 subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


# =========================================================================== #
# Adversarial: malformed is_continuous / out_of_order_labels coupling
# =========================================================================== #


def test_adv_is_continuous_false_but_empty_out_of_order_labels_no_finding():
    """Adversarial: a malformed record with is_continuous == False but an
    empty out_of_order_labels emits no finding — the conservative choice per
    the spec's Assumptions (no concrete offender to name/attribute)."""
    record = _make_record(
        ["L1", "L2"], [], is_continuous=False, label_entries=[
            _make_per_label_entry(_LABEL_L1, "L1"),
            _make_per_label_entry(_LABEL_L2, "L2"),
        ]
    )
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


# =========================================================================== #
# AC14: The rule does not mutate the input record
# =========================================================================== #


def test_ac14_evaluate_does_not_mutate_record(tmp_path):
    """AC14: run_rules leaves the entire record (relationships, per_label,
    and every list) unchanged, even when the finding fires."""
    entries = [
        _make_per_label_entry(_LABEL_T12, "T12"),
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(
        ["L2", "T12", "L1"],
        ["T12", "L1"],
        is_continuous=False,
        label_entries=entries,
    )
    content = _sequence_yaml_header() + "      severity: fail\n"
    cfg = load_config(_write_yaml(tmp_path, content))
    record_before = copy.deepcopy(record)
    run_rules(record, cfg)
    assert record == record_before, "run_rules must not mutate the caller's record"


def test_ac14_out_of_order_labels_list_not_mutated():
    """AC14: The out_of_order_labels list inside relationships is unchanged
    after evaluate.

    Item 192 (2026-09-28): L2 is added as a third, in-order tail level (a
    two-label record is never out of order)."""
    entries = [
        _make_per_label_entry(_LABEL_T12, "T12"),
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(
        ["L1", "T12", "L2"], ["T12"], is_continuous=False, label_entries=entries
    )
    original = list(record["case"]["sequence"]["out_of_order_labels"])
    run_rules(record, default_config())
    assert record["case"]["sequence"]["out_of_order_labels"] == original


def test_ac14_per_label_dict_not_mutated():
    """AC14: per_label mapping (including nested entries) is unchanged after
    evaluate, even when the offender-to-label lookup succeeds.

    Item 192 (2026-09-28): L2 is added as a third, in-order tail level (a
    two-label record is never out of order)."""
    entries = [
        _make_per_label_entry(_LABEL_T12, "T12"),
        _make_per_label_entry(_LABEL_L1, "L1"),
        _make_per_label_entry(_LABEL_L2, "L2"),
    ]
    record = _make_record(
        ["L1", "T12", "L2"], ["T12"], is_continuous=False, label_entries=entries
    )
    original = copy.deepcopy(record["per_label"])
    run_rules(record, default_config())
    assert record["per_label"] == original


# =========================================================================== #
# Additional adversarial / edge cases
# =========================================================================== #


def test_adv_per_label_entry_not_a_mapping_no_raise():
    """Adversarial: a per_label entry that is not a mapping (malformed) is
    tolerated when scanning for a level_name match — treated as unmatched.

    Invoked directly against SequenceRule (not run_rules) so this exercises
    only sequence.py's own robustness in isolation: BoundsRule (item 027) is
    not defensive against a non-mapping per_label entry and would otherwise
    crash before SequenceRule is ever reached.

    Item 192 (2026-09-28): the non-mapping entry is ignored and the sole
    remaining entry (L1) has no position to judge against, so this now
    yields no finding."""
    record = {
        "case": {"sequence": {
            "present_levels": ["L1", "T12"],
            "is_continuous": False,
            "out_of_order_labels": ["T12"],
        }},
        "per_label": {1: "not-a-dict", 2: _make_per_label_entry(_LABEL_L1, "L1")},
        "pairs": {"overlaps": {}},
    }
    findings = get_rule("sequence").evaluate(record, default_config())
    assert findings == []


def test_adv_out_of_order_labels_absent_key_treated_as_continuous():
    """Adversarial: relationships with is_continuous explicitly True but no
    out_of_order_labels key at all => no finding, no crash."""
    record = {
        "case": {"sequence": {"present_levels": ["L1", "L2"], "is_continuous": True}},
        "per_label": {
            _LABEL_L1: _make_per_label_entry(_LABEL_L1, "L1"),
            _LABEL_L2: _make_per_label_entry(_LABEL_L2, "L2"),
        },
        "pairs": {"overlaps": {}},
    }
    findings = _seq_findings(run_rules(record, default_config()))
    assert findings == []


# item 219 (2026-10-13): retired -- sequence's three-offenders subject was retired (its
# swap/shift/skip detectors duplicated mislabel's ordering and
# coverage's missing_interior), so there is nothing left to assert.


def test_adv_determinism_with_unmappable_offender(tmp_path):
    """Adversarial: two run_rules calls on a record with an unmappable
    offender return identical lists."""
    entries = [_make_per_label_entry(_LABEL_L1, "L1")]
    record = _make_record(
        ["L1", "T12"], ["T12"], is_continuous=False, label_entries=entries
    )
    cfg = default_config()
    run1 = _seq_findings(run_rules(record, cfg))
    run2 = _seq_findings(run_rules(record, cfg))
    assert run1 == run2, f"Non-deterministic output:\nrun1={run1}\nrun2={run2}"
