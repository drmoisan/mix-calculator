# End-to-End Pipeline Run (Issue #15)

Timestamp: 2026-05-27T21-08
Command: poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db
EXIT_CODE: 0

## Output Summary

- The pipeline completed with exit code 0.
- The stdout summary listed `nrr_summary` as the final derived table written:
  `nrr_summary: 20 rows`.
- The `nrr_summary` table is present in the output database with 20 rows.
- The five expected sections are present: `attribute_summary`,
  `net_revenue_realization`, `net_pricing_breakdown`, `mix_breakdown`,
  `reconciliation`.
- The 20 metric rows are emitted in the expected source order, ending with the
  `Check` row.
- A pre-existing, non-failure loader WARNING about duplicate KEY values was
  emitted (unrelated to this change; present before issue #15).

## Reconciliation Check Result

- `Check` cell result: `"ERROR"` (NOT the AC10-required `"CHECK"`).

No confidential source numerics, SKU descriptions, or category names are
disclosed in this artifact.

## AC10 Status: NOT SATISFIED — Reconciliation does not pass on real data

The internal `Check` reconciles to `"ERROR"`, not `"CHECK"`, on the real
workbook. Diagnosis (performed internally; raw confidential magnitudes not
reproduced here) established the following, in non-confidential terms:

- The realization-derived Price/Mix and the workbook's own NRR_Summary tab
  Price/Mix build-up agree (both the pipeline's realization Price/Mix and the
  workbook's printed Price/Mix build-up are the same figure). The reconciliation
  target is therefore well defined.
- The pipeline's `Total Net Pricing` (sum of the four `rate_impacts` columns)
  matches the workbook NRR_Summary tab's `Total Net Pricing` exactly. The
  pricing block is correct.
- The pipeline's `SKU Mix` total (`mix_1_sku["SKU Mix"]` column sum) and
  `Country Mix` total (`mix_4_country["Country Mix"]` column sum) match the
  workbook NRR_Summary tab values exactly.
- The pipeline's `Category Mix` total (`mix_2_category["Category Mix"]` column
  sum) and `Customer Mix` total (`mix_3_customer["Customer Mix"]` column sum) do
  NOT match the workbook NRR_Summary tab values. The plain column-total of these
  two cascade-table mix columns differs from the figures the workbook tab uses
  by several orders of magnitude, so the `Total Mix` build-up does not tie out
  to the realization Price/Mix and the `Check` resolves to `"ERROR"`.

### Root cause

The issue's `## Acceptance Criteria` AC5 prescribes that `Category Mix` and
`Customer Mix` are the plain `[[#Totals]]` column sums of the pipeline's
`mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]` cascade
columns. On the real data, the pipeline's customer/country mix layers apply a
`fill_zero_with_avg` recomputation of `Calc Net Price Impact` (see
`src/mix_rollups.py::_apply_fill_zero_and_recompute`), which changes the per-row
magnitudes such that the plain column total of the renamed mix column is not the
figure the workbook NRR_Summary tab uses. The workbook derives the Category and
Customer mix figures via a different (bottoms-up worksheet) computation that the
pipeline does not currently produce as those column totals.

### Why this is reported rather than worked around

- AC5 and the plan explicitly require preserving the
  `mix_3_customer["Customer Mix"]` mapping deliberately; changing the input
  mapping to make the reconciliation pass would violate that constraint.
- Reproducing the workbook's bottoms-up Category/Customer mix derivation is a new
  derivation not present in the pipeline and outside the approved small-path
  scope.
- The execution policy prohibits weakening tests, fabricating evidence, or
  forcing the `Check` to `"CHECK"`. The honest end-to-end signal is recorded
  here as `"ERROR"`.

### Disposition

AC10 cannot be satisfied within the current plan scope without a specification
revision to AC5 (the correct definition of the `Category Mix` and `Customer Mix`
totals) or an authorized scope expansion to derive those totals from the
bottoms-up mix computation. The builder, integration, tests, classification,
docs, and full toolchain (AC1-AC9) are complete and verified; AC10 is blocked on
this specification gap.
