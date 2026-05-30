# Phase 2 — Toolchain (F2 split) (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Single clean pass: Black -> Ruff -> Pyright strict -> Pytest+coverage.

## black
Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: All done. 170 files left unchanged (4 new fake modules added, no reformat).

## ruff check
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. The re-export `fake_views.py` uses `__all__` to mark the re-exported names, so no F401 is raised.

## pyright (strict)
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## pytest + coverage
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing` (QT_QPA_PLATFORM=offscreen)
EXIT_CODE: 0
Output Summary:
- 717 passed, 1 warning, in 31.52s.
- Coverage TOTAL: statements 3533, missed 31, branches 650, partial 23.
- Line coverage: 99.12% (>= baseline 99.12%).
- Branch coverage: 96.46% (>= baseline 96.46%).
- No regression: test count 717 (>= 717); coverage unchanged. The 16 consumer import statements (across 10 files) of `tests.gui.fakes.fake_views` resolve unchanged via the re-export.
