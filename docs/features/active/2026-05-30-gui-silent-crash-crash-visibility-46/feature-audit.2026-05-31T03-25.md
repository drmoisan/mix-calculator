# Feature Audit — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 1

- **Timestamp:** 2026-05-31T03-25
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `e17da56195d576de38faf47cfbfca2382ca702f1`
- **Prior audit:** `feature-audit.2026-05-31T02-43.md` (Cycle 0)
- **Work mode:** full-bug (AC source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`)
- **Total AC items:** 12 (AC-1 .. AC-12)

## Acceptance Criteria Evaluation

| AC | Cycle-0 verdict | Cycle-1 verdict | Evidence |
|---|---|---|---|
| AC-1 (crash-handler module exists) | PARTIAL | **PASS** | Module exists at `src/gui/_crash_handler.py` (495 lines), Pyright-clean, exports `install_crash_handlers` and `CrashHandlerInstallation` plus the pure `resolve_log_dir` helper. No bare `except:` clauses (`grep -nE 'except\s*:' src/gui/_crash_handler.py` -> no matches). Spec AC-1 verbatim text now reads `resolve_log_dir` (no leading underscore); the cycle-0 spec/code symbol drift is resolved. |
| AC-2 (four hooks installed) | PASS | PASS | `install_crash_handlers` returns `CrashHandlerInstallation.installed_hooks == ("faulthandler", "sys.excepthook", "threading.excepthook", "qt.message_handler")`. Asserted by `test_install_crash_handlers_installs_all_four_hooks`. |
| AC-3 (log-path resolution) | PASS | PASS | `resolve_log_dir` is pure (no `os.environ` read), tested parametrically over Windows (with/without LOCALAPPDATA), Darwin, Linux (with/without XDG_STATE_HOME). No tempfile usage. Parametrize at `test_resolve_log_dir_branches`. |
| AC-4 (idempotent install) | PASS | PASS | Second call returns the same `CrashHandlerInstallation` instance and does not rebind process hooks. Asserted by `test_install_crash_handlers_is_idempotent`. |
| AC-5 (worker-thread exception captured) | PASS | PASS | `pipeline_worker.py` widens to `except BaseException` with explicit re-raise of `KeyboardInterrupt`/`SystemExit`; `logger.error(..., exc_info=True)` confirmed by `test_pipeline_worker_run_logs_traceback_on_exception`. Re-raise contract pinned by two additional tests. |
| AC-6 (cross-thread Qt mutation eliminated) | PASS | PASS | `ThreadedRunner.run` constructs `_RunnerReceiver(QObject)` on the calling thread, connects `worker.finished` / `worker.error` with `Qt.ConnectionType.QueuedConnection`. Thread-affinity probe asserts callbacks fire on the GUI thread. |
| AC-7 (Qt fatal routed to log) | PASS | PASS | `make_qt_message_handler` maps each `QtMsgType` to the documented `logging` level (`test_qt_message_handler_routes_categories_to_logging_levels`). |
| AC-8 (composition root wires the installer) | PASS | PASS | `src/gui/app.py` now calls `install_for_main()` (a thin wrapper around `install_crash_handlers(app_name="mix-calculator")`) exactly once before `QApplication([])`. The retargeted composition-root test (`test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`) asserts the single call and the ordering vs QApplication init. |
| AC-9 (toolchain green) | PASS | PASS | Phase 8 evidence: `black.md` EXIT_CODE 0, `ruff.md` 0, `pyright.md` 0, `pytest.md` 0 (737/737 passed). Single-pass summary present (`single-pass-summary.md`). No new suppressions added (verified via the git-diff scan; the R4 closure tests use `vars(...)` private access to avoid `# pyright: ignore` / `# noqa: B009`). |
| AC-10 (coverage non-regressing) | PARTIAL (informational) | **PASS** | Phase 8 `pytest.md` per-file: `_crash_handler.py` 100% line / 100% branch (up from 88% / 100%); `_crash_handler_bootstrap.py` 100% line; `runners.py` 100% / 100%; `pipeline_worker.py` 100% / 100%; `app.py` 99% / 92% (non-regressing; 1 line missed at unchanged line 314). Phase 9 `coverage-delta.md` records: repo-wide 99% line (improved); branch ~96.5%; per-file non-regression confirmed. The cycle-0 closure-body gap (lines 254-263, 290-303, 374-383) is closed by the three R4 tests. |
| AC-11 (no new dependency) | PASS | PASS | `git diff --name-only 0b353ad..e17da56 -- pyproject.toml poetry.lock` returns empty. |
| AC-12 (file-size cap) | FAIL | PARTIAL | AC text says "No **production file** in the diff exceeds 500 lines." All five production files are now under cap (`src/gui/app.py` 499; `_crash_handler.py` 495; `_crash_handler_bootstrap.py` 94; `runners.py` 270; `pipeline_worker.py` 116). **However**, the cross-cutting `general-code-change.md` 500-line cap explicitly applies to test code as well, and `tests/gui/test_crash_handler.py` is 549 lines after the R4 additions. AC-12 as written (production-only) is PASS; the broader policy is FAIL. Verdict recorded as PARTIAL to reflect that the AC text is technically satisfied while the cross-cutting policy is not. |

## Acceptance Criteria Check-off

The spec file already shows all 12 AC items as `[x]`. This reaudit re-evaluates against the cycle-1 diff and concludes:

- 11 items remain correctly `[x]` (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11). AC-1 and AC-10 transition from PARTIAL to PASS in this cycle.
- 1 item is PARTIAL (AC-12: the AC's production-only scope is satisfied; the cross-cutting `general-code-change.md` cap is violated by `tests/gui/test_crash_handler.py`).

Recommendation: leave AC-12 `[x]` on its literal text (production-file scope) but treat the F5 Blocking finding in `policy-audit.2026-05-31T03-25.md` as the remediation driver. The reviewer does not modify `spec.md` here; the cycle-2 remediation should split the test file as described in `remediation-inputs.2026-05-31T03-25.md`.

## Verification Procedure

For each AC the auditor:

1. Read the spec AC text verbatim from `spec.md` (refreshed with cycle-1 wording on AC-1, AC-10, AC-12).
2. Located the implementing code via the cycle-1 diff (`git diff --name-status 0b353ad..e17da56`).
3. Located the asserting test by file/function name.
4. For coverage and toolchain AC items, cross-checked the Phase 8 / Phase 9 evidence artifacts against repository policy thresholds.
5. For AC-12, ran `wc -l` and `awk 'END{print NR}'` on every production and test file modified or added on the branch.

## Bug-Fix Behavior Verification (Issue #46)

The bug is "GUI exits silently when SKU_LU import triggers a worker-thread fault". The branch addresses both structural causes identified in `artifacts/research/skulu-gui-crash-diagnosis.md`:

1. **Cross-thread Qt widget mutation** -> fixed by `_RunnerReceiver` + `Qt.ConnectionType.QueuedConnection` (AC-6, verified by thread-affinity probe test).
2. **No crash visibility** -> fixed by the four hooks (AC-2, AC-7) plus the per-user log directory (AC-3) plus the wider worker boundary with `exc_info=True` (AC-5).

The R4 cycle-1 additions further pin the on-disk traceback write path (`_make_sys_excepthook`, `_make_threading_excepthook`, `_append_traceback`) with three direct-invocation tests. The crash-write path is now fully covered (was 88% line / 100% branch; now 100% / 100%).

The remaining concern (test-file size cap) is a process/policy regression introduced by the R4 fixture, not a functional regression.

## Final Feature-Audit Verdict

**PARTIAL** — the bug-fix behavior is delivered and verified by tests; AC-9 / AC-11 are PASS; AC-1 and AC-10 transition from PARTIAL to PASS; the regression suite is green (737/737). AC-12 is PARTIAL because the cross-cutting `general-code-change.md` cap is exceeded by `tests/gui/test_crash_handler.py` (549 lines), even though the AC's literal production-only scope is satisfied. The feature cannot be marked complete until the test file is split.

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- Total AC items: 12
- Checked off (delivered and verified): 11 (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11)
- Remaining (audit verdict not PASS): 1
  - AC-12 (PARTIAL): production-file cap is satisfied; the cross-cutting `general-code-change.md` cap is violated by `tests/gui/test_crash_handler.py` (549 lines, NEW on this branch).
