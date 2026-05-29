# Phase 1 QA — Toolchain Loop

## Black

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run black .`
EXIT_CODE: 0
Output Summary: 105 files left unchanged. (Ran twice in this phase; second run after fixing the E501 ruff finding on the new test docstring was a clean pass.)

## Ruff

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. The first attempt flagged one E501 (line-length) on the new test docstring; resolved by shortening the docstring text, and the toolchain was restarted from Black. Second pass clean.

## Pyright

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. No new suppressions added.

## Pytest with coverage

Timestamp: 2026-05-28T23-20
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 417 passed in 20.63s; 0 failed. (Baseline was 416 passed; this phase added one new positive test `test_build_application_uses_injected_exporter_registry`.)
- Line coverage (TOTAL): 99% (1956 statements, 14 missed).
- Branch coverage (TOTAL): 99% (296 branches, 2 partial).
- `src/gui/app.py`: 100% line / 100% branch (the new `exporter_registry` branch is exercised by the new test).
- Line count check: `src/gui/app.py` is 500 lines (at the cap); `tests/gui/test_app_wiring.py` is 492 lines.
- `git status` after the pytest run still shows three untracked `results_*.csv` at the repo root; this is the R-1 leak that will be remediated by Phase 3 (the CSV behavioral test was not modified in Phase 1).

## Confidentiality

No real customer/SKU/Category values introduced. New test uses `lambda _path: StringIO()` only.
