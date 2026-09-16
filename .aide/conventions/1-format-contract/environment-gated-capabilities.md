### Environment-gated capabilities (optional, additive)

Governs a capability only some environments can exercise — a GPU library,
Docker, a large optional extra — and how its verification is recorded. The
item and `progress.md` templates point here: `spec-author` fills the item
section, a stage-closing item's builder keeps the table, `aide env`
evaluates a profile, and `aide status` and `aide check` read the table.

**The verification table is read, and gates nothing.** `aide status` lists
every row not yet `✅ Verified`, and `aide check` reports on its rows — only
ever as warnings, since no stage, objective or claim waits on one. What each
verb reports is its `-h`.

**A capability gated behind an optional package or external tool (a GPU
library, Docker, a large/optional pip extra, ...) must degrade gracefully** —
its tests skip cleanly (never fail, never silently pass as if exercised) when
the dependency is absent, mirroring the project's existing optional-extra
pattern. That graceful-fallback bar is enough for a stage to reach ✅ under the
rollup rule. Two additive, non-blocking mechanisms record whether the gated
path was ever run for real:

- **The item template's optional Environment / Hardware Dependencies
  section** — filled in by any item introducing such a capability, naming the
  package/tool, its `pyproject`/equivalent declaration, and the required
  fallback behaviour.
- **`progress.md`'s optional Environment-Gated Capability Verification
  table** — one row per capability, starting `❓ Unverified`. A stage-closing
  item's Implementation Steps must add/update the row(s) for any capability
  its stage introduced. The row flips to `✅ Verified (date, host/CI)` only
  when a human or a CI runner that actually has the dependency present has
  run the gated path — never inferred from the stage's own ✅ status. A row
  still `❓ Unverified` once its stage is ✅ records why in its Notes cell.
  A row names the `[validation]` profile that would verify it in its
  Package / Tool cell, as `` `<name>` profile ``.

Both mechanisms are opt-in: a project with no environment-gated capability
omits them entirely.

Two additions make the verification *planned* rather than hoped-for:

- **`[validation]` environment profiles** (`aide.toml`, optional) — named,
  deterministic environment checks: `<name> = "<python expression>"`, true iff
  the environment provides the capability (e.g.
  `gpu = "__import__('torch').cuda.is_available()"`). Evaluated by
  `aide env --profile <name>` (exit 0 iff satisfied) in the project venv, or
  for every `❓ Unverified` row at once by `aide status --profiles`. Either
  evaluates the expression only, never the gated path.
- **Stage-validation items** — a queue that closes a roadmap stage ends with a
  `Validate stage N` item that replays the stage's use cases end-to-end and
  updates the capability table (✅ Verified where the profile is satisfied,
  else an explicit ❓ Unverified with the reason). Item specs may also carry an
  optional **Validation** section (see the item template) that the validator
  must execute.

#### Rationale

- **Why a table, and not the suite's verdict.** A skip-clean pytest run is not
  evidence the optional path was ever run for real, and nothing else records
  that gap by default — the table is the record.
- **Why the table has a reader at all.** From 1.1.0 it had none, and from
  1.49.0 said so outright (#202), while this section stated rules about it that
  nothing checked — a crossing of `docs/vision.md` commitment 5. Both local
  consumers kept the table heavily, and one wrote the row-to-profile link by
  hand in the Package cell; the link is that consumer's form, made the
  contract rather than a new column, which would have made every existing row
  unreadable (#207).
- **Why every finding is a warning.** A mis-shaped row in the other
  `progress.md` tables is an error because the dropped row takes a check's
  error with it — a ✅ over-claim. This table gates nothing, so a dropped row
  carries no over-claim away, and the table is additive and non-blocking by
  design; an error here would make verification block the loop (#207).
- **Why a closed stage's ❓ row needs a reason, not a ✅.** Graceful fallback
  lets a stage close without the dependency; what is owed is the honest
  record of why the path did not run, which the stage-validation item writes.
- **Why a stage-validation item replays use cases.** Tests prove the code
  runs; validation observes that it does something meaningful — so it replays
  the stage's use cases rather than re-running the suite.
