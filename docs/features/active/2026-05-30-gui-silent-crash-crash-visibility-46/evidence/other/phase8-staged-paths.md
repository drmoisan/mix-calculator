# Phase 8 — Files To Stage (Pre-Commit Inventory)

Timestamp: 2026-05-30T23-32

Command: `git status --porcelain` (executed at end of Phase 7).

The orchestrator owns the actual `git add` and `git commit` step. This inventory enumerates every path the orchestrator must stage for the final commit.

## Modified production / test files
- src/gui/app.py
- src/gui/runners.py
- src/gui/workers/pipeline_worker.py
- tests/gui/test_app_composition.py
- tests/gui/test_pipeline_worker.py

## New production / test files
- src/gui/_crash_handler.py
- tests/gui/test_crash_handler.py
- tests/gui/test_runners_threaded.py

## New documentation / evidence (untracked tree)
- docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/ (entire folder)
  - issue.md (already present at branch start; carried forward unchanged here)
  - spec.md (ACs ticked, Status bumped to "Implemented (pending review)")
  - plan.2026-05-30T22-45.md (plan checklist now fully ticked)
  - evidence/baseline/ (8 baseline artifacts)
  - evidence/regression-testing/ (2 artifacts: phase1-fail-before, phase5-pass-after)
  - evidence/qa-gates/phase2..phase7/ (per-phase toolchain artifacts)
  - evidence/qa-gates/phase7/_raw/ (raw toolchain logs)
  - evidence/issue-updates/ (issue-46 mirror)
  - evidence/other/ (this file + pr-draft)

The orchestrator should NOT stage `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase7/_raw/` if repo policy excludes raw tool logs from the commit; otherwise stage the whole evidence tree as-is for an audit trail.

Do not run `git commit` from this plan; the orchestrator gates the commit step.
