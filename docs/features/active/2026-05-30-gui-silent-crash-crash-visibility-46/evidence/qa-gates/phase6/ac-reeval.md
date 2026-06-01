# Phase 6 — Acceptance Criteria Re-Evaluation (R1/R2/R4)

- Timestamp: 2026-05-31T02-43

## AC-1 (crash-handler module exists)

- Status: PASS
- Evidence: spec AC-1 text now reads `resolve_log_dir(app_name, platform_system, env)` (post P3-T1); matches the public symbol exported by `src/gui/_crash_handler.py`. Checkbox remains `[x]`.
- Artifact: `evidence/qa-gates/phase3/spec-resolve-log-dir.md`.

## AC-10 (coverage non-regressing)

- Status: PASS (strengthened)
- Evidence: per-file line coverage for `src/gui/_crash_handler.py` improved from 88% to **100%** with the three new direct-invocation tests in `tests/gui/test_crash_handler.py`. The previously-uncovered closure bodies (lines 254-263, 290-303, 374-383) are now exercised. Checkbox remains `[x]`; spec text amended with a remediation-cycle-1 note pointing to the three new tests.
- Artifacts: `evidence/qa-gates/phase4/pytest-post-r4.md`, `evidence/qa-gates/phase8/pytest.md` (Phase 8 final QA), `evidence/qa-gates/phase9/coverage-delta.md` (Phase 9 delta verification).

## AC-12 (file-size cap)

- Status: PASS (was FAIL pre-R1)
- Evidence: `src/gui/app.py` reduced from 503 to 499 lines (triple-counter verified). New `src/gui/_crash_handler_bootstrap.py` is 94 lines. All five modified production files are under the 500-line cap (phase8/file-sizes.md). Checkbox remains `[x]`; spec text amended with a remediation-cycle-1 note pointing to the bootstrap module and the phase8 file-sizes artifact.
- Artifacts: `evidence/qa-gates/phase2/app-py-line-count.md`, `evidence/qa-gates/phase2/bootstrap-line-count.md`, `evidence/qa-gates/phase8/file-sizes.md`.
