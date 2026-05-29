Timestamp: 2026-05-28T23-20
Command: `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary:
- 417 passed in 21.42s; 0 failed.
- Line coverage (TOTAL): 99% (1954 statements, 14 missed).
- Branch coverage (TOTAL): 99% (296 branches, 2 partial).
- Threshold check: line >= 85%, branch >= 75% — both met (well above).
- No regression on changed lines: `src/gui/app.py` 100%/100%;
  `src/gui/presenters/pipeline_presenter.py` 99%/95%;
  `tests/gui/test_app_wiring.py` 100% (test file);
  `tests/gui/integration/test_behavioral_dialogs.py` 100% (test file);
  `tests/gui/integration/test_behavioral_pipeline_run.py` 100% (test file).
- `git status` excerpt: no untracked `results_*.csv` files at the repo root
  after the pytest run. Verified via `git status --short | grep -E "results_"`
  returning no matches. The R-1 disk-write side effect is closed.
