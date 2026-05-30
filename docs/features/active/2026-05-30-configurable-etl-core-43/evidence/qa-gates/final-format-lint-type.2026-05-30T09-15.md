# Final QA Gate — Format / Lint / Type (Issue #43)

Timestamp: 2026-05-30T09-15
Single clean pass across the whole repository.

## Stage 1 — Black
Command: poetry run black .
EXIT_CODE: 0
Output Summary: 150 files left unchanged. 0 format diffs.

## Stage 2 — Ruff
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 lint violations.

## Stage 3 — Pyright (strict)
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations (typeCheckingMode = strict).

## Suppression audit
- Scanned all feature files (src/schema_formula.py, src/_schema_formula_helpers.py,
  src/schema_loader.py, src/_schema_loader_helpers.py, typings/asteval/__init__.pyi,
  and the six new tests/test_schema_* files).
- 0 `# type: ignore`, 0 `# pyright: ignore`, 0 disallowed `# noqa`.
- The only `# noqa: E402` occurrences are the standard module-level fixture
  imports placed after a sys.path insertion in the test files (an import-order
  necessity, not a type/lint substance suppression).
- The asteval-untyped problem is resolved exclusively by the local stub
  typings/asteval/__init__.pyi; no suppression was introduced.
