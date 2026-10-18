"""Tests for item 234 -- the VerSe reference rebuilt from the development role only.

One test per Acceptance Criterion (``test_ac1`` .. ``test_ac11``; AC12 is
``test_123_recalibrate_and_regenerate.py::test_ac12_*``, not duplicated), then
the six adversarial cases the Testing Strategy names. AC1-AC8 and the named
cases run against stand-in roots built in ``tmp_path`` (never a real release);
AC9-AC11 are gated on ``SEGFACET_VERSE_COHORT`` / ``SEGFACET_VERSE20_COHORT``
and skip cleanly otherwise.

The stand-in thoracic run for AC4 and the excluded-level cases is
``T8..T12`` rather than the spec's ``T9..L1``: ``build_clean_spine`` refuses a
run that skips the transitional ``T13``, and T10 stays an interior level.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Optional

import nibabel as nib
import pytest

from segfacet.config import SUPPORTED_SCHEMA_VERSION, bundled_default_config, load_config
from segfacet.datasets import (
    Cohort,
    DatasetDescriptor,
    bundled_descriptor_path,
    load_descriptor,
    resolve,
)
from segfacet.heuristics.spline_offset import SplineOffsetRule
from segfacet.reference import ALL_STRATUM, bundled_production_reference_path, load_artifact
from segfacet.reference.ingest import ingest_dataset_cohort, ingest_subject
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.intensity import paint_clean_scan

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "scripts" / "rebuild_verse_reference.py"
_V19_VAR = "SEGFACET_VERSE_COHORT"
_V20_VAR = "SEGFACET_VERSE20_COHORT"
_V19_DIRS = ("dataset-verse19training", "dataset-verse19validation", "dataset-verse19test")
_V20_DIRS = ("dataset-01training", "dataset-02validation", "dataset-03test")
_ARTIFACT_NAME = "reference_verse_v1.json"
_SUMMARY_NAME = "verse_rebuild_summary.json"
_EXCLUDED_CASE = "sub-verse406_split-verse261"
_LUMBAR = ("L1", "L2", "L3", "L4", "L5")
_THORACIC = ("T8", "T9", "T10", "T11", "T12")


def _real_root(var: str, split_dirs) -> Optional[Path]:
    """The root named by ``var`` iff it is a directory holding every split dir."""
    raw = os.environ.get(var)
    if not raw:
        return None
    root = Path(raw)
    if not root.is_dir() or not all((root / s).is_dir() for s in split_dirs):
        return None
    return root


# Read once at import: the autouse fixture below clears the variables for the
# stand-in tests, and the gated tests must still see the real roots.
_REAL_V19 = _real_root(_V19_VAR, _V19_DIRS)
_REAL_V20 = _real_root(_V20_VAR, _V20_DIRS)

requires_both_releases = pytest.mark.skipif(
    _REAL_V19 is None or _REAL_V20 is None,
    reason=(
        f"real releases not mounted: set {_V19_VAR} to a directory holding "
        f"{', '.join(_V19_DIRS)} and {_V20_VAR} to a directory holding {', '.join(_V20_DIRS)}"
    ),
)
requires_verse19 = pytest.mark.skipif(
    _REAL_V19 is None,
    reason=f"VerSe19 cohort not mounted: set {_V19_VAR} to a directory holding {', '.join(_V19_DIRS)}",
)


@pytest.fixture(autouse=True)
def _clear_release_env(monkeypatch):
    monkeypatch.delenv(_V19_VAR, raising=False)
    monkeypatch.delenv(_V20_VAR, raising=False)


def _load_tool():
    spec = importlib.util.spec_from_file_location("rebuild_verse_reference", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _read_summary(out: Path) -> dict:
    return json.loads((out / _SUMMARY_NAME).read_text(encoding="utf-8"))


def _write_case(split_dir: Path, case_id: str, *, levels=_LUMBAR) -> None:
    """One stand-in VerSe-shaped case laid out as the bundled descriptors expect:
    ``derivatives/<sub>/<id>_seg-vert_msk.nii.gz`` and ``rawdata/<sub>/<id>_ct.nii.gz``."""
    sub = case_id  # every stand-in id is its own subject folder
    amplitude = 3.0 + (sum(map(ord, case_id)) % 5)
    spine = build_clean_spine(levels=levels, curve_amplitude_mm=amplitude)
    mask_dir = split_dir / "derivatives" / sub
    ct_dir = split_dir / "rawdata" / sub
    mask_dir.mkdir(parents=True, exist_ok=True)
    ct_dir.mkdir(parents=True, exist_ok=True)
    nib.save(spine.seg_img, str(mask_dir / f"{case_id}_seg-vert_msk.nii.gz"))
    nib.save(paint_clean_scan(spine.seg_img, seed=0), str(ct_dir / f"{case_id}_ct.nii.gz"))


def _release(root: Path, split_dirs, dev, cal, test, *, levels=_LUMBAR) -> Path:
    """A three-split stand-in release root holding the given case ids per role."""
    for split, ids in zip(split_dirs, (dev, cal, test)):
        (root / split).mkdir(parents=True, exist_ok=True)
        for case_id in ids:
            _write_case(root / split, case_id, levels=levels)
    return root


def _standin_roots(tmp_path: Path, name: str = "roots"):
    base = tmp_path / name
    v19 = _release(
        base / "v19", _V19_DIRS,
        ["sub-verse001", "sub-verse002"], ["sub-verse003"], ["sub-verse004"],
    )
    v20 = _release(
        base / "v20", _V20_DIRS,
        ["sub-gl001", "sub-gl002"], ["sub-gl003"], ["sub-gl004"],
    )
    return v19, v20


def _run(tool, out: Path, v19: Path, v20: Path, *extra: str) -> int:
    return tool.main(
        ["--out", str(out), "--verse-cohort", str(v19), "--verse20-cohort", str(v20), *extra]
    )


def _t_stats(out: Path, level: str):
    dist = load_artifact(out / _ARTIFACT_NAME)
    return dist.levels[level][ALL_STRATUM].feature_stats["spline_offset_mm"]


def _touch_mask(root: Path, split: str, case_id: str) -> None:
    path = root / split / "derivatives" / case_id / f"{case_id}_seg-vert_msk.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def _descriptor(**subsets) -> DatasetDescriptor:
    return DatasetDescriptor(
        data_root="unused",
        seg="derivatives/sub-*/**/*_seg-vert_msk.nii.gz",
        case_id=r"(?P<id>sub-verse\d+)_seg-vert_msk\.nii\.gz$",
        subsets={name: {"root": split} for name, split in subsets.items()},
    )


def _offset_record(entry: dict) -> dict:
    """A one-label record in the shape the rule reads (``per_label.<l>.curve``)."""
    return {
        "per_label": {
            str(entry["label"]): {
                "label": entry["label"],
                "level_name": entry["level_name"],
                "curve": {k: v for k, v in entry.items() if k not in ("label", "level_name")},
            }
        },
        "case": {"curve": {"is_monotonic": True}},
        "pairs": {"adjacent": {"non_monotonic_pairs": []}},
    }


def _terminal_record(terminal_offset_mm: float) -> dict:
    return _offset_record({
        "label": 24, "level_name": "L5", "closest_u": 0.5, "offset_mm": 1.0,
        "offset_voxel": 1.0, "dx_mm": 1.0, "dy_mm": 0.0, "dz_mm": 0.0,
        "is_terminal": True, "terminal_offset_mm": terminal_offset_mm,
    })


def _interior_record(offset_mm: float) -> dict:
    return _offset_record({
        "label": 22, "level_name": "L3", "closest_u": 0.5, "offset_mm": offset_mm,
        "offset_voxel": offset_mm, "dx_mm": offset_mm, "dy_mm": 0.0, "dz_mm": 0.0,
        "is_terminal": False,
    })


# =========================================================================== #
# AC1-AC8: the tool and the rule, against stand-ins
# =========================================================================== #


def test_ac1(tmp_path):
    tool = _load_tool()
    _touch_mask(tmp_path, "split-a", "sub-verse001")
    _touch_mask(tmp_path, "split-a", "sub-verse002")
    _touch_mask(tmp_path, "split-b", "sub-verse003")
    desc = _descriptor(development="split-a", calibration="split-a", test="split-b")
    with pytest.raises(tool.RoleOverlapError) as excinfo:
        tool.development_cohort([(desc, tmp_path)])
    assert "sub-verse001" in str(excinfo.value)
    assert "sub-verse002" in str(excinfo.value)


def test_ac2(tmp_path):
    tool = _load_tool()
    v19 = _release(
        tmp_path / "v19", _V19_DIRS, ["sub-verse001"], ["sub-verse001"], ["sub-verse004"],
    )
    v20 = _release(tmp_path / "v20", _V20_DIRS, ["sub-gl001"], ["sub-gl003"], ["sub-gl004"])
    out = tmp_path / "out"
    assert _run(tool, out, v19, v20) == 1
    assert not (out / _ARTIFACT_NAME).exists()


def test_ac3(tmp_path):
    tool = _load_tool()
    v19, v20 = _standin_roots(tmp_path)
    out = tmp_path / "out"
    assert _run(tool, out, v19, v20) == 0
    case_ids = load_artifact(out / _ARTIFACT_NAME).provenance.case_ids
    assert case_ids is not None
    assert tuple(case_ids) == tuple(sorted(["sub-verse001", "sub-verse002", "sub-gl001", "sub-gl002"]))


def test_ac4(tmp_path):
    tool = _load_tool()
    base = tmp_path / "roots"
    dev_all = ["sub-verse001", "sub-verse002", _EXCLUDED_CASE]
    v19_all = _release(base / "v19-all", _V19_DIRS, dev_all, ["sub-verse003"], ["sub-verse004"], levels=_THORACIC)
    v19_ab = _release(base / "v19-ab", _V19_DIRS, dev_all[:2], ["sub-verse003"], ["sub-verse004"], levels=_THORACIC)
    v20 = _release(base / "v20", _V20_DIRS, ["sub-gl001"], ["sub-gl003"], ["sub-gl004"])

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    assert _run(tool, out1, v19_all, v20) == 0
    assert _run(tool, out2, v19_ab, v20) == 0

    t10_run1 = _t_stats(out1, "T10")
    assert t10_run1.count == 2
    assert t10_run1 == _t_stats(out2, "T10")

    excluded = _read_summary(out1)["calibration"]["excluded_offsets"]
    assert len(excluded) == 1
    assert excluded[0]["case_id"] == _EXCLUDED_CASE
    assert excluded[0]["level_name"] == "T10"
    measured = ingest_subject(
        v19_all / _V19_DIRS[0] / "derivatives" / "sub-verse406" / f"{_EXCLUDED_CASE}_seg-vert_msk.nii.gz",
        config=bundled_default_config(), subject_id=_EXCLUDED_CASE, with_size_proxy=False,
    )
    t10_reading = next(r for r in measured.records if r.level_name == "T10").features["spline_offset_mm"]
    assert t10_reading > 0.0
    assert excluded[0]["offset_mm"] == pytest.approx(t10_reading)


def test_ac5(tmp_path):
    tool = _load_tool()
    v19, v20 = _standin_roots(tmp_path)
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    assert _run(tool, out_a, v19, v20) == 0
    assert _run(tool, out_b, v19, v20) == 0
    bytes_a = (out_a / _ARTIFACT_NAME).read_bytes()
    assert bytes_a
    assert bytes_a == (out_b / _ARTIFACT_NAME).read_bytes()


def test_ac6(tmp_path):
    tool = _load_tool()
    v19, _ = _standin_roots(tmp_path)
    out = tmp_path / "out"
    assert tool.main(["--out", str(out), "--verse-cohort", str(v19)]) == 0
    cohort = _read_summary(out)["cohort"]
    assert cohort["status"] == "skipped"
    assert _V20_VAR in cohort["reason"]
    assert not (out / _ARTIFACT_NAME).exists()


def test_ac7(tmp_path):
    split = tmp_path / _V19_DIRS[0]
    case_id = "sub-verse900_split-verse901"
    mask = split / "derivatives" / "sub-verse900" / f"{case_id}_seg-vert_msk.nii.gz"
    ct = split / "rawdata" / "sub-verse900" / f"{case_id}_ct.nii.gz"
    for path in (mask, ct):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    desc = load_descriptor(bundled_descriptor_path("verse19.yaml"))
    cohort = resolve(desc, data_root=tmp_path, subset="development")
    assert cohort.case_ids == (case_id,)
    assert cohort.cases[0].scan_path == str(ct.resolve())


def test_ac8():
    findings = SplineOffsetRule().evaluate(_terminal_record(10.0), bundled_default_config())
    assert findings == []


# =========================================================================== #
# AC9-AC11: the committed artifact against the real releases (gated)
# =========================================================================== #


def _role_ids(name: str, root: Path, role: str):
    return resolve(
        load_descriptor(bundled_descriptor_path(name)), data_root=root, subset=role
    ).case_ids


@requires_both_releases
def test_ac9():
    expected = sorted(
        set(_role_ids("verse19.yaml", _REAL_V19, "development"))
        | set(_role_ids("verse20.yaml", _REAL_V20, "development"))
    )
    assert expected
    committed = load_artifact(bundled_production_reference_path()).provenance.case_ids
    assert committed is not None
    assert tuple(committed) == tuple(expected)


@requires_both_releases
def test_ac10():
    held_out = set()
    for name, root in (("verse19.yaml", _REAL_V19), ("verse20.yaml", _REAL_V20)):
        for role in ("calibration", "test"):
            held_out |= set(_role_ids(name, root, role))
    assert held_out
    committed = load_artifact(bundled_production_reference_path()).provenance.case_ids
    assert committed
    assert set(committed).isdisjoint(held_out)


@requires_verse19
def test_ac11():
    desc = load_descriptor(bundled_descriptor_path("verse19.yaml"))
    development = resolve(desc, data_root=_REAL_V19, subset="development")
    case = next((c for c in development if c.case_id == _EXCLUDED_CASE), None)
    assert case is not None, f"{_EXCLUDED_CASE} not in the VerSe19 development role"
    ingested = ingest_dataset_cohort(
        Cohort(cases=(case,)),
        config=bundled_default_config(),
        with_size_proxy=False,
        with_intensity=False,
        with_morphology=False,
    )
    t10 = [r for s in ingested.subjects for r in s.records if r.level_name == "T10"]
    assert len(t10) == 1
    reading = t10[0].features["spline_offset_mm"]
    committed = load_artifact(bundled_production_reference_path())
    assert committed.levels["T10"][ALL_STRATUM].feature_stats["spline_offset_mm"].max < reading


# =========================================================================== #
# Named adversarial cases
# =========================================================================== #


def test_cross_release_duplicate(tmp_path):
    tool = _load_tool()
    root_one = tmp_path / "one"
    root_two = tmp_path / "two"
    for root in (root_one, root_two):
        _touch_mask(root, "split-a", "sub-verse001")
        _touch_mask(root, "split-b", "sub-verse003")
        _touch_mask(root, "split-c", "sub-verse004")
    desc = _descriptor(development="split-a", calibration="split-b", test="split-c")
    with pytest.raises(tool.RoleOverlapError) as excinfo:
        tool.development_cohort([(desc, root_one), (desc, root_two)])
    assert "sub-verse001" in str(excinfo.value)


def test_test_role_overlap(tmp_path):
    tool = _load_tool()
    _touch_mask(tmp_path, "split-a", "sub-verse001")
    _touch_mask(tmp_path, "split-b", "sub-verse003")
    desc = _descriptor(development="split-a", calibration="split-b", test="split-a")
    with pytest.raises(tool.RoleOverlapError) as excinfo:
        tool.development_cohort([(desc, tmp_path)])
    assert "sub-verse001" in str(excinfo.value)


def test_excluded_case_at_non_excluded_level(tmp_path):
    tool = _load_tool()
    base = tmp_path / "roots"
    dev_all = ["sub-verse001", "sub-verse002", _EXCLUDED_CASE]
    v19_all = _release(base / "v19-all", _V19_DIRS, dev_all, ["sub-verse003"], ["sub-verse004"], levels=_THORACIC)
    v19_ab = _release(base / "v19-ab", _V19_DIRS, dev_all[:2], ["sub-verse003"], ["sub-verse004"], levels=_THORACIC)
    v20 = _release(base / "v20", _V20_DIRS, ["sub-gl001"], ["sub-gl003"], ["sub-gl004"])
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    assert _run(tool, out1, v19_all, v20) == 0
    assert _run(tool, out2, v19_ab, v20) == 0
    count_ab = _t_stats(out2, "T11").count
    assert count_ab == 2
    assert _t_stats(out1, "T11").count == count_ab + 1


def test_parallel_equals_serial(tmp_path):
    tool = _load_tool()
    v19, v20 = _standin_roots(tmp_path)
    serial = tmp_path / "serial"
    parallel = tmp_path / "parallel"
    assert _run(tool, serial, v19, v20, "--jobs", "1") == 0
    assert _run(tool, parallel, v19, v20, "--jobs", "2") == 0
    serial_bytes = (serial / _ARTIFACT_NAME).read_bytes()
    assert serial_bytes
    assert serial_bytes == (parallel / _ARTIFACT_NAME).read_bytes()


def test_terminal_threshold_read_from_its_own_section(tmp_path):
    path = tmp_path / "terminal_config.yaml"
    path.write_text(
        f"schema_version: '{SUPPORTED_SCHEMA_VERSION}'\n"
        "rules:\n  spline_offset:\n    params:\n"
        "      max_terminal_offset_mm: 9.0\n",
        encoding="utf-8",
    )
    findings = SplineOffsetRule().evaluate(_terminal_record(10.0), load_config(path))
    assert len(findings) == 1
    assert "threshold 9.0 mm" in findings[0].reason


def test_interior_still_follows_max_offset_mm():
    findings = SplineOffsetRule().evaluate(_interior_record(10.0), bundled_default_config())
    assert len(findings) == 1
