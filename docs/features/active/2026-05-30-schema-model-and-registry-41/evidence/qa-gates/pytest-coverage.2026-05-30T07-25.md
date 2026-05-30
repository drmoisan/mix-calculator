# QA Gate — Pytest with Coverage (Post-Change) (Issue #41)

Timestamp: 2026-05-30T07-25
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing --cov-report=xml:artifacts/python/coverage.xml`
EXIT_CODE: 0
Output Summary:
- Tests: 578 passed, 1 warning, 0 failed (510 baseline + 68 new schema tests).
- TOTAL coverage row: 2612 statements, 18 missed, 456 branches, 5 partial.
- Post-change line coverage: 99.31% (displayed TOTAL 99%).
- Post-change branch coverage: 98.90%.
- The existing test suite remains green (AC8); no pre-existing test failed.
- New-module coverage (from the full run):
  - src/schema_model.py: 100% line, 100% branch
  - src/schema_serialization.py: 100% line, 100% branch
  - src/_schema_json_helpers.py: 98% line, 98% branch (1 defensive guard line, 160)
  - src/schema_registry.py: 100% line, 100% branch
  - src/schema_settings.py: 100% line, 100% branch
- Note: the typed JSON accessors were extracted from src/schema_serialization.py
  into src/_schema_json_helpers.py during final QC to keep every file under the
  500-line limit; the helper module is classified T2 in quality-tiers.yml.
- Raw XML coverage written to artifacts/python/coverage.xml (non-evidence tool output).
