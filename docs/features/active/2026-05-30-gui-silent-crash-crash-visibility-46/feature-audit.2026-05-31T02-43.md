# Feature Audit — gui-silent-crash-crash-visibility (Issue #46)

- **Timestamp:** 2026-05-31T02-43
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `666e84a32aa158a4554cb0305c5695512e35f0cd`
- **Work mode:** full-bug (AC source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`)
- **Total AC items:** 12 (AC-1 .. AC-12)

## Acceptance Criteria Evaluation

| AC | Verdict | Evidence |
|---|---|---|
| AC-1 (crash-handler module exists) | PARTIAL | Module exists at `src/gui/_crash_handler.py` (495 lines), is Pyright-clean, exports `install_crash_handlers` and `CrashHandlerInstallation`. No bare `except:` clauses (verified `grep -nE 'except\s*:'`). Spec text says `_resolve_log_dir`; implementation exposes `resolve_log_dir` (no underscore) — symbol drift documented in plan P2-T2. |
| AC-2 (four hooks installed) | PASS | `install_crash_handlers` returns `CrashHandlerInstallation.installed_hooks == ("faulthandler", "sys.excepthook", "threading.excepthook", "qt.message_handler")`. Asserted by `test_install_crash_handlers_installs_all_four_hooks`. |
| AC-3 (log-path resolution) | PASS | `resolve_log_dir` is pure (no `os.environ` read), tested parametrically over Windows (with/without LOCALAPPDATA), Darwin, Linux (with/without XDG_STATE_HOME). No tempfile usage. Five-parameter parametrize at `test_resolve_log_dir_branches`. |
| AC-4 (idempotent install) | PASS | Second call returns the same `CrashHandlerInstallation` instance and does not rebind process hooks. Asserted by `test_install_crash_handlers_is_idempotent`. |
| AC-5 (worker-thread exception captured) | PASS | `pipeline_worker.py` widens to `except BaseException` with explicit re-raise of `KeyboardInterrupt`/`SystemExit`; `logger.error(..., exc_info=True)` confirmed by `test_pipeline_worker_run_logs_traceback_on_exception`. Re-raise contract pinned by two additional tests. |
| AC-6 (cross-thread Qt mutation eliminated) | PASS | `ThreadedRunner.run` constructs `_RunnerReceiver(QObject)` on the calling thread, connects `worker.finished` / `worker.error` with `Qt.ConnectionType.QueuedConnection`. Thread-affinity probe asserts callbacks fire on the GUI thread (`test_threaded_runner_success_callback_runs_on_gui_thread`, `..._error_callback_runs_on_gui_thread`, and `..._uses_queued_connection_for_finished_and_error`). |
| AC-7 (Qt fatal routed to log) | PASS | `make_qt_message_handler` maps each `QtMsgType` to the documented `logging` level. Asserted via `caplog` for `QtDebugMsg`, `QtInfoMsg`, `QtWarningMsg`, `QtCriticalMsg`, `QtSystemMsg`, `QtFatalMsg` (`test_qt_message_handler_routes_categories_to_logging_levels`). |
| AC-8 (composition root wires the installer) | PASS | `src/gui/app.py:488` calls `install_crash_handlers(app_name="mix-calculator")` exactly once before `QApplication([])`. Asserted by `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` (verifies single call and ordering vs QApplication init). |
| AC-9 (toolchain green) | PASS | Phase 7 evidence: `black.md` EXIT_CODE 0, `ruff.md` 0, `pyright.md` 0, `pytest.md` 0 (734/734 passed). Single-pass attestation present (`single-pass-attestation.md`). No new suppressions added (Phase 6 `suppressions.md`, re-verified via `git diff` scan). |
| AC-10 (coverage non-regressing) | PARTIAL | Numeric thresholds met (Phase 7 `coverage-delta.md`): `_crash_handler.py` 88% line / 100% branch; `runners.py` 100% / n/a; `pipeline_worker.py` 100% / 100%; `app.py` 99% / 92%. No regression on unchanged files. However, `_crash_handler.py` missing-lines (254-263, 290-303, 374-383) are the bodies of the `sys.excepthook` and `threading.excepthook` closures and the on-disk `_append_traceback` helper — the crash-write path is structurally uncovered. AC-10 threshold is met; the underlying critical-behavior coverage is incomplete (informational PARTIAL). |
| AC-11 (no new dependency) | PASS | `git diff --name-only 0b353ad..666e84a -- pyproject.toml poetry.lock` returns empty. |
| AC-12 (file-size cap) | **FAIL** | `src/gui/app.py` is **503 lines** at HEAD (`awk 'END{print NR}'` and `wc -l` both report 503). The 500-line cap is exceeded. Phase 4 evidence reported 439 due to PowerShell `Measure-Object -Line` undercount; the actual count contradicts the AC-12 attestation. |

### Acceptance Criteria Check-off

The spec file already shows all 12 AC items as `[x]`. This audit re-evaluates against the diff and concludes:

- 9 items remain correctly `[x]` (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-11).
- 2 items are PARTIAL (AC-1 symbol-naming drift; AC-10 closure-body coverage gap with thresholds technically met).
- 1 item is FAIL (AC-12 file-size cap).

Recommendation: revert the AC-12 checkbox in `spec.md` to `[ ]` until `src/gui/app.py` returns under 500 lines. The reviewer does not modify `spec.md` here; the remediation phase should make that change as part of restoring the cap.

## Verification Procedure

For each AC the auditor:

1. Read the spec AC text verbatim from `spec.md`.
2. Located the implementing code via the branch diff (`git diff --name-status 0b353ad..666e84a`).
3. Located the asserting test by file/function name.
4. For coverage and toolchain AC items, cross-checked the Phase 7 evidence artifacts against repository policy thresholds.
5. For AC-12, ran `awk 'END{print NR}' src/gui/app.py src/gui/_crash_handler.py src/gui/runners.py src/gui/workers/pipeline_worker.py` to obtain a method-independent line count.

## Bug-Fix Behavior Verification (Issue #46)

The bug is "GUI exits silently when SKU_LU import triggers a worker-thread fault". The branch addresses both structural causes identified in `artifacts/research/skulu-gui-crash-diagnosis.md`:

1. **Cross-thread Qt widget mutation** -> fixed by `_RunnerReceiver` + `Qt.ConnectionType.QueuedConnection` (AC-6, verified by thread-affinity probe test).
2. **No crash visibility** -> fixed by the four hooks (AC-2, AC-7) plus the per-user log directory (AC-3) plus the wider worker boundary with `exc_info=True` (AC-5).

The fix matches the proposed structural change and is testable in isolation. The remaining concern (AC-12 file-size violation) is a process/policy regression, not a functional regression.

## Final Feature-Audit Verdict

**PARTIAL** — bug-fix behavior is delivered, AC-9 / AC-11 are PASS, and the regression suite is green. However AC-12 fails (file-size cap) and AC-1 / AC-10 are PARTIAL. The feature cannot be marked complete until the file-size violation is remediated.

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- Total AC items: 12
- Checked off (delivered and verified): 9 (AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-11)
- Remaining (audit verdict not PASS): 3
  - AC-1 (PARTIAL): symbol name drift between spec and code (`_resolve_log_dir` vs `resolve_log_dir`).
  - AC-10 (PARTIAL): coverage thresholds met, but the actual crash-write closures and `_append_traceback` are never invoked by tests.
  - AC-12 (FAIL): `src/gui/app.py` is 503 lines, exceeding the 500-line cap.
