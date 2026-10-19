# Reference-artifact build recipe

> Companion to [`docs/aide/dataset-verse19.md`](aide/dataset-verse19.md) (the
> real-VerSe layout/naming facts) and the item-082 spec
> ([`docs/aide/items/082-real-verse-build-recipe.md`](aide/items/082-real-verse-build-recipe.md)).
> This document is the **recipe + policy**; it adds no code. The build
> machinery it drives (`segfacet build-reference`, `ingest_cohort`,
> `build_reference`, `write_artifact`, `load_artifact`) already exists
> (items 044/045/063/081).

## Overview

The project ships and consumes **two** reference-data artifacts:

1. **The committed synthetic default** — `src/segfacet/reference/reference_default.json`.
   Built from a fixed, seeded, no-wall-clock synthetic cohort
   (`segfacet.reference.artifact.build_default_cohort`) via
   `python -m segfacet.reference.artifact`. This is the **test/determinism
   baseline**: it is byte-reproducible across platforms and runs, and Stage
   6/8 determinism tests depend on it never changing shape unexpectedly. It
   is not a stand-in for real anatomical grounding.
2. **A separately versioned real-VerSe artifact** —
   `reference_verse_vN.json` (e.g. `reference_verse_v1.json`), with
   `provenance.source == "verse-vN"` (e.g. `"verse-v1"`). Built from a real
   mounted VerSe ground-truth cohort via `segfacet build-reference` (see
   *Build invocation* below). This is the artifact that grounds the
   delta-to-reference machinery in real anatomy.

The real-VerSe artifact is **additive** — it never overwrites or replaces
`reference_default.json`.

## Storage & versioning policy

- **Raw VerSe scans (and any other real-cohort NIfTI data) are never
  committed to this repo.** They are large binary blobs and/or
  licensed/restricted data; git is the wrong storage layer for them. This
  mirrors the existing policy in `docs/aide/dataset-verse19.md` for the raw
  `dataset-verse19training/` download.
- **Only the derived distributions artifact is committed** — the small JSON
  file produced by `write_artifact` (per-level feature statistics +
  provenance), never the source scans/masks it was built from.
- **The committed synthetic `reference_default.json` is retained, not
  replaced.** A real-VerSe build does **not** overwrite the bundled default;
  it is written to its own versioned filename and shipped alongside it.
- **Versioned naming convention:** `reference_verse_vN.json`, with
  `provenance.source == "verse-vN"`. Since item 234 a rebuild replaces
  `reference_verse_v1.json` in place, and the cohort that built it is recorded
  in its `provenance.case_ids` rather than implied by a version number. When an
  actual real-VerSe artifact is built by a data-holding human or CI runner,
  it is committed under `src/segfacet/reference/` as package data (so it ships
  importable/selectable by path alongside the default), and its filename
  pattern should be pinned `text eol=lf` in `.gitattributes` for CRLF
  hygiene on Windows checkouts (see the Gotchas note in the project
  `CLAUDE.md`). **This item commits no such file** — see the fenced scope
  in the item-082 spec.

## Acquisition

Real VerSe ground truth comes from the **VerSe19** training release:

- **Source:** `dataset-verse19training.zip` from
  `https://s3.bonescreen.de/public/VerSe-complete/`.
- **DOI:** `10.17605/OSF.IO/NQJYW`.
- Full layout, naming convention, label mapping, and size/count facts are
  documented in [`docs/aide/dataset-verse19.md`](aide/dataset-verse19.md) —
  read that living reference first; this document only restates what is
  needed to stage a build.

The dataset root's exact nesting depth beneath the configured cohort root is
not fixed (see `docs/aide/dataset-verse19.md`'s "Git / versioning policy" —
some extraction tools produce a wrapping `dataset-verse19training/` directory
around the actual root, some don't); either way it contains:

```
rawdata/sub-verseNNN/sub-verseNNN_ct.nii.gz
derivatives/sub-verseNNN/sub-verseNNN_seg-vert_msk.nii.gz
```

(plus split-subject `_split-verseMMM` infixes, centroid JSON, and preview
PNGs that the build recipe does not need).

## Staging the cohort for ingestion

`segfacet.reference.ingest.ingest_cohort` was built for item 044's flat,
**non-recursive** convention: it lists a single `--cohort` directory with
`os.listdir` (no recursive walk of subdirectories) looking for files ending
in `--seg-suffix`, and for each match hardcodes the sibling scan filename as
`<id>_scan.nii.gz` (there is no `--scan-suffix` flag). Real VerSe's on-disk
layout does not match this directly — masks live nested under
`derivatives/sub-verseNNN/`, and CT scans are named `..._ct.nii.gz`, not
`..._scan.nii.gz`.

**Item 123 shipped the reproducible path, and item 234 rewrote its cohort
half**: `scripts/rebuild_verse_reference.py` no longer discovers masks by a
recursive glob or stages a directory (that mixed roles: a three-split root
ingested all 160 VerSe19 masks). It resolves two three-split release roots
(`--verse-cohort`, else the `SEGFACET_VERSE_COHORT` environment variable, for
VerSe19, and `--verse20-cohort` / `SEGFACET_VERSE20_COHORT` for VerSe20),
resolves the `development` role of the bundled `verse19.yaml` and
`verse20.yaml` descriptors against them, and refuses to build (exit `1`, no
artifact) if any development case also resolves in a calibration or test role.
With either root unresolved the run is a structured skip. It ingests the
merged cohort (`--jobs N` in parallel) and drives `aggregate_reference` /
`write_artifact` over it:

```bash
.venv/bin/python scripts/rebuild_verse_reference.py \
    --out out/verse-rebuild \
    --verse-cohort "$SEGFACET_VERSE_COHORT" \
    --verse20-cohort "$SEGFACET_VERSE20_COHORT" \
    --build-date 2026-10-18 --jobs 8
```

(Either flag may be omitted once its variable is exported; the CLI flag
overrides the environment variable when both are given.) The
tool never writes beneath the cohort roots, and never writes the committed
package copy under `src/segfacet/` — it writes
`<out>/reference_verse_v1.json` and a structured
`<out>/verse_rebuild_summary.json` recording the cohort, the
built artifact's identity, and the derived
`spline_offset.max_offset_mm` calibration (see AC9–AC17 in
[`docs/aide/items/123-recalibrate-and-regenerate-downstream-artifacts.md`](aide/items/123-recalibrate-and-regenerate-downstream-artifacts.md)).
Installing the rebuilt artifact — copying `<out>/reference_verse_v1.json`
over `src/segfacet/reference/reference_verse_v1.json` — remains a separate,
explicit operator step, exactly as it does for `scripts/refresh_reference.py`.

An unreachable cohort (no root resolvable, or a root with no matching masks)
is a structured skip recorded in the summary's `cohort` block, never a
traceback: `main` still returns `0`.

**Read VerSe masks through `segfacet.io.load_volume(path, integer_labels=True)`,
never a bare `nibabel.load`.** VerSe19's committed masks are not stored
RAS-resolving; `load_volume` reorients them (item 094's contract) and every
in-pipeline consumer sits downstream of it, but an ad-hoc measurement script
that loads raw silently measures the wrong axes — `centroid_mm[2]` is then not
the superior-inferior axis. Measured 2026-08-31 on the first eight training
subjects: through `load_volume` the ascending-label net S advance runs −26 to
−364 mm (caudal-first, as real anatomy demands); through `nibabel.load` the
same eight read −6.5 to +2.1 mm, and a traversal-order monotonicity check that
trusted the raw axes called seven of the eight non-monotonic. This bites
exactly the code that never runs in CI — cohort sweeps and one-off scripts.

## Build invocation (manual alternative)

The staging tool above is the reproducible path for a real VerSe cohort; the
underlying `segfacet build-reference` CLI can still be driven directly
against an already-flat staged directory when that's more convenient:

```bash
segfacet build-reference \
    --cohort staged_verse \
    --out src/segfacet/reference/reference_verse_v1.json \
    --source verse-v1 \
    --build-date 2026-07-15 \
    --seg-suffix _seg-vert_msk.nii.gz
```

- `--seg-suffix _seg-vert_msk.nii.gz` is the only flag needed to handle
  VerSe's mask naming; `ingest_cohort` strips it to form each `subject_id`
  (e.g. `sub-verse004` from `sub-verse004_seg-vert_msk.nii.gz`).
- `--source` and `--build-date` are caller-supplied and stamped verbatim
  into `provenance` (never derived from `date.today()`), so re-running the
  same command on a different date reproduces identical provenance.
- With scans staged as `<id>_scan.nii.gz` siblings, the build carries all
  three feature families at once: geometry (item 044,
  `INGESTED_FEATURES`), intensity (item 063,
  `INGESTED_INTENSITY_FEATURES`), and morphology (item 081,
  `INGESTED_MORPHOLOGY_FEATURES` —
  `largest_component_fraction`, `component_count`, `eigenvalue_ratio`), at
  schema version `"1.2"`. `build_reference` defaults `with_morphology=True`
  and `with_intensity=True`, and `_handle_build_reference` does not
  override either flag, so no extra CLI switches are required to get the
  full `"1.2"` artifact.
- An absent or empty `--cohort` (or a mistyped `--seg-suffix` that matches
  nothing) errors cleanly: `segfacet build-reference` exits non-zero, writes no
  partial file at `--out`, and prints an `Error:`-prefixed message to
  stderr — no Python traceback. This is existing behaviour
  (`_handle_build_reference` catching `(OSError, ReferenceArtifactError)`),
  exercised (not newly implemented) by this item's tests.

## Deployment selection

A deployment picks up the real-VerSe artifact instead of the bundled
default via either:

- the CLI flag: `segfacet run --reference-artifact src/segfacet/reference/reference_verse_v1.json …`, or
- the config key: `reference.artifact_path: src/segfacet/reference/reference_verse_v1.json`
  in the run config.

**Discouraged alternative — bundle-swap.** Overwriting
`reference_default.json` in place with a real-VerSe build is explicitly
**not** recommended: it would destroy the reproducible synthetic baseline
that Stage 6/8 determinism tests assert against, and it collapses the
distinction between "test fixture" and "grounded reference" that this policy
exists to preserve. Always ship the real build under its own versioned
filename and select it explicitly.

## Reproducibility & automation

- `build_date` is always **caller-supplied**, never `date.today()` — the
  same invocation on any date produces identical `provenance.build_date`.
  This is what makes the build recipe deterministic and testable (see
  `tests/test_082_verse_build_recipe.py`'s AC2 assertion that a re-run with
  the same arguments reproduces the same stamped values).
- `eigenvalue_ratio` (item 081's PCA-based morphology feature) is a
  platform-sensitive float — its last few bits of precision can differ
  across BLAS/LAPACK implementations. Two builds of the *same* cohort should
  be compared with a numeric tolerance (`segfacet.synth.golden.reports_close`),
  not byte-identity, per items 078/081.
- The real-VerSe artifact is **committed once**, by whoever runs the build
  against the mounted real cohort — it is **not** regenerated in CI (CI has
  no access to the real data, and even if it did, the eigenvalue-ratio float
  would make a byte-determinism test flaky across CI runners). No
  cross-platform byte-determinism test is run against it; only the bundled
  synthetic default carries that guarantee.
- For a **one-command** refresh (rebuild synthetic default + optionally the
  real artifact when a cohort is mounted + re-evaluate), see **item 083**'s
  refresh wrapper — this document only covers the manual invocation of the
  existing `segfacet build-reference` CLI.

## Rebuild record — 2026-08-29 (item 123)

`scripts/rebuild_verse_reference.py` was run against the full, real 80-subject
VerSe19 training cohort (`SEGFACET_VERSE_COHORT`, no CT/mask missing). The
build completed cleanly — all 25 canonical levels present, `subject_count ==
80` — and `derive_max_offset_mm` (item 123's pure `mislabel.max_offset_mm`
derivation rule, `p99`-over-qualifying-levels rounded up to the next `0.5`
mm, floored at `6.0` mm) measured the real-GT ceiling `P = 21.209073949050172`
mm at level `L5` (`count = 62`), giving a derived threshold of `21.5` mm.

**That value falls outside the corpus window `(5.143859, 17.507445]`** that
the 2026-08-27 "Spinal curve model — the deformity envelope" human gate
(`progress.md`, `## Human gates`) approved, so the recalibration was **not**
applied: `heuristics/mislabel.py`'s `_DEFAULT_MAX_OFFSET_MM` stays `15.0`,
and `reference_verse_v1.json` / `reference_default.json` / the corpus
goldens are unchanged. This is the item's own spec-mandated hand-back
outcome (see the item's Decisions log), not a build failure — the real GT
does reach into and past the approved envelope at `L5`, and widening (or
otherwise revising) that envelope needs a person's decision, not a rebuild.
The full evidence (`p99_by_level`, the qualifying-level list, and the
top-offset subject ids) is in the rebuild's own
`verse_rebuild_summary.json`, regenerable by re-running the command above.

## Rebuild record — 2026-08-29, resolved (item 123, terminal-vertebra exclusion)

A follow-up per-vertebra analysis of the 2026-08-29 measurement above showed
the `L5` anomaly was entirely a **terminal-extrapolation** artefact of item
120's held-out estimator (terminal `L5` `p99` `21.5` mm vs. interior `L5`
maximum `1.00` mm across the same 80-subject cohort), not real deformity. By
human decision the same date, sequence-terminal vertebrae (a subject's
cranial-most and caudal-most present level) are excluded from both the
`mislabel` rule and the reference distribution
(`src/segfacet/features/spline_offset.py`'s `is_terminal` flag;
`reference/ingest.py` / `reference/delta.py` exclude it symmetrically; see
the item spec's Decisions log for the full record).

`scripts/rebuild_verse_reference.py` was re-run against the same 80-subject
cohort (reusing the cached staged directory) under this exclusion. The
interior-only ceiling `P = 12.90577608928562` mm at level `T10`
(`count = 37`) derives a threshold of **`13.0` mm** — inside the approved
corpus window `(5.143859, 17.507445]` — so the recalibration is applied:
`heuristics/mislabel.py`'s `_DEFAULT_MAX_OFFSET_MM` and
`default_config.yaml`'s `rules.mislabel.max_offset_mm` are both `13.0`;
`reference_verse_v1.json` and `reference_default.json` are rebuilt (the
latter via `python -m segfacet.reference.artifact`); the nine corpus goldens
and `tests/golden/022_stage3_report.json` are regenerated to carry
`is_terminal`, with `displace` and `crop_at_border` additionally
moving their `mislabel` finding's threshold clause from `15.0` to `13.0` mm.
`L5` dropped to 3 interior occurrences (below the `count >= 10` qualifying
floor, mean `0.69` mm) and `C1` (always terminal-only in this cohort) carries
no `spline_offset_mm` statistic at all — both expected consequences of the
exclusion. `spline_offset_mm` is therefore now an **interior-only** feature
end to end. Full evidence (`terminal_count`/`interior_count`, `p99_by_level`,
the qualifying-level list, and the top-offset subject ids) is in the
re-run's `verse_rebuild_summary.json`.

**Intensity coverage changed with this rebuild.** The pre-123 (2026-07-17)
committed `reference_verse_v1.json` computed every level's `intensity_*`
statistics from a strict *subset* of that level's subjects (e.g. `L1`: 47 of
59; `C1`–`C4`: 1 of 13) — most likely because the manual staging recipe this
document used to carry iterated over each split-subject's *parent* directory
and so could never name a split subject's own `${sub}_split-verseMMM_ct.nii.gz`
CT. Item 123's rebuild tool discovers CTs recursively and split-infix-aware,
finds one for all 80 subjects, and the rebuilt artifact's intensity coverage is
complete (`count == record_count` on every level). Verified not to be a
scan/mask mispairing: zero geometric features moved on any level, and
spot-checked HU ranges are physiologically plausible. Anything measuring or
re-deriving thresholds from `reference_verse_v1.json`'s `intensity_*`
statistics (e.g. `heuristics/intensity_reference_delta.py` defaults) should
know a pre-123 baseline undercounted every level.

## Rebuild record — 2026-10-13 (item 221, every interior outlier withheld)

Item 221 changed the held-out spline-offset estimator to withhold every
interior level reading `10.0` mm or more (an add-then-remove search), not
only the in-sample dominant outlier. To check the effect on real data,
`scripts/rebuild_verse_reference.py --verse-cohort dataset-verse19training`
was run on the 80-subject VerSe19 training cohort at commit `704c4eea`
(item 221's branch `aide/221-held-out-spline-offset-with`). It exited `0`.

The interior ceiling is unchanged: P = 12.905776 mm at level `T10`
(`count = 37`), measured from `reference_verse_v1.json` with
`_p99_by_level` (`12.90577608928562` unrounded), which derives a threshold of
`13.0` mm. P was computed from the committed `reference_verse_v1.json`
(item 221's test reads that file); the rebuilt artifact was compared with it
but P was not read from it. The per-mask `spline_offset_mm` readings are
identical; nine statistic cells differ between the rebuilt and the committed
artifact: the `p1` and `p5` percentiles of `L3` and `L4` (by at most about
`1e-15`), `mean` and `std` (by at most about `1e-8` relative) and `min` (past
the 8th significant digit). The cause was not isolated: no rebuild at the base
commit was run, and a numpy, scipy or platform difference from the build of
the committed artifact is plausible. None of it changes a verdict, so
`reference_verse_v1.json` is **not** re-committed.

`spline_offset.max_offset_mm` stays `13.0`, and `gate-fac1` (verse406 T10,
`18.51` mm) is unchanged and still open.

## Rebuild record — 2026-10-18 (item 234, development role)

Item 234 rebuilt `reference_verse_v1.json` in place from the `development`
role of both VerSe releases, through the descriptor-driven tool:

```bash
.venv/bin/python scripts/rebuild_verse_reference.py --out <scratch> \
    --verse-cohort <VerSe19 three-split root> \
    --verse20-cohort <VerSe20 three-split root> \
    --build-date 2026-10-18 --jobs 30
```

It exited `0`. The wall time was not recorded by the builder; the spec-time
probe measured about 19 CPU-hours for a serial run (item 234, A14), hence
`--jobs 30`. A second determinism run into a separate directory was **not
run**, so the byte-identity of two real rebuilds is unverified; the stand-in
determinism (AC5) is tested.

- **Cohort.** 141 subjects: VerSe19 80 development (of 80 / 40 / 40
  development / calibration / test) and VerSe20 61 development (of 61 / 80 /
  73). The role-overlap check passed. `subjects_without_scan` is empty. The
  sorted case ids are the artifact's `provenance.case_ids`. 26 levels: C1-C7,
  T1-T13, L1-L6.
- **Threshold.** Read from the committed artifact with `_p99_by_level`: P =
  7.915787852893431 mm at level `L4` (106 readings), so
  `derive_max_offset_mm` gives **8.0 mm**, which lies inside the A9 corpus
  window and equals `_DEFAULT_MAX_OFFSET_MM`. Qualifying levels: 23 (every level
  with at least 10 interior readings; `L6` and `T13` do not qualify, `C1` is terminal-only). Item 123's
  value was 13.0 mm (P = 12.91 mm at T10 over 80 VerSe19 cases).
- **Exclusion.** The `spline_offset_mm` reading of
  `sub-verse406_split-verse261` T10 (label 17), 18.51028119357566 mm, is
  withheld (`gate-fac1`, owner decision 2026-10-16). T10 then has 72 readings
  and p99 2.977 mm (73 and 7.388 mm before). P does not move.
- **Interior development readings at or above 8.0 mm** (after the exclusion):
  3 of 1355 interior readings, maximum 8.848 mm (`sub-verse111` L4). The spec-time
  probe named them as `sub-verse111` L4 8.848, `sub-verse586` L5 8.143 and
  `sub-verse107` L4 8.033, plus the excluded verse406 T10. The interior
  p99 over all levels is 4.963 mm. 282 terminal readings are held out of the
  reference. On ground truth these are anatomy, so false positives of the
  `displaced_vertebra` condition (left open in the item).
- **Intensity coverage.** Every level's `intensity_mean` count equals its
  `record_count`: C1 27, C2 27, C3 29, C4 29, C5 33, C6 36, C7 50, L1 108,
  L2 112, L3 112, L4 111, L5 107, L6 16, T1 67, T2 69, T3 64, T4 60, T5 57,
  T6 56, T7 57, T8 59, T9 74, T10 87, T11 93, T12 96, T13 2. The 25 VerSe19
  split cases keep their intensity statistics (A8).
- **Artifact.** sha256
  `845d29e8958d8730271d38fc1087c17e25c802886a4225d8ac235f1453875062`.
- **Warnings.** The run printed many scipy `_fitpack_repro` "s too small"
  RuntimeWarnings from the spline fit. Whether they predate this item is
  unmeasured: no pre-item rebuild was run to compare counts. Item 234 does
  not change the fit path (`features/` spline code).

### Corpus through the default-reference CLI

`segfacet run --scan <scan> --seg <seg> --out <dir>` with no reference flag,
every case of `tests/corpus/manifest.json`, measured 2026-10-18 against the
rebuilt artifact. All 14 return `flagged-for-review`. The `spline_offset`
column is unchanged from the `985ee0d0` baseline.

| case | findings (by rule) |
|---|---|
| clean_control | 54 (bounds 20, reference_delta 34) |
| displace | 46 (bounds 16, reference_delta 29, spline_offset 1) |
| fragment | 55 (bounds 20, fragmentation 1, reference_delta 34) |
| inject_islands | 55 (bounds 20, fragmentation 1, reference_delta 34) |
| relabel_swap | 54 (bounds 20, mislabel 1, reference_delta 33) |
| remove_level | 45 (bounds 16, centroid_spacing 1, coverage 1, reference_delta 27) |
| crop_at_border | 25 (border 3, bounds 8, reference_delta 14) |
| sequence_break | 45 (bounds 16, mislabel 1, reference_delta 27, spline_offset 1) |
| fuse_adjacent | 42 (bounds 15, centroid_spacing 1, reference_delta 26) |
| remove_level_relabel | 44 (bounds 16, centroid_spacing 1, reference_delta 27) |
| split | 51 (bounds 18, fragmentation 1, neighbour_contact 1, reference_delta 31) |
| split_own_label | 54 (bounds 20, reference_delta 32, spline_offset 1, split_fragment 1) |
| crop_fov_si | 42 (bounds 16, reference_delta 26) |
| fuse_separate | 43 (bounds 15, centroid_spacing 1, fragmentation 1, reference_delta 26) |

The clean-control figure is 54 findings (was 55 at `985ee0d0`; the item-090
gotcha in `CLAUDE.md` still says ~40). `CLAUDE.md` is not edited here (owner
decision 2026-10-18); the correction is a separate reviewed edit.
