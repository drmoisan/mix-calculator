# Final QA — Pytest + Coverage

Timestamp: 2026-05-25T21-02
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing` (run as `env -u VIRTUAL_ENV poetry run pytest ...` per VIRTUAL_ENV quirk)
EXIT_CODE: 0
Output Summary:
- Tests: 46 passed, 0 failed (44 in the normalize-le suite across `test_normalize_le.py` and `test_normalize_le_io.py`; 2 pre-existing calculator tests).
- `src/normalize_le.py` coverage: 100% line (129 stmts, 0 missed), 100% branch (36 branches, 0 partial).
- Repository TOTAL: 100% line, 100% branch (133 stmts, 38 branches).
- Thresholds satisfied: line >= 85% and branch >= 75% (both 100%).
- Full toolchain completed a single clean pass: Black -> Ruff -> Pyright -> Pytest with no file changes or failures.
