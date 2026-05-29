# Final QA Gate — Pytest + Coverage (P6-T4)

Timestamp: 2026-05-29T00-34
Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- Result: 444 passed, 0 failed.
- Combined coverage headline (TOTAL row): 99%.
- Statements: 2093 total, 13 missed -> line coverage 99.38% (>= 85% threshold met).
- Branches: 318 total, 1 partial -> branch coverage 99.69% (>= 75% threshold met).
- New/changed modules in this feature at 100% line+branch coverage:
  - src/gui/_render_exclusivity.py (100%)
  - src/gui/presenters/import_dispatch.py (100%)
  - src/gui/_import_dispatch_wiring.py (100%)
  - src/gui/presenters/pipeline_presenter.py (100%)
  - src/gui/app.py (100%)
  - src/gui/main_window.py (100%)
  - src/gui/widgets/source_input_widget.py (97%; the 2 uncovered lines 206-207
    are in the pre-existing set_current_sheet "append missing sheet" branch,
    not changed by this feature).
