# Phase 3 — AOP Tests QA

Timestamp: 2026-05-26T14-03

This gate confirms the AOP test suites (`tests/test_load_aop.py`,
`tests/test_load_aop_io.py`, `tests/aop_fixtures.py`) pass and that coverage
meets the thresholds with the AOP tests included. The four stages ran in order
and reached a clean single pass. The loop was restarted several times during
this phase for Black reformatting, a Ruff F401 autofix, a Pyright strict
`Scalar`->`float` fix (routed through the existing `as_float` helper), and two
production hardening fixes surfaced by the new tests (see Deviation Note).

## Stage 1 — Black

Command: poetry run black .
EXIT_CODE: 0
Output Summary: PASS. 19 files left unchanged; 0 reformatted (stable pass).

## Stage 2 — Ruff

Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: PASS. "All checks passed!"; 0 lint errors.

## Stage 3 — Pyright (strict)

Command: poetry run pyright
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations.

## Stage 4 — Pytest with coverage

Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary: PASS. 110 passed, 0 failed. Coverage TOTAL line 100% (402 stmts,
0 missed), branch 100% (112 branches, 0 partial). AOP modules covered:
src\load_aop.py 100% (69 stmts, 14 branches), src\_load_aop_helpers.py 100%
(74 stmts, 16 branches). LE/ETL modules remain at 100%. Line coverage = 100%
(>= 85% threshold met); branch coverage = 100% (>= 75% threshold met).

## Deviation Note (in-task production hardening from new tests)

Two production fixes were applied as micro-actions to satisfy P3 acceptance
criteria, both within the scope of the planned tasks:

1. `clean_label_sentinels` (`src/_load_aop_helpers.py`): the property test
   (P3-T6) found that assigning a mixed None/number Python list let pandas infer
   a float column and re-coerce `None` back to `NaN`, breaking the documented
   "sentinels become None" contract. The cleaned column is now assigned as an
   object-dtype Series so the `None` markers survive. This makes the spec's
   sentinel->None behavior hold for all-numeric label columns.

2. `main` (`src/load_aop.py`): the `--snake-case` CLI test (P3-T8) found that
   `print_summary` accessed canonical column names (`KEY`, `Customer`, ...) after
   the snake_case rename had been applied to the same frame, raising
   `KeyError: 'KEY'`. `main` now persists a renamed copy while computing the
   summary from the validated (canonical-named) frame, so the stdout summary
   layout is identical with or without `--snake-case`.

Two test assertions were also corrected to match the spec-defined behavior:
the index-name test asserted `ix_aop_skunum` but the spec rule (space->`_`,
`#`->`num`) yields `ix_aop_sku_num`; and an awkward `isinstance(float(...), float)`
assertion was replaced with a value assertion via `as_float`.
