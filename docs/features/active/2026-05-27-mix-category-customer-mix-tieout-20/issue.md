# mix-category-customer-mix-tieout (Issue #20)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/mix-category-customer-mix-tieout/ (Issue #20)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #20
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/20
- Last Updated: 2026-05-28
- Work Mode: full-bug

## Summary

The mix-decomposition pipeline's `mix_2_category["Category Mix"]` and
`mix_3_customer["Customer Mix"]` column totals do not tie out to the source
workbook's authoritative mix totals, whereas the `mix_1_sku["SKU Mix"]` and
`mix_4_country["Country Mix"]` totals do. This was discovered while replicating
the `NRR_Summary` tab (issue #15): the summary's internal reconciliation `Check`
resolves to `"ERROR"` solely because of these two layers.

## Environment

- OS/version: Windows, PowerShell 7+
- Python version: 3.13 (Poetry in-project `.venv`)
- Command/flags used: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db`
- Data source or fixture: confidential `LE v AOP Gross to Net Decomp.xlsx` (gitignored)

## Steps to Reproduce

1. Run the mix pipeline end-to-end against the real workbook (command above).
2. Compare the column total of `mix_2_category["Category Mix"]` and
   `mix_3_customer["Customer Mix"]` in `artifacts/mix.db` against the workbook's
   `NRR_Summary` tab `Category Mix` / `Customer Mix` figures (equivalently, the
   `3-Category-Mix-TopDown` / `4-Customer-Mix-TopDown` table totals).
3. Repeat for `mix_1_sku["SKU Mix"]` vs `2-SKU-Mix-TopDown` and
   `mix_4_country["Country Mix"]` vs `5-Country-Mix`.

## Expected Behavior

All four mix-layer column totals tie out to the workbook's authoritative TopDown
snapshot totals (as the SKU and Country layers already do), so that the
`NRR_Summary` reconciliation `Check` resolves to `"CHECK"`.

## Actual Behavior

`mix_1_sku["SKU Mix"]` and `mix_4_country["Country Mix"]` match the workbook
exactly. `mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]`
differ from the workbook figures by several orders of magnitude (including a sign
difference), so the `Total Mix` build-up does not equal the realization-derived
`Price/Mix` and the `Check` resolves to `"ERROR"`. (Exact figures omitted: they
are confidential derived aggregates.)

## Logs / Screenshots

- [x] Attached minimal logs or screenshot
- Snippet: see `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/evidence/other/e2e-run.2026-05-27T21-08.md` (qualitative, no confidential values).

## Impact / Severity

- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

Rationale: the category and customer mix decomposition figures are incorrect
relative to the source of truth, which undermines the mix-attribution output of
the pipeline. It does not block the `NRR_Summary` feature (issue #15), which
faithfully reports the discrepancy.

## Suspected Cause / Notes

CONFIRMED root cause (see `spec.md` for the full analysis). The coarser mix
layers re-aggregate the **filtered, reshaped prior layer** instead of the
unfiltered detail: `build_mix_2_category` builds its stage from
`unstack_to_long(mix_1_sku, …)`, and so on for the customer and country layers.
`build_mix_stage` drops lines failing the nonzero-Lbs filter
(`Lbs - AOP != 0 & Lbs - LE != 0`), including single-scenario lines (for example
a SKU new in LE). Re-aggregating the already-filtered prior layer therefore
understates the coarser layers' LE-side `Lbs` and `Net-Revenue $`, corrupting the
recomputed `Calc Net Price Impact` and the mix. Verified: aggregating the
unfiltered `mix_base` at the layer granularity reproduces the workbook
category-level volume/revenue and `Calc Net Price Impact` exactly, while the
filtered `mix_1_sku` aggregation understates the LE side. The SKU layer is
correct (it aggregates `mix_base` directly); the Country layer ties out (mix 0).

Fix direction: aggregate each coarser layer from `mix_base` at its own
granularity; keep the rollup-subtraction target as the sum of the prior finer
layer's `Calc Net Price Impact`. Files: `src/mix_rollups.py`,
`src/_mix_rollups_helpers.py` (`unstack_to_long` likely removable),
`src/mix_pipeline_run.py`. The full acceptance criteria are in `spec.md`.

## Proposed Fix / Validation Ideas

- [x] Unit coverage areas: single-scenario line retention in the coarser-layer
  aggregates, and the NPI-minus-rollup identity per layer, with fabricated inputs.
- [x] Integration scenario to retest: end-to-end run where the `NRR_Summary`
  `Check` resolves to `"CHECK"` once the layers tie out.
- [x] Manual verification notes: compare each layer's mix-column total to the
  corresponding workbook TopDown total (SKU and Country already match).

## Next Step

- [x] Promote to GitHub issue (bug-report template)
- [x] Move to active fix folder / branch