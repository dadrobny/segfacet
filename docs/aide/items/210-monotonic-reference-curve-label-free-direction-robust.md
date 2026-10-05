<!-- aide-template: item 3 -->
# Item 210 — The monotonicity check's reference curve made label-free and direction-robust

> **Created:** 2026-10-03 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System (maintenance deliverable)
> **Queue:** [`../queue/queue-028.md`](../queue/queue-028.md) · Item 210
> **Objectives:** G2
> **Suggested branch:** `aide/210-monotonic-reference-label-free`

---

## Description

This item closes three `defect` entries in `docs/aide/insights.md`, all
captured by item 198 on 2026-09-29: `2026-09-29-5d37`, `2026-09-29-ab9d` and
`2026-09-29-dac4`.

**The defects.** `segfacet.features.consistency.compute_monotonic_consistency`
measures each centroid's `u` on a spline reference curve, whose point order
comes from item 132's `_traversal_order`.

- **Pose (5d37).** That order is a sort by S (`centroid_mm[2]`). Where S is
  not monotone along the spine (a strongly curved sacrum or coccyx, a lying or
  flexed pose, an unusual scan orientation), the curve zigzags. A correctly
  labelled 10-level spine on a 210° arc fires a false pair, (L4, L5).
- **Direction (ab9d).** The sort's direction comes from the supplied order's
  first-to-last net S advance. When an endpoint of the judged order is itself
  misplaced, the walk runs the wrong way. On `sequence_break` (tail L5
  relabelled T13), `mislabel`'s `ordering` fires on (L1, L2), (L2, L3) and
  (L3, L4), and never names T13.
- **Reconstruction handler (dac4).** Mode 4's
  `segfacet.synth.regression._recon_monotonic_true_spatial_order` hands the
  check ascending-integer centroids rather than the anatomical order the
  pipeline uses since item 198. It also passes a fit in ascending
  stacking-axis voxel order, which on the RAS-native corpus runs tail to
  head. Measured 2026-10-03: on the unperturbed `clean_control` map the
  handler fires `ordering` on all four pairs, and on item 198's correctly
  placed T13 map it fires three. The pipeline fires none on either.

**The fix (maintainer's choice, 2026-10-05).** The check stops using a spline.

1. **Geometric order.** A label-free path is built through the centroids: the
   longest path of their minimum spanning tree (MST). Every centroid is
   projected onto that path's polyline, giving its arc length `s` (A1).
2. **Normalisation.** `s` is divided by the path length, so `u_values` keeps
   its `[0, 1]` range and its name.
3. **Direction.** The walk runs in whichever direction has fewer rank
   inversions against the supplied order, as `sequence` has done since item
   192 (A2).
4. **Judgement.** The supplied (anatomical) label order is judged directly
   against `u`. A consecutive pair whose `u` does not advance is a
   non-monotonic pair. No spline is refitted and no closest-point search on a
   spline is made (A3). Once the geometric order is known, a spline fitted
   through the points in that order gives a `u` that is monotone by
   construction, so the verdict reduces to "label order against path
   position". Using `s` directly takes one geometric step instead of two that
   must agree. The spline stays for the offset and orientation features.
5. **Handler.** The reconstruction handler stops recomputing monotonic
   consistency. It evaluates `MislabelRule` on the record that
   `pipeline.extract_feature_record` builds, so the two paths cannot disagree
   (A5).
6. **Wording.** User-facing text that still describes a spline is reworded to
   describe position along the label-free path through the centroids:
   - the `ordering` finding's reason tail "(spline parameter does not
     advance)";
   - the `ordering` detector's question "…along the fitted spine curve?",
     which is rendered in `docs/aide/rules.generated.md`.

   The reason's leading tag, `"Vertebra ordering inconsistent with label:"`,
   is unchanged (queue-028 spec review, 2026-10-05).

**What moves** (A4, measured 2026-10-05).

- In both corpora only `sequence_break`'s findings change: its three lumbar
  `ordering` findings become one, on labels {20, 28}.
- No case's rule-level or detector-level firing set moves, so no expected set
  in `segfacet.failure_modes.SPECIFICATION` changes. `sequence_break`'s
  `reason`, which quotes the old pairs, is rewritten.
- Every case's `u_values` move, because they now measure normalised path
  arc length rather than spline `u`. The catalogue's three
  `monotonic_consistency` texts and its observed `u_values` range (now
  exactly 0–1) are regenerated with them.

**Not in scope.**

- `pipeline.py`. Its anatomical order (item 198) and the fit it passes are
  unchanged. That fit is now unused by the check (Left open).
- The `MislabelRule` logic, its consumed paths and its detector ids. Only
  prose changes there: the reason tail, the detector question, and the stale
  phrase "S-sorted label order".
- `docs/spinal-curve-model.md`, a dated design record of item 119's spline
  choice.
- `tests/corpus/manifest.json`, every corpus fixture, the severity ladders,
  every config key.

## Acceptance Criteria

Terms used below:

- **`cfg`** is `segfacet.config.bundled_default_config()`.
- **"The `X` case"** is the entry of `segfacet.synth.corpus.load_manifest()["cases"]`
  whose `case_id == "X"`.
- **`relabel(M)`** is item 198's helper: the `clean_control` case's
  `segfacet.synth.regression.loaded_seg_image`, with every voxel value `a` in
  `M` replaced by `M[a]`. Each replacement reads the original data, and the
  affine and header are kept.
- **`T13_MAP`** is `relabel({20: 28, 21: 20, 22: 21, 23: 22, 24: 23})`: T13
  then L1–L4, head to tail, with T13 correctly placed.
- **`ARC`** is ten `LabelCentroid`s with level names T8, T9, T10, T11, T12,
  L1, L2, L3, L4, L5 and labels 1–10, in that order. Centroid `i` (0-based)
  has `centroid_mm = centroid_voxel = (0.0, 60·cos tᵢ, 60·sin tᵢ)`, with
  `tᵢ = radians(−90 + 210·i/9)`. S rises to 60 mm at `t = 90°`, then falls to
  about 52 mm.
- **`ARC_SWAP`** is `ARC` with the list entries at indices 3 and 4 exchanged:
  T12's entry, with its own coordinates, comes before T11's.
- **`HANDLER_CASE`** is the `clean_control` case dict updated with
  `detection="reconstructed_record"`,
  `reconstruction="monotonic_true_spatial_order"` and
  `expected_rule_ids=["mislabel"]`.
- **`via_handler(X)`** is
  `{(f.rule_id, f.detector_id, f.labels) for f in segfacet.synth.regression.reconstructed_findings(HANDLER_CASE, cfg)}`,
  with `segfacet.synth.regression.loaded_seg_image` monkeypatched to return
  `X` for any case.

- [ ] **AC1: `sequence_break` names the misplaced level.**
  `{(f.detector_id, f.labels) for f in segfacet.synth.regression.pipeline_findings(<the sequence_break case>, cfg) if f.rule_id == "mislabel"} == {("ordering", frozenset({20, 28}))}`.
- [ ] **AC2: a curve whose S reverses reads monotone when correctly
  labelled.**
  `compute_monotonic_consistency(ARC, fit_centroid_spline(ARC)).non_monotonic_pairs == ()`.
- [ ] **AC3: the reconstruction handler agrees with the pipeline.**
  `via_handler(T13_MAP) == {(f.rule_id, f.detector_id, f.labels) for f in MislabelRule().evaluate(segfacet.pipeline.extract_feature_record(T13_MAP, cfg), cfg)}`.
- [ ] **AC4: `u` is the normalised arc length along the path.**
  `compute_monotonic_consistency(ARC, fit_centroid_spline(ARC)).u_values == pytest.approx([i / 9 for i in range(10)], abs=1e-9)`.
- [ ] **AC5: the check reads no spline.**
  `compute_monotonic_consistency(ARC_SWAP, None).non_monotonic_pairs == (("T12", "T11"),)`.

Why each is written:

- AC1 is the queue's "on `sequence_break`, `ordering` names {20, 28}" (ab9d).
  Today it fires on {20, 21}, {21, 22} and {22, 23}.
- AC2 is the queue's "a curved spine whose z reverses yields monotone `u` for
  a correctly labelled case" (5d37). Today it returns `(("L4", "L5"),)`.
- AC3 is the queue's "the reconstruction handler and
  `pipeline.extract_feature_record` hand the check the same order" (dac4),
  written as the observable consequence (A5). Today the left side holds three
  findings and the right side none.
- AC4 pins maintainer decision 2: `u` is path position scaled to `[0, 1]`.
  `ARC`'s ten points are equally spaced, so its path chords are equal.
  Today the values are spline parameters, and `u[9]` is 0.732.
- AC5 pins maintainer decision 1: the check uses no spline, so a `None` fit is
  never read. It also checks the swap on a reversing curve:
  - a reference that follows the supplied order would hide the swap and
    return `()`;
  - an S sort would add the false (L4, L5);
  - today the call raises `AttributeError` on `None.degree`.
- The queue's "every corpus case's measured firing equals its expected set" is
  not restated. `tests/test_163_specificity_ratchet.py` already fails unless
  every authored set equals its measured firing, and A4 measured that none
  moves.

None of these closes a Stage 27 acceptance criterion. This is a maintenance
item.

## Assumptions

`loop.clarify = "assume"` in `aide.toml`. This batch was briefed as
interactive with the human unreachable. The maintainer then answered on
2026-10-05; those answers are recorded as decisions below. The vision posture
is `prototype`.

Every value marked as measured was taken with `.venv/bin/python` on
`aide/queue-028`, with steps 1–2 prototyped in-process: the module attribute
`segfacet.features.consistency.compute_monotonic_consistency` was replaced,
and the pipeline's deferred import picks that up. The working checkout was
not edited. The builder re-measures each value on the real change.

- **A1 (maintainer decision, 2026-10-05: the label-free order).** The order is
  the MST longest path, with every centroid projected onto it.
  - **The tree.** Prim's algorithm on the dense Euclidean distance matrix, in
    NumPy. Start at supplied index 0; the next node is the one with the
    smallest key, lowest index on a tie. It does not use
    `scipy.sparse.csgraph.minimum_spanning_tree`, which reads a zero distance
    (coincident centroids, possible from a direct caller) as a missing edge.
    No dependency is added.
  - **The path (double sweep).** `e1` is the tree node farthest (summed edge
    length) from supplied index 0. `e2` is the node farthest from `e1`. Ties
    go to the lowest index. The path runs `e2 → e1`.
  - **`s`.** `sᵢ` is the arc length, from `e2`, of centroid `i`'s closest
    point on the polyline through the path. Each segment's projection is
    clamped to the segment, the first-found segment wins a distance tie, and a
    zero-length segment projects to its start.
  - **`u`.** `uᵢ = sᵢ / L`, where `L` is the polyline's total length. When
    `L == 0` (every centroid coincident), every `uᵢ = 0.0` and every pair is
    flagged. The pipeline never reaches that case, because item 129's
    coincident-centroid pre-check runs first.
  - **Why not a nearest-neighbour chain** (rejected 2026-10-03): on a straight
    10-level spine at 30 mm pitch with T12 moved 60 mm sideways, a greedy
    chain skips T12, returns to it last, and fires (T12, L1). The MST order
    fires nothing.
- **A2 (maintainer decision, 2026-10-05: the direction).** The forward order
  is `sorted(range(n), key=lambda i: (s[i], i))` and the backward order is
  `sorted(range(n), key=lambda i: (-s[i], i))`. Inversions are pairs `a < b`
  with `order[a] > order[b]`. The backward direction is taken only when it has
  strictly fewer inversions; it then sets `uᵢ = 1 − sᵢ / L`. A tie keeps
  forward. This is item 192's rule for `sequence`
  (`heuristics/sequence.py::_head_to_tail`), applied to the geometric order.
  *Re-checked 2026-10-05 against `aide/queue-028` at 4aa45e0 (item 192
  merged): agrees.* `SequenceRule._head_to_tail` keeps its default order
  (descending S) and takes the other (ascending S) only when `_inversions` is
  strictly smaller, so a tie keeps the default, as above. Two differences are
  this item's own choices for its own input, not a divergence: item 192 counts
  inversions against `_RANK` of the level names and breaks a sort tie on the
  label value, while A2 counts against the supplied index and breaks a tie on
  it. The supplied order is the anatomical order (item 198), so for distinct
  ranks the two inversion counts coincide.
- **A3 (maintainer decision, 2026-10-05: no spline in the check).** This
  reverses this spec's 2026-10-03 A3, which kept the body unedited and kept
  the refit.
  - `compute_monotonic_consistency(centroids, fit=None)` now makes no
    `fit_centroid_spline` call and no `find_closest_point` call.
    `consistency.py` drops both imports and keeps `SplineFit` for the
    annotation.
  - **`fit` stays in the signature.** It keeps its name and position, its
    annotation becomes `Optional[SplineFit]`, its default is `None`, and it is
    never read. That is the smallest change: `pipeline.py`, the handler's old
    shape and about sixty test call sites pass it positionally, and none has
    to change.
  - The `ValueError` for `n < 2` is unchanged. The pair criterion
    `u[i] >= u[i+1]` is unchanged, and equal `u` still counts as a break.
  - The tree, projection and direction code lives in private helpers outside
    the function body. The body's only order comparison is the `>=`, so
    `tests/test_132_monotonicity_against_traversal_order.py::test_ac12_pair_loop_still_uses_gte_not_strict_gt`
    holds unedited.
- **A4 (measured 2026-10-05: what moves).**
  - **Firing.** Over all 18 cases of both manifests, each through its own
    detection path, only `sequence_break`'s findings change. They become, in
    report order:
    - `mislabel`, `ordering`, `flagged-for-review`, labels [20, 28], reason
      `"Vertebra ordering inconsistent with label: labels 28 (T13) and 20 (L1) are out of expected order along the spine (position along the label-free path through the centroids does not advance)."`.
      That is the measured reason with step 6's new tail; the measured
      firing ended in "(spline parameter does not advance)." before the
      rewording;
    - `sequence`, `shift`, `flagged-for-review`, labels [28], unchanged.

    The verdict stays `flagged-for-review`. `relabel_swap` keeps `ordering`
    on {21, 22}. Rule-level and detector-level firing sets are unchanged for
    every case, so `sequence_break`'s `expected_firing`
    `("mislabel", "sequence")` stands.
  - **`u_values`** (geometric corpus, rounded to 9 places, in the order
    judged):

    | Case | `u_values` |
    |---|---|
    | `clean_control` | `[0.0, 0.244657315, 0.483480081, 0.730901566, 1.0]` |
    | `displace` | `[0.0, 0.232739104, 0.479861733, 0.744010399, 1.0]` |
    | `fragment` | `[0.0, 0.244656461, 0.483667275, 0.730902505, 1.0]` |
    | `inject_islands` | `[0.0, 0.244663354, 0.48350904, 0.730894924, 1.0]` |
    | `remove_level` | `[0.0, 0.244998552, 0.73052624, 1.0]` |
    | `crop_at_border` | `[0.0, 0.22390374, 0.469607133, 0.753728411, 1.0]` (item 212 re-authors this case) |
    | `sequence_break` | `[1.0, 0.0, 0.244657315, 0.483480081, 0.730901566]` (T13, L1–L4) |
    | `relabel_swap` | `[0.0, 0.483480081, 0.244657315, 0.730901566, 1.0]` |

    `sequence_break`'s `non_monotonic_pairs` is `[["T13", "L1"]]`.
  - **Artifacts.** Regenerated in-process against the committed copies:
    - `docs/aide/feature_catalogue.generated.{json,md}` move. The `u_values[]`
      corpus range goes from `0–0.999999` to `0–1` (`maximum` and `span` 1.0,
      `count` 24). The three texts change once step 4 lands.
      `observed_summary` and the leaf count of 145 are unchanged.
    - `docs/aide/golden_evidence.generated.json`,
      `docs/aide/traceability_matrix.generated.{json,md}` and
      `docs/aide/failure_modes.generated.{json,md}` are byte-identical. The
      last two move only once step 5 rewrites the reason.
    - `docs/aide/rules.generated.md` moves on exactly one line, line 22, the
      `mislabel` `ordering` row's Question cell, once step 6 rewords the
      question. This was measured on 2026-10-05 by regenerating with the
      question replaced in-process; nothing else in the file moves. The
      question text is rendered in no other generated file (grep,
      2026-10-05).
    - `segfacet.eval.severity_ladder.run_severity_harness()` is unchanged
      (compared by `repr`).
  - **Unit fixtures, unchanged result.** Item 132's AC5, AC6 and its
    first-pair, last-pair, caudal, two-centroid and doubly-swapped fixtures.
    `tests/test_020_neighbour_consistency.py`'s swap fixtures. Item 198's
    controls and adversarial maps. `tests/test_191_condition_gate.py` AC13.
    *Re-checked 2026-10-05 against `aide/queue-028` at 4aa45e0 (items 132
    and 198 merged): agrees.* Every fixture named exists there. None of
    `tests/test_132_monotonicity_against_traversal_order.py`,
    `tests/test_020_neighbour_consistency.py`,
    `tests/test_198_ordering_along_expected_sequence.py`,
    `tests/test_191_condition_gate.py`, `consistency.py`, `sequence.py` or
    `pipeline.py` has a commit after 2026-09-30, so the 2026-10-05 measurement
    ran on the code now on the base. Item 132's straight-line fixtures (AC5,
    AC6, first-pair, last-pair, caudal, two-centroid, doubly-swapped) were
    re-derived by hand under A1 and A2: the path is the S axis, so `s` is S,
    and the fewer-inversions direction gives each asserted result, including
    AC6's `("L3", "L2")` forward and `("L2", "L3")` reversed. Their
    fit-counter assertions are the separate `_patched_consistency_fit_counter`
    reconciliation under Testing Strategy.
  - **Unit fixtures, changed result** (Testing Strategy reconciles each):
    - item 132's AC11 side-by-side fixture now yields `(("L2", "L3"),)`,
      because L2 and L3 project to the same `s` (`u` 1/3 each) and `>=`
      flags them; *re-checked 2026-10-05 against the committed fixture in
      `test_ac11_exact_s_tie_no_refit_still_monotonic` (L2 at (0, 0, 10), L3
      at (5, 0, 10)): agrees.* The tree is L1–L2, L2–L3, L2–L4, L4–L5; the
      double sweep gives `e1` = L5 and `e2` = L1, so the path is the S axis,
      30 mm long, and L3 projects onto L2's point at `s` = 10;
    - item 132's scoliotic adversarial yields `(("L3", "L4"), ("L4", "L5"))`,
      because its L5 is 56.6 mm from L1 but 80.6 mm from L4, so the tree joins
      L5 to L1; *re-checked 2026-10-05 against the committed fixture in
      `test_adv_scoliotic_shape_strictly_monotonic_s_no_refit`: agrees.*
      |L5 − L1| = 56.57 mm and |L5 − L4| = 80.62 mm. Prim from L1 joins L2,
      then L4 (20 mm from L2), then L3 (22.36 mm from L2 and from L4, an
      exact tie), then L5 via L1. Whichever parent L3 takes, the path runs
      from L5 through L1 and L2 to L3, with L4 at `s` between L2 and L3. Both
      directions have 5 inversions, so the walk from L5 stands and the pairs
      are `(("L3", "L4"), ("L4", "L5"))`;
    - `tests/test_020_neighbour_consistency.py`'s two full-reversal tests now
      read in order;
    - item 130's AC20 (monotonic `u` equals the spline `closest_u`) no longer
      holds.
- **A5 (maintainer accepted, 2026-10-05: the handler delegates).**
  `_recon_monotonic_true_spatial_order` becomes
  `MislabelRule().evaluate(extract_feature_record(loaded_seg_image(case), config), config)`.
  - Its old technique, judging against true spatial order, is now what the
    check itself does, label-free.
  - The registry key `"monotonic_true_spatial_order"` stays, because
    `tests/test_120_leave_one_out_offset.py` and
    `tests/test_040_synthetic_corpus.py` pin the key set. No committed case
    uses the handler.
  - The imports only the handler used are removed: `numpy`,
    `compute_centroid`, `compute_monotonic_consistency`,
    `fit_centroid_spline` and `si_axis`. No test reaches them through
    `segfacet.synth.regression` (grep, 2026-10-03).
- **A6 (the queue-mates).** No item in queue 028 reads an interface this item
  changes, and this item pins nothing a queue-mate changes.
  - Item 212 re-authors `crop_at_border` and changes the manifest. So the
    manifest is not under Asserts against: this item reads it only to find
    its fixtures and moves no entry. Both items edit `crop_at_border`'s row in
    `test_132`'s `_PRE_ITEM_U_VALUES`; whichever lands second re-measures that
    row.
  - Item 211 also edits `src/segfacet/failure_modes.py` and
    `docs/aide/failure_modes.generated.*`, with different case reasons. Both
    specs list them under May change.
  - The new test module carries none of the five signal shapes in item 213's
    A1 (`docs/aide/items/213-windows-ci-pinned-os-sensitive-subset.md`):
    - subprocess: `subprocess`, `run_process`, `sys.executable`;
    - CLI: `segfacet.cli` imports, or a string constant starting
      `segfacet.cli`;
    - bytes or newlines: `.read_bytes`, a `newline` keyword, a
      `.gitattributes` string, or a `regenerated_failure_modes` /
      `regenerated_traceability` fixture parameter;
    - path text: `.as_posix`, `os.sep` / `os.path.sep`, `PureWindowsPath` /
      `PurePosixPath`;
    - AIDE engine in-process: an `aide_check_result` fixture parameter.

    So item 213's pinned Windows list needs no entry for it. Its monkeypatch
    target is an object attribute, not a `segfacet.cli` string. The existing
    test files this item edits gain none of these shapes.
- **A7:** no human gate is needed, and no environment-gated capability is
  involved.

## Implementation Steps

1. **`src/segfacet/features/consistency.py`**: the order, per A1 and A2.
   - Replace `_traversal_order` with one private helper that returns the
     per-centroid `u` (normalised and directed). Small private pieces for
     Prim, the double sweep and the polyline projection are fine. No new
     public name.
   - It reads only `centroid_mm` and mutates nothing.
   - Add a `ponytail:`-style comment that names the known ceiling (Left open
     b): a gross lateral displacement of about twice the pitch can make the
     longest path run along the displaced spur. Name the candidate fix:
     exclude centroids flagged `displaced_vertebra` before building the tree.
2. **`compute_monotonic_consistency`**, per A3.
   - Signature `(centroids, fit: Optional[SplineFit] = None)`. Keep the
     `n < 2` `ValueError`.
   - `u_values` comes from step 1's helper. The pair loop stays
     `u_values[i] >= u_values[i + 1]`, and nothing else in the body compares.
   - Remove the `fit_centroid_spline` and `find_closest_point` imports.
   - Rewrite the module docstring's paragraph B, the `MonotonicConsistency`
     docstring and the function docstring. `u` is normalised arc length along
     the MST longest path, its direction has fewer inversions against the
     supplied order, the supplied order is the expectation, and `fit` is
     accepted but not read. Date it 2026-10-05, item 210, and keep item 132's
     history as one clause.
3. **`src/segfacet/synth/regression.py`**, per A5.
   - The handler returns
     `MislabelRule().evaluate(extract_feature_record(loaded_seg_image(case), config), config)`,
     and its docstring says why.
   - Remove the five unused imports.
   - In the module docstring, the "same reconstruction technique item 039
     used" sentence now says that technique is the pipeline's own check since
     item 210.
4. **`src/segfacet/feature_docs.py`**: three `FeatureDoc`s.
   - `stage3.monotonic_consistency.is_monotonic`, `.non_monotonic_pairs[]` and
     `.u_values[]` describe `u` as the normalised arc-length position on the
     label-free traversal path (item 210). They no longer describe a
     closest-spline-parameter.
   - This covers both `measures` and `computation`, including
     `.non_monotonic_pairs[]`'s `measures`, "Level-name pairs whose spline
     parameter does not advance."
   - Each `computation` keeps the word "traversal"
     (`test_132` AC28). No anchor or `MODE_ANCHOR_PATHS` entry changes.
5. **`src/segfacet/failure_modes.py`.**
   - In `_MODE_9`'s `sequence_break` `CorpusCaseExpectation`, rewrite `reason`
     to A4's measured firing: `ordering` fires once, on (T13, L1), labels 20
     and 28, beside `sequence`'s `shift` on 28. Date it 2026-10-05, item 210.
   - Keep the closing sentence that points at the mechanism.
   - The reason must stay non-empty and must not contain `rank(v) == v - 1`
     (`tests/test_145_eight_hypothesised_modes.py` AC10b).
   - `expected_firing`, the mechanism and the module docstring's dated
     2026-09-28 paragraph (history) are unchanged.
6. **`src/segfacet/heuristics/mislabel.py`**, prose only. The logic,
   `consumed_paths`, `detector_id`, `description` and `_MISLABEL_TAG` are
   unchanged.
   - In the `ConditionOptIn.reason` string and the module docstring's item-191
     bullet, "a reference curve fitted in S-sorted label order" becomes "the
     centroids' label-free geometric order (item 210)".
   - The finding's reason tail "(spline parameter does not advance)." becomes
     "(position along the label-free path through the centroids does not
     advance)."
   - The `ordering` `RuleDetector.question` becomes "Do two labels sit in the
     wrong order along the label-free path through the vertebra centroids?"
7. **Regenerate.** Run each module's `main` twice into temp paths, byte-compare
   the two runs, then write the committed copy:
   - `segfacet.failure_modes` → `docs/aide/failure_modes.generated.{json,md}`;
   - `segfacet.catalogue` → `docs/aide/feature_catalogue.generated.{json,md}`;
   - `segfacet.rule_table` → `docs/aide/rules.generated.md`. Only line 22's
     Question cell may differ from the committed copy (A4); any other moved
     line is a hand-back.

   Then regenerate `segfacet.traceability` and `segfacet.golden_evidence`
   into temp paths only. Each must equal its committed
   file (A4); if one does not, hand back.
8. **Reconcile** the tests listed under Testing Strategy. Each edit carries a
   dated item-210 comment.
9. Run `python .aide/scripts/aide.py scope 210` and
   `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/features/consistency.py` — the label-free order, the spline-free judgement and docstrings (steps 1–2).
- `src/segfacet/synth/regression.py` — the mode-4 handler delegates to the pipeline record; unused imports dropped (step 3).
- `src/segfacet/feature_docs.py` — three `monotonic_consistency` texts (step 4).
- `src/segfacet/failure_modes.py` — `sequence_break`'s reason (step 5).
- `src/segfacet/heuristics/mislabel.py` — the reason tail, the detector question and one stale phrase (step 6).
- `docs/aide/failure_modes.generated.json` — regenerated (step 7).
- `docs/aide/failure_modes.generated.md` — regenerated (step 7).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 7).
- `docs/aide/feature_catalogue.generated.md` — regenerated (step 7).
- `docs/aide/rules.generated.md` — regenerated; the `ordering` question cell (step 7).
- `tests/test_210_label_free_monotonic_reference.py` — **new**: this item's test module.
- `tests/test_020_neighbour_consistency.py` — the two full-reversal tests.
- `tests/test_098_stray_components.py` — `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`, its `sequence_break` and `relabel_swap` entries.
- `tests/test_116_ras_native_corpus.py` — `_ITEM_198_ADDED_MISLABEL_PAIRS["sequence_break"]`.
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — `_PRE_129_FINDINGS["sequence_break"]`.
- `tests/test_130_one_closest_point_search.py` — AC13's consistency check and the two AC20 tests.
- `tests/test_132_monotonicity_against_traversal_order.py` — the fit counter, AC4's table, AC7, AC9, AC10, AC11, AC29 and the scoliotic adversarial.

**The reconciliation fence.** Each edit to an existing test either moves a
literal or retires a test whose subject this item removes, exactly as Testing
Strategy lists it, with a dated item-210 comment. Nothing else is retired,
skipped, marked `xfail` or loosened. **A red test in a file not listed here
is a hand-back to spec-author.**

**Asserts against:**

- `src/segfacet/pipeline.py` — AC3's right-hand side is its `extract_feature_record`, unchanged (A5).
- `tests/corpus/fixtures/sequence_break_seg.nii.gz` — AC1 reads it.
- `tests/corpus/fixtures/clean_control_seg.nii.gz` — AC3 and `handler-still-detects-swap` relabel it.
- `tests/test_163_specificity_ratchet.py` — stays green unedited: every case's measured firing equals its expected set (A4).
- `tests/test_198_ordering_along_expected_sequence.py` — stays green unedited: item 198's controls and adversarial maps fire as before (A4).
- `tests/test_191_condition_gate.py` — stays green unedited: AC13's endpoint swap still names {20, 21} (A4).

## Testing Strategy

The test module is `tests/test_210_label_free_monotonic_reference.py`, with
one test per AC. `relabel`, `ARC` and `ARC_SWAP` are module helpers built as
the AC terms define them. `LabelCentroid` is constructed directly, as
`tests/test_132_monotonicity_against_traversal_order.py`'s `_centroid` does.
The handler monkeypatch uses pytest's `monkeypatch` fixture. Values are as
measured in Assumptions.

Named adversarial cases, and no others:

- **displaced-far-lateral-not-misread:** ten centroids T8…L5 at
  `(0, 0, −30·i)` mm, with index 4 (T12) moved to `(60, 0, −120)`. Then
  `compute_monotonic_consistency(c, None).non_monotonic_pairs == ()`. This
  guards a greedy nearest-neighbour chain, which fires (T12, L1). Here the
  displaced vertebra is mid-spine on a 10-level spine, so its spur is shorter
  than the remaining path; that is not Left open (b)'s shape.
- **handler-still-detects-swap:**
  `via_handler(relabel({21: 22, 22: 21})) == {("mislabel", "ordering", frozenset({21, 22}))}`.
  This guards a handler "fix" that returns no findings. AC3 alone cannot
  catch that, since both of its sides are empty.

**Existing tests to reconcile** (measured on the prototype, 2026-10-05):

- **`tests/test_098_stray_components.py`**,
  `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS["sequence_break"]` (around line 1004).
  - The three `mislabel` dicts become one: `rule_id` `"mislabel"`,
    `detector_id` `"ordering"`, `severity` `"flagged-for-review"`, `labels`
    `[20, 28]`, `reason` A4's exact string. It stays before the unchanged
    `sequence` dict, and the verdict stays `flagged-for-review`.
  - The `relabel_swap` entry (around line 938) keeps its labels [21, 22]. Its
    reason's tail "(spline parameter does not advance)." becomes step 6's
    "(position along the label-free path through the centroids does not
    advance)."
  - The modules that import this constant read it unedited: `test_089`,
    `test_090`, `test_094`, `test_102`, `test_108`, `test_123`, `test_132`,
    `test_143`.
- **`tests/test_116_ras_native_corpus.py`**,
  `_ITEM_198_ADDED_MISLABEL_PAIRS["sequence_break"]` (line 430) becomes
  `(("mislabel", (20, 28)),)`. The comment gains a dated item-210 line. The
  constant's name stays.
- **`tests/test_129_coincident_centroids_and_held_out_floor.py`**,
  `_PRE_129_FINDINGS["sequence_break"]` (line 735) becomes
  `{("mislabel", (20, 28)), ("sequence", (28,))}`.
- **`tests/test_020_neighbour_consistency.py`**:
  `test_ac4_reversed_sequence_all_non_monotonic` and
  `test_ac4_reversed_sequence_has_non_monotonic_pairs` (lines 387–402).
  - Both are replaced by one test, `test_ac4_full_reversal_reads_in_order`.
    It runs the same fixture and asserts `non_monotonic_pairs == ()`.
  - Its comment says the check takes the direction with fewer inversions, so
    a full reversal reads in order (Left open a).
  - The other monotonic tests in the module hold. Measured: the swaps are
    still detected, the curved swap gives `(("T11", "T10"),)`, and every `u`
    is in `[0, 1]`.
- **`tests/test_130_one_closest_point_search.py`**:
  - `test_ac13_consistency_no_longer_defines_search`: drop its
    `"find_closest_point" in source` assertion. The module no longer searches
    a spline at all. Its `_find_closest_u` and `linspace` assertions stay.
  - `test_ac20_monotonic_and_offset_closest_u_agree_clean` and `_displaced`:
    retired. Monotonic `u` is no longer a spline `closest_u`, so the two
    searches they compared no longer both exist.
  - AC18 (fit counts) and AC19 (the fit object passed) hold, because
    `pipeline.py` is unchanged.
- **`tests/test_132_monotonicity_against_traversal_order.py`**:
  - `_patched_consistency_fit_counter`: patch
    `segfacet.features.spline.fit_centroid_spline`, because the consistency
    module no longer imports it. It counts zero calls from the check.
  - `_PRE_ITEM_U_VALUES`: every row becomes A4's table value (`abs=1e-9`
    holds against the 9-place rounding).
  - `test_ac7_out_of_order_sequence_exactly_one_refit`: assert
    `len(calls) == 0`. Its name gains no new meaning; the comment says the
    check makes no fit.
  - `test_ac9_item_130_closest_u_agreement_reproduced_unedited`: retired. It
    delegates to the retired item-130 AC20 tests.
  - `test_ac10_refit_inherits_supplied_fit_degree_and_smoothing`: retired.
    There is no refit.
  - `test_ac11_exact_s_tie_no_refit_still_monotonic`: assert zero calls and
    `non_monotonic_pairs == (("L2", "L3"),)`. Equal `s` is flagged by `>=`
    (Left open: ties).
  - `test_ac29_catalogue_measured_content_unchanged`: the `u_values[]` corpus
    `maximum` and `span` become `pytest.approx(1.0, abs=1e-12)`. The
    sub-floor-residue comment says the minimum is now exactly 0.0.
  - `test_adv_scoliotic_shape_strictly_monotonic_s_no_refit`: retired. Its
    subject, an S-monotone order that needs no refit, no longer exists. Its
    L5 is nearer L1 than L4, which is Left open (b)'s class.
  - Unchanged and holding: AC2, AC5, AC6, AC8, AC12, AC28 (once the catalogue
    is regenerated) and the other adversarial tests (A4).

**Checked and unaffected** (read 2026-10-05):

- `tests/test_022_stage3_serialisation.py`: its swaps are still
  non-monotonic, and its `u` values are in `[0, 1]`.
- `tests/test_036_clean_gt.py` AC11, and `tests/test_122_signed_curvature.py`.
- `tests/test_039_identity_ordering_alignment_perturbations.py`: AC17's
  rule-id set `{"mislabel", "sequence"}` holds. Its item-039 helper still
  gives (L2, L3) on `relabel_swap`.
- `tests/test_041_regression_suite.py`, `tests/test_120_leave_one_out_offset.py`
  and `tests/test_040_synthetic_corpus.py`: they pin the registry key and the
  unknown-technique error.
- `tests/test_145_eight_hypothesised_modes.py` and
  `tests/test_154_ladder_remeasurement.py`.
- `test_130` AC22 and `test_129` AC20 compare a regenerated catalogue with the
  committed one. They hold once step 7 commits the regenerated copy.
- **Pins of the reworded texts**, searched 2026-10-05 across `src/`, `tests/`
  and `docs/` for "spline parameter does not advance", "along the fitted
  spine curve", "spline parameter" and the reason tag:
  - Must move:
    - `test_098` (the two entries above);
    - `docs/aide/rules.generated.md` line 22 (regenerated);
    - `src/segfacet/feature_docs.py` line 1587 and its rendering in
      `docs/aide/feature_catalogue.generated.{json,md}` (step 4,
      regenerated).
  - Read only through the unchanged tag `"Vertebra ordering inconsistent
    with label:"`, so they hold:
    - `tests/test_033_mislabel.py`, `tests/test_035_failure_modes.py`,
      `tests/test_039_identity_ordering_alignment_perturbations.py`,
      `tests/test_132_monotonicity_against_traversal_order.py` AC13, and
      `tests/test_145_eight_hypothesised_modes.py`.
  - `tests/test_202_rule_table.py` compares each Question cell with the live
    `det.question`, so it follows step 6.
  - Not edited:
    - `tests/test_132_monotonicity_against_traversal_order.py`'s
      `_PRE_ITEM_STATUS_OVERRIDES` quotes the signed maintainer text in
      `STATUS_OVERRIDES` ("…verify order along the spline parameter…"). It is
      a review verdict, not a description of the computation, and AC30 pins
      it byte-identical.
    - `docs/aide/status/index.html` is a generated status snapshot.
    - `docs/aide/insights.md` and the earlier item specs (033, 135, 198) are
      history.

## Validation

Replay `sequence_break` through the CLI without a reference, for the reason
`CLAUDE.md` (Gotchas) gives:

```
.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/sequence_break_seg.nii.gz --out <tmp> --no-reference
```

- `<tmp>/segfacet_report.json` holds exactly the two findings of A4, with
  verdict `flagged-for-review`.
- Its `features.stage3.monotonic_consistency.non_monotonic_pairs` is
  `[["T13", "L1"]]`, and its `u_values` equal A4's `sequence_break` row.

No environment profile is needed.

## Dependencies

None. Items 132, 192 and 198, whose code this item changes or mirrors, are
merged. This item pins no interface of an unbuilt item.

**Downstream:** item 213 lists items 209–212 as its blockers, so its Windows
list is built last. This item's new module needs no entry in that list (A6).
Items 211 and 212 re-measure the corpora too. This item moves no expected
set, so its order relative to them is free.

## Decisions & Trade-offs

To be updated during implementation.

- **2026-10-05, queue-028 spec review (resolutions accepted by the
  maintainer).**
  - **Medium.** Spline wording survived in user-facing text after the
    no-spline decision: the `ordering` finding's reason ended "(spline
    parameter does not advance)", and the detector's question asked
    "…along the fitted spine curve?". The item widens to reword both,
    describing position along the label-free path through the centroids
    (Description fix 6, step 6).
    - `docs/aide/rules.generated.md` joins May change. It regenerates, and
      only its `ordering` Question cell moves (A4, measured).
    - `test_098`'s `relabel_swap` entry, which quotes the same reason, is
      reconciled beside `sequence_break`'s. The search for other pins is
      listed under Testing Strategy.
  - **Nit.** A6's list of item 213's signal shapes came from an earlier 213
    draft: it named `segfacet.synth.golden`, which 213 dropped, and missed
    `sys.executable`, `run_process`, `os.sep`, `PureWindowsPath` /
    `PurePosixPath` and the `regenerated_*` / `aide_check_result` fixture
    parameters. It is refreshed from the committed 213 A1.
- **Rejected (maintainer, 2026-10-05): an order-free principal-curve fit.**
  This is an alternating project-and-refit fit, with degrees of freedom from
  the level count and robust weights. Measured 2026-10-05, it converges to
  its initial order's verdict:
  - seeded from the MST order, it fires (T12, L1) on the L1-displaced case;
  - seeded from the S sort, it fires (L4, L5) on the 210° arc;
  - several runs did not converge within 20 iterations.

  It moves the ordering decision into the initialisation and adds a risk of
  non-determinism.
- **Rejected (2026-10-03): a nearest-neighbour chain**, for A1's reason.
- **Left open (a):** a fully reversed labelling reads as in order. The
  fewer-inversions direction walks the path the other way, as `sequence` does
  (item 192). The maintainer rules it out of this feature.
- **Left open (b):** a gross lateral displacement of roughly twice the level
  spacing or more, with the rest of the spine unmoved, can make the longest
  path run along the displaced spur.
  - Measured 2026-10-05 on a straight 6-level spine at 30 mm pitch, moving
    each level 60 mm sideways in turn. False `ordering` pairs: T12 0, L1 1,
    L2 2, L3 3, L4 1, L5 0. Moving L1 by 20, 30, 40 or 50 mm gave none.
  - The false pairs involve undisplaced neighbours, so item 191's
    findings-level condition gate does not remove them.
  - The maintainer judges it unlikely in real data. It is kept as a code
    comment (step 1) and acted on only if experiments show it. Candidate fix:
    exclude centroids flagged `displaced_vertebra` before building the tree.
- **Left open (c):** a possible follow-up, not this item: find outliers from
  the MST order by minimising the bending energy of a spline fit.
- **Left open (ties):** two centroids at equal `s`, side by side, are flagged
  by `>=`. Item 132's AC11 fixture now yields `(("L2", "L3"),)`. The
  maintainer considers this anatomically implausible and a non-issue until
  real data shows otherwise.
- **Left open:** `compute_monotonic_consistency`'s `fit` parameter is unused
  (A3). `pipeline.py` still refits an anatomically ordered spline for it when
  T13 or `Cocc` reorders the levels, which is wasted work on those maps.
  Dropping both would touch `pipeline.py`, item 130's AC19 and about sixty
  call sites, so it is a separate clean-up.
- **Left open:** whether S1–S6 share one rank in the judged order, as item 192
  decided for `sequence` (inherited from item 198). No corpus case has two
  sacral labels.
