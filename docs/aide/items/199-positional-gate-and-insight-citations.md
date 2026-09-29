<!-- aide-template: item 3 -->
# Item 199 — Positional gate and insight citations in the records rewritten to IDs

> **Created:** 2026-09-29 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar (maintenance)
> **Queue:** [`../queue/queue-026.md`](../queue/queue-026.md) · Item 199
> **Objectives:** none. This is loop-record maintenance and advances no vision objective.
> **Suggested branch:** `aide/199-positional-gate-and-insight-citations`

---

## Description

Engine 2.20.1's `aide check` warns on every citation of a human gate or an
insight by its position (§1 → human gates, §1 → insights.md). On the base
commit (`f60c3dd`) it reports 59 positional gate citations and 9 positional
insight citations. They sit in 21 merged item specs, in queues 020 and 021, and
in `docs/aide/failure-mode-taxonomy-handover.md` (insight 2026-09-29-a6d6).
This item rewrites each one to the ID of the gate or insight its text means.
The framework names this rewrite as the remedy: "wherever a durable artifact
names a gate — an item spec, a queue file … write its ID".

The rewrite is a change of reference only. What each passage claims stays the
same. There are four kinds of edit:

1. **Gate citations** become the `gate-<hex>` ID of the gate that the
   surrounding text describes. The ID is chosen by reading the text against
   the Gate cells that `aide gate list` prints. It is **not** taken from the
   position the lint names, because positions have not been append-only (A2).
   A list of positions (the pair of external-data gates, rows 1 and 2) becomes
   both IDs. The lint only sees the first number in a list.
2. **Insight citations** become `insight <ID>`. Each position is read against
   the inbox as it stood when the citing line was written, before any ID is
   chosen (A4). A list of positions (item 159 cites five in one sentence) gets
   one `insight <ID>` per number.
3. **Verbatim quotations** keep their words. The positional token inside the
   quotation is replaced by the ID in square brackets, which is the usual
   mark of an editorial change to a quotation (A5).
4. **Four false positives** in the header line of items 040, 041, 043 and 058
   use "gates" as a verb, followed directly by an item number (item 040's
   header gates items 041 and 042). The word "items" is inserted after
   "gates", as in `gates items 041/042`. The item numbers stay the same (A6).

**Not in scope.** The inbox (`insights.md`) and its archives are not touched,
because their claims are immutable and the lint does not read them. No
`progress.md` row, no root document and no framework file changes. The item
does not add a dated correction note to each rewritten spec. This spec and the
git history record the rewrite. No positional citation is fixed outside the
files listed under Authorised paths. On the base commit, `aide check` finds
none anywhere else under `docs/aide`.

## Acceptance Criteria

- [ ] **AC1: `aide check` reports no positional citation.** On the item branch,
  the set of `aide check` warnings containing "cites a human gate by
  position" or "cites an insight by position" is empty. On the base commit it
  holds the 68 warnings enumerated in A3 and A4.

  *Why this is a criterion:* it is the item's deliverable and the queue's
  *Testable* line.

- [ ] **AC2: each gate citation names the gate its text means.** Each gate
  citation listed in A3, and the one wrapped citation A3 adds, now reads as a
  `gate-<hex>` ID. That ID's Gate cell (`aide gate list`) is the gate the
  surrounding text describes. In particular, `items/125-validate-stage28.md`'s
  citation reads `gate-2765` (the spinal-curve-model gate) and not
  `gate-0fdd`.

  *Why this is a criterion:* AC1 is also satisfied by an ID that resolves but
  names the wrong gate. A script that follows the lint's "gate N is … today"
  hint writes exactly that into item 125 (A2).

- [ ] **AC3: each insight citation names the entry its text means.** Each
  insight position number listed in A4 (17 numbers on 11 lines) is replaced by
  `insight <ID>`, with the word `insight` before every ID. Each ID's claim
  (`aide insights list <ID>`) is the entry the surrounding text describes.

  *Why this is a criterion:* insight positions predate the 2026 Q3 archive, so
  today's position-to-ID hint is wrong for any number the archive shifted.
  The word `insight` before each ID is what makes `aide check` confirm that
  the ID resolves (a dangling ID is an error).

- [ ] **AC4: no second position survives in a rewritten list.** No line
  changed by this item keeps a bare gate or insight position after the first
  one, as in `gate-ae46 and 2` or `insight 2026-…, 39`. That is, the
  Validation step 3 grep returns nothing.

  *Why this is a criterion:* the lint matches only the number directly after
  the word, so AC1 passes on a half-converted list.

- [ ] **AC5: quotations are altered only inside brackets.** In each of the five
  verbatim quotations listed in A5, the only change is the positional token,
  which is replaced by the bracketed ID. Every other character of the
  quotation matches the base commit.

  *Why this is a criterion:* without it, AC1 is also satisfied by a
  paraphrase. That would turn a record of what a commit subject or an inbox
  line said into something it did not say.

- [ ] **AC6: the four false-positive headers keep their item numbers.** The
  header line 5 of items 040, 041, 043 and 058 still names the item numbers it
  named on the base commit (041/042, 042, 044–049, 059–065). The only change
  to each line is the word `items` inserted after `gates`.

  *Why this is a criterion:* deleting the parenthetical also satisfies AC1.

## Assumptions

- **A1 (engine 2.20.1):** The lint is `aide.py`'s `_GATE_POSITION_RE`
  (`gate`/`gates`/`human gate`, then an optional `#`, then 1–3 digits) and
  `_positional_citations` (`insight`/`insights`/`inbox`, optionally followed
  by `entry`, then a number, or a bare `entry N` on a line that also says
  insight/inbox). It reads each line on its own, over `docs_dir` minus the
  inbox and its archives. It has **no exemption** for code spans or
  quotations, and no suppression marker. This is why a verbatim quotation
  that keeps its positional token keeps its warning (A5).
- **A2 (measured 2026-09-29):** The insight's premise that "gate positions
  have been append-only" does not hold. On 2026-08-27 (`82d4b7f`, whose
  subject approves the third row by position) the table's third row was the
  spinal-curve-model gate, which is today's `gate-2765` at position 4. The §6
  taxonomy gate (`gate-0fdd`) was inserted above it at position 3 on
  2026-09-03 12:35 (`67c2205`). Rows 5–7 were appended at the end. So a citation of
  position 3 or 4 written before 2026-09-03 12:35 is shifted by one. Among the
  hits, only `items/125-validate-stage28.md:467` falls in that window. Every
  gate citation is therefore rewritten by reading its text, not by
  substituting from the position.
- **A3 (measured 2026-09-29, base `f60c3dd`):** The 59 positional gate
  warnings, by file and line, with the gate each means by its text. IDs are
  from `aide gate list`: `gate-ae46` real segmenter output, `gate-2f91`
  challenging-case data access, `gate-0fdd` §6 taxonomy, `gate-2765` spinal
  curve model, `gate-fb64` Stage 30 specification sign-off, `gate-d024`
  vision v4 §6, `gate-bb24` modes 3/4 sign-off.
  "Pair" below means a citation of rows 1 and 2 together, which becomes
  `gate-ae46` and `gate-2f91`.
  - `failure-mode-taxonomy-handover.md`: 4, 276, 416 → `gate-0fdd`; 394 →
    pair.
  - `items/040…`, `041…`, `043…`, `058…` line 5: false positives (A6).
  - `items/125-validate-stage28.md`: 467 → `gate-2765`. This is a quotation
    (A5).
  - `items/128-…`: 178, 245, 416 → pair.
  - `items/143-…`: 287 → `gate-0fdd`.
  - `items/144-…`: 35, 225, 264 → `gate-0fdd`; 290 → pair.
  - `items/145-…`: 30, 39, 316 → `gate-0fdd`.
  - `items/146-…`: 408 → pair.
  - `items/149-…`: 36, 334, 538 → `gate-0fdd`.
  - `items/150-…`: 579 → `gate-0fdd`. The line already quotes the Gate cell.
  - `items/151-…`: 25, 482, 540, 786 → `gate-fb64`; 836 → `gate-0fdd`; 477,
    1095 → pair.
  - `items/152-…`: 15, 209, 420 → `gate-d024`; 250, 441 → `gate-d024`. The
    last two are quotations (A5).
  - `items/160-…`: 80 → `gate-d024`. This is a quotation (A5).
  - `items/161-…`: 299, 671 → pair.
  - `items/168-…`: 391, 606 → `gate-fb64`. These are the tests that pick the
    Stage 30 sign-off row by a substring.
  - `items/169-…`: 25, 323, 560 (two matches), 742 → `gate-bb24`; 100, 713 →
    pair.
  - `queue/queue-020.md`: 63, 65, 121, 216, 357 → `gate-0fdd`; 119 → pair.
  - `queue/queue-021.md`: 44, 106, 164 → `gate-d024`; 107 → pair.

  There is one more citation that the lint cannot see, because it wraps
  across two lines: `items/148-per-path-mode-attribution.md:55–56` ("gate /
  3 decision 1") → `gate-0fdd`. It is rewritten too. The builder re-reads each
  line against `aide gate list` and does not copy this list blindly. Line
  numbers are the base commit's.
- **A4 (measured 2026-09-29, base `f60c3dd`):** The insight position numbers,
  with what the text says each entry is. The builder takes the ID by reading
  `git show <commit that wrote the line>:docs/aide/insights.md` at position N
  (the `git blame` of the line gives the commit). It then finds that same
  claim in the current inbox or in `docs/aide/insights/archive-2026-Q3.md`,
  and takes its ID from `aide insights list` (`list <ID>` also searches the
  archives).
  (This list names each position as "position N", so that this spec does not
  itself trip the lint.)
  - `failure-mode-taxonomy-handover.md:311`, position 51: the missing
    tissue-plausibility mode.
  - `failure-mode-taxonomy-handover.md:343`, position 46: the entry asking
    for a backward supersession marker on roadmap Stage 20.
  - `items/135-validate-stage29.md:861–862`, positions 37 and 38: the AC17
    allowlist gap and the bullet-status literal bug. The lint sees only 37.
  - `items/150-…:632`, positions 35, 53 and 54: the three deferred entries
    that each name item 150 as the point of decision. The lint sees only 35.
  - `items/150-…:680`, position 35: the vacuous-agreement entry.
  - `items/150-…:684`, position 53: the `dx_mm`/`dy_mm`/`dz_mm` question.
  - `items/150-…:733`, position 50: the rule-side detector ids. This is a
    quotation (A5).
  - `items/159-…:356–358`, positions 38, 39, 45, 47, 52 and 86. The first
    five were already ticked `→ item 159`. Position 86 is the item-158 entry
    of 2026-09-17 on the `_classify_warning` pin. The lint sees only 38.
  - `items/168-…:219`, position 2 in item 168's own list: the sentence points
    to the second bullet of that spec's "The two open insights aimed at this
    ground" list, not to the inbox. That bullet is the item-167 inbox entry
    of 2026-09-20 on rule-id versus detector granularity. The sentence is
    rewritten to name "the second open insight below" and add
    `(insight <ID>)`.

  That makes 17 numbers on 11 lines.
- **A5:** Clarify mode is `assume`. The queue says a citation inside a
  quotation of what `aide check` printed "is kept as quoted, and its ID is
  added beside it". Under A1, that leaves a warning, and AC1 (the queue's
  *Testable* line) then fails. No hit is a verbatim quotation of `aide check`
  output. The baseline notes that name the two awaiting gates by rows 1 and 2
  are paraphrases, and they are rewritten as ordinary citations. The five verbatim quotations that do exist
  are:
  - item 125:467, commit subject `82d4b7f`;
  - item 152:250 and 441, the merge command whose message is commit
    `cfff59e`'s subject;
  - item 160:80, the tick pointer of an archived inbox entry;
  - item 150:733, a claim copied verbatim from the inbox.

  Each quotation keeps its words, and its positional token is replaced by the
  bracketed ID: `human gate [gate-2765]`, `[gate-d024]`, `[insight <ID>]`.
  The bracket marks the alteration. The original stays recoverable from the
  commit or the inbox line, which this item leaves unchanged.
- **A6 (engine 2.20.1):** The "gates 0NN" lint false positive is filed
  upstream as aide-loop#335 (insight 2026-09-29-ea51). The queue asks for the
  reword now, rather than waiting for the upstream fix. The inserted word
  "items" breaks the match (`gates items 041/042`) and makes the phrase
  clearer, so it does not become wrong once #335 ships.

## Implementation Steps

1. **Re-measure.** Run `python .aide/scripts/aide.py check` and
   `python .aide/scripts/aide.py gate list`, and check that the warnings and
   IDs still match A3/A4. Nothing is committed from this step.
2. **Gate citations** (A3). For each line, read the text, choose the gate by
   its Gate cell, and replace the position with the ID. For example, a
   citation of the taxonomy gate becomes `gate-0fdd`, and a citation of rows 1
   and 2 together becomes `human gates gate-ae46 and gate-2f91`. Rephrase only
   enough for the sentence to read. Do not use a blind `sed` over positions:
   item 125 is the counterexample (A2).
3. **Insight citations** (A4). Resolve each number as A4 describes, then write
   `insight <ID>` for every number, repeating the word inside lists.
4. **Quotations** (A5). Replace only the positional token with the bracketed
   ID.
5. **False positives** (A6). In line 5 of items 040, 041, 043 and 058, insert
   `items` after `gates`.
6. **Record the premise correction.** Append one dated trail line under
   insight 2026-09-29-a6d6 with
   `python .aide/scripts/aide.py insights tick 2026-09-29-a6d6 --pointer "<text>"`.
   The entry is already ticked, so the verb appends a trail line. The text
   records that gate positions were not append-only: the taxonomy gate was
   inserted at position 3 on 2026-09-03 (`67c2205`), and item 125's citation
   means `gate-2765`. The claim itself is not edited.
7. Re-run `aide check`. It reports no positional-citation warning and no
   error. This spec is under `docs/aide` too, so a note the builder adds to
   Decisions & Trade-offs names a position as "position N" or "row N", never
   as the word gate or insight followed by the number.

No code, no test and no dependency is added.

## Authorised paths

**May change:**

- `docs/aide/failure-mode-taxonomy-handover.md` — gate and insight citations
- `docs/aide/items/040-committed-synthetic-fixture-corpus-spanning.md` — header false positive
- `docs/aide/items/041-full-pipeline-regression-suite-over.md` — header false positive
- `docs/aide/items/043-reference-distribution-schema-per-level.md` — header false positive
- `docs/aide/items/058-intensity-bearing-synthetic-scan-fixtures.md` — header false positive
- `docs/aide/items/125-validate-stage28.md` — quoted gate citation
- `docs/aide/items/128-relocate-the-reference-verse-v1-integrity-pin.md` — gate citations
- `docs/aide/items/135-validate-stage29.md` — insight citations
- `docs/aide/items/143-correct-the-synthetic-corpus-s-axis-stacking.md` — gate citation
- `docs/aide/items/144-the-failure-mode-specification-module.md` — gate citations
- `docs/aide/items/145-the-eight-hypothesised-modes-specified.md` — gate citations
- `docs/aide/items/146-the-ninth-mode-enters-through-the-lifecycle.md` — gate citation
- `docs/aide/items/148-per-path-mode-attribution.md` — the wrapped gate citation
- `docs/aide/items/149-the-traceability-matrix-becomes-the-conformance-report.md` — gate citations
- `docs/aide/items/150-maintainer-sign-off-of-the-specification.md` — gate and insight citations
- `docs/aide/items/151-validate-stage30.md` — gate citations
- `docs/aide/items/152-retire-the-vision-6-seed-conformance-check.md` — gate citations
- `docs/aide/items/159-the-prerequisite-test-and-import-defects.md` — insight citations
- `docs/aide/items/160-insight-triage-to-a-known.md` — quoted gate citation
- `docs/aide/items/161-validate-stage-31.md` — gate citations
- `docs/aide/items/168-maintainer-sign-off-of-modes-3-and-4.md` — gate and insight citations
- `docs/aide/items/169-validate-stage-32-and-close-stage-20.md` — gate citations
- `docs/aide/queue/queue-020.md` — gate citations
- `docs/aide/queue/queue-021.md` — gate citations

**Asserts against:**

None. This item adds no test.

## Testing Strategy

No test module. Every criterion is a fact about files under `docs/aide/**`,
and §6 forbids a test from reading a living document. Pinning `aide check`'s
warning set in the suite is the shape retired on 2026-09-16. The validator
checks each criterion through the Validation section. No adversarial cases are
named.

**Existing tests to reconcile:** none expected. The sweep ran on 2026-09-29
(grep of `tests/` for the positional shapes and for every file named above).
Only `tests/test_150_maintainer_sign_off.py` reads a file this item changes:
its AC8–AC10 parse the `### Stage-30 maintainer sign-off` section of item
150's spec. This item's edits in that section (lines 680, 684 and 733) touch
no `- Mode N — ` line and no facet line, so the test stays green.
`tests/test_aide_check_no_errors.py` stays green only if every written ID
resolves, which is AC2/AC3's own requirement. Three test comments name
gates by position (`test_137_…:1003`, `test_152_…:4`, and an `aide check`
message fixture in `test_150_…:412`). The gate lint does not read
`tests_dir`, so they are out of scope and left alone.

## Validation

The validator runs these on the item branch, in addition to the suite:

1. **AC1:** `python .aide/scripts/aide.py check` reports no warning containing
   "by position", and no error.
2. **AC2, AC3:** for each line in A3 and A4, read the changed line in
   `git diff` against `aide gate list` or `aide insights list <ID>`, and
   confirm the ID names what the text describes. Check item 125's line
   against `git show 82d4b7f:docs/aide/progress.md`: the third gate row there
   is the spinal-curve-model gate.
3. **AC4:** grep the May-change files for
   `(gate-[0-9a-f]{4,}|insight [0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9a-f]{4,})(,| and| or)\s*#?[0-9]{1,3}\b`.
   It finds nothing.
4. **AC5:** for each quotation in A5, `git diff --word-diff` shows exactly
   one change, the positional token replaced by a bracketed ID.
5. **AC6:** `git diff` of line 5 in items 040/041/043/058 shows only
   `items ` inserted.
6. **Scope:** `python .aide/scripts/aide.py scope` reports OK. Read the whole
   `git diff --word-diff`: every change is a citation token or the few words
   needed around it, and no claim is reworded.

## Dependencies

None. Every spec and queue this item rewrites belongs to a merged item or a
closed queue.

## Decisions & Trade-offs

- **Implementation (2026-09-29).** Every gate citation was read in context and
  mapped to its gate by subject. On the base commit `aide check` reported 59
  positional gate warnings plus 9 positional insight warnings; after the
  rewrite it reports none. A single gate reference absorbs the word it
  followed (a citation of row 3 became `gate-0fdd`, `human` plus row 6 became
  `human gate-d024`); pairs keep the plural (`gates gate-ae46 and gate-2f91`);
  quotations keep the word and bracket the ID (`gate [gate-d024]`).
  Item 148's citation wrapped over two lines and was rewritten too. The
  command shown in the handover's approval step (`aide gate approve`, row 3)
  now names `gate-0fdd`. Insight IDs were taken from the inbox as it stood at
  the commit that wrote each line (position N of that file), matched by claim
  to the current inbox or archive. Item 150's quoted line (position 50) is
  the per-path perturbation and rule-side detector-id entry
  (2026-09-04-4caf), not what today's position 50 holds. Item 159's
  position 86 is the entry whose text concerns the `_classify_warning` pin
  (2026-09-17-f990). A trail line correcting the append-only premise was
  appended under insight 2026-09-29-a6d6.

- **Rewriting merged records.** §1 keeps merged specs as records, and
  `items.md` forbids rewriting an assumption to agree with a later engine.
  This item changes references, not claims. The gate and insight conventions
  both prescribe this edit ("write its ID"; `insights archive` says "rewrite
  them from that list"), and `aide check` sweeps merged specs for exactly
  that reason. The inbox and its archives, whose claims are immutable, are
  not touched.
- **Left open:** whether the four false-positive rewords in items 040, 041,
  043 and 058 should be reverted once aide-loop#335 fixes the lint. They
  stay: the new wording is clearer, and reverting would be another rewrite of
  a merged record.
