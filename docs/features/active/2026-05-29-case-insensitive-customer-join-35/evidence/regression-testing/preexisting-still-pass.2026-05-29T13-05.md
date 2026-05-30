# Pre-existing tests still pass (with new tests failing as expected)

Timestamp: 2026-05-29T13-05
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py -q`
EXIT_CODE: 1

Output Summary:
- 10 passed, 8 failed, 1 warning.
- Pre-existing tests (all PASS):
  - `test_build_customer_lu_distinct_pairs`
  - `test_build_aop_norm_drops_dimensions_and_adds_scenario`
  - `test_build_le_norm_drops_dimensions_and_adds_scenario`
  - `test_build_aop_vs_le_pivots_filters_cases_and_diffs`
  - `test_build_aop_vs_le_missing_scenario_column_filled_zero`
  - `test_build_aop_vs_le_classifies_normal_for_nonzero_lbs`
  - `test_build_mix_base_enriches_and_filters`
  - `test_build_mix_base_left_join_unmatched_is_null`
  - `test_build_mix_base_excludes_inactive`
  - `test_build_aop_vs_le_le_only_keeps_le_casing` (AC6d regression guard, passes today and must keep passing)
- New failing tests (expect-fail, will pass after Phase 2/3 implementation):
  - `test_build_aop_vs_le_casefold_winco_merges` (AC5)
  - `test_build_aop_vs_le_casefold_collapses_three_casings` (AC6a)
  - `test_build_aop_vs_le_casefold_strips_whitespace` (AC6b)
  - `test_build_aop_vs_le_display_aop_casing_wins` (AC6c)
  - `test_build_aop_vs_le_five_casings_collapse_to_one` (AC6e)
  - `test_build_customer_lu_strips_whitespace` (AC4)
  - `test_build_aop_norm_strips_customer_whitespace` (AC2)
  - `test_build_le_norm_strips_customer_whitespace` (AC2)

The exit code is 1 because expected-fail tests are still failing; no pre-existing assertion was modified.
