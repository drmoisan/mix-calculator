# Final QA — Tests + Coverage (pytest)

Timestamp: 2026-06-17T15-26
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Result: 1070 passed, 5 warnings in ~30s (up from 1058 at baseline; 12 new tests).
- Coverage TOTAL row: 5057 statements, 46 missed; 942 branches, 57 partial; combined 98%.
- Line coverage (statements): (5057-46)/5057 = 99.1%  (>= 85% threshold).
- Branch coverage: (942-57)/942 = 94.0%  (>= 75% threshold).
- Touched/new files:
  - src/_schema_migration.py: 100% line.
  - src/_schema_loader_keepset.py: 95% line (2 partial branches only).
  - src/_schema_model_specs.py: 100% line.
  - src/schema_serialization.py: 98% line.
  - src/_schema_loader_helpers.py: 92% line.
- All tests pass; both coverage thresholds met.
