# Phase 2 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass. 97 files would be left unchanged.

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
Output Summary: Pass. 355 passed (+17 vs end of Phase 1: 8 new in test_main_window.py + 9 new adapter routing tests in test_app_wiring.py). 20.17s. Coverage TOTAL line 99% (1845, 11 missed), branch 100%. Both thresholds satisfied. The 11 missed lines are confined to `src/gui/runners.py::ThreadedRunner.run` (covered by P7 wiring/composition tests) and one app.py branch reached only by the P5/P7 export flow.
