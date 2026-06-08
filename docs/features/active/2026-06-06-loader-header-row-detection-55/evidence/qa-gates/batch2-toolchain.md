# Phase 2 — Batch 2 Toolchain Gate (Issue #55)

Timestamp: 2026-06-07T02-36

Run in order; the loop restarted once from Black after Ruff auto-fixed an import
ordering and Black reformatted one line in `src/normalize_le.py`. The recorded
results are the final single clean pass.

## Black
Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: 230 files left unchanged (clean, no files reformatted on the final pass).

## Ruff
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 lint errors.

## Pyright
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (Batch 2 loader modules, coverage)
Command: `poetry run pytest tests/test_normalize_le.py tests/test_load_aop.py --cov=src.normalize_le --cov=src.load_aop --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 53 passed, 0 failed.
- Module-scoped coverage in this run (loader test files only):
  - `src/normalize_le.py` — 47% line (CLI `main`/`print_summary`/`validate_tieouts`
    paths live in `test_normalize_le_io.py`/`test_normalize_le_totals.py`, excluded here).
  - `src/load_aop.py` — 66% line (CLI/persist/summary paths live in
    `test_load_aop_io.py`, excluded here).
  - These scoped numbers reflect only the two named loader test files; both
    modules are 100% under the full suite (baseline) and are re-measured at P4-T4.
- A separate run including the new flat-sheet sibling files
  (`tests/test_normalize_le_header.py`, `tests/test_load_aop_header.py`) reports
  57 passed, exercising the header-detection integration (header at index 0 and
  index-0/index-2 parity) for both loaders.
- All four stages passed in the final single pass.
