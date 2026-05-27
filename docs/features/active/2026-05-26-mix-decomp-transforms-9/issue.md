# mix-decomp-transforms (Issue #9)

- Date captured: 2026-05-26
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/mix-decomp-transforms/ (Issue #9)

- Issue: #9
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/9
- Last Updated: 2026-05-26
- Work Mode: full-feature

## Problem / Why

The repository already ingests two source planning tables into SQLite: the LE
(Latest Estimate) topline via `src/normalize_le.py` (table `LE`) and the AOP
(Annual Operating Plan) sheet via `src/load_aop.py` (table `aop`). A separate
Power Query model in `artifacts/LE v AOP Gross to Net Decomp.xlsx` consumes
those two tables and produces a gross-to-net mix/rate decomposition: it builds
customer and SKU lookups, normalizes both scenarios to a long (Attribute/Value)
shape, classifies each SKU and customer-SKU combination (inactive, eliminated,
new, normal, lost distribution, new distribution), computes per-Lb and %GS
ratios, then derives rate impacts and a multi-level price/mix decomposition
(SKU mix, category mix, customer mix, country mix) with rollups at each level.

This logic currently lives only as Power Query and cannot be run from the
Python pipeline. The need is an equivalent, tested Python implementation that
runs end-to-end from the same SQLite database the two loaders write to.

## Proposed Behavior

Add a transformation pipeline in Python that reproduces the Power Query queries
against the already-loaded `aop` and `LE` SQLite tables and persists the derived
tables into the same SQLite database. Provide a single CLI entry point that runs
both import pipelines (load_aop + normalize_le) and then the transformation
pipeline end-to-end.

Power Query queries to reproduce (semantics, not the secret data):

- Helper transforms: `NegateColumn`, `CalcRatios`, `ClassifyTable`,
  `StackPivot`, `AddRatios`, `FillZeroWithAvg`, `GroupAndLookUp`.
- Source-shaping: `LE` and `AOP` reshaped to long Attribute/Value form;
  `CustomerLU` (Customer -> Customer Master); `SkuLu` (SKU lookup with
  International -> Country, 0 -> US, 1 -> Canada).
- Comparison: `AOP_NORM`, `LE_NORM`, `AopVsLe` (combine, pivot scenario,
  diff, classify), `Mix_Base`.
- Rate impacts: `Rate_Impacts` and rollups `Mix-Rollup-1..4`.
- Mix decomposition: `Mix-1-SKu`, `Mix-2-Category`, `Mix-3-Customer`,
  `Mix-4-Country`, `Mix-0-Detail`.
- Supplemental: `Q1 Results By Sku`.

## Acceptance Criteria (early draft)

- [ ] A Python transformation pipeline reproduces the Power Query queries listed
      above against the `aop` and `LE` SQLite tables and persists each derived
      table to the same SQLite database.
- [ ] A single CLI entry point runs both ETL import pipelines (load_aop and
      normalize_le) and the transformation pipeline end-to-end against one
      workbook input and one SQLite output.
- [ ] Helper transforms (`CalcRatios`, `ClassifyTable`, `StackPivot`,
      `AddRatios`, `FillZeroWithAvg`, `NegateColumn`) are implemented as pure,
      independently tested functions.
- [ ] The classification logic matches Power Query: SKU-level
      (inactive/eliminated/new/exists) then customer-SKU level
      (inactive/normal/lost distribution/new distribution).
- [ ] No production file, test file, or reusable script exceeds 500 lines.
- [ ] Toolchain passes in a single clean run: Black, Ruff, Pyright (strict),
      Pytest with >= 85% line and >= 75% branch coverage.

## Constraints & Risks

- CONFIDENTIALITY (hard constraint): the source workbook contains confidential
  data. Customer names, product/SKU descriptions, category names, product
  numbers (SKU #), sales prices, and any discounts MUST be treated as secrets.
  None of these real values may be persisted in fixtures, Markdown files, tests,
  or source code. Column/attribute names and classification labels are schema,
  not secret; only the real data values are secret. Tests must use fabricated
  data only (the existing suite uses Acme Foods, Globex Market, Initech Grocers).
- The real workbook (`artifacts/LE v AOP Gross to Net Decomp.xlsx`,
  `artifacts/Input Files.xlsx`) and the output `.db` are gitignored and must
  remain untracked.
- Power Query `List.Sum`/pivot/`Table.Buffer` semantics must be reproduced
  faithfully in pandas, including null-to-0 replacement and divide-by-zero
  guards (ratios return 0 when the denominator is 0).
- The Power Query negates Off Invoice / Trade / Non-Trade before summing into
  Net Revenue; AOP also drops the percent columns and renames LBs -> Lbs.
- 500-line file limit forces decomposition across multiple modules; reuse the
  existing `pandas_io`, `etl_columns`, `etl_key`, `etl_totals` seams.

## Test Conditions to Consider

- [ ] Unit coverage for each helper transform (positive, negative, edge:
      zero Lbs, zero Gross Sales, null fill, negation).
- [ ] Classification matrix: every SKU-level and customer-SKU-level branch.
- [ ] Mix decomposition rollups tie out (sum of detail equals rollup).
- [ ] End-to-end CLI run against an in-memory/fabricated fixture produces all
      derived tables in SQLite.
- [ ] Confidentiality: no real customer/SKU/category/price values anywhere in
      tests or fixtures.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/mix-decomp-transforms/` folder from the template