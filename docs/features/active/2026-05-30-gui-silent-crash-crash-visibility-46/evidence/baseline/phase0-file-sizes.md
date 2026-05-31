# Phase 0 — Production File Line Counts (Baseline)

Timestamp: 2026-05-30T22-50

## Baseline sizes

src/gui/runners.py: 156
src/gui/workers/pipeline_worker.py: 79
src/gui/app.py: 431
src/gui/_crash_handler.py: 0 (does not exist at baseline; created in Phase 2)

500-line cap: all three existing files have headroom. `src/gui/app.py` is the closest to the cap with 431 lines (69 lines of headroom); planned changes add only an import and a single function call before `QApplication`, well within the cap.

## Post P2 sizes

Timestamp: 2026-05-30T23-13

src/gui/_crash_handler.py: 405 (<= 500: PASS). (Initial 389 lines; refactor for pyright strict mode and ruff TC003 added 16 lines for typed exc_value None handling and reordered imports.)
