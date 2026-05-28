# mix-bottoms-up-transforms — Spec

- **Issue:** #18
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T20-46
- **Status:** Draft
- **Version:** 0.2

## Overview

The end-to-end mix-decomposition pipeline (issue #9) replicates the TopDown mix
tables (`mix_1_sku`, `mix_2_category`, `mix_3_customer`) from the source workbook.
The same workbook also contains three "BottomsUp" tabs — `2-SKU-Mix-BottomsUp`,
`3-Category-Mix-BottomsUp`, and `4-Customer-Mix-BottomsUp` — that are not yet
reproduced by the pipeline. These BottomsUp tables decompose the gross-to-net mix
shift from the row/group level upward, and are derived entirely from tables the
pipeline already produces (`mix_0_detail`, `mix_1_sku`, `mix_2_category`,
`mix_3_customer`, and `mix_base`). This feature adds a pure-transform stage that
builds three derived tables and persists them to the same SQLite database as the
existing mix tables.

This feature adds no new CLI surface. The three tables are produced as part of the
existing `mix-pipeline` run and are written on the same database connection as the
existing derived tables. The transforms are pure functions; all reads and writes
remain in `src/pandas_io.py`, which is owned by the orchestrator.


## Behavior

A new transform stage builds three derived tables from existing pipeline outputs:

- **`mix_2_sku_bottomsup`** — one row per `mix_0_detail` row. Pass-through
  identity and measure columns come directly from `mix_0_detail` (Customer, SKU #,
  SKU Description, Category, Country, Lbs - AOP, Lbs - LE, Net Rev Per Lb - AOP,
  Net Rev Per Lb - LE). `Classification` is joined from `mix_base` on
  `(Customer, SKU #)` because it is not present on `mix_0_detail`. The Blended Rate
  and Lbs Subtotal pair (AOP/LE) is computed by aggregating `mix_1_sku` over the
  SUMIFS criteria columns `(Customer, Category)` and left-merging onto each detail
  row. The remaining columns are derived arithmetic (Share, Share Shift, Mix Rate,
  the three classification-conditional contributions, and SKU Mix).

- **`mix_3_category_bottomsup`** — one row per distinct `CustCatCountry`
  (`Customer - Category - Country`) group present in `mix_0_detail`. The row set,
  group identity, and aggregated measures (`Lbs - AOP/LE`, `Net-Revenue $ - AOP/LE`)
  are produced by a single groupby-sum over `mix_0_detail`. `Net Rev Per Lb - AOP/LE`
  is derived as `Net-Revenue $ / Lbs` (guarded to 0 when Lbs is 0). `Classification`
  is re-derived from the aggregated `Lbs - AOP/LE` using the zero-test formula. The
  Blended Rate and Lbs Subtotal pair is aggregated from `mix_2_category` over
  `(Customer, Country)` and left-merged onto the row set. The remaining derived
  arithmetic is identical to the SKU table.

- **`mix_4_customer_bottomsup`** — one row per distinct `CustCountry`
  (`Customer - Country`) group present in `mix_0_detail`. Same structure as the
  category table, grouped at `CustCountry`. The Blended Rate and Lbs Subtotal pair
  is aggregated from `mix_3_customer` over `(Country)` and left-merged onto the row
  set. The remaining derived arithmetic is identical.

The three new builder calls are added to `run_transforms` in
`src/mix_pipeline_run.py` after `mix_0_detail` is computed, and the three resulting
tables are added to its return dict. The tables then propagate through `_persist_all`
and the run summary in `src/mix_pipeline.py` without any change to that module.


## Inputs / Outputs

- **Inputs (DataFrames already in scope in `run_transforms`):**
  - `mix_0_detail` — row-level detail table; row set for the SKU table and source
    for the category/customer group aggregations. Carries the composite keys
    `CustCatCountry` and `CustCountry`.
  - `mix_base` — source of `Classification` at `(Customer, SKU #)` grain for the
    SKU table.
  - `mix_1_sku` — Blended Rate / Lbs Subtotal source for the SKU table, aggregated
    over `(Customer, Category)`.
  - `mix_2_category` — Blended Rate / Lbs Subtotal source for the category table,
    aggregated over `(Customer, Country)`.
  - `mix_3_customer` — Blended Rate / Lbs Subtotal source for the customer table,
    aggregated over `(Country)`.
- **Outputs:** three DataFrames returned from `run_transforms` and written to the
  same `.db` file as the existing tables via `write_table(..., if_exists="replace",
  index=False)` in `_persist_all`. They appear in the stdout run summary.
- **No new CLI flags, files, or environment variables are introduced.**
- **Config keys and defaults:** none added.
- **Versioning / backward-compatibility:** additive only. No existing table schema
  or column changes; no existing module behavior changes.


## API / CLI Surface

No new CLI commands or flags. The three tables are produced by the existing
`mix-pipeline` run.

New public functions (pure transforms, no I/O):

```python
def build_mix_2_sku_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_base: pd.DataFrame,
    mix_1_sku: pd.DataFrame,
) -> pd.DataFrame: ...

def build_mix_3_category_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_2_category: pd.DataFrame,
) -> pd.DataFrame: ...

def build_mix_4_customer_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_3_customer: pd.DataFrame,
) -> pd.DataFrame: ...
```

Shared helper in `src/_mix_bottomsup_helpers.py`:

```python
def build_contribution_columns(frame: pd.DataFrame) -> pd.DataFrame: ...
```

This helper computes the arithmetic columns that are identical across all three
tables (Share - AOP/LE, Share Shift, Mix Rate, New/Disco/Normal Contribution, SKU
Mix) from a frame that already carries the input columns (Classification, Lbs,
Net Rev Per Lb, Blended Rate, Lbs Subtotal).

- **Contracts and validation rules:**
  - All divisions are guarded to return `0.0` when the denominator is `0`, matching
    Excel `IF` guards and the existing `_safe_div` pattern.
  - Blended Rate and Lbs Subtotal columns are `fillna(0)` after the left-merge,
    because the source rollup tables exclude zero-Lbs groups, so unmatched merges
    must become `0`, not `NaN`.
  - Classification matching is case-sensitive against the lowercase tokens produced
    by the pipeline (`"normal"`, `"new"`, `"new distribution"`, `"lost distribution"`,
    `"eliminated"`).


## Data & State

The feature adds three tables to the existing SQLite database. No migration or
backfill is required; the tables are recreated on each run with
`if_exists="replace"`. The exact output column lists below are taken verbatim from
research section 11.

### `mix_2_sku_bottomsup`

- **Grain:** one row per `mix_0_detail` row.
- **Columns (in order):**
  `Customer`, `SKU #`, `SKU Description`, `Category`, `Country`, `Classification`,
  `Lbs - AOP`, `Lbs - LE`,
  `Net Rev Per Lb - AOP`, `Net Rev Per Lb - LE`,
  `Blended Rate - AOP`, `Blended Rate - LE`,
  `Lbs Subtotal - AOP`, `Lbs Subtotal - LE`,
  `Share - AOP`, `Share - LE`, `Share Shift`, `Mix Rate`,
  `New Contribution`, `Disco Contribution`, `Normal Contribution`, `SKU Mix`

### `mix_3_category_bottomsup`

- **Grain:** one row per distinct `CustCatCountry` (`Customer - Category - Country`)
  group present in `mix_0_detail`.
- **Columns (in order):**
  `CustCatCountry`, `Customer`, `Category`, `Country`,
  `Lbs - AOP`, `Lbs - LE`,
  `Net-Revenue $ - AOP`, `Net-Revenue $ - LE`,
  `Net Rev Per Lb - AOP`, `Net Rev Per Lb - LE`,
  `Classification`,
  `Blended Rate - AOP`, `Blended Rate - LE`,
  `Lbs Subtotal - AOP`, `Lbs Subtotal - LE`,
  `Share - AOP`, `Share - LE`, `Share Shift`, `Mix Rate`,
  `New Contribution`, `Disco Contribution`, `Normal Contribution`, `SKU Mix`

### `mix_4_customer_bottomsup`

- **Grain:** one row per distinct `CustCountry` (`Customer - Country`) group present
  in `mix_0_detail`.
- **Columns (in order):**
  `CustCountry`, `Customer`, `Country`,
  `Lbs - AOP`, `Lbs - LE`,
  `Net-Revenue $ - AOP`, `Net-Revenue $ - LE`,
  `Net Rev Per Lb - AOP`, `Net Rev Per Lb - LE`,
  `Classification`,
  `Blended Rate - AOP`, `Blended Rate - LE`,
  `Lbs Subtotal - AOP`, `Lbs Subtotal - LE`,
  `Share - AOP`, `Share - LE`, `Share Shift`, `Mix Rate`,
  `New Contribution`, `Disco Contribution`, `Normal Contribution`, `SKU Mix`

(The final column retains the name `SKU Mix` on all three tables per the Excel seed;
at the category and customer levels the label denotes a mix contribution at that
level.)

### Derived arithmetic (identical across all three tables)

Reproduced from the Excel column formulas:

- `Share - AOP` = `Lbs - AOP / Lbs Subtotal - AOP`, guarded to `0` when the subtotal
  is `0`.
- `Share - LE` = `Lbs - LE / Lbs Subtotal - LE`, guarded to `0` when the subtotal
  is `0`.
- `Share Shift` = `Share - LE − Share - AOP`.
- `Mix Rate` = `Net Rev Per Lb - AOP − Blended Rate - AOP`.
- `New Contribution` = `IF((Classification in {"new distribution", "new"}) AND
  Blended Rate - AOP ≠ 0, (Net Rev Per Lb - LE − Blended Rate - AOP) × Lbs - LE, 0)`.
- `Disco Contribution` = `IF((Classification in {"lost distribution", "eliminated"})
  AND Lbs Subtotal - AOP ≠ 0, −(Net Rev Per Lb - AOP − Blended Rate - AOP) ×
  Lbs - AOP × (Lbs Subtotal - LE / Lbs Subtotal - AOP), 0)`.
- `Normal Contribution` = `IF(Classification == "normal", Share Shift × Mix Rate ×
  Lbs Subtotal - LE, 0)`.
- `SKU Mix` = `New Contribution + Disco Contribution + Normal Contribution`.

For the category and customer tables, `Net Rev Per Lb - AOP/LE` is computed as
`Net-Revenue $ / Lbs` (guarded to `0` when `Lbs` is `0`) before the arithmetic above.

### Classification sourcing

- **SKU table:** `Classification` is joined from `mix_base` on `(Customer, SKU #)`.
  A `drop_duplicates` on `(Customer, SKU #, Classification)` of `mix_base` yields the
  join table; one `(Customer, SKU #)` carries one `Classification` value.
- **Category and customer tables:** `Classification` is re-derived from the
  aggregated `Lbs - AOP/LE` using the zero-test:
  ```
  if Lbs_AOP == 0:
      "eliminated" if Lbs_LE == 0 else "new distribution"
  else:
      "lost distribution" if Lbs_LE == 0 else "normal"
  ```
  The `"new"` token does not appear at the category or customer level; the zero-test
  maps that case to `"new distribution"`.

### Data transformations and invariants

- The SKU-table Blended Rate / Lbs Subtotal aggregation groups `mix_1_sku` by
  `(Customer, Category)` and sums `Net Rev Per Lb - AOP`, `Net Rev Per Lb - LE`,
  `Lbs - AOP`, `Lbs - LE`, then left-merges onto each detail row by
  `(Customer, Category)`. `Country` is intentionally not a join key, matching the
  Excel SUMIFS criteria. This relies on the well-formed-data expectation that each
  `(Customer, Category)` maps to a single `Country`; see Constraints & Risks.
- The category-table aggregation groups `mix_2_category` by `(Customer, Country)`
  (a grain match, so a single-row lookup) and merges by `(Customer, Country)`.
- The customer-table aggregation groups `mix_3_customer` by `(Country)` (a grain
  match, so a single-row lookup) and merges by `Country`.
- All three merges apply `fillna(0)` to the Blended Rate and Lbs Subtotal columns.

### Caching / persistence details

- Tables are written to the same `.db` file as the existing mix tables, on the same
  connection, with `if_exists="replace"`.

### Migration / backfill

- None. Tables are recreated on each run.


## Constraints & Risks

- **Confidentiality (hard constraint):** the source workbook
  `artifacts/LE v AOP Gross to Net Decomp.xlsx` is confidential. No form of its
  data may appear in the spec, any test, or any fixture. Use only fabricated example
  data (`SKU-001`, `Widget A`, `Category X`; `US` and `Canada` are not secret),
  consistent with the established precedent in the existing mix tests.
- **SUMIFS single-country expectation (SKU table):** the Excel formula for the SKU
  Blended Rate / Lbs Subtotal columns joins `mix_1_sku` on `(Customer, Category)`
  without `Country`, while `mix_1_sku` has grain `(Customer, Category, Country)`.
  The implementation joins on `(Customer, Category)` to match the Excel formula
  faithfully. This is correct only when each `(Customer, Category)` maps to a single
  `Country` in the data. If a customer-category combination spans multiple countries,
  the aggregation sums `Net Rev Per Lb` across country rows, which is not a meaningful
  blended rate. This expectation must be documented in the builder and validated
  against production data by the implementer.
- **Divide-by-zero parity:** every division must be guarded to return `0.0`, matching
  the Excel `IF` guards and the existing `_safe_div` pattern. Relying on pandas
  default `NaN`/`inf` propagation would pollute downstream sums and tie-outs.
- **Unmatched merges:** the rollup source tables (`mix_1_sku`, `mix_2_category`,
  `mix_3_customer`) exclude zero-Lbs groups, so a left-merge can produce `NaN` for
  Blended Rate / Lbs Subtotal on new-distribution or lost-distribution rows. These
  must be set to `0` via `fillna(0)` to match the Excel SUMIFS no-match behavior.
- **Case-sensitive classification matching:** the contribution formulas compare
  against the exact lowercase tokens produced by the pipeline. A case mismatch would
  silently route a row to the wrong contribution branch.
- **Classification re-derivation differs from SKU-level upstream:** at the category
  and customer levels, Classification is re-derived from aggregated Lbs and may differ
  from individual SKU-level classifications within the group. This is the intended
  Excel behavior and is replicated faithfully.
- **File-size limit (500 lines):** the transform logic is split across
  `src/mix_bottomsup.py` and `src/_mix_bottomsup_helpers.py`, consistent with the
  existing mix modules. Estimated total well under the limit.


## Implementation Strategy

- **Implementation scope:**
  - New `src/mix_bottomsup.py` containing the three builder functions and `__all__`.
  - New `src/_mix_bottomsup_helpers.py` containing the shared
    `build_contribution_columns` helper (the arithmetic identical across all three
    tables) and the `_classify_from_lbs` zero-test helper used by the category and
    customer builders.
  - Both new modules classified `T2` in `quality-tiers.yml`, consistent with the
    other mix transform modules.
  - `src/mix_pipeline_run.py`: import the three new builders; add three call sites in
    `run_transforms` after `mix_0_detail` is computed (passing the already-in-scope
    `mix_0_detail`, `mix_base`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`);
    extend the return dict with the three new tables.
  - `README.md`: list the three new tables in the mix-pipeline section.
- **No changes** to `src/mix_pipeline.py` or `src/pandas_io.py`. The new tables
  propagate through the `run_transforms` return dict into `_persist_all` and the run
  summary automatically. `mix_base` is already a parameter of `run_transforms`, so no
  signature change is required.
- **New functions to add:**
  - `build_mix_2_sku_bottomsup(mix_0_detail, mix_base, mix_1_sku)`
  - `build_mix_3_category_bottomsup(mix_0_detail, mix_2_category)`
  - `build_mix_4_customer_bottomsup(mix_0_detail, mix_3_customer)`
  - `build_contribution_columns(frame)` (helper)
  - `_classify_from_lbs(lbs_aop, lbs_le)` (helper)
- **Pure-transform + `pandas_io` boundary:** the new modules contain pure transforms
  only — no disk, network, or database access. All reads and writes remain in
  `src/pandas_io.py`, owned by the orchestrator.
- **Dependency changes:** none. Uses `pandas` and `numpy`, already in the project.
- **Logging/telemetry:** none added in the transform modules (pure functions). A
  data-quality warning for the SKU-table single-country expectation may be added at
  the builder boundary if the implementer chooses; it must not be a hard failure and
  must not emit confidential data.
- **Rollout:** additive feature, no feature flag. The tables appear on the next
  pipeline run.


## Definition of Done

- [ ] Three new derived tables (`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`,
      `mix_4_customer_bottomsup`) are produced by pure transforms with the exact
      columns and grains in Data & State, and persisted to the same SQLite database
      as the existing mix tables.
- [ ] The transform logic reproduces the Excel BottomsUp column formulas (pass-through,
      group aggregation, share, share-shift, mix-rate, the three classification-
      conditional contributions, and the SKU Mix total) with all divisions guarded to
      `0.0` and `fillna(0)` applied after the rollup merges.
- [ ] Classification is joined from `mix_base` on `(Customer, SKU #)` for the SKU
      table and re-derived from aggregated Lbs for the category and customer tables,
      with case-sensitive matching against the lowercase tokens.
- [ ] The new stage is wired into `run_transforms` in `src/mix_pipeline_run.py` and
      appears in the run summary, using the established pure-transform + `pandas_io`
      I/O boundary with no change to `src/mix_pipeline.py`.
- [ ] No confidential source data appears in any file, test, or fixture; tests use
      fabricated example data only.
- [ ] Both new modules are classified `T2` in `quality-tiers.yml`.
- [ ] Unit and property-based tests cover the behavior mapped in Acceptance Criteria.
- [ ] Edge cases and error handling (zero Lbs Subtotal, unmatched merges, each
      classification branch) are covered by tests.
- [ ] `README.md` mix-pipeline section lists the three new tables.
- [ ] Full toolchain passes in a single pass (Black, Ruff, Pyright, Pytest) with
      coverage thresholds (>= 85% line / >= 75% branch) met; no production file
      exceeds 500 lines.


## Acceptance Criteria

Each criterion maps to a verifiable test. Test names mirror the test plan in research
section 13; the test file is `tests/test_mix_bottomsup.py` (with one pipeline-level
assertion in `tests/test_mix_pipeline.py`).

- [x] **AC1 — SKU table columns and grain.** `mix_2_sku_bottomsup` carries the 22
      columns listed in Data & State, one row per `mix_0_detail` row. Verified by
      `test_build_mix_2_sku_bottomsup_columns_present` and
      `test_build_mix_2_sku_bottomsup_row_count_matches_detail`.
- [x] **AC2 — SKU normal tie-out.** For a fabricated `"normal"` SKU, `SKU Mix` equals
      `Normal Contribution` and ties out to a hand-calculated expected value. Verified
      by `test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout`.
- [x] **AC3 — New Contribution branch.** A `"new distribution"` or `"new"` SKU row
      produces nonzero `New Contribution` (and zero Disco/Normal). Verified by
      `test_build_mix_2_sku_bottomsup_new_contribution_active_when_new`.
- [x] **AC4 — Disco Contribution branch.** A `"lost distribution"` or `"eliminated"`
      SKU row produces nonzero `Disco Contribution` (and zero New/Normal). Verified by
      `test_build_mix_2_sku_bottomsup_disco_contribution_active_when_lost`.
- [x] **AC5 — Zero-subtotal share guard.** When `Lbs Subtotal` is `0`, the `Share`
      columns are `0` (not `NaN`). Verified by
      `test_build_mix_2_sku_bottomsup_zero_lbs_subtotal_share_is_zero`.
- [x] **AC6 — Classification join.** `Classification` on `mix_2_sku_bottomsup` matches
      the `mix_base` value for the same `(Customer, SKU #)`. Verified by
      `test_build_mix_2_sku_bottomsup_classification_joined_correctly`.
- [x] **AC7 — Category table columns and grain.** `mix_3_category_bottomsup` carries
      the columns listed in Data & State, one row per distinct `CustCatCountry`.
      Verified by `test_build_mix_3_category_bottomsup_columns_present` and
      `test_build_mix_3_category_bottomsup_row_count_matches_distinct_keys`.
- [x] **AC8 — Category tie-out.** A fabricated normal category group ties out `SKU Mix`
      to a hand-calculated expected value, with `Net Rev Per Lb` derived as
      `Net-Revenue $ / Lbs` and Classification re-derived from aggregated Lbs. Verified
      by `test_build_mix_3_category_bottomsup_sku_mix_tieout`.
- [x] **AC9 — Customer table columns and grain.** `mix_4_customer_bottomsup` carries
      the columns listed in Data & State, one row per distinct `CustCountry`. Verified
      by `test_build_mix_4_customer_bottomsup_columns_present` and
      `test_build_mix_4_customer_bottomsup_row_count_matches_distinct_keys`.
- [x] **AC10 — Customer tie-out.** A fabricated normal customer group ties out
      `SKU Mix` to a hand-calculated expected value. Verified by
      `test_build_mix_4_customer_bottomsup_sku_mix_tieout`.
- [x] **AC11 — SKU Mix identity (property-based).** For arbitrary valid float inputs,
      `SKU Mix = New Contribution + Disco Contribution + Normal Contribution` holds.
      Verified by `test_build_contribution_columns_sku_mix_equals_sum` (hypothesis),
      satisfying the T2 property-test-per-pure-function requirement.
- [x] **AC12 — Pipeline persistence.** The three tables appear in `sqlite_master`
      after an end-to-end `mix-pipeline` run on a single connection. Verified by
      `test_mix_pipeline_includes_bottomsup_tables` (or by extending `_DERIVED_TABLES`
      in `tests/test_mix_pipeline.py`).
- [x] **AC13 — Confidentiality.** No confidential source data appears in any file,
      test, or fixture; tests use fabricated example data only. Verified by review of
      the test and fixture files.
- [x] **AC14 — Toolchain and limits.** Black, Ruff, Pyright, and Pytest pass with
      coverage thresholds (>= 85% line / >= 75% branch) met, and no production file
      exceeds 500 lines. Verified by the toolchain run.
