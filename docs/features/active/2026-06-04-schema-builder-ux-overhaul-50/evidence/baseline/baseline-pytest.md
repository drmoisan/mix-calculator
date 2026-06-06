# Baseline — Pytest + Coverage

Timestamp: 2026-06-05T11-08
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 818 passed, 1 warning.
- TOTAL coverage line+branch combined report: 99% (term summary).
- Line coverage: (3830 statements - 20 missed) / 3830 = 99.5%.
- Branch coverage: (682 branches - 23 partial) / 682 = 96.6%.
- Thresholds (line >= 85%, branch >= 75%) satisfied at baseline.
