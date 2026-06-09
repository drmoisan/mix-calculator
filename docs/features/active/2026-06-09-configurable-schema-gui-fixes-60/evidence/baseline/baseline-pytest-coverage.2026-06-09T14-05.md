# Baseline — Test + Coverage (Issue #60)

Timestamp: 2026-06-09T14-05

Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Tests: 998 passed, 0 failed, 3 warnings.
- Coverage TOTAL row: statements=4793, missed=44, branches=894, partial=54, combined=98%.
- Line coverage = (4793 - 44) / 4793 = 99.08%.
- Branch coverage = (894 - 54) / 894 = 93.96%.
- Both exceed gates (line >= 85%, branch >= 75%). This is the no-regression
  reference for AC-13.
- Touched-file baselines:
  - src/gui/widgets/source_input_widget.py: 98% (lines 266-267 missed).
  - src/gui/presenters/source_selection_presenter.py: included in TOTAL (clean).
