# `etl-le-topline-input` — User Story

- Issue: #2
- Owner: Dan Moisan
- Status: Draft
- Last Updated: 2026-05-25

## Story Statement

- As an FP&A analyst, I want a self-contained script that normalizes the monthly LE
  workbook into one row per business key, so that I no longer depend on a fragile chain
  of in-workbook `XLOOKUP`/`SUMIF`/key-concatenation formulas.
- As an analyst who audits planning output, I want the normalization to fail fast with a
  clear message and a non-zero exit when the source schema or the tie-outs do not match,
  so that I can trust the output is faithful to the source before using it downstream.

## Problem / Why

The LE topline planning process produces a source sheet (`LE-8 + 4`) in which each
`(Customer, SKU #, Type)` tuple appears once for its year-to-date actuals (`YTD`) and once
for its year-to-go projection (`YTG`). Downstream analysis requires a single normalized
row per business key, with the YTD and YTG halves summed into a full-year line and a
derived `YTG` measure reflecting the "8 + 4" convention (Jan-Apr actual, May-Dec
projection). This normalization is currently performed by an in-workbook formula chain
that is difficult to audit, version, and run repeatably. The need is a defensive Python
script that reproduces the as-built transformation exactly on any workbook matching the
documented schema, including a known formula quirk that must be preserved rather than
corrected.

## Personas & Scenarios

- Persona: FP&A analyst
  - who the user is: a financial planning and analysis analyst responsible for the monthly
    LE topline refresh.
  - what they care about: output that matches the source workbook exactly and is auditable.
  - their constraints: works in Excel-centric workflows; needs a repeatable process; cannot
    tolerate silent divergence from the as-built numbers.
  - their goals and frustrations: wants to retire the fragile formula chain; frustrated by
    manual, error-prone key-concatenation and lookup formulas.
  - their context and motivations: runs the normalization once per planning cycle and feeds
    the normalized table into downstream analysis.
- Scenario: monthly LE normalization
  - who is acting? The FP&A analyst.
  - what triggered the action? A new monthly LE workbook is ready for normalization.
  - what steps do they take? They run `python -m src.normalize_le LE.xlsx --output le.db`.
    The script loads `LE-8 + 4` (header on Excel row 3), drops blank-`Customer` rows,
    rebuilds `KEY`, collapses rows by key (first-row text, summed numerics), derives
    `YTG = sum(May..Dec)`, validates tie-outs, and persists the normalized table to the
    SQLite database at `--output` (table named per `--table-name`, replacing it if it
    already exists).
  - what obstacles or decisions occur? If `--output` is omitted, the script exits
    non-zero (there is no default output path). If the source columns are missing, extra,
    or out-of-order, the script names the offending columns and exits non-zero. If any
    per-column tie-out exceeds `1e-6` or `FY != sum(months)`, it raises and exits non-zero.
  - what outcome do they expect? A SQLite table with one row per unique key in
    first-appearance order, a stdout tie-out summary they can spot-check (source rows,
    unique keys, output rows, per-month/FY/quarter tie-outs, first/middle/last rows), and a
    zero exit code.

## Acceptance Criteria

- [x] `src/normalize_le.py` exposes the documented CLI with the listed defaults;
      `--output` is required and must be a SQLite database path; SQLite is the only
      output sink (no Excel or CSV output).
- [x] Source load uses `header=2`, drops rows with blank `Customer`, and validates the 26
      source columns A..Z in exact order, failing with a clear error that names
      missing/extra columns on mismatch.
- [x] `KEY` is rebuilt from `Customer + coerce_sku(SKU #) + Type`; whole-number SKUs render
      as integer strings (no decimals/separators); non-numeric SKU codes (e.g. `RGFBOWLCB`,
      `NotSKU`) are preserved verbatim.
- [x] Output has 26 columns A..Z in the exact target order, one row per unique KEY, in
      first-appearance order; `YTD/YTG` is absent and a derived `YTG` column is present
      after `Q4` and before `Super Category`.
- [x] Text columns are taken from the first source row per KEY; `Jan..Dec`, `FY`, `Q1..Q4`
      are summed across all rows sharing a KEY (blanks treated as 0).
- [x] `YTG` = sum(May..Dec) computed on the output row, not from source.
- [x] `Super Category` and `PPG` are both populated from the source `PPG` column (the
      as-built quirk) and are identical per row.
- [x] Validation enforces output-row-count == unique keys, per-column source/output
      tie-outs within `1e-6`, and `FY == sum(months)` per row; failures raise and exit
      non-zero.
- [x] stdout prints source rows, unique keys, output rows, per-month/FY/quarter tie-outs,
      and first/middle/last output rows for spot-checking.
- [x] The normalized DataFrame is persisted to the SQLite database at `--output`
      via `to_sql(table, conn, if_exists="replace", index=False)`; an existing table
      of the same name is dropped and rewritten; the row index is not persisted; the
      persisted table has the 26 columns in the exact target order and one row per
      unique KEY.

## Non-Goals

- Do not pull `Super Category` from the source `Super Category` column; preserve the
  as-built quirk where both `Super Category` and `PPG` come from the source `PPG` column.
- Do not include `YTD/YTG` in the output or in the KEY.
- Do not sort the output alphabetically or by KEY; preserve first-appearance order.
- Do not round numeric values; preserve float64 precision.
- Do not change the `SKU Descripiton` header typo.
- No Excel/CSV output sink — SQLite only.
