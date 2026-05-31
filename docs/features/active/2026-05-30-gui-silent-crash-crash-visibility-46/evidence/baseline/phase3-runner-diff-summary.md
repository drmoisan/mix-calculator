# Phase 3 — Runner Diff Summary

Timestamp: 2026-05-30T23-17

Source: `src/gui/runners.py`

Symbols changed from baseline:

| Symbol | Status | Notes |
|---|---|---|
| `RunnerProtocol` | unchanged | Public Protocol surface preserved. |
| `SynchronousRunner` | unchanged | Test seam preserved. |
| `ThreadedRunner.__init__` | modified | Added `self._receiver: _RunnerReceiver | None = None` (private attribute holding the GUI-thread QObject receiver). |
| `ThreadedRunner.run` | modified | Constructs a `_RunnerReceiver` on the GUI thread; connects `worker.finished` / `worker.error` to its slots with `Qt.ConnectionType.QueuedConnection` instead of plain Python closures. `worker.finished.connect(thread.quit)` / `worker.error.connect(thread.quit)` semantics preserved (QThread.quit is thread-safe). |
| `_RunnerReceiver` | NEW | Private QObject subclass with two `@Slot` methods (`dispatch_success`, `dispatch_error`) that invoke the user-supplied callbacks. Holds GUI-thread affinity by construction (no `moveToThread`). Documents the thread-affinity invariant in its class docstring. |
| Imports | modified | Added `Qt`, `QObject`, `Slot` from `PySide6.QtCore`. Removed nothing. |

Line count: 223 (baseline 156, +67 lines for the new class, queued-connection wiring, and Google-style class/method docstrings; well under the 500-line cap).

AC coverage: AC-6 (cross-thread Qt mutation eliminated) and AC-12 (file-size cap).
