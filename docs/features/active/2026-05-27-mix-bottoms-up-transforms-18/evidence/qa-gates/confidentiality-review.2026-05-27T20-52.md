# QA Gate — Confidentiality Review (AC13)

Timestamp: 2026-05-27T20-52

## Files reviewed

- `tests/test_mix_bottomsup.py` (new)
- `tests/mix_bottomsup_fixtures.py` (new; holds all fabricated fixtures)
- `tests/test_mix_pipeline.py` (changed; `_DERIVED_TABLES` extension and docstring count)
- `src/mix_bottomsup.py`, `src/_mix_bottomsup_helpers.py`, `src/mix_pipeline_run.py`
  (new/changed production files, reviewed for incidental data leakage)

## Findings

- Identifier tokens present in the test and fixture files are all fabricated:
  `SKU-001`..`SKU-005`, `SKU-099`, `Widget` descriptions (derived as `Widget <last
  char of SKU>`), `Category X` / `Category Y` / `Category Z`, customer `Acme Foods`,
  and the country values `US` / `Canada` (the spec states `US`/`Canada` are not
  secret).
- No `SKU Description`, `Category`, customer name, or measure value traceable to
  `artifacts/LE v AOP Gross to Net Decomp.xlsx` appears in any file.
- No new or changed file references, reads, or loads the confidential workbook. A
  search for `LE v AOP`, `Gross to Net Decomp`, and `.xlsx` across all new/changed
  files returned no matches.
- No task in this feature read or loaded `artifacts/LE v AOP Gross to Net Decomp.xlsx`.
  The production modules are pure transforms over in-memory DataFrames; all I/O
  remains in `src/pandas_io.py` (unchanged).

Output Summary: Only fabricated example data appears in the new and changed test and
fixture files; no confidential source value is present and the workbook was never
read. AC13 satisfied.
EXIT_CODE: 0
