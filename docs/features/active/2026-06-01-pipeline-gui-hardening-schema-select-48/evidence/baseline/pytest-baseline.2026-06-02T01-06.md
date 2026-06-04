# Baseline — Pytest + Coverage (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 811 passed, 0 failed (1 non-error warning).
- Line coverage (headline TOTAL): 99% (3804 statements, 20 missed).
- Branch coverage: 678 branches, 23 partially covered -> approximately 96.6% branch coverage ((678-23)/678).
- Overall TOTAL Cover column: 99%.
- Offscreen Qt forced by tests/gui/conftest.py.
Both thresholds satisfied at baseline (line >= 85%, branch >= 75%).
