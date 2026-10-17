<!-- aide-template: item 3 -->
# Item 239 — The corpus sheet regenerated with the manifest

> **Created:** 2026-10-17 · status tracked in [`progress.md`](../progress.md)
> **Stage:** 34 — Maintenance
> **Queue:** [`../queue/queue-032.md`](../queue/queue-032.md) · Item 239
> **Objectives:** G7
> **Suggested branch:** `aide/239-the-corpus-sheet-regenerated-with`

---

## Description

`tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current` ties
`docs/aide/corpus_sheet.png` to a SHA-256 digest of `tests/corpus/manifest.json`
followed by each case's seg-fixture bytes (`segfacet.synth.corpus_sheet.input_digest`).
So an item that regenerates the corpus with `python -m segfacet.synth.corpus`
also has to run `python -m segfacet.synth.corpus_sheet`, as a second step.
Three of queue 030's four manifest-regenerating specs left that step out
(insight `2026-10-13-62d2`).

This item makes the corpus regeneration CLI (`segfacet.synth.corpus.main`)
write the sheet in the same run, from the manifest it has just written, so
the separate step goes away. matplotlib is a `dev` extra, not a core
dependency (`pyproject.toml` `[project.optional-dependencies] dev`), and
`corpus_sheet` imports it only inside its rendering functions. The
regeneration therefore renders the sheet only where matplotlib is
importable. Where it is not, the manifest is still written, the run says on
stderr which sheet it did not write, and it exits non-zero, so a stale sheet
is never left behind silently. Importing `segfacet.synth.corpus` still does
not import matplotlib.

The live prose that names the separate step is updated to name the one
command: `corpus_sheet.py`'s module docstring, `corpus.py`'s module and
`main` docstrings, and test_178 AC7's two failure messages.

**Not in scope.** `write_corpus` (the in-memory API that tests call into
temporary directories) does not render a sheet. Only the CLI regenerates
committed artifacts. The corpus content itself is unchanged, so the
committed manifest, fixtures and sheet are not regenerated. Merged item
specs and queue files that name the old two-step instruction are provenance
records and stay as they are. No framework or process file carries the
instruction (see A5), so none needs an edit.

## Acceptance Criteria

- [ ] **AC1: The regeneration writes a sheet that matches its manifest.**
  After `segfacet.synth.corpus.main(["--out", str(d)])` for a fresh directory
  `d`, the PNG at `d / "corpus_sheet.png"` has a `Source` text chunk equal to
  `"sha256:"` + the hex SHA-256 of `d / "manifest.json"`'s bytes followed by
  each case's seg-fixture bytes in manifest order, recomputed by the test
  from the files under `d`. This is the digest test_178 AC7 checks.
- [ ] **AC2: The default regeneration writes the committed sheet path.**
  With `segfacet.synth.corpus.CORPUS_DIR` monkeypatched to a temporary
  directory `c` and `segfacet.synth.corpus_sheet.SHEET_PATH` monkeypatched to
  a temporary file path `s`, `segfacet.synth.corpus.main([])` writes a PNG at
  `s` whose `Source` text chunk equals `"sha256:"` + the digest (as in AC1)
  of `c / "manifest.json"` and its fixtures.
- [ ] **AC3: Without matplotlib the manifest is still written.** With
  `sys.modules["matplotlib"]` set to `None`,
  `segfacet.synth.corpus.main(["--out", str(d)])` writes `d / "manifest.json"`,
  whose `load_manifest` case-id set equals the committed manifest's.
- [ ] **AC4: Without matplotlib the run names the sheet it did not write.**
  With `sys.modules["matplotlib"]` set to `None`, the stderr that
  `segfacet.synth.corpus.main(["--out", str(d)])` writes contains
  `str(d / "corpus_sheet.png")`.
- [ ] **AC5: Without matplotlib the run exits non-zero.** With
  `sys.modules["matplotlib"]` set to `None`,
  `segfacet.synth.corpus.main(["--out", str(d)])` returns `1`.
- [ ] **AC6: Importing the corpus module does not import matplotlib.** In a
  fresh interpreter (`sys.executable`, subprocess), `import
  segfacet.synth.corpus` leaves `"matplotlib"` out of `sys.modules`.

## Assumptions

- **A1:** The sheet for a non-default `--out d` is written to
  `d / "corpus_sheet.png"`, beside the manifest it digests. When `--out`
  resolves to `CORPUS_DIR` (omitted, or named explicitly), the sheet goes to
  `corpus_sheet.SHEET_PATH` (`docs/aide/corpus_sheet.png`). This is the
  defensible default under `loop.clarify = "assume"`. A single `--sheet`
  flag defaulting to `SHEET_PATH` was rejected because
  `tests/test_040_synthetic_corpus.py::test_ac18_the_one_command_regeneration_entry_point_runs`
  calls `main(["--out", tmp])` and would then overwrite the committed sheet
  from inside the suite. No `--sheet` flag is added.
- **A2:** "Reports that the sheet was not written" means one line on stderr
  that names the unwritten sheet path, says matplotlib is not importable,
  and says to rerun the same command with the `dev` extra installed. The run
  exits `1`. A non-zero exit was chosen because an unattended loop reads exit
  codes, and stderr alone is the silent failure the insight records. The
  already-present sheet at that path, if any, is left untouched, never deleted.
- **A3:** matplotlib's absence is detected by `import matplotlib` inside
  `main`, guarded by `except ImportError`, before `corpus_sheet.render_sheet`
  is called. The tests simulate absence with
  `monkeypatch.setitem(sys.modules, "matplotlib", None)`, which makes that
  import raise `ModuleNotFoundError`, even when `matplotlib.figure` is already
  cached by an earlier test. A probe of a submodule (`matplotlib.figure`)
  would be satisfied by that cache, so the probe names the top-level package.
- **A4:** `main` reads `CORPUS_DIR` and `corpus_sheet.SHEET_PATH` at call
  time and passes the sheet path to `render_sheet` explicitly.
  `render_sheet`'s `out=SHEET_PATH` default is bound when the module is
  defined, so it would ignore AC2's monkeypatch. `corpus_sheet` is imported
  inside `main`, never at `corpus.py` module level: `corpus_sheet` imports
  `MANIFEST_PATH`, `crop_to_grid` and `load_manifest` from `corpus` at its own
  top level, so a top-level import the other way is circular.
- **A5:** The prose sweep (2026-10-17, grep over `src`, `tests`, `scripts`,
  `README.md`, `docs/` outside `items/`, `queue/` and `insights/`, `CLAUDE.md`,
  `AGENTS.md`, `REVIEW.md`, `.aide/**` and `.claude/**`) found the separate
  step named in exactly three live places. They are `corpus_sheet.py` lines
  11–13 ("Regenerate the committed sheet … with `python -m
  segfacet.synth.corpus_sheet`") and test_178 AC7's two assertion messages
  (lines ~278–294). `corpus.py`'s docstrings name only the manifest. No
  framework or process file (`CLAUDE.md`, `.aide/**`, `.claude/**`) and no
  item template or convention carries the instruction, so this item needs no
  framework edit. Merged item specs (for example 207, 211, 212, 218) and
  queue files that name the step are provenance and are not rewritten.
- **A6:** Nothing at test time currently imports matplotlib through
  `segfacet.synth.corpus`. This was checked 2026-10-17 at `28e73484`:
  `.venv/bin/python -c "import sys, segfacet.synth.corpus; print('matplotlib' in sys.modules)"`
  printed `False`. AC6 pins that this stays true once `main` gains its
  lazy imports.

## Implementation Steps

1. In `src/segfacet/synth/corpus.py` `main`, after `write_corpus(Path(args.out))`
   returns `manifest_path`, resolve the sheet path. If
   `Path(args.out).resolve() == CORPUS_DIR.resolve()`, use
   `segfacet.synth.corpus_sheet.SHEET_PATH` (read at call time, A4).
   Otherwise use `Path(args.out) / "corpus_sheet.png"` (A1).
2. Probe `import matplotlib` in a `try/except ImportError` (A3). If the probe
   fails, print the one stderr line A2 describes, naming the sheet path, and
   return `1`. The manifest has already been written by then.
3. Otherwise import `segfacet.synth.corpus_sheet` inside `main` (A4). Call
   the existing `corpus_sheet.render_sheet(out=sheet_path, manifest_path=manifest_path)`,
   which already digests the given manifest through `input_digest`. Print
   `Wrote corpus sheet to <path>` beside the existing manifest line, and
   return `0`. No new rendering or digest code, and no new dependency.
4. Update `corpus.py`'s module docstring (the "CLI entry point" bullet, lines
   ~34–36) and `main`'s docstring. They say the command also writes the
   corpus sheet, where it writes it (A1), and what happens without
   matplotlib (A2).
5. Update `src/segfacet/synth/corpus_sheet.py`'s module docstring (lines
   ~11–13). The committed sheet is written by `python -m
   segfacet.synth.corpus` with the manifest. `python -m
   segfacet.synth.corpus_sheet` remains the way to render it alone from the
   committed manifest (for example after a run without matplotlib).
6. In `tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current`,
   change both failure messages to name `python -m segfacet.synth.corpus`
   as the regeneration. The assertions themselves are unchanged.
7. Add `tests/test_239_corpus_sheet_with_manifest.py` to
   `.github/workflows/ci.yml`'s `jobs.test.env.WINDOWS_TESTS` list in sorted
   position, after `tests/test_216_neighbour_pair_and_case_level_migration.py`.
   AC6 spawns a subprocess with `sys.executable`, and the digest reads bytes,
   so `tests/test_213_windows_ci_subset.py::test_ac5_list_is_exactly_the_os_sensitive_set`
   flags the module and fails until it is listed.

## Authorised paths

**May change:**

- `src/segfacet/synth/corpus.py` — `main` renders the sheet or reports why not; docstrings
- `src/segfacet/synth/corpus_sheet.py` — module docstring names the one-command regeneration
- `tests/test_178_corpus_sheet.py` — AC7's two failure messages name the corpus regeneration
- `tests/test_239_corpus_sheet_with_manifest.py` — this item's tests
- `.github/workflows/ci.yml` — `WINDOWS_TESTS` lists the new OS-sensitive test module

**Asserts against:**

- `tests/corpus/manifest.json` — AC3 compares the regenerated case-id set with the committed one
- `docs/aide/corpus_sheet.png` — test_178 AC7 pins it current; the corpus is unchanged, so it is not regenerated

## Testing Strategy

Module: `tests/test_239_corpus_sheet_with_manifest.py`. Every regeneration
writes under `tmp_path` or `tmp_path_factory`, never under `CORPUS_DIR` or
`SHEET_PATH`. AC2 and the adversarial case below monkeypatch both constants
to temporary paths first. Recompute the digest with repeated
`hashlib.sha256().update()` calls over the manifest's bytes, then each case's
seg-fixture bytes, as test_178's `_expected_digest` does. Never use the
single-expression `hashlib.sha256(<path>.read_bytes()).hexdigest()` shape
that `tests/committed_artifact_guard.py` classifies as a violation. Read the
`Source` chunk with `PIL.Image.open(...).text["Source"]`, as test_178 AC6
does. Each regeneration writes the whole corpus, so AC3–AC5 may share one
module-scoped run, with matplotlib hidden through `pytest.MonkeyPatch.context()`
and stderr captured with `contextlib.redirect_stderr`. Hide matplotlib only
with `sys.modules["matplotlib"] = None` (A3). AC6 runs
`[sys.executable, "-c", ...]` and asserts on the child's printed result.

Adversarial cases:

- `explicit-out-naming-corpus-dir`: with `CORPUS_DIR` monkeypatched to `c` and
  `SHEET_PATH` to `s`, `main(["--out", str(c)])` writes the sheet at `s`, and
  no file exists at `c / "corpus_sheet.png"`. This guards the failure where
  `python -m segfacet.synth.corpus --out tests/corpus` regenerates the
  committed manifest but leaves the committed sheet stale and drops a stray
  PNG into `tests/corpus/`. That is the exact defect this item removes,
  reached through the explicit-path spelling.

Existing tests to reconcile:

- `tests/test_040_synthetic_corpus.py::test_ac18_the_one_command_regeneration_entry_point_runs`
  calls `main(["--out", tmp])`. It now also renders a sheet into `tmp`, and
  its `rc == 0` assertion still holds wherever matplotlib is installed, as
  the `dev` extra the suite runs under guarantees. No edit is needed.
- `tests/test_178_corpus_sheet.py::test_ac7_committed_sheet_is_current`:
  only its failure messages change (step 6). Its assertion is untouched.
- No test pins `corpus.py`'s or `corpus_sheet.py`'s docstring text or the
  `Wrote corpus manifest to` stdout line (grep 2026-10-17).

## Validation

1. `.venv/bin/python -m segfacet.synth.corpus --out <scratch>/regen` exits 0
   and prints both `Wrote corpus manifest to …/regen/manifest.json` and
   `Wrote corpus sheet to …/regen/corpus_sheet.png`. That shows the
   `python -m` path works through the lazy `corpus_sheet` import, which
   re-imports `segfacet.synth.corpus` under its package name while the CLI
   runs as `__main__`.
2. `git status --porcelain` after step 1 lists nothing under `tests/corpus/`
   or `docs/aide/`. Validation never regenerates the committed corpus or
   sheet.

## Dependencies

None.

## Decisions & Trade-offs

To be updated during implementation.

- **Not an environment-gated capability.** The sheet rendering and its
  matplotlib dependency shipped with item 178. This item adds a graceful path
  for its absence and introduces no new capability, so it adds no
  Environment / Hardware Dependencies section and no verification-table row.
  The suite already requires matplotlib (test_178 imports it without a skip).
