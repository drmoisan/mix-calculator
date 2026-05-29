# Policy Audit — mix-pipeline-gui v2 (Issue #19)

- **Timestamp:** 2026-05-28T23-20
- **Branch:** feature/mix-pipeline-gui-19
- **Base:** main (merge-base used by PR context)
- **Audit scope:** Full feature branch (working tree) vs. main, v2 execution head
- **Work Mode:** full-feature (from `v2/issue.md`)
- **AC Source:** `v2/spec.md` + `v2/user-story.md` (mode-resolved)
- **PR Context:** `artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`

## Executive Summary

One Blocking finding (B-1: behavioral CSV export test leaks real files into
the repository working directory, violating the no-temp-files invariant).
All toolchain gates pass (Black, Ruff, Pyright strict, Pytest with
416 passing tests). Coverage is 99% line / 99% branch repo-wide. AC-1
through AC-8 and AC-10 through AC-12 are delivered with both unit-level and
behavioral-level evidence; AC-9's production surface is delivered, but the
behavioral verification path is defective. v1 audit artifacts and v1
evidence are untouched. No new workflow drift in v2 (the workflow diff
present is carried from v1). Overall policy verdict: **FAIL** pending the
single blocker's remediation.

## 1. General Unit Test Policy Compliance

`.claude/rules/general-unit-test.md` requires that unit tests be
independent, isolated, fast, deterministic, and readable; that they not use
temp files; that they cover positive, negative, and edge scenarios; and that
they avoid `time.sleep`, `Thread.sleep`, and equivalents.

- Independence/Isolation: PASS for all reviewed tests.
- Determinism: PASS for `tests/gui/integration/` (no polling primitives).
- Banned APIs: PASS (verified by grep above).
- Temp-file prohibition: **FAIL** (see Blocking finding B-1: the CSV
  behavioral test writes real files to the working directory).
- Scenario completeness: PASS (positive, negative, and edge-case coverage
  visible in `test_pipeline_presenter_v2.py` and the integration suite).
- Coverage thresholds: PASS (99% line / 99% branch).

## 2. General Code Change Policy Compliance

`.claude/rules/general-code-change.md` requires simplicity/reusability/
extensibility/separation-of-concerns; the mandatory seven-stage toolchain
loop; the 500-line file size limit; fail-fast error handling; and
established naming/logging conventions.

- Design principles: PASS — runner abstraction, working-tables property,
  view-protocol extension all maintain MVP separation.
- Toolchain loop: PASS — Black/Ruff/Pyright/Pytest each at exit 0.
- File size: PASS — all files under 500 lines (largest: pipeline_presenter
  at 496, app at 492; both flagged for headroom in code-review).
- Fail-fast: PASS for runtime errors; one Minor in code-review about a
  silent default in `default_export_runner` (logger.warning recommended).
- Naming: PASS.

## 3. Language-Specific Code Change Policy Compliance

Python is the only language with changes on this branch.
`.claude/rules/python.md` requires Black formatting, Ruff lint clean,
Pyright strict, complete type hints, no broad excepts without context, no
`Any` without justification, and Pytest coverage thresholds.

- Black: PASS (105 files unchanged, 0 reformatted).
- Ruff: PASS (0 errors).
- Pyright strict: PASS (0/0/0).
- Type hints: PASS — all new public APIs annotated; protocols
  `RunnerProtocol` and extended `PipelineViewProtocol` carry full
  signatures.
- Broad except: documented at the SynchronousRunner boundary; verdict PASS
  with a Minor code-review note recommending an inline rationale comment.
- `Any` introduction: PASS (final-pyright artifact confirms "no `Any`
  introduced").

## 4. Language-Specific Unit Test Policy Compliance

`.claude/rules/python.md` test policy requires Pytest, AAA structure,
behavioral assertions, parametrized matrices for boundaries, and >= 85%
line / >= 75% branch coverage.

- Pytest: PASS.
- AAA structure: PASS across all reviewed test files.
- Property test density: PASS — `on_file_path_changed` has a Hypothesis
  property test per the T2 density requirement.
- Coverage: PASS (99% / 99%).
- Temp files: FAIL — see policy compliance section 1.
- No external dependencies: PASS except for the temp-file leak (which is
  the same underlying defect as B-1).

## 5. Test Coverage Detail

See the Coverage Verification section below for the per-language table and
the Python coverage checklist.

## 6. Test Execution Metrics

- Total tests: 416 passed, 0 failed.
- Baseline test count (P0): 333.
- Test count delta: +83 v2-added tests.
- Runtime: 22.15 seconds (per `final-pytest-coverage.2026-05-28T22-10.md`).
- Coverage report: 1956 statements (14 missed); 296 branches (2 partial).

## 7. Code Quality Checks

- Black: PASS (exit 0; 105 files unchanged).
- Ruff: PASS (exit 0; 0 errors; no new suppressions).
- Pyright strict: PASS (exit 0; 0 errors / 0 warnings / 0 informations).
- Pytest: PASS (exit 0; 416 passed).
- Tier classification: PASS (26/26 src/gui modules classified).
- DoD traceability: PASS (AC-1..AC-12 mapped to passing tests).

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

None observed. The orchestrator brief scopes the audit to the v2 head against the v2 acceptance criteria of `v2/issue.md`; no narrowing to a plan/task/phase subset was attempted.

## Evidence Location Compliance

All v2 evidence artifacts are written under the canonical
`docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/<kind>/`
hierarchy. A working-tree scan against the forbidden roots (`artifacts/baselines/`,
`artifacts/qa/`, `artifacts/evidence/`, `artifacts/coverage/`) found zero v2
evidence files written outside the canonical location.

`scripts/validate_evidence_locations.py` is absent from the repository (per
memory note `evidence-validator-script-absent`), so a working-tree grep stood in
for the missing validator. No violations were found.

Outcome: **PASS**.

## Coverage Verification

Python is the only language with changed files on this branch. The coverage
artifact for Python at `coverage/lcov.info` was not produced by the executor;
instead the canonical evidence is the per-feature pytest coverage report at
`docs/features/active/2026-05-27-mix-pipeline-gui-19/v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md`.

Repo-wide values from that artifact:

- Line coverage: 99% (1956 statements, 14 missed)
- Branch coverage: 99% (296 branches, 2 partial)
- Test count: 416 passed, 0 failed
- Threshold (uniform per `quality-tiers.md`): line >= 85%, branch >= 75%

Coverage-delta evidence: `v2/evidence/qa-gates/coverage-delta.2026-05-28T22-10.md`.
Baseline (P0-T5) was 100% line / 100% branch over 333 tests; post-change is
99%/99% over 416 tests. The 1-point drop traces to `src/gui/runners.py`
`ThreadedRunner.run` (17 lines exercised only by the production threaded path,
not by behavioral tests that inject `SynchronousRunner`) and one production
threaded branch in `src/gui/app.py`. Per the coverage-delta artifact, every
modified line is reached by at least one test ("no regression on changed lines").

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 8 prod modified + 2 prod new + 12 test modified + 7 test new (working-tree state vs main + v2 working-tree) | 416 (full suite) / 192 GUI-only | PASS — 416 pass, 0 fail | 100% line / 100% branch (1793/1793 statements, 262/262 branches per v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md) | 99% line / 99% branch (1942/1956 statements, 294/296 branches per v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md) | 99% line / 99% branch on every v2 modified file; the 14 uncovered statements trace to `src/gui/runners.py::ThreadedRunner.run` (production threaded path exercised only by the production default, not by SynchronousRunner-injected behavioral tests) and one branch in `src/gui/app.py` on the same threaded path |

Note: Only Python source changed on the branch. No TypeScript, PowerShell, C#, Bash, or governed JSON files changed in v2 (the workflow change at `.github/workflows/_python-quality.yml` was authored during v1 remediation and is carried forward; no new workflow drift in v2).

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

Coverage comparison line (Baseline vs. Post-change vs. Disposition):
Baseline 100% line / 100% branch (333 tests); Post-change 99% line / 99% branch
(416 tests); Disposition: PASS. Threshold satisfied; no regression on changed
lines.

- Per-language comparison summary: see the per-language bullets directly below; baseline coverage was 100% line / 100% branch over 1793 statements / 262 branches in v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md, post-change coverage is 99% line / 99% branch over 1956 statements / 296 branches in v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md.

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 100% line / 100% branch (333 tests, 1793 statements, 262 branches). Post-change: 99% line / 99% branch (416 tests, 1956 statements, 296 branches). Change: line coverage -1 percentage point, branch coverage -1 percentage point; the drop is fully explained by 14 uncovered statements in the new `src/gui/runners.py::ThreadedRunner.run` (production threaded path) plus one branch in `src/gui/app.py` on the same threaded path; no regression on lines that were already covered. New/changed-code coverage: 99% line / 99% branch on v2 modified files; the `SynchronousRunner` path used by behavioral tests is 100% covered. Disposition: PASS. Evidence: v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md, v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md, v2/evidence/qa-gates/coverage-delta.2026-05-28T22-10.md.
- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no TypeScript files changed on this branch.
- PowerShell: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no PowerShell files changed on this branch.
- C#: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no C# files changed on this branch.

| Language | Baseline Line % | Baseline Branch % | Post-Change Line % | Post-Change Branch % | Disposition |
|---|---|---|---|---|---|
| Python | 100% | 100% | 99% | 99% | PASS |
| TypeScript | N/A | N/A | N/A | N/A | N/A — no TS files changed |
| PowerShell | N/A | N/A | N/A | N/A | N/A — no PS files changed |
| C# | N/A | N/A | N/A | N/A | N/A — no C# files changed |

## Toolchain Gates (final)

| Gate | Evidence | EXIT_CODE | Result |
|---|---|---|---|
| Black | `v2/evidence/qa-gates/final-black.2026-05-28T22-10.md` | 0 | PASS (105 files unchanged) |
| Ruff | `v2/evidence/qa-gates/final-ruff.2026-05-28T22-10.md` | 0 | PASS (0 errors) |
| Pyright strict | `v2/evidence/qa-gates/final-pyright.2026-05-28T22-10.md` | 0 | PASS (0/0/0) |
| Pytest + coverage | `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md` | 0 | PASS (416 passed) |
| Tier classification | `v2/evidence/other/tier-classification.2026-05-28T22-10.md` | 0 | PASS (26/26 classified, runners.py T2, _wiring.py T4 added) |
| DoD traceability | `v2/evidence/other/dod-traceability.2026-05-28T22-10.md` | n/a | PASS (AC-1..AC-12 mapped) |

Each evidence artifact carries the required `Timestamp:`, `Command:`,
`EXIT_CODE:`, and `Output Summary:` fields (or equivalent header for the
verification-only artifacts).

## File Size Limit (`.claude/rules/general-code-change.md`)

| File | Lines | Within 500-line cap |
|---|---|---|
| src/gui/app.py | 492 | PASS (close to cap; flagged in code-review as low-headroom) |
| src/gui/_wiring.py | 96 | PASS (helper split performed per plan P7-T1 to keep app.py under cap) |
| src/gui/runners.py | 193 | PASS |
| src/gui/presenters/pipeline_presenter.py | 496 | PASS (close to cap; flagged in code-review) |
| src/gui/main_window.py | 160 | PASS |
| src/gui/widgets/source_input_widget.py | 303 | PASS |
| src/gui/widgets/export_dialog.py | 159 | PASS |
| src/gui/exporters/csv_exporter.py | 152 | PASS |
| src/gui/presenters/source_selection_presenter.py | 198 | PASS |
| src/gui/protocols.py | 287 | PASS |
| tests/gui/integration/test_behavioral_dialogs.py | 209 | PASS |
| tests/gui/integration/test_behavioral_import_buttons.py | 175 | PASS |
| tests/gui/integration/test_behavioral_preview.py | 135 | PASS |
| tests/gui/integration/test_behavioral_composition.py | 90 | PASS |
| tests/gui/integration/test_behavioral_pipeline_run.py | 84 | PASS |
| tests/gui/test_app_wiring.py | 471 | PASS (close to cap) |
| tests/gui/test_pipeline_presenter.py | 336 | PASS |
| tests/gui/test_pipeline_presenter_v2.py | 244 | PASS (split file per plan, P4-T2) |

No production or test file exceeds 500 lines.

## Suppression Audit (`.claude/rules/python-suppressions.md`)

Working-tree grep of `# noqa`, `# type: ignore`, and `# pyright: ignore` across
all `.py` files in the branch yielded:

| Location | Suppression | Pre-authorized | Verdict |
|---|---|---|---|
| tests/gui/fakes/fake_services.py:53 | `# noqa: ARG002 - match WorkbookReaderProtocol API` | Yes (ARG002 mock-signature pattern) | PASS |
| tests/gui/fakes/fake_services.py:131 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:149 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:168 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:230 | `# noqa: ARG002 - match PipelineServiceProtocol API` | Yes | PASS |
| tests/gui/fakes/fake_services.py:278 | `# noqa: ARG002 - match DbService API` | Yes | PASS |
| src/gui/exporters/excel_exporter.py:69 | `# noqa: N802` (comment-only narrative; verified pre-existing v1, retained in v2) | Documented in v1 audit; carried unchanged | PASS |

All suppressions match pre-authorized patterns in
`.claude/rules/python-suppressions.md`. No new `# noqa` codes were introduced
outside the authorized list. The `final-ruff` evidence explicitly notes that
no new suppressions were added in v2 source files.

## Banned Test APIs (`tests/gui/integration/`)

Working-tree grep of the prohibited polling primitives in the behavioral test
directory:

| Pattern | Hits in `tests/gui/integration/` | Verdict |
|---|---|---|
| `qtbot.waitUntil` | 0 | PASS |
| `QTest.qWait` | 0 | PASS |
| `time.sleep` | 0 | PASS |
| `QThread.sleep` | 0 | PASS |
| `qtbot.waitSignal` | 0 | PASS |

`qtbot.waitSignal` is used in `tests/gui/test_pipeline_worker.py` (the
worker-isolation test, explicitly permitted by spec section 4) and in
`tests/gui/test_source_input_widget.py` (per plan P3-T3 explicit allowance for
the tab-change widget tests). Neither violates the behavioral-test isolation
invariant since both are outside `tests/gui/integration/`.

## Confidentiality Invariant

Working-tree grep of `Category`, `SKU Description`, and obvious customer terms
across new v2 files returned no matches. Fabricated values only (`SKU-001`,
`k1`, `AOP1`, `LE-8 + 4`, `results.csv`). Country tokens `US` / `Canada` are
permitted by spec.

Outcome: **PASS**.

## Workflow-Touching Diffs

The branch contains one modified workflow file vs. main:
`.github/workflows/_python-quality.yml` (commit 553547d, dated 2026-05-28
09:07; predates v2 execution; added during v1 remediation to install Qt
runtime libraries and set `QT_QPA_PLATFORM=offscreen`). Per
`.claude/rules/ci-workflows.md`: the modified step uses `shell: |` (bash, the
runner default), not `pwsh`; no deliberately-failing nested command pattern is
present, so the bash-exit-code reset rule does not apply. The change is purely
additive (apt-get + env var).

Per the `modified-workflow-needs-green-run` rule referenced by
`benchmark-baselines.md` and `ci-workflows.md`, a green workflow run against
the branch head is the second line of defense. No remediation-inputs artifact
covering the v2 head shows such a green run; this was already noted and
accepted in the v1 audit chain. The v2 execution did not re-touch the workflow.

Verdict: **PASS-with-note**. No new workflow drift in v2. The v1 workflow
diff carries forward; its merge-readiness check (a green run on the branch
head post-v2) is recommended before the orchestrator-level merge action but
is not a v2-introduced blocker.

## Benchmark Baselines

No benchmark baselines are touched by this branch (no diff under
`scripts/benchmarks/**` or `**/baseline*.json`). Rule
`.claude/rules/benchmark-baselines.md` is not engaged.

## Tier Classification

`quality-tiers.yml` updated in P1-T1 to add `src/gui/runners.py: T2` and in
P7-T1 to add `src/gui/_wiring.py: T4`. Working-tree grep confirms both
entries. The tier-classification evidence artifact enumerates all 26
`src/gui/**` modules with no unclassified files.

Outcome: **PASS**.

## v1 Artifact Preservation

The v1 audit set at `docs/features/active/2026-05-27-mix-pipeline-gui-19/v1/`
(`policy-audit.2026-05-28T13-15.md`, `code-review.2026-05-28T13-15.md`,
`feature-audit.2026-05-28T13-15.md`) was last modified by commit 48abe8d
(organize commit). The v2 execution did not touch any file under `v1/`. The v1
evidence directory at `v1/evidence/` is unchanged.

Outcome: **PASS**.

## Issues Found

### Blocking

**B-1: Behavioral CSV export test writes real files to the repository working directory.**

- File: `tests/gui/integration/test_behavioral_dialogs.py`
- Location: `test_export_csv_routes_destination_to_csv_exporter` (lines 150-181)
- AC affected: AC-9 (Export) behavioral coverage; also affects test-isolation invariants required by `.claude/rules/general-unit-test.md` and `.claude/rules/python.md`.
- Defect: The test constructs `wired = build_application(runner=SynchronousRunner(), pipeline_service=service, workbook_reader=fake_reader, save_path_chooser=..., open_path_chooser=..., export_dialog_runner=_runner)` where `_runner` returns `("CSV", "results.csv")`. No fake exporter is injected. `build_application` registers the real `CsvExporter` with the default `_default_open_writer`, which opens real files via `open(path, "w", ...)`. Clicking `export_btn` therefore writes `results_LE.csv`, `results_aop.csv`, and `results_sku_lu.csv` to the test's current working directory (the repository root in normal `pytest` invocation).
- Evidence: `git status` shows three untracked files (`results_LE.csv`, `results_aop.csv`, `results_sku_lu.csv`) whose contents (`KEY` / `k1` / `SKU` / `SKU-001`) match `_fake_imports()` in `test_behavioral_dialogs.py:30-37`. These files do not appear in `.gitignore`.
- Policy violations: (a) `.claude/rules/general-unit-test.md` "Creation and use of temporary files in tests is strictly prohibited"; (b) `.claude/rules/python.md` "No external dependencies (network, databases, external processes, runtime filesystem temp files) in unit tests"; (c) spec v2 Constraints: "Testability without temp files (unchanged from v1). No runtime temp files in unit tests".
- Remediation: extend `build_application` to accept an injectable `csv_exporter` (or `exporter_registry`) parameter, or inject a fake `open_writer` into the CSV exporter via `build_application`, or replace this behavioral test with a registry-only assertion (already present at line 181) and delete the click-through path that triggers the real write.

### Non-Blocking Observations

**N-1: v2 execution is uncommitted.** All v2 production and test changes are
in the working tree but not committed (24 modified + 7 untracked source files
per `git status`). Coverage and toolchain evidence reflect the working-tree
state, so the audit is valid against the working tree; however the
`pr_context.summary.txt`/`appendix.txt` artifacts and the `git diff main...HEAD`
view used by reviewers will not show v2 changes until commit. Recommend
committing v2 before merge.

**N-2: Workflow diff carried over from v1.** Documented above under
"Workflow-Touching Diffs". No new v2 action required, but the
`modified-workflow-needs-green-run` recommendation persists.

**N-3: app.py and pipeline_presenter.py near the 500-line cap.** Both files
are at 492 and 496 lines respectively. Any future addition will trigger
another helper split. Flagged in code-review.

## 8. Gaps and Exceptions

- **B-1 (Blocking, listed above):** the AC-9 behavioral test writes real
  files to the repository working directory.
- **N-1, N-2, N-3 (non-blocking, listed above):** v2 changes uncommitted at
  audit time; v1 workflow diff carried over without a re-run on v2 head;
  `app.py` and `pipeline_presenter.py` near the 500-line cap.
- Phase 10 / Phase 11 QA artifacts are split across `tier-classification`,
  `coverage-delta`, `dod-traceability`, and the four `final-*` files
  instead of single `phase10-qa.md` / `phase11-qa.md` aggregations; the
  required schema fields are all present in the individual artifacts, so
  this is a documentation observation rather than an evidence gap.

## 9. Summary of Changes

- New production modules: `src/gui/runners.py` (RunnerProtocol /
  ThreadedRunner / SynchronousRunner), `src/gui/_wiring.py` (default
  chooser factories and `default_export_runner` helper split out of
  `app.py` to preserve the 500-line cap).
- Modified production modules: `src/gui/app.py`,
  `src/gui/main_window.py`, `src/gui/protocols.py`,
  `src/gui/presenters/pipeline_presenter.py`,
  `src/gui/presenters/source_selection_presenter.py`,
  `src/gui/widgets/source_input_widget.py`,
  `src/gui/widgets/export_dialog.py`,
  `src/gui/exporters/csv_exporter.py`.
- Configuration: `quality-tiers.yml` (added `src/gui/runners.py: T2` and
  `src/gui/_wiring.py: T4`).
- New tests: `tests/gui/test_runners.py`, `tests/gui/test_main_window.py`,
  `tests/gui/test_pipeline_presenter_v2.py`, the entire
  `tests/gui/integration/` package (5 behavioral test files plus
  `__init__.py`).
- Modified tests: `tests/gui/test_pipeline_presenter.py`,
  `tests/gui/test_app_wiring.py`, `tests/gui/test_csv_exporter.py`,
  `tests/gui/test_export_dialog.py`,
  `tests/gui/test_app_wiring_defaults.py`,
  `tests/gui/test_source_input_widget.py`,
  `tests/gui/test_source_selection_presenter.py`,
  `tests/gui/test_app_composition.py`, `tests/gui/_wiring_test_doubles.py`,
  `tests/gui/fakes/fake_views.py`.

## 10. Compliance Verdict

**FAIL** — one Blocking finding (B-1). The user-visible v2 surface is
delivered to specification; the verification surface for AC-9 violates the
no-temp-files invariant. Remediation routes through the strict-handoff
protocol via `atomic-planner`. With B-1 fixed, the branch is mergeable.

## Appendix A: Test Inventory

| Layer | Path | Purpose |
|---|---|---|
| Unit (no QApplication) | `tests/gui/test_runners.py` | SynchronousRunner success/error/protocol coverage. |
| Unit | `tests/gui/test_pipeline_presenter.py` | v1 presenter behavior plus extended Save/Open coverage. |
| Unit | `tests/gui/test_pipeline_presenter_v2.py` | v2-specific presenter behaviors (path tracking, working_tables, invalidation, button pushes). |
| Unit | `tests/gui/test_source_selection_presenter.py` | preview_sink paths. |
| Unit | `tests/gui/test_export_presenter.py` | (unchanged from v1). |
| Unit | `tests/gui/test_csv_exporter.py` | CSV name-mangling rule, in-memory writer. |
| Unit | `tests/gui/test_app_wiring.py` | MainWindowPipelineView adapter + build_application injection. |
| Unit | `tests/gui/test_app_wiring_defaults.py` | default_export_runner filter parse. |
| Widget (offscreen) | `tests/gui/test_main_window.py` | public-attribute coverage. |
| Widget (offscreen) | `tests/gui/test_source_input_widget.py` | `_on_tab_changed` slot. |
| Widget (offscreen) | `tests/gui/test_export_dialog.py` | checklist (combo removed). |
| Widget (offscreen) | `tests/gui/test_preview_widget.py` | (unchanged from v1). |
| Widget (offscreen) | `tests/gui/test_app_composition.py` | SynchronousRunner smoke. |
| Worker (Qt with waitSignal) | `tests/gui/test_pipeline_worker.py` | off-thread proof (unchanged from v1). |
| Behavioral integration (offscreen) | `tests/gui/integration/test_behavioral_preview.py` | AC-1. |
| Behavioral integration | `tests/gui/integration/test_behavioral_import_buttons.py` | AC-2 / AC-3 / AC-4 / AC-5. |
| Behavioral integration | `tests/gui/integration/test_behavioral_pipeline_run.py` | AC-6. |
| Behavioral integration | `tests/gui/integration/test_behavioral_dialogs.py` | AC-7 / AC-8 / AC-9 (B-1 lives here). |
| Behavioral integration | `tests/gui/integration/test_behavioral_composition.py` | AC-10. |

## Appendix B: Toolchain Commands Reference

The seven-stage toolchain loop required by
`.claude/rules/general-code-change.md` was executed by the v2 executor.
Stages 4 (architecture-boundary tests) and 6 (contract/schema compatibility)
are not applicable to this Python-only feature; stages 1, 2, 3, 5, and 7 are
covered as below.

| Stage | Command | Evidence |
|---|---|---|
| 1. Formatting | `env -u VIRTUAL_ENV poetry run black .` | `v2/evidence/qa-gates/final-black.2026-05-28T22-10.md` |
| 2. Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | `v2/evidence/qa-gates/final-ruff.2026-05-28T22-10.md` |
| 3. Type checking | `env -u VIRTUAL_ENV poetry run pyright` | `v2/evidence/qa-gates/final-pyright.2026-05-28T22-10.md` |
| 4. Architecture-boundary | N/A (no architecture-boundary tests configured for this Python repo) | N/A |
| 5. Unit tests | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T22-10.md` |
| 6. Contract/schema | N/A (no external contract/schema diff applicable) | N/A |
| 7. Integration tests | Included in the Pytest run above (`tests/gui/integration/`) | Same artifact as stage 5 |

The Poetry `env -u VIRTUAL_ENV` prefix is required in this repository per
the in-repo memory note (`poetry-virtualenv-quirk`) so Poetry uses the
project virtualenv rather than the ambient global VIRTUAL_ENV.

## Overall Verdict

**FAIL** — one Blocking finding: the behavioral CSV export test leaks real
filesystem writes (B-1), violating the explicit no-temp-files invariant of
both the cross-cutting test rules and the v2 spec.
