# Phase 1 QA Gate Evidence

## Black

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: Pass. 96 files would be left unchanged (added `src/gui/runners.py` and `tests/gui/test_runners.py`).

## Ruff

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: Pass. All checks passed. 0 errors.

## Pyright

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict mode).

## Pytest with coverage

Timestamp: 2026-05-28T22-10
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: Pass. 338 passed (+5 vs baseline 333) in 20.28s. Coverage TOTAL line 99% (1845 statements, 23 missed), branch 100% (268 branches, 0 partial). Both thresholds (line >= 85%, branch >= 75%) satisfied. Per-file coverage: `src/gui/runners.py` 66% (ThreadedRunner.run not covered by P1-T3 unit tests as planned; will be covered by P7 wiring tests and P9 behavioral tests). `src/gui/app.py` 88% (new `MainWindowPipelineView.set_*_button_enabled` methods not covered until P2-T4).

## Notes

Phase 1 work also includes the P2-T1 button-rename and P2-T2 `MainWindowPipelineView` extensions: adding the four new methods to `PipelineViewProtocol` makes any structural implementor (including `MainWindowPipelineView` consumed by `PipelinePresenter`) need them, so the protocol extension cannot pass strict Pyright in isolation. P2-T1 (button promotion) and P2-T2 (adapter routing) were therefore completed alongside P1-T1..T3 to keep the gate green; the P2 task checkboxes are flipped under Phase 2.
