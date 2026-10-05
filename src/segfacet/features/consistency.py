"""Neighbour-consistency metrics for the ordered centroid sequence (item 020).

Two families of metrics are computed:

A. **Spacing regularity** — mean inter-centroid spacing, coefficient of
   variation (CV), per-pair signed deviations, and outlier-pair flags.

B. **Monotonic progression** -- whether the position *u* of each centroid
   along the spine increases (strictly) at every consecutive pair in the
   supplied anatomical order; the non-monotonic pairs are listed by level
   name. Since item 210 (2026-10-05) *u* is the normalised arc length along a
   **label-free path** through the centroids -- the longest path of their
   minimum spanning tree, every centroid projected onto its polyline -- walked
   in whichever direction has fewer rank inversions against the supplied
   order. The supplied order is the expectation being judged, never an input
   to the geometry, so a swap cannot hide behind a reference that follows it
   (item 132's concern) and a curved spine whose S reverses still reads in
   order. No spline is fitted or searched; ``fit`` is accepted but not read.

Public API
----------
``SpacingConsistency``
    Frozen dataclass with spacing-regularity metrics.
``MonotonicConsistency``
    Frozen dataclass with monotonic-progression metrics.
``compute_spacing_consistency(centroids, outlier_threshold_high=2.0, outlier_threshold_low=0.3) -> SpacingConsistency``
    Compute spacing metrics for an ordered centroid sequence.
``compute_monotonic_consistency(centroids, fit=None) -> MonotonicConsistency``
    Assess monotonicity of the supplied order against the label-free path.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

from segfacet.features.centroids import LabelCentroid
from segfacet.features.spline import SplineFit

__all__ = [
    "SpacingConsistency",
    "MonotonicConsistency",
    "compute_spacing_consistency",
    "compute_monotonic_consistency",
]


# --------------------------------------------------------------------------- #
# Result dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SpacingConsistency:
    """Spacing-regularity metrics for the ordered centroid sequence.

    Attributes
    ----------
    mean_spacing_mm : float
        Mean inter-centroid Euclidean spacing (mm).
    cv_spacing : float
        Coefficient of variation of inter-centroid spacings
        (0 = perfectly regular).  Defined as ``std(spacings) / mean(spacings)``
        using population (ddof=0) standard deviation; 0.0 when there is only
        one spacing (no variance possible).
    spacings_mm : tuple[float, ...]
        Per-adjacent-pair spacings in anatomical order
        (length == n_centroids - 1).
    deviations_mm : tuple[float, ...]
        Signed deviation of each spacing from the mean
        (same length as spacings_mm).
    outlier_pairs : tuple[tuple[str, str], ...]
        (level_a, level_b) pairs whose spacing is flagged as an outlier
        because it exceeds ``outlier_threshold_high * mean`` or is below
        ``outlier_threshold_low * mean``.
    """

    mean_spacing_mm: float
    cv_spacing: float
    spacings_mm: tuple
    deviations_mm: tuple
    outlier_pairs: tuple


@dataclass(frozen=True)
class MonotonicConsistency:
    """Monotonic-progression metrics for the label-free path position.

    Attributes
    ----------
    is_monotonic : bool
        True iff u increases strictly along the supplied order.
        ``u[i] >= u[i+1]`` is non-monotonic (equal values are flagged too --
        two vertebrae at the same path position indicate a stacking or
        near-coincident issue).
    non_monotonic_pairs : tuple[tuple[str, str], ...]
        (level_a, level_b) pairs where ``u[a] >= u[b]`` (position along the
        label-free path did not advance).
    u_values : tuple[float, ...]
        Per-centroid normalised arc length in ``[0, 1]`` along the MST longest
        path (item 210), length == n_centroids.
    """

    is_monotonic: bool
    non_monotonic_pairs: tuple
    u_values: tuple


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _euclidean_mm(a: LabelCentroid, b: LabelCentroid) -> float:
    """Return the Euclidean distance in mm between two LabelCentroid objects."""
    ax, ay, az = float(a.centroid_mm[0]), float(a.centroid_mm[1]), float(a.centroid_mm[2])
    bx, by, bz = float(b.centroid_mm[0]), float(b.centroid_mm[1]), float(b.centroid_mm[2])
    return math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)


def _tree_walk(adj: List[List[Tuple[int, float]]], src: int):
    """Return (distance-from-src, parent) over the tree ``adj``."""
    n = len(adj)
    dist = [0.0] * n
    parent = [-1] * n
    seen = [False] * n
    seen[src] = True
    stack = [src]
    while stack:
        v = stack.pop()
        for w, d in adj[v]:
            if not seen[w]:
                seen[w] = True
                dist[w] = dist[v] + d
                parent[w] = v
                stack.append(w)
    return dist, parent


def _inversions(order: List[int]) -> int:
    n = len(order)
    return sum(1 for a in range(n) for b in range(a + 1, n) if order[a] > order[b])


def _path_positions(centroids: Sequence[LabelCentroid]) -> List[float]:
    """Per-centroid ``u`` in [0, 1] along the label-free path (item 210).

    MST by Prim on the dense distance matrix (start at index 0, lowest index
    on ties; not scipy's csgraph, which reads a zero distance as no edge),
    longest path by double sweep, each centroid projected onto the path's
    polyline, ``u = s / L``, direction chosen by fewer rank inversions against
    the supplied order (a tie keeps forward). Reads only ``centroid_mm``.

    ponytail: gross lateral displacement of about twice the level pitch can
    make the longest path run along the displaced spur (item 210 Left open b).
    Candidate fix: drop centroids flagged ``displaced_vertebra`` before
    building the tree.
    """
    n = len(centroids)
    pts = np.array([[float(v) for v in c.centroid_mm[:3]] for c in centroids])
    dmat = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)

    key = dmat[0].copy()
    parent_of = [0] * n
    in_tree = np.zeros(n, dtype=bool)
    in_tree[0] = True
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for _ in range(n - 1):
        masked = np.where(in_tree, np.inf, key)
        v = int(np.argmin(masked))
        p = parent_of[v]
        adj[v].append((p, float(dmat[v, p])))
        adj[p].append((v, float(dmat[v, p])))
        in_tree[v] = True
        closer = (~in_tree) & (dmat[v] < key)
        for w in np.nonzero(closer)[0]:
            key[w] = dmat[v, w]
            parent_of[int(w)] = v

    d0, _ = _tree_walk(adj, 0)
    e1 = int(np.argmax(d0))
    d1, par = _tree_walk(adj, e1)
    e2 = int(np.argmax(d1))
    path = [e2]
    while path[-1] != e1:
        path.append(par[path[-1]])

    seg_len = [float(dmat[path[k], path[k + 1]]) for k in range(len(path) - 1)]
    total = float(sum(seg_len))
    if total == 0.0:
        return [0.0] * n
    cum = [0.0]
    for sl in seg_len:
        cum.append(cum[-1] + sl)

    s: List[float] = []
    for i in range(n):
        best_d, best_s = math.inf, 0.0
        for k, sl in enumerate(seg_len):
            a, b = pts[path[k]], pts[path[k + 1]]
            t = 0.0 if sl == 0.0 else min(1.0, max(0.0, float(np.dot(pts[i] - a, b - a)) / (sl * sl)))
            d = float(np.linalg.norm(pts[i] - (a + t * (b - a))))
            if d < best_d:
                best_d, best_s = d, cum[k] + t * sl
        s.append(best_s)

    fwd = sorted(range(n), key=lambda i: (s[i], i))
    bwd = sorted(range(n), key=lambda i: (-s[i], i))
    if _inversions(bwd) < _inversions(fwd):
        return [1.0 - v / total for v in s]
    return [v / total for v in s]


# --------------------------------------------------------------------------- #
# Public compute functions
# --------------------------------------------------------------------------- #


def compute_spacing_consistency(
    centroids: Sequence[LabelCentroid],
    outlier_threshold_high: float = 2.0,
    outlier_threshold_low: float = 0.3,
) -> SpacingConsistency:
    """Compute spacing-regularity metrics for an ordered centroid sequence.

    Parameters
    ----------
    centroids:
        Ordered (head-to-tail anatomical order) sequence of LabelCentroid
        objects.  Must have >= 2 entries; raises ValueError for 0 or 1 centroid.
    outlier_threshold_high:
        A spacing >= this factor * mean_spacing is flagged as an outlier
        (default 2.0 — double the mean).
    outlier_threshold_low:
        A spacing <= this factor * mean_spacing is flagged as an outlier
        (default 0.3 — less than 30 % of the mean).

    Returns
    -------
    SpacingConsistency

    Raises
    ------
    ValueError
        When ``len(centroids) < 2``.
    """
    n = len(centroids)
    if n < 2:
        raise ValueError(
            f"compute_spacing_consistency requires at least 2 centroids to "
            f"compute inter-centroid spacings, but received {n}. "
            f"Supply at least 2 LabelCentroid objects."
        )

    # Compute pairwise Euclidean distances in mm (do not mutate input).
    spacings: List[float] = [
        _euclidean_mm(centroids[i], centroids[i + 1]) for i in range(n - 1)
    ]

    mean_mm = float(np.mean(spacings))

    # Coefficient of variation: std / mean.  With only 1 spacing, std = 0.
    if len(spacings) == 1:
        cv = 0.0
    else:
        cv = float(np.std(spacings, ddof=0) / mean_mm) if mean_mm > 0.0 else 0.0

    # Signed deviations from the mean.
    deviations: List[float] = [s - mean_mm for s in spacings]

    # Outlier flags: flag pairs that are unusually large or small.
    outlier_pairs: List[Tuple[str, str]] = []
    for i, s in enumerate(spacings):
        if s >= outlier_threshold_high * mean_mm or s <= outlier_threshold_low * mean_mm:
            outlier_pairs.append(
                (centroids[i].level_name, centroids[i + 1].level_name)
            )

    return SpacingConsistency(
        mean_spacing_mm=mean_mm,
        cv_spacing=cv,
        spacings_mm=tuple(spacings),
        deviations_mm=tuple(deviations),
        outlier_pairs=tuple(outlier_pairs),
    )


def compute_monotonic_consistency(
    centroids: Sequence[LabelCentroid],
    fit: Optional[SplineFit] = None,
) -> MonotonicConsistency:
    """Assess whether the supplied order advances along the label-free path.

    Since item 210 (2026-10-05) *u* is the normalised arc length along the
    longest path of the centroids' minimum spanning tree (see
    :func:`_path_positions`), directed to have fewer rank inversions against
    the supplied order. The supplied (anatomical) order is judged directly
    against *u*: ``u[i] < u[i+1]`` must hold for every consecutive pair. No
    spline is fitted or searched. (Item 132 had judged against a
    traversal-ordered spline; item 130's closest-point search is no longer
    used here.)

    Parameters
    ----------
    centroids:
        Ordered (head-to-tail anatomical order) sequence of LabelCentroid
        objects.  Must have >= 2 entries; raises ValueError for 0 or 1 centroid.
    fit:
        Accepted for call-site compatibility; never read (item 210).

    Returns
    -------
    MonotonicConsistency

    Raises
    ------
    ValueError
        When ``len(centroids) < 2``.
    """
    n = len(centroids)
    if n < 2:
        raise ValueError(
            f"compute_monotonic_consistency requires at least 2 centroids to "
            f"assess monotonic progression, but received {n}. "
            f"Supply at least 2 LabelCentroid objects."
        )

    u_values: List[float] = _path_positions(centroids)

    # Identify non-monotonic consecutive pairs: u[i] >= u[i+1].
    non_monotonic_pairs: List[Tuple[str, str]] = []
    for i in range(n - 1):
        if u_values[i] >= u_values[i + 1]:
            non_monotonic_pairs.append(
                (centroids[i].level_name, centroids[i + 1].level_name)
            )

    is_monotonic = len(non_monotonic_pairs) == 0

    return MonotonicConsistency(
        is_monotonic=is_monotonic,
        non_monotonic_pairs=tuple(non_monotonic_pairs),
        u_values=tuple(u_values),
    )
