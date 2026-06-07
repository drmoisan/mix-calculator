# Final QA — Pytest with Coverage (Remediation Cycle 1, P7-T4)

Timestamp: 2026-06-05T20-28
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 932 passed, 3 warnings in ~23s; 0 failed (up from 922 at baseline; 10 new tests added across R1-R6 integrated tests, the BuildSpecProvider unit tests, and the N1 test split).
- TOTAL coverage: statements 4671, missed 62, branches 850, partial 51.
- Line coverage: (4671-62)/4671 = 98.7% (>= 85% gate).
- Branch coverage: (850-51)/850 = 94.0% (>= 75% gate).
- New/changed module coverage: _schema_builder_drag_tabs.py 96%, _schema_provider_factory.py 95%, _schema_open_helpers.py 93%, _source_signal_wiring.py 100%, _schema_discovery_wiring.py 100%, _schema_wiring.py 98%, app.py 99%, schema_builder_dialog.py 98%, _schema_builder_tabs.py 100%.
- All tests pass headless under QT_QPA_PLATFORM=offscreen.
