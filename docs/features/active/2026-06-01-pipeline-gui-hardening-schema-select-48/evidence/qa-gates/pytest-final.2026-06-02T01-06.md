# Final QA — Pytest + Coverage (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 818 passed, 0 failed (1 non-error warning). Baseline was 811 passed; +7 new lifecycle/shutdown tests.
- TOTAL line coverage: 99.48% (3830 statements, 20 missed) — headline Cover column 99%.
- TOTAL branch coverage: 96.63% (682 branches, 23 partial).
- Per-module (changed/new files):
  - src/gui/runners.py: 100% line, 100% branch (61 stmts, 0 missed; 2 branches, 0 partial). Defensive Qt-lifetime recovery branch in await_active is `# pragma: no cover` excluded.
  - src/gui/_shutdown_wiring.py: 100% line, 100% branch (9 stmts, 0 missed; 2 branches, 0 partial).
  - src/gui/app.py: 99% line (139 stmts, 1 missed: line 297, the pre-existing QApplication-singleton fallback, unchanged this cycle); branch 1 partial (pre-existing).
- Offscreen Qt forced by tests/gui/conftest.py.
Both thresholds satisfied (line >= 85%, branch >= 75%). No regression on changed lines.
