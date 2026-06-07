# Phase 2 Gate — Loader Output Determination and Bundled Schemas

## Black
Timestamp: 2026-06-06T15-18
Command: env -u VIRTUAL_ENV poetry run black .
EXIT_CODE: 0
Output Summary: All done. 225 files left unchanged.

## Ruff
Timestamp: 2026-06-06T15-18
Command: env -u VIRTUAL_ENV poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings.

## Pyright
Timestamp: 2026-06-06T15-18
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Timestamp: 2026-06-06T15-18
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 1
Output Summary:
- 959 passed, 1 failed, 3 warnings.
- The single failure is tests/test_default_schemas.py::test_le_drops_ytd_ytg_source_column,
  which asserts the now-stale `drop_columns == ("YTD/YTG",)`. The bundled LE schema's
  drop_columns is now `()` per AC-1, so this assertion is intentionally stale and is
  updated by the immediately-following task P3-T3 (plan-sequenced).
- LE and AOP parity tests are NOT among the failures (parity preserved).
- TOTAL: Stmts=4725, Miss=44, Branch=872, BrPart=51, combined Cover 98%.
- Line coverage: (4725-44)/4725 = 99.07%; Branch: (872-51)/872 = 94.15%.
- This gate's lone failure is the planned stale-assertion update; the green gate is
  re-established in Phase 3 (P3-T5).
