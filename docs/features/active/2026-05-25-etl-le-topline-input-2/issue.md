# Feature: etl-le-topline-input

- Work Mode: full-feature
- Issue: #2
- Promotion Type: feature
- Source: docs/features/potential/2026-05-25-etl-le-topline-input.md

## Problem / Why

An Excel-based "LE" (Latest Estimate) topline planning process produces a source
sheet (`LE-8 + 4`) in which each `(Customer, SKU #, Type)` tuple appears once for
its year-to-date actuals (`YTD`) and once for its year-to-go projection (`YTG`).
Downstream analysis requires a single normalized row per business key, with the
YTD and YTG halves summed into a full-year line and a derived `YTG` measure that
reflects the "8 + 4" forecast convention (Jan-Apr actual, May-Dec projection).

This normalization is currently performed by a fragile chain of in-workbook Excel
formulas (`XLOOKUP`, `SUMIF`, key-concatenation formulas) that is difficult to
audit, version, and run repeatably. The need is a self-contained, defensive Python
script that reproduces the as-built transformation exactly on any workbook matching
the documented source schema, including a known formula quirk that must be preserved
rather than corrected.

## Proposed Behavior

Deliver a single-file Python CLI, `normalize_le.py` (Python 3.10+; dependencies
`pandas`, `openpyxl`, `numpy`), that:

- Loads the source sheet `LE-8 + 4`, treating Excel row 3 as the header row.
- Validates the source schema (columns A..Z in an exact documented order) and fails
  fast with a clear, column-naming error on any mismatch.
- Rebuilds the `KEY` column from `Customer + SKU# + Type` with Excel-compatible
  coercion (never trusting the loaded formula/cached value).
- Collapses all source rows sharing a `KEY` into one normalized row: text columns
  taken from the first matching row; month, `FY`, and quarter columns summed.
- Drops the `YTD/YTG` column and adds a derived `YTG` column = sum(May..Dec).
- Preserves the as-built quirk where both `Super Category` and `PPG` output columns
  are populated from the source `PPG` column.
- Holds the fully normalized result in a single in-memory pandas DataFrame; all
  transformations occur in pandas (no intermediate spreadsheet output).
- Persists the normalized DataFrame to a SQLite database at the required `--output`
  path, into a table named per `--table-name`, replacing the table if it already
  exists (drop-and-rewrite). SQLite is the only output sink.
- Prints a validation/tie-out summary to stdout and exits non-zero on any schema or
  tie-out failure.

CLI:

```
python -m src.normalize_le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE]
```

Defaults: `--source-sheet="LE-8 + 4"`, `--table-name=LE`. `--output` is REQUIRED and
must point at a SQLite database file (e.g. `.db`/`.sqlite`); there is no default
output path. The input remains an Excel workbook read from `--source-sheet`.

### Source schema: sheet `LE-8 + 4`

Two leading non-data rows; Excel row 3 (1-indexed) is the header row; data starts
on row 4. Expected header row, columns A..Z in this exact order:

| Col | Header           | Type    | Notes |
|-----|------------------|---------|-------|
| A   | `KEY`            | text    | Excel formula `=C&E&F`; rebuild, do not trust loaded value. |
| B   | `YTD/YTG`        | text    | `"YTD"` or `"YTG"`. Not part of the key. |
| C   | `Customer`       | text    | |
| D   | `SKU Descripiton`| text    | Typo intentional; preserve verbatim. |
| E   | `SKU #`          | mixed   | Usually integer; sometimes a string code. |
| F   | `Type`           | text    | e.g. `Gross Sales`, `Off Invoice`, `PPD`, `Lbs`. |
| G   | `GtN Mapping`    | text    | Roll-up label. |
| H–S | `Jan`..`Dec`     | numeric | 12 monthly value columns. |
| T   | `FY`             | numeric | SUM(H:S) per row. |
| U   | `Q1`             | numeric | SUM(Jan-Mar). |
| V   | `Q2`             | numeric | SUM(Apr-Jun). |
| W   | `Q3`             | numeric | SUM(Jul-Sep). |
| X   | `Q4`             | numeric | SUM(Oct-Dec). |
| Y   | `Super Category` | text    | |
| Z   | `PPG`            | text    | |

### Target schema: SQLite table (default name `LE`)

The normalized DataFrame has 26 columns in this exact order, persisted as the
columns of the SQLite table:

```
KEY, Customer, SKU Descripiton, SKU #, Type, GtN Mapping,
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
FY, Q1, Q2, Q3, Q4, YTG, Super Category, PPG
```

`YTD/YTG` is dropped; a derived `YTG` column is added after `Q4`, before
`Super Category`. One row per unique KEY in first-appearance order. The DataFrame
is written with `to_sql(..., if_exists="replace", index=False)` so the row index is
not persisted and an existing table of the same name is dropped and rewritten.

## Acceptance Criteria

- [x] `src/normalize_le.py` exposes the documented CLI with the listed defaults;
      `--output` is required and must be a SQLite database path; SQLite is the only
      output sink (no Excel or CSV output).
- [x] Source load uses `header=2`, drops rows with blank `Customer`, and validates
      the 26 source columns A..Z in exact order, failing with a clear error that
      names missing/extra columns on mismatch.
- [x] `KEY` is rebuilt from `Customer + coerce_sku(SKU #) + Type`; whole-number SKUs
      render as integer strings (no decimals/separators); non-numeric SKU codes
      (e.g. `RGFBOWLCB`, `NotSKU`) are preserved verbatim.
- [x] Output has 26 columns A..Z in the exact target order, one row per unique KEY,
      in first-appearance order; `YTD/YTG` is absent and a derived `YTG` column is
      present after `Q4` and before `Super Category`.
- [x] Text columns are taken from the first source row per KEY; `Jan..Dec`, `FY`,
      `Q1..Q4` are summed across all rows sharing a KEY (blanks treated as 0).
- [x] `YTG` = sum(May..Dec) computed on the output row, not from source.
- [x] `Super Category` and `PPG` are both populated from the source `PPG` column
      (the as-built quirk) and are identical per row.
- [x] Validation enforces output-row-count == unique keys, per-column source/output
      tie-outs within `1e-6`, and `FY == sum(months)` per row; failures raise and
      exit non-zero.
- [x] stdout prints source rows, unique keys, output rows, per-month/FY/quarter
      tie-outs, and first/middle/last output rows for spot-checking.
- [x] The normalized DataFrame is persisted to the SQLite database at `--output`
      via `to_sql(table, conn, if_exists="replace", index=False)`; an existing table
      of the same name is dropped and rewritten; the row index is not persisted; the
      persisted table has the 26 columns in the exact target order and one row per
      unique KEY.

## Constraints & Risks

- The source workbook is not available during development; the script must be built
  to the documented schema contract and validated with synthetic fixtures that match
  that schema.
- The `Super Category` <- `PPG` mapping is a deliberate as-built quirk; "correcting"
  it would diverge from the source workbook and is explicitly prohibited.
- Excel/openpyxl may return the `KEY` formula string, a cached value, or `None`;
  the script must always rebuild `KEY` rather than trust the loaded value.
- Float precision must be preserved (no rounding); tie-outs use a `1e-6` tolerance.
- New runtime dependencies (`pandas`, `openpyxl`, `numpy`) are introduced; `openpyxl`
  is the Excel read engine. `sqlite3` is in the Python standard library (no new
  dependency for the SQLite sink).
- Header typo `SKU Descripiton` must be preserved verbatim. Note: the persisted
  column header `SKU #` and the SQLite table name per `--table-name` must be valid
  identifiers for SQLite; pandas `to_sql` quotes column names, so the literal
  headers (including the space and `#`) are preserved.

## Test Conditions

- [ ] Unit coverage areas: `coerce_sku` (int, np.integer, integer-valued float,
      non-integer float, NaN, string code); KEY rebuild; schema validation
      (missing column, extra column, out-of-order column); normalize aggregation
      (singleton KEY, 2-row YTD+YTG pair, 3+ rows per KEY); `YTG` derivation;
      `Super Category`/`PPG` quirk; tie-out validation pass and failure paths.
- [ ] Edge cases: trailing blank `Customer` rows dropped; KEY appearing only once
      passes through; KEY appearing 3+ times sums all; non-numeric SKU codes
      preserved; NaN month cells treated as 0; no alphabetical/KEY sorting.
- [ ] Integration scenarios: round-trip persist to a SQLite database and read the
      table back to assert columns, order, and row count; re-running against an
      existing table replaces it (no row duplication); schema-mismatch input produces
      a non-zero exit with a descriptive message; missing `--output` produces a
      non-zero exit.
- [ ] CLI/API examples: invocation with `--output <path.db>`; custom
      `--source-sheet` and `--table-name`.

## Anti-requirements (must NOT do)

- Do not pull `Super Category` from the source `Super Category` column.
- Do not include `YTD/YTG` in the output or in the KEY.
- Do not sort the output alphabetically or by KEY (preserve first-appearance order).
- Do not round numeric values (preserve float64 precision).
- Do not change the `SKU Descripiton` header typo.
