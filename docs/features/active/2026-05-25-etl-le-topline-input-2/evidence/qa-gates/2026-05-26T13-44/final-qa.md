# Final QA Gate — Position-independent column resolution + KEY handling

Timestamp: 2026-05-26T13-44
Branch: feature/etl-le-topline-input-2

## Scope (touched files, final line counts)
Production:
- src/normalize_le.py (modified) — 483 lines
- src/le_columns.py (new) — 204 lines
- src/le_key.py (new) — 262 lines
Tests:
- tests/test_le_columns.py (new) — 168 lines
- tests/test_le_key.py (new) — 209 lines
- tests/test_normalize_le.py (modified) — 435 lines
- tests/test_normalize_le_io.py (modified) — 362 lines
- tests/le_fixtures.py (modified) — 316 lines

All production and test files are < 500 lines.

## Black
Command: poetry run black .
EXIT_CODE: 0
Output Summary: 11 files left unchanged (no reformatting needed in final pass).

## Ruff
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed (0 findings).

## Pyright
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary: 72 passed. Coverage TOTAL 100% line, 100% branch.
  src/normalize_le.py 120 stmts, 0 miss, 24 branch, 0 brpart, 100%.
  src/le_columns.py 48 stmts, 0 miss, 22 branch, 0 brpart, 100%.
  src/le_key.py 56 stmts, 0 miss, 30 branch, 0 brpart, 100%.

## Delta vs baseline (2026-05-26T13-44 baseline)
- Ruff delta: 0 new findings.
- Pyright delta: 0 new diagnostics.
- Pytest delta: 0 new failures (46 -> 72 tests; +26 net).
- Coverage delta: overall 100% -> 100% (no regression).
  - src/normalize_le.py: 100% -> 100% (line + branch).
  - src/le_columns.py: new module, 100% line / 100% branch (>= 85%/75% gate).
  - src/le_key.py: new module, 100% line / 100% branch (>= 85%/75% gate).

## Suppressions
No new suppressions added. The two pre-existing pandas-boundary suppressions
remain (read_excel and to_sql), both `# pyright: ignore[reportUnknownMemberType]`.
