# `mix-decomp-transforms` — User Story

- Issue: #9
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-05-26T19-36

## Story Statement

- As a financial planning analyst, I want to run the LE-versus-AOP
  gross-to-net mix and rate decomposition from the Python pipeline against the
  SQLite database the loaders already write, so that I no longer depend on the
  Power Query workbook to produce the SKU, category, customer, and country mix
  and rate impacts.
- As a maintainer of this repository, I want the decomposition implemented as
  small, pure, independently tested transforms behind a single CLI entry point,
  so that the logic is verifiable, reproducible, and stays within the project's
  quality and confidentiality constraints.

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


## Personas & Scenarios

- Persona: Financial planning analyst
  - Who the user is: an analyst who owns the gross-to-net plan-versus-estimate
    comparison and currently maintains the calculation in a Power Query
    workbook.
  - What they care about: producing the SKU, category, customer, and country
    mix and rate impacts that tie out to the source plan and estimate.
  - Their constraints: the source data (customer names, SKU descriptions,
    category names, SKU numbers, prices, discounts) is confidential and must
    not leave the controlled workbook or appear in any tracked artifact.
  - Their goals and frustrations: the Power Query model cannot be run from the
    Python pipeline, is hard to test, and duplicates the ingestion the
    `normalize_le` and `load_aop` loaders already perform.
  - Their context and motivations: the two loaders already populate the `LE`
    and `aop` SQLite tables; the analyst wants the decomposition to run from the
    same database without re-keying or re-importing data.

- Scenario: Run the full decomposition from one workbook
  - Who is acting: the financial planning analyst.
  - What triggered the action: a refreshed LE estimate needs to be compared
    against the AOP plan to produce the mix and rate decomposition.
  - Steps they take: invoke `mix-pipeline --input "LE v AOP Gross to Net
    Decomp.xlsx" --output decomp.db`. The pipeline imports the `AOP1` and
    `LE-8 + 4` sheets, loads the `SKU_LU` sheet, then runs the transform
    pipeline in topological order, persisting each derived table.
  - Obstacles or decisions: some AOP sheets predate the `YTG` column, so the
    pivot must derive it from `May..Dec`; SKUs and customer-SKU pairs must be
    classified (inactive, eliminated, new, normal, lost distribution, new
    distribution) so eliminated and inactive lines do not distort the mix.
  - Outcome they expect: a single SQLite database containing the `aop` and `LE`
    import tables plus all nineteen derived tables, with the mix rollups tying
    out to the detail, and no confidential values written anywhere.


## Acceptance Criteria

- [x] A Python transformation pipeline reproduces the Power Query queries against the `aop` and `LE` SQLite tables and persists each derived table to the same SQLite database.
- [x] All nineteen derived tables are persisted: `le_wide`, `aop_wide`, `customer_lu`, `sku_lu`, `aop_norm`, `le_norm`, `aop_vs_le`, `mix_base`, `rate_impacts`, `mix_rollup_1`, `mix_1_sku`, `mix_rollup_2`, `mix_2_category`, `mix_rollup_3`, `mix_3_customer`, `mix_rollup_4`, `mix_4_country`, `mix_0_detail`, `q1_results_by_sku`.
- [x] A single CLI entry point (`mix-pipeline`) runs both ETL import pipelines (load_aop and normalize_le) and the transformation pipeline end-to-end against one `--input` workbook and one `--output` SQLite database, reusing the loaders rather than duplicating them.
- [x] The `SKU_LU` sheet is loaded via `--skulu-input` (default = `--input`) and `--skulu-sheet` (default `"SKU_LU"`), renaming `International` to `Country` and mapping `0` to `US` and `1` to `Canada`.
- [x] Helper transforms (`CalcRatios`, `ClassifyTable`, `StackPivot`, `AddRatios`, `FillZeroWithAvg`, `NegateColumn`) are implemented as pure, independently tested functions with no I/O.
- [x] The classification logic matches Power Query: SKU-level (inactive/eliminated/new/exists) then customer-SKU level (inactive/normal/lost distribution/new distribution), using exact zero tests.
- [x] Mix decomposition rollups tie out: the sum of detail equals the corresponding rollup, within `1e-9` for ratio columns and exactly for integer measures.
- [x] `Mix-3-Customer` uses the column name `Customer Mix` (not the M-source "Category Mix") and `Mix-4-Country` subtracts the scalar `mix_rollup_4`.
- [x] No real customer names, SKU descriptions, category names, SKU numbers, prices, or discounts appear in tests, fixtures, or docs; only fabricated values are used (the `US`/`Canada` country values are not secret).
- [x] No production file, test file, or reusable script exceeds 500 lines.
- [x] Toolchain passes in a single clean run: Black, Ruff, Pyright (strict), Pytest with >= 85% line and >= 75% branch coverage.


## Non-Goals

- Reimplementing or changing the existing `normalize_le` or `load_aop` loaders,
  their CLIs, or their SQLite table names; this feature reuses them.
- Building reporting, visualization, or drill-through UI on top of the derived
  tables; the scope ends at persisting the tables to SQLite.
- Committing or distributing the real source workbooks or output database; these
  remain gitignored and untracked.
- Schema migration or historical backfill; the pipeline rebuilds all derived
  tables from the import tables on each run.
- Performance optimization or parallel execution of the transform steps beyond
  the documented topological order.
