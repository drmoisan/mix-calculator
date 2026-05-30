# rate-impacts-summed-ratio (Issue #37)

- Date captured: 2026-05-29
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/rate-impacts-summed-ratio/ (Issue #37)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #37
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/37
- Last Updated: 2026-05-30
- Work Mode: minor-audit

## Summary

`build_rate_impacts` (the SKU-level rate calc) trusts pre-computed per-unit and %GS ratio columns that have been combined with `aggfunc="sum"` while the mix side recomputes those ratios from summed dollars and volumes. Summing a ratio across split sub-rows is mathematically invalid, so when a single SKU's gross-to-net line items are split across more than one fine-grain group the rate side and mix side disagree and the SKU Mix residual silently absorbs the discrepancy. This is the Python equivalent of a defect found and fixed in the upstream Excel Power Query (M) model.

## Environment

- OS/version: Windows (repository default)
- Python version: project Poetry environment
- Command/flags used: pipeline transform path through `src/mix_rate_impacts.py`
- Data source or fixture: gross-to-net AOP-vs-LE comparison frame; trigger is a SKU whose deduction (off-invoice) line carries dollars but zero volume on a different fine-grain group than the SKU's volume line

## Steps to Reproduce

1. Construct an AOP-vs-LE comparison in which one SKU has its dollar/volume measures correct at the `{Customer, SKU #}` grain but its carried `Net Rev Per Lb` / `%GS` ratio rows reflect an additive combination across two fine-grain sub-groups (one sub-group carrying deduction dollars with zero volume).
2. Run `build_rate_impacts` over that comparison.
3. Observe that `Net Rev Per Lb - Diff` (and the other carried ratio diffs) is the summed ratio (which can be zero) rather than the value implied by the summed dollars and volumes.
4. Roll the SKU-level `Calc Net Price Impact` up to the Customer x Category grain and compare against the category-level net-price impact; for a single-SKU group they should net to a SKU Mix of zero but do not.

## Expected Behavior

The SKU-level rate impact, summed to the Customer x Category grain, equals the category-level net-price impact for single-SKU groups (SKU Mix = 0). For a SKU whose net-revenue change originates from a zero-volume deduction sub-row, `net_rev_per_lb_diff` is the dollar-derived value, not zero. The top-down SKU Mix total equals the bottoms-up SKU Mix total.

## Actual Behavior

For a split SKU the carried summed ratio differs from the dollar-derived ratio (it can collapse to zero when a deduction sub-row carries dollars but zero volume). The SKU-level rate impact is then understated, and the SKU Mix residual absorbs the entire price move as "mix," overstating SKU Mix.

## Logs / Screenshots

- [ ] Attached minimal logs or screenshot
- Snippet: not applicable (logic defect; no error text)

## Impact / Severity

- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

Misclassifies net-price (rate) movement as mix for any SKU split across fine-grain groups. Currently masked on the LE path because `normalize_le` collapses `Super Category := PPG` per `(Customer, SKU #)`, but the AOP path has no equivalent guard, so AOP source data carrying a SKU under multiple `(Super Category, PPG)` groups would surface the defect.

## Suspected Cause / Notes

- Condition (a): ratios computed at the fine `{Customer, Super Category, PPG, SKU Descripiton, SKU #}` grain in `pivot_le`/`pivot_aop` via `calc_ratios` (`src/_mix_transforms_helpers.py`).
- Condition (b): `build_aop_vs_le` pivots with `aggfunc="sum"` over `{Customer, SKU #, Attribute}` (`src/mix_lookups.py:183-188`), summing ratio-attribute rows; `stack_pivot` sums again.
- Condition (d): `build_rate_impacts` reads the summed `Net Rev Per Lb - Diff` / `%GS` columns directly (`src/mix_rate_impacts.py:95-112`); the mix side `build_mix_stage` recomputes from summed dollars/volumes.
- Condition (c): masked on LE by `src/normalize_le.py:286-287`; unguarded on AOP.
- Read-only audit detail in `artifacts/research/20260529-rate-mix-summed-ratio-audit.md`.

## Proposed Fix / Validation Ideas

- [x] In `build_rate_impacts`, recompute the per-unit (`Net Rev Per Lb`, `Gross Sales Per Lb`) and %GS (`OI %GS`, `Trade %GS`, `Non-Trade %GS`) metrics from the additive dollar/volume wide columns (`Net-Revenue $ - AOP/LE`, `Lbs - AOP/LE`, `Gross Sales - AOP/LE`, `Off Invoice $ - AOP/LE`, `Trade Spend $ - AOP/LE`, `Non-Trade $ - AOP/LE`) at the SKU grain, using a zero-denominator guard consistent with `calc_ratios`. Keep the six impact formulas unchanged.
- [x] Unit coverage: a regression test using synthetic proportional values (NOT the confidential workbook figures) for a SKU with a zero-volume deduction sub-row, asserting `net_rev_per_lb_diff` is dollar-derived (non-zero) and the SKU-level rate rolls up to the category net-price impact (SKU Mix = 0) for a single-SKU group.
- [ ] Integration scenario to retest: end-to-end rate-vs-mix reconciliation (top-down equals bottoms-up).
- [ ] Manual verification notes: confirm single-fine-grain-row SKUs are unchanged (recomputed ratio equals carried ratio).

## Acceptance Criteria

- [x] AC1 — `build_rate_impacts` computes `net_rev_per_lb` (AOP and LE), `gross_sales_per_lb`, `OI %GS`, `Trade %GS`, and `Non-Trade %GS` from the additive dollar/volume wide columns at the `{Customer, SKU #}` grain rather than reading the carried/summed ratio columns. The six impact formulas (`RATE_IMPACT_COLUMNS`) are unchanged.
- [x] AC2 — A zero-denominator guard consistent with `calc_ratios` is applied so a zero (or non-positive) denominator yields 0 rather than `inf`/`NaN`.
- [x] AC3 — Regression test (synthetic proportional values only; no confidential workbook figures): for a SKU whose net-revenue change originates from a zero-volume deduction sub-row, `Net Rev Per Lb - Diff`/`Calc Net Price Impact` is the dollar-derived value (non-zero), not zero.
- [x] AC4 — Reconciliation test: the SKU-level `Calc Net Price Impact` summed to the Customer x Category grain equals the category-level net-price impact for a single-SKU group (SKU Mix nets to 0).
- [x] AC5 — Behavior is unchanged for SKUs with a single fine-grain row (recomputed ratio equals the previously carried ratio); existing `build_rate_impacts` tests continue to pass.
- [x] AC6 — Python toolchain passes (Black, Ruff, Pyright, Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Next Step

- [x] Promote to GitHub issue (bug-report template)
- [x] Move to active fix folder / branch