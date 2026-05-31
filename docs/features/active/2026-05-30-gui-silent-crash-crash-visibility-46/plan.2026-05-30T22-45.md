# gui-silent-crash-crash-visibility (Plan)

- **Issue:** #46
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30T22-45
- **Status:** Executed (all tasks ticked; pending orchestrator commit and PR)
- **Version:** 1.0
- **Work Mode:** full-bug
- **Spec:** [spec.md](spec.md) (Approved, v1.0)
- **Research basis:** [artifacts/research/skulu-gui-crash-diagnosis.md](../../../../artifacts/research/skulu-gui-crash-diagnosis.md)

**Fail-closed evidence rule.** Every phase that runs a toolchain command writes a step-level evidence artifact under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/` with at least: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Coverage-bearing steps include numeric line and branch percentages and the targeted-file coverage for the four modified production files. Missing artifacts force a BLOCKED audit verdict.

**Evidence location invariant.** All evidence in this plan resolves to `<FEATURE>/evidence/<kind>/`. Any caller-supplied non-canonical path (e.g., `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`) is rejected and replaced with the canonical path. This clause is non-overridable.

**Acceptance-criteria index (AC-1..AC-12).** Each AC is cited in at least one task below. Final mapping appears in the AC traceability matrix at the end of this plan.

---

### Phase 0 — Context & Baselines

- [x] [P0-T1] Read repo policy files in canonical order and record the read list. Files to read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/tonality.md`, `.claude/rules/self-explanatory-code-commenting.md`. Evidence: `evidence/baseline/phase0-instructions-read.md` with `Timestamp:`, `Policy Order:`, and explicit list of files read.
- [x] [P0-T2] Record git baseline: capture `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, and `git status --porcelain`. Evidence: `evidence/baseline/phase0-git-baseline.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (branch name, commit SHA, dirty/clean state).
- [x] [P0-T3] Read approved spec at `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md` and acknowledge AC-1..AC-12. Evidence: `evidence/baseline/phase0-spec-ack.md` listing the 12 AC IDs and their one-line summaries.
- [x] [P0-T4] Enumerate touched production files and their current line counts to confirm the 500-line cap will hold post-change. Files: `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `src/gui/app.py`. Evidence: `evidence/baseline/phase0-file-sizes.md` with `Timestamp:` and one line per file: `<path>: <line_count>`.
- [x] [P0-T5] Confirm fixture inventory in `tests/gui/conftest.py` (qtbot availability, offscreen platform) and existing related tests (`tests/gui/test_pipeline_worker.py`, `tests/gui/test_runners.py`, `tests/gui/test_app_composition.py`). Evidence: `evidence/baseline/phase0-fixture-inventory.md` listing each file's purpose and the seam it provides.
- [x] [P0-T6] Baseline format check. Command: `poetry run black --check .`. Evidence: `evidence/baseline/phase0-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (count of files needing formatting or "all formatted").
- [x] [P0-T7] Baseline lint check. Command: `poetry run ruff check .`. Evidence: `evidence/baseline/phase0-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count or "no issues").
- [x] [P0-T8] Baseline type check. Command: `poetry run pyright`. Evidence: `evidence/baseline/phase0-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (errors / warnings / informations counts).
- [x] [P0-T9] Baseline test + coverage run. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Evidence: `evidence/baseline/phase0-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` containing baseline pass/fail counts and headline line + branch coverage percentages, plus per-file baseline coverage for `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `src/gui/app.py` (the as-yet-unwritten `src/gui/_crash_handler.py` is not present at baseline).

### Phase 1 — Regression Tests (Fail-Before)

Regression tests authored before the production fix lands. Each is marked `[expect-fail]` in this phase and re-validated `[expect-pass]` in Phase 5.

- [x] [P1-T1] [expect-fail] Author `tests/gui/test_crash_handler.py` with a failing scaffold: assert `from gui._crash_handler import install_crash_handlers, CrashHandlerInstallation, _resolve_log_dir` succeeds. This pin verifies the module does not yet exist. Covers fail-before for AC-1.
- [x] [P1-T2] [expect-fail] Add to `tests/gui/test_crash_handler.py` a test `test_install_crash_handlers_installs_all_four_hooks` that calls the installer with an injected `log_dir` and asserts the returned `CrashHandlerInstallation.installed_hooks == ("faulthandler", "sys.excepthook", "threading.excepthook", "qt.message_handler")`. Covers fail-before for AC-2.
- [x] [P1-T3] [expect-fail] Add parametrized tests in `tests/gui/test_crash_handler.py` for `_resolve_log_dir` covering the three platform branches (`Windows` with and without `LOCALAPPDATA`, `Darwin`, `Linux` with and without `XDG_STATE_HOME`). Use string assertions against the returned `Path` segments — no filesystem touch, no `tempfile`. Covers fail-before for AC-3.
- [x] [P1-T4] [expect-fail] Add `test_install_crash_handlers_is_idempotent` in `tests/gui/test_crash_handler.py`: second call returns an equivalent installation value and does not double-register hooks (check `sys.excepthook is unchanged after second call`, `threading.excepthook is unchanged`, faulthandler file handle is the same object). Covers fail-before for AC-4.
- [x] [P1-T5] [expect-fail] Add `test_qt_message_handler_routes_categories_to_logging_levels` in `tests/gui/test_crash_handler.py` using `caplog` to assert each Qt category maps to the matching Python `logging` level. Covers fail-before for AC-7.
- [x] [P1-T6] [expect-fail] Extend `tests/gui/test_pipeline_worker.py` with `test_pipeline_worker_run_logs_traceback_on_exception` asserting `logger.error` is called with `exc_info=True` and the `error` signal fires. Also add `test_pipeline_worker_run_reraises_keyboard_interrupt` and `test_pipeline_worker_run_reraises_system_exit` to pin the `BaseException` widening contract. Covers fail-before for AC-5.
- [x] [P1-T7] [expect-fail] Author `tests/gui/test_runners_threaded.py` with `test_threaded_runner_uses_queued_connection_for_finished_and_error` using `qtbot` plus a thread-affinity probe (capture `threading.current_thread()` inside the callbacks and assert it equals the GUI thread). Also assert the connection type via `QObject.receivers` / signal inspection where feasible. Covers fail-before for AC-6.
- [x] [P1-T8] [expect-fail] Extend `tests/gui/test_app_composition.py` with `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` using `unittest.mock.patch` on `gui.app.install_crash_handlers` and asserting exactly one call with `app_name="mix-calculator"` before `QApplication` is constructed. Covers fail-before for AC-8.
- [x] [P1-T9] Run the regression tests in isolation to confirm fail-before. Command: `poetry run pytest tests/gui/test_crash_handler.py tests/gui/test_pipeline_worker.py tests/gui/test_runners_threaded.py tests/gui/test_app_composition.py -x`. Expected `EXIT_CODE: 1` (some tests must fail). Evidence: `evidence/regression-testing/phase1-fail-before.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` listing each test name and its observed outcome (each new test should be in the failed set or error set).

### Phase 2 — Crash-Handler Module (`src/gui/_crash_handler.py`)

- [x] [P2-T1] Create `src/gui/_crash_handler.py` containing only module-level imports, the `CrashHandlerInstallation` frozen dataclass (`log_dir: Path`, `crash_log_path: Path`, `installed_hooks: tuple[str, ...]`), and a private module-level `_State` singleton holder. File must remain under 500 lines. Add full Google-style class docstrings.
- [x] [P2-T2] Implement the pure `resolve_log_dir(app_name: str, platform_system: str, env: Mapping[str, str]) -> Path` in `src/gui/_crash_handler.py`. Branch order: Windows → `env["LOCALAPPDATA"]` if present, else `Path.home() / "AppData" / "Local"`; Darwin → `Path.home() / "Library" / "Logs"`; Linux/other → `env["XDG_STATE_HOME"]` if present, else `Path.home() / ".local" / "state"`. Each branch must have a decision-logic comment per the commenting policy. Append `<app_name> / "logs"` to the chosen base. (Renamed from `_resolve_log_dir` to `resolve_log_dir` to satisfy Pyright strict-mode `reportPrivateUsage` when accessed from tests.)
- [x] [P2-T3] Implement private hook helpers in `src/gui/_crash_handler.py`: `_make_sys_excepthook(crash_log_path)`, `_make_threading_excepthook(crash_log_path)`, `make_qt_message_handler(logger)`. Each helper returns a callable conforming to the documented hook signature. The Qt message handler maps `QtMsgType.QtDebugMsg → DEBUG`, `QtInfoMsg → INFO`, `QtWarningMsg → WARNING`, `QtCriticalMsg → ERROR`, `QtSystemMsg → ERROR`, `QtFatalMsg → CRITICAL`. (`make_qt_message_handler` renamed from `_make_qt_message_handler` per Pyright strict-mode private-usage rule.)
- [x] [P2-T4] Implement `install_crash_handlers(*, app_name: str, log_dir: Path | None = None, enable: bool = True) -> CrashHandlerInstallation` in `src/gui/_crash_handler.py`. Behavior: if `enable=False` return a no-op installation; if a prior installation exists return it unchanged (idempotency); otherwise create `log_dir` via `mkdir(parents=True, exist_ok=True)`, open the crash log file in append mode, call `faulthandler.enable(file=...)`, install `sys.excepthook` (chain to previous), install `threading.excepthook` (chain to previous), call `qInstallMessageHandler`, store the file handle on `_State` to preserve lifetime, and return a populated `CrashHandlerInstallation`.
- [x] [P2-T5] Verify the new module is under 500 lines. Command: `pwsh -NoProfile -Command "(Get-Content src/gui/_crash_handler.py | Measure-Object -Line).Lines"`. Evidence: append result to `evidence/baseline/phase0-file-sizes.md` under a new "Post P2 sizes" section; assert `<= 500`. (Post-refactor: 405 lines.)
- [x] [P2-T6] Run toolchain loop for Phase 2. Restart at black on any change or failure. Steps and evidence (one artifact per step under `evidence/qa-gates/phase2/`):
  - `poetry run black .` → `evidence/qa-gates/phase2/black.md`
  - `poetry run ruff check .` → `evidence/qa-gates/phase2/ruff.md`
  - `poetry run pyright` → `evidence/qa-gates/phase2/pyright.md`
  - `poetry run pytest tests/gui/test_crash_handler.py` → `evidence/qa-gates/phase2/pytest-crash-handler.md`
  Each artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Final test exit code must be 0. Covers AC-1, AC-2, AC-3, AC-4, AC-7.

### Phase 3 — Runner Wiring Fix (`src/gui/runners.py`)

- [x] [P3-T1] In `src/gui/runners.py`, add a private `_RunnerReceiver(QObject)` class with two `@Slot` methods `dispatch_success(self, result)` and `dispatch_error(self, message)` that call the user-supplied `on_success` / `on_error` callbacks. The receiver is constructed on the GUI thread (no `moveToThread`) so its event affinity is the calling thread. Class must include the mandatory Google-style docstring covering purpose, responsibilities, and thread-affinity invariant. (Slot methods named without underscore prefix because Qt's `@Slot` decorator and Pyright strict-mode `reportPrivateUsage` interact poorly with underscore-prefixed slot names.)
- [x] [P3-T2] In `src/gui/runners.py`, modify `ThreadedRunner.run` so `worker.finished` and `worker.error` connect to the new `_RunnerReceiver` slots with `Qt.ConnectionType.QueuedConnection` instead of direct closures. Keep the existing `worker.finished.connect(thread.quit)` / `worker.error.connect(thread.quit)` semantics intact (these are safe: `QThread.quit` is thread-safe). Hold a reference to the receiver on `self._receiver` so it is not garbage collected.
- [x] [P3-T3] Verify `RunnerProtocol` and `SynchronousRunner` are unchanged in public surface. Read both definitions in `src/gui/runners.py` and confirm only `ThreadedRunner.run` and the new private `_RunnerReceiver` class differ from baseline. Evidence: `evidence/baseline/phase3-runner-diff-summary.md` summarizing exactly which symbols changed.
- [x] [P3-T4] Run toolchain loop for Phase 3. Restart at black on any change or failure. Steps and evidence (one artifact per step under `evidence/qa-gates/phase3/`):
  - `poetry run black .` → `evidence/qa-gates/phase3/black.md`
  - `poetry run ruff check .` → `evidence/qa-gates/phase3/ruff.md`
  - `poetry run pyright` → `evidence/qa-gates/phase3/pyright.md`
  - `poetry run pytest tests/gui/test_runners.py tests/gui/test_runners_threaded.py` → `evidence/qa-gates/phase3/pytest-runners.md`
  Each artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Final test exit code must be 0. Covers AC-6.

### Phase 4 — Worker Boundary Widening + Composition Root

- [x] [P4-T1] In `src/gui/workers/pipeline_worker.py`, widen the `except Exception` clause at line 98 to `except BaseException as exc:` with an explicit guard that re-raises `KeyboardInterrupt` and `SystemExit`. Use the pattern:
  ```
  except BaseException as exc:
      if isinstance(exc, (KeyboardInterrupt, SystemExit)):
          raise
      logger.error("Pipeline task failed: %s", exc, exc_info=True)
      self.error.emit(str(exc))
      return
  ```
  Do not use bare `except:`. Update the surrounding docstring to record the boundary contract. No new `# noqa` / `# type: ignore` suppressions.
- [x] [P4-T2] In `src/gui/app.py`, import `install_crash_handlers` from `gui._crash_handler` and call `install_crash_handlers(app_name="mix-calculator")` exactly once at the top of the GUI entry point, before `QApplication` construction and before any worker or widget is created. Capture the returned `CrashHandlerInstallation` (assign to a local) so its file-handle anchor is alive for the process. Add an inline comment explaining the call ordering invariant.
- [x] [P4-T3] Confirm no new dependency landed: `git diff -- pyproject.toml poetry.lock` must show no changes. Evidence: `evidence/qa-gates/phase4/dependency-diff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` ("no changes" or BLOCKED).
- [x] [P4-T4] Confirm production-file line counts. Files: `src/gui/_crash_handler.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `src/gui/app.py`. Evidence: `evidence/qa-gates/phase4/file-sizes.md` recording each path and its line count; each must be `<= 500`.
- [x] [P4-T5] Run toolchain loop for Phase 4. Restart at black on any change or failure. Steps and evidence (one artifact per step under `evidence/qa-gates/phase4/`):
  - `poetry run black .` → `evidence/qa-gates/phase4/black.md`
  - `poetry run ruff check .` → `evidence/qa-gates/phase4/ruff.md`
  - `poetry run pyright` → `evidence/qa-gates/phase4/pyright.md`
  - `poetry run pytest tests/gui/test_pipeline_worker.py tests/gui/test_app_composition.py` → `evidence/qa-gates/phase4/pytest-worker-app.md`
  Each artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Final test exit code must be 0. Covers AC-5, AC-8, AC-11, AC-12.

### Phase 5 — Regression Tests Re-Validation (Pass-After)

- [x] [P5-T1] [expect-pass] Re-run all regression tests authored in Phase 1. Command: `poetry run pytest tests/gui/test_crash_handler.py tests/gui/test_pipeline_worker.py tests/gui/test_runners_threaded.py tests/gui/test_app_composition.py`. Expected `EXIT_CODE: 0`. Evidence: `evidence/regression-testing/phase5-pass-after.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` listing each previously-failing test and its now-passing status. The pass-after evidence MUST cite the matching fail-before line in `evidence/regression-testing/phase1-fail-before.md` for every regression test.

### Phase 6 — Suppression Audit

- [x] [P6-T1] Search the diff for new `# noqa` and `# type: ignore` markers. Command (PowerShell): `git diff --unified=0 origin/main -- src/gui/_crash_handler.py src/gui/runners.py src/gui/workers/pipeline_worker.py src/gui/app.py | Select-String -Pattern '# (noqa|type: ignore)'`. Evidence: `evidence/qa-gates/phase6/suppressions.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` enumerating each match. If any match is not pre-authorized in `.claude/rules/python-suppressions.md` with the verbatim comment format, mark the audit BLOCKED.

### Phase 7 — Final QA Loop (Full Toolchain, Coverage-Enabled)

Run the full seven-step Python toolchain on the entire repository. If any step fails or modifies files, restart at black. Each step persists its own evidence artifact under `evidence/qa-gates/phase7/`.

- [x] [P7-T1] `poetry run black .` → `evidence/qa-gates/phase7/black.md`. `EXIT_CODE: 0` required.
- [x] [P7-T2] `poetry run ruff check .` → `evidence/qa-gates/phase7/ruff.md`. `EXIT_CODE: 0` required.
- [x] [P7-T3] `poetry run pyright` → `evidence/qa-gates/phase7/pyright.md`. `EXIT_CODE: 0` and zero errors required.
- [x] [P7-T4] `poetry run pytest --cov --cov-branch --cov-report=term-missing` → `evidence/qa-gates/phase7/pytest.md`. `EXIT_CODE: 0` required. `Output Summary:` MUST record: total tests run, total pass/fail count, headline line coverage %, headline branch coverage %, and per-file coverage for `src/gui/_crash_handler.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `src/gui/app.py`.
- [x] [P7-T5] Coverage delta verification: compute baseline (Phase 0) vs post-change (Phase 7) line and branch coverage for the four touched files. Evidence: `evidence/qa-gates/phase7/coverage-delta.md` recording for each file: baseline-line%, post-line%, baseline-branch%, post-branch%, and verdict (`PASS` only if changed-line coverage >= 85% line and >= 75% branch and no regression on unchanged files). Covers AC-9, AC-10.
- [x] [P7-T6] Confirm the full toolchain completed in a single uninterrupted pass (no restart after the final loop). Evidence: `evidence/qa-gates/phase7/single-pass-attestation.md` listing the four step artifact paths and their exit codes in execution order with `Timestamp:`. Covers AC-9.

### Phase 8 — Documentation & PR Handoff

- [x] [P8-T1] Update `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`: tick AC-1..AC-12 checkboxes, bump `Status:` to `Implemented (pending review)`, and bump `Last Updated:` to the Phase 7 completion timestamp.
- [x] [P8-T2] Mirror the issue update locally. Evidence: `evidence/issue-updates/issue-46.<entry-ts>.md` with `Timestamp:`, the prepared GitHub comment text, `PostedAs: comment` (or `POSTING BLOCKED` + reason if not posted), the GitHub URL if posted.
- [x] [P8-T3] Stage the final commit on the feature branch. Files staged: `src/gui/_crash_handler.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `src/gui/app.py`, `tests/gui/test_crash_handler.py`, `tests/gui/test_runners_threaded.py`, `tests/gui/test_pipeline_worker.py`, `tests/gui/test_app_composition.py`, `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`, all `evidence/**` artifacts. Evidence: `evidence/other/phase8-staged-paths.md` listing every staged path with `Timestamp:`. Do not run `git commit`; the orchestrator owns the commit step.
- [x] [P8-T4] Draft PR title + body in `evidence/other/phase8-pr-draft.md`: title `fix(gui): surface silent SKU_LU crashes via crash handler + queued connections (#46)`; body summarizes the structural fix, lists the four changed files, includes the AC-1..AC-12 checklist mirrored from the spec, and links to the spec, issue, and research artifact. Do NOT invoke `gh pr create`; the orchestrator gates PR creation.

---

## Acceptance-Criteria Traceability Matrix

| AC | Description | Tasks |
|---|---|---|
| AC-1 | `_crash_handler.py` exists with documented public surface | P1-T1, P2-T1, P2-T2, P2-T6 |
| AC-2 | Four hooks installed and recorded in returned value | P1-T2, P2-T3, P2-T4, P2-T6 |
| AC-3 | `_resolve_log_dir` pure-function platform branches | P1-T3, P2-T2, P2-T6 |
| AC-4 | Idempotent re-install | P1-T4, P2-T4, P2-T6 |
| AC-5 | Worker boundary logs traceback and emits `error` | P1-T6, P4-T1, P4-T5, P5-T1 |
| AC-6 | Queued-connection routing in `ThreadedRunner` | P1-T7, P3-T1, P3-T2, P3-T4, P5-T1 |
| AC-7 | Qt categories routed to Python `logging` levels | P1-T5, P2-T3, P2-T4, P2-T6 |
| AC-8 | Composition root calls installer once with app name | P1-T8, P4-T2, P4-T5, P5-T1 |
| AC-9 | Full toolchain green in single pass | P7-T1..P7-T6, P6-T1 |
| AC-10 | Changed-line coverage thresholds met, no regression | P0-T9, P7-T4, P7-T5 |
| AC-11 | No new dependency | P4-T3 |
| AC-12 | No production file exceeds 500 lines | P0-T4, P2-T5, P4-T4 |
