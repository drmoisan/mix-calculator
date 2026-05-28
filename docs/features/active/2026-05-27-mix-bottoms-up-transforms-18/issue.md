# mix-bottoms-up-transforms (Issue #18)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/ (Issue #18)

- Issue: #18
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/18
- Last Updated: 2026-05-27
- Work Mode: full-feature

## Problem / Why

The end-to-end mix-decomposition pipeline (issue #9) replicates the TopDown mix
tables (`mix_1_sku`, `mix_2_category`, `mix_3_customer`) from the source workbook.
The same workbook also contains three "BottomsUp" tabs — `2-SKU-Mix-BottomsUp`,
`3-Category-Mix-BottomsUp`, and `4-Customer-Mix-BottomsUp` — that are not yet
reproduced by the pipeline. These BottomsUp tables decompose the gross-to-net mix
shift from the row/group level upward, and are derived entirely from tables the
pipeline already produces. They should be replicated as an additional transform
stage and persisted to the same SQLite database as the rest of the pipeline.

## Proposed Behavior

Add a new pure-transform stage to the mix pipeline that builds three derived
tables from existing pipeline outputs, and persist them into the same `.db`:

- **`mix_2_sku_bottomsup`** (from `2-SKU-Mix-BottomsUp`, one row per `mix_0_detail`
  row). Columns: pass-through identity/measure columns from `mix_0_detail`
  (Customer, SKU #, SKU Description, Category, Country, Classification, Lbs - AOP,
  Lbs - LE, Net Rev Per Lb - AOP, Net Rev Per Lb - LE); then a Blended Rate and
  Lbs Subtotal pair (AOP/LE) computed by summing `mix_1_sku` over the
  Customer+Category group; Share - AOP/LE (`Lbs / Lbs Subtotal`, guarded against
  divide-by-zero → 0); Share Shift (`Share-LE − Share-AOP`); Mix Rate
  (`NetRevPerLb-AOP − Blended Rate-AOP`); New / Disco / Normal Contribution
  (classification-conditional formulas); and SKU Mix (`Normal + Disco + New`).

- **`mix_3_category_bottomsup`** (from `3-Category-Mix-BottomsUp`, one row per
  distinct `Customer|Category|Country` group present in `mix_0_detail`). Group
  identity resolved from the distinct composite key; Lbs and Net-Revenue $ summed
  from `mix_0_detail` over that key; Net Rev Per Lb = NetRev$ / Lbs; Classification
  derived from AOP/LE zero tests; Blended Rate and Lbs Subtotal summed from
  `mix_2_category` over the Customer+Country group; then the same Share / Share
  Shift / Mix Rate / Contribution / SKU Mix arithmetic as the SKU table.

- **`mix_4_customer_bottomsup`** (from `4-Customer-Mix-BottomsUp`, one row per
  distinct `Customer|Country` group present in `mix_0_detail`). Same structure as
  the category table, but grouped at `Customer|Country`, summing `mix_0_detail`
  over that key, with Blended Rate / Lbs Subtotal summed from `mix_3_customer`
  over the Country group.

Wire the new stage into the pipeline orchestration so the three tables are written
on the same connection as the existing derived tables, and reported in the
stdout summary.

## Acceptance Criteria

- [ ] Three new derived tables (`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`,
      `mix_4_customer_bottomsup`) are produced by pure transforms with the exact
      columns and grains in `spec.md`, and persisted to the same SQLite database as
      the existing mix tables.
- [ ] The transform logic reproduces the Excel BottomsUp column formulas (pass-
      through, group aggregation over the SUMIFS criteria columns, share, share-shift,
      mix-rate, the three classification-conditional contributions, and the SKU Mix
      total) with all divisions guarded to `0.0` and `fillna(0)` applied after the
      rollup merges.
- [ ] Classification is joined from `mix_base` on `(Customer, SKU #)` for the SKU
      table and re-derived from aggregated Lbs for the category and customer tables,
      with case-sensitive matching against the lowercase tokens.
- [ ] The new stage is wired into `run_transforms` in `src/mix_pipeline_run.py` and
      reported in the run summary, using the established pure-transform + `pandas_io`
      I/O boundary with no change to `src/mix_pipeline.py`.
- [ ] No confidential source data is persisted in any file, test, or fixture;
      tests use fabricated example data only.
- [ ] Full toolchain (Black, Ruff, Pyright, Pytest) passes with coverage thresholds
      (≥85% line / ≥75% branch) met; no production file exceeds 500 lines.

## Constraints & Risks

- **Confidentiality (hard constraint):** the source workbook
  `artifacts/LE v AOP Gross to Net Decomp.xlsx` is confidential. No form of its
  data may be persisted in any file, test, or fixture. Reuse the established
  precedent (fabricated `SKU-001` / `Widget A` / `Category X` examples; `US`/
  `Canada` are not secret).
- The BottomsUp formulas depend on `mix_0_detail`, `mix_1_sku`, `mix_2_category`,
  and `mix_3_customer`. Risk: required columns (for example `mix_0_detail` composite
  keys `Customer|Category|Country` and `Customer|Country`, and `Net-Revenue $`
  measures) may not yet exist on those tables and may need to be derived inside the
  new transform. Research must reconcile required inputs against the current schema.
- Excel divide-by-zero guards and classification string matching
  ("normal" / "new distribution" / "new" / "lost distribution" / "eliminated")
  must be reproduced exactly to tie out.
- File-size limit (500 lines) may require a `_helpers` split, consistent with the
  existing mix modules.

## Test Conditions to Consider

- [ ] Unit coverage for each derived column family: pull-through, group aggregation,
      share, share-shift, mix-rate, each classification branch (normal / new / new
      distribution / lost distribution / eliminated), and the SKU Mix total.
- [ ] Divide-by-zero guards (zero Lbs Subtotal → share 0; zero AOP lbs handling in
      Disco contribution).
- [ ] Distinct-key grouping for the category and customer tables (one row per
      group).
- [ ] Pipeline integration: the three tables are written to the database alongside
      the existing tables on a single connection.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/mix-bottoms-up-transforms/` folder from the template