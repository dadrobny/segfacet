"""Parametric clean-GT (positive-control) spine builder (item 036).

Builds a multi-vertebra **instance label map** -- ordered, plausibly-spaced,
single-component vertebra bodies stacked along a smooth spinal curve -- such
that the real Stage 4 pipeline (:func:`segfacet.pipeline.run_qc`, under the
bundled default config) judges it ``pass`` with zero findings. This is the
positive-control base every Stage 5 perturbation (items 037-039) starts from.

Axis convention (item 116): the **affine is the source of truth**, not a
fixed axis order. ``_affine_from_spacing`` emits a plain positive diagonal
affine, which ``nibabel.aff2axcodes`` resolves to RAS axcodes -- array axis 0
runs left->right, axis 1 posterior->anterior, axis 2 inferior->superior. This
generator places bodies to match that affine's own claim (rather than
contradicting it, as the pre-116 axis-0-stacking layout did): bodies are
stacked along **axis 2** (superior-inferior), axis 0 is left-right, axis 1 is
anterior-posterior. Loading a generated fixture through :mod:`segfacet.io`
(which reorients every volume to RAS) is therefore an array-identity
operation -- the fixture is already RAS-native.

Stacking direction (item 143): ascending labels advance caudally
(descending S), matching real VerSe input read through :mod:`segfacet.io`.
The ``i``-th ascending label occupies slot ``n - 1 - i`` along axis 2, not
slot ``i`` -- so ``labels[0]`` (the most cranial anatomical level, e.g. L1)
sits at the *highest* S and ``labels[-1]`` (e.g. L5) at the *lowest*. The
label order and the array-axis-2 slot order run opposite each other.

Design -- a lordotic L1-L5 (item 173; the maintainer decision is the ``gap``
entry in ``docs/aide/insights.md`` dated 2026-09-22, "maintainer decision on
the geometric corpus base"):

* Each body is a 30 (L-R) x 25 (A-P) x 25 (S-I) mm box sized in **physical
  mm**, rotated about the L-R axis by its level's sagittal tilt: L1 -8 deg,
  L2 0 deg, L3 +8 deg, L4 +18 deg, L5 +35 deg (positive = anterior edge
  lower). The tilt is looked up by canonical level name, so a partial lumbar
  span keeps its levels' own tilts; every non-lumbar level (cervical,
  thoracic) is untilted. A voxel belongs to a body iff its centre
  (``index * spacing``, the affine's own mapping) lies inside the rotated
  box, so ``voxel_counts`` is counted from the array.
* Bodies are separated by an 8 mm gap (a disc height) along axis 2 (the
  stacking axis; disjoint -> no overlap, single component each), i.e. a
  33 mm S-I pitch, and inset from all six faces by a margin of at least one
  voxel (``max(1, ceil(15 mm / spacing))`` voxels -- no border contact at any
  spacing).
* The A-P centroid path is the integral of the tilts: walking caudally, each
  step moves A-P by the S-I step times the tangent of the mean of the two
  bodies' tilts, so each tilt is the tangent of the lordotic curve.
* There is no lateral curve by default (scoliosis is not the base case);
  ``curve_amplitude_mm`` still adds a non-negative left-right hump,
  ``amplitude * sin(pi * i / (n - 1))``, for callers that want per-subject
  variability.
* Content is purely computed (no RNG) -- deterministic (AC24).

The default level span is lumbar L1-L5 (labels 20-24): a canonically-
contiguous run with no interior transitional vertebra, so
``relationships.missing_levels`` stays empty and ``coverage`` stays silent
(see the "transitional-vertebra trap" in the item spec). Any configured
``levels`` must likewise be a contiguous run within a single anatomical group
-- crossing the T12->L1 or L5->S junction interleaves the transitional
vertebrae T13/L6 in :data:`segfacet.labels.CANONICAL_ORDER` and would (correctly)
trip the missing-interior-level coverage check; :func:`build_clean_spine`
raises :class:`~segfacet.io.FacetInputError` for such a span rather than silently
emitting a coverage-flagging map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import nibabel as nib

from segfacet.io import FacetInputError
from segfacet.labels import CANONICAL_ORDER, LabelConvention

__all__ = [
    "DEFAULT_LEVELS",
    "CleanSpine",
    "build_clean_spine",
]

# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

#: Default level span -- lumbar L1-L5 (labels 20-24 under the default
#: convention): a canonically-contiguous run with no interior transitional
#: vertebra (see the module docstring's "transitional-vertebra trap" note).
DEFAULT_LEVELS: Tuple[str, ...] = ("L1", "L2", "L3", "L4", "L5")

# Per-body physical size in mm, named by anatomical direction (not by array
# axis -- see the module docstring: array axis 0 is left-right, axis 1
# anterior-posterior, axis 2 superior-inferior). Chosen to sit comfortably inside
# every level group's DEFAULT_BOUNDS (cervical/thoracic/lumbar)
# simultaneously: volume 25*30*25 = 18750 mm^3 (cervical [3000,35000],
# thoracic [5000,70000], lumbar [8000,120000]); each extent axis is likewise
# inside every group's per-axis range.
_BODY_SIZE_SI_MM: float = 25.0
_BODY_SIZE_LR_MM: float = 30.0
_BODY_SIZE_AP_MM: float = 25.0

# Inter-body gap along the stacking (superior-inferior) axis (mm) -- a disc
# height (item 173; was 15 mm). Keeps bodies disjoint at every tilt.
_GAP_MM: float = 8.0

# Margin from every one of the six FOV faces (mm), rounded up to whole voxels
# and never less than one voxel -- keeps every body strictly inside the
# volume (no border contact) at any spacing.
_MARGIN_MM: float = 15.0

# Default lateral arc amplitude (mm): none -- scoliosis is not the base case
# (item 173).
_DEFAULT_CURVE_AMPLITUDE_MM: float = 0.0

# Sagittal tilt per canonical level name, degrees about the L-R axis;
# positive = anterior edge lower. The maintainer's lordosis table
# (docs/aide/insights.md, 2026-09-22); levels it does not name are untilted.
_TILT_DEG: Dict[str, float] = {
    "L1": -8.0,
    "L2": 0.0,
    "L3": 8.0,
    "L4": 18.0,
    "L5": 35.0,
}


# --------------------------------------------------------------------------- #
# CleanSpine dataclass
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CleanSpine:
    """A synthesised positive-control spine: a scan + instance label map pair.

    Attributes
    ----------
    scan_img:
        A matching deterministic intensity volume (same shape/affine as
        ``seg_img``), so the pair can be driven through ``segfacet run`` (item
        035/010) end-to-end.
    seg_img:
        The instance label map (integer dtype) -- the actual positive
        control every Stage 4 rule must judge clean.
    labels:
        Present integer labels, ascending.
    level_names:
        Anatomical names, parallel to ``labels``.
    spacing:
        Voxel spacing (sx, sy, sz) in mm.
    shape:
        Voxel-grid shape (nx, ny, nz).
    voxel_counts:
        ``{label: n_voxels}`` for every present label.
    """

    scan_img: nib.Nifti1Image
    seg_img: nib.Nifti1Image
    labels: Tuple[int, ...]
    level_names: Tuple[str, ...]
    spacing: Tuple[float, float, float]
    shape: Tuple[int, int, int]
    voxel_counts: Dict[int, int]


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _affine_from_spacing(spacing: Tuple[float, float, float]) -> np.ndarray:
    """A minimal diagonal RAS-ish affine with ``spacing`` on the diagonal."""
    sx, sy, sz = (float(s) for s in spacing)
    return np.diag([sx, sy, sz, 1.0]).astype(np.float64)


def _validate_span(levels: Sequence[str], convention: LabelConvention) -> Tuple[Tuple[int, ...], Tuple[str, ...]]:
    """Resolve ``levels`` to (labels, level_names), validating the span.

    Raises
    ------
    FacetInputError
        If a level name is unrecognised, or the span is not a canonically
        contiguous run (i.e. it would interleave a transitional vertebra or
        otherwise skip an entry of ``CANONICAL_ORDER``).
    """
    if not levels:
        raise FacetInputError(
            "build_clean_spine requires at least one level name; received an "
            "empty 'levels' sequence."
        )

    rank_of = {name: i for i, name in enumerate(CANONICAL_ORDER)}

    ranks = []
    for name in levels:
        rank = rank_of.get(str(name).strip().upper())
        if rank is None:
            raise FacetInputError(
                f"Unrecognised level name {name!r} in build_clean_spine(levels=...). "
                f"Known canonical level names: {list(CANONICAL_ORDER)}."
            )
        ranks.append(rank)

    for prev, cur in zip(ranks, ranks[1:]):
        if cur != prev + 1:
            raise FacetInputError(
                "build_clean_spine(levels=...) must be a canonically-contiguous "
                f"run with no gaps -- {levels!r} skips over "
                f"{CANONICAL_ORDER[prev + 1:cur]!r} in CANONICAL_ORDER (this "
                "would interleave a transitional vertebra or otherwise "
                "produce an incorrect 'missing interior level' coverage "
                "finding). Use a pure cervical, thoracic, or lumbar run."
            )

    labels = []
    level_names = []
    for name in levels:
        canonical_name = CANONICAL_ORDER[rank_of[str(name).strip().upper()]]
        value = convention.value_of(canonical_name)
        if value is None:
            raise FacetInputError(
                f"Level {canonical_name!r} (requested as {name!r}) has no "
                "integer label in the supplied LabelConvention."
            )
        labels.append(value)
        level_names.append(canonical_name)

    return tuple(labels), tuple(level_names)


# --------------------------------------------------------------------------- #
# Builder
# --------------------------------------------------------------------------- #


def build_clean_spine(
    *,
    levels: Sequence[str] = DEFAULT_LEVELS,
    spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    convention: Optional[LabelConvention] = None,
    curve_amplitude_mm: float = _DEFAULT_CURVE_AMPLITUDE_MM,
) -> CleanSpine:
    """Build a deterministic, plausibly-spaced positive-control spine.

    Item 143: ascending labels advance caudally (descending S) along the
    stacking axis (axis 2), matching real VerSe input read through
    :mod:`segfacet.io` -- the label order and the array-axis-2 slot order
    run opposite each other.

    Item 173 (a lordotic base; ``docs/aide/insights.md``, 2026-09-22): each
    30 x 25 x 25 mm body is rotated about the L-R axis by its level's
    sagittal tilt (L1 -8, L2 0, L3 +8, L4 +18, L5 +35 deg; positive =
    anterior edge lower; non-lumbar levels are untilted), bodies sit 8 mm
    apart along S-I (a 33 mm pitch), and the A-P centroid path is the
    integral of the tilts -- each caudal step moves A-P by the S-I step
    times the tangent of the two bodies' mean tilt. A voxel belongs to a
    body iff its centre lies inside the rotated box; every face keeps at
    least one empty voxel.

    Parameters
    ----------
    levels:
        Anatomical level names in head-to-tail order, e.g.
        ``("L1", ..., "L5")``. Must be a canonically-contiguous run within a
        single anatomical group (pure cervical / thoracic / lumbar) -- see
        the module docstring's "transitional-vertebra trap" note.
    spacing:
        Voxel spacing (sx, sy, sz) in mm. Body sizing accounts for spacing so
        the physical volume/extents stay inside the default rule bounds
        regardless of (an)isotropy.
    convention:
        The :class:`~segfacet.labels.LabelConvention` to resolve level names to
        integer labels. Defaults to :meth:`LabelConvention.default`.
    curve_amplitude_mm:
        Peak lateral (left-right) displacement of the smooth centroid arc, in
        mm. ``0.0`` (the default) yields no lateral curve.

    Returns
    -------
    CleanSpine

    Raises
    ------
    segfacet.io.FacetInputError
        If a level name is unrecognised or the span is not canonically
        contiguous within one anatomical group.
    """
    if convention is None:
        convention = LabelConvention.default()

    labels, level_names = _validate_span(levels, convention)
    n = len(labels)

    # sx/sy/sz are per-array-axis spacings (axis 0/1/2 respectively -- the
    # order header.get_zooms() and the affine diagonal both use). Per the
    # module docstring's RAS-native convention: axis 0 = left-right, axis 1 =
    # anterior-posterior, axis 2 = superior-inferior (the stacking axis).
    sx, sy, sz = (float(s) for s in spacing)
    spacing_arr = np.array([sx, sy, sz])

    tilts_rad = [math.radians(_TILT_DEG.get(name, 0.0)) for name in level_names]
    amplitude = max(0.0, float(curve_amplitude_mm))

    # Centroids in mm, relative to an origin fixed below. Ascending labels
    # advance caudally (descending S): the i-th ascending label occupies slot
    # n - 1 - i along the stacking axis (item 143), at a pitch of one body
    # plus one disc gap. The A-P path is the integral of the tilts: walking
    # caudally, y drops by pitch * tan(mean of the two bodies' tilts).
    pitch = _BODY_SIZE_SI_MM + _GAP_MM
    centroids = np.zeros((n, 3))
    for i in range(n):
        frac = (i / (n - 1)) if n > 1 else 0.0
        centroids[i, 0] = amplitude * math.sin(math.pi * frac)
        centroids[i, 2] = (n - 1 - i) * pitch
        if i > 0:
            mean_tilt = (tilts_rad[i - 1] + tilts_rad[i]) / 2.0
            centroids[i, 1] = centroids[i - 1, 1] - pitch * math.tan(mean_tilt)

    # Worst-case rotated half-extent over the span's levels, per axis.
    t_max = max(abs(t) for t in tilts_rad)
    half = np.array(
        [
            _BODY_SIZE_LR_MM / 2.0,
            (_BODY_SIZE_AP_MM * math.cos(t_max) + _BODY_SIZE_SI_MM * math.sin(t_max)) / 2.0,
            (_BODY_SIZE_AP_MM * math.sin(t_max) + _BODY_SIZE_SI_MM * math.cos(t_max)) / 2.0,
        ]
    )

    # Margin: at least one whole voxel per face at any spacing (item 173 A3).
    margin_vox = np.array([max(1, math.ceil(_MARGIN_MM / s)) for s in (sx, sy, sz)])
    lo = centroids.min(axis=0) - half - margin_vox * spacing_arr
    hi = centroids.max(axis=0) + half + margin_vox * spacing_arr
    centroids = centroids - lo
    # One spare voxel per axis; the grid is trimmed to the exact margin below.
    grid_shape = tuple(int(math.ceil(v / s)) + 1 for v, s in zip(hi - lo, (sx, sy, sz)))

    # Voxel centres in mm -- index * spacing, the affine's own mapping.
    gx = (np.arange(grid_shape[0]) * sx).reshape(-1, 1, 1)
    gy = (np.arange(grid_shape[1]) * sy).reshape(1, -1, 1)
    gz = (np.arange(grid_shape[2]) * sz).reshape(1, 1, -1)

    seg_data = np.zeros(grid_shape, dtype=np.uint16)
    for label, (cx, cy, cz), th in zip(labels, centroids, tilts_rad):
        y = gy - cy
        z = gz - cz
        u = y * math.cos(th) - z * math.sin(th)  # along the body's A-P axis
        v = y * math.sin(th) + z * math.cos(th)  # along the body's S-I axis
        inside = (
            (np.abs(gx - cx) <= _BODY_SIZE_LR_MM / 2.0)
            & (np.abs(u) <= _BODY_SIZE_AP_MM / 2.0)
            & (np.abs(v) <= _BODY_SIZE_SI_MM / 2.0)
        )
        if not inside.any():
            # A spacing coarser than the body can miss every voxel centre;
            # keep the label present as the voxel nearest its centroid.
            inside = np.zeros(grid_shape, dtype=bool)
            inside[tuple(int(round(c / s)) for c, s in zip((cx, cy, cz), (sx, sy, sz)))] = True
        seg_data[inside] = label

    # Trim to the occupied bounding box plus exactly ``margin_vox`` empty
    # voxels on every face, so the margin holds whatever the rounding.
    occupied = np.argwhere(seg_data)
    first = occupied.min(axis=0)
    last = occupied.max(axis=0)
    seg_data = seg_data[first[0]:last[0] + 1, first[1]:last[1] + 1, first[2]:last[2] + 1]
    seg_data = np.ascontiguousarray(
        np.pad(seg_data, [(int(m), int(m)) for m in margin_vox], mode="constant")
    )
    shape = tuple(int(d) for d in seg_data.shape)

    voxel_counts: Dict[int, int] = {
        label: int(np.count_nonzero(seg_data == label)) for label in labels
    }

    affine = _affine_from_spacing(spacing)
    seg_img = nib.Nifti1Image(seg_data, affine)

    # A deterministic, non-constant scan texture (a simple ramp along axis 2,
    # the stacking/superior-inferior axis), mirroring tests/synthetic.py's
    # make_scan(gradient=True) idiom.
    ramp = np.arange(shape[2], dtype=np.int64).reshape(1, 1, shape[2])
    scan_data = np.ascontiguousarray(np.broadcast_to(ramp, shape).astype(np.int16))
    scan_img = nib.Nifti1Image(scan_data, affine)

    return CleanSpine(
        scan_img=scan_img,
        seg_img=seg_img,
        labels=labels,
        level_names=level_names,
        spacing=(sx, sy, sz),
        shape=shape,
        voxel_counts=voxel_counts,
    )
