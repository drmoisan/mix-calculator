# Policy Audit — mix-pipeline-gui v2 EXIT (Issue #19)

- **Timestamp:** 2026-05-29T00-02
- **Cycle:** 1 EXIT audit (post-remediation)
- **Branch:** feature/mix-pipeline-gui-19
- **Base:** main (merge-base used by PR context)
- **Audit scope:** Full feature branch (working tree) vs. main, v2 post-remediation head
- **Work Mode:** full-feature (from `v2/issue.md`)
- **AC Source:** `v2/spec.md` + `v2/user-story.md` (mode-resolved); `v2/issue.md` is the AC source for the issue-level inventory
- **PR Context:** `artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`
- **Prior verdict:** cycle 1 entry audit at `2026-05-28T23-20` returned 1 BLOCKING (R-1) and a bundled non-blocking #1 (production-source test seam removal)

## Executive Summary

Zero Blocking findings. R-1 is RESOLVED: the behavioral CSV export test now uses an in-memory `_CapturingStringIO` capture seam injected through `build_application(exporter_registry=...)` and writes no file to disk; `git status` shows no untracked `results_*.csv`. Non-blocking #1 is RESOLVED: `PipelinePresenter.set_imported_tables_for_test` has been removed from the production source and all behavioral-test call sites have migrated to the standard `on_import_all` / `on_open_db` paths. All toolchain gates pass (Black 0, Ruff 0, Pyright strict 0/0/0, Pytest 417 passed, 0 failed). Coverage is 99% line / 99% branch (above the uniform 85/75 thresholds). All 12 ACs remain delivered; AC-9 is now PASS at both surface and verification levels. Overall policy verdict: **PASS**. Exit condition `blocking_count == 0` is met.

## 1. General Unit Test Policy Compliance

`.claude/rules/general-unit-test.md` requires that unit tests be independent, isolated, fast, deterministic, and readable; that they not use temp files; and that they cover positive, negative, and edge scenarios.

- Independence/Isolation: PASS.
- Determinism: PASS (no polling primitives in `tests/gui/integration/`).
- Banned APIs: PASS (no `time.sleep`, `QThread.sleep`, `QTest.qWait`, `qtbot.waitUntil` in behavioral tests).
- Temp-file prohibition: PASS — the cycle-1 entry blocker (R-1) is closed; the CSV behavioral test now uses an in-memory `_CapturingStringIO` writer injected via `exporter_registry`. `git status` after the post-remediation pytest run shows no `results_*.csv` artifacts.
- Scenario completeness: PASS.
- Coverage thresholds: PASS (99% / 99%).

## 2. General Code Change Policy Compliance

`.claude/rules/general-code-change.md` requires simplicity/reusability/extensibility/separation of concerns; the mandatory seven-stage toolchain loop; the 500-line file size limit; fail-fast error handling; and established naming/logging conventions.

- Design principles: PASS — the `exporter_registry` injection seam on `build_application` is minimal and additive.
- Toolchain loop: PASS — Black/Ruff/Pyright/Pytest each at exit 0 in one pass.
- File size: PASS with one at-cap note — `src/gui/app.py` is now exactly 500 lines (the cap); `src/gui/presenters/pipeline_presenter.py` dropped from 496 to 486 after the test-seam removal. The at-cap state of `app.py` is flagged for monitoring in code-review; it is not a violation but a zero-headroom signal.
- Fail-fast: PASS for runtime errors.
- Naming: PASS.

## 3. Language-Specific Code Change Policy Compliance

Python is the only language with changes on this branch. `.claude/rules/python.md` requires Black formatting, Ruff lint clean, Pyright strict, complete type hints, no broad excepts without context, no `Any` without justification, and Pytest coverage thresholds.

- Black: PASS (105 files unchanged, 0 reformatted).
- Ruff: PASS (0 errors; no new suppressions).
- Pyright strict: PASS (0/0/0).
- Type hints: PASS — the new `exporter_registry` parameter and `_CapturingStringIO` subclass carry full signatures.
- Broad except: documented at the `SynchronousRunner` boundary; verdict PASS.
- `Any` introduction: PASS.

## 4. Language-Specific Unit Test Policy Compliance

`.claude/rules/python.md` test policy requires Pytest, AAA structure, behavioral assertions, parametrized matrices for boundaries, and coverage thresholds.

- Pytest: PASS (417 passed; +1 vs entry-audit baseline of 416, the new `test_build_application_uses_injected_exporter_registry`).
- AAA structure: PASS.
- Property test density: PASS (T2 requirement met by Hypothesis property test on `on_file_path_changed`).
- Coverage: PASS (99% / 99%).
- Temp files: PASS (cycle-1 fix resolved the R-1 disk-leak; no other test writes to disk).
- No external dependencies: PASS.

## 5. Test Coverage Detail

See the Coverage Verification section below.

## 6. Test Execution Metrics

- Total tests: 417 passed, 0 failed.
- Cycle-1 entry baseline: 416 passed.
- Test count delta from cycle 1 entry: +1 (the new positive registry-injection test added in P1-T2).
- Runtime: 21.14 seconds (per `final-pytest-coverage.2026-05-28T23-20.md`).

## 7. Code Quality Checks

- Black: PASS (exit 0; 105 files unchanged).
- Ruff: PASS (exit 0; 0 errors; no new suppressions).
- Pyright strict: PASS (exit 0; 0 errors / 0 warnings / 0 informations).
- Pytest: PASS (exit 0; 417 passed).
- Tier classification: PASS (26/26 src/gui modules classified, unchanged from cycle-1 entry).
- DoD traceability: PASS (AC-1..AC-12 mapped to passing tests; AC-9 verification path is now disk-free).

## Required Reading Order (verified)

1. `CLAUDE.md`
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/python.md`
5. `.claude/rules/python-suppressions.md`
6. `.claude/rules/quality-tiers.md`
7. `.claude/rules/self-explanatory-code-commenting.md`
8. `.claude/rules/tonality.md`
9. `.claude/rules/ci-workflows.md`
10. `.claude/rules/benchmark-baselines.md`

## Rejected Scope Narrowing

None observed. The orchestrator brief frames the audit as the full feature-branch diff vs. the resolved base; no narrowing was attempted.

## Evidence Location Compliance

All cycle-1 evidence artifacts are written under the canonical `docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/<kind>/` hierarchy. A working-tree scan against the forbidden roots (`artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, `artifacts/coverage/`) found zero v2 evidence files written outside the canonical location. `scripts/validate_evidence_locations.py` is absent from the repository (per memory note `evidence-validator-script-absent`), so a working-tree grep stood in for the missing validator.

Outcome: **PASS**.

## Coverage Verification

Python is the only language with changed files on this branch.

Repo-wide values from `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md`:

- Line coverage: 99% (1954 statements, 14 missed)
- Branch coverage: 99% (296 branches, 2 partial)
- Test count: 417 passed, 0 failed
- Threshold (uniform per `quality-tiers.md`): line >= 85%, branch >= 75%

Coverage-delta evidence: `v2/evidence/qa-gates/coverage-delta.2026-05-28T23-20.md`. The cycle-1 entry baseline (416 tests) was 99% line / 99% branch; post-remediation (417 tests) is identical at the percentage level. The 14 uncovered statements trace to `src/gui/runners.py::ThreadedRunner.run` (production threaded path, exercised by the production default rather than by `SynchronousRunner`-injected behavioral tests). No regression on changed lines.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 9 prod modified + 2 prod new + 12 test modified + 7 test new (cycle-1 working-tree state vs main) | 417 (full suite) | PASS — 417 pass, 0 fail | 100% line / 100% branch (1793/1793 statements, 262/262 branches per v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md) | 99% line / 99% branch (1940/1954 statements, 294/296 branches per v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md) | 99% line / 99% branch on every cycle-1 modified file; the new `exporter_registry` branch on `build_application` is 100% covered by the new positive test |

Note: Only Python source changed on the branch. No TypeScript, PowerShell, C#, Bash, or governed JSON files changed in cycle 1 (the workflow change at `.github/workflows/_python-quality.yml` was authored during the v1 remediation cycle (commit 553547d) and is carried forward; no new workflow drift in cycle 1).

### Python Coverage Checklist

- [x] Coverage artifact exists for Python (per-feature pytest evidence)
- [x] Repo-wide line >= 85%: PASS (99%)
- [x] Repo-wide branch >= 75%: PASS (99%)
- [x] No regression on changed lines: PASS (per coverage-delta)

### TypeScript Coverage Checklist

- [x] TypeScript baseline coverage artifact: N/A — no TypeScript files changed in this branch
- [x] TypeScript post-change coverage artifact: N/A — no TypeScript files changed in this branch
- [x] TypeScript repo-wide line >= 85%: N/A — no TypeScript files changed in this branch
- [x] TypeScript no regression on changed lines: N/A — no TypeScript files changed in this branch

### PowerShell Coverage Checklist

- [x] PowerShell baseline coverage artifact: N/A — no PowerShell files changed in this branch
- [x] PowerShell post-change coverage artifact: N/A — no PowerShell files changed in this branch
- [x] PowerShell repo-wide line >= 85%: N/A — no PowerShell files changed in this branch
- [x] PowerShell no regression on changed lines: N/A — no PowerShell files changed in this branch

Coverage comparison line (Baseline vs. Post-change vs. Disposition): Baseline 100% line / 100% branch (333 tests); Post-change 99% line / 99% branch (417 tests); Disposition: PASS. Threshold satisfied; no regression on changed lines.

- Per-language comparison summary: see the per-language bullets directly below; baseline coverage was 100% line / 100% branch over 1793 statements / 262 branches in v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md; post-change coverage is 99% line / 99% branch over 1954 statements / 296 branches in v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md.

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 100% line / 100% branch (333 tests, 1793 statements, 262 branches). Post-change: 99% line / 99% branch (417 tests, 1954 statements, 296 branches). Change: line coverage -1 percentage point, branch coverage -1 percentage point; the drop is fully explained by 14 uncovered statements in the new `src/gui/runners.py::ThreadedRunner.run` (production threaded path); no regression on lines that were already covered, and the cycle-1 diff itself introduces zero new uncovered lines (cycle-1 baseline-to-post-remediation delta is 0). New/changed-code coverage: 99% line / 99% branch on cycle-1 modified files; the `exporter_registry` injection branch on `build_application` is 100% covered by the new positive test. Disposition: PASS. Evidence: v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md, v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md, v2/evidence/qa-gates/coverage-delta.2026-05-28T23-20.md.
- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no TypeScript files changed on this branch.
- PowerShell: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no PowerShell files changed on this branch.
- C#: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no C# files changed on this branch.

| Language | Baseline Line % | Baseline Branch % | Post-Change Line % | Post-Change Branch % | Disposition |
|---|---|---|---|---|---|
| Python | 100% | 100% | 99% | 99% | PASS |
| TypeScript | N/A | N/A | N/A | N/A | N/A — no TS files changed |
| PowerShell | N/A | N/A | N/A | N/A | N/A — no PS files changed |
| C# | N/A | N/A | N/A | N/A | N/A — no C# files changed |

## Toolchain Gates (final, cycle-1 post-remediation)

| Gate | Evidence | EXIT_CODE | Result |
|---|---|---|---|
| Black | `v2/evidence/qa-gates/final-black.2026-05-28T23-20.md` | 0 | PASS (105 files unchanged) |
| Ruff | `v2/evidence/qa-gates/final-ruff.2026-05-28T23-20.md` | 0 | PASS (0 errors) |
| Pyright strict | `v2/evidence/qa-gates/final-pyright.2026-05-28T23-20.md` | 0 | PASS (0/0/0) |
| Pytest + coverage | `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md` | 0 | PASS (417 passed) |
| Coverage delta | `v2/evidence/qa-gates/coverage-delta.2026-05-28T23-20.md` | n/a | PASS (no regression on changed lines) |
| DoD traceability | `v2/evidence/other/dod-traceability.2026-05-28T23-20.md` | n/a | PASS (AC-1..AC-12 mapped; AC-9 disk-free) |

Each evidence artifact carries the required `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` fields (or equivalent header for verification-only artifacts).

## File Size Limit (`.claude/rules/general-code-change.md`)

| File | Lines | Within 500-line cap |
|---|---|---|
| src/gui/app.py | 500 | PASS (exactly at cap; zero headroom; flagged in code-review) |
| src/gui/_wiring.py | 96 | PASS |
| src/gui/runners.py | 193 | PASS |
| src/gui/presenters/pipeline_presenter.py | 486 | PASS (dropped from 496 after `set_imported_tables_for_test` removal) |
| src/gui/exporters/csv_exporter.py | 152 | PASS |
| tests/gui/integration/test_behavioral_dialogs.py | 265 | PASS (grew by 56 lines from the in-memory capture rewrite) |
| tests/gui/integration/test_behavioral_import_buttons.py | 175 | PASS |
| tests/gui/integration/test_behavioral_preview.py | 135 | PASS |
| tests/gui/integration/test_behavioral_composition.py | 90 | PASS |
| tests/gui/integration/test_behavioral_pipeline_run.py | 98 | PASS |
| tests/gui/test_app_wiring.py | 492 | PASS (grew by 21 lines from the registry-injection test) |
| tests/gui/test_pipeline_presenter.py | 336 | PASS |
| tests/gui/test_pipeline_presenter_v2.py | 244 | PASS |

No production or test file exceeds 500 lines.

## Suppression Audit (`.claude/rules/python-suppressions.md`)

Working-tree grep of `# noqa`, `# type: ignore`, and `# pyright: ignore` across all `.py` files in the branch yielded:

| Location | Suppression | Pre-authorized | Verdict |
|---|---|---|---|
| tests/gui/fakes/fake_services.py:53 | `# noqa: ARG002 - match WorkbookReaderProtocol API` | Yes (ARG002 mock-signature pattern) | PASS |
| tests/gui/fakes/fake_services.py:131 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:149 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:168 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:230 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:278 | `# noqa: ARG002 - match DbService API` | Yes | PASS |
| src/gui/exporters/excel_exporter.py:69 | `# noqa: N802` (comment-only narrative; verified pre-existing v1, retained in v2) | Documented in v1 audit; carried unchanged | PASS |

All suppressions match pre-authorized patterns. No new `# noqa`, `# type: ignore`, or `# pyright: ignore` was introduced in cycle 1.

## Banned Test APIs (`tests/gui/integration/`)

Working-tree grep of the prohibited polling primitives in the behavioral test directory:

| Pattern | Hits in `tests/gui/integration/` | Verdict |
|---|---|---|
| `qtbot.waitUntil` | 0 | PASS |
| `QTest.qWait` | 0 | PASS |
| `time.sleep` | 0 | PASS |
| `QThread.sleep` | 0 | PASS |
| `qtbot.waitSignal` | 0 | PASS |

`qtbot.waitSignal` remains confined to `tests/gui/test_pipeline_worker.py` and `tests/gui/test_source_input_widget.py`, neither of which is under `tests/gui/integration/`.

## Confidentiality Invariant

Working-tree grep of `Category`, `SKU Description`, customer names, SKU numbers, prices, and discounts across new and modified cycle-1 files returned no matches. Fabricated values only (`SKU-001`, `k1`, `AOP1`, `LE-8 + 4`, `results.csv`). Country tokens `US` / `Canada` are permitted by spec.

Outcome: **PASS**.

## Workflow-Touching Diffs

The branch contains one modified workflow file vs. main: `.github/workflows/_python-quality.yml` (commit 553547d, dated 2026-05-28 09:07; predates cycle 1; added during the v1 remediation cycle to install Qt runtime libraries and set `QT_QPA_PLATFORM=offscreen`). Per `.claude/rules/ci-workflows.md`: the modified step uses `shell: |` (bash, the runner default), not `pwsh`; no deliberately-failing nested command pattern is present, so the bash-exit-code reset rule does not apply. The change is purely additive (apt-get + env var).

No new workflow drift was introduced in cycle 1. The cycle-1 commit log against `.github/workflows/` is empty since `2026-05-28T20:00`.

Verdict: **PASS-with-note**. No new cycle-1 workflow drift. The v1 workflow diff carries forward; its `modified-workflow-needs-green-run` recommendation persists as an orchestrator-level pre-merge check, not a cycle-1 blocker.

## Benchmark Baselines

No benchmark baselines are touched by this branch (no diff under `scripts/benchmarks/**` or `**/baseline*.json`). Rule `.claude/rules/benchmark-baselines.md` is not engaged.

## Tier Classification

`quality-tiers.yml` was updated in v2 execution to add `src/gui/runners.py: T2` and `src/gui/_wiring.py: T4`. Cycle 1 did not add or remove any module; no further tier changes were required.

Outcome: **PASS**.

## v1 Artifact Preservation

`git status --short docs/features/active/2026-05-27-mix-pipeline-gui-19/v1/` returns no entries: the v1 audit set (`policy-audit.2026-05-28T13-15.md`, `code-review.2026-05-28T13-15.md`, `feature-audit.2026-05-28T13-15.md`) and the v1 evidence root were not modified by cycle 1.

Outcome: **PASS**.

## Cycle-1 Audit Artifact Preservation

The cycle-0 v2 audit set (`policy-audit.2026-05-28T23-20.md`, `code-review.2026-05-28T23-20.md`, `feature-audit.2026-05-28T23-20.md`) and the cycle-0 remediation inputs were read-only inputs to cycle 1. They are unmodified at the post-remediation head.

Outcome: **PASS**.

## Issues Found

### Blocking

None.

### Non-Blocking Observations

**N-1: `src/gui/app.py` is exactly at the 500-line cap.** Adding the `exporter_registry` parameter and its docstring pushed `app.py` from 492 to 500 lines. Any future addition will exceed the cap and require another helper split (for example, moving `MainWindowPipelineView` into `src/gui/_main_window_view.py`). Flagged in code-review. Not a violation.

**N-2: v1 workflow diff carried over without a re-run on the cycle-1 head.** Documented above. The `modified-workflow-needs-green-run` recommendation persists as an orchestrator-level pre-merge check. No new cycle-1 action required.

**N-3: Branch is uncommitted at audit time.** All cycle-1 changes plus the original v2 changes remain in the working tree. The audit reads working-tree state; before merge the orchestrator must commit. Not a policy violation.

**N-4: Phase 10/11 QA artifact aggregation absent (carried over from cycle-0 entry).** The plan's Phase 10/11 acceptance is split across `tier-classification`, `coverage-delta`, `dod-traceability`, and the four `final-*` files. Same observation as in the cycle-0 entry audit; not a cycle-1-introduced gap.

## 8. Gaps and Exceptions

- All cycle-0 entry-audit blocking and non-blocking items are resolved. R-1 is RESOLVED (see Executive Summary citation); non-blocking #1 is RESOLVED (see Executive Summary citation).
- N-1, N-2, N-3, N-4 are non-blocking observations and do not require cycle-2 remediation.

## 9. Summary of Changes

Production:

- `src/gui/app.py`: added keyword-only parameter `exporter_registry: ExporterRegistry | None = None` on `build_application`; the local `registry` assignment now resolves to the injected registry when supplied, else `_build_registry()`. File line count rose from 492 to 500.
- `src/gui/presenters/pipeline_presenter.py`: removed the production-source test seam `set_imported_tables_for_test`. File line count dropped from 496 to 486.

Tests:

- `tests/gui/test_app_wiring.py`: added `test_build_application_uses_injected_exporter_registry` (the +1 test).
- `tests/gui/integration/test_behavioral_dialogs.py`: rewrote `test_export_csv_routes_destination_to_csv_exporter` to inject an `ExporterRegistry` with `CsvExporter(open_writer=_capture_open_writer)` whose writer returns a `_CapturingStringIO` subclass that snapshots its buffer on `close()`; replaced the other three `set_imported_tables_for_test` call sites with `on_import_all(_import_spec())` against a `FakePipelineService` configured with `import_result=_fake_imports()`.
- `tests/gui/integration/test_behavioral_pipeline_run.py`: replaced two `set_imported_tables_for_test` call sites with `on_import_all` / `on_import_one` through `FakePipelineService`.

Evidence (cycle-1, under `v2/evidence/`):

- `baseline/baseline.2026-05-28T23-20.md`
- `qa-gates/phase1-qa.2026-05-28T23-20.md`, `phase2-qa.2026-05-28T23-20.md`, `phase3-qa.2026-05-28T23-20.md`
- `qa-gates/final-black.2026-05-28T23-20.md`, `final-ruff.2026-05-28T23-20.md`, `final-pyright.2026-05-28T23-20.md`, `final-pytest-coverage.2026-05-28T23-20.md`
- `qa-gates/coverage-delta.2026-05-28T23-20.md`
- `other/phase0-instructions-read.2026-05-28T23-20.md`, `other/dod-traceability.2026-05-28T23-20.md`

## 10. Compliance Verdict

**PASS** — zero Blocking findings. Cycle-1 exit condition `blocking_count == 0` is met. The strict-handoff remediation cycle may be exited. With the working tree committed, the branch is mergeable.

## Appendix A: Test Inventory

| Layer | Path | Purpose |
|---|---|---|
| Unit (no QApplication) | `tests/gui/test_runners.py` | SynchronousRunner success/error/protocol coverage. |
| Unit | `tests/gui/test_pipeline_presenter.py` | v1 presenter behavior plus extended Save/Open coverage. |
| Unit | `tests/gui/test_pipeline_presenter_v2.py` | v2-specific presenter behaviors. |
| Unit | `tests/gui/test_source_selection_presenter.py` | preview_sink paths. |
| Unit | `tests/gui/test_export_presenter.py` | (unchanged from v1). |
| Unit | `tests/gui/test_csv_exporter.py` | CSV name-mangling rule, in-memory writer. |
| Unit | `tests/gui/test_app_wiring.py` | MainWindowPipelineView adapter + build_application injection (now includes registry-injection positive test). |
| Unit | `tests/gui/test_app_wiring_defaults.py` | default_export_runner filter parse. |
| Widget (offscreen) | `tests/gui/test_main_window.py` | public-attribute coverage. |
| Widget (offscreen) | `tests/gui/test_source_input_widget.py` | `_on_tab_changed` slot. |
| Widget (offscreen) | `tests/gui/test_export_dialog.py` | checklist (combo removed). |
| Widget (offscreen) | `tests/gui/test_preview_widget.py` | (unchanged from v1). |
| Widget (offscreen) | `tests/gui/test_app_composition.py` | SynchronousRunner smoke. |
| Worker (Qt with waitSignal) | `tests/gui/test_pipeline_worker.py` | off-thread proof (unchanged from v1). |
| Behavioral integration (offscreen) | `tests/gui/integration/test_behavioral_preview.py` | AC-1. |
| Behavioral integration | `tests/gui/integration/test_behavioral_import_buttons.py` | AC-2 / AC-3 / AC-4 / AC-5. |
| Behavioral integration | `tests/gui/integration/test_behavioral_pipeline_run.py` | AC-6 (cycle-1 migrated to standard import path). |
| Behavioral integration | `tests/gui/integration/test_behavioral_dialogs.py` | AC-7 / AC-8 / AC-9 (cycle-1: CSV path now disk-free via in-memory capture). |
| Behavioral integration | `tests/gui/integration/test_behavioral_composition.py` | AC-10. |

## Appendix B: Toolchain Commands Reference

The seven-stage toolchain loop required by `.claude/rules/general-code-change.md` was executed during cycle-1 phases P1-T3, P2-T4, P3-T2, and finally P4-T1..P4-T4. Stages 4 (architecture-boundary tests) and 6 (contract/schema compatibility) are not applicable to this Python-only feature.

| Stage | Command | Evidence |
|---|---|---|
| 1. Formatting | `env -u VIRTUAL_ENV poetry run black .` | `v2/evidence/qa-gates/final-black.2026-05-28T23-20.md` |
| 2. Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | `v2/evidence/qa-gates/final-ruff.2026-05-28T23-20.md` |
| 3. Type checking | `env -u VIRTUAL_ENV poetry run pyright` | `v2/evidence/qa-gates/final-pyright.2026-05-28T23-20.md` |
| 4. Architecture-boundary | N/A | N/A |
| 5. Unit tests | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md` |
| 6. Contract/schema | N/A | N/A |
| 7. Integration tests | Included in the Pytest run above (`tests/gui/integration/`) | Same artifact as stage 5 |

The Poetry `env -u VIRTUAL_ENV` prefix is required in this repository per the in-repo memory note (`poetry-virtualenv-quirk`).

## Overall Verdict

**PASS** — zero Blocking findings. Cycle-1 exit condition `blocking_count == 0` is met.
