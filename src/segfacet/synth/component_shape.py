"""Component & shape perturbations: fragment, fuse, inject_islands (item 037).

The first Stage 5 operator family: three seeded :class:`~segfacet.synth.
perturbation.Perturbation` subclasses that inject connected-component /
mask-topology failures onto the item-036 clean-GT positive control
(:func:`segfacet.synth.clean_gt.build_clean_spine`), each returning a
well-formed :class:`~segfacet.synth.perturbation.Expectation` naming the induced
failure mode (a ``failure_modes.SPECIFICATION`` id) and the offending label(s):

* :class:`FragmentPerturbation` (``"fragment"``) -- splits one label's body
  into >= 2 comparable disconnected pieces via a thin interior slab cut
  perpendicular to the stacking axis -- resolved from the target volume's own
  affine (item 116), not a hardcoded index -- preserving the label's
  bounding box. Drives the fragmentation-kind ``"fragmentation"`` finding.
* :class:`FusePerturbation` (``"fuse"``) -- merges an adjacent label pair:
  the neighbour's voxels are re-labelled onto the target, leaving the target
  spanning two disconnected bodies. Drives the same fragmentation-kind
  finding on the surviving label (see the item spec's Assumptions for why
  the shipped default lumbar ``bounds`` cannot fire on a two-label fuse).
* :class:`InjectIslandsPerturbation` (``"inject_islands"``) -- adds one or
  more tiny (default 27-voxel, 3x3x3) disconnected components to a target
  label in verified-empty space, inset from every FOV face and separated
  from every label (including the target) by >= 1 empty voxel. Drives the
  island-kind ``"Rogue island(s):"`` finding while the target's dominant
  body stays above the fragmentation-index threshold.
* :class:`SplitPerturbation` (``"split"``, item 166, re-authored by item
  174) -- mode 3 sub-type (a): the target's neighbour-facing cap, the
  smallest whole-slice run holding at least ``donated_fraction`` of its
  voxels, is relabelled onto the adjacent neighbour.
* :class:`SplitOwnLabelPerturbation` (``"split_own_label"``, item 174) --
  mode 3 sub-type (b): the same caudal cap gets a label of its own (the
  target's), and every label cranial to it shifts up one level (l -> l - 1).

Implemented strictly against the unchanged item-036 contract (``Perturbation``,
``Expectation``, ``PerturbationResult``, ``register_perturbation``,
``seeded_rng``); ``synth/perturbation.py`` and ``synth/clean_gt.py`` are not
modified. Every operator is seeded/deterministic, non-mutating of the
caller's input, and preserves dtype/shape/affine/spacing.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np
import nibabel as nib

from segfacet.io import FacetInputError
from segfacet.synth.axes import si_axis
from segfacet.synth.perturbation import (
    Expectation,
    FAILURE_MODE_NAMES,
    Perturbation,
    PerturbationResult,
    register_perturbation,
    seeded_rng,
)

__all__ = [
    "FragmentPerturbation",
    "FusePerturbation",
    "SplitPerturbation",
    "SplitOwnLabelPerturbation",
    "InjectIslandsPerturbation",
]


# --------------------------------------------------------------------------- #
# Shared module-private helpers
# --------------------------------------------------------------------------- #


def _present_labels(labelmap: nib.Nifti1Image) -> List[int]:
    """Sorted non-zero unique voxel values present in *labelmap*."""
    data = np.asanyarray(labelmap.dataobj)
    return sorted(int(v) for v in np.unique(data) if v != 0)


def _choose_label(labels: Sequence[int], seed: int) -> int:
    """Deterministically pick one label from *labels* using ``seeded_rng``."""
    rng = seeded_rng(seed)
    idx = int(rng.integers(0, len(labels)))
    return labels[idx]


def _choose_adjacent_pair(labels_sorted: Sequence[int], seed: int) -> Tuple[int, int]:
    """Deterministically pick a consecutive-in-sorted-order pair.

    Returns ``(target, neighbour)`` with ``target`` the lower-index member.
    """
    rng = seeded_rng(seed)
    idx = int(rng.integers(0, len(labels_sorted) - 1))
    return labels_sorted[idx], labels_sorted[idx + 1]


def _new_image(data: np.ndarray, labelmap: nib.Nifti1Image) -> nib.Nifti1Image:
    """Build a fresh image with *data* and the input's affine.

    Never mutates the caller's array; *data* must already be a private copy.
    Spacing/affine are read only from *labelmap* (matching
    :class:`~segfacet.synth.perturbation.IdentityPerturbation`'s pattern).
    """
    affine = np.array(labelmap.affine, copy=True)
    return nib.Nifti1Image(data, affine)


def _label_bbox(data: np.ndarray, label: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return ``(mins, maxs)`` voxel-index bounding box for *label* in *data*."""
    coords = np.argwhere(data == label)
    return coords.min(axis=0), coords.max(axis=0)


def _require_present(label: int, labels: Sequence[int], *, what: str) -> None:
    if label not in labels:
        raise FacetInputError(
            f"{what} {label!r} is not present in the segmentation image. "
            f"Available non-zero labels: {list(labels)}."
        )


def _neighbour_facing_cap(
    data: np.ndarray,
    target: int,
    neighbour: int,
    fraction: float,
    axis: int,
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """The target's cap facing *neighbour* along stacking axis *axis* (item 174).

    The side is the end of the target nearer the neighbour, chosen by
    comparing the two labels' mean stacking-axis index. The cap is the
    smallest number of whole stacking-axis slices, counted from that end,
    whose target-voxel count is at least ``fraction * N`` (N = the target's
    voxel count) -- so it never falls short of the fraction and the cut is a
    single S-I plane.

    Returns ``(cap_mask, (lo, hi))``: the boolean mask of the target's voxels
    in the cap, and the cap's inclusive stacking-axis index range. Raises
    :class:`FacetInputError` when *fraction* is not strictly inside (0, 1) or
    when the cap would take every slice of the target.
    """
    if not 0.0 < fraction < 1.0:
        raise FacetInputError(
            f"donated_fraction={fraction!r} must lie strictly inside (0, 1)."
        )
    target_mask = data == target
    target_idx = np.nonzero(target_mask)[axis]
    neighbour_idx = np.nonzero(data == neighbour)[axis]
    mins, maxs = _label_bbox(data, target)
    axis_min, axis_max = int(mins[axis]), int(maxs[axis])

    counts = np.bincount(target_idx - axis_min, minlength=axis_max - axis_min + 1)
    toward_high = float(neighbour_idx.mean()) > float(target_idx.mean())
    if toward_high:
        counts = counts[::-1]
    k = int(np.searchsorted(np.cumsum(counts), fraction * target_idx.size)) + 1
    if k >= counts.size:
        raise FacetInputError(
            f"donated_fraction={fraction!r} of target label {target!r} would "
            f"take all {counts.size} of its stacking-axis slices, leaving the "
            "target no voxels."
        )

    lo, hi = (axis_max - k + 1, axis_max) if toward_high else (axis_min, axis_min + k - 1)
    slab = np.zeros_like(target_mask)
    slab[tuple(slice(lo, hi + 1) if a == axis else slice(None) for a in range(3))] = True
    return target_mask & slab, (lo, hi)


# --------------------------------------------------------------------------- #
# FragmentPerturbation
# --------------------------------------------------------------------------- #


@register_perturbation
class FragmentPerturbation(Perturbation):
    """Split one label's body into >= 2 comparable disconnected pieces.

    Registered under ``"fragment"``. Carves ``n_pieces - 1`` thin (1-voxel)
    interior slabs through the target label, perpendicular to the stacking
    axis -- resolved from the target volume's own affine at ``apply()`` time
    (item 116, via :func:`segfacet.synth.axes.si_axis`) rather than a
    hardcoded index -- so the label becomes ``n_pieces`` disconnected
    components while its bounding box (and therefore ``bounds`` findings)
    stays unchanged (specification mode 1, segmentation accuracy).
    """

    name = "fragment"

    def __init__(self, *, target_label: Optional[int] = None, n_pieces: int = 2):
        if n_pieces < 2:
            raise FacetInputError(
                f"FragmentPerturbation requires n_pieces >= 2, got {n_pieces!r}."
            )
        self._target_label = target_label
        self._n_pieces = int(n_pieces)

    def apply(self, labelmap: nib.Nifti1Image, seed: int) -> PerturbationResult:
        labels = _present_labels(labelmap)
        if not labels:
            raise FacetInputError(
                "FragmentPerturbation requires at least one present label; the "
                "input segmentation has none."
            )

        if self._target_label is not None:
            _require_present(self._target_label, labels, what="target_label")
            target = self._target_label
        else:
            target = _choose_label(labels, seed)

        data = np.array(np.asanyarray(labelmap.dataobj), copy=True)
        mask = data == target
        axis = si_axis(labelmap.affine)
        mins, maxs = _label_bbox(data, target)
        axis_min, axis_max = int(mins[axis]), int(maxs[axis])
        span = axis_max - axis_min

        if span < self._n_pieces:
            raise FacetInputError(
                f"FragmentPerturbation: target label {target!r} spans only "
                f"{span + 1} voxels along the stacking axis (array axis "
                f"{axis}), too thin to carve {self._n_pieces} disconnected "
                "pieces."
            )

        # Evenly spaced interior split planes (strictly between
        # axis_min/axis_max so the union bounding box -- and thus
        # extent_x/y/z_mm -- is preserved, keeping the "bounds" rule silent).
        splits = sorted(
            {
                axis_min + max(1, min(span - 1, round(i * span / self._n_pieces)))
                for i in range(1, self._n_pieces)
            }
        )

        for split_idx in splits:
            idx = tuple(split_idx if a == axis else slice(None) for a in range(3))
            slab = mask[idx]
            view = data[idx]
            view[slab] = 0

        out_img = _new_image(data, labelmap)

        expectation = Expectation(
            failure_mode=1,
            failure_mode_name=FAILURE_MODE_NAMES[1],
            expected_rule_ids=frozenset({"fragmentation"}),
            expected_labels=frozenset({target}),
            expected_verdict="flagged-for-review",
            detail=(
                f"fragment: split label {target} into {self._n_pieces} pieces "
                f"via interior slab cut(s) at stacking-axis (array axis "
                f"{axis}) index(es) {splits}."
            ),
        )
        return PerturbationResult(labelmap=out_img, expectation=expectation)


# --------------------------------------------------------------------------- #
# FusePerturbation
# --------------------------------------------------------------------------- #


@register_perturbation
class FusePerturbation(Perturbation):
    """Merge an adjacent label pair into a single, two-body label.

    Registered under ``"fuse"``. The neighbour's voxels are re-labelled onto
    the target (unbridged -- the physical gap is not filled), leaving the
    target spanning two disconnected vertebra bodies. Drives the
    fragmentation-kind finding on the surviving label (filed under
    specification mode 2, fused vertebra segments, which that finding only
    co-detects; see the
    item spec's Assumptions for why not ``bounds``).
    """

    name = "fuse"

    def __init__(
        self,
        *,
        target_label: Optional[int] = None,
        neighbour_label: Optional[int] = None,
    ):
        self._target_label = target_label
        self._neighbour_label = neighbour_label

    def apply(self, labelmap: nib.Nifti1Image, seed: int) -> PerturbationResult:
        labels = _present_labels(labelmap)
        if len(labels) < 2:
            raise FacetInputError(
                "FusePerturbation requires at least two present labels to fuse "
                f"an adjacent pair; found {labels!r}."
            )

        if self._target_label is not None or self._neighbour_label is not None:
            if self._target_label is None or self._neighbour_label is None:
                raise FacetInputError(
                    "FusePerturbation requires both target_label and "
                    "neighbour_label when either is given explicitly."
                )
            _require_present(self._target_label, labels, what="target_label")
            _require_present(self._neighbour_label, labels, what="neighbour_label")
            idx_t = labels.index(self._target_label)
            idx_n = labels.index(self._neighbour_label)
            if abs(idx_t - idx_n) != 1:
                raise FacetInputError(
                    f"FusePerturbation: target_label={self._target_label!r} and "
                    f"neighbour_label={self._neighbour_label!r} are not adjacent "
                    f"in the sorted present-label order {labels!r}."
                )
            target, neighbour = self._target_label, self._neighbour_label
        else:
            target, neighbour = _choose_adjacent_pair(labels, seed)

        data = np.array(np.asanyarray(labelmap.dataobj), copy=True)
        data[data == neighbour] = target
        out_img = _new_image(data, labelmap)

        expectation = Expectation(
            failure_mode=2,
            failure_mode_name=FAILURE_MODE_NAMES[2],
            expected_rule_ids=frozenset({"coverage", "fragmentation"}),
            expected_labels=frozenset({target}),
            expected_verdict="flagged-for-review",
            detail=(
                f"fuse: absorbed neighbour label {neighbour} into target "
                f"label {target}; {neighbour} is no longer present. Mode 2 "
                "(fused or split vertebra segments) of the catalogue signed "
                "off at item 150; what plain run_qc fires on it today are "
                "co-detections -- fragmentation on the two disconnected "
                "bodies under one label, coverage on the absorbed level "
                "missing from the span -- not mode 2's own bounds / "
                "reference_delta proxies, which need a reference."
            ),
        )
        return PerturbationResult(labelmap=out_img, expectation=expectation)


# --------------------------------------------------------------------------- #
# SplitPerturbation
# --------------------------------------------------------------------------- #


@register_perturbation
class SplitPerturbation(Perturbation):
    """Relabel one label's neighbour-facing cap onto its adjacent neighbour.

    Registered under ``"split"``: mode 3 sub-type (a), part of a vertebra
    carries a neighbouring vertebra's label (item 166; re-authored by item
    174, 2026-09-23). The cap is the part of the target beyond one S-I cut on
    the side facing the neighbour along the affine-resolved stacking axis
    (item 116, via :func:`segfacet.synth.axes.si_axis`): the smallest number
    of whole slices holding at least ``donated_fraction`` of the target's
    **voxels** (not of its stacking-axis span). Nothing is deleted or created:
    the foreground mask is unchanged and exactly one label's voxels change
    hands, leaving the target a single connected component and the neighbour
    spanning two disconnected bodies, the cap touching the donor.
    """

    name = "split"

    def __init__(
        self,
        *,
        target_label: Optional[int] = None,
        neighbour_label: Optional[int] = None,
        # A voxel fraction of the target (item 174, A1). Measured 2026-09-23
        # on the lordotic default base, L4 -> L5 at 0.2: the cap is 9 of L4's
        # 32 slices (4 030 of 19 344 voxels); the donor keeps 15 314 mm3
        # with extents 31 / 31 / 23 mm, inside the lumbar bounds.
        donated_fraction: float = 0.2,
    ):
        self._target_label = target_label
        self._neighbour_label = neighbour_label
        self._donated_fraction = float(donated_fraction)

    def apply(self, labelmap: nib.Nifti1Image, seed: int) -> PerturbationResult:
        labels = _present_labels(labelmap)
        if len(labels) < 2:
            raise FacetInputError(
                "SplitPerturbation requires at least two present labels to "
                f"split onto an adjacent neighbour; found {labels!r}."
            )

        if self._target_label is not None or self._neighbour_label is not None:
            if self._target_label is None or self._neighbour_label is None:
                raise FacetInputError(
                    "SplitPerturbation requires both target_label and "
                    "neighbour_label when either is given explicitly."
                )
            _require_present(self._target_label, labels, what="target_label")
            _require_present(self._neighbour_label, labels, what="neighbour_label")
            idx_t = labels.index(self._target_label)
            idx_n = labels.index(self._neighbour_label)
            if abs(idx_t - idx_n) != 1:
                raise FacetInputError(
                    f"SplitPerturbation: target_label={self._target_label!r} and "
                    f"neighbour_label={self._neighbour_label!r} are not adjacent "
                    f"in the sorted present-label order {labels!r}."
                )
            target, neighbour = self._target_label, self._neighbour_label
        else:
            target, neighbour = _choose_adjacent_pair(labels, seed)

        data = np.array(np.asanyarray(labelmap.dataobj), copy=True)
        axis = si_axis(labelmap.affine)
        mins, maxs = _label_bbox(data, target)
        n_target = int(np.count_nonzero(data == target))
        donate_mask, (slab_lo, slab_hi) = _neighbour_facing_cap(
            data, target, neighbour, self._donated_fraction, axis
        )
        data[donate_mask] = neighbour

        out_img = _new_image(data, labelmap)

        expectation = Expectation(
            failure_mode=3,
            failure_mode_name=FAILURE_MODE_NAMES[3],
            expected_rule_ids=frozenset({"fragmentation"}),
            expected_labels=frozenset({neighbour}),
            expected_verdict="flagged-for-review",
            detail=(
                f"split: requested donated_fraction {self._donated_fraction!r} "
                f"of target label {target!r}'s voxels; relabelled its "
                f"stacking-axis (array axis {axis}) slices {slab_lo}-{slab_hi} "
                f"of {int(mins[axis])}-{int(maxs[axis])} "
                f"({int(np.count_nonzero(donate_mask))} of {n_target} voxels) "
                f"to neighbour label {neighbour!r}."
            ),
        )
        return PerturbationResult(labelmap=out_img, expectation=expectation)


# --------------------------------------------------------------------------- #
# SplitOwnLabelPerturbation
# --------------------------------------------------------------------------- #


@register_perturbation
class SplitOwnLabelPerturbation(Perturbation):
    """Give one label's caudal cap a label of its own, shifting cranial labels.

    Registered under ``"split_own_label"``: mode 3 sub-type (b), part of a
    vertebra carries a label of its own (item 174, 2026-09-23). The cap faces
    the next-higher present label (caudal, since ascending labels advance
    caudally) and is cut by the same rule as :class:`SplitPerturbation`.
    Every present label ``l <= target`` becomes ``l - 1`` and the cap becomes
    ``target``: on the lumbar base the rest of L4 reads L3, and L1 reads T12.
    """

    name = "split_own_label"

    def __init__(
        self,
        *,
        target_label: Optional[int] = None,
        donated_fraction: float = 0.2,
    ):
        self._target_label = target_label
        self._donated_fraction = float(donated_fraction)

    def apply(self, labelmap: nib.Nifti1Image, seed: int) -> PerturbationResult:
        labels = _present_labels(labelmap)
        if len(labels) < 2:
            raise FacetInputError(
                "SplitOwnLabelPerturbation requires at least two present "
                f"labels; found {labels!r}."
            )
        if self._target_label is not None:
            _require_present(self._target_label, labels, what="target_label")
            target = self._target_label
        else:
            target = _choose_label(labels[:-1], seed)
        if target == labels[-1]:
            raise FacetInputError(
                f"SplitOwnLabelPerturbation: target_label={target!r} is the "
                "highest present label, so it has no caudal neighbour to cut "
                "a cap toward."
            )
        if labels[0] == 1:
            raise FacetInputError(
                "SplitOwnLabelPerturbation: the lowest present label is 1, so "
                "the cranial shift would relabel it as background."
            )
        neighbour = labels[labels.index(target) + 1]

        data = np.asanyarray(labelmap.dataobj)
        axis = si_axis(labelmap.affine)
        cap_mask, (lo, hi) = _neighbour_facing_cap(
            data, target, neighbour, self._donated_fraction, axis
        )
        out = np.array(data, copy=True)
        shift = (data != 0) & (data <= target)
        out[shift] = data[shift] - 1
        out[cap_mask] = target
        out_img = _new_image(out, labelmap)

        expectation = Expectation(
            failure_mode=3,
            failure_mode_name=FAILURE_MODE_NAMES[3],
            expected_rule_ids=frozenset({"bounds"}),
            expected_labels=frozenset({target}),
            expected_verdict="flagged-for-review",
            detail=(
                f"split_own_label: requested donated_fraction "
                f"{self._donated_fraction!r} of target label {target!r}'s "
                f"voxels; its caudal cap, stacking-axis (array axis {axis}) "
                f"slices {lo}-{hi} ({int(np.count_nonzero(cap_mask))} voxels), "
                f"keeps label {target!r} and every label <= {target!r} "
                "elsewhere shifts to label - 1."
            ),
        )
        return PerturbationResult(labelmap=out_img, expectation=expectation)


# --------------------------------------------------------------------------- #
# InjectIslandsPerturbation
# --------------------------------------------------------------------------- #


@register_perturbation
class InjectIslandsPerturbation(Perturbation):
    """Add one or more tiny rogue disconnected components to a label.

    Registered under ``"inject_islands"``. Each island is a small solid
    block (a cube when ``island_voxels`` is a perfect cube, else a 1-voxel-
    wide line of ``island_voxels`` length) placed in confirmed-empty voxels
    adjacent to the target body along array axis 1 (the clean GT's margin
    space on that axis): >= 1 empty voxel from the body (disconnected under
    6-connectivity) and >= 1 voxel from every FOV face (specification mode 4, islands). This
    placement is purely geometric (internal margin space, not a named
    anatomical face), so it is unaffected by which array axis carries which
    anatomical direction -- see the module/item-116 note on ``fragment``
    for the one operator in this file that does resolve an axis from the
    affine.
    """

    name = "inject_islands"

    def __init__(
        self,
        *,
        target_label: Optional[int] = None,
        n_islands: int = 1,
        island_voxels: int = 27,
    ):
        if n_islands < 1:
            raise FacetInputError(
                f"InjectIslandsPerturbation requires n_islands >= 1, got {n_islands!r}."
            )
        if island_voxels < 1:
            raise FacetInputError(
                "InjectIslandsPerturbation requires island_voxels >= 1, got "
                f"{island_voxels!r}."
            )
        self._target_label = target_label
        self._n_islands = int(n_islands)
        self._island_voxels = int(island_voxels)

    def _block_dims(self) -> Tuple[int, int, int]:
        """Voxel-index shape of a single island block."""
        n = self._island_voxels
        side = round(n ** (1.0 / 3.0))
        if side >= 1 and side * side * side == n:
            return side, side, side
        # Not a perfect cube: fall back to a 1-voxel-wide line along axis 2
        # (trivially connected, exactly n voxels).
        return 1, 1, n

    def apply(self, labelmap: nib.Nifti1Image, seed: int) -> PerturbationResult:
        labels = _present_labels(labelmap)
        if not labels:
            raise FacetInputError(
                "InjectIslandsPerturbation requires at least one present "
                "label; the input segmentation has none."
            )

        if self._target_label is not None:
            _require_present(self._target_label, labels, what="target_label")
            target = self._target_label
        else:
            target = _choose_label(labels, seed)

        data = np.array(np.asanyarray(labelmap.dataobj), copy=True)
        shape = data.shape
        mins, maxs = _label_bbox(data, target)
        x0, y0, z0 = (int(v) for v in mins)
        x1, y1, z1 = (int(v) for v in maxs)

        bx, by, bz = self._block_dims()

        placed = 0
        # Space successive islands along axis 0 within the body's own x-span
        # (with a 1-voxel gap between islands) so multiple islands don't
        # collide with each other.
        x_max_start = max(x0, x1 - bx + 1)
        x_cursor = x0
        for _ in range(self._n_islands):
            if x_cursor > x_max_start:
                x_cursor = x0  # wrap; blocks are tiny relative to body span
            x_start = min(x_cursor, x_max_start)
            z_start = z0 + max(0, (z1 - z0 + 1 - bz) // 2)

            region = self._find_empty_band(
                data=data,
                shape=shape,
                axis1_low=y0,
                axis1_high=y1,
                block_dims=(bx, by, bz),
                x_start=x_start,
                z_start=z_start,
            )
            if region is None:
                raise FacetInputError(
                    "InjectIslandsPerturbation: no valid empty placement found "
                    f"for label {target!r} (island {placed + 1}/{self._n_islands}); "
                    "the target body's margin is too small for the requested "
                    "island_voxels."
                )
            xs, ys, zs = region
            data[xs, ys, zs] = target
            placed += 1
            x_cursor += bx + 1

        out_img = _new_image(data, labelmap)

        expectation = Expectation(
            failure_mode=4,
            failure_mode_name=FAILURE_MODE_NAMES[4],
            expected_rule_ids=frozenset({"fragmentation"}),
            expected_labels=frozenset({target}),
            expected_verdict="flagged-for-review",
            detail=(
                f"inject_islands: added {self._n_islands} tiny island(s) of "
                f"{self._island_voxels} voxel(s) each to label {target}."
            ),
        )
        return PerturbationResult(labelmap=out_img, expectation=expectation)

    @staticmethod
    def _find_empty_band(
        *,
        data: np.ndarray,
        shape: Tuple[int, int, int],
        axis1_low: int,
        axis1_high: int,
        block_dims: Tuple[int, int, int],
        x_start: int,
        z_start: int,
    ):
        """Find a confirmed-empty block placement below/above the body along axis 1.

        Returns a ``(xs, ys, zs)`` fancy-index tuple (each an ndarray) for the
        block's voxels, or ``None`` if no valid placement exists in either
        direction.
        """
        bx, by, bz = block_dims

        # Candidate 1: strictly below the body along axis 1 (with a 1-voxel
        # gap), inset by >= 1 voxel from the y=0 face.
        y_end = axis1_low - 2  # last row of the block; axis1_low - 1 stays empty
        y_start = y_end - by + 1
        candidates = []
        if y_start >= 1:
            candidates.append((y_start, y_end))

        # Candidate 2: strictly above the body along axis 1 (with a 1-voxel
        # gap), inset by >= 1 voxel from the y=shape[1]-1 face.
        y_start2 = axis1_high + 2
        y_end2 = y_start2 + by - 1
        if y_end2 <= shape[1] - 2:
            candidates.append((y_start2, y_end2))

        x_end = x_start + bx - 1
        z_end = z_start + bz - 1

        if x_start < 1 or x_end > shape[0] - 2:
            return None
        if z_start < 1 or z_end > shape[2] - 2:
            return None

        for y_start_c, y_end_c in candidates:
            block = data[x_start : x_end + 1, y_start_c : y_end_c + 1, z_start : z_end + 1]
            if np.all(block == 0):
                xs, ys, zs = np.meshgrid(
                    np.arange(x_start, x_end + 1),
                    np.arange(y_start_c, y_end_c + 1),
                    np.arange(z_start, z_end + 1),
                    indexing="ij",
                )
                return xs.ravel(), ys.ravel(), zs.ravel()

        return None
