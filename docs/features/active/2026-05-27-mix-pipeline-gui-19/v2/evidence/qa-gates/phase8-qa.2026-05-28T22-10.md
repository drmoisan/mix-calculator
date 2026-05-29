# Phase 8 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass.

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
Output Summary: Pass. 405 passed (+15 vs Phase 7: 5 AC-1 preview tests in `tests/gui/integration/test_behavioral_preview.py` plus 10 AC-2..AC-5 import-button tests in `test_behavioral_import_buttons.py`). Coverage TOTAL line 99%, branch 99%. Both thresholds satisfied. Notes: the integration tests use a typed `_click` helper that invokes `QPushButton.click()` directly because `qtbot.mouseClick` loses argument types under Pyright strict; the SynchronousRunner makes either approach behaviorally equivalent for the deterministic flow.
