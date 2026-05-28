# Test Inventory Post-Split

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command 'Select-String -Path tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py -Pattern "^def (test_[A-Za-z0-9_]+)" | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object'`

EXIT_CODE: 0

Output Summary:

11 test function names enumerated across the two test modules (sorted):

1. test_build_mix_0_detail_composite_keys
2. test_build_mix_1_sku_produces_sku_mix_column
3. test_build_mix_rollup_1_groups_by_customer_country_category
4. test_build_mix_rollup_4_returns_scalar_sum
5. test_build_mix_stage_keeps_only_nonzero_lbs_lines
6. test_category_layer_retains_single_scenario_volume
7. test_customer_layer_retains_single_scenario_volume
8. test_full_mix_chain_columns_and_fill_zero
9. test_layer_mix_equals_full_aggregation_minus_rollup
10. test_mix_4_country_subtracts_scalar_rollup_4
11. test_rollup_tie_out_customer_layer_sum_matches_scalar

Parity verdict: PASS. The sorted post-split inventory is set-equal to the pre-split baseline captured in `evidence/remediation-baseline/test-inventory-baseline.2026-05-27T22-40.md` (same 11 names; no test added, removed, or renamed).
