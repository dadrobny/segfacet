"""Spline-offset (displaced-vertebra) rule (item 189).

Item 033's ``mislabel`` rule originally carried two detectors: Detector A
(spline-offset misalignment) and Detector B (out-of-order label sequence,
specification mode 9). The item-150 sign-off (2026-09-14) retired the
failure-mode reading of Detector A: the offset from the fitted spinal curve
is an anatomy-classification signal (spondylolisthesis, scoliosis, a rigid
misplacement), not a segmentation defect, so it serves no mode in
``failure_modes.SPECIFICATION``. This item (2026-09-28) gives that detector
a rule of its own -- ``SplineOffsetRule``, modelled on ``border.py`` -- and
makes it the **recording rule** of a new case CONDITION,
``failure_modes.CONDITIONS["displaced_vertebra"]``, alongside
``fov_truncation``. ``mislabel`` keeps only Detector B (ordering).

Design decisions (moved unchanged from item 033's Detector A, recorded here
per item 189 spec A1-A3):
- The detector's evaluate logic, tag text, threshold, comparison, terminal
  skip, direction clause and severity handling move **verbatim** from
  ``mislabel.py``. The only visible difference is the finding's ``rule_id``:
  ``"spline_offset"`` instead of ``"mislabel"``.
- Fires on ``offset_mm >= max_offset_mm`` (default ``13.0``, inclusive) and
  is label-attributed (single offending label).
- Never fires on a **terminal** entry (``is_terminal`` truthy, item 123) --
  an entry with no ``is_terminal`` key, or one carrying ``None``, is interior
  and still fires. See "Threshold calibration (item 123)" below for why, and
  ``features/spline_offset.py``'s "Terminal-vertebra exclusion" section for
  the mechanism.
- Reads ``dx_mm``/``dy_mm``/``dz_mm`` when all three are present and finite
  (item 120), naming the dominant displacement direction as one of
  ``"left-right"``, ``"anterior-posterior"`` or ``"cranio-caudal"`` -- the
  largest of ``|dx_mm|``, ``|dy_mm|``, ``|dz_mm|``, ties broken x -> y -> z.
  This reading rests on the RAS axis contract stated in
  ``features/spline_offset.py``'s module docstring: array axis 0 is
  left-right, axis 1 anterior-posterior, axis 2 cranio-caudal, because
  ``io.load_volume`` reorients every volume to ``("R", "A", "S")`` and
  ``centroid_mm`` carries no affine of its own. An entry missing any
  component, or carrying a non-finite one, omits the direction clause
  entirely rather than guessing or raising.
- Findings are emitted in ascending label order.
- Unrecognised severity string raises ValueError before any per-record
  processing.
- The caller's record is never mutated.
- **Params live in the rule's own section** (A3): reads
  ``rules.spline_offset.params.max_offset_mm`` (default 13.0) and
  ``rules.spline_offset.params.severity`` (default ``"flagged-for-review"``).
  Enabled when the section is absent, like ``neighbour_contact``. The
  retired ``mislabel.flag_offset_outliers`` key has no equivalent here: this
  rule has no companion detector to gate against, so there is nothing for a
  second flag to disable.

Scope fence: no change to the offset feature (``features/spline_offset.py``
code) or to the threshold value; no re-calibration; no change to what
``mislabel``'s ``ordering`` detector reads. The condition gate itself lives in
the runner (``segfacet.heuristics.runner.run_rules``, item 191); this rule
only declares its own opt-in to ``displaced_vertebra`` (``condition_opt_ins``
below) -- it opts in to no other condition, so a label this rule reports that
is also a member of ``fov_truncation`` is gated (the crop displaces the
truncated label's centroid, so it cannot also be judged genuinely displaced).

Threshold calibration (item 123, recalibrated 2026-08-29)
-----------------------------------------------------------
``_DEFAULT_MAX_OFFSET_MM`` is derived (``scripts/rebuild_verse_reference.py
::derive_max_offset_mm``) from the real, 80-subject VerSe19 training cohort's
committed ``reference_verse_v1.json``: the smallest multiple of ``0.5`` mm
strictly above ``P``, floored at ``6.0`` mm, where ``P`` is the maximum
``spline_offset_mm`` ``p99`` over levels with at least 10 **interior**
(non-terminal, see below) occurrences. The measured ceiling is
``P = 12.91`` mm at level ``T10``, giving ``_DEFAULT_MAX_OFFSET_MM = 13.0``.

**Terminal vertebrae are excluded from this measurement and from this
detector itself** (item 123, human decision 2026-08-29): the first
calibration run measured `P = 21.209` mm at `L5`, driven entirely by the
held-out estimator's terminal-extrapolation artefact
(`features/spline_offset.py`'s "Terminal-vertebra exclusion" section)
rather than real anatomy -- `L5`'s *interior* offset never exceeds `1.00` mm
in the same cohort. Excluding terminal entries from both the reference
distribution (`reference/ingest.py`) and this detector brought the
measurement back inside the approved corpus window.

Corpus margins (from `tests/corpus/manifest.json`'s cases, each measured via
a freshly built `extract_feature_record`, all on **interior** entries only,
re-measured 2026-09-28 against the lordotic base fixture, item 189):
- `relabel_swap`'s largest interior reading (label 23 / L4) is
  `5.624555` mm and must **not** fire -- the non-firing ceiling.
- `crop_at_border`'s label-22 reading is `0.226480` mm, a non-firing interior
  reading (item 212, 2026-10-05: the case is now a true anterior volume crop,
  not the translation whose `18.025609` mm reading used to fire here). It no
  longer bounds the threshold, so ``_DEFAULT_MAX_OFFSET_MM``'s upper bound
  rests on `displace`'s reading alone. The non-firing ceiling above does not
  move.
- `displace`'s label-22 reading is `14.615923` mm and **must** fire --
  1.62 mm above the threshold (item 177's lateral form lowered it from item
  173's 17.615126).

Distribution calibrated against: `src/segfacet/reference/reference_verse_v1.json`.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from segfacet.heuristics.finding import Finding
from segfacet.heuristics.rule import (
    ConditionOptIn,
    ConsumedPath,
    Rule,
    RuleDetector,
    RuleModeDeclaration,
    register_rule,
)
from segfacet.verdict import Severity

__all__ = ["SplineOffsetRule"]


# --------------------------------------------------------------------------- #
# Reason tag constant — stable, testable start-of-reason marker
# --------------------------------------------------------------------------- #

_MISALIGN_TAG = "Vertebra misaligned from spinal curve:"

_DEFAULT_MAX_OFFSET_MM = 13.0


# --------------------------------------------------------------------------- #
# Severity helper (mirrors mislabel.py / border.py)
# --------------------------------------------------------------------------- #

_LABEL_TO_SEVERITY: Dict[str, Severity] = {sev.label: sev for sev in Severity}


def _severity_from_param(label: str) -> Severity:
    """Map a severity label string to its Severity member.

    Raises
    ------
    ValueError
        If *label* is not a recognised Severity label string.
    """
    sev = _LABEL_TO_SEVERITY.get(label)
    if sev is None:
        known = list(_LABEL_TO_SEVERITY.keys())
        raise ValueError(
            f"Unknown severity label {label!r} in spline_offset rule config. "
            f"Known labels: {known}."
        )
    return sev


# --------------------------------------------------------------------------- #
# SplineOffsetRule
# --------------------------------------------------------------------------- #


@register_rule
class SplineOffsetRule(Rule):
    """Spline-offset (displaced-vertebra) rule (item 189).

    Records the ``displaced_vertebra`` CONDITION
    (``failure_modes.CONDITIONS``): a vertebra whose centroid is a large
    outlier from the fitted spinal curve, via the per-vertebra perpendicular
    spline offset (``per_label.{label}.curve.offset_mm``, item 018).
    Moved unchanged from ``mislabel.py``'s former Detector A.
    """

    rule_id = "spline_offset"

    # This rule is displaced_vertebra's recording rule (item 191): its own
    # finding on a genuinely displaced label must always survive the
    # runner's condition gate. It opts in to no other condition.
    condition_opt_ins = (
        ConditionOptIn(
            condition="displaced_vertebra",
            paths=(
                "per_label.{label}.curve.dx_mm",
                "per_label.{label}.curve.dy_mm",
                "per_label.{label}.curve.dz_mm",
                "per_label.{label}.curve.offset_mm",
            ),
            reason=(
                "the offset and its axis components are the "
                "displaced_vertebra condition's own evidence: this rule is "
                "its recording rule"
            ),
        ),
    )

    # No failure mode (item 150): DisplacePerturbation
    # (src/segfacet/synth/identity_ordering_alignment.py) is the fixture of
    # the displaced_vertebra CONDITION, not of a mode in
    # failure_modes.SPECIFICATION.
    mode_declaration = RuleModeDeclaration(
        mode_less_reason=(
            "records the displaced_vertebra CONDITION "
            "(failure_modes.CONDITIONS['displaced_vertebra']), not a "
            "failure mode: the offset from the spinal curve is an "
            "anatomy-classification signal (spondylolisthesis, scoliosis, "
            "a rigid misplacement), not a defect of the segmentation -- "
            "item-150 sign-off, moved here from mislabel.py's Detector A at "
            "item 189 (2026-09-28). tests/corpus/manifest.json's displace "
            "is that condition's fixture."
        ),
        consumed_paths=(
            ConsumedPath(
                path="per_label",
                role="bookkeeping",
                reason=(
                    "container: the rule iterates the per-label entries to "
                    "reach each label's curve block; the container is not "
                    "itself a feature"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.curve.dx_mm",
                role="bookkeeping",
                reason=(
                    "message interpolation only (the ', predominantly "
                    "<axis>' clause), not the condition's evidence"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.curve.dy_mm",
                role="bookkeeping",
                reason=(
                    "message interpolation only (the ', predominantly "
                    "<axis>' clause), not the condition's evidence"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.curve.dz_mm",
                role="bookkeeping",
                reason=(
                    "message interpolation only (the ', predominantly "
                    "<axis>' clause), not the condition's evidence"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.curve.is_terminal",
                role="bookkeeping",
                reason=(
                    "gate: the terminal exemption, which suppresses a "
                    "finding rather than evidencing one"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.curve.offset_mm",
                role="condition-signal",
                reason=(
                    "evidence of the displaced_vertebra CONDITION this rule "
                    "records (item 150/189), which is not a failure mode"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.label",
                role="bookkeeping",
                reason=(
                    "identity: the label id carried into the finding's "
                    "labels set"
                ),
            ),
            ConsumedPath(
                path="per_label.{label}.level_name",
                role="bookkeeping",
                reason=(
                    "identity and message interpolation: names the level "
                    "in the finding"
                ),
            ),
        ),
        detectors=(
            RuleDetector(
                detector_id="spline_offset",
                description=_MISALIGN_TAG,
                question=(
                    "Does a vertebra's centroid sit far off the spinal curve "
                    "fitted through its neighbours?"
                ),
                fires_when=(
                    "a non-terminal label's `offset_mm` >= `max_offset_mm` "
                    "(inclusive); terminal (sequence-first/last) labels are "
                    "skipped"
                ),
                params=(("max_offset_mm", _DEFAULT_MAX_OFFSET_MM),),
                mode_less_reason=(
                    "the offset from the spinal curve is an "
                    "anatomy-classification signal (spondylolisthesis, "
                    "scoliosis), not a failure mode -- item-150 sign-off"
                ),
            ),
        ),
    )

    def evaluate(self, record, config) -> List[Finding]:  # type: ignore[override]
        """Evaluate spline-offset misalignment for *record*.

        Parameters
        ----------
        record:
            Per-case feature dict (read-only). Reads each
            ``record["per_label"][key]["curve"]`` entry, and its entry's
            ``label`` / ``level_name`` (item 215).
        config:
            HeuristicConfig instance. Reads ``rules.spline_offset.params``.

        Returns
        -------
        list[Finding]
            Zero or more findings, one per offending label, in ascending
            label order.

        Raises
        ------
        ValueError
            If ``rules.spline_offset.params.severity`` is an unrecognised
            string (raised before any per-record processing).
        """
        # Read severity once up-front; raises immediately on a bad string.
        sev_label: str = config.rule_param(
            self.rule_id, "severity", default="flagged-for-review"
        )
        severity = _severity_from_param(sev_label)

        max_offset = float(
            config.rule_param(
                self.rule_id, "max_offset_mm", default=_DEFAULT_MAX_OFFSET_MM
            )
        )

        per_label = record.get("per_label")
        if not isinstance(per_label, dict):
            per_label = {}

        return self._detect_offset_outliers(per_label, severity, max_offset)

    @staticmethod
    def _dominant_direction(entry: dict) -> Optional[str]:
        """Return the dominant displacement direction name for *entry*, or
        ``None`` when any of ``dx_mm``/``dy_mm``/``dz_mm`` is missing or
        non-finite (item 120, AC14/AC15).

        Selected as the largest of ``|dx_mm|``, ``|dy_mm|``, ``|dz_mm|``,
        ties broken x -> y -> z (left-right -> anterior-posterior ->
        cranio-caudal), per the RAS axis contract in
        ``features/spline_offset.py``.
        """
        components = []
        for key, name in (
            ("dx_mm", "left-right"),
            ("dy_mm", "anterior-posterior"),
            ("dz_mm", "cranio-caudal"),
        ):
            if key not in entry:
                return None
            try:
                value = float(entry[key])
            except (TypeError, ValueError):
                return None
            if not math.isfinite(value):
                return None
            components.append((abs(value), name))

        # Stable sort by descending magnitude keeps x -> y -> z tie order
        # (the insertion order above) for equal magnitudes.
        best = max(components, key=lambda c: c[0])
        return best[1]

    @staticmethod
    def _detect_offset_outliers(
        per_label: dict, severity: Severity, max_offset: float
    ) -> List[Finding]:
        """Spline-offset outliers (displaced-vertebra condition)."""
        normalised = []
        for label_entry in per_label.values():
            if not isinstance(label_entry, dict) or "label" not in label_entry:
                continue
            # The offset fields live in the label's ``curve`` kind block; the
            # identity (label, level_name) is the entry's own, stored once.
            entry = label_entry.get("curve")
            if not isinstance(entry, dict):
                continue
            if entry.get("is_terminal"):
                # A terminal (sequence-first/last) entry's held-out offset
                # extrapolates past the end of the estimator's own parameter
                # domain rather than measuring a genuine displacement -- item
                # 123, see this module's docstring. A missing key or `None`
                # is falsy and therefore interior, unchanged from before.
                continue
            try:
                label = int(label_entry["label"])
            except (TypeError, ValueError):
                continue
            offset = float(entry.get("offset_mm", 0.0) or 0.0)
            name = label_entry.get("level_name")
            direction = SplineOffsetRule._dominant_direction(entry)
            normalised.append((label, name, offset, direction))

        normalised.sort(key=lambda t: t[0])

        findings: List[Finding] = []
        for label, name, offset, direction in normalised:
            if offset >= max_offset:
                direction_clause = f", predominantly {direction}" if direction else ""
                findings.append(
                    Finding(
                        rule_id="spline_offset",
                        severity=severity,
                        reason=(
                            f"{_MISALIGN_TAG} label {label} ({name}) centroid "
                            f"lies {offset:.1f} mm off the fitted spinal curve"
                            f"{direction_clause} "
                            f"(threshold {max_offset:.1f} mm)."
                        ),
                        labels=frozenset({label}),
                        detector_id="spline_offset",
                    )
                )
        return findings
