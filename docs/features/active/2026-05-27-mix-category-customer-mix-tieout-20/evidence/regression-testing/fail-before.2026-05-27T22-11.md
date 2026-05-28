# Fail-Before Evidence (Issue #20, AC4)

Timestamp: 2026-05-27T22-11

Command: `poetry run pytest tests/test_mix_rollups.py -k "single_scenario or full_aggregation_minus_rollup" -p no:randomly`

EXIT_CODE: 1

Output Summary:
The three new behavioral regression tests FAIL against the current (unfixed) code, confirming the volume-loss regression and the NPI-minus-rollup contract are not yet satisfied. Result: 3 failed, 9 deselected.

Failing tests:
- `test_category_layer_retains_single_scenario_volume` — the corrected category layer must aggregate the unfiltered `mix_base` at `{Customer, Country}`. Pre-fix, `build_mix_2_category(mix_base, rollup_2)` runs the old `unstack_to_long(mix_base, ...)` path, which zero-fills wide columns absent from raw long-form `mix_base`; the nonzero-Lbs filter then removes every row, so the `{Acme Foods, US}` group is absent (`assert 0 == 1`).
- `test_customer_layer_retains_single_scenario_volume` — analogous failure at `{Country}` granularity for `build_mix_3_customer(mix_base, rollup_3)`; the US group is empty pre-fix (`assert 0 == 1`).
- `test_layer_mix_equals_full_aggregation_minus_rollup` — independently recomputes the category-layer NPI via `build_mix_stage(mix_base, ["Customer", "Country"])` (2 rows) and asserts the builder produces the same group set; pre-fix the builder yields an empty frame (`assert 0 == 2`).

Note: `pytest-randomly` is not installed; `-p no:randomly` is a no-op disable and runs cleanly. The independent `build_mix_stage(mix_base, ["Customer", "Country"])` recomputation already produces the expected 2-row aggregation, confirming the corrected aggregation source is sound while the unfixed builder drops all rows.
