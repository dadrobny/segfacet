<!-- aide-template: item 2 -->
# Item 169 — Validate stage 32: Selected-Mode Refinement, and close Stage 20

> **Created:** 2026-09-22 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 169
> **Objectives:** G2, G7, G8
> **Suggested branch:** `aide/169-validate-stage-32-selected-mode`

---

## Description

Stage 32 **D3**, which is also Stage 20's held validation deliverable (Stage 20's
item 142, re-queued under this number at the queue-022 boundary). Items 162–168
each proved their own deliverable against their own tests. This item asks the two
stage-level questions: does the merged tree meet the five criteria in
[`roadmap.md`](../roadmap.md)'s Stage 32 "Validation / acceptance" block, and do
Stage 20's criteria 3–5 — each carrying a retraction trail that routes its
attestation through this item — now hold when measured from a clean clone? It
records the measured answer in `progress.md`, one criterion at a time, **including
where the answer is no.** It fixes nothing it finds.

**Stage 32's criterion 1 is expected to stay open, and that is the planned
outcome, not a failure of this item.** Human gate 7 was resolved on 2026-09-22
with **both** modes 3 and 4 signed off at `outcome = "intermediate-state"`.
Conditions 1–5 of the roadmap's six-condition bar hold live for both modes
(measured below), but condition 6 asks for a maintainer sign-off *at the bar*,
and `intermediate-state` is by its own record a statement that the mode is not
there yet: the maintainer review of 2026-09-22 (the `insights.md` entries of that
date) names what must change first, and that work is queue 023's. Queue-022's
entry for this item is explicit — *"If mode 4 does not reach the bar, item 169
records that and the stage stays open — it is not forced."* So criterion 1 is
left unticked with the measured reason, and Stage 32's other four criteria are
attested on their own evidence.

**"From a clean clone" means a fresh `git clone` with its own venv.** Item 135
set the rule and item 151 adopted it for stage validations. CLAUDE.md's Gotchas
say why a second tree reached through `PYTHONPATH` is invalid: the editable
install's meta-path finder resolves `segfacet` ahead of `sys.path`, so the second
tree is silently shadowed and every "clean" result is invalid with no error at
all.

**How the replay is built.** Every stage-level claim Stage 32 makes already has
an in-suite check, merged with the item that made it true:

- `tests/test_162_corpus_exercise_report.py` — the per-rule and per-operator
  exercise report.
- `tests/test_163_specificity_ratchet.py` — measured firing equals authored
  expected firing, per case.
- `tests/test_165_mode_4_at_the_bar.py` — `traceability.bar_conditions` over
  conditions 1–5.
- `tests/test_168_maintainer_sign_off.py` — the `ModeSignOff` records and the
  gate's coherence.
- `tests/test_151_stage30_validation.py` — every mode row's title, derived
  status and edge rungs against the committed rendering.

The replay runs those checks by node id in the clone. It does **not** copy them
into a new module. The new module, `tests/test_169_stage32_validation.py`, holds
only what no merged test covers: the live-state invariants behind the numbers
this item writes into `progress.md`, and the Stage 20 bullet sweep.

**Stage 20's ladder-base bullet.** Stage 20's item-141 deliverable still reads
⏸️ although its work landed in Stage 31 as item 154's re-measurement. ⏸️ is
terminal-but-not-shipped in the rollup, so a single ⏸️ bullet keeps Stage 20 from
ever reaching ✅. Closing Stage 20 therefore includes resolving that bullet to ❌
with a dated pointer to item 154 — the same shape the queue-022 boundary used for
items 139, 140 and 142's retired numbers. With that bullet ❌ and this item's own
Stage 20 bullet ✅ at merge, every Stage 20 deliverable is ✅ or ❌ and the stage
rolls up on its own.

**What is measured already (2026-09-22, on this branch's base, engine 1.59.2).**
These are starting points. The item re-measures every one from the clone, and
where a re-measurement differs, the measured value wins and Decisions records the
difference.

- **Derived status over the 16 specification modes:** validated 7, implemented 2,
  specified 0, proposed 7.
- **Derived mode rungs:** synthetic-demonstrable 6, needs-real-data 2,
  structurally-unobservable 1, none 7.
- **Conformance:** 16 committed corpus cases (12 geometric + 4 intensity); every
  case's measured firing equals its authored `expected_firing`.
- **Exercise:** 10 registered rules — 7 exercised, 3 (`bounds`,
  `reference_delta`, `intensity_reference_delta`) unexercised with reason
  `needs-real-data`; 12 registered operators, all used. Both direction reports
  read `complete=True, holes=()`.
- **The bar:** `traceability.bar_conditions(3)` and `bar_conditions(4)` each
  report conditions 1–5 `met=True`. Mode 3's deciding detector is
  `fragmentation/neighbour_contact`, mode 4's is `fragmentation/islands`. Both
  modes' `MODE_SIGN_OFFS` records read `outcome="intermediate-state"`, dated
  2026-09-22. **No mode is at the bar.**
- **Cross-mode margins** (`segfacet.eval.severity_ladder`, measured by item 154 on
  2026-09-16): `displace inf`, `fragment inf`, `inject_islands 112.0`,
  `relabel_swap inf`, `remove_level inf`, `crop_at_border 0.3585`,
  `sequence_break inf`, `force_overlap 1.038`; couplings
  `crop_at_border → unanchored_foreground_fraction 2.79` and
  `force_overlap → unanchored_foreground_fraction 0.9629`. `RECORDED_MARGINS`
  carries no ladder for item 166's `split` operator.
- **`aide check`:** `OK (8 warning(s))` — 1 assumptions-block warning, 2
  awaiting-a-decision warnings (gates 1 and 2), 5 retracted-criterion warnings
  (Stage 20 criteria 1, 3, 4 twice, 5).

**In scope:**

- the clean-clone replay and its measurements;
- the Stage 32 and Stage 20 acceptance bookkeeping in `progress.md`, through
  `aide progress accept` / `amend`, plus the hand-written reason annotation §1
  allows beside a box left unticked;
- resolving Stage 20's item-141 bullet to ❌;
- the in-suite invariant module;
- one-line `insights.md` findings.

**Not in scope:**

- Fixing anything the replay finds. Every divergence becomes a finding, never a
  remediation — the 2026-09-22 review's work is queue 023's.
- Forcing Stage 32's criterion 1. No mode is signed at the bar, and no sign-off
  is edited here.
- Editing Stage 32's D0 or D3 deliverable bullets, which carry no item marker
  (A5), or any Environment-Gated row (A8).
- Editing `roadmap.md`, `vision.md` or `src/segfacet/**`.
- Ticking, rewording or archiving any existing `insights.md` entry.

## Acceptance Criteria

Two kinds of criterion sit below, as in items 151 and 161. **In-suite** criteria
are pinned by `tests/test_169_stage32_validation.py`. **Replay** criteria are
executed by the builder and re-executed by the validator; their observed output
is recorded verbatim in Decisions & Trade-offs, and they add no test. "The clone"
is AC1's clone, and "passes in the clone" means the named node ids, run from the
clone's own venv, exit `0` with no skip among them. A criterion annotated
*(closes Stage N criterion M)* is evidence for that criterion; a criterion
carrying no annotation closes none.

### The clean-clone rig

- [ ] **AC1: the replay runs in a fresh clone whose code is the clone's own.**
  (Replay.) Clone this branch into the session scratchpad, then bootstrap the
  clone's venv with `python <clone>/.aide/scripts/aide.py --repo <clone> env
  --bootstrap`. Record the clone path, the clone's `HEAD` SHA (equal to this
  branch's tip at clone time), and `segfacet.__file__` as printed by `python -P`
  from the clone's venv, which resolves under the clone. A resolution under the
  working checkout invalidates every clone result below.

### Every generated artifact regenerates byte-identically

- [ ] **AC2: each committed generated artifact equals a fresh regeneration, byte
  for byte, in the clone.** (Replay.) From the clone's venv, regenerate each of
  the following into a temporary directory and compare `read_bytes()` with the
  committed file. Every comparison is equal.
  - `docs/aide/failure_modes.generated.json` and `.md` —
    `python -P -m segfacet.failure_modes --json <tmp>/fm.json --md <tmp>/fm.md`
  - `docs/aide/traceability_matrix.generated.json` and `.md` —
    `python -P -m segfacet.traceability --json <tmp>/tm.json --md <tmp>/tm.md`
  - `docs/aide/feature_catalogue.generated.json` and `.md` —
    `python -P -m segfacet.catalogue --json <tmp>/fc.json --md <tmp>/fc.md`
  - `docs/aide/golden_evidence.generated.json` —
    `python -P -m segfacet.golden_evidence --out <tmp>/ge.json`
  - `tests/corpus/manifest.json` and every file it names —
    `python -P -m segfacet.synth.corpus --out <tmp>/corpus`
  - `tests/corpus/intensity/manifest.json` and every file it names —
    `python -P -m segfacet.synth.intensity --out <tmp>/intensity`

  Record the artifact list with each comparison's result. A mismatch is recorded
  with its diff and is not repaired here.

### Stage 20 criteria 3 and 4 / Stage 32 criterion 4

- [ ] **AC3: the specificity assertion is driven over every committed corpus case
  of both corpora, and every case agrees.** (Replay.)
  `tests/test_163_specificity_ratchet.py` passes in the clone, in full. Record
  the collected node count, and — read from
  `segfacet.traceability.build_matrix().conformance` in the clone — the case ids
  driven, split by corpus, and the count of cases whose `agrees` is `False`
  (expected `0`). The driven case-id set equals the union of both committed
  manifests' `case_id` values, so no case is exempt.
  *(closes Stage 20 criterion 4)* *(closes Stage 32 criterion 4)*
- [ ] **AC4: every registered rule and every registered operator is exercised by a
  case or recorded as unexercised with a reason.** (Replay.)
  `tests/test_162_corpus_exercise_report.py` passes in the clone, in full.
  Record, from `build_matrix().exercise` in the clone, each rule's state and —
  where unexercised — its reason and reason modes, each operator's state, and
  both `DirectionReport`s. Neither direction report carries a hole.
  *(closes Stage 20 criterion 3)* *(closes Stage 32 criterion 4)*

### The cross-mode margins

- [ ] **AC5: the severity-ladder margins and couplings are re-measured in the
  clone and compared with the committed constants.** (Replay.) From the clone's
  venv, run `score_harness(run_severity_harness())` from
  `segfacet.eval.severity_ladder`. Record the printed summary, each ladder's
  margin, each coupling, and the `passed` value. Compare every value with
  `RECORDED_MARGINS` / `KNOWN_CROSS_MODE_COUPLINGS` read fresh from the clone.
  Record any operator registered in `synth` that has no ladder — item 166's
  `split` is the expected case. A divergence or a missing ladder is recorded in
  Decisions and appended to `insights.md` as one line; nothing is retuned here.

### Stage 20 criterion 5 / Stage 32 criterion 5 — the detection count

The three clauses below are written into the shared evidence note by AC13's
verbs. Each in-suite test recomputes its clause's integers from
`segfacet.failure_modes` and asserts equality; no integer is pinned as a
literal, and each test reads the **last** matching clause in the section, since
`aide progress amend` appends a correction rather than rewriting (item 151's
AC35 precedent).

- [ ] **AC6: the status-count clause equals the live derivation.** (In-suite.)
  The last match of
  `derived status counts over (\d+) modes: validated (\d+), implemented (\d+), specified (\d+), proposed (\d+)`
  in `progress.md`'s Stage 20 section has `N == len(SPECIFICATION)` and each
  count equal to the number of modes whose `derive_status(mode)` is that status.
  *(closes Stage 20 criterion 5)*
- [ ] **AC7: the rung-count clause equals the live derivation.** (In-suite.) The
  last match of
  `derived mode rung counts: synthetic-demonstrable (\d+), needs-real-data (\d+), structurally-unobservable (\d+), none (\d+)`
  in the same section has each count equal to the number of modes whose
  `derive_mode_rung(mode)` is that rung, with `None` counted as `none`.
  *(closes Stage 20 criterion 5)*
- [ ] **AC8: the refined/bar/drafts clause equals the live partition.**
  (In-suite.) The last match of
  `modes refined by stage 32: ([0-9, ]+); at the fully-specified bar: (\S+); left as documented drafts: (\d+)`
  in the same section has: the first group equal to `sorted(MODE_SIGN_OFFS)`
  rendered comma-separated; the second group equal to the same rendering of the
  modes at the bar (AC9's set), or the literal `none` when that set is empty; and
  the third group equal to `len(SPECIFICATION) - len(MODE_SIGN_OFFS)`.
  *(closes Stage 32 criterion 5)*

### Stage 32 criterion 1 — the bar, and why it stays open

- [ ] **AC9: the set of modes meeting all six bar conditions, recomputed live, is
  empty.** (In-suite.) For every mode id in `SPECIFICATION`, the mode is at the
  bar iff every record `traceability.bar_conditions(mode_id, catalogue=...)`
  returns has `met is True` **and** `failure_modes.mode_sign_off(mode_id)` is not
  `None` with `outcome == "at-the-bar"`. The resulting set is empty. The test
  also records, per mode carrying a sign-off, which of the two halves failed.
- [ ] **AC10: Stage 32's criterion-1 box is unticked and carries a dated reason
  naming the measured cause.** (In-suite.) The first acceptance box of
  `progress.md`'s Stage 32 section is `- [ ]` and its box text contains a
  non-empty `*(…)*` annotation that names item 169, an ISO date, and each mode id
  carrying a sign-off whose `outcome != "at-the-bar"` — recomputed from
  `MODE_SIGN_OFFS`, not matched against a literal list.

### Stage 32 criteria 2 and 3

- [ ] **AC11: every mode this stage refined carries a maintainer sign-off with
  date and outcome in the specification module.** (Replay.)
  `tests/test_168_maintainer_sign_off.py` passes in the clone, in full, and
  `tests/test_165_mode_4_at_the_bar.py` passes in the clone, in full. Record
  `sorted(MODE_SIGN_OFFS)` read from the clone, and each record's `date` and
  `outcome`. That key set equals the modes queue-022 selected for refinement.
  *(closes Stage 32 criterion 2)*
- [ ] **AC12: every mode not refined keeps a complete entry and is reported at its
  derived status in the rendering.** (Replay.) In the clone,
  `tests/test_151_stage30_validation.py::test_ac3_every_mode_row_title_authored_status_and_edge_rungs_match_specification`
  and `::test_ac18_status_matches_independent_recomputation_and_committed_rendering`
  pass. Record the per-mode status table they recompute, and confirm no mode is
  absent from `docs/aide/failure_modes.generated.md` and none renders without a
  status. *(closes Stage 32 criterion 3)*

### Closing Stage 20's held bullet

- [ ] **AC13: no Stage 20 deliverable bullet is left ⏸️, and the item-141 bullet
  reads ❌ with a pointer to item 154.** (In-suite.) In `progress.md`'s Stage 20
  section, no deliverable bullet's leading icon is ⏸️; the one bullet carrying
  the marker `*(Item 141)*` leads with `❌`, and its bullet text names item 154
  and an ISO date on or after 2026-09-22.

### Bookkeeping, environment, check, suite

- [ ] **AC14: each criterion is attested or annotated through the matching verb,
  and no box is ticked on evidence that failed.** (Replay.) Record the exact
  command and the evidence or reason text for each criterion:
  - **Stage 20 criteria 3, 4 and 5**, and **Stage 32 criteria 2, 3, 4 and 5**,
    where their ACs hold:
    `python .aide/scripts/aide.py progress accept <stage> --criterion N --evidence "<text>"`.
    Each text names the ACs above and the clone commit; Stage 20's criterion 5
    and Stage 32's criterion 5 share the three clauses of AC6–AC8.
  - **Stage 32 criterion 1**: it stays unticked. A hand-written annotation
    ` *(not attested YYYY-MM-DD, item 169: <measured reason>)*` is appended to
    the end of its box's last line, and one `gap` entry is appended to
    `docs/aide/insights.md` naming `stage 32 criterion 1`, both sign-off outcomes,
    and that the remedial work is queue 023's.
  - **Stage 20 criteria 1 and 2** are already ticked and are not in this item's
    routing; they are left untouched (A3).
- [ ] **AC15: the environment profiles are evaluated and the gated table is left
  unchanged, for a recorded reason.** (Replay.) Record the output and exit code of
  `python .aide/scripts/aide.py env` and of `env --profile pyradiomics`,
  `--profile docker` and `--profile gpu`. `progress.md`'s Environment-Gated
  Capability Verification table has no row whose "Introduced by" column names
  Stage 32 (verified by reading its rows), the table is left unchanged, and
  Decisions records the reason: Stage 32 introduced no gated capability and no
  replay above depends on a profile.
- [ ] **AC16: `aide check` reports no error, and every warning is recorded.**
  (Replay.) After the bookkeeping, `python .aide/scripts/aide.py check` reports no
  error. Record every warning line verbatim and compare the set with the
  2026-09-22 baseline of 8 warnings recorded in the Description. The baseline is
  recorded for comparison and **pinned nowhere in the suite**, by count or by
  class.
- [ ] **AC17: the full configured suite is green in a fresh clone of the final
  commit.** (Replay.) Once every commit of this item has landed, bring AC1's clone
  up to the branch tip with `python <clone>/.aide/scripts/aide.py --repo <clone>
  sync --item 169`, re-print AC1's resolution proof, and run the configured suite
  from the clone's venv with no explicit path, so `pyproject.toml`'s `testpaths`
  picks up both `tests` and `.aide/scripts/tests` (item 161's AC19 correction).
  Run it in the **foreground**, split into chunks if one call would exceed the
  tool timeout. Record pass, skip and fail counts, the commit, and the reason for
  every environment-gated skip. The run has no failures. A skip is never recorded
  as verification.

## Assumptions

- **A1: bar condition 6 is read as a sign-off whose `outcome` is `at-the-bar`.**
  `failure_modes.SIGN_OFF_OUTCOMES` is a closed two-member vocabulary,
  `("at-the-bar", "intermediate-state")`, and both shipped records' notes open
  with "Signed at a recorded intermediate state, not at the bar." So a mode signed
  `intermediate-state` does not satisfy condition 6, and AC9's predicate reads the
  outcome rather than the mere presence of a record. This is the defensible
  default under `loop.clarify = "assume"`; the alternative reading — that any
  dated sign-off satisfies condition 6 — would let Stage 32 claim a mode at the
  bar that its own sign-off says is not, which is the shape §1 rules out.
- **A2: Stage 32's criterion 1 stays open, and the stage stays 🚧.** Follows from
  A1 and from queue-022's item-169 entry ("If mode 4 does not reach the bar, item
  169 records that and the stage stays open — it is not forced"), which gate 7's
  own resolution text repeats ("Item 169 attests Stage 32 with criterion 1 open
  and closes Stage 20"). No new human gate is raised: the decision this item would
  need has already been made and recorded.
- **A3: Stage 20's criteria 1 and 2 are out of this item's routing.** Only
  criteria 3, 4 and 5 carry retraction trails naming this item (2026-09-02 and
  2026-09-20). Criterion 1 is ticked with a 2026-09-03 correction and criterion 2
  is ticked from item 137; both are left exactly as they stand. Re-attesting a
  ticked box needs `amend`, and nothing measured here corrects either.
- **A4 (engine 1.59.2): no verb writes ❌ or annotates an unticked box.** `aide
  progress set` takes only `in-progress | in-review | done`, and `accept` /
  `amend` / `retract` act on acceptance boxes, not deliverable bullets. So AC13's
  ⏸️ → ❌ flip and AC14's criterion-1 reason annotation are hand edits to
  `progress.md` — the item 151 A4 / item 161 A6 precedent. Both are inside the
  always-authorised `progress.md`.
- **A5 (engine 1.59.2): Stage 32's D0 and D3 deliverable bullets carry no
  `*(Item NNN)*` marker.** This item's own deliverable bullet lives in Stage 20
  (`📋 Stage 20 end-to-end validation … *(Item 169)*`), so `aide progress set 169
  …` and `aide merge` move that bullet and no Stage 32 bullet. Stage 32 therefore
  stays 🚧 after this item, which agrees with criterion 1 being open. This item
  does not hand-edit either unmarked bullet; that Stage 32's D0 and D3 bullets are
  unmarked while their work has landed is recorded as one `insights.md` line, not
  repaired here.
- **A6: "every generated artifact" is exactly AC2's list.** The queue entry names
  the failure-mode rendering, the traceability matrix, the feature catalogue, the
  exercise report and both corpus manifests; the exercise report is a section of
  `traceability_matrix.generated.*` (item 162) rather than a file of its own, and
  `golden_evidence.generated.json` is added because it is the sixth committed
  `docs/aide/*.generated.*` artifact and regenerates from the same tree. The
  corpus comparison covers every file each manifest names, `.nii.gz` fixtures
  included — `.gitattributes` pins those `binary` and the manifests `text eol=lf`,
  so the CLAUDE.md CRLF gotcha does not apply to either.
- **A7: every number in the Description is a starting point**, measured
  2026-09-22 on this branch's base. Where a clone re-measurement differs, the
  measured value wins, and Decisions records the difference row by row.
- **A8: this item introduces no environment-gated capability.** No row of
  `progress.md`'s verification table names Stage 32, no `[validation]` profile
  gates any criterion above, and AC15 evaluates the three profiles for the record
  only. The only external needs are `git` and disk space for one clone and its
  venv.
- **A9: the `split` operator legitimately has no severity ladder.** Item 166 added
  the operator and its corpus case; item 154 measured `RECORDED_MARGINS` on
  2026-09-16, before it existed. AC5 records the gap as a finding rather than
  treating it as a regression, because widening the ladder set is a measurement
  item, not a validation one.

## Implementation Steps

1. **Preconditions.** `python .aide/scripts/aide.py status` — confirm items
   162–168 are ✅. Record `aide check`'s baseline (AC16).
2. **Rig (AC1).** Clone this branch into the scratchpad, bootstrap the clone's
   venv with the clone's own `aide env --bootstrap`, print the resolution proof.
3. **Artifacts (AC2).** Run the six regeneration commands into a scratch
   directory from the clone's venv and compare bytes. Reuse each module's own
   `--json` / `--md` / `--out` argument; write no new generator and no comparison
   helper beyond `pathlib.Path.read_bytes`.
4. **Named checks (AC3, AC4, AC11, AC12).** Run each module or node-id group in
   the clone, in the **foreground**, and record exit codes and counts.
5. **Measurements (AC3, AC4, AC5, AC11).** From the clone's venv, read
   `traceability.build_matrix()`'s `conformance` and `exercise` reports,
   `failure_modes.MODE_SIGN_OFFS`, and run
   `severity_ladder.score_harness(run_severity_harness())`. Record each verbatim.
   `build_matrix()` and `catalogue.build_catalogue(strict=True)` are called once
   each and their results reused, the module-scoped-drive idiom items 149, 162,
   163 and 165 established.
6. **Findings.** Append one `insights.md` line per divergence (AC5), one for the
   criterion-1 gap (AC14), and one for A5's unmarked Stage 32 bullets. Tick,
   reword or archive no existing entry.
7. **Write `tests/test_169_stage32_validation.py` (AC6–AC10, AC13).** The
   test-writer does this. It needs no production change. Stage-section and
   acceptance-box location go through `.aide/scripts/aide.py`'s `stage_section` /
   `acceptance_boxes`, loaded in-process — the `test_150` / `test_161` idiom —
   never a private reimplementation.
8. **Stage 20's held bullet (AC13).** Hand-edit the `*(Item 141)*` bullet's
   leading icon from ⏸️ to ❌ and append the dated pointer to item 154. Update
   `_HELD_ITEMS[141]` in `tests/test_150_maintainer_sign_off.py` to `"❌"` in the
   same commit — that module's own comment asks the first item landing any of
   139–142 to do exactly this.
9. **Bookkeeping (AC6–AC8, AC14).** Stage by stage, criterion by criterion in
   ascending order, run the matching `aide progress accept`, and hand-annotate
   Stage 32's criterion 1. Stage 20's criterion-5 and Stage 32's criterion-5
   evidence each carry AC6–AC8's three clauses verbatim.
10. **Environment (AC15).** Run `aide env` and the three profile checks.
11. **Check (AC16).** Re-run `aide check` and compare against the baseline.
12. **Suite (AC17).** Bring the clone up to the final commit, run the configured
    suite, record the counts, then delete the clone.
13. Record everything in Decisions & Trade-offs.

## Authorised paths

**May change:**

- `tests/test_169_stage32_validation.py` — the in-suite invariant module
  (AC6–AC10, AC13)
- `tests/test_150_maintainer_sign_off.py` — `_HELD_ITEMS[141]` moves from `⏸️`
  to `❌` with AC13, as that module's own note requires

`docs/aide/progress.md` (Stage 20's and Stage 32's acceptance boxes, Stage 20's
item-141 bullet, and this item's own Stage 20 bullet via `aide progress set`),
`docs/aide/insights.md` (appended findings) and this spec are always authorised.
No other part of `progress.md` is edited.

**Asserts against:**

- `src/segfacet/failure_modes.py` — `SPECIFICATION`, `MODE_SIGN_OFFS`,
  `derive_status`, `derive_mode_rung` recomputed live (AC6–AC11)
- `src/segfacet/traceability.py` — `bar_conditions`, and `build_matrix`'s
  `conformance` and `exercise` reports (AC3, AC4, AC9)
- `src/segfacet/catalogue.py` — the catalogue `bar_conditions` reads (AC9)
- `src/segfacet/eval/severity_ladder.py` — `RECORDED_MARGINS` and
  `KNOWN_CROSS_MODE_COUPLINGS` re-measured against a fresh harness run (AC5)
- `.aide/scripts/aide.py` — `stage_section` / `acceptance_boxes` loaded
  in-process (AC10, AC13)
- `docs/aide/roadmap.md` — Stage 32's six-condition bar and both stages'
  acceptance bullets (AC9, AC14)
- `docs/aide/failure_modes.generated.json` — regenerated and compared (AC2)
- `docs/aide/failure_modes.generated.md` — regenerated and compared; the
  per-mode status rendering (AC2, AC12)
- `docs/aide/traceability_matrix.generated.json` — regenerated and compared (AC2)
- `docs/aide/traceability_matrix.generated.md` — regenerated and compared (AC2)
- `docs/aide/feature_catalogue.generated.json` — regenerated and compared (AC2)
- `docs/aide/feature_catalogue.generated.md` — regenerated and compared (AC2)
- `docs/aide/golden_evidence.generated.json` — regenerated and compared (AC2)
- `tests/corpus/manifest.json` — regenerated and compared; the case-id set AC3
  measures no-exemption against (AC2, AC3)
- `tests/corpus/intensity/manifest.json` — regenerated and compared; the
  intensity half of AC3's case-id set (AC2, AC3)
- `tests/test_162_corpus_exercise_report.py` — named checks (AC4)
- `tests/test_163_specificity_ratchet.py` — named checks (AC3)
- `tests/test_165_mode_4_at_the_bar.py` — named checks (AC11)
- `tests/test_168_maintainer_sign_off.py` — named checks (AC11)
- `tests/test_151_stage30_validation.py` — named checks (AC12)

## Testing Strategy

New module `tests/test_169_stage32_validation.py`, deliberately small: six AC
tests (AC6, AC7, AC8, AC9, AC10, AC13) plus the five cases below. Every replay
criterion is executed, not tested — its evidence is the recorded output in
Decisions, which the validator re-executes.

Each AC test recomputes its subject from the primary source — `SPECIFICATION`,
`MODE_SIGN_OFFS`, `derive_status`, `derive_mode_rung`, `bar_conditions` — and
compares it with what `progress.md` says. **No integer, mode id or rung name is
written into the module as a literal expectation.** One module-scoped fixture
builds `catalogue.build_catalogue(strict=True)` once and one holds the per-mode
`bar_conditions` results, the idiom test_149/test_162/test_163/test_165 use; no
test body calls `build_catalogue()` a second time.

**Adversarial cases.** Each is an in-memory `progress.md` text or a constructed
sign-off mapping passed to the same helper; none writes a file or touches the
shipped mapping.

- **`status-clause-missing`**: a section carrying no status-count clause yields no
  match — guards a parser that would read an absent note as agreement, letting an
  unwritten number pass as measured.
- **`status-clause-off-by-one`**: a clause whose `validated` count is the live
  value plus one fails — guards the exact defect item 167's 2026-09-20 correction
  found, a hardcoded literal that happened to equal live state at writing.
- **`refined-clause-names-a-wrong-mode`**: a clause reading `modes refined by
  stage 32: 3, 5` fails against a `MODE_SIGN_OFFS` of `{3, 4}` — guards a
  hand-written clause drifting from the mapping it claims to summarise.
- **`bar-predicate-is-not-vacuous`**: over a constructed mapping in which one mode
  whose conditions 1–5 all hold carries `outcome="at-the-bar"`, AC9's predicate
  returns that mode — guards a predicate that yields the empty set for the wrong
  reason, such as an outcome string that never matches.
- **`deferred-bullet-anywhere-is-flagged`**: an in-memory Stage 20 section whose
  ⏸️ bullet is some deliverable **other** than item 141's is flagged — guards a
  scan that checks only the item-141 line and would let another deferred bullet
  block the rollup unnoticed.

**Discipline.**

- The module asserts no `aide check` warning count or warning class (item 159
  removed those pins from test_146 and test_150), no suite total, no engine
  version and no severity-ladder constant. Those are dated measurements later
  verbs and stages legitimately move; they live in `progress.md`'s evidence and in
  Decisions.
- It pins no `insights.md` entry. Were one ever read, it would have to search
  `docs/aide/insights/archive-*.md` as well as the inbox (CLAUDE.md gotcha).
- It reads no git history and needs no clone, network or profile.

**Existing tests to reconcile.**

- `tests/test_150_maintainer_sign_off.py` — `_HELD_ITEMS = {139: "❌", 140: "❌",
  141: "⏸️", 142: "❌"}` drives
  `test_ac13_each_stage_20_held_item_bullet_carries_its_recorded_icon`. AC13
  flips item 141's bullet to ❌, so `_HELD_ITEMS[141]` becomes `"❌"` and the
  comment above it records that item 169 landed the change. That module's own note
  asks for exactly this and names the authorised-paths consequence; without it the
  first validation round fails on a stale assertion rather than on new code.
- Swept 2026-09-22 across `tests/`: no other module parses Stage 20's or Stage
  32's acceptance boxes or deliverable bullets. `test_135`, `test_146`,
  `test_151` and `test_161` mention Stage 20 only in prose or an in-memory
  fixture. `tests/test_aide_check_no_errors.py` asserts no *errors* and says
  nothing about warnings, so the bookkeeping moves no assertion there.

## Validation

This item **is** the stage validation, so the validator re-executes the replay
criteria, not only the suite, and confirms each Decisions record against its own
run:

- the rig and the resolution proof (AC1);
- each artifact's byte comparison (AC2);
- each named-check group's exit code and the measured reports (AC3, AC4, AC11,
  AC12);
- the harness print and the constant comparison (AC5);
- the three evidence clauses in `progress.md` against a fresh read of
  `failure_modes` (AC6–AC8);
- the bar recomputation and the criterion-1 annotation (AC9, AC10);
- the Stage 20 bullet sweep (AC13);
- each `aide progress` command against the `progress.md` diff (AC14);
- the profiles (AC15);
- `aide check` (AC16);
- the full-suite counts from a fresh clone of the final commit (AC17);
- `python .aide/scripts/aide.py scope`.

**Environment gating.** No criterion depends on a `[validation]` profile.
`pyradiomics`, `docker` and `gpu` are evaluated and recorded only (AC15).

**Honest downgrade.** A replay that cannot run is recorded as **not performed**,
naming what was missing, and its criterion stays unticked with that reason. A
skip-clean run is never evidence.

## Dependencies

- **Item 162** — the per-rule and per-operator exercise report (AC4, Stage 20
  criterion 3).
- **Item 163** — the specificity ratchet over both corpora (AC3, Stage 20
  criterion 4).
- **Item 164** — first-class detector ids, which make "a detector serves no other
  mode" mechanical (AC9, bar condition 4).
- **Item 165** — `traceability.bar_conditions`, the live check behind conditions
  1–5 (AC9, AC11).
- **Item 166** — mode 3's split operator and corpus case (AC2, AC3, AC5).
- **Item 167** — mode 3's feature and detector (AC9, AC12).
- **Item 168** — the `ModeSignOff` records for modes 3 and 4, written after human
  gate 7 was resolved (AC9, AC10, AC11). Gate 7 — `Blocks: 168, 169` — was
  approved 2026-09-22.

**Downstream:** queue 023 carries the 2026-09-22 maintainer review's work — the
lordotic corpus base, the re-authored operators, `neighbour_contact` moving into
its own rule, and mode 4's `island_distance_from_main_body_mm`. An item there
that brings a mode to the bar re-opens Stage 32's criterion 1 on its own
evidence; it corrects this item's `progress.md` notes with `aide progress amend`,
never by editing them in place. This item's dated measurements stand as the
record of what was true on 2026-09-22.

## Decisions & Trade-offs

**Rig (AC1).** Clean clone at
`/tmp/claude-1005/-mnt-data-spine-codes-SegFACET/954f1565-db96-4372-a5d1-22b92ab8fdff/scratchpad/clone169`,
created with `git clone <working checkout> <clone>` and checked out onto this
branch. Bootstrapped with `python <clone>/.aide/scripts/aide.py --repo <clone>
env --bootstrap` — `aide env: bootstrap done (ok: venv is Python 3.11; `import
segfacet` succeeds; `import pytest` succeeds)`. `segfacet.__file__` from the
clone's own venv (`<clone>/.venv/bin/python -P -c "import segfacet; print(segfacet.__file__)"`)
resolved to `<clone>/src/segfacet/__init__.py` — under the clone, not the
working checkout. Clone `HEAD` at clone time: `2c4b62bcf2dcad5f37ec88273a74eae432b06df2`,
equal to this branch's tip at that moment.

**Artifacts (AC2).** All six regeneration commands ran with rc 0 from the
clone's venv, output into a scratch directory. 27 byte comparisons (7 doc
artifacts + 2 manifests + 18 named fixture files: 11 geometric `.nii.gz` +
5 intensity fixtures, matching each manifest's `case_id` set), all equal:
`docs/aide/failure_modes.generated.{json,md}`,
`docs/aide/traceability_matrix.generated.{json,md}`,
`docs/aide/feature_catalogue.generated.{json,md}`,
`docs/aide/golden_evidence.generated.json`, `tests/corpus/manifest.json` +
every named fixture, `tests/corpus/intensity/manifest.json` + every named
fixture. Zero mismatches.

**AC3 (Stage 20 criterion 4 / Stage 32 criterion 4).**
`tests/test_163_specificity_ratchet.py -v` in the clone: 22 passed, 0 failed.
`traceability.build_matrix().conformance` in the clone: 16 cases driven — 12
geometric (`clean_control`, `crop_at_border`, `displace`, `force_overlap`,
`fragment`, `fuse_adjacent`, `inject_islands`, `relabel_swap`, `remove_level`,
`remove_level_relabel`, `sequence_break`, `split`) and 4 intensity
(`clean_hu`, `degenerate_uniform`, `implausible_metal`,
`implausible_soft_tissue`); 0 cases disagree. This set equals the union of
both committed manifests' `case_id` values (16 cases named in the two
manifests: 12 + 4).

**AC4 (Stage 20 criterion 3 / Stage 32 criterion 4).**
`tests/test_162_corpus_exercise_report.py -v` in the clone: 18 passed, 0
failed. `build_matrix().exercise` in the clone: 10 registered rules — 7
exercised (`border`, `coverage`, `fragmentation`, `intensity`, `mislabel`,
`overlap`, `sequence`), 3 unexercised with reason `needs-real-data`
(`bounds`: modes 1,2,3,4; `reference_delta`: modes 1,2,3,4,8;
`intensity_reference_delta`: mode 16); 12 registered operators, all `used`
(`crop_at_border`, `displace`, `force_overlap`, `fragment`, `fuse`,
`identity`, `inject_islands`, `relabel_swap`, `remove_level`,
`remove_level_relabel`, `sequence_break`, `split`). Both `DirectionReport`s
read `complete=True, holes=()`. Every number matches the Description's
2026-09-22 starting point exactly — no divergence.

**AC5 (cross-mode margins).** `score_harness(run_severity_harness())` in the
clone reproduced every recorded value exactly: `displace inf`, `fragment
inf`, `inject_islands 112.037…` (rounds to the recorded `112.0`),
`relabel_swap inf`, `remove_level inf`, `crop_at_border 0.358518…` (rounds to
`0.3585`), `sequence_break inf`, `force_overlap 1.038626…` (rounds to
`1.038`); `passed=True`. Couplings: `crop_at_border →
unanchored_foreground_fraction 2.7892…` (rounds to `2.79`), `force_overlap →
unanchored_foreground_fraction 0.9628…` (rounds to `0.9629`). No divergence
from `RECORDED_MARGINS` / `KNOWN_CROSS_MODE_COUPLINGS`. Operators registered
in `synth` with no ladder entry (main or supplementary): `identity` (the
clean-control no-op — never had one), `remove_level_relabel` (a corpus-case
variant of `remove_level`, not its own ladder — never had one), and `split`
(item 166's operator, added 2026-09-18, after item 154's 2026-09-16
measurement — the new, expected gap per A9). Only the `split` gap is a new
finding; it is appended to `insights.md` as a `gap` entry per AC5's
instruction. `fuse` has its own `SUPPLEMENTARY_LADDERS` entry outside the
eight cross-mode ladders, so it is not "no ladder".

**AC9 (the bar, recomputed live).** For every mode in `SPECIFICATION`, `mode
4`'s five conditions all read `met=True` (deciding detector
`fragmentation/islands`) and `mode 3`'s five conditions all read `met=True`
(deciding detector confirmed by `test_167`/`test_165`'s own coverage, not
independently re-measured here since AC9 only requires the per-mode
predicate). `fm.MODE_SIGN_OFFS` = `{3: intermediate-state, 4:
intermediate-state}` — neither carries `outcome="at-the-bar"`, so the set of
modes meeting all six conditions is empty. **No mode is at the bar** — the
planned outcome per the Description and A2.

**AC11 (Stage 32 criterion 2).** `tests/test_168_maintainer_sign_off.py` (18
passed) and `tests/test_165_mode_4_at_the_bar.py` (11 passed) in the clone —
29 passed, 0 failed. `sorted(MODE_SIGN_OFFS) == [3, 4]`, equal to the modes
queue-022 selected for refinement (mode 3 split, mode 4 islands). Mode 3:
`date=2026-09-22, outcome=intermediate-state`. Mode 4: `date=2026-09-22,
outcome=intermediate-state`.

**AC12 (Stage 32 criterion 3).**
`tests/test_151_stage30_validation.py::test_ac3_every_mode_row_title_authored_status_and_edge_rungs_match_specification`
and `::test_ac18_status_matches_independent_recomputation_and_committed_rendering`
in the clone: 2 passed, 0 failed. Live derivation: 16 modes, `validated 7,
implemented 2, specified 0, proposed 7`; every mode appears in
`docs/aide/failure_modes.generated.md` at its derived status, none absent,
none status-less.

**AC6–AC8 (the three clauses, Stage 20 criterion 5 / Stage 32 criterion 5).**
Live from `segfacet.failure_modes` in the clone: `derived status counts over
16 modes: validated 7, implemented 2, specified 0, proposed 7`. `derived mode
rung counts: synthetic-demonstrable 6, needs-real-data 2,
structurally-unobservable 1, none 7`. `modes refined by stage 32: 3, 4; at
the fully-specified bar: none; left as documented drafts: 14` (`14 = 16 -
len({3, 4})`). Written verbatim into both Stage 20 criterion 5's and Stage 32
criterion 5's `aide progress accept` evidence text, per Implementation Step
9. All three clauses match the Description's 2026-09-22 starting point
exactly.

**AC13 (Stage 20's held bullet).** The `*(Item 141)*` bullet's leading icon
flipped `⏸️ → ❌`, with a dated (`2026-09-22`) pointer naming item 154 and
recording that its work landed there as Stage 31's eval-harness re-key
(item 154's own file name:
`items/154-re-measure-the-ladders-and-mode-1s-anchor.md`). No other Stage 20
deliverable bullet reads `⏸️` (confirmed: zero `⏸️` bullets remain anywhere in
`progress.md`). `tests/test_150_maintainer_sign_off.py`'s `_HELD_ITEMS[141]`
moved `"⏸️" → "❌"` in the same commit, with its guiding comment updated to
record the change, per that module's own note.

**AC14 (bookkeeping verbs).** In ascending stage/criterion order:
`aide progress accept 20 --criterion 3/4/5`, then `aide progress accept 32
--criterion 2/3/4/5`, each with the evidence text recorded above (verified
against the `progress.md` diff — each command ticked exactly the criterion
named and appended exactly the evidence text passed). Stage 32 criterion 1
stayed unticked; the hand-written annotation
`*(not attested 2026-09-22, item 169: modes 3 and 4 both carry a maintainer
sign-off dated 2026-09-22 at outcome="intermediate-state", not
"at-the-bar"; conditions 1-5 hold live for both (recomputed via
`traceability.bar_conditions`), but condition 6 requires an "at-the-bar"
sign-off, so no mode meets all six conditions and the set of modes at the
bar is empty)*` was appended to the end of its box's last line by hand. One
`gap` `insights.md` entry names `stage 32 criterion 1`, both sign-off
outcomes (`intermediate-state` for both modes 3 and 4), and that the
remedial work is queue 023's. Two further `gap` entries were appended: A5's
unmarked Stage 32 `D0`/`D3` bullets, and A9's `split`-operator ladder gap.
Stage 20 criteria 1 and 2 were left untouched (A3).

**AC15 (environment).** `aide env`: `OK (venv is Python 3.11; import segfacet
succeeds; import pytest succeeds)`, exit 0. `aide env --profile pyradiomics`:
`NOT satisfied (ModuleNotFoundError: No module named 'radiomics')`, exit 1.
`aide env --profile docker`: `NOT satisfied`, exit 1. `aide env --profile
gpu`: `NOT satisfied (ModuleNotFoundError: No module named 'cupy')`, exit 1.
`progress.md`'s Environment-Gated Capability Verification table carries no
row naming Stage 32 (verified by reading its rows); left unchanged. Stage 32
introduced no gated capability, and no replay criterion above depends on a
profile.

**AC16 (`aide check`).** After the bookkeeping: `aide check: OK (8
warning(s))` — 1 assumptions-block warning, 2 awaiting-a-decision warnings
(gates 1 and 2), 5 retracted-criterion warnings (Stage 20 criteria 1, 3, 4
twice, 5). Identical to the 2026-09-22 baseline recorded in the Description,
both before and after this item's bookkeeping — no new warning, no error.
Re-verified in the clone at the final commit with the same result.

**AC17 (full suite, fresh clone of the final commit).** Clone brought up to
the branch tip (`python <clone>/.aide/scripts/aide.py --repo <clone> sync
--item 169`); `segfacet.__file__` re-resolved under the clone. Final commit:
`0346da1e546db31402742001db2d713b71007a89`. Full configured suite (`tests` +
`.aide/scripts/tests`, per `pyproject.toml`'s `testpaths`), run in the
foreground with `pytest -n auto -q` (one call, under the timeout — the suite
completed in 338.84s / 5m39s, not the ~28 minutes a non-parallel run takes):
**9091 passed, 66 skipped, 0 failed.** Every skip is a pre-known
environment-gated skip: Docker CLI/daemon not available (`test_066`,
`test_069`, `test_070`), CuPy/GPU not available (`test_072`, `test_073`,
`test_074`, `test_075`), PyRadiomics not importable (`test_features_radiomics`),
no real VerSe19 cohort mounted (`SEGFACET_VERSE_COHORT`; `test_084`,
`test_088`, `test_091`, `test_118`, `test_125`), no real SPINEPS fixture
(`SEGFACET_SPINEPS_FIXTURE`; `test_097`), and no pinned pre-098 shape for
three operators (`test_108`). No skip is recorded as verification of
anything above — each replay criterion's evidence is the named node-id run
in the clone (AC3, AC4, AC11, AC12), not this full-suite pass. The clone was
deleted after this run.

**Stage 32 stays 🚧 (A2).** This item's own deliverable bullet lives in Stage
20 (`*(Item 169)*`); Stage 32's `D0`/`D3` bullets carry no item marker (A5),
so `aide progress set 169 in-progress` moved only the Stage 20 bullet. Stage
32's rollup is driven by its acceptance boxes, and criterion 1 stays open —
consistent with the stage staying 🚧, per queue-022's own item-169 entry and
gate 7's resolution text.

- **Left open:** whether Stage 32's D0 and D3 deliverable bullets should carry
  `*(Item NNN)*` markers so the stage's rollup tracks its own items. Both are
  unmarked today (A5), which keeps Stage 32 at 🚧 — the right answer while
  criterion 1 is open, but for the wrong reason. Settling it means deciding what
  a stage's rollup should say when its deliverables shipped and an acceptance
  criterion did not hold, which is a framework question rather than this item's;
  it is captured to `insights.md` instead.

- **2026-09-22 → review finding fixed:** this item's diff flipped Stage 20's
  item-141 deliverable bullet (progress.md ~line 1019) from ⏸️ to ❌ with a
  dated pointer to item 154, but left the queue-022 planning blockquote note
  further down the same section (progress.md ~line 1084, added 2026-09-18)
  reading "Item 141's bullet keeps ⏸️ — its work moved to Stage 31 (item 154)
  and is not re-queued," which the flip made false. Amended that sentence to
  state the bullet was resolved ❌ on 2026-09-22 by this item, with a pointer
  to item 154, its work having landed in Stage 31 — no other text in the note
  changed, and no acceptance box or bullet icon was touched.
