# Phase 7 — Pytest with Coverage (Final)

Timestamp: 2026-05-30T23-30

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

## Output Summary

- Tests run: 734 (baseline 717, +17 new regression tests)
- Tests passed: 734
- Tests failed: 0
- Warnings: 1 (pre-existing pandas FutureWarning in `src/mix_lookups.py:173`; unrelated to this feature)

## Headline coverage (TOTAL, with `--cov-branch`)

- Statements: 3651 (baseline 3533, +118 for `_crash_handler.py`)
- Missed lines: 33 (baseline 31; +2 in `_crash_handler.py` net of +118 added lines)
- Branches: 660 (baseline 650, +10 for `_crash_handler.py`)
- Branch partial: 23 (unchanged from baseline)
- Total coverage: 99% (unchanged from baseline)

## Per-file coverage for the four touched files

| File | Stmts | Miss | Branch | BrPart | Line cover | Branch cover | Missing |
|---|---|---|---|---|---|---|---|
| src/gui/_crash_handler.py | 99 | 13 | 8 | 0 | 88% | 100% | 254-263, 290-303, 374-383 |
| src/gui/runners.py | 46 | 0 | 0 | 0 | 100% | n/a | none |
| src/gui/workers/pipeline_worker.py | 24 | 0 | 2 | 0 | 100% | 100% | none |
| src/gui/app.py | 138 | 1 | 12 | 1 | 99% | 92% | 314 (pre-existing branch partial, unchanged from baseline) |

## Notes on uncovered lines in `_crash_handler.py`

Lines 254-263 and 290-303 are inside the closures returned by `_make_sys_excepthook` and `_make_threading_excepthook`. The Phase 2 tests verify the closures are created and recorded in `installed_hooks` but do not invoke them directly (the tests patch the install seam so the closures are never wired into the process hooks; this is the test-purity requirement to avoid rebinding process-wide state). Lines 374-383 are `_append_traceback`, called only from within the uninvoked closures. Per AC-10, all four touched files exceed the 85% line / 75% branch thresholds: `_crash_handler.py` is at 88% line / 100% branch on changed lines.
