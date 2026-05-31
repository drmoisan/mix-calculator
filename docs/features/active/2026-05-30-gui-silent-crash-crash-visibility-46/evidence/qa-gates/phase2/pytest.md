# Phase 2 — Pytest (Remediation Cycle 1, Post-R1)

Timestamp: 2026-05-31T02-43

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- 734 passed, 0 failed, 1 warning in 23.63s
- Total: 3656 statements, 33 missed, 660 branches, 23 partial -> **99% line coverage**
- Branch coverage: (660 - 23) / 660 ~= **96.5%** (policy line >= 85%, branch >= 75%)
- Per-file (changed files post-R1):
  - `src/gui/app.py` -> 137 stmts, 1 missed, 12 branches, 1 partial -> **99% line**
  - `src/gui/_crash_handler_bootstrap.py` -> 6 stmts, 0 missed, 0 branches -> **100% line** (covered by `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`)
  - `src/gui/_crash_handler.py` -> 99 stmts, 13 missed, 8 branches, 0 partial -> 88% line (R4 in Phase 4 will improve this)
  - `src/gui/runners.py` -> 46 stmts, 0 missed -> 100% / 100%
  - `src/gui/workers/pipeline_worker.py` -> 24 stmts, 0 missed -> 100% / 100%
- Composition-root test retarget (`test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`) passes: patch site moved from `app_module.install_crash_handlers` to `crash_bootstrap_module.install_crash_handlers`; recorder still captures exactly one call with `app_name="mix-calculator"` and ordering invariant (`install_crash_handlers` before `qapplication_init`) holds.
- Single-pass loop result: clean. black -> ruff -> pyright -> pytest all green in this iteration.
