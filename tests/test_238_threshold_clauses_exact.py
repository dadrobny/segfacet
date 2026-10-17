"""Item 238: threshold literals in pinned reasons are compared exactly.

Each test drives the real shipped test_098 AC15 against a mutated copy of the
pinned ``remove_level`` / ``fragment`` entry. The shared constant is never
mutated in place: eight modules import it.
"""

from __future__ import annotations

import copy

import pytest

import test_098_stray_components as t098

_PINNED = t098._PRE_098_GOLDEN_VERDICT_AND_FINDINGS


def _mutated(monkeypatch, case_id, detector_id, old, new):
    entry = copy.deepcopy(_PINNED[case_id])
    matches = [f for f in entry["findings"] if f.get("detector_id") == detector_id]
    assert matches
    finding = matches[0]
    assert old in finding["reason"]
    finding["reason"] = finding["reason"].replace(old, new)
    monkeypatch.setitem(_PINNED, case_id, entry)


def test_ac1_gap_ratio_threshold_1_4_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "remove_level", "missing_level", "strictly above 1.5", "strictly above 1.4")
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("remove_level")


def test_ac2_gap_ratio_threshold_1_6_fails_ac15(monkeypatch):
    _mutated(monkeypatch, "remove_level", "missing_level", "strictly above 1.5", "strictly above 1.6")
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("remove_level")


def test_ac3_measured_last_digit_difference_still_passes(monkeypatch):
    _mutated(monkeypatch, "remove_level", "missing_level", "1.887x", "1.888x")
    t098.test_ac15_golden_verdict_and_findings_unchanged("remove_level")


def test_size_ratio_clause(monkeypatch):
    _mutated(monkeypatch, "remove_level", "missing_level", "at most 1.5x", "at most 1.6x")
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("remove_level")


def test_threshold_phrasing(monkeypatch):
    entry = copy.deepcopy(_PINNED["fragment"])
    reason = entry["findings"][0]["reason"]
    assert "threshold 0.75" in reason
    entry["findings"][0]["reason"] = reason.replace("threshold 0.75", "threshold 0.76")
    monkeypatch.setitem(_PINNED, "fragment", entry)
    with pytest.raises(AssertionError):
        t098.test_ac15_golden_verdict_and_findings_unchanged("fragment")
