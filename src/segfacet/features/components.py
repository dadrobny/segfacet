"""Connected-components analysis per label (item 012).

For a given integer label in a NIfTI instance label map, this module runs a
**6-connectivity** connected-components analysis (face-neighbours only, not
diagonal or edge neighbours) and computes:

* **component_count** — number of distinct connected components.
* **component_sizes** — voxel count per component, sorted descending.
* **component_volumes_mm3** — physical volume (mm³) per component, in the same
  order as ``component_sizes``.
* **largest_component_fraction** — ``component_sizes[0] / sum(component_sizes)``;
  equals ``1.0`` when the label is a single connected piece.
* **small_fragments** — list of component sizes (voxel counts) for components
  strictly below the ``min_fragment_voxels`` threshold from
  :class:`~segfacet.config.HeuristicConfig`. Empty when the threshold is ``0``.
* **stray_component_count** — number of components other than the dominant one
  (item 098); ``component_count - 1``.
* **stray_component_sizes** — ``component_sizes[1:]`` — every component's voxel
  count except the (largest, index-0) dominant one, same descending order, as
  a non-aliasing copy (item 098).
* **stray_volume_mm3** — ``sum(component_volumes_mm3[1:])``, the summed
  physical volume of the stray population, reusing the already-computed
  per-component volumes rather than a second ``voxel_volume`` multiply (item
  098).
* **stray_volume_fraction** — ``1.0 - largest_component_fraction``, the
  arithmetic complement of that field so the two are always consistent by
  construction rather than by a second, independently-rounded computation
  (item 098).
* **stray_contact_area_mm2** — the maximum, over every stray component, of
  that component's 6-neighbour face-contact area (mm²) with any single
  other non-zero label; mode 3's (*split vertebra segment*) discriminating
  signal (item 167).
* **stray_contact_label** — the other label id carrying that maximal
  interface, or the ``0`` background sentinel when
  ``stray_contact_area_mm2 == 0.0`` (item 167).
* **component_contacts** — one :class:`ComponentContact` per component, in
  ``component_sizes`` order (index 0 is the label's largest component,
  ``[1:]`` are its stray components): the component's own surface area, its
  contact area with its single most-contacted other label, and that contact
  as a *fraction of the component's own surface* — item 187's relative
  measure, which separates "most of a small component's surface touches a
  neighbour" from "a large component's absolute contact happens to be big".
* **label_contact_fraction** — the same fraction, computed once more over the
  label as a whole (all of its components' contact tallies and surfaces
  summed together) rather than any single component (item 187).

"Stray" means **every connected component of a label other than its single
largest (dominant) one** — the exact ``component_sizes[1:]`` population. A
single-component label reports the stray-population zero case:
``stray_component_count == 0``, ``stray_component_sizes == []``,
``stray_volume_mm3 == 0.0``, ``stray_volume_fraction == 0.0``.

Connectivity
------------
**6-connectivity** is the only connectivity used here: two voxels are
connected if and only if they share a face (±x, ±y, or ±z neighbour).
Voxels sharing only an edge or a corner are *not* connected. This is the
default ``structure`` for ``scipy.ndimage.label`` (the 3-D cross-shaped
structuring element), so no explicit structuring element is needed.

Public API
----------
``ComponentsInfo``
    Frozen dataclass carrying all per-label connected-components results.
``compute_components(seg_img, label, config) -> ComponentsInfo``
    Compute connected-components for a single label in a NiBabel image.
``CONNECTIVITY``
    Integer constant (``6``) documenting the connectivity used.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import nibabel as nib

import segfacet.backend as _backend_mod
from segfacet.backend import Backend

__all__ = [
    "ComponentContact",
    "ComponentsInfo",
    "compute_components",
    "CONNECTIVITY",
]

# Documented connectivity constant so callers can query it.
CONNECTIVITY: int = 6


# --------------------------------------------------------------------------- #
# ComponentContact dataclass (item 187)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ComponentContact:
    """One connected component's 6-neighbour face-contact measure (item 187).

    ``surface_area_mm2`` is the component's total 6-neighbour face area
    toward anything that is not itself — another label, background, or the
    image boundary (a padding voxel). ``contact_area_mm2`` is the face area
    toward the single most-contacted *other non-zero label*
    (``neighbour_label``), and ``contact_fraction`` is that contact as a
    fraction of the component's own surface — the relative measure a small
    component needs, since its absolute contact area is small even when most
    of its surface touches a neighbour. See the item 187 spec's A2 for the
    exact face/surface/tie-break definitions (item 167's face-contact
    definition, unchanged, now divided by the same component's own face
    count).

    Attributes
    ----------
    neighbour_label:
        The other label id carrying this component's largest contact area,
        or ``0`` when the component touches no other non-zero label.
    contact_area_mm2:
        The contact area (mm²) with ``neighbour_label`` (``0.0`` when
        ``neighbour_label == 0``).
    surface_area_mm2:
        The component's total 6-neighbour face area (mm²), including faces
        toward background and the image boundary.
    contact_fraction:
        ``contact_area_mm2 / surface_area_mm2``, in ``[0.0, 1.0]``.
    """

    neighbour_label: int
    contact_area_mm2: float
    surface_area_mm2: float
    contact_fraction: float


# --------------------------------------------------------------------------- #
# ComponentsInfo dataclass
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ComponentsInfo:
    """All connected-components properties for a single integer label.

    All fields are populated by :func:`compute_components`. The dataclass is
    frozen (immutable) and carries no NiBabel objects, so it is cheaply
    serialisable and safe to compare with ``==``.

    Attributes
    ----------
    component_count:
        Number of distinct connected components found for this label.
        Always >= 1 (a label with at least one voxel has at least one
        component).
    component_sizes:
        Voxel count for each component, sorted **descending** (largest
        component first). Length equals ``component_count``.
    component_volumes_mm3:
        Physical volume in mm³ for each component, in the same order as
        ``component_sizes``. Computed as voxel_count × product(spacings).
    largest_component_fraction:
        ``component_sizes[0] / sum(component_sizes)`` — the fraction of
        label voxels that belong to the single largest component. Equals
        ``1.0`` when the label is a single connected piece. Always in
        ``[0.0, 1.0]``.
    small_fragments:
        List of component sizes (voxel counts) for every component whose
        size is **strictly below** the ``min_fragment_voxels`` threshold.
        Empty when ``min_fragment_voxels == 0`` (threshold of 0 means
        nothing is strictly below it). Contains one entry per fragment —
        if two components have the same sub-threshold size, both appear.
    stray_component_count:
        Number of components other than the dominant one — always
        ``component_count - 1`` (item 098). ``0`` for a single-component
        label.
    stray_component_sizes:
        ``component_sizes[1:]`` — every component's voxel count except the
        dominant (index-0) one, in the same descending order, as a
        non-aliasing copy (item 098). ``[]`` for a single-component label.
    stray_volume_mm3:
        ``sum(component_volumes_mm3[1:])`` — the summed physical volume of
        the stray components, derived from the already-computed
        per-component volumes rather than a second ``voxel_volume``
        multiplication (item 098). ``0.0`` (a ``float``) for a
        single-component label.
    stray_volume_fraction:
        ``1.0 - largest_component_fraction`` — the arithmetic complement of
        ``largest_component_fraction``, so the two always sum to ``1.0``
        by construction (item 098). ``0.0`` for a single-component label.
    stray_contact_area_mm2:
        Neighbour-label contact area (item 167): the maximum, over every
        connected component of this label **other than its largest**, of
        that component's 6-neighbour face-contact area (mm²) with any
        single other non-zero label. ``0.0`` for a single-component label,
        or when no stray component touches another label at all. This is
        mode 3's (*split vertebra segment*) discriminating signal: a
        substantial stray piece pressed against the label that claimed it,
        as opposed to a detached-but-untouching stray (mode 2) or a small
        own-label island (mode 4). Tie-break policy (item 167): components
        are ordered by descending voxel count, ties broken by ascending
        component id, and the first of that order is the label's largest and
        is excluded from this search; among contacting labels of equal area,
        the lowest label id wins.
    stray_contact_label:
        The other label id carrying the interface at ``stray_contact_area_mm2``
        (item 167). ``0`` — the background sentinel — whenever
        ``stray_contact_area_mm2 == 0.0``, so the field is always numeric.
        Same tie-break policy as ``stray_contact_area_mm2``: components
        ordered by descending voxel count, ties broken by ascending
        component id, and among contacting labels of equal area the lowest
        label id wins.
    component_contacts:
        One :class:`ComponentContact` per component, in ``component_sizes``
        order (item 187). Index 0 is the label's largest component;
        ``component_contacts[1:]`` are its stray components, same order as
        ``stray_component_sizes``.
    label_contact_fraction:
        The same relative contact measure as :class:`ComponentContact`, but
        for the label as a whole rather than any single component (item 187,
        A3): the label's contact area with its single most-contacted
        neighbour label (summed across all of its components' contact with
        that neighbour), divided by the label's total surface area (summed
        across all of its components' surfaces). ``0.0`` when the label
        touches no other non-zero label.
    """

    component_count: int
    component_sizes: List[int]
    component_volumes_mm3: List[float]
    largest_component_fraction: float
    small_fragments: List[int]
    stray_component_count: int
    stray_component_sizes: List[int]
    stray_volume_mm3: float
    stray_volume_fraction: float
    stray_contact_area_mm2: float
    stray_contact_label: int
    component_contacts: List[ComponentContact]
    label_contact_fraction: float


# --------------------------------------------------------------------------- #
# Core compute function
# --------------------------------------------------------------------------- #


def compute_components(
    seg_img: nib.Nifti1Image,
    label: int,
    config,
    *,
    backend: Optional[Backend] = None,
) -> ComponentsInfo:
    """Compute connected-components analysis for a single integer label.

    The function is **read-only** — the input image is never modified. It is
    **deterministic**: identical inputs always produce identical outputs.

    6-connectivity is used (face-neighbours only). See :data:`CONNECTIVITY`.

    Parameters
    ----------
    seg_img:
        A NiBabel ``Nifti1Image`` carrying an integer label map. The header's
        voxel dimensions (``get_zooms()``) are used for physical-volume
        calculations.
    label:
        The integer label value to analyse.
    config:
        A :class:`~segfacet.config.HeuristicConfig` instance. The
        ``min_fragment_voxels`` field controls the small-fragment threshold.
    backend:
        Optional :class:`~segfacet.backend.Backend` handle routing the array/
        ndimage operations through ``numpy``/``scipy.ndimage`` (CPU) or
        ``cupy``/``cupyx.scipy.ndimage`` (GPU). When ``None`` (the default),
        resolved via :func:`segfacet.backend.get_backend`.

    Returns
    -------
    ComponentsInfo
        All connected-components properties for the requested label.

    Raises
    ------
    ValueError
        If ``label`` is not present in ``seg_img`` (no voxels carry that value).
    """
    backend = backend or _backend_mod.get_backend()
    xp = backend.xp

    # Read data without copying — we never write to it.
    data = xp.asarray(np.asanyarray(seg_img.dataobj))

    # Build boolean mask for the requested label (does not mutate data).
    mask = data == label  # new boolean array, not a view of data

    if not mask.any():
        available = sorted(
            int(v) for v in np.unique(np.asanyarray(seg_img.dataobj)) if v != 0
        )
        raise ValueError(
            f"Label {label!r} is not present in the segmentation image "
            f"(no voxels found). Available non-zero labels: {available}"
        )

    # Run 6-connectivity labelling via backend.ndimage.label (scipy.ndimage
    # for CPU, cupyx.scipy.ndimage for GPU).
    # The default structuring element for ndimage.label is the 3-D cross
    # (face-neighbours only), which implements 6-connectivity.
    labelled, n_components = backend.ndimage.label(mask)
    # labelled: integer array (0=background, 1..n_components=component ids)

    # Count voxels per component and sort descending.
    # xp.bincount is fast and deterministic; index 0 is the background count.
    counts = xp.bincount(labelled.ravel())
    # Slice off index 0 (background), get component counts for ids 1..n.
    component_counts = counts[1:n_components + 1]
    # Sort descending.
    component_sizes_arr = xp.sort(component_counts)[::-1]
    component_sizes: List[int] = [int(s) for s in component_sizes_arr]

    # Voxel volume from the image header.
    zooms = seg_img.header.get_zooms()
    voxel_vol = float(zooms[0]) * float(zooms[1]) * float(zooms[2])

    # Physical volumes in the same order as component_sizes.
    component_volumes_mm3: List[float] = [
        float(s) * voxel_vol for s in component_sizes
    ]

    # Largest-component fraction.
    total_voxels = sum(component_sizes)
    largest_component_fraction = float(component_sizes[0]) / float(total_voxels)

    # Small-fragment detection: strictly below threshold.
    min_frag = int(config.min_fragment_voxels)
    small_fragments: List[int] = [s for s in component_sizes if s < min_frag]

    # Stray-component metrics (item 098): every component other than the
    # dominant (index-0) one.
    stray_component_sizes: List[int] = list(component_sizes[1:])
    stray_component_count: int = len(stray_component_sizes)
    stray_volume_mm3: float = float(sum(component_volumes_mm3[1:]))
    stray_volume_fraction: float = 1.0 - largest_component_fraction

    # Neighbour-label contact area (item 167) and per-component contact/surface
    # measures (item 187). Descending-size component ids (not just sizes): id
    # at each rank, so the dominant (index-0) id is identified and every
    # component -- largest included -- is walked in the array it actually
    # occupies.
    # Tie-break policy (item 167): components are ordered by descending
    # voxel count, ties broken by ascending component id -- an explicit
    # `sorted(...)` key, not `xp.argsort(...)[::-1]`, whose default sort
    # kind is not stable and so is implementation-dependent under a tie
    # (in NumPy or CuPy alike).
    counts_by_id = [(idx + 1, int(component_counts[idx])) for idx in range(n_components)]
    component_ids_desc = [
        comp_id
        for comp_id, _count in sorted(counts_by_id, key=lambda pair: (-pair[1], pair[0]))
    ]

    # Per-axis face area from the header zooms -- never a hardcoded or
    # assumed-isotropic axis.
    face_area = {
        0: float(zooms[1]) * float(zooms[2]),
        1: float(zooms[0]) * float(zooms[2]),
        2: float(zooms[0]) * float(zooms[1]),
    }
    padded = xp.pad(data, 1, mode="constant", constant_values=0)
    neighbour_slices = []
    for axis in range(3):
        pos = [slice(1, -1)] * 3
        pos[axis] = slice(2, None)
        neg = [slice(1, -1)] * 3
        neg[axis] = slice(0, -2)
        neighbour_slices.append((tuple(pos), face_area[axis]))
        neighbour_slices.append((tuple(neg), face_area[axis]))

    # Item 187 (A2): a component's surface is every face NOT shared with
    # another voxel of the same component -- i.e. every face toward another
    # label, background, or the image boundary (a padding voxel, which reads
    # as 0). Two components of one label never share a face under
    # 6-connectivity, so this is exactly the component's faces toward
    # "not itself".
    component_tallies: Dict[int, tuple] = {}  # comp_id -> (area_by_other, surface)
    for comp_id in component_ids_desc:
        comp_mask = labelled == comp_id
        area_by_other: Dict[int, float] = {}
        surface = 0.0
        for sl, area in neighbour_slices:
            selected = padded[sl][comp_mask]
            for other_label in [int(v) for v in xp.unique(selected)]:
                if other_label == label:
                    continue
                count = int(xp.count_nonzero(selected == other_label))
                surface += count * area
                if other_label != 0:
                    area_by_other[other_label] = (
                        area_by_other.get(other_label, 0.0) + count * area
                    )
        component_tallies[comp_id] = (area_by_other, surface)

    component_contacts: List[ComponentContact] = []
    for comp_id in component_ids_desc:
        area_by_other, surface = component_tallies[comp_id]
        if area_by_other:
            # Tie-break policy (item 167): among contacting labels of equal
            # area, the lowest label id wins -- stated explicitly rather than
            # inherited from xp.unique's ascending order and dict insertion
            # order.
            neighbour = max(area_by_other, key=lambda k: (area_by_other[k], -k))
            contact = area_by_other[neighbour]
        else:
            neighbour, contact = 0, 0.0
        fraction = contact / surface if surface else 0.0
        component_contacts.append(
            ComponentContact(
                neighbour_label=neighbour,
                contact_area_mm2=contact,
                surface_area_mm2=surface,
                contact_fraction=fraction,
            )
        )

    # Absolute stray-contact fields (item 167), kept exactly as before: the
    # maximum, over every stray component (index 1: of component_ids_desc),
    # of that component's contact area with any single other non-zero label.
    # A single-component label short-circuits to (0.0, 0).
    stray_contact_area_mm2: float = 0.0
    stray_contact_label: int = 0
    for contact in component_contacts[1:]:
        # Strict `>` (not `>=`) across components: under the
        # descending-count/ascending-id order above, this keeps the
        # lowest-id component's contact on an area tie between components
        # (item 167).
        if contact.contact_area_mm2 > stray_contact_area_mm2:
            stray_contact_area_mm2 = contact.contact_area_mm2
            stray_contact_label = contact.neighbour_label

    # Label-scope contact fraction (item 187, A3): the same measure over the
    # label as a whole, from the already-computed per-component tallies (a
    # label's contact with k is the sum of its components' contact with k,
    # and its surface is the sum of their surfaces) -- not a second pass.
    label_area_by_other: Dict[int, float] = {}
    label_surface = 0.0
    for area_by_other, surface in component_tallies.values():
        label_surface += surface
        for other_label, area in area_by_other.items():
            label_area_by_other[other_label] = (
                label_area_by_other.get(other_label, 0.0) + area
            )
    if label_area_by_other:
        label_neighbour = max(label_area_by_other, key=lambda k: (label_area_by_other[k], -k))
        label_contact = label_area_by_other[label_neighbour]
    else:
        label_contact = 0.0
    label_contact_fraction: float = label_contact / label_surface if label_surface else 0.0

    return ComponentsInfo(
        component_count=n_components,
        component_sizes=component_sizes,
        component_volumes_mm3=component_volumes_mm3,
        largest_component_fraction=largest_component_fraction,
        small_fragments=small_fragments,
        stray_component_count=stray_component_count,
        stray_component_sizes=stray_component_sizes,
        stray_volume_mm3=stray_volume_mm3,
        stray_volume_fraction=stray_volume_fraction,
        stray_contact_area_mm2=stray_contact_area_mm2,
        stray_contact_label=stray_contact_label,
        component_contacts=component_contacts,
        label_contact_fraction=label_contact_fraction,
    )
