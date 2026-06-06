# Baseline — Pytest + Coverage (Remediation Cycle 1)

Timestamp: 2026-06-05T20-28
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 922 passed, 3 warnings in ~22s; 0 failed.
- TOTAL coverage: statements 4534, missed 74, branches 832, partial 47.
- Line coverage: (4534-74)/4534 = 98.4% (>= 85% gate).
- Branch coverage: (832-47)/832 = 94.4% (>= 75% gate).
- Cycle-entry note: the orphaned modules show partial coverage where production wiring is missing — _columns_tab_drag.py 82%, _key_tab_drag.py 84%, _derived_formula_dialog.py 94%. Remediation adds integrated coverage for these seams.
