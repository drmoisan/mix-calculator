# Phase 7 — pytest smoke

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest -x`

EXIT_CODE: 0

Output Summary: 488 tests passed; 0 failed. No regression versus the Phase 4 smoke (487 passed). The +1 delta is the new ordering test `test_main_calls_velopack_app_run_before_qapplication` added in Phase 5; the asset additions in Phase 7 do not affect any test.
