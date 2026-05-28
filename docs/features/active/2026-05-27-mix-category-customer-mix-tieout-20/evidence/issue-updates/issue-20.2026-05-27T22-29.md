# Issue #20 Update Mirror

Timestamp: 2026-05-27T22-29

PostedAs: comment

Comment URL: https://github.com/drmoisan/mix-calculator/issues/20#issuecomment-4560335312

---

## Exact text posted

## Issue #20 — Category/Customer mix tie-out fix: complete

The coarser mix layers (`mix_2_category`, `mix_3_customer`, `mix_4_country`) were re-aggregating the already-filtered prior layer, so single-scenario lines (zero AOP Lbs / nonzero LE Lbs and the reverse) dropped by the SKU-layer nonzero-Lbs filter never reached the coarser aggregates. The fix re-sources each coarser layer from the unfiltered `mix_base` at its own granularity (`{Customer, Country}`, `{Country}`, all-rows), while keeping the rollup-subtraction target as the summed prior finer layer's `Calc Net Price Impact`. The now-unused `unstack_to_long` helper (and its test) were removed.

### Outcome
- End-to-end run (`poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db`): exit 0; `mix_1_sku`, `mix_2_category`, `mix_3_customer`, `mix_4_country`, and `nrr_summary` all written.
- `nrr_summary` reconciliation `Check`: resolves to `"CHECK"` (was `"ERROR"`).

### Four-layer tie-out to workbook TopDown totals (pass/fail only; no confidential figures)
| Layer | Tie-out |
|---|---|
| SKU | PASS |
| Category | PASS |
| Customer | PASS |
| Country | PASS |

### Quality gates
- Black, Ruff, Pyright: clean (exit 0 each).
- Pytest: 220 passed, 0 failed; 100% line / 100% branch coverage. New deterministic regression tests cover single-scenario volume retention and the NPI-minus-rollup identity (fabricated inputs; no temp files/network).
- Changed-code coverage: 100% line / 100% branch; no regression on changed lines.

### Scope notes / deviations
- `mix_1_sku` unchanged; `mix_3_customer["Customer Mix"]` column name and `mix_4_country` single-row shape preserved.
- During execution, an external merge (PR #22, BottomsUp feature) landed on this branch. Its `build_chain` test fixture used the pre-fix builder signatures, causing 13 BottomsUp unit tests to fail. The fixture was reconciled to pass `mix_base` to the changed builders (the same signature propagation applied to `run_transforms`); no production behavior changed as a result.

Acceptance criteria AC1–AC9 are all satisfied.
