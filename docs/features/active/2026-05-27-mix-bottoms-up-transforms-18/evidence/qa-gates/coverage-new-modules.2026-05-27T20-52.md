# QA Gate — New-Module Coverage (Interim, end of Phase 2)

Timestamp: 2026-05-27T20-52
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

## New-module coverage (T2 thresholds: line >= 85%, branch >= 75%)

| Module | Stmts | Miss | Branch | BrPart | Line % | Branch % |
|---|---|---|---|---|---|---|
| `src/_mix_bottomsup_helpers.py` | 39 | 0 | 2 | 0 | 100% | 100% |
| `src/mix_bottomsup.py` | 57 | 0 | 2 | 0 | 100% | 100% |

Output Summary: 204 tests passed. Both new modules at 100% line and 100% branch
coverage, comfortably above the T2 thresholds (>= 85% line, >= 75% branch). Overall
suite line coverage 100% (977 statements, 0 missed); overall branch coverage 100%
(196 branches, 0 partial). No targeted-test top-up required.
