# Phase 7 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass. 99 files left unchanged (added `src/gui/_wiring.py`).

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
Output Summary: Pass. 390 passed (+7 vs Phase 6). Coverage TOTAL line 99%, branch 99%. Both thresholds satisfied. Notes: per the plan's P7-T1 escape hatch, `src/gui/app.py` was kept under the 500-line cap (492 lines) by splitting `default_save_chooser`/`default_open_chooser`/`default_export_runner` into a new private module `src/gui/_wiring.py` (96 lines). The chooser tests reference the choosers' filter-string parse contract via `_wiring.QFileDialog`; the constants `_SQLITE_FILTER` and `_EXPORT_FILTER` moved with the choosers. A new `PreviewSinkProtocol` was added so `PreviewWidget` (which only implements `show_preview`) satisfies the `preview_sink` parameter type without inheriting the wider `SourceSelectionViewProtocol`.
