# Phase 2 QA — Toolchain Loop

## Black

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run black .`
EXIT_CODE: 0
Output Summary: 105 files left unchanged.

## Ruff

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 errors.

## Pyright

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. The production seam
`PipelinePresenter.set_imported_tables_for_test` was removed and no caller
remains anywhere under `src/` or `tests/` (verified by `grep -rn` returning
no matches).

## Pytest with coverage

Timestamp: 2026-05-28T23-20
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 417 passed in 21.64s; 0 failed.
- Line coverage (TOTAL): 99% (1954 statements, 14 missed). Statement count
  dropped by 2 versus Phase 1 because the removed `set_imported_tables_for_test`
  body is no longer counted.
- Branch coverage (TOTAL): 99% (296 branches, 2 partial).
- `src/gui/presenters/pipeline_presenter.py`: 99% line / 95% branch (one
  uncovered line at 166 — same uncovered-branch fingerprint as baseline; no
  regression introduced).
- File line-count check: `src/gui/presenters/pipeline_presenter.py` is 486
  lines (under the 500-line cap). `tests/gui/integration/test_behavioral_dialogs.py`
  is 222 lines. `tests/gui/integration/test_behavioral_pipeline_run.py` is 98 lines.
- `grep -rn "set_imported_tables_for_test" src tests` returns no matches.
- `git status` after the pytest run still shows the three untracked
  `results_*.csv` artifacts at the repo root because the CSV behavioral test
  (line 156 in `test_behavioral_dialogs.py`) was migrated for its
  `set_imported_tables_for_test` removal but has not yet been rewritten to
  capture in-memory. That rewrite is P3-T1. The files were cleaned between
  phases so the leak is captured here as the still-extant pre-P3 condition.

## Confidentiality

Only fabricated values (`SKU-001`, `k1`, `le.xlsx`, `aop.xlsx`, `sku_lu.xlsx`).
