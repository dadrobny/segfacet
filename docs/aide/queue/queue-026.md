<!-- aide-template: queue 1 -->
# FACET — Work Queue 026

> **Created:** 2026-09-29
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> **Maintenance queue** at the queue-025 boundary. It is served before
> [`queue-027.md`](queue-027.md), which closes Stage 33. Supersedes
> [`queue-025.md`](queue-025.md).

---

## Scope of this queue

This queue batches the open `defect` and `gap` entries in `insights.md` that
no Stage 33 deliverable absorbs (`.aide/conventions.md` §1 →
`insights-maintenance-queue.md`). It holds four items. The entries that
Stage 33's D4–D6 fill are queued in the stage queue instead: the bar
checker's condition 2, the severity-ladder constants and the rule table.

**Prioritisation.** The four items are independent of one another and can be
claimed in any order. Item 198 changes what a rule fires, so it re-measures
the corpus's expected sets. The other three change no corpus behaviour.

**Build posture (`prototype`).** Items 196–198 fix recorded defects in shipped
code, or a blind spot in a guard that already exists. Item 199 clears
`aide check` warnings that the engine 2.20.1 update raised. None is
preparatory.

**Numbering.** Continues at the next free integer: **196–199**.

---

## Work items

### Item 196: Stale prose after items 189, 190 and 195 brought up to date

Four comments or docstrings still describe corpus cases or constants that
later items changed. No test reads any of them.

- `tests/test_120_leave_one_out_offset.py`'s
  `test_ac24_corpus_pipeline_detection_is_nine_of_ten` docstring files
  records under "1 (displace, fragment)" and "0 (crop)". Since item 189,
  `displace` is a `displaced_vertebra` condition case, and since item 190,
  condition cases have their own buckets (insight 2026-09-28-15eb).
- `tests/committed_artifact_guard.py`'s `ALLOWLIST` reason for
  `tests/corpus/094_pre_migration_snapshot.json` says "285 float leaves".
  The committed snapshot held 342 on 2026-09-28 (insight 2026-09-28-ebb9).
- `src/segfacet/heuristics/neighbour_contact.py`'s design-decision comment
  cites `force_overlap`'s labels 20/21 as a live example, and item 195
  removed that case (insight 2026-09-28-0b6c).
- `src/segfacet/synth/golden.py`'s cross-platform-tolerance comment lists
  `force_overlap` among the asymmetric-geometry cases (insight
  2026-09-28-922d).

Each number or example a sentence quotes is re-measured on the live corpus
when the sentence is rewritten, not carried over. *Testable:* none of the four
passages names `force_overlap`, the retired buckets or the 285 count. The
guard's float-leaf count matches a recursive count of the committed snapshot,
and the suite is green.

### Item 197: `test_155`'s zero-comparison scan covers truthiness and ordering

`tests/test_155_corpus_case_kind.py`'s `_zero_comparisons` AST scan was
widened by item 184. It still misses two shapes (insight 2026-09-25-31b7).
The first is bare truthiness of a `failure_mode` access in a test position:
an `if` or `while` test, a ternary test, an `and`/`or` operand, or a
comprehension `if`. The second is an ordering comparison against 0, such as
`> 0` or `>= 1`. One live hit exists:
`tests/test_138_traceability_matrix.py` selects pipeline cases with
`... and case.get("failure_mode")`. That reads "failure_mode truthy means a
failure case", which is the double meaning item 155 retired in favour of
`corpus_case_kind`. Widen the scan, and rewrite the live hit to read
`corpus_case_kind`. *Testable:* each planted shape is reported. The live tree
reports nothing, and `test_138`'s case selection is unchanged.

### Item 198: `mislabel`'s `ordering` detector judges order along the expected sequence

`mislabel`'s `ordering` detector reads
`stage3.monotonic_consistency.non_monotonic_pairs[]`. That list is judged in
ascending integer label order. So a correctly labelled transitional or
coccygeal level misreads as out of order, the way `sequence` did before item
192 (insight 2026-09-28-d6ed). Measured 2026-09-28: the clean control
relabelled T13, L1–L4, with T13 correctly above L1, fires on (20, 21),
(21, 22) and (22, 23). Relabelled L4, L5, S1, S2, `Cocc`, with the coccyx
correctly last, it fires on (27, 29). Item 192 re-based only `sequence`,
because reordering the centroid sequence also moves the spline fit and every
Stage 3 feature. Judge the order along item 186's expected sequence. The spec
decides whether that happens inside the rule or in the feature, and records
which Stage 3 features move if it is the feature. *Testable:* both relabelled
controls fire no `ordering` finding. `relabel_swap` still fires. Every corpus
case's expected set is re-measured, and the specificity ratchet is green.

### Item 199: Positional gate and insight citations in the records rewritten to IDs

About 60 citations of human gates by their position in the table, and 9
citations of insights by their position in the inbox, remain in merged item
specs, in closed queues 020 and 021, and in
`docs/aide/failure-mode-taxonomy-handover.md`. `aide check` warns on each
(insight 2026-09-29-a6d6). Gate positions have been append-only, so the gate
citations can be rewritten to IDs by script. Insight positions predate
archives, so each of the 9 is read before an ID is chosen. The four hits on
line 5 of items 040, 041, 043 and 058 are false positives. There, "gates" is a
verb followed by an item number. Each is reworded so that it no longer reads
as a gate citation. A citation inside a quotation of what `aide check` printed at the
time is kept as quoted, and its ID is added beside it. *Testable:*
`aide check` reports no positional gate or insight citation. Each rewritten
insight citation resolves to the entry that the surrounding text describes.
