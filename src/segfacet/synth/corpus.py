"""Committed synthetic fixture corpus for the failure-mode specification plus the
clean-GT positive control, and its versioned manifest (item 040).

Materialises the **fourteen canonical cases** -- item 040's original nine (the
clean control plus one per mode of the vision.md v3 seed list, history ids
1-8, whose case ids name
the case's perturbation operator -- item 157 (2026-09-17) dropped the stale
``modeN_`` prefixes those ids carried, since the manifest's ``failure_mode``
field is the authority and the prefix was a second, drifting copy of it) and
the ``fuse_adjacent`` and ``remove_level_relabel`` cases item 150 added, and
the ``split`` case item 166 added (2026-09-20), and the ``split_own_label``
case item 174 added (2026-09-23), and the ``crop_fov_si`` case item 175
added (2026-09-24), a volume crop on a smaller grid carrying its own scan;
each manifest entry's
``failure_mode`` field carries the current mode number, and (item 155) a
``kind`` field records which of the three closed values
(``segfacet.synth.perturbation.CASE_KINDS``: ``"clean_control"``,
``"condition"``, ``"failure"``) the case is, derived from ``failure_mode``
and ``condition`` by ``segfacet.synth.perturbation.case_kind`` -- using
the merged Stage 5 generators (items 036-039): :func:`build_clean_spine`
(item 036) as the shared base, and the registered operators from item 037
(``fragment``), item 038 (``remove_level``, ``crop_at_border``,
``force_overlap``), and item 039 (``displace``, ``relabel_swap``,
``sequence_break``).

Two public surfaces:

* An **in-memory API** -- :func:`build_corpus` (the recipe -> per-case
  ``CorpusCase`` objects, no disk I/O) and :func:`write_corpus` (materialise
  fixtures + manifest to disk, deterministically).
* A **CLI entry point** -- ``python -m segfacet.synth.corpus [--out DIR]``
  (:func:`main`), regenerating the committed corpus under
  ``tests/corpus/`` by default.

One of the fourteen cases (mode 15 -- ``force_overlap``) is documented by item 038
as **structurally invisible** to the plain ``run_qc`` pipeline (a
single-integer label map cannot encode an overlap). This module faithfully
represents that fact: its manifest entry carries
``detection == "reconstructed_record"`` and a ``reconstruction`` technique
key, rather than pretending ``run_qc`` would catch it. Mode 1 (``displace``)
was reconstructed_record before item 120 promoted a held-out per-label
spline offset into the pipeline itself; it is now ``detection == "pipeline"``.
The mode-9 ``relabel_swap`` case was reconstructed_record before item 132 (2026-08-31)
made ``compute_monotonic_consistency`` judge against a curve fitted in
geometric traversal order rather than the ordering under test, so the swap
now reads out of order through plain ``run_qc``; it is now
``detection == "pipeline"`` like every case but the overlap one. See the item 040
spec's Assumptions for the full rationale.

Item 157 (2026-09-17) dropped the ``modeN_`` prefixes above; the mapping is
also recorded in code as :data:`RENAMED_CASE_IDS`, a frozen historical record
kept for the handful of tests that must still reach a pre-rename artifact.
Each pair, old id -> new id:

* ``mode1_displace`` -> ``displace``
* ``mode2_fragment`` -> ``fragment``
* ``mode3_inject_islands`` -> ``inject_islands``
* ``mode4_relabel_swap`` -> ``relabel_swap``
* ``mode5_remove_level`` -> ``remove_level``
* ``mode6_crop_at_border`` -> ``crop_at_border``
* ``mode7_sequence_break`` -> ``sequence_break``
* ``mode8_force_overlap`` -> ``force_overlap``
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import nibabel as nib
import numpy as np

from segfacet.io import FacetInputError
from segfacet.synth.clean_gt import build_clean_spine
from segfacet.synth.perturbation import Expectation, get_perturbation

# Import the operator-family modules so every operator self-registers before
# get_perturbation() is used below. Imported from submodules (not the
# segfacet.synth package) to avoid a circular import, since segfacet/synth/__init__
# additively re-exports this module too.
import segfacet.synth.component_shape  # noqa: F401
import segfacet.synth.coverage_border_overlap  # noqa: F401
import segfacet.synth.identity_ordering_alignment  # noqa: F401

__all__ = [
    "CORPUS_DIR",
    "MANIFEST_PATH",
    "FIXTURES_DIRNAME",
    "MANIFEST_VERSION",
    "CorpusCase",
    "CASE_RECIPE",
    "RENAMED_CASE_IDS",
    "crop_to_grid",
    "build_corpus",
    "write_corpus",
    "load_manifest",
    "main",
]

# --------------------------------------------------------------------------- #
# Module constants
# --------------------------------------------------------------------------- #

#: The committed corpus directory: <repo>/tests/corpus.
CORPUS_DIR: Path = Path(__file__).resolve().parents[3] / "tests" / "corpus"

#: The committed manifest file.
MANIFEST_PATH: Path = CORPUS_DIR / "manifest.json"

#: Name of the fixtures subdirectory under a corpus directory.
FIXTURES_DIRNAME: str = "fixtures"

#: Manifest schema version (bump on any incompatible schema change).
MANIFEST_VERSION: int = 1

#: Item 157 (2026-09-17): the frozen historical record of the eight
#: ``modeN_`` case-id prefixes dropped from the corpus, old id -> new id.
#: Never extended by later renames without a new decision (A2), and nothing
#: in ``src/`` reads it at runtime -- it exists for documentation and for the
#: tests that must resolve a pre-rename artifact (a pinned git blob, a
#: retired file, a dated comparison record).
RENAMED_CASE_IDS: Dict[str, str] = {
    "mode1_displace": "displace",
    "mode2_fragment": "fragment",
    "mode3_inject_islands": "inject_islands",
    "mode4_relabel_swap": "relabel_swap",
    "mode5_remove_level": "remove_level",
    "mode6_crop_at_border": "crop_at_border",
    "mode7_sequence_break": "sequence_break",
    "mode8_force_overlap": "force_overlap",
}

#: Name of the shared base-scan fixture (every case derives from the same
#: default clean spine; a case on the base grid shares this scan -- see the
#: item 040 spec's "all nine canonical cases share one base scan"
#: Assumption). A case on a different grid (item 175's ``crop_fov_si``, a
#: volume crop) carries its own ``<case_id>_scan.nii.gz``: the base scan cut
#: to its grid by :func:`crop_to_grid`.
_BASE_SCAN_FIXTURE_NAME: str = "base_scan.nii.gz"

#: The default clean-spine build parameters used by every case's base.
_DEFAULT_BASE_PARAMS: Dict[str, Any] = {
    "levels": ["L1", "L2", "L3", "L4", "L5"],
    "spacing": [1.0, 1.0, 1.0],
    "curve_amplitude_mm": 0.0,
}


# --------------------------------------------------------------------------- #
# The recipe -- the single declarative source of the canonical cases
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _RecipeEntry:
    """One row of the case table: which operator, params, seed, and base."""

    case_id: str
    perturbation: str
    perturbation_params: Dict[str, Any] = field(default_factory=dict)
    seed: int = 0
    base: Dict[str, Any] = field(default_factory=lambda: dict(_DEFAULT_BASE_PARAMS))
    detection: str = "pipeline"
    reconstruction: Optional[str] = None


#: The fourteen canonical cases (item 040 spec's case table, then item 150's
#: two, then item 166's split, then item 174's split_own_label, then item 175's crop_fov_si), in table
#: order.
CASE_RECIPE: List[_RecipeEntry] = [
    _RecipeEntry(
        case_id="clean_control",
        perturbation="identity",
        perturbation_params={},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="displace",
        perturbation="displace",
        # Item 177 (2026-09-24): mostly left-right -- 14 voxels right, 5
        # anterior on the 1 mm base. The magnitude is explicit so a change to
        # the operator's default cannot move this fixture; 14 L-R voxels is
        # the most the field of view admits with the 1-voxel inset.
        perturbation_params={"target_label": 22, "displacement_mm": 15.0, "ap_angle_deg": 20.0},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="fragment",
        perturbation="fragment",
        perturbation_params={"target_label": 22},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="inject_islands",
        perturbation="inject_islands",
        perturbation_params={"target_label": 22},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="relabel_swap",
        perturbation="relabel_swap",
        perturbation_params={"target_label": 21, "neighbour_label": 22},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="remove_level",
        perturbation="remove_level",
        perturbation_params={"target_label": 22},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="crop_at_border",
        perturbation="crop_at_border",
        perturbation_params={"target_label": 22, "face": "anterior"},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="sequence_break",
        perturbation="sequence_break",
        perturbation_params={},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="force_overlap",
        perturbation="force_overlap",
        perturbation_params={"target_label": 20, "neighbour_label": 21},
        detection="reconstructed_record",
        reconstruction="overlap_mask_stack",
    ),
    # Item 150 (2026-09-14): the two cases the signed-off taxonomy needed.
    # Case ids name the case's perturbation operator, like the cases above
    # (item 157 dropped their stale "modeN_" prefixes); the manifest's
    # failure_mode field is the authority.
    # Item 176 (2026-09-24): fuse_adjacent is the bridged, renumbered fuse --
    # one connected label over L3 + L4, with L5 renumbered 23 so the sequence
    # stays continuous. ``bridged`` is written explicitly so a later change of
    # the operator's default cannot move the committed fixture.
    _RecipeEntry(
        case_id="fuse_adjacent",
        perturbation="fuse",
        perturbation_params={"target_label": 22, "neighbour_label": 23, "bridged": True},
        detection="pipeline",
    ),
    _RecipeEntry(
        case_id="remove_level_relabel",
        perturbation="remove_level_relabel",
        perturbation_params={"target_label": 22},
        detection="pipeline",
    ),
    # Item 166 (2026-09-20): mode 3's first corpus case, converse of
    # fuse_adjacent above. Item 174 (2026-09-23) re-authored it as mode 3
    # sub-type (a): a caudal cap of label 23 (L4) holding 20 % of its voxels
    # is relabelled 24 (L5). The fraction is written explicitly so a later
    # change of the operator's default cannot move the committed fixture.
    _RecipeEntry(
        case_id="split",
        perturbation="split",
        perturbation_params={
            "target_label": 23,
            "neighbour_label": 24,
            "donated_fraction": 0.2,
        },
        detection="pipeline",
    ),
    # Item 174 (2026-09-23): mode 3 sub-type (b) -- the same cap under a
    # label of its own (23), with every cranial label shifted up one level.
    _RecipeEntry(
        case_id="split_own_label",
        perturbation="split_own_label",
        perturbation_params={"target_label": 23, "donated_fraction": 0.2},
        detection="pipeline",
    ),
    # Item 175 (2026-09-24): the S-I FOV crop -- the volume cut at the
    # inferior face through L5 (24), removing at least 65 % of its voxels.
    # A true crop: a smaller grid, so the case carries its own scan. Face and
    # fraction are written explicitly so a later default change cannot move
    # the committed fixture.
    _RecipeEntry(
        case_id="crop_fov_si",
        perturbation="crop_fov",
        perturbation_params={
            "target_label": 24,
            "face": "inferior",
            "removed_fraction": 0.65,
        },
        detection="pipeline",
    ),
]


# --------------------------------------------------------------------------- #
# CorpusCase -- in-memory representation of a built case
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CorpusCase:
    """One fully-built corpus case: metadata + images + the operator's
    Expectation. No disk I/O has happened yet."""

    case_id: str
    perturbation: str
    perturbation_params: Dict[str, Any]
    seed: int
    base: Dict[str, Any]
    detection: str
    reconstruction: Optional[str]
    scan_img: nib.Nifti1Image
    seg_img: nib.Nifti1Image
    expectation: Expectation


# --------------------------------------------------------------------------- #
# crop_to_grid (item 175)
# --------------------------------------------------------------------------- #


def crop_to_grid(img: nib.Nifti1Image, grid_img: nib.Nifti1Image) -> nib.Nifti1Image:
    """Return the sub-block of *img* on *grid_img*'s grid (item 175).

    The block is located from the two affines: ``o = inv(img.affine) @
    grid_img.affine[:, 3]`` is its start index and ``grid_img.shape`` its
    size. Returns *img* itself when the grids are identical (equal shape,
    ``np.allclose`` affines); otherwise a fresh image holding a copy of the
    data, *img*'s dtype and *grid_img*'s affine.

    Raises
    ------
    FacetInputError
        If the rotation/zoom blocks differ, the offset is not integral within
        1e-6, or the block leaves *img*'s grid.
    """
    shape =tuple(grid_img.shape[:3])
    if shape == tuple(img.shape[:3]) and np.allclose(img.affine, grid_img.affine):
        return img
    if not np.allclose(img.affine[:3, :3], grid_img.affine[:3, :3]):
        raise FacetInputError(
            "crop_to_grid: the two images' rotation/zoom blocks differ, so "
            "one grid is not a sub-grid of the other."
        )
    offset = (np.linalg.inv(img.affine) @ grid_img.affine[:, 3])[:3]
    start = np.round(offset).astype(int)
    if not np.allclose(offset, start, rtol=0.0, atol=1e-6):
        raise FacetInputError(
            f"crop_to_grid: the grid offset {offset.tolist()!r} is not an "
            "integral voxel index."
        )
    stop = start + np.asarray(shape)
    if np.any(start < 0) or np.any(stop > np.asarray(img.shape[:3])):
        raise FacetInputError(
            f"crop_to_grid: the block [{start.tolist()}, {stop.tolist()}) "
            f"leaves the source grid of shape {tuple(img.shape[:3])!r}."
        )
    block = np.asanyarray(img.dataobj)[
        start[0] : stop[0], start[1] : stop[1], start[2] : stop[2]
    ]
    # Explicit dtype: nibabel refuses an int64 array without it, and the
    # loaded-fixture images the test cohort builders pass are int64.
    return nib.Nifti1Image(
        np.array(block, copy=True),
        np.array(grid_img.affine, copy=True),
        dtype=block.dtype,
    )


# --------------------------------------------------------------------------- #
# build_corpus
# --------------------------------------------------------------------------- #


def build_corpus() -> List[CorpusCase]:
    """Build every canonical case in memory (no disk I/O).

    For each recipe entry: build the base clean spine, instantiate the
    registered operator with its explicit params, apply it (seeded) to the
    base segmentation, and assemble a :class:`CorpusCase` carrying the base
    scan, the perturbed segmentation, and the operator's ``Expectation`` --
    the single source of truth for the manifest's expected_* fields (AC17).
    """
    cases: List[CorpusCase] = []
    for entry in CASE_RECIPE:
        clean = build_clean_spine(**entry.base)
        operator_cls = get_perturbation(entry.perturbation)
        operator = operator_cls(**entry.perturbation_params)
        result = operator.apply(clean.seg_img, entry.seed)

        cases.append(
            CorpusCase(
                case_id=entry.case_id,
                perturbation=entry.perturbation,
                perturbation_params=dict(entry.perturbation_params),
                seed=entry.seed,
                base=dict(entry.base),
                detection=entry.detection,
                reconstruction=entry.reconstruction,
                # Item 175: the base scan on the case's own grid (the base
                # scan itself for every case that keeps the base grid).
                scan_img=crop_to_grid(clean.scan_img, result.labelmap),
                seg_img=result.labelmap,
                expectation=result.expectation,
            )
        )
    return cases


# --------------------------------------------------------------------------- #
# write_corpus
# --------------------------------------------------------------------------- #


def _save_deterministic(img: nib.Nifti1Image, path: Path) -> None:
    """Save *img* to *path* deterministically (byte-stable across runs).

    nibabel (verified: 5.3.3) writes gzip via a deterministic gzip wrapper
    (``mtime=0``), so plain ``nib.save`` already yields byte-identical output
    across successive calls for identical content -- see the item spec's
    Assumptions. Header fields that could vary by wall-clock time (e.g.
    ``regular``) are not touched by nibabel's writer, so no extra
    normalisation is required here.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(img, str(path))


def write_corpus(dest: Path) -> Path:
    """Materialise the corpus under *dest*.

    Writes one shared ``fixtures/base_scan.nii.gz`` (named by every case whose
    scan equals the first case's; a case on a different grid writes its own
    ``fixtures/<case_id>_scan.nii.gz`` -- item 175) and one
    ``fixtures/<case_id>_seg.nii.gz`` per case, plus ``dest/manifest.json``
    (fixture paths relative to *dest*). Deterministic: two successive calls
    (even into different directories) produce byte-identical output for
    identical content.

    Returns
    -------
    Path
        The written manifest path (``dest/manifest.json``).
    """
    dest = Path(dest)
    fixtures_dir = dest / FIXTURES_DIRNAME
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    cases = build_corpus()

    # Dedup contract (item 175 re-derived item 040's): a case whose scan is
    # array- and affine-equal to the first case's shares the one base scan;
    # any other case (a different grid) writes its own scan fixture.
    base_data = np.asanyarray(cases[0].scan_img.dataobj)
    base_affine = np.asarray(cases[0].scan_img.affine)

    base_scan_path = fixtures_dir / _BASE_SCAN_FIXTURE_NAME
    _save_deterministic(cases[0].scan_img, base_scan_path)

    manifest_cases: List[Dict[str, Any]] = []
    for case in cases:
        scan_data = np.asanyarray(case.scan_img.dataobj)
        if np.array_equal(scan_data, base_data) and np.array_equal(
            np.asarray(case.scan_img.affine), base_affine
        ):
            scan_fixture_name = _BASE_SCAN_FIXTURE_NAME
        else:
            scan_fixture_name = f"{case.case_id}_scan.nii.gz"
            _save_deterministic(case.scan_img, fixtures_dir / scan_fixture_name)

        seg_fixture_name = f"{case.case_id}_seg.nii.gz"
        seg_path = fixtures_dir / seg_fixture_name
        _save_deterministic(case.seg_img, seg_path)

        expectation_dict = case.expectation.to_dict()

        manifest_case = {
            "case_id": case.case_id,
            "failure_mode": expectation_dict["failure_mode"],
            "failure_mode_name": expectation_dict["failure_mode_name"],
            "condition": expectation_dict["condition"],
            "kind": expectation_dict["kind"],
            "detection": case.detection,
            "reconstruction": case.reconstruction,
            "perturbation": case.perturbation,
            "perturbation_params": case.perturbation_params,
            "seed": case.seed,
            "base": case.base,
            "scan_fixture": f"{FIXTURES_DIRNAME}/{scan_fixture_name}",
            "seg_fixture": f"{FIXTURES_DIRNAME}/{seg_fixture_name}",
            "expected_rule_ids": expectation_dict["expected_rule_ids"],
            "expected_labels": expectation_dict["expected_labels"],
            "expected_verdict": expectation_dict["expected_verdict"],
            "detail": expectation_dict["detail"],
        }
        manifest_cases.append(manifest_case)

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "generator": "segfacet.synth.corpus",
        "cases": manifest_cases,
    }

    manifest_path = dest / "manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    # Write raw bytes (rather than Path.write_text) so line endings are
    # exactly "\n" regardless of platform/Python version -- required for
    # byte-identical regeneration (AC16) on Windows, and Path.write_text's
    # newline= kwarg is only available on Python >= 3.10 (this project
    # targets 3.9+).
    manifest_path.write_bytes(manifest_text.encode("utf-8"))

    return manifest_path


# --------------------------------------------------------------------------- #
# load_manifest
# --------------------------------------------------------------------------- #


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    """Parse and return the manifest dict at *path* (default: the committed
    ``tests/corpus/manifest.json``)."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``python -m segfacet.synth.corpus [--out DIR]`` -- regenerate the corpus.

    Regenerates the fixtures + manifest under ``--out`` (default:
    :data:`CORPUS_DIR`). Returns ``0`` on success.
    """
    parser = argparse.ArgumentParser(
        prog="segfacet.synth.corpus",
        description="Regenerate the committed synthetic fixture corpus.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(CORPUS_DIR),
        help="Destination directory (default: the committed tests/corpus).",
    )
    args = parser.parse_args(argv)

    manifest_path = write_corpus(Path(args.out))
    print(f"Wrote corpus manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
