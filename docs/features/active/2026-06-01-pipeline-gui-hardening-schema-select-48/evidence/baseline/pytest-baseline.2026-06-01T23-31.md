# Baseline — Pytest + Coverage

Timestamp: 2026-06-01T23-31
Command: $env:QT_QPA_PLATFORM="offscreen"; poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 801 passed, 0 failed, 1 warning.
- TOTAL coverage line: 3787 statements, 20 missed => 99.47% line coverage.
- TOTAL coverage branch: 674 branches, 23 partial => 96.59% branch coverage.
- Combined coverage headline reported by pytest-cov: 99%.
- Relevant target files at baseline: src/schema_registry.py 47 stmts / 6 branch / 100%; src/schema_matching.py 92 stmts / 28 branch / 97%.
- Both line (>= 85%) and branch (>= 75%) thresholds satisfied at baseline.
