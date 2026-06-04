# Baseline — File Size (500-line cap) (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06

Line counts (total lines including final content line; the 500-line cap is the limit):

| File | Lines |
|---|---|
| src/gui/runners.py | 271 |
| src/gui/app.py | 500 |
| src/gui/main_window.py | 201 |
| tests/gui/test_runners_threaded.py | 152 |

Notes:
- `src/gui/app.py` is AT the 500-line cap. Per the plan, the shutdown hook must be added via the new sibling module `src/gui/_shutdown_wiring.py`; `app.py` may gain only a single import and a single call site, and must remain <= 500 lines (verified in P2-T3).
- `src/gui/runners.py` has ample headroom (271 lines) for the Phase 1 lifecycle changes.
- Counts derived from the file content (last content line index); `wc -l` newline counts are one lower because each file ends with a trailing newline.
