"""Generated feature & rule catalogue (item 103; Stage 19).

The single shared generator behind two committed artifacts
(``docs/aide/feature_catalogue.generated.json`` / ``.md``) and the HTML status
report's Feature Catalogue section (``scripts/aide_status_report.py``). It
replaces the hand-typed ``FEATURE_CATALOG`` literal that used to live in the
status-report script with a catalogue built from the *realised* record shape
plus **code-derived** rule/mode attribution, joined with authored prose from
:mod:`segfacet.feature_docs`.

Four derivation mechanisms, each carrying its own evidence tag
--------------------------------------------------------------
- **A. Dynamic access trace** (``observed``) — wrap a realised driver record in
  a non-invasive ``dict``-subclass proxy (:func:`trace_record_access`) that
  records every leaf path actually read, then run every registered rule
  (:func:`segfacet.heuristics.rule.iter_rules`) over the traced record.
- **B. Path-aware static AST scan** (``static``) — item 223 (insight
  ``2026-10-06-1935``). Each registered rule's own ``evaluate`` is followed from
  its record parameter, through variables, loops and calls to same-module or
  ``segfacet.*``-imported helpers, to the path every string-key read
  (``x["k"]`` / ``x.get("k")``) indexes (:func:`_rule_read_paths`). The read
  is attributed to the catalogue leaf paths that path names and to nothing
  else; a read whose base cannot be traced to the record contributes nothing --
  there is **no last-segment fallback**. Catches branches the driver set never
  realises (e.g. ``reference_delta``'s out-of-range reads, whose driver record
  has an empty ``out_of_range_features[]``). History: item 110 matched every
  string key in the module against the last path segment of leaf paths, when
  exactly one leaf ended in it; that missed shared-last-segment reads and
  invented reads through blocks no driver realises.

  Limits (unresolved reads attribute nothing). Resolved: same-module and
  ``from segfacet.x import f`` helpers, followed to a depth cap. Not resolved:
  nested ``def`` helpers and lambdas inside ``evaluate``; comprehension results
  (and a comprehension variable leaks into the enclosing ``env``);
  ``from segfacet.heuristics import fov`` then ``fov.f(...)``; relative
  imports; helper methods inherited from a base class. The scan is
  flow-insensitive: bindings are unioned into ``env`` (like tuple unpacking),
  so reusing one variable name for two values attributes both values' reads to
  both -- an over-approximation, not a missed read.
- **C. The committed geometric corpus manifest** — ``rule_id -> failure
  mode(s)``, read from every failure-kind case of
  ``tests/corpus/manifest.json`` (item 182; via
  :func:`segfacet.synth.corpus.load_manifest`), mapping each of a case's
  ``expected_rule_ids`` to that case's ``failure_mode``. No hand-typed
  rule-id -> mode dictionary exists anywhere in this module's source (drift
  guard, AC13). Exposed publicly as :func:`scan_synth_rule_mode_map`. It reads
  the geometric manifest only and cannot see the intensity corpus, whose
  cases carry ``expected_firing``, not ``expected_rule_ids`` (item 156, Seam
  2) — see the function's own docstring for its two remaining consumers.
- **D. Non-rule consumers** (``observed`` / ``vocabulary``) — the same trace
  proxy run through ``eval.per_mode.compute_per_mode_metrics`` and
  ``human_report.render_feature_table``, plus the declared feature-name
  vocabularies (``reference.delta.MORPHOLOGY_FEATURES``,
  ``reference.ingest.INGESTED_FEATURES``, ``eval.feature_match.
  TRACKED_FEATURES``) matched by last path segment via
  :data:`segfacet.feature_docs.PATH_ALIASES`.

A third source of ``mode_evidence`` (item 136) sits alongside C: each
registered rule's own class-attribute ``RuleModeDeclaration``
(:mod:`segfacet.heuristics.rule`) states the failure mode(s) it targets (or that
it targets none, or that its disposition is pending). ``mode_evidence`` gains
the tag ``"rule_declaration"`` when at least one of an entry's
``consuming_rules`` carries a declaration with non-empty ``modes``. Because
declared modes may include an *analytic* attribution with no corpus
corroboration (item 137's ``bounds``/``reference_delta``, tagged
``"analytic"`` rather than ``"corpus"`` in the declaration's own
``evidence``), a declared mode is **not** guaranteed to already be a subset
of mechanism C's corpus-derived map — against *that* map,
:func:`rule_declaration_conflicts` only enforces the corpus → declaration
direction (a corpus case must be reflected in the declaration), never the
declaration → corpus-map reverse (item 147 retired that direction
permanently; a declaration's *analytic* attribution is legitimately absent
from the corpus). Disagreement between the declaration and the corpus-derived
map — in either enforced direction — is reported by
:func:`rule_declaration_conflicts`, never silently resolved here.
:func:`rule_declaration_conflicts` also enforces a *second*, unrelated
reverse direction (item 156, Seam 1): declaration → **specification** (not
the corpus-derived map) — every declared known mode must be mirrored by an
``IntendedRule`` edge in :data:`segfacet.failure_modes.SPECIFICATION`.

A fourth tag, ``"rule_mode_less"`` (item 137, ordered last — after
``"rule_declaration"``), marks an entry with at least one consuming rule
that has *declared itself mode-less* (a non-empty ``mode_less_reason``): a
source that spoke and said "no mode", categorically different from
``"rule_unmapped"`` ("nobody has said"). After item 137, ``"rule_unmapped"``
means exactly that latter case — a consuming rule with no corpus-derived
modes, no declared modes, and no mode-less declaration either — and is
reachable only when a shipped rule carries no ``RuleModeDeclaration`` at all
or an undischarged ``pending_reason`` (neither ships on this tree; both are
exercised adversarially by the test suite).

Per-path classification (item 148)
-----------------------------------
Both rule-sourced mode terms are **gated per path**. Each declaration also
carries ``consumed_paths`` — a ``ConsumedPath(path, role, reason)`` for every
leaf path this module attributes to that rule, with ``role`` from the closed
vocabulary ``("signal", "bookkeeping", "not-read", "condition-signal")`` (see
:data:`segfacet.heuristics.rule.PATH_ROLES`). A rule contributes its
corpus-derived (C) and declared (item 136) modes to a path **only** where
that ``(rule, path)`` pair is ``"signal"``: before item 148 every leaf path a
declaring rule consumed inherited that rule's *whole* mode tuple, so pure
bookkeeping paths (label ids, level names, containers iterated, availability
gates, band values interpolated into a message) were painted with modes they
cannot evidence. A rule whose ``consumed_paths`` is empty contributes
**nothing** — never a fall-back to the item-136 behaviour, which would be a
silent default; :func:`path_classification_conflicts` reports it, along with
an unclassified consumed path, a classified path the rule does not consume,
and a ``"not-read"`` claim on a pair mechanism A observed being read. The
classification is *declared, never inferred*: no heuristic over path names,
no default. The path-keyed item-099 anchor term is untouched — it is already
per-path.

The classification is **rendered, not silently applied**:
``CatalogueEntry.mode_roles`` carries the entry's ``(rule_id, role)`` pairs
into both artifacts (the JSON's ``"mode_roles"`` key, the Markdown's
``Mode role(s)`` column), and ``mode_evidence`` gains
``"rule_bookkeeping"`` / ``"rule_not_read"``, so a reader can tell "a source
spoke and said this path cannot evidence a mode" from ``"rule_unmapped"``
("nobody has said") and from ``()`` ("no rule reads it").

``consuming_rules = A ∪ B``. ``failure_modes`` = (item-099 mode anchors) ∪
(modes of ``consuming_rules`` under C, item 148: through a ``"signal"`` path
only) ∪ (modes of ``consuming_rules`` declared per rule, item 136 — may
include an analytic attribution outside the C term, item 137; item 148:
through a ``"signal"`` path only). ``mode_evidence`` is the ordered
subsequence of ``("per_mode_metric", "rule_mode_map", "rule_declaration",
"rule_mode_less", "rule_bookkeeping", "rule_not_read",
"rule_condition_signal")`` whose sources fired (the last, item 150, marks a
path a mode-less rule reads as a case *condition*'s evidence),
or exactly ``("rule_unmapped",)`` when no source fired but a consuming rule
said nothing, or ``()`` when neither applies. ``status`` = an authored
:data:`segfacet.feature_docs.STATUS_OVERRIDES` entry if present, else
``"keep"`` when A ∪ B ∪ D is non-empty, else **``"unwired"``**.

Two tiers, one ``origin``
--------------------------
Every catalogued path is realised by :func:`iter_driver_records` — the
"record"-tier drivers (built from :mod:`segfacet.synth` +
:func:`segfacet.pipeline.extract_feature_record`) and two "augmented" drivers
(``image_features`` / ``reference_delta``, built through the existing
converters over hand-constructed placeholder dataclass instances — no
PyRadiomics, no reference artifact, no scan). Both tiers flow through the
*same* :func:`iter_leaf_paths` walk and therefore the same ``origin ==
"record"`` classification (see the item's Decisions log for why a second
``origin`` value is not introduced: nothing downstream needs to distinguish
them and doing so would break the driver-union coverage equality, AC6).

Determinism contract
---------------------
:func:`build_catalogue` never mutates any input; two calls return equal
catalogues. :func:`catalogue_to_dict` / :func:`render_markdown` are pure
functions of the catalogue and are byte-reproducible within one session.
Heavy imports (NumPy/SciPy/NiBabel, via ``segfacet.pipeline``/
``segfacet.synth``) are deferred into function bodies, per ``cli.py``'s house
style, so ``import segfacet.catalogue`` alone stays cheap.

Scope fence
-----------
This module does **not** change any extractor, rule, threshold, schema,
report, or CLI behaviour. It touches no file under ``src/segfacet/
features/**``, ``heuristics/**``, ``eval/**``, ``synth/**``, ``reference/**``,
and none of ``pipeline.py``, ``feature_report.py``, ``cli.py``,
``report_schema_v0.json`` (AC25). It is not the drift test (item 104 — this
module only exposes the two shared primitives, :func:`iter_leaf_paths` and
:func:`iter_driver_records`, that test needs) and not the golden-file decision
table (item 105).

Public API
----------
``CatalogueError``, ``FeatureDocMissing`` (subclass)
    Raised by :func:`build_catalogue` in strict mode.
``CatalogueEntry``, ``CatalogueGroup``, ``FeatureCatalogue``
    Frozen dataclasses making up the catalogue.
``normalise_leaf_path(path) -> str``
    Pure, idempotent leaf-path normaliser (schema granularity).
``iter_leaf_paths(record) -> set[str]``
    Walk a record to its normalised leaf-path set.
``iter_driver_records() -> Iterator[tuple[str, dict]]``
    The deterministic, in-package driver-record set.
``trace_record_access(record, callable) -> set[str]``
    Non-invasive dynamic-access tracer (mechanism A's primitive).
``build_catalogue(*, strict=True, reference=None) -> FeatureCatalogue``
    Assemble the full catalogue. ``reference`` (item 124) steers the
    observed-range reference population; see :mod:`segfacet.observed_range`.
``catalogue_to_dict(cat) -> dict``, ``render_markdown(cat) -> str``
    Deterministic serialisers.
``path_classification_conflicts() -> tuple[str, ...]``
    Item 148's conformance checker over the per-path classification: every
    disagreement between a declaration's ``consumed_paths`` and the leaf
    paths this module attributes to that rule. Empty on the shipped tree.
``main(argv=None) -> int``
    ``python -m segfacet.catalogue [--json PATH] [--md PATH] [--reference PATH]``.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import cycle
    from segfacet.observed_range import ObservedRange

__all__ = [
    "CatalogueError",
    "FeatureDocMissing",
    "CatalogueEntry",
    "CatalogueGroup",
    "FeatureCatalogue",
    "normalise_leaf_path",
    "iter_leaf_paths",
    "iter_driver_records",
    "trace_record_access",
    "build_catalogue",
    "catalogue_to_dict",
    "render_markdown",
    "scan_synth_rule_mode_map",
    "rule_declaration_conflicts",
    "path_classification_conflicts",
    "main",
]

SCHEMA_VERSION = "1.2"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_JSON_PATH = _REPO_ROOT / "docs" / "aide" / "feature_catalogue.generated.json"
_DEFAULT_MD_PATH = _REPO_ROOT / "docs" / "aide" / "feature_catalogue.generated.md"

_CATALOGUE_NOTE = (
    "Generated by `python -m segfacet.catalogue` (item 103). Do not hand-edit "
    "this document -- edit `src/segfacet/feature_docs.py` (prose / owners / "
    "mode anchors / status overrides) and regenerate. `record[\"reference\"]` "
    "is deliberately excluded: the `bounds` and `fragmentation` rules read it, "
    "but it is a `ReferenceDistribution` object handle, not serialised feature "
    "data with a leaf path. Item 124's `observed` block reports each numeric "
    "path's observed range across two independent populations -- the "
    "in-package synthetic driver corpus (never flags a feature dead) and the "
    "committed real-GT reference distribution (the only population that can "
    "produce the `\"degenerate\"` verdict) -- but only the 21 of 99 numeric "
    "paths the reference vocabulary covers can ever read `\"degenerate\"`; "
    "the rest get their numbers reported and no verdict stronger than "
    "`\"constant-synthetic\"`."
)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class CatalogueError(Exception):
    """Base error for a catalogue that fails to build in strict mode."""


class FeatureDocMissing(CatalogueError):
    """A realised leaf path has no ``feature_docs.FEATURE_DOCS`` entry."""


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CatalogueEntry:
    """One catalogued feature: a normalised leaf path plus its provenance."""

    path: str
    group_title: str
    stage_label: str
    module: str
    measures: str
    computation: str
    units: str
    scale_sensitivity: str
    documented: bool
    origin: str
    consuming_rules: Tuple[str, ...]
    rule_evidence: Tuple[Tuple[str, str], ...]
    consumers: Tuple[str, ...]
    failure_modes: Tuple[int, ...]
    mode_evidence: Tuple[str, ...]
    mode_roles: Tuple[Tuple[str, str], ...]
    status: str
    observed: "ObservedRange"


@dataclass(frozen=True)
class CatalogueGroup:
    """A ``BLOCK_OWNERS`` group: a title/stage/module plus its entries."""

    title: str
    stage_label: str
    module: str
    intro: str
    entries: Tuple[CatalogueEntry, ...]


@dataclass(frozen=True)
class FeatureCatalogue:
    """The whole generated catalogue: groups, plus a flattened entry list."""

    schema_version: str
    note: str
    groups: Tuple[CatalogueGroup, ...]
    entries: Tuple[CatalogueEntry, ...]


# =========================================================================== #
# Step 3: the normaliser and walker
# =========================================================================== #


def normalise_leaf_path(path: str) -> str:
    """Collapse *path* to its schema-granularity, normalised form.

    Idempotent: ``normalise_leaf_path(normalise_leaf_path(p)) ==
    normalise_leaf_path(p)`` for every input. Collapses (a) every list index to
    ``[]``, (b) an integer ``per_label`` key to ``{label}`` (both
    ``per_label.<int>`` and nested, e.g. ``image_features.per_label.<int>``),
    (c) an ``extended.<anything>`` key to ``extended.{radiomic}`` (an
    unbounded PyRadiomics-derived vocabulary), (d) a
    ``reference_delta.per_label.<int>`` key to ``reference_delta.{label}``.
    Values are never inspected -- only path segments are ever touched.
    """
    segments = path.split(".")

    # (c) extended.<anything> -> extended.{radiomic}: truncate at the first
    # "extended" segment, regardless of anything beyond it.
    if "extended" in segments:
        idx = segments.index("extended")
        segments = segments[: idx + 1] + ["{radiomic}"]

    # (d) reference_delta.per_label.<int> -> reference_delta.{label}
    collapsed: List[str] = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        if (
            seg == "reference_delta"
            and i + 2 < len(segments)
            and segments[i + 1] == "per_label"
            and segments[i + 2].isdigit()
        ):
            collapsed.append("reference_delta")
            collapsed.append("{label}")
            i += 3
            continue
        collapsed.append(seg)
        i += 1
    segments = collapsed

    # (b) per_label.<int> -> per_label.{label} (any remaining occurrence).
    collapsed = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        if seg == "per_label" and i + 1 < len(segments) and segments[i + 1].isdigit():
            collapsed.append("per_label")
            collapsed.append("{label}")
            i += 2
            continue
        collapsed.append(seg)
        i += 1
    segments = collapsed

    # (a) any remaining bare-integer segment is a generic list index -> merge
    # into the preceding segment as "prev[]".
    collapsed = []
    for seg in segments:
        if seg.isdigit() and collapsed:
            collapsed[-1] = collapsed[-1] + "[]"
        else:
            collapsed.append(seg)
    segments = collapsed

    return ".".join(segments)


def _walk_leaf_paths(value: Any, path: str, sink: Set[str]) -> None:
    if isinstance(value, dict):
        if not value:
            if path:
                sink.add(path)
            return
        for key, sub in value.items():
            sub_path = f"{path}.{key}" if path else str(key)
            _walk_leaf_paths(sub, sub_path, sink)
        return

    if isinstance(value, list):
        if value and all(isinstance(el, dict) for el in value):
            container_path = f"{path}[]" if path else "[]"
            for el in value:
                _walk_leaf_paths(el, container_path, sink)
            return
        # Empty list, or a scalar (non-dict-element) list -> a single leaf.
        sink.add(f"{path}[]" if path else "[]")
        return

    # Scalar leaf (str / int / float / bool / None).
    if path:
        sink.add(path)


def iter_leaf_paths(record: Mapping[str, Any]) -> Set[str]:
    """Walk *record* to its set of normalised, schema-granularity leaf paths.

    A scalar list yields ``container[]``; a list of dicts recurses into each
    element under the shared ``container[]`` path; an empty dict or empty list
    still yields a leaf (never silently dropped). Pure -- never mutates
    *record*.
    """
    sink: Set[str] = set()
    _walk_leaf_paths(dict(record) if record else {}, "", sink)
    return {normalise_leaf_path(p) for p in sink}


def _last_segment(path: str) -> str:
    tail = path.rsplit(".", 1)[-1]
    return tail[:-2] if tail.endswith("[]") else tail


# =========================================================================== #
# Step 4: the driver-record set
# =========================================================================== #


def iter_driver_records() -> Iterator[Tuple[str, dict]]:
    """Yield ``(driver_id, record)`` pairs realising every catalogued block.

    Built **only** from :mod:`segfacet.synth` and :mod:`segfacet.pipeline`
    (this function's source names no path under the tests directory) so item
    104's drift test never needs a second, drifting copy of the driver set.
    Deterministic: two calls yield equal records. The union of the yielded
    records' leaf paths realises at least one non-empty ``pairs.overlaps``
    element, one record with Stage 3 fields (``case.curve``), and one
    degenerate (0/1-label, hence no Stage 3) record.
    """
    import numpy as np
    import nibabel as nib

    from segfacet.config import bundled_default_config
    from segfacet.feature_report import (
        build_image_features_block,
        build_intensity_entries,
    )
    from segfacet.features.intensity import LabelIntensity
    from segfacet.features.overlap import detect_overlaps
    from segfacet.pipeline import extract_feature_record
    from segfacet.reference.delta import (
        REFERENCE_DELTA_VERSION,
        FeatureDelta,
        LabelDelta,
        ReferenceDelta,
        reference_delta_to_dict,
    )
    from segfacet.reference.ingest import INGESTED_FEATURES
    from segfacet.synth.clean_gt import build_clean_spine
    from segfacet.synth.perturbation import get_perturbation

    config = bundled_default_config()

    clean = build_clean_spine()
    clean_record = extract_feature_record(clean.seg_img, config)
    yield "clean", clean_record

    zero_data = np.zeros(clean.shape, dtype=np.uint16)
    zero_img = nib.Nifti1Image(zero_data, clean.seg_img.affine)
    yield "zero_label", extract_feature_record(zero_img, config)

    single = build_clean_spine(levels=("L3",))
    yield "single_label", extract_feature_record(single.seg_img, config)

    # A deliberate non-empty overlaps block: reuse the clean record's other
    # blocks verbatim, replacing only ``pairs.overlaps`` with a real
    # detect_overlaps() result over a two-channel stack sharing every voxel
    # of the first label -- a multi-channel input the catalogue builds
    # itself, since no committed corpus case can express one (item 195,
    # 2026-09-28).
    data = np.asanyarray(clean.seg_img.dataobj)
    label_a, label_b = clean.labels[0], clean.labels[1]
    mask_a = data == label_a
    stack = np.stack([mask_a, np.array(mask_a, copy=True)], axis=0)
    overlap_pairs = detect_overlaps(stack, np.array([label_a, label_b]))
    overlaps_record = dict(clean_record)
    overlaps_record["pairs"] = {
        **clean_record["pairs"],
        "overlaps": [
            {
                "label_a": p.label_a,
                "label_b": p.label_b,
                "overlap_voxels": p.overlap_voxels,
            }
            for p in overlap_pairs
        ],
    }
    yield "overlaps", overlaps_record

    fragment_cls = get_perturbation("fragment")
    fragmented_img, _ = fragment_cls().apply(clean.seg_img, seed=0)
    yield "fragmented", extract_feature_record(fragmented_img, config)

    remove_level_cls = get_perturbation("remove_level")
    missing_img, _ = remove_level_cls().apply(clean.seg_img, seed=0)
    yield "missing_level", extract_feature_record(missing_img, config)

    sequence_break_cls = get_perturbation("sequence_break")
    seqbreak_img, _ = sequence_break_cls().apply(clean.seg_img, seed=0)
    yield "sequence_break", extract_feature_record(seqbreak_img, config)

    # stage3_unavailable (item 220): two concentric boxes share one exact
    # centroid, so Stage 3 is skipped. A partial record, like the
    # image_features and reference_delta drivers below, so no other path's
    # observed range moves.
    concentric = np.zeros((20, 20, 40), dtype=np.uint16)
    concentric[5:15, 5:15, 10:30] = 21
    concentric[8:12, 8:12, 17:23] = 22
    concentric_img = nib.Nifti1Image(concentric, np.eye(4))
    concentric_record = extract_feature_record(concentric_img, config)
    yield "stage3_unavailable", {
        "stage3_unavailable": concentric_record["stage3_unavailable"]
    }

    # Two augmented drivers, realised through the existing converters over
    # hand-constructed placeholder dataclass instances -- no PyRadiomics, no
    # reference artifact, no scan, fully deterministic (item 103 Assumptions
    # "Two tiers").
    placeholder_intensity = LabelIntensity(
        voxel_count=100,
        n_nonfinite_excluded=0,
        mean=500.0,
        median=480.0,
        std=50.0,
        min=100.0,
        max=900.0,
        p05=200.0,
        p25=400.0,
        p50=480.0,
        p75=600.0,
        p95=800.0,
        range=800.0,
        iqr=200.0,
        entropy=3.5,
    )
    image_features_block = build_image_features_block(
        backend="builtin",
        radiomics_available=False,
    )
    intensity_entries = build_intensity_entries(
        {label_a: placeholder_intensity},
        extended={label_a: {"original_firstorder_Mean": 480.0}},
    )
    yield "image_features", {
        "per_label": {str(label_a): {"intensity": intensity_entries[str(label_a)]}},
        "case": {"intensity": image_features_block},
    }

    # One placeholder per feature name ``compute_reference_delta`` scores from a
    # record (``INGESTED_FEATURES``), so the catalogue lists every
    # ``reference_delta.{label}.features.<f>.<s>`` path a real report carries
    # (item 215, D8) -- not only ``physical_volume_mm3``'s.
    placeholder_feature_deltas = tuple(
        FeatureDelta(
            feature=name,
            value=18750.0,
            z_score=0.1,
            robust_z=0.2,
            percentile_rank=55.0,
            out_of_range=False,
        )
        for name in INGESTED_FEATURES
    )
    placeholder_label_delta = LabelDelta(
        label=label_a,
        level_name="L1",
        stratum="all",
        available=True,
        features=placeholder_feature_deltas,
        distribution_distance=0.2,
        out_of_range_features=(),
    )
    placeholder_reference_delta = ReferenceDelta(
        reference_delta_version=REFERENCE_DELTA_VERSION,
        reference_schema_version="1.0",
        reference_source="synthetic-placeholder",
        stratum="all",
        lower_pct=1,
        upper_pct=99,
        per_label={label_a: placeholder_label_delta},
    )
    yield "reference_delta", {
        "reference_delta": reference_delta_to_dict(placeholder_reference_delta)
    }


# =========================================================================== #
# Step 5: the trace proxy (mechanism A)
# =========================================================================== #


class _TracedDict(dict):
    """A ``dict`` subclass that records every leaf path actually read.

    Retrieving a nested dict or a list-of-dicts returns a further-wrapped
    proxy and records nothing; retrieving a scalar records its normalised
    path; retrieving any other list (empty, or of non-dict elements) records
    ``path[]``. Never writes back into the wrapped mapping.
    """

    def __init__(self, data: Mapping[str, Any], path: str, sink: Set[str]):
        super().__init__(data)
        self._path = path
        self._sink = sink

    def _child_path(self, key: Any) -> str:
        return f"{self._path}.{key}" if self._path else str(key)

    def _wrap(self, key: Any, value: Any) -> Any:
        child_path = self._child_path(key)
        if isinstance(value, dict):
            return _TracedDict(value, child_path, self._sink)
        if isinstance(value, list):
            if value and all(isinstance(el, dict) for el in value):
                return _TracedList(value, f"{child_path}[]", self._sink)
            self._sink.add(normalise_leaf_path(f"{child_path}[]"))
            return value
        self._sink.add(normalise_leaf_path(child_path))
        return value

    def __getitem__(self, key: Any) -> Any:
        value = dict.__getitem__(self, key)
        return self._wrap(key, value)

    def get(self, key: Any, default: Any = None) -> Any:
        if not dict.__contains__(self, key):
            return default
        return self[key]

    def items(self):
        return [(k, self[k]) for k in dict.keys(self)]

    def values(self):
        return [self[k] for k in dict.keys(self)]


class _TracedList(list):
    """A ``list`` subclass wrapping a list-of-dicts under one shared path."""

    def __init__(self, data: Sequence[Any], path: str, sink: Set[str]):
        super().__init__(data)
        self._path = path
        self._sink = sink

    def _wrap(self, item: Any) -> Any:
        if isinstance(item, dict):
            return _TracedDict(item, self._path, self._sink)
        return item

    def __iter__(self):
        for item in list.__iter__(self):
            yield self._wrap(item)

    def __getitem__(self, index):
        item = list.__getitem__(self, index)
        if isinstance(index, slice):
            return [self._wrap(el) for el in item]
        return self._wrap(item)


def trace_record_access(record: Mapping[str, Any], fn) -> Set[str]:
    """Call ``fn(traced_record)`` and return the set of leaf paths it read.

    *record* is never mutated -- ``_TracedDict``/``_TracedList`` always
    construct fresh wrapper objects around shallow-copied contents.
    """
    sink: Set[str] = set()
    traced = _TracedDict(record, "", sink)
    fn(traced)
    return sink


# =========================================================================== #
# Step 6: the static scanners (mechanisms B and C)
# =========================================================================== #


# Item 223: path-aware mechanism B. A path is a tuple of tokens: a key string,
# ``"[]"`` for "an element of the list", or ``None`` for "some one key/index".
_WILD = None
_ITER = "[]"
_ELEMS = "<elems>"  # marks a local list whose elements sit at the preceding path
_MAX_CALL_DEPTH = 20  # call-following cap; deeper calls attribute nothing
_Paths = frozenset  # frozenset of token tuples


class _ModuleInfo:
    """Parsed module: functions by (class, name), and ``from segfacet.x import n``."""

    def __init__(self, module_name: str):
        import ast
        import importlib.util
        import sys

        self.name = module_name
        origin = getattr(sys.modules.get(module_name), "__file__", None)
        if not origin:
            try:
                spec = importlib.util.find_spec(module_name)
            except (ImportError, ValueError):
                spec = None
            origin = spec.origin if spec else None
        if not origin:
            raise OSError(f"no readable source for module {module_name!r}")
        self.tree = ast.parse(Path(origin).read_text(encoding="utf-8"))
        self.funcs: Dict[Tuple[Optional[str], str], Any] = {}
        self.imports: Dict[str, Tuple[str, str]] = {}
        for cls_name, node in self._functions(self.tree, None):
            self.funcs.setdefault((cls_name, node.name), node)
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("segfacet."):
                for alias in node.names:
                    self.imports[alias.asname or alias.name] = (node.module, alias.name)

    def _functions(self, node, cls_name):
        import ast

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                yield from self._functions(child, child.name)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield cls_name, child
                yield from self._functions(child, cls_name)
            else:
                yield from self._functions(child, cls_name)


class _PathScan:
    """Follows the record from a rule's ``evaluate`` parameter and collects the
    paths of every string-key read (``x["k"]`` / ``x.get("k")``)."""

    def __init__(self):
        self.modules: Dict[str, _ModuleInfo] = {}
        self.reads: Set[Tuple[Any, ...]] = set()
        self._memo: Dict[Any, _Paths] = {}
        self._depth = 0

    def module(self, name: str) -> _ModuleInfo:
        if name not in self.modules:
            self.modules[name] = _ModuleInfo(name)
        return self.modules[name]

    def run_rule(self, rule) -> Set[Tuple[Any, ...]]:
        import ast

        info = self.module(type(rule).__module__)
        import inspect

        named = [
            n
            for n in ast.walk(info.tree)
            if isinstance(n, ast.ClassDef) and n.name == type(rule).__name__
        ]
        # Same-named classes in one module: prefer the one at the rule class's
        # own source line (decorators included); else the first.
        start = inspect.getsourcelines(type(rule))[1] if len(named) > 1 else None
        cls = next(
            (n for n in named if min([n.lineno] + [d.lineno for d in n.decorator_list]) == start),
            named[0] if named else None,
        )
        fn = next(
            (
                n
                for n in (cls.body if cls else [])
                if isinstance(n, ast.FunctionDef) and n.name == "evaluate"
            ),
            None,
        )
        if fn is None:
            return set()
        self.reads = set()
        self._call(info, cls.name, fn, [frozenset({()})], {}, skip_self=True)
        return self.reads

    # -- calls ------------------------------------------------------------
    def _call(self, info, cls_name, fn, args, kwargs, skip_self=False) -> _Paths:
        params = [a.arg for a in fn.args.posonlyargs + fn.args.args]
        if skip_self and params and params[0] in ("self", "cls"):
            params = params[1:]
        env: Dict[str, _Paths] = {}
        for name, paths in list(zip(params, args)) + list(kwargs.items()):
            if paths:
                env[name] = paths
        if not env:
            return frozenset()
        key = (info.name, cls_name, fn.name, tuple(sorted(env.items(), key=lambda kv: kv[0])))
        if key in self._memo:
            return self._memo[key]
        if self._depth >= _MAX_CALL_DEPTH:  # growing-path recursion: stop, attribute nothing
            return frozenset()
        self._memo[key] = frozenset()  # recursion guard
        ret: Set[Tuple[Any, ...]] = set()
        self._depth += 1
        try:
            self._block(fn.body, env, info, cls_name, ret)
        finally:
            self._depth -= 1
        self._memo[key] = frozenset(ret)
        return self._memo[key]

    # -- statements -------------------------------------------------------
    def _block(self, stmts, env, info, cls, ret) -> None:
        import ast

        for st in stmts:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(st, ast.Assign):
                v = self.ev(st.value, env, info, cls)
                for t in st.targets:
                    self._bind(t, v, st.value, env, info, cls)
            elif isinstance(st, ast.AnnAssign):
                if st.value is not None:
                    self._bind(st.target, self.ev(st.value, env, info, cls), st.value, env, info, cls)
            elif isinstance(st, ast.Return):
                if st.value is not None:
                    ret |= self.ev(st.value, env, info, cls)
            elif isinstance(st, (ast.For, ast.AsyncFor)):
                self._bind_iter(st.target, st.iter, env, info, cls)
                for _ in range(2):  # loop-carried bindings settle in two passes
                    self._block(st.body, env, info, cls, ret)
                self._block(st.orelse, env, info, cls, ret)
            elif isinstance(st, ast.While):
                self.ev(st.test, env, info, cls)
                for _ in range(2):
                    self._block(st.body, env, info, cls, ret)
                self._block(st.orelse, env, info, cls, ret)
            elif isinstance(st, ast.If):
                self.ev(st.test, env, info, cls)
                self._block(st.body, env, info, cls, ret)
                self._block(st.orelse, env, info, cls, ret)
            elif isinstance(st, (ast.With, ast.AsyncWith)):
                for item in st.items:
                    v = self.ev(item.context_expr, env, info, cls)
                    if item.optional_vars is not None:
                        self._bind(item.optional_vars, v, item.context_expr, env, info, cls)
                self._block(st.body, env, info, cls, ret)
            elif isinstance(st, ast.Try):
                self._block(st.body, env, info, cls, ret)
                for h in st.handlers:
                    self._block(h.body, env, info, cls, ret)
                self._block(st.orelse, env, info, cls, ret)
                self._block(st.finalbody, env, info, cls, ret)
            else:
                for child in ast.iter_child_nodes(st):
                    if isinstance(child, ast.expr):
                        self.ev(child, env, info, cls)

    def _bind(self, target, paths, value_node, env, info, cls) -> None:
        import ast

        if isinstance(target, ast.Name):
            env[target.id] = env.get(target.id, frozenset()) | paths
        elif isinstance(target, (ast.Tuple, ast.List)):
            if isinstance(value_node, (ast.Tuple, ast.List)) and len(value_node.elts) == len(target.elts):
                for t, v in zip(target.elts, value_node.elts):
                    self._bind(t, self.ev(v, env, info, cls), v, env, info, cls)
            else:
                for t in target.elts:
                    self._bind(t, paths, value_node, env, info, cls)

    def _bind_iter(self, target, it, env, info, cls) -> None:
        """Bind a loop/comprehension target to the elements of *it*."""
        import ast

        if isinstance(it, ast.Call):
            f = it.func
            if isinstance(f, ast.Name) and f.id in ("sorted", "list", "reversed", "tuple") and it.args:
                for extra in list(it.args[1:]) + [k.value for k in it.keywords]:
                    self.ev(extra, env, info, cls)
                return self._bind_iter(target, it.args[0], env, info, cls)
            if isinstance(f, ast.Attribute) and f.attr in ("items", "values") and not it.args:
                base = self.ev(f.value, env, info, cls)
                wild = frozenset(p + (_WILD,) for p in base)
                if f.attr == "items" and isinstance(target, ast.Tuple) and len(target.elts) == 2:
                    self._bind(target.elts[1], wild, it, env, info, cls)
                else:
                    self._bind(target, wild, it, env, info, cls)
                return
            if isinstance(f, ast.Name) and f.id == "enumerate" and it.args:
                inner = self.ev(it.args[0], env, info, cls)
                elems = frozenset(p + (_ITER,) for p in inner)
                if isinstance(target, ast.Tuple) and len(target.elts) == 2:
                    self._bind(target.elts[1], elems, it, env, info, cls)
                return
        paths = self.ev(it, env, info, cls)
        elems = frozenset(p[:-1] if p and p[-1] == _ELEMS else p + (_ITER,) for p in paths)
        self._bind(target, elems, it, env, info, cls)

    # -- expressions ------------------------------------------------------
    def ev(self, node, env, info, cls) -> _Paths:
        import ast

        ev = lambda n: self.ev(n, env, info, cls)  # noqa: E731
        if node is None:
            return frozenset()
        if isinstance(node, ast.Name):
            return env.get(node.id, frozenset())
        if isinstance(node, ast.Subscript):
            base = ev(node.value)
            sl = node.slice
            if isinstance(sl, ast.Slice):
                for part in (sl.lower, sl.upper, sl.step):
                    ev(part)
                return base
            ev(sl)
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                out = frozenset(p + (sl.value,) for p in base)
                self.reads |= out
                return out
            return frozenset(p + (_WILD,) for p in base)
        if isinstance(node, ast.BoolOp):
            out: Set[Tuple[Any, ...]] = set()
            for v in node.values:
                out |= ev(v)
            return frozenset(out)
        if isinstance(node, ast.IfExp):
            ev(node.test)
            return ev(node.body) | ev(node.orelse)
        if isinstance(node, ast.NamedExpr):
            v = ev(node.value)
            self._bind(node.target, v, node.value, env, info, cls)
            return v
        if isinstance(node, ast.Call):
            return self._ev_call(node, env, info, cls)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            for gen in node.generators:
                self._bind_iter(gen.target, gen.iter, env, info, cls)
                for cond in gen.ifs:
                    ev(cond)
            for part in ("elt", "key", "value"):
                ev(getattr(node, part, None))
            return frozenset()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                ev(child)
        return frozenset()

    def _ev_call(self, node, env, info, cls) -> _Paths:
        import ast

        ev = lambda n: self.ev(n, env, info, cls)  # noqa: E731
        f = node.func
        args = [ev(a) for a in node.args]
        kwargs = {k.arg: ev(k.value) for k in node.keywords if k.arg}
        if isinstance(f, ast.Attribute):
            if f.attr == "get" and node.args:
                base = ev(f.value)
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    out = frozenset(p + (a0.value,) for p in base)
                    self.reads |= out
                    return out
                return frozenset(p + (_WILD,) for p in base)
            if f.attr in ("copy",):
                return ev(f.value)
            if f.attr == "append" and len(args) == 1 and isinstance(f.value, ast.Name):
                # ``lst.append(x)``: remember where the list's elements come from.
                node_arg = node.args[0]
                elems = set().union(*(self.ev(e, env, info, cls) for e in node_arg.elts)) if isinstance(node_arg, ast.Tuple) else set(args[0])
                env[f.value.id] = env.get(f.value.id, frozenset()) | frozenset(p + (_ELEMS,) for p in elems)
                return frozenset()
            if isinstance(f.value, ast.Name) and f.value.id in ("self", "cls"):
                fn = info.funcs.get((cls, f.attr))
                if fn is not None:
                    return self._call(info, cls, fn, args, kwargs, skip_self=True)
            else:
                ev(f.value)
            return frozenset()
        if isinstance(f, ast.Name):
            if f.id in ("dict", "list", "sorted", "tuple", "reversed") and args:
                return args[0]
            fn = info.funcs.get((None, f.id))
            if fn is not None:
                return self._call(info, None, fn, args, kwargs)
            if f.id in info.imports:
                mod_name, orig = info.imports[f.id]
                try:
                    other = self.module(mod_name)
                except Exception:
                    return frozenset()
                fn = other.funcs.get((None, orig))
                if fn is not None:
                    return self._call(other, None, fn, args, kwargs)
        return frozenset()


def _rule_read_paths(rule) -> Set[Tuple[Any, ...]]:
    """Resolved string-key read paths of one registered rule (item 223)."""
    return _PathScan().run_rule(rule)


def _leaf_tokens(path: str) -> Tuple[str, ...]:
    out: List[str] = []
    for seg in path.split("."):
        n = 0
        while seg.endswith("[]"):
            seg, n = seg[:-2], n + 1
        out.append(seg)
        out.extend([_ITER] * n)
    return tuple(out)


def _collapse_per_label(read: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """A wildcard right after ``per_label`` is ``{label}`` (cf. normalise_leaf_path)."""
    out: List[Any] = []
    i = 0
    while i < len(read):
        if read[i] == "per_label" and i + 1 < len(read) and read[i + 1] is _WILD:
            if out[-1:] != ["reference_delta"]:  # ``reference_delta.per_label.<k>`` -> ``reference_delta.{label}``
                out.append("per_label")
            out.append("{label}")
            i += 2
            continue
        out.append(read[i])
        i += 1
    return tuple(out)


def _read_matches(read: Tuple[Any, ...], leaf: Tuple[str, ...]) -> bool:
    if leaf[-1:] == (_ITER,) and len(leaf) == len(read) + 1:
        leaf = leaf[:-1]  # a read of ``p`` also matches the scalar-list leaf ``p[]``
    return len(read) == len(leaf) and all(r is _WILD or r == t for r, t in zip(read, leaf))


def _scan_synth_rule_mode_map() -> Dict[str, Tuple[int, ...]]:
    """``rule_id -> failure mode(s)``, read from the committed geometric corpus
    manifest's failure-kind cases (item 182; ``tests/corpus/manifest.json``,
    via :func:`segfacet.synth.corpus.load_manifest`). Every case whose
    :func:`segfacet.synth.perturbation.corpus_case_kind` is
    ``CASE_KIND_FAILURE`` contributes each of its ``expected_rule_ids``,
    mapped to that case's ``failure_mode``. No rule-id -> mode mapping is
    hand-typed anywhere in this module's source (AC13's drift guard).

    Geometric-only (item 156, Seam 2; item 182 A1): this reads the geometric
    manifest only, so it never sees the intensity corpus (whose cases carry
    ``expected_firing``, not ``expected_rule_ids``). Its two remaining
    consumers, both geometric-only by the same limit: mechanism C of
    :func:`build_catalogue` (this module's own ``rule_mode_map`` evidence
    term), and the corpus -> declaration direction of
    :func:`rule_declaration_conflicts`.
    :func:`segfacet.traceability.build_matrix` used to read this scan for
    ``corpus_designated_unregistered_rule_ids`` too; since item 156 it derives
    that field from the two committed manifests
    (``tests/corpus/manifest.json`` and ``tests/corpus/intensity/manifest.json``)
    directly, so an intensity case naming an unregistered rule is reported.

    A case with no recognised ``kind`` propagates
    :func:`~segfacet.synth.perturbation.corpus_case_kind`'s ``ValueError``
    rather than being skipped in silence (item 182 A3)."""
    import segfacet.synth.corpus as corpus
    from segfacet.synth.perturbation import CASE_KIND_FAILURE, corpus_case_kind

    accum: Dict[str, Set[int]] = defaultdict(set)
    for case in corpus.load_manifest().get("cases", []):
        if corpus_case_kind(case) != CASE_KIND_FAILURE:
            continue
        for rule_id in case.get("expected_rule_ids", ()):
            accum[rule_id].add(case["failure_mode"])

    return {rule_id: tuple(sorted(modes)) for rule_id, modes in accum.items()}


def scan_synth_rule_mode_map() -> Dict[str, Tuple[int, ...]]:
    """Public name for :func:`_scan_synth_rule_mode_map` (item 136).

    ``rule_id -> failure mode(s)``, read from the committed geometric corpus
    manifest's failure-kind cases (item 182) -- the corpus-derived side of the
    declaration <-> corpus agreement checked by
    :func:`rule_declaration_conflicts`. Geometric-only: see
    :func:`_scan_synth_rule_mode_map`'s docstring for what this cannot see
    and who still reads it.
    """
    return _scan_synth_rule_mode_map()


# =========================================================================== #
# Step 7: mechanism D -- non-rule consumers
# =========================================================================== #


def _mechanism_d_consumers(
    driver_records: Sequence[Tuple[str, dict]], path_aliases: Mapping[str, str], leaf_union: Set[str]
) -> Dict[str, Set[str]]:
    from segfacet.eval.feature_match import TRACKED_FEATURES
    from segfacet.eval.per_mode import compute_per_mode_metrics
    from segfacet.human_report import render_feature_table
    from segfacet.reference.delta import MORPHOLOGY_FEATURES
    from segfacet.reference.ingest import INGESTED_FEATURES

    consumers: Dict[str, Set[str]] = defaultdict(set)

    for _driver_id, record in driver_records:
        for callable_name, fn in (
            ("compute_per_mode_metrics", lambda traced: compute_per_mode_metrics(traced)),
            ("render_feature_table", lambda traced: render_feature_table(traced)),
        ):
            try:
                sink = trace_record_access(record, fn)
            except Exception:
                continue
            for path in sink:
                consumers[path].add(callable_name)

    by_last_segment: Dict[str, List[str]] = defaultdict(list)
    for path in leaf_union:
        by_last_segment[_last_segment(path)].append(path)

    vocab_names = set(MORPHOLOGY_FEATURES) | set(INGESTED_FEATURES) | set(TRACKED_FEATURES)
    for name in vocab_names:
        target_paths: List[str]
        alias_path = path_aliases.get(name)
        if alias_path is not None and alias_path in leaf_union:
            target_paths = [alias_path]
        else:
            target_paths = by_last_segment.get(name, [])
        for path in target_paths:
            consumers[path].add("vocabulary")

    return consumers


# =========================================================================== #
# Step 8: build_catalogue
# =========================================================================== #


def _group_for_path(path: str, block_owners: Sequence[Tuple[str, str, str, str]]) -> Tuple[str, str, str]:
    """Longest-prefix match of *path* against ``BLOCK_OWNERS`` rows."""
    best: Optional[Tuple[str, str, str, str]] = None
    for row in block_owners:
        prefix = row[0]
        if prefix == "" or path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "["):
            if best is None or len(prefix) > len(best[0]):
                best = row
    if best is None:
        return ("Uncategorised", "", "")
    return (best[1], best[2], best[3])


def build_catalogue(*, strict: bool = True, reference: Any = None) -> FeatureCatalogue:
    """Assemble the full :class:`FeatureCatalogue` (AC6-AC17).

    Never mutates any input. Two calls return equal catalogues.

    Parameters
    ----------
    reference:
        The reference population for item 124's ``observed`` block: ``None``
        (the bundled production reference), a ``ReferenceDistribution``
        instance, or a path to a reference artifact on disk. A missing or
        unparseable artifact degrades every entry's ``observed.reference`` to
        ``covered=False`` rather than raising.

    Raises
    ------
    FeatureDocMissing
        In strict mode, if a realised leaf path has no
        ``feature_docs.FEATURE_DOCS`` entry.
    CatalogueError
        In strict mode, if a ``feature_docs.FEATURE_DOCS`` key matches no
        realised leaf path.
    """
    from segfacet import feature_docs as _feature_docs_module
    from segfacet.config import bundled_default_config
    from segfacet.heuristics.rule import iter_rule_declarations, iter_rules
    from segfacet.observed_range import build_observed_ranges

    config = bundled_default_config()

    driver_records = list(iter_driver_records())
    observed_ranges = build_observed_ranges(driver_records=driver_records, reference=reference)

    leaf_union: Set[str] = set()
    for _driver_id, record in driver_records:
        leaf_union |= iter_leaf_paths(record)

    # Mechanism A: dynamic access trace.
    attributions: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    rules = list(iter_rules())
    for _driver_id, record in driver_records:
        for rule in rules:
            def _runner(traced, _rule=rule):
                try:
                    _rule.evaluate(traced, config)
                except Exception:
                    pass
                return None

            sink = trace_record_access(record, _runner)
            for path in sink:
                attributions[path][rule.rule_id].add("observed")

    # Mechanism B: path-aware static AST scan (item 223; insight 2026-10-06-1935).
    # Each rule's ``evaluate`` is followed from its record parameter through
    # variables, loops and helper calls to the path every string-key read
    # indexes; the read is attributed to the leaf paths that path names and to
    # nothing else. A read whose base cannot be traced to the record
    # contributes nothing -- there is no last-segment fallback. A path that is
    # the dotted prefix of another leaf (an empty container in one driver
    # record, e.g. ``case.sequence`` on ``zero_label``) is a container, not a
    # field, and is never attributed (item 216, D18).
    containers = {p.rsplit(".", 1)[0] for p in leaf_union if "." in p}
    leaf_tokens = {
        path: _leaf_tokens(path) for path in leaf_union if path not in containers
    }

    for rule in rules:
        try:
            reads = _rule_read_paths(rule)
        except (OSError, SyntaxError, TypeError):
            # Only an unreadable source: a rule class with no source file
            # (defined ad hoc in a test/adversarial context; OSError from
            # _ModuleInfo / inspect, TypeError from inspect on a builtin) or
            # unparsable source. Mechanism B contributes nothing for it. Any
            # other error is a scan bug and propagates.
            continue
        for read in {_collapse_per_label(r) for r in reads}:
            for path, tokens in leaf_tokens.items():
                if _read_matches(read, tokens):
                    attributions[path][rule.rule_id].add("static")

    # Mechanism C: rule_id -> failure mode(s), from the committed geometric
    # corpus manifest's failure-kind cases (item 182).
    rule_mode_map = _scan_synth_rule_mode_map()

    # Declaration source (item 136): rule_id -> declared failure mode(s), read
    # from each rule's own class-attribute RuleModeDeclaration.
    declared_modes_by_rule: Dict[str, Tuple[int, ...]] = {
        rule_id: decl.modes
        for rule_id, decl in iter_rule_declarations()
        if decl is not None and decl.modes
    }

    # Mode-less declaration source (item 137): rule_ids whose declaration
    # states, with a reason, that they target no failure mode -- a source that
    # has *spoken* and said "no mode", categorically different from
    # "rule_unmapped" ("nobody has said").
    mode_less_by_rule: Set[str] = {
        rule_id
        for rule_id, decl in iter_rule_declarations()
        if decl is not None and decl.mode_less_reason
    }

    # Per-path classification (item 148): rule_id -> {leaf path -> role}, read
    # from each declaration's ``consumed_paths``. A rule contributes its
    # corpus-derived (mechanism C) and declared (item 136) modes to a path
    # only where that (rule, path) pair is classified "signal". A rule with
    # an empty ``consumed_paths`` contributes **nothing** -- never a
    # fall-back to item 136's rule-granular behaviour, which would be a
    # silent default; :func:`path_classification_conflicts` reports it.
    roles_by_rule: Dict[str, Dict[str, str]] = {
        rule_id: {cp.path: cp.role for cp in decl.consumed_paths}
        for rule_id, decl in iter_rule_declarations()
        if decl is not None
    }

    # Mechanism D: non-rule consumers.
    consumers_map = _mechanism_d_consumers(
        driver_records, _feature_docs_module.PATH_ALIASES, leaf_union
    )

    feature_docs = _feature_docs_module.FEATURE_DOCS
    mode_anchor_paths = _feature_docs_module.MODE_ANCHOR_PATHS
    status_overrides = _feature_docs_module.STATUS_OVERRIDES
    block_owners = _feature_docs_module.BLOCK_OWNERS
    group_intros = _feature_docs_module.GROUP_INTROS

    anchor_modes_by_path: Dict[str, Set[int]] = defaultdict(set)
    for mode, paths in mode_anchor_paths.items():
        for path in paths:
            anchor_modes_by_path[path].add(mode)

    if strict:
        undocumented = sorted(p for p in leaf_union if p not in feature_docs)
        if undocumented:
            raise FeatureDocMissing(
                "build_catalogue(strict=True): the following realised leaf "
                f"path(s) have no segfacet.feature_docs.FEATURE_DOCS entry: "
                f"{undocumented!r}."
            )
        stale = sorted(k for k in feature_docs if k not in leaf_union)
        if stale:
            raise CatalogueError(
                "build_catalogue(strict=True): the following "
                f"segfacet.feature_docs.FEATURE_DOCS key(s) match no realised "
                f"leaf path: {stale!r}."
            )

    entries_by_group: Dict[Tuple[str, str, str], List[CatalogueEntry]] = defaultdict(list)
    group_order: List[Tuple[str, str, str]] = []

    for path in sorted(leaf_union):
        doc = feature_docs.get(path)
        documented = doc is not None
        measures = doc.measures if doc is not None else ""
        computation = doc.computation if doc is not None else ""
        units = doc.units if doc is not None else ""
        scale_sensitivity = doc.scale_sensitivity if doc is not None else ""

        rule_ids = tuple(sorted(attributions.get(path, {}).keys()))
        rule_evidence = tuple(
            (rule_id, evidence)
            for rule_id in rule_ids
            for evidence in sorted(attributions[path][rule_id])
        )
        consumers = tuple(sorted(consumers_map.get(path, set())))

        anchor_modes = anchor_modes_by_path.get(path, set())
        mapped_rule_modes: Set[int] = set()
        declared_rule_modes: Set[int] = set()
        had_mode_less_rule = False
        had_unmapped_rule = False
        had_bookkeeping_rule = False
        had_not_read_rule = False
        had_condition_signal_rule = False
        mode_roles: List[Tuple[str, str]] = []
        for rule_id in rule_ids:
            modes_for_rule = rule_mode_map.get(rule_id)
            declared_for_rule = declared_modes_by_rule.get(rule_id)
            is_mode_less = rule_id in mode_less_by_rule
            role = roles_by_rule.get(rule_id, {}).get(path)
            if role is not None:
                mode_roles.append((rule_id, role))
            if role == "bookkeeping":
                had_bookkeeping_rule = True
            elif role == "not-read":
                had_not_read_rule = True
            elif role == "condition-signal":
                had_condition_signal_rule = True
            # Item 148: only a "signal" pair lets this rule's modes reach
            # this path. A bookkeeping / not-read / unclassified pair
            # contributes no mode, in either mechanism.
            if role == "signal":
                if modes_for_rule:
                    mapped_rule_modes.update(modes_for_rule)
                if declared_for_rule:
                    declared_rule_modes.update(declared_for_rule)
            if is_mode_less:
                had_mode_less_rule = True
            if not modes_for_rule and not declared_for_rule and not is_mode_less:
                had_unmapped_rule = True

        all_modes = anchor_modes | mapped_rule_modes | declared_rule_modes
        mode_evidence_parts: List[str] = []
        if anchor_modes:
            mode_evidence_parts.append("per_mode_metric")
        if mapped_rule_modes:
            mode_evidence_parts.append("rule_mode_map")
        if declared_rule_modes:
            mode_evidence_parts.append("rule_declaration")
        if had_mode_less_rule:
            mode_evidence_parts.append("rule_mode_less")
        if had_bookkeeping_rule:
            mode_evidence_parts.append("rule_bookkeeping")
        if had_not_read_rule:
            mode_evidence_parts.append("rule_not_read")
        if had_condition_signal_rule:
            mode_evidence_parts.append("rule_condition_signal")

        if all_modes:
            failure_modes = tuple(sorted(all_modes))
            mode_evidence = tuple(mode_evidence_parts)
        elif mode_evidence_parts:
            # Mode-less-only case (item 137): a consuming rule has declared
            # itself mode-less and nothing else spoke -- honestly report the
            # "rule_mode_less" tag, never "rule_unmapped".
            failure_modes = ()
            mode_evidence = tuple(mode_evidence_parts)
        elif rule_ids and had_unmapped_rule:
            failure_modes = ()
            mode_evidence = ("rule_unmapped",)
        else:
            failure_modes = ()
            mode_evidence = ()

        override = status_overrides.get(path)
        if override is not None:
            status = override[0]
        elif rule_ids or consumers:
            status = "keep"
        else:
            status = "unwired"

        group_title, stage_label, module = _group_for_path(path, block_owners)
        group_key = (group_title, stage_label, module)
        if group_key not in entries_by_group:
            group_order.append(group_key)

        entries_by_group[group_key].append(
            CatalogueEntry(
                path=path,
                group_title=group_title,
                stage_label=stage_label,
                module=module,
                measures=measures,
                computation=computation,
                units=units,
                scale_sensitivity=scale_sensitivity,
                documented=documented,
                origin="record",
                consuming_rules=rule_ids,
                rule_evidence=rule_evidence,
                consumers=consumers,
                failure_modes=failure_modes,
                mode_evidence=mode_evidence,
                mode_roles=tuple(mode_roles),
                status=status,
                observed=observed_ranges[path],
            )
        )

    # Groups in BLOCK_OWNERS order (falling back to first-seen order for any
    # path that matched no row -- "Uncategorised", never dropped).
    owner_order = [(row[1], row[2], row[3]) for row in block_owners]
    ordered_group_keys: List[Tuple[str, str, str]] = []
    for k in owner_order:
        if k in entries_by_group and k not in ordered_group_keys:
            ordered_group_keys.append(k)
    for k in group_order:
        if k not in ordered_group_keys:
            ordered_group_keys.append(k)

    groups: List[CatalogueGroup] = []
    all_entries: List[CatalogueEntry] = []
    for group_key in ordered_group_keys:
        title, stage_label, module = group_key
        entries = tuple(sorted(entries_by_group[group_key], key=lambda e: e.path))
        groups.append(
            CatalogueGroup(
                title=title,
                stage_label=stage_label,
                module=module,
                intro=group_intros.get(title, ""),
                entries=entries,
            )
        )
        all_entries.extend(entries)

    return FeatureCatalogue(
        schema_version=SCHEMA_VERSION,
        note=_CATALOGUE_NOTE,
        groups=tuple(groups),
        entries=tuple(all_entries),
    )


# =========================================================================== #
# Step 8b: rule <-> mode declaration/corpus agreement checker (item 136)
# =========================================================================== #


def rule_declaration_conflicts() -> Tuple[str, ...]:
    """Report every disagreement between each rule's ``RuleModeDeclaration``
    and the corpus-derived ``rule_id -> failure mode(s)`` map (item 136).

    Returns a sorted tuple of human-readable messages, empty when the two
    sources agree. Reports, for the shipped registry:

    - a registered rule with no declaration at all (naming its ``rule_id``);
    - a corpus-designated ``(rule_id, mode)`` pair the rule's declaration does
      not carry in ``modes`` (naming both);
    - a corpus-designated ``rule_id`` that **no rule registers** (naming it) --
      item 147: this direction used to iterate the registered rules and was
      therefore blind to exactly the case it was meant to catch, a corpus
      case designating a rule that does not exist;
    - a declared mode outside :data:`segfacet.failure_modes.SPECIFICATION`'s
      key set -- the authored failure-mode specification (item 144), which
      since item 146 is the in-code failure-mode catalogue -- (naming both).
      Before item 146 this check sourced its known-mode set from
      :data:`segfacet.feature_docs.MODE_ANCHOR_PATHS`'s keys instead; the two
      agreed exactly while both were 1-8, and the specification is the one
      that grows when a mode enters through the lifecycle (item 147 completes
      the collapse of the remaining partial sources onto it);
    - (item 156, Seam 1) a declared **known** mode with no mirroring
      ``IntendedRule`` edge (naming both rule and mode) -- the declaration ->
      specification direction. Unconditional: reported whether or not a
      corpus case exists for the mode (spec Assumption A2). This is the
      direction :func:`segfacet.failure_modes.specification_conflicts`
      does not check (it only checks specification -> declaration), and the
      corpus -> declaration direction below does not check either (a corpus
      case's silence about a mode says nothing about whether the
      specification mirrors a declaration that names it). A mode in the
      ``proposed`` state trips ``specification_conflicts``' proposed-drift
      check first, so a declaration naming one (item 147's ``(1, 2, 5)``
      control against ``reference_delta``) is not silent there: it returns
      messages, none naming the pair. Replay such a control against this
      function, not ``specification_conflicts`` alone (measured 2026-09-16).

    Item 147 retired the reserved ``"corpus"`` evidence tag and the
    declaration -> corpus direction it gated. That direction was an
    exact-element membership test over an unvalidated tuple, and the claim
    it stood for -- "a committed corpus case demonstrates this mode
    end-to-end" -- is data now: the per-edge ``evidence_rung`` on each
    ``IntendedRule`` in :data:`segfacet.failure_modes.SPECIFICATION`, whose
    own conformance check is
    :func:`segfacet.failure_modes.specification_conflicts`. A declaration's
    ``evidence`` is free-form provenance; nothing here reads an element of
    it for meaning, and no tag is an escape hatch from the corpus ->
    declaration direction, which is unconditional.

    Pure: never mutates the registry, never raises for a missing declaration
    (A3 -- absence is reported, not rejected).
    """
    from segfacet import failure_modes as _failure_modes_module
    from segfacet.heuristics.rule import iter_rule_declarations

    known_modes = set(_failure_modes_module.SPECIFICATION.keys())
    corpus_map = _scan_synth_rule_mode_map()

    declarations = dict(iter_rule_declarations())

    messages: List[str] = []
    for rule_id, decl in sorted(declarations.items()):
        if decl is None:
            messages.append(
                f"rule {rule_id!r} has no RuleModeDeclaration (mode_declaration is None)."
            )
            continue

        for mode in sorted(set(decl.modes) - known_modes):
            messages.append(
                f"rule {rule_id!r}: declared failure mode {mode} is outside "
                f"segfacet.failure_modes.SPECIFICATION's key set "
                f"{sorted(known_modes)!r}."
            )

        # Declaration -> specification (item 156, Seam 1). For every known
        # mode the rule declares, the specification must mirror it with an
        # IntendedRule edge -- the direction nothing checked before this
        # item: a rule could declare a listed mode with no edge naming it,
        # and both rule_declaration_conflicts() (corpus -> declaration only,
        # until now) and failure_modes.specification_conflicts()
        # (specification -> declaration only) stayed silent (A1, A2
        # unconditional -- reported whether or not a corpus case exists).
        for mode in sorted(set(decl.modes) & known_modes):
            edges = {
                edge.rule_id for edge in _failure_modes_module.SPECIFICATION[mode].intended_rules
            }
            if rule_id not in edges:
                messages.append(
                    f"rule {rule_id!r}: declares failure mode {mode}, but "
                    f"SPECIFICATION[{mode}].intended_rules carries no "
                    f"IntendedRule edge for it (edges: {sorted(edges)!r})."
                )

    # Corpus -> declaration. Item 147: iterate the **corpus map's** rule_ids,
    # not the registered rules, so a corpus case designating a rule_id no
    # rule registers is consulted and reported rather than skipped in
    # silence -- the direction that was previously blind.
    for rule_id in sorted(corpus_map):
        corpus_modes = set(corpus_map.get(rule_id, ()))
        if rule_id not in declarations:
            messages.append(
                f"rule {rule_id!r}: the corpus-derived map designates failure mode(s) "
                f"{sorted(corpus_modes)!r} for it, but no rule registers that "
                f"rule_id (registered: {sorted(declarations)!r})."
            )
            continue
        decl = declarations[rule_id]
        if decl is None:
            # Already reported above as an absent declaration; reporting the
            # same rule a second time here would say nothing new.
            continue
        declared_modes = set(decl.modes)
        # Item 150: a corpus case's expected rule set records co-detections
        # too (vision.md section 6, "co-detection is recorded, not
        # suppressed"), so a designated (rule, mode) pair is a conflict only
        # when the specification does NOT carry that rule in one of the
        # mode's corpus cases' expected_firing -- the specification, not the
        # Expectation literal, is the authority on what a case fires.
        # The exemption is narrow by construction: it covers a rule that
        # co-detects on the mode's case WITHOUT being one of that mode's own
        # intended rules. A rule the specification names as intended for the
        # mode must declare it, and a corpus designation it drops is reported
        # here -- otherwise this direction could never fire, because the scan
        # and the co-detection record derive from the same expected sets.
        recorded_co_detections = {
            mode_id
            for mode_id, mode_spec in _failure_modes_module.SPECIFICATION.items()
            if any(rule_id in case.expected_firing for case in mode_spec.corpus_cases)
            and rule_id not in {edge.rule_id for edge in mode_spec.intended_rules}
        }
        for mode in sorted(corpus_modes - declared_modes - recorded_co_detections):
            messages.append(
                f"rule {rule_id!r}: corpus designates failure mode {mode} but the "
                f"declaration does not include it (declared modes: {sorted(declared_modes)!r})."
            )

    return tuple(sorted(messages))


# =========================================================================== #
# Step 8c: per-path classification checker (item 148)
# =========================================================================== #


def path_classification_conflicts() -> Tuple[str, ...]:
    """Report every disagreement between each rule's declared per-path
    classification (``RuleModeDeclaration.consumed_paths``, item 148) and the
    leaf paths :func:`build_catalogue` actually attributes to that rule.

    Returns a sorted tuple of human-readable messages, empty when the
    declarations and the measured attribution agree. Every message names both
    the ``rule_id`` and the leaf path, so a failure points at the one literal
    to correct. Reports:

    - a registered rule with a non-empty ``modes`` and an empty
      ``consumed_paths`` — it contributes no mode to any path, and that is a
      declaration gap rather than a silent fall-back to item 136's
      rule-granular behaviour;
    - a registered rule with a non-empty ``modes`` and a non-empty
      ``consumed_paths`` whose entries carry no ``"signal"`` role (item 193)
      — the declaration still contributes no mode to any path, a state the
      previous check cannot see because ``consumed_paths`` is not empty;
    - a consumed ``(rule, path)`` pair with **no classification**
      (completeness);
    - a classified path the rule does **not** consume (soundness);
    - a pair classified ``"not-read"`` whose ``rule_evidence`` carries
      mechanism A's ``"observed"`` tag — a dynamic access trace saw the rule
      read it, which refutes the claim. This is what keeps ``"not-read"``
      from being an escape hatch from the other two directions.

    Kept **separate** from :func:`rule_declaration_conflicts` deliberately
    (item 148, Decisions D4): that function answers a different question —
    does a declaration agree with the corpus and the specification? — and is
    asserted clean by three items' tests, whose meaning folding these checks
    in would change.

    Pure: never mutates the registry, never raises.
    """
    from segfacet.heuristics.rule import iter_rule_declarations

    cat = build_catalogue(strict=True)

    reach_by_rule: Dict[str, Set[str]] = defaultdict(set)
    observed_by_rule: Dict[str, Set[str]] = defaultdict(set)
    for entry in cat.entries:
        for rule_id in entry.consuming_rules:
            reach_by_rule[rule_id].add(entry.path)
        for rule_id, evidence in entry.rule_evidence:
            if evidence == "observed":
                observed_by_rule[rule_id].add(entry.path)

    messages: List[str] = []
    for rule_id, decl in sorted(iter_rule_declarations(), key=lambda pair: pair[0]):
        if decl is None:
            # Absence of a declaration is rule_declaration_conflicts()'s
            # report, not this one's; saying it twice adds nothing.
            continue

        classified = {cp.path: cp.role for cp in decl.consumed_paths}
        consumed = reach_by_rule.get(rule_id, set())

        if decl.modes and not decl.consumed_paths:
            messages.append(
                f"rule {rule_id!r}: declares failure mode(s) {sorted(decl.modes)!r} but "
                f"its 'consumed_paths' classification is empty, so it contributes "
                f"no mode to any of the {len(consumed)} leaf path(s) the catalogue "
                f"attributes to it."
            )
        elif decl.modes and decl.consumed_paths and not any(
            cp.role == "signal" for cp in decl.consumed_paths
        ):
            messages.append(
                f"rule {rule_id!r}: declares failure mode(s) {sorted(decl.modes)!r} "
                f"but none of its {len(decl.consumed_paths)} 'consumed_paths' "
                f"entries is classified 'signal', so it contributes no mode to "
                f"any path."
            )

        for path in sorted(consumed - set(classified)):
            messages.append(
                f"rule {rule_id!r}: consumes leaf path {path!r} but its "
                f"'consumed_paths' classification does not cover it -- classify it "
                f"'signal', 'bookkeeping' or 'not-read'."
            )

        for path in sorted(set(classified) - consumed):
            messages.append(
                f"rule {rule_id!r}: classifies leaf path {path!r} as "
                f"{classified[path]!r}, but the catalogue does not attribute that "
                f"path to this rule."
            )

        for path in sorted(observed_by_rule.get(rule_id, set())):
            if classified.get(path) == "not-read":
                messages.append(
                    f"rule {rule_id!r}: classifies leaf path {path!r} as 'not-read', "
                    f"but mechanism A's dynamic access trace observed this rule "
                    f"reading it -- an observed read refutes a 'not-read' claim."
                )

    return tuple(sorted(messages))


# =========================================================================== #
# Step 9: serialisation
# =========================================================================== #


def _quantise(v: Optional[float]) -> Optional[float]:
    """Six-significant-digit quantisation (AC15): the value it would
    round-trip to at six significant digits. ``None`` passes through
    unchanged (AC4's null, never ``0``)."""
    return None if v is None else float(f"{v:.6g}")


def _population_range_to_dict(pop: Any) -> dict:
    # emission_range clamps a covered-but-not-informative population's
    # numeric fields to 0.0 (item 124 post-merge fix, 2026-08-30): a
    # sub-floor measurement is numerical noise whose exact bits are
    # platform-dependent, and this document is compared byte-exactly. See
    # segfacet.observed_range's module docstring, "Sub-floor noise is
    # clamped to 0.0 at emission". Classification already happened on the
    # raw, unclamped value (build_observed_ranges._derive_verdict) -- this
    # clamp only affects what gets written here.
    from segfacet.observed_range import emission_range

    minimum, maximum, span, magnitude = emission_range(pop)
    return {
        "population": pop.population,
        "source": list(pop.source),
        "covered": pop.covered,
        "count": pop.count,
        "minimum": _quantise(minimum),
        "maximum": _quantise(maximum),
        "span": _quantise(span),
        "magnitude": _quantise(magnitude),
        "informative": pop.informative,
    }


def _observed_range_to_dict(observed: Any) -> dict:
    return {
        "numeric": observed.numeric,
        "verdict": observed.verdict,
        "corpus": _population_range_to_dict(observed.corpus),
        "reference": _population_range_to_dict(observed.reference),
    }


_VERDICT_VOCABULARY = (
    "varies",
    "degenerate",
    "constant-synthetic",
    "placeholder",
    "non-numeric",
    "unobserved",
)


def catalogue_to_dict(cat: FeatureCatalogue) -> dict:
    """A deterministic, JSON-ready dict for *cat*. No timestamp, hostname,
    absolute path, or dependency-version string."""
    observed_summary = {verdict: 0 for verdict in _VERDICT_VOCABULARY}
    for entry in cat.entries:
        observed_summary[entry.observed.verdict] += 1

    return {
        "schema_version": cat.schema_version,
        "note": cat.note,
        "observed_summary": observed_summary,
        "groups": [
            {
                "title": g.title,
                "stage": g.stage_label,
                "module": g.module,
                "intro": g.intro,
                "entries": [
                    {
                        "path": e.path,
                        "measures": e.measures,
                        "computation": e.computation,
                        "units": e.units,
                        "scale_sensitivity": e.scale_sensitivity,
                        "documented": e.documented,
                        "origin": e.origin,
                        "consuming_rules": list(e.consuming_rules),
                        "rule_evidence": [list(pair) for pair in e.rule_evidence],
                        "consumers": list(e.consumers),
                        "failure_modes": list(e.failure_modes),
                        "mode_evidence": list(e.mode_evidence),
                        "mode_roles": [list(pair) for pair in e.mode_roles],
                        "status": e.status,
                        "observed": _observed_range_to_dict(e.observed),
                    }
                    for e in g.entries
                ],
            }
            for g in cat.groups
        ],
    }


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _fmt_population(pop: Any) -> str:
    # See _population_range_to_dict: emission_range clamps sub-floor noise
    # to 0.0 so the Markdown table's "observed range" cell agrees with the
    # JSON's clamped values instead of embedding platform-dependent noise
    # digits into a byte-compared document.
    from segfacet.observed_range import emission_range

    minimum, maximum, _span, _magnitude = emission_range(pop)
    if minimum is None:
        return "\u2014"
    minimum = _quantise(minimum)
    maximum = _quantise(maximum)
    return f"{minimum:.6g}\u2013{maximum:.6g}"


def _fmt_observed_range(observed: Any) -> str:
    return f"corpus {_fmt_population(observed.corpus)} \u00b7 ref {_fmt_population(observed.reference)}"


def render_markdown(cat: FeatureCatalogue) -> str:
    """Render *cat* as a single Markdown table, one row per entry, in the
    catalogue's own deterministic order."""
    lines = [
        f"# Feature & Rule Catalogue ({len(cat.entries)} entries)",
        "",
        _md_escape(cat.note),
        "",
        "| path | module / item | measures | computation | units | "
        "scale sensitivity | observed range | observed verdict | "
        "Mode(s) | Mode role(s) | consuming rules | status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in cat.entries:
        module_item = f"{e.stage_label} \u00b7 {e.module}" if e.stage_label else e.module
        modes = ", ".join(str(m) for m in e.failure_modes)
        mode_roles = ", ".join(f"{rule_id}: {role}" for rule_id, role in e.mode_roles)
        rules = ", ".join(e.consuming_rules)
        cells = [
            e.path,
            _md_escape(module_item),
            _md_escape(e.measures),
            _md_escape(e.computation),
            _md_escape(e.units),
            _md_escape(e.scale_sensitivity),
            _md_escape(_fmt_observed_range(e.observed)),
            e.observed.verdict,
            modes,
            _md_escape(mode_roles),
            rules,
            e.status,
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# =========================================================================== #
# __main__
# =========================================================================== #


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Regenerate the generated feature & rule catalogue (item 103)."
    )
    parser.add_argument("--json", type=Path, default=_DEFAULT_JSON_PATH)
    parser.add_argument("--md", type=Path, default=_DEFAULT_MD_PATH)
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help=(
            "Path to a reference-distribution artifact to build the "
            "observed-range reference population from (item 124). Defaults "
            "to the bundled production reference."
        ),
    )
    args = parser.parse_args(argv)

    cat = build_catalogue(strict=True, reference=args.reference)

    json_text = json.dumps(catalogue_to_dict(cat), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    md_text = render_markdown(cat)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(json_text.encode("utf-8"))
    args.md.write_bytes(md_text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
