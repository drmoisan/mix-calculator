# Baseline — Tests + Coverage (pytest)

Timestamp: 2026-06-17T14-06
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Result: 1058 passed, 5 warnings in ~37s.
- Coverage TOTAL row: 5031 statements, 46 missed; 932 branches, 55 partial; combined 98%.
- Line coverage (statements): (5031-46)/5031 = 99.1%.
- Branch coverage: (932-55)/932 = 94.1%.
- Both exceed policy thresholds (line >= 85%, branch >= 75%).
- Touched-file baselines: src/schema_serialization.py 98% (line 486 missing-partial); src/schema_model.py 100%; src/_schema_loader_helpers.py covered via loader/parity suites.
