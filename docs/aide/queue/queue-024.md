<!-- aide-template: queue 1 -->
# FACET — Work Queue 024

> **Created:** 2026-09-25
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> **Maintenance queue** at the queue-023 boundary. It is served before
> [`queue-025.md`](queue-025.md), which is Stage 33's D3. Supersedes
> [`queue-023.md`](queue-023.md).

---

## Scope of this queue

This queue batches the open `defect` and `gap` entries in `insights.md` that
no Stage 33 deliverable absorbs (`.aide/conventions.md` §1 →
`insights-maintenance-queue.md`). It holds six items. Entries that a Stage 33
deliverable fills are queued in the stage queue instead. That covers the
`CANONICAL_ORDER` T13 defect, the stale `default_config.yaml` and
`mislabel.py` values, and the 2026-09-22 review decisions.

**Prioritisation.** Item 182 leads, because queue-025 changes rule→mode
declarations, and the catalogue's corpus-derived map would report false
conflicts against them. The other five items are independent of one another
and can be claimed in any order.

**Build posture (`prototype`).** Each item fixes a recorded defect in shipped
code, or a blind spot in a guard that already exists. None is preparatory.

**Numbering.** Continues at the next free integer: **180–185**.

---

## Work items

### Item 180: `segfacet evaluate` reports an input error instead of a traceback

`src/segfacet/cli.py`'s `_handle_evaluate` calls `evaluate_cohort` outside
every `try`. So a `FacetInputError` raised inside it ends in a traceback from
`eval.overlap.compute_overlap`, for example on a cohort that pairs a candidate
and a GT of different array shapes (`insights.md`, item 175, 2026-09-24).
Catch it the way the `run` handler does. *Testable:* a two-case cohort with
mismatched shapes exits 1, with the error message on stderr and no traceback.

### Item 181: Reference-backed Stage 6 and item-090 tests made discriminating

On the lordotic base, two tests pass whether or not the perturbation they test
did anything. `test_049`'s
`test_ac11_size_distorting_perturbation_flags_label_22_out_of_range` and its
`..._fires_reference_delta_finding_on_label_22` sibling are the first: the
unperturbed `clean_control` already reads label 22 out of range against
`bundled_default_reference()`. `test_090`'s
`test_ac14_mode6_crop_at_border_fires_bounds_on_label_22_against_verse_v1` is
the second: `bounds` fires on every label of the unperturbed control against
`bundled_production_reference()` (`insights.md`, item 175, 2026-09-24, two
entries). Each test gains a control arm, meaning the same assertion on the
unperturbed case must fail. If no perturbation separates the two arms on this
base, the test is rewritten or retired, with the reason recorded. *Testable:*
each rewritten test fails when its perturbation is replaced by the identity.

### Item 182: The catalogue's corpus-derived rule→mode map read from the committed cases

`catalogue._scan_synth_rule_mode_map` builds its map from literal
`Expectation(failure_mode=…, expected_rule_ids=…)` calls in
`src/segfacet/synth/*.py`, not from the committed manifests' cases. Two
consequences follow. An operator branch that no corpus case applies still
designates rule→mode pairs, and a designation that is not a literal drops out
silently. Measured 2026-09-24: `fuse`'s unbridged literal yields two false
`rule_declaration_conflicts` (`insights.md`, item 176, 2026-09-24). Derive the
map from the cases that are actually committed. *Testable:* an `Expectation`
literal on an operator branch that no case applies adds no pair. The two
false `fuse` conflicts are gone. Dropping a committed case's expected rule
removes its pair.

### Item 183: `FusePerturbation(bridged=True)` fills each column in its own order

The bridged branch decides which label is "low" once, from the two labels'
mean stacking-axis index. It then fills `max(low)+1 .. min(high)` in every
column. So in a column where the order is locally reversed, or where one
label sits on both sides of the other, the range is empty and a real gap is
left unfilled (`insights.md`, item 176, 2026-09-24). The defect is dormant on
the committed base, because all 682 bridged columns are in global order. Decide
the order per column. `tests/test_176_fuse_bridged.py`'s helpers share the
global-order assumption, so they are fixed too. *Testable:* a constructed
two-label array with one reversed column is bridged in that column. The
committed corpus regenerates byte-identically.

### Item 184: `test_155`'s zero-comparison scan covers every comparison shape

`tests/test_155_corpus_case_kind.py`'s `_zero_comparisons` AST scan flags only
single-op `Eq`/`NotEq`/`Is`/`IsNot` comparisons, and `not`-truthiness, against
a `failure_mode` access. So an `in (0,)` or `in {0}` membership test, a chained
comparison, or a `bool(...)`-wrapped truthiness test on the same access passes
undetected (`insights.md`, item 155, 2026-09-16). Widen the scan to those
shapes. *Testable:* each of the three shapes, planted in a scanned source
string, is reported. The live tree reports nothing.

### Item 185: `committed_artifact_guard` resolves the `dirname(abspath(__file__))` root

`tests/committed_artifact_guard.py`'s resolver has no branch for the
`os.path.dirname(os.path.abspath(__file__))` root idiom, which is live in four
test modules (019, 121, 122, 131). It is the same defect class as item 158's
two fixes, and it is missing from the docstring's "Still skipped in silence"
list (`insights.md`, item 158, 2026-09-17). Resolve the idiom. *Testable:* a
planted fresh-vs-committed comparison rooted through the idiom is flagged. The
live tree is still clean.
