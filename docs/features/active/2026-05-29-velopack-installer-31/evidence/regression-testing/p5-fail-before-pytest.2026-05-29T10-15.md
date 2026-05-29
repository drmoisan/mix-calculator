# Phase 5 — Fail-before pytest evidence [expect-fail]

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest tests/gui/test_app_composition.py -x`

EXIT_CODE: 1

Output Summary:
- 1 failed, 4 passed.
- The failing test is `test_main_entry_point_runs_event_loop`. The assertion `events == ["velopack_run", "qapplication_init"]` fails because `main()` does not yet call `velopack.App().run()` — the actual recorded events list is `["qapplication_init"]` only.
- This is the expected fail-before signal for Phase 5; the sibling new test `test_main_calls_velopack_app_run_before_qapplication` is also expected to fail once reached, for the same reason. Pytest stopped at the first failure per `-x`.
