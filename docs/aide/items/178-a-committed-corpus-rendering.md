<!-- aide-template: item 2 -->
# Item 178 — A committed corpus rendering

> **Created:** 2026-09-24 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 33 — Corpus & Rule Re-grounding: modes 3 and 4 to the bar
> **Queue:** [`../queue/queue-023.md`](../queue/queue-023.md) · Item 178
> **Objectives:** G2, G7
> **Suggested branch:** `aide/178-a-committed-corpus-rendering`

---

## Description

One committed image, `docs/aide/corpus_sheet.png`, shows every case of the
geometric corpus (`tests/corpus/manifest.json`, 14 cases on 2026-09-24) as
a pair of panels: a sagittal and a coronal max-label projection. Voxels that
differ from `clean_control` are outlined in red. The sheet is regenerated from
the committed manifest by `python -m segfacet.synth.corpus_sheet`. The origin
is the `insights.md` entry of 2026-09-21 (queue-022), ticked into roadmap
Stage 33 D1. The sheet is one of the inputs to Stage 33's D5 sign-off gate.

The generator absorbs
`scripts/prototypes/2026-09-22-lordotic-corpus/corpus_sheet.py`, with two
defects fixed. Both were measured on 2026-09-24:

- **The prototype's grid is fixed at 4 × 6 axes**, which holds 12 cases. On
  today's 14 cases it raises `IndexError: index 4 is out of bounds for axis 0
  with size 4` at the 13th case. The new layout is computed from the case
  count.
- **The prototype blanks the outline of a case on a different grid.** It uses
  `np.zeros(seg.shape, bool)` when the shapes differ. `crop_fov_si` (item 175)
  is `(61, 86, 158)` with origin z = 35 mm, against clean_control's
  `(61, 86, 193)` at origin 0. The new generator places such a case on
  clean_control's grid at the integral voxel offset its affine gives, with
  background outside its field of view, and then compares. Measured this way,
  `crop_fov_si` differs in 12 586 voxels, the removed part of L5.

This is the last item that draws on the prototype directory, so it deletes the
directory. Everything else in it has already been absorbed (A5).

**PNG bytes are not compared.** matplotlib's PNG output depends on the
matplotlib, FreeType and zlib versions, so the bytes are not reproducible
across platforms. Two things are compared instead:

- **The panel data**: projections and changed-voxel masks. This is pure NumPy
  and is checked against the fixtures (AC1–AC4).
- **An input digest** stored in the PNG's `Source` text chunk. The committed
  sheet must carry the digest of the committed manifest and fixtures (AC7), so
  a corpus change that is not followed by a regeneration goes red.

**Not in scope:**

- the intensity corpus (`tests/corpus/intensity/manifest.json`), because the
  queue line names the geometric cases;
- the status report (item 179);
- any change to a corpus case, operator, rule or expected set;
- any re-export from `segfacet/synth/__init__.py`.

## Acceptance Criteria

- [ ] **AC1: one panel pair per case, in manifest order.**
  `[p.case_id for p in corpus_sheet.sheet_panels()]` equals
  `[c["case_id"] for c in load_manifest()["cases"]]`, read from the committed
  `tests/corpus/manifest.json`.
- [ ] **AC2: the panels are max-label projections on clean_control's grid.**
  For every manifest case, let `placed` be the case's seg-fixture array written
  into a zero array of clean_control's shape. It goes at the voxel offset
  `round(inv(clean.affine) @ case.affine[:, 3])[:3]`, which is `(0, 0, 0)` for
  a case on the same grid. The panel's `sagittal` then equals
  `placed.max(axis=0).T` and its `coronal` equals `placed.max(axis=1).T`
  (`np.array_equal`).
- [ ] **AC3: the outlines are the changed voxels.** For every manifest case,
  with `placed` as in AC2 and `clean` the clean_control fixture array, the
  panel's `sagittal_changed` equals `(placed != clean).any(axis=0).T` and its
  `coronal_changed` equals `(placed != clean).any(axis=1).T`
  (`np.array_equal`).
- [ ] **AC4: clean_control has no outline.** The `clean_control` panel's
  `sagittal_changed` and `coronal_changed` each hold no `True` value.
- [ ] **AC5: the sheet draws every panel.** The `Figure` that
  `corpus_sheet.render_sheet(out=<tmp>.png)` returns has exactly
  `2 * len(load_manifest()["cases"])` axes that hold an image
  (`len(ax.images) > 0`).
- [ ] **AC6: the sheet regenerates from the manifest.**
  `corpus_sheet.main(["--out", str(tmp_path / "sheet.png")])` returns `0`.
  The written file's PNG text chunk `Source` equals `"sha256:" + D`. `D` is
  the SHA-256 hex digest, which the test computes itself, of the committed
  manifest file's bytes followed by the bytes of each case's `seg_fixture`
  file in manifest order. Each `seg_fixture` path is resolved against the
  manifest's directory.
- [ ] **AC7: the committed sheet is current.** The PNG text chunk `Source` of
  the committed `docs/aide/corpus_sheet.png` equals `"sha256:" + D`, with `D`
  recomputed as in AC6 from the committed manifest and fixtures.
- [ ] **AC8: the prototype directory is gone.**
  `scripts/prototypes/2026-09-22-lordotic-corpus` does not exist in the
  working tree.
- [ ] **AC9: nothing imports from the prototype.** No `*.py` file under
  `src/`, `tests/` or `scripts/` holds an `ast.Import` or `ast.ImportFrom`
  node whose top-level module name is `lordotic_spine`, `corpus_v2`,
  `check_and_render` or `corpus_sheet`. `segfacet.synth.corpus_sheet` does not
  match, because its top-level name is `segfacet`.

None of these ACs closes a Stage 33 acceptance criterion.

## Assumptions

- **A1 (defensible default: the sheet's home and name).** The committed image
  is `docs/aide/corpus_sheet.png`, next to the generated documents the D5 gate
  also reads (`failure_modes.generated.md`, and later
  `rules.generated.md`). Two things rule out other names:
  - It deliberately has no `.generated.` infix.
    `tests/test_156_conformance_seams.py::test_ac11_no_complete_always_phrasing_in_source_or_generated_artifacts`
    globs `docs/aide/*.generated.*` and calls `read_text(encoding="utf-8")` on
    each hit. A PNG there raises `UnicodeDecodeError`.
  - It deliberately lives outside `tests/`, so the `tests/` non-`.py`
    inventory stays at 26. That inventory is pinned by `test_105` AC3,
    `test_126` and `test_134` AC18.
- **A2 (defensible default: the generator's home).** The generator is
  `src/segfacet/synth/corpus_sheet.py`. The prototype insight
  (`insights.md`, 2026-09-22) said "take what they need into
  `src/segfacet/synth/` (and the rendering into wherever the status report's
  corpus section is rebuilt)". Item 179's queue line does not embed the sheet.
  Every other committed-artifact generator is a `python -m segfacet.…`
  module: `synth.corpus`, `failure_modes` and `traceability`. So the sheet's
  generator sits beside the corpus it renders.
- **A3 (measured 2026-09-24: no new dependency).** matplotlib is in the `dev`
  extra (`matplotlib>=3.5`). It is also a transitive runtime dependency of
  `tptbox` (`constraints.txt`: `matplotlib==3.11.1`, `pillow==12.3.0`). Every
  CI job installs `.[dev]`. The import is deferred into `render_sheet`, as
  `features/sagittal_projection.py` already does, so importing the module
  costs nothing.
- **A4 (measured 2026-09-24: orientation).** Every committed geometric seg
  fixture is RAS (`nib.aff2axcodes`) on a 1 mm grid with an identity rotation
  block. So array axis 0 is L-R and a max over it is the sagittal view. Axis 1
  is P-A and a max over it is the coronal view. Axis 2 is I-S and is drawn
  upward (`origin="lower"`). The labels present across the corpus are
  19, 20, 21, 22, 23, 24 and 28.
- **A5 (measured 2026-09-24: nothing absorbed is still missing).**
  - `lordotic_spine.build` is in `synth/clean_gt.py` (item 173).
  - `corpus_v2.py`'s five local operators are registered in `synth/`:
    `split` and `split_own_label` in `component_shape.py` (item 174),
    `crop_fov` in `coverage_border_overlap.py` (item 175), bridged `fuse` in
    `component_shape.py` (item 176), and the lateral `displace` in
    `identity_ordering_alignment.py` (item 177).
  - `corpus_sheet.py` is absorbed by this item.
  - `check_and_render.py` is not absorbed, on purpose. Its pipeline check of
    a candidate base is now the specificity ratchet
    (`tests/test_163_specificity_ratchet.py`) and item 173's
    clean-control test. Its side-by-side rendering is superseded by the sheet.
  - The README's measurements are recorded in `insights.md` (2026-09-22) and
    in the specs of items 173–177.
  - A grep of `src/`, `tests/`, `scripts/`, `pyproject.toml`, `.gitattributes`,
    `.github/` and `README.md` finds the directory named only by its own files.
    The one import of it is `corpus_v2.py` importing `lordotic_spine`.
- **A6 (defensible default: what the digest covers).** The digest covers the
  sheet's inputs, meaning the manifest (case ids and title fields) and the
  seg-fixture bytes. It does not cover the rendering code. File bytes are
  stable:
  - `manifest.json` is pinned `text eol=lf` and `fixtures/*.nii.gz` is pinned
    `binary`;
  - `test_040`'s AC16 already requires a fresh corpus to equal the committed
    one byte for byte on every CI platform.

  A layout change that is not followed by a regeneration therefore stays
  green. This is accepted, because the layout does not change what the sheet
  claims.

## Implementation Steps

1. **New module `src/segfacet/synth/corpus_sheet.py`.** The module docstring
   records:
   - where it came from: the prototype path, now deleted;
   - the regeneration command;
   - why PNG bytes are not compared, and what is compared instead (A6).

   The docstring carries no `§6 mode N` phrasing, because `test_161`
   criterion 2 sweeps `src/**/*.py` for it. The module holds:
   - `SHEET_PATH = Path(__file__).resolve().parents[3] / "docs" / "aide" /
     "corpus_sheet.png"`.
   - A frozen dataclass `SheetPanel(case_id, sagittal, coronal,
     sagittal_changed, coronal_changed)`. The label projections are integer
     arrays and the changed-voxel masks are bool arrays, all already
     transposed for display (rows run I→S).
   - `sheet_panels(manifest_path=MANIFEST_PATH) -> list[SheetPanel]`:
     - Read the manifest with `segfacet.synth.corpus.load_manifest` and load
       each `seg_fixture` relative to `manifest_path.parent`.
     - Take clean_control as the manifest's `clean_control` case.
     - Place each case on clean_control's grid. First call
       `segfacet.synth.corpus.crop_to_grid(clean_img, case_img)` so a case
       that is not an integral sub-grid raises `FacetInputError` instead of
       rendering misaligned. Then write the case's array into a zero array of
       clean_control's shape at `start = round(inv(clean.affine) @
       case.affine[:, 3])[:3]`, which is `crop_to_grid`'s own formula.
     - Project and diff as AC2/AC3 state.
   - `input_digest(manifest_path=MANIFEST_PATH) -> str`: the hex digest AC6
     defines. Use one `hashlib.sha256()` fed with `update()`.
   - `render_sheet(out=SHEET_PATH, manifest_path=MANIFEST_PATH) -> Figure`:
     - Import `matplotlib.figure.Figure` inside the function. Use the
       object-oriented `Figure` API with no pyplot, so no global figure
       registry is kept.
     - Lay out 6 columns and `2 * ceil(N / 6)` rows, one row pair per six
       cases (sagittal row above coronal row).
     - Colour a voxel by its label **value**, from one fixed table shared by
       every panel (for example tab10 at `label % 10`, with background
       black). Then a relabel reads as a colour change. The prototype's
       per-run lookup table could not guarantee that.
     - Draw the red outline with `ax.contour(mask, levels=[0.5])`, and only
       where the mask holds any `True`.
     - Build each title from manifest fields only: `case_id`, `kind`,
       `failure_mode`, `condition` and `expected_rule_ids`. Write no
       mode-name or rung string literal in the source, because `test_147`
       AC1/AC2 sweep `src/**/*.py` string literals for them.
     - Turn unused axes off. Save with `fig.savefig(out, dpi=90,
       metadata={"Software": None, "Source": "sha256:" + input_digest(...)})`.
   - `main(argv=None) -> int` with one `--out` option (default `SHEET_PATH`),
     calling `render_sheet`. Plus `if __name__ == "__main__"`.

   No change to `synth/__init__.py`, `synth/corpus.py` or any operator.
2. **Regenerate the committed sheet** with
   `.venv/bin/python -m segfacet.synth.corpus_sheet`, and commit
   `docs/aide/corpus_sheet.png`.
3. **Pin it:** add `docs/aide/corpus_sheet.png binary` to `.gitattributes`,
   with a one-line comment naming item 178.
4. **Delete the prototype.** Run `git rm -r
   scripts/prototypes/2026-09-22-lordotic-corpus`. Then remove the directory
   from disk as well. On the authoring machine it still holds an untracked,
   gitignored `__pycache__/`, which would keep AC8 red locally. Also remove
   the `scripts/prototypes/` parent it leaves empty.

No dependency is added.

## Authorised paths

**May change:**

- `src/segfacet/synth/corpus_sheet.py` — **new**: the generator (step 1).
- `docs/aide/corpus_sheet.png` — **new**: the committed sheet (step 2).
- `.gitattributes` — the `binary` pin (step 3).
- `scripts/prototypes/2026-09-22-lordotic-corpus/**` — deleted (step 4).
- `tests/test_178_corpus_sheet.py` — **new**: this item's test module.

**Asserts against:**

- `tests/corpus/manifest.json` — AC1, AC5, AC6 and AC7 read its cases and bytes.
- `tests/corpus/fixtures/*.nii.gz` — AC2, AC3, AC4, AC6 and AC7 read the seg fixtures.
- `src/segfacet/synth/corpus.py` — `load_manifest`, `MANIFEST_PATH` and `crop_to_grid` are reused unchanged.

Some paths stay off **May change** on purpose, so `aide scope` refuses them:

- `tests/corpus/**`: the corpus is read, never regenerated here.
- `src/segfacet/synth/__init__.py`: no re-export (Description).

> **Amended 2026-09-24.** One entry was removed from the head of this list.
> As first written it read: "every other `tests/test_*.py`: the sweep below
> found nothing to reconcile. A red test elsewhere is a hand-back to
> spec-author, not an edit." `aide scope` reads every bullet after the
> **Asserts against:** label, including this list, as a pinned-not-changed
> path, and it matches a glob literally, with no "every other". So
> `tests/test_*.py` also matched this item's own
> `tests/test_178_corpus_sheet.py`, which is under **May change**, and
> `aide scope` failed on that file as changed-but-pinned. No bullet replaces
> the entry. A test file that is not under **May change** is already refused
> by `aide scope` as unauthorised. Naming each existing test file here would
> declare as pinned files that this item's tests never read. The intent is
> unchanged: a red test elsewhere is a hand-back to spec-author, not an edit.

## Testing Strategy

**The new module is `tests/test_178_corpus_sheet.py`**, with one test per AC
(AC1–AC9). The test-writer writes it.

- **Recompute from primary sources.** AC2–AC4 load fixtures with
  `nibabel.load` and build `placed` themselves from the two affines. They
  never call the module's placement helper. One module-scoped fixture holds
  `sheet_panels()` for AC1–AC4.
- **The off-grid case.** `crop_fov_si` is the case whose grid differs, so it
  is where AC2 and AC3 exercise the placement. The AC3 test asserts that at
  least one manifest case has a shape or affine different from
  clean_control's, so the placement cannot pass vacuously.
- **The digest.** AC6 and AC7 read the `Source` chunk with
  `PIL.Image.open(path).text`. They compute `D` with one
  `h = hashlib.sha256()` and repeated `h.update(path.read_bytes())`. Do not
  write it as the single-expression shape
  `hashlib.sha256(<path>.read_bytes()).hexdigest()`, which
  `tests/committed_artifact_guard.py` (item 127) classifies. AC7's failure
  message names the regeneration command
  `python -m segfacet.synth.corpus_sheet`.
- **Where tests write.** AC5 and AC6 write only under `tmp_path`, never to
  `SHEET_PATH`. `test_102` AC24 hashes `src/segfacet/**` across the run, and
  the suite runs under `-n auto`. AC5 closes nothing, because the `Figure`
  API keeps no registry.
- **The import sweep.** AC9 parses with `ast`, so a docstring that names the
  deleted path is not a hit. The new module's provenance note is such a
  docstring.

Adversarial cases, each written once:

- **`import-matcher-flags-seeded-import`**: AC9's matcher, applied to the
  source strings `"from lordotic_spine import build"` and
  `"import corpus_sheet"`, reports a hit for each. Applied to
  `"from segfacet.synth import corpus_sheet"` and
  `"import segfacet.synth.corpus_sheet"`, it reports none. This guards a
  matcher that never matches, which would let AC9 pass vacuously over the
  whole tree.

**Existing tests to reconcile: none.** This item changes no existing default
or behaviour. The sweep of 2026-09-24 checked every test that walks a
directory this item writes to or deletes from:

- `test_156` AC11 globs `docs/aide/*.generated.*` and reads each hit as text.
  The sheet's name avoids that glob (A1).
- `test_105` AC3 (`== 26`), `test_126`'s inventory, and `test_134` AC18
  (`_ITEM_126_INVENTORY_COUNT + len(_INVENTORY_ADDED_AFTER_126)`) count the
  non-`.py` files under `tests/`. Nothing is added there.
- `test_105`'s `_SECTION2_EXPECTED_FIXTURES` is a hand-set list of seven. It
  holds no `docs/aide/*.generated.*` document beyond the feature catalogue,
  and the sheet is not a golden file, so it takes no row.
- `test_102` AC24 hashes `src/segfacet/**/*.py|json` at collection and at the
  end of the run. The tests write nowhere in `src/`.
- `test_131` AC12, `test_147` AC1/AC2, `test_152` and `test_161` criterion 2
  sweep the text or string literals of `src/segfacet/**/*.py`. Step 1 keeps
  the new module clear of each.
- No test enumerates `scripts/` or names the prototype directory: a grep of
  `tests/` for `prototypes` finds nothing.
- No test pins the whole of `.gitattributes`, only the presence of named
  lines.

## Validation

Run `.venv/bin/python -m segfacet.synth.corpus_sheet --out <scratch>/sheet.png`
and open the image. Confirm:

- It holds one sagittal/coronal pair per manifest case (14 on 2026-09-24),
  titled by case id.
- `clean_control` has no red outline.
- `crop_fov_si`'s outline encloses the removed inferior part of L5 in both
  views, and its visible L5 remnant is shorter than clean_control's.
- `relabel_swap`'s two swapped bodies are outlined and shown in each other's
  colour.
- `PIL.Image.open(...).text["Source"]` matches the committed sheet's value.

No `[validation]` profile is needed.

## Dependencies

- Item 173 — the lordotic base the sheet renders.
- Item 174 — the `split` and `split_own_label` cases.
- Item 175 — `crop_fov_si`, the case on its own grid.
- Item 176 — the bridged `fuse_adjacent` case.
- Item 177 — the lateral `displace` case.

**Downstream:** AC7 makes every later change to the geometric manifest or a
seg fixture regenerate the sheet in the same item. That includes the next
queue's D3 expected-set edits, which change the titles. Those items list
`docs/aide/corpus_sheet.png` under May change. Stage 33's D5 gate reads the
committed sheet. Item 179 is independent of this item.

## Decisions & Trade-offs

- **`crop_to_grid` called as `crop_to_grid(clean_img, case_img)`.** The spec's
  prose (Implementation Steps §1) reads "call
  `segfacet.synth.corpus.crop_to_grid(clean_img, case_img)`", which,
  read as `crop_to_grid`'s own signature (`crop_to_grid(img, grid_img)`),
  crops `clean_img` down to `case_img`'s (possibly smaller) grid. That is the
  call that validates `case_img` is an integral sub-grid of `clean_img` and
  raises `FacetInputError` otherwise — the reverse order raises
  unconditionally for `crop_fov_si`, whose grid is smaller than
  `clean_control`'s. `sheet_panels()` places the case's own array afterwards
  with the independent AC2 offset formula, not `crop_to_grid`'s return value;
  `crop_to_grid`'s call here is validation-only.
- **Left open:** whether the intensity corpus gets its own sheet. The queue
  line names the geometric cases, and no consumer of an intensity rendering is
  declared.
- **Left open:** whether the status report (item 179 or later) embeds the
  sheet. That item's queue line re-keys its corpus section off the generated
  specification and does not mention the sheet.
- **Left open:** whether the digest should also cover the rendering code
  (A6). No consumer reads the layout, so a stale layout was not worth a
  version constant.
