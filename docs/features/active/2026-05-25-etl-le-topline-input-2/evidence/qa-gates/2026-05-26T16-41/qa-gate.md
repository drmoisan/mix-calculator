# QA Gate Evidence — test file split remediation (issue #2)

Timestamp: 2026-05-26T16-41
Scope: tests/test_normalize_le.py (reduced), tests/test_normalize_le_totals.py (new).
No production files changed.

## Black
Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: All done. 14 files left unchanged. No reformatting.

## Ruff
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings (no unused-import F401, no suppressions added).

## Pyright
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: 77 passed. Coverage TOTAL line 100%, branch 100% (BrPart 0).
test_normalize_le.py: 28 tests; test_normalize_le_totals.py: 3 tests (31 combined, matches pre-split).

## Delta vs baseline (2026-05-26T16-41 baseline)
- Black delta: 0 (clean -> clean).
- Ruff delta: 0 new findings.
- Pyright delta: 0 new diagnostics.
- Pytest delta: 0 new failures; total count 77 -> 77 (unchanged).
- Coverage delta: 100%/100% -> 100%/100% (no regression).

## Line counts (post-change)
- tests/test_normalize_le.py: 436 (under 500 limit)
- tests/test_normalize_le_totals.py: 121 (under 500 limit)

## Tests moved
From test_normalize_le.py to test_normalize_le_totals.py (verbatim, same names/assertions):
- test_load_source_fills_blank_fy_and_quarters_from_months
- test_load_source_fills_blank_totals_treating_blank_months_as_zero
- test_load_source_preserves_populated_fy_and_quarters

## Constraint confirmation
- No artifacts/ files read; no real customer names or figures introduced (fabricated: Acme Foods, Globex Market, Initech Grocers).
- No new # noqa / # type: ignore / # pyright: ignore.
- No assertions weakened or deleted; pure relocation.
- All Excel I/O on io.BytesIO; SQLite on :memory: (unchanged in both files).
