# Phase 3 — Pytest (runners)

Timestamp: 2026-05-30T23-22

Command: `poetry run pytest tests/gui/test_runners.py tests/gui/test_runners_threaded.py`

EXIT_CODE: 0

Output Summary: 8 tests passed in 0.53s.

Per-test outcomes:
- test_synchronous_runner_success_routes_to_on_success — PASSED
- test_synchronous_runner_value_error_routes_to_on_error — PASSED
- test_synchronous_runner_non_value_error_routes_to_on_error — PASSED
- test_threaded_runner_implements_runner_protocol — PASSED
- test_synchronous_runner_implements_runner_protocol — PASSED
- test_threaded_runner_success_callback_runs_on_gui_thread — PASSED (was FAILED at fail-before; AC-6 satisfied)
- test_threaded_runner_error_callback_runs_on_gui_thread — PASSED (was FAILED at fail-before; AC-6 satisfied)
- test_threaded_runner_uses_queued_connection_for_finished_and_error — PASSED (was FAILED at fail-before; AC-6 structural fingerprint satisfied)

Iteration note: an interim pytest run hung on the third test because the ThreadedRunner's QThread had no clean join. Added `_join_runner_thread(runner)` helper that calls `thread.wait(5000)` after the queued callback fires; each test now joins the worker thread before returning.

AC coverage: AC-6.
