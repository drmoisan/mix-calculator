# Remediation Plan — gui-silent-crash-crash-visibility (Issue #46), Cycle 1

- **Issue:** #46
- **Cycle:** 1
- **Entry Timestamp:** 2026-05-31T02-43
- **Plan Path:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-plan.2026-05-31T02-43.md`
- **Feature Folder:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/`
- **Mode:** full-bug (bug-fix remediation; spec.md is required, user-story.md not required)

## Inputs

- Remediation inputs: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-inputs.2026-05-31T02-43.md`
- Policy audit: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/policy-audit.2026-05-31T02-43.md`
- Code review: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/code-review.2026-05-31T02-43.md`
- Feature audit: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/feature-audit.2026-05-31T02-43.md`
- Spec: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- Original plan: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/plan.2026-05-30T22-45.md`

## Scope (verbatim from remediation-inputs)

- **R1 (Blocking):** Reduce `src/gui/app.py` (currently 503 lines) to <= 500 lines by extracting the crash-handler bootstrap into `src/gui/_crash_handler_bootstrap.py` exposing `install_for_main() -> None`. No observable behavior change.
- **R2 (Material):** Update `spec.md` to use `resolve_log_dir` (drop the leading underscore) wherever the substring `_resolve_log_dir` appears. Documentation-only.
- **R3 (Material):** Regenerate `evidence/qa-gates/phase4/file-sizes.md` using `wc -l` / `awk NR` / `(Get-Content <path>).Count` (not PowerShell `Measure-Object -Line`). Add a corrected post-fix counterpart under `evidence/qa-gates/phase8/file-sizes.md`.
- **R4 (Material):** Add three tests in `tests/gui/test_crash_handler.py` so the crash-write closures and `_append_traceback` are invoked under test:
  - `test_sys_excepthook_appends_traceback_record`
  - `test_threading_excepthook_appends_traceback_record`
  - `test_append_traceback_swallows_oserror`

## Hard Constraints

- No new dependency.
- No new `# noqa` / `# type: ignore` / `# pyright: ignore` markers.
- The new helper module `src/gui/_crash_handler_bootstrap.py` must be Pyright-clean with full type hints, must be < 500 lines, and must expose only `install_for_main() -> None`. It imports `install_crash_handlers` from `src.gui._crash_handler` and calls it with `app_name="mix-calculator"`. The returned `CrashHandlerInstallation` is held on a module-level private name to keep the faulthandler file descriptor alive (mirrors the prior in-line `_crash_installation = ...; del _crash_installation` semantics, where the value is in fact anchored by the installer's `_State`; keeping a module-level reference here is functionally equivalent and harmless).
- The composition-root test `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` in `tests/gui/test_app_composition.py` MUST continue to pass. Because the call has moved into the new module, the test must be retargeted to patch `install_crash_handlers` on the `_crash_handler_bootstrap` module (not `app_module`), so the recorder still intercepts the call and the assertions hold.
- Spec text change in R2: replace every occurrence of the substring `_resolve_log_dir` with `resolve_log_dir` in `spec.md`. Identified occurrences are at lines 103, 176, 180, 202, and 206 of the current spec.
- R3 evidence: rewrite `evidence/qa-gates/phase4/file-sizes.md` in place with corrected counts and an inline correction note pointing at the original `Measure-Object`-based command. Add a fresh `evidence/qa-gates/phase8/file-sizes.md` with the post-fix counts. (No `phase4/_raw/file-sizes.log` exists in the feature folder; the correction note is recorded inline.)
- R4 tests: follow `.claude/rules/general-unit-test.md` — no runtime temporary files. Use `BytesIO`-backed sinks or `monkeypatch` to redirect file opens to in-memory buffers. `tmp_path` is not used.

## Mandatory Python Toolchain Loop (Required after every production-file change)

```
poetry run black .
poetry run ruff check .
poetry run pyright
poetry run pytest --cov --cov-branch --cov-report=term-missing
```

Restart the loop from `black` whenever any stage fails or any stage changes files. Phase 8 is the single-pass green gate.

## Plan Phases

### Phase 0 — Context, Policy Reads, and Baseline Capture

- [x] [P0-T1] Read `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`, `.claude/rules/benchmark-baselines.md`, and `.claude/rules/ci-workflows.md`. Record the policy read in `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase0/instructions-read.md` with `Timestamp:`, `Policy Order:` (in the order above), and the explicit file list.
- [x] [P0-T2] Read the cycle-1 remediation inputs and the three audit artifacts (`remediation-inputs.2026-05-31T02-43.md`, `policy-audit.2026-05-31T02-43.md`, `code-review.2026-05-31T02-43.md`, `feature-audit.2026-05-31T02-43.md`) and acknowledge the four findings (R1–R4) in `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase0/remediation-inputs-acknowledged.md` with `Timestamp:` and a verbatim quote of each finding's `Definition of done`.
- [x] [P0-T3] Record the working baseline: current git branch, current `HEAD` commit SHA, and the in-scope file list (`src/gui/app.py`, `src/gui/_crash_handler.py`, `tests/gui/test_crash_handler.py`, `tests/gui/test_app_composition.py`, `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`, `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md`). Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/branch-and-commit.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T4] Capture baseline line counts of `src/gui/app.py` from THREE independent counters and record them together so the measurement is double-checked. Run `wc -l src/gui/app.py`, `awk 'END{print NR}' src/gui/app.py`, and (PowerShell) `(Get-Content src/gui/app.py).Count`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/app-py-line-count.md` with `Timestamp:`, `Command:` (all three commands listed), `EXIT_CODE:`, and `Output Summary:` (the three numeric results, expected to be 503 per the remediation inputs).
- [x] [P0-T5] Baseline `poetry run black --check .`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail + count of files that would be reformatted).
- [x] [P0-T6] Baseline `poetry run ruff check .`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T7] Baseline `poetry run pyright`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning/information counts).
- [x] [P0-T8] Baseline `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` containing the headline pass/fail count AND numeric total line and branch coverage percentages (policy: >= 85% line, >= 75% branch).

### Phase 1 — R3a: Correct the Phase 4 File-Sizes Evidence

- [x] [P1-T1] Recompute the line counts for `src/gui/app.py`, `src/gui/_crash_handler.py`, `src/gui/runners.py`, and `src/gui/workers/pipeline_worker.py` using `wc -l` (and verify with `awk 'END{print NR}'`). Record the four numeric results in a working scratchpad inside the task evidence; do not yet modify the phase4 artifact.
- [x] [P1-T2] Rewrite `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md` in place. Replace the `Command:` line with the corrected command (`wc -l` per file; verified with `awk 'END{print NR}'`). Replace the per-file counts with the values measured in P1-T1. Add an inline `## Correction Note` section that records: the original (incorrect) command `pwsh -NoProfile -Command "(Get-Content <path> | Measure-Object -Line).Lines"`, the reason for correction (Measure-Object -Line counts line-terminator characters and drops the trailing partial line; cited in policy audit F3 and code review), and a pointer back to this remediation plan (`remediation-plan.2026-05-31T02-43.md`, R3). Keep the artifact's `Timestamp:` header but add a new `Corrected At:` field set to `2026-05-31T02-43`. Re-evaluate the per-file `PASS / FAIL` column against the 500-line cap honestly: `src/gui/app.py` MUST be marked over-cap at this point in the plan (R1 has not been applied yet).

### Phase 2 — R1: Extract Crash-Handler Bootstrap and Restore the 500-Line Cap

- [x] [P2-T1] Create new module `src/gui/_crash_handler_bootstrap.py`. The module MUST:
  - Be Pyright-clean with full type hints.
  - Include a top-of-file module docstring describing purpose, responsibilities, and the rationale for the module-level anchor (keeping the `CrashHandlerInstallation` reachable so the faulthandler file descriptor is not collected; documents the parity with the prior in-line `_crash_installation = ...; del _crash_installation` pattern).
  - Import `install_crash_handlers` from `src.gui._crash_handler`.
  - Expose exactly one public symbol: `install_for_main() -> None`. `install_for_main` has a full Google-style docstring (`Args:` none, `Returns:` `None`, `Side effects:` registers the four crash hooks via `install_crash_handlers(app_name="mix-calculator")` and stores the returned installation on a module-level private name so the faulthandler file handle is not garbage-collected before process exit).
  - Hold the returned installation on a module-level private name (for example `_INSTALLATION: CrashHandlerInstallation | None = None`, mutated inside `install_for_main` via `global _INSTALLATION`).
  - Be under 500 lines (expected size: under 50 lines).
  - Use no `# noqa`, `# type: ignore`, or `# pyright: ignore` markers.
  - Set `__all__ = ["install_for_main"]`.
- [x] [P2-T2] Modify `src/gui/app.py`: replace the four-line block at lines 483–489 (the crash-visibility installer comment block + `_crash_installation = install_crash_handlers(app_name="mix-calculator")` + `del _crash_installation`) with a single call `install_for_main()`. Add the import `from src.gui._crash_handler_bootstrap import install_for_main` to the import block (alphabetical order). Remove the now-unused import `from src.gui._crash_handler import install_crash_handlers` from `src/gui/app.py` ONLY IF no other code in the file references it (verify by grep within the file; the file is expected to be free of other references once the bootstrap call is the only consumer). Preserve the inline comment that explains AC-8 ordering (crash hooks installed BEFORE QApplication construction) directly above the new `install_for_main()` call.
- [x] [P2-T3] Retarget the composition-root test `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name` in `tests/gui/test_app_composition.py`: change the `monkeypatch.setattr(app_module, "install_crash_handlers", _record_install)` line to patch the symbol on the bootstrap module instead, i.e. `from src.gui import _crash_handler_bootstrap as crash_bootstrap_module` (added near the existing `from src.gui import app as app_module` lines inside the test function) and `monkeypatch.setattr(crash_bootstrap_module, "install_crash_handlers", _record_install)`. All assertion lines remain unchanged: the recorder must still be invoked exactly once with `{"app_name": "mix-calculator"}`, and the event log ordering `install_crash_handlers` < `qapplication_init` must still hold. Add a single explanatory comment above the patch line noting that `main()` now invokes the installer through `_crash_handler_bootstrap.install_for_main()`, so the patch site is the bootstrap module.
- [x] [P2-T4] Verify the new `src/gui/app.py` line count is <= 500 by running ALL THREE counters (`wc -l src/gui/app.py`, `awk 'END{print NR}' src/gui/app.py`, and `(Get-Content src/gui/app.py).Count`). Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase2/app-py-line-count.md` with `Timestamp:`, `Command:` (all three), `EXIT_CODE:`, and `Output Summary:` listing the three numeric results. The task is satisfied only when all three counters return values <= 500 AND agree to within +/- 1.
- [x] [P2-T5] Verify the new `src/gui/_crash_handler_bootstrap.py` line count is under 500 by running `wc -l src/gui/_crash_handler_bootstrap.py` and `awk 'END{print NR}' src/gui/_crash_handler_bootstrap.py`. Persist as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase2/bootstrap-line-count.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P2-T6] Run the mandatory Python toolchain loop after the P2 production-code changes: `poetry run black .` then `poetry run ruff check .` then `poetry run pyright` then `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist four artifacts under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase2/`: `black.md`, `ruff.md`, `pyright.md`, `pytest.md`. Each artifact MUST include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. The `pytest.md` `Output Summary:` MUST include the headline pass/fail count, the numeric total line coverage, and the numeric total branch coverage. If any stage fails or changes files, restart the loop from `black` and overwrite the four artifacts in place; the task is satisfied only when all four stages complete in a single pass.

### Phase 3 — R2: Update Spec to Use `resolve_log_dir`

- [x] [P3-T1] In `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`, replace every occurrence of the substring `_resolve_log_dir` with `resolve_log_dir`. The five known occurrences are at lines 103, 176, 180, 202, and 206. After the edit, grep the file for `_resolve_log_dir` and confirm the count is zero.
- [x] [P3-T2] Update the `Last Updated:` field in `spec.md` (currently `2026-05-30T23-30`) to `2026-05-31T02-43`.
- [x] [P3-T3] Persist verification evidence as `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase3/spec-resolve-log-dir.md` with `Timestamp:`, `Command:` (the grep command used: `grep -n '_resolve_log_dir' docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`), `EXIT_CODE:` (expected non-zero from grep when there are zero matches), and `Output Summary:` confirming zero occurrences and listing the post-fix `resolve_log_dir` matches by line number.

### Phase 4 — R4: Pin Crash-Write Closure Bodies with Direct Invocation Tests

- [x] [P4-T1] In `tests/gui/test_crash_handler.py`, add `test_sys_excepthook_appends_traceback_record`. The test MUST:
  - Build a sink: a `BytesIO` instance (or a small `io.StringIO`-backed wrapper opened via `monkeypatch.setattr(Path, "open", ...)`) that captures bytes written when `_append_traceback` opens the crash log.
  - Construct the hook via `crash_handler._make_sys_excepthook(crash_log_path, lambda *_: None)` where `crash_log_path` is a `Path` whose `.open` is monkeypatched at the `Path` class level (or replaced via a wrapper class) to return the sink instead of touching the filesystem.
  - Invoke the hook with a synthesized `(ValueError, ValueError("boom"), None)` triple.
  - Assert the sink content (`sink.getvalue().decode("utf-8")` or equivalent) contains the substring `sys.excepthook`, the substring `ValueError`, and the substring `boom`.
  - Use no temp files, no real filesystem writes, no `tempfile` usage, and no new `# noqa`/`# type: ignore` markers. Include an Arrange-Act-Assert layout per `.claude/rules/general-unit-test.md`.
  - Include a docstring stating: "AC-10 (informational): exercises the `sys.excepthook` closure built by `_make_sys_excepthook` end-to-end, ensuring `_append_traceback` is invoked and writes the expected record."
- [x] [P4-T2] In `tests/gui/test_crash_handler.py`, add `test_threading_excepthook_appends_traceback_record`. The test MUST:
  - Build a sink using the same in-memory technique as P4-T1.
  - Construct the hook via `crash_handler._make_threading_excepthook(crash_log_path, lambda _args: None)`.
  - Build a `threading.ExceptHookArgs` instance with a `ValueError("boom")` exception value and a named `threading.Thread` (e.g. `threading.Thread(name="test-worker")`), then invoke the hook.
  - Assert the captured content contains the substrings `threading.excepthook`, `ValueError`, `boom`, and `test-worker`.
  - Add a second assertion that the previous-hook callable was invoked exactly once with the same args (use a list recorder closure as the `previous` argument).
  - Use no temp files, no real filesystem writes, no new suppression markers. Arrange-Act-Assert layout. Docstring states: "AC-10 (informational): exercises the `threading.excepthook` closure built by `_make_threading_excepthook`."
- [x] [P4-T3] In `tests/gui/test_crash_handler.py`, add `test_append_traceback_swallows_oserror`. The test MUST:
  - Build a `Path`-like object whose `.open` raises `OSError("disk full")` when called. Use `monkeypatch.setattr` on the `Path.open` method scoped to a specific `Path` instance (via wrapper class) or patch `Path.open` globally and restore via `monkeypatch.context()`. Do not write to disk.
  - Use `caplog.at_level(logging.ERROR, logger="src.gui._crash_handler")` to capture the module logger output.
  - Call `crash_handler._append_traceback(crash_log_path, source="sys.excepthook", exc_type=ValueError, exc_value=ValueError("boom"), exc_tb=None)`.
  - Assert no exception propagates out of the call.
  - Assert `caplog.records` contains at least one record whose `levelno == logging.ERROR` and whose message contains `Failed to append crash record`.
  - Use no temp files, no new suppression markers. Arrange-Act-Assert layout. Docstring states: "AC-10 (informational): `_append_traceback` swallows `OSError` from the log open and reports it through the module logger so a write failure cannot cascade into a second crash."
- [x] [P4-T4] Run the mandatory Python toolchain loop after the P4 test additions: `poetry run black .` then `poetry run ruff check .` then `poetry run pyright` then `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist four artifacts under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/`: `black-post-r4.md`, `ruff-post-r4.md`, `pyright-post-r4.md`, `pytest-post-r4.md`. Each artifact MUST include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. The `pytest-post-r4.md` `Output Summary:` MUST include the headline pass/fail count AND numeric total line and branch coverage values. The task is satisfied only when all four stages complete in a single pass. (These filenames are suffixed `-post-r4` so they do not collide with the pre-existing `phase4/file-sizes.md` corrected by P1-T2.)

### Phase 5 — R3b: Add Post-Fix Phase 8 File-Sizes Evidence

- [x] [P5-T1] Generate `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md` with the post-fix counts for `src/gui/app.py`, `src/gui/_crash_handler.py`, `src/gui/_crash_handler_bootstrap.py`, `src/gui/runners.py`, and `src/gui/workers/pipeline_worker.py`. Use both `wc -l <path>` and `awk 'END{print NR}' <path>` per file and record both results so the measurement is double-checked. Include `Timestamp:` (`2026-05-31T02-43`), `Command:` (both commands), `EXIT_CODE:`, and a results table identical in shape to the corrected phase4 artifact: columns `File | Baseline | Post-change | Under 500-line cap`. Every row MUST show PASS for the 500-line cap. Add an inline `## Notes` section that points back to the corrected phase4 artifact and explains that phase8 captures the post-R1 state.

### Phase 6 — AC Re-Evaluation in `spec.md`

- [x] [P6-T1] In `spec.md`, re-evaluate the three ACs flagged by the audits (AC-1, AC-10, AC-12) under their existing checklist items. Confirm `AC-1` text now uses `resolve_log_dir` (post P3-T1) and that the checkbox remains `[x]`. Confirm `AC-10` checkbox remains `[x]` and add a one-line note under it pointing to the three new tests added in Phase 4 (`tests/gui/test_crash_handler.py::test_sys_excepthook_appends_traceback_record`, `::test_threading_excepthook_appends_traceback_record`, `::test_append_traceback_swallows_oserror`). Confirm `AC-12` checkbox remains `[x]` and add a one-line note pointing to the `src/gui/_crash_handler_bootstrap.py` extraction and the phase8 file-sizes artifact. No other AC text changes.
- [x] [P6-T2] Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase6/ac-reeval.md` with `Timestamp:`, the three AC IDs re-evaluated, and a per-AC `Status:` line citing the evidence artifact path that supports the status.

### Phase 7 — Re-Verify No New Suppressions Introduced

- [x] [P7-T1] Compare the suppression markers in the workspace against the `HEAD` baseline captured in P0-T3 by running:
  ```
  git diff HEAD -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'
  ```
  Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase7/suppression-diff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:` (expected non-zero: no added suppression lines), and `Output Summary:` confirming zero added suppression markers. The task fails if any line in the diff contains a new suppression marker.

### Phase 8 — Final Single-Pass QA Loop

- [x] [P8-T1] Run `poetry run black --check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/black.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming all files pass formatting in a single pass. If the check fails, run `poetry run black .` (without `--check`), then restart the loop from P8-T1.
- [x] [P8-T2] Run `poetry run ruff check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming zero lint findings. If non-zero, fix the lint findings and restart the loop from P8-T1.
- [x] [P8-T3] Run `poetry run pyright`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming zero errors, zero warnings, zero informations (or matching the existing baseline counts when not all categories are gated). If non-zero, fix the type findings and restart from P8-T1.
- [x] [P8-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` containing the headline pass/fail count, the numeric total line coverage (MUST be >= 85%), the numeric total branch coverage (MUST be >= 75%), and the new-code coverage for `src/gui/_crash_handler_bootstrap.py` and `src/gui/_crash_handler.py` (the latter expected to improve relative to baseline because the three new tests in Phase 4 exercise previously-uncovered closure bodies). If the test run fails or coverage regresses on the changed lines, restart the loop from P8-T1.
- [x] [P8-T5] Persist a single-pass summary `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/single-pass-summary.md` with `Timestamp:`, a four-line summary citing the EXIT_CODE for each of P8-T1..P8-T4, and a final `Single-Pass Result:` field reading `PASS` only when all four artifacts above record `EXIT_CODE: 0` from the same loop iteration. The task is satisfied only when `Single-Pass Result: PASS`.

### Phase 9 — Coverage Delta Verification

- [x] [P9-T1] Compute the coverage delta between the P0-T8 baseline and the P8-T4 post-change run for: (a) repo-wide total line coverage, (b) repo-wide total branch coverage, (c) per-file line coverage for `src/gui/_crash_handler.py`, and (d) per-file line coverage for `src/gui/app.py`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase9/coverage-delta.md` with `Timestamp:`, `Command:` (cites the two `poetry run pytest --cov --cov-branch --cov-report=term-missing` runs), `EXIT_CODE: 0`, and `Output Summary:` containing baseline percent, post-change percent, and absolute delta for each of (a)–(d). The task is satisfied only when (a) and (b) are >= policy thresholds (>= 85% line, >= 75% branch), and when (c) shows non-negative line coverage delta versus baseline (the three new closure-body tests must not regress crash-handler coverage) and (d) shows non-negative line coverage delta versus baseline.

## AC Traceability Matrix (re-citing the audit-flagged ACs)

| AC | Spec Text Pointer | Audit Finding | Remediating Tasks | Verification Evidence |
|---|---|---|---|---|
| AC-1 (crash-handler module exists; `resolve_log_dir` helper) | `spec.md` line 202 (post-fix) | Policy audit F2 / Code review Material / Feature audit AC-1 PARTIAL — spec said `_resolve_log_dir`, implementation exposes `resolve_log_dir`. | P3-T1 (spec text replacement), P3-T2 (spec `Last Updated:`), P3-T3 (grep verification), P6-T1 (AC re-eval) | `evidence/qa-gates/phase3/spec-resolve-log-dir.md`, `evidence/qa-gates/phase6/ac-reeval.md` |
| AC-10 (worker-thread exception captured and traceback recorded) | `spec.md` AC-10 checklist item | Policy audit F4 / Code review Material / Feature audit AC-10 PARTIAL (informational) — crash-write closures and `_append_traceback` were never invoked by tests. | P4-T1, P4-T2, P4-T3 (three new direct-invocation tests), P4-T4 (post-test toolchain loop), P6-T1 (AC re-eval note pointing to the three tests) | `tests/gui/test_crash_handler.py` (new tests), `evidence/qa-gates/phase4/pytest-post-r4.md`, `evidence/qa-gates/phase8/pytest.md`, `evidence/qa-gates/phase9/coverage-delta.md`, `evidence/qa-gates/phase6/ac-reeval.md` |
| AC-12 (file-size cap: every changed production file <= 500 lines) | `spec.md` AC-12 checklist item | Policy audit F1 / Code review Blocking / Feature audit AC-12 FAIL — `src/gui/app.py` was 503 lines; phase4 evidence reported 439 due to `Measure-Object -Line` undercount. | P1-T1, P1-T2 (R3a — regenerate phase4 evidence with correct command), P2-T1 (new `_crash_handler_bootstrap.py`), P2-T2 (replace inline block in `app.py`), P2-T3 (retarget composition-root test patch site), P2-T4 (triple-counter verification of `app.py` <= 500), P2-T5 (verify bootstrap module < 500), P2-T6 (post-R1 toolchain loop), P5-T1 (phase8 file-sizes artifact), P6-T1 (AC re-eval) | `evidence/qa-gates/phase4/file-sizes.md` (corrected, R3a), `evidence/qa-gates/phase2/app-py-line-count.md`, `evidence/qa-gates/phase2/bootstrap-line-count.md`, `evidence/qa-gates/phase8/file-sizes.md`, `evidence/qa-gates/phase6/ac-reeval.md`, `evidence/qa-gates/phase2/pytest.md`, `evidence/qa-gates/phase8/pytest.md` |

## Notes for Executor

- All evidence artifacts MUST be written under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/` per the canonical evidence-and-timestamp conventions. Writing to `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical path is a policy violation.
- The toolchain loop in Phase 8 is the green-in-a-single-pass gate; partial passes do not satisfy P8-T5.
- The R1 extraction MUST not change observable behavior. The composition-root test in `tests/gui/test_app_composition.py` was originally passing because `app_module.install_crash_handlers` was the symbol called by `main()`; after R1, the call site is `crash_bootstrap_module.install_crash_handlers`, so the patch target moves to that module. The recorder's call assertions remain identical.
- The R4 tests are intentionally written so the three previously-uncovered code paths (lines 254–263, 290–303, 374–383 in `src/gui/_crash_handler.py`) execute under test. The coverage delta verification in Phase 9 confirms the per-file line coverage does not regress as a result.
