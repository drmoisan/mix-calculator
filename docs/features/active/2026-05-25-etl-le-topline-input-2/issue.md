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
- Resolves the source columns to the expected schema without depending on exact
  positions (see "Column resolution" below): matches first by position, then by
  normalized fuzzy match for any columns whose positions do not line up; halts only
  when a required expected column cannot be matched; logs a warning and continues
  when all required columns are matched but extra columns remain.
- Establishes the `KEY` column (see "KEY handling" below): if the source has no
  `KEY` column, creates it by concatenating `Customer + coerce_sku(SKU #) + Type`;
  if a `KEY` column is present and its values match that expected pattern, trusts and
  keeps it; if a `KEY` column is present but its values do not match the pattern,
  resolves the conflict per `--key-mismatch` (prompt the user when interactive,
  otherwise fail fast).
- Fills blank `FY`/`Q1..Q4` totals from their monthly components before collapsing:
  the source omits these totals on some rows even though they are definitionally the
  sum of their months, and a blank total reads as 0 and breaks the per-row tie-out. A
  blank `FY` is filled with `sum(Jan..Dec)` and a blank `Qn` with the sum of its three
  months; populated totals are left unchanged (NaN months count as 0).
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
poetry run normalize-le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE] \
  [--key-mismatch {prompt,trust,overwrite}]
```

Defaults: `--source-sheet="LE-8 + 4"`, `--table-name=LE`,
`--key-mismatch=prompt`. `--output` is REQUIRED and must point at a SQLite database
file (e.g. `.db`/`.sqlite`); there is no default output path. The input remains an
Excel workbook read from `--source-sheet`.

### Column resolution (position-independent)

Extraction must not depend on the columns being in their documented positions. The
expected source columns are resolved as follows:

1. Position pass: for each expected column, if the actual column at the same index
   has a matching name (compared after normalization — case-folded, with spaces and
   punctuation removed), bind it.
2. Fuzzy pass: for each still-unbound expected column, match it against the remaining
   unbound actual columns by normalized exact match first, then by a similarity score
   (`difflib.SequenceMatcher` on normalized names) with a threshold of `>= 0.85`.
3. Missing: if any required expected column remains unmatched after the fuzzy pass,
   halt with a clear error naming the unmatched expected column(s).
4. Extras: if every required expected column is matched but unmatched actual columns
   remain, log a warning naming the extra column(s) and continue.

After resolution the working frame is selected and renamed to the canonical expected
names, so all downstream logic uses canonical names regardless of source order. The
`KEY` column is optional in the source and is resolved by name only (no fuzzy match),
then handled per "KEY handling".

### KEY handling

- If no `KEY` column is present in the source, create it as
  `Customer + coerce_sku(SKU #) + Type`.
- If a `KEY` column is present and every value equals that expected pattern
  (the rebuilt concatenation), trust the existing column and continue.
- If a `KEY` column is present but one or more values do not match the expected
  pattern, resolve per `--key-mismatch`:
  - `trust`: keep the existing `KEY` values; log a warning.
  - `overwrite`: replace with the rebuilt pattern; log a warning.
  - `prompt` (default): when stdin is an interactive TTY, ask the user to choose
    trust or overwrite; when stdin is not interactive (automation/CI), do not block —
    fail fast with a non-zero exit instructing the caller to pass
    `--key-mismatch trust|overwrite`.

### Source schema: sheet `LE-8 + 4`

Two leading non-data rows; Excel row 3 (1-indexed) is the header row; data starts
on row 4. The documented header order is below, but it is the canonical reference for
matching — extraction does not require columns to be in these exact positions (see
"Column resolution"). `KEY` is optional in the source; every other listed column is
required.

| Col | Header           | Type    | Notes |
|-----|------------------|---------|-------|
| A   | `KEY`            | text    | Optional; Excel formula `=C&E&F`. Created when absent; trusted when its values match the pattern; otherwise resolved per `--key-mismatch`. |
| B   | `YTD/YTG`        | text    | `"YTD"` or `"YTG"`. Not part of the key. |
| C   | `Customer`       | text    | |
| D   | `SKU Descripiton`| text    | Typo intentional; preserve verbatim. |
| E   | `SKU #`          | mixed   | Usually integer; sometimes a string code. |
| F   | `Type`           | text    | e.g. `Gross Sales`, `Off Invoice`, `PPD`, `Lbs`. |
| G   | `GtN Mapping`    | text    | Roll-up label. |
| H–S | `Jan`..`Dec`     | numeric | 12 monthly value columns. |
| T   | `FY`             | numeric | SUM(H:S) per row. May be blank; filled with `sum(Jan..Dec)` when blank. |
| U   | `Q1`             | numeric | SUM(Jan-Mar). May be blank; filled with `sum(Jan..Mar)` when blank. |
| V   | `Q2`             | numeric | SUM(Apr-Jun). May be blank; filled with `sum(Apr..Jun)` when blank. |
| W   | `Q3`             | numeric | SUM(Jul-Sep). May be blank; filled with `sum(Jul..Sep)` when blank. |
| X   | `Q4`             | numeric | SUM(Oct-Dec). May be blank; filled with `sum(Oct..Dec)` when blank. |
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
- [x] Source load uses `header=2` and drops rows with blank `Customer`.
- [x] Column resolution does not depend on positions: expected columns are matched
      first by position (normalized name equality at the same index), then unmatched
      expected columns are resolved against remaining actual columns by normalized
      equality and then `difflib` similarity `>= 0.85`. After resolution the frame is
      renamed to canonical expected names.
- [x] If any required expected column cannot be matched after the fuzzy pass, the run
      halts with a clear error naming the unmatched expected column(s).
- [x] If every required expected column is matched but extra actual columns remain,
      a warning naming the extra column(s) is logged and the run continues.
- [x] `coerce_sku` renders whole-number SKUs as integer strings (no
      decimals/separators) and preserves non-numeric SKU codes (e.g. `RGFBOWLCB`,
      `NotSKU`) verbatim; the rebuilt pattern is `Customer + coerce_sku(SKU #) + Type`.
- [x] `KEY` handling: when the source has no `KEY` column it is created from the
      rebuilt pattern; when present and all values equal the pattern it is trusted;
      when present and values diverge it is resolved per `--key-mismatch`
      (`trust`/`overwrite` log a warning; `prompt` asks interactively on a TTY and
      fails fast with a non-zero exit when stdin is not interactive).
- [x] Output has 26 columns A..Z in the exact target order, one row per unique KEY,
      in first-appearance order; `YTD/YTG` is absent and a derived `YTG` column is
      present after `Q4` and before `Super Category`.
- [x] Text columns are taken from the first source row per KEY; `Jan..Dec`, `FY`,
      `Q1..Q4` are summed across all rows sharing a KEY (blanks treated as 0).
- [x] `YTG` = sum(May..Dec) computed on the output row, not from source.
- [x] `Super Category` and `PPG` are both populated from the source `PPG` column
      (the as-built quirk) and are identical per row.
- [ ] Blank `FY`/`Q1..Q4` cells in the source are filled from their monthly
      components before collapsing (`FY <- sum(Jan..Dec)`, `Qn <- sum(its months)`);
      populated totals are left unchanged and NaN months count as 0.
- [x] Validation enforces output-row-count == unique keys, per-column source/output
      tie-outs within `1e-6`, `FY == sum(months)` per row, and `Qn == sum(its months)`
      per row; failures raise and exit non-zero.
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
- Excel/openpyxl may return the `KEY` formula string, a cached value, or `None`. The
  script does not blindly trust a loaded `KEY`: it is created when absent, trusted
  only when its values match the rebuilt pattern, and otherwise resolved per
  `--key-mismatch`.
- Fuzzy matching carries a mis-mapping risk: a similarity threshold that is too low
  could bind two genuinely different columns. The threshold is fixed at `>= 0.85` and
  applied to normalized names; the position and normalized-equality passes run first
  so well-formed inputs never reach the similarity step.
- The interactive `--key-mismatch prompt` path must never block automation: it prompts
  only when stdin is an interactive TTY and otherwise fails fast with guidance.
- Float precision must be preserved (no rounding); tie-outs use a `1e-6` tolerance.
- New runtime dependencies (`pandas`, `openpyxl`, `numpy`) are introduced; `openpyxl`
  is the Excel read engine. `sqlite3`, `difflib`, and `logging` are in the Python
  standard library (no new dependency for the SQLite sink, fuzzy matching, or warning
  logs).
- Header typo `SKU Descripiton` must be preserved verbatim. Note: the persisted
  column header `SKU #` and the SQLite table name per `--table-name` must be valid
  identifiers for SQLite; pandas `to_sql` quotes column names, so the literal
  headers (including the space and `#`) are preserved.

## Test Conditions

- [x] Unit coverage areas: `coerce_sku` (int, np.integer, integer-valued float,
      non-integer float, NaN, string code); KEY rebuild; column resolution
      (exact-by-position; reordered columns resolved by name; a typo/variant resolved
      by fuzzy `>= 0.85`; a required column unmatched -> halt; extra columns -> warn
      and continue); KEY handling (absent -> created; present-and-matching -> trusted;
      present-and-diverging -> trust/overwrite/prompt resolution; non-TTY prompt ->
      fail fast); normalize aggregation (singleton KEY, 2-row YTD+YTG pair, 3+ rows
      per KEY); `YTG` derivation; `Super Category`/`PPG` quirk; tie-out validation
      pass and failure paths.
- [x] Edge cases: trailing blank `Customer` rows dropped; KEY appearing only once
      passes through; KEY appearing 3+ times sums all; non-numeric SKU codes
      preserved; NaN month cells treated as 0; no alphabetical/KEY sorting; columns
      supplied in a shuffled order still resolve; a source with no `KEY` column.
- [x] Integration scenarios: round-trip persist to a SQLite database and read the
      table back to assert columns, order, and row count; re-running against an
      existing table replaces it (no row duplication); schema-mismatch input produces
      a non-zero exit with a descriptive message; missing `--output` produces a
      non-zero exit.
- [x] CLI/API examples: invocation with `--output <path.db>`; custom
      `--source-sheet` and `--table-name`.

## Anti-requirements (must NOT do)

- Do not pull `Super Category` from the source `Super Category` column.
- Do not include `YTD/YTG` in the output or in the KEY.
- Do not sort the output alphabetically or by KEY (preserve first-appearance order).
- Do not round numeric values (preserve float64 precision).
- Do not change the `SKU Descripiton` header typo.
