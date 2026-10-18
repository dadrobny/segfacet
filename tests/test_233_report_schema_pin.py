"""Tests for item 233: the report schema version moves whenever a feature path moves.

One test per Acceptance Criterion plus the two named adversarial cases
(``missing-pin``, ``empty-live-set``). The live leaf-path set is computed here
from the catalogue primitives, never through ``live_leaf_paths()``, so the
guard is not asked to vouch for itself. Everything runs in-process and reads
files with ``read_text``.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

import segfacet
import segfacet.catalogue
import segfacet.report_schema_pin as pin_mod
from segfacet.config import default_config
from segfacet.report import REPORT_SCHEMA_VERSION, serialize_report
from segfacet.synth.golden import assert_matches_committed_artifact
from segfacet.verdict import Verdict

_PIN_FILE = Path(segfacet.__file__).resolve().parent / "report_schema_pin.json"


@pytest.fixture(scope="module")
def live_paths() -> frozenset[str]:
    paths: set[str] = set()
    for _name, record in segfacet.catalogue.iter_driver_records():
        paths |= segfacet.catalogue.iter_leaf_paths(record)
    return frozenset(paths)


def _built_report_version() -> str:
    report = serialize_report(
        Verdict.build(reasons=[], per_label={}), "case", default_config()
    )
    return report["schema_version"]


def _renamed(live: frozenset[str]) -> tuple[str, str, frozenset[str]]:
    removed = sorted(live)[0]
    added = f"{removed}_item233_renamed"
    return removed, added, frozenset((live - {removed}) | {added})


def test_ac1_committed_pin_is_the_live_pair(live_paths):
    assert live_paths
    expected = {
        "schema_version": _built_report_version(),
        "feature_leaf_paths": sorted(live_paths),
    }
    assert_matches_committed_artifact(expected, _PIN_FILE)


def test_ac2_shipped_tree_has_no_pin_conflict():
    assert pin_mod.pin_conflicts() == ()


def test_ac3_added_path_without_version_change_is_a_conflict(monkeypatch):
    real = segfacet.catalogue.iter_driver_records
    extra = "zz_item233_added_leaf"

    def wrapper():
        for index, (name, record) in enumerate(real()):
            if index == 0:
                record = copy.deepcopy(record)
                record[extra] = 1.0
            yield name, record

    monkeypatch.setattr(segfacet.catalogue, "iter_driver_records", wrapper)
    conflicts = pin_mod.pin_conflicts()
    assert isinstance(conflicts, tuple)
    assert conflicts
    assert any(extra in message for message in conflicts)


def test_ac4_renamed_path_without_version_change_is_a_conflict(live_paths):
    assert live_paths
    removed, added, renamed = _renamed(live_paths)
    conflicts = pin_mod.pin_conflicts(live_paths=renamed)
    assert conflicts
    text = "\n".join(conflicts)
    assert removed in text
    assert added in text


def test_ac5_repin_of_changed_set_under_same_version_is_refused(tmp_path, live_paths):
    assert live_paths
    pin_file = tmp_path / "pin.json"
    pin_mod.repin(
        pin_path=pin_file, live_paths=live_paths, report_version=REPORT_SCHEMA_VERSION
    )
    before = pin_file.read_text(encoding="utf-8")
    assert before
    _removed, _added, renamed = _renamed(live_paths)
    with pytest.raises(pin_mod.PinError):
        pin_mod.repin(
            pin_path=pin_file, live_paths=renamed, report_version=REPORT_SCHEMA_VERSION
        )
    assert pin_file.read_text(encoding="utf-8") == before


def test_ac6_renamed_path_with_version_change_and_repin_passes(tmp_path, live_paths):
    assert live_paths
    pin_file = tmp_path / "pin.json"
    pin_mod.repin(
        pin_path=pin_file, live_paths=live_paths, report_version=REPORT_SCHEMA_VERSION
    )
    _removed, _added, renamed = _renamed(live_paths)
    new_version = f"{REPORT_SCHEMA_VERSION}-item233"
    pin_mod.repin(pin_path=pin_file, live_paths=renamed, report_version=new_version)
    assert (
        pin_mod.pin_conflicts(
            live_paths=renamed, report_version=new_version, pin_path=pin_file
        )
        == ()
    )


def test_ac7_report_version_moved_off_pre_215_value():
    assert _built_report_version() != "0.1"


def test_missing_pin(tmp_path):
    absent = tmp_path / "absent.json"
    conflicts = pin_mod.pin_conflicts(pin_path=absent)
    assert conflicts
    assert any(absent.name in message for message in conflicts)


def test_empty_live_set(tmp_path):
    pin_file = tmp_path / "pin.json"
    pin_mod.repin(
        pin_path=pin_file,
        live_paths=frozenset(),
        report_version=REPORT_SCHEMA_VERSION,
    )
    assert pin_mod.pin_conflicts(live_paths=frozenset(), pin_path=pin_file)
