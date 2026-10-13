<!-- aide-template: item 3 -->
# Item 221 — Held-out spline offset with every outlier withheld

> **Created:** 2026-10-12 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-030.md`](../queue/queue-030.md) · Item 221
> **Objectives:** G3
> **Suggested branch:** `aide/221-withhold-every-outlier`

---

## Description

The held-out spline-offset estimator,
`compute_leave_one_out_spline_offsets` in
`src/segfacet/features/spline_offset.py` (items 120, 123, 129, 130), withholds
one "dominant outlier" per refit. Insight `2026-10-09-ddc5` part (i) records
the consequence, and the owner wants it fixed next (decision 2026-10-09).
With two or more displaced levels, a clean vertebra can read a larger offset
than a displaced one.

**Why the shipped scheme fails, measured 2026-10-12.** The shipped scheme
picks the dominant outlier as the largest *in-sample* offset. The
`s = n_points` smoothing spline absorbs displacements: on every synthetic
case probed, every in-sample offset is 1.65 mm or less, displaced levels
included. On the two-opposite-displacements case the "dominant outlier" it
withholds is a clean level (index 3). So no in-sample cutoff can find the
outliers, and the cutoff here is applied to **held-out** readings.

**The queue's numbers are stale.** The queue and the shipped docstring quote
a clean 31.96 mm against a displaced 19.31 mm. Today the same case reads:

- the clean terminal T8 (index 7) at 27.74 mm;
- a clean interior level (index 6) at 19.36 mm;
- the displaced index 5 at 12.76 mm.

The drift is from later changes to the synthetic fixture. The defect is
unchanged.

**What this item builds: an add-then-remove search over held-out
readings.** The owner chose this method and its two parameters on
2026-10-12. A1 gives the exact algorithm.

1. **First pass.** Compute today's readings, which withhold the in-sample
   dominant outlier.
2. **Initial withheld set.** Withhold every **interior** level whose
   first-pass reading is at least `_OUTLIER_CUTOFF_MM = 10.0` mm.
3. **Remove phase.** Refit every level with that set withheld. Then put
   back, one at a time, the withheld level that now reads lowest below the
   cutoff, until every withheld level reads at or above it.
4. **Add phase.** If an interior level outside the set now reads at or
   above the cutoff, withhold the largest such reading and return to
   step 3. Each level enters by an add step at most once.
5. **Result.** If the set ends empty, the output is the first pass
   unchanged. Otherwise the output is the readings under the final set. The
   in-sample dominant is no longer withheld in that case: the set replaces
   it.

Terminal levels are never candidates. They stay with item 222.

The VerSe19 interior p99 that `spline_offset.max_offset_mm` was set from is
re-measured and recorded in `docs/reference-build.md` beside `gate-fac1`.

**Not in scope.**

- **The threshold.** `spline_offset.max_offset_mm` (13.0, `heuristics/spline_offset.py`)
  is not retuned. The queue text names it `mislabel.max_offset_mm`, its
  pre-item-189 home. That threshold is `gate-fac1`'s to settle.
- **No record change.** No feature key is added, removed or renamed. No
  rule changes. `reference_verse_v1.json` is not re-committed.
- **Terminal vertebrae.** They are item 222's.
- **Curve formulation.** Degree, smoothing, `u` and `_WITHHELD_WEIGHT` are
  unchanged. They are `gate-2765`'s approval.

## Acceptance Criteria

Terms used below:

- **"The 8-level spine"** is `build_clean_spine(levels=("T1",…,"T8"), spacing=(1.0, 1.0, 1.0), curve_amplitude_mm=6.0)`.
  Its centroids come from `compute_centroid` per label in `spine.labels`
  order. This is test_120's `_eight_level_thoracic_spine()`.
- **"Displace index k by m"** adds `m` mm to `centroid_mm[0]` of the k-th
  centroid, via `dataclasses.replace`.
- **"The two-opposite case"** is the 8-level spine with index 2 displaced by
  +15.0 and index 5 by −15.0.
- **"The item-120 computation for withheld set S"** is built in the test from
  `fit_centroid_spline` and `compute_spline_offsets`, never from this item's
  helpers. For each index `i`:
  - Refit with `fit_centroid_spline(centroids, u=fit_centroid_spline(centroids).u, weights=w)`.
    Here `w[j] = _WITHHELD_WEIGHT` for `j` in `S ∪ {i}`, and `w[j] = 1.0`
    otherwise.
  - Take `compute_spline_offsets([centroids[i]], refit)[0]`.
  - Set its `is_terminal` to `i in (0, n-1)`.

The criteria:

- [ ] **AC1: on the two-opposite case, displaced levels outread every clean
  level.** `min(r[2].offset_mm, r[5].offset_mm) > max(r[k].offset_mm for k in (0, 1, 3, 4, 6, 7))`,
  where `r = compute_leave_one_out_spline_offsets(<two-opposite case>)`.
  Terminals are counted as clean.
- [ ] **AC2: a single outlier reads as before.** On the 8-level spine with
  index 3 displaced by +15.0:
  - `compute_leave_one_out_spline_offsets` returns a list equal, element for
    element, to the item-120 computation for S = {3}.
  - Index 3 is the in-sample dominant the shipped code withholds, so this
    pins that output.
- [ ] **AC3: the withheld set on the two-opposite case is exactly the two
  displaced levels.** `_withhold_outliers(...)`, called as Implementation
  step 3 defines, returns a withheld set equal to `frozenset({2, 5})` on the
  two-opposite case.
- **AC4: withdrawn 2026-10-13** (cross-spec review M3, owner-approved). It
  pinned `_held_out_records` for item 222, which never calls it. AC2 already
  checks the helper's per-level computation through the public function. The
  number is kept free so AC5–AC7 keep their names.
- [ ] **AC5: the cutoff is 10.0 mm.** `segfacet.features.spline_offset._OUTLIER_CUTOFF_MM == 10.0`.
- [ ] **AC6: a terminal level is never withheld.** Take the 8-level spine
  with index 0 displaced by +18.0. That terminal's first-pass reading is
  19.40 mm, and no interior level reads 10 mm or more. On it:
  - `_withhold_outliers` returns an empty withheld set.
  - Its records equal the item-120 computation for S = {the in-sample
    dominant index}, which is today's output.
- [ ] **AC7: the re-measured VerSe19 interior ceiling is recorded.**
  - `docs/reference-build.md` has a section whose heading begins
    `## Rebuild record — ` and contains `item 221`.
  - That section states `P = <value>` mm, where `<value>` equals
    `round(P_artifact, 6)`.
  - `P_artifact` is the largest `spline_offset_mm` `p99` over levels with
    `count >= 10` in the committed `reference_verse_v1.json`. It is computed
    with `scripts/rebuild_verse_reference.py`'s `_p99_by_level`, over the
    artifact `segfacet.reference.artifact.load_artifact(bundled_production_reference_path())`
    loads.

Why each is written:

- **AC1** is the queue's headline claim, and it fails today (12.76 < 27.74).
- **AC2** is the queue's "a single-outlier case reads as before".
- **AC3** pins the withheld set, element 0 of `_withhold_outliers`' return,
  which is the one thing item 222 reads (A6).
- **AC5** is the only pin of the owner's chosen cutoff. A3 measured 8 and 10
  identically on every probed case, so no behavioural test tells them apart.
  Item 222 does not read the constant.
- **AC6** pins the owner's interior-only decision (Q2). Without it, a
  terminal's extrapolation reading enters the set. Measured, that raises the
  VerSe19 interior p99 to about 17 mm (A4).
- **AC7** is "recorded beside `gate-fac1`". The commit and the gate name in
  that section are diff-time facts, and the validator reads them
  (Validation step 3).

Not written, because an existing test already fails without them:

- **"Every corpus case's measured firing equals its expected set."** A4
  measures every geometric corpus case's offsets as bit-identical, so no
  firing moves. `tests/test_147_specification_is_the_record.py::test_ac26_every_corpus_case_agrees_and_status_derives_correctly`
  and `tests/test_041_regression_suite.py` assert this for every case.
- **"A clean case makes no extra refit."** `tests/test_130_one_closest_point_search.py`
  AC15 and AC18 pin the fit counts (5 and 6) on a clean 5-level spine.

No AC closes a Stage 34 criterion. This is a maintenance item.

## Assumptions

`loop.clarify` was forced to interactive for this batch. The owner answered
three questions on 2026-10-12:

- **Method:** first, the backward search over held-out readings. After
  seeing A5's sweep the same day, the owner switched to the add-then-remove
  variant (Decisions & Trade-offs).
- **Q1:** a cutoff of 10.0 mm, as `_OUTLIER_CUTOFF_MM`.
- **Q2:** interior levels only.
- **Q3:** a dated rebuild record in `docs/reference-build.md`.

All numbers were measured 2026-10-12 on `aide/queue-030` at `f60e512`, with
`.venv/bin/python`. Source is identical to `2a1491d`. The scratch probes
re-implemented the method outside the repo. The builder re-measures on the
real change.

- **A1 (decided: the add-then-remove search, exactly).** Notation:
  - `n = len(centroids)`.
  - The interior is the indices `1 … n-2` of the input sequence.
  - `C = _OUTLIER_CUTOFF_MM`.
  - `H(S)` is `_held_out_records(centroids, S, reference_fit, spacing_mm, backend)`.
  - `r[i]` is `r[i].offset_mm`.
  - `lab(i)` is `centroids[i].label`.

  The search:
  1. Take `first = H({dominant})`. `dominant` is today's in-sample choice:
     the largest in-sample `offset_mm`, ties broken by ascending label.
  2. Set `W = {i in interior : first[i] >= C}`. If `W` is empty, return
     `(frozenset(), first)`.
  3. Set `added = set()` and `cur = H(W)`.
  4. **Remove phase.** While some `j` in `W` has `cur[j] < C`:
     - remove the `j` with the smallest `(cur[j], lab(j))`;
     - set `cur = H(W)` if `W` is non-empty, else `cur = first`.
  5. **Add phase.** Let
     `cand = {i in interior : i not in W, i not in added, cur[i] >= C}`.
     - If `cand` is empty, go to step 6.
     - Otherwise take the `k` with the smallest `(-cur[k], lab(k))`: the
       largest reading, ties to the smaller label.
     - Add `k` to both `added` and `W`, set `cur = H(W)`, and go to step 4.
  6. Return `(frozenset(W), cur)` if `W` is non-empty, else
     `(frozenset(), first)`.

  **Termination.** Each interior index enters through step 5 at most once,
  so there are at most `n-2` add steps. Each remove phase ends within `|W|`
  removals.

  **Refit count.** A clean case, where no interior first-pass reading
  reaches `C`, makes exactly `n` refits, as today.

  Members of the initial set from step 2 are not in `added`. Such a member
  re-admitted in step 4 can therefore re-enter once through step 5.
- **A2 (measured: why held-out, and why a search).** Three alternatives were
  probed on eight synthetic cases: clean ×2, single, two-opposite, two
  same-side, adjacent pair, 12 levels with two displaced, 12 levels with
  three displaced.
  - **In-sample cutoff.** Fixed 5 mm or median + 3·MAD are identical to
    today. In-sample offsets never exceed 1.65 mm.
  - **One pass over first-pass readings.** On the two-opposite case it
    withholds every level, and the fit collapses to a global least-squares
    cubic.
  - **Forward search from a pure leave-one-out.** It withholds terminals
    first and diverges (readings up to 212 mm).
  - **The backward-only search at 10 mm, and the A1 variant at 10 mm.** Both
    recover exactly the displaced set on all eight cases. On the
    two-opposite case both read 14.99 / 14.96 mm displaced against at most
    2.65 mm clean (terminal T1).
  - A5's full sweep is what separates the two.
- **A3 (measured under A1: why 10.0 mm).** The workable window is still
  (6.92, 12.76) mm.
  - **Lower bound.** At 6 mm the corpus `displace` case also withholds its
    neighbour index 1, which reads 6.92. That drops label 22 from 14.615923
    to 9.48 mm, below 13.0, so `spline_offset` would stop firing on the
    `displaced_vertebra` condition's own fixture.
  - **Upper bound.** At 13 mm the two-opposite case fails: index 5's
    first-pass 12.76 does not enter the set, the search settles on
    `{1, 4, 5, 6}`, and a clean level reads 22.78 mm.
  - 8 and 10 behave identically on all nine cases probed: the eight above
    plus AC6's. The owner chose 10, which sits near the window's centre.
  - Tying the cutoff to `max_offset_mm` was rejected. It fails the window,
    and the threshold is derived from offsets the cutoff would shape, so it
    is circular.
- **A4 (measured under A1: the effect on real data and the corpus).** The
  backward-only search measured the same values.
  - **VerSe19.** The cohort is 80 subjects: 863 vertebra rows, 703 interior
    and 160 terminal, staged under `out/verse-rebuild/staged_verse`.
    Centroids came from `compute_centroid` in `anatomical_order`, as
    `pipeline.extract_feature_record` does.
    - Every reading is bit-identical to today: max |diff| 0.
    - Only `sub-verse406_split-verse261` gets a non-empty set, `{T10}`.
      That is today's in-sample dominant, so it reads 18.51 mm as before.
    - Interior `P = 12.906` mm at T10 (count 37, derived threshold 13.0).
      This equals the committed artifact's `12.90577608928562`.
  - **Admitting terminals as candidates** (rejected, Q2): 18–30 subjects
    change, and interior P rises to 16.5–17.0 mm at L4 (derived threshold
    17.0). Withholding a terminal makes the next interior level extrapolate.
  - **Corpus.** Every one of the 15 geometric corpus cases is bit-identical.
    `displace` gets `W = {2}`, which is today's dominant. So no golden, no
    expected set and no threshold margin in `heuristics/spline_offset.py`'s
    docstring moves.
  - **Correction (2026-10-13, re-checked at `79ae4964` after items 218, 219
    and 220 merged into `aide/queue-030`).** `tests/corpus/manifest.json`
    holds **14** cases, not 15, and held 14 at `f60e512` too. Items 218 and
    219 changed the synth generators, so the claim was re-measured with a
    prototype of A1 in a throwaway worktree: every one of the 14 cases'
    whole `pipeline.extract_feature_record` output is identical to the
    shipped code's. `displace` label 22 still reads 14.615923 mm and its
    neighbour label 21 6.918745 mm (A3). The conclusion stands.
- **A5 (measured: what each method fixes).** The sweep displaced every pair
  of interior levels, ±15 mm on axis 0, on clean thoracic spines of 6, 8, 10
  and 12 levels (`build_clean_spine`, `curve_amplitude_mm=6.0`). A pair
  counts when both displaced levels outread every clean level, terminals
  included. The probe was a scratch script and is not committed. The
  builder can reproduce the table from this definition.

  | Levels | Pairs | Opposite: today / backward-only / **A1** | Same-side: today / backward-only / **A1** |
  |---|---|---|---|
  | 6 | 6 | 0 / 3 / **3** | 0 / 1 / **1** |
  | 8 | 15 | 0 / 10 / **11** | 0 / 5 / **6** |
  | 10 | 28 | 0 / 25 / **27** | 0 / 16 / **19** |
  | 12 | 45 | 2 / 33 / **43** | 0 / 29 / **35** |

  - **What the add phase fixes.** The backward-only search misses mostly
    displacements two levels apart. The clean level between them reads high
    on the first pass, and a search that only removes cannot add the
    displaced one.
  - **What A1 still misses.**
    - **Same-side displacements one or two levels apart.** The smoothing
      spline follows them as a bend, so they read under the cutoff on the
      first pass. For example, the 8-level spine with indices 2 and 3 both
      +15 mm first-reads 7.20 and 0.71 mm, so nothing about them is
      withheld.
    - **Spines of six levels or fewer.**
  - **The docstring.** The module docstring records this table and these
    two shortfalls as a documented limitation. It replaces today's "only the
    single dominant outlier is withheld" block.
  - **A first variant, also measured.** It had no `added` bound and stopped
    at a repeated set. It measured the same or one pair fewer in every cell
    (opposite 10 levels 26, same-side 12 levels 35). A1's bounded rule was
    kept because it terminates within `n-2` add steps.
- **A6 (the interface; item 222 reads one part of it).** Item 222 reads only
  element 0 of `_withhold_outliers`' return, the withheld set. It never calls
  `_held_out_records`, and it does not read `_OUTLIER_CUTOFF_MM` directly.
  The other names below are this item's own structure. All of them live in
  `src/segfacet/features/spline_offset.py`.
  - **The public function.**
    `compute_leave_one_out_spline_offsets(centroids, spacing_mm=None, *, fit=None, backend=None) -> List[VertebralSplineOffset]`.
    Its signature, record fields, record order, the `fit` count check, the
    single-centroid return and the below-five fallback are unchanged.
  - **`_OUTLIER_CUTOFF_MM: float = 10.0`.**
  - **`_held_out_records(centroids, withheld, reference_fit, spacing_mm, backend) -> List[VertebralSplineOffset]`.**
    For each index `i` it:
    - refits through `reference_fit.u` with `_WITHHELD_WEIGHT` on `i` and on
      every index in `withheld`, and `1.0` elsewhere;
    - measures `centroids[i]` with `compute_spline_offsets`;
    - sets `is_terminal` from the outer sequence (`n <= 2 or i in (0, n-1)`).

    `withheld` is any iterable of sequence indices. It may contain `i`, and
    may be empty. The result is in input order.
  - **`_withhold_outliers(centroids, first_pass, reference_fit, spacing_mm, backend) -> Tuple[FrozenSet[int], List[VertebralSplineOffset]]`.**
    It runs A1 steps 2–6 from the first-pass records: the add-then-remove
    search. A first draft of this spec gave a backward-only search under the
    same name and signature; the algorithm changed and the interface did not.
    It returns the final withheld set (sequence indices, interior only,
    empty when nothing survives) and the records measured under it, which
    are `first_pass` itself when the set is empty.

  The public function is `_withhold_outliers(c, first, fit, ...)[1]` above
  the fallback.
- **A7: no human gate and no environment-gated capability.**
  - The VerSe19 cohort is read only by Validation steps 1–2, under the
    existing `SEGFACET_VERSE_COHORT` convention. No test reads it.
  - `gate-fac1` stays ⏳ and is not touched. The record in
    `docs/reference-build.md` names it so a reader of the gate finds the new
    number.

## Implementation Steps

1. **`_held_out_records`** (A6). Lift the body of today's per-level loop
   into it:
   - the `weights` construction;
   - `fit_centroid_spline(centroids, u=reference_fit.u, weights=..., backend=backend)`;
   - `compute_spline_offsets([centroids[i]], refit, ...)[0]`;
   - the `is_terminal` substitution through `dataclasses.replace`.

   Weights are `1.0`, except `_WITHHELD_WEIGHT` at `i` and at every index in
   `withheld`.
2. **`_OUTLIER_CUTOFF_MM = 10.0`.** Add it beside `_WITHHELD_WEIGHT`, with a
   comment giving A3's window and the owner decision of 2026-10-12.
3. **`_withhold_outliers`** (A1 steps 2–6, A6). Follow A1 exactly:
   - The remove phase picks the smallest `(offset_mm, label)`.
   - The add phase picks the smallest `(-offset_mm, label)`, and only from
     interior indices not yet in `added`.
   - An emptied set falls back to `first_pass`.

   `label` is `centroids[j].label`. The `added` bound is the termination
   guarantee; do not replace it with an iteration cap.
4. **`compute_leave_one_out_spline_offsets`.** After the existing fallbacks,
   compute `in_sample` and `worst_idx` as today. Then:
   - `first = _held_out_records(centroids, {worst_idx}, reference_fit, spacing_mm, backend)`;
   - return `_withhold_outliers(centroids, first, reference_fit, spacing_mm, backend)[1]`.

   Update the function docstring.
5. **The module docstring.**
   - Rewrite "Held-out evaluation" step 1–2. The dominant outlier is the
     first pass; then the add-then-remove search, the cutoff, interior only,
     and why held-out rather than in-sample (A2). Keep the words "ascending" and
     "label" for the tie-break, which test_120 AC6 reads.
   - Replace the block "Documented limitation: only the single dominant
     outlier is withheld" with A5's sweep and its cause.
   - Re-word the "terminal level on a short spine" limitation, which
     mentions "the dominant outlier".
   - Keep every token another test reads, unchanged: "five", "cubic",
     "interpolat", "weight", "0.001", "15", "degree", "human gate",
     "deformity", "cpu", "fallback", "load_volume", "centroid_voxel" and
     "spacing".
6. **`src/segfacet/feature_docs.py`**, `GROUP_INTROS["Spline Offset"]`.
   "refit with that level and the case's dominant outlier down-weighted"
   becomes "refit with that level, and every interior level that still reads
   10 mm or more once its fellow outliers are withheld, down-weighted (item
   221)". Keep "held-out" and the RAS sentence, which test_120 AC30 reads.
   Regenerate with `.venv/bin/python -m segfacet.catalogue`, twice into
   scratch, byte-compare, then the committed copies.
7. **The VerSe19 record.** Run Validation steps 1–2. Then add
   `## Rebuild record — <date> (item 221, every interior outlier withheld)`
   to `docs/reference-build.md`, after item 123's two records. It states:
   - the method (`scripts/rebuild_verse_reference.py` on the 80-subject
     cohort, `--verse-cohort dataset-verse19training`);
   - the commit measured at;
   - `P = <round(P, 6)>` mm at its level, with count;
   - the derived threshold;
   - that every level's `spline_offset_mm` statistics equal the committed
     artifact's, which is therefore not re-committed;
   - that `spline_offset.max_offset_mm` stays 13.0 and that `gate-fac1`
     (verse406 T10, 18.51 mm) is unchanged and still open.
8. **Reconcile the existing test** (Testing Strategy). Add a dated
   `# Item 221 (2026-10-12): ...` comment, the house style.
9. Run `python .aide/scripts/aide.py scope 221` and
   `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. `fit_centroid_spline`, `compute_spline_offsets` and
`dataclasses.replace` are already used here.

## Authorised paths

**May change:**

- `src/segfacet/features/spline_offset.py` — the search, the two helpers, the constant, the docstrings (steps 1–5).
- `src/segfacet/feature_docs.py` — the Spline Offset group note (step 6).
- `docs/aide/feature_catalogue.generated.json` — regenerated (step 6).
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/reference-build.md` — the item-221 rebuild record (step 7).
- `tests/test_221_withhold_every_outlier.py` — **new**: this item's test module.
- `tests/test_120_leave_one_out_offset.py` — reconcile the two-opposite limitation test (step 8).

**Asserts against:**

- `src/segfacet/reference/reference_verse_v1.json` — AC7 recomputes P from it; it is not rebuilt into the tree.
- `scripts/rebuild_verse_reference.py` — AC7 reads its `_p99_by_level`; unchanged.
- `tests/test_130_one_closest_point_search.py` — must stay green unedited: a clean case makes no extra refit.

## Testing Strategy

The test module is `tests/test_221_withhold_every_outlier.py`, with one test
per AC. Spines are built with `segfacet.synth.clean_gt.build_clean_spine` and
`compute_centroid`, exactly as the AC terms define. The item-120 computation
is written out in the test from `fit_centroid_spline` and
`compute_spline_offsets`. It never calls `_held_out_records`; otherwise AC2
would compare the helper with itself. AC4 is withdrawn and gets no test.

Adversarial cases, each with the failure mode it guards, and no others:

- `emptied-set-returns-first-pass`: the 8-level spine with indices 2 and 3
  both displaced by +15.0.
  - Measured: index 1 enters on the first pass (11.39 mm). It is
    re-admitted, re-added once through the add phase, and re-admitted again.
  - `_withhold_outliers` returns an empty set, and the public function's
    records equal the item-120 computation for S = {the in-sample dominant}.
  - It guards a search that, once emptied, returns the pure leave-one-out
    readings. Those differ from today's: index 1 reads 0.80 mm there
    against 11.39.
  - This is one of A5's same-side misses. The test pins the fallback, not a
    separation.
- `add-step-bounded`: the 8-level spine with index 2 displaced by +15.0 and
  index 4 by −15.0, under `_OUTLIER_CUTOFF_MM` monkeypatched to 6.0, 10.0
  and 13.0.
  - Measured final sets: `{1, 5, 6}`, `{5}` and the empty set.
  - Each `_withhold_outliers` call returns. The returned set is a subset of
    the interior `1 … 6`.
  - It guards an add/remove cycle that never ends when the `added` bound is
    dropped or mis-keyed. Its three cutoffs end in three different sets, so
    the search exercises both phases.
- `five-levels-every-interior-withheld`: `build_clean_spine(levels=("L1",…,"L5"), …)`
  with indices 1, 2 and 3 displaced by +15, −15 and +15.
  - The set is `{1, 2, 3}`. All five records are finite, and none raises.
  - It guards the degenerate fit with only the two terminals at full
    weight.
- `withheld-set-is-interior-indices`: on the two-opposite case and on AC6's
  case, every index in the returned set lies in `1 … n-2`.
  - It guards an off-by-one candidate range that admits index 0 or `n-1`
    through the boundary rather than through a terminal's reading.

**Existing tests to reconcile.** These were found by grepping `tests/` for
`compute_leave_one_out_spline_offsets`, "dominant outlier", "single
dominant" and the module-docstring assertions. They are a lower bound
(`CLAUDE.md`, "A spec-time probe ... is a lower bound").

- **`tests/test_120_leave_one_out_offset.py::test_adv_two_opposite_displacements_both_separate`.**
  Its first two assertions (both displaced levels over 5 mm) still hold:
  14.99 and 14.96. Its last assertion pins the limitation this item removes
  (clean index 7 > index 5). Today that reads 27.74 > 12.76; after this item
  it reads 1.39 < 14.96, so it fails.
  - Invert it to `records[7].offset_mm < records[5].offset_mm`.
  - Re-word the docstring to name item 221.
  - AC1 is the full claim, so nothing more is added here.

Checked and expected to stay green unedited:

- **test_120**: AC6 `displace` (W = {2}, bit-identical), AC6 tie-break text,
  AC7–AC9, AC17, AC30, AC31, and the terminal-5, terminal-8, 30 mm z-step,
  anisotropic, four-level, one-level-removed and not-mutated cases. On the
  probe, terminal-8 and z-step read identically to today.
- **`test_123`**, **`test_129`** and **`test_135`** docstring tests: the
  tokens are kept (step 5).
- **`test_130`**: fit counts on a clean spine.
- **`test_072`**: CPU-fallback text.

**Re-check (2026-10-13, at `79ae4964`, after items 218, 219 and 220 merged
into `aide/queue-030`).** None of the three touched
`src/segfacet/features/spline_offset.py`. A1 plus Implementation step 6
(the group note, then the catalogue regenerated) was prototyped in a
throwaway `git worktree`, since removed, and the whole `tests/` suite was
run against it: 8180 collected, 8106 passed, 73 skipped, 1 failed. The one
failure is `test_adv_two_opposite_displacements_both_separate`, at
`1.3855 > 14.9609`, so the fence above is complete as written. Every
figure in the Acceptance Criteria, A3, A5's worked example and the
adversarial cases above re-measured the same: 27.74, 19.36 and 12.76 mm
today; 14.99 and 14.96 against at most 2.65 mm after; AC6's 19.40 mm; the
11.39 and 0.80 mm of `emptied-set-returns-first-pass`; the cutoff-6, 10 and
13 sets `{1, 5, 6}`, `{5}` and empty; `{1, 2, 3}` on five levels. AC7's `P`
recomputes to `12.90577608928562` at T10, count 37. Two limits on this
probe. The VerSe19-gated tests in `test_084`, `086`, `087`, `088`, `091`,
`118`, `123` and `125` skip when `SEGFACET_VERSE_COHORT` is unset, which
is how the suite runs by default, so they were not compared; Validation
steps 1–2 measure VerSe19 directly. And regenerating the catalogue changes
only `docs/aide/feature_catalogue.generated.json`, one `intro` string:
the `.md` rendering does not carry group notes, so its **May change**
entry will normally stay unused.

## Validation

1. **Rebuild the VerSe19 reference on the branch.** Where
   `SEGFACET_VERSE_COHORT` or the `dataset-verse19training` symlink reaches
   the cohort, run:

   ```
   .venv/bin/python scripts/rebuild_verse_reference.py --out <tmp>/verse-rebuild --verse-cohort dataset-verse19training
   ```

   It exits `0`, and `verse_rebuild_summary.json`'s cohort block reports 80
   masks.
2. **Compare the offset statistics.** For every level, the rebuilt
   artifact's `spline_offset_mm` statistics equal the committed
   `src/segfacet/reference/reference_verse_v1.json`'s. The summary's
   `calibration` reads P ≈ 12.906 at T10 and threshold 13.0.
   - A difference in `spline_offset_mm` means the real-data behaviour
     departs from A4. **Hand back**; do not commit a rebuilt artifact.
   - Differences in other features are outside this item. Record them in
     Decisions & Trade-offs and do not commit them.
3. **Read the record.** The new section in `docs/reference-build.md`:
   - names `gate-fac1`;
   - gives a commit hash on this branch that `git cat-file -t` resolves to a
     commit;
   - states P to six decimals;
   - says `max_offset_mm` is unchanged.

   Where the cohort is absent, record **❓ Unverified (VerSe19 absent)**
   against steps 1–2 in Decisions & Trade-offs, rather than a pass. Step 7's
   record then cannot be written from a measurement, so **hand back**. No
   `[validation]` profile exists for the cohort.

## Dependencies

None.

**Downstream:**

- Item 222 changes the same estimator for terminal vertebrae and lands after
  this item. It reads element 0 of `_withhold_outliers`' return (the
  withheld set), as A6 states.
- Stage 35's reference rebuild (queue 031) reads the estimator, so this
  queue goes first.

## Decisions & Trade-offs

To be updated during implementation.

- **Implemented (2026-10-13), commit `704c4eea`.** `_held_out_records`, `_withhold_outliers` and `_OUTLIER_CUTOFF_MM` follow A1 and A6 exactly. Module and function docstrings and the `feature_docs.py` group note are updated, and the catalogue JSON is regenerated (two runs byte-identical; the `.md` rendering did not change).
- **VerSe19 validation (Validation steps 1-2): verified.** The rebuild exited 0 on 80 masks. `P = 12.90577608928562` mm at T10 (count 37), threshold 13.0. Every `spline_offset_mm` percentile at or above p25 equals the committed artifact's. `L3` p1 and `L4` p1 and p5 differ by 1e-15 or less, and `mean`, `std` and `min` by float-summation noise (at most 1e-8 relative). No behavioural difference, so the artifact is not re-committed. Strict bit-equality of those cells does not hold.
  - *Correction, 2026-10-13:* the cause of the differing cells is not established. The per-mask readings are identical, and nine statistic cells differ (percentiles by at most about 1e-15, mean and std by at most about 1e-8 relative, min past the 8th significant digit); an order statistic such as min, p1 or p5 cannot move with summation order. No rebuild at the base commit was run, so a numpy, scipy or platform difference from the committed artifact's build is only plausible. P was computed from the committed `reference_verse_v1.json`.
- The full suite (`-n auto`, ignoring `.aide`) was green: 11787 passed, 74 skipped.

- **Decision (owner, 2026-10-12): add-then-remove, not backward-only.**
  - The owner first chose the backward-only search on an eight-case probe,
    where it recovered every displaced set.
  - A5's full pair sweep then showed it missing many displacements two
    levels apart: 33 of 45 opposite pairs at 12 levels.
  - The A1 variant measured 43 of 45 there, and the same or better in every
    other cell.
  - The variant leaves the cutoff window, the corpus and VerSe19 exactly as
    the backward-only search did (A3, A4).
  - The owner switched the same day. The interface item 222 reads (A6) did
    not change.
- **Left open:** same-side displacements one or two levels apart are still
  often missed: 35 of 45 same-side pairs at 12 levels, and 6 of 15 at 8
  (A5). The smoothing spline follows two neighbours displaced the same way
  as a bend, so they first-read under the cutoff and never enter the set.
  No withholding rule that starts from the first-pass readings sees them.
  Whether another signal should is a later item's question.
- **Left open:** on six or fewer levels, two displaced interior levels
  separate in at most half the pairs. A short field of view carries too few
  full-weight points, the same cause as the four-level blind spot item 129
  recorded.
- **Left open:** the cutoff is a constant, not a rule parameter. It shapes
  the feature the reference is built from, so making it configurable per run
  would make the reference artifact depend on run configuration.
