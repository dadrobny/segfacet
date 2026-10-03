<!-- aide-template: item 3 -->
# Item 208 — Mode 3's own detector, from contact fraction and small size

> **Created:** 2026-09-30 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (D5 re-plan)
> **Queue:** [`../queue/queue-027.md`](../queue/queue-027.md) · Item 208
> **Objectives:** G2, G8
> **Suggested branch:** `aide/208-mode-3-s-own-detector`

---

## Description

This item gives mode 3 (split vertebra segment) a detector of its own. It is
the last of the four re-plan items (205–208) that must land before the
at-the-bar sign-off of modes 2 and 3 under gate `gate-0133` (item 203;
`queue-027.md`, "Re-plan").

**Why the detector is needed.** Since item 205, mode 3 is the fragment case:
part of a vertebra carrying a label of its own, where that label covers no
other vertebra. Its one committed case is `split_own_label`: the caudal 20 %
cap of L4 keeps label 23, the rest of L4 reads 22, and L5 reads 24. Only
the `bounds` proxy fires on it (twice, on the cap). `bounds` is a generic
volume proxy that bar condition 4 does not count, so mode 3 meets bar
conditions 1, 2 and 5 but not 3 and 4 (measured, A7).

The cap's own signal is already extracted and read by no rule (item 187).
Its whole-label `label_contact_fraction` is 0.3317: a third of its surface
touches the rest of L4. It is also small: 4030 mm³ against about 19 000 mm³
for a whole level. Neither signal decides alone:

- **Contact.** The remainder of an encroached vertebra touches its
  neighbour too. `split`'s label 23 (L4 minus the cap it lost to label 24)
  reads 0.1859, and so does `split_own_label`'s label 22 (L4 minus the cap
  that became label 23).
- **Size.** A label cropped by the field of view is small and touches
  nothing. `crop_fov_si`'s label 24 reads 6758 mm³ with contact 0.0.

**The detector.** A new rule, `split_fragment`, in its own module
`src/segfacet/heuristics/split_fragment.py`, with one detector, also
`split_fragment`. It fires on a label that **both** touches a neighbouring
label over more than a tenth of its own surface **and** is less than half
the median volume of its neighbouring labels (A1–A5). It serves mode 3
alone. It follows the rule-engine architecture:

- the module self-registers through `@register_rule` and one import line in
  `heuristics/__init__.py`;
- its thresholds are read from `HeuristicConfig` under
  `rules.split_fragment`;
- `config.rule_enabled("split_fragment")` gates it inside the unchanged
  runner.

**What this item changes.**

- `heuristics/split_fragment.py` (new) and one import line in
  `heuristics/__init__.py`.
- `default_config.yaml`: a commented documentation block, with no active
  section (A5).
- `failure_modes.py`, `_MODE_3`: a `split_fragment` edge,
  `split_own_label`'s expected set and reason, and the mechanism. The
  module docstring gains an item-208 paragraph.
- `synth/component_shape.py`: `SplitOwnLabelPerturbation`'s `Expectation`
  designates `split_fragment` beside `bounds` (A8).
- The corpus manifest, the corpus sheet, and the generated specification,
  traceability, catalogue, rule-table and golden-evidence documents are
  regenerated.
- `progress.md`: two count clauses are amended with `aide progress amend`:
  Stage 30 criterion 3 and Stage 20 criterion 5 (A10).
- The existing tests listed under Testing Strategy are reconciled.

**Not in scope.**

- No feature, no fixture, and no threshold of another rule. No corpus case
  other than `split_own_label` fires differently, and no verdict moves (A6).
- The label left covering only the remainder of an encroached vertebra,
  which has no mode yet (Left open).
- The lumbarised-S1 sub-type of mode 3 (Left open).
- `MODE_SIGN_OFFS` (item 203).

## Acceptance Criteria

Terms used below:

- **"The corpus cases"** are every entry of
  `segfacet.synth.corpus.load_manifest()["cases"]` (the geometric corpus)
  and every entry of
  `segfacet.synth.intensity.load_intensity_manifest()["cases"]` (the
  intensity corpus).
- **"A case's findings"** are
  `segfacet.synth.regression.pipeline_findings(case)` for a geometric case
  and `segfacet.synth.regression.intensity_pipeline_findings(case)` for an
  intensity case, each under the bundled default config. These are the
  functions `failure_modes.measured_firing` dispatches to.

- [ ] **AC1: `split_fragment` fires on the cap and nowhere else.**
  The set of `(corpus, case_id, label)` triples, over the corpus cases and
  over every finding of a case whose `rule_id == "split_fragment"` and every
  label in that finding's `labels`, equals
  `{("geometric", "split_own_label", 23)}`.
- [ ] **AC2: the detector serves mode 3 alone.**
  `segfacet.failure_modes.modes_for_detector("split_fragment", "split_fragment") == (3,)`.
- [ ] **AC3: mode 3 meets bar conditions 1–5 live.**
  `tuple(c.met for c in segfacet.traceability.bar_conditions(3)) == (True, True, True, True, True)`.

Why each is written:

- AC1 is the queue's "fires on `split_own_label` and on nothing else in
  either corpus", as one equality over both corpora. The label is part of
  each triple, so a detector firing on the cap's donor (label 22) fails it.
  It also carries "neither signal decides alone": the three donor labels
  with contact above 0.1 (`split` 23 and 24, `split_own_label` 22) and the
  small, untouching `crop_fov_si` label 24 are all in the silent set.
- AC2 is the queue's "it serves mode 3 alone". `modes_for_detector` is
  computed from every mode's edges, so an edge on another mode, or no edge
  on mode 3, fails it.
- AC3 is the queue's "Mode 3 meets bar conditions 1–5 live". Item 203's
  decision brief reads it. No existing test asserts it for mode 3:
  `tests/test_166_split_operator.py`'s AC9 checks condition 1 only, and
  `tests/test_169_stage32_validation.py`'s AC9 checks only that no mode is
  at the bar with a sign-off. Condition 3 is the one this item could break
  quietly. It quantifies over the new detector's signal paths, so a signal
  path the catalogue does not mark `observed.corpus.covered` fails AC3.

Not written, because something already fails without them:

- "`split_own_label`'s expected set is updated to include it":
  `tests/test_163_specificity_ratchet.py` fails on any committed case whose
  measured firing differs from its expected set. So do
  `tests/test_145_eight_hypothesised_modes.py`'s AC13 and
  `tests/test_146_ninth_mode_and_first_proposed.py`'s AC21.
- The manifest's designation of `split_own_label`:
  `tests/test_040_synthetic_corpus.py`'s AC17 (the manifest equals the
  operator's `Expectation`) and `tests/test_041_regression_suite.py`'s
  AC4–AC6 cover it.
- The declaration mirrors the edge: `catalogue.rule_declaration_conflicts()`
  reports a declared mode with no edge, and
  `tests/test_136_rule_mode_declarations.py` asserts it returns `()`.
- The declared paths equal the consumed paths:
  `tests/test_148_per_path_mode_attribution.py`'s AC4.
- The rule is registered and enabled by default:
  `tests/test_148_per_path_mode_attribution.py`'s AC16 requires its
  `_AC16_CASES` to cover every registered rule id. AC1 above cannot pass
  through the pipeline unless the runner runs the rule.
- The rule-table row: `tests/test_202_rule_table.py` compares the committed
  `docs/aide/rules.generated.md` with a fresh render.

None of these closes a Stage 33 acceptance criterion. Criterion 1 is closed
by item 203's sign-off. Criteria 2 and 3 are attested by item 204's
clean-clone replay.

## Assumptions

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measured value below was taken on this branch at `1c73277` on 2026-09-30
with `.venv/bin/python`. The measurements came from scratch probes that:

- registered a prototype of the rule in memory (A1–A5 exactly);
- replaced `failure_modes.SPECIFICATION` with a mapping whose mode 3 carries
  the new edge and `split_own_label`'s new expected set;
- patched `segfacet.synth.corpus.load_manifest` to return the committed
  manifest with `split_own_label` re-designated as A8 says.

No fixture's voxels change, so the committed fixtures were read as they
are. The builder re-measures each value on the real change.

- **A1 (decided: what "small" is measured against).** The queue offered
  three references: the level's `bounds` minimum, a ratio to the
  neighbouring labels, and the reference distribution. This item uses a
  ratio to the neighbouring labels.
  - **The measure.** A label's `size_ratio` is its
    `per_label.{label}.geometry.physical_volume_mm3` divided by the
    `statistics.median` of the same field over its **window**. The window
    is the judged labels (A4) within two places of it on either side, in
    ascending integer label order, excluding itself: up to four labels,
    fewer at the ends.
  - **Why the median of a window, and not the larger adjacent label.** The
    larger adjacent label is item 207's choice for `fused_label`. Mode 2
    and 3 errors change the size of a fragment's own neighbours, and the
    window median resists one abnormal neighbour. Against the larger
    adjacent label, the remainder of an encroached vertebra reads small
    beside the enlarged label that took its cap. On
    `SplitPerturbation(target_label=23, neighbour_label=24)` it reads
    0.4982 at a 30 % donation and 0.4086 at 40 %. Both have contact above
    0.1, so it would fire on a label the maintainer left without a mode
    (gate-51da). The same case run on the window median reads 0.6619 and
    0.5774, and stays silent. Both are the `split` severity ladder's rungs
    3 and 4.
  - **Why not the `bounds` minimum.** It would re-read the proxy's own
    per-level table, and bar condition 4 does not count that proxy.
  - **Why not the reference.** `pipeline_findings` runs `run_qc` without a
    reference, so a reference-based size would never fire on the committed
    corpus. Also, item 193 made the reference rules no mode's own detector.
- **A2 (decided: the contact gate).** The rule reads
  `per_label.{label}.components.label_contact_fraction`: the label's contact
  with its most-contacted neighbour, over its own surface (item 187). It
  does not read the per-component `component_contacts[]`. The cap is its
  label's only component, so the two scopes agree on it. The whole-label
  scope is the queue's named signal, and it keeps the rule off
  `neighbour_contact`'s stray-component path.
- **A3 (decided: end labels and small maps).** An end label is judged on
  the up to two labels on its one side. A label with an empty window (a
  one-label map) is not judged.
- **A4 (decided: sacral and coccygeal labels are outside the rule).** A
  label whose `level_name` starts with `"S"` (`labels.SACRUM`) or equals
  `"Cocc"` is neither judged nor counted in any window. A sacrum label
  covers several fused segments, so it would inflate L4's and L5's
  windows. A coccyx is small beside the sacrum and commonly touches it.
- **A5 (decided: thresholds, comparison and config).**
  - **The firing condition.** Fire when
    `label_contact_fraction > contact_fraction_threshold` **and**
    `size_ratio < size_ratio_threshold`, both strictly (item 027's
    convention).
  - **The defaults.** `DEFAULT_CONTACT_FRACTION = 0.1` is the value
    `neighbour_contact` applies to the same relative measure at component
    scope. The lordotic base's separated bodies read 0.0. The rule keeps
    its own constant, so re-tuning one rule never moves the other.
    `DEFAULT_SIZE_RATIO = 0.5` means "less than half a neighbouring level".
    Both are calibrated on the synthetic corpora only; Stage 21
    re-calibrates on real data.
  - **The config reads.** Both are read through
    `config.rule_param("split_fragment", "contact_fraction_threshold", default=...)`
    and `"size_ratio_threshold"`. `"severity"` defaults to
    `"flagged-for-review"`.
  - **No active config section.** No active `rules.split_fragment` section
    is added to `default_config.yaml`. An active section would change the
    parsed `rules` dict, and so `config_hash` in every report.
    `neighbour_contact` and `fused_label` ship section-less for the same
    reason, and `rule_enabled` returns `True` for an absent section.
- **A6 (decided: rule identity).**
  - `rule_id = "split_fragment"`, with one
    `RuleDetector(detector_id="split_fragment")` whose message tag is
    `"Split fragment:"`.
  - One finding per firing label, whose `labels` is that label alone, in
    ascending label order.
  - `mode_declaration.modes == (3,)`, with `evidence` led by
    `"corpus-manifest"`.
  - `consumed_paths`:
    - `per_label`: bookkeeping, the container iterated;
    - `per_label.{label}.components.label_contact_fraction`: signal;
    - `per_label.{label}.geometry.physical_volume_mm3`: signal;
    - `per_label.{label}.level_name`: bookkeeping, names the level and
      excludes sacral and coccygeal labels.
  - The detector's `signal_paths` are the two signal paths. Its `params` are
    `(("contact_fraction_threshold", 0.1), ("size_ratio_threshold", 0.5))`.
  - No `condition_opt_ins`, so the runner's gate drops a finding on a
    `fov_truncation` or `displaced_vertebra` label.
  - Mode 3's new edge is `IntendedRule(rule_id="split_fragment",
    detector_ids=("split_fragment",), evidence_rung="synthetic-demonstrable")`.
- **A7 (measured: what fires).**
  - **The one firing.** With the prototype registered, over the corpus
    cases, `split_fragment` fires exactly once: on `split_own_label`, label
    23 (L4).
    - Contact 0.3317.
    - Volume 4030 mm³ against a window of 19437 (21), 15314 (22) and 19344
      (24). The median is 19344, so the size is 0.2083.
    - The case's findings become `bounds` × 2 and `split_fragment` × 1, all
      on label 23. The verdict stays `flagged-for-review`, and `verify_case`
      stays `True`.
  - **Silent labels with contact above 0.1.**
    - `split` label 23: contact 0.1859, size 0.7879.
    - `split` label 24: contact 0.1021, size 1.3452.
    - `split_own_label` label 22: contact 0.1859, size 0.7910.
  - **Every other label** in both corpora reads contact 0.0.
  - **No other verdict moves.**
  - **Operators.** Over all registered operators at seeds 0–5 and spacings
    (1, 1, 1) and (1, 1, 3), only `split_own_label` fires it. It fires on
    the cap at every seed, with contact 0.33–0.37 and size 0.20–0.24.
  - **Clean spines.** L1–L5, T5–T10, C3–C5, L1–L4, L1–L3, L1–L2 and L1, at
    spacings (1, 1, 1), (1, 1, 3) and (2, 2, 2): all silent.
  - **Severity ladders.** Over every rung of `SEVERITY_LADDERS` and
    `SUPPLEMENTARY_LADDERS`, it fires only on the `split_own_label`
    ladder's rungs 1–3.
  - **Cohort evaluation** over the geometric corpus, in the shape
    `tests/test_120_leave_one_out_offset.py` builds, is unchanged:
    sensitivity 1.0, false-positive rate 0.0, per-mode `n_cases` unchanged
    (mode 3 still 1).
- **A8 (decided: which `Expectation` moves).** `SplitOwnLabelPerturbation`
  designates `expected_rule_ids={"bounds", "split_fragment"}`. Its labels
  (`{target}`), verdict and `detail` are unchanged. `SplitPerturbation`'s
  `Expectation` is unchanged.
- **A9 (measured: what the derivations move).**
  - **Conflict checks.** `specification_conflicts()`,
    `catalogue.rule_declaration_conflicts()`,
    `catalogue.path_classification_conflicts()` and
    `traceability.operator_reason_conflicts()` all return `()`.
  - **Conformance.** 18 cases (14 geometric and 4 intensity), all agree.
    Every case's served modes (the union of `modes_for_detector` over its
    findings) are unchanged: `split_own_label` stays `{2, 3, 4}`, and no
    case's served modes contain 1 beside another mode except
    `fuse_separate`'s `{1, 2}`.
  - **`bar_conditions(3)`, before → after.**
    - Conditions 1, 2 and 5 are met both before and after. Condition 2's
      subjects stay `("split_own_label",)`, and condition 5 stays
      `validated`.
    - Condition 3: not met with subjects `()` → met with subjects
      `("per_label.{label}.components.label_contact_fraction", "per_label.{label}.geometry.physical_volume_mm3")`.
    - Condition 4: not met with `()` → met with
      `("split_fragment/split_fragment",)`.
  - **`bar_conditions(2)`** is unchanged: all five are met.
  - **Derived status** is unchanged for every mode: validated 6,
    implemented 3, specified 2, proposed 5. The validated split stays 6
    pipeline-detected and 0 reconstructed-only.
  - **Derived mode rung moves for mode 3**, from `needs-real-data` to
    `synthetic-demonstrable`. Counts over 16 modes: synthetic-demonstrable
    5 → 6, needs-real-data 3 → 2, structurally-unobservable 1, none 7.
  - **Per-edge rung counts:** 14 edges (synthetic-demonstrable 6,
    needs-real-data 7, structurally-unobservable 1) → 15 edges
    (synthetic-demonstrable 7, needs-real-data 7, structurally-unobservable
    1).
  - **Registry.** The registry goes from 13 rules to 14.
    `catalogue.scan_synth_rule_mode_map()` gains `"split_fragment": (3,)`.
  - **Catalogue.** The catalogue keeps 145 entries.
    - `per_label.{label}.components.label_contact_fraction`:
      `failure_modes` `()` → `(3,)`; `mode_evidence` `()` →
      `("rule_mode_map", "rule_declaration")`; consuming rules none →
      `("split_fragment",)`; status `unwired` → `keep`.
    - `per_label`, `per_label.{label}.geometry.physical_volume_mm3` and
      `per_label.{label}.level_name` gain `split_fragment` as a consuming
      rule. Their modes and evidence are unchanged.
    - Entries carrying mode 3 go 4 → 5, and mode 2's count stays 11.
    - The `()` evidence bucket goes 90 → 89, and the
      `("rule_mode_map", "rule_declaration")` bucket 11 → 12.
  - **Traceability.**
    - One new rule row and one new exercise row (`split_fragment`,
      exercised by `geometric/split_own_label`).
    - Mode 3's row gains the edge (attributed `corpus`), the rule, and
      `label_contact_fraction` as a read path. Its rung becomes
      `synthetic-demonstrable`, and `pipeline_detected` stays `True`.
    - "Read by >=1 rule" 53 → 54, "read by no rule" 92 → 91,
      `unwired` 35 → 34.
    - The analytic-edge witness in `tests/test_138_traceability_matrix.py`
      is unchanged, because the new edge is corpus-attributed.
  - **Golden evidence moves.**
    `docs/aide/golden_evidence.generated.json`'s `unwired_leaf_paths` goes
    31 → 30 for all 14 geometric cases, because `label_contact_fraction`
    becomes wired. `total_leaf_paths` stays 101. Unlike item 207's path,
    this one carries no `STATUS_OVERRIDES` entry, so its status is derived.
  - **Rule table.** `docs/aide/rules.generated.md` gains one row,
    `split_fragment`, with modes column `3`.
- **A10 (defensible default: two progress clauses are amended).**
  - **Stage 30 criterion 3.**
    `tests/test_151_stage30_validation.py::test_ac35_rung_counts_note_matches_live_derivation`
    compares the last `derived mode rung counts: ...; per-edge rung counts
    over N edges: ...` clause in Stage 30's section with a live recount.
    Today's last clause is item 207's (5, 3, 1, 7; 14 edges: 6, 7, 1).
  - **Stage 20 criterion 5.**
    `tests/test_169_stage32_validation.py::test_ac7_rung_count_clause_equals_live_derivation`
    compares the last `derived mode rung counts:` clause in Stage 20's
    section. Today's last clause is item 205's (5, 3, 1, 7).
  - **How.** The builder amends both with `aide progress amend`, as items
    167, 188, 192, 193, 194, 205 and 207 did.
  - **What does not move.** Stage 30 criterion 1's status and
    validated-split clauses. The Stage 20 status clause and the
    refined/bar/drafts clause: AC6 and AC8 of test_169 stay green, and
    mode 3's sign-off stays `intermediate-state`, so the at-the-bar set
    stays empty.
- **A11: no human gate, and no environment-gated capability.**

## Implementation Steps

1. **`src/segfacet/heuristics/split_fragment.py` (new)**, modelled on
   `heuristics/fused_label.py`:
   - **Module docstring:** the item; the fragment case and why neither
     signal decides alone; design decisions A1–A6 with their measured
     values (A7); and a scope fence. The fence says there is no new
     feature, no other rule changes, and the remainder label and the
     lumbarised-S1 sub-type are not this rule.
   - **Constants:** `DEFAULT_CONTACT_FRACTION: float = 0.1` and
     `DEFAULT_SIZE_RATIO: float = 0.5`, each with a docstring giving the
     rationale and the measured margins (A5, A7).
   - **`_severity_from_param`:** a module-level function whose message
     names the rule, as each rule module defines its own.
   - **The class:** `@register_rule class SplitFragmentRule(Rule)`, with the
     A6 declaration.
   - **`evaluate(record, config)`:**
     - read `severity` first, so a bad string raises `ValueError` before any
       work, then both thresholds via `config.rule_param`;
     - `per_label = record.get("per_label", {})`, and return `[]` if it is
       not a dict;
     - walk its keys ordered by `int`. Return `[]` if any entry is not a
       dict. Skip sacral and coccygeal labels (A4). Return `[]` if a
       remaining entry lacks a numeric `geometry.physical_volume_mm3`: the
       case is then not judged;
     - per judged label, read `components.label_contact_fraction`, and skip
       the label if the value is absent or not numeric;
     - build the A1 window. Skip the label if the window is empty or its
       median is not positive. Emit one finding when both gates pass (A5).
   - **The finding reason** names the label, its level, the contact
     fraction, the size ratio, the window median, and both thresholds.
   - **Record access.** Read the record exactly as the prototype did:
     `.get` or subscript on the keys the A6 paths name, and no others. The
     catalogue's access trace and AST scan then attribute to the rule
     exactly the declared paths, so
     `catalogue.path_classification_conflicts()` returns `()`.
   - **Never mutate the record.** Use `statistics.median` for the window.
2. **`src/segfacet/heuristics/__init__.py`.** Add one import line after
   `fused_label`'s:
   `from segfacet.heuristics import split_fragment  # noqa: F401 — registers SplitFragmentRule (item 208)`.
   The runner is not touched.
3. **`src/segfacet/default_config.yaml`.** Add a commented block after
   `fused_label`'s, in its shape: what the rule reads, why it is
   section-less, and the two defaults and the severity, as comments only.
4. **`src/segfacet/failure_modes.py`, `_MODE_3`.**
   - **`intended_rules`:** append the A6 edge after `bounds`.
   - **`corpus_cases`:** `split_own_label` gets
     `expected_firing=("bounds", "split_fragment")`. Rewrite its reason:
     - it is pipeline-detected, measured live via
       `segfacet.synth.regression.pipeline_findings`, with the date and
       item 208;
     - `split_fragment` fires once on the cap, with A7's contact, volume,
       window median and size;
     - `bounds` still fires twice on the cap, and `coverage` still does not
       fire (the item-186 facts stay);
     - `neighbour_contact` still does not fire.
   - **`mechanism`:** rewrite it around `split_fragment`: both signals, both
     thresholds, strictly, on `split_own_label`.
     - Keep the `bounds` proxy sentence and the sentence on
       `neighbour_contact`'s silence.
     - Drop "no rule reads it yet".
     - It may name `per_label.{label}.components.label_contact_fraction` and
       `per_label.{label}.geometry.physical_volume_mm3`: mode 3's own rules
       consume both, which `tests/test_138_traceability_matrix.py`'s AC31
       checks.
     - Keep a whole-word `split_own_label` or `split_fragment` (AC31's token
       check).
     - Do not use the `(measured: findings == [...])` idiom.
   - **`candidate_features`, `definition` and `discriminator`** are
     unchanged, and so is the authored `status`.
   - **The module docstring** gains an item-208 paragraph in its history.
     `MODE_SIGN_OFFS` is not touched.
5. **`src/segfacet/synth/component_shape.py`.** In
   `SplitOwnLabelPerturbation.apply`, set the `Expectation`'s
   `expected_rule_ids` to `frozenset({"bounds", "split_fragment"})` (A8).
   Nothing else changes, and no voxel logic changes.
6. **Regenerate.** Run each generator twice into temp paths and
   byte-compare. Then run it once with no flags to write the committed
   copies:
   - `.venv/bin/python -m segfacet.synth.corpus`. Only `manifest.json` may
     change, and only in `split_own_label`'s `expected_rule_ids`. If a
     fixture's bytes change, hand back;
   - `.venv/bin/python -m segfacet.synth.corpus_sheet` (its `Source` digest
     covers the manifest);
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`;
   - `.venv/bin/python -m segfacet.rule_table`;
   - `.venv/bin/python -m segfacet.golden_evidence`. Only the 14
     `unwired_leaf_paths` values may move (31 → 30, A9); if anything else
     moves, hand back.
7. **Record the bar.** Run `traceability.bar_conditions(3)` on the real
   change. Write the result, per condition with its subjects, into
   Decisions & Trade-offs with the date.
8. **Amend the count clauses** (A10) with
   `python .aide/scripts/aide.py progress amend`, re-measuring every number
   live first. Each `--evidence` starts `Item 208 (<date>): mode 3 gains
   split_fragment's synthetic-demonstrable edge, moving its derived rung
   from needs-real-data to synthetic-demonstrable and adding one edge.
   Re-measured live:` and continues:
   - `amend 30 --criterion 3`: `derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7; per-edge rung counts over 15 edges: synthetic-demonstrable 7, needs-real-data 7, structurally-unobservable 1.`
   - `amend 20 --criterion 5`: `derived status counts over 16 modes: validated 6, implemented 3, specified 2, proposed 5. derived mode rung counts: synthetic-demonstrable 6, needs-real-data 2, structurally-unobservable 1, none 7.`
9. **Reconcile** the tests listed under Testing Strategy, each edit with a
   dated item-208 comment.
10. Run `python .aide/scripts/aide.py scope 208` and
    `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. `statistics` is the standard library.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/split_fragment.py` — **new**: the rule (step 1).
- `src/segfacet/heuristics/__init__.py` — one import line (step 2).
- `src/segfacet/default_config.yaml` — one comment block (step 3).
- `src/segfacet/failure_modes.py` — mode 3's edge, case and mechanism; the docstring (step 4).
- `src/segfacet/synth/component_shape.py` — `SplitOwnLabelPerturbation`'s `Expectation` (step 5).
- `tests/corpus/manifest.json` — regenerated; `split_own_label`'s designation (step 6).
- `docs/aide/corpus_sheet.png` — regenerated; one panel title and the input digest (step 6).
- `docs/aide/failure_modes.generated.json` — regenerated (step 6).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 6).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 6).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated; one new row (step 6).
- `docs/aide/golden_evidence.generated.json` — regenerated; `unwired_leaf_paths` 31 → 30 (step 6, A9).
- `tests/test_208_split_fragment_rule.py` — **new**: this item's test module.
- `tests/test_103_feature_catalogue.py` — `_RULE_MODE_MAP` gains `split_fragment`.
- `tests/test_126_golden_retirement.py` — AC22's pinned `(31, 101)` becomes `(30, 101)`.
- `tests/test_136_rule_mode_declarations.py` — two rule counts and `stayed_empty`.
- `tests/test_137_mode_less_rule_disposition.py` — the rule count and two distribution buckets.
- `tests/test_148_per_path_mode_attribution.py` — two counts and one `_AC16_CASES` row.
- `tests/test_151_stage30_validation.py` — the edge count 14 → 15.
- `tests/test_174_split_sub_types.py` — AC8's measured firing of `split_own_label`.
- `tests/test_186_expected_level_sequence.py` — AC16's measured firing of `split_own_label`.
- `tests/test_187_neighbour_contact_rule.py` — the rule count.

**The reconciliation fence.** Every edit to an existing test is a moved
literal, with a dated item-208 comment. A moved literal is a count, a rule id
added to a map or a case table, a pinned pair, or an expected set. No test is
retired, skipped, `xfail`-marked or loosened, and no structural edit is
authorised. A red test in a file not listed here is a hand-back to
spec-author.

**Asserts against:**

- `tests/corpus/fixtures/**` — every fixture must regenerate byte-identical; `tests/test_040_synthetic_corpus.py`'s AC15/AC16 compare them, and AC1 reads them.
- `tests/corpus/intensity/manifest.json` — AC1 reads the intensity cases through it.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited; it drives `split_own_label`'s firing against its expected set.
- `tests/test_041_regression_suite.py` — must stay green unedited; it drives `split_own_label`'s verdict, designation and labels.
- `tests/test_138_traceability_matrix.py` — must stay green unedited; its AC31 is what step 4's mechanism satisfies, and its AC20 witness does not move.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — must stay green unedited; its enclosed-core map now fires the rule (Testing Strategy).

`tests/test_169_stage32_validation.py` is listed under neither heading. No
line of it is edited: step 8's Stage 20 amendment keeps its AC7 green. Item
203, which runs later, may edit it.

## Testing Strategy

The test module is `tests/test_208_split_fragment_rule.py`, with one test per
AC.

- AC1 iterates both manifests through `pipeline_findings` and
  `intensity_pipeline_findings` (never a hand-built record) and compares the
  triple set with the literal. It never filters to `split_own_label` first.
- AC2 calls `modes_for_detector` live.
- AC3 calls `traceability.bar_conditions(3)` live.

Adversarial cases, each with the failure mode it guards, and no others:

- **`remainder-beside-enlarged-receiver-silent`.**
  - Setup: on `segfacet.synth.build_clean_spine().seg_img`, apply
    `SplitPerturbation(target_label=23, neighbour_label=24,
    donated_fraction=0.4)` with `seed=0`, then `run_qc` under the bundled
    config.
  - Expected: no `split_fragment` finding.
  - Non-vacuity: the same map's `extract_feature_record` gives label 23 a
    `label_contact_fraction` above 0.1, so the silence comes from the size
    gate.
  - Guards A1. Measured against the larger adjacent label, the remainder
    reads 0.4086 and fires. That would attribute to mode 3 the label the
    maintainer left without a mode.
- **`coccygeal-label-not-judged`.**
  - Setup: take `split_own_label`'s record from `extract_feature_record`,
    deep-copied, with label 23's `level_name` set to `"Cocc"`.
  - Expected: `SplitFragmentRule().evaluate(record, config) == []`.
  - Control: the unmodified record gives exactly one finding, on label 23.
  - Guards A4. A coccyx is small beside the sacrum and commonly touches
    it.
- **`contact-threshold-read-from-own-section`.**
  - Setup: set `rules.split_fragment.params.contact_fraction_threshold` to
    1000.0, building the config as
    `tests/test_189_spline_offset_condition.py::test_threshold_read_from_own_section`
    does, then `run_qc` on `split_own_label`.
  - Expected: no `split_fragment` finding.
  - Guards the contact gate being hard-coded or read from another key.
- **`size-threshold-read-from-own-section`.**
  - Setup: the same, with `size_ratio_threshold` set to 0.0.
  - Expected: no finding, because nothing is strictly below 0.
  - Guards the size gate the same way.

**Existing tests to reconcile.** Found on 2026-09-30 in three ways. First,
by applying the change in memory (Assumptions, preamble) and replaying every
derivation, the generators and the cohort evaluation. Second, by grepping
`tests/` for every literal the derivations move: rule counts, edge counts,
catalogue buckets, the rule → mode map, the golden-evidence pair,
`split_own_label`'s measured firing, and each place item 207's
`fused_label` was pinned. Third, by a read-only sweep of the roughly 90 test
modules that drive the rule registry, looking for hand-built label maps
with touching labels.

Moved literals, each with a dated item-208 comment:

- `tests/test_136_rule_mode_declarations.py`:
  - L198 (`test_ac1_iter_rule_declarations_ascending_by_rule_id`):
    `len(pairs) == 13` → `14`;
  - L261 (`test_ac3_ten_rules_registered`): `len(list(iter_rules())) == 13`
    → `14`;
  - L862 (`test_adv_expected_artifact_movement_counts_from_spec`):
    `stayed_empty == 90` → `89`, with a `Reconciled again (item 208,
    2026-09-30)` paragraph in that test's docstring saying that
    `label_contact_fraction` leaves the `()` bucket because `split_fragment`
    consumes it.
- `tests/test_137_mode_less_rule_disposition.py`:
  - L243: `len(rules) == 13` → `14`;
  - in the distribution table: L974 `(): 90` → `89`, and L983
    `("rule_mode_map", "rule_declaration"): 11` → `12`;
  - append a `Re-measured (item 208, 2026-09-30)` docstring paragraph in the
    shape of item 207's;
  - `len(entries)` stays 145, `mode1_count` 5, `mode2_count` 11 and
    `mode16_count` 2.
- `tests/test_148_per_path_mode_attribution.py`:
  - L366: `checked == 13` → `14` (AC4, one per declaring rule);
  - L1105: `checked == 13` → `14` (AC18, one per matrix rule row);
  - `_AC16_CASES` gains `("split_own_label", "geo", ("split_fragment",))`
    after the `fuse_adjacent` row;
  - L1068 stays 12: it counts the modules of
    `_EXPECTED_THRESHOLD_CONSTANTS`, which this item does not extend.
- `tests/test_151_stage30_validation.py`: L486 `total_edges == 14` → `15`,
  with a `14 -> 15: item 208` line in the comment above it.
- `tests/test_187_neighbour_contact_rule.py`: L252
  `len(list(iter_rules())) == 13` → `14`.
- `tests/test_103_feature_catalogue.py`: `_RULE_MODE_MAP` (L597–620) gains
  `"split_fragment": (3,)`, with a comment naming `split_own_label`.
- `tests/test_126_golden_retirement.py`:
  - in `test_ac22_documented_2694_evidence_still_verifies_unchanged`,
    L1072's `(31, 101)` → `(30, 101)`, and the message's `31/101` →
    `30/101`;
  - append a dated `(31, 101) -> (30, 101): item 208` sentence to the
    docstring: `label_contact_fraction` becomes wired.
- `tests/test_174_split_sub_types.py::test_ac8_split_own_label_fires_bounds_and_coverage`:
  L235 `== {"bounds"}` → `== {"bounds", "split_fragment"}`. The name stays.
- `tests/test_186_expected_level_sequence.py::test_ac16_split_own_label_no_longer_fires_coverage`:
  L268 the same edit. The name stays; the test still pins that `coverage`
  does not fire.

Green once the spec edit and step 6's regeneration land, with no test edit.
Each compares live state with the specification or a committed artifact:

- **Expected sets against measured firing:**
  - `tests/test_145_eight_hypothesised_modes.py`'s
    `test_ac13_every_expected_firing_equals_a_fresh_measurement`;
  - `tests/test_146_ninth_mode_and_first_proposed.py`'s AC21;
  - `tests/test_147_specification_is_the_record.py`'s AC26;
  - `tests/test_151_stage30_validation.py`'s AC8 and AC9 (the count stays
    18);
  - `tests/test_149_conformance_report.py`'s AC16;
  - `tests/test_163_specificity_ratchet.py`.
- **The manifest's designation of `split_own_label`:**
  - `tests/test_040_synthetic_corpus.py`'s AC15–AC17;
  - `tests/test_041_regression_suite.py`'s AC4–AC6;
  - `tests/test_110_neighbourhood_wiring.py::test_ac11_corpus_verify_case_unchanged`;
  - `tests/test_120_leave_one_out_offset.py::test_ac22_every_corpus_case_verifies`;
  - `tests/test_174_split_sub_types.py`'s AC7.
- **failure_modes:** `test_144` AC19/AC20, `test_145` AC23, `test_146`
  (L132–137, L1331), `test_147` AC24, `test_151` AC4/AC14/AC18, `test_157`
  AC16.
- **Catalogue:** `test_103` AC19, `test_106` AC7, `test_119` (L820–840),
  `test_120` AC30, `test_123` AC47, `test_124` AC17/AC18, `test_129` AC20,
  `test_130` (L747–761), `test_136` AC13, `test_137` AC15, `test_148` AC14.
- **Traceability:** `test_138` AC4, `test_143` AC12/AC15, `test_148` AC18,
  `test_149` AC19/AC20, `test_157` AC17, `test_162` AC9/AC10, `test_164`
  AC9.
- **Rule table:** `test_202`.
- **Corpus sheet:** `test_178` AC7 (the `Source` digest).
- **Golden evidence:** `tests/test_105_golden_decision_table.py`'s AC7 (a
  live recount against the companion), and
  `tests/test_134_decision_table_evidence_companion.py`'s AC4 and AC15.

**`progress.md` count clauses.** Two clauses move (A10), and step 8's
amendments turn both green:

- `tests/test_151_stage30_validation.py::test_ac35_rung_counts_note_matches_live_derivation`
  reads Stage 30 criterion 3.
- `tests/test_169_stage32_validation.py::test_ac7_rung_count_clause_equals_live_derivation`
  reads Stage 20 criterion 5.

These do not move:

- Stage 30 criterion 1's status and validated-split clauses (`test_151`
  AC35's other two tests);
- Stage 20's status and refined/bar/drafts clauses (`test_169` AC6 and
  AC8).

Checked and unaffected (measured or read):

- **`tests/test_129_coincident_centroids_and_held_out_floor.py`.**
  `_coincident_label_map()` encloses label 22 (96 voxels) inside label 21,
  so label 22 reads contact 1.0 against a window of label 21 alone and
  fires `split_fragment`. Measured with and without the bundled production
  reference, the verdict stays `flagged-for-review`, because
  `flag_escalation_count` is 0. So the CLI's exit code stays 0 (`cli.py`
  returns 1 only on `Severity.FAIL`). Its AC12, AC14, AC15, AC17 and AC18
  assert the stage-3 degradation, the text's level names and the exit
  code, never the finding set. Its other coincident maps go through
  `extract_feature_record` only.
- **`tests/test_167_mode_3_detector.py::test_existing_detectors_unchanged`.**
  It applies `SplitPerturbation(23, 24, 0.4)`, which is silent under A1,
  and filters findings by `(rule_id, detector_id)`.
- **`tests/test_194_mode_1_catch_all.py`.** AC2's served modes are
  unchanged (A9). `test_adv_served_modes_see_a_shared_detector` still
  measures `split_own_label` served by `{1, 2, 3, 4}`, because
  `split_fragment` serves 3, which is already in the set.
- **Hand-built records run through the full registry.** These include
  `test_035_failure_modes`'s int-keyed records with `geometry: {}`,
  `test_062`'s non-dict `per_label` entry, `test_089`'s records with no
  volume, and the records of `test_026`–`test_033`, `test_047`, `test_064`,
  `test_186`, `test_198` and `test_heuristics_bounds_source`. None carries
  `components.label_contact_fraction` beside numeric volumes, so step 1's
  early returns and skips cover them. `split_fragment` sorts after
  `reference_delta`, so it cannot pre-empt `test_047`'s and `test_064`'s
  expected `ValueError`.
- **Maps with separated labels.** `tests/synthetic.py`'s canonical cases
  are non-touching, and so is every clean-spine map (A7).
  `tests/test_cli_run.py`'s two blocks meet at a corner only, with no
  shared face, so their contact is 0.
- **`tests/test_035_default_config.py`, `tests/test_065_config_intensity.py`
  and `tests/test_090_reference_derived_defaults.py` AC16.** No active
  config section is added (A5), so the seven-section set and `config_hash`
  hold.
- **`tests/test_191_condition_gate.py` AC10 and AC12.** The rule declares
  no condition opt-in, so every condition's `opting_in_rules` is unchanged.
- **`tests/test_138_traceability_matrix.py`.**
  - AC15: mode 3's rung becomes `synthetic-demonstrable` with
    `pipeline_detected` `True`.
  - AC20's witness and mixed set are unchanged.
  - `test_adv_singleton_declaring_rule_mode_renders_a_well_formed_row`
    still finds singleton modes (1, 11, 15, 16).
- **`tests/test_137_mode_less_rule_disposition.py::test_adv_per_label_container_keeps_corpus_modes_and_gains_declaration_last`.**
  `per_label` gains a bookkeeping consumer only; its modes and evidence
  are unchanged.
- **Cohort metrics.** `tests/test_057_acceptance_stage7.py`,
  `tests/test_120_leave_one_out_offset.py` AC24 and
  `tests/test_101_per_mode_cohort.py` are unchanged (A7).
- **Ladder tests.** `tests/test_100_severity_ladder.py`,
  `tests/test_154_ladder_remeasurement.py` and
  `tests/test_201_severity_ladder_remeasured.py` measure per-mode metrics,
  not findings.
- **Live-computed bar tests.**
  - `tests/test_200_bar_condition_2.py` computes its subjects live.
  - `tests/test_166_split_operator.py`'s AC9 checks condition 1 only, and
    its `test_mode_3_proxy_edges_unchanged` reads mode 2's edges.
  - `tests/test_168_maintainer_sign_off.py` skips signed modes when it
    looks for a non-qualifying one.
- **`tests/test_205_mode_2_3_boundary.py`.** Mode 3's only case is still
  `split_own_label`.

## Validation

1. Replay mode 3's case through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/split_own_label_seg.nii.gz --out <tmp> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives: the bundled
   VerSe reference is not calibrated for the synthetic corpus. In
   `<tmp>/segfacet_report.json` the `findings` hold two `bounds` findings
   and one `split_fragment` finding, all on label 23. The verdict is
   `flagged-for-review`, and the `split_fragment` reason reads as A7's
   values.
2. Replay `split_seg.nii.gz` the same way. There is no `split_fragment`
   finding: its label 23 has contact but normal size.
3. Read `docs/aide/rules.generated.md`. It has one `split_fragment` row,
   with its question, both paths, both defaults, and modes column `3`.
4. Read `docs/aide/failure_modes.generated.md`. Mode 3 lists the
   `split_fragment` edge at `synthetic-demonstrable`, and `split_own_label`
   with its new expected set.
5. Run `python .aide/scripts/aide.py status` and confirm that Stages 20 and
   30 show step 8's amendments.

No environment profile is needed.

## Dependencies

- Item 205: mode 3 re-drawn as the fragment case, with `split_own_label` as
  its only case and no edge but `bounds` (✅).
- Item 207: `fused_label`, the model for this rule, and the test literals
  (rule count 13, edge count 14, catalogue buckets) this item moves on
  from (✅).
- Item 187: `per_label.{label}.components.label_contact_fraction` (✅).
- Item 174: the `split_own_label` case and operator (✅).
- Item 200: the detector-granular bar condition 2 that A9 records (✅).
- Item 202: the rule table that step 6 regenerates (✅).

**Downstream:**

- Item 203 re-measures `bar_conditions(3)` for its decision brief under
  gate `gate-0133`, after items 205–208.

## Decisions & Trade-offs

Recorded at implementation, 2026-09-30.

- **Bar conditions, mode 3 (`traceability.bar_conditions(3)`, live):**
  - condition 1 met (specification completeness, all eight fields);
  - condition 2 met, subjects `("split_own_label",)`;
  - condition 3 met, subjects
    `("per_label.{label}.components.label_contact_fraction",
    "per_label.{label}.geometry.physical_volume_mm3")`;
  - condition 4 met, subjects `("split_fragment/split_fragment",)`;
  - condition 5 met, subjects `("validated",)`.
- **Malformed records return `[]`.** `evaluate` returns `[]` for a
  `per_label` that is not a dict, for any key `int()` rejects (caught as
  `TypeError`/`ValueError` around the sort), for a non-dict entry, and for a
  judged label without a numeric volume. A label without a numeric contact
  fraction is skipped. The severity check still raises first.
- **Regeneration.** Each generator ran twice into scratch paths with
  byte-identical output before the committed copies were written. The
  corpus regeneration changed only `tests/corpus/manifest.json`
  (`split_own_label`'s `expected_rule_ids`); no fixture changed.
  `golden_evidence.generated.json` moved only the 14 `unwired_leaf_paths`
  values, 31 to 30.
- **Re-measured counts** match A9: status validated 6, implemented 3,
  specified 2, proposed 5; mode rungs synthetic-demonstrable 6,
  needs-real-data 2, structurally-unobservable 1, none 7; 15 edges
  (synthetic-demonstrable 7, needs-real-data 7, structurally-unobservable
  1). Both `progress amend` calls (Stage 30 criterion 3, Stage 20 criterion
  5) carry them.
- **Reconciled tests** (moved literals only, each with a dated item-208
  comment): test_103 `_RULE_MODE_MAP`; test_126 AC22 `(30, 101)`; test_136
  L198, L261 (13 to 14) and L862 (90 to 89); test_137 L243 (13 to 14),
  `(): 89` and `("rule_mode_map", "rule_declaration"): 12`; test_148 L366
  and L1105 (13 to 14) and the `split_own_label` `_AC16_CASES` row; test_151
  edge count 15; test_174 AC8 and test_186 AC16 expected set
  `{"bounds", "split_fragment"}`; test_187 rule count 14.

- **Left open:** the label left covering only the remainder of an
  encroached vertebra. Gate-51da gave it no mode, and this rule is silent
  on it up to a 40 % donation (A1). Past about half the vertebra, the
  remainder is the smaller part. It is then geometrically the same as an
  own-label fragment, reading 0.4944 at a 50 % donation, and the rule
  fires on it. Only a mode for the remainder can settle which label a
  finding should name. The deferral is recorded in `insights.md`,
  queue-027, 2026-09-30.
- **Left open:** the lumbarised-S1 sub-type of mode 3. A lumbarised S1
  given its own label is vertebra-sized, not small, so this rule does not
  see it. Sacral labels are outside the rule by A4. Neither corpus holds
  such a map.
- **Left open:** adjacency by ascending integer label. The window uses the
  same order as every Stage 3 spacing feature. For TPTBox labels whose
  integers are not anatomical (T13 = 28, L6 = 25; item 198), the window
  holds the wrong neighbours. Neither corpus holds such a map with a
  fragment.
- **Left open:** real-data calibration of both thresholds, and whether
  C1 and C2 read as a small, touching pair on real scans. The synthetic
  bodies never touch, and no real cohort is mounted on this machine. That
  is Stage 21's re-calibration.
