# Pass-After — Regression Tests (Issue #37)

Timestamp: 2026-05-29T21-59
Command: env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py::test_zero_volume_deduction_yields_dollar_derived_net_price_impact tests/test_mix_rate_impacts.py::test_single_sku_group_rolls_up_to_category_net_price_impact tests/test_mix_rate_impacts.py::test_single_fine_grain_recompute_equals_carried_ratio -v -p no:cacheprovider
EXIT_CODE: 0
Output Summary:
- 3 passed in 0.52s against the post-change production code.
- AC3 (test_zero_volume_deduction_yields_dollar_derived_net_price_impact): PASSED. The zero-volume deduction sub-row yields a dollar-derived non-zero Calc Net Price Impact (2.0 * 10.0 = 20.0), not the zero the carried summed ratio implied.
- AC4 (test_single_sku_group_rolls_up_to_category_net_price_impact): PASSED. The SKU-level Calc Net Price Impact rolled to the {Customer, Category} grain equals the category net-price impact for the single-SKU group; SKU Mix residual = 0 within 1e-9.
- AC5 (test_single_fine_grain_recompute_equals_carried_ratio): PASSED. Single-fine-grain recompute equals the previously carried ratios.
- Full suite (P2-T4): 510 passed, including all four pre-existing tests in tests/test_mix_rate_impacts.py.
