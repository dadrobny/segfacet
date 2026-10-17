> Stage 31's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 31`, run on the main or queue branch, moves it back.

## Stage 31 — Post-Sign-Off Maintenance: follow-ups, prerequisite defects, engine update (G7, G8)

**Goal.** Item 150 re-organised the failure-mode catalogue from ten entries to sixteen
modes plus a condition, and deliberately left three things behind: a Stage-18/29 eval
harness still keyed by the pre-sign-off ids, a `vision.md` §6 whose numbered list no longer
matches the specification, and a set of open `insights.md` defects in the surfaces Stage 32
will work on. Stage 32 refines each mode against the specification and the corpus;
starting it on a harness that measures retired ids, a vision that contradicts the record
and seams with known defects would make every per-mode checkpoint argue with stale
artifacts. This stage clears that ground. **It changes no failure mode's definition, adds
no rule and moves no expected firing set** — those are Stage 32's.

**Deliverables.**

- **D0 — AIDE engine update (process work, not an item).** The installed engine is
  1.37.0 and the framework has moved to 1.52.1 (measured 2026-09-15 with
  `install.py --into . --check`). Updated through the framework-update workflow in
  CLAUDE.md ("Updating the framework") as its own reviewed PR, before this stage's queue is
  planned, so the queue is authored and run under the current engine. The two open
  `framework` insights (`rollup_status` treating ⏸️ as terminal, queue-020, 2026-09-03;
  `aide merge` deleting the claim branch before its test gate, item 146, 2026-09-04) are
  checked against the new engine's changelog and either ticked with a pointer or handed
  over to `aide-loop`; the Stage 20 status that defect wrote into `progress.md` (item 143,
  2026-09-03) is restored to 🚧 in the same pass.
- **D1 — `vision.md` §6 re-issued (human-gated, not an item).** Through
  `/aide-create-vision` and a reviewed PR: §6 keeps its principles and points at the
  specification as the catalogue, with no numbered mode list (`insights.md`, item 150,
  2026-09-14); the observability classes gain `needs-ground-truth` and
  `needs-external-classifier`; the evidence-rungs paragraph's "two-descent" wording for the
  `L1 → T12 → L2 → L5` example is corrected (`insights.md`, item 147, 2026-09-04); the
  "mode 6 / mode 1" and "mode 8" examples are re-stated against the signed-off ids, and the
  FOV-truncation **condition** is named as a first-class concept. Raised as a human gate
  that blocks D2.
- **D2 — the seed-conformance check follows the re-issue.** Once §6 carries no numbered
  list, `failure_modes.vision_seed_titles()` / `VISION_SEED_DISPOSITION` /
  `vision_seed_conflicts()` are re-pointed or retired as provenance-only, and the
  specification's docstring and generated note stop describing §6 as a seed list. No mode
  content changes.
- **D3 — the eval harness re-keyed to the signed-off catalogue.**
  `segfacet.eval.per_mode`, `severity_ladder`, `per_mode_cohort`, their JSON schemas and
  every pin in `test_099`–`test_102`, `test_109`, `test_125` and `test_135` move from
  `LEGACY_STAGE18_MODE_NAMES` (ids 1–8) to `failure_modes.SPECIFICATION` ids, and the
  legacy map is retired. Each Stage-18 metric is re-homed to the mode it measures or
  recorded as measuring no mode (the `displace` ladder measures the spline-offset signal,
  which after item 150 serves no mode); `KNOWN_CROSS_MODE_COUPLINGS` and `RECORDED_MARGINS`
  are **re-measured**, never carried over. Absorbs Stage 20's **item 141** (the mode-1
  ladder base): the ladder is re-derived for what mode 1 now means, or recorded as having
  no ladder. `feature_docs.MODE_ANCHOR_PATHS[1]` is re-anchored on a path the mode's own
  signal reads (`insights.md`, item 150, 2026-09-14). The false `rank(v) == v - 1` claim in
  `severity_ladder.py` is corrected in the same pass (`insights.md`, item 147, 2026-09-04).
- **D4 — Stage-30 residue in the specification seams.** Each a located `insights.md`
  entry, fixed or recorded as not worth fixing with a reason:
  `failure_mode == 0` meaning both "clean control" and "condition-only case" (replace with
  an explicit sentinel or a `kind` field so a consumer filtering `failure_mode != 0` cannot
  silently drop a condition case); the traceability `_NOTE` and docstring still asserting
  "mode → rule is complete, always" although `proposed` modes are legitimately rule-less;
  the rule-attribution scan covering only the geometric corpus (the intensity corpus is
  unscannable, so mode 16's attribution renders "analytic" beside a demonstrated rung);
  no check reporting a rule that declares a known mode the specification's
  `intended_rules` do not mirror; and the corpus case ids' `modeN_` prefixes, which now lie
  (`mode2_fragment` is mode 1, `mode5_remove_level` is mode 6, `mode8_force_overlap` is
  mode 15). The prefixes are either renamed to mode-neutral ids in one corpus-value change
  with every pin updated, or kept with a recorded decision — the maintainer decides at the
  queue's planning.
- **D5 — prerequisite test and import defects.** The open `defect` entries in the
  surfaces Stage 32 edits: tests skipping forever on a base ref that no longer exists
  (`aide/queue-018`); the committed-artifact guard's missing ground for the traceability
  matrix and its narrow module-root resolver; `segfacet/__init__.py` importing NiBabel
  eagerly, so every submodule import pays for it; the S-axis record test pinned to a
  live-derived fixture set; the AC18 invariance tests and the surplus-declared-mode test
  that still exercise the retired `"corpus"` evidence tag. Entries a later item already
  fixed are ticked with a pointer, not re-fixed.
- **D6 — insight triage to a known state.** Every open `defect` and `gap` entry in
  `insights.md` at this stage's start is ticked with a pointer (fixed here), re-homed with
  a pointer to the mode it belongs to in the specification (for Stage 32 or later
  per-mode work) or to a later stage, or left open with a dated
  reason. `knowledge` entries are left as they are. The CI dev-tooling lockfile and the
  per-grid-point re-extraction in `evaluate --calibrate` are re-homed, not fixed.
- **D7 — stage validation.** The full suite green; the eval harness re-run from a clean
  tree with the re-measured constants recorded in `progress.md`; `aide check` clean of any
  warning this stage's surfaces raise; the triage counts (ticked / re-homed / left open)
  recorded as measured numbers.

**Dependencies.** Stage 30 closed (item 151). D0 lands before the queue is planned; D1's
gate blocks D2 only. Runs before Stage 32 and therefore before Stages 27, 21 and 16.

**Validation / acceptance.**

- The installed engine version equals the framework's at the time the stage's queue was
  planned, or the gap and its reason are recorded.
- `vision.md` §6 names the specification as the catalogue and carries no numbered mode
  list, and no module under `src/segfacet/` asserts that it does (**G8**).
- No module or test under `src/segfacet/` or `tests/` references
  `LEGACY_STAGE18_MODE_NAMES` or keys a per-mode metric, ladder or cohort count by an id
  outside `failure_modes.SPECIFICATION`; the re-measured cross-mode constants are recorded
  with what they were measured on (**G7**).
- No consumer distinguishes a clean control from a condition-only case by
  `failure_mode == 0` alone.
- Every open `defect` and `gap` insight present at the stage's start is ticked, re-homed
  with a pointer, or left open with a dated reason; the three counts are recorded in
  `progress.md` (**G7**).
