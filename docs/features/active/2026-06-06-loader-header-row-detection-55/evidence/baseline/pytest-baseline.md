# Phase 0 — Pytest + Coverage Baseline (Issue #55)

Timestamp: 2026-06-07T02-36
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0

Output Summary:
- Tests: 966 passed, 0 failed, 3 warnings in 24.90s.
- TOTAL coverage row: 4725 statements, 44 missed, 872 branches, 51 partial branches.
- Line coverage (total): 98% (4725 stmts, 44 missed).
- Branch coverage (total): approx 94.1% ((872 - 51) / 872 = 821/872).
- In-scope module baselines:
  - `src/normalize_le.py` — 100% (107 stmts, 20 branches, 0 missed).
  - `src/load_aop.py` — not shown in tail excerpt; covered by full suite (see final-pytest for post-change value).
  - `src/pandas_io.py` — 100% (15 stmts, 0 branches, 0 missed).
- Baseline line coverage 98% and branch coverage approx 94.1% are well above the
  policy floors (line >= 85%, branch >= 75%).
