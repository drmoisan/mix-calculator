# Feature Audit — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 2

- **Timestamp:** 2026-05-31T03-52
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `b59bb3660ce9fa510a450d326f92ffd46a1776aa`
- **Prior audits:** `feature-audit.2026-05-31T02-43.md` (Cycle 0), `feature-audit.2026-05-31T03-25.md` (Cycle 1)
- **Work mode:** full-bug (AC source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`)
- **Total AC items:** 12 (AC-1 .. AC-12)

## Scope and Baseline

- **Baseline (merge-base):** `0b353adcd596ff450db5cfa7ca771ef22565e53a` (resolved against `main`).
- **Branch head:** `bug/gui-silent-crash-crash-visibility-46` at `b59bb3660ce9fa510a450d326f92ffd46a1776aa` (cycle-2 commit `b59bb36` on top of cycle-1 `e17da56` on top of cycle-0 `666e84a`).
- **AC source resolution (full-bug mode):** `spec.md` only; no `user-story.md` is required. Acceptance criteria are read verbatim from `## Acceptance Criteria` in `spec.md` (lines 200-227, AC-1..AC-12).
- **Scope invariant:** The audit scope is the full branch diff against the resolved base. The cycle-2 caller prompt reaffirmed this verbatim and did not attempt any narrowing.
- **Changed `.py` files in scope (10):** `src/gui/_crash_handler.py` (NEW), `src/gui/_crash_handler_bootstrap.py` (NEW in R1), `src/gui/app.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`, `tests/gui/test_app_composition.py`, `tests/gui/test_crash_handler.py` (NEW, post-R5 split), `tests/gui/test_crash_handler_closures.py` (NEW in R5), `tests/gui/test_pipeline_worker.py`, `tests/gui/test_runners_threaded.py`.

## Acceptance Criteria Inventory

| AC ID | One-line summary |
|---|---|
| AC-1 | Crash-handler module exists at `src/gui/_crash_handler.py` with `install_crash_handlers` and pure `resolve_log_dir`. |
| AC-2 | `install_crash_handlers` installs all four hooks (faulthandler, sys.excepthook, threading.excepthook, qInstallMessageHandler). |
| AC-3 | `resolve_log_dir` is pure with parametric tests for Windows / Darwin / Linux branches; no tempfile usage. |
| AC-4 | Second `install_crash_handlers` call is idempotent (no duplicate handler). |
| AC-5 | Worker-thread exceptions log a traceback with `exc_info=True`, emit `error` signal, surface a `QMessageBox` on the GUI thread. |
| AC-6 | `runners.py` no longer uses plain Python closures; signals route via `_RunnerReceiver` (QObject) with `Qt.ConnectionType.QueuedConnection`. |
| AC-7 | `qDebug`/`qWarning`/`qCritical`/`qFatal` are routed through Python `logging` at matching levels. |
| AC-8 | `app.py` calls `install_crash_handlers(app_name="mix-calculator")` exactly once before `QApplication`. |
| AC-9 | Full Python toolchain passes single-pass (black, ruff, pyright, pytest); no new suppressions. |
| AC-10 | Coverage non-regressing on `_crash_handler.py`, `runners.py`, `pipeline_worker.py`, `app.py` (>= 85% line / >= 75% branch). |
| AC-11 | No new dependency: `pyproject.toml` and `poetry.lock` are unchanged. |
| AC-12 | File-size cap: no production file in the diff exceeds 500 lines (and per `general-code-change.md` also applies to test code at cycle-2). |

## Summary

The cycle-2 R5 remediation cleared the sole Blocking finding from cycle 1. All 12 ACs now evaluate to PASS. The bug-fix behavior for issue #46 (silent SKU_LU GUI crash) is delivered and verified by tests: the four crash hooks are installed, the cross-thread Qt mutation is eliminated, the worker boundary logs tracebacks, the per-user log directory is resolved deterministically, and the composition root wires the installer exactly once. The cycle-2 split of `tests/gui/test_crash_handler.py` (549 -> 332) plus the new `tests/gui/test_crash_handler_closures.py` (258) brings test code into compliance with the cross-cutting 500-line cap defined in `.claude/rules/general-code-change.md`. The full Python toolchain passes single-pass (black, ruff, pyright, pytest at 737/737). `src/gui/_crash_handler.py` coverage stays at 100% line / 100% branch; repo-wide Python coverage is 99.5% line / 96.5% branch.

## Acceptance Criteria Evaluation

| AC | Cycle-0 verdict | Cycle-1 verdict | Cycle-2 verdict | Evidence |
|---|---|---|---|---|
| AC-1 (crash-handler module exists) | PARTIAL | PASS | **PASS** | `src/gui/_crash_handler.py` (495 lines), Pyright-clean, exports `install_crash_handlers`, `CrashHandlerInstallation`, and pure `resolve_log_dir`. `grep -nE 'except\s*:' src/gui/_crash_handler.py` returns no matches. Spec AC-1 uses `resolve_log_dir` (no leading underscore). |
| AC-2 (four hooks installed) | PASS | PASS | **PASS** | `install_crash_handlers` returns `CrashHandlerInstallation.installed_hooks == ("faulthandler", "sys.excepthook", "threading.excepthook", "qt.message_handler")`. Asserted by `test_install_crash_handlers_installs_all_four_hooks` (retained in `tests/gui/test_crash_handler.py`). |
| AC-3 (log-path resolution) | PASS | PASS | **PASS** | `resolve_log_dir` is pure; parametrized over Windows (with/without LOCALAPPDATA), Darwin, Linux (with/without XDG_STATE_HOME); no `tempfile` usage. Test `test_resolve_log_dir_branches` in `tests/gui/test_crash_handler.py`. |
| AC-4 (idempotent install) | PASS | PASS | **PASS** | Second call returns the same `CrashHandlerInstallation`; process-wide hooks not re-bound. Asserted by `test_install_crash_handlers_is_idempotent`. |
| AC-5 (worker-thread exception captured) | PASS | PASS | **PASS** | `pipeline_worker.py` uses `except BaseException` with explicit re-raise of `KeyboardInterrupt`/`SystemExit`; `logger.error(..., exc_info=True)` confirmed by `test_pipeline_worker_run_logs_traceback_on_exception`. Re-raise contract pinned by two additional tests. |
| AC-6 (cross-thread Qt mutation eliminated) | PASS | PASS | **PASS** | `ThreadedRunner.run` uses `_RunnerReceiver(QObject)` + `Qt.ConnectionType.QueuedConnection`. Thread-affinity probe in `tests/gui/test_runners_threaded.py` asserts callbacks fire on the GUI thread. |
| AC-7 (Qt fatal routed to log) | PASS | PASS | **PASS** | `make_qt_message_handler` maps each `QtMsgType` to the documented `logging` level. Asserted by `test_qt_message_handler_routes_categories_to_logging_levels` (retained in `tests/gui/test_crash_handler.py`). |
| AC-8 (composition root wires the installer) | PASS | PASS | **PASS** | `src/gui/app.py` calls `install_for_main()` exactly once before `QApplication`. Asserted by `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`. |
| AC-9 (toolchain green) | PASS | PASS | **PASS** | Cycle-2 phase-4 evidence: `black.md` EXIT 0, `ruff.md` 0, `pyright.md` 0, `pytest.md` 0 (737 passed). `single-pass-summary.md` records `Single-Pass Result: PASS`. No new suppressions added across the entire branch diff (`grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'` returns no `^+` matches against base). |
| AC-10 (coverage non-regressing) | PARTIAL | PASS | **PASS** | `_crash_handler.py` 100% line / 100% branch (lcov: LF=99 LH=99 BRF=8 BRH=8); `_crash_handler_bootstrap.py` 100%; `runners.py` 100%/100%; `pipeline_worker.py` 100%/100% (LF=24 LH=24 BRF=2 BRH=2); `app.py` 99%/92% (LF=137 LH=136 BRF=12 BRH=11). Repo-wide 99.5% line / 96.5% branch. No regression versus cycle-1 post-state. |
| AC-11 (no new dependency) | PASS | PASS | **PASS** | `git diff --name-only 0b353ad..b59bb36 -- pyproject.toml poetry.lock` returns empty. |
| AC-12 (file-size cap) | FAIL | PARTIAL | **PASS** | All five production files under cap (`_crash_handler.py` 495, `_crash_handler_bootstrap.py` 94, `runners.py` 270, `pipeline_worker.py` 116, `app.py` 499). Cycle-2 R5 split also brings test code into compliance with the cross-cutting cap in `.claude/rules/general-code-change.md`: `tests/gui/test_crash_handler.py` 332 (was 549); `tests/gui/test_crash_handler_closures.py` 258 (NEW); `tests/gui/test_app_composition.py` 480; `tests/gui/test_pipeline_worker.py` 244; `tests/gui/test_runners_threaded.py` 151. AC-12 spec text (production-only) is satisfied; cross-cutting policy is also satisfied. |

## Acceptance Criteria Check-off

The spec file already shows all 12 AC items as `[x]`. This reaudit re-evaluates against the cycle-2 diff and concludes:

- 12 of 12 AC items are correctly `[x]`. AC-12 transitions from PARTIAL (cycle 1) to PASS in this cycle because the R5 split also brings test code into compliance with the cross-cutting 500-line cap.
- 0 of 12 items remain at PARTIAL / FAIL / UNVERIFIED.

No spec change is required for this cycle; `spec.md` already shows AC-12 `[x]` with cycle-2 notes recording the test-file split.

## Verification Procedure

For each AC the auditor:

1. Read the spec AC text verbatim from `spec.md` (cycle-2 wording on AC-1, AC-10, AC-12).
2. Located the implementing code via the branch diff (`git diff --name-status 0b353ad..b59bb36`).
3. Located the asserting test by file/function name. For tests relocated by R5, confirmed the new location in `tests/gui/test_crash_handler_closures.py` (`grep -nE "^def test_(sys_excepthook_appends|threading_excepthook_appends|append_traceback_swallows_oserror)" tests/gui/test_crash_handler_closures.py` -> lines 144, 182, 220).
4. For coverage and toolchain AC items, cross-checked `artifacts/python/lcov.info` and the regenerated Phase 8 evidence artifacts against repository policy thresholds.
5. For AC-12, ran `wc -l` and `awk 'END{print NR}'` on every production and test file modified or added on the branch and confirmed each is under 500.

## Bug-Fix Behavior Verification (Issue #46)

The bug is "GUI exits silently when SKU_LU import triggers a worker-thread fault." The branch addresses both structural causes identified in `artifacts/research/skulu-gui-crash-diagnosis.md`:

1. **Cross-thread Qt widget mutation** -> fixed by `_RunnerReceiver` + `Qt.ConnectionType.QueuedConnection` (AC-6, verified by thread-affinity probe test in `tests/gui/test_runners_threaded.py`).
2. **No crash visibility** -> fixed by the four hooks (AC-2, AC-7) plus the per-user log directory (AC-3) plus the wider worker boundary with `exc_info=True` (AC-5).

The R4 cycle-1 additions (three direct-invocation closure tests) pin the on-disk traceback write path (`_make_sys_excepthook`, `_make_threading_excepthook`, `_append_traceback`). The cycle-2 R5 split relocates those three tests and their fixtures into `tests/gui/test_crash_handler_closures.py` without changing the assertions, the seam, or the coverage profile. The crash-write path remains fully covered (100% line / 100% branch).

The cycle-1 process/policy regression (test-file size cap) is now also remediated. There are no remaining policy or functional gaps relative to the spec.

## Final Feature-Audit Verdict

**PASS** — the bug-fix behavior is delivered and verified by tests; all 12 ACs are PASS; the regression suite is green (737/737); coverage on the four changed production files and the new module is at or above the repo thresholds; the cross-cutting 500-line cap is satisfied on production and test code alike; no new dependencies and no new suppression markers were introduced on the branch.

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- Total AC items: 12
- Checked off (delivered and verified): 12 (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12)
- Remaining (audit verdict not PASS): 0
- Items remaining: none
