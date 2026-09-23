<!-- aide-template: item 1 -->
# Item 160 — Insight triage to a known state

> **Created:** 2026-09-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update
> **Queue:** [`../queue/queue-021.md`](../queue/queue-021.md) · Item 160
> **Objectives:** G7
> **Suggested branch:** `aide/160-insight-triage-to-a-known`

---

## Description

Roadmap Stage 31 D6. Every `defect` and `gap` entry that was open in
[`../insights.md`](../insights.md) when this stage started gets exactly one
recorded disposition. The same goes for every `defect` and `gap` entry
captured while the stage's queue ran. This item writes documents only. It
changes no production code, and it fixes none of the claims it disposes of.

**The three dispositions.** Each one is defined by what the inbox shows
afterwards, so a test can check it:

- **ticked**: the entry is `[x]` and carries a pointer to what fixed it. The
  pointer is either on the entry line after ` → ` or in a trail line under the
  entry. Sixteen stage-start entries were already ticked this way by items
  152–159. This item ticks two more.
- **re-homed**: the entry is `[x]` and its pointer on the entry line starts
  `re-homed (YYYY-MM-DD): ` and names a location in
  [`../roadmap.md`](../roadmap.md). That location is a stage deliverable, a
  Stage 32 "Known inputs per mode" bullet (the failure-mode id it belongs to),
  or a roadmap section. A re-home ticks the entry because the claim now has a
  durable home that is not the inbox. This is the same reasoning as folding a
  `knowledge` entry into the document that owns it (A4).
- **left open**: the entry stays `[ ]` and carries a trail line
  `- **YYYY-MM-DD** → left open: <reason>`. No home carries the claim yet, so
  the open inbox stays the place a future queue author reads it from.

**Which entries are in scope.** Stage start is the queue-021 planning commit
`99520a9` (2026-09-16, "docs(aide): add work queue 021"). It is the last commit
before any Stage 31 item ran. The later planning commit `653e93a` changed only
the queue file. At `99520a9`, the inbox had **29** open `defect`/`gap` entries
(12 `defect`, 17 `gap`). That matches the queue's own count. They are rows
**S1–S29** below. The queue items 152–159 captured **six** more `defect`/`gap`
entries, dated 2026-09-16 and 2026-09-17. They are rows **Q1–Q6**. They are
disposed of by the same rules but counted separately (A2), because the
stage's acceptance criterion counts only entries present at the stage's start.

**Entries are keyed by type, provenance, date and a claim substring, never by
list number.** Numbers come from position in the file. `aide insights archive`
renumbers entries, and a tick followed by an archive can move them. The builder
re-runs `python .aide/scripts/aide.py insights list --open` before **each**
tick and finds the row by its key. On 2026-09-17 each key was measured to
resolve to exactly one entry across the inbox and
`docs/aide/insights/archive-2026-Q3.md`. The list number in the table is that
day's value. It is a convenience and not an identity.

### Disposition table (measured 2026-09-17, engine 1.52.1)

"Source" is the entry's provenance field exactly as written (`—` means a bare
date). "Claim contains" is a substring of the claim text with no backticks.

**Stage-start cohort, S1–S29 (open at `99520a9`):**

| Row | #@09-17 | Type | Source | Date | Claim contains | Disposition | Pointer / reason (builder writes; `DATE` = the day of the edit) |
|---|---|---|---|---|---|---|---|
| S1 | 5 | gap | — | 2026-09-01 | three of the five CI legs in | **re-homed** | `re-homed (DATE): roadmap.md Carried defects — a packaging decision no stage owns (a constraints-dev.txt on every CI leg, numpy override after); roadmap Stage 31 D6 re-homes it, the next roadmap revision lists it` |
| S2 | 6 | gap | — | 2026-09-01 | re-extracts every case's features once per grid point | **re-homed** | `re-homed (DATE): roadmap.md Stage 21 — threshold calibration on a real cohort is where the per-grid-point re-extraction (0.64 s vs 74.25 s on two cases) is paid; roadmap Stage 31 D6 re-homes it` |
| S3 | 14 | gap | stage 20 criterion 5 | 2026-09-02 | acceptance criterion retracted: | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 D3 — item 142 states the end-to-end detection count and closes Stage 20 criterion 5` |
| S4 | 15 | gap | stage 20 criterion 4 | 2026-09-02 | acceptance criterion retracted: | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 D0 — item 140, the specificity assertion, Stage 20 criterion 4` |
| S5 | 16 | gap | stage 20 criterion 3 | 2026-09-02 | acceptance criterion retracted: | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 D0 — item 139, the per-rule exercise report, Stage 20 criterion 3` |
| S6 | 17 | gap | stage 20 criterion 1 | 2026-09-02 | acceptance criterion retracted: | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 D3 — item 142 closes Stage 20; the box was re-attested by item 138 (2026-09-02), and its "never silent" wording is refuted by the proposed modes (item 156's 2026-09-17 trail on the item-146 "complete, always" entry)` |
| S7 | 30 | gap | item 143 | 2026-09-03 | is now byte-compared fresh-vs-committed | ticked (already) | `item 158` |
| S8 | 31 | defect | item 143 | 2026-09-03 | test_ac16_record_covers_exactly_the_required_artifact_set | ticked (already) | `item 159` |
| S9 | 33 | defect | item 144 | 2026-09-03 | unconditionally imports | ticked (already) | `item 159` |
| S10 | 34 | gap | item 144 | 2026-09-03 | classifier resolves a module root only from a | ticked (already) | `item 158` |
| S11 | 38 | defect | item 146 | 2026-09-04 | test_ac23_fresh_matches_committed_structurally_and_carries_all_eight_ids | ticked (already) | `item 159` |
| S12 | 39 | defect | item 146 | 2026-09-04 | test_ac30_proposed_entry_acquiring_a_declaring_rule_is_reported | ticked (already) | `item 159` |
| S13 | 41 | defect | item 146 | 2026-09-04 | now carries mode 9 as a mode row whose | ticked (already) | `item 156` |
| S14 | 42 | defect | item 146 | 2026-09-04 | the two documents the contract was authored in still assert it verbatim | ticked (already) | `item 156` |
| S15 | 44 | defect | item 147 | 2026-09-04 | evidence-rungs paragraph calls mode 7's | **ticked** | `vision.md v4 §6 removes the example (PR #77, commit 7d800a2; human gate 6 approved 2026-09-16) — Stage 31 D1` |
| S16 | 45 | defect | item 147 | 2026-09-04 | relying on exactly the declared→corpus direction item 147 step 8 deletes | ticked (already) | `item 159` |
| S17 | 46 | defect | item 147 | 2026-09-04 | carries the same false mode-7 claim item 147 corrected | ticked (already) | `item 154` |
| S18 | 47 | defect | item 147 | 2026-09-04 | checks cannot pass as written against item 147's own spec | ticked (already) | `item 159` |
| S19 | 49 | gap | item 147 | 2026-09-04 | nothing reports a rule declaring a | ticked (already) | `item 156` |
| S20 | 50 | gap | item 148 | 2026-09-04 | classification (item 148) is an authored claim no shipped check can refute | **left open** | `left open: the per-detector half is re-homed with the item-150 (2026-09-14) per-detector entry to roadmap Stage 32's mode 9 input; the per-path perturbation harness that would refute a signal classification has no stage or mode home` |
| S21 | 51 | defect | item 148 | 2026-09-04 | omits two pins that break as a direct, mechanical consequence | **ticked** | `fixed in place at capture by item 148's test-writer — tests/test_137_mode_less_rule_disposition.py's _CANONICAL_TAG_ORDER carries rule_bookkeeping and rule_not_read, and its schema_version pin no longer reads 1.1 (verified 2026-09-17, item 160)` |
| S22 | 52 | defect | item 148 | 2026-09-04 | two committed tests fail against item 148's own spec, both test-side | ticked (already) | `item 159` |
| S23 | 56 | gap | item 150 | 2026-09-14 | the Stage-18/29 eval harness | ticked (already) | `item 153` |
| S24 | 57 | gap | item 150 | 2026-09-14 | numbered eight-item list no longer matches the catalogue | ticked (already) | `item 152` |
| S25 | 58 | gap | item 150 | 2026-09-14 | three detectors the sign-off asked for that no shipped rule provides | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 Known inputs per mode — mode 6 spacing-gap signal, mode 11 transitional-label detector, modes 13/14 per-component centroids (the entry's old ids 4, 6, 8; read through the item-150 2026-09-15 id map)` |
| S26 | 59 | gap | item 150 | 2026-09-14 | lumbosacral transitional-anatomy sub-type | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 Known inputs per mode — mode 2, the intervertebral-disc-channel sub-type decided in or out` |
| S27 | 61 | gap | item 150 | 2026-09-14 | per-detector attribution is now a live need, not a nicety | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 Known inputs per mode — mode 9, per-detector attribution for mislabel's spline-offset detector` |
| S28 | 63 | gap | item 150 | 2026-09-14 | in a corpus manifest now means two things | ticked (already) | `item 155` |
| S29 | 68 | gap | item 150 | 2026-09-15 | detectors and fixtures the 2026-09-15 split asked for | **re-homed** | `re-homed (DATE): roadmap.md Stage 32 Known inputs per mode — mode 5 enclosed-cavity feature, mode 7 above-expected-count check, mode 3 split operator` |

**In-queue cohort, Q1–Q6 (captured by items 152–159, after `99520a9`):**

| Row | #@09-17 | Type | Source | Date | Claim contains | Disposition | Pointer / reason |
|---|---|---|---|---|---|---|---|
| Q1 | 76 | defect | item 152 | 2026-09-16 | test_ac14_every_item_150_insight_is_well_formed_and_honestly_dated | ticked (already) | `ecdc81d (queue-021 fix commit)` |
| Q2 | 79 | defect | item 154 | 2026-09-16 | declaring mode 1 by | **left open** | `left open: measured 2026-09-17, src/segfacet/heuristics/reference_delta.py's mode-1 comment still names stage3.per_label_offsets[].offset_mm as MODE_ANCHOR_PATHS[1], which item 154 re-anchored on per_label.{label}.components.fragmentation_index; rule-declaration content that item 156 did not take and no Stage 32 input names` |
| Q3 | 81 | gap | item 155 | 2026-09-16 | the eval harness groups corpus cases by | **left open** | `left open: a condition-keyed per-mode bucket is an eval-harness schema change that no stage deliverable or mode input names` |
| Q4 | 82 | gap | item 155 | 2026-09-16 | would pass the scan undetected | **left open** | `left open: a hardening of tests/test_155_corpus_case_kind.py's AST scan; no stage owns test-hygiene work now that Stage 29 is closed, so it waits for a maintenance queue` |
| Q5 | 85 | gap | item 158 | 2026-09-17 | resolver has no branch for the os.path.dirname(os.path.abspath(__file__)) root idiom | **left open** | `left open: the same defect class as item 158's fixes, hiding no comparison today (item 158, 2026-09-17); no stage owns it, so it waits for a maintenance queue` |
| Q6 | 86 | defect | item 158 | 2026-09-17 | splits it into copies with byte-identical prose | ticked (already) | `item 159` |

**Counts to record, measured on the table above (2026-09-17):**

| Cohort | ticked | re-homed | left open | total |
|---|---|---|---|---|
| Stage start (S1–S29) | 18 (16 by items 152–159, 2 by this item) | 10 | 1 | 29 |
| In-queue (Q1–Q6) | 2 | 0 | 4 | 6 |

**What this item does NOT do.** It does not touch `knowledge`, `framework`
or `automation` entries. They are routed through `/aide-review-insights`,
not through a queue (conventions §1 → `insights-triage.md`). This holds even
where a premise has visibly decayed. For example, the item-150 (2026-09-14)
`knowledge` entry on `modeN_` prefixes was answered by item 157 (A9). The
item does not reword, reorder or delete any captured claim. It does not
archive. It does not edit `roadmap.md`, a root document, so S1's destination
section gains its bullet only at the next roadmap revision (A5). It does not
record the counts in `progress.md` or tick Stage 31 acceptance criterion 5.
Both belong to item 161, the stage validation, which records "item 160's
triage counts … as measured numbers" (queue-021). No AC here closes a stage
criterion.

## Acceptance Criteria

The rows S1–S29 and Q1–Q6 are the table in the Description. The test module
transcribes them once as a frozen tuple of
`(row, type, source, date, claim_substring, disposition, evidence)`. "Across
the inbox and archives" means the entries that `parse_insights` returns for
`docs/aide/insights.md` plus every `docs/aide/insights/archive-*.md`. An
`aide insights archive` sweep must not turn any of these tests red.

- [ ] **AC1: every row resolves to exactly one entry.** For each of the 35
  rows, exactly one entry across the inbox and archives has the row's `type`,
  `source` (the provenance field exactly as written, `None` for a bare date),
  `date`, and a claim text containing `claim_substring`.
- [ ] **AC2: ticked rows are ticked with a pointer.** For each row whose
  disposition is *ticked* (S7–S14, S15, S16–S19, S21, S22–S24, S28, Q1, Q6),
  the resolved entry is ticked and carries a non-empty pointer, either on the
  entry line or in at least one trail line.
- [ ] **AC3: a ticked row's pointer names its recorded evidence.** For each
  *ticked* row, the entry-line pointer, or any trail line under the entry,
  contains the row's evidence token. The tokens are `item 158`/`item 159`/
  `item 156`/`item 154`/`item 153`/`item 152`/`item 155` for the rows ticked
  by items 152–159, `ecdc81d` for Q1, `7d800a2` for S15, and
  `tests/test_137_mode_less_rule_disposition.py` for S21.
- [ ] **AC4: re-homed rows are ticked with a dated re-home pointer.** For each
  *re-homed* row (S1–S6, S25, S26, S27, S29), the resolved entry is ticked and
  its entry-line pointer matches `^re-homed \(\d{4}-\d{2}-\d{2}\): ` with a
  valid calendar date.
- [ ] **AC5: a re-home pointer names its recorded destination.** For each
  *re-homed* row, the entry-line pointer contains the row's destination token.
  S1 uses `roadmap.md Carried defects`, S2 uses `roadmap.md Stage 21`, S3/S6
  use `roadmap.md Stage 32 D3`, S4/S5 use `roadmap.md Stage 32 D0`, and S25,
  S26, S27, S29 use `roadmap.md Stage 32 Known inputs per mode`. Each of S25,
  S26, S27 and S29 also contains every mode id recorded for it, as `mode N`
  or `modes N/M`: S25 → 6, 11, 13/14; S26 → 2; S27 → 9; S29 → 5, 7, 3.
- [ ] **AC6: every re-home destination exists in `roadmap.md`.** Each
  destination token from AC5 resolves against `docs/aide/roadmap.md` as it
  stands. `Carried defects` resolves to a line starting `# Carried defects`.
  `Stage 21` resolves to a line starting `## Stage 21 — `. `Stage 32 D0` and
  `Stage 32 D3` each resolve to a bullet starting `- **D0 — ` / `- **D3 — `
  inside the `## Stage 32 — ` section. `Stage 32 Known inputs per mode`
  resolves to a line starting `**Known inputs per mode` inside that section.
  Each mode id recorded in AC5 resolves to a bullet in that list whose
  italicised label starts `*Mode N `, or `*Modes 13 ` for the 13/14 pair
  (`- *Modes 13 collapsed / 14 duplicated:*`).
- [ ] **AC7: left-open rows carry a dated reason.** For each *left open* row
  (S20, Q2, Q3, Q4, Q5), at least one trail line under the resolved entry
  matches `^\s+- \*\*(\d{4}-\d{2}-\d{2})\*\* → left open: \S`, with a valid
  calendar date. The check does not require the entry to be unticked, so a
  later item that fixes the claim and ticks the entry keeps this test green.
- [ ] **AC8: no stage-start defect or gap entry is still untriaged.** Every
  `defect` or `gap` entry across the inbox and archives that is dated on or
  before 2026-09-16 and is **unticked** carries a trail line matching AC7's
  `left open:` pattern. The date bound makes this stable. A later capture is
  dated after it, and a later tick only removes entries from the checked set.
- [ ] **AC9: no captured claim was changed.** Take every entry line in
  `docs/aide/insights.md` at the item's merge base with `aide/queue-021`.
  Reduce each line to its claim: the type, the claim text, the provenance, the
  date and the engine note, with the checkbox and the entry-line pointer
  removed. Each claim is present unchanged in the branch head's inbox or
  archives, the same number of times. *(A diff-time claim. The Validation
  section checks it on the branch, and the suite does not pin it (§6).)*
- [ ] **AC10: `knowledge`, `framework` and `automation` entries are untouched.**
  Between the merge base and the branch head, no entry of these three types
  changed its checkbox, its entry-line pointer or its trail lines. *(Diff-time,
  checked in Validation.)*
- [ ] **AC11: the S rows are exactly the stage-start set.** The open `defect`
  and `gap` entry lines in `git show 99520a9:docs/aide/insights.md` resolve
  one-to-one onto rows S1–S29. *(Checked in Validation, because a shallow CI
  clone cannot reach `99520a9`.)*
- [ ] **AC12: the counts are recorded as a measurement.** When the builder
  finishes, `## Decisions & Trade-offs` records the per-cohort counts
  (ticked / re-homed / left open), measured by classifying each row's
  resolved entry with the AC2/AC4/AC7 predicates. The validator re-measures
  the counts and confirms them against
  `python .aide/scripts/aide.py insights list --trail`. *(A recorded
  measurement, not a live-equality pin. A later tick of a left-open entry
  moves the live count, and that must not turn anything red (§6).)*
- [ ] **AC13: `aide check` reports no error.** `run_checks` returns no error
  after the edits. The existing
  `tests/test_aide_check_no_errors.py` asserts this, and no new test is
  written for it.

## Assumptions

- **A1:** "Stage start" is the queue-021 planning commit `99520a9`
  (2026-09-16 17:20 +0100). It is the first commit that plans Stage 31 items,
  and no Stage 31 item existed before it. The follow-up planning commit
  `653e93a` changed only `docs/aide/queue/queue-021.md`. At `99520a9` the
  inbox held 29 open `defect`/`gap` entries (12 + 17), which matches the
  queue's own "12 `defect`, 17 `gap`". Two things were ruled out as the
  stage's start: the Stage 31 D0 engine-update merge, because the queue says
  its inbox was read at planning, and the first item claim, which comes after
  planning.
- **A2:** `defect`/`gap` entries captured while the queue ran are **in scope
  and counted separately**. They are Q1–Q6, measured 2026-09-17 after item
  159 merged. Leaving them untriaged would hand Stage 32's planner an inbox
  whose newest defects have no recorded reading. Merging them into the stage
  count would misstate a criterion that counts only stage-start entries. A
  `defect`/`gap` captured after this measurement and before the builder runs
  is disposed of by the same rules, logged in Decisions, and left out of the
  frozen table (no spec amendment is needed for it).
- **A3 (engine 1.52.1, re-checked 1.59.0, re-checked 2.1.0):** `aide insights tick N --pointer P` on an
  **unticked** entry flips the checkbox and writes ` → P` on the entry line.
  It adds no date and no trail line. On an **already-ticked** entry it
  appends `  - **<today>** → P` as a trail line
  (`.aide/scripts/aide.py::tick_insight_text`). **No verb appends a trail line
  to an unticked entry**, so the verb cannot produce the queue line's "left
  open with a dated reason". The builder therefore hand-appends left-open
  trail lines directly under the entry, in the exact shape the verb writes
  (`  - **YYYY-MM-DD** → left open: <reason>`, two-space indent, or the
  indent of an existing trail line). That shape is still an append to the
  bookkeeping trail and never an edit of the claim (§1 → `insights.md`). The
  inbox already carries this precedent: the open item-150 (2026-09-15)
  `knowledge` entry narrowing mode 10 has a trail line. Every tick, fixed or
  re-homed, goes through the verb. The date is written into a re-home
  pointer's own text because the verb writes none. The gap is captured as a
  `framework` insight (item 160, 2026-09-17).
  **Re-check 2026-09-18 (engine 1.59.0): no longer holds.** Engine 1.54.0
  (aide-loop issue #236) added `aide insights tick N --trail --pointer P`,
  which appends the dated trail line under an entry and leaves its checkbox
  alone. The hand-append this item used was correct on 1.52.1 and is not
  the route on 1.54.0 or later: a left-open trail line goes through the verb.
- **A4:** A **re-home ticks the entry**. §1 → `insights-triage.md` says
  routing a `defect`/`gap` never ticks it, and it says so because the queue
  that will carry the entry does not exist yet. A re-home here points at a
  roadmap location that already names the claim. That location is Stage 32's
  D0/D3 deliverables, which name items 139, 140 and 142 against Stage 20
  criteria 3–5; its "Known inputs per mode" bullets, which carry S25, S26,
  S27 and S29 with their mode ids; or Stage 21 for S2. The one exception is
  S1 (A5). This is the tick-when-there-is-nothing-left-for-a-queue-to-carry
  case the convention allows for a decayed premise. It also keeps the open
  inbox limited to claims nothing else carries. Roadmap Stage 31 D6 and the
  stage acceptance line list re-homed separately from left open, which
  supports reading re-homed as closed.
- **A5 (judgement call, surfaced for the queue boundary):** S1, the CI
  dev-tooling lockfile, is re-homed because roadmap Stage 31 D6 names it
  re-homed. **No roadmap stage or section carries it today.** The destination
  is the roadmap's `# Carried defects — no stage owns them yet` section, which
  exists. An item may not edit a root document, so the bullet itself must be
  added by the next roadmap revision. Until then the claim lives only in the
  ticked entry. The alternative, left open with that reason, contradicts the
  roadmap's fixed disposition. A human reviewer may prefer it.
- **A6 (judgement call):** S6, the Stage 20 criterion 1 retraction, is
  re-homed and not ticked as fixed. Its premise ("Item 138's deliverable,
  still open") has decayed: item 138 merged, and its validator re-ticked the
  box on 2026-09-02. `aide check` still reports that box as retracted
  ("the box is open again"). The criterion's "never silent" wording is also
  refuted by the seven `proposed` modes, as item 156 measured. Stage 32 D3
  (item 142) is where Stage 20 is closed, so the entry points there.
- **A7 (judgement call):** S20 is left open, not re-homed. Its per-detector
  half duplicates S27, which is re-homed to Stage 32's mode 9 input. Its
  per-path perturbation harness half has no stage or mode home. Ticking the
  whole entry would drop that half from the open inbox.
- **A8 (engine 1.52.1, re-checked 1.59.0, re-checked 2.1.0):** The test loads `.aide/scripts/aide.py` through
  `importlib`, as `tests/test_aide_check_no_errors.py` already does, and uses
  `parse_insights(text)`. Each returned `InsightEntry` has `.type`, `.source`
  (provenance text, or `None` for a bare date), `.date`, `.text` (the claim
  without provenance or pointer), `.ticked`, `.pointer` (text after ` → ` on
  the entry line, or `None`) and `.trail` (raw trail lines). If a later engine
  renames these fields, the builder/validator hands the item back. The test
  does not reimplement the parser.
- **A9:** `knowledge`, `framework` and `automation` entries are left alone
  even where their premise has visibly moved. Examples are the item-150
  (2026-09-14) `modeN_` prefix entry, which item 157 renamed, and the
  item-150 `MODE_ANCHOR_PATHS[1]` entry, which item 154 re-anchored.
  `/aide-review-insights` judges those. The queue line states this scope, and
  it is not assumed silently.
- **A10:** The pointer and trail text in the table is what the builder
  writes, with `DATE` replaced by the day of the edit. AC3/AC5 pin only the
  evidence and destination tokens, so the builder may fix a wording slip
  without a spec amendment. The builder may not change a disposition without
  one.
- **A11:** The S21 pointer's fact was measured on 2026-09-17:
  `tests/test_137_mode_less_rule_disposition.py`'s `_CANONICAL_TAG_ORDER`
  contains `"rule_bookkeeping"` and `"rule_not_read"`, and its schema pin
  reads `"1.2"`. The S15 fact was also measured that day: `docs/aide/vision.md`
  carries the v4 revision note and has no two-descent example in §6. The
  human-gate row cites commit `7d800a2` for the accepted v4 text.

## Implementation Steps

There is no production code. `source_dir` is untouched.

1. Run `python .aide/scripts/aide.py sync --item 160`, then
   `python .aide/scripts/aide.py insights list --open --trail`. Confirm that
   every S/Q row marked **re-homed**, **ticked** (not "already") or
   **left open** still resolves to one open entry. If an entry is gone or
   ambiguous, hand back.
2. **The two fixed ticks (S15, S21).** For each: re-run
   `insights list --open`, find the entry by type + source + date + claim
   substring, then run
   `python .aide/scripts/aide.py insights tick <N> --pointer "<table pointer>"`.
3. **The ten re-homes (S1–S6, S25, S26, S27, S29).** Same procedure, one at a
   time, re-listing before each tick. Each pointer starts
   `re-homed (<today>): ` and uses the table text.
4. **The five left-open reasons (S20, Q2, Q3, Q4, Q5).** No verb covers these
   (A3). Edit `docs/aide/insights.md` by hand. Insert exactly one line
   directly after the entry's last line (after its last trail line if it has
   one): `  - **<today>** → left open: <table reason>`. Do not change the entry
   line or any other line.
5. Run `python .aide/scripts/aide.py check` and confirm there are no errors.
   Then run `python .aide/scripts/aide.py insights list --trail` and classify
   each S/Q row. Record the two cohorts' counts (ticked / re-homed /
   left open) and the `insights list` summary line in `## Decisions &
   Trade-offs` as a dated measurement (AC12).
6. Commit. `tick` commits each edit itself unless `--no-commit` is passed.
   The hand trail lines and the Decisions record go in one plain commit.

## Authorised paths

**May change:**

- `tests/test_160_insight_triage.py` — the new test module (AC1–AC8)

**Asserts against:**

- `docs/aide/insights/*.md` — the archive files. AC1–AC8 read every
  `archive-*.md` beside the inbox, so an archive sweep keeps them green. They
  are read and never written
- `docs/aide/roadmap.md` — AC6 resolves each re-home destination against its
  headings and bullets
- `.aide/scripts/aide.py` — the tests load `parse_insights` from it (A8)

`docs/aide/insights.md`, `docs/aide/progress.md` and this spec are always
authorised and are not listed.

## Testing Strategy

The new module is **`tests/test_160_insight_triage.py`**. It has one test per
AC for AC1–AC8, parametrised over the frozen row tuple where the AC is
per-row. AC9–AC12 are diff-time or recorded-measurement claims, and the
Validation section checks them on the branch (§6: a diff-time claim belongs on
the branch, and a count the loop's verbs move is never pinned). AC13 is
covered by the existing `tests/test_aide_check_no_errors.py`.

- **Reading.** Build the entry list from `docs/aide/insights.md` plus
  `sorted(Path("docs/aide/insights").glob("archive-*.md"))`, as
  `tests/test_117_scope_verb_swap.py` and `tests/test_157_case_id_rename.py`
  already do. Read with `encoding="utf-8"`. Parse with `aide.parse_insights`
  (A8). Do not pin list numbers, ordinals, line numbers or the inbox's total
  or open counts anywhere.
- **Resolution helper.** `_resolve(row)` returns the single entry matching
  type, source, date and `claim_substring in entry.text`. AC1 asserts that
  exactly one matches. The other ACs call the helper and fail with the row id
  in the message.
- **Adversarial / edge cases.** These run on synthetic text passed to
  `parse_insights` and never touch the real file:
  - An entry that is ticked but has no pointer and no trail fails the AC2
    predicate.
  - A pointer `re-homed: roadmap.md Stage 32 D0` with no date fails AC4. So
    does `re-homed (2026-13-40): …`, an invalid date that must be rejected by
    `datetime.date.fromisoformat` and not by the regex alone.
  - A left-open trail line with an empty reason (`→ left open: `) fails AC7.
    A trail line of the right shape but indented zero spaces is parsed as not
    a trail and fails.
  - The AC8 predicate on a synthetic inbox fails when it holds an unticked
    `gap` dated 2026-09-15 with no trail. It passes when that entry is dated
    2026-09-18, which shows the bound is on the date.
  - A synthetic inbox with the same entry duplicated across the inbox text
    and an archive text makes AC1's resolver report two matches, not one.
  - AC6's resolver, given a roadmap text whose `## Stage 32 — ` section lacks
    a `- **D3 — ` bullet, fails. So does a `- **D3 — ` bullet that exists only
    under another stage's section. The resolver scopes by section, because a
    document-wide search is the unsafe shape the item-150 (2026-09-14)
    `knowledge` entry records.
- **Determinism / immutability.** The module never writes a file, and every
  adversarial case works on in-memory strings.
- **Existing tests to reconcile.** Swept on 2026-09-17 with
  `grep -rln "insights.md" tests/`. The modules that read the inbox
  (`test_117`, `test_137`, `test_150`, `test_151`, `test_157`) match specific
  captured claims by content, and none pins the ticked state, pointer or trail
  of any S/Q row. One module needs a closer look.
  `test_150::test_ac14_every_item_150_insight_is_well_formed_and_honestly_dated`
  matches item-150 lines with `_ITEM_150_GRAMMAR_RE`, whose tail is
  `(?: → .+)?$`, and flags any line containing `(item 150,` or `(item 150)`
  through `_ITEM_150_CLAIM_RE`. Checked 2026-09-17: the re-home pointers for
  S25, S26, S27 and S29 match that tail. None of the pointer or trail texts
  in the table contains `(item 150,` or `(item 150)`, because they write
  `item-150 (2026-09-14)` instead. **No existing test needs reconciling.** If
  the builder rewords a pointer (A10), it must keep both properties.
  `tests/test_150_maintainer_sign_off.py` is not authorised here.

## Validation

The validator runs these on the item branch, in addition to the suite:

1. **AC9, claim immutability.** `git merge-base HEAD aide/queue-021` gives
   `<base>`. `git show <base>:docs/aide/insights.md` gives the pre-item
   inbox. Parse it and the head's inbox plus archives with `parse_insights`.
   Map each entry to `(type, text, source, date, note)` and check that the
   multiset from before is contained in the multiset after. Record
   "N claims before, all present after".
2. **AC10.** For every `knowledge`/`framework`/`automation` entry, compare
   `(ticked, pointer, trail)` at `<base>` with head. Record that no entry
   differs.
3. **AC11.** `git show 99520a9:docs/aide/insights.md`. List its unticked
   `defect`/`gap` entries, resolve each onto S1–S29 by the table's keys, and
   record 29 ↔ 29 with no unmatched entry on either side.
4. **AC12.** Run `python .aide/scripts/aide.py insights list --trail`.
   Classify each S/Q row's entry (ticked with a pointer that is not a
   re-home / ticked with a `re-homed (` pointer / unticked with a
   `left open:` trail) and confirm the builder's recorded counts: stage start
   18 / 10 / 1, in-queue 2 / 0 / 4. Record the list's summary line. A
   mismatch is a FAIL unless the Decisions section explains it (A2).
5. `python .aide/scripts/aide.py check` reports no error.

No `[validation]` profile is needed.

## Dependencies

Items 152, 153, 154, 155, 156, 157, 158 and 159. Each ticked the stage-start
entries recorded above as "ticked (already)" or captured a Q row, and this
item's counts are final only once all of them have merged (queue-021:
"Item 160 runs after every item that ticks an entry").

**Downstream:** item 161 (Validate stage 31) records this item's counts in
`progress.md` and attests Stage 31 acceptance criterion 5.

## Decisions & Trade-offs

- **2026-09-17 — measured disposition counts.** Every S/Q row's resolved entry
  was classified with the AC2/AC4/AC7 predicates after all edits. Stage start
  (S1–S29): **18 ticked** (16 already by items 152–159, plus the 2 this item
  ticked — S15, S21), **10 re-homed** (S1–S6, S25, S26, S27, S29), **1 left
  open** (S20). In-queue (Q1–Q6): **2 ticked** (Q1, Q6, already by items 152
  and 159), **0 re-homed**, **4 left open** (Q2, Q3, Q4, Q5). Both match the
  Description's recorded table exactly. `python .aide/scripts/aide.py
  insights list --trail` summary line after the edits: `aide insights: 88
  entries, 23 open (16 knowledge, 1 defect, 4 gap, 2 framework)` (down from 35
  open `defect`/`gap` entries before this item's 12 ticks).
- **2026-09-17 — verb vs. hand edits.** The two fixed ticks (S15, S21) and the
  ten re-homes (S1–S6, S25–S27, S29) were each written with `python
  .aide/scripts/aide.py insights tick <ordinal> --pointer "<table text>"`,
  re-running `insights list --open` before every tick per the spec's
  resolve-by-key instruction; no row's ordinal moved between ticks (ticking
  edits a line in place and does not add or remove entries, so ordinals stay
  stable within one session — confirmed by re-listing after the first tick).
  The five left-open reasons (S20, Q2, Q3, Q4, Q5) were hand-appended as
  `  - **2026-09-17** → left open: <table reason>` trail lines directly under
  each entry, per A3 (no verb can append a trail line to an unticked entry).
  No entry line, claim text, or other trail line was touched.
- **2026-09-17 — `aide check` after the edits.** Reports `OK (7 warning(s))`,
  no errors. All seven warnings pre-date this item (missing `## Assumptions`
  blocks in 32 old item specs, two Stage-16 human-gate awaiting-decision
  notices, and four Stage-20 acceptance-criterion retraction notices) — none
  names a path this item wrote, and none is a new warning class.
