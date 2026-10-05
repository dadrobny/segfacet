<!-- aide-template: item 3 -->
# Item 211 — `fused_label` judges the pair of adjacent spacings together

> **Created:** 2026-10-03 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 27 — Feature Schema Taxonomy & Coordinate System (maintenance deliverable)
> **Queue:** [`../queue/queue-028.md`](../queue/queue-028.md) · Item 211
> **Objectives:** G2
> **Suggested branch:** `aide/211-fused-label-spacing-pair`

---

## Description

`fused_label` (item 207, `src/segfacet/heuristics/fused_label.py`) is mode 2's
own detector. It fires on a label that is both large against its adjacent
labels (`size_ratio`) and flanked by wide centroid spacing (`spacing_ratio`).
Today `spacing_ratio` is the **smaller** of the label's adjacent spacings
over the median of the case's other spacings. That has two defects, and this
item fixes both.

**1. The spacing gate reads each side alone (insight 2026-10-02-5d97,
maintainer feedback at the `gate-0133` sign-off).** A fused label adds about
one vertebra's pitch of extra distance between its two neighbours' centroids.
Where its own centroid sits decides how that extra distance is split between
its two adjacent spacings. The split depends on the centroid convention:
whole label or body only, or another segmenter's convention. With the
centroid midway, both spacings read about 1.5 times the pitch, as on the
synthetic corpus. With the centroid on one of the two bodies, one spacing
reads normal and the other doubled, and today's `min` reads 1.0 and stays
silent. The sum of the two spacings is the same in every case. So the gate
judges the pair together: `spacing_ratio` becomes the **mean** of the
adjacent spacings over the baseline median, which is their sum over twice the
baseline for an interior label. The threshold stays 1.25, halfway between a
normal pair (mean 1.0) and a fused one (mean 1.5).

**2. A non-integer `per_label` key raises (insight 2026-09-30-5763).**
`evaluate` orders `per_label` keys with `sorted(..., key=int)`. Once the
`stage3` and spacing-count guards pass, a non-integer key raises `ValueError`.
The module docstring says a malformed record is not judged. It now returns
`[]`.

**Not in scope.**

- No other rule, feature, fixture, threshold value or parameter name. The
  size gate, A3 (end labels), A4 (sacral and coccygeal labels) and adjacency
  by ascending integer label are unchanged.
- No corpus case fires differently (A2). No `Expectation`, manifest entry or
  expected set moves.
- `MODE_SIGN_OFFS` is not touched (A5).
- The detector's `question`, `fires_when` and `params` strings are unchanged,
  so `docs/aide/rules.generated.md` does not move (A4).

## Acceptance Criteria

Terms used below:

- **"The fuse_separate record"** is
  `segfacet.pipeline.extract_feature_record(segfacet.synth.regression.loaded_seg_image(case), segfacet.config.bundled_default_config())`
  for the `case` in `segfacet.synth.corpus.load_manifest()["cases"]` whose
  `case_id == "fuse_separate"`. Its labels are 20–23, and label 22 (index 2)
  is the fused label, so its adjacent spacings are `spacings_mm[1]` and
  `spacings_mm[2]`, and its baseline is `spacings_mm[0]` alone.
- **"Evaluate"** is `FusedLabelRule().evaluate(record, bundled_default_config())`.

- [ ] **AC1: one normal and one doubled adjacent spacing fires.** On a deep
  copy of the fuse_separate record with
  `stage3.spacing_consistency.spacings_mm[1]` set to `spacings_mm[0]` and
  `spacings_mm[2]` set to `2 * spacings_mm[0]`, evaluate returns exactly one
  finding, and its `labels == frozenset({22})`.
- [ ] **AC2: a non-integer `per_label` key is not judged.** On a deep copy of
  the fuse_separate record with the entry under key `"20"` moved to key
  `"x"`, evaluate returns `[]` and raises nothing.

Why each is written:

- AC1 is the queue's "a large label with one normal and one doubled adjacent
  spacing fires". Measured 2026-10-03, today's code returns `[]` on that
  record (A1), so the test fails before the change. The size gate is not
  touched: label 22 reads size 2.0016 on the unmodified record.
- AC2 is the queue's "a record with a non-integer `per_label` key returns no
  finding and does not raise". Measured 2026-10-03, today's code raises
  `ValueError: invalid literal for int() with base 10: 'x'`.

Not written, because something already fails without them:

- "The detector still fires on `fuse_adjacent` and `fuse_separate` and on
  nothing else in either corpus":
  `tests/test_207_fused_label_rule.py::test_ac1_fused_label_fires_on_the_two_fused_labels_and_nowhere_else`
  asserts exactly that triple set over both corpora, and stays unedited.
  `tests/test_163_specificity_ratchet.py` and the expected-set tests that
  item 207's spec lists also fail on any changed firing.
- "Mode 2 still meets bar conditions 1–5 live":
  `tests/test_167_mode_3_detector.py::test_ac11_mode_2_meets_all_five_bar_conditions`
  and `tests/test_187_neighbour_contact_rule.py::test_ac13_mode_2_meets_all_five_bar_conditions`
  assert it, and stay unedited.
- A fused end label still fires:
  `tests/test_207_fused_label_rule.py::test_caudal_end_fuse_fires` (an end
  label has one adjacent spacing, and the mean of one value is that value).
- The committed failure-mode and traceability documents agree with the
  source: `tests/test_144_failure_mode_specification.py`,
  `tests/test_150_maintainer_sign_off.py`'s AC12 and
  `tests/test_138_traceability_matrix.py` compare them with a fresh render.

No AC closes a Stage 27 acceptance criterion. This is a maintenance item.

## Assumptions

`loop.clarify = "assume"` in `aide.toml`, vision posture `prototype`. This
spec was briefed as interactive, with the human unreachable, so each open
decision takes a default, recorded here, and the three closest calls are
returned as questions. Every value was measured on `aide/queue-028` on
2026-10-03 with `.venv/bin/python`. Scratch probes computed each label's
`size_ratio` and both spacing statistics from `extract_feature_record`, using
item 207's A1–A4 exactly, over every case of both corpora, every rung of
`SEVERITY_LADDERS` and `SUPPLEMENTARY_LADDERS`, and all registered operators
at seeds 0–5 on `build_clean_spine(spacing=(1,1,1))` and `(1,1,3)`. The
builder re-measures on the real change.

- **A1 (decided: the pair statistic).** `spacing_ratio` is
  `statistics.mean(adjacent spacings) / median(non-adjacent spacings)`. For
  an interior label that is (sum of its two spacings) / (2 × baseline). It
  does not depend on how the extra distance is split. For an end label it is
  its one spacing over the baseline, as today. Fire when
  `size_ratio > size_ratio_threshold` and `spacing_ratio > spacing_ratio_threshold`,
  both strictly, with defaults 1.5 and 1.25, unchanged. Measured on the
  fuse_separate record with its pair sum held at 3 × the baseline: split 1:2,
  1.5:1.5 and 2:1, the mean reads 1.5 and fires each time, while today's
  `min` fires only on 1.5:1.5. With the pair sum at 2 × the baseline (a
  normal pair), split 2/3:4/3 and 4/3:2/3, the mean reads 1.0 and is silent.
  A `max` statistic would fire on both of those, so `max` was rejected.
  *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50 (item 207
  merged): agrees.* `FusedLabelRule.evaluate` still computes
  `spacing_ratio = min(adj_sp) / base_med` and fires on
  `size_ratio > size_thr and spacing_ratio > spacing_thr`, with
  `DEFAULT_SIZE_RATIO = 1.5` and `DEFAULT_SPACING_RATIO = 1.25` read through
  `config.rule_param`; `statistics` is imported. `fused_label.py` is
  unchanged since this spec was written (687eb15).
- **A2 (measured: what fires does not change).** Over both corpora the mean
  fires on exactly the labels `min` fires on: `fuse_adjacent` label 22 (size
  2.3248, spacing min 1.4782 → mean 1.5380 from `[33.49, 49.51, 53.52]`) and
  `fuse_separate` label 22 (2.0016, 1.4768 → 1.5371 from
  `[33.49, 49.46, 53.50]`). The same holds on every ladder rung (the
  supplementary `fuse` ladder's rungs 1 and 2, label 20, means 1.3956 and
  1.8026, end labels) and for every operator, seed and spacing (only
  `FusePerturbation` fires, means 1.3546–1.5703). No other registered
  operator fires at either spacing.
  - Silent labels with size above 1.5 (the size gate passes): `split_own_label`
    label 24 (size 4.8000, mean 0.8885) and `split` label 24 (1.5263,
    1.0512). Both are end labels, so their reading is unchanged. On the
    `split` ladder rungs 3 and 4, label 24 reads size 2.0072 and 2.4475 at
    means 1.0219 and 1.0050.
  - **Margin traded (decided).** Under `min`, the spacing gate alone kept
    labels beside a missed level silent. Under the mean, labels at normal
    size pass the spacing gate, and the size gate alone keeps them silent:
    `remove_level` / `remove_level_relabel` label L4/22 (size 0.9984,
    mean 1.5408, min 1.0999), L2/21 (0.9968, 1.3555), the `relabel_swap`
    ladder rung 1 labels 21–22 (1.0000, 1.4070 and 1.4200), and the
    `split_own_label` ladder rung 1 label 23 (0.9952, 1.5549, min 1.4897). The
    highest silent mean is 1.7915 (`relabel_swap` label 20, size 1.0000,
    end label, unchanged). This is the conjunction item 207 designed:
    neither signal decides alone.
  - *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50 (items 207
    and 210 merged): the firing claim agrees; the "Margin traded" list is
    corrected.* Re-measured with `.venv/bin/python` over both corpora and
    every rung of `SEVERITY_LADDERS` and `SUPPLEMENTARY_LADDERS`, reading
    the record exactly as `FusedLabelRule.evaluate` does.
    - **Agrees.** Every spacing list, size and ratio quoted above
      re-measures to the same four decimals (fuse_adjacent 2.3248 /
      1.4782 → 1.5380, fuse_separate 2.0016 / 1.4768 → 1.5371, the `fuse`
      ladder's 1.3956 and 1.8026, the `split` and `split_own_label`
      readings, and every "Margin traded" reading listed). The rule as
      merged fires on exactly fuse_adjacent label 22, fuse_separate label
      22 and `fuse` ladder rungs 1–2 label 20, and the mean fires on the
      same set on every case and rung. Item 210 does not move this:
      `fused_label` reads no `monotonic_consistency` field, and item 210's
      diff to `features/consistency.py` touches only the monotonic half,
      so `spacings_mm` and the volumes are unchanged. The registered-
      operator sweep was not re-run, for the same reason: nothing it reads
      has changed since 2026-10-03.
    - **Correction 1: the traded list is incomplete.** Four more interior
      labels at normal size pass the mean's spacing gate where `min` did
      not, all on ladder rungs, and the size gate alone keeps them silent:
      the `remove_level` ladder rung 1 label 22 (size 1.0000, mean 1.3555,
      min 0.9194), the `relabel_swap` ladder rung 2 labels 21 (1.0032,
      1.2755, min 0.6435) and 22 (0.9952, 1.2838, min 0.6531), and the
      `split_own_label` ladder rung 2 label 20 (0.9968, 1.2969, min
      1.2239). The smallest size margin among all traded labels is
      therefore 0.4968 (`relabel_swap` rung 2 label 21, size 1.0032), not
      the 0.50 at size 0.9984 that Decisions & Trade-offs quotes.
    - **Correction 2: "the highest silent mean is 1.7915" holds over the
      two corpora only.** On the ladders, end labels at normal size read
      higher: 2.6952 (`remove_level` rung 2 label 20, size 1.0048), 2.0735
      (`relabel_swap` rung 2 label 24, size 0.9952) and 1.8667
      (`remove_level` rung 1 label 20, size 1.0000). An end label has one
      adjacent spacing, so `min` and the mean read the same and nothing
      fires differently. The highest silent **interior** mean anywhere
      measured is 1.5549 (`split_own_label` rung 1 label 23). The
      Decisions & Trade-offs bullet naming `relabel_swap` label 20 as "the
      highest-spacing silent label at normal size" has the same corpus-only
      scope.
    - **Clarification.** "L4/22" names level L4: it is label 23 on
      `remove_level` (no renumbering) and label 22 on
      `remove_level_relabel`. `missing-vertebra-not-fused` reads
      `remove_level_relabel` label 22, whose readings (spacings
      `[33.49, 66.38, 36.84]`, size 0.9984, mean 1.5408) re-measure as
      stated.
- **A3 (decided: the malformed-key guard).** The `sorted(..., key=int)`
  call is wrapped so that `TypeError` or `ValueError` returns `[]`. A `None`
  key raises `TypeError` and a non-numeric string raises `ValueError`, and
  neither is judged. The guard sits where the sort is, after the existing
  `stage3` and spacing-count guards, so every record that returns `[]` today
  still returns `[]`.
  *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50: agrees.*
  `keys = sorted(per_label.keys(), key=int)` still follows the `stage3`,
  `spacing_consistency`, numeric-spacings and `len(spacings) !=
  len(per_label) - 1` guards. On the fuse_separate record the merged code
  raises `ValueError` for key `"x"` and `TypeError` for key `None`, and
  returns `[]` on the AC1 construction, so AC1, AC2 and
  `none-key-not-judged` each fail before the change.
- **A4 (decided: what the change touches in text).**
  - The finding's reason says the label's adjacent centroid spacings average
    the ratio over the case's other spacings, not "its smaller adjacent
    centroid spacing".
  - The module docstring's A2 bullet, its measured block (A7 there), the
    class docstring and `DEFAULT_SPACING_RATIO`'s docstring give the mean
    and the A2 readings above.
  - The `mode_declaration` evidence string quotes the new spacing readings,
    1.5380 and 1.5371. It is rendered into
    `docs/aide/traceability_matrix.generated.*`.
  - The `RuleDetector`'s `question`, `fires_when` and `params` are not
    changed. "Flanked by wide centroid spacing" and
    "`spacing_ratio` > `spacing_ratio_threshold`" still hold, so
    `docs/aide/rules.generated.md` does not move.
  - In `failure_modes.py`, mode 2's `mechanism` replaces "the smaller spacing
    adjacent to the label over the median of the other spacings, about 1.5x,
    because the fused centroid falls between its two bodies". The new text
    says it is the mean of the label's adjacent spacings over the median of
    the other spacings, about 1.5x, whichever side the fused centroid falls
    on. Its other sentences stay, including "split reads size 1.53 at
    spacing 1.05", which is still true.
  - The `fuse_adjacent` and `fuse_separate` `reason` strings quote the mean
    readings, with a re-measurement date and item 211. Their
    `expected_firing` is unchanged.
  - `default_config.yaml`'s commented `fused_label` block describes the mean,
    and its "about 1.48-1.57" becomes the new range, about 1.35-1.80. That
    range is the fused readings measured in A2 across the corpus, the ladders
    and the operators: 1.3546 to 1.8026.
  - *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50: agrees.*
    Every quoted text is present as described: the reason's "smaller
    adjacent centroid spacing", the module docstring's A2 bullet and A7
    measured block, the class docstring, `DEFAULT_SPACING_RATIO`'s
    docstring, the `mode_declaration` evidence (1.4782 / 1.4768), the
    unchanged `RuleDetector` strings, `_MODE_2`'s mechanism clause (with
    "split reads size 1.53 at spacing 1.05"), both fuse cases' reasons
    and `default_config.yaml`'s "about 1.48-1.57". Item 210 changed
    `failure_modes.py` in `_MODE_9`'s `sequence_break` reason only, and
    regenerated `failure_modes.generated.json` for it, so step 5
    regenerates on top of that and `_MODE_2` is untouched.
- **A5 (decided: mode 2's at-the-bar sign-off stands).** `gate-0133` signed
  mode 2 at the bar on 2026-10-02. `MODE_SIGN_OFFS[2].note` records this
  feedback as non-blocking. The firing set over both corpora is unchanged
  (A2), and bar conditions 1–5 still hold (the two tests named above stay
  green). Condition 6 reads the record's `outcome`, and no digest of the mode
  text exists to invalidate it. So no human gate is raised and
  `MODE_SIGN_OFFS` is not touched. This is returned to the human as
  question 3.
  *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50: agrees.*
  `MODE_SIGN_OFFS[2]` reads `outcome="at-the-bar"`, dated 2026-10-02, with
  the note naming "fused_label's centroid-spacing judgement" as
  non-blocking feedback. `traceability.bar_conditions(2)` reads all five
  met live, and condition 4's subjects are
  `("fused_label/fused_label", "neighbour_contact/stray_contact")`.
- **A6 (decided: end labels).** An end label is judged on its one spacing,
  as today. A fused end label whose centroid falls on its inner body reads a
  normal inner spacing, because the extra distance lies beyond the end of
  the measured spacings, and it is missed. Recorded under Decisions as
  Left open. Judging an end label on size alone was rejected: `split_own_label`
  label 24 (size 4.80) and the `split` ladder's label 24 (up to 2.45) are end
  labels at normal spacing and would fire.
  *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50: agrees.* The
  merged loop forms `adj_sp` from `(i - 1, i)` within range, so an end label
  has one adjacent spacing, and a label with no non-adjacent spacing is
  skipped (`fuse` ladder rung 3 reads no finding). `split_own_label` label
  24 (4.8000) and the `split` ladder's label 24 (2.0072, 2.4475) re-measure
  as stated.
- **A7: no human gate, no environment-gated capability, and no interface a
  queue-028 sibling reads.** Items 210 and 212 re-measure both corpora's
  expected sets. This item moves none of them (A2), so either can land first.
  *Re-checked 2026-10-05 against `aide/queue-028` at 7949f50 (item 210
  merged): agrees.* Item 210 replaced the monotonicity reference with a
  label-free path and re-measured `sequence_break`'s `mislabel` pairs (one
  reason string in `_MODE_9`). It touched none of `fused_label.py`, the spacing half of
  `features/consistency.py`, `_MODE_2`, `default_config.yaml` or the
  traceability matrix. The `fused_label` firing set over both corpora is
  unchanged on the merged base (A2's re-check). Item 212 is still to land.

## Implementation Steps

1. **`src/segfacet/heuristics/fused_label.py`, `FusedLabelRule.evaluate`.**
   - Wrap `keys = sorted(per_label.keys(), key=int)` in
     `try` / `except (TypeError, ValueError): return []` (A3).
   - Replace `spacing_ratio = min(adj_sp) / base_med` with
     `statistics.mean(adj_sp) / base_med` (A1). `statistics` is already
     imported. No other line of the loop changes.
   - Reword the finding's reason (A4).
2. **The same module's text** (A4): the module docstring's A2 bullet and the
   "Absence-tolerant" bullet, which gains the non-integer key. Its measured
   block gets the A2 readings, re-dated with item 211. Also the class
   docstring, `DEFAULT_SPACING_RATIO`'s docstring and the `mode_declaration`
   evidence string. Leave the `RuleDetector` strings unchanged.
3. **`src/segfacet/failure_modes.py`, `_MODE_2` only** (A4): the one
   mechanism clause and the two fuse cases' `reason` strings. Keep the
   whole-word case ids and both dotted signal paths in the mechanism
   (`tests/test_138_traceability_matrix.py` AC31). No other mode, no
   `expected_firing` and no `MODE_SIGN_OFFS` change.
4. **`src/segfacet/default_config.yaml`**: the commented `fused_label` block's
   spacing comment only (A4). It stays commented, because an active section
   would move `config_hash`.
5. **Regenerate.** Run each generator twice into scratch paths and
   byte-compare the two runs, then once to write the committed copies:
   `.venv/bin/python -m segfacet.failure_modes` and
   `.venv/bin/python -m segfacet.traceability`. Then confirm that a fresh
   render of each of these matches its committed copy byte for byte, and
   hand back if one does not: `python -m segfacet.rule_table`,
   `python -m segfacet.catalogue`, `python -m segfacet.synth.corpus` (no
   manifest or fixture change) and `python -m segfacet.golden_evidence`.
6. Run `python .aide/scripts/aide.py scope 211` and
   `python .aide/scripts/aide.py check`. Neither may report an error.

No dependency is added. No existing helper is re-implemented: the record is
read exactly as today.

## Authorised paths

**May change:**

- `src/segfacet/heuristics/fused_label.py` — the statistic, the key guard, the reason, docstrings and evidence (steps 1–2).
- `src/segfacet/failure_modes.py` — mode 2's mechanism clause and two case reasons (step 3).
- `src/segfacet/default_config.yaml` — one comment in the commented `fused_label` block (step 4).
- `docs/aide/failure_modes.generated.json` — regenerated (step 5).
- `docs/aide/failure_modes.generated.md` — rendering of the same.
- `docs/aide/traceability_matrix.generated.json` — regenerated; mode 2's mechanism and the rule's evidence (step 5).
- `docs/aide/traceability_matrix.generated.md` — rendering of the same.
- `tests/test_211_fused_label_spacing_pair.py` — **new**: this item's test module.

**Asserts against:**

- `tests/corpus/fixtures/fuse_separate_seg.nii.gz` — AC1, AC2, `split-proportion-invariant` and `none-key-not-judged` build their record from it.
- `tests/corpus/fixtures/remove_level_relabel_seg.nii.gz` — `missing-vertebra-not-fused` builds its record from it.
- `tests/test_207_fused_label_rule.py` — must stay green unedited; its AC1 is the queue's "fires on both fuse cases and nothing else in either corpus", and `test_caudal_end_fuse_fires` holds A6.
- `tests/test_167_mode_3_detector.py` — must stay green unedited; its AC11 is mode 2's bar conditions 1–5.
- `tests/test_187_neighbour_contact_rule.py` — must stay green unedited; its AC13 is the same, and AC14 pins mode 2's condition-4 subjects.

`tests/corpus/manifest.json` is read through `load_manifest()` for
`fuse_separate`'s entry only, and is listed under neither heading. Item 212
regenerates it for `crop_at_border`, an entry this item does not read.
`docs/aide/rules.generated.md`, the feature catalogue and
`golden_evidence.generated.json` must not move (step 5). Their existing tests
(`test_202`, `test_103`/`test_104`, `test_134`) guard that. This item's tests
do not read them, and siblings 210 and 212 may legitimately regenerate them.

## Testing Strategy

The test module is `tests/test_211_fused_label_spacing_pair.py`, with one
test per AC. Each test builds its record from a committed corpus case
through `extract_feature_record` and edits a `copy.deepcopy` of it, never a
hand-built record. Every test uses `fuse_separate` except
`missing-vertebra-not-fused`, which uses `remove_level_relabel`. The AC1 test also asserts that the unmodified record
gives one finding on label 22, so the control is not vacuous.

Adversarial cases, each with the failure mode it guards, and no others:

- `split-proportion-invariant`: on the fuse_separate record, with label 22's
  pair (`spacings_mm[1]`, `spacings_mm[2]`) set to `(a·p, b·p)` where
  `p = spacings_mm[0]`, evaluate gives exactly one finding on label 22 for
  `(a, b)` in `(1, 2)`, `(1.5, 1.5)` and `(2, 1)`. It gives `[]` for
  `(2/3, 4/3)` and `(4/3, 2/3)` (a normal pair sum). It guards a statistic
  that weighs the two sides unequally: one side only, which fails the
  mirrored `(2, 1)`, and `max`, which fires on the normal-sum splits (A1).
- `missing-vertebra-not-fused`: the committed `remove_level_relabel` record
  (mode 6, L3 deleted and the caudal labels renumbered; built through
  `extract_feature_record(loaded_seg_image(case))`, spacings
  `[33.49, 66.38, 36.84]`) is used twice. As it stands, label 22 has a
  normal size (0.9984) and one doubled adjacent spacing (mean 1.5408), and
  evaluate gives `[]`. In a deep copy with label 22's pair set to
  `(2·p, 2·p)` (`p = spacings_mm[0]`, both sides widened, mean 2.0), evaluate
  gives `[]` again. To show the spacing gate passes and the size gate is the
  one rejecting, the test also runs both records under a config with
  `rules.fused_label.params.size_ratio_threshold = 0.9`, built the way
  `test_207`'s `size-threshold-read-from-own-section` builds its config.
  That run must give a finding whose `labels` include 22. It guards the
  maintainer's 2026-10-05 constraint: the detector must stay spacing AND
  larger volume combined, because the pair statistic alone fires on a
  missing vertebra (mode 6) or a skipped label (mode 10) just as it does on
  a fused one. A change that dropped or weakened the size gate fails it.
- `none-key-not-judged`: the AC2 construction with key `None` instead of
  `"x"` gives `[]` and raises nothing. It guards a guard that catches
  `ValueError` only, because `int(None)` raises `TypeError` (A3).

**Existing tests to reconcile.** None. Found 2026-10-03 by grepping
`tests/` for `fused_label`, `spacing_ratio`, `spacings_mm`, "smaller
adjacent" and the old readings 1.4782 / 1.4768. Every test that runs the
rule either reads firing sets, which do not move (A2), or builds records
without `stage3.spacing_consistency.spacings_mm`, which return `[]` before the
changed lines (item 207's spec, "Checked and unaffected"). The `fused_label`
thresholds, parameter names and enablement are unchanged.

Red until step 5's regeneration lands, with no test edit: the comparisons of
the committed failure-mode and traceability documents with a fresh render,
in `tests/test_144_failure_mode_specification.py`,
`tests/test_145_eight_hypothesised_modes.py`,
`tests/test_146_ninth_mode_and_first_proposed.py`,
`tests/test_147_specification_is_the_record.py`,
`tests/test_149_conformance_report.py`,
`tests/test_150_maintainer_sign_off.py` (AC12),
`tests/test_138_traceability_matrix.py`, `tests/test_143_s_axis_correction.py`,
`tests/test_148_per_path_mode_attribution.py`,
`tests/test_151_stage30_validation.py`, `tests/test_157_case_id_rename.py`,
`tests/test_164_detector_ids.py` and `tests/test_179_status_report_corpus.py`.

Stale prose that asserts nothing is left alone:
`tests/test_040_synthetic_corpus.py` L508's docstring quotes "spacing
1.4782".

## Validation

1. Replay both fuse cases through the CLI:

   ```
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_adjacent_seg.nii.gz --out <tmp1> --no-reference
   .venv/bin/segfacet run --scan tests/corpus/fixtures/base_scan.nii.gz --seg tests/corpus/fixtures/fuse_separate_seg.nii.gz --out <tmp2> --no-reference
   ```

   `--no-reference` is needed for the reason `CLAUDE.md` gives. Each
   `segfacet_report.json` holds the same findings and verdict as before the
   change (`fused_label` on label 22, plus `fragmentation` on `<tmp2>`). The
   `fused_label` reason gives the mean spacing ratio, 1.538 and 1.537.
2. Read `docs/aide/failure_modes.generated.md`'s mode 2 section. The
   mechanism describes the mean of the adjacent spacings, and both fuse
   cases' reasons quote 1.5380 and 1.5371.

No environment profile is needed.

## Dependencies

- Item 207: the `fused_label` rule this item changes (✅).

**Downstream:** items 210 and 212 re-measure both corpora's expected sets.
This item moves none of them, so their order relative to this item is free.

## Decisions & Trade-offs

Implementation (2026-10-05): built as specified, no deviation. `spacing_ratio`
is `statistics.mean(adj_sp) / base_med`, the `sorted(..., key=int)` call is
guarded for `TypeError`/`ValueError`, and the reason, docstrings, evidence,
mode 2's mechanism clause, both fuse reasons and the `default_config.yaml`
comment (about 1.35-1.80) quote the mean. `failure_modes` and `traceability`
were each run twice into scratch paths and byte-compared (identical) before
the committed copies were written. `rule_table` and `golden_evidence` renders
left the tree unchanged. Note for readers: the "Margin traded" figures below
are corrected by the A2 re-check (smallest size margin 0.4968, highest silent
interior mean 1.5549).

Recorded at spec time (maintainer answers, 2026-10-05). The three open
questions, the pair statistic, end labels and the sign-off, were answered
as A1, A6 and A5 propose: the mean at 1.25, end labels unchanged, and no
re-sign gate.

- **The size gate is now the sole discriminator against a missing vertebra
  or a skipped label.** The maintainer's constraint is that the detector
  stays spacing AND larger volume combined. A missing vertebra (mode 6) or a
  skipped label (mode 10) widens the pair of spacings around its neighbour
  just as a fused label does, so the mean reads as wide on both. Under the
  old `min`, a one-sided gap also failed the spacing gate. Under the mean it
  passes, and only `size_ratio > 1.5` keeps the label silent. Margins
  measured 2026-10-03:
  - On `remove_level` and `remove_level_relabel`, label L4 (22) reads size
    0.9984 against the 1.5 threshold, a margin of 0.50, at spacing mean
    1.5408 (old min 1.0999). L2 (21) reads size 0.9968 at mean 1.3555.
  - On a copy of `remove_level_relabel` with both of label 22's sides
    widened to 2 × the pitch, it reads size 0.9984 at mean 2.0.
  - The highest-spacing silent label at normal size is `relabel_swap` label
    20: size 1.0000, mean 1.7915.
  - `missing-vertebra-not-fused` pins the constraint. Any future change to
    the size gate, its threshold or its "larger neighbour" baseline moves
    this margin, and must re-measure it.
- **Left open:** a fused **end** label whose centroid convention puts its
  centroid on the inner body reads a normal spacing and is missed (A6). The
  extra distance lies beyond the last measured spacing, so a centroid
  statistic cannot recover it. A fix needs another signal (an expected-length
  or reference-pitch feature), which is not this rule's scope.
- **Left open:** whole-label against body-only centroids is argued, not
  measured. The synthetic corpus labels bodies only. A1's
  proportion-invariance is the property that makes the convention not
  matter, and a real cohort (Stage 21) is where it can be measured.
