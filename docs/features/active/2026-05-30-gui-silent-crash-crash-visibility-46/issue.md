# gui-silent-crash-crash-visibility (Issue #46)

- Date captured: 2026-05-30
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/gui-silent-crash-crash-visibility/ (Issue #46)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #46
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/46
- Last Updated: 2026-05-31
- Work Mode: full-bug

## Summary

The PySide6 GUI exits silently with no traceback, dialog, or crash dump when the user invokes Import on the SKU_LU tab. The process terminates from inside the worker thread without surfacing any signal to the UI or to disk.

## Environment

- OS/version: Windows 11 (developer workstation)
- Python version: per `pyproject.toml` (>= 3.12); reproduced on 3.13 (same as CI)
- Command/flags used: `poetry run python -m src.gui.app` (or the Velopack-built `mix-calculator.exe`)
- Data source or fixture: real `.xlsx` workbook containing a SKU_LU sheet (file not preserved by the user; behavior is reproducible by clicking Import on the SKU_LU tab against the workbook in question)

## Steps to Reproduce

1. Launch the GUI.
2. Select a source workbook in the source input widget.
3. Switch to the SKU_LU tab.
4. Click the Import button.
5. Observe: the process disappears with no error dialog, no stderr output, and no file on disk recording the cause.

## Expected Behavior

A catastrophic failure (whether a native fault or an unhandled Python exception in a worker) must:

- Write a full traceback / fault report to a persistent log file under a known per-user location.
- Surface a non-fatal error dialog on the GUI thread when the failure originated in a worker and the event loop is still alive.
- Exit with a non-zero exit code rather than vanish.
- Never mutate Qt widgets from a non-GUI thread (a structural cause of native aborts that bypass Python exception handling).

## Actual Behavior

The process exits silently. No traceback is printed because `sys.excepthook` is not overridden, `faulthandler` is not enabled, and no log handler writes to disk. The Qt event loop and the Python interpreter both terminate before any signal can be raised back to the UI.

## Logs / Screenshots

- [x] Attached minimal logs or screenshot — research artifact records the full call path and the absence of crash-visibility infrastructure.
- Snippet (paraphrased from research): no `sys.excepthook`, no `threading.excepthook`, no `faulthandler.enable()`, no `qInstallMessageHandler`, no log file; `logging.basicConfig(level=WARNING)` writes only to `stderr`, which is invisible in a windowed GUI.

## Impact / Severity

- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

User cannot complete the SKU_LU import workflow and cannot self-diagnose because no record of the failure exists.

## Suspected Cause / Notes

Per `artifacts/research/skulu-gui-crash-diagnosis.md`, two structural causes combine:

1. **Cross-thread Qt widget mutation (confirmed policy violation).** [src/gui/runners.py:136-141](src/gui/runners.py#L136-L141) connects `worker.finished` and `worker.error` to plain Python closures. PySide6 falls back to a direct connection in that case, so the success/error callbacks run on the worker thread. Those callbacks then call `setEnabled` and `showMessage` on live Qt widgets, which is a documented native-abort vector that bypasses Python exception handling.
2. **Native fault path through openpyxl / lxml.** [src/load_skulu.py:86](src/load_skulu.py#L86) calls `pandas.read_excel(engine="openpyxl")` via the [src/pandas_io.py:111](src/pandas_io.py#L111) adapter. A malformed `.xlsx` can SIGSEGV inside the C extensions, which Python never sees as an exception.

In both cases the absence of a crash handler (no `faulthandler`, no `sys.excepthook`, no `threading.excepthook`, no Qt message handler, no log file) means the user observes a silent disappearance.

## Proposed Fix / Validation Ideas

Structural fixes (small file footprint; user has selected the large audit path for stability):

- Fix cross-thread callback wiring in [src/gui/runners.py](src/gui/runners.py): route `finished` / `error` through a `QObject` trampoline on the GUI thread, or use `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`.
- Add a new `src/gui/_crash_handler.py` module that installs:
  - `faulthandler.enable(file=<rotating-crash-log>)` at startup, plus `faulthandler.register` for the abort signals available on Windows.
  - `sys.excepthook` writing a full Python traceback to the same log directory and surfacing a `QMessageBox` when a GUI thread is alive.
  - `threading.excepthook` so worker-thread exceptions are captured.
  - `qInstallMessageHandler` routing Qt warnings/criticals/fatals through Python `logging`.
  - A log-file location resolver (Windows: `%LOCALAPPDATA%\mix-calculator\logs\`; falling back to a deterministic per-user path on other platforms).
- Widen the `except Exception` clause in [src/gui/workers/pipeline_worker.py:99](src/gui/workers/pipeline_worker.py#L99) and add `exc_info=True` so caught exceptions include a traceback.
- Validation:
  - Unit tests (pytest) for the crash-handler installation (idempotent install, log-file path resolution, excepthook chaining behavior).
  - Unit tests for the corrected runner wiring asserting that callbacks are dispatched via a queued connection / posted to the GUI thread.
  - Integration / behavioral test that injects a worker-thread exception and asserts a log file is written and the error signal reaches the GUI thread.

## Next Step

- [x] Promote to GitHub issue (bug-report template)
- [ ] Move to active fix folder / branch