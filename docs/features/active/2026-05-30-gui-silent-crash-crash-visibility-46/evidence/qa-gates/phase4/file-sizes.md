# Phase 4 — File Sizes (Post-Change, Corrected)

Timestamp: 2026-05-30T23-25
Corrected At: 2026-05-31T02-43

Command: `wc -l <path>` (per file); verified with `awk 'END{print NR}' <path>` (per file)

EXIT_CODE: 0

Output Summary:

| File | Baseline | Post-change | Under 500-line cap |
|---|---|---|---|
| src/gui/_crash_handler.py | 0 (NEW) | 495 | PASS |
| src/gui/runners.py | 156 | 270 | PASS |
| src/gui/workers/pipeline_worker.py | 79 | 116 | PASS |
| src/gui/app.py | 493 | 503 | **FAIL** |

`src/gui/app.py` is over the 500-line cap by 3 lines at HEAD `666e84a32aa158a4554cb0305c5695512e35f0cd`. AC-12 is NOT satisfied at this point in the plan; R1 (Phase 2) extracts the crash-handler bootstrap to restore the cap.

## Correction Note

- Original (incorrect) command: `pwsh -NoProfile -Command "(Get-Content <path> | Measure-Object -Line).Lines"`.
- Reason for correction: `Measure-Object -Line` counts line-terminator characters (newline sequences) and drops the trailing partial line. Files ending without a trailing newline are undercounted by 1 or more; the original artifact reported `app.py = 439` when both `wc -l` and `awk 'END{print NR}'` return `503`. Cited in `policy-audit.2026-05-31T02-43.md` F3 and `code-review.2026-05-31T02-43.md`.
- Authoritative counters used here: `wc -l` and `awk 'END{print NR}'`; both agree on 503 for `src/gui/app.py`.
- Pointer back: see `remediation-plan.2026-05-31T02-43.md` R3 (Phase 1) for the full correction context.
