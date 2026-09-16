# AIDE conventions

The shared contract every agent, script, and human obeys.

This file is the **index**. Each section is one file under
[`conventions/`](conventions/), so a pointer of the form `§6` resolves to
[`conventions/6-test-hygiene.md`](conventions/6-test-hygiene.md), and one of the
form `§1 → insights.md` to
[`conventions/1-format-contract/insights.md`](conventions/1-format-contract/insights.md).
Read the section you were pointed at; nothing here expects a top-to-bottom read.

| § | Section | What it governs |
|---|---|---|
| 1 | [Format contract](conventions/1-format-contract.md) | The exact shapes `aide.py` parses in `docs/aide/**`, and the rule that every durable artifact must read cold. Its own index — one file per document shape, and per reader where several roles act on one |
| 2 | [Claim protocol](conventions/2-claim-protocol.md) | How "this item is taken" is signalled between concurrent runs — the pushed claim branch, not a `🚧` on a feature branch |
| 3 | [Command hygiene](conventions/3-command-hygiene.md) | The canonical shell-command rules. Runtime-general; an adapter enforces them, it does not restate them |
| 4 | [Git modes](conventions/4-git-modes.md) | What `git.mode` changes inside `aide claim` / `aide merge`. Agent instructions are identical across modes |
| 5 | [Clarify mode](conventions/5-clarify-mode.md) | How `spec-author` resolves an ambiguous queued item under `loop.clarify` — and why the root documents sit outside it: authored via their entry point, interactively |
| 6 | [Test hygiene](conventions/6-test-hygiene.md) | Portability, and tests that can actually fail. Runtime-general, like §3 |
| 7 | [Off-platform verification](conventions/7-off-platform-verification.md) | No role in this loop sees a non-Linux checkout or real CI status; this is how to look at the gate that does |
| 8 | [Reaching into another repository](conventions/8-sibling-repos.md) | A repository's own instructions bind for work inside it |
| 9 | [Review and validation](conventions/9-review-and-validation.md) | Two different reads of one diff: what each answers, why neither covers for the other, and how a finding triages. Runtime-general, like §3 and §6 |

Sections are **runtime-general**: an adapter delivers them to its own agents by
whatever mechanism it has, and never restates a rule as its own. Each section is
written **core first**: the rule, its shape examples and the cases that
disambiguate it, in the order an agent decides them; then a closing
**Rationale** heading holding the defect that earned a rule, the counterfactual
and the rejected alternative, for the reader who follows a pointer. A delivered
copy carries the core; nothing under Rationale changes a decision the core does
not already make.

Every section is written in **one style**, so a reader who has followed one
pointer knows the shape of the next:

- **The opener.** The first line under the heading says what the section
  governs and who acts on it — a delivered section names the roles it is
  delivered to; a section reached by pointer names the verb or role that
  follows the pointer. The rule comes after the opener, never in it.
- **The bullet.** A bullet leads with its rule — one sentence, **bold** — and
  the rest of the bullet is what disambiguates it. Where a bullet defines a
  named thing (a mode, a setting, a list), the bold is that name and the rule
  follows it. A bullet with no rule to lead with is prose, not a bullet.
- **The Rationale.** A list of `- **Why X.**` bullets, one per rule that
  earned one, in the core's order; a Rationale with one thing to say is still
  one bullet, never a bare sentence or a paragraph.
- **The consumer annotation.** A bullet that states a shape the engine parses
  closes with its consumers in italic brackets — `*(aide check, claim,
  spec-author)*`: the verbs and roles that read that shape. It is a hint to a
  manifest of who reaches what, so every shape bullet of a document section
  carries one, or none does.
- **Verb mechanism lives in `-h`.** What a verb does — its grounds, its
  defaults, what it discounts, what it prints and refuses — is the verb's own
  help text (`python .aide/scripts/aide.py <verb> -h`). A section keeps the
  sentence that names the verb and the rule an author decides against it; it
  does not restate the help.

The one page that must bind before anything points anywhere is
[`AGENT-CONTEXT.md`](AGENT-CONTEXT.md).
