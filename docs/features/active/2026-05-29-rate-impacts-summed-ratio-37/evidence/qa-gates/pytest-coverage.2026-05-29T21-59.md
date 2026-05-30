# Final QC — Pytest + Coverage (Issue #37)

Timestamp: 2026-05-29T21-59
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 510 passed, 0 failed, 1 warning in 22.41s (baseline was 507; +3 new regression/reconciliation/behavior tests). All 7 tests in tests/test_mix_rate_impacts.py pass.
- Total line coverage: 99% (TOTAL 2295 statements, 17 missed).
- Total branch coverage: 356 branches, 4 partial -> ~98.9% branch.
- Per-module src/mix_rate_impacts.py: 43 statements, 0 missed, 0 branches, 0 partial, 100% line coverage.
