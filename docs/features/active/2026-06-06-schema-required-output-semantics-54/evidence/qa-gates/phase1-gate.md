# Phase 1 Gate — Model and Serialization

## Black
Timestamp: 2026-06-06T15-08
Command: env -u VIRTUAL_ENV poetry run black .
EXIT_CODE: 0
Output Summary: All done. 225 files left unchanged. No reformatting.

## Ruff
Timestamp: 2026-06-06T15-08
Command: env -u VIRTUAL_ENV poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings.

## Pyright
Timestamp: 2026-06-06T15-08
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Timestamp: 2026-06-06T15-08
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 960 passed, 3 warnings (2 new in_output serialization tests added).
- TOTAL: Stmts=4726, Miss=44, Branch=872, BrPart=51, combined Cover 98%.
- Line coverage: (4726-44)/4726 = 99.07%.
- Branch coverage: (872-51)/872 = 94.15%.
- Thresholds satisfied (line >= 85%, branch >= 75%).
