# Final QC — Pytest with coverage

Timestamp: 2026-05-29T13-45

## Full suite
Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing -q`
EXIT_CODE: 0

Output Summary:
- 507 passed, 0 failed, 1 warning (pre-existing pandas FutureWarning on empty concat).
- Global post-change coverage: 2273 statements, 17 missed; 356 branches, 4 partial. Total: 99% line + branch.
- Baseline (P0-T7): 497 passed, total 99%.
- Net change: +10 tests added (8 new in `tests/test_mix_lookups_casefold.py`, 1 added to `tests/test_mix_pipeline.py`, 1 net new from re-grouping — total assertions per AC verification table below).

## Module-specific (src/mix_lookups.py)
Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src.mix_lookups --cov-branch --cov-report=term-missing tests/test_mix_lookups.py tests/test_mix_lookups_casefold.py`
EXIT_CODE: 0

Output Summary:
- `src/mix_lookups.py` post-change line coverage: 100% (58/58 statements).
- `src/mix_lookups.py` post-change branch coverage: 100% (4/4 branches, 0 partial).
- Baseline (P0-T6): 43 statements at 100% line, 4 branches at 100% branch.
- No regression on changed lines; all 15 new statements (helper + pivot rework) are 100% covered.
- Coverage thresholds satisfied: >= 85% line and >= 75% branch (AC8).
