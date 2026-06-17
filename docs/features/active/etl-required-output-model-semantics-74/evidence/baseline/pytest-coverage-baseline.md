# Pytest + Coverage Baseline (cycle 2)

Timestamp: 2026-06-17T13-10

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- Tests: 1058 passed, 5 warnings, ~36s.
- Coverage TOTAL: statements 5031, missed 46; branches 932, partial 55; term headline 98%.
- Precise line coverage: 98.27% (>= 85% threshold).
- Precise branch coverage: 93.88% (covered 875 of 932) (>= 75% threshold).
- Target test files (`tests/test_default_schemas.py`, `tests/test_schema_loader_parity_aop.py`,
  `tests/test_schema_loader_parity_le.py`) included in the suite and passing.
