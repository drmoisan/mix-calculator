# gui-silent-crash-crash-visibility (Spec)

- **Issue:** #46
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-31T02-43
- **Status:** Implemented (pending review)
- **Version:** 1.0

## Context
The PySide6 GUI exits silently with no traceback, dialog, or crash dump when the user invokes Import on the SKU_LU tab. The process terminates from inside the worker thread without surfacing any signal to the UI or to disk.

Environment:
- OS/version: Windows 11 (developer workstation)
- Python version: per `pyproject.toml` (>= 3.12); reproduced on 3.13 (same as CI)
- Command/flags used: `poetry run python -m src.gui.app` (or the Velopack-built `mix-calculator.exe`)
- Data source or fixture: real `.xlsx` workbook containing a SKU_LU sheet (file not preserved by the user; behavior is reproducible by clicking Import on the SKU_LU tab against the workbook in question)

Impact / Severity:
- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

User cannot complete the SKU_LU import workflow and cannot self-diagnose because no record of the failure exists.


## Repro & Evidence
Steps to Reproduce:
1. Launch the GUI.
2. Select a source workbook in the source input widget.
3. Switch to the SKU_LU tab.
4. Click the Import button.
5. Observe: the process disappears with no error dialog, no stderr output, and no file on disk recording the cause.

Expected:
A catastrophic failure (whether a native fault or an unhandled Python exception in a worker) must:

- Write a full traceback / fault report to a persistent log file under a known per-user location.
- Surface a non-fatal error dialog on the GUI thread when the failure originated in a worker and the event loop is still alive.
- Exit with a non-zero exit code rather than vanish.
- Never mutate Qt widgets from a non-GUI thread (a structural cause of native aborts that bypass Python exception handling).

Actual:
The process exits silently. No traceback is printed because `sys.excepthook` is not overridden, `faulthandler` is not enabled, and no log handler writes to disk. The Qt event loop and the Python interpreter both terminate before any signal can be raised back to the UI.

Logs / Screenshots:
- [x] Attached minimal logs or screenshot — research artifact records the full call path and the absence of crash-visibility infrastructure.
- Snippet (paraphrased from research): no `sys.excepthook`, no `threading.excepthook`, no `faulthandler.enable()`, no `qInstallMessageHandler`, no log file; `logging.basicConfig(level=WARNING)` writes only to `stderr`, which is invisible in a windowed GUI.


## Scope & Non-Goals
- In scope:
  - A new module `src/gui/_crash_handler.py` (T3-Adapters tier classification, matching `src/gui/app.py`'s neighborhood) that installs the four crash hooks (`faulthandler`, `sys.excepthook`, `threading.excepthook`, `qInstallMessageHandler`) and resolves a per-user log directory.
  - Wiring the new crash-handler installer into the GUI composition root at [src/gui/app.py](src/gui/app.py) so the hooks are live before any worker or widget is created.
  - Fixing the cross-thread Qt widget mutation in [src/gui/runners.py](src/gui/runners.py) by routing the `finished` / `error` notifications through a `QObject` receiver bound to the GUI thread with `Qt.ConnectionType.QueuedConnection`.
  - Adding `exc_info=True` to the worker boundary log call at [src/gui/workers/pipeline_worker.py:99](src/gui/workers/pipeline_worker.py#L99) and widening it to `except BaseException` re-raising `KeyboardInterrupt` / `SystemExit`, so caught exceptions retain a traceback in the log.
  - Pytest unit tests for the four installers (idempotency, log-path resolution, excepthook chaining), the corrected runner wiring (queued-connection routing), and the wider worker boundary.
  - One pytest-qt behavioral test that injects a worker-thread exception and asserts (a) the error signal reaches the GUI thread and (b) a log file is written under the resolved log directory.
- Out of goals / non-goals:
  - No change to the loader logic in [src/load_skulu.py](src/load_skulu.py), the workbook reader, or the pipeline service. The root cause is structural (crash visibility + thread affinity), not algorithmic.
  - No change to the SKU_LU sheet's data interpretation, dedup logic, or schema-discovery path.
  - No new external dependencies. `faulthandler`, `sys`, `threading`, `logging`, and `PySide6` are all already in the runtime closure.
  - No GUI cosmetic changes beyond the new `QMessageBox` shown on a captured worker-thread or main-thread exception.
- Explicitly excluded systems, integrations, or datasets:
  - The Velopack bootstrap and installer paths ([src/gui/_velopack_bootstrap.py](src/gui/_velopack_bootstrap.py)) are not modified. The crash-handler installer must be safe to call inside both the dev-launched and packaged process, but no Velopack-specific behavior is introduced.
  - No telemetry upload. The crash log is local-only.

## Root Cause Analysis
Per `artifacts/research/skulu-gui-crash-diagnosis.md`, two structural causes combine:

1. **Cross-thread Qt widget mutation (confirmed policy violation).** [src/gui/runners.py:136-141](src/gui/runners.py#L136-L141) connects `worker.finished` and `worker.error` to plain Python closures. PySide6 falls back to a direct connection in that case, so the success/error callbacks run on the worker thread. Those callbacks then call `setEnabled` and `showMessage` on live Qt widgets, which is a documented native-abort vector that bypasses Python exception handling.
2. **Native fault path through openpyxl / lxml.** [src/load_skulu.py:86](src/load_skulu.py#L86) calls `pandas.read_excel(engine="openpyxl")` via the [src/pandas_io.py:111](src/pandas_io.py#L111) adapter. A malformed `.xlsx` can SIGSEGV inside the C extensions, which Python never sees as an exception.

In both cases the absence of a crash handler (no `faulthandler`, no `sys.excepthook`, no `threading.excepthook`, no Qt message handler, no log file) means the user observes a silent disappearance.


## Proposed Fix

### Design summary (what changes where):
A new `src/gui/_crash_handler.py` module owns the four crash hooks and the log-path resolver. The GUI composition root in `src/gui/app.py` calls `install_crash_handlers(...)` exactly once, as early as possible (before `QApplication`-touching code, before workers, before any widget). The runner in `src/gui/runners.py` is changed so worker `finished` / `error` signals reach the GUI thread via a `QObject` receiver with `Qt.ConnectionType.QueuedConnection`. The worker boundary in `src/gui/workers/pipeline_worker.py` is widened to `except BaseException` (re-raising `KeyboardInterrupt` and `SystemExit`) and the `logger.error` call gains `exc_info=True`.

### Boundaries and invariants to preserve:
- Domain transforms and the loader (`load_skulu`, `pandas_io`) remain unchanged. The fix is structural, not algorithmic.
- The MVP passive-view structure of the GUI (presenters do not import Qt; widgets implement protocols) is preserved.
- The `RunnerProtocol` contract used by AC-6 of issue #19 is preserved. The threaded runner's externally observable behavior (a single `finished` or `error` callback per task) is unchanged.
- No new third-party dependency is introduced.
- The crash-handler installer is idempotent and safe to call from a single process.

### Dependencies or blocked work:
- None. The fix builds on stdlib (`faulthandler`, `sys`, `threading`, `logging`, `pathlib`, `tempfile`, `platform`) and `PySide6` (`QtCore.qInstallMessageHandler`, `QtCore.QObject`, `QtCore.Qt`, `QtCore.QMetaObject`, `QtWidgets.QMessageBox`), all already in the runtime closure.

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- `src/gui/_crash_handler.py` — NEW. Installer + log-path resolver + Qt message-handler adapter.
- `src/gui/app.py` — call `install_crash_handlers(...)` at the start of the entry point.
- `src/gui/runners.py` — replace direct-connection closures with a `QObject` receiver + queued connections, OR `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection`, so callbacks execute on the GUI thread.
- `src/gui/workers/pipeline_worker.py` — widen exception handling to `except BaseException` (re-raising `KeyboardInterrupt` / `SystemExit`), pass `exc_info=True` to `logger.error`.

#### Functions/classes/CLI commands impacted:
- New: `install_crash_handlers(*, app_name: str, log_dir: Path | None = None) -> CrashHandlerInstallation` and a small `CrashHandlerInstallation` value object recording what was installed and where logs go.
- New: `resolve_log_dir(app_name: str, platform_system: str, env: Mapping[str, str]) -> Path` (pure, testable).
- Modified: `ThreadedRunner.run` (or its helper) in `src/gui/runners.py` to dispatch callbacks via a queued connection.
- Modified: `PipelineWorker.run` in `src/gui/workers/pipeline_worker.py`.

#### Data flow and validation changes:
- None to business data. The new flow is: native fault or Python exception → captured by hook → traceback written to `<log_dir>/crash-<pid>-<utc-ts>.log` → optional `QMessageBox` shown on GUI thread → process exits with code 1 (Python excepthook path only; native faults still abort but with a recorded traceback).

#### Error handling and logging updates:
- New rotating log file in a per-user directory.
- New Qt message handler converts Qt categories to Python `logging` levels (`debug` → DEBUG, `info` → INFO, `warning` → WARNING, `critical` → ERROR, `fatal` → CRITICAL).
- `logger.error(..., exc_info=True)` at the worker boundary so even caught Python exceptions are logged with a traceback.

#### Rollback/feature-flag considerations (if applicable):
- A keyword argument `install_crash_handlers(..., enable: bool = True)` lets a future regression be disabled without code surgery. Not exposed to end users.

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
- `install_crash_handlers` returns a `CrashHandlerInstallation` dataclass exposing `log_dir: Path`, `crash_log_path: Path`, and `installed_hooks: tuple[str, ...]` for assertion in tests.
- Crash log records: ISO-8601 UTC timestamp, hook source (`faulthandler` / `sys.excepthook` / `threading.excepthook` / `qt.<category>`), thread name, full traceback.

#### Required configuration keys and defaults:
- App-name constant: `"mix-calculator"`.
- Default log directory resolution: Windows -> `%LOCALAPPDATA%\mix-calculator\logs\`; macOS -> `~/Library/Logs/mix-calculator/`; Linux -> `${XDG_STATE_HOME:-~/.local/state}/mix-calculator/logs/`. Tests inject the directory directly.

#### Backward-compatibility expectations:
- No public-API change in `pipeline_worker.py` or `runners.py` beyond a connection-type change. Existing tests that simulate runners synchronously (`SynchronousRunner`) keep their existing seam.

#### Performance constraints (latency/throughput/memory):
- Hook installation is one-time at startup, O(1).
- Queued-connection callback dispatch adds a single event-loop hop per pipeline task completion; negligible compared with the workbook-load duration.

## Assumptions, Constraints, Dependencies
- Assumptions (environment, data, access):
  - The pytest-qt fixture (`qtbot`) is available in the test environment (already in the dev dependency tree; the CI runner installs the system libraries per the orchestrator memory entry `pyside6-ci-system-libs`).
  - The CI runner already exports `QT_QPA_PLATFORM=offscreen` for pytest-qt collection; no new env config required.
- Constraints (budget, performance, compatibility):
  - File-size cap: every modified or added production file must stay under 500 lines.
  - No new dependency: stdlib + already-present PySide6 only.
  - Compatibility: the existing `RunnerProtocol` contract and `SynchronousRunner` test seam are preserved.
- External dependencies (services, libraries, releases):
  - None added.

## Data / API / Config Impact
- User-facing or API changes:
  - A new on-disk artifact: a crash log file under the per-user log directory. No CLI flag changes.
  - A new `QMessageBox` dialog appears on captured worker-thread exceptions; no other UI surface changes.
- Data or migration considerations:
  - None.
- Logging/telemetry updates (if any):
  - New rotating crash-log file. New Qt-message-handler routing through Python `logging`. No external telemetry.
- Compatibility notes (CLI flags, config schemas, versioning):
  - None. The crash handler is enabled by default and not surfaced via configuration.

## Test Strategy
Seeded from issue:

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

- Regression tests to add or update:
  - `tests/gui/test_crash_handler.py` (new) — covers AC-1 through AC-4 and AC-7 with the pure `resolve_log_dir` paths, the installer return-value contract, idempotency, and the Qt message-handler routing.
  - `tests/gui/test_runners_threaded.py` (new or augmented) — covers AC-6 by asserting the worker-signal connection type is `Qt.ConnectionType.QueuedConnection` and that callbacks reach the GUI thread.
  - `tests/gui/test_pipeline_worker.py` (existing; extended) — covers AC-5 by injecting an exception inside `PipelineWorker.run` and asserting the traceback is logged (`exc_info=True`) and the error signal fires.
  - `tests/gui/test_app_composition.py` (existing or new) — covers AC-8 by patching `install_crash_handlers` in the composition root and asserting it is called exactly once with `app_name="mix-calculator"`.
- Unit tests (pytest) for the fixed behavior and boundaries: all of the above plus targeted unit tests for `resolve_log_dir` parameterized over `("Windows", env_with_LOCALAPPDATA)`, `("Darwin", env_with_HOME)`, `("Linux", env_without_XDG_STATE_HOME)`, `("Linux", env_with_XDG_STATE_HOME)`.
- Edge cases and negative scenarios:
  - Missing `LOCALAPPDATA` env var on Windows → fall back to `~/AppData/Local/mix-calculator/logs/`.
  - Log directory does not exist → installer creates it (parents=True, exist_ok=True).
  - Second `install_crash_handlers` call returns the same `CrashHandlerInstallation` (or an equivalent value) without re-registering hooks.
  - Worker raises `BaseException` (e.g., `SystemExit`) → re-raised; `KeyboardInterrupt` → re-raised; `Exception` → captured and surfaced.
- Error handling and logging verification:
  - Assert `logger.error` is called with `exc_info=True` at the worker boundary.
  - Assert the Qt message handler converts each Qt category to the matching `logging` level.
- Coverage impact and targets for changed lines/modules: changed-line coverage on the four production files >= 85% line / >= 75% branch.
- Toolchain commands to run (format → lint → type-check → test):
  - `poetry run black .`
  - `poetry run ruff check .`
  - `poetry run pyright`
  - `poetry run pytest --cov --cov-branch --cov-report=term-missing`
- Manual validation steps (if required):
  - Smoke-test the GUI: launch, select a workbook, click SKU_LU Import; expect either successful load or a clear error dialog plus a log file at the resolved per-user path.
  - Intentionally inject a malformed `.xlsx` to confirm a non-silent failure with a captured traceback.


## Acceptance Criteria

- [x] **AC-1 (crash-handler module exists).** A new module `src/gui/_crash_handler.py` exists and exposes a single `install_crash_handlers(*, app_name: str, log_dir: Path | None = None) -> CrashHandlerInstallation` entry point plus a pure `resolve_log_dir(app_name, platform_system, env)` helper. The module is Pyright-clean with full type hints and contains no broad bare `except:` clauses.

- [x] **AC-2 (four hooks installed).** Calling `install_crash_handlers` installs all four hooks: `faulthandler.enable(file=<crash-log>)`, `sys.excepthook`, `threading.excepthook`, and `qInstallMessageHandler`. A pytest test asserts each of the four hooks is in place after installation (state inspected through the returned `CrashHandlerInstallation` value object).

- [x] **AC-3 (log-path resolution).** `resolve_log_dir` is a pure function whose unit tests cover three platform branches (`Windows`, `Darwin`, `Linux`) with injected `env` mappings, and whose behavior matches the resolution table in the spec. No `tempfile` usage in tests; resolution is verified by string assertion on the returned `Path` against an injected `env`/`home`.

- [x] **AC-4 (idempotent install).** Calling `install_crash_handlers` a second time is a no-op (the prior handlers remain installed; no duplicate handler is registered). A pytest test asserts this.

- [x] **AC-5 (worker-thread exception captured).** When a `PipelineWorker.run` task raises an exception, the worker boundary logs the traceback via `logger.error(..., exc_info=True)`, emits the `error` signal, and surfaces a `QMessageBox` on the GUI thread via a queued connection. A pytest-qt test injects a worker exception and asserts (a) the error signal handler runs on the GUI thread, (b) a log line containing the traceback is present, and (c) the GUI does not abort.

- [x] **AC-6 (cross-thread Qt mutation eliminated).** [src/gui/runners.py](src/gui/runners.py) no longer connects worker signals to plain Python closures. All `finished` / `error` notifications are routed through a `QObject` receiver bound to the GUI thread with `Qt.ConnectionType.QueuedConnection` (or `QMetaObject.invokeMethod` with `Qt.QueuedConnection`). A pytest-qt test asserts the receiver is queued, not direct.

- [x] **AC-7 (Qt fatal routed to log).** Qt warnings/criticals/fatals issued via `qDebug` / `qWarning` / `qCritical` / `qFatal` are routed through Python `logging` at corresponding levels. A pytest test installs the handler against a captured log and asserts the routing.

- [x] **AC-8 (composition root wires the installer).** [src/gui/app.py](src/gui/app.py) calls `install_crash_handlers(app_name="mix-calculator")` exactly once at process startup, before `QApplication` is constructed. A pytest test loads the composition root with mocked installer and asserts a single call with the expected app name.

- [x] **AC-9 (toolchain green).** Full Python toolchain passes in a single uninterrupted loop: `poetry run black .`, `poetry run ruff check .`, `poetry run pyright`, `poetry run pytest --cov --cov-branch --cov-report=term-missing`. No new suppressions (`# noqa` / `# type: ignore`) are added unless they match a pre-authorized pattern.

- [x] **AC-10 (coverage non-regressing).** Changed-line coverage on `src/gui/_crash_handler.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, and `src/gui/app.py` is at or above the repo thresholds (>= 85% line, >= 75% branch). Coverage on unchanged files does not regress.
  - Remediation cycle 1: three new direct-invocation tests added in `tests/gui/test_crash_handler.py` — `test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror` — bringing `_crash_handler.py` line coverage from 88% to 100%.

- [x] **AC-11 (no new dependency).** `pyproject.toml` and `poetry.lock` are unchanged. The fix uses stdlib and `PySide6` only.

- [x] **AC-12 (file-size cap).** No production file in the diff exceeds 500 lines.
  - Remediation cycle 1: `src/gui/app.py` reduced from 503 to 499 lines by extracting the crash-handler bootstrap into the new `src/gui/_crash_handler_bootstrap.py` (94 lines). Post-fix counts captured in `evidence/qa-gates/phase8/file-sizes.md`.

## Risks & Mitigations
- Technical or operational risks:
  - `faulthandler` writes to a file handle that must remain open for the life of the process. If the file handle is closed early (e.g., by a GC of the installer's return value), `faulthandler` will silently drop output. Mitigation: hold the file handle on a module-level `_State` object owned by the installer; tested via AC-2.
  - `qInstallMessageHandler` returns the previous handler. The installer must record and not overwrite a pre-installed handler. Mitigation: idempotency check in `install_crash_handlers` per AC-4.
  - The new queued connection introduces an event-loop dependency for callback delivery. If a test invokes the runner without a running event loop, callbacks will never fire. Mitigation: tests that rely on the queued path use `qtbot.waitSignal` / `qtbot.waitUntil`; the `SynchronousRunner` test seam is unchanged for tests that want direct dispatch.
  - Crash logs may accumulate without bound. Mitigation: deferred — capture the question as a follow-up; the priority of this fix is non-silent failure, not log management.
- Mitigations and rollbacks:
  - Rollback: revert the PR; no migration required.
  - Feature gate: `install_crash_handlers(enable: bool = True)` lets a future regression be disabled at the composition root without surgery, though this is not exposed to users.

## Rollout & Follow-up
- Release/rollout steps:
  - Merge PR after CI green; the next Velopack build picks up the change automatically.
- Post-fix monitoring or clean-up tasks:
  - Manually trigger the SKU_LU repro after the next build; confirm the new dialog and the log file.
  - Follow-up issue (not blocking this PR): introduce log-file size cap or rotation.
- Links: issue, PRs, related docs
  - Issue: https://github.com/drmoisan/mix-calculator/issues/46
  - Research basis: `artifacts/research/skulu-gui-crash-diagnosis.md`
