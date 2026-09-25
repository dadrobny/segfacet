<!-- aide-template: item 2 -->
# Item 183 — `FusePerturbation(bridged=True)` fills each column in its own order

> **Created:** 2026-09-25 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-024.md`](../queue/queue-024.md) · Item 183
> **Objectives:** G7
> **Suggested branch:** `aide/183-fuseperturbation-bridged-true-fills-each`

---

## Description

`FusePerturbation(bridged=True)` (item 176, `src/segfacet/synth/component_shape.py`)
fills the gap between an adjacent label pair, column by column along the
affine-resolved stacking axis. It decides which label is "low" **once for the
whole array**, from the two labels' mean stacking-axis index. It then fills
`max(low-label index) + 1 .. min(high-label index) - 1` in every column that
holds both labels. Two column shapes break that rule (`insights.md`, `defect`
entry of item 176, 2026-09-24):

- **Reversed column.** The pair sits in the opposite order to the global one.
  The range is empty, so the real gap is left unfilled.
- **Sandwiched column.** One label has voxels on both sides of the other. The
  range is again empty, so neither gap is filled.

The defect is dormant on the committed base: all 682 columns that hold both
labels are in global order (A2). `tests/test_176_fuse_bridged.py`'s helpers
`_facing_side` and `_column_gap` share the global-order assumption, so no
existing test would catch it.

This item decides the order **per column**, by the rule in A1. The rule gives
the same output as today on every column whose pair voxels are in one order,
so the committed corpus does not move. The two `test_176` helpers are fixed to
the same per-column rule.

**Not in scope:**

- The unbridged (default) branch, which the severity ladder applies.
- The caudal renumbering, and the `Expectation` the bridged branch returns.
- The comment above `fuse`'s `Expectation(...)` call. Item 182 rewrote it and
  it is still accurate.
- Turning `fuse`'s branch-computed `expected_rule_ids` back into literals
  (item 182's **Left open**). Since item 182, the catalogue's rule→mode map
  reads `tests/corpus/manifest.json` and no synth-source literal, so no
  consumer reads the form. The item leaves it as it is.
- Any regeneration of `tests/corpus/**`, the catalogue artifacts or the
  specification. None moves (A2).

## Acceptance Criteria

The **gap** of a column is defined in A1. The "constructed" arrays are small
two-label NIfTI images built in the test with an identity (RAS) affine, so the
stacking axis is array axis 2. They hold labels 22 and 23 only, and are fused
with `FusePerturbation(target_label=22, neighbour_label=23, bridged=True)`.

- [ ] **AC1: A reversed column is bridged in its own order.** Take a
  constructed array where every column but one holds label 22 below label 23
  along axis 2, and one column holds label 23 below label 22 with background
  between them. In the bridged output, the set of that column's indices with
  value 22 equals the union of three sets: the column's input label-22
  indices, its input label-23 indices, and the input-background indices
  strictly between its last label-23 voxel and its first label-22 voxel.
- [ ] **AC2: A sandwiched column is bridged on both sides.** Take a constructed
  array with one column that holds label 22, then background, then label 23,
  then background, then label 22 again along axis 2. In the bridged output, the
  set of that column's indices with value 22 equals the union of the column's
  input label-22 indices, its input label-23 indices, and the input-background
  indices of both gaps.
- [ ] **AC3: The committed corpus regenerates byte-identically.** Every fixture
  file and `manifest.json` that `segfacet.synth.corpus.write_corpus` writes
  into a fresh directory is byte-identical to its committed copy under
  `tests/corpus/`. The test is the existing
  `tests/test_040_synthetic_corpus.py::test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`,
  which must pass unchanged. No new test is written for this AC.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

- **A1: The per-column gap rule.** The queue line says "decide the order per
  column" but gives no rule for a sandwiched column. The rule taken here: walk
  one column along the stacking axis and keep only the voxels whose input
  value is the target or the neighbour, in index order. For each **two
  consecutive such voxels that carry different labels**, every input-background
  (0) voxel strictly between them is in the gap. Nothing else in the column is.
  Three consequences follow:
  - On a column whose pair voxels are in one order, this is exactly item 176's
    facing-end rule, including its handling of a third label: background on
    either side of the third label is filled, and the third label is kept.
  - A background run bounded by the same label on both sides (a hole inside
    one body) is never filled.
  - Only the input decides the gap. A voxel filled in one column never
    changes another column's gap.
- **A2: The committed base is unchanged.** Measured 2026-09-25 on this branch's
  base (`aide/queue-024` after item 182), on `build_clean_spine().seg_img`
  (which equals the committed `clean_control` seg):
  - The stacking axis is array axis 2. Label 23 has the lower mean index.
  - 682 columns hold both 22 and 23. All 682 are in global order: 0 are
    reversed and 0 are sandwiched.
  - The A1 rule, computed independently of the operator, fills the same 6262
    voxels over the same 682 columns as the shipped operator. The two bridge
    masks are equal.

  So `fuse_adjacent_seg.nii.gz` and the manifest's `fuse_adjacent` `detail`
  string ("filling 6262 background voxels over 682 columns") do not change.
  Because the manifest does not change, item 182's manifest-derived rule→mode
  map and the catalogue artifacts do not change either. The builder hands back
  if a regeneration differs.
- **A3: Item 182 is merged and nothing here pins it.** Item 182 changed only
  the comment above `fuse`'s `Expectation` call and the catalogue's source for
  its rule→mode map (now `tests/corpus/manifest.json`). This item edits the
  bridged fill code above that comment and leaves the comment and the
  `Expectation` as they are. It reads nothing of item 182's interface, so
  there is no dependency and no pin to re-check.

## Implementation Steps

1. In `FusePerturbation.apply`'s bridged branch in
   `src/segfacet/synth/component_shape.py`, replace the global-direction
   bridge (the `both`, `neighbour_low`, `low`/`high`, `lo`/`hi` block) with the
   A1 rule. Compute it on the same `cols = np.moveaxis(data, axis, -1)` view of
   the private copy, from input values only, before any write. A vectorised
   form, in NumPy only:
   - `pair = (cols == target) | (cols == neighbour)`.
   - The index of the previous pair voxel at or below each position:
     `np.maximum.accumulate(np.where(pair, idx, -1), axis=-1)`.
   - The index of the next pair voxel at or above each position: the same with
     `np.minimum.accumulate` over the flipped array, then flipped back.
   - Read the label at each of those indices, treating "none" as 0.
   - `bridge = (cols == 0) & (prev_label != 0) & (next_label != 0) & (prev_label != next_label)`.

   Keep `cols[bridge] = target`, `n_bridged` and `n_columns` as they are.
   No helper is added to the module, and no dependency is added.
2. Rewrite the bridged sentence of `FusePerturbation`'s class docstring
   ("every background voxel strictly between the pair's facing ends, column by
   column…") to state the A1 rule and that the order is decided per column
   (item 183). Leave the module docstring, the unbridged branch, the
   renumbering, the `Expectation` and the comment above it unchanged.
3. Do not regenerate `tests/corpus/**`. Confirm A2 by running `write_corpus`
   into a scratch directory and comparing bytes, and hand back if anything
   differs.

## Authorised paths

**May change:**

- `src/segfacet/synth/component_shape.py` — the bridged branch's gap rule and the class docstring sentence
- `tests/test_183_fuse_bridged_per_column.py` — the AC tests and the named adversarial case
- `tests/test_176_fuse_bridged.py` — replace the global-order helpers `_facing_side` and `_column_gap` with the per-column A1 rule, and update their callers

**Asserts against:**

- `tests/corpus/manifest.json` — AC3: the existing `test_040` AC16 compares a fresh regeneration with it byte for byte
- `tests/corpus/fixtures/*.nii.gz` — AC3 as above for every fixture, and `test_176` AC7 also compares the operator's output with `fuse_adjacent_seg.nii.gz`

## Testing Strategy

New module `tests/test_183_fuse_bridged_per_column.py`: one test for AC1 and one
for AC2. AC3's test is the existing `test_040` AC16 (see AC3).

- Build each constructed array with `nib.Nifti1Image(data, np.eye(4), dtype=data.dtype)`.
  Assert `si_axis(img.affine) == 2` before using axis 2.
- Each test checks its own premise before the main assertion:
  - AC1: the reversed column's order is the opposite of the order that the two
    labels' mean axis-2 index gives, and it has at least one background voxel
    between the pair.
  - AC2: the column really does hold label 22 on both sides of label 23, with
    background in each gap.

  The shipped global-direction rule leaves both columns unfilled. So each test
  fails before the fix and passes after it.
- Compute each expected index set in the test from the constructed input, with
  plain Python over the column. Do not call the operator's internals.

Adversarial case (write this one and no other):

- `no-fill-between-same-label`: a constructed column holds label 22, then
  background, then label 22 again, then background, then label 23. The first
  background run stays 0 in the bridged output, and the second becomes 22.
  This guards a per-column rule that fills from a column's first pair voxel to
  its last, which would pass AC1 and AC2 and fill a hole inside one body.

**Existing tests to reconcile:** `tests/test_176_fuse_bridged.py`.

- Replace `_facing_side` (the global mean-index side) and `_column_gap` (one
  `(lo, hi)` range from that side) with one helper. The helper returns a
  column's gap positions by the A1 rule, computed with plain Python over the
  column.
- Move its three callers to the new helper: `test_ac3_bridge_stays_inside_the_gap`,
  `test_ac4_bridge_fills_the_gap` and `test_fuse_bridge_keeps_third_label`.
- Their assertions keep their meaning. On the committed base the new helper
  returns the same positions as the old one (A2), so all three stay green.

A grep made 2026-09-25 found no other test that pins the bridged fill: the
other `bridged` hits in `tests/` are comments about `fuse_adjacent`'s case
designations.

## Dependencies

None. Item 176, which built the bridged branch, and item 182, which last edited
the same method, are both merged.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** whether a column in which a third label lies between the pair
  should be bridged at all. Filling the background on either side of the third
  label leaves the fused label split in that column. A1 keeps item 176's
  behaviour, and the committed base has no such column. Changing it would
  change what item 176's AC4 asserts.
