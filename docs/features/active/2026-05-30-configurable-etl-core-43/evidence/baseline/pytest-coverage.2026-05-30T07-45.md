# Baseline — Pytest + Coverage (Issue #43)

Timestamp: 2026-05-30T07-45
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 604 passed, 0 failed, 1 warning, in 26.55s.
- TOTAL coverage row: 2768 statements, 22 missed; 514 branches, 11 partial.
- Baseline total line coverage: 99.21%.
- Baseline total branch coverage: 97.86%.
- Highest-miss module at baseline: src/schema_matching.py at 95% (Feature B, not modified by this feature).
- New feature modules (src/schema_formula.py, src/schema_loader.py) do not yet exist; their baseline coverage is N/A (introduced in Phases 1-3).
