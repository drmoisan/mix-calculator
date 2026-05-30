# Final QA — New-module coverage (AC7)

Timestamp: 2026-05-30T07-59
Command: `poetry run pytest --cov=src.etl_column_probe --cov=src.schema_matching --cov=src._schema_matching_helpers --cov-branch --cov-report=term-missing`
EXIT_CODE: 0

Output Summary:
- Tests: 604 passed, 0 failed.
- Per-module coverage for the new feature modules:

| Module | Stmts | Miss | Branch | BrPart | Line cov | Branch cov |
|---|---|---|---|---|---|---|
| `src/etl_column_probe.py` | 45 | 0 | 20 | 0 | 100% | 100% |
| `src/schema_matching.py` | 92 | 2 | 28 | 4 | 95% | ~86% (24/28) |
| `src/_schema_matching_helpers.py` | 19 | 2 | 10 | 2 | 86% | 80% (8/10) |
| TOTAL (new code) | 156 | 4 | 58 | 6 | 95% | ~90% |

- Threshold check (AC7: >= 85% line, >= 75% branch):
  - `src/etl_column_probe.py`: line 100% >= 85% PASS; branch 100% >= 75% PASS.
  - `src/schema_matching.py`: line 95% >= 85% PASS; branch ~86% >= 75% PASS.
  - `src/_schema_matching_helpers.py`: line 86% >= 85% PASS; branch 80% >= 75% PASS.
- All three new modules meet both the line and branch thresholds.
- A `hypothesis` property test (`tests/test_schema_matching_property.py`) covers
  scoring determinism, satisfying the T2 property-test requirement of AC7.
