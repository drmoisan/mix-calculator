# Phase 0 — Fixture Inventory

Timestamp: 2026-05-30T22-50

## tests/gui/conftest.py
- Purpose: GUI test harness configuration.
- Seams provided:
  - Sets `QT_QPA_PLATFORM=offscreen` at module-import time so all GUI tests run headless before any PySide6 import.
  - Session-scoped autouse fixture `force_offscreen_qt_platform` re-asserts the variable for every session.
- `qtbot` is supplied by the pytest-qt plugin (declared via `pytestqt.qtbot.QtBot` type hints throughout).

## tests/gui/test_pipeline_worker.py
- Purpose: Behavioral tests for `PipelineWorker` (`src/gui/workers/pipeline_worker.py`).
- Seams used:
  - `qtbot.waitSignal` to assert event-driven `finished` / `error` emissions.
  - `_SignalBlockerView` typed Protocol + `cast` to read `blocker.args` without a per-call suppression (pandas_io containment pattern).
- Existing tests: success-path finished emission, failure-path error emission, main-thread direct `run` invocations.
- Phase 1 (P1-T6) extends this file with traceback-logging and `BaseException` re-raise tests.

## tests/gui/test_runners.py
- Purpose: Unit tests for `RunnerProtocol` and its two implementations (`SynchronousRunner`, `ThreadedRunner`).
- Seams used: Pure Python (no QApplication required). Exercises `SynchronousRunner` exception routing and `isinstance(..., RunnerProtocol)` structural checks.
- Phase 3 work does not modify this file; the new pytest-qt `tests/gui/test_runners_threaded.py` is the queued-connection seam.

## tests/gui/test_app_composition.py
- Purpose: Composition-root smoke tests for `src/gui/app.py` (`build_application`, `main`).
- Seams used: `qtbot` for the managed QApplication, `monkeypatch` to override `QApplication.exec`, `velopack.App`, `resolve_icon_path`, and `QIcon`.
- Existing AC-10 ordering test pins `velopack.App().run()` to run before `QApplication` construction. Phase 1 (P1-T8) adds an `install_crash_handlers` ordering test that asserts the same pre-`QApplication` invariant for the new installer.
