# Phase 7 QA Gate

Phase 7 — PipelinePresenter and ExportPresenter. Single clean pass of the toolchain loop.

## Black
Timestamp: 2026-05-27T20-59
Command: poetry run black .
EXIT_CODE: 0
Output Summary: Pass. 67 files left unchanged (after reformat restarts).

## Ruff
Timestamp: 2026-05-27T20-59
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: Pass. "All checks passed!" — 0 errors.

## Pyright
Timestamp: 2026-05-27T20-59
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: Pass. 0 errors, 0 warnings, 0 informations (strict). No new Any. `make_run_task`
returns a typed `Callable[[], dict[str, pd.DataFrame]]`. Negative-flow fakes use configurable
fields (`raise_on_import`, `import_calls`) rather than method assignment, avoiding suppressions.

## Pytest (coverage)
Timestamp: 2026-05-27T20-59
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 252 passed (226 prior + 26 new), 0 failed. Determinism confirmed across 2 runs.
- `src/gui/presenters/pipeline_presenter.py`: 100% line, 100% branch.
- `src/gui/presenters/export_presenter.py`: 100% line, 100% branch.
- Repository TOTAL: 100% line, 100% branch. Gate satisfied.
- No regression on changed lines.

## Notes
- `quality-tiers.yml`: added `src/gui/presenters/pipeline_presenter.py: T2`,
  `src/gui/presenters/export_presenter.py: T2`.
- PipelinePresenter guards Run until imports/open complete; routes service ValueError to show_error;
  exposes the Run task as a plain callable for the Phase 8 worker.
- ExportPresenter rejects an empty selection before any exporter call; an unknown format raises a
  registry KeyError before reading the selection.
- T2 property tests (hypothesis): run-summary count invariant; export-all selects exactly available names.
- Confidentiality: fabricated values only.
