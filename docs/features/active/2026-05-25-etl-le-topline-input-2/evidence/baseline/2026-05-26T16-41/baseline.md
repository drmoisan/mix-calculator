# Baseline Evidence — test file split remediation (issue #2)

Timestamp: 2026-05-26T16-41
Scope: split `tests/test_normalize_le.py` (532 lines, over 500-line limit) into a sibling module.

## Black
Command: `poetry run black --check .`
EXIT_CODE: 0
Output Summary: All done. 13 files would be left unchanged. No reformatting needed.

## Ruff
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed. 0 findings.

## Pyright
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: 77 passed. Coverage TOTAL line 100%, branch 100% (BrPart 0).
test_normalize_le.py contributed 31 tests in this run.

## Line counts (pre-change)
- tests/test_normalize_le.py: 532 (over limit)
- tests/test_normalize_le_io.py: 428
- tests/test_le_columns.py: 168
- tests/test_le_key.py: 209
