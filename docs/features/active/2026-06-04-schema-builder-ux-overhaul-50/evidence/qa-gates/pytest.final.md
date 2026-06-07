# Pytest + Coverage Final

Timestamp: 2026-06-05T23-17
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 1
Output Summary:
- Tests: 940 passed, 1 failed (941 total). Net +9 tests vs baseline (931 passed),
  all 9 new cycle-3 tests pass.
- Total line coverage: 98% (TOTAL 4661 statements, 44 missed).
- Total branch coverage: 856 branches, 51 partial (term-missing TOTAL column reports 98%).
- Coverage on files in remediation scope (post-change):
  - src/gui/_schema_discovery_wiring.py: 100% (20 stmts, 4 branches, 0 missed/partial).
  - src/gui/presenters/source_selection_presenter.py: 99% (76 stmts, 16 branches,
    0 missed; one PRE-EXISTING partial branch 287->289 in _apply_activation_decision,
    unrelated to the cycle-3 guard, which is fully covered).
  - src/gui/services/workbook_reader.py: 100% (28 stmts, 6 branches, 0 missed/partial).

## Pre-existing baseline failure (OUT OF REMEDIATION SCOPE — NOT a regression)

- Failing test: tests/test_schema_formula.py::test_property_col_round_trips_values
- This is the identical pre-existing failure captured in the Phase 0 baseline
  (evidence/baseline/pytest.baseline.md). It is a hypothesis falsifying example using a
  column literally named "col" that shadows the col() helper in the FormulaEvaluator
  symbol table. It is outside the B1/B2 remediation scope (which covers
  source_selection_presenter.py, _schema_discovery_wiring.py, workbook_reader.py) and was
  failing before any cycle-3 change. The cycle-3 fix does not touch src/schema_formula.py
  or tests/test_schema_formula.py and does not change this result.
- EXIT_CODE is 1 solely because of this pre-existing, out-of-scope failure. All scope-
  relevant tests pass.
