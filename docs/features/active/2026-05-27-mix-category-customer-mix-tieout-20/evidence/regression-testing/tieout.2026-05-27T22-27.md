# Per-Layer Mix Tie-Out (Issue #20, AC8)

Timestamp: 2026-05-27T22-27

Command: compare each `artifacts/mix.db` mix-layer mix-column total to the corresponding
workbook TopDown table total (relative tolerance < 1e-6), via an in-memory openpyxl +
sqlite3 read. Per-layer pass/fail only; no confidential figures recorded.

EXIT_CODE: 0

## Mapping (DB column -> workbook TopDown source)
- `mix_1_sku["SKU Mix"]` -> `2-SKU-Mix-TopDown` (Calc Net Price Impact minus Rate-Rollup-1).
- `mix_2_category["Category Mix"]` -> `3-Category-Mix-TopDown` (Category Mix column).
- `mix_3_customer["Customer Mix"]` -> `4-Customer-Mix-TopDown` (the workbook's mislabeled
  "Category Mix" column, which is the customer-layer mix per the issue #9 rename).
- `mix_4_country["Country Mix"]` -> `5-Country-Mix` (Country Mix column).

## Per-layer result (pass/fail only)
| Layer | Tie-out |
|---|---|
| SKU | PASS |
| Category | PASS |
| Customer | PASS |
| Country | PASS |

All four mix-layer column totals tie out to their workbook TopDown totals within a relative
tolerance of 1e-6. The SKU and Country layers were already tied out before the fix; the
Category and Customer layers now tie out as a result of the issue #20 fix (re-sourcing the
coarser layers from the unfiltered `mix_base`). No confidential figures are disclosed.
