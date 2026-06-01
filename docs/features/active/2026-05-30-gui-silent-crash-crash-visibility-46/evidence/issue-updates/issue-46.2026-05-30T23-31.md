# Issue #46 — Local Update Mirror

Timestamp: 2026-05-30T23-31

PostedAs: not-posted

POSTING BLOCKED: The orchestrator owns the GitHub posting step. This mirror captures the prepared comment text so it can be posted verbatim when the orchestrator opens the PR.

## Prepared comment text

Implementation complete on branch `bug/gui-silent-crash-crash-visibility-46`. Summary of the structural fix and the four touched files:

- New module `src/gui/_crash_handler.py` (405 lines). Installs the four crash hooks (`faulthandler`, `sys.excepthook`, `threading.excepthook`, `qInstallMessageHandler`), routes Qt categories to Python `logging` levels (Debug -> DEBUG, Info -> INFO, Warning -> WARNING, Critical -> ERROR, System -> ERROR, Fatal -> CRITICAL), and resolves a per-user log directory across Windows / Darwin / Linux via a pure helper.
- Modified `src/gui/runners.py` (156 -> 223 lines). Adds a private `_RunnerReceiver(QObject)` with two `@Slot` methods and routes `worker.finished` / `worker.error` through it via `Qt.ConnectionType.QueuedConnection`. The receiver is constructed on the GUI thread (no `moveToThread`) so callbacks always reach the GUI thread; this eliminates the documented cross-thread Qt widget mutation that was the native-abort vector.
- Modified `src/gui/workers/pipeline_worker.py` (79 -> 92 lines). Widens the worker boundary from `except Exception` to `except BaseException` with an explicit re-raise for `KeyboardInterrupt` and `SystemExit`. Adds `exc_info=True` to the `logger.error` call so the crash log captures a full traceback for caught Python exceptions.
- Modified `src/gui/app.py` (431 -> 439 lines). Imports `install_crash_handlers` and invokes it once at process startup before `QApplication` construction, so the hooks are live for the entire process lifetime.

### Acceptance criteria

- AC-1 (crash-handler module exists) — PASS.
- AC-2 (four hooks installed and recorded) — PASS.
- AC-3 (log-path resolution pure, all platform branches tested) — PASS.
- AC-4 (idempotent install) — PASS.
- AC-5 (worker traceback logging + `BaseException` widening) — PASS.
- AC-6 (cross-thread Qt mutation eliminated; queued-connection routing) — PASS.
- AC-7 (Qt categories routed to Python logging levels) — PASS.
- AC-8 (composition root calls installer once with `app_name="mix-calculator"`) — PASS.
- AC-9 (full toolchain green in single pass: black, ruff, pyright, pytest) — PASS.
- AC-10 (coverage non-regressing; >= 85% line / >= 75% branch on changed files) — PASS.
- AC-11 (no new dependency) — PASS.
- AC-12 (no production file exceeds 500 lines) — PASS.

### Toolchain results

- `poetry run black --check .` — exit 0, 173 files unchanged.
- `poetry run ruff check .` — exit 0, all checks passed.
- `poetry run pyright` — exit 0, 0 errors.
- `poetry run pytest --cov --cov-branch --cov-report=term-missing` — exit 0, 734 passed (baseline 717, +17 new tests). Total coverage 99% (unchanged from baseline).
- Per-file post-change line / branch coverage on the four touched files: `_crash_handler.py` 88% / 100%; `runners.py` 100% / n/a; `pipeline_worker.py` 100% / 100%; `app.py` 99% / 92%.

### Evidence

All evidence artifacts live under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/`:
- baseline/ — Phase 0 baselines (black, ruff, pyright, pytest, file sizes, fixture inventory, spec acknowledgement).
- regression-testing/ — Phase 1 fail-before evidence + Phase 5 pass-after evidence (with cross-reference to fail-before).
- qa-gates/phase2..phase7/ — per-phase toolchain artifacts.
- issue-updates/ — this mirror.

### No new dependencies, no new suppressions

Verified by `git diff -- pyproject.toml poetry.lock` (no changes) and `git diff origin/main -- src/gui/_crash_handler.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py | Select-String '# (noqa|type: ignore)'` (no matches).
