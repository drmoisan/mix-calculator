# Phase 3 — AOP Parity (Top Invariant)

Timestamp: 2026-06-06T15-22
Command: env -u VIRTUAL_ENV poetry run pytest tests/test_schema_loader_parity_aop.py -v
EXIT_CODE: 0
Output Summary:
- 4 passed in 0.66s.
- test_aop_parity_with_ytg, test_aop_parity_without_ytg,
  test_aop_parity_sentinel_clean_labels, test_aop_parity_no_row_collapse all PASSED.
- AOP schema-driven output equals load_aop output exactly, including the
  optional-but-output YTG (required:false, in_output:true), after the none-mode emit
  path switched to in_output filtering.
