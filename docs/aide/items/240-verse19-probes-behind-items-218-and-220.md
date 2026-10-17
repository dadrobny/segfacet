<!-- aide-template: item 3 -->
# Item 240 — VerSe19 probes behind items 218 and 220

> **Created:** 2026-10-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-032.md`](../queue/queue-032.md) · Item 240
> **Objectives:** G2, G3
> **Suggested branch:** `aide/240-verse19-probes-behind-items-218`

---

## Description

This item closes two `defect` entries in `insights.md`.

- **`2026-10-13-af10`.** Item 220 cites three closest-centroid-pair figures as
  measured facts: 12.542 mm (geometric corpus), 32.695 mm (intensity corpus)
  and 11.082 mm (VerSe19 ground truth, 159 masks). They appear in
  `src/segfacet/heuristics/collapsed_labels.py`, in a comment in
  `src/segfacet/default_config.yaml`, and (11.082 only) in mode 13's
  `mechanism` in `src/segfacet/failure_modes.py`. They come from the
  spec-time probe at `2a1491d`. Item 220's Validation step 1 replay was never
  run in the build, and is recorded ❓ Unverified.
- **`2026-10-13-3619`.** Item 218's `centroid_spacing` rule has a
  `missing_level` detector with no sacral or coccygeal exclusion. Its
  `fused_label` detector has one (item 218 A4, inherited from item 207). A
  gap beside a sacral label of normal size ratio may read above 1.5 and give
  a false `Missing level:` finding. Item 218's A7 VerSe19 probe was not shown
  to cover such gaps.

This item does three things.

1. **It replays item 220's figures, and the suite keeps replaying them.** The
   spec-time replay at `20219443` reproduces every figure exactly (A1), so no
   citation changes. New tests recompute each figure from its primary source
   and compare it with every place that cites it. The two corpus figures are
   measured on every run. The VerSe19 figure is measured where the cohort is
   mounted, and its test skips cleanly elsewhere.
2. **It measures `missing_level` on VerSe19 and records the result.** At
   `20219443` the rule fires nothing on 159 masks (A2). But VerSe19 ground
   truth has no label 26 (S1) or 27 (Cocc) at all, so no sacral gap could be
   measured.
3. **It adds the sacral and coccygeal exclusion to `missing_level`.** A gap
   is not judged when either label beside it is sacral or coccygeal. This is
   the same predicate `fused_label` already applies (A3, A4).

**Not in scope:**

- Speeding up `compute_centroid`. The replay finishes without it (A7).
- Any change to `collapsed_labels`, its tolerance, mode 13, or the
  `default_config.yaml` comment. No figure moved (A8).
- Calibrating `missing_level` on real segmenter output. That belongs to
  Stage 16 (Left open).

## Acceptance Criteria

- [ ] **AC1: The geometric-corpus figure equals the live measurement at every
  site that cites it.** Let `m` be the minimum, over every case in
  `tests/corpus/manifest.json`, of the smallest pairwise `math.dist` between
  that case's label centroids. Each centroid is
  `segfacet.features.centroids.compute_centroid(img, label).centroid_mm`, with
  `img = segfacet.synth.regression.loaded_seg_image(case)`. `f"{m:.3f} mm"`
  then occurs in three places:
  - `segfacet.heuristics.collapsed_labels.__doc__`;
  - the docstring of `DEFAULT_MAX_CENTROID_DISTANCE_MM`, which is the string
    expression right after that assignment in the module's AST;
  - the prose element of `CollapsedLabelsRule.mode_declaration.evidence`.

  `f"{m:.2f} mm"` also occurs in the text of
  `segfacet.config.default_config_path()`.
- [ ] **AC2: The intensity-corpus figure equals the live measurement at every
  site that cites it.** This is AC1's measurement and AC1's four sites, but
  over every case of `segfacet.synth.intensity.load_intensity_manifest()`.
  Each image is `loaded_seg_image(case, INTENSITY_CORPUS_DIR)`.
- [ ] **AC3: The VerSe19 figure equals the live measurement at every site
  that cites it** *(gated on the VerSe19 cohort, A5)*. Let `m` be the minimum
  of the smallest pairwise centroid distance over every
  `*_seg-vert_msk.nii.gz` found recursively under the VerSe19 root that has
  two or more labels. The centroids are computed as in AC1, on the mask
  loaded with `nibabel.load`. `f"{m:.3f} mm"` occurs in AC1's three
  `collapsed_labels` sites and in `segfacet.failure_modes.SPECIFICATION[13].mechanism`.
  `f"{m:.2f} mm"` occurs in the text of `default_config_path()`.
- [ ] **AC4: The VerSe19 mask count equals the count cited beside the figure**
  *(gated on the VerSe19 cohort, A5)*. Let `n` be the number of AC3's masks
  with two or more labels. Collapse whitespace in each text to single spaces.
  Then `collapsed_labels.__doc__` contains `f"{n} VerSe19 GT masks"`, and the
  `DEFAULT_MAX_CENTROID_DISTANCE_MM` docstring contains `f"{n} masks"`.
- [ ] **AC5: `missing_level` does not judge a gap beside a sacral label.**
  Take `extract_feature_record(loaded_seg_image(remove_level case),
  bundled_default_config())`. As a precondition, `CentroidSpacingRule().evaluate`
  on it returns exactly one `missing_level` finding, on labels `{21, 23}`.
  Copy the record and set label 23's `level_name` to `"S1"`. `evaluate` on
  the copy then returns no finding whose `detector_id` is `missing_level`.

## Assumptions

- **A1 (measured: the `2026-10-13-af10` replay reproduces every figure).** Measured
  2026-10-17 at `20219443` with `compute_centroid`, every pair of labels per
  case, and `math.dist` over `centroid_mm`.
  - **Geometric corpus (14 cases):** the minimum is 12.542003580961284 mm, on
    `split_own_label` labels 22 and 23 (L3–L4). The next closest is
    `crop_fov_si` at 29.786 mm. The figure is the same whether the fixture
    is read with `nibabel.load` or with `loaded_seg_image`.
  - **Intensity corpus (4 cases, one shared seg `clean_spine_seg`):** the
    minimum is 32.695217722421916 mm, on labels 21 and 22 (L2–L3).
  - **VerSe19 ground truth:** 160 masks were found under the three-split
    root. 159 have two or more labels; `sub-verse116` has one. The minimum
    is 11.08206996606983 mm, on `sub-verse401_split-verse201` labels 3 and 4
    (C3–C4). The next closest are 12.303 mm (`sub-verse230` C5–C6) and
    12.443 mm (`sub-verse207` C4–C5). No mask has a pair at or below 2.0 mm.

  These are item 220 A3's figures and counts, unchanged. So every citation
  holds, and AC1–AC4 pass on the current tree with no source edit.
- **A2 (measured: `missing_level` on VerSe19 ground truth).** Measured
  2026-10-17 at `20219443`, on all 159 masks with two or more labels. Each
  record is `extract_feature_record` with the bundled config. The rule was
  run two ways: `CentroidSpacingRule().evaluate` (raw), and `run_rules` with
  that rule alone (after the condition gate).
  - Raw and gated, there are **0 `missing_level` findings and 0
    `fused_label` findings**.
  - The largest gap ratio is 1.3782, on `sub-verse207` labels 2–3 (C2–C3),
    with flanking size ratios 1.272 and 0.786. 157 masks have three or more
    spacings. Both match item 218 A7 (1.378, 157 masks), which was measured
    with scipy centres of mass. On every mask, path order equals integer
    order.
  - **Label counts:** label 25 (L6) appears in 6 masks. Labels 26 (S1),
    27 (Cocc) and 28 (T13) appear in none. VerSe19 ground truth therefore
    holds **no gap touching a sacral or coccygeal label**, and the risk in `2026-10-13-3619`
    cannot be measured on this cohort.
  - The six L5–L6 gaps read 0.783–0.986. One of them (`sub-verse131`)
    touches the volume border on both labels.
- **A3 (decided: add the exclusion although no firing was measured).** The
  queue line says to add the exclusion "if any fires falsely". The
  measurement can say nothing about that, because the cohort has no sacral
  label (A2), so the condition is unresolved rather than false. The
  exclusion is added for these reasons:
  - **Analytic.** `missing_level`'s premise is a regular vertebral pitch.
    The sacrum is five fused segments, and its centroid does not lie one
    pitch below L5. A gap to it is not a pitch measurement. This is the
    reason `fused_label` excludes sacral and coccygeal labels.
  - **Cost.** It moves nothing measured. No committed corpus case, ladder
    case or VerSe19 mask carries label 26, 27 or 29–33.
  - **Exposure.** Stage 16 runs the rule on real segmenter output, where
    sacrum labels are routine.

  **What is lost:** a missed L5 between L4 and S1 is no longer reported by
  `missing_level` (Left open).
- **A4 (decided: the predicate is `fused_label`'s, and label 25 is lumbar).**
  "Sacral or coccygeal" means `str(level_name).startswith("S")` or
  `level_name == "Cocc"`, as `centroid_spacing.py`'s `fused_label` loop reads
  it today. Under `segfacet.labels.DEFAULT_LABEL_MAP` that is labels 26 (S1),
  27 (Cocc) and 29–33 (S2–S6).
  - Insight `2026-10-13-3619` says "labels 25/26", but label 25 is `L6`, a lumbar
    transitional vertebra. It is not excluded, and it stays judged. The
    `l6-flank-still-judged` case guards this.
  - A gap is skipped when **either** flanking label matches. The two
    spacings that each sit beside a sacral gap still serve as a baseline
    for their own neighbours (Left open).
- **A5 (decided: the VerSe19 cohort, the variable and the skip).**
  - **No new gated capability, and no `[validation]` profile.** The tests
    read the cohort through the existing `SEGFACET_VERSE_COHORT` convention,
    as `tests/test_084`, `088`, `091`, `118` and `125` do. `aide.toml`'s
    `[validation]` comment keeps machine-varying inputs in the environment.
    The cohort is already ✅ Verified in `progress.md`'s Environment-Gated
    table ("Real VerSe GT reference distributions"), so no row is added.
  - **The root is the VerSe19 directory that holds all three splits**:
    `dataset-verse19training`, `dataset-verse19validation` and
    `dataset-verse19test`. A1's 159 is a three-split count.
  - The gated tests skip when the variable is unset or empty, when it is not
    a directory, or when any of the three split directories is missing
    beneath it. The skip reason names `SEGFACET_VERSE_COHORT` and the
    three-split requirement.
  - The variable means two different roots today: `test_125` AC10 expects
    the training split alone, which is 80 masks (insight `2026-10-17-e94a`).
    Requiring all three splits makes this item's tests skip, not fail,
    under the training-only value.
  - **Per-machine note (how the validator sets it).** On the reference host
    where items 218, 220 and this item measured, the root is the parent
    directory of the target of the repo-root `dataset-verse19training`
    symlink. Item 218's Decisions correction of 2026-10-13 names it. Resolve
    it there, or on another host wherever the three splits were unzipped.
    Export it for the one pytest invocation in Validation step 1. This spec
    deliberately does not record the absolute path.
- **A6 (decided: the VerSe19 `missing_level` replay is a Validation step,
  not a test).** It needs a full `extract_feature_record` per mask.
  - Measured 2026-10-17: 7.9 s on `sub-verse009`, a 459 × 459 × 66 volume
    with 16 labels, where `compute_components` takes 4.4 s. That is
    minutes to tens of minutes serially over 159 masks.
  - No source in the tree cites a VerSe19 firing count, so there is no
    citation for a test to keep honest. Item 218 A7's 1.378 / 157 is cited,
    in `centroid_spacing.py`, and A2 confirms it here. A per-run guard on it
    is left out for the same cost.
- **A7 (decided: no `compute_centroid` speed-up).** The slow replay that
  `2026-10-13-af10` records came from `compute_centroid` reading `seg_img.dataobj` once
  per label off a lazily loaded `.nii.gz`. A test that wraps the loaded
  array in an in-memory `Nifti1Image` decompresses each mask once. Measured
  on one 6-label mask: 0.8 s lazy against 0.1 s in memory. The production
  function stays as it is.
- **A8 (decided: no citation is edited).** Every figure reproduced (A1), so
  `collapsed_labels.py`, `default_config.yaml` and `failure_modes.py` are
  pinned, not changed. If the build-time replay (Validation step 1) moves a
  figure, the builder hands back. A changed citation would move the
  generated catalogue, traceability and failure-mode docs, which carry the
  evidence and mechanism prose, and those paths are not authorised here.
- **A9 (measured: a border-touching sacral label is already gated).**
  `CentroidSpacingRule` has no `condition_opt_ins`. So the runner's
  `fov_truncation` gate (`segfacet.heuristics.runner`, item 191) already
  drops a `missing_level` finding on a label that touches a volume face.
  That covers the "cropped sacral label" half of `2026-10-13-3619`. The exclusion covers
  the other half: a small sacral label that is not on the border.

## Implementation Steps

1. **`src/segfacet/heuristics/centroid_spacing.py`.**
   - Add a module-private `_is_sacral_or_coccygeal(level_name) -> bool`
     holding today's `fused_label` predicate
     (`str(level_name).startswith("S") or level_name == "Cocc"`).
   - Use it in the `fused_label` loop in place of the inline test. That
     changes no behaviour.
   - In the `missing_level` loop, before the gap ratio is computed, skip gap
     `i` when either `per_label[keys[i]]` or `per_label[keys[i + 1]]` has a
     sacral or coccygeal `level_name` (`level_name` defaults to `"unknown"`,
     as in the `fused_label` loop).
   - Leave the spacings, the baselines and `size_ratio` unchanged.
   - Module docstring, `missing_level` paragraph: add one sentence. A gap
     beside a sacral or coccygeal label is not judged (item 240), because the
     sacrum's centroid does not sit at a vertebral pitch, which is the same
     reason as `fused_label`'s.
   - Leave the detectors' `question` and `fires_when` unchanged. `fused_label`'s
     do not name its exclusion either. `level_name`'s `ConsumedPath` reason
     already reads "excludes sacral and coccygeal labels from judgement".
     So `docs/aide/rules.generated.md`, which `segfacet.rule_table` builds
     from those fields, does not move.
2. **No other source change.** No dependency is added. `collapsed_labels.py`,
   `default_config.yaml` and `failure_modes.py` are not edited (A8).
3. **Run Validation steps 1 and 2**, and record each result with the commit
   under Decisions & Trade-offs.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/centroid_spacing.py` — the `missing_level` sacral and coccygeal exclusion, and its docstring sentence (step 1)
- `tests/test_240_verse19_probes.py` — the new test module

**Asserts against:**

- `src/segfacet/heuristics/collapsed_labels.py` — AC1–AC4 read its module docstring, the constant's docstring and the evidence prose
- `src/segfacet/default_config.yaml` — AC1–AC3 read the `collapsed_labels` comment's two-decimal figures
- `src/segfacet/failure_modes.py` — AC3 reads mode 13's `mechanism`
- `tests/corpus/manifest.json` — AC1 iterates its cases, and AC5 takes the `remove_level` case from it
- `tests/corpus/fixtures/*.gz` — AC1 and AC5 load the committed seg fixtures
- `tests/corpus/intensity/manifest.json` — AC2 iterates its cases
- `tests/corpus/intensity/fixtures/*.gz` — AC2 loads the committed seg fixture

## Testing Strategy

The module is `tests/test_240_verse19_probes.py`, with one test per AC.

- **Shared measurement.** One helper per image gives `(minimum, label_a,
  label_b)`. It runs `compute_centroid` over every non-zero label and takes
  `min` over `itertools.combinations` of `math.dist`.
- **Gating (AC3, AC4).** A local `real_verse19_root()` returns the root only
  when A5's conditions hold. The helper is copied, as tests 084, 088, 091,
  118 and 125 each copy theirs, and is not imported from a stage-validation
  module. A `requires_verse19` `skipif` mark applies it.
- **Shared VerSe19 fixture.** One module-scoped fixture computes the
  per-mask results once for AC3 and AC4. It loads each mask with
  `nibabel.load` and wraps the array in an in-memory `Nifti1Image` with the
  original affine and header, so each mask is decompressed once (A7).
- **Text sites.** The AST read of the constant's docstring parses
  `collapsed_labels.__file__`. The `default_config.yaml` text is read with
  `read_text(encoding="utf-8")`.
- Every AC test asserts its precondition first: the measured minimum is a
  finite positive number, and AC5's control finding exists.

Adversarial cases (exactly these):

- `cocc-flank-excluded`: AC5's copy with label 23's `level_name` set to
  `"Cocc"` gives no `missing_level` finding. This guards a predicate that
  covers `S*` and not the coccyx.
- `upper-flank-excluded`: AC5's copy with label 21's `level_name` set to
  `"S1"`, and label 23 left as it is, gives no `missing_level` finding. This
  guards an exclusion that checks only the caudal flank.
- `l6-flank-still-judged`: AC5's copy with label 23's `level_name` set to
  `"L6"` still gives the `missing_level` finding on `{21, 23}`. This guards
  an over-broad exclusion that treats label 25 or `L6` as sacral (A4).
- `verse19-root-without-splits-skips`: with `SEGFACET_VERSE_COHORT`
  monkeypatched to a `tmp_path` directory holding only
  `dataset-verse19training/`, `real_verse19_root()` returns `None`. This
  guards the training-only value of insight `2026-10-17-e94a`, which would
  otherwise run AC3/AC4 on 80 masks and fail rather than skip.

**Existing tests to reconcile: none.** A grep of `tests/` for
`CentroidSpacingRule`, `centroid_spacing`, `Missing level` and sacral level
names finds no test that expects a `missing_level` finding beside a sacral
or coccygeal label. Every corpus case and severity-ladder spine is lumbar
only. Three existing tests must stay green unchanged:
`tests/test_207_fused_label_rule.py::test_sacral_label_not_judged` (the
refactored `fused_label` predicate), `tests/test_218_centroid_spacing_rule.py`
AC1, and `tests/test_163_specificity_ratchet.py` AC2 (every corpus case's
measured firing equals its expected set).

## Validation

1. **Run the gated tests on the cohort.** Where the VerSe19 three-split root
   is available (A5's per-machine note), run:

   ```
   SEGFACET_VERSE_COHORT=<VerSe19 root> .venv/bin/python -m pytest tests/test_240_verse19_probes.py -rs
   ```

   - AC3 and AC4 must **run and pass**. A skip is not a pass. Read the `-rs`
     summary.
   - Record the commit, the measured minimum and the mask count under
     Decisions & Trade-offs.
   - Where the root is absent, record **❓ Unverified (VerSe19 not
     mounted)**, never a pass.
2. **Replay `missing_level` on VerSe19 with the rule itself** (A2, A6). For
   every mask from step 1 with two or more labels:
   - run `extract_feature_record` with `bundled_default_config()` (a
     process pool is fine);
   - count the `centroid_spacing` findings whose `detector_id` is
     `missing_level`, both from `CentroidSpacingRule().evaluate` and after
     `run_rules`;
   - record both counts, the largest gap ratio, and how many masks carry
     label 26 or 27, with the commit.

   Expected: 0, 0, 1.378, 0. A non-zero count is a false positive on clean
   ground truth, and is handed back. Where the root is absent, record
   **❓ Unverified (VerSe19 not mounted)**.

## Dependencies

- Item 218: the `centroid_spacing` rule and its `missing_level` detector,
  which step 1 edits (✅).
- Item 220: the `collapsed_labels` citations that AC1–AC4 pin (✅).

## Decisions & Trade-offs

To be updated during implementation.

- **Left open:** Whether the sacral and coccygeal exclusion costs real
  sensitivity: a missed L5 between L4 and S1 is no longer reported by
  `missing_level`. No cohort this item can read has a sacral label (A2). It
  is measured where Stage 16 scores the rule on real segmenter output.
- **Left open:** A spacing beside a sacral gap still serves as a baseline
  for its neighbouring lumbar gap. A long L5–sacrum spacing therefore makes
  the L4–L5 gap read smaller, which lowers sensitivity there and adds no
  false positive. Changing that needs a sacral-labelled cohort to measure
  against.
