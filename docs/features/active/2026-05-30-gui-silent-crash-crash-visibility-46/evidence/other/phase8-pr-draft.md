# Phase 8 — Pull Request Draft

Timestamp: 2026-05-30T23-32

The orchestrator owns the actual `gh pr create` step. This draft is the title + body the orchestrator must use verbatim.

## Title

`fix(gui): surface silent SKU_LU crashes via crash handler + queued connections (#46)`

## Body

### Summary
- Adds a new `src/gui/_crash_handler.py` that installs the four crash hooks (`faulthandler`, `sys.excepthook`, `threading.excepthook`, `qInstallMessageHandler`) and resolves a per-user crash-log directory across Windows / Darwin / Linux.
- Wires the installer into `src/gui/app.py` so the hooks are alive before `QApplication` is constructed (AC-8).
- Eliminates cross-thread Qt widget mutation in `src/gui/runners.py` by routing `worker.finished` / `worker.error` through a GUI-thread `QObject` receiver with `Qt.ConnectionType.QueuedConnection` (AC-6).
- Widens the worker boundary in `src/gui/workers/pipeline_worker.py` to `except BaseException` (re-raising `KeyboardInterrupt` / `SystemExit`) and adds `exc_info=True` so the crash log captures a traceback for caught Python exceptions (AC-5).
- No new dependency (AC-11). No production file exceeds 500 lines (AC-12).

### Files changed
- NEW `src/gui/_crash_handler.py` (405 lines).
- MOD `src/gui/runners.py` (156 -> 223 lines).
- MOD `src/gui/workers/pipeline_worker.py` (79 -> 92 lines).
- MOD `src/gui/app.py` (431 -> 439 lines).
- NEW tests: `tests/gui/test_crash_handler.py`, `tests/gui/test_runners_threaded.py`.
- MOD tests: `tests/gui/test_pipeline_worker.py`, `tests/gui/test_app_composition.py`.

### Acceptance criteria

- [x] AC-1 — Crash-handler module exists with documented public surface.
- [x] AC-2 — Four hooks installed and recorded.
- [x] AC-3 — `resolve_log_dir` pure-function platform branches (Windows w/ and w/o `LOCALAPPDATA`; Darwin; Linux w/ and w/o `XDG_STATE_HOME`).
- [x] AC-4 — Idempotent re-install.
- [x] AC-5 — Worker boundary logs traceback (`exc_info=True`) and emits `error`; `KeyboardInterrupt`/`SystemExit` re-raised.
- [x] AC-6 — Queued-connection routing through `_RunnerReceiver` in `ThreadedRunner`.
- [x] AC-7 — Qt categories routed to Python logging levels (Debug -> DEBUG, Info -> INFO, Warning -> WARNING, Critical -> ERROR, System -> ERROR, Fatal -> CRITICAL).
- [x] AC-8 — Composition root calls installer once with `app_name="mix-calculator"` before `QApplication`.
- [x] AC-9 — Full toolchain green in single uninterrupted pass (black + ruff + pyright + pytest).
- [x] AC-10 — Changed-line coverage thresholds met (>= 85% line / >= 75% branch); no regression on unchanged files.
- [x] AC-11 — No new dependency (`pyproject.toml` and `poetry.lock` unchanged).
- [x] AC-12 — No production file exceeds 500 lines.

### Toolchain results (Phase 7, single-pass)

- `poetry run black --check .` — exit 0.
- `poetry run ruff check .` — exit 0.
- `poetry run pyright` — exit 0, 0 errors / 0 warnings.
- `poetry run pytest --cov --cov-branch --cov-report=term-missing` — exit 0, 734 passed (baseline 717, +17 new), total coverage 99% (unchanged from baseline).

### Links

- Issue: https://github.com/drmoisan/mix-calculator/issues/46
- Spec: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md` (Status: Implemented, pending review)
- Plan: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/plan.2026-05-30T22-45.md` (all tasks ticked)
- Research basis: `artifacts/research/skulu-gui-crash-diagnosis.md`
- Evidence root: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/`

Do not invoke `gh pr create` from the plan; the orchestrator gates PR creation.
