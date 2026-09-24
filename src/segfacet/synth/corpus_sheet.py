"""Committed contact sheet of the geometric corpus (item 178).

Absorbs ``scripts/prototypes/2026-09-22-lordotic-corpus/corpus_sheet.py``
(now deleted), fixing two defects measured against the 2026-09-24, 14-case
corpus: the prototype's grid was fixed at 4 x 6 axes (raises ``IndexError``
past 12 cases) and it blanked the outline of a case whose grid differs from
``clean_control``'s instead of placing it. The new generator computes its
layout from the case count and places an off-grid case on ``clean_control``'s
grid at the voxel offset its affine gives before comparing.

Regenerate the committed sheet (``docs/aide/corpus_sheet.png``) with::

    python -m segfacet.synth.corpus_sheet

PNG bytes are not compared anywhere: matplotlib's PNG output depends on the
matplotlib/FreeType/zlib versions in use, so it is not reproducible across
platforms. Two things are checked instead: the panel data (projections and
changed-voxel masks, pure NumPy, checked against the committed fixtures) and
an input digest -- the SHA-256 of the committed manifest's bytes followed by
each case's seg-fixture bytes in manifest order -- stored in the written
PNG's ``Source`` text chunk as ``"sha256:" + <hex digest>``, so a corpus
change that is not followed by a regeneration is caught (see
:func:`input_digest`).
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from segfacet.synth.corpus import MANIFEST_PATH, crop_to_grid, load_manifest

__all__ = [
    "SHEET_PATH",
    "SheetPanel",
    "sheet_panels",
    "input_digest",
    "render_sheet",
    "main",
]

#: The committed sheet: <repo>/docs/aide/corpus_sheet.png.
SHEET_PATH: Path = Path(__file__).resolve().parents[3] / "docs" / "aide" / "corpus_sheet.png"

#: Axes columns per row pair (one sagittal row above one coronal row).
_COLUMNS: int = 6


@dataclass(frozen=True)
class SheetPanel:
    """One case's sagittal/coronal panel pair, already transposed for display
    (rows run inferior -> superior)."""

    case_id: str
    sagittal: np.ndarray
    coronal: np.ndarray
    sagittal_changed: np.ndarray
    coronal_changed: np.ndarray


def sheet_panels(manifest_path: Path = MANIFEST_PATH) -> list:
    """Build one :class:`SheetPanel` per manifest case, in manifest order."""
    import nibabel as nib

    manifest = load_manifest(manifest_path)
    cases = manifest["cases"]

    clean_entry = next(c for c in cases if c["case_id"] == "clean_control")
    clean_img = nib.load(str(manifest_path.parent / clean_entry["seg_fixture"]))

    panels = []
    for case in cases:
        case_path = manifest_path.parent / case["seg_fixture"]
        case_img = nib.load(str(case_path))
        # crop_to_grid: raises FacetInputError for a case that is not an
        # integral sub-grid of clean_control, instead of rendering misaligned.
        crop_to_grid(clean_img, case_img)
        placed = _place_case_on_clean_grid(clean_img, case_img)
        changed = placed != np.asanyarray(clean_img.dataobj)
        panels.append(
            SheetPanel(
                case_id=case["case_id"],
                sagittal=placed.max(axis=0).T,
                coronal=placed.max(axis=1).T,
                sagittal_changed=changed.any(axis=0).T,
                coronal_changed=changed.any(axis=1).T,
            )
        )
    return panels


def _place_case_on_clean_grid(clean_img, case_img) -> np.ndarray:
    """The AC2 placement formula: start = round(inv(clean.affine) @
    case.affine[:, 3])[:3], which is (0, 0, 0) for a case on the same grid."""
    clean_data = np.asanyarray(clean_img.dataobj)
    case_data = np.asanyarray(case_img.dataobj)
    start = np.round(
        (np.linalg.inv(clean_img.affine) @ case_img.affine[:, 3])[:3]
    ).astype(int)
    placed = np.zeros(clean_data.shape, dtype=case_data.dtype)
    stop = start + np.asarray(case_data.shape[:3])
    placed[start[0] : stop[0], start[1] : stop[1], start[2] : stop[2]] = case_data
    return placed


def input_digest(manifest_path: Path = MANIFEST_PATH) -> str:
    """SHA-256 hex digest of the committed manifest's bytes followed by each
    case's seg-fixture bytes, in manifest order (AC6/AC7)."""
    manifest_path = Path(manifest_path)
    manifest = load_manifest(manifest_path)
    h = hashlib.sha256()
    h.update(manifest_path.read_bytes())
    for case in manifest["cases"]:
        fixture_path = manifest_path.parent / case["seg_fixture"]
        h.update(fixture_path.read_bytes())
    return h.hexdigest()


def render_sheet(out: Path = SHEET_PATH, manifest_path: Path = MANIFEST_PATH):
    """Render the contact sheet and save it to *out*. Returns the ``Figure``.

    Object-oriented ``Figure`` API, no pyplot, so no global figure registry
    is kept. Layout: :data:`_COLUMNS` columns, ``2 * ceil(N / _COLUMNS)``
    rows -- one sagittal row above one coronal row per row of cases. A voxel
    is coloured by its label value from one fixed table shared by every
    panel, so a relabel reads as a colour change.
    """
    import math

    from matplotlib.figure import Figure

    panels = sheet_panels(manifest_path)
    manifest = load_manifest(manifest_path)
    cases_by_id = {c["case_id"]: c for c in manifest["cases"]}
    n = len(panels)
    n_case_rows = math.ceil(n / _COLUMNS)
    n_rows = 2 * n_case_rows

    fig = Figure(figsize=(3 * _COLUMNS, 3.4 * n_rows))
    axes = fig.subplots(n_rows, _COLUMNS, squeeze=False)

    cmap = _label_colormap()

    for i, panel in enumerate(panels):
        case_row, col = divmod(i, _COLUMNS)
        case = cases_by_id[panel.case_id]
        title = (
            f"{case['case_id']}\n"
            f"{case.get('kind')} / {case.get('failure_mode')}"
            + (f" ({case['condition']})" if case.get("condition") else "")
            + "\n"
            + (", ".join(case.get("expected_rule_ids", [])) or "-")
        )
        for row_offset, img, mask in (
            (0, panel.sagittal, panel.sagittal_changed),
            (1, panel.coronal, panel.coronal_changed),
        ):
            ax = axes[2 * case_row + row_offset, col]
            ax.imshow(
                cmap(img % 10),
                origin="lower",
                interpolation="nearest",
            )
            if mask.any():
                ax.contour(mask, levels=[0.5], colors="red", linewidths=1.2)
            ax.set_xticks([])
            ax.set_yticks([])
            if row_offset == 0:
                ax.set_title(title, fontsize=8)

    for ax in axes.ravel():
        if not ax.images:
            ax.axis("off")

    fig.tight_layout()

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out,
        dpi=90,
        metadata={"Software": None, "Source": "sha256:" + input_digest(manifest_path)},
    )
    return fig


def _label_colormap():
    """One fixed table mapping a label value's ``value % 10`` to a colour,
    background (0) black, shared by every panel so a relabel reads as a
    colour change rather than depending on a per-run lookup table."""
    from matplotlib.colors import ListedColormap
    from matplotlib import colormaps

    tab10 = colormaps["tab10"]
    colours = ["black"] + [tab10(i) for i in range(9)]
    return ListedColormap(colours)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """``python -m segfacet.synth.corpus_sheet [--out PATH]`` -- regenerate
    the committed contact sheet. Returns ``0`` on success."""
    parser = argparse.ArgumentParser(
        prog="segfacet.synth.corpus_sheet",
        description="Regenerate the committed geometric-corpus contact sheet.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(SHEET_PATH),
        help="Destination PNG path (default: the committed docs/aide/corpus_sheet.png).",
    )
    args = parser.parse_args(argv)

    render_sheet(out=Path(args.out))
    print(f"Wrote corpus sheet to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
