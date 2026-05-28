# mix-category-customer-mix-tieout (Issue #20)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/mix-category-customer-mix-tieout/ (Issue #20)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #20
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/20
- Last Updated: 2026-05-28
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

The category and customer mix layers (`src/mix_rollups.py::build_mix_2_category`,
`build_mix_3_customer`) compute the mix column via a reshape +
`join_rollup_mix` cascade, and the customer/country layers additionally apply
`_apply_fill_zero_and_recompute` (`fill_zero_with_avg`). The resulting per-row
mix magnitudes do not reproduce the workbook's bottoms-up Category/Customer mix
methodology (the workbook's TopDown mix columns are hardcoded value snapshots
pasted from the BottomsUp tabs `3-Category-Mix-BottomsUp` /
`4-Customer-Mix-BottomsUp`). Files to inspect: `src/mix_rollups.py`,
`src/_mix_rollups_helpers.py`, `src/mix_transforms.py` (`fill_zero_with_avg`),
and the workbook BottomsUp tabs for the intended methodology.

## Proposed Fix / Validation Ideas

- [ ] Unit coverage areas: per-layer mix-column derivation for the category and
  customer levels with fabricated inputs that reproduce the bottoms-up method.
- [ ] Integration scenario to retest: end-to-end run where the `NRR_Summary`
  `Check` resolves to `"CHECK"` once the two layers tie out.
- [ ] Manual verification notes: compare each layer's mix-column total to the
  corresponding workbook TopDown total (SKU and Country already match).

## Next Step

- [ ] Promote to GitHub issue (bug-report template)
- [ ] Move to active fix folder / branch