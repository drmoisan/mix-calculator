# Phase 5 QA Gate

Phase 5 — Concrete Exporters (Excel, CSV). Single clean pass of the full toolchain loop.

## Black
Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 58 files left unchanged (after loop restarts for reformatting/lint fixes).

## Ruff
Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors. (TC002 on csv_exporter pandas import and
an import-sort fix were resolved during the loop; final pass clean.)

## Pyright
Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any. The Excel/CSV
exporters wrap pandas to_excel/to_csv via typed Protocol views + cast (the pandas_io pattern),
so no per-call suppression. (Resolved a reportPrivateUsage by testing the default sink through the
public CsvExporter rather than the private factory.)

## Pytest (coverage)
Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 217 passed (210 prior + 7 new), 0 failed. Determinism confirmed across 2 runs.
- `src/gui/exporters/excel_exporter.py`: 100% line, 100% branch.
- `src/gui/exporters/csv_exporter.py`: 100% line, 100% branch.
- Repository TOTAL: 99% line, 100% branch. Gate satisfied (>= 85% line, >= 75% branch).
- No regression on changed lines.

## Notes
- `quality-tiers.yml`: added `src/gui/exporters/excel_exporter.py: T3`, `src/gui/exporters/csv_exporter.py: T3`.
- CSV exporter test uses an injected in-memory StringIO write seam; no temp files created.
- Excel exporter test reads sheets back via the typed `src.pandas_io.read_excel_sheet` and enumerates
  sheets via openpyxl; cross-format dtype coercion handled with `check_dtype=False`.
- Confidentiality: fabricated values only.
