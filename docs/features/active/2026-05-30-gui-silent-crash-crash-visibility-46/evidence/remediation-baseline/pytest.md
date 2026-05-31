# Remediation Baseline — Pytest with Coverage (Cycle 2)

- Timestamp: 2026-05-31T03-25
- Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
- EXIT_CODE: 0
- Output Summary:
  - Headline: **737 passed**, 1 warning in 22.53s
  - Total: 3656 statements, 20 missed, 660 branches, 23 partial -> **99% line coverage** (>= 85% policy)
  - Branch coverage: (660 - 23) / 660 ~= **96.5%** (>= 75% policy)
  - Per-file (key files):
    - `src/gui/_crash_handler.py` -> 99 stmts, 0 missed, 8 branches, 0 partial -> **100% line, 100% branch** (matches the cycle-1 post-R4 state)
    - `src/gui/_crash_handler_bootstrap.py` -> 6 stmts, 0 missed, 0 branches -> **100%**
    - `src/gui/runners.py` -> 46 stmts, 0 missed, 0 branches -> **100% line, 100% branch**
    - `src/gui/workers/pipeline_worker.py` -> 24 stmts, 0 missed, 2 branches, 0 partial -> **100% line, 100% branch**
  - Cycle-2 entry baseline confirmed: 737 collected, `_crash_handler.py` at 100% / 100%.
