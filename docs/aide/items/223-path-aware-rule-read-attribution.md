<!-- aide-template: item 3 -->
# Item 223 — Path-aware rule-read attribution in the catalogue

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 223
> **Objectives:** G4, G8
> **Suggested branch:** `aide/223-path-aware-rule-read-attribution`

---

## Description

The feature catalogue (`src/segfacet/catalogue.py`) works out which rule
reads which feature in two ways. Mechanism A traces the reads a rule makes at
run time over the driver records. Mechanism B scans each rule module's source
for string keys. Today mechanism B ignores the path a key is read through. It
takes every string used as a subscript or as `.get(...)`'s first argument
anywhere in the rule's module file and matches it against the last segment of
the catalogue's leaf paths. It attributes the read only when exactly one leaf
path ends in that key (item 110).

That rule makes two errors:

- **It misses genuine reads.** Since item 215, five features under
  `reference_delta.{label}.features.<f>` share the last segments `value`,
  `percentile_rank` and `robust_z`. The `reference_delta` rule reads `value`
  and `percentile_rank` for every feature named in a label's
  `out_of_range_features[]` (`heuristics/reference_delta.py`, the
  out-of-range detector). Neither scan attributes those reads, because the
  catalogue's placeholder driver has an empty `out_of_range_features[]`, so
  mechanism A never sees the branch run. "Read by >=1 rule" in
  `docs/aide/traceability_matrix.generated.md` fell from 54 to 51 at item
  215, and reads 50 since item 216 (insight `2026-10-06-1935`).
- **It invents reads.** `intensity_reference_delta` reads the block
  `record["intensity_reference_delta"]`, which no driver realises. The
  last-segment match still attributes four `reference_delta.*` paths to it:
  `lower_pct`, `upper_pct`, `{label}.distribution_distance` and
  `{label}.out_of_range_features[]`. Its declaration has to carry them as
  `not-read`, a role whose only purpose is to excuse such guesses.

This item replaces mechanism B with a **path-aware** scan, applied to every
string-key read. The scan follows the record from the rule's own `evaluate`
parameter, through variables, loops and helper calls, to the path each read
indexes. It attributes the read to the catalogue leaf paths that path names,
and to nothing else. A read whose path it cannot resolve attributes nothing.
Each rule's `consumed_paths` declaration is updated to match what the new
scan attributes, so `path_classification_conflicts()` stays empty. The
committed catalogue and traceability documents are regenerated.

**Not in scope:**

- No rule's `evaluate` body, threshold, finding or firing changes. Only
  `mode_declaration.consumed_paths` entries and comments change in rule
  modules.
- Mechanisms A, C and D are unchanged. So is the driver-record set: the
  `reference_delta` placeholder keeps its empty `out_of_range_features[]`,
  because that branch is exactly the kind mechanism B exists to catch.
- `segfacet.observed_range`'s own last-segment matching (item 124) is a
  different mechanism and is unchanged.
- The `not-read` role stays in `PATH_ROLES`. Whether to retire it is left
  open (Decisions).

## Acceptance Criteria

- [ ] **AC1: The reference_delta rule's out-of-range reads are attributed.**
  For each of the ten leaf paths
  `reference_delta.{label}.features.<f>.value` and
  `reference_delta.{label}.features.<f>.percentile_rank`, with `<f>` each of
  `extent_x_mm`, `extent_y_mm`, `extent_z_mm`, `physical_volume_mm3` and
  `spline_offset_mm`, the entry of `build_catalogue(strict=True)` has
  `"reference_delta"` in its `consuming_rules`.
- [ ] **AC2: A read through a block no leaf path lies under stays
  unattributed.** No entry of `build_catalogue(strict=True)` whose path
  starts with `reference_delta.` has `"intensity_reference_delta"` in its
  `consuming_rules`. The rule reads these keys through
  `record["intensity_reference_delta"]`, and no catalogued leaf path lies
  under that block.
- [ ] **AC3: Reads made through an imported helper are attributed to the
  rule that calls it.** `coverage` passes its record to
  `segfacet.heuristics.fov.derive_fov_coverage`. For each of
  `per_label.{label}.level_name`,
  `per_label.{label}.geometry.touches_superior` and
  `per_label.{label}.geometry.touches_inferior`, the entry of
  `build_catalogue(strict=True)` has `"coverage"` in its `consuming_rules`.
- [ ] **AC4: The committed traceability matrix agrees with a fresh build.**
  `docs/aide/traceability_matrix.generated.json`, parsed, equals a fresh
  `segfacet.traceability` build of the live tree. That makes its
  `features.read_by_rule` the live count of catalogue entries with a
  non-empty `consuming_rules`. There is no numeric floor (A3). The measured
  count is recorded under Validation.

## Assumptions

- **A1 (owner, 2026-10-12): the queue's "five `physical_volume_mm3` paths"
  is stale wording.** The `reference_delta` rule reads `value` and
  `percentile_rank` for whichever feature `out_of_range_features[]` names,
  so the paths it indexes are those ten, across all five features (AC1).
  `physical_volume_mm3` has six leaves under `reference_delta`, not five, and
  only before item 215 was it the one feature catalogued there. The original
  queue text stands in `queue-030.md` as the record.
- **A2 (owner, 2026-10-12): path-awareness covers every string-key read**,
  not only keys whose last segment is ambiguous. The owner chose this so
  that `intensity_reference_delta`'s last-segment false positives are
  removed and its `consumed_paths` trimmed to match. **If any rule loses a
  (rule, path) pair it genuinely reads, the scan is wrong.** The builder
  hands the item back rather than reclassifying the loss away.
- **A3 (owner, 2026-10-12): no numeric floor on "Read by >=1 rule".** Items
  218, 219, 220 and 222 in this queue also move the count. The ACs name the
  paths, and the existing drift tests carry the count (AC4). The count is
  measured and recorded, not asserted. Spec-time measurement: **50 → 60** at
  commit `9438bc4`, whose `src/` and `tests/` are identical to `2a1491d`.
- **A4: measured before/after diff of attributed (rule, path) pairs.**
  Measured at `9438bc4` by a scratch prototype of the scan specified under
  Implementation Steps, run against the live driver records. It is a spec-time
  measurement and a lower bound, so the builder re-measures it on the branch.
  - **Mechanism B alone: 62 → 82 pairs.**
  - **Lost: 4 pairs, all from `intensity_reference_delta`.** They are
    `reference_delta.lower_pct`, `reference_delta.upper_pct`,
    `reference_delta.{label}.distribution_distance` and
    `reference_delta.{label}.out_of_range_features[]`. The rule reads these
    keys through `record["intensity_reference_delta"]`, so the losses are the
    false positives the owner asked to remove (A2).
  - **Gained: 20 pairs.**
    - `reference_delta`: the ten paths of AC1, plus
      `reference_delta.{label}.available` and the five
      `reference_delta.{label}.features.<f>.robust_z` paths. The last six were
      already attributed through mechanism A.
    - `intensity`: `case.intensity.available`,
      `per_label.{label}.intensity.first_order.median` and `.std`. All three
      were already attributed through mechanism A.
    - `border`: `case.sequence.present_levels[]`, and
      `per_label.{label}.geometry.touches_superior` and `.touches_inferior`.
      These are read inside `fov.derive_fov_coverage`, and all three were
      already attributed through mechanism A.
    - `coverage`: `per_label.{label}.geometry.touches_superior` and
      `.touches_inferior`. These are read inside `fov.derive_fov_coverage`,
      which `coverage` calls only in its opt-in expected-span check. The
      default config never runs that check, so mechanism A never sees it.
  - **Catalogue `consuming_rules`, mechanisms A and B together: 87 → 95
    pairs.**
    - Lost: the same 4 `intensity_reference_delta` pairs.
    - Gained: 12 pairs, the ten of AC1 and the two `coverage` touch flags.
    - No path stops being read by some rule, and ten paths start being read
      (AC1). That is the 50 → 60 of A3.
  - **Reads the scan cannot resolve**, each of whose key names a catalogue
    leaf:
    - `border`: `label`, `per_label`.
    - `coverage`: `label`, `level_name` and `per_label`. The `level_name`
      read is in `coverage.py`'s own `_find_entry_by_level_name`, a copy with
      no caller. The live call path goes through `fov.py`'s copy, which the
      scan does resolve (AC3).
    - `fragmentation`: `component_count`, `largest_component_fraction`.

    Each of these pairs stays attributed through another resolved read or
    through mechanism A. Under the old scan, this coverage pair existed only
    because of the uncalled copy. Without following calls into `fov.py`
    (AC3), `coverage` would lose `per_label.{label}.level_name`, a pair it
    genuinely reads.
- **A5: what the scan resolves.** The builder implements this, and the
  adversarial cases test it.
  - **Root.** The registered rule class's own `evaluate` method. Its first
    parameter after `self` is the record, at the empty path. The scan seeds
    no other function by its name.
  - **What a resolved read indexes.**
    - A string-constant subscript `x["k"]`, or `x.get("k", ...)`, extends
      `x`'s path by `k`.
    - A non-constant subscript or `.get` argument extends it by a one-segment
      wildcard.
    - `x[a:b]` keeps `x`'s path.
  - **Bindings.**
    - A plain assignment, an annotated assignment or a walrus binds the name
      to the value's path. A value of the form `a or b` or `a if c else b`
      gives the union of the paths of `a` and `b`.
    - `for v in x` binds `v` to the path of `x`'s elements, written `x[]`.
      The same holds for `sorted(x)`, `list(x)` and `reversed(x)`.
    - `for k, v in x.items()`, and `for v in x.values()`, bind `v` to `x`
      plus a wildcard.
    - `for i, v in enumerate(x)` binds `v` to `x`'s elements.
    - `dict(x)`, `list(x)`, `sorted(x)` and `tuple(x)` keep `x`'s path.
  - **Calls.**
    - A call to a function or method of the same module, via a bare name or
      `self.`/`cls.`, binds the callee's parameters to the argument paths,
      positional and keyword.
    - A call to a function imported with `from segfacet.<module> import
      <name>` does the same, scanning the callee's own module.
    - A callee's `return` value carries its path back to the caller.
    - All of this iterates to a fixed point.
  - **Matching.** A resolved read is matched against the catalogue leaf
    paths after the existing normalisation:
    - A wildcard right after a `per_label` segment becomes `{label}`.
      `reference_delta.per_label.<wildcard>` becomes `reference_delta.{label}`,
      as `normalise_leaf_path` collapses it.
    - Any other wildcard matches exactly one segment.
    - A read path `p` also matches the scalar-list leaf `p[]`.
    - Item 216 D18's container exclusion is kept: a path that is the direct
      parent of another leaf is never attributed.
  - **Unresolved reads.** A read whose base the scan cannot trace to the
    record contributes nothing. There is no last-segment fallback.
- **A6: roles for the changed pairs.** These follow each module's existing
  precedent (`heuristics/rule.py` `PATH_ROLES`).
  - `reference_delta`'s ten new paths are `bookkeeping`. They are message
    interpolation into the out-of-range finding, as `lower_pct` and
    `upper_pct` already are, and the rule is mode-less (item 193).
  - `coverage`'s two touch flags are `bookkeeping`. They gate the
    border-aware exemption in the opt-in expected-span check, as its
    `per_label.{label}.level_name` already does. They are never mode-10
    evidence.
  - Three `per_label` entries, in `reference_delta`, `intensity_reference_delta`
    and `intensity`, move from `not-read` to `bookkeeping`. Their reasons say
    "mechanism B last-path-segment match only". Under the path-aware scan
    each rule demonstrably indexes `record["per_label"]`, so `not-read` would
    be false. `bookkeeping` ("containers iterated") is the role every other
    rule already gives that read. Owner-approved at the queue-030 spec
    review (2026-10-13). The cross-spec review found no sibling in queue 030
    that declares `per_label` as `not-read`.
- **A7: siblings scanned on landing.** Item 218 renames `fused_label` to
  `centroid_spacing`. Item 219 retires `sequence`'s swap, shift and skip
  detectors. Item 220 adds `collapsed_labels`. Item 222 adds
  `curve.terminal_offset_mm`. Whichever of these lands after this item is
  scanned by the path-aware mechanism. `path_classification_conflicts()`
  reports any mismatch between that rule's declaration and what the scan
  attributes, and the later-landing item regenerates the shared documents.
  No ordering is declared, because none of them pins anything this item
  changes.

## Implementation Steps

1. **`src/segfacet/catalogue.py`, mechanism B.** In `build_catalogue`,
   replace the last-segment loop (the block under `# Mechanism B: static AST
   scan`) with the scan A5 describes. It is one private helper returning, per
   rule, the set of resolved read paths. Match those paths against the
   existing `by_last_segment`-feeding field set: `leaf_union` minus the D18
   `containers`. Add each match as `attributions[path][rule_id]` with the
   existing tag `"static"`.
   - Reuse `normalise_leaf_path` for the `per_label` collapse, with a digit
     sentinel in the wildcard's place.
   - Keep the `try/except` that skips a rule whose module source cannot be
     read.
   - Use `ast` from the standard library only. Add no dependency.
   - Delete `_scan_literal_string_keys` and `_rule_module_literal_keys` once
     nothing calls them. No module outside `catalogue.py` does at
     `9438bc4`. `_last_segment` stays, because mechanism D uses it.
2. **`src/segfacet/catalogue.py`, prose.** Rewrite the module docstring's
   "B. Static AST scan" paragraph and the inline comments of the replaced
   block, so they describe path-aware resolution and its no-fallback rule.
   Name this item and the insight. Leave the item-110 history readable as
   history.
3. **`src/segfacet/heuristics/reference_delta.py`.** In `consumed_paths`:
   - Add ten `ConsumedPath(role="bookkeeping")` entries for AC1's paths,
     with the reason "message interpolation: printed in the out-of-range
     finding; the firing decision is out_of_range_features[]'s membership".
   - Change `per_label` from `not-read` to `bookkeeping`, with a true reason
     (A6).
4. **`src/segfacet/heuristics/intensity_reference_delta.py`.** Remove the
   four `ConsumedPath` entries A4 lists as lost, and change `per_label` to
   `bookkeeping` (A6). Keep the `mode_less_reason` as written: it already
   says the block is not realised.
5. **`src/segfacet/heuristics/intensity.py`.** Change `per_label` from
   `not-read` to `bookkeeping` (A6).
6. **`src/segfacet/heuristics/coverage.py`.** Add `ConsumedPath(role=
   "bookkeeping")` entries for `per_label.{label}.geometry.touches_superior`
   and `.touches_inferior`, with a gate reason (A6). Change nothing else in
   the module.
7. **`src/segfacet/heuristics/rule.py`.** Reword the `PATH_ROLES` comment's
   `not-read` bullet so it no longer says the catalogue attributes such a
   path "by mechanism B's last-path-segment name match". Keep the role and
   the observed-refutes-it sentence.
8. **Regenerate** with `.venv/bin/python -m segfacet.catalogue` and
   `.venv/bin/python -m segfacet.traceability`.
9. **Reconcile the existing tests** listed under Testing Strategy, each with
   a dated `item 223 (2026-10-12)` note beside the moved literal, as earlier
   reconciliations in those files do. Re-measure every literal from the
   regenerated catalogue. Do not copy the spec-time numbers.

## Authorised paths

**May change:**

- `src/segfacet/catalogue.py` — the path-aware mechanism B and its prose (steps 1–2).
- `src/segfacet/heuristics/reference_delta.py` — `consumed_paths` only (step 3).
- `src/segfacet/heuristics/intensity_reference_delta.py` — `consumed_paths` only (step 4).
- `src/segfacet/heuristics/intensity.py` — one `consumed_paths` role (step 5).
- `src/segfacet/heuristics/coverage.py` — two `consumed_paths` entries (step 6).
- `src/segfacet/heuristics/rule.py` — the `not-read` comment (step 7).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 8).
- `docs/aide/feature_catalogue.generated.md` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.json` — regenerated (step 8).
- `docs/aide/traceability_matrix.generated.md` — regenerated (step 8).
- `tests/test_223_path_aware_rule_read_attribution.py` — this item's tests.
- `tests/test_136_rule_mode_declarations.py` — reconcile `stayed_empty`.
- `tests/test_137_mode_less_rule_disposition.py` — reconcile the evidence-bucket distribution.
- `tests/test_148_per_path_mode_attribution.py` — reconcile AC10's `not-read` floor and AC9's comment.

**Asserts against:**

None.

## Testing Strategy

Module: `tests/test_223_path_aware_rule_read_attribution.py`. It builds the
catalogue once per module through `segfacet.catalogue.build_catalogue(strict=True)`,
the producer, never a parsed copy of the committed JSON.

- **AC1–AC3:** one test each. AC1 and AC3 are parametrised over their
  named paths.
- **AC4:** covered by the existing
  `tests/test_138_traceability_matrix.py::test_ac4_committed_json_parses_to_a_fresh_build`,
  with `::test_ac21_feature_direction_counts_match_a_fresh_catalogue` tying
  `read_by_rule` to the live catalogue. The test-writer adds no test for
  AC4.

**Adversarial cases.** Each registers an ad-hoc `Rule` subclass defined in
the test module, and restores `_RULES` from a snapshot in `finally`, as
`test_103`'s raising-rule case does. Mechanism A also runs an ad-hoc rule
over the driver records, so each case asserts on the
`(rule_id, "static")` pairs in `rule_evidence`, not on `consuming_rules`.

- `unresolved-read-no-fallback`: a rule whose `evaluate` reads `"lower_pct"`
  from a local dict not derived from the record. It must not be attributed
  `reference_delta.lower_pct`. This guards against a silent last-segment
  fallback bringing back the false positives A2 removes.
- `seed-is-the-registered-class-only`: two ad-hoc rule classes in one
  module. Only the second reads `record["reference_delta"]["lower_pct"]`.
  The first is attributed no `reference_delta.*` path. This guards against
  a scan that seeds every function named `evaluate` in a module and so
  credits one class with another's reads.
- `wildcard-is-one-segment`: a rule reading
  `record["reference_delta"]["per_label"][k]["features"][name]["value"]`.
  It is attributed exactly the five `…features.<f>.value` paths and no
  `percentile_rank` or `robust_z` path. This guards against a wildcard that
  swallows more than one segment, or matches on the last segment alone.

**Existing guards this item must keep green, with no new test:**

- `path_classification_conflicts() == ()` at
  `tests/test_148_per_path_mode_attribution.py:378` and
  `tests/test_193_reference_delta_mode_less.py:109`. They catch any
  declaration left out of step with the new scan, including a lost
  slice-through or `enumerate` read in `neighbour_contact`, whose
  `component_contacts[].neighbour_label` pair only mechanism B attributes.
- The catalogue's committed-versus-fresh test,
  `tests/test_103_feature_catalogue.py::test_ac19_committed_docs_match_fresh_regeneration`.

**Existing tests to reconcile.** Spec-time numbers; re-measure each.

- `tests/test_136_rule_mode_declarations.py`: `stayed_empty == 102` → 92.
  The ten AC1 paths leave the `()` bucket.
- `tests/test_137_mode_less_rule_disposition.py`, the `mode_evidence`
  distribution:
  - `()` 102 → 92.
  - `("rule_mode_less", "rule_bookkeeping")` 11 → 26: +10 from AC1, +4
    from the paths losing `intensity_reference_delta`'s `not-read`, +1 for
    `per_label`.
  - `("rule_mode_less", "rule_bookkeeping", "rule_not_read")` 5 → 0,
    leaving the dict.
  - `("rule_mode_less", "rule_condition_signal")` 7 → 5.
  - New bucket `("rule_mode_less", "rule_bookkeeping",
    "rule_condition_signal")`: 2, the touch flags.
  - `len(entries)`, `mode1_count`, `mode2_count` and `mode16_count` do not
    move.
- `tests/test_148_per_path_mode_attribution.py`:
  - `test_ac10_evidence_gains_bookkeeping_and_not_read_tags_correctly`
    asserts `checked_not_read > 0`. After A6 no shipped declaration uses
    `not-read`, so that floor goes, with a dated note. The per-entry
    equivalence it checks stays.
  - The comment in `test_ac9…` (around line 566) calls
    `reference_delta.lower_pct` a path "shared with a mechanism-B-only
    not-read declarer". Reword it, because its assertion still holds with
    one declarer.
- Items 218, 219 and 220 move these same literals. Whichever lands later
  re-measures on top.

## Validation

1. On the claim branch, run `.venv/bin/python -m segfacet.catalogue` and
   `.venv/bin/python -m segfacet.traceability`. Then `git diff --stat`
   must list no change. The committed documents are already the fresh
   ones.
2. Read the line `Total catalogued paths: N. Read by >=1 rule: M.` in
   `docs/aide/traceability_matrix.generated.md`. Record `M` and the commit
   hash in Decisions & Trade-offs. The spec-time figure is 60 (A3). Any
   difference is explained by a sibling that has landed on the base since.
3. Compare `consuming_rules` per path between `git show
   <base>:docs/aide/feature_catalogue.generated.json` and the branch's copy.
   Every (rule, path) pair gained or lost must appear in A4's list, or
   belong to a sibling rule that landed since. Any other loss is a hand-back
   (A2).

## Dependencies

None.

## Decisions & Trade-offs

- **Scan shape (item 223).** `catalogue._PathScan` is a flow-insensitive,
  union-on-rebind abstract interpreter over the rule's `evaluate`
  (paths as token tuples: key, `"[]"` iteration, wildcard). A same-class
  `self.`/`cls.` call, a same-module call and a `from segfacet.<m> import f`
  call are followed context-sensitively, memoised on the bound argument
  paths, with a recursion guard. Calls with no traced argument are skipped.
  A local list built by `.append(...)` remembers its elements' paths, so
  `reference_delta`'s `normalised` list of `(label, key, entry)` tuples still
  resolves; tuple targets over a non-tuple value take the union (an
  over-approximation that only adds paths under the record).
- **Measured on the branch (base `6e3de213`).** Catalogue `consuming_rules`
  pairs: lost exactly A4's four `intensity_reference_delta` pairs; gained
  exactly A4's twelve (AC1's ten and `coverage`'s two touch flags). The
  traceability line reads `Total catalogued paths: 160. Read by >=1 rule: 64.`
  (spec-time 60; the difference is the sibling items 218-222 landed since).
  `path_classification_conflicts()` and `rule_declaration_conflicts()` are
  empty.
- **Declarations.** `consumed_paths` tuples must be ascending by path, so the
  ten new `reference_delta` and two new `coverage` entries sit in sorted
  position, not appended.

- **Left open:** whether to retire the `not-read` role from `PATH_ROLES`.
  After this item no shipped declaration uses it, because the path-aware
  scan attributes only paths a rule indexes. The role is kept because
  `path_classification_conflicts()` and its adversarial tests still exercise
  it. Retiring it is a vocabulary change, outside a fix to attribution.
- Fix round 1 (review): `build_catalogue` now catches only `OSError`,
  `SyntaxError` and `TypeError` around the mechanism B scan (an unreadable
  or unparsable rule source; `_ModuleInfo` raises `OSError` when no source
  file is found). A scan bug propagates instead of silently dropping a
  rule's static evidence. Call-following in `_PathScan._call` is capped at
  depth 20 so a helper recursing on a growing path terminates
  deterministically, attributing nothing past the cap. The scan's
  unresolved constructs (nested defs, lambdas, comprehensions, module-attribute
  calls, relative imports, inherited helpers) and its flow-insensitive
  over-approximation are listed in the `catalogue.py` docstring. When a
  module holds several same-named classes, `run_rule` prefers the one at the
  rule class's own source line.
