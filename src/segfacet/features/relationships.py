"""Inter-vertebra relationships (item 014).

Given an ordered sequence of :class:`~segfacet.features.centroids.LabelCentroid`
records, computes:

* **present_levels** — anatomical names in canonical head-to-tail order.
* **missing_levels** — expected-sequence levels absent within the observed
  present span (item 186: walks a per-section-count expected sequence, not a
  raw ``CANONICAL_ORDER`` slice -- see below).
* **neighbour_spacings_mm** — Euclidean distances between adjacent centroids
  (in canonical order).
* **is_continuous** — whether the *input* order is monotonically non-decreasing
  in canonical rank.
* **out_of_order_labels** — labels (in input order) that broke monotonicity.

Item 186: ``missing_levels`` no longer walks a raw ``CANONICAL_ORDER`` slice
between the first and last present level -- that placed the transitional T13
between T12 and L1 (and L6 between L5 and S1), so a common thoraco-lumbar case
holding T12 and L1 with no T13 reported T13 missing. It now walks
``segfacet.labels.expected_level_sequence`` for a per-section vertebra count
resolved from the present labels (or supplied via ``section_counts``) by
``segfacet.labels.resolve_section_counts`` -- see that module for the section
model. ``present_levels``, the spacings and the continuity walk are unchanged
and keep using ``CANONICAL_ORDER``.

Public API
----------
``SpineRelationships``
    Frozen dataclass carrying the result.
``compute_spine_relationships(centroids, convention=None, *, section_counts=None) -> SpineRelationships``
    Entry-point function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence

from segfacet.features.centroids import LabelCentroid
from segfacet.labels import (
    CANONICAL_ORDER,
    SACRUM,
    UNKNOWN,
    LabelConvention,
    expected_level_sequence,
    resolve_section_counts,
)

__all__ = [
    "SpineRelationships",
    "compute_spine_relationships",
]

#: Sacral label names, which all collapse onto ``SACRUM`` in the expected
#: sequence (the sacrum is not split into levels -- A3).
_SACRAL_NAMES = frozenset(f"S{i}" for i in range(1, 7))

# Canonical rank for O(1) comparisons.
_CANONICAL_RANK: dict[str, int] = {name: i for i, name in enumerate(CANONICAL_ORDER)}


@dataclass(frozen=True)
class SpineRelationships:
    """Inter-vertebra relationship record for a single segmentation case.

    Attributes
    ----------
    present_levels:
        Anatomical names of the recognised labels in canonical head-to-tail order.
    missing_levels:
        Expected-sequence levels absent within the observed present span, in
        sequence order (item 186: walks a per-section-count expected sequence,
        not a raw ``CANONICAL_ORDER`` slice -- see the module docstring).
    neighbour_spacings_mm:
        Euclidean distances (mm) between adjacent centroids in canonical order.
        Length is ``len(present_levels) - 1``; empty when fewer than 2 levels present.
    is_continuous:
        ``True`` iff the *input* order of level names is monotonically
        non-decreasing in canonical rank.
    out_of_order_labels:
        Label names (in input order) that broke monotonicity. Empty when
        ``is_continuous`` is ``True``.
    """

    present_levels: List[str]
    missing_levels: List[str]
    neighbour_spacings_mm: List[float]
    is_continuous: bool
    out_of_order_labels: List[str]


def compute_spine_relationships(
    centroids: Sequence[LabelCentroid],
    convention: Optional[LabelConvention] = None,
    *,
    section_counts: Optional[Mapping[str, int]] = None,
) -> SpineRelationships:
    """Compute inter-vertebra relationships from an ordered centroid sequence.

    Parameters
    ----------
    centroids:
        Sequence of :class:`~segfacet.features.centroids.LabelCentroid` records.
        May be supplied in any order; ``present_levels`` is always in canonical
        order. ``UNKNOWN`` and non-canonical level names are silently skipped.
    convention:
        Unused — reserved for API symmetry with sibling functions. Level names
        are read directly from ``LabelCentroid.level_name`` and compared against
        :data:`~segfacet.labels.CANONICAL_ORDER`.
    section_counts:
        Optional ``{section_name: count}`` override (item 186), passed straight
        to :func:`segfacet.labels.resolve_section_counts` as ``supplied``. A
        supplied section's reading needs no field-of-view corroboration.

    Returns
    -------
    SpineRelationships

    Raises
    ------
    segfacet.io.FacetInputError
        If ``section_counts`` names an unknown section, or a value outside its
        section's valid range.
    """
    # Keep only centroids whose level_name is in CANONICAL_ORDER.
    # UNKNOWN and any custom/non-canonical names are silently skipped.
    known = [c for c in centroids if c.level_name in _CANONICAL_RANK]

    # --- AC4: continuity assessed against *input* order of known centroids --- #
    is_continuous = True
    out_of_order_labels: List[str] = []
    prev_rank = -1
    for c in known:
        rank = _CANONICAL_RANK[c.level_name]
        if rank < prev_rank:
            is_continuous = False
            out_of_order_labels.append(c.level_name)
        else:
            prev_rank = rank

    # --- AC1: sort known centroids by canonical rank for remaining computations --- #
    sorted_centroids = sorted(known, key=lambda c: _CANONICAL_RANK[c.level_name])
    present_levels: List[str] = [c.level_name for c in sorted_centroids]

    # --- AC2 (item 186): missing levels within the expected-sequence span --- #
    # Resolved section counts (from the labels, or `section_counts`) build the
    # expected sequence; each present level maps onto it by identity, except
    # sacral labels S1-S6, which all collapse onto the single SACRUM element
    # (A3). Names not in the sequence (Cocc, UNKNOWN) are dropped.
    resolved = resolve_section_counts(present_levels, supplied=section_counts)
    sequence = expected_level_sequence(resolved.counts)
    seq_rank = {name: i for i, name in enumerate(sequence)}

    present_sequence_elements: List[str] = []
    seen_elements = set()
    for name in present_levels:
        element = SACRUM if name in _SACRAL_NAMES else name
        if element not in seq_rank or element in seen_elements:
            continue
        seen_elements.add(element)
        present_sequence_elements.append(element)

    missing_levels: List[str] = []
    if len(present_sequence_elements) >= 2:
        ranks = [seq_rank[element] for element in present_sequence_elements]
        lo, hi = min(ranks), max(ranks)
        present_set = set(present_sequence_elements)
        missing_levels = [
            name for name in sequence[lo : hi + 1] if name not in present_set
        ]

    # --- AC3: neighbour spacings in canonical order --- #
    neighbour_spacings_mm: List[float] = []
    for i in range(len(sorted_centroids) - 1):
        a = sorted_centroids[i].centroid_mm
        b = sorted_centroids[i + 1].centroid_mm
        dist = math.sqrt(sum((bi - ai) ** 2 for ai, bi in zip(a, b)))
        neighbour_spacings_mm.append(float(dist))

    return SpineRelationships(
        present_levels=present_levels,
        missing_levels=missing_levels,
        neighbour_spacings_mm=neighbour_spacings_mm,
        is_continuous=is_continuous,
        out_of_order_labels=out_of_order_labels,
    )
