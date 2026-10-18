> Stage 33's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 33`, run on the main or queue branch, moves it back.

## Stage 33 — Corpus & Rule Re-grounding: modes 2 and 3 to the bar (G2, G7, G8)

> **Re-targeted 2026-09-30.** The stage was titled and scoped for modes 3 and 4. At gate
> `gate-51da` (declined 2026-09-30) the maintainer re-drew the mode 2/3 boundary and moved
> the selected modes to **2 (fused vertebra segments) and 3 (split vertebra segment)**;
> mode 4 (islands) left the stage with its `gate-bb24` intermediate-state record standing
> (`insights.md`, 2026-09-30). The goal and scope paragraphs below are kept as written on
> 2026-09-22 and read through this note; D5 and the acceptance criteria name the final
> targets. Title corrected 2026-10-03 (`insights.md`, item 204, 2026-10-02).

**Goal.** Queue-022 took modes 3 (split vertebra segment) and 4 (islands) through bar
conditions 1–5, but the maintainer signed both off only at a recorded intermediate state
(gate `gate-bb24`, 2026-09-22). The review behind that decision (`insights.md`, entries dated
2026-09-22) found that the evidence rests on a corpus that cannot express what the rules
are meant to decide. The geometric base is five non-touching, axis-aligned boxes, so
`neighbour_contact`'s one firing value is simply the fixture's largest cross-section. Several
fixtures do not express the mode they are attributed to (`crop_at_border` is a
displacement, `fuse_adjacent` is two components with a gap, and `force_overlap`'s overlap
exists only in a reconstructed record). Several rules serve a mode by the wrong signal. This
stage rebuilds the base, re-authors those fixtures and re-homes the rules the review named.
It then brings **modes 3 and 4** back to the maintainer for an **at-the-bar** sign-off.
That sign-off is what closes **Stage 32's criterion 1** as well as this stage.

**Scope decisions (maintainer, 2026-09-22).** Target modes are 3 and 4 only. Modes 2 and 6
are re-grounded as fixtures and attributions but are **not** driven to the bar. The
inter-centroid-spacing rule they need (over `stage3.spacing_consistency.spacings_mm[]`) is
left to a later per-mode queue. Vertebra-local extents for `bounds` belong to **Stage 27**
(coordinate system), not here. Every value the specification and the specs quote is
re-measured on the new base, never carried over.

**Deliverables.**

- **D0 — protective fixes, at the head of the first queue.** These are justified siblings
  of this stage's work under the `prototype` posture: each makes the corpus regeneration
  cheaper, or stops it from passing silently.
  - Session-scoped fixtures for the whole-`aide check` run and for the specification and
    traceability regeneration, which about 27 tests repeat. The suite wall-clock doubled
    between 2026-09-01 and 2026-09-18 (`insights.md`, 2026-09-18).
  - Negative controls whose "wrong" input is a literal are rebuilt from live values with a
    constructed perturbation, and the class is grepped across `tests/`. Moving every corpus
    value is exactly the drift that turns such a control green (`insights.md`, item 167,
    2026-09-20).
  - `UNUSED_OPERATOR_REASONS` entries are validated: an entry for a name that is not
    registered, or for an operator that is registered and used, is reported as a conflict
    (`insights.md`, item 162, 2026-09-20). The first entry lands in this stage.
- **D1 — the lordotic geometric base.** `synth/clean_gt.py`'s five boxes are replaced by a
  lordotic L1–L5 with an 8 mm disc gap and per-level sagittal tilts of −8°, 0°, +8°, +18°
  and +35°. The A-P centroid path is the integral of the tilts, and there is no lateral
  curve (`insights.md`, 2026-09-22). The clean control fires nothing under the bundled
  default config. Both committed manifests and every downstream artifact are regenerated.
  The prototype under `scripts/prototypes/2026-09-22-lordotic-corpus/` is absorbed into
  `src/segfacet/synth/`, and the directory is deleted by this stage's last item that
  draws on it.
  - **A committed corpus rendering.** One sheet shows each case as a sagittal and coronal
    max-label projection, with the voxels changed against `clean_control` outlined
    (`insights.md`, queue-022, 2026-09-21).
  - **The status report's corpus section re-keyed** off `failure_modes.generated.json` and
    `traceability_matrix.generated.json`, replacing its hand-typed eight-mode legend
    (`insights.md`, queue-022, 2026-09-21).
- **D2 — fixtures that express their mode**, re-authored on the new base (`insights.md`,
  2026-09-22):
  - `split` becomes a ~20 % caudal cap of L4 relabelled L5. A new `split_own_label`
    puts the same cap under its own label, with the labels cranial to it shifted up. These
    are mode 3's two sub-types.
  - `crop_at_border` becomes a crop of the clean-control **volume** that removes 65 % of
    L5 inferiorly. It is the fixture the border gating of the size rules is measured on.
  - `fuse_adjacent` is bridged under L3, with L5 renumbered to L4. It is expected to fire
    nothing under the shipped rules, and its expected set records that honestly.
  - `displace` moves mostly left-right.
  - `force_overlap` and the `overlap` rule: either both are declared to need multi-channel
    input and the fixture is retired, or both go. Mode 15 may stay unimplemented, but no
    fixture may claim a mode it does not express.
  - `fragment` is parked as mode 1's catch-all case, with no further investment.

  **Reconciliation risk.** A corpus change reaches tests that pin the corpus's *values*
  without naming any corpus file. So each item's reconciliation sweep asks what new values
  the change emits, and greps for assertions that compare fresh output against a literal
  set (`insights.md`, item 166, 2026-09-20).
- **D3 — rules re-homed to the signal they read** (`insights.md`, 2026-09-22):
  - `neighbour_contact` leaves `fragmentation` and becomes a rule of its own, serving
    mode 3. `fragmentation` stops declaring mode 3. The rule-count and rule-id pins are
    paid once, in the same queue as the base regeneration. Contact is measured relative
    to the component's own surface, not as an absolute area, and is reported per
    connected component (naming the neighbour it touches, to guide merging) and per
    whole label (maintainer feedback, 2026-09-25).
  - `coverage` is re-homed from mode 6 to mode 10 (skipped level label). `remove_level`
    and `remove_level_relabel` stay attributed to mode 6, whose own rule is decided
    later. `coverage`'s firing on `remove_level` is a mode-10 co-detection (maintainer
    feedback, 2026-09-25).
  - `mislabel` keeps its `ordering` detector, extended to any out-of-sequence label. Its
    `spline_offset` detector moves to a new **displaced-vertebra condition** in
    `failure_modes.CONDITIONS`, beside `fov_truncation`. `displace` becomes that
    condition's fixture, and its severity ladder, which designates mode 1's
    `unanchored_foreground_fraction`, is re-homed with it (`insights.md`, item 153,
    2026-09-16). The per-label offset stays an anatomy signal and moves to a clinical
    group when Stage 27 re-taxonomises the schema.
  - A label in a condition (`fov_truncation`, the displaced vertebra) is excluded from
    every rule unless that rule explicitly opts in to the condition. This inverts
    `ConditionSpec.exempting_rules`. Which features stay valid on such a label is decided
    per rule when the rule uses them. `bounds` and `reference_delta`'s size features are
    the first measured instance (maintainer feedback, 2026-09-25).
  - `sequence` reports which sub-type it saw across modes 8–11. Mode 12 stays out.
  - `reference_delta` and `intensity_reference_delta` stay as general outlier detectors
    and are no mode's own detector. `intensity_reference_delta`'s claim on mode 16 with
    zero `signal` paths is resolved, and the conflict check learns to see that state
    (`insights.md`, item 164, 2026-09-20).
  - The expected level sequence admits per-section vertebra counts: cervical 7, thoracic
    11–13, lumbar 4–6, in any combination, with the sacrum not split into levels. The
    default is (7, 12, 5), so no rule reports an absent transitional vertebra as a gap.
    The order must be monotonic. A non-default count is accepted only when the scan shows
    the whole section plus the first vertebra on either side, or when the count is
    supplied as prior knowledge of the subject; otherwise `sequence` reports it as the
    transitional sub-type (maintainer feedback, 2026-09-25).
  - Mode 1 is attributed only when no other mode applies, and the rendering says so. The
    vocabulary is applied as the review defined it: a mode describes the vertebra, and
    "fragmentation" is one label in several parts.
  - With two conditions, the eval harness gains a condition-keyed bucket, so neither
    condition's case is reported under the clean-control name (`insights.md`, item 155,
    2026-09-16).
- **D4 — the bar checker and the rule documentation.**
  - `traceability.bar_conditions`' condition 2 is read **existentially**, as this
    roadmap words it: at least one committed case expresses the mode. That every attached
    case agrees is the specificity ratchet's job (`insights.md`, item 165, 2026-09-20).
    Condition 2 is also made **detector-granular**, intersecting `(rule_id, detector_id)`
    pairs from the measured findings (`insights.md`, item 167, 2026-09-20).
  - The severity-ladder constants are re-measured on the new base, covering the split
    operators (`insights.md`, item 169, 2026-09-22).
  - A generated `docs/aide/rules.generated.md` gives one row per detector: the question
    it asks, the path it reads, when it fires, its default, and the modes it serves
    (`insights.md`, 2026-09-22).
- **D5 — modes 2 and 3 re-signed at the bar (human gate).** The maintainer reads both
  modes' rendering, the corpus sheet and the rule table, and signs each off at the bar or
  records why not. The outcome is written to `MODE_SIGN_OFFS`. (Written for modes 3 and 4;
  re-targeted to 2 and 3 at `gate-51da`, 2026-09-30, and signed at `gate-0133`.)
- **D6 — stage validation, closing Stage 32.** Run from a clean clone: every generated
  artifact byte-identical, every corpus case's measured firing equal to its expected set,
  and the detection count re-stated per status and rung. This is Stage 32's D3 re-run on
  the re-grounded corpus. It attests Stage 32 criterion 1 alongside this stage's own
  criteria.

**Dependencies.** Stage 32's queue-022 (✅, merged). D0 leads the first queue. D1 lands
before D2 and D3, which re-measure on the new base. D5's gate needs D1–D4. Runs before
Stages 27, 21 and 16. Per-mode work on modes 2, 6 and 10 (the spacing rule and a
skip-relabel fixture) is not blocked by this stage and belongs to no stage.

**Validation / acceptance.**

- Modes 2 and 3 each meet all six conditions of Stage 32's "fully specified end to end", checked against live state on the lordotic corpus. Each carries a maintainer sign-off at `outcome="at-the-bar"`, or a recorded reason why it does not (**G2**). Re-targeted from modes 3 and 4 when gate-51da was declined (2026-09-30); mode 4 keeps its gate-bb24 intermediate-state sign-off.
- No committed corpus case is attributed to a mode or condition that its label map does
  not express, and every case's measured firing equals its expected set, across both
  corpora (**G2**, **G7**).
- No rule declares a mode through a detector that reads another mode's signal. Condition 4
  of the bar is checked mechanically at detector granularity (**G2**, **G8**).
- A label map holding both T12 and L1, and no T13, produces no missing-level finding
  (**G2**).
- The detection count is re-stated in `progress.md` per lifecycle status and per rung,
  as measured numbers with what they were measured on (**G7**).
