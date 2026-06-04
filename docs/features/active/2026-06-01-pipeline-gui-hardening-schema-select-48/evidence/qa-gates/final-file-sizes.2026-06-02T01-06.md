# Final File Sizes — 500-line Cap (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06

| File | Lines | Within cap (<= 500)? |
|---|---|---|
| src/gui/runners.py | 416 | Yes |
| src/gui/_shutdown_wiring.py | 72 | Yes |
| src/gui/app.py | 500 | Yes (at cap) |
| tests/gui/test_runners_threaded_lifecycle.py | 213 | Yes |
| tests/gui/test_shutdown_wiring.py | 113 | Yes |
| tests/gui/test_runners_threaded.py | 161 | Yes |

Result: All touched and new production and test files are <= 500 lines. `src/gui/app.py` is exactly at the 500-line cap; the shutdown hook was added via the sibling module `src/gui/_shutdown_wiring.py` with only one import and one call site in `app.py`, offset by tightening pre-existing comments to keep the file at the cap.
