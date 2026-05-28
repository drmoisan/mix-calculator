---
name: nrr-summary-mix-total-spec-gap
description: Issue #15 NRR-summary surfaced an upstream mix tie-out defect (now tracked as #20); the NRR_Summary replication itself is correct
metadata:
  type: project
---

Issue #15 (`nrr-summary-mix-pipeline`) is a faithful replication of the workbook
`NRR_Summary` tab. Its internal reconciliation `Check` resolves to `"ERROR"` on
the real workbook, which correctly surfaces a PRE-EXISTING upstream defect rather
than a defect in the summary feature.

**Why:** the summary sums each mix layer's column total exactly as the workbook
tab does. `mix_1_sku["SKU Mix"]` and `mix_4_country["Country Mix"]` tie out to the
workbook; `mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]` do
not (they differ by orders of magnitude and sign). The customer/country layers
apply `fill_zero_with_avg` recomputation in
`src/mix_rollups.py::_apply_fill_zero_and_recompute`; the workbook derives the
Category/Customer mix via the bottoms-up tabs (`3-Category-Mix-BottomsUp`,
`4-Customer-Mix-BottomsUp`), which the pipeline does not replicate. Pricing block,
realization Price/Mix, SKU/Country mix, and the build-up arithmetic are correct.
(Confidential: never record the actual derived mix figures in any committed
file; describe the discrepancy qualitatively only.)

**How to apply:** Resolved 2026-05-27 by user decision "Option A" — #15 lands as a
faithful replication; AC10 was revised to verify the `Check` is reported
accurately (the `"ERROR"` is correct given upstream state). The upstream tie-out
defect is tracked separately as **issue #20** (`mix-category-customer-mix-tieout`,
full-bug). The fix belongs there, in `src/mix_rollups.py` /
`src/_mix_rollups_helpers.py`, not in `src/mix_nrr_summary.py`. Do NOT force
`Check` to `"CHECK"` or change the deliberate `mix_3_customer["Customer Mix"]`
mapping to mask the gap.
