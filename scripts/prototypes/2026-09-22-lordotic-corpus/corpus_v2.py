"""Prototype geometric corpus on the lordotic base (maintainer review 2026-09-22).

Reuses the committed operators that still apply; the five re-authored ones are
local functions over the array. Every case is run through run_qc and the
measured firing set is printed in its panel title.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).parent))
from lordotic_spine import build  # noqa: E402

from segfacet.pipeline import run_qc  # noqa: E402
from segfacet.synth.component_shape import FragmentPerturbation, InjectIslandsPerturbation  # noqa: E402
from segfacet.synth.coverage_border_overlap import RemoveLevelPerturbation, RemoveLevelRelabelPerturbation  # noqa: E402
from segfacet.synth.identity_ordering_alignment import RelabelSwapPerturbation, SequenceBreakPerturbation  # noqa: E402
from segfacet.synth.regression import bundled_default_config  # noqa: E402

L1, L2, L3, L4, L5 = 20, 21, 22, 23, 24
base_img, _ = build()
base = np.asarray(base_img.dataobj).astype(np.uint16)
aff = base_img.affine


def img(a):
    return nib.Nifti1Image(a.astype(np.uint16), aff)


def via(op):  # committed operator, seed 0
    return np.asarray(op.apply(base_img, 0).labelmap.dataobj).astype(np.uint16)


# --- re-authored operators ---------------------------------------------------
def displace_lr(a, lab=L3, dx=13, dy=3):
    """Mostly left-right shift of one body (was 13/13 along both axes)."""
    out = a.copy()
    out[a == lab] = 0
    out[np.roll(np.roll(a == lab, dx, 0), dy, 1)] = lab
    return out


def crop_inferior(a, lab=L5, lost=0.65):
    """Cut the FOV so `lost` of L5's voxels are gone; the remnant touches the face."""
    zcut = int(np.quantile(np.nonzero(a == lab)[2], lost))
    return a[:, :, zcut:]


def fuse(a, upper=L3, lower=L4):
    """Bridge the disc gap column-wise under the upper label, then renumber
    every caudal label up by one so the sequence stays continuous."""
    out = a.copy()
    up, lo = a == upper, a == lower
    cols = up.any(2) & lo.any(2)
    for x, y in zip(*np.nonzero(cols)):
        z_lo = np.nonzero(lo[x, y])[0].max()
        z_up = np.nonzero(up[x, y])[0].min()
        out[x, y, z_lo + 1 : z_up] = upper
    for lab in sorted(l for l in np.unique(a) if l > lower):
        out[a == lab] = lab - 1
    out[lo] = upper
    return out


def caudal_cap(a, lab, frac=0.2):
    """Mask of the caudal `frac` of a body, cut by a horizontal plane."""
    m = a == lab
    z = np.nonzero(m)[2]
    zcut = np.quantile(z, frac)
    cap = m.copy()
    cap[:, :, int(np.ceil(zcut)) :] = False
    return cap


def split_to_neighbour(a, lab=L4, frac=0.2):
    """~20% of L4 (below an S-I level) relabelled as L5: mode 3, sub-type (a)."""
    out = a.copy()
    out[caudal_cap(a, lab, frac)] = lab + 1
    return out


def split_own_label(a, lab=L4, frac=0.2):
    """Same portion gets its own label; L5 kept, every label from the split
    part upward shifts by one (split part -> L4, rest of L4 -> L3, ... L1 -> T12)."""
    out = a.copy()
    cap = caudal_cap(a, lab, frac)
    for l in sorted(l for l in np.unique(a) if 0 < l <= lab):
        out[a == l] = l - 1
    out[cap] = lab
    return out


cases = [
    ("clean_control", "0", base),
    ("displace (L-R)", "condition", displace_lr(base)),
    ("fragment (parked)", "1", via(FragmentPerturbation(target_label=L3))),
    ("inject_islands", "4", via(InjectIslandsPerturbation(target_label=L3))),
    ("relabel_swap", "9", via(RelabelSwapPerturbation())),
    ("remove_level", "6", via(RemoveLevelPerturbation(target_label=L3))),
    ("remove_level_relabel", "6", via(RemoveLevelRelabelPerturbation(target_label=L3))),
    ("sequence_break", "9", via(SequenceBreakPerturbation())),
    ("crop_inferior (FOV cut)", "condition", crop_inferior(base)),
    ("fuse (bridged, renumbered)", "2", fuse(base)),
    ("split -> neighbour", "3a", split_to_neighbour(base)),
    ("split -> own label", "3b", split_own_label(base)),
]

cfg = bundled_default_config()
cmap = ListedColormap(["black"] + [plt.cm.tab10(i) for i in range(10)])
lut = {19: 6, 20: 1, 21: 2, 22: 3, 23: 4, 24: 5, 28: 7}
names = {19: "T12", 20: "L1", 21: "L2", 22: "L3", 23: "L4", 24: "L5", 28: "T13"}
fig, axes = plt.subplots(2, 12, figsize=(30, 11))
for k, (name, mode, a) in enumerate(cases):
    res, _ = run_qc(img(a), cfg)
    fired = sorted({f.rule_id for f in res.findings})
    dets = sorted({f"{f.rule_id}.{f.detector_id}" for f in res.findings})
    print(f"{name:28s} mode {mode:9s} verdict={res.verdict.overall.label:18s} {dets}")
    idx = np.vectorize(lambda v: lut.get(int(v), 8 if v else 0))(a)
    same = a.shape == base.shape
    diff = (a != base) if same else np.zeros(a.shape, bool)
    for row, proj, d in ((0, idx.max(0).T, diff.any(0).T), (1, idx.max(1).T, diff.any(1).T)):
        ax = axes[row, k]
        # superior-aligned: a cropped (shorter) array keeps its top at the base's top
        top = base.shape[2]
        ext = (0, proj.shape[1], top - proj.shape[0], top)
        ax.imshow(proj, cmap=cmap, vmin=0, vmax=10, origin="lower", interpolation="nearest", extent=ext)
        if d.any():
            ax.contour(d, levels=[0.5], colors="red", linewidths=1.0, extent=ext)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_xlim(0, base.shape[1] if row == 0 else base.shape[0]), ax.set_ylim(0, base.shape[2])
    axes[0, k].set_title(f"{name}\nmode {mode}\nfires: {', '.join(fired) or '—'}", fontsize=9)
axes[0, 0].set_ylabel("sagittal (P→A × I→S)"), axes[1, 0].set_ylabel("coronal (L→R × I→S)")
fig.legend(
    handles=[Patch(color=cmap(lut[l]), label=f"{names[l]} ({l})") for l in (19, 20, 21, 22, 23, 24, 28)],
    loc="lower center", ncol=7, fontsize=10, frameon=False,
)
fig.suptitle("Prototype corpus on the lordotic base — red outline = voxels changed vs clean_control (same-shape cases only)", fontsize=13)
fig.tight_layout(rect=(0, 0.04, 1, 1))
out = Path(sys.argv[1])
fig.savefig(out, dpi=80)
print("wrote", out)
