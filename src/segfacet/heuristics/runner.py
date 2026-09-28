"""Config-driven rule runner for the heuristic rule engine (item 026).

The runner is the execution entry point: it selects enabled rules, calls each
one's ``evaluate`` method in a deterministic order, aggregates the findings,
and gates them against the case CONDITIONs (item 191).

Design decisions:
- Default to ``iter_rules()`` (all registered rules, sorted by ``rule_id``)
  when no explicit ``rules`` list is given, so callers need not enumerate rules
  by hand; the registry is the authoritative source.
- Respect ``config.rule_enabled(rule.rule_id)`` before calling a rule so that
  the operator can disable individual rules without touching code.
- Never mutate the ``record`` mapping: pass it to each rule as-is (read-only
  by convention; the core does not deep-copy it, relying on well-behaved rules
  and the immutability contract documented in the spec).
- Return a plain ``list`` (never ``None``) — callers can always iterate the
  result without a None-guard.

The condition gate (item 191)
------------------------------
A label named by a case CONDITION (``segfacet.failure_modes.CONDITIONS``) is
excluded from every rule's finding unless that rule opts in
(``Rule.condition_opt_ins``). The gate runs here, once, on the raw findings —
never inside a rule's own ``evaluate`` and never by masking the record (a
masked label would look *absent* to a rule like ``coverage`` that reads the
present-label set, not merely as one it should not judge). A finding is
dropped when **any** of its ``labels`` is a member of a condition the
producing rule does not opt in to; a case-level finding (empty ``labels``) is
never dropped, and a duck-typed rule with no ``condition_opt_ins`` attribute
(a test double) defaults to opting in to nothing (read via
``getattr(rule, "condition_opt_ins", ())``).

Two conditions are gated, in this order, because ``fov_truncation``
membership must be settled before ``displaced_vertebra`` is derived: a
truncated label's centroid is displaced by the crop, so it cannot also be
judged genuinely displaced (item 191 A2/A3):

1. ``fov_truncation`` — membership is
   ``segfacet.heuristics.fov.border_touching_labels(record)``, a pure
   function of the record (never of any rule's findings).
2. ``displaced_vertebra`` — membership is the labels of the *surviving*
   findings whose ``rule_id`` is one of
   ``segfacet.failure_modes.CONDITIONS["displaced_vertebra"].recording_rules``
   (``spline_offset``). Because it is derived from findings, not from the
   record, it is computed only after the ``fov_truncation`` gate has already
   run.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional

from segfacet import failure_modes
from segfacet.heuristics.finding import Finding
from segfacet.heuristics.fov import border_touching_labels
from segfacet.heuristics.rule import Rule, iter_rules

__all__ = ["run_rules"]


def run_rules(
    record: Mapping[str, Any],
    config: Any,
    rules: Optional[Iterable[Rule]] = None,
) -> List[Finding]:
    """Run all enabled rules against *record*, gate the findings against the
    case CONDITIONs (item 191), and return the survivors.

    Parameters
    ----------
    record:
        The per-case feature dict (a read-only ``Mapping[str, Any]`` as
        produced by ``segfacet.feature_report.build_features_block``).  The
        runner never mutates this mapping.
    config:
        A :class:`~segfacet.config.HeuristicConfig` instance.  Each rule's
        enabled state is queried via ``config.rule_enabled(rule.rule_id)``.
    rules:
        An optional iterable of :class:`~segfacet.heuristics.Rule` instances to
        run.  When ``None`` (the default), all rules currently in the registry
        are used via :func:`~segfacet.heuristics.rule.iter_rules` (sorted
        ascending by ``rule_id``).  Pass an empty list to run nothing.

    Returns
    -------
    list[Finding]
        Surviving findings from all enabled rules, in the order each rule
        produced them (ascending ``rule_id``, then that rule's own emission
        order) with any condition-gated finding removed.  Always a list;
        never ``None``.
    """
    effective_rules: Iterable[Rule] = iter_rules() if rules is None else rules

    # Run every enabled rule first, keeping each finding paired with its
    # producing rule (needed for the per-rule opt-in check below) and with
    # the original emission order (preserved by appending in iteration
    # order, never re-sorted).
    pairs: List[tuple] = []
    for rule in effective_rules:
        if not config.rule_enabled(rule.rule_id):
            continue
        for finding in rule.evaluate(record, config):
            pairs.append((rule, finding))

    # Gate 1: fov_truncation. Membership is a pure function of the record.
    fov_labels = border_touching_labels(record)
    survivors: List[tuple] = []
    for rule, finding in pairs:
        opt_ins = {o.condition for o in getattr(rule, "condition_opt_ins", ())}
        if finding.labels and (finding.labels & fov_labels) and "fov_truncation" not in opt_ins:
            continue
        survivors.append((rule, finding, opt_ins))

    # Gate 2: displaced_vertebra. Membership is derived from the survivors of
    # gate 1's recording rule(s) findings, so it must run after gate 1.
    recording_rules = set(
        failure_modes.CONDITIONS["displaced_vertebra"].recording_rules
    )
    displaced_labels: set = set()
    for rule, finding, _opt_ins in survivors:
        if rule.rule_id in recording_rules:
            displaced_labels.update(finding.labels)

    aggregated: List[Finding] = []
    for rule, finding, opt_ins in survivors:
        if (
            finding.labels
            and (finding.labels & displaced_labels)
            and "displaced_vertebra" not in opt_ins
        ):
            continue
        aggregated.append(finding)

    return aggregated
