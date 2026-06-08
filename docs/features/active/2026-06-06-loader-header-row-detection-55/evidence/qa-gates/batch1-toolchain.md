# Phase 1 — Batch 1 Toolchain Gate (Issue #55)

Timestamp: 2026-06-07T02-36

Run in order; the loop restarted from Black once after a pyright invariance
finding on the test helper was fixed (list[list[object]] -> Sequence[Sequence[object]]
with per-row list() materialization for openpyxl append). The recorded results
are the final single clean pass.

## Black
Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: 228 files left unchanged (clean, no files reformatted on the final pass).

## Ruff
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 lint errors.

## Pyright
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (Batch 1 modules, coverage)
Command: `poetry run pytest tests/test_header_detection.py --cov=src._header_detection --cov=src.pandas_io --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 6 passed, 0 failed.
- `src/_header_detection.py` — 97% line (24 stmts, 0 missed, 8 branch, 1 partial:
  the `_rewind_if_seekable` path/non-seekable branch `69->exit`, exercised by the
  full suite via the loader integration in Phase 2/4).
- `src/pandas_io.py` — 60% line in this isolated module-scoped run because
  `read_table`/`write_table` are not exercised by this test file; both are at
  100% under the full suite (baseline) and are re-measured at P4-T4.
- All four stages passed in the final single pass.
