# Baseline — Position-independent column resolution + KEY handling

Timestamp: 2026-05-26T13-44
Branch: feature/etl-le-topline-input-2
Scope (planned): src/normalize_le.py (modify), src/le_columns.py (new); tests/test_le_columns.py (new), tests/test_normalize_le.py (modify), tests/le_fixtures.py (modify)

## Black
Command: poetry run black --check .
EXIT_CODE: 0
Output Summary: All done. 7 files would be left unchanged.

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
Output Summary: 46 passed. Coverage TOTAL 100% line, 100% branch.
  src/normalize_le.py 129 stmts, 0 miss, 36 branch, 0 brpart, 100%.
  src/calculator.py 100%. src/__init__.py 100%.

## Per-file baseline (for delta gate)
- src/normalize_le.py: line 100%, branch 100%
- src/le_columns.py: does not yet exist
