# Phase 2 — Pyright

Timestamp: 2026-05-30T23-12

Command: `poetry run pyright`

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations.

Iteration history (toolchain restarts during Phase 2):
1. Initial pyright run reported 34 errors in `tests/gui/test_crash_handler.py` (Unknown lambdas, private-usage warnings on `_reset_for_tests`/`_get_state_for_tests`/`_make_qt_message_handler`/`_resolve_log_dir`).
2. Refactor: renamed test-accessible helpers to non-underscore names (`resolve_log_dir`, `make_qt_message_handler`, `reset_for_tests`) and added them to `__all__`. Removed `_get_state_for_tests` (redundant given the public idempotency assertion). Replaced lambdas with typed module-level no-op functions.
3. After refactor, pyright reported 3 production errors in `_crash_handler.py`: `threading.excepthook` return type is `object` (not `None`), and `ExceptHookArgs.exc_value` is `BaseException | None`. Fixed by updating callable types and adding a None-handling branch with a synthetic placeholder.
4. Final pyright run: 0 errors, 0 warnings, 0 informations.
