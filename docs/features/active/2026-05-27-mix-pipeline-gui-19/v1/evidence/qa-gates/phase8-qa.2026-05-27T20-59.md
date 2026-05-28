# Phase 8 QA Gate

Phase 8 — PipelineWorker (QObject + QThread). Single clean pass of the toolchain loop.

## Black
Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 70 files left unchanged (after reformat restart).

## Ruff
Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors. The worker's broad `except Exception` is the
documented worker-thread failure boundary (logs + re-emits via the `error` signal); ruff's BLE rule
is not in the project's select list, so no suppression is needed.

## Pyright
Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any.

Risk [P8-T1] resolution — Pyright-strict Qt signal typing:
- A probe confirmed PySide6 6.11 stubs type `Signal` class attributes, `.emit()`, and `.connect()`
  cleanly under strict mode. The signals (`finished: Signal = Signal(dict)`, etc.) are therefore
  declared directly with NO broad suppression and NO strictness reduction. The spec risk did not
  materialize for the production signal declarations.
- The only loosely-typed surface was pytest-qt's `SignalBlocker.args` in the test; it is contained
  behind a typed Protocol view (`_SignalBlockerView`) plus `cast` — the same containment pattern used
  in `src/pandas_io.py` — rather than a per-call suppression.

## Pytest (coverage)
Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 256 passed (252 prior + 4 new), 0 failed. Determinism confirmed across 2 runs.
- `src/gui/workers/pipeline_worker.py`: 100% line, 100% branch.
- Repository TOTAL: 100% line, 100% branch. Gate satisfied.
- No regression on changed lines.

## Notes
- `quality-tiers.yml`: added `src/gui/workers/__init__.py: T4`, `src/gui/workers/pipeline_worker.py: T3`.
- Qt-thread tests (success + failure) use only event-driven `qtbot.waitSignal`. The banned timing APIs
  (`time.sleep`, `QThread.sleep`, `QTest.qWait`) do not appear in test code (verified by grep; the only
  match is the docstring stating they are absent).
- Two synchronous main-thread `run` tests provide deterministic coverage of the `run` body (coverage.py
  does not trace the QThread worker thread by default; the cross-thread tests verify behavior).
- Confidentiality: fabricated values only.
