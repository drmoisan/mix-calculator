# Phase 1 — test_crash_handler_closures.py Line Count (Post-Create)

- Timestamp: 2026-05-31T03-25
- Command:
  - `wc -l tests/gui/test_crash_handler_closures.py`
  - `awk 'END{print NR}' tests/gui/test_crash_handler_closures.py`
  - `pwsh -NoProfile -Command "(Get-Content tests/gui/test_crash_handler_closures.py).Count"`
- EXIT_CODE: 0
- Output Summary:
  - `wc -l`: 258
  - `awk NR`: 258
  - `(Get-Content).Count`: 258
  - All three counters agree exactly. 258 <= 500 (cap satisfied with 242 lines of headroom).
