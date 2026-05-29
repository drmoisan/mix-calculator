# Baseline — Pyright

- Timestamp: 2026-05-29T00-00
- Command: `poetry run pyright`
- EXIT_CODE: 0
- Output Summary: PASS — `0 errors, 0 warnings, 0 informations`.

Note: An initial baseline attempt produced 5038 errors because Poetry dependencies had not been installed into the project venv (`pandas`, `openpyxl`, `pyside6` were absent). `poetry install` was executed once before this baseline run to restore the dev environment; the install only resynced declared dependencies and did not change any tracked file.
