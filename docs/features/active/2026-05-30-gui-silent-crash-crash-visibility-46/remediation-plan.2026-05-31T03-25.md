# Remediation Plan — gui-silent-crash-crash-visibility (Issue #46), Cycle 2

- **Issue:** #46
- **Cycle:** 2
- **Entry Timestamp:** 2026-05-31T03-25
- **Plan Path:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-plan.2026-05-31T03-25.md`
- **Feature Folder:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/`
- **Mode:** full-bug (bug-fix remediation; `spec.md` required, `user-story.md` not required)

## Inputs

- Remediation inputs: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-inputs.2026-05-31T03-25.md`
- Policy audit: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/policy-audit.2026-05-31T03-25.md`
- Code review: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/code-review.2026-05-31T03-25.md`
- Feature audit: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/feature-audit.2026-05-31T03-25.md`
- Prior cycle inputs: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-inputs.2026-05-31T02-43.md`
- Prior cycle plan: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/remediation-plan.2026-05-31T02-43.md`
- Spec: `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- Test file in scope: `tests/gui/test_crash_handler.py` (HEAD `e17da56`, 549 lines)

## Scope (verbatim from remediation-inputs)

- **R5 (Blocking):** Split `tests/gui/test_crash_handler.py` (549 lines at HEAD `e17da56`) to restore the 500-line cap defined in `.claude/rules/general-code-change.md`. The cap applies to test code.
  - `tests/gui/test_crash_handler.py` retains: AC-1..AC-4 / AC-7 installer-contract tests, idempotency test, `resolve_log_dir` parametric test, Qt message-handler routing test. Approximate residual: 345 lines.
  - `tests/gui/test_crash_handler_closures.py` (NEW): the `_FakePath` / `_FakeHandle` fixture pair (lines 346-432 of the current file) plus the three R4 closure-invocation tests:
    - `test_sys_excepthook_appends_traceback_record`
    - `test_threading_excepthook_appends_traceback_record`
    - `test_append_traceback_swallows_oserror`
  - Re-import shared symbols at the top of the new file: `crash_handler`, `pytest`, `cast`, `Callable`, `Path`, `Any`, `threading`, `logging`, and `BytesIO`. No `# pyright: ignore` / `# noqa: B009` is needed — the closure tests already access private symbols via `vars(crash_handler)["..."]`.

## Hard Constraints

- No new dependency.
- No new `# noqa` / `# type: ignore` / `# pyright: ignore` markers anywhere in the diff.
- After the split, no file in the diff (production or test) may exceed 500 lines.
- The three R4 closure-invocation tests MUST continue to access private symbols via the same `vars(crash_handler)[...]` path. Do not change the access mechanism, do not remove the `cast` annotations, and do not rename the tests.
- The `_FakePath` / `_FakeHandle` fixture pair MUST be moved verbatim (docstrings, comments, and structure preserved); no behavior change.
- No runtime temporary files in tests. The in-memory `BytesIO` sink technique used in the current file MUST be preserved in the new file.
- All 737 tests must continue to pass after the split.
- `src/gui/_crash_handler.py` line and branch coverage MUST remain at 100% / 100% (the post-cycle-1 state).
- AC-12 spec text remains `[x]` on its literal production-only scope; this remediation enforces the cross-cutting cap defined in `.claude/rules/general-code-change.md` on test code.

## Mandatory Python Toolchain Loop (Required after every code change)

```
poetry run black .
poetry run ruff check .
poetry run pyright
poetry run pytest --cov --cov-branch --cov-report=term-missing
```

Restart the loop from `black` whenever any stage fails or any stage changes files. Phase 4 is the single-pass green gate.

## Plan Phases

### Phase 0 — Context, Policy Reads, and Baseline Capture

- [x] [P0-T1] Read the repository policy files in the canonical order: `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`, `.claude/rules/benchmark-baselines.md`, and `.claude/rules/ci-workflows.md`. Record the policy read at `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase0/instructions-read.md` with `Timestamp:` (`2026-05-31T03-25`), `Policy Order:` listing the files in the order above, and the explicit file list.
- [x] [P0-T2] Read the cycle-2 remediation inputs and the three audit artifacts (`remediation-inputs.2026-05-31T03-25.md`, `policy-audit.2026-05-31T03-25.md`, `code-review.2026-05-31T03-25.md`, `feature-audit.2026-05-31T03-25.md`) and acknowledge the sole finding (R5). Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase0/remediation-inputs-acknowledged.md` with `Timestamp:` and a verbatim quote of R5's `Definition of done`.
- [x] [P0-T3] Record the working baseline: current git branch, current `HEAD` commit SHA (expected `e17da56` or descendant), and the in-scope file list (`tests/gui/test_crash_handler.py`, `tests/gui/test_crash_handler_closures.py` (NEW), `tests/gui/test_app_composition.py`, `tests/gui/test_runners_threaded.py`, `tests/gui/test_pipeline_worker.py`, `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md`, `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md`). Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/branch-and-commit.md` with `Timestamp:`, `Command:` (`git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`), `EXIT_CODE:`, and `Output Summary:`.
- [x] [P0-T4] Capture pre-fix line counts of `tests/gui/test_crash_handler.py` from THREE independent counters and record them together so the measurement is double-checked. Run `wc -l tests/gui/test_crash_handler.py`, `awk 'END{print NR}' tests/gui/test_crash_handler.py`, and (PowerShell) `(Get-Content tests/gui/test_crash_handler.py).Count`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/test-crash-handler-line-count.md` with `Timestamp:`, `Command:` (all three commands listed), `EXIT_CODE:`, and `Output Summary:` (the three numeric results; expected to be 549 per the remediation inputs and to agree within +/- 1).
- [x] [P0-T5] Capture the pre-fix existence check of `tests/gui/test_crash_handler_closures.py` (expected: file does not exist). Run `git ls-files tests/gui/test_crash_handler_closures.py` and a filesystem check (e.g., `Test-Path tests/gui/test_crash_handler_closures.py`). Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/test-crash-handler-closures-pre-existence.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (expected: no output from `git ls-files`; `Test-Path` returns `False`).
- [x] [P0-T6] Baseline `poetry run black --check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail plus count of files that would be reformatted).
- [x] [P0-T7] Baseline `poetry run ruff check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`.
- [x] [P0-T8] Baseline `poetry run pyright`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error/warning/information counts).
- [x] [P0-T9] Baseline `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/remediation-baseline/pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` containing: headline pass/fail count (expected 737 passed), numeric total line coverage (>= 85%), numeric total branch coverage (>= 75%), and the per-file line/branch coverage for `src/gui/_crash_handler.py` (expected 100% / 100% per cycle-1 post-state).

### Phase 1 — R5: Create New `tests/gui/test_crash_handler_closures.py`

- [x] [P1-T1] Create the new file `tests/gui/test_crash_handler_closures.py`. The file MUST:
  - Begin with a module docstring describing purpose ("Closure-pinning tests for the crash-write closures and `_append_traceback` in `src.gui._crash_handler`. Split from `test_crash_handler.py` to keep both files under the 500-line cap defined in `.claude/rules/general-code-change.md`."), responsibilities (exercise `_make_sys_excepthook`, `_make_threading_excepthook`, and `_append_traceback`), and the determinism/isolation note (no temp files; `BytesIO`-backed sinks).
  - Include `from __future__ import annotations`.
  - Re-import the shared symbols required by the relocated code: `logging`, `threading`, `from io import BytesIO`, `from pathlib import Path`, `from typing import TYPE_CHECKING, Any, cast`, `import pytest`, `from src.gui import _crash_handler as crash_handler`, and a `TYPE_CHECKING` block for `from collections.abc import Callable` (matching the original file's import shape; verify by reading lines 1-50 of `tests/gui/test_crash_handler.py` before authoring).
  - Contain the `_FakePath` and `_FakeHandle` classes verbatim from the current `tests/gui/test_crash_handler.py` (lines 346-432: the block containing both class definitions and any preceding meta-what comment block on lines 339-344). Preserve all docstrings, inline comments, type hints, and class structure.
  - Contain the three closure-invocation tests verbatim from the current `tests/gui/test_crash_handler.py`:
    - `test_sys_excepthook_appends_traceback_record` (lines 435-470)
    - `test_threading_excepthook_appends_traceback_record` (lines 473-508)
    - `test_append_traceback_swallows_oserror` (lines 511-549)
  - The private-symbol access path in each test MUST remain `vars(crash_handler)["_make_sys_excepthook"]`, `vars(crash_handler)["_make_threading_excepthook"]`, and `vars(crash_handler)["_append_traceback"]` respectively. Do not introduce alternative access mechanisms.
  - Contain no `# noqa`, `# type: ignore`, or `# pyright: ignore` markers.
  - Be under 500 lines (expected size: ~210 lines = 87-line fixture block + 115-line test block + ~10-line imports/docstring header).
- [x] [P1-T2] Verify the new `tests/gui/test_crash_handler_closures.py` line count is <= 500 by running ALL THREE counters (`wc -l tests/gui/test_crash_handler_closures.py`, `awk 'END{print NR}' tests/gui/test_crash_handler_closures.py`, and `(Get-Content tests/gui/test_crash_handler_closures.py).Count`). Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase1/test-crash-handler-closures-line-count.md` with `Timestamp:`, `Command:` (all three commands listed), `EXIT_CODE:`, and `Output Summary:` listing the three numeric results. The task is satisfied only when all three counters return values <= 500 AND agree to within +/- 1.

### Phase 2 — R5: Trim `tests/gui/test_crash_handler.py` to Retain Only the Installer-Contract Tests

- [x] [P2-T1] Modify `tests/gui/test_crash_handler.py` to delete the lines moved to `tests/gui/test_crash_handler_closures.py` in P1-T1. The deletion MUST:
  - Remove the `_FakePath` class definition (and any preceding meta-what comment block introducing the fixture pair).
  - Remove the `_FakeHandle` class definition.
  - Remove `test_sys_excepthook_appends_traceback_record`.
  - Remove `test_threading_excepthook_appends_traceback_record`.
  - Remove `test_append_traceback_swallows_oserror`.
  - Preserve unchanged: AC-1..AC-4 / AC-7 installer-contract tests, idempotency test, `resolve_log_dir` parametric test, Qt message-handler routing test, the module docstring, and all top-of-file imports that remain in use by the retained tests.
  - Remove from the top-of-file imports any symbol that is no longer referenced by the retained tests after the deletion. Identification rule: after deletion, grep the trimmed file body for each top-of-file import name; remove any import whose name no longer appears in the body. Candidates likely to become unused after the split (verify each): `BytesIO`, `threading`, `logging`, `cast`, `Any`, `Callable` (under `TYPE_CHECKING`). Do NOT remove imports still referenced by retained tests (e.g., `pytest`, `Path`, `crash_handler`).
- [x] [P2-T2] Verify the trimmed `tests/gui/test_crash_handler.py` line count is <= 500 by running ALL THREE counters (`wc -l tests/gui/test_crash_handler.py`, `awk 'END{print NR}' tests/gui/test_crash_handler.py`, and `(Get-Content tests/gui/test_crash_handler.py).Count`). Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase2/test-crash-handler-line-count.md` with `Timestamp:`, `Command:` (all three commands listed), `EXIT_CODE:`, and `Output Summary:` listing the three numeric results. The task is satisfied only when all three counters return values <= 500 AND agree to within +/- 1. Expected residual count: ~345 lines per the remediation inputs.

### Phase 3 — Verify No New Suppression Markers Introduced

- [x] [P3-T1] Compare suppression markers in the workspace diff against the cycle-2 entry baseline by running:
  ```
  git diff HEAD -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'
  ```
  Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase3/suppression-diff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:` (expected non-zero from `grep` when there are zero matches), and `Output Summary:` confirming zero added suppression markers. The task fails if any line in the diff contains a new `# noqa`, `# type: ignore`, or `# pyright: ignore` marker.

### Phase 4 — Final Single-Pass QA Loop

- [x] [P4-T1] Run `poetry run black --check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/black.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming all files pass formatting in a single pass. If the check fails, run `poetry run black .` (without `--check`), overwrite the artifact, and restart the loop from P4-T1.
- [x] [P4-T2] Run `poetry run ruff check .`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming zero lint findings. If non-zero, fix the lint findings and restart from P4-T1.
- [x] [P4-T3] Run `poetry run pyright`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` confirming zero errors, zero warnings, zero informations (or matching the cycle-1 post-state counts when not all categories are gated). If non-zero, fix the type findings and restart from P4-T1.
- [x] [P4-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE: 0`, and `Output Summary:` containing:
  - The headline pass/fail count (MUST be `737 passed`).
  - The numeric total line coverage (>= 85%).
  - The numeric total branch coverage (>= 75%).
  - The per-file line and branch coverage for `src/gui/_crash_handler.py` (MUST be 100% / 100%; no regression versus the cycle-1 post-state captured in `evidence/qa-gates/phase8/pytest.md`).
  - Confirmation that all three relocated tests (`test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror`) are collected from `tests/gui/test_crash_handler_closures.py` (e.g., via a one-line grep against the pytest collection output or against the verbose test list).
  - If the test run fails, the pass count is not 737, or coverage regresses, restart the loop from P4-T1.
- [x] [P4-T5] Persist a single-pass summary `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/single-pass-summary.md` with `Timestamp:`, a four-line summary citing the `EXIT_CODE` for each of P4-T1..P4-T4 (all `0`), and a final `Single-Pass Result:` field reading `PASS` only when all four artifacts above record `EXIT_CODE: 0` from the same loop iteration. The task is satisfied only when `Single-Pass Result: PASS`.

### Phase 5 — Regenerate Phase 8 File-Sizes Evidence (Include Test Files)

- [x] [P5-T1] Regenerate `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md` IN PLACE so the post-fix table includes the five production files already recorded plus all four test files referenced by the remediation inputs. The artifact MUST:
  - Update `Timestamp:` to `2026-05-31T03-25` and retain the existing `Corrected At:` semantics by adding a `Last Updated:` field set to `2026-05-31T03-25`.
  - Use `Command:` lines: `wc -l <path>` (per file) and `awk 'END{print NR}' <path>` (per file; both counters cross-verified) and add a third counter line citing `(Get-Content <path>).Count` (PowerShell) so the triple-verification rule from the remediation inputs is satisfied.
  - Replace the existing `## Results` table with a single table containing rows for, in order:
    - `src/gui/_crash_handler.py`
    - `src/gui/_crash_handler_bootstrap.py`
    - `src/gui/runners.py`
    - `src/gui/workers/pipeline_worker.py`
    - `src/gui/app.py`
    - `tests/gui/test_crash_handler.py`
    - `tests/gui/test_crash_handler_closures.py`
    - `tests/gui/test_runners_threaded.py`
    - `tests/gui/test_pipeline_worker.py`
    - `tests/gui/test_app_composition.py`
  - Column shape: `File | Baseline | Post-change | Under 500-line cap`. The `Baseline` column for `tests/gui/test_crash_handler.py` MUST cite `549` (cycle-2 entry state). The `Baseline` column for `tests/gui/test_crash_handler_closures.py` MUST cite `0 (NEW)`. Every row in the `Under 500-line cap` column MUST show `PASS`.
  - Add or update the `## Notes` section to record: (a) the cap policy reference (`.claude/rules/general-code-change.md`), (b) the cycle-2 driver (R5), (c) a back-reference to the cycle-1 phase4 corrected file-sizes artifact at `evidence/qa-gates/phase4/file-sizes.md`, and (d) confirmation that `wc -l`, `awk 'END{print NR}'`, and `(Get-Content).Count` agree on every line count.
- [x] [P5-T2] Verify the regenerated phase8 file-sizes table is internally consistent by re-running `wc -l` and `awk 'END{print NR}'` against each of the ten files in the table and recording the second-pass results. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase5/file-sizes-verification.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` confirming the second-pass counts match the values written into `phase8/file-sizes.md` in P5-T1.

### Phase 6 — Regenerate Phase 8 Pytest Evidence (Post-Split)

- [x] [P6-T1] Regenerate `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md` IN PLACE so it reflects the post-split run captured in P4-T4. The artifact MUST:
  - Update `Timestamp:` to `2026-05-31T03-25`.
  - Cite `Command:` `poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  - Set `EXIT_CODE: 0`.
  - In `Output Summary:`, record the headline `737 passed`, the numeric total line coverage, the numeric total branch coverage, and the per-file line/branch coverage for `src/gui/_crash_handler.py` (MUST be 100% / 100%; explicit statement of no regression versus the cycle-1 post-state).
  - Add a `## Notes` section confirming that the three closure-invocation tests are now collected from `tests/gui/test_crash_handler_closures.py` (cite the pytest collection output) and that the total test count is unchanged versus the cycle-1 post-state.
- [x] [P6-T2] Cross-check the regenerated `phase8/pytest.md` against the P4-T4 `phase4/pytest.md` artifact: assert the headline pass count matches, the total line and branch coverage values match, and the `src/gui/_crash_handler.py` per-file coverage matches. Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase6/pytest-cross-check.md` with `Timestamp:`, `Command:` (the diff or grep used), `EXIT_CODE:`, and `Output Summary:` confirming the two artifacts agree on every checked value.

### Phase 7 — AC Re-Evaluation in `spec.md`

- [x] [P7-T1] In `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`, re-evaluate AC-12 (line 225) under its existing `[x]` checkbox. AC-12 spec text is production-only ("No production file in the diff exceeds 500 lines") and remains satisfied without text change. Add a one-line note under AC-12 pointing to the cycle-2 R5 remediation (the cross-cutting cap defined in `.claude/rules/general-code-change.md` is now enforced on test code via the split into `tests/gui/test_crash_handler.py` + `tests/gui/test_crash_handler_closures.py`) and citing `evidence/qa-gates/phase8/file-sizes.md` as the verification artifact.
- [x] [P7-T2] Update the `Last Updated:` field in `spec.md` to `2026-05-31T03-25`.
- [x] [P7-T3] Persist `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase7/ac-reeval.md` with `Timestamp:`, AC-12 status, and a `Status:` line citing the evidence artifact paths that support the status (`evidence/qa-gates/phase8/file-sizes.md`, `evidence/qa-gates/phase4/single-pass-summary.md`, `evidence/qa-gates/phase8/pytest.md`).

## AC Traceability Matrix

| AC | Spec Text Pointer | Audit Finding | Remediating Tasks | Verification Evidence |
|---|---|---|---|---|
| AC-12 (file-size cap) | `spec.md` line 225 (`No production file in the diff exceeds 500 lines.`) | Policy audit F5 / Code review Blocking / Feature audit AC-12 PARTIAL — `tests/gui/test_crash_handler.py` is 549 lines after the cycle-1 R4 closure-pinning tests were added. The cross-cutting cap in `.claude/rules/general-code-change.md` applies to test code. AC-12 spec text remains satisfied on its literal production-only scope. | P1-T1 (create `test_crash_handler_closures.py` with verbatim relocation of `_FakePath`/`_FakeHandle` and the three R4 tests), P1-T2 (triple-counter line-count verification of the new file), P2-T1 (trim `test_crash_handler.py` and prune now-unused imports), P2-T2 (triple-counter line-count verification of the trimmed file), P3-T1 (no new suppression markers), P4-T1..P4-T5 (single-pass green QA loop with 737 passed and `_crash_handler.py` at 100%/100% coverage), P5-T1 (regenerate `phase8/file-sizes.md` to include the four test files plus the bootstrap module), P5-T2 (second-pass verification of the regenerated table), P6-T1 (regenerate `phase8/pytest.md` post-split), P6-T2 (cross-check phase4 vs phase8 pytest evidence), P7-T1 (AC-12 spec note pointing to the cycle-2 remediation), P7-T2 (`Last Updated:` bump), P7-T3 (AC re-eval evidence). | `evidence/qa-gates/phase1/test-crash-handler-closures-line-count.md`, `evidence/qa-gates/phase2/test-crash-handler-line-count.md`, `evidence/qa-gates/phase3/suppression-diff.md`, `evidence/qa-gates/phase4/black.md`, `evidence/qa-gates/phase4/ruff.md`, `evidence/qa-gates/phase4/pyright.md`, `evidence/qa-gates/phase4/pytest.md`, `evidence/qa-gates/phase4/single-pass-summary.md`, `evidence/qa-gates/phase5/file-sizes-verification.md`, `evidence/qa-gates/phase6/pytest-cross-check.md`, `evidence/qa-gates/phase7/ac-reeval.md`, `evidence/qa-gates/phase8/file-sizes.md` (regenerated), `evidence/qa-gates/phase8/pytest.md` (regenerated) |

## Notes for Executor

- All evidence artifacts MUST be written under `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/<kind>/` per the canonical `evidence-and-timestamp-conventions` scheme. Writing to `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical path is a policy violation and will be caught by the PreToolUse hook.
- The toolchain loop in Phase 4 is the single-pass green gate. Partial passes do not satisfy P4-T5. If any stage changes files or fails, restart from P4-T1.
- The R5 split MUST not change observable test behavior. The three relocated tests must continue to pass with identical assertions, identical private-symbol access via `vars(crash_handler)[...]`, and identical in-memory `BytesIO` sink technique. The total collected test count must remain at 737.
- The `_FakePath` / `_FakeHandle` fixture pair is relocated verbatim. If `pyright` or `ruff` reports a finding in the new file that did not exist in the original, the cause is almost certainly a missing or misordered import in `tests/gui/test_crash_handler_closures.py` — fix the import block (do not add suppressions).
- Phase 5 regenerates the existing `phase8/file-sizes.md` artifact in place. Do not create a sibling timestamped file; the artifact is overwritten with a refreshed timestamp and expanded results table per the plan-path-continuity rule.
- Phase 6 regenerates the existing `phase8/pytest.md` artifact in place under the same overwrite-with-fresh-timestamp rule.
- The cycle-2 entry baseline is `HEAD = e17da56` per the remediation inputs. P0-T3 records the actual `HEAD` SHA at the time of execution so the cycle-2 diff is auditable end-to-end.
