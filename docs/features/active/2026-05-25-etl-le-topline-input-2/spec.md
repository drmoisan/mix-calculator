# etl-le-topline-input — Spec

- **Issue:** #2
- **Parent (optional):** n/a
- **Owner:** Dan Moisan
- **Last Updated:** 2026-05-25T20-21
- **Status:** Draft
- **Version:** 0.1.0

## Overview

A single-file Python CLI that normalizes an Excel "LE" (Latest Estimate) topline
planning workbook into one row per business key, reproducing an as-built in-workbook
Excel formula chain exactly — including a known quirk that must be preserved rather
than corrected.

- Target users/personas and primary use cases: FP&A analysts who run the script
  monthly against the LE planning workbook to produce a normalized table persisted
  to a SQLite database for downstream analysis, replacing a fragile chain of
  `XLOOKUP`/`SUMIF`/key-concatenation formulas with an auditable, repeatable,
  version-controllable transform.
- Success metrics or expected impact: deterministic, fail-fast normalization whose
  per-column source/output tie-outs match within `1e-6`; the manual formula chain is
  no longer required to produce the normalized output.

## Behavior

End-to-end, the tool loads the source sheet, validates its schema, rebuilds the
business key, collapses rows by key, derives the `YTG` measure, validates tie-outs,
persists the result to SQLite, and prints a tie-out summary.

- Main user flow (happy path): a valid workbook matching the documented source schema
  is loaded (Excel row 3 as header, data from row 4); rows with blank `Customer` are
  dropped; `KEY` is rebuilt from `Customer + coerce_sku(SKU #) + Type`; all rows
  sharing a `KEY` collapse into one row (text from the first matching row, numeric
  columns summed); the `YTD/YTG` column is dropped and a derived `YTG = sum(May..Dec)`
  is added after `Q4`; all transformations occur in a single in-memory pandas
  DataFrame (no intermediate spreadsheet output); the 26-column normalized DataFrame is
  persisted to the SQLite database at `--output`, into the table named per
  `--table-name`, via `to_sql(..., if_exists="replace", index=False)`; a
  validation/tie-out summary is printed to stdout; the process exits zero.
- Alternate/edge flows:
  - Replace-existing-table: if a table of the same name already exists in the
    destination SQLite database, `to_sql(if_exists="replace", ...)` drops and rewrites
    it before persisting the new rows; re-running against an existing table produces no
    row duplication.
  - Singleton key passes through unchanged; a key appearing 3+ times sums all matching
    rows; NaN month cells are treated as 0; first-appearance order is preserved with no
    alphabetical or KEY sorting.
- Error handling and recovery behavior:
  - Missing `--output`: the CLI does not provide a default output path; invocation
    without `--output` exits non-zero.
  - Schema mismatch (missing, extra, or out-of-order column) raises a clear error that
    names the offending columns and exits non-zero.
  - Tie-out failure (output-row-count != unique keys, any per-column source/output
    tie-out outside `1e-6`, or `FY != sum(months)` on any row) raises and exits
    non-zero.
  - Errors are surfaced fail-fast via `ValueError` (or a dedicated exception subclass)
    rather than silently ignored; `main` maps the failure to a non-zero exit code.

## Inputs / Outputs

- Inputs (CLI flags, files, env vars):
  - Positional `<input.xlsx>` — path to the source Excel workbook.
  - `--output <path.db>` — REQUIRED; destination path to a SQLite database file
    (e.g. `.db`/`.sqlite`). There is no default; a missing `--output` exits non-zero.
  - `--source-sheet <name>` — source worksheet name.
  - `--table-name <name>` — name of the SQLite table to persist.
- Outputs (artifacts, logs, telemetry):
  - SQLite: a table named per `--table-name` in the database at `--output`, containing
    the 26 target columns in exact order, one row per unique KEY.
  - stdout: tie-out summary (source rows, unique keys, output rows, per-month/FY/
    quarter tie-outs, and first/middle/last output rows for spot-checking).
  - Exit code: zero on success; non-zero on missing `--output`, schema failure, or
    tie-out failure.
- Config keys and defaults:
  - `--source-sheet` default `"LE-8 + 4"`.
  - `--table-name` default `LE`.
  - `--output` is REQUIRED and has no default; it must point at a SQLite database file.
- Versioning or backward-compatibility constraints: the source and target schemas are
  fixed 26-column contracts in exact A..Z order; the header typo `SKU Descripiton` is
  preserved verbatim in both schemas.

## API / CLI Surface

Invocation (Poetry console-script entry point `normalize-le`, declared under
`[tool.poetry.scripts]`):

```
poetry run normalize-le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE]
```

Public functions (per the research module layout):

- `coerce_sku(val) -> str` — Excel-compatible SKU coercion: whole-number SKUs render as
  integer strings (no decimals/separators); non-numeric codes preserved verbatim.
- `rebuild_key(customer, sku, type_) -> str` — concatenates `Customer + coerce_sku(SKU #)
  + Type` with no separator; never trusts the loaded/cached `KEY` value.
- `validate_schema(columns) -> None` — confirms the 26 source columns in exact A..Z
  order; raises a column-naming error on mismatch.
- `load_source(path, sheet_name, ...) -> pd.DataFrame` — I/O boundary; reads with
  `header=2`, drops blank-`Customer` rows.
- `normalize(df) -> pd.DataFrame` — pure transform: collapse by KEY, build target
  schema.
- `compute_ytg(df) -> pd.Series` — derived `YTG = sum(May..Dec)` on the output row.
- `validate_tieouts(source_df, output_df) -> None` — enforces row-count, per-column
  tie-outs within `1e-6`, and `FY == sum(months)`; raises on failure.
- `write_sqlite(df, dest, table_name) -> None` — I/O boundary; persists the normalized
  DataFrame to the SQLite database at `dest` via
  `df.to_sql(table_name, conn, if_exists="replace", index=False)`.
- `main(argv: list[str] | None = None) -> int` — CLI entry point returning an exit code.

- Example invocations with expected outputs (concise):
  - `poetry run normalize-le book.xlsx --output le.db` — persists table `LE` to
    `le.db`, prints tie-out summary, exits 0.
  - `poetry run normalize-le book.xlsx` (no `--output`) — exits non-zero (output is
    required).
  - `poetry run normalize-le bad.xlsx --output le.db` (schema mismatch) — prints the
    missing/extra columns and exits non-zero.
- Contracts and validation rules: `--output` is required and must be a SQLite database
  path. The literal column headers (including the space in `SKU Descripiton` and the
  `#` in `SKU #`) and the table name are preserved as-is; pandas `to_sql` quotes column
  names so they round-trip without modification. Source schema and tie-outs are
  validated as described above.

## Data & State

This feature introduces a pure data transform that reads an Excel workbook and
persists the normalized result to a SQLite database with no persistent state beyond
the written table.

- Source schema — sheet `LE-8 + 4`, two leading non-data rows, Excel row 3 is the
  header, data from row 4; 26 columns A..Z in exact order:

  | Col | Header | Type | Notes |
  |-----|--------|------|-------|
  | A | `KEY` | text | Excel `=C&E&F`; rebuild, never trust loaded value. |
  | B | `YTD/YTG` | text | `"YTD"` or `"YTG"`; not part of the key. |
  | C | `Customer` | text | |
  | D | `SKU Descripiton` | text | Typo intentional; preserve verbatim. |
  | E | `SKU #` | mixed | Usually integer; sometimes a string code. |
  | F | `Type` | text | e.g. `Gross Sales`, `Off Invoice`, `PPD`, `Lbs`. |
  | G | `GtN Mapping` | text | Roll-up label. |
  | H–S | `Jan`..`Dec` | numeric | 12 monthly value columns. |
  | T | `FY` | numeric | SUM(H:S) per row. |
  | U | `Q1` | numeric | SUM(Jan-Mar). |
  | V | `Q2` | numeric | SUM(Apr-Jun). |
  | W | `Q3` | numeric | SUM(Jul-Sep). |
  | X | `Q4` | numeric | SUM(Oct-Dec). |
  | Y | `Super Category` | text | |
  | Z | `PPG` | text | |

- Target schema — SQLite table (default name `LE`), 26 columns A..Z in exact order:

  ```
  KEY, Customer, SKU Descripiton, SKU #, Type, GtN Mapping,
  Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
  FY, Q1, Q2, Q3, Q4, YTG, Super Category, PPG
  ```

  `YTD/YTG` is dropped; derived `YTG` is added after `Q4`, before `Super Category`.

- Persistence invariant: the normalized DataFrame is persisted with
  `to_sql(table_name, conn, if_exists="replace", index=False)`. The row index is not
  persisted; an existing table of the same name is dropped and rewritten; the 26 target
  columns are persisted in exact order, one row per unique KEY.

- Data transformations and invariants:
  - Collapse-by-KEY: text columns taken from the first matching source row per KEY;
    `Jan..Dec`, `FY`, `Q1..Q4` summed across all rows sharing a KEY (blanks treated as 0,
    `groupby(sort=False)` with default `min_count=0`).
  - Super Category <- PPG quirk: both `Super Category` and `PPG` output columns are
    populated from the source `PPG` column and are identical per row. This is an
    invariant to preserve, not a defect to correct.
  - Float64 no-rounding invariant: numeric values preserve float64 precision; no rounding
    is applied; tie-outs use a `1e-6` tolerance.
  - First-appearance ordering invariant: one row per unique KEY in first-appearance order;
    no alphabetical or KEY sorting.
- Caching or persistence details: the only persisted artifact is the SQLite table at
  `--output`; an existing table of the same name is replaced on each run.
- Migration or backfill requirements (if any): none.

## Constraints & Risks

- Limits and acceptable trade-offs:
  - The source workbook is unavailable during development; the script is built to the
    documented schema contract and validated with synthetic in-memory fixtures.
  - Temp files are prohibited in tests; the Excel read fixture uses in-memory
    `io.BytesIO` for `pd.read_excel`, and the SQLite persist round-trip uses an
    in-memory or test-scoped database via `sqlite3.connect(":memory:")` so no temp
    files are created.
  - openpyxl may return the `KEY` formula string, a cached value, or `None`; the script
    must always rebuild `KEY`.
- Security/privacy considerations: local file I/O only (Excel read, SQLite write); no
  network or external process access. Source data is planning data handled entirely
  in-process.
- Operational/rollout risks and mitigations:
  - New runtime dependencies `pandas` and `openpyxl` (and transitive `numpy`) are
    introduced; `openpyxl` remains the Excel read engine used by pandas. `sqlite3` is
    in the Python standard library, so the SQLite sink adds no new dependency.
    `hypothesis` is added as a dev dependency for T2 property tests.
  - Risk: divergence from the as-built workbook if the Super Category/PPG quirk or the
    `SKU Descripiton` typo is "corrected." Mitigation: both are encoded as explicit
    invariants and asserted by tests.

## Implementation Strategy

- Implementation scope: add `src/normalize_le.py` (pure transform plus thin I/O
  boundaries and a CLI entry point); keep the file under 500 lines, extracting helpers
  into `src/_normalize_le_helpers.py` if needed. Add `tests/test_normalize_le.py`.
- New classes/functions/commands to add: `coerce_sku`, `rebuild_key`, `validate_schema`,
  `load_source`, `normalize`, `compute_ytg`, `validate_tieouts`, `write_sqlite`,
  `print_summary`, `main` (per the research layout).
- Dependency changes and rationale: add `pandas >=2.2,<3.0` and `openpyxl >=3.1,<4.0` as
  runtime dependencies (pandas for the transform, openpyxl as the Excel read engine used
  by pandas); add `hypothesis >=6.100,<7.0` as a dev dependency (T2 requires >=1 property
  test per pure function). numpy is pulled transitively by pandas and is not pinned
  explicitly unless CI surfaces a conflict. `sqlite3` is in the Python standard library
  and adds no new dependency for the SQLite sink.
- Logging/telemetry additions and locations: no logging framework; behavior is fail-fast
  via raised `ValueError`/exception with a clear message plus a non-zero exit code from
  `main`. The tie-out summary is printed to stdout by `print_summary`.
- Rollout plan: classified T2 — Core. The module is a pure transform with no `datetime`,
  `time`, or `random` usage, so no Clock interface or seeded RNG is required. No feature
  flag is needed; the script is invoked directly.

## Definition of Done

- [x] Acceptance criteria documented and mapped to tests or demos
  - CLI/defaults/required-`--output` → CLI tests for custom flags; missing-`--output`
    non-zero exit test.
  - `header=2`, blank-`Customer` drop, schema validation → schema-validation unit tests
    (missing/extra/out-of-order) and load tests.
  - `coerce_sku`/KEY rebuild → `coerce_sku` unit + property tests; `rebuild_key` tests.
  - Target column order / one-row-per-KEY / first-appearance → `normalize` unit + property
    tests.
  - First-row text + summed numerics (blanks as 0) → `normalize` aggregation tests.
  - `YTG = sum(May..Dec)` on output → `compute_ytg` unit + property tests.
  - Super Category/PPG quirk → quirk-invariant test asserting both equal source `PPG`.
  - Tie-out validation (row-count, `1e-6`, `FY == sum(months)`) → `validate_tieouts` pass
    and failure tests; non-zero exit assertion.
  - stdout summary → `print_summary`/`main` test with `capsys`.
  - SQLite persist + replace-if-exists → `sqlite3.connect(":memory:")` round-trip
    integration test asserting columns, order, and row count; re-run replaces table with
    no row duplication.
- [x] Behavior matches acceptance criteria in all documented environments
- [x] Tests updated/added (unit/integration as applicable)
- [x] Edge cases and error handling covered by tests
- [x] Docs updated (README, docs/features/active/... links)
- [x] Telemetry/logging added or updated (if applicable) — N/A: CLI summary uses `print` by design; no library logging applicable
- [x] Toolchain pass completed (format → lint → type-check → test)
