# Phase 0 — Remediation Inputs Acknowledged (Cycle 2)

Timestamp: 2026-05-31T03-25

Artifacts read:
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-inputs.2026-05-31T03-25.md`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/policy-audit.2026-05-31T03-25.md`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/code-review.2026-05-31T03-25.md`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/feature-audit.2026-05-31T03-25.md`

Sole cycle-2 finding: R5 (Blocking).

## R5 — Split `tests/gui/test_crash_handler.py` to restore the 500-line cap (Blocking)

Verbatim "Definition of done" from `remediation-inputs.2026-05-31T03-25.md`:

> - `awk 'END{print NR}' tests/gui/test_crash_handler.py` returns `<= 500`.
> - `awk 'END{print NR}' tests/gui/test_crash_handler_closures.py` returns `<= 500`.
> - All four Python toolchain stages pass in a single pass.
> - `src/gui/_crash_handler.py` line and branch coverage remain at 100% / 100% (post-R4 state).
> - All 737 tests still pass (the three R4 tests should appear in the new file and run identically).
> - `evidence/qa-gates/phase8/file-sizes.md` is regenerated to include all four test files; rows for `test_crash_handler.py`, `test_crash_handler_closures.py`, `test_runners_threaded.py`, `test_pipeline_worker.py`, and `test_app_composition.py` should each show `PASS`.
