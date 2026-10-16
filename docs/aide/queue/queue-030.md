<!-- aide-template: queue 1 -->
# FACET — Work Queue 030

> **Created:** 2026-10-12
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> **Maintenance queue** (roadmap Stage 34) at the queue-029 boundary. It is
> served before [`queue-031.md`](queue-031.md), which opens Stage 35.
> Supersedes [`queue-029.md`](queue-029.md).

---

## Scope of this queue

This queue batches the open `defect` and `gap` entries in `insights.md` that
have a concrete fix, or a fix the owner has already decided
(`.aide/conventions.md` §1 → `insights-maintenance-queue.md`). It holds ten
items, at the cap. Entries that still need a maintainer decision, or a stage
of their own, are passed over and stay open; the queue PR body names each one.

**Prioritisation.** The items are independent and can be claimed in any
order, with one exception: items 221 and 222 both change the held-out
spline-offset estimator, so 222 lands after 221. Items 218–222 change what a
rule fires, so each re-measures the expected sets of both corpora, and
whichever lands later re-measures on top of the earlier ones. Items 223–227
change no corpus behaviour. Stage 35's reference rebuild (queue 031) reads
the estimator, so this queue goes first.

**Gate `gate-fac1` is still open.** It asks whether the one VerSe19 value
that set `mislabel.max_offset_mm = 13.0` is anatomy or a labelling artefact.
Items 221 and 222 change how that value is estimated. Each records what the
re-measured VerSe19 interior p99 is, and neither retunes `max_offset_mm`: the
threshold stays the gate's to settle.

**Build posture (`prototype`).** Every item fixes a recorded defect or gap in
shipped code, a shipped test, or shipped CI, or carries an owner decision
recorded in `insights.md` (2026-10-09 and 2026-10-12). None is preparatory.

**Numbering.** Continues at the next free integer: **218–227**.

---

## Work items

### Item 218: One inter-centroid-spacing rule for modes 2 and 6

Owner decision 2026-10-12 (insights `2026-09-22-c151` and `2026-09-22-d85a`,
with `2026-09-29-4562` a duplicate of the first): one rule over the adjacent
inter-centroid spacings serves both mode 2 (fused vertebra segments) and
mode 6 (vertebra not segmented). Since those entries were written,
`fused_label` (items 207, 211) has served mode 2 on spacing plus size, and
item 216 moved the spacings to `pairs.adjacent.spacings_mm[]` in anatomical
order. What is still missing is mode 6: one gap of about two pitches beside
labels of normal size, whether or not the labels were renumbered. This item
extends the spacing reading to mode 6, so that one rule reads both modes,
and declares the rule against mode 6 in `failure_modes.py`. The renumbered
`remove_level_relabel` case, undetected since item 143, then fires. A gap
from a label-sequence break must not fire: on `sequence_break`, spacing
alone reads 4.01 at T13 and only `fused_label`'s size gate keeps it silent
(insight `2026-10-05-a332`, now in `fused_label`'s Measured docstring), and modes
9 and 10 own that case. *Testable:* `remove_level_relabel` fires the rule
and is attributed to mode 6; `fuse_adjacent` and `fuse_separate` still fire
it as mode 2; `sequence_break` does not fire it; every corpus case's measured
firing equals its expected set, re-measured where this item moves it.

### Item 219: One check per failure mode for label order and label-set gaps

Two rules check mode 9 (labels out of order along the spine): `mislabel`'s
`ordering` (position along the label-free path, item 210) and `sequence`'s
`swap`/`shift` (item 192, sorted by `centroid_mm[2]`). The z-sort is not
robust to curvature or pose. Two rules also report mode 10 (a gap in the
label set): `coverage`'s `missing_interior` and `sequence`'s `skip` (insight
`2026-09-29-a832`). Item 210 has made the path-based check label-free, which
the entry named as the precondition. Give mode 9 to `ordering` and retire
`swap`/`shift`, or re-base them on the path position, whichever the spec
measures to keep every expected detection. Keep one detector for mode 10,
and update `failure_modes.py`'s rule declarations to match. This finishes
what the maintainer's item-106 note on `monotonic_consistency` in
`feature_docs.STATUS_OVERRIDES` asks for ("Should be wired into the
sequence rule directly; …"). The note reads as an open action that has
been closed since item 132 (insight `2026-10-09-9de3`). Append the owner's
line of 2026-10-12, dated, after the note, and keep the item-106
transcript as written: "Done: order is judged along the label-free path by
`mislabel`, items 210/219." *Testable:* each
of modes 9 and 10 is declared against exactly one detector; a curved or
reclined spine, correctly labelled, fires no ordering finding; every corpus
case that expected a mode-9 or mode-10 detection still has one; every corpus
case's measured firing equals its expected set, re-measured where this item
moves it; the `monotonic_consistency` override carries the owner's dated
line after the unchanged item-106 note.

### Item 220: A collapsed label set no longer passes silently

When two labels share an exact centroid, Stage 3 is absent:
`features.stage3_unavailable` records why, every rule that reads `stage3`
returns early, and `detect_overlaps` sees no overlapping voxels. So no
finding fires and the verdict is pass (insight `2026-10-09-c1b7`; Stage 30
D3 lists it as proposed mode 13). Add a rule that reads
`stage3_unavailable` and fires a finding naming the reason, and give that
key its `FEATURE_DOCS` entry. Mode 13's specification stays at its current
rung unless the rule's declaration requires otherwise. *Testable:* a label
map with two labels on one centroid yields the finding and is not a pass;
a record with Stage 3 present fires nothing new; the regenerated catalogue
lists `stage3_unavailable` with a doc entry, and its drift test agrees; every
corpus case's measured firing is unchanged.

### Item 221: Held-out spline offset with every outlier withheld

The held-out spline-offset estimator withholds only the single dominant
outlier per refit. With two or more displaced levels, a clean vertebra can
read a larger offset than an offender: measured clean 31.96 mm against
displaced 19.31 mm on the two-opposite-displacements case (insight
`2026-10-09-ddc5` part (i), wanted next by owner decision 2026-10-09).
Withhold every level above an outlier cutoff when fitting the reference
curve. Re-measure the VerSe19 interior p99 the threshold was set from, and
record it beside `gate-fac1` without changing `mislabel.max_offset_mm`.
*Testable:* on the two-opposite-displacements case both displaced levels
read larger offsets than every clean level; a single-outlier case reads as
before; the re-measured VerSe19 interior p99 is recorded with the commit it
was measured at; every corpus case's measured firing equals its expected set,
re-measured where this item moves it.

### Item 222: Held-out spline offset at the ends of the sequence

Item 123 excludes sequence-terminal vertebrae from the held-out offset
outright, yet terminal vertebrae are 41 of the 45 VerSe19 outliers at or
above 6 mm (insight `2026-10-09-ddc5` part (ii), wanted next by owner
decision 2026-10-09). The entry names three candidates: a separately
calibrated terminal threshold, an estimator that knows it is extrapolating,
or a curvature model that does not need both neighbours. Choose one by
measurement on VerSe19 and record why. `mislabel.max_offset_mm` for interior
levels stays as `gate-fac1` leaves it. Runs after item 221. *Testable:* a
terminal vertebra displaced on a synthetic case is judged and flagged; the
VerSe19 terminal levels' false-positive count under the chosen method is
recorded with the commit it was measured at; every corpus case's measured
firing equals its expected set, re-measured where this item moves it.

### Item 223: Path-aware rule-read attribution in the catalogue

The catalogue's static scan attributes a string-key read to a leaf path only
when exactly one leaf path ends in that key. Since item 215, five features
share the last segment `percentile_rank` / `value` under `reference_delta`,
so the `reference_delta` rule's reads are attributed to none of them, and
"Read by ≥1 rule" in `traceability_matrix.generated.md` reads 51 where it
was 54 (insight `2026-10-06-1935`). Attribute a read by the path the rule
indexes, not only by its last segment. *Testable:* the `reference_delta`
rule's reads are attributed to the five `physical_volume_mm3` paths; the
regenerated traceability matrix's "Read by ≥1 rule" count is at least 54
and its drift test agrees; a key shared by several paths and read through
none of them is still left unattributed.

### Item 224: Platform-sensitive comparisons tolerant, determinism checks exact

Two shipped tests compare at the wrong strictness. `tests/test_098_stray_components.py`
compares whole findings against `_PRE_098_GOLDEN_VERDICT_AND_FINDINGS`,
whose reason strings carry rendered floats such as `14.6 mm` and
`fragmentation_index=0.52579`, so a last-digit platform difference fails it
(insight `2026-10-05-87c9`). Compare the rendered numbers with a numeric
tolerance and everything else exactly. `tests/test_082_verse_build_recipe.py::test_adv_determinism_two_builds_produce_equal_parsed_artifacts`
compares two builds from one session with `reports_close`, where every
sibling determinism test asserts byte-identity, so nondeterminism in
`segfacet build-reference` passes unnoticed (insight `2026-10-09-bc75`).
Tighten it to byte-identity. *Testable:* test_098 passes on a finding whose
rendered float differs in its last digit and fails on a changed verdict or
a changed finding; test_082's determinism test fails when the two builds
differ by one byte.

### Item 225: Three test guards that see only half of what they guard

Close three blind spots in shipped test guards. `tests/committed_artifact_guard.py`
flags an exact `==` only on a direct `.read_bytes()` / `.read_text()` /
sha256 read of a committed path, so `json.loads(p.read_text())['x'] == fresh`
passes unflagged (insight `2026-10-05-aac0`). `tests/test_155_corpus_case_kind.py`'s
`_zero_comparisons` scans function bodies only, so a tracked comparison in
a decorator, a default value or an annotation is not reported (insight
`2026-10-05-90c4`). The `asserted by` column of
`docs/aide/golden-decision-table.md` is checked one way only: every named
test exists, but a test that reads the golden and is not named passes. The
one live golden is read by twelve modules and its row names four (insight
`2026-10-09-7e82`). Add the reverse check, and match the shared-attribute
idioms such as `.GOLDEN_PATH`. *Testable:* each guard reports a planted
instance of the shape it missed; the decision table's row for
`report_format_contract.json` names every test module that reads it; the
live tree passes all three guards.

### Item 226: Two owner-decided retirements

Owner decisions of 2026-10-09. Retire `src/segfacet/features/sagittal_projection.py`
(item 021), which nothing reaches but its own test, and delete that test,
`tests/test_021_sagittal_projection.py` (insight `2026-10-09-2c9f`). Retire
the `scope-check` job in `.github/workflows/ci.yml`: under `[git] mode =
"auto-merge"` no `aide/NNN-` head ref ever becomes a PR, so the job always
matches nothing. State in `CLAUDE.md` (Branching) that the in-loop validator
running `aide scope` is the per-item scope gate (insight `2026-10-09-ed9b`).
*Testable:* no module imports `sagittal_projection` and the suite passes
without it; generated docs that listed it are regenerated, and their drift
tests agree; the workflow has no `scope-check` job; `CLAUDE.md` no longer
describes a green `item scope check` as a signal.

### Item 227: Stale descriptions of shipped behaviour, and the path-position end clamp

Three small corrections. `src/segfacet/synth/identity_ordering_alignment.py`
(the `relabel_swap` expectation detail) and `src/segfacet/synth/corpus.py`
(lines 43–46) still describe the monotonicity reference as a curve fitted
in geometric traversal order; since item 210 the check fits no curve and
reads position along a label-free path (insight `2026-10-05-ffc6`).
`src/segfacet/eval/severity_ladder.py` says `crop_depth` is "pinned at the
corpus's 5", in its module docstring, a comment and a `LadderSpec`
rationale. Since item 212 no corpus case carries `crop_depth` (insight
`2026-10-05-7f33`). `features/consistency.py`'s `_path_positions` divides
naively accumulated lengths by a `sum()` that Python 3.12+ compensates, so
the path-end label's `u` can read just above 1.0 there (insight
`2026-10-06-934c`). Clamp `u` to [0, 1], or normalise by the final
accumulated length. *Testable:* the three descriptions match the shipped
behaviour; `u` lies in [0, 1] for a path whose segment lengths make naive
accumulation overshoot the compensated sum; every corpus case's measured
firing is unchanged.
