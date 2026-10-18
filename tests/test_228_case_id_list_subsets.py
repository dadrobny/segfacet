"""Tests for item 228 -- descriptor subsets as explicit case-id lists.

AC1-AC4 build directory trees of empty ``.nii.gz`` files (the resolver
discovers files by layout, never reads voxels); AC5 runs the pipeline over
real tiny synthetic NIfTIs.
"""
from __future__ import annotations

from pathlib import Path

import nibabel as nib
import pytest

from segfacet.cli import main
from segfacet.datasets import DatasetDescriptor, DatasetSchemaError, resolve
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.intensity import paint_clean_scan

VERSE_ID = r"(?P<id>sub-verse\d+(?:_split-verse\d+)?)_seg-vert_msk\.nii\.gz$"


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def _tree(root: Path, case_ids) -> Path:
    for cid in case_ids:
        sub = cid.split("_split-")[0]
        _touch(root / "derivatives" / sub / f"{cid}_seg-vert_msk.nii.gz")
    return root


def _descriptor(root: Path, subsets) -> DatasetDescriptor:
    return DatasetDescriptor.from_dict(
        {
            "data_root": str(root),
            "seg": "derivatives/sub-*/**/*_seg-vert_msk.nii.gz",
            "case_id": VERSE_ID,
            "scan": "rawdata/{id}/{id}_ct.nii.gz",
            "subsets": subsets,
        },
        descriptor_dir=str(root),
    )


def test_ac1_ids_subset_resolves_exactly_the_listed_cases(tmp_path):
    _tree(tmp_path, ["sub-verse004", "sub-verse004_split-verse01", "sub-verse005", "sub-verse006"])
    d = _descriptor(tmp_path, {"picked": {"ids": ["sub-verse004", "sub-verse006"]}})
    assert resolve(d, subset="picked").case_ids == ("sub-verse004", "sub-verse006")


def test_ac2_listed_id_without_mask_raises_naming_every_missing_id(tmp_path):
    _tree(tmp_path, ["sub-verse004"])
    d = _descriptor(
        tmp_path, {"picked": {"ids": ["sub-verse004", "sub-verse098", "sub-verse099"]}}
    )
    with pytest.raises(DatasetSchemaError) as exc:
        resolve(d, subset="picked")
    assert "sub-verse098" in str(exc.value)
    assert "sub-verse099" in str(exc.value)


def test_ac3_csv_listed_id_without_mask_raises_naming_it(tmp_path):
    _tree(tmp_path, ["sub-verse004"])
    (tmp_path / "role.csv").write_text(
        "case_id\nsub-verse004\nsub-verse099\n", encoding="utf-8"
    )
    d = _descriptor(tmp_path, {"role": {"csv": "role.csv"}})
    with pytest.raises(DatasetSchemaError, match="sub-verse099"):
        resolve(d, subset="role")


@pytest.mark.parametrize(
    "selector",
    [
        pytest.param({"root": "x", "ids": ["sub-verse004"]}, id="root-and-ids"),
        pytest.param(["sub-verse004"], id="bare-list"),
        pytest.param({"column": "case_id"}, id="no-selector-key"),
        pytest.param({"ids": None}, id="ids-none"),
        pytest.param({"ids": "sub-verse004"}, id="ids-bare-string"),
        pytest.param({"csv": 5}, id="csv-not-string"),
    ],
)
def test_ac4_malformed_selector_refused_at_construction(tmp_path, selector):
    with pytest.raises(DatasetSchemaError, match="badrole"):
        _descriptor(tmp_path, {"badrole": selector})


def test_review_csv_column_keyset_resolves_listed_cases(tmp_path):
    _tree(tmp_path, ["sub-verse004", "sub-verse005", "sub-verse006"])
    (tmp_path / "role.csv").write_text(
        "other,pick\nx,sub-verse004\ny,sub-verse006\n", encoding="utf-8"
    )
    d = _descriptor(tmp_path, {"role": {"csv": "role.csv", "column": "pick"}})
    assert resolve(d, subset="role").case_ids == ("sub-verse004", "sub-verse006")


def test_ac5_cli_subset_selects_ids_subset(tmp_path):
    root = tmp_path / "verse"
    for i, sub in enumerate(("sub-verse004", "sub-verse005", "sub-verse006")):
        spine = build_clean_spine(
            levels=("L1", "L2", "L3", "L4", "L5"),
            spacing=(1.0, 1.0, 1.0),
            curve_amplitude_mm=4.0 + i,
        )
        scan = paint_clean_scan(spine.seg_img, seed=i)
        (root / "derivatives" / sub).mkdir(parents=True, exist_ok=True)
        (root / "rawdata" / sub).mkdir(parents=True, exist_ok=True)
        nib.save(spine.seg_img, str(root / "derivatives" / sub / f"{sub}_seg-vert_msk.nii.gz"))
        nib.save(scan, str(root / "rawdata" / sub / f"{sub}_ct.nii.gz"))
    # ``as_posix()`` keeps Windows backslashes out of the double-quoted YAML scalar.
    desc = tmp_path / "d.yaml"
    desc.write_text(
        f'data_root: "{root.as_posix()}"\n'
        'seg: "derivatives/sub-*/**/*_seg-vert_msk.nii.gz"\n'
        'case_id: "(?P<id>sub-verse\\\\d+(?:_split-verse\\\\d+)?)_seg-vert_msk\\\\.nii\\\\.gz$"\n'
        'scan: "rawdata/{id}/{id}_ct.nii.gz"\n'
        "subsets:\n"
        "  picked:\n"
        "    ids: [sub-verse004, sub-verse006]\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    main(["run", "--dataset-schema", str(desc), "--subset", "picked",
          "--no-reference", "--out", str(out)])
    assert {p.name for p in out.iterdir()} == {"sub-verse004", "sub-verse006"}
