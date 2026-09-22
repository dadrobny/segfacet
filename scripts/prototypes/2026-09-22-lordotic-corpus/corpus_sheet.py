"""Contact sheet of the committed geometric corpus: sagittal + coronal slice per
case, taken through the plane where the case differs most from clean_control,
with the changed voxels outlined in red."""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap

root = Path("tests/corpus")
out = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
cases = manifest["cases"] if isinstance(manifest, dict) else manifest
load = lambda p: np.asarray(nib.load(str(p)).dataobj).astype(int)
clean = load(root / "fixtures" / "clean_control_seg.nii.gz")

labels = sorted(set(np.unique(clean)) | {25, 28})
cmap = ListedColormap(["black"] + [plt.cm.tab10(i) for i in range(9)])
lut = {lab: i for i, lab in enumerate(sorted(set(labels) - {0}), start=1)}


def idx(a):
    o = np.zeros_like(a)
    for lab in np.unique(a):
        if lab:
            o[a == lab] = lut.setdefault(int(lab), (len(lut) % 9) + 1)
    return o


fig, axes = plt.subplots(4, 6, figsize=(18, 20))
for k, case in enumerate(cases):
    seg = load(root / case["seg_fixture"])
    diff = (seg != clean) if seg.shape == clean.shape else np.zeros(seg.shape, bool)
    # max-label projections: the fixtures are axis-aligned blocks, so a projection
    # loses nothing and needs no slice selection (an island is never missed)
    r, c = divmod(k, 6)
    for row, img, d, view in (
        (2 * r, seg.max(0).T, diff.any(0).T, "sagittal projection (A-P x S-I)"),
        (2 * r + 1, seg.max(1).T, diff.any(1).T, "coronal projection (L-R x S-I)"),
    ):
        ax = axes[row, c]
        ax.imshow(idx(img), cmap=cmap, vmin=0, vmax=9, origin="lower", interpolation="nearest")
        if d.any():
            ax.contour(d, levels=[0.5], colors="red", linewidths=1.2)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlabel(view, fontsize=8)
        if row % 2 == 0:
            ax.set_title(
                f"{case['case_id']}\nmode {case.get('failure_mode')} · fires: "
                f"{', '.join(case.get('expected_rule_ids', [])) or '—'}",
                fontsize=10,
            )
for ax in axes.ravel():
    if not ax.images:
        ax.axis("off")
fig.suptitle("SegFACET geometric corpus — red outline = voxels changed vs clean_control", fontsize=14)
fig.tight_layout()
fig.savefig(out, dpi=90)
print(out, len(cases), sorted(lut))
