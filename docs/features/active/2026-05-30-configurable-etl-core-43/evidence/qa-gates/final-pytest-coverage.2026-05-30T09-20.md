# Final QA Gate — Pytest + Coverage (Issue #43)

Timestamp: 2026-05-30T09-20
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- 669 passed, 0 failed, 1 warning, in 31.87s.
- Baseline suite was 604 passed; this feature adds 65 tests (formula engine,
  loader core, derived/drop/output, LE parity, AOP parity, integration).
- Existing suite remains green (AC11): all pre-existing tests pass; no existing
  loader/transform/CLI/GUI behavior changed.
- Post-change TOTAL: 3026 statements, 30 missed; 618 branches, 22 partial.
- Post-change total line coverage: 99.01%.
- Post-change total branch coverage: 96.44%.

Per-new-module coverage (from the feature-scoped run):
- src/schema_formula.py: line 100% (52 stmts), branch 100% (20 branches).
- src/schema_loader.py: line 100% (31 stmts), branch 100% (6 branches).
- src/_schema_formula_helpers.py: line 95% (59 stmts, 3 missed), branch 89% (28 branches, 3 partial).
- src/_schema_loader_helpers.py: line 96% (116 stmts, 5 missed), branch 84% (50 branches, 8 partial).
All four new modules meet >= 85% line and >= 75% branch.
