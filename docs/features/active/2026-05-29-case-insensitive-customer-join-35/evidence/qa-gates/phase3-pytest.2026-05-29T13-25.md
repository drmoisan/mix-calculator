# Phase 3 — Pytest pass-after

Timestamp: 2026-05-29T13-25
Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_lookups.py -v`
EXIT_CODE: 0

Output Summary:
- 18 passed, 0 failed.
- Pre-existing tests (all PASS): `test_build_customer_lu_distinct_pairs`, `test_build_aop_norm_drops_dimensions_and_adds_scenario`, `test_build_le_norm_drops_dimensions_and_adds_scenario`, `test_build_aop_vs_le_pivots_filters_cases_and_diffs`, `test_build_aop_vs_le_missing_scenario_column_filled_zero`, `test_build_aop_vs_le_classifies_normal_for_nonzero_lbs`, `test_build_mix_base_enriches_and_filters`, `test_build_mix_base_left_join_unmatched_is_null`, `test_build_mix_base_excludes_inactive`.
- AC2 tests PASS: `test_build_aop_norm_strips_customer_whitespace`, `test_build_le_norm_strips_customer_whitespace`.
- AC3+AC5 test PASS: `test_build_aop_vs_le_casefold_winco_merges`.
- AC4 test PASS: `test_build_customer_lu_strips_whitespace`.
- AC6a-e tests PASS: `test_build_aop_vs_le_casefold_collapses_three_casings`, `test_build_aop_vs_le_casefold_strips_whitespace`, `test_build_aop_vs_le_display_aop_casing_wins`, `test_build_aop_vs_le_le_only_keeps_le_casing`, `test_build_aop_vs_le_five_casings_collapse_to_one`.
