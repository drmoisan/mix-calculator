# Phase 0 — Baseline Pytest (coverage)

Timestamp: 2026-06-06T15-01
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Result: 958 passed, 3 warnings in ~25s
- Combined Cover (term-missing TOTAL column): 98%
- TOTAL: Stmts=4725, Miss=44, Branch=872, BrPart=51
- Line coverage headline: (4725-44)/4725 = 99.07%
- Branch coverage headline: (872-51)/872 = 94.15%
- Thresholds: line >= 85% and branch >= 75% both satisfied at baseline.
