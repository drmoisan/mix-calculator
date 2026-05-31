# Phase 1 — Fail-Before Evidence (Regression Tests)

Timestamp: 2026-05-30T22-58

## Commands run

1. `poetry run pytest tests/gui/test_crash_handler.py tests/gui/test_pipeline_worker.py tests/gui/test_runners_threaded.py tests/gui/test_app_composition.py`
   - EXIT_CODE: 2 (pytest collection error)
   - Output Summary: Collection halts on `ModuleNotFoundError: No module named 'src.gui._crash_handler'` in `tests/gui/test_crash_handler.py:41`. This is the expected fail-before signal for AC-1/AC-2/AC-3/AC-4/AC-7 because their tests all depend on importing the not-yet-created production module.

2. `poetry run pytest tests/gui/test_pipeline_worker.py tests/gui/test_runners_threaded.py tests/gui/test_app_composition.py` (collection-isolated run to enumerate the remaining new tests)
   - EXIT_CODE: 1
   - Output Summary: 5 failed, 14 passed.

## Per-test fail-before outcomes

| Test | File | Outcome | Fail-before AC |
|---|---|---|---|
| `test_module_exposes_documented_public_surface` | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-1 |
| `test_resolve_log_dir_branches` (5 params) | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-3 |
| `test_install_crash_handlers_installs_all_four_hooks` | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-2 |
| `test_install_crash_handlers_disabled_returns_noop` | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-2 (rollback contract) |
| `test_install_crash_handlers_is_idempotent` | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-4 |
| `test_qt_message_handler_routes_categories_to_logging_levels` | test_crash_handler.py | collection error (ModuleNotFoundError) | AC-7 |
| `test_pipeline_worker_run_logs_traceback_on_exception` | test_pipeline_worker.py | FAILED — `kwargs.get("exc_info")` is None (current logger.error is called without `exc_info=True`) | AC-5 |
| `test_pipeline_worker_run_reraises_keyboard_interrupt` | test_pipeline_worker.py | PASSED at baseline — `KeyboardInterrupt` already propagates because the current `except Exception` clause does not catch `BaseException`. This is a pin test that verifies the widening to `except BaseException` preserves the re-raise contract. | AC-5 (post-change invariant) |
| `test_pipeline_worker_run_reraises_system_exit` | test_pipeline_worker.py | PASSED at baseline — same rationale as KeyboardInterrupt. Pin test for the post-widening invariant. | AC-5 (post-change invariant) |
| `test_threaded_runner_success_callback_runs_on_gui_thread` | test_runners_threaded.py | FAILED — callback ran on `_DummyThread(Dummy-3, started daemon 36852)` (worker thread), not `_MainThread(MainThread, started 84936)`. | AC-6 |
| `test_threaded_runner_error_callback_runs_on_gui_thread` | test_runners_threaded.py | FAILED — error callback ran on worker thread, not GUI thread. | AC-6 |
| `test_threaded_runner_uses_queued_connection_for_finished_and_error` | test_runners_threaded.py | FAILED — `runner._receiver` is `None`; the AC-6 structural fingerprint (QObject receiver held on the runner) is absent. | AC-6 |
| `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` | test_app_composition.py | FAILED — `AttributeError: module 'src.gui.app' has no attribute 'install_crash_handlers'`. The composition root does not yet import the installer. | AC-8 |

Two re-raise tests (`KeyboardInterrupt` / `SystemExit`) PASS at baseline by accident: the current `except Exception` clause does not catch `BaseException` subclasses, so those exceptions propagate today. The widening to `except BaseException` with an explicit re-raise preserves the same observable behavior; these are pin tests rather than fail-before regression tests. The remaining seven new test functions and all six tests in `test_crash_handler.py` are genuine fail-before evidence.

All fourteen previously-passing GUI tests in the three pre-existing test files still pass; no regression on the existing suite.

Fail-before contract: every new test that requires production code that does not yet exist (AC-1..AC-8) is in the failed or collection-error set. The two `BaseException` re-raise pin tests pass at baseline by design and are documented above.
