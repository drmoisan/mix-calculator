# Final QA — Pytest + Coverage (AC-11)

Timestamp: 2026-06-16T20-20
Command: QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 1085 passed, 5 warnings.
- TOTAL coverage row: 5291 statements, 51 missed, 990 branches, 65 partial branches.
- Line coverage: 99.04% (>= 85% threshold).
- Branch coverage: 93.43% (>= 75% threshold).
- coverage.py term report prints "98%" rounded TOTAL (combined line+branch denominator).
- GUI tests run under QT_QPA_PLATFORM=offscreen.
