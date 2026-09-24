"""Tests for item 178 -- the committed corpus rendering
(``docs/aide/corpus_sheet.png``) and its generator,
``segfacet.synth.corpus_sheet``.

Covers Acceptance Criteria AC1-AC9 from
``docs/aide/items/178-a-committed-corpus-rendering.md``, one test each, plus
the one named adversarial case from its Testing Strategy:
``import-matcher-flags-seeded-import``.

Per the Testing Strategy, AC2-AC4 recompute the placed/projected/diffed
arrays themselves from the manifest and fixture files with plain NumPy and
nibabel -- never through the module's own ``sheet_panels()`` placement logic
-- and AC6/AC7's digest is computed with repeated ``hashlib.sha256().update()``
calls rather than the single-expression ``hashlib.sha256(<path>.read_bytes())
.hexdigest()`` shape ``tests/committed_artifact_guard.py`` (item 127)
classifies as a violation.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from segfacet.synth.corpus import CORPUS_DIR, MANIFEST_PATH, load_manifest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROTOTYPE_DIR = (
    _REPO_ROOT / "scripts" / "prototypes" / "2026-09-22-lordotic-corpus"
)
_SRC_ROOT = _REPO_ROOT / "src"
_TESTS_ROOT = _REPO_ROOT / "tests"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
_COMMITTED_SHEET = _REPO_ROOT / "docs" / "aide" / "corpus_sheet.png"

#: The prototype's deleted top-level module names (spec AC9).
_PROTOTYPE_MODULE_NAMES = frozenset(
    {"lordotic_spine", "corpus_v2", "check_and_render", "corpus_sheet"}
)


# =========================================================================== #
# Shared helpers
# =========================================================================== #


def _committed_manifest() -> dict:
    return load_manifest(MANIFEST_PATH)


def _load_seg_array(case: dict) -> nib.Nifti1Image:
    path = MANIFEST_PATH.parent / case["seg_fixture"]
    return nib.load(str(path))


def _clean_control_case(manifest: dict) -> dict:
    matches = [c for c in manifest["cases"] if c["case_id"] == "clean_control"]
    assert len(matches) == 1, matches
    return matches[0]


def _placed_on_clean_grid(clean_img: nib.Nifti1Image, case_img: nib.Nifti1Image) -> np.ndarray:
    """The spec's own placement algorithm (AC2), computed independently of
    the module under test."""
    clean_data = np.asanyarray(clean_img.dataobj)
    case_data = np.asanyarray(case_img.dataobj)
    start = np.round(
        (np.linalg.inv(clean_img.affine) @ case_img.affine[:, 3])[:3]
    ).astype(int)
    placed = np.zeros(clean_data.shape, dtype=case_data.dtype)
    stop = start + np.asarray(case_data.shape[:3])
    placed[start[0] : stop[0], start[1] : stop[1], start[2] : stop[2]] = case_data
    return placed


def _expected_digest(manifest_path: Path, manifest: dict) -> str:
    h = hashlib.sha256()
    h.update(manifest_path.read_bytes())
    for case in manifest["cases"]:
        fixture_path = manifest_path.parent / case["seg_fixture"]
        h.update(fixture_path.read_bytes())
    return h.hexdigest()


def _import_module_names(source: str) -> set:
    """Every top-level module name reached by an ``import``/``from ... import``
    statement in *source* (AC9's matcher)."""
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None and node.level == 0:
                names.add(node.module.split(".")[0])
    return names


def _has_prototype_import(source: str) -> bool:
    return bool(_import_module_names(source) & _PROTOTYPE_MODULE_NAMES)


# =========================================================================== #
# Module-scoped fixture: sheet_panels() over the committed corpus
# =========================================================================== #


@pytest.fixture(scope="module")
def sheet_panels():
    from segfacet.synth import corpus_sheet

    return corpus_sheet.sheet_panels()


@pytest.fixture(scope="module")
def committed_manifest():
    return _committed_manifest()


# =========================================================================== #
# AC1: one panel pair per case, in manifest order
# =========================================================================== #


def test_ac1_one_panel_pair_per_case_in_manifest_order(sheet_panels, committed_manifest):
    assert [p.case_id for p in sheet_panels] == [
        c["case_id"] for c in committed_manifest["cases"]
    ]


# =========================================================================== #
# AC2: the panels are max-label projections on clean_control's grid
# =========================================================================== #


def test_ac2_panels_are_max_label_projections_on_clean_control_grid(
    sheet_panels, committed_manifest
):
    clean_case = _clean_control_case(committed_manifest)
    clean_img = _load_seg_array(clean_case)
    panels_by_id = {p.case_id: p for p in sheet_panels}

    for case in committed_manifest["cases"]:
        case_img = _load_seg_array(case)
        placed = _placed_on_clean_grid(clean_img, case_img)
        panel = panels_by_id[case["case_id"]]

        assert np.array_equal(panel.sagittal, placed.max(axis=0).T)
        assert np.array_equal(panel.coronal, placed.max(axis=1).T)


# =========================================================================== #
# AC3: the outlines are the changed voxels
# =========================================================================== #


def test_ac3_outlines_are_the_changed_voxels(sheet_panels, committed_manifest):
    clean_case = _clean_control_case(committed_manifest)
    clean_img = _load_seg_array(clean_case)
    clean_data = np.asanyarray(clean_img.dataobj)
    panels_by_id = {p.case_id: p for p in sheet_panels}

    # The off-grid case (crop_fov_si) is where placement is actually
    # exercised -- guard against a vacuous pass if the corpus ever stopped
    # carrying a case with a different shape/affine than clean_control.
    has_off_grid_case = any(
        _load_seg_array(c).shape != clean_img.shape
        or not np.allclose(_load_seg_array(c).affine, clean_img.affine)
        for c in committed_manifest["cases"]
    )
    assert has_off_grid_case

    for case in committed_manifest["cases"]:
        case_img = _load_seg_array(case)
        placed = _placed_on_clean_grid(clean_img, case_img)
        panel = panels_by_id[case["case_id"]]

        changed = placed != clean_data
        assert np.array_equal(panel.sagittal_changed, changed.any(axis=0).T)
        assert np.array_equal(panel.coronal_changed, changed.any(axis=1).T)


# =========================================================================== #
# AC4: clean_control has no outline
# =========================================================================== #


def test_ac4_clean_control_has_no_outline(sheet_panels):
    panels_by_id = {p.case_id: p for p in sheet_panels}
    clean_panel = panels_by_id["clean_control"]

    assert not clean_panel.sagittal_changed.any()
    assert not clean_panel.coronal_changed.any()


# =========================================================================== #
# AC5: the sheet draws every panel
# =========================================================================== #


def test_ac5_sheet_draws_every_panel(tmp_path, committed_manifest):
    from segfacet.synth import corpus_sheet

    fig = corpus_sheet.render_sheet(out=tmp_path / "sheet.png")

    axes_with_images = [ax for ax in fig.axes if len(ax.images) > 0]
    assert len(axes_with_images) == 2 * len(committed_manifest["cases"])


# =========================================================================== #
# AC6: the sheet regenerates from the manifest
# =========================================================================== #


def test_ac6_sheet_regenerates_from_the_manifest(tmp_path, committed_manifest):
    from PIL import Image

    from segfacet.synth import corpus_sheet

    out_path = tmp_path / "sheet.png"
    rc = corpus_sheet.main(["--out", str(out_path)])
    assert rc == 0

    expected_digest = _expected_digest(MANIFEST_PATH, committed_manifest)

    with Image.open(out_path) as img:
        source = img.text["Source"]
    assert source == "sha256:" + expected_digest


# =========================================================================== #
# AC7: the committed sheet is current
# =========================================================================== #


def test_ac7_committed_sheet_is_current(committed_manifest):
    from PIL import Image

    assert _COMMITTED_SHEET.is_file(), (
        "docs/aide/corpus_sheet.png is missing or stale; regenerate with "
        "`python -m segfacet.synth.corpus_sheet`"
    )

    expected_digest = _expected_digest(MANIFEST_PATH, committed_manifest)

    with Image.open(_COMMITTED_SHEET) as img:
        source = img.text.get("Source")

    assert source == "sha256:" + expected_digest, (
        "docs/aide/corpus_sheet.png's Source digest does not match the "
        "committed manifest + fixtures; regenerate with "
        "`python -m segfacet.synth.corpus_sheet`"
    )


# =========================================================================== #
# AC8: the prototype directory is gone
# =========================================================================== #


def test_ac8_prototype_directory_is_gone():
    assert not _PROTOTYPE_DIR.exists()


# =========================================================================== #
# AC9: nothing imports from the prototype
# =========================================================================== #


def test_ac9_nothing_imports_from_the_prototype():
    hits = []
    for root in (_SRC_ROOT, _TESTS_ROOT, _SCRIPTS_ROOT):
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            if _has_prototype_import(source):
                hits.append(path.relative_to(_REPO_ROOT).as_posix())

    assert hits == []


# =========================================================================== #
# Named adversarial case: import-matcher-flags-seeded-import
# =========================================================================== #


def test_import_matcher_flags_seeded_import():
    assert _has_prototype_import("from lordotic_spine import build")
    assert _has_prototype_import("import corpus_sheet")

    assert not _has_prototype_import("from segfacet.synth import corpus_sheet")
    assert not _has_prototype_import("import segfacet.synth.corpus_sheet")
