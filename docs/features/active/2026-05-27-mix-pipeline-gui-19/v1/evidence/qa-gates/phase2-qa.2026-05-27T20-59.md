# Phase 2 QA Gate

Phase 2 — PipelineService (ImportSpec + import/run + Protocol).
Single clean pass of the full toolchain loop.

## Black

Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 43 files left unchanged (after an initial reformat of one signature line
in `pipeline_service.py`, the loop was restarted and Black is now a no-op).

## Ruff

Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors.

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
- Tests: 192 passed (185 prior + 7 new), 0 failed. Determinism confirmed across 2 clean runs.
- `src/gui/pipeline_service.py`: 100% line, 100% branch.
- `src/gui/protocols.py`: 0% (interface-only, not yet imported by a test; covered in later phases).
- Repository TOTAL: 98% line, 100% branch. Gate satisfied (>= 85% line, >= 75% branch).
- No regression on changed lines.

## Notes

- `quality-tiers.yml`: added `src/gui/pipeline_service.py: T2`.
- `PipelineService` reuses the existing loaders and transforms; no transform logic re-implemented.
- `save_to_db`/`open_db` are declared on `PipelineServiceProtocol`; the concrete delegation to
  `DbService` is added in Phase 3 (P3-T2) per the plan.
- Confidentiality: fabricated values only (Acme Foods, SKU-001/002, Widget A/B, Category X/Y).
