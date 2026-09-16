<!-- generated-from: .aide/conventions/3-command-hygiene.md
     Everything below the shaping note is that file, down to its `Rationale`
     heading, written here by `install.py` at install time (issue #109). There
     is no hand-written copy of §3 to drift, so this file declares no `pins`
     block: that mechanism guards a restatement, and this is not one. Edit
     the section. -->

**Delivery, not a second source of truth.** What follows is
`.aide/conventions.md` §3 — `.aide/conventions/3-command-hygiene.md`, down to
its `Rationale` heading — rendered here verbatim at install time, so it cannot
say anything the engine does not. A `PreToolUse` hook enforces the mechanical
rules and bounces a violating shape back with the fix, and an unattended run
that emits a shape nothing pre-approved stalls on a permission prompt — so
getting them right first time is what keeps a long run moving.

**The shaping this runtime adds**, which §3 leaves to the adapter: **use the
Bash tool, not PowerShell** for git / `aide` / venv / grep commands — only
`Bash(...)` rules are allow-listed.

## 3. Command hygiene (canonical rules)

Runtime-general: they hold whether or not a runtime has a permission model.
An adapter **delivers** this section to its own roles in *positive form*; how
the rules are **enforced**, and any provider-specific **command shaping** a
permission policy demands on top of them, are adapter concerns — see the
adapter's README.

The rules:

- **If an `aide` verb covers it, the raw git form is wrong.** Session preflight
  (fetch, clean-tree check, landing on the right branch) is `aide sync
  [--item NNN]`; claiming is `aide claim`; starting a queue or specs-queue
  branch is `aide queue start NNN [--specs]`; landing is `aide merge`; branch
  clean-up is `aide gc`; checking a branch's changed files against its item's
  authorised paths is `aide scope`. Do not improvise the equivalent `git
  fetch`/`git status`/`git switch -c`/`git diff --name-only` sequences.
- **One command per call.** Never chain with `&&`, `||` or `;`. A single `|`
  pipe (`git branch -r | grep aide/`) is fine.
- **No `cd` prefix and no directory-changing wrapper** — `git -C "<path>"`,
  `git --git-dir=<path>`, `git --work-tree=<path>`, or a `GIT_DIR=<path>`/
  `GIT_WORK_TREE=<path>` prefix all point git at a repo other than cwd. The
  tool's working directory is already the repo root — run the bare command.
  **Unless the repo is declared** in the adapter's personal, machine-local
  config: a command whose repo-override paths all resolve to one declared
  repo is allowed; one naming two different repos stays blocked even when
  both are declared. Declaring a repo relaxes this rule and grants
  nothing else — the command must still clear whatever permission policy the
  runtime applies.
- **No `2>&1`** or other redirections — the tool already captures stderr.
- **No command substitution in commits.** Avoid `$(…)`/backticks; use single-line
  `-m "msg"`, repeated `-m` for paragraphs, or `git commit -F <file>`.

The `aide` CLI always runs as `python .aide/scripts/aide.py <cmd>` — stdlib-only
and venv-independent, so it works before any project venv exists and identically
across runtimes.

**Python and pytest run from the project venv by relative path** —
`.venv/Scripts/python -m pytest` on Windows, `.venv/bin/python -m pytest` on
macOS and Linux. Never a bare `python`/`pytest`, and never an absolute path.

**Against a declared sibling repo** (§8), the CLI needs no `cd` and no git-style
wrapper either — run the *sibling's own install* with an explicit root:

```
python <sibling>/.aide/scripts/aide.py --repo <sibling> <cmd>
```
