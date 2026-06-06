# Phase 3 Gate — Parity Verification + Behavioral Tests

## Black
Timestamp: 2026-06-06T15-30
Command: env -u VIRTUAL_ENV poetry run black .
EXIT_CODE: 0
Output Summary: All done. 225 files left unchanged (after one earlier reformat of the new
test file, the loop restarted and black confirmed clean).

## Ruff
Timestamp: 2026-06-06T15-30
Command: env -u VIRTUAL_ENV poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings.

## Pyright
Timestamp: 2026-06-06T15-30
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Timestamp: 2026-06-06T15-30
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 963 passed, 3 warnings (parity green; stale drop_columns assertion updated; 4 new
  output-membership tests + 1 renamed exclusion test added).
- LE parity (5) and AOP parity (4) tests pass.
- TOTAL: Stmts=4725, Miss=44, Branch=872, BrPart=51, combined Cover 98%.
- Line coverage: (4725-44)/4725 = 99.07%; Branch: (872-51)/872 = 94.15%.
- Thresholds satisfied (line >= 85%, branch >= 75%).
