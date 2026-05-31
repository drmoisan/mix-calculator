# Phase 0 — Baseline Pytest with Coverage

Timestamp: 2026-05-30T22-51

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

## Output Summary

- Tests run: 717
- Tests passed: 717
- Tests failed: 0
- Warnings: 1 (FutureWarning from pandas concat in `src/mix_lookups.py:173` — unrelated to this feature)

## Headline coverage (TOTAL)

- Statements: 3533
- Missed: 31
- Branches: 650
- Branch partial: 23
- Coverage: 99%

## Per-file baselines (touched files)

| File | Stmts | Miss | Branch | BrPart | Line cover | Missing |
|---|---|---|---|---|---|---|
| src/gui/runners.py | 32 | 11 | 0 | 0 | 66% | 131-147 (`ThreadedRunner.run` body) |
| src/gui/workers/pipeline_worker.py | 22 | 0 | 0 | 0 | 100% | none |
| src/gui/app.py | 135 | 1 | 12 | 1 | 99% | 313 (one branch-partial) |
| src/gui/_crash_handler.py | n/a | n/a | n/a | n/a | n/a | file does not exist at baseline; introduced in Phase 2 |

Note: `src/gui/runners.py` baseline line coverage is 66%. The currently-untested block (lines 131-147) is exactly the body of `ThreadedRunner.run` that Phase 3 modifies. The new `tests/gui/test_runners_threaded.py` raises this coverage as it exercises the queued-connection wiring (AC-10).
