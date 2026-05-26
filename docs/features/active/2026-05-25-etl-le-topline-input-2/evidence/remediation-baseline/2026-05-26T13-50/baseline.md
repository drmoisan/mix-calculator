# Remediation Baseline — Suppression Elimination (issue 2)

Timestamp: 2026-05-26T13-50
Scope: src/normalize_le.py, tests/le_fixtures.py (plus optional small helper module)

## Black
Command: poetry run black --check .
EXIT_CODE: 0
Output Summary: All done. 11 files would be left unchanged.

## Ruff
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed (0 findings).

## Pyright
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Pytest (coverage)
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary: 72 passed. Coverage TOTAL line 100% / branch 100%. src/normalize_le.py 100% line / 100% branch.

## File line counts (pre-change)
- src/normalize_le.py: 483 lines (near the 500-line limit)
- tests/le_fixtures.py: 316 lines

## Flagged suppressions
1. tests/le_fixtures.py:85 — # noqa: S608 on f-string SELECT in read_table
2. src/normalize_le.py:168 — # pyright: ignore[reportUnknownMemberType] on pd.read_excel
3. src/normalize_le.py:354 — # pyright: ignore[reportUnknownMemberType] on df.to_sql
4. tests/le_fixtures.py:89 — # pyright: ignore[reportUnknownMemberType] on pd.read_sql
