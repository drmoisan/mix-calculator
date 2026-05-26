# etl-le-topline-input (Issue #2)

- Date captured: 2026-05-25
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/etl-le-topline-input/ (Issue #2)

- Issue: #2
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/2
- Last Updated: 2026-05-26
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
- Writes the result to sheet `LE84Data` as a real Excel Table named `LE`
  (`A1:Z<n+1>`), replacing the sheet if it already exists; writes CSV instead when
  `--output` ends in `.csv`.
- Prints a validation/tie-out summary to stdout and exits non-zero on any schema or
  tie-out failure.

CLI:

```
python normalize_le.py <input.xlsx> [--output <path>] \
  [--source-sheet "LE-8 + 4"] [--output-sheet LE84Data] [--table-name LE]
```

Defaults: `--source-sheet="LE-8 + 4"`, `--output-sheet=LE84Data`,
`--table-name=LE`, `--output`=input path (write the new sheet back into the same
workbook).

## Acceptance Criteria (early draft)

- [ ] `normalize_le.py` exposes the documented CLI with the listed defaults; output
      defaults to the input path; `.csv` output skips Excel-table formatting.
- [ ] Source load uses `header=2`, drops rows with blank `Customer`, and validates
      the 26 source columns A..Z in exact order, failing with a clear error that
      names missing/extra columns on mismatch.
- [ ] `KEY` is rebuilt from `Customer + coerce_sku(SKU #) + Type`; whole-number SKUs
      render as integer strings (no decimals/separators); non-numeric SKU codes
      (e.g. `RGFBOWLCB`, `NotSKU`) are preserved verbatim.
- [ ] Output has 26 columns A..Z in the exact target order, one row per unique KEY,
      in first-appearance order; `YTD/YTG` is absent and a derived `YTG` column is
      present after `Q4` and before `Super Category`.
- [ ] Text columns are taken from the first source row per KEY; `Jan..Dec`, `FY`,
      `Q1..Q4` are summed across all rows sharing a KEY (blanks treated as 0).
- [ ] `YTG` = sum(May..Dec) computed on the output row, not from source.
- [ ] `Super Category` and `PPG` are both populated from the source `PPG` column
      (the as-built quirk) and are identical per row.
- [ ] Validation enforces output-row-count == unique keys, per-column source/output
      tie-outs within `1e-6`, and `FY == sum(months)` per row; failures raise and
      exit non-zero.
- [ ] stdout prints source rows, unique keys, output rows, per-month/FY/quarter
      tie-outs, and first/middle/last output rows for spot-checking.
- [ ] Excel output writes sheet `LE84Data` with a real Excel Table named per
      `--table-name` (`A1:Z<n+1>`, `TableStyleMedium2`, row stripes), replacing the
      sheet if it already exists.

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
  is already implied by Excel I/O and the others are widely-used, well-maintained
  packages.
- Header typo `SKU Descripiton` must be preserved verbatim in both schemas.

## Test Conditions to Consider

- [ ] Unit coverage areas: `coerce_sku` (int, np.integer, integer-valued float,
      non-integer float, NaN, string code); KEY rebuild; schema validation
      (missing column, extra column, out-of-order column); normalize aggregation
      (singleton KEY, 2-row YTD+YTG pair, 3+ rows per KEY); `YTG` derivation;
      `Super Category`/`PPG` quirk; tie-out validation pass and failure paths.
- [ ] Edge cases: trailing blank `Customer` rows dropped; KEY appearing only once
      passes through; KEY appearing 3+ times sums all; non-numeric SKU codes
      preserved; NaN month cells treated as 0; no alphabetical/KEY sorting.
- [ ] Integration scenarios: round-trip write of `LE84Data` sheet/table into an
      existing workbook (replace-if-exists); `.csv` output path; schema-mismatch
      input produces non-zero exit with descriptive message.
- [ ] CLI/API examples: default invocation; custom `--source-sheet`,
      `--output-sheet`, `--table-name`, `--output` (xlsx and csv).

## Anti-requirements (must NOT do)

- Do not pull `Super Category` from the source `Super Category` column.
- Do not include `YTD/YTG` in the output or in the KEY.
- Do not sort the output alphabetically or by KEY (preserve first-appearance order).
- Do not round numeric values (preserve float64 precision).
- Do not change the `SKU Descripiton` header typo.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/etl-le-topline-input/` folder from the template