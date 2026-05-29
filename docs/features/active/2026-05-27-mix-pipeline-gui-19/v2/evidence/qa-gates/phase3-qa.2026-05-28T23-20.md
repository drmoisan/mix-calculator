# Phase 3 QA — Toolchain Loop

## Black

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run black .`
EXIT_CODE: 0
Output Summary: 105 files left unchanged.

## Ruff

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. The first attempt flagged one E501
(line-length) on the rewritten test docstring. Resolved by wrapping the
docstring into a multi-line PEP-257 form. Toolchain restarted from Black;
second pass clean.

## Pyright

Timestamp: 2026-05-28T23-20
Command: `env -u VIRTUAL_ENV poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. No suppressions
introduced. The `_CapturingStringIO` subclass overrides `close()` returning
`None`, matching `io.StringIO.close()` so no `# type: ignore` is required.

## Pytest with coverage

Timestamp: 2026-05-28T23-20
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 417 passed in 21.11s; 0 failed.
- Line coverage (TOTAL): 99% (1954 statements, 14 missed).
- Branch coverage (TOTAL): 99% (296 branches, 2 partial).
- `src/gui/exporters/csv_exporter.py`: 100% line / 100% branch (unchanged).
- The rewritten test passes and the new `_CapturingStringIO` subclass is
  exercised three times per run (once per fabricated table).
- File line-count check: `tests/gui/integration/test_behavioral_dialogs.py`
  is 265 lines (under the 500-line cap).
- `git status` after the pytest run shows no untracked `results_*.csv` files
  at the repo root (`ls results_*.csv` returns "No such file or directory").
  The R-1 disk-write side effect is eliminated.

## R-1 acceptance check

- Behavioral test completes without creating any file on disk: confirmed.
- `git status` shows no untracked `results_*.csv` at the repo root: confirmed.
- AC-9 user-visible surface remains verified by `tests/gui/test_csv_exporter.py`
  (registry resolution and name-mangling unit contract) AND by the rewritten
  behavioral test's in-memory capture assertions (per-table file names and
  non-empty content).
