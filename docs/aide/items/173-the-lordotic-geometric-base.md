<!-- aide-template: item 2 -->
# Item 173 — The lordotic geometric base

> **Created:** 2026-09-23 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 173
> **Objectives:** G2, G7
> **Suggested branch:** `aide/173-the-lordotic-geometric-base`

---

## Description

Roadmap Stage 33 D1, first bullet. The maintainer decision is the `gap` entry
in `docs/aide/insights.md` dated 2026-09-22 ("maintainer decision on the
geometric corpus base").

`src/segfacet/synth/clean_gt.py::build_clean_spine` builds every synthetic
spine in the repo: the clean control and base of both committed corpora, the
severity-ladder base, the synthetic `reference_default.json` cohort, and the
catalogue's driver records. Today it builds five axis-aligned 30 × 25 × 25 mm
boxes with a 15 mm gap along S-I and a 6 mm lateral hump. The queue-022 review
found that this base cannot express what the rules are meant to decide. For
example, `neighbour_contact`'s one firing value is just the fixture's largest
cross-section.

This item replaces that geometry in place with a lordotic L1–L5:

- **Tilt.** Each body keeps its 30 × 25 × 25 mm size and is rotated about the
  L-R axis by a per-level sagittal tilt: L1 −8°, L2 0°, L3 +8°, L4 +18°,
  L5 +35°. Positive means the anterior edge is lower.
- **Gap.** The inter-body gap along S-I is 8 mm, a disc height. It was 15 mm.
- **A-P path.** The path is the integral of the tilts. Walking caudally, each
  step moves A-P by the S-I step times the tangent of the mean of the two
  bodies' tilts.
- **No lateral curve.** Scoliosis is not the base case.

The builder is absorbed from
`scripts/prototypes/2026-09-22-lordotic-corpus/lordotic_spine.py`. It moves
into `clean_gt.py` and keeps `build_clean_spine`'s signature, so every existing
caller and every manifest `base` record still reproduces its spine.

With the base replaced, this item regenerates both committed corpora and every
generated artifact downstream of them:

- the synthetic reference;
- the feature catalogue;
- the failure-mode specification rendering;
- the traceability matrix;
- the golden-evidence companion;
- the `test_094` loader snapshot.

It also re-transcribes the severity-ladder constants measured on the old base,
because `test_154` pins the ladder's base to the corpus's base and pins each
constant to a fresh measurement. Every value that `src/` prose quotes from the
corpus is re-measured and not carried over.

**Not in scope.** No operator is changed. Measured on 2026-09-23, `fragment`
and `split` still carve and donate correctly on tilted bodies (A9). `split`,
`crop_at_border`, `fuse_adjacent` and `displace` are re-authored by items
174–177. No rule and no threshold changes. No corpus case is added or
removed. The prototype directory is not touched, because item 178 deletes it.
The severity ladder does not gain a `split` entry, which is D4's work. No
`expected_firing` changes unless a measured firing moved, and none did in
the 2026-09-23 measurement (A6).

## Acceptance Criteria

Unless stated otherwise, every criterion is measured on the **committed**
`clean_control` seg fixture. The test resolves it through
`segfacet.synth.corpus.load_manifest()` and `CORPUS_DIR`, and loads it with
`nibabel`. Voxel centres are taken in mm through the fixture's own affine,
with x as L-R (array axis 0), y as A-P (axis 1, +anterior) and z as S-I
(axis 2, +superior). A label's centroid is the mean of its voxel centres. The
tilt values are the maintainer's, written literally in the test, and are never
read from the module under test.

- [ ] **AC1: Each body carries its level's sagittal tilt.** For each of labels
  20–24, the tilt measured from the voxel mask is within 1.0° of the
  maintainer's value. The values are 20 (L1) −8°, 21 (L2) 0°, 22 (L3) +8°,
  23 (L4) +18° and 24 (L5) +35°. The measurement uses the label's voxel
  centres projected onto (y, z) and deduplicated, with mean (ȳ, z̄). For θ in
  (−45°, 45°] at 0.1° steps, compute u = (y−ȳ)·cosθ − (z−z̄)·sinθ and
  v = (y−ȳ)·sinθ + (z−z̄)·cosθ. The measured tilt is the θ that minimises
  (max u − min u) · (max v − min v), the minimum-area bounding rectangle.
- [ ] **AC2: Consecutive bodies sit 33 mm apart along S-I.** For each
  consecutive label pair (20, 21), (21, 22), (22, 23) and (23, 24), the S-I
  centroid of the lower-numbered label minus that of the higher-numbered label
  is 33.0 ± 1.0 mm. That is a 25 mm body plus the 8 mm disc gap, advancing
  caudally.
- [ ] **AC3: The A-P path is the integral of the tilts.** For each consecutive
  pair (a, b), let Δ be b's centroid minus a's centroid. Then ΔAP equals
  ΔS · tan((tilt_a + tilt_b) / 2) within 0.5 mm, using AC1's literal tilts.
- [ ] **AC4: There is no lateral curve.** The largest L-R centroid minus the
  smallest, over labels 20–24, is at most 0.5 mm.
- [ ] **AC5: The default build is the committed clean control.**
  `segfacet.synth.clean_gt.build_clean_spine()`, called with no arguments,
  returns a `seg_img` whose array is `np.array_equal` to the committed
  `clean_control` fixture's array.
- [ ] **AC6: The default build's affine is the committed clean control's.**
  `build_clean_spine().seg_img.affine` is `np.array_equal` to the committed
  `clean_control` fixture's affine.
- [ ] **AC7: Both corpora sit on the same base.** The committed intensity
  corpus's clean seg fixture has an array that is `np.array_equal` to the
  committed geometric `clean_control` array. The test resolves it as the
  `seg_fixture` of the `clean_hu` case in
  `segfacet.synth.intensity.load_intensity_manifest()`, under
  `INTENSITY_CORPUS_DIR`.

These criteria close no stage acceptance criterion. Stage 33's criteria are
closed by D5 and D6.

## Assumptions

- **A1 (defensible default: replace in place, keyed by level name).**
  `build_clean_spine`'s geometry is replaced for **every** call. There is no
  opt-in flag. The keyword signature (`levels`, `spacing`, `convention`,
  `curve_amplitude_mm`) is unchanged. The decision says "replace", and item
  143 is the precedent for changing the generator globally.

  The tilt is looked up by canonical level name, from a private module
  mapping `L1 −8, L2 0, L3 +8, L4 +18, L5 +35`. A level outside that mapping
  (any cervical or thoracic level) has tilt 0°. The maintainer's tilts are
  lumbar-only, and a partial lumbar span such as `("L3", "L4", "L5")` keeps
  those levels' own tilts. `curve_amplitude_mm` stays as a parameter because
  about 15 callers pass it, including the reference cohort's per-subject
  variability. Its default becomes `0.0`.
- **A2 (defensible default: the three base-parameter dicts).**
  `segfacet.synth.corpus._DEFAULT_BASE_PARAMS`,
  `segfacet.synth.intensity._DEFAULT_BASE_PARAMS` and
  `segfacet.eval.severity_ladder._BASE_PARAMS` keep their `curve_amplitude_mm`
  key, set to `0.0`. The manifest `base` record keeps its shape.
  `severity_ladder._BASE_PARAMS` must equal the corpus's
  (`test_154` AC4/AC5). `synth/regression.py` rebuilds `force_overlap`'s base
  from `case["base"]`, so the base must stay reproducible from those
  parameters.
- **A3 (defensible default: voxelisation).** Membership follows the
  prototype. A voxel belongs to a body iff its centre, `index · spacing` (the
  affine's own mapping), lies inside the rotated box. The shape is the
  centroid span plus the worst-case rotated half-extent over the span's levels
  plus the margin, per axis. The margin is **at least one voxel** on every
  face at any spacing, so `max(1, ceil(15 mm / s))` voxels, as the old builder
  guaranteed. The prototype's mm-only margin touches the right face at 20 mm
  spacing: probe shape `(3, 4, 7)` gave three `border` findings, and
  `tests/test_092_eval_reference_wiring.py` builds exactly that spacing.
  `voxel_counts` is counted from the array. It is no longer the box product.
- **A4 (defensible default: the reference cohort recipe is unchanged).**
  `reference/artifact.py::_DEFAULT_COHORT_RECIPE` keeps its subjects,
  spacings and curve amplitudes. Only the builder under it changes, and
  `reference_default.json` is regenerated.
- **A5 (defensible default: the prototype directory is untouched).**
  `corpus_v2.py` imports `lordotic_spine.build`, and items 174–177 draw their
  operators from `corpus_v2.py`. Item 178 deletes the directory
  (queue-023). This item copies the builder's logic. It neither imports nor
  deletes the prototype.
- **A6 (measured 2026-09-23, spec-author probe on this branch's base, not
  committed).** The probe monkeypatched a builder per A1–A3 over
  `clean_gt.build_clean_spine` and the three base dicts. Findings:
  - The default build passes with zero findings. It is one component per
    label, with shape `(60, 92, 197)` and voxel counts 19 344–19 437.
  - Measured tilts are −8.1, 0.0, 8.1, 18.4 and 35.0°.
  - S-I steps are 32.6–33.4 mm.
  - ΔAP is within 0.24 mm of ΔS·tan(mean tilt). L5 sits 24.1 mm posterior of
    L1. The L-R centroid spread is 0.0 mm.
  - All twelve geometric cases' rule-level firing sets equal today's
    `expected_firing`, and so do their detector sets. `split` is still
    `fragmentation.components` plus `fragmentation.neighbour_contact`.
  - All four intensity cases' firing sets are unchanged.
  - Both corpora regenerate byte-identically run to run.
  - The spans `T5`–`T10`, `L3`, `L5` and `L1`–`L2` pass, and so do spacings
    `(1, 1, 3)`, `(2, 0.5, 1.5)`, `(1, 1, 0.8)` and `(1.1, 1.1, 1.1)`.

  The builder re-measures every value above. If any case's firing moves, the
  queue's instruction applies (step 5).
- **A7 (measured 2026-09-23, same probe): `split`'s stray contact moves.**
  `per_label["23"].components.stray_contact_area_mm2` on the regenerated
  `split` case is 775.0 mm², which is +675.0 above the 100.0 mm² threshold.
  Every other label of every other case reads 0.0 mm². `src/` prose quotes
  750.0 and +650.0 in four places (step 6).
- **A8 (measured 2026-09-23, same probe): the severity ladder's ratchet
  fails on the new base.** `score_harness(run_severity_harness(base=<lordotic
  base>))`:
  - `crop_at_border`'s coupling response to `unanchored_foreground_fraction`
    is 3.832, against the recorded 2.79 · 1.05. Its margin is 0.2609, against
    the recorded 0.3585 · 0.95.
  - The other margins are: `inject_islands` 118.49 (recorded 112.0),
    `force_overlap` 1.742 (recorded 1.038), and the rest `inf`.
  - `force_overlap`'s coupling cause text credits "the constant 15mm
    inter-body gap".

  `test_154` AC6–AC10 pin fresh transcription, the measured coupling set and
  base equality, so every constant is re-transcribed from one fresh run
  (step 7). This is not deferred to D4, because the base cannot move without
  them. D4 still re-measures after D2 and adds `split`.
- **A9 (measured 2026-09-23): `fragment` and `split` need no change.** A
  1-voxel cut perpendicular to array axis 2 through a tilted convex body
  still disconnects it, so `fragment` leaves L3 in two components. `split`'s
  donated end-slab of L3 (indices 85–95 of 85–112) is still a detached piece
  of L4. The queue's "made to work on the tilted base" holds with no code
  change. `fragment` is parked (queue-023, item 173).
- **A10 (merged dependencies, read live on `aide/queue-023`):**
  - Item 170's session fixtures `regenerated_failure_modes` and
    `regenerated_traceability` exist in `tests/conftest.py`, backed by
    `tests/session_artifacts.py::regenerate`. A reconciled test that needs a
    regeneration uses them rather than calling a regenerator itself.
  - Item 171's rule applies to any negative control this item's tests build:
    the "wrong" value is derived from live state.
  - Item 172's `traceability.operator_reason_conflicts()` must stay empty.
    This item takes no operator out of use.

  These are the merged code, not forward pins.
- **A11: no human gate, and no environment-gated capability.** Every step
  runs in the plain project venv. The intensity corpus is measured with
  `enable_pyradiomics=False` (`regression.intensity_pipeline_findings`).

## Implementation Steps

1. **Replace the geometry in `src/segfacet/synth/clean_gt.py`.** Absorb
   `lordotic_spine.py`'s `centroids_mm` and `build` into
   `build_clean_spine`, generalised to its arguments.
   - Reuse `_validate_span`, `_affine_from_spacing`, the `CleanSpine`
     dataclass and the scan ramp unchanged.
   - Set `_GAP_MM = 8.0` and `_DEFAULT_CURVE_AMPLITUDE_MM = 0.0`, and add a
     private tilt mapping keyed by canonical level name (A1).
   - Keep the S slot assignment: the i-th ascending label goes at slot
     `n − 1 − i`, with pitch equal to body plus gap.
   - Walk A-P caudally with the mean-tilt tangent step.
   - Keep the lateral hump formula, `amplitude · sin(π · i / (n − 1))`, which
     is zero by default.
   - Size the grid and fill the rotated boxes per A3. The margin is at least
     one voxel per face, and `voxel_counts` is counted from the array.
   - Rewrite the module docstring's design bullets and `build_clean_spine`'s
     docstring. Drop the "solid rectangular block" and 15 mm gap claims.
     State the tilt table, the 8 mm gap, the integrated A-P path, the untilted
     non-lumbar levels, and the insight entry of 2026-09-22 the values come
     from.
   - Keep the phrase "ascending labels advance caudally" in both docstrings
     (`test_143` AC5). Keep the item 116 affine-as-source-of-truth paragraph
     (`test_116` AC4). Keep the transitional-vertebra guard.

   No dependency is added. NumPy is all the builder needs.
2. **Set `curve_amplitude_mm` to `0.0`** in `synth/corpus.py`'s and
   `synth/intensity.py`'s `_DEFAULT_BASE_PARAMS`, and in
   `eval/severity_ladder.py`'s `_BASE_PARAMS` (A2).
3. **Regenerate the two corpora first.** Every later artifact reads them.
   Run `python -m segfacet.synth.corpus` and `python -m segfacet.synth.intensity`.
   Run each twice into two temp destinations and diff the bytes before
   overwriting the committed copies. Then run
   `python -m segfacet.reference.artifact` the same way.
4. **Re-capture `tests/corpus/094_pre_migration_snapshot.json`** with a
   throwaway script that mirrors `test_094`'s own reader. For each
   `scan_fixture`/`seg_fixture` in both manifests, load it through
   `segfacet.io.load_volume` with its recorded `integer_labels`. Record
   `{path, integer_labels, shape, dtype, data_sha256, spacing, affine}`, with
   `sha256` taken over `np.ascontiguousarray(data).tobytes()`. Write it with
   `write_bytes(json.dumps(..., indent=2, sort_keys=True).encode() + b"\n")`.
   This is the item 143 method. Do not commit the script.
5. **Measure every case's firing.** Use
   `segfacet.traceability.build_matrix().conformance.cases`, or
   `failure_modes.measured_firing` per case. A6 predicts no change.
   - If a case's measured set moved, re-author its `expected_firing` in
     `src/segfacet/failure_modes.py` from the measurement, with a dated
     reason that states why it moved.
   - If the operator's own `Expectation.expected_rule_ids` would then fail
     `_corpus_case_conflicts`' subset relation, hand back. Operator files
     belong to items 174–177 and are not authorised here.
6. **Re-measure the quoted corpus values (A7), then update the prose.** Take
   `stray_contact_area_mm2` on the regenerated `split` case, and confirm every
   other label of every other case, in both corpora, reads 0.0. Update each
   quote with the fresh value, its distance above
   `DEFAULT_NEIGHBOUR_CONTACT_AREA_MM2` and the measurement date:
   - `failure_modes.py`: mode 3's `mechanism`.
   - `failure_modes.py`: the `split` case's `reason`.
   - `heuristics/fragmentation.py`: the module docstring's measured-value
     sentence.
   - `heuristics/fragmentation.py`: the `neighbour_contact` declaration's
     evidence string.

   These are prose only. No rule logic and no threshold changes. **Never
   edit a `MODE_SIGN_OFFS` note.** It is a dated signed record, even where
   it quotes 750 mm².
7. **Re-transcribe the severity-ladder constants (A8).** Run
   `score_harness(run_severity_harness())` once on the new default base.
   - Transcribe every `RECORDED_MARGINS` value from that run, rounded down to
     4 significant figures, with `math.inf` kept.
   - Transcribe every `KNOWN_CROSS_MODE_COUPLINGS.recorded_response`, rounded
     up to 4 significant figures.
   - Make the coupling **set** what the run measures (`test_154` AC8). Drop
     an entry that no longer couples, and add one that newly does.
   - Set `_MEASUREMENT_PROVENANCE.measured_on` to the run's date.
   - Re-word every `cause` string and comment whose number or mechanism the
     new base falsified: the 15 mm gap, and "~19.8 mm max `displacement_mm`
     on this base".

   Record the printed run in Decisions. Add no `split` entry (D4).
8. **Regenerate the derived documents after steps 5–7.** Use each module's
   `main` with the committed `--json`/`--md` paths, twice into temp first:
   - `segfacet.catalogue`
   - `segfacet.failure_modes`
   - `segfacet.traceability`
   - `segfacet.golden_evidence`
9. **Run the suite and reconcile only what moved**, under the fence in
   Authorised paths (`tests/*.py`). Work the "existing tests to reconcile"
   list in the Testing Strategy. Record each retired test (fence clause c) in
   Decisions by node id, with the box-geometry property it pinned.
10. **Run `python .aide/scripts/aide.py scope 173 --base aide/queue-023`** and
    confirm it exits 0.

## Authorised paths

**May change:**

- `src/segfacet/synth/clean_gt.py` — the lordotic geometry (step 1).
- `src/segfacet/synth/corpus.py` — `_DEFAULT_BASE_PARAMS` curve amplitude to 0.0 (step 2).
- `src/segfacet/synth/intensity.py` — `_DEFAULT_BASE_PARAMS` curve amplitude to 0.0 (step 2).
- `src/segfacet/eval/severity_ladder.py` — `_BASE_PARAMS` and the re-transcribed constants, provenance and cause text (steps 2 and 7).
- `src/segfacet/failure_modes.py` — the re-measured `split` quotes, plus an `expected_firing` only if a measured firing moved (steps 5 and 6).
- `src/segfacet/heuristics/fragmentation.py` — prose only: the re-measured contact-area quotes (step 6).
- `tests/corpus/fixtures/*.nii.gz` — the regenerated geometric corpus.
- `tests/corpus/manifest.json` — regenerated (the `base` curve amplitude and operator `detail` text move).
- `tests/corpus/intensity/fixtures/*.nii.gz` — the regenerated intensity corpus.
- `tests/corpus/intensity/manifest.json` — regenerated.
- `tests/corpus/094_pre_migration_snapshot.json` — re-captured fixture digests (step 4).
- `src/segfacet/reference/reference_default.json` — rebuilt from `build_clean_spine`.
- `docs/aide/feature_catalogue.generated.json` — observed-range column recomputed over the new corpus.
- `docs/aide/feature_catalogue.generated.md` — rendering of the same.
- `docs/aide/failure_modes.generated.json` — carries the re-measured `split` quotes.
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — carries the re-worded declaration evidence and the measured firing.
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `docs/aide/golden_evidence.generated.json` — per-case leaf-path counts over the new corpus.
- `tests/test_173_lordotic_geometric_base.py` — **new**: this item's test module.
- `tests/*.py` — reconciliation only, under the fence stated below this list.

**The reconciliation fence for `tests/*.py`.** Three kinds of change are
allowed:

- **(a) A moved literal.** A literal expected value that the new base moved
  may be updated to the fresh measurement. The assertion keeps its shape and
  its tolerance.
- **(b) A re-derived premise.** A constructed input whose stated premise was
  the box geometry may be re-derived for the lordotic base, keeping what the
  test asserts. Examples are the voxelisation "floor" in the stage-6
  acceptance module's bracketing cohort, and a closed-form box product.
- **(c) A retirement.** A test may be retired only when its sole subject is a
  property of the axis-aligned boxes themselves that has no lordotic
  counterpart. The known instance is item 143's mirror-plus-relabel identity,
  which the asymmetric tilts break by design. Each retirement is listed in
  Decisions.

Nothing may be skipped, `xfail`-marked or loosened in tolerance.

**Asserts against:**

None. The criteria read only the two regenerated clean-seg fixtures and the
two manifests, and all of them are under **May change**.

Every regenerated committed path is already pinned in `.gitattributes`, and
this item adds no entry. The two corpus manifests, the 094 snapshot, the
synthetic reference and the four `docs/aide/*.generated.*` families are
`text eol=lf`. Both fixture directories' `*.nii.gz` are `binary`.

Some files must stay byte-unchanged, so they are left off **May change** and
`aide scope` refuses them:

- `.gitattributes`
- `reference_verse_v1.json`
- the report-format contract
- `119_pre_119_digests.json`, which holds structure, not corpus values
  (item 143, A5)
- every operator module
- everything under the prototype directory

This section was amended on 2026-09-23, after the builder's hand-back. The
full record is the `## Correction — 2026-09-23` section at the end of this
spec. It adds one path
below and fence clause (d), which applies only to the tests that correction
names. Nothing else in this section changes.

**May change:**

- `docs/spinal-curve-model.md` — item 118's ten non-VerSe measurements, re-measured on the lordotic base (Correction, part 2).

## Testing Strategy

The new module is `tests/test_173_lordotic_geometric_base.py`, with one test
per AC (AC1–AC7).

- Resolve fixture paths from the manifests (`load_manifest()` plus
  `CORPUS_DIR`, and `load_intensity_manifest()` plus `INTENSITY_CORPUS_DIR`).
  Never use a hardcoded fixture path.
- Load the fixtures with `nib.load`. Take voxel centres in mm with
  `nibabel.affines.apply_affine(affine, np.argwhere(mask))`.
- AC1's tilt measurement is a helper in the test module, not a production
  function. Its search is a plain loop over 901 angles.
- The tilt table (−8, 0, 8, 18, 35) is a literal in the test. It is the
  maintainer's decision, not live state. Reading it from `clean_gt` would let
  a wrong constant pass.
- Nothing in this module regenerates a corpus or an artifact. Determinism and
  fresh-vs-committed equality are already guarded (see below), and the
  module stays fast.

The queue's three *Testable* claims are already enforced by existing tests,
which run on the regenerated corpus without edits:

- **Clean control fires nothing, one component per label.**
  `tests/test_036_clean_gt.py` AC2 and AC7 check `build_clean_spine()`, and
  AC5 above ties that build to the committed fixture.
  `tests/test_163_specificity_ratchet.py` compares
  the committed `clean_control` against the empty set.
- **Both corpora regenerate byte-identically.** `tests/test_116_ras_native_corpus.py`
  AC10/AC11, `tests/test_143_s_axis_correction.py` AC11–AC13 and
  `tests/test_040_synthetic_corpus.py` check this.
- **The specificity ratchet is green.** `tests/test_163_specificity_ratchet.py` is the ratchet.
  `tests/test_154_ladder_remeasurement.py` AC4–AC10 keep the ladder
  constants honest (A8).

Adversarial cases, each written once:

- **`tilt-oracle-responds`**: take the committed fixture's label-21 mask,
  whose tilt AC1 measures as the live value t₂₁. Rotate it in the (y, z)
  plane by +20° with `scipy.ndimage.rotate(..., axes=(1, 2), order=0,
  reshape=True)`. AC1's helper must then return a value whose absolute
  difference from t₂₁ is 20° ± 1°. This leaves scipy's rotation-sign
  convention out of the claim. This guards a vacuous oracle that
  returns the expected table whatever the mask holds. The "wrong" angle is
  built from the live measurement, per item 171.
- **`coarse-spacing-margin`**: `build_clean_spine(levels=("L1", "L2", "L3"),
  spacing=(20.0, 20.0, 20.0))`. Every label's `geometry` record from
  `extract_feature_record` has every `touches_*` flag false. This guards a
  margin computed in mm only, which collapses to zero voxels at coarse
  spacing and fires `border` (A3). `test_092`'s outlier case builds at
  exactly this spacing.
- **`partial-lumbar-span-keeps-level-tilts`**:
  `build_clean_spine(levels=("L3", "L4", "L5"))`. AC1's helper measures 8°,
  18° and 35°, each ± 1°. This guards a tilt looked up by position in the
  span rather than by level name, which would give −8°, 0° and 8°.
- **`non-lumbar-span-is-untilted`**: `build_clean_spine(levels=("T5", "T6",
  "T7", "T8", "T9", "T10"))`. Every label's measured tilt is 0° ± 1°, and
  consecutive S-I centroid steps are 33.0 ± 1.0 mm. This guards a lookup that
  falls back to the lumbar table for a level it does not name.
- **`single-steepest-body-fits`**: `build_clean_spine(levels=("L5",))`. The
  build yields one component and no `touches_*` flag set. This guards the
  worst-case half-extent computation at the largest tilt with no neighbour
  to widen the grid.

**Existing tests to reconcile.** This is the stale-assumption sweep. Each
fix goes under the fence in Authorised paths. The first four are certain.
The rest are candidates that a full run confirms or clears.

- `tests/test_143_s_axis_correction.py`:
  - `_EXPECTED_DEFAULT_SHAPE (66, 55, 215)` and
    `_EXPECTED_DEFAULT_VOXEL_COUNTS` (the 18 750 box product) move.
  - `test_ac3_mirror_plus_relabel_reproduces_the_array_exactly` no longer
    holds under asymmetric tilts (fence clause c).
  - `_PRE_ITEM_NET_ADVANCE_S_MM_MAGNITUDE`, which is 160.0 at a 40 mm pitch,
    moves.
  - The AC7/AC8 tangent-angle tables move.
- `tests/test_131_tangent_direction_normalisation.py`: the `_PRE_ITEM_*`
  corpus tables move (tangent angles, net advance, inter-tangent angles,
  other curvature fields).
- `tests/test_167_mode_3_detector.py`: `test_ac1_feature_measures_the_split`'s
  literal `750.0` becomes the fresh value (A7). Its live recomputation half
  stays.
- `tests/test_154_ladder_remeasurement.py` and `tests/test_100_severity_ladder.py`:
  the ladder constants, their provenance date and base, and the coupling set
  (A8, step 7).
- `tests/test_049_acceptance_stage6.py`: the bracketing cohort's premise is
  the box voxelisation floor (18 750 mm³ / 25 mm), which is fence clause b.
  Candidates alongside it are `tests/test_049_reference_integration.py`,
  `tests/test_045_reference_artifact.py`, `tests/test_046_reference_delta.py`,
  `tests/test_063_reference_intensity.py` and
  `tests/test_090_reference_derived_defaults.py`. These read
  `reference_default.json` or build a reference from `build_clean_spine`.
- `tests/test_098_stray_components.py`, `tests/test_099_per_mode_metrics.py`
  and `tests/test_102_stage18_validation.py`: reason strings quoting
  `component_sizes=[18750, 27]`.
- `tests/test_094_tptbox_image_layer.py`: the re-captured snapshot digests
  (step 4).
- `tests/test_036_clean_gt.py`, `tests/test_037_component_shape_perturbations.py`,
  `tests/test_038_coverage_border_overlap_perturbations.py`,
  `tests/test_039_identity_ordering_alignment_perturbations.py`,
  `tests/test_116_ras_native_corpus.py` and `tests/test_166_split_operator.py`:
  operator and builder tests over the default base. Watch for extents and
  slab indices quoted as literals.
- `tests/test_040_synthetic_corpus.py`, `tests/test_041_regression_suite.py`,
  `tests/test_042_golden_determinism.py`, `tests/test_058_intensity_fixtures.py`
  and `tests/test_065_intensity_pipeline.py`: corpus round-trip and
  inventory.
- `tests/test_103_feature_catalogue.py`, `tests/test_104_feature_catalogue_drift.py`,
  `tests/test_124_observed_range.py`, `tests/test_105_golden_decision_table.py`,
  `tests/test_134_decision_table_evidence_companion.py`,
  `tests/test_138_traceability_matrix.py`,
  `tests/test_144_failure_mode_specification.py` and
  `tests/test_149_conformance_report.py`: the regenerated companions. These
  use item 170's session fixtures where they regenerate.
- `tests/test_119_curve_formulation.py`, `tests/test_120_leave_one_out_offset.py`,
  `tests/test_122_signed_curvature.py`, `tests/test_123_recalibrate_and_regenerate.py`,
  `tests/test_129_coincident_centroids_and_held_out_floor.py`,
  `tests/test_130_one_closest_point_search.py` and
  `tests/test_132_monotonicity_against_traversal_order.py`: curve-family
  measurements over the corpus. `test_132` carries `_PRE_ITEM_U_VALUES`.
- `tests/test_115_stage26_validation.py`, `tests/test_125_stage28_validation.py`,
  `tests/test_135_stage29_validation.py`, `tests/test_151_stage30_validation.py`
  and `tests/test_169_stage32_validation.py`: stage-validation modules that replay corpus
  measurements.
- `tests/test_aide_status_report.py`: check whether its `18750.0` range comes
  from a hand-built fixture (untouched) or from the committed catalogue (it
  moves).

## Validation

1. `python -m segfacet.synth.corpus --out <tmp>` and the intensity
   equivalent. Diff `<tmp>` against `tests/corpus/` and confirm there is no
   difference.
2. `.venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/clean_control_seg.nii.gz --no-reference --out <tmp>`.
   `--no-reference` is required (see the CLAUDE.md gotcha). Expect `pass` with
   zero findings.
3. Print the regenerated `split` case's `stray_contact_area_mm2` for label 23.
   Confirm that the value quoted in `docs/aide/failure_modes.generated.md`
   (mode 3's mechanism and the `split` row) and in
   `docs/aide/traceability_matrix.generated.md` (the `fragmentation` row) is
   that value.
4. `python .aide/scripts/aide.py scope 173 --base aide/queue-023` exits 0.
5. Run `.venv/bin/python -m pytest --collect-only -q` on this branch and on
   `aide/queue-023`. The branch's collected test-id set must be the base's
   set plus this item's new tests, minus exactly the retirements listed in
   Decisions.

No `[validation]` profile is needed, so there is no ❓ Unverified downgrade
path.

## Dependencies

Items 170, 171 and 172 (all merged into `aide/queue-023`). They are the D0
protective fixes that queue-023 orders ahead of this regeneration: the session
regeneration fixtures, live-derived negative controls, and validated
`UNUSED_OPERATOR_REASONS`.

**Downstream:** items 174, 175, 176 and 177 re-author their operators on this
base. Item 178 renders the regenerated corpus and deletes the prototype
directory. Item 179 needs only this item.

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** the `split` operator's `donated_fraction` comment in
  `src/segfacet/synth/component_shape.py` says 0.4 "leaves the donor's
  extent_z at exactly the lumbar min_extent_z_mm of 15.0 mm". That is false
  on the tilted base, where the donor keeps 17 of 28 S-I voxels. Item 174
  re-authors `split` and its default (a 20 % cap of L4), so this item leaves
  operator files alone (A9).
- **Left open:** tilts for non-lumbar levels. The maintainer's table is
  lumbar-only, so cervical and thoracic spans stay untilted (A1). A
  thoracic kyphosis base is a question for a later corpus, not this one.
- **Left open:** the severity ladder's coverage of `split` and the D2
  operators. This item re-transcribes only the existing ladders on the new
  base (A8). Roadmap Stage 33 D4 re-measures after items 174–177.
- **Left open (2026-09-23):** `force_overlap` on the full lordotic L1–L5
  span. An unspecified-target draw of (22, 23) or (23, 24) records an overlap
  `Expectation` that the operator does not produce (0 voxels).
  `test_038`'s `test_adv_different_seeds_unspecified_target_stay_self_consistent[force_overlap]`
  passes only because seeds 1 and 42 draw (21, 22) and (20, 21). The
  maintainer declined to fix the operator (Correction, part 1). Removing it is
  the follow-up captured in `docs/aide/insights.md` (item 173, 2026-09-23).
- **Left open (2026-09-23):** the sign of `principal_axis`.
  `features/orientation.py::_pca_principal_axis` returns the `eigh`
  eigenvector with no sign convention. On the lordotic base,
  `crop_at_border` label 22 reads `[-1.0, …]` where every other entry reads
  `[1.0, …]`, so a serialised report's `principal_axis` sign can flip with
  the geometry. The feature is an axis, and item 121 demoted it, so this item
  compares it without sign (Correction, part 3) and does not change the
  feature.
- **Reconciliation record (2026-09-23, builder, second pass after the
  Correction).** Every value below was measured fresh on this branch. Box-base
  values not quoted here are in the files as of commit `d054c98`.
  - **Curve-model re-measurement (Correction part 2).** Two runs of
    `scripts/compare_curve_candidates.py` with no VerSe cohort gave identical
    `candidates` blocks. Fresh values: `interpolating_cubic` clean
    pass-through 1.1450798611788938e-05; `smoothing_spline` 0.43458129896917025;
    `lsq_bspline_fixed_knots` 0.43458129896917114; `polynomial_per_plane`
    0.4577550398566493; in-sample separation `interpolating_cubic`
    -1.953287316705293e-05, `smoothing_spline` 0.10386267167625829,
    `lsq_bspline_fixed_knots` -0.31287547231229595, `polynomial_per_plane`
    1.9328463500464323; leave-one-out `smoothing_spline` 4.920549648197529,
    `interpolating_cubic` 4.992062592706033; `compared_samples` 100. Every
    value is within 1e-6 mm of the Correction's table.
    `docs/spinal-curve-model.md` was updated per the Correction's procedure.
  - **Renames (Correction).** `test_119` AC8 is now
    `test_ac8_clean_gt_sweep_exceeds_0_4mm_but_stays_under_0_44mm` (bracket
    (0.4, 0.44], measured 0.434581). `test_121` AC5 is now
    `test_ac5_clean_control_sagittal_tilts_vary_across_levels`.
  - **Clause (d), as prescribed.** `test_121` AC5's principal-axis half and
    AC10 now compare the axis to L-R without sign within 1e-12. The doubling-back
    adversarial moved to the sagittal plane. `test_123`'s four-level adversarial
    is now `abs=1e-6`. The fresh residue is 7.7e-9 mm at L2 and 1.27e-8 mm at
    L3. That is below the 1e-7 hand-back bound, and 1e-6 is about 79 times the
    larger value (the Correction's "about 130 times" used the L2 value only).
  - **Clause (b), per the Correction.** `test_038` AC27 `[force_overlap]` runs
    on `build_clean_spine(levels=("L1", "L2", "L3"))`. Seed 3 draws (21, 22)
    there.
  - **Retired (clause c).**
    `tests/test_143_s_axis_correction.py::test_ac3_mirror_plus_relabel_reproduces_the_array_exactly`.
    It pinned the box spine's S-mirror symmetry, which the asymmetric tilts
    break.
  - **Re-derived (clause b).**
    - `test_049` `_BRACKETING_COHORT_PARAMS`: rows 1–3 now use amplitude 0.0
      (was 6/3/9), and the spacing_z 2.0 row now uses amplitude 0.0 (was 8.0).
      Its in-sample offsets sit below clean_control's, so p1 still brackets.
    - `test_039` AC8: a swap now carries each body's own count
      (label 21 gets clean 22's count and vice versa). Before, the five box
      bodies had equal counts.
    - `test_112` AC6: the trim cut moved 50→40, because GT foreground now ends
      at axis-0 index 45.
    - `test_124` AC6: the constant-synthetic path moved `dy_mm`→`dx_mm`,
      because the curve is now sagittal. The test name still says `dy_mm`.
    - `test_143` AC3 shape: `(66, 55, 215)`→`(61, 86, 193)`. Counts moved from
      18 750 each to 19 437 / 19 375 / 19 437 / 19 344 / 19 344, taken from
      the array.
  - **Moved literals (clause a), old→new.**
    - `test_098`/`test_102` reason snapshots:
      - fragment `[9000, 9000]`/0.5 → `[9796, 8835]`/0.52579.
      - inject_islands `[18750, 27]`/0.9985620706183096 →
        `[19437, 27]`/0.9986128236744759.
      - displace offset 18.7 → 17.6 mm.
      - crop_at_border offset 17.5 → 18.0 mm.
    - `test_099`:
      - fragment index 0.5 → 0.5257903494176372 (AC7, AC23).
      - relabel_swap 0.4 → 0.4003837543971858.
      - unrestricted 0.2 → 0.19955228653661655.
      - overlap 1950 → 1085.
      - AC15 matrix cells: displace 0.1456 → 0.14814776607487337;
        inject_islands 0.000288 → 0.000278531417312275; crop_at_border 0.12
        → 0.1429485129517109; force_overlap 0.1232 → 0.07515190278221938 and
        0.0208 → 0.011192836584585865; fragment 0.5 → 0.5257903494176372;
        inject_islands 0.9985620706183096 → 0.9986128236744759;
        relabel_swap 0.4 → 0.4003837543971858; overlap 1950 → 1085.
      - Diagonal dominance still holds.
    - `test_100` AC19: 1950 → 1085.
    - `test_102`:
      - AC9 value_a 0.079264 → 0.08327062954602459.
      - AC9 value_b 0.0784 → 0.08242412841735641.
      - AC9 delta and normalised_delta -0.000864 → -0.0008465011286681728, and
        the swapped run's value is the same with the sign flipped.
      - AC16 margins: inject_islands 112.037 → 118.4907; crop_at_border
        0.3585 → 0.3253; force_overlap 1.0386 → 1.7418.
    - `test_120` AC23: 17.507 → 18.0256.
    - `test_123` AC45 interior ceiling: 2.510990 → 5.624555 (relabel_swap,
      now label 23; still below the 13.0 mm threshold).
    - `test_129` AC28 remove_level offsets: 8.999e-05 / 7.67e-08 / 7.67e-08 /
      8.978e-05 → 7.595758137565312e-05 / 8.717388010901323e-07 /
      2.8611762188838856e-07 / 7.745963365341523e-05.
    - `test_131`:
      - `_PRE_ITEM_TANGENT_ANGLES_DEG`, `_PRE_ITEM_NET_ADVANCE_S_MM`
        (-160/-142 → -131.97402926021348/-121.97402926021348),
        `_PRE_ITEM_INTER_TANGENT_ANGLES_DEG` and
        `_PRE_ITEM_OTHER_CURVATURE_FIELDS` were re-measured whole. Every
        case's `curvature_plane` moved coronal→sagittal, except
        crop_at_border, which was already sagittal.
      - AC4 relabel_swap: `[3.2953, 177.6490, 175.2184, 1.4658, 22.0118]` →
        `[2.4934, 174.7774, 176.1799, 13.5824, 68.7966]`. The fold still
        differs by more than 1°.
      - AC17 tangent range 0.0–8.1652 → 0.254105–33.9343, and inter range
        3.83716–7.59031 → 7.32060–19.74878.
      - `test_143` imports these tables. Its AC6 magnitudes moved
        160/142 → 131.97402926021348/121.97402926021348.
    - `test_132` `_PRE_ITEM_U_VALUES`: re-measured whole.
    - `test_167` AC1: 750.0 → 775.0.
  - **Names that still record the box-base value.** `test_099`'s
    `..._is_half`, `..._is_04`, `..._would_give_02` and `..._is_1950`,
    `test_100`'s `..._1950`, `test_123`'s `..._is_2_510990` and `test_124`'s
    `..._dy_mm` keep their names. Validation step 5 authorises only the
    Correction's two renames. Each literal carries a dated comment giving the
    fresh value.
  - **No firing moved.** No corpus `expected_firing` changed, and no operator
    file was touched. Two out-of-scope findings went to `insights.md`
    (item 173, 2026-09-23): the stale margins in `heuristics/mislabel.py`'s
    docstring, and the platform-fragile coronal row of relabel_swap.
- **Builder record (2026-09-23, "Correction — 2026-09-23 (review findings)").**
  - **Part 1, `src/segfacet/synth/clean_gt.py`.** The fill loop now writes
    only each body's rotated box; the in-loop fallback was removed. After
    every box is written and before the trim, a second pass walks
    `sorted(labels)` and gives each label with zero voxels the still-
    unclaimed (value-0) voxel nearest its centroid in mm (squared-distance
    over the full grid via `np.argmin`, so ties resolve to the lowest
    C-order flat index, `np.argmin`'s own tie-break). Verified: the default
    build's shape and per-label counts are unchanged, `(61, 86, 193)` /
    19437, 19375, 19437, 19344, 19344 — no committed fixture regenerates
    differently. Confirmed by regenerating into temp dirs and byte-diffing
    against committed: both corpus manifests and fixture trees,
    `reference_default.json`, and all four `docs/aide/*.generated.*`
    families (`feature_catalogue`, `failure_modes`, `traceability_matrix`,
    `golden_evidence`) — every diff empty, so nothing was overwritten. The
    three L1–L3 coarse-spacing sweeps ((20,20,60), (20,20,66), (20,20,100))
    and the L1–L5 (20,20,60) sweep from the Correction's table now give
    every requested label at least one voxel.
  - **Part 2, `tests/test_131_tangent_direction_normalisation.py::test_ac21_other_curvature_fields_unmoved`.**
    Joined fence clause (d) as prescribed: for `relabel_swap` only,
    `coronal_tangent_angles_deg` is compared entry-by-entry as a circle
    distance (`abs((actual - expected + 180) % 360 - 180) <= 1e-6`);
    `coronal_curvature_deg`, `total_curvature_deg` and `curvature_plane` are
    not compared for that case, with a comment naming this Correction
    section and the branch-cut reason. Every other case (and every other
    field of `relabel_swap`) keeps the prior direct-equality comparison. The
    `_PRE_ITEM_OTHER_CURVATURE_FIELDS` table literals are unchanged.
  - **Part 3, `tests/test_119_curve_formulation.py`.** The AC8 trailing
    comment now says "Implied by the 0.44 ceiling above". The module
    docstring's AC7/AC8 bullet now says the sweep "exceeds 0.4 mm, bounded
    at 0.44 mm on the lordotic base (2026-09-23) and inside stage 28's 1.0 mm
    acceptance bound". No assertion changed.

## Correction — 2026-09-23

**Appended, not a rewrite.** Everything above stands as authored on
2026-09-23. The builder stopped part-way and handed back with commit `73bf20f`
("partial, handed back"). By then the base, both corpora, the reference and
the derived artifacts were regenerated, and the ladder constants were
re-transcribed. The suite was red in three places the spec above did not
authorise. This section records the maintainer's decisions of 2026-09-23 on
those three and rules on each affected test.

**No acceptance criterion, assumption or implementation step above changes.**
Three things are added:

- one **May change** path, `docs/spinal-curve-model.md`;
- fence clause (d), below;
- the per-test prescriptions below.

**Fence clause (d): a re-decided comparison.** A tolerance or a comparison
shape may change only for a test this correction names under clause (d), and
only as prescribed here, with the reason recorded here. It must be the right
bound for what the test measures. It must never be a bound chosen so the test
passes. No other test may use clause (d). "Nothing may be skipped,
`xfail`-marked or loosened in tolerance" still holds everywhere else.

**Validation step 5, amended.** The branch's collected test-id set must equal
the base's set, plus this item's new tests, minus the retirements listed in
Decisions, with **two renames** each counted as the old id out and the new id
in:

- `tests/test_119_curve_formulation.py::test_ac8_clean_gt_sweep_exceeds_half_mm_but_stays_under_0_56mm`
  becomes `test_ac8_clean_gt_sweep_exceeds_0_4mm_but_stays_under_0_44mm`.
- `tests/test_121_tangent_orientation.py::test_ac5_clean_control_coronal_tilts_vary_across_levels`
  becomes `test_ac5_clean_control_sagittal_tilts_vary_across_levels`.

A grep of `tests/` and `src/` on 2026-09-23 found no reference to either old
identifier outside its own definition, so no third file needs an edit.

### 1. `force_overlap` stops overlapping on the lower lumbar pairs

**Finding.** The builder found this, and the spec-author re-measured it on
this branch on 2026-09-23. `ForceOverlapPerturbation` shifts the target along
S by the target's bounding-box gap to the neighbour plus `overlap_depth`, and
that premise is the axis-aligned box. On the lordotic L1–L5 default base, each
explicit pair was passed through the reconstructed two-channel stack to
`detect_overlaps`:

| Pair | Overlap voxels |
|---|---|
| 20→21 | 1 085 |
| 21→22 | 930 |
| 22→23 | 0 |
| 23→24 | 0 |

`_choose_adjacent_pair` draws (23, 24) at seed 3, so
`tests/test_038_coverage_border_overlap_perturbations.py::test_ac27_unspecified_target_is_seed_deterministic_and_self_consistent[force_overlap]`
fails. The committed corpus case is the explicit 20→21 pair, and it still
fires.

**Maintainer decision.** "We currently don't have full multi-channel
segmentation support, so we don't really need a fixture for overlap."

- The operator is not fixed in this item, and no operator file is authorised.
- The committed `force_overlap` corpus case (20→21) stays.
- The position and the candidate removal follow-up are captured as the
  `knowledge` entry on `ForceOverlapPerturbation` in `docs/aide/insights.md`
  (item 173, 2026-09-23).

**Ruling: re-derive (clause b), not retire.** The test's subject is the
unspecified-target path. Two `apply(seed=3)` calls must give identical output,
and the designated rule must fire for the pair recorded in the result's own
`expectation`. The test's premise was that the operator can overlap every
adjacent pair of the default base with an S shift, and that was a property
of the box geometry.

The re-derived premise is an input span on which the operator overlaps every
pair it can draw. `build_clean_spine(levels=("L1", "L2", "L3"))` is such a
span. Both of its drawable pairs overlap, at 20→21 (1 302 voxels) and 21→22
(837 voxels), measured 2026-09-23. Seed 3 draws (21, 22) there, so the
seed-driven choice is still exercised.

Retirement was rejected. The L1–L3 input keeps both halves of what the test
asserts, and retiring it would drop the only unspecified-target determinism
check on an operator that still ships. Prescription:

- The change applies to the `force_overlap` parametrisation only. Its
  operator input and the `clean_data` passed to `_designated_rule_fires` both
  come from `build_clean_spine(levels=("L1", "L2", "L3"))`. The other three
  parametrisations keep `_clean()`. Use a small helper in the test module
  that maps an operator name to its input. Add no new fixture file.
- The assertions do not change: same-seed `np.array_equal`, then
  `_designated_rule_fires`.
- Add one dated sentence to the docstring. It names the L1–L3 span and gives
  the reason: on the lordotic base the operator overlaps 20→21 and 21→22 only,
  and the maintainer declined to fix it on 2026-09-23.
- The node id does not change.

`test_adv_different_seeds_unspecified_target_stay_self_consistent[force_overlap]`
is not touched, because it passes and did not move. See the Left open entry
dated 2026-09-23.

### 2. Item 118's curve-formulation measurements

**Finding.** `scripts/compare_curve_candidates.py` builds its synthetic sweeps
through `build_clean_spine`. As a result, the ten non-VerSe rows of the
`## Measurements` table in `docs/spinal-curve-model.md` moved. Four tests
fail:

- `tests/test_118_curve_formulation_decision.py::test_ac6_non_verse_measurements_reproduce_from_fresh_run`
- `tests/test_119_curve_formulation.py::test_ac25_test_118_ac6_reproduction_stays_green`
- `tests/test_130_one_closest_point_search.py::test_ac25_test_118_non_verse_reproduction_stays_green`
- `tests/test_119_curve_formulation.py::test_ac8_clean_gt_sweep_exceeds_half_mm_but_stays_under_0_56mm`

The first three all read the same table through `test_118`'s helpers.

**Maintainer decision.** "Re-measure, unless it's a lot of rework."

**Assessment: the formulation choice holds, so the re-measurement is
authorised as fence work.** The spec-author measured these values on this
branch on 2026-09-23, with
`.venv/bin/python scripts/compare_curve_candidates.py --out <tmp>` and no
VerSe cohort:

| Row key, under `candidates.` | Documented (box base) | Measured (lordotic base) |
|---|---|---|
| `interpolating_cubic.clean_pass_through.in_sample.max_mm` | 0.0000138 | 0.0000115 |
| `smoothing_spline.clean_pass_through.in_sample.max_mm` | 0.552139 | 0.434581 |
| `lsq_bspline_fixed_knots.clean_pass_through.in_sample.max_mm` | 0.552139 | 0.434581 |
| `polynomial_per_plane.clean_pass_through.in_sample.max_mm` | 0.548571 | 0.457755 |
| `interpolating_cubic.separation.smallest_margin_mm.in_sample` | -0.0000232 | -0.0000195 |
| `smoothing_spline.separation.smallest_margin_mm.in_sample` | 0.140882 | 0.103863 |
| `lsq_bspline_fixed_knots.separation.smallest_margin_mm.in_sample` | -0.244683 | -0.312875 |
| `polynomial_per_plane.separation.smallest_margin_mm.in_sample` | 1.873170 | 1.932846 |
| `smoothing_spline.separation.smallest_margin_mm.leave_one_out` | 4.999144 | 4.920550 |
| `interpolating_cubic.separation.smallest_margin_mm.leave_one_out` | 4.999936 | 4.992063 |
| `smoothing_spline.determinism.compared_samples` | 100 | 100 |

Checked against the document's own decision logic, subsection by subsection:

- **Family.** `smoothing_spline` was chosen for real-anatomy fidelity, on the
  VerSe19 rows (2.099807 mm against 17.675639 and 27.859506). Those rows are
  measured on real ground truth, never read `build_clean_spine`, and do not
  move.
- **In-sample separation.** The ordering is unchanged:
  `polynomial_per_plane` > `smoothing_spline` > `interpolating_cubic` >
  `lsq_bspline_fixed_knots`. Every sign is unchanged, so
  `lsq_bspline_fixed_knots` still re-absorbs the point and `smoothing_spline`
  still separates.
- **Degrees of freedom.** `smoothing_spline` and `lsq_bspline_fixed_knots`
  are still numerically identical on the clean sweep (0.434581 both). The
  worst case is at the same grid point as before: 5 levels, spacing
  (0.8, 0.8, 1.0), label 22.
- **Breaking circularity.** The leave-one-out margins, 4.920550 and 4.992063
  against a 5 mm displacement, are still essentially the displacement for
  both families.
- **Deformity envelope.** The proposal is already superseded by item 123's
  13.0 mm. Its synthetic evidence value moves from 4.999144 to 4.920550, and
  the argument does not change.
- **Stage 28's 1.0 mm pass-through bound** still holds at 0.434581.
- **The only ordering that flips.** `polynomial_per_plane`'s clean
  pass-through (0.457755) is now above `smoothing_spline`'s (0.434581). On the
  box base it was below (0.548571 against 0.552139). The document uses this
  pair only to say that the two fits differ, and no choice or threshold reads
  their order.

**Procedure for `docs/spinal-curve-model.md` (clause a, applied to a
document).**

1. Run `.venv/bin/python scripts/compare_curve_candidates.py --out <tmp1>`,
   then the same with `--out <tmp2>`, with no `--verse-cohort`. Confirm that
   the two `candidates` blocks are identical.
2. Replace the `Value` cell of each of the ten non-VerSe mm rows with the
   fresh value. Use 6 decimal places, except for the two
   `interpolating_cubic` rows below 1e-3 in magnitude, which keep 3
   significant figures as they do now. If any fresh value differs from the
   table above by more than 0.001 mm, the document's own tolerance, stop and
   hand back.
3. Leave these untouched:
   - the five VerSe rows and the `compared_samples` row;
   - every `Key`, `Units` and `Source` cell;
   - `## Reproducing these numbers`;
   - the 2026-08-30 correction blockquote;
   - `## Revisions to apply when item 119 implements this`.
4. In `## Decision`, update every quote of a moved value to the same fresh
   value:
   - **Family**, Consequence: "~0.55 mm" becomes "~0.43 mm".
   - **Family**, Evidence: 1.873170, -0.244683 and 0.140882.
   - **Degrees of freedom**, Evidence: both occurrences of 0.552139.
   - **Parameterisation**, Evidence: 0.552139 and 0.548571.
   - **Breaking circularity**, Evidence: 4.999144, 4.999936, -0.0000232 and
     0.140882.
   - **Deformity envelope**, Evidence: both occurrences of 4.999144.

   No wording changes beyond the numbers, because every sentence stays true
   (checked above).
5. Directly under the table, append one dated blockquote headed
   `**Re-measured (2026-09-23, item 173):**`. It states:
   - that the ten rows were re-measured after `build_clean_spine` became the
     lordotic base;
   - each row's previous value;
   - that the VerSe rows are real anatomy and did not move;
   - in two sentences, why the choice is unaffected.

   Two constraints apply. No line of the blockquote may contain "gate"
   together with "approved", "resolved" or "signed off" (`test_118` AC3). No
   line of it may start with `|` (`test_118`'s table parser).
6. Do not edit `test_118`, `test_119` AC25 or `test_130` AC25. They read the
   document, and they turn green once step 2 is done.
7. Do not edit the dated records elsewhere that quote 0.552139: the Stage 28
   attestation in `docs/aide/progress.md` and the Stage 28 note in
   `docs/aide/roadmap.md`. They are dated measurements of the box base, and
   Stage 28's criterion, a 1.0 mm bound, still holds.

**`test_119` AC8 (clauses a and b, and a rename).**

- Rename the test to
  `test_ac8_clean_gt_sweep_exceeds_0_4mm_but_stays_under_0_44mm`.
- Assert `overall_max > 0.4` and `overall_max <= 0.44`.
- Keep the `overall_max < 1.0` assertion and its Stage 28 comment unchanged.

The bracket follows the original's own rule: the floor is the measured
maximum rounded down to 0.1 mm, and the ceiling is the measured maximum
rounded up to 0.01 mm. That rule gave 0.5 and 0.56 from 0.552139, and gives
0.4 and 0.44 from 0.434581. The spec-author measured 0.434581 through the
test's own loop, at 5 levels, spacing (0.8, 0.8, 1.0) and label 22.

Re-word the docstring and failure messages:

- The recorded value is 0.434581 mm (2026-09-23, lordotic base), and
  0.552139 mm on the box base.
- The floor no longer coincides with item 017's 0.5 mm unit tolerance,
  because the lordotic sweep does not reach it.
- What the floor pins is unchanged in kind. The sweep's maximum stays four
  orders of magnitude above the interpolating fit's on the same sweep (about
  1.1e-5 mm), so a drift back toward interpolation still fails it.

If the fresh measurement falls outside (0.4, 0.44], hand back.

**`test_119` AC9's docstring.** Its parenthetical quote of 4.999144 becomes
4.920550 (2026-09-23), with 4.999144 kept as the box-base value. The 4.5 mm
assertion does not move.

### 3. Four failures outside the fence's three clauses

The spec-author re-measured each value below on this branch on 2026-09-23,
except the one marked builder-reported.

**(i)
`tests/test_121_tangent_orientation.py::test_ac5_clean_control_coronal_tilts_vary_across_levels`:
re-derive (clause b), rename, and clause (d) for its principal-axis half.**

The test is evidence that item 121's tangent estimate varies across levels on
a curved spine, against a `principal_axis` that does not vary. `clean_control`
curved in the coronal plane only because of the 6 mm lateral hump. The
lordotic base has none (AC4), so `coronal_deg` is 0.0 at every level within
4e-14. The curve now lies in the sagittal plane, where the measured
`sagittal_deg` values are:

| Label | `sagittal_deg` |
|---|---|
| 20 | −7.575480 |
| 21 | −0.241862 |
| 22 | 8.322515 |
| 23 | 19.245122 |
| 24 | 33.589953 |

The spread is 41.165433°. Prescription:

- Rename the test to `test_ac5_clean_control_sagittal_tilts_vary_across_levels`.
- Assert `sagittal_deg` against `[-7.5755, -0.2419, 8.3225, 19.2451, 33.5900]`
  within `1e-3`, the unchanged tolerance.
- Assert the spread against `41.1654` within `1e-3`.
- Take all of these literals from the builder's fresh run.

The principal-axis half, `len(set(principal_axes)) == 1`, also fails on the
new base. The five axes differ at the 1e-16 level: labels 20, 22 and 23 carry
residues up to 3.2e-16 off-axis, while labels 21 and 24 read exactly
`(1.0, 0.0, 0.0)`. Under clause (d), assert instead that every level's axis
equals the L-R axis without sign: `abs(axis[0])` is within `1e-12` of 1.0,
and `abs(axis[1])` and `abs(axis[2])` are each at most `1e-12`. The reason is
given under (ii).

**(ii)
`tests/test_121_tangent_orientation.py::test_ac10_principal_axis_exactly_left_right_off_the_named_exceptions`:
re-decide the comparison (clause d), and keep the name.**
`tests/test_126_golden_retirement.py` line 510 names this test by its
identifier.

The test is evidence that PCA's principal axis is the L-R axis on every
non-exceptional corpus case. On the box base, every covariance matrix was
exactly diagonal, so `eigh` returned `[1.0, 0.0, 0.0]` bit-exactly. The
lordotic bodies are rotated about the L-R axis, so their x–y and x–z
covariance entries are zero only analytically. They reach `eigh` as summation
residue. The largest off-axis component measured over the non-exceptional
cases is 4.9e-16.

`_pca_principal_axis` also fixes no eigenvector sign, and `crop_at_border`
label 22 now reads `[-1.0, -4.9e-16, 6.8e-17]`.

The replacement assertion, for every entry: `abs(axis[0])` is within `1e-12`
of 1.0, and `abs(axis[1])` and `abs(axis[2])` are each at most `1e-12`.

- **Why `1e-12`.** It is about 2 000 times the measured residue. It is far
  below the smallest real tilt of the axis the sibling
  `test_ac10_principal_axis_within_0996_of_left_right_on_every_golden`
  admits, where a dot of 0.996 allows about 0.09 off-axis.
- **Why without sign.** The feature is an axis. Its sign carries no meaning
  under the function's contract, and the sibling test already compares with
  `abs(dot)`.

The exception set, the manifest-derived count and the non-empty checks do not
change. Update the docstring to say "exactly the L-R axis, up to summation
residue and sign", with this date.

**(iii)
`tests/test_121_tangent_orientation.py::test_adv_doubling_back_contrasted_with_unwrapped_curvature_convention`:
re-derive (clause b), and keep the name.** The name does not name a plane.

The test contrasts two conventions on the real `relabel_swap` case. Item
121's per-vertebra angles are wrapped to (−180, 180], and item 122's
curvature arrays are unwrapped. On the box base the doubling-back showed in
the coronal plane. On the lordotic base there is no lateral offset, so the
coronal tangent angles sit at 0 and at −179.99999999999997. That is a
floating-point boundary reading, not a doubling-back, and the unwrapped
coronal array no longer leaves the range.

The doubling-back now shows in the sagittal plane, along the lordotic A-P
path:

- `SpineCurvature.sagittal_tangent_angles_deg` is
  `[2.4934, -174.7774, -176.1799, -346.4176, -291.2034]`.
- The wrapped `sagittal_deg` values are
  `[2.4934, -174.7017, 91.4601, 13.7898, 67.6713]`, all inside the range.

Prescription:

- Switch both halves of the contrast to the sagittal plane.
  - Every record's `sagittal_deg` lies in (−180, 180].
  - Some value of `curvature_result.sagittal_tangent_angles_deg` is at most
    −180 or above 180.
- The assertion message names the sagittal plane.
- Re-word the docstrings of this test and of
  `_mode4_relabel_swap_ordered_centroids`. Replace the retired
  182.3510 / 184.7816 / 358.5342 coronal figures with the fresh sagittal
  values, dated.
- Add no coronal assertion. A reading that sits on the range boundary by
  floating-point accident is not evidence of either convention.

**(iv)
`tests/test_123_recalibrate_and_regenerate.py::test_adv_exactly_four_level_mask_yields_zero_offsets_not_a_crash`:
re-decide the tolerance (clause d), and keep the name.**

The test pins a structural zero. With four levels, each held-out refit is a
cubic spline, `k = min(3, n − 1) = 3`, with as many coefficients as points,
so it interpolates, and the exact held-out offset is 0. Any non-zero value is
residue from the fit and the closest-point search. That residue depends on
the input coordinates: below 1e-9 mm on the box base, and 7.7e-9 mm on the
lordotic base (builder-reported, 2026-09-23).

Change `pytest.approx(0.0, abs=1e-9)` to `abs=1e-6`.

- **Why `1e-6` mm.** It is about 130 times the measured residue. It is still
  more than five orders of magnitude below the smallest genuine offset this
  estimator produces on the clean base: 0.434581 mm on the in-sample clean
  sweep (part 2), and the held-out offsets are larger. A real estimator
  change, which is what the test exists to make visible, would therefore
  still fail it.

The docstring gains one dated sentence on the residue. If the builder's
fresh residue exceeds 1e-7 mm, hand back, because the bound would then sit
less than an order of magnitude above it.

## Correction — 2026-09-23 (review findings)

**Appended, not a rewrite.** Everything above, including the first
`## Correction — 2026-09-23`, stands as written. Validation round 1 passed on
commit `437a0d6`. The in-loop reviewer then raised two blocking findings in
scope for this item and one minor one. This section rules on all three. The
spec-author measured every value below on this branch on 2026-09-23 with
throwaway probes that are not committed.

**No acceptance criterion or assumption above changes.** Four things are
added:

- one amended builder behaviour, part 1 (Implementation step 1);
- one adversarial case, part 1 (Testing Strategy);
- one more test under fence clause (d), part 2;
- one authorised comment and docstring edit, part 3.

**Authorised paths do not change.** `src/segfacet/synth/clean_gt.py` and
`tests/test_173_lordotic_geometric_base.py` are already listed under
**May change**. `tests/test_131_tangent_direction_normalisation.py` and
`tests/test_119_curve_formulation.py` fall under `tests/*.py` and its fence.
Clause (d) is extended below by name, as that clause requires.

### 1. The coarse-spacing fallback drops a level

**Finding.** `build_clean_spine` fills each body in turn. When a body's
rotated box contains no voxel centre, it writes one voxel at
`round(centroid / spacing)`. Nothing checks whether that voxel is already
claimed, or whether a later body's fill overwrites it. The label then ends
with 0 voxels, and nothing reports it. On this branch's builder:

| Levels | Spacing (mm) | Voxel count per label |
|---|---|---|
| L1–L3 | (20, 20, 60) | 20: 0, 21: 1, 22: 1 |
| L1–L3 | (20, 20, 66) | 20: 0, 21: 1, 22: 1 |
| L1–L3 | (20, 20, 100) | 20: 1, 21: 0, 22: 1 |

A sweep over x and y spacings in {1, 10, 20, 30, 40} mm, S-I spacings in
{1, 10, 20, 33, 40, 60, 66, 100} mm, and the spans L1–L3, L1–L5 and L4–L5
found 99 builds that drop at least one label. No committed caller is among
them. The default build, the reference cohort's spacings, and `test_092`'s
(20, 20, 20) all fill every label from its own box. `coarse-spacing-margin`
asserts only that `per_label` is non-empty, so it cannot see a dropped label.

**Ruling: every requested level is present with at least one voxel, at any
spacing. The builder does not raise.**

- **Why presence and not an error.** The fallback exists to keep the label
  present, as its comment says, and A3 already requires the build to hold at
  any spacing. Presence is always achievable, so no input needs an error. The
  grid keeps at least one empty voxel of margin on every face, outside every
  box, so an unclaimed voxel always exists. An error would also turn coarse
  builds that work today into failures.
- **Why a second pass, and not "the nearest unclaimed voxel" inside the
  existing loop.** The reviewer proposed choosing the nearest unclaimed voxel
  at the moment a body falls back. That variant was measured over the same
  sweep and still drops labels. On L1–L5 at (20, 20, 60) it drops 20 and 22,
  and 24 builds fail in total. The cause is that a later body's box fill
  overwrites an earlier body's fallback voxel. The second pass below dropped
  no label anywhere in the sweep, and left the default build
  `np.array_equal` to the current one.

**Implementation step 1, amended (builder, `src/segfacet/synth/clean_gt.py`).**

1. The fill loop writes each body's rotated box and nothing else. Remove the
   in-loop fallback.
2. After every box is written, and before the trim, make a second pass over
   the labels in ascending order. For each label with no voxel in the array,
   write it into one voxel:
   - The voxel must be unclaimed (value 0) at that moment.
   - It is the unclaimed voxel whose centre, `index · spacing`, lies nearest
     that label's centroid by Euclidean distance in mm.
   - Ties go to the lowest C-order flat index, which is what `np.argmin`
     returns first.
3. `voxel_counts` stays counted from the array.
4. Re-word the comment at the fallback. It should say what the second pass
   guarantees (every requested label keeps at least one voxel) and why it
   runs after all fills (a later box can overwrite an earlier voxel).
5. A build in which every body claims at least one voxel from its own box
   must come out byte-identical. That covers every committed caller. If
   regenerating shows any change to a committed corpus fixture, a manifest,
   `reference_default.json` or a `docs/aide/*.generated.*` file, hand back.
   The guards already exist: AC5, `test_116` AC10/AC11, `test_143` AC11–AC13,
   and `test_131`'s
   `test_ac20_fresh_default_reference_matches_committed`.

**Testing Strategy, amended (test-writer,
`tests/test_173_lordotic_geometric_base.py`).** One adversarial case is
added. Every case listed earlier stays as it is.

- **`coarse-spacing-keeps-every-level`**: parametrised over four builds:
  `build_clean_spine(levels=("L1", "L2", "L3"), spacing=s)` for `s` equal to
  `(20.0, 20.0, 60.0)`, `(20.0, 20.0, 66.0)` and `(20.0, 20.0, 100.0)`, and
  `build_clean_spine(levels=("L1", "L2", "L3", "L4", "L5"), spacing=(20.0, 20.0, 60.0))`.
  For every label of the requested levels, `np.count_nonzero(array == label)`
  is greater than 0. The array is the returned `seg_img`'s. The expected
  label sets are literals, `{20, 21, 22}` and `{20, 21, 22, 23, 24}`. They
  are not read from `voxel_counts`, which comes from the module under test.
  Each build guards a failure mode:
  - The three L1–L3 builds guard a fallback voxel that lands on a voxel
    already claimed. Today they drop label 20, label 20 and label 21 in turn.
  - The L1–L5 build guards a later body's box overwriting an earlier body's
    fallback voxel. This is the failure the in-loop "nearest unclaimed" fix
    leaves open: that variant drops labels 20 and 22 here.

### 2. Fence clause (d), extended: `test_131` AC21's `relabel_swap` coronal row

**Finding.** `_PRE_ITEM_OTHER_CURVATURE_FIELDS["relabel_swap"]` in
`tests/test_131_tangent_direction_normalisation.py` pins
`coronal_tangent_angles_deg` as `[0.0, -180.0, -180.0, 0.0, 0.0]` and
`coronal_curvature_deg` as `180.0`, at `abs=1e-6`.

At indices 1 and 2, the direction-normalised tangent's L-R component is pure
summation residue, −4.26e-16 and −5.82e-16. Its S component is −0.9958 and
−0.9978. So `atan2` sits on its branch cut, and the ±180 is decided by the
sign of the residue. The lordotic base has no lateral curve (AC4), so the
analytic L-R component is 0. The insight entry dated 2026-09-23 on the
`relabel_swap` coronal row records this.

A flipped residue does more than turn −180 into +180. All four sign
combinations of the two residues were passed through
`features/orientation.py::_signed_plane_angles_deg`:

| Residue signs (index 1, index 2) | Unwrapped coronal array | `coronal_curvature_deg` |
|---|---|---|
| (−, −), this platform | `[0, -180, -180, 0, 0]` | 180 |
| (+, +) | `[0, 180, 180, 0, 0]` | 180 |
| (+, −) | `[0, 180, 180, 360, 360]` | 360 |
| (−, +) | `[0, -180, -180, -360, -360]` | 360 |

When the signs are mixed, `coronal_curvature_deg` is 360. That exceeds
`sagittal_curvature_deg` (348.91102), so `total_curvature_deg` becomes 360
and `curvature_plane` becomes `"coronal"`. A platform with mixed residue
signs therefore fails AC21 on three fields beyond the angle list.

CI runs Linux, Windows and macOS on two numpy majors, so this is a platform
dependence in the suite. Clause (d) exists for exactly this case.

**Ruling:
`tests/test_131_tangent_direction_normalisation.py::test_ac21_other_curvature_fields_unmoved`
joins clause (d), and its name does not change.** The prescription applies
to the `relabel_swap` case only.

- **`coronal_tangent_angles_deg`: compare as angles on the circle.** The
  lengths must be equal. For each index `i`, assert
  `abs((actual[i] - expected[i] + 180.0) % 360.0 - 180.0) <= 1e-6`. The table
  literal stays `[0.0, -180.0, -180.0, 0.0, 0.0]`. All four rows of the
  table above pass this, and a real change of direction does not.
- **`coronal_curvature_deg`, `total_curvature_deg` and `curvature_plane`: not
  compared for this case.** Their values are set by the residue signs, so no
  literal holds on every platform. Keep the table entries as the dated record
  of this platform's reading. Mark them with a comment that points to this
  section and names the reason, and skip them in the comparison.
- **Everything else stays as it is.** For `relabel_swap`,
  `sagittal_tangent_angles_deg` and `sagittal_curvature_deg` are still
  compared at `abs=1e-6`. No sagittal entry is within 3.8° of the branch cut.
  The other eight cases are compared on every field exactly as before.

**Why this is the right comparison.** AC21 is evidence that item 131 changed
nothing but `tangent_angles_deg`.

- The coronal angles of `relabel_swap` are directions, and the circle
  comparison still fails if any direction moves.
- The three skipped fields keep their evidence of being unmoved on the eight
  other cases, where nothing sits on the branch cut.
- The skip is not a loosened tolerance. The three fields cannot be measured
  independently of the platform.

The production side, a sweep and plane that change with residue sign, is
`features/orientation.py`'s. That file is not in this item's scope, so it is
recorded as a dated line under the existing insight entry and not fixed
here.

**Other entries on the ±180 boundary: none that any test pins.** The probe
covered every geometric corpus case, in both planes. It checked
`SpineCurvature`'s raw `atan2`, looking for entries within 1e-6 of ±180, and
item 121's wrapped per-vertebra `coronal_deg` and `sagittal_deg`, looking for
entries within 1e-3 of ±180.

- **The only hits are `relabel_swap` labels 21 and 22 in the coronal
  plane.** The `SpineCurvature` hits are the row ruled on above.
- **Item 121's per-vertebra `coronal_deg` for those two labels reads
  −179.99999999999997 and −179.99999999996305.** No test pins it. The first
  Correction's (iii) moved `test_121`'s doubling-back test to the sagittal
  plane and added no coronal assertion. `test_121`'s range check near line
  822 runs on the hand-built `_mode4_relabel_swap_shape`, not on the corpus.
- **`tangent_angles_deg` and `inter_tangent_angles_deg` have no branch
  cut.** They come from `acos`. That covers `test_131` AC4, AC5 and AC7, and
  `test_143` AC8.
- **The feature catalogue's observed range for the curvature fields is not
  affected.** It is taken over `catalogue.py`'s own synthetic records (clean,
  fragmented, missing_level, overlaps, sequence_break), which do not include
  `relabel_swap`.

### 3. `test_119` AC8's stale 0.56 mm quotes (minor)

The first Correction moved AC8's ceiling from 0.56 to 0.44 mm. Two passages
in `tests/test_119_curve_formulation.py` still quote the old value. Both are
authorised under fence clause (a), as prose that follows a moved literal:

- AC8's trailing comment, "Implied by the 0.56 ceiling above", becomes
  "Implied by the 0.44 ceiling above".
- The module docstring's AC7/AC8 bullet says the sweep "exceeds it once,
  bounded at 0.56 mm", where "it" is item 017's 0.5 mm tolerance. Re-word it
  to say the sweep exceeds 0.4 mm and is bounded at 0.44 mm on the lordotic
  base (2026-09-23), inside stage 28's 1.0 mm bound. It no longer exceeds
  0.5 mm, as the first Correction records.

No assertion changes.

### Who does what

- **test-writer:** adds `coarse-spacing-keeps-every-level` to
  `tests/test_173_lordotic_geometric_base.py`. It fails against the current
  builder.
- **builder:** makes the second-pass fallback change in `clean_gt.py`
  (part 1). The builder also makes the two existing-test edits, as step 9
  reconciliation, in the same way it made the first Correction's clause (d)
  edits: the clause (d) comparison in `test_131` AC21 (part 2) and the
  comment and docstring edit in `test_119` (part 3). The builder records each
  in Decisions.
- **Validation step 5:** the four new parametrised ids of
  `coarse-spacing-keeps-every-level` count as this item's new tests. No id
  is renamed or retired.
