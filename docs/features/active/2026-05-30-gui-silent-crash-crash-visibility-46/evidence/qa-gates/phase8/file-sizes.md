# Phase 8 — File Sizes (Post-Fix State, Cycle 2)

- Timestamp: 2026-05-31T03-25
- Last Updated: 2026-05-31T03-25
- Command:
  - `wc -l <path>` (per file)
  - `awk 'END{print NR}' <path>` (per file; cross-verified with `wc -l`)
  - `pwsh -NoProfile -Command "(Get-Content <path>).Count"` (per file; third-counter triple-verification)
- EXIT_CODE: 0

## Results

| File | Baseline | Post-change | Under 500-line cap |
|---|---|---|---|
| src/gui/_crash_handler.py | 0 (NEW) | 495 | PASS |
| src/gui/_crash_handler_bootstrap.py | 0 (NEW in R1) | 94 | PASS |
| src/gui/runners.py | 156 | 270 | PASS |
| src/gui/workers/pipeline_worker.py | 79 | 116 | PASS |
| src/gui/app.py | 493 | 499 | PASS |
| tests/gui/test_crash_handler.py | 549 | 332 | PASS |
| tests/gui/test_crash_handler_closures.py | 0 (NEW) | 258 | PASS |
| tests/gui/test_runners_threaded.py | unchanged in this branch | 151 | PASS |
| tests/gui/test_pipeline_worker.py | unchanged in this branch | 244 | PASS |
| tests/gui/test_app_composition.py | unchanged in this branch | 480 | PASS |

Every row is under the 500-line cap. AC-12's spec text (production-only scope) is satisfied for all modified production files at the post-R1 / post-R4 state. The cycle-2 R5 remediation extends the same cap enforcement to the test code at issue (`tests/gui/test_crash_handler.py`), as required by `.claude/rules/general-code-change.md`.

## Notes

- Cap policy reference: `.claude/rules/general-code-change.md` — the 500-line file size limit applies to production code, test code, and reusable script files.
- Cycle-2 driver: R5 (Blocking) — split `tests/gui/test_crash_handler.py` (was 549, over cap by 49) into `tests/gui/test_crash_handler.py` (now 332, retains installer-contract tests) and a new sibling `tests/gui/test_crash_handler_closures.py` (258, contains `_FakePath`/`_FakeHandle` fixtures and the three R4 closure-invocation tests).
- Back-reference: this artifact extends the cycle-1 corrected file-sizes artifact at `evidence/qa-gates/phase4/file-sizes.md` by adding rows for the four test files and the bootstrap module; the cycle-1 production rows are unchanged.
- All ten rows have `wc -l`, `awk 'END{print NR}'`, and `(Get-Content).Count` in agreement (verified independently for every file in this table; see also `evidence/qa-gates/phase5/file-sizes-verification.md`).
