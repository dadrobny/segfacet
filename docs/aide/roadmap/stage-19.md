> Stage 19's section, archived from [roadmap.md](../roadmap.md) by `aide progress archive`; `aide progress unarchive --stage 19`, run on the main or queue branch, moves it back.

## Stage 19 — Generated Feature & Rule Catalogue + Steering Review (G7, G8)

**Goal.** Make the feature set reviewable, then review it. `FEATURE_CATALOG` in
`scripts/aide_status_report.py` documents 9 groups / 41 entries and says in a comment
*"Not derived from a filesystem scan: keep in sync by hand"*; a single realised feature
record has **185 distinct leaf paths**. Those count different things (an entry such as
`touches_*` covers six fields), so the gap is not a straight drift figure — but nothing
verifies the two agree, and no document records *which failure mode each feature is for*.

**Deliverables.**

- **A generated catalogue** — realised record shape from `extract_feature_record` plus
  extractor docstrings — replacing the hand-maintained table. Columns: feature ·
  module/item · what it measures · **how it is computed** · units · spacing/scale
  sensitivity · **§6 failure mode(s) targeted** · **rules that consume it** ·
  **status: keep / retune / retire / unwired**.
- **A drift test**: every leaf path in a reference record must be covered; CI fails when
  a feature lands undocumented.
- **A golden-file decision table** — one row per committed golden: what it asserts,
  keep or retire, and what replaces it. Working assumption is **retire most**: the nine
  `tests/corpus/golden/*.json` are whole-record snapshots (~185 leaf paths) of a corpus
  Stage 21 replaces, and every feature retune this stage authorises forces a wholesale
  regeneration, after which the golden diff can no longer distinguish an intended change
  from a regression. Byte-level reproducibility is **not** what they guard — that is the
  separate intra-run `dest1 == dest2` determinism assertion, which is independent of the
  goldens and stays. Report-formatting and schema goldens are the likely survivors.

**Dependencies.** None. **This stage carries the human checkpoint** — `aide.toml` sets
`clarify = "assume"`, so run it through `/aide-spec-queue`, which front-loads the review
so execution can then proceed unattended.

**Validation / acceptance.**

- The catalogue is generated, not hand-written; the drift test fails on a
  deliberately undocumented feature (**G7**).
- Every feature carries a status and **one of**: a named failure mode · the
  marker `unwired` · or *statused but mode-unmapped, with the consuming
  mode-less rule named* (**G8**).
- The golden decision table is complete and signed off by the human reviewer.

> **G8 wording amended 2026-08-11.** The original sentence named only two
> states and was unsatisfiable as written by the mechanism this stage shipped: a path
> consumed solely by a rule that carries no §6 mapping (`bounds`, `intensity`,
> `reference_delta`, `intensity_reference_delta`) is statused `keep` with empty
> `failure_modes` and `mode_evidence == ("rule_unmapped",)` — statused, not `unwired`, and
> naming no mode. 72 of 111 entries sit there. The third state is now named explicitly, and
> the *substantive* close is **Stage 20**'s job: map those four rules to §6 modes or record
> that they target none. A rule that consumes features but targets no catalogued failure
> mode is itself the finding.
