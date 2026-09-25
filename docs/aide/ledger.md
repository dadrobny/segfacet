<!--
  AIDE run ledger. One row per item worked, appended by the verbs that end an
  item. The engine creates docs/aide/ledger.md from this file, byte for byte,
  the first time one of them has a row to write; nobody copies it by hand and
  nothing edits a row afterwards.
  What each column holds, and which cells a caller passes rather than the
  engine reading: conventions.md §1 → ledger.md. How a cell is filled, and
  what each verb refuses: `python .aide/scripts/aide.py merge -h` and
  `python .aide/scripts/aide.py ledger -h`. This comment is the shape; the
  aide-template line below it names the template version this file was
  created from.

  Row — one cell per column of the table, in the table's order:
    | 001 | 001 | 2 | normal | merged | 3 | 4 | 6 | 2 | 1 | 2 | 0 | 1.58.0 | 2026-09-17 |
  A cell left empty is one nothing supplied or nothing could measure. It is
  blank rather than 0, which would read as a measurement. One of the three
  finding cells may instead hold `-`; which verb writes that mark, and when,
  is at `python .aide/scripts/aide.py merge -h`.
-->
<!-- aide-template: ledger 2 -->
# Run Ledger

_One row per item, newest last._

| Item | Queue | Stage | Kind | Outcome | ACs | Tests | Files | Rounds | Blocking | Minor | Nit | Engine | Date |
|------|-------|-------|------|---------|-----|-------|-------|--------|----------|-------|-----|--------|------|
| 162 | 022 | 32 | normal | merged | 15 | 21 | 9 | 3 | 0 | 1 | 1 | 1.59.2 | 2026-09-20 |
| 163 | 022 | 32 | normal | merged | 6 | 7 | 5 | 1 | 0 | 0 | 0 | 1.59.2 | 2026-09-20 |
| 164 | 022 | 32 | maintenance | merged | 14 | 19 | 35 | 2 | 0 | 1 | 0 | 1.59.2 | 2026-09-20 |
| 165 | 022 | 32 | maintenance | merged | 7 | 11 | 5 | 2 | 0 | 0 | 1 | 1.59.2 | 2026-09-20 |
| 166 | 022 | 32 | normal | merged | 9 | 19 | 37 | 2 | 0 | 0 | 1 | 1.59.2 | 2026-09-20 |
| 167 | 022 | 32 | normal | merged | 11 | 23 | 34 | 2 | 0 | 2 | 0 | 1.59.2 | 2026-09-20 |
| 168 | 022 | 32 | normal | merged | 12 | 18 | 6 | 1 | 0 | 0 | 1 | 1.59.2 | 2026-09-20 |
| 169 | 022 | 32 | validate-stage | merged | 19 | 11 | 5 | 2 | 0 | 2 | 0 | 1.59.2 | 2026-09-22 |
| 170 | 023 | 33 | maintenance | merged | 7 | 12 | 19 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-23 |
| 171 | 023 | 33 | maintenance | merged | 6 | 7 | 8 | 2 | 0 | 0 | 1 | 2.1.0 | 2026-09-23 |
| 172 | 023 | 33 | maintenance | merged | 4 | 5 | 4 | 2 | 0 | 1 | 0 | 2.1.0 | 2026-09-23 |
| 173 | 023 | 33 | maintenance | merged | 7 | 13 | 57 | 2 | 2 | 1 | 0 | 2.1.0 | 2026-09-23 |
| 174 | 023 | 33 | maintenance | merged | 10 | 16 | 38 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 175 | 023 | 33 | maintenance | merged | 11 | 17 | 32 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 176 | 023 | 33 | maintenance | merged | 11 | 17 | 24 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 177 | 023 | 33 | maintenance | merged | 5 | 10 | 13 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 178 | 023 | 33 | maintenance | merged | 15 | 17 | 12 | 2 | 1 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 179 | 023 | 33 | maintenance | merged | 6 | 10 | 5 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-24 |
| 180 | 024 | 33 | maintenance | merged | 3 | 4 | 4 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-25 |
| 181 | 024 | 33 | maintenance | merged | 3 | 0 | 4 | 1 | 0 | 0 | 0 | 2.1.0 | 2026-09-25 |
