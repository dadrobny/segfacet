"""The failure-mode specification module (item 144; Stage 30 -- Failure-Mode
Specification: the vision.md §6 catalogue as an authored source).

This module is the **primary record** vision.md §6 describes: one frozen
:class:`ModeSpec` declaration per §6 failure mode, shaped after
``RuleModeDeclaration`` (:mod:`segfacet.heuristics.rule`, item 136), from
which ``docs/aide/failure_modes.generated.{md,json}`` are rendered by
zero-argument regeneration (:func:`main`). Today the catalogue exists as five
partial sources that agree without any of them being a specification
(queue-020, "The five partial sources this stage collapses"); this module is
the object the rest of the stage (items 145-151) reads, writes into, and
renders.

**This module ships the schema, the validation, the derivation and the
rendering.** Item 144 shipped a minimal seed set of two entries to exercise
both derivation paths end-to-end (item spec A4); item 145 entered vision.md
§6's eight hypothesised modes; item 146 added the ninth mode and the first
``proposed`` entry; item 147 collapsed the five partial sources onto it.
Item 150's maintainer sign-off (2026-09-14) then **re-organised the
catalogue** -- see "Taxonomy as signed off" below -- so :data:`SPECIFICATION`
now carries ten modes in a one-tier hierarchy plus one :data:`CONDITIONS`
entry.

Taxonomy as signed off (item 150, 2026-09-14)
---------------------------------------------
Ids are assigned in this module and are stable from the sign-off on; the
vision.md §6 list is provenance only (:data:`VISION_SEED_DISPOSITION`), so a
§6 re-issue through the create-vision entry point is owed and does not move
an id. The tree runs generic to specific, and a case that meets a parent's
definition but no sub-mode's rule is classified at the parent::

    1  Segmentation accuracy (over-/under-segmentation)   needs-ground-truth
       2  Fused or split vertebra segments                 single-channel (proxies, to be proven)
       3  Disconnected components / islands                single-channel
       4  Vertebra not segmented                           needs-ground-truth
    5  Semantic mislabelling                               single-channel (proxies)
       6  Implausible label sequence                       single-channel; severity fail
       7  Shifted label sequence                           needs-external-classifier; proposed
       8  Collapsed or duplicated label set                single-channel; proposed
    9  Overlapping segments                                structurally-unobservable
    10 Implausible tissue under a label                    needs-paired-scan
    Condition: FOV truncation (was mode 6)                  border rule records it

What moved, and why (the full walkthrough is transcribed in
``docs/aide/items/150-maintainer-sign-off-of-the-specification.md``):

* The old mode 1 ("label not aligned with the vertebra it names") is
  retired: it was covered by semantic mislabelling, and the spline-offset
  signal it rested on is an anatomy-classification signal
  (spondylolisthesis, scoliosis), not a failure signal. ``mislabel``'s
  spline-offset detector therefore serves **no** mode; its ordering
  detector serves mode 6.
* The old mode 2 ("over-/under-segmentation") is split: overall accuracy
  is the new catch-all mode 1, and fused/split correspondence is mode 2.
  A label in two large pieces is a connectivity defect, so
  ``mode2_fragment`` and ``fragmentation``'s component detector move to
  mode 3.
* "Missing interior level" is a label-sequence finding, so ``coverage``'s
  interior-gap detector and ``mode5_remove_level`` move to mode 6; mode 4
  (vertebra not segmented) keeps ``coverage``'s opt-in span/count checks
  and gains ``remove_level_relabel`` -- a vertebra removed with the labels
  renumbered to stay continuous -- which no shipped rule detects.
* A relabel swap breaks the sequence, so ``mode4_relabel_swap`` and
  ``mislabel``'s ordering detector move to mode 6. Mode 5 keeps only the
  per-level-geometry proxy (``reference_delta``).
* Mode 6 (partial vertebra at the border) becomes the FOV-truncation
  **condition**: ``border`` declares no mode, and ``mode6_crop_at_border``
  is the condition's fixture, still expecting ``{border, mislabel}``.
* Two observability classes are added, ``needs-ground-truth`` and
  ``needs-external-classifier``; ``bounds`` and ``reference_delta`` are
  declared for every mode their volume/extent signal can proxy.
* ``"validated"`` now requires a non-empty agreeing case that fires one of
  the mode's **own** intended rules (:func:`_demonstrates`); co-detections
  and empty expected sets never validate.

Known divergence, deferred to a follow-up item: the Stage-18/29 eval
harness (``segfacet.eval.per_mode``, ``severity_ladder``,
``per_mode_cohort``) is still keyed by the **pre-sign-off** ids 1-8 and
names them through ``segfacet.eval.per_mode.LEGACY_STAGE18_MODE_NAMES``;
re-keying it needs re-measured ladder constants and is not this module's.

Adding the ninth mode (item 146, 2026-09-04)
--------------------------------------------
Mode 9 ("Implausible tissue under a label") is deliberately **not** one of
vision.md §6's numbered eight. It entered through this module's schema,
acquired its rules by their declarations moving from mode-less to
``modes=(9,)``, and derives ``"validated"`` from live state -- evidence for
§6's own claim that a mode can be added **without everything being rebuilt**:
neither the eight seed entries, the ``ModeSpec`` schema, the rule engine, nor
any rule's ``evaluate`` body was touched. What had to change, and only this:

* ``src/segfacet/failure_modes.py`` -- ``_MODE_9`` and ``_MODE_10`` authored
  and appended to the ``_build_specification`` tuple; :func:`measured_firing`
  gained a first-level dispatch on ``CorpusCaseExpectation.corpus``;
  :func:`specification_conflicts` gained the ``proposed``-drift check;
  :func:`render_markdown` gained ``- (none)`` for an empty section; and
  :func:`derive_status` gained a declaring-rule precondition on
  ``"validated"`` (the item-145 review finding, ``docs/aide/insights.md``,
  2026-09-03).
* ``src/segfacet/heuristics/intensity.py`` and
  ``src/segfacet/heuristics/intensity_reference_delta.py`` -- the
  ``mode_declaration`` **literal** only, from ``mode_less_reason=...`` to
  ``modes=(9,)`` with an ``evidence`` tuple naming
  ``tests/corpus/intensity/manifest.json``. No threshold, condition,
  severity or ``evaluate`` line changed; ``run_rules``' output on a fixed
  record is unchanged, because the declaration is metadata the engine never
  reads.
* ``src/segfacet/synth/regression.py`` -- ``loaded_intensity_case`` and
  ``intensity_pipeline_findings``, the intensity sibling of
  ``loaded_seg_image`` / ``pipeline_findings``. The second committed corpus
  had no public harness at all until this item.
* ``src/segfacet/synth/__init__.py`` -- both names re-exported, additively.
* ``src/segfacet/synth/intensity.py`` -- the manifest's per-case
  ``failure_mode`` / ``failure_mode_name`` / ``detection`` /
  ``expected_firing`` fields, written by the generator (never hand-edited)
  at an unchanged ``INTENSITY_MANIFEST_VERSION``, since the change is purely
  additive.
* ``src/segfacet/catalogue.py`` -- ``rule_declaration_conflicts``' known-mode
  set now comes from :data:`SPECIFICATION`'s keys rather than
  ``feature_docs.MODE_ANCHOR_PATHS``' (item 146 A7; item 147 completes the
  collapse). ``MODE_ANCHOR_PATHS`` itself is untouched and its key set stays
  exactly 1-8, which is why mode 9's candidate features carry
  ``role="hypothesised"`` and never ``"stage18-metric-anchor"``.

Mode 10 ("Collapsed or duplicated label set") is the catalogue's first
``proposed`` entry: no rules, no corpus cases, one hypothesised candidate
feature, and a status that derives ``"proposed"`` from that emptiness. It
exists so the conformance report shows a listed, unimplemented mode, and so
the rendering has to render one legibly. Its detector is explicitly item
146's non-goal; nothing here fabricates one.

Becoming the record (item 147, 2026-09-04)
------------------------------------------
Items 144-146 built the specification beside the five partial sources
queue-020 names; item 147 collapses those sources onto it, so this module
is now the single place an operational claim about a failure mode is
authored:

* ``ModeSpec`` gained two authored fields. ``short_name`` carries the
  paraphrase both committed corpus manifests hold in ``failure_mode_name``
  (``segfacet.synth.perturbation.FAILURE_MODE_NAMES`` is now
  :func:`failure_mode_names` derived over :data:`SPECIFICATION`, not a
  hand-typed literal); ``mechanism`` carries the evidence-rung mechanism
  sentence that ``segfacet.traceability.MODE_RUNGS`` used to author. Both
  default to ``""`` so a standalone ``ModeSpec(...)`` in a test keeps
  working; every shipped entry carries both, non-empty.
* ``traceability.MODE_RUNGS`` / ``ModeRung`` / ``RUNGS`` are retired.
  :data:`RUNG_LABELS` moved here verbatim, and the matrix's per-mode rung
  is :func:`derive_mode_rung` over the per-edge rungs item 145 authored.
* The ``vision.md`` §6 parse moved here as the public
  :func:`vision_seed_titles`. It is the **seed**, not the record: the one
  kept conformance check in that direction is that modes 1-8's ``name``
  fields still equal §6's list. No other module under ``src/segfacet/``
  reads ``vision.md``.
* The reserved ``"corpus"`` evidence tag is retired rather than hardened
  (``docs/aide/insights.md``, item 136, 2026-09-02, three located defects):
  it was an exact-element membership test over an unvalidated tuple. The
  claim it stood for is data now -- item 145's per-edge rungs -- and the
  seam it gated is replaced by :func:`specification_conflicts`' two new
  specification-side directions (an ``IntendedRule`` edge the named rule
  does not declare; a committed corpus case the specification does not
  carry, or whose manifest expectation disagrees with it).

Mode 7's rung rationale is settled here as one measured sentence
(:data:`SPECIFICATION`\\ ``[7].mechanism``), correcting the ``rank(v) ==
v - 1`` claim item 145 transcribed from ``MODE_RUNGS``: see that field.

Lifecycle status
-----------------
``status`` is **authored only** for ``"proposed"`` and ``"specified"``
(:data:`AUTHORED_STATUSES`) -- constructing a :class:`ModeSpec` with
``status="implemented"`` or ``status="validated"`` raises ``ValueError``
even though both are members of :data:`STATUSES`. ``"implemented"`` (>=1
**registered** rule declares the mode) and ``"validated"`` (every corpus
case's **measured** firing set equals its authored ``expected_firing``) are
derived from live state on every read and on every regeneration by
:func:`derive_status` -- never authored, and a value forced past
``__post_init__`` (via ``object.__setattr__``) is reported by
:func:`specification_conflicts`, naming the mode.

Scope fence
-----------
No new rule, threshold, extractor, verdict, report schema or CLI behaviour.
Nothing under ``src/segfacet/heuristics/`` changes: :func:`derive_status`
*reads* the registry and each rule's ``RuleModeDeclaration``; moving any
declaration onto this schema is item 146's/147's. No corpus case is added or
changed; the committed corpus (``tests/corpus/manifest.json``) is **read** to
measure firing sets. ``vision.md`` and ``roadmap.md`` are not edited.

Determinism contract
---------------------
:func:`specification_to_dict` and :func:`render_markdown` never mutate any
input and return a fresh tree on every call; two calls compare equal and
neither leaks state into a later call. Heavy imports (NumPy / SciPy /
NiBabel, reached only through :mod:`segfacet.synth.regression` inside
:func:`measured_firing`) are deferred into function bodies, per house style
(:mod:`segfacet.traceability`), so ``import segfacet.failure_modes`` alone
stays cheap.

Public API
----------
``ModeSpec``, ``CandidateFeature``, ``IntendedRule``, ``CorpusCaseExpectation``
    Frozen dataclasses (the schema).
``SPECIFICATION``
    The immutable, ascending-by-id seed (a ``MappingProxyType``).
``iter_modes() -> Iterator[ModeSpec]``
    Yield the seed modes in ascending ``id`` order. Takes no argument.
``vision_seed_titles() -> Dict[int, str]``
    The vision.md §6 numbered titles, parsed live (item 147 AC4) -- this
    module is the only reader of that document under ``src/segfacet/``.
``failure_mode_names() -> Mapping[int, str]``
    ``{0: CLEAN_CONTROL_NAME}`` plus every mode's ``short_name``; the
    binding ``segfacet.synth.perturbation.FAILURE_MODE_NAMES`` resolves to.
``CLEAN_CONTROL_NAME`` / ``RUNG_LABELS``
    The key-0 clean-control name, and the human-readable rung labels moved
    here from ``segfacet.traceability`` (item 147).
``derive_status(mode) -> str`` / ``derive_mode_rung(mode) -> Optional[str]``
    Live derivations (AC9/AC10, AC14).
``measured_firing(case) -> Tuple[str, ...]`` / ``case_agrees(case) -> bool``
    Drive one ``CorpusCaseExpectation`` through the same public harness
    ``segfacet.synth.regression`` exposes (dispatching on the manifest case's
    ``detection`` field), and compare against its authored
    ``expected_firing``.
``specification_conflicts(modes=None) -> Tuple[str, ...]``
    The conformance check: a hand-set derived ``status`` past construction;
    ``proposed`` drift; an ``IntendedRule`` edge the named rule does not
    declare (or that no rule registers); a committed corpus case the
    specification does not carry, or whose manifest expectation disagrees
    with it. Defaults to the shipped :data:`SPECIFICATION`.
``specification_to_dict() -> dict``
    A deterministic, JSON-ready dict. Takes no argument.
``render_markdown() -> str``
    A deterministic Markdown rendering of the same specification.
``main(argv=None) -> int``
    ``python -m segfacet.failure_modes [--json PATH] [--md PATH]``; defaults
    to the two committed artifact paths under ``docs/aide/``.

Sign-off
--------
Signed off: 2026-09-14 -- accepted with changes: the maintainer reviewed all ten entries of the item-149 rendering and re-organised the catalogue (one mode retired, one split, one re-homed as a condition, one added, ids re-assigned in a one-tier hierarchy, two observability classes added); the entry-by-entry walkthrough is transcribed in docs/aide/items/150-maintainer-sign-off-of-the-specification.md.

The changes are the "Taxonomy as signed off" section above, applied in
this module, the rule declarations, both committed corpora and
``feature_docs.MODE_ANCHOR_PATHS``; the eval-harness re-key, the vision.md
§6 re-issue and the new rules the review asked for are follow-up items.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import MappingProxyType
from typing import Dict, FrozenSet, Iterable, Iterator, Mapping, Optional, Tuple

__all__ = [
    "ModeSpec",
    "CandidateFeature",
    "IntendedRule",
    "CorpusCaseExpectation",
    "SPECIFICATION",
    "ConditionSpec",
    "CONDITIONS",
    "iter_modes",
    "iter_conditions",
    "mode_path",
    "VISION_SEED_DISPOSITION",
    "vision_seed_conflicts",
    "vision_seed_titles",
    "failure_mode_names",
    "CLEAN_CONTROL_NAME",
    "RUNG_LABELS",
    "derive_status",
    "derive_mode_rung",
    "measured_firing",
    "case_agrees",
    "specification_conflicts",
    "specification_to_dict",
    "render_markdown",
    "main",
    "STATUSES",
    "AUTHORED_STATUSES",
    "OBSERVABILITY",
    "PROVENANCE",
    "CANDIDATE_ROLES",
    "EVIDENCE_RUNGS",
    "SCHEMA_VERSION",
    "JSON_PATH",
    "MD_PATH",
]

SCHEMA_VERSION = "2.0"

_REPO_ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.json"
MD_PATH = _REPO_ROOT / "docs" / "aide" / "failure_modes.generated.md"

_NOTE = (
    "Generated by `python -m segfacet.failure_modes` (item 144; taxonomy "
    "signed off at item 150, 2026-09-14). Do not "
    "hand-edit this document -- edit the seed ModeSpec entries in "
    "src/segfacet/failure_modes.py (the authored fields), then regenerate. "
    "`status_authored` is the hand-set proposed/specified value; "
    "`status_derived` and `derived_rung` are computed live from the rule "
    "registry and the committed corpus on every regeneration -- never "
    "hand-set past construction (see specification_conflicts())."
)


# =========================================================================== #
# Closed vocabularies (AC4-AC6, AC12, AC13, AC15)
# =========================================================================== #

STATUSES: Tuple[str, ...] = ("proposed", "specified", "implemented", "validated")
AUTHORED_STATUSES: Tuple[str, ...] = ("proposed", "specified")

OBSERVABILITY: Tuple[str, ...] = (
    "single-channel-observable",
    "needs-paired-scan",
    "needs-ground-truth",
    "needs-external-classifier",
    "structurally-unobservable",
)

PROVENANCE: Tuple[str, ...] = ("hypothesised", "discovered")

CANDIDATE_ROLES: Tuple[str, ...] = ("stage18-metric-anchor", "hypothesised")

# Strongest-first (A6 / AC14: "a mode's rung is derived as the strongest of
# its edges").
EVIDENCE_RUNGS: Tuple[str, ...] = (
    "synthetic-demonstrable",
    "needs-real-data",
    "structurally-unobservable",
)
_RUNG_STRENGTH: Dict[str, int] = {rung: index for index, rung in enumerate(EVIDENCE_RUNGS)}

#: Human-readable label per rung. Moved here verbatim from
#: ``segfacet.traceability`` by item 147 (A11), beside the vocabulary it
#: labels -- ``traceability`` kept a second, identical copy of both the
#: vocabulary (``RUNGS``) and these labels while the rungs themselves were
#: authored there.
RUNG_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "synthetic-demonstrable": "Demonstrated end-to-end on a synthetic corpus case",
        "needs-real-data": "Needs real data, or a corpus the fixtures cannot express",
        "structurally-unobservable": "Structurally unobservable in the supported input format",
    }
)

#: The name the two committed corpus manifests carry for the key-0 clean
#: control. Key 0 is **not** a failure mode and has no ``ModeSpec``; it stays
#: an explicit constant so :func:`failure_mode_names` can carry it without
#: the specification having to pretend a tenth-plus-one mode exists.
CLEAN_CONTROL_NAME = "clean control (no failure)"


def _accepted_severities() -> FrozenSet[str]:
    """Derived from :class:`segfacet.verdict.Severity`, minus ``"pass"``
    (A9/AC15) -- never hand-typed, so this stays honest if the enum changes."""
    from segfacet.verdict import Severity

    return frozenset(s.label for s in Severity) - {"pass"}


# =========================================================================== #
# Frozen record dataclasses -- the schema (AC2, AC12, AC13)
#
# Only ModeSpec validates (its __post_init__ walks the whole tree it owns);
# CandidateFeature / IntendedRule / CorpusCaseExpectation are plain frozen
# records so a caller can construct an intentionally-invalid one to exercise
# ModeSpec's validation (the item spec's Testing Strategy pattern).
# =========================================================================== #


@dataclasses.dataclass(frozen=True)
class CandidateFeature:
    """One candidate feature path for a mode, labelled with its **role**
    (AC12) -- ``"stage18-metric-anchor"`` (validated against
    ``segfacet.feature_docs.MODE_ANCHOR_PATHS[mode.id]`` by
    :class:`ModeSpec`) or ``"hypothesised"`` (not yet anchored)."""

    path: str
    role: str


@dataclasses.dataclass(frozen=True)
class IntendedRule:
    """One mode <-> rule edge, carrying the **per-edge evidence rung**
    (AC13, gate 3 decision 3). ``detector`` names the specific detector
    within a rule that has several; may be empty."""

    rule_id: str
    detector: str
    evidence_rung: str


@dataclasses.dataclass(frozen=True)
class CorpusCaseExpectation:
    """One committed corpus case's **expected** firing set for a mode (A2:
    the full set of ``rule_id``s the case's detection path produces, not the
    manifest's narrower ``expected_rule_ids``)."""

    case_id: str
    corpus: str
    expected_firing: Tuple[str, ...]
    reason: str


@dataclasses.dataclass(frozen=True)
class ModeSpec:
    """One frozen failure-mode declaration, carrying exactly vision.md §6's
    fields (AC2). Validates the whole tree it owns in ``__post_init__``;
    every raised ``ValueError`` names the offending mode (``id``, or
    ``name`` where ``id`` itself is the offending field) and field."""

    id: int
    name: str
    short_name: str = ""
    parent: Optional[int] = None
    definition: str = ""
    discriminator: str = ""
    mechanism: str = ""
    observability: str = ""
    candidate_features: Tuple[CandidateFeature, ...] = ()
    intended_rules: Tuple[IntendedRule, ...] = ()
    corpus_cases: Tuple[CorpusCaseExpectation, ...] = ()
    severity: str = ""
    status: str = ""
    provenance: str = ""

    def __post_init__(self) -> None:
        self._require_valid_id()
        self._require_valid_parent()

        # `short_name` and `mechanism` are the two fields item 147 moved onto
        # this schema from the partial sources it retired
        # (``synth.perturbation.FAILURE_MODE_NAMES``' paraphrases and
        # ``traceability.MODE_RUNGS``' mechanism sentences). They default to
        # `""` at the dataclass level so every standalone ``ModeSpec(...)``
        # construction in the suite keeps working (item 147 A2), and the
        # "every shipped entry carries both, non-empty" invariant is asserted
        # over SPECIFICATION by the test suite rather than enforced here.
        # A non-str value is still rejected: it would reach the rendering.
        for optional_field_name in ("short_name", "mechanism"):
            optional_value = getattr(self, optional_field_name)
            if not isinstance(optional_value, str):
                raise ValueError(
                    f"ModeSpec {self.id}: '{optional_field_name}' must be a str "
                    f"(possibly empty), got {type(optional_value).__name__}."
                )

        for field_name in (
            "name",
            "definition",
            "discriminator",
            "observability",
            "severity",
            "status",
            "provenance",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"ModeSpec {self.id}: '{field_name}' must be a non-empty str, "
                    f"got {value!r}."
                )

        if self.status not in STATUSES:
            raise ValueError(
                f"ModeSpec {self.id}: 'status' {self.status!r} is not a member of "
                f"STATUSES {STATUSES}."
            )
        if self.status not in AUTHORED_STATUSES:
            raise ValueError(
                f"ModeSpec {self.id}: 'status' may only be authored as one of "
                f"AUTHORED_STATUSES {AUTHORED_STATUSES}; {self.status!r} is derived "
                f"exclusively by derive_status(), never hand-authored past construction."
            )

        if self.observability not in OBSERVABILITY:
            raise ValueError(
                f"ModeSpec {self.id}: 'observability' {self.observability!r} is not a "
                f"member of OBSERVABILITY {OBSERVABILITY}."
            )

        if self.provenance not in PROVENANCE:
            raise ValueError(
                f"ModeSpec {self.id}: 'provenance' {self.provenance!r} is not a member "
                f"of PROVENANCE {PROVENANCE}."
            )

        accepted_severities = _accepted_severities()
        if self.severity not in accepted_severities:
            raise ValueError(
                f"ModeSpec {self.id}: 'severity' {self.severity!r} is not a member of "
                f"{sorted(accepted_severities)} (derived from segfacet.verdict.Severity, "
                f"minus 'pass')."
            )

        self._validate_candidate_features()
        self._validate_intended_rules()
        self._validate_corpus_cases()

    def _require_valid_id(self) -> None:
        value = self.id
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"ModeSpec {self.name!r}: 'id' must be an int >= 1, got {value!r}."
            )

    def _require_valid_parent(self) -> None:
        value = self.parent
        if value is None:
            return
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(
                f"ModeSpec {self.id}: 'parent' must be an int >= 1 or None, got "
                f"{value!r}."
            )
        if value == self.id:
            raise ValueError(
                f"ModeSpec {self.id}: 'parent' must not be the mode's own id."
            )

    def _validate_candidate_features(self) -> None:
        if not isinstance(self.candidate_features, tuple):
            raise ValueError(
                f"ModeSpec {self.id}: 'candidate_features' must be a tuple, got "
                f"{type(self.candidate_features).__name__}."
            )

        from segfacet import feature_docs as feature_docs_module

        for feature in self.candidate_features:
            if not isinstance(feature, CandidateFeature):
                raise ValueError(
                    f"ModeSpec {self.id}: 'candidate_features' elements must be "
                    f"CandidateFeature, got {feature!r}."
                )
            if feature.role not in CANDIDATE_ROLES:
                raise ValueError(
                    f"ModeSpec {self.id}: candidate feature {feature.path!r} has role "
                    f"{feature.role!r}, which is not a member of CANDIDATE_ROLES "
                    f"{CANDIDATE_ROLES}."
                )
            if feature.role == "stage18-metric-anchor":
                anchor_paths = feature_docs_module.MODE_ANCHOR_PATHS.get(self.id)
                if anchor_paths is None:
                    raise ValueError(
                        f"ModeSpec {self.id}: candidate feature {feature.path!r} is "
                        f"labelled 'stage18-metric-anchor', but mode {self.id} has no "
                        f"entry in segfacet.feature_docs.MODE_ANCHOR_PATHS (keys: "
                        f"{sorted(feature_docs_module.MODE_ANCHOR_PATHS)})."
                    )
                if feature.path not in anchor_paths:
                    raise ValueError(
                        f"ModeSpec {self.id}: candidate feature path {feature.path!r} "
                        f"is labelled 'stage18-metric-anchor' but is not an element of "
                        f"MODE_ANCHOR_PATHS[{self.id}] {anchor_paths!r}."
                    )

    def _validate_intended_rules(self) -> None:
        if not isinstance(self.intended_rules, tuple):
            raise ValueError(
                f"ModeSpec {self.id}: 'intended_rules' must be a tuple, got "
                f"{type(self.intended_rules).__name__}."
            )

        seen_rule_ids: set = set()
        for rule in self.intended_rules:
            if not isinstance(rule, IntendedRule):
                raise ValueError(
                    f"ModeSpec {self.id}: 'intended_rules' elements must be "
                    f"IntendedRule, got {rule!r}."
                )
            if not rule.rule_id:
                raise ValueError(
                    f"ModeSpec {self.id}: an intended rule has an empty 'rule_id' "
                    f"({rule!r})."
                )
            if rule.evidence_rung not in EVIDENCE_RUNGS:
                raise ValueError(
                    f"ModeSpec {self.id}: intended rule {rule.rule_id!r} has "
                    f"evidence_rung {rule.evidence_rung!r}, which is not a member of "
                    f"EVIDENCE_RUNGS {EVIDENCE_RUNGS}."
                )
            if rule.rule_id in seen_rule_ids:
                raise ValueError(
                    f"ModeSpec {self.id}: duplicate intended-rule rule_id "
                    f"{rule.rule_id!r}."
                )
            seen_rule_ids.add(rule.rule_id)

    def _validate_corpus_cases(self) -> None:
        if not isinstance(self.corpus_cases, tuple):
            raise ValueError(
                f"ModeSpec {self.id}: 'corpus_cases' must be a tuple, got "
                f"{type(self.corpus_cases).__name__}."
            )

        seen_case_ids: set = set()
        for case in self.corpus_cases:
            if not isinstance(case, CorpusCaseExpectation):
                raise ValueError(
                    f"ModeSpec {self.id}: 'corpus_cases' elements must be "
                    f"CorpusCaseExpectation, got {case!r}."
                )
            if not isinstance(case.expected_firing, tuple):
                raise ValueError(
                    f"ModeSpec {self.id}: corpus case {case.case_id!r}'s "
                    f"'expected_firing' must be a tuple, got "
                    f"{type(case.expected_firing).__name__}."
                )
            if case.case_id in seen_case_ids:
                raise ValueError(
                    f"ModeSpec {self.id}: duplicate corpus case_id {case.case_id!r}."
                )
            seen_case_ids.add(case.case_id)


@dataclasses.dataclass(frozen=True)
class ConditionSpec:
    """One case **condition** (item 150): a state of the case that gates
    other rules and is deliberately **not** a failure mode. FOV truncation
    is the first: the maintainer's 2026-09-14 sign-off retired failure mode
    6 ("partial vertebra at the image border") into this section, because
    a truncated vertebra is a property of the scan, not a defect of the
    segmentation. A condition carries the rule(s) that *record* it, the
    rule(s) that grant it an exemption today, and its corpus fixtures with
    expected firing sets -- measured and compared exactly as a mode's are,
    so a condition case is never a silent hole in the conformance report.
    """

    id: str
    name: str
    short_name: str
    definition: str
    mechanism: str
    candidate_features: Tuple[str, ...]
    recording_rules: Tuple[str, ...]
    exempting_rules: Tuple[str, ...]
    corpus_cases: Tuple[CorpusCaseExpectation, ...]

    def __post_init__(self) -> None:
        for field_name in ("id", "name", "short_name", "definition", "mechanism"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"ConditionSpec {self.id!r}: '{field_name}' must be a non-empty "
                    f"str, got {value!r}."
                )
        for field_name in (
            "candidate_features",
            "recording_rules",
            "exempting_rules",
            "corpus_cases",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, tuple):
                raise ValueError(
                    f"ConditionSpec {self.id!r}: '{field_name}' must be a tuple, got "
                    f"{type(value).__name__} -- a bare str or a list is not accepted."
                )
        if not self.recording_rules:
            raise ValueError(
                f"ConditionSpec {self.id!r}: 'recording_rules' must name at least "
                f"one rule."
            )
        seen: set = set()
        for case in self.corpus_cases:
            if not isinstance(case, CorpusCaseExpectation):
                raise ValueError(
                    f"ConditionSpec {self.id!r}: 'corpus_cases' elements must be "
                    f"CorpusCaseExpectation, got {case!r}."
                )
            if not isinstance(case.expected_firing, tuple):
                raise ValueError(
                    f"ConditionSpec {self.id!r}: corpus case {case.case_id!r}'s "
                    f"'expected_firing' must be a tuple."
                )
            if case.case_id in seen:
                raise ValueError(
                    f"ConditionSpec {self.id!r}: duplicate corpus case_id "
                    f"{case.case_id!r}."
                )
            seen.add(case.case_id)


# =========================================================================== #
# The catalogue as signed off (item 150, 2026-09-14).
#
# Ids are assigned HERE and are stable from this sign-off on; the vision.md
# section 6 list is provenance only (see VISION_SEED_DISPOSITION). The tree is
# generic-to-specific: a case that meets a parent's definition but no
# sub-mode's rule is classified at the parent. expected_firing values are
# measured live on the item-150 corpus and recorded literally (a computed
# value at module level would defeat the no-heavy-import contract).
# =========================================================================== #

_MODE_1 = ModeSpec(
    id=1,
    name="Segmentation accuracy (over-/under-segmentation)",
    short_name="segmentation accuracy (over-/under-segmentation)",
    definition=(
        "Relative to ground truth, the predicted segment for a correctly "
        "identified and labelled vertebra misses part of that vertebra "
        "(under-segmentation) or extends beyond it into background or "
        "adjacent tissue (over-segmentation). The catch-all for accuracy "
        "defects no more specific sub-mode claims: a case that is inaccurate "
        "but meets no sub-mode's rule is classified here."
    ),
    discriminator=(
        "Mode 2 when the overreach covers a substantial part of a "
        "neighbouring vertebra, or the missing part is claimed by another "
        "label; mode 3 when the surplus is a disconnected component rather "
        "than contiguous with the body; mode 4 when the whole vertebra is "
        "absent; the FOV-truncation condition when the missing part lies "
        "beyond an image face."
    ),
    mechanism=(
        "No shipped rule decides this mode: it needs a ground-truth label "
        "map, which the per-case pipeline never sees. The label-map proxies "
        "are the bounds rule's per-label volume/extent ranges "
        "(per_label.{label}.geometry.physical_volume_mm3) and "
        "reference_delta's cohort z-scores "
        "(reference_delta.{label}.features.physical_volume_mm3.robust_z), "
        "both declared at needs-real-data. The corpus case mode1_displace "
        "(a rigidly translated vertebra, which is over-segmentation into "
        "background plus under-segmentation of the true body) fires "
        "mislabel's spline-offset detector via "
        "stage3.per_label_offsets[].offset_mm -- a detector that serves no "
        "failure mode (the spline offset is an anatomy-classification "
        "signal), so the case is recorded as a co-detection and does not "
        "validate this mode."
    ),
    observability="needs-ground-truth",
    candidate_features=(
        CandidateFeature(
            path="stage3.per_label_offsets[].offset_mm",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="per_label.{label}.geometry.physical_volume_mm3",
            role="hypothesised",
        ),
        CandidateFeature(
            path="reference_delta.{label}.features.physical_volume_mm3.robust_z",
            role="hypothesised",
        ),
        CandidateFeature(
            path="eval.overlap.per_label[].dice",
            role="hypothesised",
        ),
        CandidateFeature(
            path="eval.per_mode.unanchored_foreground_fraction",
            role="hypothesised",
        ),
        CandidateFeature(
            path="boundary_error_band_thickness_mm",
            role="hypothesised",
        ),
        CandidateFeature(
            path="local_blob_error_volume_mm3",
            role="hypothesised",
        ),
        CandidateFeature(
            path="error_spatial_distribution",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="bounds",
            detector="",
            evidence_rung="needs-real-data",
        ),
        IntendedRule(
            rule_id="reference_delta",
            detector="",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="mode1_displace",
            corpus="geometric",
            expected_firing=("mislabel",),
            reason=(
                "pipeline-detected by a mode-less detector only: mislabel's "
                "spline-offset detector fires because label 22 (L3) is "
                "rigidly translated off the fitted spinal curve, measured "
                "live via segfacet.synth.regression.pipeline_findings "
                "(2026-09-14). Neither of this mode's intended rules fires "
                "without a reference attached, so the case is a recorded "
                "co-detection and does not validate mode 1."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_2 = ModeSpec(
    id=2,
    parent=1,
    name="Fused or split vertebra segments",
    short_name="fused or split vertebra segments",
    definition=(
        "Fused: one predicted segment covers a substantial part of more than "
        "one ground-truth vertebra. Split: one ground-truth vertebra is "
        "covered by more than one predicted segment, such that merging them "
        "gives a better prediction. Typically a mostly correct vertebra that "
        "misses a part or extends partly onto a neighbour; both can occur at "
        "once. Sub-type: transitional lumbosacral anatomy (sacralised L5, "
        "lumbarised S1) causing a fusion or split at the junction; a "
        "hypothesised extra signal is disc labels lying inside the sacrum "
        "label, which needs an intervertebral-disc channel the current label "
        "convention does not carry."
    ),
    discriminator=(
        "Mode 1 when the error stays within one vertebra and its "
        "background; mode 3 when the pieces carry the same label rather "
        "than a neighbour's; mode 4 when the missing vertebra's voxels are "
        "unclaimed rather than absorbed by a neighbour; mode 8 when two "
        "whole vertebrae share one label a full spacing apart."
    ),
    mechanism=(
        "Observable from the label map via proxies, still to be proven: a "
        "fused pair reads over the level's volume/extent range and a split "
        "part reads under it (bounds, "
        "per_label.{label}.geometry.physical_volume_mm3; reference_delta, "
        "reference_delta.{label}.features.physical_volume_mm3.robust_z), "
        "both edges needs-real-data. The corpus case fuse_adjacent absorbs "
        "label 23 (L4) into 22 (L3) unbridged, so what fires today is "
        "fragmentation's component detector "
        "(per_label.{label}.components.fragmentation_index) and coverage's "
        "interior-gap detector (relationships.missing_levels[]) -- mode 3's "
        "and mode 6's detectors co-detecting, recorded, not this mode's own."
    ),
    observability="single-channel-observable",
    candidate_features=(
        CandidateFeature(
            path="per_label.{label}.geometry.physical_volume_mm3",
            role="hypothesised",
        ),
        CandidateFeature(
            path="reference_delta.{label}.features.physical_volume_mm3.robust_z",
            role="hypothesised",
        ),
        CandidateFeature(
            path="stage3.spacing_consistency.spacings_mm[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="stage3.per_label_offsets[].offset_mm",
            role="hypothesised",
        ),
        CandidateFeature(
            path="spline_leave_one_out_shape_change",
            role="hypothesised",
        ),
        CandidateFeature(
            path="surface_topology",
            role="hypothesised",
        ),
        CandidateFeature(
            path="metric_change_under_split_or_merge_candidate",
            role="hypothesised",
        ),
        CandidateFeature(
            path="disc_labels_inside_sacrum_label",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="bounds",
            detector="",
            evidence_rung="needs-real-data",
        ),
        IntendedRule(
            rule_id="reference_delta",
            detector="",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="fuse_adjacent",
            corpus="geometric",
            expected_firing=("coverage", "fragmentation"),
            reason=(
                "pipeline-detected by co-detections only, measured live via "
                "segfacet.synth.regression.pipeline_findings (2026-09-14): "
                "the fused label 22 spans two disconnected bodies "
                "(fragmentation, Fragmentation:) and the absorbed level L4 "
                "is missing from the interior of the span (coverage, "
                "Missing interior level(s):). Neither of this mode's own "
                "intended rules fires without a reference, so the case does "
                "not validate mode 2."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_3 = ModeSpec(
    id=3,
    parent=1,
    name="Disconnected components / islands",
    short_name="disconnected components / islands",
    definition=(
        "A label's foreground voxels form more than one connected component, "
        "of any size ratio. Islands tend to be small fractions of the label, "
        "may cover background (non-vertebra) voxels, and may lie far from "
        "the main component, for example noise at the scan border."
    ),
    discriminator=(
        "Mode 1 when the surplus is contiguous with the body; mode 2 when "
        "the pieces carry different labels; mode 8 when the components are "
        "two whole vertebrae one spacing apart. The size ratio and the "
        "island's distance from the main body grade the finding rather than "
        "bound the mode: the further an island lies from the label's "
        "centroid, the larger it may be and still count as an island."
    ),
    mechanism=(
        "Both fragmentation detectors serve this mode end-to-end on the "
        "committed corpus: mode2_fragment splits label 22 into two "
        "comparably-sized components and drives the Fragmentation: "
        "detector via per_label.{label}.components.fragmentation_index; "
        "mode3_inject_islands adds tiny rogue blocks and drives the Rogue "
        "island(s): detector via "
        "per_label.{label}.components.stray_component_sizes[]. bounds and "
        "reference_delta stay needs-real-data: a stray island shifts volume "
        "only marginally."
    ),
    observability="single-channel-observable",
    candidate_features=(
        CandidateFeature(
            path="per_label.{label}.components.fragmentation_index",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="per_label.{label}.components.stray_component_sizes[]",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="per_label.{label}.components.largest_component_fraction",
            role="hypothesised",
        ),
        CandidateFeature(
            path="island_distance_from_main_body_mm",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="fragmentation",
            detector="Fragmentation: / Rogue island(s):",
            evidence_rung="synthetic-demonstrable",
        ),
        IntendedRule(
            rule_id="bounds",
            detector="",
            evidence_rung="needs-real-data",
        ),
        IntendedRule(
            rule_id="reference_delta",
            detector="",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="mode2_fragment",
            corpus="geometric",
            expected_firing=("fragmentation",),
            reason=(
                "pipeline-detected; fragmentation (Fragmentation: the "
                "label's fragmentation_index falls below threshold, two "
                "comparably-sized components) is the sole rule that fires, "
                "measured live via segfacet.synth.regression."
                "pipeline_findings (2026-09-14). Re-homed from the retired "
                "over-/under-segmentation mode at the item-150 sign-off: a "
                "label in two large pieces is a connectivity defect, not a "
                "label-to-vertebra correspondence defect."
            ),
        ),
        CorpusCaseExpectation(
            case_id="mode3_inject_islands",
            corpus="geometric",
            expected_firing=("fragmentation",),
            reason=(
                "pipeline-detected; fragmentation (Rogue island(s): a small "
                "non-dominant component strictly below island_min_voxels) "
                "is the sole rule that fires, measured live via "
                "segfacet.synth.regression.pipeline_findings (2026-09-14)."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_4 = ModeSpec(
    id=4,
    parent=1,
    name="Vertebra not segmented",
    short_name="vertebra not segmented",
    definition=(
        "One or more vertebrae in the scan are not segmented: a "
        "ground-truth vertebra is (mostly) not covered by any predicted "
        "segment. Usually the level's label is also absent, but the labels "
        "of the remaining vertebrae may have been renumbered so that the "
        "label sequence stays continuous over a spatial gap."
    ),
    discriminator=(
        "Mode 2 when the missing vertebra's voxels are absorbed by a "
        "neighbouring label rather than left unclaimed; modes 5 and 6 when "
        "the expected label is present but used elsewhere on the wrong "
        "vertebra; mode 6 when the only evidence is a missing label in an "
        "otherwise complete span (that finding is mode 6's, and the "
        "unsegmented vertebra it implies is this mode's)."
    ),
    mechanism=(
        "Defined against ground truth (the Stage-18 metric counts GT levels "
        "with no candidate voxels). From the label map alone the shipped "
        "signals are indirect: coverage's opt-in expected-span and "
        "expected-count checks over relationships.present_levels[] (both "
        "ship disabled, needs-real-data), and the hypothesised spacing-gap "
        "signal -- the corpus case remove_level_relabel deletes L3 and "
        "renumbers L4/L5 to L3/L4, leaving a continuous label sequence with "
        "a double inter-centroid spacing that no shipped rule reads, so its "
        "expected firing set is empty and the mode does not validate. Two "
        "further hypothesised signals cover a missing vertebra at the FOV "
        "end: extrapolating the centroid sequence toward the image face, "
        "and checking that no label touches a scan boundary that lacks a "
        "terminal label."
    ),
    observability="needs-ground-truth",
    candidate_features=(
        CandidateFeature(
            path="relationships.present_levels[]",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="stage3.spacing_consistency.spacings_mm[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="eval.per_mode.missing_level_count",
            role="hypothesised",
        ),
        CandidateFeature(
            path="extrapolated_centroid_gap_to_image_face_mm",
            role="hypothesised",
        ),
        CandidateFeature(
            path="scan_boundary_without_terminal_label",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="coverage",
            detector="Incomplete coverage (span): / Below expected count:",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="remove_level_relabel",
            corpus="geometric",
            expected_firing=(),
            reason=(
                "not detected today: label 22 (L3) is deleted and labels "
                "23/24 (L4/L5) are renumbered to 22/23, so the label "
                "sequence stays continuous while the centroid spacing "
                "between L2 and the renumbered L3 doubles; no shipped rule "
                "reads stage3.spacing_consistency.spacings_mm[], measured "
                "live via segfacet.synth.regression.pipeline_findings "
                "(2026-09-14). Recorded so the hypothesised spacing-gap "
                "signal has its fixture; an empty expected set never "
                "validates a mode."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_5 = ModeSpec(
    id=5,
    name="Semantic mislabelling (wrong vertebra identification)",
    short_name="semantic mislabelling (wrong level identity)",
    definition=(
        "A segmented vertebra carries the label of a different vertebra "
        "level. Any number of vertebrae per scan may be affected, and the "
        "label sequence may remain valid: mislabelling need not take the "
        "form of swapped labels. The catch-all for identity defects no "
        "sub-mode claims."
    ),
    discriminator=(
        "Mode 6 when the wrong identities make the label sequence "
        "implausible (every mode-6 case contains at least one mislabelled "
        "vertebra); mode 7 when every label is offset by the same number of "
        "levels; mode 8 when two labels collapse onto one centroid or one "
        "label covers two vertebrae. The label sits on a real vertebra, "
        "which separates it from mode 1's voxel-level inaccuracy."
    ),
    mechanism=(
        "Single-channel-observable only where the mislabelled vertebra's "
        "geometry does not fit the level it is named: reference_delta's "
        "per-level cohort z-scores "
        "(reference_delta.{label}.features.physical_volume_mm3.robust_z) "
        "are the shipped proxy, needs-real-data. The whole-sequence shift "
        "is mode 7 and needs an external vertebra classifier. The corpus "
        "swap case (mode4_relabel_swap) is a mode-6 case: a swap breaks the "
        "sequence, which is the observable form."
    ),
    observability="single-channel-observable",
    candidate_features=(
        CandidateFeature(
            path="stage3.monotonic_consistency.is_monotonic",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="reference_delta.{label}.features.physical_volume_mm3.robust_z",
            role="hypothesised",
        ),
        CandidateFeature(
            path="eval.per_mode.mislabelled_volume_fraction",
            role="hypothesised",
        ),
        CandidateFeature(
            path="vertebra_level_classifier_output",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="reference_delta",
            detector="",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_6 = ModeSpec(
    id=6,
    parent=5,
    name="Implausible label sequence",
    short_name="implausible label sequence",
    definition=(
        "The sequence of labelled vertebra levels is not one a spine can "
        "carry: a level appears out of cranio-caudal order relative to its "
        "neighbours, a level is missing from the interior of an otherwise "
        "present span, or a valid but unprompted numbering variant is used "
        "(a transitional label such as T13 or L6 in a scan not configured "
        "for it, where the default numbering is expected). A valid sequence "
        "is a contiguous run in canonical order, with transitional labels "
        "admitted only when configured or prompted, and accommodates a "
        "varying field of view."
    ),
    discriminator=(
        "Always contains at least one mode-5 mislabelling, not the "
        "converse: mode 5 alone when the sequence stays valid. Mode 7 when "
        "the whole sequence is offset but internally valid. Mode 4 owns the "
        "unsegmented vertebra a missing interior label implies; this mode "
        "owns the label-sequence finding itself. An out-of-order sequence "
        "means at least one label is certainly wrong and should fail the "
        "case; an unprompted variant is plausible anatomy off the default "
        "numbering and is flagged."
    ),
    mechanism=(
        "Three detectors serve this mode: sequence fires on "
        "relationships.out_of_order_labels[] (mode7_sequence_break relabels "
        "the tail to T13 -- one rank descent, since "
        "segfacet.labels.CANONICAL_ORDER ranks T13 between T12 and L1); "
        "mislabel's ordering detector fires on "
        "stage3.monotonic_consistency.non_monotonic_pairs[] "
        "(mode4_relabel_swap exchanges L2 and L3); coverage's interior-gap "
        "detector fires on relationships.missing_levels[] "
        "(mode5_remove_level deletes L3 without renumbering). The "
        "unprompted-variant detector does not exist yet: it is a candidate "
        "over relationships.present_levels[] plus a configuration flag. A "
        "multi-relabel scramble is not expressible by the fixture "
        "generator, which is why the sequence edge stays needs-real-data "
        "although its case is pipeline-detected."
    ),
    observability="single-channel-observable",
    candidate_features=(
        CandidateFeature(
            path="relationships.is_continuous",
            role="stage18-metric-anchor",
        ),
        CandidateFeature(
            path="relationships.out_of_order_labels[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="stage3.monotonic_consistency.non_monotonic_pairs[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="relationships.missing_levels[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="relationships.present_levels[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="unprompted_transitional_label",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="sequence",
            detector="Non-continuous label sequence:",
            evidence_rung="needs-real-data",
        ),
        IntendedRule(
            rule_id="mislabel",
            detector="Vertebra ordering inconsistent with label:",
            evidence_rung="synthetic-demonstrable",
        ),
        IntendedRule(
            rule_id="coverage",
            detector="Missing interior level(s):",
            evidence_rung="synthetic-demonstrable",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="mode4_relabel_swap",
            corpus="geometric",
            expected_firing=("mislabel",),
            reason=(
                "pipeline-detected; mislabel's ordering detector is the "
                "sole rule that fires, measured live via "
                "segfacet.synth.regression.pipeline_findings (2026-09-14): "
                "labels 21 (L2) and 22 (L3) are out of expected order along "
                "the spline. Re-homed from semantic mislabelling at the "
                "item-150 sign-off: a swap is the sequence-breaking form of "
                "mislabelling."
            ),
        ),
        CorpusCaseExpectation(
            case_id="mode5_remove_level",
            corpus="geometric",
            expected_firing=("coverage",),
            reason=(
                "pipeline-detected; coverage (Missing interior level(s): L3 "
                "absent within the observed present-level span) is the sole "
                "rule that fires, measured live via "
                "segfacet.synth.regression.pipeline_findings (2026-09-14). "
                "Re-homed from vertebra-not-segmented at the item-150 "
                "sign-off: the finding is about the label sequence; the "
                "unsegmented vertebra it implies is mode 4's."
            ),
        ),
        CorpusCaseExpectation(
            case_id="mode7_sequence_break",
            corpus="geometric",
            expected_firing=("sequence",),
            reason=(
                "pipeline-detected; sequence is the sole rule that fires, "
                "measured live via segfacet.synth.regression."
                "pipeline_findings (2026-09-14). The tail vertebra is "
                "relabelled to T13, a single rank descent; why the edge's "
                "rung sits below this measured detection is in the "
                "mechanism sentence."
            ),
        ),
    ),
    severity="fail",
    status="specified",
    provenance="hypothesised",
)

_MODE_7 = ModeSpec(
    id=7,
    parent=5,
    name="Shifted label sequence",
    short_name="shifted label sequence",
    definition=(
        "Every label in the scan is offset from its true level by the same "
        "number of levels, so the sequence is internally valid and no "
        "label-map feature distinguishes it from a correct labelling. "
        "Deciding it needs an external vertebra-level classifier -- spine "
        "section, rib attachment, or a counting reference such as C2 or "
        "the sacrum -- or ground truth."
    ),
    discriminator=(
        "Mode 6 when the sequence itself is implausible; mode 5 when only "
        "some labels are wrong. The whole-sequence offset with a valid "
        "sequence is what makes this a separate mode: a rule reading the "
        "label map alone cannot fire on it."
    ),
    mechanism=(
        "No shipped rule, no candidate feature in the record, no corpus "
        "case: listed as proposed. The one hypothesised input is a "
        "vertebra-level classifier's output (spine section and counting "
        "reference), compared against relationships.present_levels[]."
    ),
    observability="needs-external-classifier",
    candidate_features=(
        CandidateFeature(
            path="vertebra_level_classifier_output",
            role="hypothesised",
        ),
        CandidateFeature(
            path="relationships.present_levels[]",
            role="hypothesised",
        ),
    ),
    intended_rules=(),
    corpus_cases=(),
    severity="flagged-for-review",
    status="proposed",
    provenance="hypothesised",
)

_MODE_8 = ModeSpec(
    id=8,
    parent=5,
    name="Collapsed or duplicated label set",
    short_name="collapsed or duplicated label set",
    definition=(
        "Decidable on centroids alone. Collapsed: two or more labels' "
        "centroids lie closer together than a fraction of the expected "
        "inter-vertebral spacing. Duplicated: one label value carries two "
        "centroids -- in segmentation terms, two whole vertebrae roughly a "
        "vertebral spacing apart share a label. When centroids coincide "
        "exactly the Stage 3 spline fit cannot be computed, the record "
        "carries a stage3_unavailable reason instead of a stage3 block, "
        "every stage3-reading rule short-circuits and no finding of any "
        "kind is raised: the case passes silently (carried defect, item "
        "129, 2026-08-31)."
    ),
    discriminator=(
        "Mode 3 when the components under one label are a vertebra in "
        "pieces (an island is smaller than a body); mode 2 when the shared "
        "label is a fusion (the bodies are adjacent, not a spacing apart); "
        "mode 9 (overlapping segments) needs a shared voxel, which a "
        "collapsed pair of disjoint labels never has."
    ),
    mechanism=(
        "No rule exists for this mode yet, which is what proposed means. "
        "The candidate inputs are per-component centroids and volumes "
        "(not extracted today), the minimum inter-label centroid distance "
        "relative to the expected spacing "
        "(stage3.spacing_consistency.spacings_mm[]), and the "
        "stage3_unavailable.reason field the degenerate case populates "
        "(item 129), which no rule reads."
    ),
    observability="single-channel-observable",
    candidate_features=(
        CandidateFeature(
            path="stage3_unavailable.reason",
            role="hypothesised",
        ),
        CandidateFeature(
            path="stage3.spacing_consistency.spacings_mm[]",
            role="hypothesised",
        ),
        CandidateFeature(
            path="per_component_centroids",
            role="hypothesised",
        ),
    ),
    intended_rules=(),
    corpus_cases=(),
    severity="flagged-for-review",
    status="proposed",
    provenance="hypothesised",
)

_MODE_9 = ModeSpec(
    id=9,
    name="Overlapping segments",
    short_name="overlapping segments",
    definition=(
        "Two labels' foreground voxel sets intersect -- the same voxel is "
        "claimed by more than one label, a condition impossible in a valid "
        "single-channel integer label map."
    ),
    discriminator=(
        "Distinguishes from every other mode by requiring a second label's "
        "mask: it is unobservable from any single label's geometry alone, "
        "and from a single-channel label map at all, unlike modes 1-8, "
        "which are decidable from one label's geometry, the label map's "
        "per-label statistics, or an external input."
    ),
    mechanism=(
        "A single-channel integer label map cannot assign two labels to one "
        "voxel, so overlaps[] populates only on a case deliberately "
        "corrupted to violate that invariant, which no real segmenter "
        "output can be; mode8_force_overlap therefore stays "
        "detection=\"reconstructed_record\" rather than pipeline-detected, "
        "while the overlap rule and the paths it reads remain correct and "
        "fully wired."
    ),
    observability="structurally-unobservable",
    candidate_features=(
        CandidateFeature(
            path="overlaps[].overlap_voxels",
            role="stage18-metric-anchor",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="overlap",
            detector="Overlapping segments:",
            evidence_rung="structurally-unobservable",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="mode8_force_overlap",
            corpus="geometric",
            expected_firing=("overlap",),
            reason=(
                "reconstructed-record-detected; overlap is the sole rule "
                "that fires on this corpus case, measured live via "
                "segfacet.synth.regression.reconstructed_findings "
                "(2026-09-14). A voxel in a single-channel integer label map "
                "holds exactly one label, so overlaps[] can only populate "
                "when the record is deliberately corrupted to violate that "
                "invariant -- which this case's reconstruction does."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)

_MODE_10 = ModeSpec(
    id=10,
    name="Implausible tissue under a label",
    short_name="implausible tissue under a label",
    definition=(
        "On CT, the voxels a vertebra label claims do not carry "
        "bone-plausible Hounsfield-unit statistics: the label's median HU "
        "is implausibly low (soft tissue or air), implausibly high (metal "
        "or an implant), or its intensity spread is degenerate -- a "
        "near-zero standard deviation over a uniform region, which no real "
        "trabecular/cortical bone produces. The label map's geometry may be "
        "entirely well-formed; the failure is that the tissue underneath it "
        "is not the tissue the label names."
    ),
    discriminator=(
        "Distinguishes from modes 1-9 by requiring the paired intensity "
        "scan: every one of those is decidable from the label map, ground "
        "truth or an external classifier, whereas this mode is invisible "
        "without the scan (observability = needs-paired-scan). A label may "
        "sit exactly where it belongs, correctly shaped, and still cover "
        "the wrong tissue."
    ),
    mechanism=(
        "The committed intensity corpus demonstrates this mode end-to-end "
        "three times over: implausible_metal (label 22's median reads 2999 "
        "HU, above the plausible bone band's ceiling), "
        "implausible_soft_tissue (40 HU, below its floor) and "
        "degenerate_uniform (a constant fill, zero spread) each drive the "
        "intensity rule through "
        "segfacet.synth.regression.intensity_pipeline_findings, which is "
        "why that edge sits at the strongest rung. intensity_reference_delta "
        "stays a rung below: the synthetic intensity corpus is built "
        "against no reference distribution and the harness attaches none, "
        "so nothing in the committed corpus can exercise it."
    ),
    observability="needs-paired-scan",
    candidate_features=(
        CandidateFeature(
            path="image_features.per_label[].median_hu",
            role="hypothesised",
        ),
        CandidateFeature(
            path="image_features.per_label[].std_hu",
            role="hypothesised",
        ),
        CandidateFeature(
            path="intensity_reference_delta.per_label[].robust_z",
            role="hypothesised",
        ),
    ),
    intended_rules=(
        IntendedRule(
            rule_id="intensity",
            detector=(
                "Implausible intensity (too low): / (too high): / "
                "(degenerate/uniform):"
            ),
            evidence_rung="synthetic-demonstrable",
        ),
        IntendedRule(
            rule_id="intensity_reference_delta",
            detector="",
            evidence_rung="needs-real-data",
        ),
    ),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="implausible_metal",
            corpus="intensity",
            expected_firing=("intensity",),
            reason=(
                "intensity-pipeline-detected; intensity is the sole rule "
                "that fires on this case, measured live via "
                "segfacet.synth.regression.intensity_pipeline_findings over "
                "tests/corpus/intensity/manifest.json (2026-09-14): label 22 "
                "(L3)'s median reads 2999 HU, above the plausible bone "
                "band's 2000 HU ceiling. intensity_reference_delta cannot "
                "fire here because the synthetic intensity corpus is built "
                "against no reference distribution and the harness attaches "
                "none (item 146 A3), which is why its edge stays at "
                "needs-real-data."
            ),
        ),
        CorpusCaseExpectation(
            case_id="implausible_soft_tissue",
            corpus="intensity",
            expected_firing=("intensity",),
            reason=(
                "intensity-pipeline-detected; intensity is the sole rule "
                "that fires on this case, measured live via "
                "segfacet.synth.regression.intensity_pipeline_findings over "
                "tests/corpus/intensity/manifest.json (2026-09-14): label 22 "
                "(L3)'s median reads 40 HU, below the plausible bone band's "
                "100 HU floor -- soft tissue under a vertebra label. "
                "intensity_reference_delta attaches no reference here (item "
                "146 A3), so it stays needs-real-data."
            ),
        ),
        CorpusCaseExpectation(
            case_id="degenerate_uniform",
            corpus="intensity",
            expected_firing=("intensity",),
            reason=(
                "intensity-pipeline-detected; intensity is the sole rule "
                "that fires on this case, measured live via "
                "segfacet.synth.regression.intensity_pipeline_findings over "
                "tests/corpus/intensity/manifest.json (2026-09-14). It raises "
                "two findings, both from the same rule: the "
                "degenerate/uniform detector (std 0.00 HU, at or below the "
                "1.00 HU threshold) and, because the constant fill is 0 HU, "
                "the too-low detector as well -- so the firing SET is still "
                "{intensity}. intensity_reference_delta attaches no "
                "reference here (item 146 A3), so it stays needs-real-data."
            ),
        ),
    ),
    severity="flagged-for-review",
    status="specified",
    provenance="hypothesised",
)


# =========================================================================== #
# Conditions (item 150): case conditions that gate other rules and are not
# failure modes. Rendered as their own section after the modes.
# =========================================================================== #

_CONDITION_FOV_TRUNCATION = ConditionSpec(
    id="fov_truncation",
    name="FOV truncation (partial vertebra at the image border)",
    short_name="FOV truncation (condition, not a failure mode)",
    definition=(
        "A vertebra at the edge of the imaging field of view is only "
        "partially captured: its label touches an image face, its geometry "
        "is impacted to a varying degree (overall size, connectedness, "
        "shape), and the missing region displaces its measured centroid. "
        "Many rules cannot be applied to such a vertebra unless the missing "
        "region has little impact. A vertebra at a cranio-caudal FOV end is "
        "the expected form; an in-plane (left/right/anterior/posterior) "
        "clip is the unexpected form. Retired as failure mode 6 at the "
        "item-150 sign-off (2026-09-14): a condition on the case, not a "
        "defect of the segmentation."
    ),
    mechanism=(
        "The border rule records the condition end-to-end on "
        "mode6_crop_at_border, which crops label 22's anterior face "
        "(per_label.{label}.geometry.touches_anterior), classifying it an "
        "unexpected clip; cropping also displaces the centroid off the "
        "fitted spinal curve, so mislabel's mode-less spline-offset "
        "detector co-fires via stage3.per_label_offsets[].offset_mm. The "
        "border rule declares no failure mode. The exemptions the condition "
        "grants today: mislabel's spline-offset detector skips terminal "
        "entries (stage3.per_label_offsets[].is_terminal), and coverage's "
        "border-aware span check resolves the covered span through the "
        "FOV-end labels."
    ),
    candidate_features=(
        "per_label.{label}.geometry.touches_anterior",
        "per_label.{label}.geometry.touches_posterior",
        "per_label.{label}.geometry.touches_left",
        "per_label.{label}.geometry.touches_right",
        "per_label.{label}.geometry.touches_superior",
        "per_label.{label}.geometry.touches_inferior",
        "stage3.per_label_offsets[].is_terminal",
        "fraction_of_expected_volume_present",
    ),
    recording_rules=("border",),
    exempting_rules=("mislabel", "coverage"),
    corpus_cases=(
        CorpusCaseExpectation(
            case_id="mode6_crop_at_border",
            corpus="geometric",
            expected_firing=("border", "mislabel"),
            reason=(
                "pipeline-detected; measured live via "
                "segfacet.synth.regression.pipeline_findings (2026-09-14): "
                "border, because the cropped label 22 (L3) touches the "
                "anterior image face, and mislabel, because the crop "
                "displaces the centroid off the fitted spinal curve. Both "
                "are the condition's recorded signature; neither names a "
                "failure mode."
            ),
        ),
    ),
)


# =========================================================================== #
# Provenance: what became of each vision.md section 6 seed title (item 150).
# The vision list is the SEED the catalogue started from, never its ids; the
# one conformance claim in that direction is that every seed title has a
# disposition here and every referenced mode id exists.
# =========================================================================== #

VISION_SEED_DISPOSITION: Mapping[str, str] = MappingProxyType(
    {
        "Label not aligned with the anatomical vertebra it names": "retired",
        "Over-/under-segmentation — fused or fragmented vertebra segments": "mode:1",
        "Disconnected components / islands, especially tiny rogue segments": "mode:3",
        "Semantic mislabelling (wrong vertebra identification)": "mode:5",
        "Not all vertebrae in the image are segmented": "mode:4",
        "Partial vertebra at the image border whose appearance changes": (
            "condition:fov_truncation"
        ),
        "Non-continuous label sequence (e.g. L1 → T12 → L2 → L5)": "mode:6",
        "Overlapping segments": "mode:9",
    }
)


def _build_specification(modes: Iterable[ModeSpec]) -> Mapping[int, ModeSpec]:
    """Index *modes* by ``id`` into an immutable, ascending mapping,
    rejecting a duplicate ``id`` rather than letting the later entry
    silently replace the earlier one, and validating the hierarchy: every
    ``parent`` must name a mode in the same set, and a parent is itself a
    top-level mode (one tier of sub-modes, item 150)."""
    by_id: Dict[int, ModeSpec] = {}
    for mode in modes:
        if mode.id in by_id:
            raise ValueError(
                f"SPECIFICATION: duplicate mode id {mode.id} "
                f"({by_id[mode.id].name!r} and {mode.name!r}) -- every mode id must "
                f"be unique."
            )
        by_id[mode.id] = mode
    for mode in by_id.values():
        if mode.parent is None:
            continue
        if mode.parent not in by_id:
            raise ValueError(
                f"SPECIFICATION: mode {mode.id} names parent {mode.parent}, which "
                f"is not a mode id in the specification (ids: {sorted(by_id)!r})."
            )
        if by_id[mode.parent].parent is not None:
            raise ValueError(
                f"SPECIFICATION: mode {mode.id} names parent {mode.parent}, which "
                f"is itself a sub-mode of {by_id[mode.parent].parent}; the "
                f"hierarchy is one tier deep."
            )
    return MappingProxyType({mode_id: by_id[mode_id] for mode_id in sorted(by_id)})


def _build_conditions(
    conditions: Iterable[ConditionSpec],
) -> Mapping[str, ConditionSpec]:
    by_id: Dict[str, ConditionSpec] = {}
    for condition in conditions:
        if condition.id in by_id:
            raise ValueError(
                f"CONDITIONS: duplicate condition id {condition.id!r}."
            )
        by_id[condition.id] = condition
    return MappingProxyType({key: by_id[key] for key in sorted(by_id)})


SPECIFICATION: Mapping[int, ModeSpec] = _build_specification(
    (
        _MODE_1,
        _MODE_2,
        _MODE_3,
        _MODE_4,
        _MODE_5,
        _MODE_6,
        _MODE_7,
        _MODE_8,
        _MODE_9,
        _MODE_10,
    )
)

CONDITIONS: Mapping[str, ConditionSpec] = _build_conditions(
    (_CONDITION_FOV_TRUNCATION,)
)


def iter_conditions() -> Iterator[ConditionSpec]:
    """Yield the conditions in ascending ``id`` order. Takes no argument."""
    for condition_id in sorted(CONDITIONS):
        yield CONDITIONS[condition_id]


def mode_path(mode: ModeSpec) -> str:
    """The hierarchical display path of *mode* -- ``"1"`` for a top-level
    mode, ``"1.2"`` for the second sub-mode (by ascending id) of mode 1.
    Display only: the stable identity is ``mode.id``."""
    if mode.parent is None:
        return str(mode.id)
    siblings = sorted(
        m.id for m in SPECIFICATION.values() if m.parent == mode.parent
    )
    return f"{mode.parent}.{siblings.index(mode.id) + 1}"


def iter_modes() -> Iterator[ModeSpec]:
    """Yield the seed modes in ascending ``id`` order. Takes no argument."""
    for mode_id in sorted(SPECIFICATION):
        yield SPECIFICATION[mode_id]


# =========================================================================== #
# The vision.md §6 parse (item 147 AC4) -- one home, here.
# =========================================================================== #


def vision_seed_titles() -> Dict[int, str]:
    """The numbered titles of ``docs/aide/vision.md`` §6, parsed live.

    This is the **seed**, not the record, and it provides no ids. §6
    names the eight modes this catalogue started from; :data:`SPECIFICATION`
    is what the catalogue *is* today, re-organised at the item-150 sign-off
    (2026-09-14). The one conformance claim in this direction is
    :func:`vision_seed_conflicts`: every seed title has a
    :data:`VISION_SEED_DISPOSITION` entry that resolves -- nothing else
    reads this, and no consumer should treat a missing key as a missing
    mode.

    Item 147 moved this function here from ``segfacet.traceability``
    (where it was private) so that exactly one module under
    ``src/segfacet/`` reads ``vision.md`` at all.
    """
    import re

    text = (_REPO_ROOT / "docs" / "aide" / "vision.md").read_text(encoding="utf-8")
    section_match = re.search(
        r"^## 6\. Segmentation Failure Modes[^\n]*\n(.*?)(?=^## \d|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section_match is None:
        raise RuntimeError(
            "segfacet.failure_modes: docs/aide/vision.md carries no "
            "'## 6. Segmentation Failure Modes' section to transcribe titles from."
        )
    section_text = section_match.group(1)
    items = re.findall(r"^\d+\.\s+(.+)$", section_text, flags=re.MULTILINE)
    titles: Dict[int, str] = {}
    for index, raw in enumerate(items, start=1):
        title = raw.strip()
        if title.endswith("."):
            title = title[:-1]
        title = re.sub(r"\s+", " ", title).strip()
        titles[index] = title
    return titles


# =========================================================================== #
# The derived failure-mode name map (item 147 AC21) -- the binding
# `segfacet.synth.perturbation.FAILURE_MODE_NAMES` now resolves to.
# =========================================================================== #


def failure_mode_names() -> Mapping[int, str]:
    """``{0: CLEAN_CONTROL_NAME}`` plus every mode's ``short_name``, keyed by
    mode id and ascending.

    The values are the **paraphrases** both committed corpus manifests carry
    in ``failure_mode_name``, not the vision §6 titles ``ModeSpec.name``
    holds -- which is why they are an authored field rather than derived
    from ``name``: re-pointing the manifests at ``name`` would be a corpus
    value change. Key 0 is explicit because the clean control is not a
    failure mode and has no ``ModeSpec`` entry.

    Returns an immutable mapping; a fresh proxy over a fresh dict on every
    call, so a caller mutating nothing can still not leak into a later one.
    """
    names: Dict[int, str] = {0: CLEAN_CONTROL_NAME}
    for mode_id in sorted(SPECIFICATION):
        names[mode_id] = SPECIFICATION[mode_id].short_name
    return MappingProxyType(names)


# =========================================================================== #
# Derivation: measured_firing / case_agrees / derive_status / derive_mode_rung
# (AC9, AC10, AC14) -- deferred heavy imports (A3).
# =========================================================================== #


def measured_firing(case: CorpusCaseExpectation) -> Tuple[str, ...]:
    """The full set of ``rule_id``s among the findings *case*'s manifest
    entry's detection path produces, measured live through
    :mod:`segfacet.synth.regression`.

    ``corpus`` is the **first** dispatch key (item 146): it selects which
    committed manifest the ``case_id`` is resolved against, and the
    vocabulary is closed and exact -- any value other than ``"geometric"``
    or ``"intensity"`` raises ``ValueError`` naming both the case and the
    unrecognised value, never a silent empty set. Within each corpus the
    manifest case's own ``detection`` field is the second dispatch key:

    * ``"geometric"`` -- ``tests/corpus/manifest.json``;
      ``pipeline_findings`` for ``detection == "pipeline"``,
      ``reconstructed_findings`` for ``detection == "reconstructed_record"``.
    * ``"intensity"`` -- ``tests/corpus/intensity/manifest.json``;
      ``intensity_pipeline_findings`` for
      ``detection == "intensity_pipeline"`` (item 146's public harness, the
      one intensity composition in production).
    """
    if case.corpus == "geometric":
        return _measured_firing_geometric(case)
    if case.corpus == "intensity":
        return _measured_firing_intensity(case)
    raise ValueError(
        f"measured_firing: unrecognised corpus {case.corpus!r} for case_id="
        f"{case.case_id!r}; the dispatch vocabulary is exactly "
        f"('geometric', 'intensity')."
    )


def _measured_firing_geometric(case: CorpusCaseExpectation) -> Tuple[str, ...]:
    """The ``corpus == "geometric"`` branch of :func:`measured_firing` --
    today's body verbatim, over ``tests/corpus/manifest.json``."""
    from segfacet.synth.corpus import load_manifest
    from segfacet.synth.regression import pipeline_findings, reconstructed_findings

    manifest = load_manifest()
    manifest_case = None
    for candidate in manifest.get("cases", []):
        if candidate.get("case_id") == case.case_id:
            manifest_case = candidate
            break
    if manifest_case is None:
        raise ValueError(
            f"measured_firing: case_id {case.case_id!r} not found in the committed "
            f"corpus manifest (corpus={case.corpus!r})."
        )

    detection = manifest_case.get("detection")
    if detection == "pipeline":
        findings = pipeline_findings(manifest_case)
    elif detection == "reconstructed_record":
        findings = reconstructed_findings(manifest_case)
    else:
        raise ValueError(
            f"measured_firing: unrecognised detection {detection!r} for "
            f"case_id={case.case_id!r}."
        )
    return tuple(sorted({finding.rule_id for finding in findings}))


def _measured_firing_intensity(case: CorpusCaseExpectation) -> Tuple[str, ...]:
    """The ``corpus == "intensity"`` branch of :func:`measured_firing`, over
    the committed ``tests/corpus/intensity/manifest.json``.

    ``segfacet.synth.intensity.load_intensity_manifest`` is reached through
    the module object rather than imported by name, so a test can substitute
    a manifest whose ``detection`` is unrecognised and observe the raise."""
    from segfacet.synth import intensity as intensity_module
    from segfacet.synth.regression import intensity_pipeline_findings

    manifest = intensity_module.load_intensity_manifest()
    manifest_case = None
    for candidate in manifest.get("cases", []):
        if candidate.get("case_id") == case.case_id:
            manifest_case = candidate
            break
    if manifest_case is None:
        raise ValueError(
            f"measured_firing: case_id {case.case_id!r} not found in the committed "
            f"intensity corpus manifest tests/corpus/intensity/manifest.json "
            f"(corpus={case.corpus!r})."
        )

    detection = manifest_case.get("detection")
    if detection != "intensity_pipeline":
        raise ValueError(
            f"measured_firing: unrecognised detection {detection!r} for "
            f"case_id={case.case_id!r} in the intensity corpus; the only "
            f"recognised value is 'intensity_pipeline'."
        )
    findings = intensity_pipeline_findings(manifest_case)
    return tuple(sorted({finding.rule_id for finding in findings}))


def case_agrees(case: CorpusCaseExpectation) -> bool:
    """``True`` iff *case*'s live :func:`measured_firing` set equals its
    authored ``expected_firing`` set.

    ``expected_firing`` must be a tuple. A bare ``str`` reaching this
    function -- a :class:`CorpusCaseExpectation` built standalone, outside
    the :class:`ModeSpec` tree whose ``__post_init__`` enforces AC7 -- would
    otherwise be compared character-wise (``set("border")``) and silently
    return ``False``, so it is rejected here too."""
    expected = case.expected_firing
    if not isinstance(expected, tuple):
        raise ValueError(
            f"case_agrees: corpus case {case.case_id!r}'s 'expected_firing' must be "
            f"a tuple, got {type(expected).__name__} -- a bare str or list would be "
            f"compared element-wise against the measured firing set."
        )
    return set(measured_firing(case)) == set(expected)


def _registry_declares(mode_id: int) -> bool:
    """``True`` iff at least one **registered** rule's
    ``RuleModeDeclaration`` lists *mode_id* among its ``modes``.

    This is vision.md §6's lifecycle definition verbatim ("``implemented``
    -- at least one registered rule declares the mode"), so a declaration
    spanning several modes (the real ``heuristics.fragmentation`` declares
    ``modes=(2, 3)``) counts for **every** mode it lists, not only for a
    mode it declares alone.

    Item 145 A1 authorised the same containment correction as a fallback;
    the item-144 review (commit 51dff83) had already landed it here.
    """
    from segfacet.heuristics.rule import iter_rule_declarations

    for _rule_id, declaration in iter_rule_declarations():
        if declaration is not None and mode_id in declaration.modes:
            return True
    return False


def derive_status(mode: ModeSpec) -> str:
    """The live-derived lifecycle status for *mode* (AC9, AC10).

    ``"validated"`` iff at least one **registered** rule declares
    ``mode.id`` **and** *mode* carries >=1 corpus case, every one of which
    :func:`case_agrees`; else ``"implemented"`` iff a registered rule
    declares ``mode.id`` (:func:`_registry_declares`); else the authored
    ``mode.status`` (``"proposed"`` or ``"specified"``) unchanged.
    The empty set never satisfies the "every case agrees" quantifier
    vacuously -- an empty ``corpus_cases`` cannot reach ``"validated"``.

    The declaring-rule precondition on ``"validated"`` is item 146's
    correction of an item-145 review finding (``docs/aide/insights.md``,
    item 145, 2026-09-03): the layering used to test the corpus-agreement
    clause first, so a mode with agreeing corpus cases and **no rule
    declaring it anywhere** derived ``"validated"`` without ever passing
    through ``"implemented"``. vision.md section 6's ladder is cumulative --
    validated implies implemented -- so the rung below is now a
    precondition, not merely the fallback. No shipped mode moves: all ten
    entries that reach the corpus-agreement clause are declared.
    """
    declared = _registry_declares(mode.id)
    if declared and mode.corpus_cases and _demonstrates(mode):
        return "validated"
    if declared:
        return "implemented"
    return mode.status


def _demonstrates(mode: ModeSpec) -> bool:
    """The item-150 lifecycle semantics for ``"validated"``: every corpus
    case agrees with its measurement, **and** at least one case has a
    non-empty expected firing set that names one of the mode's own
    ``intended_rules``. An empty expected set is recorded (it documents
    "not detected today") and never validates; a case detected only by
    another mode's rule, or by a mode-less detector, is a recorded
    co-detection and never validates either."""
    if not all(case_agrees(case) for case in mode.corpus_cases):
        return False
    own_rules = {edge.rule_id for edge in mode.intended_rules}
    return any(
        case.expected_firing and own_rules.intersection(case.expected_firing)
        for case in mode.corpus_cases
    )


def derive_mode_rung(mode: ModeSpec) -> Optional[str]:
    """The strongest :data:`EVIDENCE_RUNGS` member among *mode*'s
    ``intended_rules`` edges (AC14, A6); ``None`` for a mode with no edges."""
    if not mode.intended_rules:
        return None
    return min(
        (rule.evidence_rung for rule in mode.intended_rules),
        key=lambda rung: _RUNG_STRENGTH[rung],
    )


def specification_conflicts(
    modes: Optional[Iterable[ModeSpec]] = None,
) -> Tuple[str, ...]:
    """The conformance check behind AC8, defence in depth: one conflict per
    mode whose ``status`` field holds a value outside
    :data:`AUTHORED_STATUSES` (only reachable via ``object.__setattr__``
    forcing a value past ``__post_init__``, since construction itself
    already rejects it). Defaults to the shipped :data:`SPECIFICATION`
    (via :func:`iter_modes`); returns ``()`` for it.

    Since item 146 it also reports **``proposed`` drift**: a mode authored
    ``"proposed"`` -- listed, defined, deliberately unimplemented -- whose
    :func:`derive_status` no longer returns ``"proposed"``, because a rule
    has acquired it or a corpus case now demonstrates it. That is not an
    error in the tree; it is the signal that the entry has outgrown its
    authored status and wants re-authoring as ``"specified"``.

    This check is deliberately **not** generalised to authored-vs-derived
    equality across the board: ``"specified"`` is precisely the status that
    is expected to derive further (every one of modes 1-9 is authored
    ``"specified"`` and derives ``"implemented"`` or ``"validated"``), so a
    blanket comparison would report the whole specification.
    """
    if modes is None:
        modes = tuple(iter_modes())
    modes = tuple(modes)
    conflicts = []
    for mode in modes:
        if mode.status not in AUTHORED_STATUSES:
            conflicts.append(
                f"mode {mode.id}: 'status' field holds {mode.status!r}, which is not "
                f"a member of AUTHORED_STATUSES {AUTHORED_STATUSES} -- "
                f"'implemented'/'validated' must only ever be derived via "
                f"derive_status(), never hand-set past construction."
            )
            continue
        if mode.status == "proposed":
            derived = derive_status(mode)
            if derived != "proposed":
                conflicts.append(
                    f"mode {mode.id}: authored status 'proposed' but derive_status() "
                    f"now returns {derived!r} -- a proposed (listed, unimplemented) "
                    f"entry has acquired a declaring rule or a demonstrating corpus "
                    f"case, and wants re-authoring as 'specified'."
                )

    conflicts.extend(_intended_rule_conflicts(modes))
    conflicts.extend(_corpus_case_conflicts(modes))
    return tuple(conflicts)


def _intended_rule_conflicts(modes: Tuple[ModeSpec, ...]) -> Tuple[str, ...]:
    """AC13: every ``IntendedRule`` edge must be an edge the named rule
    itself declares -- the specification -> declaration direction.

    Two shapes are reported, distinguished in the message: the named
    ``rule_id`` registers no rule at all, and the named rule registers but
    its ``RuleModeDeclaration`` does not list this mode. Together with
    ``catalogue.rule_declaration_conflicts()``'s opposite direction (a
    declared mode outside :data:`SPECIFICATION`), this replaces the
    ``"corpus"``-tagged declaration -> corpus check item 147 retired.
    """
    from segfacet.heuristics.rule import iter_rule_declarations

    declarations = dict(iter_rule_declarations())
    conflicts = []
    for mode in modes:
        for edge in mode.intended_rules:
            if edge.rule_id not in declarations:
                conflicts.append(
                    f"mode {mode.id}: intended rule {edge.rule_id!r} names a rule_id "
                    f"that no rule registers (registered: "
                    f"{sorted(declarations)!r})."
                )
                continue
            declaration = declarations[edge.rule_id]
            declared = set(declaration.modes) if declaration is not None else set()
            if mode.id not in declared:
                conflicts.append(
                    f"mode {mode.id}: intended rule {edge.rule_id!r} is registered but "
                    f"its RuleModeDeclaration does not declare mode {mode.id} "
                    f"(declared modes: {sorted(declared)!r})."
                )
    return tuple(conflicts)


def _corpus_case_conflicts(modes: Tuple[ModeSpec, ...]) -> Tuple[str, ...]:
    """AC14/AC15: every committed corpus case, in both manifests, must be
    carried by the mode its manifest entry names, and its manifest
    expectation must agree with the specification's ``expected_firing``.

    The two manifests express expectation differently (item 147 A9), and the
    relation applied is named in the message:

    * ``tests/corpus/manifest.json`` carries ``expected_rule_ids``, the
      narrow set expected *among* the fired findings -- compared by
      **subset**;
    * ``tests/corpus/intensity/manifest.json`` carries ``expected_firing``,
      the full set -- compared by **equality**.

    Cases whose ``failure_mode`` is 0 are the clean controls: not a failure
    mode, no ``ModeSpec`` entry, skipped. Manifests are read through the
    module objects (deferred imports, house style) so a test can substitute
    one.
    """
    from segfacet.synth import corpus as corpus_module
    from segfacet.synth import intensity as intensity_module

    by_id = {mode.id: mode for mode in modes}
    conflicts = []

    for corpus_name, cases, expectation_key, relation in (
        (
            "tests/corpus/manifest.json",
            corpus_module.load_manifest().get("cases", []),
            "expected_rule_ids",
            "subset",
        ),
        (
            "tests/corpus/intensity/manifest.json",
            intensity_module.load_intensity_manifest().get("cases", []),
            "expected_firing",
            "equality",
        ),
    ):
        for case in cases:
            mode_id = case.get("failure_mode")
            case_id = case.get("case_id")
            if mode_id == 0:
                condition_id = case.get("condition") or ""
                if condition_id:
                    conflicts.extend(
                        _condition_case_conflicts(
                            corpus_name, case, condition_id, expectation_key, relation
                        )
                    )
                continue
            mode = by_id.get(mode_id)
            if mode is None:
                # Out of scope for *this* call, not a conflict. `modes` may
                # be any subset of the specification -- item 144's
                # adversarial probes pass a single hand-built ModeSpec --
                # and a manifest case belonging to a mode the caller did not
                # pass says nothing about the modes it did. Reporting them
                # would bury the one conflict such a probe is asking about.
                continue
            expectation = None
            for candidate in mode.corpus_cases:
                if candidate.case_id == case_id:
                    expectation = candidate
                    break
            if expectation is None:
                conflicts.append(
                    f"corpus case {case_id!r} ({corpus_name}) names failure_mode "
                    f"{mode_id}, but mode {mode_id}'s corpus_cases do not carry that "
                    f"case_id (carried: "
                    f"{sorted(c.case_id for c in mode.corpus_cases)!r})."
                )
                continue
            manifest_set = set(case.get(expectation_key) or ())
            specified_set = set(expectation.expected_firing)
            disagrees = (
                not manifest_set <= specified_set
                if relation == "subset"
                else manifest_set != specified_set
            )
            if disagrees:
                conflicts.append(
                    f"corpus case {case_id!r} ({corpus_name}, mode {mode_id}): the "
                    f"manifest's {expectation_key} {sorted(manifest_set)!r} disagrees "
                    f"with the specification's expected_firing "
                    f"{sorted(specified_set)!r} under the {relation} relation this "
                    f"corpus is compared by."
                )

    return tuple(conflicts)


def _condition_case_conflicts(
    corpus_name: str,
    case: dict,
    condition_id: str,
    expectation_key: str,
    relation: str,
) -> Tuple[str, ...]:
    """The condition half of :func:`_corpus_case_conflicts` (item 150): a
    manifest case carrying ``failure_mode == 0`` **and** a ``condition``
    must be carried by that :class:`ConditionSpec`'s ``corpus_cases`` with
    an agreeing expectation, under the same relation as a mode's case."""
    case_id = case.get("case_id")
    condition = CONDITIONS.get(condition_id)
    if condition is None:
        return (
            f"corpus case {case_id!r} ({corpus_name}) names condition "
            f"{condition_id!r}, which is not a CONDITIONS entry (known: "
            f"{sorted(CONDITIONS)!r}).",
        )
    expectation = None
    for candidate in condition.corpus_cases:
        if candidate.case_id == case_id:
            expectation = candidate
            break
    if expectation is None:
        return (
            f"corpus case {case_id!r} ({corpus_name}) names condition "
            f"{condition_id!r}, but that condition's corpus_cases do not carry "
            f"that case_id (carried: "
            f"{sorted(c.case_id for c in condition.corpus_cases)!r}).",
        )
    manifest_set = set(case.get(expectation_key) or ())
    specified_set = set(expectation.expected_firing)
    disagrees = (
        not manifest_set <= specified_set
        if relation == "subset"
        else manifest_set != specified_set
    )
    if disagrees:
        return (
            f"corpus case {case_id!r} ({corpus_name}, condition {condition_id!r}): "
            f"the manifest's {expectation_key} {sorted(manifest_set)!r} disagrees "
            f"with the specification's expected_firing {sorted(specified_set)!r} "
            f"under the {relation} relation this corpus is compared by.",
        )
    return ()


def vision_seed_conflicts() -> Tuple[str, ...]:
    """The one conformance claim kept in the vision -> specification
    direction (item 150): every ``docs/aide/vision.md`` section 6 seed
    title has a :data:`VISION_SEED_DISPOSITION` entry, every disposition
    resolves (``mode:<id>`` to a :data:`SPECIFICATION` key,
    ``condition:<id>`` to a :data:`CONDITIONS` key, or ``retired``), and no
    disposition names a title section 6 does not carry. The seed list
    provides provenance, never ids."""
    conflicts = []
    titles = set(vision_seed_titles().values())
    for title in sorted(titles):
        if title not in VISION_SEED_DISPOSITION:
            conflicts.append(
                f"vision.md section 6 seed title {title!r} has no "
                f"VISION_SEED_DISPOSITION entry."
            )
    for title, disposition in VISION_SEED_DISPOSITION.items():
        if title not in titles:
            conflicts.append(
                f"VISION_SEED_DISPOSITION names {title!r}, which vision.md section "
                f"6 does not carry."
            )
        if disposition == "retired":
            continue
        kind, _sep, target = disposition.partition(":")
        if kind == "mode" and target.isdigit() and int(target) in SPECIFICATION:
            continue
        if kind == "condition" and target in CONDITIONS:
            continue
        conflicts.append(
            f"VISION_SEED_DISPOSITION[{title!r}] = {disposition!r} does not "
            f"resolve to a SPECIFICATION mode, a CONDITIONS entry or 'retired'."
        )
    return tuple(conflicts)


# =========================================================================== #
# Rendering: specification_to_dict / render_markdown (AC19, AC20, AC23)
# =========================================================================== #


def specification_to_dict() -> dict:
    """A deterministic, JSON-ready dict for the shipped specification. Takes
    no argument. Returns a fresh dict tree on every call -- mutating the
    result never leaks into a later call."""
    modes = []
    for mode in iter_modes():
        modes.append(
            {
                "id": mode.id,
                "parent": mode.parent,
                "path": mode_path(mode),
                "name": mode.name,
                "short_name": mode.short_name,
                "definition": mode.definition,
                "discriminator": mode.discriminator,
                "mechanism": mode.mechanism,
                "observability": mode.observability,
                "candidate_features": [
                    {"path": feature.path, "role": feature.role}
                    for feature in mode.candidate_features
                ],
                "intended_rules": [
                    {
                        "rule_id": rule.rule_id,
                        "detector": rule.detector,
                        "evidence_rung": rule.evidence_rung,
                    }
                    for rule in mode.intended_rules
                ],
                "corpus_cases": [
                    {
                        "case_id": case.case_id,
                        "corpus": case.corpus,
                        "expected_firing": list(case.expected_firing),
                        "reason": case.reason,
                        "agrees": case_agrees(case),
                    }
                    for case in mode.corpus_cases
                ],
                "severity": mode.severity,
                "status_authored": mode.status,
                "status_derived": derive_status(mode),
                "derived_rung": derive_mode_rung(mode),
                "provenance": mode.provenance,
            }
        )
    conditions = []
    for condition in iter_conditions():
        conditions.append(
            {
                "id": condition.id,
                "name": condition.name,
                "short_name": condition.short_name,
                "definition": condition.definition,
                "mechanism": condition.mechanism,
                "candidate_features": list(condition.candidate_features),
                "recording_rules": list(condition.recording_rules),
                "exempting_rules": list(condition.exempting_rules),
                "corpus_cases": [
                    {
                        "case_id": case.case_id,
                        "corpus": case.corpus,
                        "expected_firing": list(case.expected_firing),
                        "reason": case.reason,
                        "agrees": case_agrees(case),
                    }
                    for case in condition.corpus_cases
                ],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "note": _NOTE,
        "modes": modes,
        "conditions": conditions,
        "vision_seed_disposition": dict(VISION_SEED_DISPOSITION),
    }


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown() -> str:
    """A deterministic Markdown rendering of the shipped specification --
    the review surface item 150 signs. Takes no argument. Lifecycle status
    is rendered as its word, never as one of the six AIDE status icons
    (AC23).

    An empty ``Candidate features:`` / ``Intended rules:`` / ``Corpus
    cases:`` section renders one ``- (none)`` bullet rather than nothing at
    all (item 146): the catalogue's first ``proposed`` entry has two empty
    sections by design, and a bare heading followed by the next heading
    reads to a reviewer as a hole in the document rather than as a
    deliberate absence."""
    payload = specification_to_dict()
    lines = [
        "# Failure-Mode Specification",
        "",
        _md_escape(payload["note"]),
        "",
        f"Schema version: {payload['schema_version']}.",
        "",
    ]
    for mode in payload["modes"]:
        if mode["parent"] is None:
            lines.append(f"## Mode {mode['id']}: {mode['name']}")
        else:
            lines.append(
                f"## Mode {mode['id']} ({mode['path']}, sub-mode of "
                f"{mode['parent']}): {mode['name']}"
            )
        lines.append("")
        lines.append(f"- Short name (corpus manifests): {mode['short_name'] or '(none)'}")
        parent = mode["parent"] if mode["parent"] is not None else "(none, top-level)"
        lines.append(f"- Parent: {parent}")
        lines.append(f"- Definition: {_md_escape(mode['definition'])}")
        lines.append(f"- Discriminator: {_md_escape(mode['discriminator'])}")
        lines.append(f"- Observability: {mode['observability']}")
        lines.append(f"- Severity: {mode['severity']}")
        lines.append(f"- Provenance: {mode['provenance']}")
        lines.append(f"- Status, authored: {mode['status_authored']}")
        lines.append(f"- Status, derived (live): {mode['status_derived']}")
        rung = mode["derived_rung"] if mode["derived_rung"] is not None else "none"
        lines.append(f"- Derived rung (strongest edge, live): {rung}")
        lines.append("")
        lines.append("Candidate features:")
        lines.append("")
        if not mode["candidate_features"]:
            lines.append("- (none)")
        for feature in mode["candidate_features"]:
            if feature["role"] == "stage18-metric-anchor":
                lines.append(
                    f"- Stage-18 metric anchor path (`{feature['role']}`): "
                    f"`{feature['path']}`"
                )
            else:
                lines.append(f"- `{feature['role']}` candidate path: `{feature['path']}`")
        lines.append("")
        # Rendered *after* the candidate-feature list, deliberately: a
        # mechanism sentence names the paths it reasons about, and the first
        # place a reader (or a test scanning for the first occurrence of an
        # anchor path) meets one must be the bullet that labels it a
        # Stage-18 metric anchor, not a sentence that merely mentions it.
        lines.append(f"Mechanism: {_md_escape(mode['mechanism']) or '(none)'}")
        lines.append("")
        lines.append("Intended rules:")
        lines.append("")
        if not mode["intended_rules"]:
            lines.append("- (none)")
        for rule in mode["intended_rules"]:
            detector = rule["detector"] or "(none)"
            lines.append(
                f"- `{rule['rule_id']}` (detector: {detector}) -- evidence rung: "
                f"{rule['evidence_rung']}"
            )
        lines.append("")
        lines.append("Corpus cases:")
        lines.append("")
        if not mode["corpus_cases"]:
            lines.append("- (none)")
        for case in mode["corpus_cases"]:
            expected = ", ".join(case["expected_firing"]) if case["expected_firing"] else "(none)"
            lines.append(
                f"- `{case['case_id']}` ({case['corpus']}): expected firing = "
                f"[{expected}]; agrees with live measurement: {case['agrees']}. "
                f"{_md_escape(case['reason'])}"
            )
        lines.append("")
    for condition in payload["conditions"]:
        lines.append(f"## Condition {condition['id']}: {condition['name']}")
        lines.append("")
        lines.append(f"- Short name (corpus manifests): {condition['short_name']}")
        lines.append(f"- Definition: {_md_escape(condition['definition'])}")
        lines.append(
            f"- Recording rules: {', '.join(condition['recording_rules'])}"
        )
        exempting = ", ".join(condition["exempting_rules"]) or "(none)"
        lines.append(f"- Exempting rules: {exempting}")
        lines.append("")
        lines.append("Candidate features:")
        lines.append("")
        for path in condition["candidate_features"]:
            lines.append(f"- `hypothesised` candidate path: `{path}`")
        lines.append("")
        lines.append(f"Mechanism: {_md_escape(condition['mechanism'])}")
        lines.append("")
        lines.append("Corpus cases:")
        lines.append("")
        if not condition["corpus_cases"]:
            lines.append("- (none)")
        for case in condition["corpus_cases"]:
            expected = ", ".join(case["expected_firing"]) if case["expected_firing"] else "(none)"
            lines.append(
                f"- `{case['case_id']}` ({case['corpus']}): expected firing = "
                f"[{expected}]; agrees with live measurement: {case['agrees']}. "
                f"{_md_escape(case['reason'])}"
            )
        lines.append("")
    lines.append("## Vision section 6 seed disposition")
    lines.append("")
    for title, disposition in payload["vision_seed_disposition"].items():
        lines.append(f"- {_md_escape(title)} -> {disposition}")
    lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


# =========================================================================== #
# __main__
# =========================================================================== #


def main(argv: Optional[Iterable[str]] = None) -> int:
    """``python -m segfacet.failure_modes [--json PATH] [--md PATH]``.
    Defaults to the two committed artifact paths under ``docs/aide/``.
    Writes both through ``Path.write_bytes`` -- never ``write_text`` -- so
    the byte stream is exactly what is serialised, with no platform newline
    translation (AC21)."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Regenerate the generated failure-mode specification rendering "
            "(item 144)."
        )
    )
    parser.add_argument("--json", type=Path, default=JSON_PATH)
    parser.add_argument("--md", type=Path, default=MD_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = specification_to_dict()
    json_text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    md_text = render_markdown()

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(json_text.encode("utf-8"))
    args.md.write_bytes(md_text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
