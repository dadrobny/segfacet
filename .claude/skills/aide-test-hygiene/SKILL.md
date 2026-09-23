---
name: aide-test-hygiene
description: Load before creating or editing a test file — portability rules and tests that can actually fail (conventions §6).
user-invocable: false
paths:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
  - "**/tests/**/*.py"
---

<!-- generated-from: .aide/conventions/6-test-hygiene.md
     Everything below the note is that file, down to its `Rationale` heading,
     written here by `install.py` at install time (issue #109). There is no
     hand-written copy of §6 to drift, so this file declares no `pins`
     block: that mechanism guards a restatement, and this is not one. Edit
     the section. -->

**Delivery, not a second source of truth.** What follows is
`.aide/conventions.md` §6 — `.aide/conventions/6-test-hygiene.md`, down to its
`Rationale` heading — rendered here verbatim at install time, so it cannot say
anything the engine does not. The defect each rule was earned by is in the
section below that heading; `.aide/conventions.md` resolves any `§N`.

The `paths:` above match by filename rather than by `project.tests_dir`, so they
hold whatever a consumer configured: the default pytest naming plus any
directory named `tests`. A project that overrides pytest's `python_files`, or
keeps tests in `spec/`, needs them widened to match.

## 6. Test hygiene (portability, and tests that can actually fail)

Runtime-general, like §3. An adapter **delivers** this section to a role about
to write a test rather than pointing at it.

**Every rule below was earned by a defect that passed every gate this loop runs
and reached `main` anyway.** That is the structural point: spec → tests → build
→ validate → merge all execute in one place, on one platform, against one
checkout, so a defect invisible under those conditions is invisible to the
entire loop, indefinitely.

**Portability.**

- **A test must be deterministic and pass on Windows, macOS and Linux, with no
  network access.** The rules below are the specific ways that is lost; this is
  the general statement they serve, and it binds a case none of them names.
- **Never write the repo's own working-directory path literally into a test.**
  Resolve from the test file (`Path(__file__).resolve().parents[N]`).
- **Any `Path` entering a hash, comparison, or match must be `.as_posix()`.**
  `str(Path)` — including a `Path` interpolated into an f-string, which calls
  `str()` — renders the OS-native separator, so an identical tree hashes
  differently on Windows.
- **A committed byte-exact fixture needs a `.gitattributes` `text eol=lf` pin.**
  Without it `core.autocrlf` rewrites the file on checkout and every byte
  comparison against it fails on Windows only. `aide check` warns on the cases
  it can decide: a path built from literals, compared with `==` or fed to a
  hash, resolving to a file that exists in the checkout and is covered by no
  `eol=lf` pattern. It reports **only what it can resolve** — a fixture reached
  through a `tmp_path`, a function argument, or a constant imported from
  another package is skipped in silence rather than guessed at. Treat a
  warning as authoritative and its silence as partial: the pin is still your
  responsibility on a path the check cannot see. **Silence has a second cause,
  and it is the one that misleads:** the lint decides a *read shape*, not
  whether a file needs a pin. `read_text()` applies universal-newline
  translation, so a committed artifact its tests read that way and then parse —
  `json.loads`, a Markdown table walked cell by cell — is immune to the rewrite
  and draws no warning whether or not it is pinned. `read_bytes()` has no such
  immunity, so **any** use of it on a committed path is reported. The immunity
  is a property of the reader, not of parsing. And a `read_text()` parse may
  still need the pin for a byte-reproducibility claim made where the lint
  cannot look, so never write
  "the eol-pin lint passes" as an acceptance criterion: assert the pin itself.
  `binary` and `-text` count as pins alongside `eol=lf` — all three stop the
  conversion — while a bare `text` enables it.
- **A test that captures subprocess output as text must pass
  `encoding="utf-8"`.** `text=True` (and its older spelling
  `universal_newlines=True`) names no codec, so Python decodes with
  `locale.getpreferredencoding()` — UTF-8 on a Linux runner, **cp1252** on a
  Windows one — and the same bytes become different strings on the two legs of
  one CI run. `aide check` warns on a `run`/`Popen`/`check_output` call
  carrying `text=` or `universal_newlines=` and no `encoding=`. It sees only
  direct calls: a suite that wraps its subprocess calls in a helper shows this
  lint one call site and hides the rest. **The codec is the producing side's
  job too**, and both ends must agree: a script that writes non-ASCII to
  stdout or stderr inherits the console codepage on Windows, so it must
  reconfigure its own streams — `aide.py`'s `main()` and the command-hygiene
  hook both do. A codec disagreement surfaces as a **missing value rather than
  an error** — the decode runs in `subprocess.run`'s reader thread, where a
  `UnicodeDecodeError` never reaches the caller, so `stdout` comes back
  `None`. So name the codec on the read, fix the writer if you own it, and
  pass `errors="replace"` when you do not — then assert the value is there
  before asserting anything about it.

**What the item's tests are.**

- **One test per acceptance criterion is the floor and the ceiling, unless
  the spec's Testing Strategy names the case.** The Testing Strategy names
  each adversarial case with the failure mode it guards; the tests an item
  adds cover every criterion and every named case, **and no other**. A test's
  name says which it covers — the criterion's number (`ac3`) or the label the
  Testing Strategy gave the case — so the link is readable without the spec.
  Depth is the spec author's decision, made where the deliverable and the
  posture (§1 → vision.md) are known; a test with no criterion and no named
  case behind it is a test nobody asked for — `aide scope` warns on one
  (`aide scope -h` states the grammar).
- **An item's tests live in `test_NNN_<topic>.py` under `tests_dir`, NNN
  its item number, unless the project has a reason to diverge.** The file
  name is what says whose criteria a test covers once a later item edits the
  file, so `aide scope` reads another item's file against that item's spec
  (`aide scope -h`). **A test reconciled in another item's file keeps that
  item's criterion number** — the number is its provenance; renumbering it to
  the reconciling item's criteria claims a criterion that item never wrote.
- **A consumer test never hand-builds a producer's serialised form.** It
  obtains the form from the producer's code, or from a fixture the producer's
  item ships, and asserts on what it reads — so when the shape changes, one
  test changes. A literal of another item's output written into this item's
  test is a second copy of that shape, and it is the copy that goes red.

**Tests that can actually fail.**

- **Prefer calling the function over shelling out to the command that calls
  it.** The CLI's logic is importable and returns structured data; a subprocess
  boundary adds stdout encoding, platform quirks, and a re-parse of what was
  structured a moment earlier. **A test asserting on `aide check`'s own
  output should call `run_checks` in-process**, which returns
  `(errors, warnings)` as structured data, rather than replaying the CLI's
  stdout.
- **Never pin an exact warning or error count from a module that itself trips
  the lint being counted.** The module raises the count by one the moment it is
  committed, so a baseline recorded before it existed is falsified by the act of
  adding it — a measurement that includes the measurer. Assert on the warning
  you mean by matching it, not on how many there are.
- **A scope claim about a diff belongs on the branch, not in the suite.**
  "This item did not touch X" is decided by `aide scope` against the item's
  declared paths (§1 → authorised paths), proved as §1 → authorised-paths-proof
  rules; written as a test it asserts
  something that stops being true the moment the item merges — on a stacked
  queue, where the item's base is the queue branch and not `main`, it reports
  every sibling item's legitimate change as this item's violation. **Deriving
  the base from `aide scope` is not the repair**: the verb reads the *current*
  branch's recorded base, and `aide merge` re-runs the suite from the merge
  target, so the test then fails by construction inside the loop's own
  post-merge run. Nor is a skip guard, which leaves the test permanently
  skipped once the claim branch is deleted. `aide check` warns on both literal
  shapes; a test that computes its base (`git merge-base HEAD origin/main`) is
  a claim about the branch rather than about an item and is deliberately not
  reported.
- **Assert a derived value is recognisable *before* asserting anything about
  it.** A glob that matched nothing, a capture that came back empty, a slice
  taken from a failed `find()` — each yields a value that flows into the
  assertion and passes while checking nothing.

`aide check` decides the ones a script can, six of them: the repository's own
absolute path written into a test file, a `str()` around a `relative_to(...)`,
a shell-out to the CLI whose function was importable, a text capture that names
no codec, a byte-compared fixture no `eol=lf` pattern covers, and a diff-time
scope claim written as a suite assertion. The rest of this section binds
identically and is checked by nobody, so read a warning as authoritative and
silence as partial throughout — not only on the pin.
