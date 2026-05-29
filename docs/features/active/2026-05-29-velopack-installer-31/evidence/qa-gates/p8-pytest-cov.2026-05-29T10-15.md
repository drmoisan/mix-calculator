# Phase 8 — Final pytest + coverage

Timestamp: 2026-05-29T10-15

Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- 488 tests passed; 0 failed; 0 skipped.
- Total project coverage: 99% line (2225 statements, 16 missed; 348 branches, 3 partials).
- Per-file (key new and modified files):
  - `src/build_velopack.py`: 98% line (91 statements, 1 missed; 24 branches, 1 partial). Missing line 541 = defensive `raise RuntimeError` inside the upload-path token-None narrowing guard (unreachable in practice).
  - `src/gui/app.py`: 99% line (148 statements, 1 missed; 16 branches, 1 partial). Missing line 107 = defensive `raise RuntimeError` inside `_run_velopack_bootstrap` for an absent `velopack.App` attribute (also unreachable when velopack >= 1.0.1 is installed).
- AC15 satisfied: line coverage on `src/build_velopack.py` is 98% (>> 85%); branch coverage on `src/build_velopack.py` is ~95.8% (>> 75%).
- AC17 satisfied for Python: Black + Ruff + Pyright + Pytest all pass in a single loop pass with no auto-fix.
