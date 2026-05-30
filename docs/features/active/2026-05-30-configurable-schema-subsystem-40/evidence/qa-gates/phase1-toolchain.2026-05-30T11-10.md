# Phase 1 — Toolchain (F1 refactor) (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Single clean pass: Black -> Ruff -> Pyright strict -> Pytest+coverage.

## black
Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: All done. 166 files left unchanged (no reformat).

## ruff check
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. E402 now genuinely absent (no longer suppressed); the 9 `# noqa: E402` directives are removed.

## pyright (strict)
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## pytest + coverage
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing` (QT_QPA_PLATFORM=offscreen)
EXIT_CODE: 0
Output Summary:
- 717 passed, 1 warning, in 33.26s.
- Coverage TOTAL: statements 3533, missed 31, branches 650, partial 23.
- Line coverage: 99.12% (>= baseline 99.12%).
- Branch coverage: 96.46% (>= baseline 96.46%).
- No regression: test count 717 (>= 717); coverage unchanged.
