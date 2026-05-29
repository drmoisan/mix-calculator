# Coverage-Delta Verification (P6-T5)

Timestamp: 2026-05-29T00-34
Command (post-change): QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0

## Baseline vs Post-Change (aggregate)

| Metric | Baseline (P0-T5, 2026-05-28T23-40) | Post-Change (P6-T4) | Threshold | Result |
|---|---|---|---|---|
| Tests | 417 passed | 444 passed | — | +27 tests, all pass |
| Statements | 1954 (14 missed) | 2093 (13 missed) | — | — |
| Line coverage | 99.28% | 99.38% | >= 85% | PASS (no regression) |
| Branches | 296 (2 partial) | 318 (1 partial) | — | — |
| Branch coverage | 99.32% | 99.69% | >= 75% | PASS (no regression) |

Aggregate line and branch coverage both increased; no regression at the
repository level.

## Changed-Line Coverage (four touched production files + two new modules)

| File | Status | Coverage |
|---|---|---|
| src/gui/app.py (P1-T2, P3-T1) | modified | 100% line+branch |
| src/gui/presenters/pipeline_presenter.py (P2-T2) | modified | 100% line+branch |
| src/gui/main_window.py (P4-T2) | modified | 100% line+branch |
| src/gui/widgets/source_input_widget.py (P4-T1) | modified | 97% line (uncovered 206-207 are the pre-existing set_current_sheet append branch, not changed by this feature) |
| src/gui/_render_exclusivity.py (P1-T1, new wire_render_checkboxes) | new/modified | 100% line+branch |
| src/gui/presenters/import_dispatch.py (P2-T1) | new | 100% line+branch |
| src/gui/_import_dispatch_wiring.py (P3-T1) | new | 100% line+branch |

## No-Regression on Changed Lines

All lines added or modified by this feature are exercised by the new and
existing tests; every changed/new production line is covered. The only
uncovered lines in any touched file (source_input_widget.py 206-207) are in a
pre-existing method (`set_current_sheet`) untouched by this feature, so they do
not constitute a regression on changed lines.

## Outcome

PASS. Line >= 85% and branch >= 75% thresholds met; no regression on changed
lines. No required coverage value was unavailable.
