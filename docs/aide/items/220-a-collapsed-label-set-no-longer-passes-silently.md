<!-- aide-template: item 3 -->
# Item 220 — A collapsed label set no longer passes silently

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 220
> **Objectives:** G2, G3
> **Suggested branch:** `aide/220-collapsed-labels-rule`

---

## Description

Two labels whose centroids coincide exactly make Stage 3 absent. The record
then carries `stage3_unavailable` (item 129) instead of `case.curve`, every
rule that reads Stage 3 returns early, and `detect_overlaps` sees no
overlapping voxels. No finding names the collapse (insight `2026-10-09-c1b7`,
roadmap Stage 30 D3, failure mode 13 "Collapsed labels").

This item adds one rule, **`collapsed_labels`**
(`src/segfacet/heuristics/collapsed_labels.py`), declared against mode 13.
It has two detectors, and it emits one finding per collapsed pair:

- **`coincident_centroids`** reads `stage3_unavailable`. When the key is
  present it fires one finding on the pair the key names, and the reason
  quotes the key's `reason` and `detail`.
- **`near_coincident_centroids`** reads every label's
  `per_label.{label}.centroid.centroid_mm[]`. It fires on each pair of labels
  whose centroids lie within `max_centroid_distance_mm` of each other (default
  **2.0 mm**, a config parameter), except the pair `coincident_centroids` has
  already reported. This covers the near-collapsed case, where Stage 3 is
  computed but the two labels sit on essentially one point.

The severity is `flagged-for-review`, which is mode 13's authored severity.

Mode 13 in `src/segfacet/failure_modes.py` changes as follows:

- It is re-authored from `proposed` to `specified`, and gains one
  `needs-real-data` edge to `collapsed_labels` with no corpus case, as modes
  10 and 11 have. It then derives `implemented`.
- Its `mechanism` is rewritten around the rule.
- Its `definition` keeps every word and gains a dated closing note.

`stage3_unavailable` gets its `FEATURE_DOCS` entries, one per leaf path. The
catalogue gains a driver record that carries the key, so the regenerated
catalogue lists it.

**Not in scope:**

- **No corpus case.** The edge stays at `needs-real-data`, and no operator,
  manifest or fixture changes.
- **No other rule changes.**
- **No new feature extractor.** Both detectors read fields the record already
  carries.
- **No threshold on a fraction of the adjacent spacing.** That is the broader
  mode-13 reading of mode 13's definition, and it is left open (Decisions).
- **No `displaced_vertebra` opt-in.**
- **`mislabel.max_offset_mm` and `gate-fac1` are untouched.**

## Acceptance Criteria

Fixtures named here:

- **The coincident map** is `_coincident_label_map()` from
  `tests/test_129_coincident_centroids_and_held_out_floor.py`: labels 21 (L2)
  and 22 (L3) as concentric boxes, both centroids at (9.5, 9.5, 19.5) mm.
  Item 220's test module either imports it or builds the same map with
  `tests/synthetic.make_labelmap`.
- **The near map** is a label map the test module builds with
  `make_labelmap`. Two of its labels' centroids, recomputed from the
  extracted record, lie strictly between 0 and 2.0 mm apart, and the record
  carries no `stage3_unavailable` key. The test asserts both facts as
  preconditions.

The ACs:

- [ ] **AC1: Exact coincidence fires once, on the named pair.**
  `get_rule("collapsed_labels").evaluate(record, bundled_default_config())`
  on `extract_feature_record` of the coincident map returns findings whose
  `{(detector_id, labels)}` set equals
  `{("coincident_centroids", frozenset(record["stage3_unavailable"]["labels"]))}`.
  There is exactly one finding.
- [ ] **AC2: The coincident finding names the reason.** The AC1 finding's
  `reason` contains `record["stage3_unavailable"]["reason"]` and
  `record["stage3_unavailable"]["detail"]`, each read from the record.
- [ ] **AC3: The collapsed case is not a pass.** Use a config that disables
  every registered rule except `collapsed_labels`. `run_qc` on the coincident
  map returns a verdict whose overall severity is `flagged-for-review`. The
  test first asserts, as its precondition, that the same run with
  `collapsed_labels` also disabled returns `pass`.
- [ ] **AC4: A near-coincident pair fires.** On the near map's record, the
  rule returns exactly one finding, with `detector_id ==
  "near_coincident_centroids"` and `labels` equal to the pair the test
  recomputes from the record's `centroid_mm` values as the pair closer than
  2.0 mm.
- [ ] **AC5: The tolerance is the config parameter.** On the near map's
  record, take `d`, the pair's centroid distance recomputed from the record.
  The rule returns no finding when `rules.collapsed_labels.params.max_centroid_distance_mm`
  is set to `d / 2`. It returns the AC4 finding when the parameter is set to
  `d`.
- [ ] **AC6: A record with Stage 3 present and no close pair fires
  nothing.** On `extract_feature_record` of the committed
  `clean_control` corpus fixture, the rule returns `[]`.
- [ ] **AC7: No committed corpus case fires the rule.** Drive every case of
  `tests/corpus/manifest.json` and `tests/corpus/intensity/manifest.json`
  through its own detection path, using the harness
  `tests/test_163_specificity_ratchet.py` uses. No case's findings carry
  `rule_id == "collapsed_labels"`.
- [ ] **AC8: The rule declares mode 13 and the specification carries the
  matching edge.** The registered rule's `mode_declaration.modes == (13,)`.
  `SPECIFICATION[13].intended_rules` is exactly one `IntendedRule`, whose
  `rule_id == "collapsed_labels"`, whose `evidence_rung ==
  "needs-real-data"`, and whose `detector_ids` equal the rule's declared
  detector ids in order. The test reads those ids from
  `mode_declaration.detectors`.
- [ ] **AC9: Mode 13 derives `implemented`.**
  `derive_status(SPECIFICATION[13]) == "implemented"`.
- [ ] **AC10: Mode 13's definition is appended to, not rewritten.**
  `SPECIFICATION[13].definition` starts with the definition as shipped
  before this item. The test holds that sentence as a literal copied from
  the base-branch source. The text after it names `collapsed_labels` and an
  ISO date.
- [ ] **AC11: The catalogue lists `stage3_unavailable`.** The set of
  `build_catalogue(strict=True)` entry paths that start with
  `stage3_unavailable.` equals the set of `stage3_unavailable.` leaf paths of
  `extract_feature_record(coincident map)`, as
  `segfacet.catalogue.iter_leaf_paths` computes them.
- [ ] **AC12: Every `stage3_unavailable` catalogue entry is documented.**
  Every AC11 entry has `documented is True`, and a non-empty `measures` and
  `computation`.

## Assumptions

- **A1: The interactive clarify answers (2026-10-12), owner's decisions.**
  - Declare the rule against mode 13. Re-author mode 13 `proposed` →
    `specified` with one `needs-real-data` edge and no corpus case, as modes
    10 and 11 are.
  - Append a dated closing note to the definition's "passes silently"
    sentence.
  - The severity is `flagged-for-review`.
  - Cover near-coincident centroids too, with a very small tolerance chosen
    by measurement, kept as a config parameter. It must move no corpus
    case's firing and fire on nothing in clean VerSe19 GT.
  - The rule id is `collapsed_labels`, a finding names both labels, and the
    rule opts in to `fov_truncation`.
- **A2: The "passes silently" premise has partly decayed, and AC3 is
  isolated for that reason.** Measured 2026-10-12 at `2a1491d`, with
  `run_qc` and the bundled config on the coincident map: the verdict is
  already `flagged-for-review`.
  - Seven `bounds` findings fire, because the boxes are tiny.
  - One `split_fragment` finding fires, on the 96-voxel core inside the
    shell. Item 208's spec records this.
  - No finding names the collapse.

  A full-pipeline "not a pass" check would therefore pass with no new rule at
  all. AC3 disables every other rule, and its `pass` precondition is what
  makes it discriminating.
- **A3: The tolerance is an absolute 2.0 mm, chosen by measurement.**
  Measured 2026-10-12 at `2a1491d`: the minimum pairwise centroid distance
  over every pair of labels, using `segfacet.features.centroids.compute_centroid`.
  - **Geometric corpus (14 cases):** the closest pair is `split_own_label`
    L3–L4 at **12.542 mm**. That pair is legitimate: L4's caudal 20 % cap
    carries label 23, which pulls L4's centroid towards L3. The next closest
    is `crop_fov_si` L4–L5 at 29.786 mm.
  - **Intensity corpus (one seg, `clean_spine_seg`):** the closest pair is
    L2–L3 at 32.695 mm.
  - **VerSe19 GT:** every `*_seg-vert_msk.nii.gz` across the training,
    validation and test splits was measured, 159 masks with two or more
    labels. The closest pair is **11.082 mm**
    (`sub-verse401_split-verse201` C3–C4). The next closest are 12.303 mm
    (`sub-verse230` C5–C6) and 12.443 mm (`sub-verse207` C4–C5). No mask has
    a pair at or below 2.0 mm.

  2.0 mm sits more than five times below the closest legitimate pair in any
  of the three sets.

  **Why absolute rather than a fraction of the local spacing:** the collapsed
  pair's own adjacent spacing is the one that shrinks. A relative test would
  therefore need a reference spacing taken from the case's other pairs, and
  a record with two or three labels has no robust one. An absolute distance
  is defined for any two labels. The fraction reading is the broader mode-13
  detector, and it is left open.
- **A4: Pairs are judged over all labels, not only anatomical neighbours.** A
  collapsed pair need not be adjacent in the anatomical order (for example L2
  and L4 both on one vertebra). With at most about 30 labels the O(n²) scan
  costs nothing.
  - Pairs are visited in ascending `(int label_a, int label_b)` order.
  - The near test is `distance <= max_centroid_distance_mm`.
  - Distance is `math.dist` over the two `centroid_mm` triples. That is the
    voxel × spacing physical frame, the same frame `pairs.adjacent.spacings_mm[]`
    is computed in.
- **A5: One finding per collapsed pair.** `coincident_centroids` reports the
  one pair `stage3_unavailable.labels` names, which is
  `find_coincident_centroid_pair`'s first pair. `near_coincident_centroids`
  skips exactly that pair and reports every other pair within the tolerance,
  including further exact pairs (distance 0) in a three-way coincidence.
- **A6: `coincident_centroids` fires whenever `stage3_unavailable` is a
  mapping.** It does not filter on `reason`. Today `pipeline.extract_feature_record`
  writes the key in one place, with `reason == "coincident_centroids"`. A
  future reason would still produce a finding quoting it, and would not pass
  silently. If such a reason is ever added, revisit whether it is mode 13
  (Decisions, left open).
- **A7: Opting in to `fov_truncation`, and not to `displaced_vertebra`.**
  - **`fov_truncation`:** the runner drops a finding when any of its labels
    is in a condition the producing rule has not opted in to (item 191). A
    collapsed pair touching the volume border would otherwise be silently
    dropped. A crop shifts a label's centroid within its own vertebra and
    cannot bring two labels on different vertebrae within 2 mm of each
    other.
  - **`displaced_vertebra`:** that condition is derived from `spline_offset`
    findings, and there are none when Stage 3 is absent. A near pair sits
    together on one point of the curve, so neither label reads as displaced.
    The opt-in is left out until a case shows otherwise (Decisions).
- **A8: Mode 13's edge rung is `needs-real-data`.** No committed corpus case
  expresses a collapsed label set. This is the precedent of modes 10 and 11,
  whose edges are `needs-real-data` with no corpus case. A corpus case and a
  `synthetic-demonstrable` rung were offered (option B) and not chosen.
- **A9: The derived counts move, and three progress clauses are amended
  live.** `tests/test_151_stage30_validation.py` AC35 and
  `tests/test_169_stage32_validation.py` AC6 read the last count clauses in
  `progress.md`'s Stage 30 and Stage 20 sections and compare them with the
  live derivation.
  - Measured 2026-10-12 at `2a1491d`, before this item:
    - status counts: validated 6, implemented 3, specified 2, proposed 5;
    - mode rung counts: synthetic-demonstrable 6, needs-real-data 2,
      structurally-unobservable 1, none 7;
    - per-edge rung counts over 15 edges: 7 / 7 / 1.
  - This item alone moves those to:
    - status counts: implemented 4, proposed 4;
    - mode rungs: needs-real-data 3, none 6;
    - edges: 16, with needs-real-data 8.
  - Siblings 218 and 219 move them too, so step 9 re-measures live and
    writes whatever the tree holds.
- **A10: Mode 13 has no maintainer per-mode sign-off.** `MODE_SIGN_OFFS`
  holds modes 2, 3 and 4 only. Re-authoring mode 13's status, edge and
  mechanism needs no gate, which is the precedent of items 188 and 192 for
  modes 10 and 11.
- **A11: VerSe19 cannot be measured in the suite.** The GT is not in the
  repository or in CI. The "fires on nothing in clean VerSe19 GT"
  requirement is therefore A3's recorded measurement plus the Validation
  section's replay, not an AC. The 2.0 mm default leaves a margin of more
  than five times.

## Implementation Steps

1. **`src/segfacet/heuristics/collapsed_labels.py` (new).** Use
   `split_fragment.py` as the template for structure, `_severity_from_param`,
   `_is_num`, absence tolerance and the docstring shape. Do not import it:
   each rule keeps its own copy.
   - **Module docstring:** item 220, mode 13, both detectors, A3's numbers
     with date and commit, A4–A7, and a scope fence.
   - **Constant:** `DEFAULT_MAX_CENTROID_DISTANCE_MM: float = 2.0`, with a
     docstring carrying A3's three measured minima.
   - **`CollapsedLabelsRule`:** `rule_id = "collapsed_labels"`, decorated
     with `@register_rule`.
   - **`mode_declaration`:** `modes=(13,)`, with free-form `evidence` naming
     item 220 and the analytic grounds: the coincident map from item 129, and
     A3's measurements.
   - **`consumed_paths`**, ascending by path:
     - `per_label`: bookkeeping, container;
     - `per_label.{label}.centroid.centroid_mm[]`: signal;
     - `per_label.{label}.level_name`: bookkeeping, names the levels in the
       near finding;
     - `stage3_unavailable.detail`: bookkeeping, message interpolation;
     - `stage3_unavailable.labels[]`: bookkeeping, identity of the reported
       pair;
     - `stage3_unavailable.reason`: signal.
   - **`detectors`**, ascending:
     - `coincident_centroids`: `signal_paths=("stage3_unavailable.reason",)`,
       no params;
     - `near_coincident_centroids`:
       `signal_paths=("per_label.{label}.centroid.centroid_mm[]",)`,
       `params=(("max_centroid_distance_mm", DEFAULT_MAX_CENTROID_DISTANCE_MM),)`.
     - Each carries `description`, `question` and `fires_when` in
       `split_fragment`'s style, because `segfacet.rule_table` renders them.
   - **`condition_opt_ins`:** one
     `ConditionOptIn(condition="fov_truncation", paths=(...), reason=...)`.
     Its paths are the two signal paths and `stage3_unavailable.labels[]`,
     and its reason is A7's first bullet.
   - **`evaluate(record, config)`:**
     - Read `severity` (default `"flagged-for-review"`; an unknown label
       raises `ValueError` before any work) and `max_centroid_distance_mm`
       through `config.rule_param`.
     - **Coincident detector:** if `record.get("stage3_unavailable")` is a
       dict, take its `labels` as a frozenset of ints. Emit one finding: a
       `"Collapsed labels:"` tag, then `detail`, then the quoted `reason`.
       Its labels are that frozenset and its `detector_id` is
       `coincident_centroids`.
     - **Near detector:** if `per_label` is a dict with int-like keys,
       collect each label's `centroid.centroid_mm` when it is a
       length-3 numeric list. Skip a label whose centroid is absent or
       malformed. For each pair in A4's order other than the reported pair,
       emit one finding when `math.dist <= tolerance`. The reason names both
       labels and levels, the distance (`.4g`) and the tolerance.
     - Never mutate the record.
   - **Record access:** read exactly the declared paths, by `.get` or
     subscript, so `segfacet.catalogue.path_classification_conflicts()`
     returns `()`.
2. **`src/segfacet/heuristics/__init__.py`:** one import line after
   `split_fragment`'s, in its shape. The runner is not touched.
3. **`src/segfacet/default_config.yaml`:** one commented block after
   `split_fragment`'s, in its shape: what the rule reads, why it is
   section-less (`config_hash`), and `max_centroid_distance_mm: 2.0` with
   A3's minima and `severity: flagged-for-review`. Comments only.
4. **`src/segfacet/failure_modes.py`, `_MODE_13`:**
   - `status="specified"`.
   - `intended_rules=(IntendedRule(rule_id="collapsed_labels",
     detector_ids=("coincident_centroids", "near_coincident_centroids"),
     evidence_rung="needs-real-data"),)`.
   - **`definition`:** append one sentence after the shipped text, which
     stays verbatim. It reads "Closed <ISO date> (item 220): the
     collapsed_labels rule reads stage3_unavailable and the centroids, so a
     collapsed pair now raises a flagged-for-review finding."
   - **`mechanism`:**
     - Rewrite it around `collapsed_labels`: both detectors, the 2.0 mm
       tolerance and why it is absolute (A3), and the fact that no corpus
       case expresses the mode, hence `needs-real-data`.
     - Keep a whole-word `collapsed_labels`.
     - It may name `stage3_unavailable.reason` and
       `per_label.{label}.centroid.centroid_mm[]`, which the rule consumes.
     - It must **not** name `pairs.adjacent.spacings_mm[]`. Mode 13's own
       rules do not consume it, and `tests/test_138_traceability_matrix.py`'s
       AC31 check (1) fails on that.
     - Do not use the `(measured: findings == [...])` idiom.
   - **Unchanged:** `candidate_features`, `discriminator`, `severity`,
     `observability`, `corpus_cases` and `MODE_SIGN_OFFS`.
   - **`CONDITIONS["fov_truncation"].opting_in_rules`:** `("border",)` →
     `("border", "collapsed_labels")`. `tests/test_191_condition_gate.py` AC10 requires this
     tuple to match the rules in the registry whose `condition_opt_ins` name
     `fov_truncation`, and step 1's opt-in adds `collapsed_labels` to that
     set. This is the only edit to `CONDITIONS`. The amendment was approved
     by the owner on 2026-10-13 after the cross-spec review, finding B7.
   - **Module docstring:** remove "; proposed" from mode 13's row in the
     taxonomy table, and add an item-220 paragraph to the history in
     item 208's shape.
5. **`src/segfacet/feature_docs.py`:**
   - **`FEATURE_DOCS`:** one entry per catalogued `stage3_unavailable` leaf:
     - `stage3_unavailable.reason`: categorical;
     - `stage3_unavailable.detail`: identifier;
     - `stage3_unavailable.levels[]`: identifier;
     - `stage3_unavailable.labels[]`: identifier;
     - `stage3_unavailable.coordinate_mm[]`: mm, scales with spacing.

     Write `measures` and `computation` from `pipeline.extract_feature_record`
     lines 178–196 and `features.spline.find_coincident_centroid_pair`.
   - **`BLOCK_OWNERS`:** one row, `("stage3_unavailable", "Stage 3
     Availability", "Stage 3 · item 129", "segfacet.pipeline")`.
   - **`GROUP_INTROS`:** its entry, one or two sentences.
   - If `strict` refuses a different leaf set, the leaf set
     `iter_leaf_paths` yields is the authority.
6. **`src/segfacet/catalogue.py`, `iter_driver_records`:** add one driver
   after `sequence_break`.
   - Build the AC fixture's concentric two-box map in-function, with
     NumPy, in a `nib.Nifti1Image` whose affine is the identity and whose
     spacing is 1 mm. Keep the function's rule that no tests path is named.
   - Run `extract_feature_record` on it.
   - Yield `("stage3_unavailable", {"stage3_unavailable":
     record["stage3_unavailable"]})`. That is a partial record, as the
     `image_features` and `reference_delta` drivers are, so no other path's
     observed range moves.
   - Extend the docstring's list of what the union realises.
7. **Regenerate.** Run each generator twice into temp paths and
   byte-compare, then once with no flags to write the committed copies:
   - `.venv/bin/python -m segfacet.failure_modes`;
   - `.venv/bin/python -m segfacet.traceability`;
   - `.venv/bin/python -m segfacet.catalogue`;
   - `.venv/bin/python -m segfacet.rule_table`;
   - `.venv/bin/python -m segfacet.golden_evidence`.

   The corpus generators are **not** run, and no fixture or manifest
   changes.
8. **Reconcile the existing tests** listed under Authorised paths (Testing
   Strategy, "Existing tests to reconcile"). Each edit is a moved literal or
   a re-pointed exemplar, and carries a dated item-220 comment.
9. **Amend the count clauses** (A9) with
   `python .aide/scripts/aide.py progress amend`, re-measuring every number
   live first, in the item-208 format:
   - `amend 30 --criterion 1`: derived status counts over 16 modes, plus the
     validated split;
   - `amend 30 --criterion 3`: derived mode rung counts, plus per-edge rung
     counts over N edges;
   - `amend 20 --criterion 5`: derived status counts and derived mode rung
     counts.

   Each `--evidence` starts `Item 220 (<date>): mode 13 gains
   collapsed_labels' needs-real-data edge and derives implemented.
   Re-measured live:`.

**Correction to step 4's `mechanism` (2026-10-13, review finding, minor).**
The shipped mechanism says `coincident_centroids` "fires once on the pair
stage3_unavailable.reason names". That is wrong:

- the pair is named by `stage3_unavailable.labels[]`;
- `reason` is only the literal `coincident_centroids`, which the finding's
  reason quotes.

The clause is reworded in `src/segfacet/failure_modes.py`, and the four
`failure_modes` / `traceability_matrix` generated files are regenerated.
Each of those paths is already authorised.

**The constraint is `tests/test_138_traceability_matrix.py` AC31 check
(1).** Every record path the mechanism names, matched as a verbatim
substring, must be one of `collapsed_labels`' consumed paths:

- `per_label`
- `per_label.{label}.centroid.centroid_mm[]`
- `per_label.{label}.level_name`
- `stage3_unavailable.detail`
- `stage3_unavailable.labels[]`
- `stage3_unavailable.reason`

Naming `stage3_unavailable.labels[]` is therefore allowed. The mechanism
must still not name:

- `pairs.adjacent.spacings_mm[]`;
- `stage3_unavailable.levels[]`;
- `stage3_unavailable.coordinate_mm[]`.

No rule consumes the last two.

**The allowed wording for the clause:**

> its coincident_centroids detector fires once, on the pair
> stage3_unavailable.labels[] names, and quotes stage3_unavailable.reason
> and stage3_unavailable.detail in its reason (the exact-coincidence case,
> where Stage 3 is absent)

The rest of the mechanism stands.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/collapsed_labels.py` — **new**: the rule (step 1).
- `src/segfacet/heuristics/__init__.py` — one import line (step 2).
- `src/segfacet/default_config.yaml` — one comment block (step 3).
- `src/segfacet/failure_modes.py` — mode 13's status, edge, definition note and mechanism; `fov_truncation`'s `opting_in_rules`; the docstring (step 4).
- `src/segfacet/feature_docs.py` — five `FEATURE_DOCS` entries, one `BLOCK_OWNERS` row, one `GROUP_INTROS` entry (step 5).
- `src/segfacet/catalogue.py` — one driver record in `iter_driver_records` (step 6).
- `docs/aide/failure_modes.generated.json` — regenerated (step 7).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 7).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 7).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/rules.generated.md` — regenerated; one new rule (step 7).
- `docs/aide/golden_evidence.generated.json` — regenerated (step 7); expected byte-identical, since no corpus record gains a path.
- `tests/test_220_collapsed_labels_rule.py` — **new**: this item's test module.
- `tests/test_136_rule_mode_declarations.py` — two rule counts 14 → 15; the catalogue entry count and `stayed_empty`.
- `tests/test_137_mode_less_rule_disposition.py` — the rule count 14 → 15 and any declaration-state bucket it pins.
- `tests/test_138_traceability_matrix.py` — `PROPOSED_MODES` pin `{5, 7, 12, 13, 14}` → `{5, 7, 12, 14}`.
- `tests/test_145_eight_hypothesised_modes.py` — `_PROPOSED_MODE_IDS` drops 13.
- `tests/test_146_ninth_mode_and_first_proposed.py` — AC27/AC28 re-stated for mode 13's new state; AC29, AC30, AC31 and the mode-13 adversarial re-pointed to mode 14 as the proposed exemplar.
- `tests/test_148_per_path_mode_attribution.py` — two rule counts 14 → 15; the unreachable set drops 13.
- `tests/test_151_stage30_validation.py` — the edge count 15 → 16.
- `tests/test_156_conformance_seams.py` — only if red: its stub's exemplar mode 13 → 14.
- `tests/test_187_neighbour_contact_rule.py` — the rule count 14 → 15.
- `tests/test_124_observed_range.py` — L566's catalogue entry count `len(paths) == 154` gains the five `stage3_unavailable.*` entries (cross-spec review B6, 2026-10-13).
- `tests/test_132_monotonicity_against_traversal_order.py` — L735's `leaf_count == 154` and `_PRE_ITEM_OBSERVED_SUMMARY` move for the same five entries (B6).
- `tests/test_189_spline_offset_condition.py` — AC12's `opting_in_rules` set `{"border"}` → `{"border", "collapsed_labels"}` (B7).
- `tests/test_126_golden_retirement.py` — only if step 7 moves it: AC22's pinned `(30, 95)` unwired/total pair, which is counted per corpus record, not over the catalogue union, so it is expected to stay.

**The reconciliation fence.** Every edit to an existing test is one of two
kinds. A moved literal is a count, a pinned id set, or a pinned pair. A
re-pointed exemplar is a test that used mode 13 as "a proposed mode" and now
uses mode 14, which stays `proposed`.

test_146 AC27 and AC28 assert facts about mode 13 itself, so they are
re-stated rather than re-pointed. They now assert the new state: `specified`,
the one `collapsed_labels` edge, a derived `implemented`, and a rung of
`needs-real-data`. The candidate-feature and definition assertions stay as
they are.

Each edit carries a dated item-220 comment. No test is retired, skipped,
`xfail`-marked or loosened. A red test in a file not listed here is a
hand-back to spec-author.

**Correction (2026-10-13, validation round 1).** The round-1 suite run went
red on 14 tests outside the list above. Every one is a pin this item
legitimately moves, and none is a behaviour regression in `src/`. Each
failure traces to one of three facts the item creates:

1. The catalogue gains the five `stage3_unavailable.*` leaves (154 → 159).
2. Mode 13 leaves the proposed and edgeless sets. It gains one
   `needs-real-data` edge and derives `implemented`.
3. `per_label.{label}.centroid.centroid_mm[]` gains `collapsed_labels` as a
   second signal consumer.

The original list above stands. The bullets below widen it. Each edit falls
under the same fence: a moved literal, a re-pointed exemplar, or a row added
in an existing table's own shape. Each carries a dated item-220 comment, and
none retires, skips, `xfail`s or loosens a test. Further pins in test_137,
test_138 and test_148, which are already listed, are named in Testing
Strategy's round-1 correction. So are the test_103 reconciliation and why it
keeps equality exact.

- `tests/corpus/119_pre_119_digests.json` — `catalogue_leaf_path_set_sha256` moves to the live leaf-path digest (round 1 measured `82f9a70d90cc64e86c40976c0ed61b26fce3a13157da3d47c393872f88164f21`); the one fixture behind test_119 AC27, test_120 AC12 and test_123 AC49, which are not edited; items 167, 187, 215 and 216 bumped it the same way; a JSON test pin, not a corpus fixture.
- `tests/test_131_tangent_direction_normalisation.py` — `_PRE_ITEM_TOTAL_LEAF_PATH_COUNT` 154 → 159 (AC16).
- `tests/test_216_neighbour_pair_and_case_level_migration.py` — AC1's `stored` set gains the five `stage3_unavailable.*` paths, which items 215 and 216 never migrated and the mapping table has no row for; the precedent is `case.sequence.order[]`, added in the same place. `docs/feature-taxonomy.md` is not edited.
- `tests/test_103_feature_catalogue.py` — AC13's effect test, `sequence` parametrisation (Testing Strategy, round-1 correction).
- `tests/test_147_specification_is_the_record.py` — AC26's `_EXPECTED_DERIVED_STATUS[13]` `"proposed"` → `"implemented"`; AC8's edgeless-mode set drops 13, to `{5, 6, 7, 8, 12, 14}`.
- `tests/test_149_conformance_report.py` — `_DEGENERATE_MODES` drops 13, as it dropped 10 (item 188) and 11 (item 192); this removes the `[13]` case of both AC7 tests.

**Asserts against:**

- `tests/corpus/manifest.json` — AC7 drives every geometric case through it; no case's firing may move.
- `tests/corpus/intensity/manifest.json` — AC7 drives the intensity cases through it.
- `tests/corpus/fixtures/**` — AC6 and AC7 read them; nothing regenerates them.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — must stay green unedited: its AC29 pins every corpus case's finding set, and the new test module reads its coincident map.
- `tests/test_163_specificity_ratchet.py` — must stay green unedited: no case fires a rule it does not expect.
- `tests/test_104_feature_catalogue_drift.py` — must stay green unedited: the committed catalogue equals a fresh build.
- `tests/test_202_rule_table.py` — must stay green unedited: `rules.generated.md` equals a fresh render.
- `tests/test_169_stage32_validation.py` — must stay green unedited: its AC6 reads the Stage 20 clause step 9 amends.

## Testing Strategy

The test module is `tests/test_220_collapsed_labels_rule.py`. It has one test
per AC (AC1–AC12) and the named adversarial cases below, and no others.
Every fixture fact a test relies on is recomputed from the extracted record
and asserted as a precondition, so a change to `compute_centroid` fails
loudly instead of passing vacuously.

**Adversarial cases:**

- `border-touching-pair-survives-the-runner`: a collapsed pair at the volume
  border would be dropped by the runner's `fov_truncation` gate, which is
  silent again. Use the coincident map shifted so that label 21 touches a
  volume face. Precondition: `segfacet.heuristics.fov.border_touching_labels(record)`
  contains 21. Through `run_rules(record, bundled_default_config())`, the
  surviving findings include the `collapsed_labels` finding on {21, 22}.
  The runner reads the rule's own `condition_opt_ins`, so the test needs
  nothing beyond that. The `CONDITIONS` mirror that step 4 updates is
  checked by `tests/test_191_condition_gate.py` AC10, not by this test.
- `triple-coincidence-one-finding-per-pair`: guards a pair reported twice,
  or the second and third exact pairs going unreported. Use
  `_triple_coincident_label_map()` (test_129). The rule returns exactly three
  findings: one `coincident_centroids` finding on the pair
  `stage3_unavailable.labels` names, and two `near_coincident_centroids`
  findings on the other two pairs. Their label sets are pairwise distinct.
- `non-adjacent-pair-is-judged`: guards a scan restricted to anatomical
  neighbours (A4). Use a near map where the close pair is two levels apart
  in the anatomical order, for example L2 and L4 with L3 elsewhere. The
  rule fires on that pair.
- `malformed-centroid-skipped-not-raised`: guards the rule crashing
  `run_rules` on a partial record. Take a record copy in which one label's
  `centroid` is missing. `evaluate` returns without raising, and still
  judges the remaining labels.
- `unknown-severity-raises`: guards a typo in config silently defaulting.
  Setting `severity` to an unknown label raises `ValueError`.

**Existing tests to reconcile** are the files under May change above, from
`tests/test_126` to `tests/test_187`. A sweep on 2026-10-12 found these
pins:

- the rule count of 14 in test_136, test_137, test_148 and test_187;
- the edge count of 15 in test_151;
- mode 13 as the proposed exemplar or in a proposed set, in test_138:1336,
  test_145:98, test_146 (AC27–AC31 and `test_adv_mode13_*`) and
  test_148:693;
- the catalogue entry count and `stayed_empty` in test_136;
- the catalogue entry and leaf counts of 154 in test_124:566 and
  test_132:735, and test_132's `_PRE_ITEM_OBSERVED_SUMMARY`;
- the `fov_truncation` `opting_in_rules` set in test_189 AC12;
- the golden-evidence pair in test_126, which is expected to stay.

The sweep is a lower bound: it lists each pin once, at its first sight, so
the fence above governs the rest.

**Correction (2026-10-13, validation round 1): further pins to reconcile.**
Authorised paths names the files. The edits that need more than a line:

- **test_103, `test_ac13_rule_mode_map_effect_on_failure_modes[sequence]`.**
  - **Why it fails:** the test matches each rule against the signal
    entries that rule consumes *alone*. `sequence`'s only such entry was
    `centroid_mm[]`, and `collapsed_labels` now consumes it as signal too.
    The match set is therefore empty, and the precondition fails.
  - **The change:** widen the match set to the signal entries whose
    `consuming_rules` contain the rule and are a subset of
    `{rule_id, "collapsed_labels"}`. Where `collapsed_labels` consumes such
    an entry as signal, add its declared modes to the exact `expected` set.
  - **Equality stays exact.** For `sequence` the expected set is
    `{9, 10, 11, 13}`, which is the entry's live `failure_modes`.
  - **Measured on the committed catalogue, 2026-10-13:** the widening adds
    `centroid_mm[]` to `sequence`'s match set and changes no other
    parametrisation's set.
- **test_137, `test_adv_measured_artifact_movement_counts_from_spec`.**
  - `len(entries)` moves 154 → 159.
  - Every `mode_evidence` bucket that the five new entries and
    `centroid_mm[]`'s new consumer move is updated. The new counts are read
    live off the regenerated catalogue and recorded in the docstring's
    "Re-measured (item NNN)" style.
  - `mode1_count`, `mode2_count` and `mode16_count` are expected to stay.
- **test_138.**
  - AC10's literal `proposed_mode_ids == {"5", "7", "12", "13", "14"}`
    drops `"13"`.
  - AC20's analytic-edge `witness` gains `(13, "collapsed_labels")`. The
    edge is analytic because no corpus case designates it.
- **test_148.**
  - AC19's `len(cat.entries) == 154` moves to 159.
  - AC16's `_AC16_CASES` gains one row driving `collapsed_labels`. AC7 rules
    out a corpus case, so the row is a planted record run through
    `run_rules`, in the shape of item 195's `planted_overlap` row and its
    `_overlap_reconstructed_record`.
  - The record may be a hand-built one carrying `stage3_unavailable` and the
    two labels' `per_label` entries. It may instead be
    `extract_feature_record` of the item-129 coincident map.
  - The row expects `("collapsed_labels",)`.

## Validation

1. **Replay the VerSe19 measurement (A3, A11)** with the scratch probe's
   method:
   - For every `*_seg-vert_msk.nii.gz` under the VerSe19 root
     (`SEGFACET_VERSE_COHORT`, or `/mnt/data/spine/data/datasets/VerSe/VerSe19`
     on the reference host), compute every label's centroid with
     `segfacet.features.centroids.compute_centroid`.
   - Take the minimum pairwise distance per case.
   - Confirm that no case has a pair at or below 2.0 mm, and that the minimum
     is the one A3 records.
   - Record the result with the commit in Decisions & Trade-offs.
   - When the root is absent, record `❓ Unverified: VerSe19 not mounted`.
     Never record a pass.
2. **Run the CLI on the coincident map:** `segfacet run --scan <scan> --seg
   <seg> --out <dir> --no-reference`, with the map and scan written as
   test_135 AC15 does.
   - The JSON report's findings include one `collapsed_labels` finding on
     labels 21 and 22.
   - The text report shows its reason.

## Dependencies

None.

**Downstream / siblings, not blockers:** queue-030 items 218, 219, 223 and
226 edit some of the same files (`src/segfacet/failure_modes.py`,
`src/segfacet/catalogue.py`, the generated docs and the shared count
literals). Neither side pins what the other produces, so whichever lands
later regenerates and re-measures on top. Step 9 re-measures the count
clauses live for that reason.

## Decisions & Trade-offs

- **Implemented as specified (2026-10-13).** `collapsed_labels` reads `severity`
  and `max_centroid_distance_mm` through `config.rule_param`, as `split_fragment`
  does. The rule's evidence tuple is `("analytic", <prose>)`.
- **Catalogue driver** builds the item-129 concentric boxes (labels 21 and 22,
  shell and core) in-function with NumPy and an identity affine, so no tests
  path is named. Strict build refuses nothing: the five `stage3_unavailable.*`
  leaves are `reason`, `detail`, `levels[]`, `labels[]`, `coordinate_mm[]`.
- **Measured live after the change:** catalogue 159 entries, of which 104 have
  empty mode evidence; observed summary non-numeric 40, varies 86, others
  unchanged. Derived status counts: validated 6, implemented 4, specified 2,
  proposed 4. Rungs: synthetic-demonstrable 6, needs-real-data 3,
  structurally-unobservable 1, none 6. Edges: 16, with needs-real-data 8.
- **Validation step 1 (VerSe19 replay):** ❓ Unverified, not run in this
  build step. A3's recorded measurement stands.

- **Left open:** A mode-13 detector on a *fraction* of the expected spacing,
  through the candidate feature `pairs.adjacent.spacings_mm[]`. It would
  catch labels that are close but not collapsed, as mode 13's definition
  reads. It needs a calibration this item does not have, and it risks moving
  the `split_own_label` and `fuse_*` cases, whose closest pairs sit at 0.40×
  the median spacing.
- **Left open:** Whether a `stage3_unavailable` reason other than
  `coincident_centroids`, if one is ever added, is mode 13. Today the rule
  reports any reason (A6).
- **Left open:** A `displaced_vertebra` opt-in for the near detector (A7),
  to be added once a case shows `spline_offset` firing on a label of a near
  pair.
