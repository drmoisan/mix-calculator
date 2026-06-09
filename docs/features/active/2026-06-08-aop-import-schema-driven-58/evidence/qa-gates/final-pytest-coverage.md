# Final QA — Pytest + Coverage

Timestamp: 2026-06-08T14-30
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 998 passed, 0 failed, 3 warnings in ~35.5s (baseline was 987; +11 net new tests).
- TOTAL combined coverage: 98%.
- Statements: 4793 total, 44 missed -> line coverage = (4793-44)/4793 = 99.08%.
- Branches: 894 total, 54 partial -> branch coverage = (894-54)/894 = 93.96%.
- Changed/new production modules:
  - src/schema_loader.py: 32 stmts, 0 missed, 6 branch, 0 partial -> 100% line & branch.
  - src/gui/pipeline_service.py: 76 stmts, 0 missed, 0 partial -> 100%.
  - src/gui/_aop_schema_import.py (new): 17 stmts, 0 missed, 0 partial -> 100%.
  - src/schemas/default_aop.schema.json: data-only edit (not executable; covered by schema parse/round-trip and parity tests).

Thresholds met: line 99.08% >= 85%, branch 93.96% >= 75%. No regression on changed lines (all changed/new modules at 100%).
