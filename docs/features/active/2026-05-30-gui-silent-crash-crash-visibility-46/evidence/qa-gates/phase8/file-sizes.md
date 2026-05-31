# Phase 8 — File Sizes (Post-Fix State)

- Timestamp: 2026-05-31T02-43
- Command:
  - `wc -l <path>` (per file)
  - `awk 'END{print NR}' <path>` (per file; both counters cross-verified)
- EXIT_CODE: 0

## Results

| File | Baseline | Post-change | Under 500-line cap |
|---|---|---|---|
| src/gui/_crash_handler.py | 0 (NEW) | 495 | PASS |
| src/gui/_crash_handler_bootstrap.py | 0 (NEW in R1) | 94 | PASS |
| src/gui/runners.py | 156 | 270 | PASS |
| src/gui/workers/pipeline_worker.py | 79 | 116 | PASS |
| src/gui/app.py | 493 | 499 | PASS |

Every row is under the 500-line cap. AC-12 satisfied for all modified production files at the post-R1 / post-R4 state. `src/gui/app.py` was reduced from 503 (pre-R1, over cap) to 499 (post-R1, under cap by 1 line) via extraction of the crash-handler bootstrap into the new `src/gui/_crash_handler_bootstrap.py` (94 lines) plus a minor inline-comment reduction at the call site.

## Notes

- This artifact captures the post-fix state corresponding to the corrected phase4 artifact at `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md`. The phase4 artifact has been corrected in place (see its `Correction Note`) and continues to show the pre-R1 state with `src/gui/app.py` at 503 lines (FAIL). The phase8 artifact records the post-R1 state in which `src/gui/app.py` is 499 lines (PASS).
- Both `wc -l` and `awk 'END{print NR}'` agree on every line count above.
