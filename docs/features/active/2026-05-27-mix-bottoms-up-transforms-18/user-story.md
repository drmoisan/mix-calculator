# `mix-bottoms-up-transforms` — User Story

- Issue: #18
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-05-27T20-46

## Story Statement

- As a finance/FP&A analyst who runs the mix-decomposition pipeline, I want the
  three BottomsUp views (`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`,
  `mix_4_customer_bottomsup`) written to the same SQLite database as the existing
  TopDown tables, so that I can analyze the gross-to-net mix shift from the
  row/group level upward without recomputing the BottomsUp tabs in Excel.
- As a finance/FP&A analyst, I want the BottomsUp tables produced automatically by
  the existing `mix-pipeline` run with no new flags or commands, so that I obtain
  the SKU, Category, and Customer mix views from a single pipeline invocation
  against the source workbook.

## Problem / Why

The end-to-end mix-decomposition pipeline (issue #9) replicates the TopDown mix
tables (`mix_1_sku`, `mix_2_category`, `mix_3_customer`) from the source workbook.
The same workbook also contains three "BottomsUp" tabs — `2-SKU-Mix-BottomsUp`,
`3-Category-Mix-BottomsUp`, and `4-Customer-Mix-BottomsUp` — that are not yet
reproduced by the pipeline. These BottomsUp tables decompose the gross-to-net mix
shift from the row/group level upward, and are derived entirely from tables the
pipeline already produces. They should be replicated as an additional transform
stage and persisted to the same SQLite database as the rest of the pipeline.


## Personas & Scenarios

- Persona: Priya, a finance/FP&A analyst.
  - Who the user is: an FP&A analyst responsible for the periodic gross-to-net
    revenue mix analysis. She owns the source workbook and runs the mix-pipeline
    to produce the SQLite database the downstream reporting consumes.
  - What they care about: the BottomsUp mix views tying out exactly to the Excel
    workbook formulas, and being available alongside the existing TopDown tables
    in one database for querying.
  - Their constraints: the source workbook is confidential and its data must not
    be persisted to repository files, tests, or fixtures. She does not write code
    and relies on the pipeline producing correct outputs without manual steps.
  - Their goals and frustrations: she wants to query the BottomsUp views directly
    from the database. Today she must recompute the BottomsUp tabs in Excel, which
    is manual and not reproducible alongside the pipeline output.
  - Their context and motivations: she works against a single SQLite database that
    already holds the TopDown tables, and wants the BottomsUp views in the same
    place so analysis spans both without exporting from Excel.
- Scenario: producing and querying the BottomsUp tables.
  - Who is acting: Priya, the FP&A analyst.
  - What triggered the action: a new reporting period requires the BottomsUp mix
    decomposition at the SKU, Category, and Customer levels.
  - Steps they take:
    1. Priya runs the existing `mix-pipeline` command against the source workbook,
       using the same invocation she already uses for the TopDown tables.
    2. The pipeline computes the existing tables and then the new transform stage
       builds `mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, and
       `mix_4_customer_bottomsup` from tables the pipeline already produces.
    3. The three new tables are written to the same `.db` file on the same
       connection as the existing tables and are listed in the stdout run summary.
    4. Priya opens the SQLite database and queries the three new tables to review
       Share, Share Shift, Mix Rate, the three contribution columns, and the
       SKU Mix total at each level.
  - Obstacles or decisions: no new flags or commands are needed; the tables appear
    on the next run. If a value looks unexpected, she compares it against the Excel
    BottomsUp tab, which the transforms reproduce.
  - Outcome they expect: the three BottomsUp views are present in the database with
    the documented columns and grains, tie out to the Excel formulas, and can be
    queried without recomputing in Excel.


## Acceptance Criteria

`spec.md` is the authoritative source for these acceptance criteria. The list below
reproduces AC1–AC14 from `spec.md` verbatim, and the two lists must stay in sync; if
they ever diverge, `spec.md` governs.

- [x] **AC1 — SKU table columns and grain.** `mix_2_sku_bottomsup` carries the 22 columns listed in Data & State, one row per `mix_0_detail` row. Verified by `test_build_mix_2_sku_bottomsup_columns_present` and `test_build_mix_2_sku_bottomsup_row_count_matches_detail`.
- [x] **AC2 — SKU normal tie-out.** For a fabricated `"normal"` SKU, `SKU Mix` equals `Normal Contribution` and ties out to a hand-calculated expected value. Verified by `test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout`.
- [x] **AC3 — New Contribution branch.** A `"new distribution"` or `"new"` SKU row produces nonzero `New Contribution` (and zero Disco/Normal). Verified by `test_build_mix_2_sku_bottomsup_new_contribution_active_when_new`.
- [x] **AC4 — Disco Contribution branch.** A `"lost distribution"` or `"eliminated"` SKU row produces nonzero `Disco Contribution` (and zero New/Normal). Verified by `test_build_mix_2_sku_bottomsup_disco_contribution_active_when_lost`.
- [x] **AC5 — Zero-subtotal share guard.** When `Lbs Subtotal` is `0`, the `Share` columns are `0` (not `NaN`). Verified by `test_build_mix_2_sku_bottomsup_zero_lbs_subtotal_share_is_zero`.
- [x] **AC6 — Classification join.** `Classification` on `mix_2_sku_bottomsup` matches the `mix_base` value for the same `(Customer, SKU #)`. Verified by `test_build_mix_2_sku_bottomsup_classification_joined_correctly`.
- [x] **AC7 — Category table columns and grain.** `mix_3_category_bottomsup` carries the columns listed in Data & State, one row per distinct `CustCatCountry`. Verified by `test_build_mix_3_category_bottomsup_columns_present` and `test_build_mix_3_category_bottomsup_row_count_matches_distinct_keys`.
- [x] **AC8 — Category tie-out.** A fabricated normal category group ties out `SKU Mix` to a hand-calculated expected value, with `Net Rev Per Lb` derived as `Net-Revenue $ / Lbs` and Classification re-derived from aggregated Lbs. Verified by `test_build_mix_3_category_bottomsup_sku_mix_tieout`.
- [x] **AC9 — Customer table columns and grain.** `mix_4_customer_bottomsup` carries the columns listed in Data & State, one row per distinct `CustCountry`. Verified by `test_build_mix_4_customer_bottomsup_columns_present` and `test_build_mix_4_customer_bottomsup_row_count_matches_distinct_keys`.
- [x] **AC10 — Customer tie-out.** A fabricated normal customer group ties out `SKU Mix` to a hand-calculated expected value. Verified by `test_build_mix_4_customer_bottomsup_sku_mix_tieout`.
- [x] **AC11 — SKU Mix identity (property-based).** For arbitrary valid float inputs, `SKU Mix = New Contribution + Disco Contribution + Normal Contribution` holds. Verified by `test_build_contribution_columns_sku_mix_equals_sum` (hypothesis), satisfying the T2 property-test-per-pure-function requirement.
- [x] **AC12 — Pipeline persistence.** The three tables appear in `sqlite_master` after an end-to-end `mix-pipeline` run on a single connection. Verified by `test_mix_pipeline_includes_bottomsup_tables` (or by extending `_DERIVED_TABLES` in `tests/test_mix_pipeline.py`).
- [x] **AC13 — Confidentiality.** No confidential source data appears in any file, test, or fixture; tests use fabricated example data only. Verified by review of the test and fixture files.
- [x] **AC14 — Toolchain and limits.** Black, Ruff, Pyright, and Pytest pass with coverage thresholds (>= 85% line / >= 75% branch) met, and no production file exceeds 500 lines. Verified by the toolchain run.


## Non-Goals

- No new CLI flags or commands. The three tables are produced by the existing
  `mix-pipeline` run; the command surface is unchanged.
- No changes to existing tables or existing TopDown logic. The feature is additive;
  no existing table schema, column, or module behavior is modified.
- No user interface. The tables are queried directly from the SQLite database.
- The confidential source workbook data is never persisted to repository files,
  tests, or fixtures. Tests use fabricated example data only.
