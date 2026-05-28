# Pytest Final QA (coverage on)

Timestamp: 2026-05-27T22-40

Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- Total tests collected: 220
- Passed: 220
- Failed: 0
- Skipped: 0
- Deselected: 0
- Per-module post-split counts for the affected modules:
  - `tests/test_mix_rollups.py`: 8 tests (passed)
  - `tests/test_mix_rollups_tieout.py`: 3 tests (passed)
  - Combined: 11 — matches the pre-split baseline of 11 in `tests/test_mix_rollups.py`.
- TOTAL coverage: line 100%, branch 100% (Stmts 1085 / Miss 0 / Branch 206 / BrPart 0)
- Per-file coverage for the three issue-#20 production files:
  - `src/mix_rollups.py`: line 100%, branch 100%
  - `src/_mix_rollups_helpers.py`: line 100%, branch 100%
  - `src/mix_pipeline_run.py`: line 100%, branch 100%
- Wall time: 18.27s
- Result: PASS.
