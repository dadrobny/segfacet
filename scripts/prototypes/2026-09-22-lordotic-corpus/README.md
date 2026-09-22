# Prototype: lordotic corpus base and re-authored operators (2026-09-22)

Provenance for the maintainer review of 2026-09-22 (`docs/aide/insights.md`,
entries dated 2026-09-22). **Imported by nothing, tested by nothing, and to be
absorbed into `src/segfacet/synth/` by the items that implement those
insights, then deleted** — not maintained here.

Run from the repo root with the project venv:

| Script | What it does |
|---|---|
| `lordotic_spine.py <out.nii.gz>` | The proposed clean-control base: L1–L5, 8 mm disc gap, per-level sagittal tilts −8/0/+8/+18/+35°, A-P centroid path the integral of the tilts, no lateral curve. Prints per-label voxel counts, extents, centroids. |
| `check_and_render.py <seg.nii.gz> <out.png>` | Runs a candidate base through `run_qc` (bundled default config), prints verdict, findings, per-label component count and nearest-other-label distance, spline offsets and spacings; renders it beside the committed `clean_control`. |
| `corpus_v2.py <out.png>` | The prototype corpus on that base: reuses the committed operators that still apply (`fragment`, `inject_islands`, `relabel_swap`, `remove_level`, `remove_level_relabel`, `sequence_break`) and authors locally the five changed ones — `displace_lr` (mostly L-R), `crop_inferior` (FOV cut losing 65 % of L5), `fuse` (bridged, renumbered), `split_to_neighbour` (20 % caudal cap of L4 → L5), `split_own_label` (same cap under its own label, labels above shifted up). Runs every case through `run_qc` and prints the measured firing per case; renders a 12-panel contact sheet, superior-aligned. |
| `corpus_sheet.py <out.png>` | The same contact sheet for the **committed** `tests/corpus/manifest.json` (sagittal + coronal max-label projections, voxels changed vs `clean_control` outlined). |

Measured on 2026-09-22 (`corpus_v2.py`): the base passes with zero findings;
`split_to_neighbour` fires `fragmentation.neighbour_contact` alone;
`split_own_label` fires `bounds` on the cap and — the defect the review
recorded — `coverage` on a "missing" T13 between T12 and L1; `fuse` and
`remove_level_relabel` fire nothing; `crop_inferior` fires `bounds` on the
7 719 mm³ L5 remnant while `border` suppresses the expected end.
