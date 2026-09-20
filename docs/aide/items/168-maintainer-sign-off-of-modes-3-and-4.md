<!-- aide-template: item 2 -->
# Item 168 — Maintainer sign-off of modes 3 and 4

> **Created:** 2026-09-20 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 32 — Selected-Mode Refinement: one failure mode fully specified end to end
> **Queue:** [`../queue/queue-022.md`](../queue/queue-022.md) · Item 168
> **Objectives:** G2, G8
> **Suggested branch:** `aide/168-maintainer-sign-off-of-modes`

---

## Description

Roadmap Stage 32's bar for "fully specified end to end" has six conditions.
Items 165, 166 and 167 brought modes 4 (islands) and 3 (split vertebra
segment) through conditions 1–5, each recomputed live by
`segfacet.traceability.bar_conditions`. **Condition 6 is the sixth:**

> 6. It is signed off by the maintainer, with date and outcome recorded in the
>    specification module.

That is a person's decision. It is not derivable from the code, no agent may
take it, and **no acceptance criterion below asserts an outcome that depends
on it**.

This item is therefore built in two separable halves.

**Half A — the mechanism, buildable now.** `src/segfacet/failure_modes.py`
gains a first-class record for a per-mode sign-off: a frozen `ModeSignOff`
(`mode_id`, `date`, `outcome`, `note`), a two-member outcome vocabulary
`SIGN_OFF_OUTCOMES`, a read-only `MODE_SIGN_OFFS` mapping **shipped empty**,
an accessor `mode_sign_off(mode_id) -> Optional[ModeSignOff]`, and one
`sign_off` key per mode in `specification_to_dict()` / one
`- Maintainer sign-off:` bullet per mode in `render_markdown()`. With the
mapping empty, every one of the sixteen modes reads as **unsigned** — `null`
in the JSON, `(none recorded)` in the Markdown — which is the honest state and
is what the acceptance criteria pin. Half A also raises the human gate.

**Half B — the record, gated.** Once, and only once, a person resolves the
gate, the two `ModeSignOff` records are added to `MODE_SIGN_OFFS` and both
committed artifacts are regenerated. Half B cannot be done by this loop.

**Why a constant and not the module docstring.** Item 150's catalogue sign-off
is one anchored `Signed off: YYYY-MM-DD -- …` line in the docstring's
`Sign-off` section, and two tests read it by regex, both requiring **exactly
one** such line (`tests/test_150_maintainer_sign_off.py::_sign_off_match`,
`tests/test_151_stage30_validation.py::test_ac29_…`). A per-mode record cannot
join that section without breaking them, and a regex over prose is a poor
surface for `bar_conditions` to read if condition 6 is ever mechanised.
`MODE_SIGN_OFFS` is that surface: keyed by mode id, validated at import,
serialised into both artifacts. The docstring gains a pointer sentence to it,
never a second copy of the record (`.aide/AGENT-CONTEXT.md`: move it, do not
copy it).

**How `bar_conditions` would read it, if it ever did.** It does not, and this
item does not change `src/segfacet/traceability.py`. `BAR_CONDITIONS` holds
conditions 1–5 by construction and its docstring states condition 6 is
excluded deliberately. The shape a later item would add is
`failure_modes.mode_sign_off(mode_id) is not None`, plus — for a mode whose
recorded outcome is `at-the-bar` — the cross-check AC9 makes here, that
conditions 1–5 all still hold live. That cross-check is written as a test in
this item rather than as a sixth `BarCondition`, because adding a condition
would move `BAR_CONDITIONS`' length and the tuple width every item 165/167
assertion measures, for no gain this item's criteria can observe.

### What this item is NOT

- **Not the decision.** This item raises a gate. It never runs
  `aide gate approve` or `aide gate decline`, and neither does any agent.
- **Not an attestation.** No acceptance criterion below carries a
  *(closes Stage N criterion M)* annotation, so **none closes a stage
  criterion**. Stage 32's acceptance is attested by **item 169**, from a clean
  clone with its own venv.
- **Not a change to either mode.** No `ModeSpec` field, no `IntendedRule`
  edge, no `CorpusCaseExpectation`, no rule, detector, threshold, feature or
  fixture moves. Mode 3's and mode 4's entries are signed *as they stand*; a
  change the maintainer asks for at the gate is a new item, not an amendment
  to this one.
- **Not a second corpus case** for either mode, and not the two unbuilt
  mode-3 candidate features — see the decision brief's open judgements.

### Decision brief — what the maintainer is being asked, and what is true

Everything in this section was **measured on this tree on 2026-09-20** with
`.venv/bin/python`, not recalled. It lays out what is true; it does not argue
for an answer.

#### The ask

For **each** of mode 3 and mode 4, one of three answers:

1. **Sign off at the bar** (`outcome = "at-the-bar"`) — the entry, the
   fixture, the feature and the detector make sense together, and the mode
   counts toward Stage 32's D1/D2.
2. **Sign off at a recorded intermediate state**
   (`outcome = "intermediate-state"`) — the work is accepted as far as it
   went, and the mode does not count toward the bar. Roadmap Stage 32 D2
   names this an accepted outcome explicitly.
3. **Neither yet** — name what must change first. The gate stays ⏳, and the
   change is a new item.

#### Mode 4 — islands (disconnected components)

`bar_conditions(4)` measures **`(True, True, True, True, True)`** today:

| # | Condition | Measured subject |
|---|-----------|------------------|
| 1 | Entry complete | all eight fields non-empty |
| 2 | A committed fixture expresses it | `inject_islands` (geometric), `expected_firing = ('fragmentation',)`, agrees with the measured firing |
| 3 | Every path the detector reads is extracted **and** catalogued | five `components` paths, each `observed.corpus.covered is True` |
| 4 | A non-proxy detector serving this mode alone | `fragmentation/islands` |
| 5 | Status derives `validated` | `validated`, rung `synthetic-demonstrable` |

**What the maintainer is actually being asked to affirm.** Item 165 changed
**nothing** about mode 4: it built the generic checker and measured the mode
against it. Mode 4's rendered entry is byte-for-byte the text signed at item
150 on 2026-09-14/15. So the affirmation is narrow and is about *judgement,
not mechanism*:

- that `fragmentation`'s `islands` detector — "a small non-dominant component
  strictly below `island_min_voxels`" — is the right decider for the entry's
  definition ("A label's foreground includes components disconnected from its
  main body. Typically small islands close to the vertebra … rarely larger
  blobs further away");
- that `inject_islands` is a fair fixture for it;
- and that the entry's discriminator sentence — *"The island's size and
  distance from the main body grade the finding rather than bound the
  mode"* — is acceptable **as an unbuilt claim**. Item 165 left
  `island_distance_from_main_body_mm` a `hypothesised` candidate path and did
  not build it, because no bar condition needs it (condition 3 asks only
  about paths the deciding detector already reads) and building it would
  change `fragmentation`'s findings, needing a near/far fixture pair and an
  authored expected-set edit. **The entry therefore describes a grading the
  code does not perform.** That is the one substantive thing to affirm or
  overturn for mode 4.

#### Mode 3 — split vertebra segment

Mode 3 went from nothing to `(True, True, True, True, True)` across items 166
and 167. Concretely, what was built:

- **The `split` operator** (item 166, `src/segfacet/synth/`): reassigns a
  contiguous end-slab — 0.4 of the donor label's stacking-axis extent — from
  one label to its adjacent neighbour, deterministic under its seed, refusing
  a label with no adjacent neighbour, carrying the machine-readable record of
  what was broken.
- **One committed geometric corpus case**, `split` (labels 22 → 23).
- **Two new feature fields** (item 167, `features/components.py`):
  `stray_contact_area_mm2` and `stray_contact_label` — inter-label
  face-contact area **restricted to a label's non-largest connected
  components**, and the label contacted.
- **A third detector on the `fragmentation` rule**, id `neighbour_contact`,
  firing strictly above `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2 = 100.0` mm².
- **The specification edge** `fragmentation` / `neighbour_contact` at
  `synthetic-demonstrable`, which is what moved `derive_status(3)` from
  `implemented` to **`validated`** and the mode's rung to
  `synthetic-demonstrable`.

**Why the restriction to non-largest components matters.** Bare inter-label
contact area does not separate mode 3: over all twelve committed geometric
cases only two carry any, `split` (750.0 mm²) and `force_overlap` (mode 15,
725.0 mm²) — 25 mm² apart, so no threshold on the bare scalar works.
Restricting to non-largest components moves `force_overlap` to `0.0` and
leaves `split` at `750.0`. **Margins:** the only firing value anywhere in
either committed corpus is `750.0` mm² (7.5× the threshold); every non-firing
label measures exactly `0.0`. There is no fixture value near the threshold.

#### Open judgement 1 — is `fragmentation` the right home for mode 3's detector?

Item 167 flagged this explicitly for this gate, and said plainly that it is
not derivable from the code.

**The case for `fragmentation` (what was built).** Item 164 made the
*detector*, not the rule, the unit of mode attribution, precisely so one rule
may serve several modes; `bar_conditions`' condition 4 reads
`modes_for_detector(rule_id, detector_id)` and excludes only
`PROXY_RULE_IDS == ("bounds", "reference_delta")`, so `fragmentation`
qualifies mechanically. And the signal *is* a property of a label's connected
components — the block `fragmentation` already owns and already computes.

**The case against (the cost item 167 recorded of the alternative).** A rule
named for the mode would be clearer to a reader: `fragmentation` now carries
three detectors serving modes 1, 3 and 4. Item 167 did not take that route
because a new rule id would move `len(iter_rules()) == 10` (pinned twice in
`tests/test_136_rule_mode_declarations.py`), the rule-id enumerations in
**fourteen** test modules, the `split` case's `expected_rule_ids` in the
committed `tests/corpus/manifest.json` (forcing a corpus regeneration), and
the per-rule exercise report.

**What it costs today.** One thing, and it is open judgement 3 below: because
`fragmentation` already fired on the `split` case through mode 1's
`components` detector, the rule-id-granular expected set did not move.

Nothing about this is reversible for free later: a rule id appears in the
committed manifest, so moving the detector to its own rule after the fact is a
corpus regeneration plus fourteen test modules, the same cost as doing it now.

#### Open judgement 2 — the co-detection shape on the `split` case

The `split` case's authored `expected_firing` is `('fragmentation',)`, and
`failure_modes.measured_firing` returns a set of **rule ids**, never detector
ids. On that one case, **two** detectors of that one rule fire:

- `fragmentation` / `components` — mode 1's detector, because label 23 now
  spans two disconnected bodies (the donated slab plus its own);
- `fragmentation` / `neighbour_contact` — mode 3's own detector,
  `stray_contact_area_mm2 = 750.0` against label 22.

So the ratchet (item 163) sees **one** rule, and the expected set was
unchanged by item 167 — which is also why no corpus regeneration was needed.

**What to be comfortable or uncomfortable with.** The evidence that mode 3's
own detector fires exists one level down: `Finding.detector_id` has carried
the id since item 164, and item 167's AC3/AC7 swept both committed manifests,
every label, and measured the `neighbour_contact` firing set as exactly
`{("geometric", "split", 23)}` — it fires on that case and on no other, clean
control and `fuse_adjacent` included. What is *not* covered is the generic
checker: condition 2 would read "met" from the rule id alone even if the new
detector fired on nothing. That is open insight 2 below.

#### Open judgement 3 — item 167's four `Left open` notes

1. **The two unbuilt candidate paths** — `spline_leave_one_out_shape_change`
   and `metric_change_under_merge_candidate` remain `hypothesised` in mode 3's
   `candidate_features`. The first candidate measured separated the corpus
   completely, and the `prototype` posture stopped the ladder there. Signing
   mode 3 at the bar signs an entry that names two signals the code does not
   compute.
2. **A blind spot in the detector** — a split in which the **donated** part is
   larger than the receiving label's own body reads `0.0`, because the
   contacting component would then be that label's *largest*. Not expressible
   on the corpus as it stands (`split` donates 0.4 of the donor), and a
   fixture for it is a new corpus case item 167 deliberately did not add.
3. **The report schema** — `stray_contact_area_mm2` and
   `stray_contact_label` are in `report_schema_v0.json`'s `properties` but not
   its `required` list, so nine hand-built test fixtures stay valid and the
   detector can read a pre-item record. Tightening it is a separate,
   mechanical item.
4. **Whether `100.0` mm² survives real data** — calibrated on the synthetic
   corpus alone, where the nearest competing value is `0.0`. The named worry
   is real facet-joint contact between adjacent vertebrae, which is genuine
   anatomy and could exceed 100 mm² at 1 mm isotropic (100 voxel faces).
   Roadmap Stage 21 re-calibrates thresholds on real GT.

#### The two open insights aimed at this ground

Both are recorded in [`insights.md`](../insights.md), both dated 2026-09-20,
and **both are properties of the generic checker, not defects in mode 3 or
mode 4**:

- **Condition 2 is universal where the roadmap is existential** *(item 165)*.
  The roadmap asks that *a* committed fixture express the mode;
  `bar_conditions` computes `all(case_agrees(c) for c in mode.corpus_cases)`
  **and** at least one intersecting expected set. The two readings coincide
  for a mode with one corpus case — which is exactly what both mode 3 and
  mode 4 have. The divergence is conservative: it can only under-certify.
- **Condition 2 is rule-id-granular while condition 4 is detector-granular**
  *(item 167)*. Open judgement 2 above is this insight's subject.

**Whether either bears on this sign-off.** Neither changes what is true of
mode 3 or mode 4 today — each has exactly one corpus case, and item 167's
AC3/AC7 closed the granularity hole for mode 3 at the detector level by
direct measurement. Both bear on the *next* mode refined through an existing
rule's new detector, and on any mode that acquires a second corpus case; a
later item that adds one meets both at the same time. They are named here so
that "signed off at the bar" is read as "signed off against a checker with
two recorded, conservative divergences" rather than against a perfect one.

#### What is unchanged either way

No rule, threshold, fixture, feature, firing set or `config_hash` moves in
this item, under any of the three answers. The committed corpora are not
regenerated. `derive_status`, `derive_mode_rung` and `bar_conditions` return
exactly what they return today.

## Acceptance Criteria

**Part A — the mechanism.** AC1–AC8 are satisfiable now and do not depend on
any decision.

- [ ] **AC1: the sign-off record type.** `segfacet.failure_modes.ModeSignOff`
      is a frozen dataclass whose field names, read live via
      `dataclasses.fields`, equal `("mode_id", "date", "outcome", "note")` in
      that order.
- [ ] **AC2: every field is validated at construction.** For each entry of a
      table of invalid constructions — `mode_id` not an `int >= 1` (`bool`
      included), `date` not matching `^\d{4}-\d{2}-\d{2}$`, `outcome` not a
      member of `SIGN_OFF_OUTCOMES`, `note` not a non-empty `str` —
      `ModeSignOff(...)` raises `ValueError` whose message names the offending
      field.
- [ ] **AC3: the outcome vocabulary is closed and two-valued.**
      `segfacet.failure_modes.SIGN_OFF_OUTCOMES == ("at-the-bar",
      "intermediate-state")`.
- [ ] **AC4: the mapping is read-only.**
      `segfacet.failure_modes.MODE_SIGN_OFFS` is a `MappingProxyType`, and
      assigning into it raises `TypeError`.
- [ ] **AC5: the mapping is keyed by its records' own mode ids, all of which
      the specification carries.** For every key `k` of `MODE_SIGN_OFFS`,
      `k in SPECIFICATION` and `MODE_SIGN_OFFS[k].mode_id == k`, recomputed
      live over the mapping rather than over a literal.
- [ ] **AC6: an unsigned mode reads as unsigned.** For every mode id in
      `SPECIFICATION`, `mode_sign_off(mode_id)` equals
      `MODE_SIGN_OFFS.get(mode_id)` — the record when one exists, and `None`
      when none does.
- [ ] **AC7: the serialisation carries one `sign_off` key per mode.** For
      every record of `specification_to_dict()["modes"]`, its `sign_off` value
      equals `None` when `mode_sign_off(record["id"]) is None`, and otherwise
      equals `{"date": …, "outcome": …, "note": …}` taken from that record's
      fields — recomputed live for all sixteen modes.
- [ ] **AC8: the rendering carries one sign-off bullet per mode.** Every
      `## Mode N…` section of `render_markdown()` contains exactly one line
      beginning `- Maintainer sign-off: `, whose remainder equals
      `(none recorded)` when `mode_sign_off(N) is None` and
      `f"{r.date} -- {r.outcome} -- {_md_escape(r.note)}"` otherwise —
      recomputed live for all sixteen modes.

**Part B — the gate, and the record only a person can create.** AC9–AC12 are
written as invariants that hold in **both** halves. **None of them asserts
that a sign-off happened, that its outcome was approval, or that mode 3 or
mode 4 is signed.** AC9 and AC12 are vacuously true while `MODE_SIGN_OFFS` is
empty; AC11 is what keeps that emptiness honest rather than unexamined, and
the Testing Strategy's `at-the-bar-claim-over-a-failing-mode` and
`resolution-coherence-is-not-vacuous` cases are what prove the two predicates
can fail.

- [ ] **AC9: a sign-off claiming the bar is cross-checked against live
      state.** For every entry of `MODE_SIGN_OFFS` whose `outcome` is
      `"at-the-bar"`, `tuple(c.met for c in
      segfacet.traceability.bar_conditions(mode_id))` equals
      `(True, True, True, True, True)`.
- [ ] **AC10: the human gate exists, is unique, and reaches items 168 and
      169.** Parsed from `docs/aide/progress.md` through the CLI's
      `human_gates()`, exactly one `## Human gates` row's Gate cell contains
      `Stage 32 selected-mode sign-off`, and that gate's parsed `blocks`
      equals `[168, 169]`, its `stage` is `None`, and its `blocks_all` is
      `False`.
- [ ] **AC11: a record exists if and only if the gate is resolved.**
      `bool(MODE_SIGN_OFFS)` equals `AC10's gate.kind != "awaiting"`, both
      recomputed live — so a record cannot ship under an unresolved gate, and
      a resolved gate cannot leave the specification module silent.
- [ ] **AC12: a recorded sign-off carries the resolved gate's own date.** For
      every entry of `MODE_SIGN_OFFS`, `entry.date` equals the ISO date parsed
      from AC10's gate row's Status cell.

## Assumptions  <!-- MANDATORY: what was assumed when the queued one-liner was ambiguous -->

`loop.clarify = "assume"` (`aide.toml`), vision posture `prototype`. Every
measurement below was run on this tree on 2026-09-20 with `.venv/bin/python`.

**None of these is an interface pin.** Items 165, 166 and 167 are all merged
✅ and every statement below was measured against their built code, not
predicted from their specs — so under `.aide/conventions.md` §5 these are
audit entries, and nothing here is re-checked at a later claim.

- **A1 (measured 2026-09-20):** the sign-off is recorded as a module-level
  frozen `MODE_SIGN_OFFS: Mapping[int, ModeSignOff]`, **not** as a `ModeSpec`
  field and **not** as prose in the docstring's `Sign-off` section. A
  `ModeSpec` field would put the sign-off inside the frozen seed that
  `specification_conflicts()` polices as authored taxonomy — it is neither;
  and the docstring is already parsed by two tests requiring **exactly one**
  `Signed off:` line (`tests/test_150_maintainer_sign_off.py::_sign_off_match`
  and `tests/test_151_stage30_validation.py::test_ac28_…`,
  `::test_ac29_…`), which a per-mode line would break. The mapping is
  validated at import by a module-level `_validate_sign_offs()` rather than
  through a new `specification_conflicts()` direction, which would move
  `tests/test_149_conformance_report.py`'s scored-direction surface for no
  gain this item's criteria can measure.

- **A2 (measured 2026-09-20):** `MODE_SIGN_OFFS` **ships empty** and the
  buildable half is complete with it empty. The alternative — holding the
  whole item until a person decides — stalls the queue on work that does not
  need the decision, and `.aide/conventions.md` §1 → human gates is explicit
  that raising a gate is always safe. AC11 makes the emptiness a measured
  claim against the gate's own status rather than an unexamined default.

- **A3 (measured 2026-09-20):** the gate's reach is **`168, 169`**, not
  `stage 32`. Per §1 → human gates, `stage N` is for a decision that could
  *invalidate* a stage's work; this decision invalidates nothing already
  built — the three answers all leave every artifact as it is — and it holds
  exactly two threads: this item's Half B and item 169's Stage 32
  attestation, which cannot be made without condition 6. Including 168 is
  operationally safe and was checked: `aide claim` consults gates only when
  picking an item to claim (`.aide/scripts/aide.py`, `cmd_claim`), item 168 is
  already claimed on its branch, and `aide merge` does not consult the gate
  table at all. The consequence is intended — after item 168 merges, the
  queue pauses at item 169 until a person decides.

- **A4 (measured 2026-09-20):** the new gate row's Gate cell must **not**
  contain the substring `Stage 30 failure-mode specification sign-off`.
  `tests/test_150_maintainer_sign_off.py::_sign_off_gate` and
  `tests/test_151_stage30_validation.py::test_ac28_…` both select gate 5 by
  that substring and assert **exactly one** match. The proposed cell opens
  `Stage 32 selected-mode sign-off`, which collides with neither. The cell
  also carries no `|`, which would split the row and make it unreadable as a
  gate (`aide check` error, holding every claim).

- **A5 (measured 2026-09-20):** the `sign_off` key goes **inside each mode
  record**, never at the payload's top level.
  `tests/test_152_retire_vision_seed.py::test_ac14_committed_json_top_level_shape_is_unchanged`
  asserts `set(payload.keys()) == {"schema_version", "note", "modes",
  "conditions", "vision_seed_disposition"}` — a literal key-set equality, and
  the only one in this surface. A per-mode key leaves it green. A grep across
  `tests/` on 2026-09-20 found **no** assertion pinning the per-mode key set
  or a per-mode bullet count, so the added key and bullet reconcile by
  regenerating the artifacts alone.

- **A6 (measured 2026-09-20):** `SCHEMA_VERSION` moves `"2.1"` → `"2.2"`. The
  payload gains a key, which is a schema change, and nothing in `tests/` or
  `src/` pins the literal `"2.1"` for this module (grepped 2026-09-20 —
  `traceability_matrix.generated.*` carries its own `1.2` and never embeds
  this one). The value is compared to the artifacts only by the
  regenerate-and-compare tests, which reconcile in the same commit.

- **A7 (engine 1.59.2):** `aide scope` proves this item's diff against the
  **Authorised paths** list below; a path listed there and left unchanged is
  not a scope violation.

## Implementation Steps

Steps 1–8 are **Half A** and are done now. Step 9 is **Half B** and is done
only after a person has resolved the gate.

1. **Add `SIGN_OFF_OUTCOMES` and `ModeSignOff` to
   `src/segfacet/failure_modes.py`**, beside the existing frozen schema
   dataclasses (`CandidateFeature`, `IntendedRule`, `CorpusCaseExpectation`)
   and in their house style: `@dataclasses.dataclass(frozen=True)`, a
   `__post_init__` that raises `ValueError` naming the offending field, and
   the same `f"ModeSignOff {self.mode_id}: '<field>' …"` message shape those
   three already use. Reuse the module's existing `re`-free validation idiom
   where it suffices; the ISO-date check is the one place a small `re.fullmatch`
   is warranted, matching no other module's helper.

2. **Add `MODE_SIGN_OFFS` and `_validate_sign_offs()`**, placed **after**
   `SPECIFICATION` so the key check can read it. `MODE_SIGN_OFFS =
   MappingProxyType({})` — reusing the `MappingProxyType` the module already
   imports for `SPECIFICATION`, not a new freezing helper — followed by one
   `_validate_sign_offs()` call that raises `ValueError` for a key absent from
   `SPECIFICATION` or a key disagreeing with its record's `mode_id`.

3. **Add `mode_sign_off(mode_id) -> Optional[ModeSignOff]`**, a one-line
   `MODE_SIGN_OFFS.get(mode_id)` with the docstring stating that `None` means
   *not signed off* and never *signed off with nothing recorded*.

4. **Extend `__all__`** with `ModeSignOff`, `SIGN_OFF_OUTCOMES`,
   `MODE_SIGN_OFFS` and `mode_sign_off`.

5. **Add the `sign_off` key in `specification_to_dict()`**, inside the
   per-mode dict built in the `iter_modes()` loop, after `"provenance"`:
   `None`, or `{"date": …, "outcome": …, "note": …}` from the record. The
   record's `mode_id` is deliberately not repeated — it is the record's key.
   Leave the top-level return dict untouched (A5). Values are strings or
   `None`, so the committed JSON stays float-free and
   `tests/committed_artifact_guard.py`'s `"no-float-leaf"` allowlist ground
   for it holds.

6. **Add the bullet in `render_markdown()`**, immediately after the
   `- Derived rung (strongest edge, live): …` line, reading
   `- Maintainer sign-off: (none recorded)` or
   `- Maintainer sign-off: {date} -- {outcome} -- {note}`, with the note
   passed through the existing `_md_escape` helper (never a second escaper).

7. **Bump `SCHEMA_VERSION` to `"2.2"`** (A6) and regenerate both committed
   artifacts with `.venv/bin/python -m segfacet.failure_modes` — the module's
   own entry point, which already defaults to the two `docs/aide/` paths.
   Never hand-edit either file.

8. **Extend the module docstring**: add `ModeSignOff` / `SIGN_OFF_OUTCOMES` /
   `MODE_SIGN_OFFS` / `mode_sign_off` to the `Public API` section in its
   existing style, and add **one** sentence to the `Sign-off` section pointing
   at `MODE_SIGN_OFFS` as the per-mode record. That sentence must not begin a
   line with `Signed off: ` and must not contain a `<number> entries` phrase
   (A4, A1) — item 150's single anchored line and its entry count stay
   exactly as they are.

9. **Raise the gate** — add the row of the shape below to
   `docs/aide/progress.md`'s `## Human gates` table, as the table's last row.
   This is the one `progress.md` edit this item makes, and the only edit to
   that file it makes at all.

---

**Half B — after, and only after, a person has resolved the gate.** Add one
`ModeSignOff` per signed mode to `MODE_SIGN_OFFS`, using the gate row's own
resolution date (AC12) and the outcome the person chose; re-run step 7 to
regenerate both artifacts; append a dated note to this spec's Decisions &
Trade-offs recording what was decided. **No agent runs `aide gate approve` or
`aide gate decline`.** If the gate is still ⏳ when this item's suite runs,
Half A is the whole deliverable and AC9/AC12 are vacuous by construction —
AC11 asserts exactly that state.

## Authorised paths

**May change:**

- `src/segfacet/failure_modes.py` — `ModeSignOff`, `SIGN_OFF_OUTCOMES`,
  `MODE_SIGN_OFFS`, `_validate_sign_offs`, `mode_sign_off`, the `__all__` and
  docstring additions, the `sign_off` key, the rendering bullet and
  `SCHEMA_VERSION`.
- `docs/aide/failure_modes.generated.json` — regenerated by step 7; gains one
  `sign_off` key per mode and the bumped `schema_version`.
- `docs/aide/failure_modes.generated.md` — regenerated by step 7; gains one
  `- Maintainer sign-off:` bullet per mode and the bumped schema line.
- `tests/test_168_maintainer_sign_off.py` — this item's test module.

**Asserts against:**

- `src/segfacet/traceability.py` — AC9 reads `bar_conditions` live; this item
  adds no condition and changes no scorer, and `BAR_CONDITIONS` stays five
  entries long.
- `src/segfacet/heuristics/fragmentation.py` — its three detectors and their
  `signal_paths` are what AC9's conditions 3 and 4 resolve through; unchanged,
  so no finding moves.
- `tests/corpus/manifest.json` — the geometric corpus `case_agrees` drives
  through AC9's condition 2; read-only, no case added, removed or
  regenerated.
- `docs/aide/feature_catalogue.generated.json` — the committed form of the
  catalogue AC9's condition 3 recomputes live; pinned, never regenerated by
  this item.

## Testing Strategy

**Module:** `tests/test_168_maintainer_sign_off.py`.

**Shape.** One module-scoped fixture calling
`catalogue.build_catalogue(strict=True)` once and passing it into every
`bar_conditions(...)` call — the idiom `tests/test_165_mode_4_at_the_bar.py`
established, and the sole reason `bar_conditions` takes a `catalogue`
argument. `progress.md` is parsed by loading `.aide/scripts/aide.py` in
process and calling its `human_gates()` / `_split_row`, the idiom
`tests/test_150_maintainer_sign_off.py` established — never by a hand-written
Markdown table parser, and **never** by writing to `progress.md`.

**One test per AC** (AC1–AC12), each recomputing its predicate from the
primary source — `segfacet.failure_modes`, `segfacet.traceability` and the
live `progress.md` — and asserting the record agrees, never comparing against
a transcribed literal.

**Adversarial cases, each with the failure mode it guards.** The test-writer
writes these and no others.

- `sign-off-for-an-unknown-mode:` `_validate_sign_offs` over a constructed
  mapping whose key is absent from `SPECIFICATION` raises `ValueError` naming
  that key — otherwise a typo'd mode id ships as a silent no-op that
  `mode_sign_off` never returns and no artifact ever renders.
- `key-disagrees-with-its-record:` `_validate_sign_offs` over a constructed
  mapping whose key differs from its record's `mode_id` raises `ValueError`
  naming both — otherwise `mode_sign_off(k)` returns a record signed for a
  different mode.
- `at-the-bar-claim-over-a-failing-mode:` AC9's predicate, re-run over a
  constructed `ModeSignOff(outcome="at-the-bar")` for a mode whose
  `bar_conditions` are not all met (a `proposed` mode — measured 2026-09-20,
  seven modes qualify), must **fail** — otherwise AC9 passes vacuously on the
  empty shipped mapping and certifies nothing at all.
- `resolution-coherence-is-not-vacuous:` AC11's predicate, re-run over an
  in-memory copy of `progress.md` whose gate Status cell is replaced with
  `✅ Approved (2026-09-21)` (the `_with_status_cell` idiom of
  `tests/test_150_maintainer_sign_off.py`, in memory only), must **fail**
  against the empty shipped mapping — otherwise the if-and-only-if is
  satisfied by both sides being false and asserts nothing.
- `unsigned-never-renders-as-a-blank-record:` no mode section of
  `render_markdown()` and no record of `specification_to_dict()` carries an
  empty-string date or an empty-string outcome — an unsigned mode is
  `(none recorded)` / `None`, never a record with nothing in it that a
  downstream reader could count as a sign-off.
- `gate-row-is-four-cells:` the raised row splits into exactly four cells
  through the CLI's `_split_row` — a row of any other width is not read as a
  gate at all, makes `aide check` error, and holds every item's claim.

**Existing tests to reconcile.** Everything below was grepped across
`tests/` on 2026-09-20. **Nothing in this list needs an edit** — the whole
reconciliation is regenerating the two artifacts in step 7, plus two naming
constraints already fixed by A4 and step 8. It is enumerated because this
queue lost three validation rounds to reconciliation surfaces that were not
enumerated.

*What new values this change emits:* one `"sign_off": null` leaf per mode in
`failure_modes.generated.json` (16), one
`- Maintainer sign-off: (none recorded)` line per mode in
`failure_modes.generated.md` (16), and the string `"2.2"` in place of `"2.1"`
in both. No new float leaf, no new numeric value, no new feature path, no new
leaf-path digest, no `config_hash` change, no corpus regeneration.

- **Regenerate-and-compare over both artifacts — green once step 7 runs, no
  edit:** `tests/test_144_failure_mode_specification.py` (before/after
  `read_bytes()` around `main()`),
  `tests/test_145_eight_hypothesised_modes.py::test_ac23_…` (structural
  fresh-vs-committed plus `fresh_md == committed_md`),
  `tests/test_146_ninth_mode_and_first_proposed.py`,
  `tests/test_147_specification_is_the_record.py` (via
  `assert_matches_committed_artifact`),
  `tests/test_149_conformance_report.py`,
  `tests/test_150_maintainer_sign_off.py`,
  `tests/test_157_case_id_rename.py`.
- **`tests/test_152_retire_vision_seed.py::test_ac14_committed_json_top_level_shape_is_unchanged`**
  — the one literal key-set pin in this surface. It stays green **because**
  `sign_off` is a per-mode key (A5); a top-level one would redden it.
- **`tests/test_150_maintainer_sign_off.py::test_ac12_every_authored_field_is_present_in_both_artifacts`**
  — iterates the authored string fields and compares them against both
  artifacts; tolerant of an added key and an added bullet, and verified so by
  reading the comparison loop.
- **`tests/test_149_conformance_report.py::test_ac21_failure_modes_specification_has_no_float_leaf`**
  and `tests/committed_artifact_guard.py`'s `"no-float-leaf"` allowlist
  entries for both paths — the new leaf is a string or `null`, so both hold.
- **`tests/test_150_maintainer_sign_off.py::_sign_off_gate` and
  `tests/test_151_stage30_validation.py::test_ac28_signed_off_date_matches_the_approved_gate`**
  — both select gate 5 by the substring
  `"Stage 30 failure-mode specification sign-off"` and assert exactly one
  match. Reconciled **by naming** (A4): the new gate's cell opens
  `Stage 32 selected-mode sign-off`.
- **`tests/test_150_maintainer_sign_off.py::_sign_off_match` and
  `tests/test_151_stage30_validation.py::test_ac29_sign_off_entry_count_matches_specification_length`**
  — require exactly one `^Signed off: YYYY-MM-DD -- …$` line in the
  docstring's `Sign-off` section, and read the entry count from its outcome
  text. Reconciled **by wording** (step 8): the pointer sentence matches
  neither pattern.
- **`tests/test_aide_check_no_errors.py`** — a gate row of any width but four
  makes `aide check` error. The `gate-row-is-four-cells` case above guards the
  same thing from the item's own module.
- **`tests/test_163_specificity_ratchet.py` and
  `tests/test_162_corpus_exercise_report.py`** — untouched: no expected firing
  set, rule, detector or operator moves.

## Validation  <!-- OPTIONAL: how to OBSERVE this working, beyond the tests -->

Needs no `[validation]` profile — every command is stdlib or the project venv.
The validator executes all four:

1. `.venv/bin/python -m segfacet.failure_modes` — then `git status` must show
   **no** change to `docs/aide/failure_modes.generated.json` or `.md`
   (regenerating a second time is a no-op; the committed pair is the module's
   own output).
2. Read modes 3's and 4's sections of `docs/aide/failure_modes.generated.md`
   and confirm each carries exactly one `- Maintainer sign-off:` bullet, and
   that it reads `(none recorded)` — the honest state while the gate is ⏳.
3. `python .aide/scripts/aide.py gate list` — the new gate appears, `⏳`, and
   the line names `blocks 168, 169`.
4. `python .aide/scripts/aide.py check` — exits OK with **no errors**. The
   gate adds one "awaiting a decision" *warning*, which is expected and is
   never pinned (CLAUDE.md: clear a warning, never pin the set).

**Do not run `aide gate approve` or `aide gate decline`.** Resolving is a
person's act; the validator's job here ends at confirming the gate is present,
well-formed and awaiting.

## Dependencies

- **Item 165** — `traceability.bar_conditions`, `BAR_CONDITIONS` and
  `PROXY_RULE_IDS`, which AC9 reads, and mode 4's measured clearance of
  conditions 1–5. Merged ✅.
- **Item 166** — the `split` operator and mode 3's committed corpus case,
  which the decision brief reports. Merged ✅.
- **Item 167** — mode 3's `stray_contact_area_mm2` feature and the
  `fragmentation` / `neighbour_contact` detector that moved
  `bar_conditions(3)` to all-true, and the four `Left open` notes the brief
  puts in front of the maintainer. Merged ✅.

This item's own human gate reaches exactly this item and the next —
`Blocks: 168, 169` — which names the reach without creating dependency edges.

**Downstream:** item 169 attests Stage 32's acceptance from a clean clone with
its own venv, and cannot attest criterion 1 (all six bar conditions) or
criterion 2 (every refined mode carries a sign-off) until this item's Half B
has recorded one.

## Decisions & Trade-offs

To be updated during implementation.

- **2026-09-20, Half A implemented.** Built exactly the mechanism the spec
  describes: `SIGN_OFF_OUTCOMES`, the frozen `ModeSignOff` dataclass
  (`mode_id`, `date`, `outcome`, `note`, in that order, each validated with a
  `ValueError` naming the offending field), `MODE_SIGN_OFFS` as a
  `MappingProxyType({})` validated at import by `_validate_sign_offs()` (which
  takes the mapping as its first positional argument, defaulting to
  `MODE_SIGN_OFFS`, per the test-writer's flagged interface requirement),
  `mode_sign_off()`, the per-mode `"sign_off"` JSON key and the
  `- Maintainer sign-off:` Markdown bullet, `SCHEMA_VERSION` "2.1" -> "2.2",
  and the module-docstring pointer sentence. `MODE_SIGN_OFFS` ships empty, as
  A2 requires; no `ModeSignOff` record was added for mode 3, mode 4 or any
  other mode, and no `aide gate` command was run. Both generated artifacts
  were regenerated via `python -m segfacet.failure_modes`; a second
  regeneration is a byte-identical no-op. Confirmed by direct measurement
  (not assumed): the docstring's `Sign-off` section still matches exactly one
  `^Signed off: YYYY-MM-DD -- …$` line via the same regex
  `tests/test_150_maintainer_sign_off.py::_sign_off_match` uses, the added
  pointer sentence sits in a separate paragraph so it does not extend that
  match, and the outcome text's `<count> entries` phrase is unchanged
  ("giving sixteen entries") -- so `test_151`'s `test_ac29_…` still resolves
  to `len(SPECIFICATION) == 16`. `specification_to_dict()["schema_version"]`
  is `"2.2"` and the top-level payload key set is unchanged
  (`{"schema_version", "note", "modes", "conditions",
  "vision_seed_disposition"}`), so `test_152`'s
  `test_ac14_committed_json_top_level_shape_is_unchanged` stays green because
  `sign_off` is a per-mode key, not a top-level one.

- **Left open:** whether condition 6 should ever become a sixth
  `BarCondition` in `traceability.BAR_CONDITIONS`, computed as
  `mode_sign_off(mode_id) is not None`. Not done here: it would change the
  tuple width every item 165 and 167 assertion measures, and no consumer in
  this queue reads a sixth entry. The mechanism this item ships is what such
  an item would read; AC9 is the cross-check it would need.
- **Left open:** whether a **declined** sign-off should be representable in
  `SIGN_OFF_OUTCOMES`. It is not: a declined gate keeps blocking and the
  remedy is to re-plan (`.aide/conventions.md` §1 → human gates), so a decline
  lives in the gate row's own Status cell and leaves the specification module
  silent — which AC11 asserts. A future item that wants a *recorded refusal*
  in the module would add the third member and its own criteria.
- **Left open:** whether `MODE_SIGN_OFFS` should eventually carry the sign-off
  for the **FOV-truncation condition** as well as for modes. Roadmap Stage 32
  speaks only of modes, `CONDITIONS` is a separate seed, and no consumer needs
  it; the mapping is keyed by mode id and `_validate_sign_offs` enforces that.
