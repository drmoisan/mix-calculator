# Remediation Baseline — Pytest with Coverage

- Timestamp: 2026-05-31T02-43
- Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
- EXIT_CODE: 0
- Output Summary:
  - 734 passed, 0 failed, 1 warning in 23.65s
  - Total: 3651 statements, 33 missed, 660 branches, 23 partial -> 99% line coverage
  - Branch coverage: derived from totals: (660 - 23) / 660 ~= 96.5% (meets policy: line >= 85%, branch >= 75%)
  - Per-file (changed files):
    - `src/gui/_crash_handler.py` -> 99 stmts, 13 missed, 8 branches, 0 partial -> **88%** line, missing lines 254-263, 290-303, 374-383 (closure bodies and `_append_traceback`; R4 addresses these)
    - `src/gui/runners.py` -> 46 stmts, 0 missed -> **100%** line, **100%** branch
    - `src/gui/workers/pipeline_worker.py` -> 24 stmts, 0 missed, 2 branches, 0 partial -> **100%** line, **100%** branch
    - `src/gui/app.py` -> 138 stmts, 1 missed, 12 branches, 1 partial -> **99%** line, ~92% branch (missing line 314)
  - Note: Required restoration of working-tree-deleted `packaging/velopack/icon.ico` via `git checkout -- packaging/velopack/icon.ico` to enable 49 GUI tests that depend on the application icon. This file was tracked in git but uncommitted-deleted locally; the deletion was outside the scope of issue #46 and unrelated to R1-R4. No code change.
