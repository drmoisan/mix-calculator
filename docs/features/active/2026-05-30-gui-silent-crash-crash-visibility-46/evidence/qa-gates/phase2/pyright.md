# Phase 2 — Pyright (Remediation Cycle 1, Post-R1)

Timestamp: 2026-05-31T02-43

Command: `poetry run pyright`

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations.

Iteration history during Phase 2 remediation:
1. First run flagged `_INSTALLATION` (uppercase) as `reportConstantRedefinition` because the module-level anchor was reassigned inside `install_for_main`.
2. Renamed the module-level anchor to `_installation` (lowercase) in `src/gui/_crash_handler_bootstrap.py`; ran black + ruff (clean); re-ran pyright; zero findings.
