# Acceptance Verification (Issue #9)

Timestamp: 2026-05-26T20-00

Work Mode: full-feature. AC sources: `user-story.md` (Acceptance Criteria) and
`spec.md` (Definition of Done).

## user-story.md Acceptance Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Python pipeline reproduces the Power Query queries and persists each derived table to SQLite | PASS | `src/mix_pipeline.py` + `src/mix_pipeline_run.py`; `tests/test_mix_pipeline.py::test_mix_pipeline_end_to_end` persists 2 import + 19 derived tables |
| All nineteen derived tables persisted | PASS | `tests/test_mix_pipeline.py` `_DERIVED_TABLES` asserts every table exists in `sqlite_master` |
| Single CLI (`mix-pipeline`) runs both ETL imports + transforms end-to-end against one --input/--output, reusing the loaders | PASS | `src/mix_pipeline.py:main` reuses `normalize_le`/`load_aop`/`load_skulu`; integration test runs end-to-end |
| `SKU_LU` loaded via --skulu-input/--skulu-sheet, International->Country, 0->US/1->Canada | PASS | `src/load_skulu.py`; `tests/test_load_skulu.py::test_load_skulu_maps_country_codes`, `_renames_international_to_country` |
| Helper transforms implemented as pure, independently tested, no I/O | PASS | `src/mix_transforms.py` + `src/_mix_transforms_helpers.py`; `tests/test_mix_transforms.py`, `tests/test_mix_pivots.py` |
| Classification matches Power Query (SKU-level then customer-SKU level, exact zero tests) | PASS | `_sku_level_label`/`_cust_sku_label`/`classify_table`; `tests/test_mix_transforms.py::test_classify_table_*` |
| Mix rollups tie out within 1e-9 (ratio) / exact (integer measures) | PASS | `tests/test_mix_rollups.py::test_rollup_tie_out_customer_layer_sum_matches_scalar`; `tests/test_mix_pipeline.py::test_mix_pipeline_rollup_tie_out` |
| `Mix-3-Customer` uses `Customer Mix`; `Mix-4-Country` subtracts scalar `mix_rollup_4` | PASS | `src/mix_rollups.py::build_mix_3_customer`/`build_mix_4_country`; `tests/test_mix_rollups.py::test_full_mix_chain_columns_and_fill_zero`, `test_mix_4_country_subtracts_scalar_rollup_4` |
| No real confidential values in tests/fixtures/docs; only fabricated values | PASS | All fixtures use Acme Foods/Globex Market/Initech Grocers, SKU-00x, Widget A/B, Category X/Y; US/Canada not secret |
| No production/test/script file exceeds 500 lines | PASS | All new files <= 500 (max: `_mix_transforms_helpers.py` 379, `test_mix_rollups.py` 338) |
| Toolchain passes single clean run: Black, Ruff, Pyright strict, Pytest >= 85% line / >= 75% branch | PASS | Final QC artifacts: black/ruff/pyright EXIT 0; pytest 185 passed, 100% line/branch |

## spec.md Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Acceptance criteria documented and mapped to tests | PASS | This artifact |
| Behavior matches acceptance criteria | PASS | All AC PASS above |
| Tests added (unit/integration) | PASS | 7 new test files, +56 tests (129 -> 185) |
| Edge cases and error handling covered | PASS | zero-denominator guards, classification branches, loader-error exit, missing-measure fills |
| Docs updated (README, feature links) | PASS | `README.md` `mix-pipeline` section; feature folder linked |
| Telemetry/logging | PASS | `mix_pipeline.main` configures logging once; loader WARNING logging reused |
| Toolchain pass completed | PASS | Final QC artifacts |
| `mix-pipeline` runs end-to-end from one --input to one --output, all 19 derived tables | PASS | integration test |
| Six helper transforms pure and independently tested; classification two-level | PASS | `tests/test_mix_transforms.py` |
| Mix rollups tie out within 1e-9 / exact | PASS | tie-out tests |
| No file exceeds 500 lines | PASS | line-count checks in phase QA gates |
| Pytest coverage >= 85% line and >= 75% branch single clean run | PASS | 100%/100% |
| No real confidential values anywhere | PASS | fabricated values only |
| Seven new T2 entries in quality-tiers.yml | PASS (exceeded) | ten new T2 entries added (seven primary + three 500-line-limit split helpers); all classified T2 |

## Documented deviations from the plan

1. `src/mix_transforms.py` was split into `src/_mix_transforms_helpers.py` (primitives) + `src/mix_transforms.py` (pivots + re-exports) to stay under the 500-line limit, following the `_load_aop_helpers.py` pattern. The pivot tests were split into `tests/test_mix_pivots.py` for the same reason.
2. `src/mix_pipeline.py`'s steps 9-19 transform chain was factored into `src/mix_pipeline_run.py` so `main` holds no transform logic and the file stays under 500 lines.
3. `calc_ratios` was made tolerant of absent measure columns (treated as zero) so the later rollup stages — which carry only `Lbs`/`Net Rev Per Lb`/`Net-Revenue $` — can run `add_ratios` without a KeyError while keeping `Net Rev Per Lb` exact.
4. `quality-tiers.yml` gained ten T2 entries (the seven named modules plus the three split helpers) rather than seven, so every new project has a tier.

All deviations are mechanical (file splitting and a robustness adjustment) and do
not change the documented behavior; no acceptance criterion is left unmet.

## Result

All acceptance criteria and Definition-of-Done items are PASS. No criterion is
remediation-required.
