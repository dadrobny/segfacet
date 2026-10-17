> Stage 32's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 32`, run on the main or queue branch, moves it back.

## Stage 32 — Selected-Mode Refinement: one failure mode fully specified end to end (G2, G7, G8)

> **Annotation 2026-09-22.** Queue-022 shipped D0–D2. Modes 3 and 4 were signed off at a
> recorded intermediate state, not at the bar (gate `gate-bb24`), so criterion 1 does not hold. The
> review behind that outcome is carried by **Stage 33**, which re-grounds the corpus and the
> rules, re-signs both modes, and re-runs D3's validation at its own close; that close
> attests criterion 1 here. Nothing below is re-edited.

**Goal.** The signed-off specification **documents** all sixteen modes; it does not
commit to implementing them. What each mode has behind it is uneven: on 2026-09-15 six
modes derive `validated` (1, 4, 6, 9, 15, 16), three `implemented` (2, 3, 8) and seven are
`proposed` with no rule (5, 7, 10–14). Several fixtures express their mode only through
co-detections (`fuse_adjacent` is caught by mode 1's and mode 6's detectors, not mode
2's), and some detectors serve a mode only by proxy (`bounds` and `reference_delta` on
five modes). This stage does not level that out. It takes **modes the maintainer
selects**, interactively, and brings **at least one of them to fully specified end to
end** — the pipeline's MVP: one failure mode whose definition, fixture, features and rule
all make sense together and are demonstrated on the corpus. Every other mode stays in the
specification as documented, at whatever status it derives, and can be picked up
individually, when and where wanted, in any later queue. Some tests will fail or be
rewritten on the way, and that is expected.

**What "fully specified end to end" means** — the bar a mode must clear to count toward
this stage:

1. Its specification entry is complete and confirmed by the maintainer (definition,
   discriminator, scope, observability, severity, candidate features, intended rules,
   corpus cases).
2. At least one committed synthetic fixture expresses the mode, and its expected firing
   set names at least one of the mode's own intended rules and agrees with the measured
   firing.
3. Every feature path that detector reads is extracted and catalogued.
4. At least one detector decides the mode and serves no other mode — the generic volume
   proxies (`bounds`, `reference_delta`) do not count.
5. Its status derives `validated`.
6. It is signed off by the maintainer, with date and outcome recorded in the
   specification module.

**How it runs.** The maintainer selects the mode(s) at each queue's planning; the first
queue must include a mode that can reach the bar. A queue may hold one mode or several
related ones, and ends in a human gate over those modes' rendering in
`docs/aide/failure_modes.generated.md`. Items are **interactive by design**: each mode's
item spec is authored with the maintainer, whatever `loop.clarify` says, because "does
this fixture, feature and rule make sense for this mode" is not derivable from the code.
An item may change **anything its mode needs** — the catalogue entry, fixtures and
operators, features, rules, detectors and thresholds — provided every change is authored
in the specification and approved at the checkpoint. A threshold retuned here is
calibrated on the synthetic corpus only and is re-calibrated on real GT in Stage 21. A
mode may be deliberately left at a draft stage (`proposed` or `specified`), and a mode
that turns out not to reach the bar is recorded as such, not forced.

**Deliverables.**

- **D0 — Stage 20's exercise report and specificity ratchet, at the head of the first
  queue.** Stage 20's items **139** (per-rule and per-operator corpus-exercise reporting,
  across both corpora) and **140** (no unintended rule may fire, allowlist derived from
  each corpus case's `expected_firing`) are re-specified against the specification and
  built **first**, so from the first refinement item on, every change in what fires is
  either authored in the specification or fails the suite. A co-detection is allowed only
  where the specification records it.
  **Build posture, 2026-09-18.** Item 139's preserved spec
  ([`items/139-per-rule-and-per-operator.md`](../items/139-per-rule-and-per-operator.md),
  authored 2026-09-03 for queue-019) carries 33 acceptance criteria written against
  the pre-sign-off catalogue and the pre-1.56.0 contract. It is **re-authored from
  item template 2, not re-checked or amended**: acceptance criteria for the exercise
  report's own deliverable only, and a Testing Strategy that names each extra case
  with a label and the failure mode it guards, since the test-writer writes one test
  per criterion plus the labelled cases and nothing else (§6). Its recorded
  measurements are inputs to the new spec. Item 140 has no spec yet and is authored
  to the same bound. Both are justified siblings of the first refinement item, which
  is what lets them lead its queue under the `prototype` posture.
- **D1 — the MVP mode.** At least one maintainer-selected mode brought to the bar above
  and signed off.
- **D2 — further selected modes, optional.** Any other modes the maintainer selects,
  refined as far as wanted and signed off at their queue's checkpoint — to the bar, or to a
  recorded intermediate state.
- **D3 — Stage 20 closed and this stage validated.** Stage 20's item **142** runs at the
  end of the last queue: the traceability artifact regenerated from a clean tree, the
  specificity assertion driven over every corpus case, the cross-mode margins re-measured,
  and the end-to-end detection count stated in `progress.md` per lifecycle status and per
  rung. This stage's own validation runs in the same item: every generated artifact
  byte-identical from a clean tree, every corpus case's measured firing equal to its
  expected set, and which modes were refined, which met the bar, and which were left as
  documented drafts.

**Known inputs per mode — a menu, not a commitment.** Recorded so a selected mode's
planning starts from what is already known (each a dated `insights.md` entry); nothing
here obliges the stage to build it:

- *Mode 2 fused:* a bridged fuse operator, so the mode is decided by its own signal rather
  than co-detections; the intervertebral-disc-channel sub-type decided in or out.
- *Mode 3 split:* a split operator (part of one label reassigned to its neighbour).
- *Mode 4 islands:* island distance from the main body.
- *Mode 5 holes:* an enclosed-cavity or Euler-characteristic feature.
- *Mode 6 not segmented:* the spacing-gap signal over
  `stage3.spacing_consistency.spacings_mm[]` for the renumbered form
  (`remove_level_relabel`, which fires nothing today).
- *Mode 7 hallucinated:* an above-expected-count check and a fixture.
- *Mode 1 accuracy:* its ground-truth-relative sub-analyses (boundary band, local blob,
  spatial distribution) decided in or out; the FOV-truncation condition's exemptions
  reviewed against the rules that serve each mode.
- *Mode 10 skipped level label:* a skip-relabel operator and a spacing-aware detector
  separating it from mode 6.
- *Mode 11 unprompted variant:* a transitional-label detector over
  `relationships.present_levels[]` plus a configuration flag.
- *Modes 13 collapsed / 14 duplicated:* per-component centroids (not extracted today);
  mode 13's coincident-centroid silent pass (carried defect, item 129).
- *Mode 9 out-of-order:* a multi-relabel fixture, if expressible, to lift the `sequence`
  edge off `needs-real-data`; per-detector attribution so `mislabel`'s spline-offset
  detector can serve no mode without its firing signal being classified `bookkeeping`.
- *Mode 12 shifted:* stays `needs-external-classifier` unless an external classifier input
  is decided.
- *Mode 15 overlap:* stays `structurally-unobservable` unless multichannel input is decided
  (Backlog).
- *Mode 16 implausible tissue:* an intensity corpus case built against a reference, for
  the `intensity_reference_delta` edge.

**Dependencies.** Stage 31 (the harness, the vision and the seams it clears). Stage 20's
items 136–138 (✅). Runs before Stage 27 — new features are added in the current record
shape and are expected to be renamed there — and before Stages 21 and 16, which need a
pipeline with at least one mode demonstrated end to end. Per-mode work beyond this stage
is not blocked by it and belongs to no stage.

**Validation / acceptance.**

- At least one mode in the specification meets all six conditions of "fully specified
  end to end" above, each checked against live state: the committed fixture's measured
  firing agrees with its expected set, the deciding detector serves no other mode, and
  the status derives `validated` (**G2**).
- Every mode this stage refined carries a maintainer sign-off with date and outcome in the
  specification module (**G8**).
- Every mode not refined keeps a complete specification entry and is reported at its
  derived status in `docs/aide/failure_modes.generated.md`; a mode left at `proposed`,
  `specified` or `implemented` is an accepted end state, and a mode with no entry or no
  status is not (**G2**).
- The specificity assertion is enforced for every corpus case across both corpora, and
  every registered rule and operator is exercised by a case or recorded as unexercised with
  a reason (**G2**, Stage 20 criteria 3–4).
- The end-to-end detection count is recorded in `progress.md` per lifecycle status and per
  evidence rung, as measured numbers with what they were measured on, naming the modes
  refined and the modes left as documented drafts (**G7**, Stage 20 criterion 5).
