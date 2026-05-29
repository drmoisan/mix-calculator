# Phase 5 QA Gate Evidence

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
Output Summary: Pass. 378 passed. Coverage TOTAL line 99%, branch 99%. Both thresholds satisfied. Tests updated to match v2 behavior: `tests/gui/test_export_dialog.py` (combo removed; new `set_table_list(["LE", "aop", "sku_lu"])` flow added); `tests/gui/test_app_wiring_defaults.py` (filter-string parse contract for Excel and CSV); `tests/gui/test_app_composition.py` (dropped `wired.export_dialog.available_formats()` assertion).
