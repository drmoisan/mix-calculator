# Final QA — Pytest full suite with coverage (P6-T4)

Timestamp: 2026-06-06T13-08

Command: poetry run pytest --cov --cov-branch --cov-report=term-missing

EXIT_CODE: 0

Output Summary:
- Total tests passed: 834 passed, 1 warning, in ~22s (baseline was 818; +16 net
  from the new/reworked etl_key, dialog, seam, bridge, and pipeline-service tests).
- TOTAL coverage row: 3891 statements, 20 missed; 698 branches, 23 partial; 99%.
- Total line coverage: (3891 - 20) / 3891 = 99.49%.
- Total branch coverage: (698 - 23) / 698 = 96.70%.
- CLI stdin-path tests (AC-6): `pytest -k "prompt or tty or key_mismatch or stdin"`
  across tests/test_etl_key.py, tests/test_normalize_le.py, tests/test_load_aop.py
  => 6 passed, 69 deselected. The decide_key_action stdin/prompt seam is unchanged.

Changed/added module coverage (full-suite):
- src/etl_key.py: 100% (67 stmts / 38 branches)
- src/_normalize_le_columns.py: 100% (28 stmts / 8 branches)
- src/normalize_le.py: 100% (107 stmts / 20 branches)
- src/load_aop.py: 100% (87 stmts / 24 branches)
- src/gui/pipeline_service.py: 100% (75 stmts / 0 branches)
- src/gui/_key_mismatch_seam.py: 100% (8 stmts)
- src/gui/_key_mismatch_dialog.py: 100% (30 stmts / 2 branches)
- src/gui/_key_mismatch_bridge.py: 100% (32 stmts / 4 branches)
- src/gui/app.py: 99% (139 stmts / 10 branches; the one uncovered line 297 is a
  pre-existing QApplication-singleton fallback branch unrelated to this change).
