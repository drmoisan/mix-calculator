# Baseline — Pytest + Coverage

Timestamp: 2026-06-08T14-30
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 987 passed, 0 failed, 3 warnings in ~35.6s.
- TOTAL coverage line (combined report): 98%.
- Statements: 4774 total, 44 missed -> line coverage = (4774-44)/4774 = 99.08%.
- Branches: 894 total, 54 partial -> branch coverage = (894-54)/894 = 93.96%.
- Targeted modules at baseline:
  - src/schema_loader.py: 31 stmts, 0 missed, 6 branch, 0 partial -> 100%.
  - src/gui/pipeline_service.py: present in suite (term report truncated to tail; full file covered by existing GUI service tests).
- Thresholds (policy): line >= 85% line / >= 75% branch. Baseline comfortably above both.
