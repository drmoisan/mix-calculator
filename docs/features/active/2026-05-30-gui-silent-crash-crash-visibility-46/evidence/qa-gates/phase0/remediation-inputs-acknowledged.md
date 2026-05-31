# Phase 0 — Remediation Inputs Acknowledged

- Timestamp: 2026-05-31T02-43

Verbatim "Definition of done" for each finding from `remediation-inputs.2026-05-31T02-43.md`:

## R1 — Restore the 500-line cap in `src/gui/app.py` (Blocking)

> - `awk 'END{print NR}' src/gui/app.py` returns `<= 500`.
> - All four toolchain stages pass in a single pass.
> - `test_main_entry_point_runs_event_loop`, `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`, and `test_main_calls_velopack_app_run_before_qapplication` continue to pass without modification (no observable behavior change).

## R2 — Resolve the `_resolve_log_dir` vs `resolve_log_dir` spec/code drift (Material PARTIAL)

> - Spec AC-1 text matches the public symbol name in source.
> - Pyright remains clean (no new suppressions).

## R3 — Regenerate `evidence/qa-gates/phase4/file-sizes.md` with a faithful line-count command (Material PARTIAL)

> - Artifact contains line counts matching `wc -l` / `awk NR` to within +/- 1 line.
> - Artifact accurately reflects whether each file is under or over the cap.

## R4 — Pin the crash-write closure bodies with direct invocation tests (Material PARTIAL, informational)

> - The three closures execute under test.
> - `_crash_handler.py` missing-lines list no longer includes 254-263, 290-303, 374-383 (or the residual list is documented and accepted).
