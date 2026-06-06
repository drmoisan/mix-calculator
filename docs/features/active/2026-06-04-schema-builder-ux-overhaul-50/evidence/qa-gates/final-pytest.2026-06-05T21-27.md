# Final QA — Pytest with Coverage (Cycle 2)

Timestamp: 2026-06-05T21-27
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- 932 passed, 0 failed, 3 warnings in ~22.8s.
- TOTAL coverage row: statements 4653, missed 44, branches 850, partial 51.
- Line coverage (statements): (4653 - 44) / 4653 = 99.05% (>= 85% gate).
- Branch coverage: (850 - 51) / 850 = 93.99% (>= 75% gate).
- Combined reported total: 98%.
- The two type-only protocol modules are ABSENT from the per-file report, confirming
  the N4 omit fix in [tool.coverage.run].omit:
  - src/gui/_columns_tab_protocol.py: not present as a coverage row.
  - src/gui/_key_tab_protocol.py: not present as a coverage row.
- Relative to the Cycle-2 baseline (P0-T5: 4671 stmts / 62 missed), TOTAL statements
  dropped by exactly 18 (4671 -> 4653) and missed dropped by exactly 18 (62 -> 44),
  which is the 10 + 8 = 18 omitted protocol-module statements. No previously-counted
  source line was removed from coverage.
- No prior QA step (Black/Ruff/Pyright) changed files this pass, so the loop did not
  restart.
