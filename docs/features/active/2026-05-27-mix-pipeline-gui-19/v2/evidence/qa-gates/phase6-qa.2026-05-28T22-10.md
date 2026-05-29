# Phase 6 QA Gate Evidence

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
Output Summary: Pass. 383 passed. Coverage TOTAL line 99%, branch 99%. Tests updated to match v2 behavior: `tests/gui/test_csv_exporter.py` rewritten for the `<base>_<table>.csv` name-mangling rule (Decision 1); `tests/gui/test_gui_integration.py` updated to call the exporter with a CSV file path instead of a directory and to assert the mangled `results_mix_rollup_4.csv` filename.
