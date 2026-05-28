# Pytest + Coverage Baseline (Issue #20)

Timestamp: 2026-05-27T22-07

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- Tests: 199 passed, 0 failed.
- Overall line coverage: 100% (1006 statements, 0 missed).
- Overall branch coverage: 100% (210 branches, 0 partial).
- Per-module baseline coverage for in-scope files:
  - `src/mix_rollups.py`: 61 statements, 0 missed, 0 branch, 0 partial — 100% line / 100% branch.
  - `src/_mix_rollups_helpers.py`: 49 statements, 0 missed, 8 branch, 0 partial — 100% line / 100% branch.
  - `src/mix_pipeline_run.py` (also in production-file budget): 22 statements, 0 missed, 0 branch — 100% line / n/a branch.
