# Phase 4 — Pytest (Post-R4)

- Timestamp: 2026-05-31T02-43
- Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
- EXIT_CODE: 0
- Output Summary:
  - **737 passed**, 0 failed, 1 warning in 23.13s (baseline was 734; three new tests added by R4)
  - Total: 3656 statements, 20 missed, 660 branches, 23 partial -> **99% line coverage** (baseline was 33 missed; -13 missed lines from R4 alone)
  - Branch coverage: (660 - 23) / 660 ~= **96.5%**
  - Per-file (post-R4):
    - `src/gui/_crash_handler.py` -> 99 stmts, **0** missed, 8 branches, 0 partial -> **100% line, 100% branch** (baseline was 88% line with missing lines 254-263, 290-303, 374-383). All three previously-uncovered closure bodies are now exercised by the new direct-invocation tests; R4 acceptance criteria met.
    - `src/gui/_crash_handler_bootstrap.py` -> 6 stmts, 0 missed -> **100% line**
  - The three new tests in `tests/gui/test_crash_handler.py`:
    - `test_sys_excepthook_appends_traceback_record` — exercises `_make_sys_excepthook` closure body and `_append_traceback`; in-memory sink via `_FakePath` (no temp files).
    - `test_threading_excepthook_appends_traceback_record` — exercises `_make_threading_excepthook` closure body with a synthesized `threading.ExceptHookArgs` and a named worker thread; in-memory sink.
    - `test_append_traceback_swallows_oserror` — exercises the `OSError` catch branch in `_append_traceback` via a `_RaisingPath` wrapper whose `.open` raises `OSError`; `caplog` captures the `Failed to append crash record` log line.
  - Single-pass loop result: clean. black -> ruff -> pyright -> pytest all green in this iteration (after the one-shot black reformatting of the new test additions and the one-shot pyright fix to widen the wrapper's return type).
