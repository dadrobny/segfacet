"""Item 224: platform-sensitive snapshot comparisons are tolerant, determinism
checks are exact.

Each test drives the real shipped test function (test_098 AC15, test_102
``test_ac5``, test_123 AC28, test_082's determinism test) against a mutated
copy of the pinned ``displace`` / ``fragment`` / ``relabel_swap`` entry, so it
proves the shipped comparison is the one that tolerates or catches the change.
The shared constant is never mutated in place: eight modules import it.
"""

from __future__ import annotations

import copy
import json

import pytest

import test_082_verse_build_recipe as t082
import test_098_stray_components as t098
import test_102_stage18_validation as t102
import test_123_recalibrate_and_regenerate as t123

_PINNED = t098._PRE_098_GOLDEN_VERDICT_AND_FINDINGS


def _mutated(monkeypatch, case_id, mutate):
    entry = copy.deepcopy(_PINNED[case_id])
    mutate(entry)
    monkeypatch.setitem(_PINNED, case_id, entry)


def _replace_in_reason(old, new):
    def mutate(entry):
        reason = entry["findings"][0]["reason"]
        assert old in reason
        entry["findings"][0]["reason"] = reason.replace(old, new)

    return mutate


def test_ac1_last_digit_difference_passes_ac15(monkeypatch):
    _mutated(monkeypatch, "displace", _replace_in_reason("14.6", "14.7"))
    t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_ac2_changed_verdict_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "displace", lambda e: e.update(verdict="pass"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_ac3_decimal_more_than_one_unit_off_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "displace", _replace_in_reason("14.6", "14.8"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_ac4_integer_token_changed_by_one_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "fragment", _replace_in_reason("9796", "9797"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("fragment")


def test_ac5_changed_non_numeric_text_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "displace", _replace_in_reason("left-right", "anterior-posterior"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_ac6_changed_finding_label_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "displace", lambda e: e["findings"][0].update(labels=[21]))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_ac7_test_102_snapshot_comparison_tolerates_last_digit_difference():
    pinned = _PINNED["displace"]
    report = copy.deepcopy(pinned)
    report["findings"][0]["reason"] = report["findings"][0]["reason"].replace("14.6", "14.7")
    t102.test_ac5_report_verdict_and_findings_match_pre_098_snapshot(
        {"displace": report}, "displace"
    )


def test_ac8_test_123_ac28_tolerates_last_digit_difference(monkeypatch):
    _mutated(monkeypatch, "displace", _replace_in_reason("14.6", "14.7"))
    t123.test_ac28_pinned_snapshot_reasons_equal_committed_golden_reasons()


def test_ac9_one_byte_build_difference_fails_determinism_test(monkeypatch, tmp_path):
    original = t082._run_build_reference
    calls = []

    def wrapper(cohort_dir, out_path, **kwargs):
        code = original(cohort_dir, out_path, **kwargs)
        calls.append(out_path)
        if len(calls) == 2:
            with open(out_path, "ab") as fh:
                fh.write(b"\n")
        return code

    monkeypatch.setattr(t082, "_run_build_reference", wrapper)
    with pytest.raises(AssertionError):
        t082.test_adv_determinism_two_builds_produce_equal_parsed_artifacts(tmp_path)

    assert len(calls) == 2
    parsed = [json.loads(p.read_text(encoding="utf-8")) for p in calls]
    assert parsed[0] == parsed[1]


def test_adv_pinned_precision_width(monkeypatch):
    _mutated(monkeypatch, "fragment", _replace_in_reason("0.52579", "0.52581"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("fragment")


def test_adv_integer_stands_in_for_decimal(monkeypatch):
    _mutated(monkeypatch, "displace", _replace_in_reason("14.6", "15"))
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("displace")


def test_adv_extra_finding(monkeypatch):
    _mutated(
        monkeypatch,
        "relabel_swap",
        lambda e: e["findings"].append(copy.deepcopy(e["findings"][0])),
    )
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("relabel_swap")
