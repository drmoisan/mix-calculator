# Remediation Baseline — test_crash_handler.py Line Count (Pre-Fix)

- Timestamp: 2026-05-31T03-25
- Command:
  - `wc -l tests/gui/test_crash_handler.py`
  - `awk 'END{print NR}' tests/gui/test_crash_handler.py`
  - `pwsh -NoProfile -Command "(Get-Content tests/gui/test_crash_handler.py).Count"`
- EXIT_CODE: 0
- Output Summary:
  - `wc -l`: 549
  - `awk NR`: 549
  - `(Get-Content).Count`: 549
  - All three counters agree exactly. The 549-line count matches the cycle-2 entry state cited in `remediation-inputs.2026-05-31T03-25.md`. Exceeds the 500-line cap by 49 lines, which is the R5 cycle-2 driver.
