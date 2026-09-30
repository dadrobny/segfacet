<!-- aide-template: item 3 -->
# Item 203 — Modes 3 and 4 re-signed by the maintainer at the bar

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D5)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 203
> **Objectives:** G2, G8
> **Suggested branch:** `aide/203-modes-3-and-4-re`

---

## Description

Roadmap Stage 33 D5: the maintainer re-reads modes 3 (split vertebra segment)
and 4 (islands) on the re-grounded corpus and, for each, signs it off at the
bar or records why not. The outcome replaces the two `intermediate-state`
records that gate `gate-bb24` wrote to
`segfacet.failure_modes.MODE_SIGN_OFFS` on 2026-09-22.

**The decision is a person's.** No agent may take it, and no acceptance
criterion below asserts which outcome was chosen. The mechanism already
exists (item 168: `ModeSignOff`, `SIGN_OFF_OUTCOMES`, `MODE_SIGN_OFFS`, the
`sign_off` key and the `- Maintainer sign-off:` bullet in both generated
artifacts). This item adds no mechanism. It does three things:

1. **Raises the human gate** `gate-51da` (`Stage 33 at-the-bar sign-off of
   modes 3 and 4`) in `progress.md`, with reach `203, 204`. The spec-author
   raised it when this spec was written.
2. **States the decision brief** below: each of the six bar conditions as
   measured live on the lordotic corpus, and what has changed since
   `gate-bb24`.
3. **After, and only after, a person has approved the gate**, the builder
   transcribes the maintainer's per-mode outcome and reason into
   `MODE_SIGN_OFFS` as one `ModeSignOff` per mode, dated with the gate's
   resolution date. It then regenerates both specification artifacts and
   reconciles the tests that pinned the 2026-09-22 records.

**The builder does not start while the gate is `⏳ Awaiting`.** A gate that
reads `❌ Declined` means "neither yet". The decline keeps blocking, the
change the maintainer names is re-planned as new work, and this item does
not merge. `aide merge` does not consult the gate table (only `aide claim`
does, through `_pick_item`), so this hold is the orchestrator's to keep.
The acceptance criteria also enforce it: AC2 and AC3 cannot pass until a
person has approved the gate.

### What this item is NOT

- **Not the decision.** No agent runs `aide gate approve` or
  `aide gate decline`.
- **Not a change to either mode.** No `ModeSpec` field, `IntendedRule` edge,
  `CorpusCaseExpectation`, rule, detector, threshold, feature, operator or
  fixture moves. A change the maintainer asks for at the gate is a new item.
- **Not an attestation.** No criterion carries a *(closes Stage N criterion
  M)* annotation. Stage 33's criterion 1 and Stage 32's criterion 1 are
  attested by item 204 from a clean clone.
- **Not condition 6 mechanised.** `traceability.BAR_CONDITIONS` stays five
  entries long (A2).

### Decision brief — what the maintainer is asked, and what is true

Everything below was **measured on this tree on 2026-09-29** (branch
`aide/203-modes-3-and-4-re` at `2d2306d`, which carries items 200–202 merged
on `aide/queue-027`) with `.venv/bin/python`, through
`traceability.bar_conditions`, `failure_modes.measured_detector_firing` and
`pipeline.extract_feature_record` under the bundled default config. It says
what is true and does not argue for an answer.

#### The ask

For **each** of mode 3 and mode 4, one of three answers:

1. **At the bar** (`outcome = "at-the-bar"`): the entry, the fixtures, the
   feature and the detector make sense together, and the mode counts toward
   Stage 33 criterion 1 and Stage 32 criterion 1.
2. **At a recorded intermediate state** (`outcome = "intermediate-state"`),
   with the reason: the work is accepted as far as it went, and the mode does
   not count toward the bar. Roadmap Stage 33's criterion 1 accepts "a
   recorded reason why it does not".
3. **Neither yet**: decline the gate and name what must change first. The
   gate keeps blocking items 203 and 204, and the change is new work.

The approval's `--evidence` should name each mode's outcome and its note. The
builder transcribes it and invents nothing.

#### Mode 3 — split vertebra segment

`bar_conditions(3)` measures **`(True, True, True, True, True)`**:

| # | Condition | Measured subject |
|---|-----------|------------------|
| 1 | Entry complete | all eight fields non-empty |
| 2 | A committed fixture expresses it (existential, detector-granular since item 200) | `split`, `split_own_label` |
| 3 | Every path the deciding detector reads is extracted and catalogued | `per_label.{label}.components.component_contacts[].contact_fraction` |
| 4 | A non-proxy detector serving this mode alone | `neighbour_contact/stray_contact` |
| 5 | Status derives `validated` | `validated`, rung `synthetic-demonstrable` |
| 6 | Maintainer sign-off | `2026-09-22`, `intermediate-state` (gate `gate-bb24`) |

**What changed since `gate-bb24`, against the reasons given on 2026-09-22:**

- *"`neighbour_contact` moves out of `fragmentation` into its own rule"*:
  **done** (item 187). `neighbour_contact` is a rule of its own with one
  detector, `stray_contact`, serving mode 3 alone. `fragmentation` no longer
  declares mode 3.
- *"The threshold has no evidence: the one firing value is the fixture's
  maximum cross-section"*: **the measure changed, and the corpus still has
  no touching bodies.** The detector now reads a relative
  `contact_fraction`, the contact area over the stray component's own
  surface, against `contact_fraction_threshold = 0.1`. It no longer reads an
  absolute area. On `split` it measures **0.3317** (806.0 mm² over 2430.0 mm²,
  label 24 against label 23), which is +0.2317 above the threshold. Every
  other stray component in the 13-case geometric corpus measures **0.0**
  (`inject_islands` label 22, `fragment` label 22). Whole-label contact
  (`label_contact_fraction`) is non-zero **only** on `split` (labels 23 and
  24) and `split_own_label` (labels 22 and 23). Every other case, including
  `clean_control`, reads zero, because the lordotic base keeps an 8 mm disc
  gap. No committed value lies near the threshold. Real facet-joint contact
  between adjacent vertebrae, the worry item 167 recorded, is still
  unmeasured. Stage 21 re-calibrates on real GT.
- *"The split case is re-authored at ~20 % on a lordotic base, with a second
  own-label sub-type"*: **done** (items 173 and 174). `split` gives the
  caudal 20 % cap of L4 (4030 of 19344 voxels) to L5. `split_own_label`
  keeps that cap under its own label and shifts the cranial labels up.

**Open judgements for mode 3:**

- **Sub-type (b) is expressed only through a proxy.** On `split_own_label`,
  mode 3's own detector does not fire, because the cap is its label's only
  component and has no stray component to measure. The case's whole measured
  firing is `bounds/metric_out_of_range`, twice on the cap: volume 4030 mm³
  below the lumbar minimum 8000, and extent_z 9 mm below 15. `bounds` is one
  of mode 3's intended edges at `needs-real-data`. Condition 2 counts every
  one of the mode's own `(rule_id, detector_id)` pairs, and only condition 4
  excludes the proxies. So `split_own_label` is a condition-2 subject through
  `bounds`. Condition 2 would still hold on `split` alone. The cap's
  `label_contact_fraction` (0.3317) is extracted, but no rule reads it.
- **The blind spot item 167 recorded still stands.** A split whose donated
  part is larger than the receiving label's own body reads nothing. The
  detector never checks index 0, the largest component, so the donated part
  would be read as the body. No committed case expresses this.
- **Stale and unbuilt candidates.** `candidate_features` still lists
  `stray_contact_area_mm2`, item 167's absolute area, which is extracted but
  read by no rule since item 187. It also lists the two unbuilt paths
  `spline_leave_one_out_shape_change` and
  `metric_change_under_merge_candidate`, all `hypothesised`.
- **Severity ladders (item 201).** `split` has a margin of 2.566, with one
  recorded coupling: `min_dominant_component_fraction` responds at 0.3896,
  because the receiving label becomes two bodies. `split_own_label` has an
  infinite margin. Both ladders designate mode 8's
  `mislabelled_volume_fraction`, because mode 3 has no metric of its own.

#### Mode 4 — islands (disconnected components)

`bar_conditions(4)` measures **`(True, True, True, True, True)`**:

| # | Condition | Measured subject |
|---|-----------|------------------|
| 1 | Entry complete | all eight fields non-empty |
| 2 | A committed fixture expresses it | `inject_islands` |
| 3 | Every path the deciding detector reads is extracted and catalogued | five `components` paths (`component_count`, `component_sizes[]`, `fragmentation_index`, `largest_component_fraction`, `stray_component_sizes[]`) |
| 4 | A non-proxy detector serving this mode alone | `fragmentation/islands` |
| 5 | Status derives `validated` | `validated`, rung `synthetic-demonstrable` |
| 6 | Maintainer sign-off | `2026-09-22`, `intermediate-state` (gate `gate-bb24`) |

**What changed since `gate-bb24`, against the reasons given on 2026-09-22:**

- *"The corpus base the fixture sits on is replaced by a lordotic one"*:
  **done** (item 173). `inject_islands` still agrees with its expected set
  `('fragmentation',)` on the lordotic base. Its measured detector firing is
  exactly `{('fragmentation', 'islands')}`. The one stray component is 27
  voxels against `island_min_voxels = 50`. The case's recorded `reason` is
  still the 2026-09-14 text, but it agrees live.
- *"The discriminator describes a grading by the island's distance from the
  main body that the code does not perform"*: **unchanged.** No Stage 33 item
  built it. `island_distance_from_main_body_mm` is still a `hypothesised`
  candidate, and the discriminator still says *"the further an island lies
  from the label's centroid, the larger it may be and still count as an
  island"*. **This is the 2026-09-22 reason for mode 4, and it still holds
  word for word.**
- The `islands` detector gained a reference branch: `component_count` above
  the level's reference upper percentile, when a reference covers it (see
  `docs/aide/rules.generated.md`). The committed corpus runs without a
  reference, so the voxel floor decides there. Item 201 re-measured the
  `inject_islands` severity ladder's margin at 118.4.

#### The checker the modes are signed against

Item 200 closed both divergences the item-168 brief named. Condition 2 is now
existential (at least one expressing case) and detector-granular (it
intersects the mode's own `(rule_id, detector_id)` pairs with
`measured_detector_firing`). One reading is left for the maintainer: that
**condition 2 admits a proxy pair**, which is mode 3's `split_own_label`
above. Condition 6 is still a record (`MODE_SIGN_OFFS`), not a computed
`BarCondition` (A2).

#### What is unchanged either way

No rule, threshold, fixture, feature, firing set or `config_hash` moves under
any of the three answers. Neither committed corpus is regenerated.
`derive_status`, `derive_mode_rung` and `bar_conditions` return exactly what
they return today. The only change is the two `MODE_SIGN_OFFS` records and
their rendering in both specification artifacts.

## Acceptance Criteria

AC1 holds from the moment this spec is committed. AC2 and AC3 hold only once
a person has approved the gate. That is deliberate: the item's deliverable
*is* the recorded decision, so it cannot be validated before the decision
exists. None of the three asserts which outcome was chosen.

- [ ] **AC1: the gate exists, is unique, and reaches items 203 and 204.**
      Parsed from `docs/aide/progress.md` through the CLI's `human_gates()`,
      exactly one `## Human gates` row's Gate cell contains
      `Stage 33 at-the-bar sign-off of modes 3 and 4`. That gate's parsed
      `blocks` equals `[203, 204]`, its `stage` is `None` and its
      `blocks_all` is `False`.
- [ ] **AC2: the gate is resolved as an approval.** AC1's gate's parsed
      `kind` equals `"approved"`, read live from `progress.md`.
- [ ] **AC3: each re-signed record carries the gate's own resolution
      date.** For each mode id in `(3, 4)`, `mode_sign_off(mode_id).date`
      equals the ISO date parsed from AC1's gate row's Status cell (the
      `(YYYY-MM-DD)` group), both read live.

The queue's other two testables are already held by existing tests, and this
item does not add a duplicate. See Decisions & Trade-offs.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Items
200, 201 and 202 had merged on `aide/queue-027` before this spec was written,
so every statement below was measured against their built code on
2026-09-29. **None is an interface pin** (§5), and there is nothing to
re-check at a later claim.

- **A1 (measured 2026-09-29):** re-signing **replaces** the mode's record in
  `MODE_SIGN_OFFS`. The mapping is keyed by mode id, one record per mode
  (item 168 A1), and the queue asks for "one `ModeSignOff` per mode". Keeping
  a history would change the mapping's value type, the `sign_off` JSON shape
  and the Markdown bullet, and nothing reads a history. The 2026-09-22
  records remain on record in `gate-bb24`'s row, in item 168's Decisions &
  Trade-offs, and in git.
- **A2 (measured 2026-09-29):** the queue's "meets all six conditions under
  `traceability.bar_conditions`" is read as **conditions 1–5 from
  `bar_conditions`, plus condition 6 from `MODE_SIGN_OFFS`**, not as a sixth
  `BarCondition`. `BAR_CONDITIONS` is five entries long, and its comment
  states that condition 6 is excluded by design. Adding one would move the
  tuple width that items 165, 167 and 200's tests measure, and no consumer in
  this queue needs a computed sixth condition: item 204 can read
  `MODE_SIGN_OFFS` directly. Item 168's Left open note on this question
  stands.
- **A3 (measured 2026-09-29):** the gate's reach is **`203, 204`**, not
  `stage 33`. Nothing already built is invalidated by any answer. The
  decision holds this item's records and item 204's attestation. Blocking 203
  while it is claimed is safe: `aide claim` consults gates only in
  `_pick_item`, and `aide merge` does not read the gate table
  (`.aide/scripts/aide.py`, engine 2.25.0).
- **A4 (measured 2026-09-29):** the new Gate cell must **not** contain
  `Stage 32 selected-mode sign-off`, `Stage 30 failure-mode specification
  sign-off` or `spinal curve model`. Three tests select an existing gate by
  those substrings and require exactly one match:
  `tests/test_168_maintainer_sign_off.py::_sign_off_gate`,
  `tests/test_150_maintainer_sign_off.py` (with
  `tests/test_151_stage30_validation.py`), and
  `tests/test_118_curve_formulation_decision.py::test_ac8_…`. The cell as
  raised contains none of the three, and no `|`.
- **A5 (measured 2026-09-29):** a mode's `note` is the maintainer's reason as
  given in the gate's evidence. It is transcribed, and it is split per mode
  only where the evidence names both modes in one text. An
  `intermediate-state` record's reason is what roadmap Stage 33 criterion 1
  calls "a recorded reason why it does not".
- **A6 (engine 2.25.0):** `aide scope` proves this item's diff against the
  Authorised paths below. A path listed under May change and left unchanged
  is not a violation, and that matters here: two of the three test-module
  reconciliations depend on the outcome.

## Implementation Steps

**Step 0 (every step below depends on it).** Run
`python .aide/scripts/aide.py gate list`. If the `Stage 33 at-the-bar sign-off
of modes 3 and 4` gate is not `✅`, stop and hand back without writing
anything. `⏳` means the decision is pending, and `❌` means re-plan.

1. **Replace the two records in `MODE_SIGN_OFFS`** in
   `src/segfacet/failure_modes.py`, keys `3` and `4`. Each is
   `ModeSignOff(mode_id=…, date=<the gate's Status-cell date>,
   outcome=<the maintainer's outcome for that mode>, note=<the maintainer's
   reason for that mode>)`. Reuse the existing dataclass, and add no field.
   The import-time `_validate_sign_offs()` call already guards keys.
2. **Rewrite the comment block above `MODE_SIGN_OFFS`** so it describes the
   records it now holds: the gate that recorded them (`gate-51da`), its date, and that they supersede `gate-bb24`'s
   2026-09-22 records. While there, correct `ModeSignOff`'s docstring phrase
   "shipped empty", which has been untrue since 2026-09-22. Leave the module
   docstring's `Sign-off` section alone: its single anchored
   `Signed off:` line and its entry count are pinned by `test_150` and
   `test_151`.
3. **Regenerate both artifacts** with `.venv/bin/python -m
   segfacet.failure_modes`, the module's own entry point. Never hand-edit
   either file. `SCHEMA_VERSION` does not move, because the shape is
   unchanged.
4. **Reconcile the tests that pinned the 2026-09-22 records** (the list is in
   Testing Strategy). Retire or rescope only the named functions, and edit
   nothing else in those modules.
5. **Append a dated entry to this spec's Decisions & Trade-offs** recording
   what the maintainer decided for each mode, and which conditional
   reconciliations were applied.

## Authorised paths

**May change:**

- `src/segfacet/failure_modes.py` — the two `MODE_SIGN_OFFS` records, their comment block and the `ModeSignOff` docstring phrase.
- `docs/aide/failure_modes.generated.json` — regenerated by step 3 (the two `sign_off` values).
- `docs/aide/failure_modes.generated.md` — regenerated by step 3 (the two `- Maintainer sign-off:` bullets).
- `tests/test_203_modes_3_and_4_re_signed.py` — this item's test module.
- `tests/test_168_maintainer_sign_off.py` — `test_ac12_…` retired (Testing Strategy).
- `tests/test_169_stage32_validation.py` — `test_ac8_…` rescoped and `test_ac9_…` retired, only if a mode is signed at the bar.

**Asserts against:**

None. This item's tests read `progress.md` (always authorised) and
`segfacet.failure_modes` (May change) and nothing else.

## Testing Strategy

**Module:** `tests/test_203_modes_3_and_4_re_signed.py`. Parse `progress.md`
by loading `.aide/scripts/aide.py` in process and calling `human_gates()` /
`_split_row`, following the idiom of `tests/test_168_maintainer_sign_off.py`
(`_aide_module`, `_progress_lines`, `_with_status_cell`). Never use a
hand-written table parser, and never write to `progress.md`.

**One test per AC** (AC1–AC3). Each recomputes its predicate from
`progress.md` and `segfacet.failure_modes` live. None compares against a
transcribed date or outcome.

**Adversarial cases, each with the failure mode it guards.** The test-writer
writes these and no others.

- `declined-gate-is-not-an-approval:` AC2's predicate, run over an in-memory
  copy of `progress.md` whose gate Status cell is replaced with
  `❌ Declined (<the live cell's date>)`, must fail. This guards the
  `kind != "awaiting"` reading (item 168's AC11 shape), which would count a
  decline, the maintainer's "neither yet", as a sign-off.
- `date-off-by-one-is-caught:` AC3's predicate, run over an in-memory Status
  cell whose date is the live gate date shifted one day with `datetime`
  (derived from the live value, never a literal), must fail for both modes.
  This guards a comparison that takes its expected date from the records
  instead of the gate.

**Existing tests to reconcile.** Grepped across `tests/` on 2026-09-29 for
`MODE_SIGN_OFFS`, `mode_sign_off`, `intermediate-state` and the gate-cell
substrings. Only `tests/test_168_…` and `tests/test_169_…` read the sign-off
records.

*What new values this change emits:* two new `date` strings, two `outcome`
strings (unchanged if the maintainer keeps `intermediate-state`) and two
`note` strings. They appear in `failure_modes.generated.json` and in the two
`- Maintainer sign-off:` bullets of `failure_modes.generated.md`. There is no
float leaf, numeric value, feature path, `config_hash` change or corpus
regeneration.

- **Always:**
  `tests/test_168_maintainer_sign_off.py::test_ac12_a_recorded_sign_off_carries_the_resolved_gates_own_date`
  asserts every record's date equals `gate-bb24`'s 2026-09-22. That becomes
  false by design once the records are re-signed, so **retire it**. This
  item's AC3 is its successor for the records that now exist. The rest of
  `test_168` stays green: AC9 (every `at-the-bar` record clears conditions
  1–5) holds, because modes 3 and 4 measure all-true. AC11 holds, because
  `gate-bb24` is approved and the mapping is non-empty. AC10 and
  `test_resolution_coherence_is_not_vacuous` hold, because they select
  `gate-bb24` by its own substring (A4).
- **Only if either mode is signed `at-the-bar`:**
  - `tests/test_169_stage32_validation.py::test_ac9_no_mode_recomputed_live_meets_all_six_bar_conditions`
    asserts the at-the-bar set is empty. That was item 169's measurement on
    2026-09-22, recorded as evidence on Stage 32 criterion 1 in
    `progress.md`. **Retire it.**
  - `tests/test_169_stage32_validation.py::test_ac8_refined_bar_drafts_clause_equals_live_partition`
    compares the Stage 20 evidence clause "at the fully-specified bar: none"
    against the live at-the-bar set. **Rescope it:** drop the at-the-bar
    comparison, and keep the refined-modes and drafts comparisons, which
    stay equal because `sorted(MODE_SIGN_OFFS)` is still `[3, 4]`. Evidence
    text in `progress.md` is not rewritten.
  - Checked, and needs no edit: `test_adv_bar_predicate_is_not_vacuous`
    picks the lowest mode clearing conditions 1–5. That is mode 1 (1, 3, 4
    and 16 qualify, measured 2026-09-29), which is unsigned. And
    `test_ac10_stage32_criterion1_box_unticked_with_dated_reason` names only
    non-bar modes, so it is vacuous for an at-the-bar mode.
- **Regenerate-and-compare, green once step 3 runs, no edit:**
  `tests/test_144_failure_mode_specification.py`,
  `tests/test_145_eight_hypothesised_modes.py`,
  `tests/test_146_ninth_mode_and_first_proposed.py`,
  `tests/test_147_specification_is_the_record.py`,
  `tests/test_149_conformance_report.py`,
  `tests/test_150_maintainer_sign_off.py`,
  `tests/test_157_case_id_rename.py`.
- **Gate table:** `tests/test_aide_check_no_errors.py`. The row raised here
  is four cells wide. `aide check` was run after raising it and reports no
  error.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

Needs no `[validation]` profile. The validator runs:

1. `python .aide/scripts/aide.py gate list`: the `Stage 33 at-the-bar
   sign-off of modes 3 and 4` gate reads `✅` and names `blocks items 203,
   204`.
2. `.venv/bin/python -m segfacet.failure_modes`, then `git status`: no change
   to either `docs/aide/failure_modes.generated.*` file, which shows the
   committed pair is the module's own output.
3. Read modes 3's and 4's `- Maintainer sign-off:` bullets in
   `docs/aide/failure_modes.generated.md`. Each carries the gate's date and
   the outcome and reason the gate's evidence gives for that mode.
4. `python .aide/scripts/aide.py check`: no errors.

**Do not run `aide gate approve` or `aide gate decline`.**

## Dependencies

- **Item 200**: condition 2 made existential and detector-granular. The brief's
  condition-2 subjects are measured through it. Merged ✅.
- **Item 201**: severity-ladder constants re-measured with the split ladders.
  The brief quotes them. Merged ✅.
- **Item 202**: `docs/aide/rules.generated.md`, which the maintainer reads at
  the gate. Merged ✅.

This item's own gate names its reach without creating dependency edges —
`Blocks: 203, 204`.

**Downstream:** item 204 attests Stage 33's criterion 1 and Stage 32's
criterion 1 from this item's outcome. Ticking Stage 32's criterion-1 box will
redden `tests/test_169_stage32_validation.py::test_ac10_…`, which asserts that
box stays unticked. That reconciliation belongs to item 204.

## Decisions & Trade-offs

To be updated during implementation.

- **The queue's second and third testables are not new criteria.** "A mode
  at `outcome="at-the-bar"` meets all six conditions" is held for every
  record by `tests/test_168_maintainer_sign_off.py::test_ac9_…` (conditions
  1–5 live, and condition 6 is the record itself, A2). "A mode at any other
  outcome carries its recorded reason" is held by `ModeSignOff.__post_init__`
  (a non-empty `note`), which `test_168::test_ac2_…` pins. Restating either
  here would buy a duplicate test and nothing else.
- **Left open:** whether `condition 2` should exclude the proxy pairs
  (`bounds`, `reference_delta`) as condition 4 does. On this tree it decides
  nothing, because mode 3 meets condition 2 through `split` alone. It is one
  of the maintainer's open judgements above, and changing the checker is not
  a sign-off's work.
- **Left open:** whether `MODE_SIGN_OFFS` should keep a sign-off history per
  mode rather than the latest record (A1). Nothing reads a history today.

---

**Amendment (2026-09-30, gate `gate-51da` declined; everything above stands
as the record of the item as first specified).** The maintainer declined
the sign-off of modes 3 and 4 with "neither yet" and re-drew the mode 2/3
boundary. Mode 2 keeps the paired case: one label covering its own vertebra
plus part or all of a neighbour. Mode 3 becomes the own-label fragment case
only. The label left covering only the remainder of an encroached vertebra
gets no mode yet. The selected modes become **2 and 3**, and mode 4 keeps its
`gate-bb24` intermediate-state record. Roadmap Stage 33's criterion 1 was
reworded to match with `aide progress reword` (2026-09-30).

What changes for this item:

- **Scope.** It is now the at-the-bar sign-off of modes 2 and 3, recorded as
  one `ModeSignOff` each. Mode 4's `MODE_SIGN_OFFS` record is left as it
  stands.
- **Gate.** `gate-51da` no longer blocks anything. It is the record of the
  decline. The sign-off is now held by `gate-0133` (Blocks `203, 204`),
  raised on 2026-09-30.
- **Order.** The item runs after queue-027's items 205–208: the boundary
  re-draw, a fixture for one label over two full, separate vertebrae, mode 2's
  fused-label detector from size and centroid spacing, and mode 3's own
  detector from contact fraction and small size.
- **Decision brief, criteria and tests.** Items 205–208 change every value
  the brief quotes, so the brief is superseded. When the item is next claimed,
  the spec-author re-measures `bar_conditions(2)` and `bar_conditions(3)` and
  writes a new brief. They re-derive the Acceptance Criteria for modes 2 and 3
  and correct Assumptions A1–A2 where they name modes 3 and 4, as appended
  corrections. The test module written for the first scope is not carried
  forward: it pins modes 3 and 4.
- **A brief a reader can act on without asking.** Condition 1's row read
  "all eight fields non-empty" without naming the fields, and the maintainer
  had to ask which fields they were. The new brief names them: `definition`,
  `discriminator`, `scope`, `observability`, `severity`, `candidate_features`,
  `intended_rules`, `corpus_cases` (`traceability.bar_conditions`,
  `completeness_fields`). It also states for each of conditions 2–5 what the
  check actually computes.
