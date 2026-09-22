"""Pipeline check + sagittal/coronal rendering of a candidate clean control,
side by side with the committed clean_control."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap
from scipy import ndimage

from segfacet.pipeline import run_qc
from segfacet.synth.regression import bundled_default_config

cand = Path(sys.argv[1])
out = Path(sys.argv[2])
committed = Path("tests/corpus/fixtures/clean_control_seg.nii.gz")

# --- pipeline verdict + min inter-label gap ---------------------------------
img = nib.load(str(cand))
seg = np.asarray(img.dataobj).astype(int)
res, block = run_qc(img, bundled_default_config())
print("verdict:", res.verdict.overall.label, "| findings:", [(f.rule_id, f.message[:60]) for f in res.findings])
for lab in np.unique(seg)[1:]:
    ncomp = ndimage.label(seg == lab)[1]
    dist = ndimage.distance_transform_edt(seg != lab)
    other = (seg != 0) & (seg != lab)
    print(f"label {lab}: components={ncomp} nearest other label={dist[other].min():.1f} mm")
s3 = block.get("stage3", {})
offs = s3.get("per_label_offsets", [])
print("spline offsets mm:", [round(o["offset_mm"], 2) for o in offs])
print("spacings mm:", [round(v, 1) for v in s3.get("spacing_consistency", {}).get("spacings_mm", [])])

# --- rendering ------------------------------------------------------------------
cmap = ListedColormap(["black"] + [plt.cm.tab10(i) for i in range(5)])
fig, axes = plt.subplots(1, 4, figsize=(14, 8))
for j, (path, name) in enumerate(((committed, "committed clean_control"), (cand, cand.stem))):
    a = np.asarray(nib.load(str(path)).dataobj).astype(int)
    a = np.where(a > 0, a - 19, 0)
    for k, (proj, lab) in enumerate(((a.max(0).T, "sagittal: posterior ← → anterior"), (a.max(1).T, "coronal: left ← → right"))):
        ax = axes[2 * j + k]
        ax.imshow(proj, cmap=cmap, vmin=0, vmax=5, origin="lower", interpolation="nearest", aspect="equal")
        ax.set_title(f"{name}\n{lab}", fontsize=9)
        ax.set_xlabel("mm"), ax.set_ylabel("S-I mm")
fig.tight_layout()
fig.savefig(out, dpi=100)
print("wrote", out)
