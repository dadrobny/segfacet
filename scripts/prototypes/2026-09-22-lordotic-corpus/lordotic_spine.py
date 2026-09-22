"""Prototype: a lordotic L1-L5 clean control -- rotated bodies on a curved path.

Same conventions as segfacet.synth.clean_gt (RAS-native, axis 0 = L-R,
axis 1 = P->A, axis 2 = I->S, ascending labels advance caudally), but:

* the inter-body gap is a disc height (8 mm) instead of 15 mm;
* each body is tilted about the L-R axis by a per-level sagittal angle
  (positive = anterior edge lower);
* the centroid path is the integral of those tilts, so the tilt is the
  tangent of the lordotic curve: L1 slightly posterior and tilted up, L2
  horizontal, L3-L5 increasingly tilted down and posterior.

Content is purely computed (no RNG).
"""
import math
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

BODY_LR, BODY_AP, BODY_SI = 30.0, 25.0, 25.0  # mm, as clean_gt
GAP_MM = 8.0            # disc height (was 15)
MARGIN_MM = 15.0
LABELS = (20, 21, 22, 23, 24)  # L1..L5
# Sagittal tilt per level, degrees; + = anterior edge lower ("downward").
TILT_DEG = (-8.0, 0.0, 8.0, 18.0, 35.0)


def centroids_mm():
    """(n, 3) centroids in mm relative to an origin fixed later by the margins."""
    n = len(LABELS)
    pitch = BODY_SI + GAP_MM
    z = np.array([(n - 1 - i) * pitch for i in range(n)])          # L1 highest S
    x = np.zeros(n)  # no lateral curve: scoliosis is not the base case
    y = np.zeros(n)
    for i in range(1, n):  # walk caudally: y drops by pitch * tan(mean tilt)
        mean_tilt = math.radians((TILT_DEG[i - 1] + TILT_DEG[i]) / 2)
        y[i] = y[i - 1] - pitch * math.tan(mean_tilt)
    return np.stack([x, y, z], axis=1)


def build(spacing=(1.0, 1.0, 1.0)):
    c = centroids_mm()
    # rotated half-extents (worst case over levels) so the margins hold
    half = np.array([BODY_LR / 2, 0.0, 0.0])
    t = np.radians(np.abs(TILT_DEG)).max()
    half[1] = (BODY_AP * math.cos(t) + BODY_SI * math.sin(t)) / 2
    half[2] = (BODY_AP * math.sin(t) + BODY_SI * math.cos(t)) / 2
    lo = c.min(0) - half - MARGIN_MM
    hi = c.max(0) + half + MARGIN_MM
    c = c - lo
    shape = tuple(int(math.ceil(v / s)) for v, s in zip(hi - lo, spacing))
    grid = np.indices(shape).astype(float)  # voxel centres in mm
    gx, gy, gz = (grid[k] * spacing[k] for k in range(3))
    seg = np.zeros(shape, dtype=np.uint16)
    for lab, (cx, cy, cz), tilt in zip(LABELS, c, TILT_DEG):
        th = math.radians(tilt)
        y, z = gy - cy, gz - cz
        u = y * math.cos(th) - z * math.sin(th)   # along the body's A-P axis
        v = y * math.sin(th) + z * math.cos(th)   # along the body's S-I axis
        inside = (np.abs(gx - cx) <= BODY_LR / 2) & (np.abs(u) <= BODY_AP / 2) & (np.abs(v) <= BODY_SI / 2)
        seg[inside] = lab
    affine = np.diag([*spacing, 1.0])
    return nib.Nifti1Image(seg, affine), c


if __name__ == "__main__":
    out = Path(sys.argv[1])
    img, c = build()
    nib.save(img, out)
    seg = np.asarray(img.dataobj)
    print("shape", seg.shape)
    for lab, cen in zip(LABELS, c):
        m = seg == lab
        idx = np.nonzero(m)
        print(lab, "voxels", int(m.sum()), "extent", [int(i.max() - i.min() + 1) for i in idx], "centroid", np.round(cen, 1))
