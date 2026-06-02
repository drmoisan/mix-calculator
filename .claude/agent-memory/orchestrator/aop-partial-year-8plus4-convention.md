---
name: aop-partial-year-8plus4-convention
description: AOP/LE workbooks use a partial-year "8+4" convention; YTD is actuals-through-cutoff (not full year), YTG is the remaining months
metadata:
  type: project
---

AOP (and LE) source workbooks in this project follow a partial-year "8+4"
planning convention: a column named `YTD` holds year-to-date **actuals through a
cutoff month** (e.g. the "GS YTD April + YTG 5.8" sheet has YTD = sum(Jan..Apr)),
and `YTG` holds year-to-go for the remaining months (May..Dec). The full year is
`YTD + YTG == sum(Jan..Dec)`, not `YTD == sum(Jan..Dec)`.

**Why:** Issue #48 — a real workbook (`AOP1` sheet, 1522 rows) was rejected
because `validate_aop` asserted `YTD == sum(all 12 months)`, which only holds for
rows where YTG is zero. The module already defined `YTG_MONTHS = MONTHS[4:]`, so
the YTD check was internally inconsistent with the YTG split. Confirmed via
openpyxl: `YTD == sum(Jan..Apr)`, `YTG == sum(May..Dec)`, and
`YTD + YTG == sum(Jan..Dec)` each held for 1522/1522 rows.

**How to apply:** Treat YTD as a partial-year measure whose cutoff advances
through the year (the split is data-driven by `YTG_MONTHS`). When touching AOP
validation or any total/identity check, keep the YTD/YTG split consistent: when a
`YTG` column is present, `YTD == sum(months not in YTG_MONTHS)` and
`YTG == sum(YTG_MONTHS)`; when absent, `YTD == sum(all months)` (a full-year
sheet). Do not reintroduce the full-year YTD assumption. See
[[real-pipeline-workbook-location]] for end-to-end verification.
