# Parity and Full-Suite Verification (LE + AOP)

Timestamp: 2026-06-07T20-45
Command: poetry run pytest tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py tests/test_normalize_le_io.py tests/test_normalize_le_totals.py tests/test_etl_columns.py tests/test_load_aop.py --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- 100 passed, 0 failed, in 13.62s.
- All LE loader tests pass: parity for the standard full-column LE-8 + 4 source is
  confirmed. The dedicated parity test
  (test_full_column_source_output_parity_with_standard_fixture) and the existing
  full-column assertion (test_load_source_header_and_columns:
  set(frame.columns) == set(SOURCE_COLUMNS)) both pass, confirming the located
  optionals (YTD/YTG, Super Category) are carried exactly as before.
- AOP tests (tests/test_load_aop.py) pass unchanged: src/load_aop.py was not modified.
- The TOTAL coverage row reads low here (10%) only because this command runs a subset
  of test files; whole-suite coverage is recorded in final-pytest-coverage.md.

PARITY OUTCOME: PASS. The standard full-column LE source output is unchanged.
