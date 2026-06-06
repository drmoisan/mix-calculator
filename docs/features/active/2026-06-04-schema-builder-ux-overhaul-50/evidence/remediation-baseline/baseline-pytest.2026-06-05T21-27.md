# Baseline — Pytest with Coverage (Cycle 2)

Timestamp: 2026-06-05T21-27
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Result: 932 passed, 0 failed, 3 warnings in ~22.8s.
- TOTAL coverage row: 4671 statements, 62 missed, 850 branches, 51 partial branches.
- Line coverage (statements): (4671 - 62) / 4671 = 98.67% (>= 85% threshold).
- Branch coverage: (850 - 51) / 850 = 93.99% (>= 75% threshold).
- Combined reported total: 98%.
- Per-file coverage for the two N4 target modules (0% — TYPE_CHECKING-only Protocol
  contracts, no runtime execution):
  - src/gui/_columns_tab_protocol.py: 10 statements, 10 missed, 0 branches, 0%
    (missing lines 19-111).
  - src/gui/_key_tab_protocol.py: 8 statements, 8 missed, 0 branches, 0%
    (missing lines 17-75).
