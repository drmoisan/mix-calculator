# End-to-End Run (Issue #20, AC7)

Timestamp: 2026-05-27T22-27

Command: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db`

EXIT_CODE: 0

## Output Summary (table presence and row counts only; no confidential values)
The pipeline completed with exit code 0. Tables written:
- LE (import), aop (import)
- le_wide: 3864 rows
- aop_wide: 3135 rows
- customer_lu: 17 rows
- aop_norm: 3135 rows
- le_norm: 3864 rows
- aop_vs_le: 4046 rows
- mix_base: 1152 rows
- rate_impacts: 112 rows
- mix_rollup_1: 37 rows
- mix_1_sku: 38 rows
- mix_rollup_2: 15 rows
- mix_2_category: 15 rows
- mix_rollup_3: 1 row
- mix_3_customer: 1 row
- mix_rollup_4: 1 row
- mix_4_country: 1 row
- mix_0_detail: 192 rows
- mix_2_sku_bottomsup: 192 rows (from the merged BottomsUp feature, PR #22)
- mix_3_category_bottomsup: 54 rows (merged feature)
- mix_4_customer_bottomsup: 18 rows (merged feature)
- q1_results_by_sku: 276 rows
- nrr_summary: 20 rows

## Required-table presence (AC7)
- mix_1_sku: PRESENT
- mix_2_category: PRESENT
- mix_3_customer: PRESENT
- mix_4_country: PRESENT
- nrr_summary: PRESENT

Note: a non-fatal WARNING about duplicate AOP KEY values is emitted by the loader; it is
informational ("not a failure") and does not affect the exit code or the tables written.

The confidential workbook `artifacts/LE v AOP Gross to Net Decomp.xlsx` was present and
readable in the execution environment; no confidential figures are recorded here.
