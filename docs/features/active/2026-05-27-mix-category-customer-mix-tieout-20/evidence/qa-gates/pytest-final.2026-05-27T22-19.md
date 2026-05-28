# Pytest + Coverage Final Gate (Issue #20, AC5/AC6)

Timestamp: 2026-05-27T22-19

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- Tests: 201 passed, 0 failed (baseline was 199; +3 new behavioral tests, -1 removed `unstack_to_long` test).
- Overall line coverage: 100% (985 statements, 0 missed).
- Overall branch coverage: 100% (202 branches, 0 partial).
- Per-module post-change coverage for in-scope files:
  - `src/mix_rollups.py`: 59 statements, 0 missed, 0 branch, 0 partial — 100% line / 100% branch.
  - `src/_mix_rollups_helpers.py`: 30 statements, 0 missed, 0 branch, 0 partial — 100% line / 100% branch.
  - `src/mix_pipeline_run.py`: 22 statements, 0 missed, 0 branch — 100% line.
- The full loop (Black -> Ruff -> Pyright -> Pytest) completed in a single clean pass; no stage changed files, so no restart was required.
