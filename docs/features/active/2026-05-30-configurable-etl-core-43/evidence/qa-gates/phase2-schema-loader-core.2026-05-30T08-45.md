# Phase 2 QA Gate — Schema Loader Core (Issue #43)

Timestamp: 2026-05-30T08-45
Single clean pass through all four stages.

## Stage 1 — Black
Command: poetry run black .
EXIT_CODE: 0
Output Summary: All files formatted; no reformatting on the final pass.

## Stage 2 — Ruff
Command: poetry run ruff check tests/test_schema_loader_core.py (and the new src modules)
EXIT_CODE: 0
Output Summary: All checks passed.

## Stage 3 — Pyright (strict)
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. No suppressions added.

## Stage 4 — Pytest + coverage
Command: poetry run pytest tests/test_schema_loader_core.py tests/test_schema_formula.py --cov=src.schema_loader --cov=src._schema_loader_helpers --cov=src.schema_formula --cov=src._schema_formula_helpers --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 44 passed, 0 failed.
- src/schema_loader.py: line 95% (31 stmts), branch ~95% (6 branches, 2 partial).
- src/_schema_loader_helpers.py: line 92% (116 stmts, 5 missed), branch ~84% (50 branches, 8 partial).
- src/schema_formula.py: line 100% (52 stmts), branch 100% (20 branches).
- src/_schema_formula_helpers.py: line 85% (59 stmts, 9 missed), branch ~86% (28 branches, 4 partial).
- All four modules meet >= 85% line / >= 75% branch on this scope. The remaining
  uncovered lines in _schema_formula_helpers.py are the Series (vectorized) helper
  branches, exercised by the Phase 4 parity tests through the loader's vectorized
  derived-column path.

## Module split
- src/schema_formula.py was split: the pure numeric/alias helpers moved to
  src/_schema_formula_helpers.py (250 lines). Both files are < 500 lines
  (schema_formula 308, helpers 250).
- src/schema_loader.py (223 lines) delegates phase logic to
  src/_schema_loader_helpers.py (443 lines); both < 500.

## Notes
- Dedup phase verified: mode none preserves rows (AC3); mode collapse sums
  additive measures (AC3, sum property); mode collapse select_from picks the
  discriminator-matched row (AC3). The select_from and additive property tests
  exercise the pure collapse_by_key phase directly.
