# Pytest Coverage Baseline

Timestamp: 2026-06-15T21-45
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
  - 1041 passed, 5 warnings in 38.70s
  - Overall line coverage: 98% (4927 stmts, 46 missed)
  - Overall branch coverage: ~94% (926 branches, 55 missed) [computed: (926-55)/926 = 94.1%]
  - In-scope file `src/gui/widgets/_columns_tab_drag.py`: 94% line coverage (126 stmts, 4 missed), branches 22/5 missed
  - `tests/gui/test_columns_tab_widgets.py`: 12 tests all PASSED
  - All coverage thresholds satisfied: line >= 85%, branch >= 75%
