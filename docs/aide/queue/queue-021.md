<!-- aide-template: queue 1 -->
# FACET — Work Queue 021

> **Created:** 2026-09-16
> Step 4 of the AIDE loop · derived from [`../vision.md`](../vision.md),
> [`../roadmap.md`](../roadmap.md), and [`../progress.md`](../progress.md) ·
> each item below is specced into [`../items/`](../items/) and tracked in
> `../progress.md` (queue state is derived there, never declared here).
> Opens and closes **Stage 31**; supersedes [`queue-020.md`](queue-020.md)
> (Stage 30, complete at item 151).

---

## Scope of this queue

Delivers roadmap **Stage 31 — Post-Sign-Off Maintenance: follow-ups,
prerequisite defects, engine update** (G7, G8): ten items covering deliverables
**D2–D7**, at `loop.queue_cap = 10`. The queue stops at the stage boundary —
Stage 32 (Selected-Mode Refinement) is next in the pinned run order
(**31 → 32 → 20 (remainder) → 27 → 21 → 16**) and nothing is drawn from it here.

Stage 31 clears the ground item 150's re-organisation left behind, so that
Stage 32 refines a mode against artifacts that agree with the signed-off
catalogue rather than against retired ids. **It changes no failure mode's
definition, adds no rule and moves no expected firing set** — those are Stage
32's, and an item here that finds a rule wrong records the finding in
[`../insights.md`](../insights.md) and hands back.

### What D0 and D1 already delivered — this queue starts from them

The stage's first two deliverables are process work, not items, and both landed
before this queue was planned. Items below start from their result, not from the
roadmap's prose:

- **D0 — AIDE engine 1.37.0 → 1.52.1** (PR #76, merged 2026-09-16), through
  CLAUDE.md's framework-update workflow. Two consequences items here inherit:
  `aide progress set NNN` now hard-errors on an item with no `progress.md`
  reference, and every living document carries an `<!-- aide-template: … -->`
  marker. The permanently-skipping `aide/queue-018` base-ref tests
  (`test_135`'s AC26/AC28, `test_128`'s diff test) were retired in that pass —
  item 159 confirms rather than re-does it.
- **D1 — `vision.md` §6 re-issued as v4** (PR #77, branch
  `docs/vision-v4-section-6`), accepted at human gate 6 on 2026-09-16 as a
  gate-approved draft. §6 now carries principles plus a pointer to
  `segfacet.failure_modes.SPECIFICATION` and **no numbered mode list**, the five
  observability classes, the FOV-truncation condition as a first-class concept,
  and the corrected single-rank-descent evidence-rungs example. That PR merges
  back to back with this queue; item 152 is the code-side half of it and is the
  only item that depends on the new §6 text.

### Why this queue is the maintenance batch, and no separate one is written

A maintenance queue exists to get insight-derived fixes merged ahead of a stage
that does not contain them (`.aide/conventions.md` §1 →
`insights-maintenance-queue.md`). Here the stage **is** the fixes: D4, D5 and D6
are, in the roadmap's own words, the triage of the open `defect` and `gap`
entries in the surfaces Stage 32 edits. Splitting them off would produce two
queues over one set of entries and would strand D7 — the stage validation that
records the triage counts — behind a batch it is meant to measure. So
**queue-021 is the maintenance batch**, and every entry it absorbs is ticked
with the item number it became, exactly as a maintenance queue would.

### The open inbox at this queue's planning — 41 entries

Read with `python .aide/scripts/aide.py insights list --open` on 2026-09-16: 12
`defect`, 17 `gap`, 11 `knowledge`, 1 `framework`. The 11 `knowledge` and 1
`framework` entries are not this step's to route (§1 → `insights-triage.md`) and
go through `/aide-review-insights`; several of them are nonetheless the
**located record** an item below starts from, and are named there.

Of the 29 `defect`/`gap` entries, 16 are absorbed by items 152–159 and ticked;
13 stay open by decision, and item 160's triage gives each a dated pointer or a
dated reason. The two the roadmap names explicitly as **re-homed, not fixed** —
the CI dev-tooling lockfile (2026-09-01) and the per-grid-point re-extraction in
`evaluate --calibrate` (2026-09-01) — are among them: both are packaging or
production-performance decisions with no bearing on what Stage 32 refines.

### Scope fence for the whole queue

**No mode content changes.** No item below edits a `ModeSpec`'s definition,
discriminator, mechanism, severity, observability or authored status, adds or
removes a mode, adds a rule, or moves a corpus case's `expected_firing`. Items
153 and 154 re-key and re-measure the **eval harness**, which is a separate
cohort-level surface from the per-case rule engine; a re-measurement that
contradicts a signed-off mode is a finding, recorded and handed back.

**Root documents are not edited from inside an item.**
[`../vision.md`](../vision.md) and [`../roadmap.md`](../roadmap.md) change only
through their own loop entry point and a reviewed PR. This bites twice here:
`roadmap.md`'s two "**Yes, always**" completeness rows (lines 919–920) are a
standing counterexample to the shipped matrix and are **handed back to the next
roadmap revision** by item 156, not fixed in it; and `progress.md`'s restatement
of them (lines 967–968) is a dated 2026-08-11 record of what that roadmap said,
which is kept as written.

**Byte-reproducible committed artifacts.** Items 153–157 regenerate committed
generated documents (`docs/aide/failure_modes.generated.*`,
`traceability_matrix.generated.*`, `feature_catalogue.generated.md`, the corpus
manifests). Any new committed text fixture must be written with `\n`
(`write_bytes`, not `write_text`) and pinned `text eol=lf` in
[`../../../.gitattributes`](../../../.gitattributes) — CLAUDE.md's Gotchas; the
pin is not optional and `aide check`'s `.gitattributes` lint must stay clean.

**Human gates.** Gate 6 (the v4 §6 re-issue) is approved and its Blocks cell is
narrowed to item **152**, the only item that reads the new text. Gates 1 and 2
(real segmenter output; access to the curated challenging-case data) block Stage
16 only, and no Stage 16 work is in this queue. **Item 157 carries a decision
that is the maintainer's, not an item's** — see its entry: it is raised at this
queue's review, not inside the item.

**Prioritisation.** Item **152** lands first: it is the only item gated on PR #77
and it removes a seed-conformance surface three later items would otherwise have
to preserve. Items **153 → 154** are then one ordered pair — the ladders and
cross-mode constants can only be re-measured once the harness is keyed by the
specification's ids — and item 154 absorbs Stage 20's deferred item 141
(the mode-1 ladder base), which is re-derived for what mode 1 now means or
recorded as having no ladder. Items **155**, **156**, **157** and **158** are
independent of each other and of 153/154, and may be claimed in any order.
Item **159** is independent but should follow 152, which retires three of the
test modules it also touches. Item **160** runs after every item that ticks an
entry, so that the counts it records are final; item **161** closes the stage
and must be last.

**Numbering.** Continues at the next free integer: **152–161**.

---

## Work items

### Item 152: Retire the vision §6 seed-conformance check

Vision v4's §6 carries no numbered mode list, so the three symbols that read one
have nothing left to conform against: `failure_modes.vision_seed_titles()`
(`failure_modes.py:2149`), `VISION_SEED_DISPOSITION` (`:2033`) and
`vision_seed_conflicts()` (`:2641`) are retired, or kept as **provenance only** —
a frozen record of what §6's eight seed titles became, with no live parse of the
document behind it. `vision_seed_titles()` returning `{}` against v4 is not an
acceptable end state: it makes `vision_seed_conflicts()` report every
disposition title as absent, which is what reds the nine tests below. The
module's own prose goes with the symbols: `failure_modes.py`'s docstring
("It is the **seed**, not the record", `:179-182`, `:238-239`, `:27-28`,
`:114-117`, `:745`), the generated `_NOTE` and the generated document's
`## Vision section 6 seed disposition` section stop describing §6 as a numbered
seed list and describe it as the principles document that points here. The nine
tests the 2026-09-16 inbox entry measured as red are re-pointed at the
provenance shape or retired with the symbol they test —
`test_137::test_ac17_vision_section_six_still_has_exactly_eight_modes`,
`test_138::test_ac9_vision_section_six_titles_are_dispositioned_provenance`,
`test_144::test_ac16_vision_section_six_seed_titles_all_have_a_resolving_disposition`
and `test_144::test_ac16_vision_seed_conflicts_reports_an_unresolvable_disposition`
(with `test_144`'s private `_vision_mode_titles()` parse, which goes with them),
`test_145::test_ac3_every_vision_seed_title_has_a_resolving_disposition`,
`test_147::test_ac4_vision_parse_has_one_home`,
`test_147::test_ac5_every_vision_seed_title_disposes_and_resolves`,
`test_147::test_adv_ac5_unresolvable_disposition_is_reported` and
`test_151::test_ac27_vision_seed_conflicts_is_empty`. **No mode content
changes**: not one `ModeSpec` field moves, and the regenerated
`failure_modes.generated.*` diff is exactly the seed-disposition and note
change. **Measured against vision v4, not against `main`:** this item's tests
are written against `docs/aide/vision.md` as it stands on branch
`docs/vision-v4-section-6` (PR #77, gate 6 approved). The builder gets that text
by **merging `origin/docs/vision-v4-section-6` into the item branch** at the
start of the item — a merge, not a cherry-pick, so the vision commit is not
duplicated when PR #77 lands on `main` — and the item's spec records the head
sha it merged. If PR #77 has already merged to `main` when the item is claimed,
`aide sync` alone brings it and no merge is needed; the spec says which of the
two happened. *Testable:* against vision v4, the whole suite is green with no
test reading §6's numbered form; no module under `src/segfacet/` parses
`vision.md` for mode titles, asserted by a tree-wide scan rather than by
hand-listing; whichever of retire-or-keep-as-provenance is chosen, no surviving
symbol's value depends on the document's text; the regenerated specification
artifacts are byte-identical to the committed copies and their diff against the
pre-item copies contains no mode field.

### Item 153: Re-key the per-mode eval harness onto the signed-off catalogue

`segfacet.eval.per_mode`, `severity_ladder`, `per_mode_cohort` and their JSON
schemas are still keyed by the pre-sign-off ids 1–8, frozen as
`per_mode.LEGACY_STAGE18_MODE_NAMES` — a map whose "mode 1" is *label not
aligned with the vertebra it names* while the specification's mode 1 is
*Segmentation accuracy (over-/under-segmentation)*. This item moves every key,
name and schema field onto `failure_modes.SPECIFICATION`'s ids and retires the
legacy map, updating the pins in `test_099`–`test_102`, `test_109`, `test_125`
and `test_135` that hand-transcribe it. Each Stage-18 metric is **re-homed to
the mode it measures, or recorded as measuring no mode** — the roadmap names the
`displace` ladder as the case in point, since the spline-offset signal serves no
mode after item 150 — and "measures no mode" is an explicit, rendered value, not
a missing key. The re-keying is a mapping decision per metric, recorded in the
item's spec with what each old id measured and which specification id (if any)
now owns it; a metric whose re-homing is not derivable from the specification is
recorded as such rather than guessed. The re-measurement of the ladder constants
that this re-key invalidates is item 154's, deliberately: this item changes ids
and names, not numbers. *Testable:* no module or test under `src/segfacet/` or
`tests/` references `LEGACY_STAGE18_MODE_NAMES` or keys a per-mode metric,
ladder or cohort count by an id outside `failure_modes.SPECIFICATION`, asserted
by a tree-wide scan; every schema-emitted mode id validates against the
specification; each re-homed or no-mode-measuring metric carries its recorded
disposition in the emitted record and a test reads it back; `segfacet evaluate`
and the compare-runs CLI still run end to end on the two-case cohort fixture.

### Item 154: Re-measure the ladders, the cross-mode constants and mode 1's anchor

The severity ladders exist to say how a per-mode signal responds to a
monotonically worse perturbation, and every recorded number behind them was
measured against the pre-sign-off ids. `KNOWN_CROSS_MODE_COUPLINGS` (two
entries, both naming a foreign mode 1) and `RECORDED_MARGINS` (eight entries,
five of them `inf`) are **re-measured from a clean tree, never carried over**,
and each is recorded with what it was measured on — corpus, base fixture, date.
This item absorbs Stage 20's deferred **item 141** (the mode-1 ladder base): the
ladder is re-derived for what mode 1 now means, or mode 1 is recorded as having
no ladder, and that record is the deliverable either way. Two false claims are
corrected in the same pass: `eval/severity_ladder.py`'s module docstring and its
mode-7 ladder `rationale` both assert `rank(v) == v - 1` for every value 1–24,
which is false for exactly the lumbar block the corpus fixtures use
(`labels.CANONICAL_ORDER` inserts `T13` at index 19, so `L1`–`L5` have canonical
rank equal to their value) — the premise the "degenerate, 2 rungs" argument
rests on; whether the conclusion survives the corrected premise is recorded as a
finding, not silently preserved. And `feature_docs.MODE_ANCHOR_PATHS[1]` is
re-anchored on a path mode 1's own signal reads, since the item-150 sign-off
reclassified `mislabel`'s offset paths as bookkeeping serving no mode, leaving
mode 1's anchor and mode 1's mechanism disagreeing about which rule reads it.
*Testable:* every cross-mode coupling and recorded margin in the tree carries a
measurement provenance string naming corpus and date, and a test fails on one
that does not; re-running the measurement from a clean tree reproduces the
committed values within the recorded tolerance; no source file contains the
literal `rank(v) == v - 1`; `MODE_ANCHOR_PATHS[1]` names a path that mode 1's
`intended_rules` actually consume, asserted against the catalogue's consumed-path
table rather than by hand; mode 1 either has a ladder with a re-derived base or a
recorded no-ladder disposition, and a test reads back whichever.

### Item 155: A corpus case is a clean control or a condition case, never `failure_mode == 0` alone

In both corpus manifests `failure_mode == 0` now means two different things — a
clean control, or a condition-only case whose `condition` field is non-empty
(the FOV-truncation crop case). `synth.regression.verify_case`,
`traceability._build_conformance` and `failure_modes._corpus_case_conflicts`
each distinguish them by hand; any other consumer filtering `failure_mode != 0`
silently drops the condition case, as `test_040`'s rebuild sweep did until it
was reconciled. Replace the overload with an explicit discriminator — a
dedicated sentinel or a `kind` field on the manifest entry, chosen in the spec
and applied to both `tests/corpus/manifest.json` and
`tests/corpus/intensity/manifest.json` — and sweep every consumer onto it, so
that "is this a failure case?" is one documented call and not a comparison
against zero. The manifests are byte-reproducible committed fixtures: the
regeneration must be byte-identical and the `.gitattributes` pins must stay
clean. *Testable:* no consumer under `src/segfacet/` or `tests/` distinguishes a
clean control from a condition-only case by `failure_mode == 0` alone, asserted
by a tree-wide scan for the comparison; a synthetic condition-only case
constructed in a test is classified correctly by every sweeping consumer; both
manifests regenerate byte-identically; the regenerated conformance and
traceability artifacts differ from the committed copies only in the new field.

### Item 156: The three unclosed conformance seams in the specification checks

Three Stage-30 residues, each a located `insights.md` entry, fixed here or
recorded as not worth fixing with a reason. **(1) The unmirrored declaration.**
Nothing reports a rule declaring a *known* mode that the specification's own
`intended_rules` do not mirror: `failure_modes._intended_rule_conflicts` checks
specification → declaration and `catalogue.rule_declaration_conflicts` checks
corpus → declaration plus "mode outside the key set", so a declaration naming a
listed mode with no matching `IntendedRule` edge and no corpus case passes every
check — measured 2026-09-04, giving `reference_delta` the modes `(1, 2, 5)`
yields no conflict from either while `build_matrix()` lists mode 5's rules as
`('coverage', 'reference_delta')` and regenerates that into the committed matrix
as a claim no check made. **(2) The geometric-only attribution scan.** Item 149
re-pointed the per-edge `attribution` column at the specification, but
`catalogue.scan_synth_rule_mode_map` remains an AST scan of geometric
`Expectation(...)` literals alone and is still read for
`corpus_designated_unregistered_rule_ids`, so that one direction is blind to
every intensity case; it reads both corpora or its remaining consumer is fenced
and the limit is rendered beside the value. **(3) The retired "complete,
always" contract.** `traceability.py`'s `_NOTE` and docstring already say a
`proposed` mode is a legitimate mode → rule hole; a tree-wide check pins that,
and the two surviving restatements in `roadmap.md` (lines 919–920, the two
"**Yes, always**" rows) are **handed back to the next roadmap revision** with
the measurement that refutes them — `build_matrix()` reports
`mode_to_rule.complete is False` with holes at the `proposed` modes — because a
root document is not edited from inside an item. *Testable:* a rule declaring a
known mode with no mirroring `IntendedRule` edge and no corpus case is reported
by name, naming both the rule and the mode, with the `reference_delta` `(1, 2,
5)` perturbation as the positive control; the corpus-designated-unregistered
direction reports an intensity-manifest case, or its qualifier names the corpus
it cannot see and a test reads that qualifier; no module or generated artifact
under `src/segfacet/` or `docs/aide/*.generated.*` asserts either direction is
complete-always; the regenerated matrix's diff is exactly these changes.

### Item 157: The `modeN_` corpus case-id prefixes — rename, or record the decision

The geometric corpus case ids keep historical `modeN_` prefixes that no longer
name the mode they carry: after the item-150 re-keying `mode2_fragment` is mode
1, `mode5_remove_level` is mode 6, `mode8_force_overlap` is mode 15, and
`mode6_crop_at_border` carries no mode at all (it is the FOV-truncation
condition). The manifest's `failure_mode` field is the authority and the prefix
is now actively misleading to a reader — and to any test that keys off it. The
roadmap puts two options and says **the maintainer decides at the queue's
planning**: rename them to mode-neutral ids in one corpus-value change with
every pin updated (43 test modules name them), or keep them with the reason
recorded where a reader meets the ids. **This queue could not ask, so the
decision is raised at the queue's review and belongs to the maintainer, not to
the item.** Absent a decision by the time the item is specced, the item takes the
record-the-decision branch and states that default in its Decisions log: a
rename across 43 modules is a large, low-reversibility change, while a recorded
decision can be revisited in any later queue at no cost. Either way the outcome
is a written disposition, in the manifest's own documentation and beside the
case ids, not a silent status quo. *Testable:* under the rename branch, no id
under `tests/corpus/` carries a `modeN_` prefix, every pin resolves, both
manifests regenerate byte-identically and the full suite is green; under the
record branch, a test asserts that each surviving prefixed id is accompanied by
its recorded disposition and that nothing in `src/` or `tests/` derives a mode
from the prefix — the prefix-to-mode inference is what the item forbids in both
branches.

### Item 158: The committed-artifact guard's two blind spots

`tests/committed_artifact_guard.py` is the static enforcement behind every
fresh-vs-committed comparison, and two shapes pass through it in silence.
**(1) The unresolvable module root.** `_is_file_root_chain`
(`committed_artifact_guard.py:239-255`) resolves a module root only from a
`Path(__file__)` chain of at least two literal `.parent` steps, so the equally
common `Path(__file__).resolve().parents[1]` idiom resolves to nothing and every
committed path built from such a root is skipped — measured 2026-09-03, the same
two-line module classifies clean written with `parents[1]` and reports a
violation written with `.parent.parent`. Both
`tests/test_138_traceability_matrix.py:69` and
`tests/test_144_failure_mode_specification.py:33` use `parents[1]`, which makes
test_138's guard-clean attestation an attestation over a blind spot. **(2) The
missing ground.** `docs/aide/traceability_matrix.generated.{json,md}` is
byte-compared fresh-vs-committed by `test_143`'s AC15 with no `ALLOWLIST` entry
naming a ground for it; the comparison is sound on its merits (the artifact has
zero float leaves, measured 2026-09-03), which is exactly why it deserves an
explicit entry rather than a blind spot — the justification currently lives in a
source comment because item 143's AC14 forbade allowlist growth. Resolve the
root idiom first, then ground the comparison, so the entry is added to a guard
that can actually see it. *Testable:* a two-line synthetic module written with
`parents[1]` and with `.parent.parent` classifies identically, asserted both
ways; with the resolver fixed, the traceability-matrix comparison is visible to
the guard and is either grounded by an allowlist entry naming why or reported as
a violation; `test_138`'s and `test_144`'s guard-clean attestations still hold
and now mean something; the guard's own docstring lists the shapes it still
skips, and a test reads that list back.

### Item 159: The prerequisite test and import defects Stage 32 edits

The remaining located defects in the surfaces Stage 32 works on, each fixed or
ticked with a pointer if a later item already fixed it — the item **verifies
before re-fixing**, since several were repaired in passing. In scope: the eager
import in `src/segfacet/__init__.py`, which unconditionally pulls
`features.fragmentation` and so loads NumPy/NiBabel on any `import segfacet.X`,
including `traceability` and `failure_modes`, whose own docstrings claim to stay
import-cheap (the one production change here, and the reason a bare
`import segfacet.failure_modes` cannot be asserted lightweight today); the two
`test_147` checks that cannot pass as written against their own spec — the
"exactly four files mention `MODE_ANCHOR_PATHS`" count, which a comment in
`heuristics/reference_delta.py:128` breaks, and
`test_ac9_every_mechanism_names_a_token_that_resolves_live[10]`, unsatisfiable
because it omits the one source (the mode's candidate feature) its own spec
names (this entry's third check, `test_ac4_vision_parse_has_one_home`, is item
152's, and the `MODE_ANCHOR_PATHS` count interacts with item 154's re-anchor —
both are noted in the spec so the three items do not collide);
`test_136::test_ac8_surplus_declared_mode_is_reported_naming_both`, which still
exercises the retired `"corpus"` evidence tag its authorised neighbours were
re-pointed away from; `test_143::test_ac16_record_covers_exactly_the_required_artifact_set`,
whose **equality** against a live-derived artifact set pins a dated historical
record to growing state, so the next corpus case turns a document about
2026-09-03 red; `test_145::test_ac23_...`'s `committed_ids == {1..8}` equality,
long overtaken by sixteen modes; `test_146::test_ac30_...`'s closing assertion
`specification_conflicts(tuple(iter_modes())) != conflicts`, which cannot hold by
construction because that tuple is the function's own default; and `test_148`'s
`_status_report_module()` helper, missing the `sys.modules[spec.name] = module`
line its model carries, plus `test_103`'s AC13 `overlap` parametrisation, empty
by construction under item 148's own authored table. The `aide/queue-018`
base-ref skips are **confirmed retired** (D0's pass) and recorded, not re-done.
*Testable:* `import segfacet.failure_modes` and `import segfacet.traceability`
add no NumPy or NiBabel entry to `sys.modules`, asserted in a subprocess so the
suite's own imports cannot mask it, while `import segfacet` keeps its public
surface; each named test passes on its own merits rather than by deletion, and
where a check is retired the item records what replaced its claim; no test in
the tree asserts an equality against a live-derived artifact set that a later
corpus case would break, asserted for the two named records; the full suite is
green with no permanently-skipping git-diff test remaining.

### Item 160: Insight triage to a known state

Take `docs/aide/insights.md` to a state where every open `defect` and `gap`
entry present at this stage's start has a recorded disposition: **ticked** with a
pointer to the item that fixed it (items 152–159 above, and any entry a later
item had already fixed), **re-homed** with a dated pointer to the mode in the
specification it belongs to, or to the stage that will carry it, or **left open
with a dated reason**. `knowledge` and `framework` entries are left exactly as
they stand — they route through `/aide-review-insights`, not through a queue —
and that is itself stated rather than assumed. The two the roadmap fixes in
advance are re-homed, not fixed: the CI dev-tooling lockfile (a packaging
decision — a `constraints-dev.txt` applied on every leg with the numpy override
after) and `evaluate --calibrate`'s per-grid-point re-extraction (a production
change, measured at 0.64 s versus 74.25 s on a two-case cohort). The entries
this queue passed over at planning — the four retracted Stage-20 acceptance
criteria, the per-detector-id and per-path perturbation harness gaps, the three
sign-off detectors and two fixture gaps with no shipped rule, the disc-label
channel that needs its own decision, and the vision §6 "two-descent" defect that
D1's re-issue closes — each get their pointer or their dated reason here. Every
edit goes through the verb (`aide insights tick N --pointer …`): the claim is
immutable, a judgement is a dated trail line indented under the entry, and
nothing is reworded or deleted. *Testable:* after the item, `aide insights list
--open` reports no `defect` or `gap` entry without either a tick or a dated
trail line, asserted by a test that reads the inbox **and** every
`docs/aide/insights/archive-*.md` (an archive sweep must not red the suite);
every captured claim present before the item is present afterwards verbatim; the
three counts (ticked / re-homed / left open) are recorded and match what the
verb reports; `aide check` reports no insights error.

### Item 161: Validate stage 31: Post-Sign-Off Maintenance

Replay Stage 31's acceptance end to end, not just the unit suite, and record
what was measured rather than what was expected. The full suite green from a
clean tree; the eval harness re-run from that clean tree with items 153 and
154's re-measured constants recorded in [`../progress.md`](../progress.md)
together with the corpus and date they were measured on; a tree-wide check that
no module or test keys a per-mode metric, ladder or cohort count by an id
outside `failure_modes.SPECIFICATION` and that `LEGACY_STAGE18_MODE_NAMES` is
gone; a check that `vision.md` §6 names the specification as the catalogue and
that no module under `src/segfacet/` asserts it carries a numbered list; a check
that no consumer distinguishes a clean control from a condition-only case by
`failure_mode == 0` alone; and item 160's triage counts recorded as measured
numbers. `aide check` must be clean of any warning this stage's surfaces raise —
the pre-existing baseline classes (item specs with no `## Assumptions` block,
the two Stage-16 gates awaiting a decision, the four retracted Stage-20 criteria)
are recorded as the baseline and **not** pinned by count, which is the failure
mode the retired per-item warning-count tests had. Any Environment-Gated
Capability Verification row this stage touches is evaluated with
`aide env --profile <name>` and flipped to verified where the environment
allows, else its Notes cell records why it stays unverified. *Testable:* each
acceptance line above is replayed by a named check in the validation module or,
where it has no stable in-suite shape, recorded in the item's Validation section
with the command and its measured output; the stage's five acceptance criteria
in `progress.md` are attested one by one against live state, with any criterion
that does not hold retracted rather than ticked.
