# Phase 0 — Spec Acknowledgement

Timestamp: 2026-05-30T22-50

Spec read: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md` (Status: Approved, Version 1.0)

Acceptance Criteria acknowledged:

- AC-1 — Crash-handler module `src/gui/_crash_handler.py` exposes `install_crash_handlers` and pure `_resolve_log_dir`; Pyright-clean, no bare except.
- AC-2 — All four hooks installed: `faulthandler.enable(file=...)`, `sys.excepthook`, `threading.excepthook`, `qInstallMessageHandler`; verifiable via returned value.
- AC-3 — `_resolve_log_dir` is pure with tests covering Windows / Darwin / Linux platform branches via injected `env`; no `tempfile`.
- AC-4 — Repeated `install_crash_handlers` calls are no-op (no duplicate hook registration); test enforces this.
- AC-5 — `PipelineWorker.run` logs traceback via `logger.error(..., exc_info=True)`, emits `error` signal; test injects exception and verifies behavior.
- AC-6 — `runners.py` routes `finished` / `error` through `QObject` receiver with `Qt.ConnectionType.QueuedConnection`; test asserts queued connection.
- AC-7 — Qt categories routed to Python `logging` levels (Debug -> DEBUG, Info -> INFO, Warning -> WARNING, Critical -> ERROR, Fatal -> CRITICAL); test verifies routing.
- AC-8 — `src/gui/app.py` calls `install_crash_handlers(app_name="mix-calculator")` exactly once before `QApplication`; test patches and asserts single call.
- AC-9 — Full toolchain green in single pass: black, ruff, pyright, pytest with coverage; no unauthorized suppressions.
- AC-10 — Changed-line coverage on the four files >= 85% line / >= 75% branch; unchanged-file coverage does not regress.
- AC-11 — `pyproject.toml` and `poetry.lock` unchanged; stdlib + already-present PySide6 only.
- AC-12 — No production file in the diff exceeds 500 lines.
