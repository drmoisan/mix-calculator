# Phase 4 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass. 98 files left unchanged.

## Ruff

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: Pass. All checks passed.

## Pyright

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations.

## Pytest with coverage

Timestamp: 2026-05-28T22-10
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: Pass. 377 passed (+14 vs Phase 3; tests added to `test_pipeline_presenter_v2.py` covering file-path tracking, working_tables, derived-table invalidation, button-state pushes, the open-db sentinel, and on_run_success/on_run_error). 20.69s. Coverage TOTAL line 99%, branch 99%. Both thresholds satisfied. Note: P4 added a sibling test file `tests/gui/test_pipeline_presenter_v2.py` so the original `tests/gui/test_pipeline_presenter.py` would remain under the 500-line cap; plan permits this split.
