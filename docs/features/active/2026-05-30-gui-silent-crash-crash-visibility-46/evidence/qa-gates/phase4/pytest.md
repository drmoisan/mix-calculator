# Phase 4 — Pytest with Coverage

- Timestamp: 2026-05-31T03-25
- Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
- EXIT_CODE: 0
- Output Summary:
  - Headline: **737 passed**, 1 warning in 22.62s (unchanged total versus the cycle-2 entry baseline of 737).
  - Total: 3656 statements, 20 missed, 660 branches, 23 partial -> **99% line coverage** (>= 85% policy floor).
  - Branch coverage: (660 - 23) / 660 ~= **96.5%** (>= 75% policy floor).
  - Per-file (key files):
    - `src/gui/_crash_handler.py` -> 99 stmts, 0 missed, 8 branches, 0 partial -> **100% line, 100% branch** (no regression versus the cycle-1 post-state captured in `evidence/qa-gates/phase8/pytest.md`).
    - `src/gui/_crash_handler_bootstrap.py` -> 6 stmts, 0 missed, 0 branches -> **100%**.
  - Collected from `tests/gui/test_crash_handler.py`: 10 tests (cycle-2 entry had 13; 3 relocated to the new file). All 10 PASSED.
  - Collected from `tests/gui/test_crash_handler_closures.py` (NEW): 3 tests. All 3 PASSED. These are the three R4 closure-invocation tests relocated from the original file:
    - `test_sys_excepthook_appends_traceback_record`
    - `test_threading_excepthook_appends_traceback_record`
    - `test_append_traceback_swallows_oserror`
  - Cycle-2 R5 split is behaviorally invariant: 10 + 3 = 13 (matches the original count), total suite count unchanged at 737, `_crash_handler.py` coverage unchanged at 100% / 100%.
