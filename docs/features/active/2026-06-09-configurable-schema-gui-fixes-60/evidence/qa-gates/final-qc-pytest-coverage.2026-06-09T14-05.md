# Final QC — Pytest + Coverage (Issue #60, P4-T3)

Timestamp: 2026-06-09T14-05

Command: QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

Output Summary:
- Tests: 1023 passed, 0 failed, 3 warnings.
- Coverage TOTAL row: statements=4860, missed=44, branches=908, partial=54, combined=98%.

Post-change coverage (numeric):
- Line coverage = (4860 - 44) / 4860 = 99.09%.
- Branch coverage = (908 - 54) / 908 = 94.05%.
- Both exceed gates (line >= 85%, branch >= 75%).

Delta vs. P0-T4 baseline (baseline-pytest-coverage.2026-06-09T14-05.md):
- Baseline line coverage = 99.08%; post-change = 99.09%; delta = +0.01 pp (no regression).
- Baseline branch coverage = 93.96%; post-change = 94.05%; delta = +0.09 pp (no regression).
- Baseline tests = 998 passed; post-change = 1023 passed; +25 tests (Phases 1-3 additions).

No regression on changed lines (touched-file post-change coverage):
- src/gui/presenters/source_selection_presenter.py: 99% (only partial branch 342->344;
  Defect 3 _best_header_row selection paths covered). No regression vs. baseline (clean in TOTAL).
- src/gui/widgets/source_input_widget.py: 97% (lines 263-264 missed); baseline was 98%
  (lines 266-267 missed). The missed lines are pre-existing, not the new Edit-Schema
  surface; the new button/signal/property and gating paths are exercised by the
  Phase-3 tests. Overall TOTAL line and branch coverage both improved vs. baseline,
  so there is no aggregate or changed-line coverage regression.
- src/gui/widgets/_source_input_button_wiring.py: 100% (new extraction module fully covered).

Conclusion: all four final-QC stages exit 0; post-change line 99.09% and branch 94.05%
both exceed thresholds with no regression vs. baseline. AC-11 and AC-13 satisfied.
