# Baseline — Pytest + Coverage (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing` (QT_QPA_PLATFORM=offscreen)

EXIT_CODE: 0

Output Summary:
- Tests: 717 passed, 1 warning, in 33.06s.
- Coverage TOTAL: statements 3533, missed 31, branches 650, partial 23.
- Line coverage: (3533 - 31) / 3533 = 99.12%.
- Branch coverage: (650 - 23) / 650 = 96.46%.
- Matches the plan baseline: 717 tests, 99.12% line / 96.46% branch.

Only partially-covered production module: `src/schema_matching.py` (97%, lines 141->148, 148->152, 168) — pre-existing, unaffected by this test-only cycle.
