# Issue Update Mirror — Issue #37

Timestamp: 2026-05-29T21-59
PostedAs: unknown

POSTING NOTE: This is a local mirror of the acceptance-criteria status updated in the feature `issue.md`. No GitHub posting was performed by the executor; this artifact records the local check-off state for audit reconciliation.

## Acceptance Criteria status (all satisfied)

- [x] AC1 — `build_rate_impacts` recomputes net_rev_per_lb (AOP/LE), gross_sales_per_lb, OI %GS, Trade %GS, Non-Trade %GS from the additive dollar/volume wide columns at the {Customer, SKU #} grain; the six RATE_IMPACT_COLUMNS formulas are unchanged.
- [x] AC2 — Zero-denominator guard (`_guarded_div`, `den > 0` => quotient else 0.0) matches `calc_ratios`/`_safe_div`; `calc_ratios`/`_safe_div` behavior unchanged.
- [x] AC3 — Regression test (synthetic, proportional values) proves a zero-volume deduction sub-row yields a dollar-derived non-zero Calc Net Price Impact (fail-before captured; pass-after captured).
- [x] AC4 — Reconciliation test proves SKU-level Calc Net Price Impact rolled to {Customer, Category} equals the category net-price impact for a single-SKU group (SKU Mix residual = 0 within 1e-9).
- [x] AC5 — Single-fine-grain recompute equals the previously carried ratio; the four pre-existing tests pass unchanged (fixture extended with consistent dollar/volume columns).
- [x] AC6 — Black, Ruff, Pyright, Pytest pass; total line coverage 99% (>= 85%), total branch ~98.9% (>= 75%); src/mix_rate_impacts.py 100% line; no regression on changed lines.

## Scope

- Production changed: src/mix_rate_impacts.py (within scope lock).
- Test changed: tests/test_mix_rate_impacts.py (within scope lock).
- No files outside the 2-file scope lock were modified. `_mix_transforms_helpers.py`, `calc_ratios`, `_safe_div`, `mix_lookups.py`, and policy files are unchanged.

## Confidentiality

- No confidential workbook aggregates, reconciliation totals, or source dollar/lbs/per-lb values appear in code, tests, evidence, or this mirror. All test data is synthetic and proportional.
