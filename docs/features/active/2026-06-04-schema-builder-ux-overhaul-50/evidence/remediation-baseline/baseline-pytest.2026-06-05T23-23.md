# Baseline — Pytest (full suite, coverage) (Cycle 4 Remediation)

Timestamp: 2026-06-05T23-23
Command: `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 1
Output Summary:
- Result: 1 failed, 940 passed, 3 warnings in 23.09s.
- Failing test (expected entry-state failure): `tests/test_schema_formula.py::test_property_col_round_trips_values`
- Overall coverage TOTAL: 98% (combined line+branch reporting line).
  - Statements: 4661 total, 44 missed -> line coverage 99.06%.
  - Branches: 856 total, 51 partial -> branch coverage 94.04%.
- Targeted module `src/schema_formula.py`: 52 statements, 0 missed (line 100%); 20 branches, 0 partial (branch 100%).

Notes: The single failure is the Hypothesis property test demonstrating the C1 `col`-shadowing defect. All other tests pass at baseline.
