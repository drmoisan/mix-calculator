---
name: aop-ytd-convention-varies-by-workbook
description: AOP1 YTD convention differs across real workbooks — v3 uses full-year YTD with YTG present; LE_NEW uses partial Jan..Apr YTD; YTG presence does not determine the YTD month set
metadata:
  type: project
---

The AOP1 YTD convention is NOT uniform across the user's real workbooks, and the
presence of a `YTG` column does not determine it. Verified via the loader's own
read/coerce path (1e-6 tol):

- `artifacts/LE_NEW v LE_ORIG Gross to Net Decomp.xlsx` AOP1 (1522 rows):
  `YTD == sum(Jan..Apr)` for all rows; `YTG == sum(May..Dec)` for all rows.
- `artifacts/LE v AOP Gross to Net Decomp v3.xlsx` AOP1 (1953 rows):
  `YTD == sum(Jan..Dec)` (full year) for all rows; `YTG == sum(May..Dec)` for all
  rows.

Both sheets carry `YTG`. `YTG == sum(May..Dec)` holds in both; only the YTD month
set differs (partial vs full year).

**Why:** The GUI failed importing the v3 workbook with
`AOP validation failed: YTD != sum(months)`. `build_per_row_checks` in
`src/_load_aop_helpers.py` chooses the YTD month set solely on whether `YTG` is
present (issue #48 fix: YTG present ⇒ YTD == sum(Jan..Apr)). That is correct for
LE_NEW but rejects v3, where YTD is the full year despite YTG being present. The
#48 fix swapped one hardcoded assumption (full-year) for another
(partial-when-YTG); neither single rule covers both real workbooks.

**How to apply:** When touching AOP YTD/YTG validation, do not key the YTD month
set off YTG presence alone. Either accept YTD that matches EITHER sum(Jan..Apr)
OR sum(Jan..Dec) per row (keeping YTG==sum(May..Dec) and quarter identities
strict), or detect the convention per sheet. Keep the blank-total fill in
`load_aop.py` consistent with whatever validation accepts. Supersedes the strict
reading in [[aop-partial-year-8plus4-convention]]. See
[[real-pipeline-workbook-location]].
