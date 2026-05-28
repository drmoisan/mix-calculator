# AC8 Tie-Out Module — Post-Split Verification

Timestamp: 2026-05-27T22-40

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups_tieout.py -v`

EXIT_CODE: 0

Output Summary:

```
tests/test_mix_rollups_tieout.py::test_category_layer_retains_single_scenario_volume PASSED [ 33%]
tests/test_mix_rollups_tieout.py::test_customer_layer_retains_single_scenario_volume PASSED [ 66%]
tests/test_mix_rollups_tieout.py::test_layer_mix_equals_full_aggregation_minus_rollup PASSED [100%]

============================== 3 passed in 0.45s ==============================
```

- Total: 3
- Passed: 3
- Failed: 0
- Skipped: 0
- Deselected: 0
- xfailed: 0

Verdict: PASS. The AC8 four-layer tie-out / issue #20 regression tests all pass after the split. The verification path is preserved.
