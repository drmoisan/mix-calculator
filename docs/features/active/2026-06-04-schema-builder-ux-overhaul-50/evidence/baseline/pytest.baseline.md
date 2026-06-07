# Pytest + Coverage Baseline

Timestamp: 2026-06-05T23-08
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 1
Output Summary:
- Tests: 931 passed, 1 failed (932 total).
- Total line coverage: 98% (TOTAL 4653 statements, 44 missed).
- Total branch coverage: 850 branches, 51 partial (~94% branch); aggregate term-missing TOTAL column reports 98%.
- Coverage on files in remediation scope (baseline):
  - src/gui/presenters/source_selection_presenter.py: 100% (confirmed in full term-missing output).
  - src/gui/_schema_discovery_wiring.py: 100%.
  - src/gui/services/workbook_reader.py: 100%.

## Pre-existing baseline failure (OUT OF REMEDIATION SCOPE)

- Failing test: tests/test_schema_formula.py::test_property_col_round_trips_values
- Cause: a hypothesis falsifying example uses a column literally named "col" which
  shadows the col() helper in the FormulaEvaluator symbol table, raising
  FormulaError ("'0.0' is not callable").
- This failure exists on the branch head BEFORE any cycle-3 change. No src/ or
  tests/ file was modified at the time this baseline was captured (verified via
  `git diff --stat`, which showed only evidence-artifact changes).
- This module (src/schema_formula.py, tests/test_schema_formula.py) is NOT in the
  B1/B2 remediation scope (which is source_selection_presenter.py,
  _schema_discovery_wiring.py, workbook_reader.py). It is recorded here as the
  authoritative baseline state; the cycle-3 fix must not regress it further, and
  fixing it is out of plan scope.
