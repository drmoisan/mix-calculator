# Baseline — Targeted Coverage for src/gui/runners.py (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06
Command: env -u VIRTUAL_ENV poetry run pytest tests/gui/test_runners.py tests/gui/test_runners_threaded.py --cov=src.gui.runners --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Tests: 8 passed, 0 failed.
- src/gui/runners.py: 46 statements, 0 missed, 0 branches, 0 branch-partials -> line coverage 100%, branch coverage 100%.
Note: The plan text references `tests/gui/test_runners_threaded.py`; both that file and `tests/gui/test_runners.py` were included. The `--cov=src.gui.runners` dotted-module form is used (the `--cov=src/gui/runners` path form emits a "module not imported" warning under this layout).
