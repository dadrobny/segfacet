<!-- aide-template: item 3 -->
# Item 227 — Stale descriptions of shipped behaviour, and path positions kept in [0, 1]

> **Created:** 2026-10-13 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 227
> **Objectives:** G6, G7
> **Suggested branch:** `aide/227-stale-descriptions-path-positions`

---

## Description

Three small corrections to shipped code. None of them changes what any rule
fires on Python 3.11, the only interpreter CI runs.

**1. The `relabel_swap` description still credits a fitted curve.** Two
places say the monotonicity check judges against "a curve fitted in geometric
traversal order":

- the `detail` string of the `Expectation` that
  `RelabelSwapPerturbation.apply` returns, in
  `src/segfacet/synth/identity_ordering_alignment.py`;
- the module docstring of `src/segfacet/synth/corpus.py`, the paragraph on
  the mode-9 `relabel_swap` case.

Item 132 introduced that curve, and item 210 (2026-10-05) replaced it.
`compute_monotonic_consistency` now fits no curve. It reads each label's `u`,
its position along the longest path of the centroids' minimum spanning tree,
a path built without reading labels, and judges the supplied order against
`u` (insight `2026-10-05-ffc6`). The `detail` string is copied into the
committed `tests/corpus/manifest.json`, so that file is regenerated.

**2. The `crop_at_border` severity ladder credits the corpus with its
`crop_depth`.** `src/segfacet/eval/severity_ladder.py` says `crop_depth` is
"pinned at the corpus's 5" in three places: the module docstring's
`crop_at_border` bullet, the comment in `_crop_at_border_ladder`, and that
function's `LadderSpec` `rationale`. Since item 212 no corpus case carries
`crop_depth`, because the corpus case moved to `crop_fov` (insight
`2026-10-05-7f33`). The value 5 stays, as the ladder's own constant. Only
the claim that the corpus sets it is removed.

**3. The path-end `u` can leave [0, 1] on Python 3.12 and later.** In
`src/segfacet/features/consistency.py`, `_path_positions` builds the path
arc lengths `cum[]` by adding segment lengths one at a time. It then divides
by `total = float(sum(seg_len))`. On Python 3.11 `sum()` adds the same way,
so `total == cum[-1]` exactly. From Python 3.12, `sum()` of floats is
compensated, so `total` can be one ulp below `cum[-1]`. The label at the path
end then reads `u = 1.0000000000000002` on the forward branch, or
`1 - u = -2.2e-16` on the backward branch (insight `2026-10-06-934c`). The
fix is to normalise by the final accumulated length (`total = cum[-1]`).
Every projected arc length `s` is at most `cum[-1]` under IEEE rounding, so
every `u` lies in [0, 1], and the end reads exactly 1.0 (or 0.0 on the
backward branch). The result no longer depends on how `sum()` rounds.

**Not in scope:**

- a Python 3.12 CI leg (maintainer decision, recorded under insight
  `2026-10-06-934c` on 2026-10-07);
- a clamp (see Decisions);
- the stale comments in `tests/test_039_*` and `tests/test_040_*` that
  repeat description 1 (captured as insight `2026-10-13-cc62`);
- any change to `crop_depth`'s value or to any rung.

## Acceptance Criteria

- [ ] **AC1: Every path position lies in [0, 1] when `sum()` is compensated.**
  The test stands in for Python 3.12 by patching the name `sum` in
  `segfacet.features.consistency` to `math.fsum` (an exactly rounded sum).
  It calls `_path_positions` on the five-centroid `OVERSHOOT_SPINE` fixture
  from the Testing Strategy, supplied in the order listed. For every
  returned value `u`, `0.0 <= u <= 1.0`. Before this item, the fifth value
  is `1.0000000000000002`.
- [ ] **AC2: Path positions do not depend on how `sum()` rounds.** On the
  same `OVERSHOOT_SPINE` fixture, the list `_path_positions` returns with
  `sum` patched to `math.fsum` equals, element for element with `==`, the
  list it returns unpatched. Before this item, four of the five values
  differ.
  - *Correction (2026-10-14):* re-measured on `aide/queue-030` HEAD
    `94364da8` (items 218–226 merged), three of the five `OVERSHOOT_SPINE`
    values differ between the patched and unpatched runs (indices 1, 2 and
    4), not four. Four of five differ on `BACKWARD_OVERSHOOT_SPINE`. The
    criterion itself, element-wise equality, is unchanged. Neither AC1 nor
    AC2 is satisfied or contradicted by the merged items, because
    `src/segfacet/features/consistency.py` is unchanged since this spec was
    written.

The three wording fixes have no criterion (see Decisions). The validator
reads them under Validation. The existing test_040 test that compares a fresh
manifest byte for byte with the committed file
(`test_040_synthetic_corpus.py`, the `write_corpus` determinism test, which
asserts `manifest_path1.read_bytes() == MANIFEST_PATH.read_bytes()`) fails
until the regenerated manifest carries the new `detail`.

## Assumptions

- **A1 (decided: normalise, do not clamp).** The orchestrator took the
  recommended default, and the human was told and did not object.
  `_path_positions` divides by `cum[-1]`. No clamp is added, because once
  every `s <= cum[-1]` a clamp could never fire.
- **A2 (the fix is a no-op on Python 3.11).** On 3.11, `sum(seg_len)`
  starts from the integer 0 and adds left to right, exactly as `cum[]` is
  built, so `float(sum(seg_len)) == cum[-1]` bit for bit. This was measured
  on the project venv on 2026-10-13, where the unpatched `OVERSHOOT_SPINE`
  output reads `[0.0, 0.2449506347037949, 0.4865309333321359,
  0.7407204414427608, 1.0]`. So on 3.11 every `u`, every `path_u` in a
  report, and every corpus case's firing is unchanged. The existing corpus
  and eval suites keep asserting the firing, so the item writes no new
  criterion for it.
  - **Re-checked 2026-10-14** on `aide/queue-030` HEAD `94364da8`, items
    218–226 merged: agrees. `src/segfacet/features/consistency.py` is
    unchanged since this spec was written (`_path_positions` still sets
    `total = float(sum(seg_len))`, line 192), and the unpatched
    `OVERSHOOT_SPINE` output re-measured on the project venv (Python
    3.11.15) is the same five values.
- **A3 (the order of `u` is preserved: the interface items 218 and 219
  read).** Item 218's A5 reads `path_u` only to order labels. Item 219's A5
  keeps `pairs.adjacent.non_monotonic_pairs[]` meaning "`path_u` does not
  advance". This item preserves both:
  - On Python 3.11 the output is bit-identical (A2).
  - On 3.12 and later, every `u` is divided by `cum[-1]` instead of a
    `total` at most a few ulps smaller. Dividing by one positive constant
    never reverses two values, so if `s_i <= s_j` then `u_i <= u_j`, and the
    `1 - s/L` branch holds the same way. The direction choice reads `s`,
    not `u`, so it is unchanged.
  - **Correction to the brief:** on 3.12 the end label is not the only
    value that moves. Interior values can change in the last ulp. In the
    measured fixture, three interior values moved, for example
    `0.24495063470379494` became `0.2449506347037949`.
  - A strict order could only become a tie for two `s` values within about
    one ulp of each other, which happens the same way under either divisor.
  - **Re-checked 2026-10-14** (same base): the interface agrees. Item 218's
    `centroid_spacing` (`src/segfacet/heuristics/centroid_spacing.py`) reads
    `path_u` only as a sort key, `rows.sort(key=lambda r: (r[0], r[1]))`,
    ties broken by label. `pairs.adjacent.non_monotonic_pairs[]` is still
    built from `u_values[i] >= u_values[i + 1]` in
    `compute_monotonic_consistency`, and item 219's readers (`mislabel`'s
    ordering detector, `sequence`'s transitional detector) read the pair
    list, never `u`. Item 222's terminal spline offset reads no path
    position. **Correction to the third bullet:** re-measured, the patched
    forward output moves two interior values (indices 1 and 2,
    `0.24495063470379494` and `0.48653093333213593`) plus the end value.
    Index 3 reads `0.7407204414427608` either way. So two interior values
    move, not three. The bullet's conclusion, that interior values can
    change in the last ulp, stands.
- **A4 (the replacement wording).** These replacements are defaults the
  builder may reword, provided each passage reads true against the code:
  - **`relabel_swap` `detail`:** the check reads each label's position
    along a label-free path through the centroids (item 210), never the
    ordering under test, so the swap reads out of order and MislabelRule's
    ordering detector fires directly.
  - **`corpus.py` docstring:** `relabel_swap` became
    `detection == "pipeline"` with item 132 (2026-08-31). Since item 210 the
    monotonicity check reads position along the label-free path rather than
    a fitted curve.
  - **`severity_ladder.py`:** `crop_depth` is held at 5 on every rung, as
    the ladder's own constant (no corpus case carries `crop_depth` since
    item 212). `fov_clipped_label_count` is invariant to it.

  The `detail` must still contain "mislabel" (case-insensitive). It must
  not contain "reconstructed" or "Not surfaced by plain run_qc", because
  `tests/test_132_monotonicity_against_traversal_order.py` lines 476–479
  assert all three.

  **Re-checked 2026-10-14** (same base): the wording defaults agree, and
  the line numbers are corrected.
  - The stale passages are unchanged: the `detail` at
    `identity_ordering_alignment.py` lines 423–429, the `corpus.py`
    docstring lines 44–48, and `severity_ladder.py` lines 69–70, 842 and
    866. The committed manifest still carries the old `detail` (line 173).
    Outside `docs/aide/`'s own records, a grep for "geometric traversal
    order" over `src`, `tests` and `docs` finds only those two source files
    and the manifest, so no other generated artifact carries the text.
  - Item 219 edited `SequenceBreakPerturbation` in the same module, a
    separate hunk, and dropped its "unlike ``displace`` and
    ``relabel_swap``" aside. Nothing there contradicts the defaults above.
  - **Correction:** test_132's three token checks are now lines 475–477,
    in `test_ac17_committed_manifest_mode4_detail_names_mislabel_not_pipeline_miss`.
    Item 219's edits above them moved them. The three checks are unchanged.
- **A5 (a test on Python 3.11 needs the patch).** On 3.11 no input
  reproduces the defect, because `sum()` and the `cum[]` loop round
  identically. The tests patch the module-global `sum` with
  `monkeypatch.setattr(consistency, "sum", math.fsum, raising=False)`.
  `math.fsum` is exactly rounded. It is not bit-identical to 3.12's
  compensated `sum()`, but it overshoots the same way, and that is the
  defect. The patch has no effect once the code stops calling `sum()`.
  - **Re-checked 2026-10-14** (same base): agrees. `_path_positions` still
    calls the module-global `sum`. With it patched to `math.fsum`, the
    forward fifth value re-measured `1.0000000000000002` and the backward
    second value `-2.220446049250313e-16`.

## Implementation Steps

1. In `src/segfacet/features/consistency.py`, `_path_positions`:
   - Build `cum[]` first.
   - Set `total = cum[-1]` and drop the `sum()` call.
   - Keep the `total == 0.0` early return, all zeros, after `cum[]` is
     built.
   - Update the docstring's `u = s / L` sentence to say `L` is the final
     accumulated path length.
   - Nothing else changes. No helper is added and no dependency.
2. In `src/segfacet/synth/identity_ordering_alignment.py`, rewrite only the
   `detail` string in `RelabelSwapPerturbation.apply`'s `Expectation` (A4).
   Item 219 edits `SequenceBreakPerturbation` in the same file, a different
   hunk.
3. In `src/segfacet/synth/corpus.py`, rewrite the `relabel_swap` sentences
   of the module docstring (the paragraph from "The mode-9 ``relabel_swap``
   case").
4. In `src/segfacet/eval/severity_ladder.py`, rewrite three passages and
   leave every `crop_depth: 5` literal as it is:
   - the module docstring's `crop_at_border` bullet;
   - the comment at the top of `_crop_at_border_ladder`;
   - that function's `rationale` string.
5. Regenerate the committed corpus:
   `.venv/bin/python -m segfacet.synth.corpus`. In the corpus itself, the
   only expected diff is the `relabel_swap` `detail` in
   `tests/corpus/manifest.json`. The fixtures should be byte-identical, so
   `git status` shows no `.nii.gz` change. If another queue-030 item has
   already landed a manifest change, regenerate on top of it.
6. Regenerate the corpus sheet:
   `.venv/bin/python -m segfacet.synth.corpus_sheet`. Item 222 uses the same
   command. test_178 AC7 requires the digest embedded in
   `docs/aide/corpus_sheet.png` to equal sha256(manifest bytes + fixtures).
   Step 5 changes the manifest bytes, so the PNG changes too, even though
   nothing the sheet renders has moved.

## Authorised paths

**May change:**

- `src/segfacet/features/consistency.py` — normalise by `cum[-1]` and correct the docstring
- `src/segfacet/synth/identity_ordering_alignment.py` — the `relabel_swap` `detail` string
- `src/segfacet/synth/corpus.py` — the module docstring's `relabel_swap` paragraph
- `src/segfacet/eval/severity_ladder.py` — the three `crop_depth` passages
- `tests/corpus/manifest.json` — regenerated to carry the new `detail`
- `docs/aide/corpus_sheet.png` — regenerated, because its embedded digest covers the manifest bytes (test_178 AC7, step 6)
- `tests/test_227_path_position_normalisation.py` — this item's tests
- `tests/test_220_collapsed_labels_rule.py` — only if red. Item 220 pins the manifest, which this item regenerates after it (Dependencies). It is expected to stay unedited, because no firing moves.

**Asserts against:**

None.

## Testing Strategy

Module: `tests/test_227_path_position_normalisation.py`. Both tests patch
`sum` as A5 says, and build `LabelCentroid` objects with
`centroid_voxel == centroid_mm` from this fixture, in this order:

```
OVERSHOOT_SPINE = [
    (0.0, 0.0, 0.0),
    (2.0665311091502883, 1.5477264176418153, 28.411431616616902),
    (0.6200316109080684, 1.6153747458534662, 56.510114365625185),
    (2.322823145116704, 0.4352511023270309, 86.0420534486723),
    (2.8231153818468915, 2.8839284134990417, 116.1357905650201),
]
```

The centroids are spaced 28–31 mm apart along S with a few mm of lateral
drift. Off-axis points matter: when the points lie exactly on one axis, the
segment lengths add exactly and never overshoot. Measured before this item
with the patch: `[0.0, 0.24495063470379494, 0.48653093333213593,
0.7407204414427608, 1.0000000000000002]`.

- AC1 and AC2: one test each, as written.
- **backward-branch:** the fix must cover the `1 - s/L` return as well as
  the forward one. A fix applied to one return, or a clamp at the top only,
  leaves the backward path start at `-2.2e-16`. Fixture
  `BACKWARD_OVERSHOOT_SPINE`, supplied in this order:
  ```
  [(-1.5098163182215227, -3.9720566376064594, 84.46705062824944),
   (0.0, 0.0, 0.0),
   (0.40939765999365907, -2.1731235016702133, 22.465964361582984),
   (-1.867495223422111, -2.765824254685681, 51.82482120939568),
   (-0.05574349640587961, -5.663996879209332, 114.24421384989117)]
  ```
  Measured before this item with the patch, the second value is
  `-2.220446049250313e-16`. Assert that every value is in [0, 1] with the
  patch.
- **zero-length-path:** moving the zero-length guard while switching to
  `cum[-1]` can turn a degenerate path into a `ZeroDivisionError` or NaNs.
  With three identical centroids, `_path_positions` returns
  `[0.0, 0.0, 0.0]`.

**No existing tests to reconcile.** No test calls `_path_positions` or
patches `sum`. The output does not change on 3.11 (A2). The only test that
reads the `relabel_swap` `detail` is test_132 (lines 476–479), and A4 keeps
all three of its token checks true. The stale comments in
`tests/test_039_*` (line 401) and `tests/test_040_*` (lines 102 and 314) are
left alone (insight `2026-10-13-cc62`).

**Re-checked 2026-10-14** (`aide/queue-030` HEAD `94364da8`): still no test
calls `_path_positions` or patches `sum`, so there is still nothing to
reconcile. Some line numbers moved. test_132's token checks are now lines
475–477 (A4). The stale comment in `tests/test_039_*` is now line 413, not
401. The `tests/test_040_*` comments are still at lines 102 and 314. The
manifest byte check is
`test_ac16_regeneration_is_byte_identical_across_runs_and_vs_committed`
(assertion at line 425).

## Validation

The validator reads each corrected passage against the code it describes,
and records a one-line verdict per passage.

1. **`relabel_swap` `detail` and the `corpus.py` docstring.** Each must
   describe what `compute_monotonic_consistency` and `_path_positions`
   actually do: position along the label-free MST longest path, with no
   fitted curve. Neither may describe a curve, a fit, or a "geometric
   traversal order".
2. **`severity_ladder.py`, all three passages.** `crop_depth` must be
   presented as the ladder's own constant. Run
   `grep -n crop_depth src/segfacet/synth/corpus.py` and confirm no corpus
   recipe sets it.
3. **The regenerated manifest.** Run `git diff <base> -- tests/corpus/` on
   the branch. The `relabel_swap` `detail` must be the only changed text it
   shows that this item introduced, and it must equal the string in
   `identity_ordering_alignment.py` with labels 21 and 22 substituted.
   Outside `tests/corpus/`, the other regenerated artefact this item
   expects is `docs/aide/corpus_sheet.png` (step 6). The validator confirms
   that it changed, and that test_178 AC7 passes on the regenerated pair.

## Dependencies

- Item 220: its Asserts against pins `tests/corpus/manifest.json` ("no
  case's firing may move"), and this item regenerates that file. The only
  change is the `relabel_swap` `detail` text. No expected set moves, so
  item 220's corpus-wide firing test is not expected to go red. Its test file
  is listed under May change only so the ordered pair is declared, which is
  what `aide check --queue` requires, and it should stay unedited. This item
  lands after item 220, the same order the queue's other manifest-
  regenerating siblings declare.

**Downstream:**

- Item 218 (A5) reads `path_u` only for its order. This item preserves the
  order (A3).
- Item 219 edits `SequenceBreakPerturbation` in the same synth module and
  also regenerates `tests/corpus/manifest.json`. Whichever of the two lands
  later regenerates on top of the other. This item does not pin the
  manifest.
- **Re-checked 2026-10-14** (`aide/queue-030` HEAD `94364da8`): item 220
  is merged, so the declared order holds. Items 218 and 219 have also
  landed manifest changes, so step 5 regenerates on top of both. Item 222
  did not touch `tests/corpus/manifest.json`: its new `spline_offset`
  expectations are the `expected_firing` tuples of `sequence_break` and
  `split_own_label` in `src/segfacet/failure_modes.py`, not this case.
  `relabel_swap`'s manifest expectation is still `mislabel` on {21, 22}.
  Item 219 reduced its plain `run_qc` findings from two to one (test_132
  AC13) and its `expected_firing` to `("mislabel",)`. `aide check --queue
  030` reports no error.

## Decisions & Trade-offs

To be updated during implementation.

- **Normalise, not clamp (2026-10-13).** Dividing by `cum[-1]` keeps every
  `u` in [0, 1] and also makes interior values independent of the
  interpreter's `sum()`. A clamp would fix only the end value and leave 3.11
  and 3.12 disagreeing in the last ulp.
- **No criterion for the wording fixes (2026-10-13).** Any automated check
  of prose is a token check that wording can satisfy while still being
  wrong (§1 → items). The validator reads the passages under Validation
  instead, and test_040's byte-identity check keeps the regenerated manifest
  in step with the source string.
- **Left open:** whether CI should gain a Python 3.12+ leg. Without one,
  nothing exercises the compensated `sum()` path for real, and AC1 and AC2
  stand in through the patch. The maintainer declined the leg on 2026-10-07
  (insight `2026-10-06-934c`).
