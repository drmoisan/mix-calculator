# Baseline — Pytest + coverage (P0-T6)

Timestamp: 2026-06-06T11-45

Command: poetry run pytest --cov --cov-branch --cov-report=term-missing

EXIT_CODE: 0

Output Summary:
- Total tests passed: 818 passed, 1 warning, in ~24s.
- TOTAL coverage row: 3830 statements, 20 missed; 682 branches, 23 partial; 99%.
- Total line coverage: (3830 - 20) / 3830 = 99.48%.
- Total branch coverage: (682 - 23) / 682 = 96.63%.
- In-scope module baselines: src/etl_key.py 100%; src/normalize_le.py 100%
  (124 stmts / 26 branches); src/load_aop.py 100% (87 stmts / 24 branches).

These numbers are the no-regression reference for AC-8: post-change total line
coverage must remain >= 85% and branch coverage >= 75%, with no regression on
changed lines.
