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

### Rationale

- **Why delivered, not pointed at.** A pointer is followed only if the role
  chooses to, and these rules bind whether or not it did. Each rule was caught
  by a human reading a CI log, or by a reviewer outside the loop — never by a
  gate inside it — and each lint above was added after the class it names had
  already reached `main`.
- **The absolute path.** It ignores where the process runs, so it passes on
  the machine that authored it and matches nothing anywhere else — including
  a fresh clone in a *different* directory. A hardcoded sandbox path made a
  glob return nothing on every CI runner, collapsing a digest to
  SHA-256-of-empty input and failing all four legs while every local gate
  stayed green.
- **The separator.** The `.as_posix()` class alone has caused four separate
  CI-only failures.
- **Why the eol lint stays narrow.** The majority of `read_bytes()` calls in a
  real suite compare two freshly generated files to each other and need no pin
  at all, so guessing at an unresolvable path would be noise; and warning on
  a `read_text()` parse would be wrong rather than merely noisy, since the
  reader is immune — `p.read_bytes().decode()` on a CRLF checkout leaves a
  `\r` in the last cell of a Markdown row where `read_text()` does not.
- **Why the in-process call binds on `aide check` itself.** It is where the
  rule looks least applicable and binds hardest; `aide check` flags a module
  that replays its stdout, and that is the rule working rather than the verb
  flagging itself.
- **Why the lints run without the loop.** They read `tests_dir`, never
  `docs_dir`, so `aide check` in a repo with no `docs_dir` runs them, says so
  in a `notice:`, and exits 0 — a repo may adopt these conventions and the
  CLI without adopting the loop. `aide check -h` says so.
- **The codec, twice.** Six items in a single queue independently wrote
  `capture_output=True, text=True`; all six passed the Linux-only validator,
  and `windows-latest` raised a `KeyError` on a mangled em-dash heading in one
  test and — worse — left an emoji-diff guard **matching nothing and reporting
  PASS** in another. That second one is the shape to fear: a false negative, a
  gate that is green having verified nothing. Then, on the very branch that
  added the rule, the windows CI leg caught the producing side: the hygiene
  hook wrote its em-dash as cp1252, a strict UTF-8 reader rejected byte
  `0x97`, and the read came back `None`. A `capture_output=True, text=True`
  call that "returned `stdout is None`" had been recorded earlier as a Windows
  quirk and fixed by deleting the subprocess boundary; it was this codec
  disagreement all along.
- **The count.** A spec's Assumptions held 3 warnings, the base commit already
  carrying the checking module reported 4, and the 4th was that module.
- **The scope claim.** Two independent items in one consumer wrote `git diff
  main...HEAD` in a test — the signature of a missing rule rather than a
  careless author.
- **The unrecognisable value.** Had that Windows capture returned `""` rather
  than `None`, the loop over its lines would have iterated zero times and the
  test would have reported PASS having verified nothing.
- **The floor and the ceiling.** The item loop's gates all pushed toward more
  tests and none toward fewer: the validator FAILs an uncovered criterion,
  and the test-writer — the one role that never reads the vision — was told
  to add four categories of adversarial input on its own judgement, so a
  fifth test of the same branch failed nothing. Measured across consumers on
  engine ≤ 1.54.1 (issue #242): suites in the thousands within a few queues,
  most of them pinning behaviour no criterion named. Naming the case in the
  spec moves the decision to the role that knows what the deliverable is for,
  and the name rule is what makes "no other" checkable: `aide scope` warns
  on a test the branch added whose name carries neither, the counter-gate the
  loop lacked, reported as a warning first so a consumer lives with it
  before it gates anything.
- **The hand-built form.** Consumers on the same engines saw one item's tests
  invalidated by the next: the consumer's test carried a literal of the
  producer's JSON, so every legitimate change to the producer went red in a
  test that had read one field of it. §5 holds the spec-side half — a
  producer pins what is read, in the form it is read — and this is the
  test-side half, since a fixture the producer ships is the one copy of the
  shape that changes with it.
