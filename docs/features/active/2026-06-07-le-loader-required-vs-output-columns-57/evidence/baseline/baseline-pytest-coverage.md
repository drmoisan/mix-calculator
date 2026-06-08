# Phase 0 — Pytest + Coverage Baseline

Timestamp: 2026-06-07T20-45
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Tests: 976 passed, 0 failed, 3 warnings, in 27.18s.
- Coverage TOTAL row: statements 4761, missed 44, branches 884, partial 54, 98% reported.
- Line coverage (computed): (4761 - 44) / 4761 = 99.08%.
- Branch coverage (computed): (884 - 54) / 884 = 96.15%.
- Both above policy thresholds (line >= 85%, branch >= 75%).

Files in scope at baseline (per term-missing): src/_normalize_le_columns.py and
src/normalize_le.py are fully exercised by the existing LE suite.
