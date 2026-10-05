<!-- aide-template: queue 1 -->
# FACET — Work Queue 028

> **Created:** 2026-10-03
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> **Maintenance queue** at the queue-027 boundary. It is served before
> [`queue-029.md`](queue-029.md), which opens Stage 27. Supersedes
> [`queue-027.md`](queue-027.md).

---

## Scope of this queue

This queue batches the open `defect`, `gap` and `automation` entries in
`insights.md` that have a concrete, already-decided fix
(`.aide/conventions.md` §1 → `insights-maintenance-queue.md`). It holds five
items. Entries that still need a maintainer decision, or a stage of their own,
are passed over and stay open (named in the queue PR body).

**Prioritisation.** The five items are independent and can be claimed in any
order. Items 210, 211 and 212 each change what a rule fires or what a corpus
case holds, so each re-measures the expected sets of both corpora. Whichever
lands second re-measures on top of the first. Items 209 and 213 change no
corpus behaviour.

**Build posture (`prototype`).** Items 209–212 fix recorded defects in shipped
code or a shipped fixture, or answer maintainer feedback recorded at the
`gate-0133` sign-off and after queue 027. Item 213 is CI hygiene the maintainer
directed on 2026-10-03, and finishes a change already half-landed on `main`.
None is preparatory.

**Numbering.** Continues at the next free integer: **209–213**.

---

## Work items

### Item 209: `test_155`'s tracked-shape scan: nested scopes and value defaults

`tests/test_155_corpus_case_kind.py::_zero_comparisons` reports a tracked
shape inside a nested function twice: the outer scope walks into the inner
`def`, and the inner `def` is then scanned again (insight 2026-09-29-dcbd).
It still misses a walrus test (`if (m := c['failure_mode'])`), a `match`
guard and `>= 1.0`. The and/or-operand rule also reports a tracked access
used as a value default (`m = c.get("failure_mode") or 0`), so a legitimate
default would trip AC12 (insight 2026-09-29-4706). Scan each scope once,
cover the three missed shapes, and let a value default through. *Testable:* a
nested-function violation is reported exactly once; the walrus, `match`-guard
and `>= 1.0` shapes are each reported; `x = c.get("failure_mode") or 0` is
not; the live tree still passes.

### Item 210: The monotonicity check's reference curve made label-free and direction-robust

`segfacet.features.consistency._traversal_order` (item 132) orders the points
for `compute_monotonic_consistency`'s reference spline by S (z) coordinate.
Wherever z is not monotone along the spine (curved sacrum or coccyx, lying or
flexed pose, unusual orientation) the curve zigzags and every `u` it yields is
unreliable (insight 2026-09-29-5d37). It also takes the walk's direction from
the judged order's first-to-last net advance, so a misplaced endpoint reverses
the walk and `mislabel`'s `ordering` names the correctly ordered neighbours:
on `sequence_break` it fires on (L1,L2), (L2,L3), (L3,L4) instead of (T13, L1)
(insight 2026-09-29-ab9d). Order the curve's points by a label-free geometric
chain through the centroids (nearest-neighbour chain, or the longest path
through their minimum spanning tree). Keep the label order only as the
expectation the `u` sequence is judged against, and take the direction with
fewer inversions, as `sequence` has done since item 192. Mode 4's
reconstruction handler,
`segfacet.synth.regression._recon_monotonic_true_spatial_order`, still passes
ascending-integer centroids and must pass what the pipeline passes since item
198 (insight 2026-09-29-dac4). *Testable:* on `sequence_break`, `ordering`
names {20, 28}; a curved spine whose z reverses yields monotone `u` for a
correctly labelled case; the reconstruction handler and
`pipeline.extract_feature_record` hand the check the same order; every
corpus case's measured firing equals its expected set, re-measured where this
item moves it.

### Item 211: `fused_label` judges the pair of adjacent spacings together

`fused_label` (item 207, mode 2) takes `spacing_ratio` as the *smaller* of the
two spacings adjacent to a label. A fused label whose spacing is normal on one
side and doubled on the other does not fire. The extra distance a fused label
adds can be split between the two sides in any proportion, and the test must
hold across centroid conventions (whole label vs body, or another segmenter's).
So it judges the pair together, for example their sum against twice the
pitch (maintainer feedback at `gate-0133`, insight 2026-10-02-5d97). The same
module sorts `per_label` keys with `key=int` and raises `ValueError` on a
non-integer key, though its docstring says a malformed record is not judged
(insight 2026-09-30-5763). *Testable:* a large label with one normal and one
doubled adjacent spacing fires; the detector still fires on `fuse_adjacent`
and `fuse_separate` and on nothing else in either corpus; a record with a
non-integer `per_label` key returns no finding and does not raise; mode 2
still meets bar conditions 1–5 live.

### Item 212: `crop_at_border` re-authored as a true anterior crop

`CropAtBorderPerturbation` (`src/segfacet/synth/coverage_border_overlap.py`)
translates label 22 toward the anterior face by margin + 5 voxels and clips
the overhang. The committed fixture therefore also carries an 18.0 mm spline
offset on an interior label, above the 13.0 mm threshold (the `displace` case
reads 14.6 mm). The maintainer prefers a true in-plane volume crop (insight
2026-10-03-ab8d). Item 175's `crop_fov` operator with `face="anterior"` does
that, but because the body sits inside the face the cut must be deeper to
reach it. Re-author the case on that operator at the shallowest depth that
cuts the body, re-measure its ladder home in `test_153` and the roughly 60
test pins on its content (item 175 D2's count). The recipe comments in
`src/segfacet/synth/corpus.py` that still call `split` "mode 3 … sub-type (a)"
and `split_own_label` "sub-type (b)" are corrected in the same pass (insight
2026-09-30-7db1). *Testable:* the committed `crop_at_border` is produced by
`crop_fov` with `face="anterior"`; no interior label of it carries a spline
offset above the threshold; its measured firing equals its expected set; the
`corpus.py` recipe comments name `split` as mode 2 and carry no sub-type
lettering.

### Item 213: The Windows CI leg runs a pinned OS-sensitive subset

`test (windows-latest)` is the workflow's critical path: 25.5 min against
Ubuntu's 16.5 min on run 37042666246, running work Windows cannot refute
(insight 2026-10-03-5252). The first half (`--ignore=.aide/scripts/tests` on
the Windows leg, `--durations=30` on both) landed with the 2026-10-03
maintenance branch. This item decides what *needs* Windows — path handling,
newline and `.gitattributes` byte-identity, subprocess and CLI behaviour —
and runs only that list there. Ubuntu keeps the whole suite. A test pins the
list, the way `aide-loop`'s `tests/test_ci_shards.py` pins its `UBUNTU_ONLY`
list, so a new OS-sensitive module cannot silently miss Windows. *Testable:*
the Windows leg's pytest invocation names exactly the pinned list; a test
fails when a module reading or writing committed bytes, spawning a
subprocess or invoking the CLI is absent from it; Ubuntu's invocation is
unchanged.
