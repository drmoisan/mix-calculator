# Phase 3 — LE Parity (Top Invariant)

Timestamp: 2026-06-06T15-22
Command: env -u VIRTUAL_ENV poetry run pytest tests/test_schema_loader_parity_le.py -v
EXIT_CODE: 0
Output Summary:
- 5 passed in 0.70s.
- test_le_parity_multi_row_collapse, test_le_parity_blank_totals_fill,
  test_le_parity_ppg_quirk, test_le_parity_multiple_keys[ppg_values0],
  test_le_parity_multiple_keys[ppg_values1] all PASSED.
- LE schema-driven output equals normalize_le.TARGET_COLUMNS exactly after the
  switch to in_output inclusion (YTD/YTG required:false, in_output:false, drop_columns []).
