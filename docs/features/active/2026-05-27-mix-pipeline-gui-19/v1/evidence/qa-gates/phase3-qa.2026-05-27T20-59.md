# Phase 3 QA Gate

Phase 3 — Boundary Services (WorkbookReader, DbService + save_to_db/open_db).
Single clean pass of the full toolchain loop.

## Black

Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 48 files left unchanged.

## Ruff

Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors. (An import-ordering issue was
auto-fixed during the loop; the loop was restarted and Ruff is now clean with no changes.)

## Pyright

Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any.

## Pytest (coverage)

Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 205 passed (192 prior + 13 new across workbook_reader/db_service/pipeline_service), 0 failed.
  Determinism confirmed across 2 clean runs.
- `src/gui/services/workbook_reader.py`: 100% line, 100% branch.
- `src/gui/services/db_service.py`: 100% line, 100% branch.
- `src/gui/pipeline_service.py`: 100% line (save_to_db/open_db delegation now covered).
- `src/gui/protocols.py`: 0% (interface-only, covered in later phases).
- Repository TOTAL: 99% line, 100% branch. Gate satisfied (>= 85% line, >= 75% branch).
- No regression on changed lines.

## Notes

- `quality-tiers.yml`: added `src/gui/services/__init__.py: T4`, `src/gui/services/workbook_reader.py: T3`,
  `src/gui/services/db_service.py: T3`.
- `DbService` routes all SQLite reads/writes through `src.pandas_io` (no per-call type suppression).
- `PipelineService.save_to_db`/`open_db` now delegate to the constructor-injected `DbService`.
- Invalid-workbook negative flow asserts the specific `zipfile.BadZipFile` (an .xlsx is a zip
  container), avoiding a blind-except assertion.
- Confidentiality: fabricated values only.
