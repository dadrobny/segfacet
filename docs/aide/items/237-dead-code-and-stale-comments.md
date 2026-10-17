<!-- aide-template: item 3 -->
# Item 237 — Dead code and stale comments left by items 210, 223 and 227

> **Created:** 2026-10-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-032.md`](../queue/queue-032.md) · Item 237
> **Objectives:** G7
> **Suggested branch:** `aide/237-dead-code-and-stale-comments`

---

## Description

Four leftovers from items 210, 223 and 227, each recorded in an insight with
its location. None changes what any rule reads or fires, and no generated
document moves.

**1. Dead helper in `coverage.py`** (insight `2026-10-13-aeec`).
`_find_entry_by_level_name` in `src/segfacet/heuristics/coverage.py` has no
caller. The live lookup is the copy in `src/segfacet/heuristics/fov.py`,
reached through `derive_fov_coverage`. Under item 110's last-segment
catalogue scan the dead copy's string keys still counted, so it kept
`coverage`'s `level_name` attribution alive. Since item 223 the scan follows
`evaluate` through the helpers it calls (test_223 AC3 pins that attribution
through `fov.py`), so the copy contributes nothing. It is deleted, with the
`Optional` import it alone uses.

**2. `relabel_swap` detection credited to a fitted curve** (insights
`2026-10-13-cc62`, `2026-10-16-50ce`). Since item 210 (2026-10-05)
`compute_monotonic_consistency` fits no curve. It reads each label's `u`,
the normalised arc length along the longest path of the centroids' minimum
spanning tree, a path built without reading labels, and judges the supplied
order against `u`. Item 227 corrected the production descriptions. These
passages still say the check judges against item 132's traversal-ordered
reference fit, or one fitted in label order:

- `src/segfacet/failure_modes.py`, module docstring, the item-191
  "Correction (2026-09-28, after validation round 1)" paragraph (~line 279):
  "judged against a reference curve fitted in S-sorted label order";
- `tests/test_039_identity_ordering_alignment_perturbations.py`, the
  `test_ac11_relabel_swap_run_qc_does_not_surface_swap` docstring (~line 413);
- `tests/test_040_synthetic_corpus.py`, the comment above
  `_PIPELINE_ONLY_MODES` (~line 102) and the
  `test_ac8_modes_4_8_reconstructed_record_rest_pipeline` docstring
  (~line 314);
- found by this spec's sweep, the same claim:
  `tests/test_057_acceptance_stage7.py` (module docstring ~line 43 and the
  comment ~line 82), `tests/test_116_ras_native_corpus.py` (~line 409),
  `tests/test_098_stray_components.py` (~line 926),
  `tests/test_129_coincident_centroids_and_held_out_floor.py` (~line 732)
  and `tests/test_125_stage28_validation.py` (module docstring ~line 18 and
  the `test_ac7_mode4_relabel_swap_is_monotonic_pinned_true` docstring
  ~line 326).

**3. Mechanism B described as a last-segment match** (insight
`2026-10-14-94ec`). Since item 223, `segfacet.catalogue`'s mechanism B is a
path-aware scan with no last-segment fallback, and it tags every attribution
`static`. No mechanism has emitted `static-ambiguous` since. In
`tests/test_103_feature_catalogue.py`:

- the module docstring (~line 84) lists an adversarial case "an ambiguous
  static name resolving to >1 path (`static-ambiguous` on every candidate)";
- `test_ac12_rule_evidence_tags_and_rule_id_sets` (~line 591) still accepts
  `static-ambiguous`;
- `test_adv_ambiguous_static_name_tagged_on_every_candidate` (~lines
  1324–1352) only asserts anything when some entry carries
  `static-ambiguous`, which none does, so it can never fail.

Three dated reconciliation notes describe the old mechanism:
`tests/test_136_rule_mode_declarations.py` (~line 868, the item-215 note) and
`tests/test_137_mode_less_rule_disposition.py` (~line 604, the item-148 note;
~line 968, the item-215 note).

**4. The vacuous ambiguity test is replaced** by one that fails when
mechanism B regresses or is gone (AC3).

**Not in scope:**

- `fov.py`'s live `_find_entry_by_level_name`;
- `segfacet.observed_range`'s own last-segment matching (item 124) and the
  `tests/test_124_observed_range.py` comments on it, which describe that
  mechanism correctly;
- the specification string in `failure_modes.py` (~line 2532) saying "a
  label swap can put a centroid off the curve fitted in label order". That
  curve is `spline_offset`'s, which is still fitted in label order, so the
  string is true. It is also rendered into
  `docs/aide/failure_modes.generated.*`;
- `tests/test_132_*` and `tests/test_210_*`, whose docstrings describe what
  their own items built;
- any rule, feature, threshold or generated artifact.

## Acceptance Criteria

- [ ] **AC1: The dead coverage helper is gone.** After
  `import segfacet.heuristics.coverage as m`,
  `hasattr(m, "_find_entry_by_level_name")` is `False`.
- [ ] **AC2: Every rule attribution is tagged `observed` or `static`.** In
  `build_catalogue(strict=True)`, the set of evidence tags over every
  entry's `rule_evidence` pairs is a subset of `{"observed", "static"}`.
- [ ] **AC3: A static read is attributed to exactly the path it names.** An
  ad-hoc `Rule` registered for the build, whose `evaluate` reads
  `record.get("reference_delta", {}).get("per_label", {}).get(k, {}).get("features", {}).get("physical_volume_mm3", {}).get("value")`
  with `k` not a string literal, gets `(rule_id, "static")` in
  `build_catalogue(strict=False)` on exactly one entry, whose path is
  `reference_delta.{label}.features.physical_volume_mm3.value`. Four other
  catalogue paths end in `.value`, so a last-segment fallback attributes
  none of them and an every-candidate tag attributes all five; a build with
  mechanism B gone attributes none.

## Assumptions

- **A1 (no generated artifact moves).** Deleting the uncalled helper changes
  no catalogue attribution, because the path-aware scan only follows calls
  made from `evaluate`. The `failure_modes.py` paragraph is in the module
  docstring, which no generator renders (only
  `scripts/aide_status_report.py` reads a `__doc__`, its own). Test comments
  render nowhere. So `docs/aide/feature_catalogue.generated.*`,
  `docs/aide/traceability_matrix.generated.*`,
  `docs/aide/failure_modes.generated.*` and `docs/aide/rules.generated.md`
  stay byte-identical, and are declared under Asserts against. If a
  regeneration moves any of them, the builder hands back rather than
  committing the change.
- **A2 (dated notes are amended, not rewritten).** Most of the passages in
  Description 2 and all three in test_136/137 are dated records ("2026-08-31
  (item 132): …", "Reconciled (item 148, …)"), true of the code when they
  were written. Each is kept and gets a short dated addition in the same
  passage, for example `Since item 210 (2026-10-05) the check fits no curve:
  it reads position along a label-free MST path.` (or, for mechanism B,
  `Since item 223 mechanism B is path-aware, with no last-segment
  fallback.`). Where the passage states the old mechanism in the present
  tense (the `failure_modes.py` paragraph, test_039 AC11 "surfaces the
  swap", test_040 ~102 and ~314 "judges"), that clause is reworded to the
  current mechanism and the item-132 history stays in the sentence. The
  builder may reword, provided each passage reads true against
  `compute_monotonic_consistency` and `_path_positions` in
  `src/segfacet/features/consistency.py` (or `build_catalogue`'s mechanism
  B in `src/segfacet/catalogue.py`).
- **A3 (the replacement for `failure_modes.py`).** A default the builder may
  reword: "The ordering signal is not spoiled by a displacement -- it reads
  each label's position along a label-free path through the centroids (item
  210), and a swapped label keeps its place along that path unless it moves
  past a neighbour."
- **A4 (the vacuous test is retired from test_103, not rewritten there).**
  The queue allowed either. Its replacement is item 237's AC3, because the
  property it guards now is mechanism B's path-awareness, not item 103's
  tagging. The module-docstring entry at test_103 ~line 84 goes with it.
- **A5 (test_103 AC12 is reconciled, not duplicated away).** AC2 is
  item 237's own test. test_103's `test_ac12_rule_evidence_tags_and_rule_id_sets`
  keeps item 103's criterion number (§6) and its `rule_ids_in_evidence`
  check, and its `allowed` set drops `static-ambiguous`.
- **A6 (the extra sweep sites).** The queue named four sites. A grep for
  "traversal-ordered", "reference fit", "reference curve" and "fitted in"
  over `src/` and `tests/` found seven more passages in five files making the
  same claim (Description 2). They are in scope because the queue's
  testable line covers every test and module docstring.

## Implementation Steps

1. **`src/segfacet/heuristics/coverage.py`:** delete
   `_find_entry_by_level_name` (~lines 438–450) and drop `Optional` from the
   `typing` import if nothing else uses it.
2. **`src/segfacet/failure_modes.py`:** reword the one clause in the item-191
   correction paragraph (A3). Nothing else in the module changes.
3. **The `relabel_swap` test comments** (Description 2): amend each passage
   per A2. No assertion, test name or parametrisation changes.
4. **`tests/test_103_feature_catalogue.py`:** drop `static-ambiguous` from
   `test_ac12`'s `allowed` set; delete
   `test_adv_ambiguous_static_name_tagged_on_every_candidate`; remove the
   module docstring's "ambiguous static name" adversarial entry.
5. **`tests/test_136_*` and `tests/test_137_*`:** amend the three mechanism-B
   passages per A2. No assertion changes.
6. Regenerate nothing. Run `.venv/bin/python -m segfacet.catalogue --json
   <scratch>/c.json --md <scratch>/c.md` once and compare against the
   committed pair to confirm A1.

No helper is written and no dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/coverage.py` — the dead helper and its import (step 1)
- `src/segfacet/failure_modes.py` — the item-191 paragraph's clause (step 2)
- `tests/test_039_identity_ordering_alignment_perturbations.py` — the AC11 docstring (step 3)
- `tests/test_040_synthetic_corpus.py` — the comment and AC8 docstring (step 3)
- `tests/test_057_acceptance_stage7.py` — two passages (step 3)
- `tests/test_098_stray_components.py` — one comment (step 3)
- `tests/test_116_ras_native_corpus.py` — one comment (step 3)
- `tests/test_125_stage28_validation.py` — two passages (step 3)
- `tests/test_129_coincident_centroids_and_held_out_floor.py` — one comment (step 3)
- `tests/test_103_feature_catalogue.py` — AC12's set, the retired test and its docstring entry (step 4)
- `tests/test_136_rule_mode_declarations.py` — one dated note (step 5)
- `tests/test_137_mode_less_rule_disposition.py` — two dated notes (step 5)
- `tests/test_237_dead_code_and_stale_comments.py` — this item's AC tests

**Asserts against:**

- `docs/aide/feature_catalogue.generated.json` — A1: stays byte-identical; the existing drift tests compare it with a fresh build
- `docs/aide/feature_catalogue.generated.md` — A1, as above
- `docs/aide/traceability_matrix.generated.json` — A1, as above
- `docs/aide/traceability_matrix.generated.md` — A1, as above
- `docs/aide/failure_modes.generated.json` — A1: the docstring change does not reach it
- `docs/aide/failure_modes.generated.md` — A1, as above
- `docs/aide/rules.generated.md` — A1, as above

## Testing Strategy

Module: `tests/test_237_dead_code_and_stale_comments.py`, one test per AC.

- **AC1:** import the module and assert the attribute is absent.
- **AC2:** one `build_catalogue(strict=True)` (module-scoped fixture), the
  union of tags over all `rule_evidence` pairs compared with
  `{"observed", "static"}`.
- **AC3:** register the ad-hoc rule in `segfacet.heuristics.rule._RULES`
  around one `build_catalogue(strict=False)` and restore the registry in a
  `finally`, the pattern `tests/test_223_path_aware_rule_read_attribution.py`'s
  `_static_paths` uses. Assert the set of entry paths carrying
  `(rule_id, "static")` equals
  `{"reference_delta.{label}.features.physical_volume_mm3.value"}`. As a
  precondition, assert the fresh catalogue has more than one path ending in
  `.value`, so a regression to a last-segment fallback cannot pass by the
  path's being unique.

No adversarial cases beyond these: the prose changes have no behaviour to
test, and are read by the Validation step instead.

**Existing tests to reconcile** (step 7 sweep, `grep -rn static-ambiguous
tests`): `tests/test_103_feature_catalogue.py` lines ~84, ~591, ~1324–1352,
the only hits (step 4). No test calls or imports `coverage`'s
`_find_entry_by_level_name` (`grep -rn _find_entry_by_level_name tests`
finds none).

## Validation

The validator reads each corrected passage against the code it describes and
records a one-line verdict per file.

1. **The `relabel_swap` passages** (Description 2, all eleven): each must
   read true against `compute_monotonic_consistency` and `_path_positions`
   in `src/segfacet/features/consistency.py`. None may say that the check
   now judges against a fitted curve, a reference fit or label order.
2. **The mechanism-B passages** (test_136, test_137): each must say, or be
   followed in the same passage by a dated line saying, that mechanism B has
   been path-aware since item 223.
3. **Re-sweep:** `grep -rn -i "traversal-ordered\|reference fit\|S-sorted"
   src tests` and `grep -rn static-ambiguous src tests`. Every remaining hit
   is either in an excluded file (`test_132_*`, `test_210_*`) or a dated
   line that the same passage supersedes.
4. **A1:** regenerate the catalogue into a scratch directory (step 6) and
   confirm both files equal the committed pair byte for byte.

## Dependencies

None.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether `fov.py`'s `_find_entry_by_level_name` and
  `mislabel.py`'s `_label_for_level`, two scans of `per_label` by
  `level_name`, should become one shared helper. No defect is recorded
  against either, and this item only deletes dead code.
