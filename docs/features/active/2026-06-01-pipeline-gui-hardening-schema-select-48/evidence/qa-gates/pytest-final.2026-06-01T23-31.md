# Final QA — Pytest + Coverage

Timestamp: 2026-06-01T23-31
Command: $env:QT_QPA_PLATFORM="offscreen"; poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 811 passed, 0 failed, 1 warning (baseline was 801 passed; +10 new tests).
- TOTAL coverage line: 3804 statements, 20 missed => 99.47% line coverage (>= 85%).
- TOTAL coverage branch: 678 branches, 23 partial => 96.61% branch coverage (>= 75%).
- Combined coverage headline reported by pytest-cov: 99%.
- Changed/new file coverage:
  - src/gui/_schema_list_wiring.py: 7 stmts / 2 branch / 100%.
  - src/schema_registry.py: 54 stmts / 8 branch / 100%.
  - src/gui/app.py: 137 stmts / 10 branch / 99% (only pre-existing line 299, the
    fresh-QApplication construction branch, remains uncovered; unrelated to this change).
- Both line and branch thresholds satisfied; all gates green in a single pass.
