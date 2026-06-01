# Phase 2 — test_crash_handler.py Line Count (Post-Trim)

- Timestamp: 2026-05-31T03-25
- Command:
  - `wc -l tests/gui/test_crash_handler.py`
  - `awk 'END{print NR}' tests/gui/test_crash_handler.py`
  - `pwsh -NoProfile -Command "(Get-Content tests/gui/test_crash_handler.py).Count"`
- EXIT_CODE: 0
- Output Summary:
  - `wc -l`: 332
  - `awk NR`: 332
  - `(Get-Content).Count`: 332
  - All three counters agree exactly. 332 <= 500 (cap satisfied with 168 lines of headroom).
  - Delta vs cycle-2 entry: 549 -> 332 (-217 lines). 215 lines relocated to `tests/gui/test_crash_handler_closures.py` (covering the R4 meta-what comment block, `_FakePath`, `_FakeHandle`, and the three closure tests) plus one removed import symbol (`cast`) and one blank-line trim at end-of-file.
  - Removed unused import: `cast` from `from typing import IO, TYPE_CHECKING, Any, cast` -> `from typing import IO, TYPE_CHECKING, Any`. All other top-of-file imports remain referenced by the retained tests.
