# Phase 5 — Pass-After Evidence (Regression Tests)

Timestamp: 2026-05-30T23-27

Command: `poetry run pytest tests/gui/test_crash_handler.py tests/gui/test_pipeline_worker.py tests/gui/test_runners_threaded.py tests/gui/test_app_composition.py`

EXIT_CODE: 0

Output Summary: 29 tests passed in 0.78s. All previously-failing regression tests authored in Phase 1 now pass after the production changes in Phases 2-4. The cross-reference to `evidence/regression-testing/phase1-fail-before.md` is preserved per the plan.

## Per-test pass-after status (mirrors fail-before table)

| Test | Phase 1 fail-before | Phase 5 pass-after |
|---|---|---|
| `test_module_exposes_documented_public_surface` (test_crash_handler.py) | collection error (no module) | PASSED |
| `test_resolve_log_dir_branches` (5 params, test_crash_handler.py) | collection error (no module) | PASSED (5/5 params) |
| `test_install_crash_handlers_installs_all_four_hooks` (test_crash_handler.py) | collection error (no module) | PASSED |
| `test_install_crash_handlers_disabled_returns_noop` (test_crash_handler.py) | collection error (no module) | PASSED |
| `test_install_crash_handlers_is_idempotent` (test_crash_handler.py) | collection error (no module) | PASSED |
| `test_qt_message_handler_routes_categories_to_logging_levels` (test_crash_handler.py) | collection error (no module) | PASSED |
| `test_pipeline_worker_run_logs_traceback_on_exception` (test_pipeline_worker.py) | FAILED (no exc_info=True) | PASSED |
| `test_pipeline_worker_run_reraises_keyboard_interrupt` (test_pipeline_worker.py) | PASSED at baseline (pin) | PASSED (contract preserved) |
| `test_pipeline_worker_run_reraises_system_exit` (test_pipeline_worker.py) | PASSED at baseline (pin) | PASSED (contract preserved) |
| `test_threaded_runner_success_callback_runs_on_gui_thread` (test_runners_threaded.py) | FAILED (ran on worker thread) | PASSED |
| `test_threaded_runner_error_callback_runs_on_gui_thread` (test_runners_threaded.py) | FAILED (ran on worker thread) | PASSED |
| `test_threaded_runner_uses_queued_connection_for_finished_and_error` (test_runners_threaded.py) | FAILED (no `_receiver`) | PASSED |
| `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` (test_app_composition.py) | FAILED (no installer import) | PASSED |

Reference: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/regression-testing/phase1-fail-before.md`.
