# Phase 4 Gate — Schema-Builder Carries in_output End-to-End

## Black
Timestamp: 2026-06-06T15-48
Command: env -u VIRTUAL_ENV poetry run black .
EXIT_CODE: 0
Output Summary: After an initial reformat of 2 files (multi-line annotations), the loop
restarted and black reports 226 files left unchanged.

## Ruff
Timestamp: 2026-06-06T15-48
Command: env -u VIRTUAL_ENV poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings.

## Pyright
Timestamp: 2026-06-06T15-48
Command: env -u VIRTUAL_ENV poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. Repo-wide clean after the 4-tuple
-> 5-tuple column-row migration (all unpack/annotation sites updated, including
set_columns/get_columns signatures in the three view/widget files).

## Pytest (coverage)
Timestamp: 2026-06-06T15-48
Command: env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 966 passed, 3 warnings (3 new builder tests added vs Phase 3: real-bundled-LE optional
  split + 2 assemble_schema in_output forwarding tests).
- TOTAL: Stmts=4725, Miss=44, Branch=872, BrPart=51, combined Cover 98%.
- Line coverage: (4725-44)/4725 = 99.07%; Branch: (872-51)/872 = 94.15%.
- All in-scope files <= 500 lines (largest: schema_builder_dialog.py at 493).
- P4-T5 note: src/gui/_schema_provider_factory.py required NO code change; its split
  already keys on column.required, so bundled LE YTD/YTG (required:false) lands in the
  optional specs as required by AC-7.
