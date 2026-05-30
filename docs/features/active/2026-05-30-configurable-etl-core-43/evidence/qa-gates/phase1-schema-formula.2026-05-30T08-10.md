# Phase 1 QA Gate — Formula Engine (Issue #43)

Timestamp: 2026-05-30T08-10
Single clean pass through all four stages (format -> lint -> type -> test).

## Stage 1 — Black
Command: poetry run black .
EXIT_CODE: 0
Output Summary: 142 files left unchanged. No reformatting required on the final pass.

## Stage 2 — Ruff
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 lint violations.

## Stage 3 — Pyright (strict)
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. asteval typed via local stub typings/asteval/__init__.pyi; NO suppression added.

## Stage 4 — Pytest + coverage
Command: poetry run pytest tests/test_schema_formula.py --cov=src.schema_formula --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 36 passed, 0 failed.
- src/schema_formula.py coverage: line 99% (77 statements, 0 missed); branch 97% (34 branches, 1 partial at 282->270, a property-test loop guard).
- Thresholds met: line 99% >= 85%, branch 97% >= 75%.
- No _schema_formula_helpers.py was required (module is 386 lines < 500).

## Notes
- T1 property tests present (>= 1 per pure function): safe_div (positive/non-positive/None/NaN denominators), alias_for (always-valid-identifier), build_alias_map (round-trip + unique), col (value round-trip), validator unsafe-corpus rejection, validator safe-arithmetic acceptance.
- AC6 covered: special-char columns (SKU #, Off Invoice $) reachable via identifier alias and via col() accessor; descriptive FormulaError on syntax error, attribute access, subscript, lambda, comprehension, non-whitelisted call, unknown column.
