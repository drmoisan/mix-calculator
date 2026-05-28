# Test Inventory Baseline (Pre-Remediation)

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command 'Select-String -Path tests/test_mix_rollups.py -Pattern "^def (test_[A-Za-z0-9_]+)" | ForEach-Object { $_.Matches[0].Groups[1].Value }'`

EXIT_CODE: 0

Output Summary:

11 test function names enumerated in `tests/test_mix_rollups.py`:

1. test_build_mix_rollup_1_groups_by_customer_country_category
2. test_build_mix_rollup_4_returns_scalar_sum
3. test_build_mix_1_sku_produces_sku_mix_column
4. test_full_mix_chain_columns_and_fill_zero
5. test_mix_4_country_subtracts_scalar_rollup_4
6. test_build_mix_0_detail_composite_keys
7. test_build_mix_stage_keeps_only_nonzero_lbs_lines
8. test_rollup_tie_out_customer_layer_sum_matches_scalar
9. test_category_layer_retains_single_scenario_volume
10. test_customer_layer_retains_single_scenario_volume
11. test_layer_mix_equals_full_aggregation_minus_rollup
