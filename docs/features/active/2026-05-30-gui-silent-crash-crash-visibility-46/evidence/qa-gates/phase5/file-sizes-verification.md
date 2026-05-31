# Phase 5 — File Sizes Verification (Second Pass)

- Timestamp: 2026-05-31T03-25
- Command:
  - `wc -l <path>` (per file)
  - `awk 'END{print NR}' <path>` (per file)
- EXIT_CODE: 0
- Output Summary:
  - Second-pass counts re-verified against the values recorded in `evidence/qa-gates/phase8/file-sizes.md`. Every row matches and every counter agrees.

| File | wc -l | awk NR | Matches phase8 table |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | 495 | YES |
| src/gui/_crash_handler_bootstrap.py | 94 | 94 | YES |
| src/gui/runners.py | 270 | 270 | YES |
| src/gui/workers/pipeline_worker.py | 116 | 116 | YES |
| src/gui/app.py | 499 | 499 | YES |
| tests/gui/test_crash_handler.py | 332 | 332 | YES |
| tests/gui/test_crash_handler_closures.py | 258 | 258 | YES |
| tests/gui/test_runners_threaded.py | 151 | 151 | YES |
| tests/gui/test_pipeline_worker.py | 244 | 244 | YES |
| tests/gui/test_app_composition.py | 480 | 480 | YES |
