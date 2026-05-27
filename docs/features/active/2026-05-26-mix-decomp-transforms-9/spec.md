# mix-decomp-transforms — Spec

- **Issue:** #9
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-26T19-36
- **Status:** Draft
- **Version:** 0.1

## Overview

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


## Behavior

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


## Inputs / Outputs

Inputs:

- `--input <workbook.xlsx>` (required): an `.xlsx` workbook that supplies the
  `AOP1` and `LE-8 + 4` sheets. The decomp workbook
  (`LE v AOP Gross to Net Decomp.xlsx`) contains `AOP1`, `LE-8 + 4`, and
  `SKU_LU`, so a single `--input` pointed at it can run the whole pipeline
  end-to-end. `Input Files.xlsx` contains only `AOP1` and `LE-8 + 4` (no SkuLu
  sheet).
- `--output <database.db>` (required): the single SQLite database that receives
  the `aop` and `LE` import tables and all derived tables.
- The `SKU_LU` sheet (default sourced from `--input`) supplies the SKU lookup:
  header on row 1; columns `SKU`, `SKU Description`, `Category`, `International`
  (~106 data rows). `International` is renamed to `Country` and its `0`/`1`
  codes are mapped to `US`/`Canada`.

Outputs:

- The SQLite database at `--output`, populated with the two import tables
  (`aop`, `LE`) and the nineteen derived tables listed under Data & State.
- WARNING-level log messages to stderr (extra source columns, KEY resolution,
  duplicate KEYs), reusing the existing loader logging behavior.
- A stdout summary describing the tables written and row counts (CLI tool
  output, not library logging).

Config keys and defaults:

- `--le-sheet` (default `"LE-8 + 4"`).
- `--aop-sheet` (default `"AOP1"`).
- `--skulu-input` (default = value of `--input`).
- `--skulu-sheet` (default `"SKU_LU"`).

Versioning or backward-compatibility constraints:

- `normalize_le` and `load_aop` logic is reused, not duplicated; their existing
  CLI entry points and SQLite table names (`LE`, `aop`) are unchanged.
- The `aop` loader marks `YTG` as optional. When the source AOP sheet predates
  `YTG`, `pivot_aop` derives the year-to-go measure by summing `May..Dec` (the
  same `YTG_MONTHS` derivation the LE loader applies) so the pipeline remains
  compatible with older AOP sheets.

## API / CLI Surface

New CLI entry point `src/mix_pipeline.py` (module name `mix-pipeline`):

```
mix-pipeline --input <workbook.xlsx> --output <database.db>
             [--le-sheet "LE-8 + 4"]
             [--aop-sheet "AOP1"]
             [--skulu-input <workbook.xlsx>]
             [--skulu-sheet "SKU_LU"]
```

Example invocation (single-workbook end-to-end run against the decomp
workbook):

```
mix-pipeline --input "LE v AOP Gross to Net Decomp.xlsx" --output decomp.db
```

Expected effect: the `aop` and `LE` import tables plus all nineteen derived
tables are written into `decomp.db`; a summary of the tables and row counts is
printed to stdout; exit code `0` on success.

Contracts and validation rules:

- `main()` returns `0` on success and `1` when a column-resolution,
  KEY-resolution, or validation `ValueError` is raised by a reused loader. A
  missing required `--input` or `--output` causes `argparse` to exit non-zero.
- `main()` orchestrates only; it contains no transform logic. The orchestration
  order is: `normalize_le` import -> `load_aop` import -> `load_skulu` import ->
  the transform pipeline in topological order -> persist each derived table.
- Pure transforms accept and return `pandas.DataFrame` (or a `float` for the
  `mix_rollup_4` scalar); they perform no I/O. All reads and writes route
  through `src.pandas_io.read_table` and `src.pandas_io.write_table`.
- Ratio guards return `0` when the denominator is `<= 0` (strict `> 0` test),
  matching the Power Query `CalcRatios` semantics.

## Data & State

Data flow: the two import tables are loaded into SQLite (reusing the existing
loaders), then the transform pipeline reads them back through `pandas_io`,
computes the derived tables in topological order, and persists each derived
table into the same database. `mix_pipeline.main` performs all I/O; the
transform modules are pure.

Evaluation order (topological; steps 1-4 are independent and may run in any
order):

```
 1  pivot_le              LE (SQLite)                     -> le_wide
 2  pivot_aop             aop (SQLite)                    -> aop_wide
 3  build_customer_lu     aop_wide                        -> customer_lu
 4  load_skulu            SKU_LU sheet                    -> sku_lu
 5  build_aop_norm        aop_wide                        -> aop_norm
 6  build_le_norm         le_wide                         -> le_norm
 7  build_aop_vs_le       aop_norm, le_norm               -> aop_vs_le
 8  build_mix_base        aop_vs_le, sku_lu               -> mix_base
 9  build_rate_impacts    aop_vs_le (buffer), sku_lu      -> rate_impacts
10  build_mix_rollup_1    rate_impacts                    -> mix_rollup_1
11  build_mix_1_sku       mix_base (buffer), mix_rollup_1 -> mix_1_sku
12  build_mix_rollup_2    mix_1_sku                       -> mix_rollup_2
13  build_mix_2_category  mix_1_sku, mix_rollup_2         -> mix_2_category
14  build_mix_rollup_3    mix_2_category                  -> mix_rollup_3
15  build_mix_3_customer  mix_2_category, mix_rollup_3    -> mix_3_customer
16  build_mix_rollup_4    mix_3_customer                  -> mix_rollup_4 (scalar)
17  build_mix_4_country   mix_3_customer, mix_rollup_4    -> mix_4_country
18  build_mix_0_detail    mix_base                        -> mix_0_detail
19  build_q1_results_by_sku  LE (SQLite, raw)             -> q1_results_by_sku
```

Derived SQLite table names (snake_case): `le_wide`, `aop_wide`, `customer_lu`,
`sku_lu`, `aop_norm`, `le_norm`, `aop_vs_le`, `mix_base`, `rate_impacts`,
`mix_rollup_1`, `mix_1_sku`, `mix_rollup_2`, `mix_2_category`, `mix_rollup_3`,
`mix_3_customer`, `mix_rollup_4` (single-row scalar table), `mix_4_country`,
`mix_0_detail`, `q1_results_by_sku`.

Data transformations and invariants:

- Both `LE` and `aop` are stored long (one row per `(..., label, measure)`
  pair) and must be pivoted wide before use. `pivot_le` pivots `GtN Mapping` on
  `YTG`; `pivot_aop` pivots `Type` on `YTG`. Each pivot then negates
  `Off Invoice $`, `Trade Spend $`, and `Non-Trade $`, adds
  `Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $`,
  applies `CalcRatios`, and melts back to long Attribute/Value form.
- `CalcRatios` appends eight ratio columns (`Gross Sales Per Lb`, `OI Per Lb`,
  `Trade Per Lb`, `Non-Trade Per Lb`, `Net Rev Per Lb`, `OI %GS`, `Trade %GS`,
  `Non-Trade %GS`), each guarded to return `0` when its denominator is `<= 0`.
- `ClassifyTable` applies two-level classification on the `Lbs` rows: SKU-level
  (`inactive`/`eliminated`/`new`/`exists`) using zero/non-zero AOP and LE Lbs
  totals, then customer-SKU-level (`inactive`/`normal`/`lost distribution`/
  `new distribution`) for `exists` SKUs. Zero tests use exact equality to match
  the M source (no float tolerance).
- `AopVsLe` filters out `Attribute == "Cases"` (LE has no `Cases` row, so it
  fills `0`) and adds `Diff = LE - AOP` before classification.
- `Mix_Base` casts `SKU #` to `str` before the left-join to `sku_lu` on
  `SKU # == SKU`, then filters to the six measure attributes and excludes
  `Classification == "inactive"`.
- `FillZeroWithAvg` replaces zero `Net Rev Per Lb` values with the cross-row
  average rate in `Mix-3-Customer` and `Mix-4-Country`.
- `mix_rollup_4` is a scalar (`float`) computed as
  `mix_3_customer["Calc Net Price Impact"].sum()`; `Mix-4-Country` subtracts it
  as a broadcast scalar.
- Regression tie-out tolerance: `1e-9` for ratio columns; exact equality for
  integer-valued measure columns (`Lbs`, `Cases`).

M-source deviations to document in code:

- `Mix-3-Customer` uses the column label "Category Mix" in the M source; the
  Python implementation uses `Customer Mix` for clarity and reserves
  `Category Mix` for `Mix-2-Category`.
- `Mix-4-Country` subtracts the scalar `Mix-Rollup-4` to produce its mix column.

Caching or persistence details:

- All derived tables are persisted with `if_exists="replace"` semantics through
  `pandas_io.write_table`. Intermediate tables (`le_wide`, `aop_wide`,
  `aop_norm`, `le_norm`) are persisted to support incremental re-runs and
  tie-out debugging.

Migration or backfill requirements (if any):

- None. The pipeline rebuilds all derived tables from the import tables on each
  run; there is no schema migration or historical backfill.

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


## Implementation Strategy

Implementation scope (what changes, not sequencing):

- Add the transform pipeline as new `src/` modules; do not modify the existing
  `normalize_le`, `load_aop`, or ETL leaf modules beyond importing them. Reuse
  the `pandas_io`, `etl_columns`, `etl_key`, and `etl_totals` seams.
- Keep pure transform logic separate from I/O: transforms read no SQLite and
  write no SQLite; only `mix_pipeline.main` performs reads and writes through
  `pandas_io`.
- Decompose across modules so no production or test file exceeds 500 lines (per
  the research module list):
  - `src/load_skulu.py` (~200 lines): load and clean the `SKU_LU` sheet into the
    `sku_lu` table, mirroring `load_aop.py` (Excel read via
    `pandas_io.read_excel_sheet`, SQLite write via `pandas_io.write_table`).
  - `src/mix_transforms.py` (~350 lines): pure primitives `pivot_le`,
    `pivot_aop`, `negate_column`, `calc_ratios`, `classify_table`,
    `stack_pivot`, `add_ratios`, `fill_zero_with_avg`.
  - `src/mix_lookups.py` (~250 lines): `build_customer_lu`, `build_aop_norm`,
    `build_le_norm`, `build_aop_vs_le`, `build_mix_base`.
  - `src/mix_rate_impacts.py` (~200 lines): `build_rate_impacts` and its six
    derived-impact columns (separated as the most complex single step).
  - `src/mix_rollups.py` (~400 lines): `build_mix_rollup_1..4`,
    `build_mix_1_sku`, `build_mix_2_category`, `build_mix_3_customer`,
    `build_mix_4_country`, `build_mix_0_detail`.
  - `src/mix_q1.py` (~100 lines): `build_q1_results_by_sku`, which reads the
    monthly `Jan`/`Feb`/`Mar` columns the main `LE` pivot discards.
  - `src/mix_pipeline.py` (~300 lines): orchestration and the `mix-pipeline` CLI
    entry point; no transform logic.

New classes/functions/commands to add or update:

- New CLI command `mix-pipeline` exposed by `src/mix_pipeline.py:main`,
  following the `argparse` pattern of `normalize_le.main` and `load_aop.main`.
- New pure functions enumerated above; `main()` calls the reused loader entry
  points (`normalize_le` import, `load_aop` import) plus `load_skulu`, then runs
  the transforms in topological order and persists each derived table.
- Add seven new `T2` entries to `quality-tiers.yml` for the new modules, with
  the same rationale as the existing ETL modules (bugs cause feature
  regressions, not data loss; per-row and cross-table tie-outs are the
  correctness gate).

Dependency changes (new/removed packages) and rationale:

- None. The implementation uses the already-approved `pandas`/`numpy`/`openpyxl`
  stack. `numpy.where` is used for vectorized divide-by-zero guards in
  `calc_ratios`.

Logging/telemetry additions and locations:

- Reuse the existing WARNING-level logging from the loaders (extra columns, KEY
  resolution, duplicate KEYs). `mix_pipeline.main` configures `logging` once at
  the entry point and prints a stdout summary of persisted tables and row
  counts. No new telemetry sink is introduced.

Rollout plan (feature flags, staged deploys, fallback path):

- No feature flag or staged deploy. The new CLI is additive and does not change
  the behavior of the existing loaders. The fallback path is to run the existing
  `normalize-le` and `load-aop` CLIs independently, which remain unchanged.

## Definition of Done

- [x] Acceptance criteria documented and mapped to tests or demos
- [x] Behavior matches acceptance criteria in all documented environments
- [x] Tests updated/added (unit/integration as applicable)
- [x] Edge cases and error handling covered by tests
- [x] Docs updated (README, docs/features/active/... links)
- [x] Telemetry/logging added or updated (if applicable)
- [x] Toolchain pass completed (format -> lint -> type-check -> test)
- [x] `mix-pipeline` CLI runs end-to-end from one `--input` workbook to one
      `--output` database and persists all nineteen derived tables
- [x] All six helper transforms implemented as pure, independently tested
      functions; classification matches the two-level Power Query logic
- [x] Mix rollups tie out (sum of detail equals the corresponding rollup) within
      `1e-9` for ratio columns and exactly for integer measures
- [x] No production, test, or reusable script file exceeds 500 lines
- [x] Pytest coverage >= 85% line and >= 75% branch in a single clean run
- [x] No real customer/SKU/category/price values appear in tests, fixtures, or
      docs (including `SKU Description` and `Category` from SkuLu)
- [x] Seven new `T2` module entries added to `quality-tiers.yml`

## Seeded Test Conditions (from potential)
- [x] Unit coverage for each helper transform (positive, negative, edge:
- [x] zero Lbs, zero Gross Sales, null fill, negation).
- [x] Classification matrix: every SKU-level and customer-SKU-level branch.
- [x] Mix decomposition rollups tie out (sum of detail equals rollup).
- [x] End-to-end CLI run against an in-memory/fabricated fixture produces all
- [x] derived tables in SQLite.
- [x] Confidentiality: no real customer/SKU/category/price values anywhere in
- [x] tests or fixtures.
