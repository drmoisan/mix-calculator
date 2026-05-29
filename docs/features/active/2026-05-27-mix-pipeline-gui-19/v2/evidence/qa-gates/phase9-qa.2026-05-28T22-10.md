# Phase 9 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass.

## Ruff

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: Pass.

## Pyright

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations.

## Pytest with coverage

Timestamp: 2026-05-28T22-10
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: Pass. 416 passed (+11 vs Phase 8: 2 AC-6 pipeline-run tests, 7 AC-7/8/9 dialogs tests, 2 AC-10 composition tests). Coverage TOTAL line 99%, branch 99%. Both thresholds satisfied. Notes: added `set_imported_tables_for_test` test seam to `PipelinePresenter` so behavioral tests can pre-populate the working-table set without going through the import pipeline (the equivalent of v1 tests calling `on_import_all` for state setup).
