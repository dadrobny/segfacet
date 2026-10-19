"""Tests for item 229 -- VerSe20 ground-truth descriptor and dataset-role subsets.

One test per Acceptance Criterion (``test_ac1`` .. ``test_ac7``). AC5-AC7 are
gated on the real releases: ``SEGFACET_VERSE20_COHORT`` (AC5, AC6) and
``SEGFACET_VERSE_COHORT`` (AC7) must name a directory holding all three split
directories, and skip cleanly otherwise.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path
from typing import Optional

import pytest

from segfacet.datasets import bundled_descriptor_path, load_descriptor, resolve

_ROLES = ("development", "calibration", "test")
_VERSE19_DIRS = ("dataset-verse19training", "dataset-verse19validation", "dataset-verse19test")
_VERSE20_DIRS = ("dataset-01training", "dataset-02validation", "dataset-03test")


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def _real_root(var: str, split_dirs) -> Optional[Path]:
    """The root named by ``var`` iff it is a directory holding every split dir."""
    raw = os.environ.get(var)
    if not raw:
        return None
    root = Path(raw)
    if not root.is_dir():
        return None
    if not all((root / s).is_dir() for s in split_dirs):
        return None
    return root


requires_verse19 = pytest.mark.skipif(
    _real_root("SEGFACET_VERSE_COHORT", _VERSE19_DIRS) is None,
    reason=(
        "VerSe19 cohort not mounted: set SEGFACET_VERSE_COHORT to a directory "
        "holding dataset-verse19training, dataset-verse19validation, dataset-verse19test"
    ),
)
requires_verse20 = pytest.mark.skipif(
    _real_root("SEGFACET_VERSE20_COHORT", _VERSE20_DIRS) is None,
    reason=(
        "VerSe20 cohort not mounted: set SEGFACET_VERSE20_COHORT to a directory "
        "holding dataset-01training, dataset-02validation, dataset-03test"
    ),
)


def _mask(split_dir: Path, sub: str, name: str) -> None:
    _touch(split_dir / "derivatives" / sub / name)


def _roles_resolve_own_split(tmp_path, descriptor_name, split_dirs):
    root = tmp_path / "root"
    expected = {}
    for n, (role, split) in enumerate(zip(_ROLES, split_dirs)):
        subs = [f"sub-verse{n}0{i}" for i in range(2)]
        for sub in subs:
            _mask(root / split, sub, f"{sub}_seg-vert_msk.nii.gz")
        expected[role] = tuple(sorted(subs))
    d = load_descriptor(bundled_descriptor_path(descriptor_name))
    for role in _ROLES:
        got = resolve(d, data_root=root, subset=role).case_ids
        assert got == expected[role], role


def test_ac1(tmp_path):
    _roles_resolve_own_split(tmp_path, "verse19.yaml", _VERSE19_DIRS)


def test_ac2(tmp_path):
    _roles_resolve_own_split(tmp_path, "verse20.yaml", _VERSE20_DIRS)


def test_ac3(tmp_path):
    split = tmp_path / "dataset-01training"
    for name in (
        "sub-verse500_dir-ax_seg-vert_msk.nii.gz",
        "sub-verse501_dir-iso_seg-vert_msk.nii.gz",
        "sub-verse502_dir-sag_seg-vert_msk.nii.gz",
        "sub-verse503_seg-vert_msk.nii.gz",
        "sub-gl004_dir-ax_seg-vert_msk.nii.gz",
        "sub-verse504_split-verse600_dir-ax_seg-vert_msk.nii.gz",
    ):
        _mask(split, name.split("_")[0], name)
    d = load_descriptor(bundled_descriptor_path("verse20.yaml"))
    cohort = resolve(d, data_root=tmp_path, subset="development")
    assert cohort.case_ids == (
        "sub-gl004",
        "sub-verse500",
        "sub-verse501",
        "sub-verse502",
        "sub-verse503",
        "sub-verse504_split-verse600",
    )


def test_ac4(tmp_path):
    split = tmp_path / "dataset-01training"
    cts = {
        "sub-verse500": split / "rawdata" / "sub-verse500" / "sub-verse500_dir-ax_ct.nii.gz",
        "sub-verse503": split / "rawdata" / "sub-verse503" / "sub-verse503_ct.nii.gz",
    }
    for sub, ct in cts.items():
        _mask(split, sub, f"{sub}_seg-vert_msk.nii.gz")
        _touch(ct)
    d = load_descriptor(bundled_descriptor_path("verse20.yaml"))
    cohort = resolve(d, data_root=tmp_path, subset="development")
    assert cohort.case_ids == ("sub-verse500", "sub-verse503")
    for case in cohort:
        assert case.scan_path == str(cts[case.case_id].resolve())


@requires_verse20
def test_ac5():
    root = _real_root("SEGFACET_VERSE20_COHORT", _VERSE20_DIRS)
    d = load_descriptor(bundled_descriptor_path("verse20.yaml"))
    resolved = sum(len(resolve(d, data_root=root, subset=r)) for r in _ROLES)
    on_disk = sum(
        len(list((root / s / "derivatives").rglob("*_seg-vert_msk.nii.gz")))
        for s in _VERSE20_DIRS
    )
    assert on_disk > 0
    assert resolved == on_disk


@requires_verse20
def test_ac6():
    root = _real_root("SEGFACET_VERSE20_COHORT", _VERSE20_DIRS)
    d = load_descriptor(bundled_descriptor_path("verse20.yaml"))
    sets = [set(resolve(d, data_root=root, subset=r).case_ids) for r in _ROLES]
    assert all(sets)
    for a, b in itertools.combinations(sets, 2):
        assert a.isdisjoint(b)


@requires_verse19
def test_ac7():
    root = _real_root("SEGFACET_VERSE_COHORT", _VERSE19_DIRS)
    d = load_descriptor(bundled_descriptor_path("verse19.yaml"))
    sets = [set(resolve(d, data_root=root, subset=r).case_ids) for r in _ROLES]
    assert all(sets)
    for a, b in itertools.combinations(sets, 2):
        assert a.isdisjoint(b)
