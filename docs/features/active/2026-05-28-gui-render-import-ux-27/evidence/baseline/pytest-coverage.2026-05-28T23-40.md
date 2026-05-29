# Baseline — Pytest + Coverage (Issue #27)

Timestamp: 2026-05-28T23-40
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary: PASS. 417 passed. Coverage TOTAL line: 1954 statements, 14 missed -> line coverage 99.28%; 296 branches, 2 partial -> branch coverage 99.32%. Aggregate term-report TOTAL column: 99%. Both thresholds (line >= 85%, branch >= 75%) met at baseline. Touched-file baselines: src/gui/app.py 100%, src/gui/main_window.py 100%, src/gui/presenters/pipeline_presenter.py 100%, src/gui/widgets/source_input_widget.py 96% (missing lines 154-155 in set_current_sheet append branch).
