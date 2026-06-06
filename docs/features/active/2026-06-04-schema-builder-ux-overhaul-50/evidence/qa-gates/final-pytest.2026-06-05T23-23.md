# Final QA — Pytest (full suite, coverage) (Cycle 4 Remediation)

Timestamp: 2026-06-05T23-23
Command: `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- Result: 942 passed, 0 failed, 3 warnings in 23.07s.
- `tests/test_schema_formula.py::test_property_col_round_trips_values` -> PASSED.
- `tests/test_schema_formula.py::test_evaluate_column_named_col_round_trips_via_col_callable` -> PASSED (new regression test).
- Overall coverage TOTAL: 98%.
  - Statements: 4664 total, 44 missed -> line coverage 99.06%.
  - Branches: 856 total, 51 partial -> branch coverage 94.04%.
- Targeted module `src/schema_formula.py`: 55 statements, 0 missed (line 100%); 20 branches, 0 partial (branch 100%).

Test-count delta vs baseline: baseline had 941 tests (940 passed + 1 failed); post-change has 942 passed (+1 from the new C1 regression test; the previously-failing property test now passes). No files were changed by the format/lint/type-check stages, so no loop restart was required.
