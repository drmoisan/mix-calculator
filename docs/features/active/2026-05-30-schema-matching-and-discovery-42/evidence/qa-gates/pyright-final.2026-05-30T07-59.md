# Final QA — Pyright (strict) type check

Timestamp: 2026-05-30T07-59
Command: `poetry run pyright`
EXIT_CODE: 0

Output Summary:
- 0 errors, 0 warnings, 0 informations.
- No `reportPrivateUsage` for `src/etl_column_probe.py` (the private resolver
  helper is reimplemented locally, not imported across modules).
- No new errors relative to the P0-T4 baseline (baseline was 0 errors).
- New modules (`src/etl_column_probe.py`, `src/schema_matching.py`,
  `src/_schema_matching_helpers.py`) are fully type-annotated and Pyright-clean.
