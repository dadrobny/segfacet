> Stage 20's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 20`, run on the main or queue branch, moves it back.

## Stage 20 — Failure-Mode ↔ Feature ↔ Rule Traceability & Specificity Harness (G2, G7)

> **⚠️ Annotated 2026-09-03 — read before the text below.** This stage is in progress
> (items 136, 137, 138 ✅; queue-019 was cut after item 138), so its goal, deliverables
> and acceptance are immutable and stand as written. What follows is the backward
> supersession record the text itself cannot carry:
>
> - **The goal paragraph's numbers have moved.** Re-measured 2026-09-02: 5 of 10 rules
>   fire through plain `run_qc` (not 4 — `mislabel` moved in at Stage 28); 1 of 9 cases
>   fires nothing (`mode8_force_overlap`, not 3 of 9); cross-talk is **1/9**, not 0/9
>   (`mode6_crop_at_border` fires `mislabel` beside `border`), so "the assertion is free to
>   adopt now" no longer holds as stated.
> - **D4 (reachability for modes 1/4/8) is superseded in part by Stage 28** (2026-08-27):
>   modes 1 and 4 were one defect, the interpolating spline fit, closed by items 120/132/135;
>   the FOV-headroom remedy proposed for mode 1 could not have worked. What remained of D4 —
>   mode 8's mechanism — item 138 recorded.
> - **Stage 30 runs before the remainder of this stage.** The remaining deliverables
>   (per-rule/per-operator exercise reporting, the specificity ratchet, the mode-1 ladder
>   base, the validation) each rested on a definition of the modes that did not exist —
>   see [`failure-mode-taxonomy-handover.md`](../failure-mode-taxonomy-handover.md) §1–§4.
>   Stage 30 authors that specification; items 139–142 are re-specified against it and
>   re-queued after Stage 30's sign-off. Whether the ladder-base deliverable stays in this
>   stage is decided at that queue's planning: it is a Stage 18 metric-surface fix and
>   stays only if the mode-1 / mode-6 discriminator makes "mode 6 clears on its own" a
>   meaningful claim. The carried defect "the synthetic fixture corpus is anatomically
>   inverted along S" (item 131) lands in Stage 30 as D0, so the specificity baseline the
>   ratchet pins is measured on the corrected corpus, as that entry asks.
> - **How the acceptance bullets are read once Stage 30 has landed** (handover §12.2; the
>   wording is not changed — criteria 1 and 2 are attested, criteria 3–5 carry retraction
>   trails): *every §6 mode* means every mode at lifecycle status `implemented` or above,
>   with a `proposed` mode reported as unimplemented, not silent; the evidence rung sits on
>   each mode ↔ rule edge and the mode's rung is derived; *unintended* in the specificity
>   assertion is defined by the specification's per-case expected firing set, so the
>   allowlist is derived from the specification rather than authored beside it; and the
>   honest detection count is stated per lifecycle status and per rung, never as one
>   number over a list that mixes hypothesised and demonstrated modes.

> **⚠️ Annotated 2026-09-15 — after Stage 30's sign-off (item 150, gate `gate-fb64` approved).**
> The remainder of this stage is not re-queued as a stage of its own; it is **interleaved
> into Stage 32** (per-mode refinement), and its criteria are read against the signed-off
> sixteen-mode catalogue in `src/segfacet/failure_modes.py`:
>
> - **Item 139 (per-rule and per-operator exercise reporting)** and **item 140 (the
>   specificity ratchet)** are re-specified against the specification and built at the
>   **start of Stage 32's first queue**, so every firing change a refinement item
>   makes is authored in the specification and checked by the ratchet from then on. The
>   ratchet's allowlist is each corpus case's `expected_firing` — derived, never authored
>   beside it — so it guards the refinement rather than freezing the current rules.
> - **Item 141 (the mode-1 severity-ladder base)** moves to **Stage 31**, where the
>   Stage-18/29 eval harness is re-keyed from the legacy mode ids 1–8
>   (`eval.per_mode.LEGACY_STAGE18_MODE_NAMES`) to the signed-off catalogue. Mode 1 no
>   longer means what the ladder was built for, so the ladder is re-derived there, not
>   widened here.
> - **Item 142 (this stage's validation)** runs at the **close of Stage 32**, once the
>   selected modes have passed their checkpoints, so the detection count it states covers
>   them; it is a count at that date, not a claim that every mode is implemented.
> - **"Every §6 failure mode"** means every entry of the specification at `implemented`
>   or above; the seven `proposed` entries (5, 7, 10–14 on 2026-09-15) are reported as
>   unimplemented, never silently — the 2026-09-03 reading above, applied to the new ids.
>   Mode numbers quoted in this stage's text (mode 1 displacement, mode 6 border, mode 8
>   overlap) are the pre-sign-off ids; see Stage 30's annotation for the mapping.

**Goal.** Close the gap between "the suite is green" and "the rules are specific".
Measured on the committed corpus: **10 rules are registered and enabled, but only 4 ever
fire** (`fragmentation`, `coverage`, `border`, `sequence`) — `bounds`, `mislabel`,
`overlap`, `intensity`, `reference_delta` and `intensity_reference_delta` fire on **zero**
cases. **Three of nine cases fire nothing at all** through `run_qc`
(`mode1_displace`, `mode4_relabel_swap`, `mode8_force_overlap`); their intended rule is
reached only by feeding a hand-reconstructed record straight to the rule. That is
documented as item 040's limitation, but the effect is that **three of eight failure modes
are not detected end-to-end while the corpus still reads as covering all eight**.

Separately, `verify_case` asserts the designated rule fires and the offending labels
match — it **never asserts that no other rule fires**. Cross-talk today is 0/9, so the
assertion is free to adopt *now*; once cases become realistic it is expensive to
introduce retroactively.

### What the matrix is — and what it is not *(clarified 2026-08-11)*

The matrix is read in **three directions, only two of which must ever be complete**. This
is the load-bearing distinction of the stage, and Stage 19's G8 sentence originally implied
the opposite:

| Direction | Complete? | A hole means |
| --- | --- | --- |
| **mode → rule** | **Yes, always** | a catalogued §6 failure mode nothing can detect. A defect, and this stage's primary finding. Restates [`vision.md`](../vision.md) §6: *"at least one heuristic must detect each"* |
| **rule → mode** | **Yes, always** | a registered rule targeting no catalogued mode — so either the mode catalogue is short a mode, or the rule is speculative. Four rules sit here today (`bounds`, `intensity`, `reference_delta`, `intensity_reference_delta`) |
| **feature → rule** | **No — by design** | *nothing.* The feature record is a deliberately over-broad vector that rules **select from**. A leaf path no rule reads is inventory (`unwired`), not a gap; 34 of item 103's 111 catalogued paths are read by nothing today, and full consumption is never an expected end state |

**Evidence rungs.** *"A rule covers this mode"* and *"we have demonstrated it end-to-end"*
are different claims and each mode's row carries **both**. Three legitimate evidence
states, drawn from Stage 21's realism ladder:

- **synthetic-demonstrable** — a rung-1 fixture drives the rule end-to-end today.
- **needs real data (or a corpus the fixtures cannot express)** — the rule exists but the
  hand-crafted geometry cannot produce the input. Mode 7 is structurally capped at a
  **single** rank descent by the label convention (`rank(v) == v - 1` under the TPTBox
  default), so §6.7's own two-descent example — `L1 → T12 → L2 → L5` — is not representable
  at rung 1 at all; mode 1's severity ladder is FOV-capped by the five-level fixture.
- **structurally unobservable in the supported input format** — the *feature* the mode
  targets cannot occur. Mode 8 (overlap) is exactly this: a **single-channel integer label
  map cannot assign two labels to one voxel**, so `overlaps[]` populates only on a map
  deliberately corrupted to violate that invariant, which no real segmenter output can be.
  The `overlap` rule and all six fields it reads are correct and fully wired — the mode
  becomes meaningfully testable only if multichannel / probabilistic segmentation input is
  ever supported, which no stage currently plans.

A row recording *needs real data* or *structurally unobservable* is an acceptable outcome.
A row that is **silent** is not.

**Growth contract.** The catalogue of modes, the rule set and the feature pool grow
**together, and usually in tandem**: a new §6 mode arrives with the rule(s) that detect it,
plus any new feature(s) those rules need when the existing pool does not suffice. The
matrix is what makes that enforceable — a mode with no rule row, or a rule with no mode
row, fails the same way item 104's drift test fails an undocumented feature. **Features may
be added alone** (an unwired feature awaiting a future rule is legitimate and expected); a
mode or a rule may not.

**Deliverables.**

- The **traceability matrix**, *generated* from item 103's catalogue + the rule registry +
  a corpus run rather than hand-maintained: 8 failure modes × rules × the features each
  rule actually consumes, with the three directions above scored separately, and every mode
  row carrying its evidence rung.
- **Map the four mode-less rules** (`bounds`, `intensity`, `reference_delta`,
  `intensity_reference_delta`) to §6 modes, or record that they target none and why —
  closing Stage 19's G8 shortfall at its root.
- **The specificity assertion** — no unintended rule may fire — adopted as a ratchet.
- **Close the reachability hole for modes 1/4/8** by naming the *mechanism* per mode, not
  just the symptom: mode 8 is single-channel-unobservable (above), mode 1's ladder is
  FOV-capped, mode 4's cause is to be determined by the stage. Made pipeline-detectable
  where the mechanism allows, recorded with its mechanism where it does not. Not both
  silent.
- **Per-rule *and per-operator* corpus-exercise reporting**, so neither "6 of 10 rules fire
  on zero cases" nor "the registered `fuse` operator generates no corpus case at all"
  (`synth/component_shape.py:209` vs `synth/corpus.py`'s `CASE_RECIPE`) can recur unnoticed.
- **Widen item 100's mode-1 ladder base** (a larger FOV, or a base with headroom for a
  30–40 mm displacement) so mode 1's own metric swing is set by the perturbation rather than
  the fixture's walls — the recorded root cause of mode 6's Stage-18 specificity shortfall,
  which should then clear without touching mode 6.

**Dependencies.** Stage 19 (the catalogue supplies the feature↔mode column). ⚠️ Several
Stage-26 remediation defects touch the same surfaces this stage audits (`normalised_delta`
attribution, the RAS `touches_*` face mapping, `neighbourhood.py`'s dead wiring) — auditing
before they are fixed records findings that are about to change.

**Validation / acceptance.**

- Every §6 failure mode has ≥1 rule **and** a recorded evidence rung — never
  silent (**G2**).
- Every registered rule maps to ≥1 §6 mode or is recorded as mode-less with a
  reason.
- Every registered rule is exercised by ≥1 case or recorded as unexercised with
  a reason (**G2**).
- The specificity assertion is enforced for every corpus case.
- The end-to-end detection count is stated honestly in `progress.md` (**G7**).
**Explicitly not required:** feature→rule completeness — unwired features are a designed
state, not a defect.
