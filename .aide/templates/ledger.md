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
    | 001 | 001 | 2 | normal | merged | 3 | 4 | 6 | 2 | 1 | 2 | 0 | 2.7.0 | 2026-09-25 | 41 | 0 |
  A cell left empty is one nothing supplied or nothing could measure. It is
  blank rather than 0, which would read as a measurement. One of the three
  finding cells may instead hold `-`; which verb writes that mark, and when,
  is at `python .aide/scripts/aide.py merge -h`. So is when the Suite s cell
  reads like `41 (reused)`. A row written before the last two columns
  existed has fourteen cells and is read as it stands.
-->
<!-- aide-template: ledger 3 -->
# Run Ledger

_One row per item, newest last._

| Item | Queue | Stage | Kind | Outcome | ACs | Tests | Files | Rounds | Blocking | Minor | Nit | Engine | Date | Suite s | Inherited |
|------|-------|-------|------|---------|-----|-------|-------|--------|----------|-------|-----|--------|------|---------|-----------|
