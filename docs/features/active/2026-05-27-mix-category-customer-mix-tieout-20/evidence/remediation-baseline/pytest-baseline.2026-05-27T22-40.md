# Pytest Baseline (Pre-Remediation, coverage on)

Timestamp: 2026-05-27T22-40

Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- Total tests collected: 220
- Passed: 220
- Failed: 0
- Skipped: 0
- `tests/test_mix_rollups.py` test count: 11 (matches the cohesive-split inventory in the plan)
- TOTAL coverage: line 100%, branch 100% (Stmts 1085 / Miss 0 / Branch 206 / BrPart 0)
- Per-file coverage for the three issue-#20 production files:
  - `src/mix_rollups.py`: line 100%, branch 100% (59 stmts, 0 branches)
  - `src/_mix_rollups_helpers.py`: line 100%, branch 100% (30 stmts, 0 branches)
  - `src/mix_pipeline_run.py`: line 100%, branch 100% (26 stmts, 0 branches)
- Wall time: 22.68s
- Result: PASS.
