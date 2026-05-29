# Cycle-1 Baseline (post-v2-execution working tree)

## Black

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run black --check .`
EXIT_CODE: 0
Output Summary: All checks passed. 105 files would be left unchanged.

## Ruff

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 errors.

## Pyright

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest with coverage

Timestamp: 2026-05-28T23-20
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 416 passed in 21.49s; 0 failed.
- Line coverage (repository TOTAL): 99% (1956 statements, 14 missed).
- Branch coverage (repository TOTAL): 99% (296 branches, 2 partial).
- `src/gui/app.py`: 100% line / 100% branch.
- `src/gui/presenters/pipeline_presenter.py`: 99% line / 95% branch (one
  uncovered line at 172).
- `src/gui/runners.py`: 66% (lines 131-147 uncovered — the production
  `ThreadedRunner` thread-callback path; tests use `SynchronousRunner`).
- `git status` after the pytest run records three untracked artifacts at the
  repo root: `results_LE.csv`, `results_aop.csv`, `results_sku_lu.csv`. This
  confirms the R-1 leak that this cycle is remediating. The three files are
  deleted before continuing to Phase 1 so subsequent QA gates start from a
  clean working tree.
