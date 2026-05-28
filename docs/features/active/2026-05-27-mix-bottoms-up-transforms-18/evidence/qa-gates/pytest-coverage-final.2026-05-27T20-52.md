# Final QA Gate — Pytest + Coverage

Timestamp: 2026-05-27T20-52
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

## Result

- Tests: 204 passed (up from the 185-test baseline; 19 new tests added).
- Overall line coverage: 100% (981 statements, 0 missed).
- Overall branch coverage: 100% (196 branches, 0 partial).

## Per-module coverage for the new modules (T2: line >= 85%, branch >= 75%)

| Module | Stmts | Miss | Branch | BrPart | Line % | Branch % |
|---|---|---|---|---|---|---|
| `src/_mix_bottomsup_helpers.py` | 39 | 0 | 2 | 0 | 100% | 100% |
| `src/mix_bottomsup.py` | 57 | 0 | 2 | 0 | 100% | 100% |
| `src/mix_pipeline_run.py` (changed) | 24 | 0 | 0 | 0 | 100% | 100% |

Output Summary: All 204 tests pass. Overall and per-new-module coverage are 100% line
and 100% branch, above the T2 thresholds. No coverage regression on changed lines.
