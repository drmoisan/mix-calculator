# Policy Compliance Audit: mix-pipeline-gui (Issue #19)

**Audit Date:** 2026-05-27
**Code Under Test:** Feature branch `feature/mix-pipeline-gui-19` (head `ad8c84fa25aa52296360284ff39ba5176ac1494d`) versus base `main` at merge-base `703de5170c37dadb8189eecc01398730d5c50e8d`. 24 production modules under `src/gui/**` (1538 stmts, 238 branches across full repo, of which 657 stmts and 46 branches are new GUI code). 19 test modules under `tests/gui/**`. Two project manifest files (`pyproject.toml`, `quality-tiers.yml`) and `poetry.lock`.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 24 prod + 19 test files | 279 tests | PASS — 279 pass, 0 fail | 100% line / 100% branch (881 stmts / 192 branches) | 100% line / 100% branch (1538 stmts / 238 branches) | 100% line / 100% branch on every `src/gui/**` module |

Note: Only Python source files changed on the branch. No TypeScript, PowerShell, C#, Bash, or governed JSON files changed. Workflow files under `.github/workflows/**` and `scripts/benchmarks/**` did not change.

### Coverage Evidence Checklist

- Python baseline coverage artifact: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/baseline/pytest-coverage.2026-05-27T20-59.md`
- Python post-change coverage artifact: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md`
- TypeScript baseline coverage artifact: `N/A - out of scope (no TypeScript files on branch)`
- TypeScript post-change coverage artifact: `N/A - out of scope (no TypeScript files on branch)`
- PowerShell baseline coverage artifact: `N/A - out of scope (no PowerShell files on branch)`
- PowerShell post-change coverage artifact: `N/A - out of scope (no PowerShell files on branch)`
- Per-language comparison summary: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/coverage-delta.2026-05-27T20-59.md`

**Verdict gate:** Numeric baseline and post-change coverage are present for the in-scope language (Python). No baseline, QA, or coverage-comparison artifact is missing.

---

## Executive Summary

The mix-pipeline-gui feature adds a PySide6 desktop application driving the existing mix decomposition pipeline. The change is Python-only and adheres to the agreed Model-View-Presenter passive-view design: view contracts in `src/gui/protocols.py` carry no Qt import, presenters in `src/gui/presenters/**` run without a `QApplication`, and Qt widgets in `src/gui/widgets/**` are thin signal/slot adapters. Excel/SQLite I/O routes through typed boundaries (`WorkbookReaderProtocol`, the reused loaders, the existing `src/pandas_io.py`, and the new `DbService`); transforms reuse the existing pure functions unchanged.

The full Python toolchain was executed and recorded by the executor in `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-*.md`. All four stages passed: `poetry run black .` (0 reformats), `poetry run ruff check .` (0 errors), `poetry run pyright` (0 errors, 0 warnings strict), and `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` (279 pass, 0 fail; 100% line / 100% branch repo-wide and on every new GUI module).

One non-blocking finding is recorded: `src/gui/exporters/excel_exporter.py:69` carries `# noqa: N802 - mirrors the pandas API member name`, which is not on the pre-authorized list in `.claude/rules/python-suppressions.md` and has no recorded explicit user approval. The suppression sits on a Protocol method intentionally named `ExcelWriter` so the typed-view of pandas matches the real API member; the policy escalation path (try alternative resolutions, then explicit user approval) is documented but no approval is on file. Verdict: non-blocking PARTIAL — narrowest possible suppression, factual rationale, no security or correctness impact, no other suppressions in production code.

**Policy documents evaluated:**
- PASS `CLAUDE.md` (standing instructions)
- PASS `.claude/rules/general-code-change.md`
- PASS `.claude/rules/general-unit-test.md`
- PASS `.claude/rules/quality-tiers.md`
- PASS `.claude/rules/tonality.md`
- PASS `.claude/rules/self-explanatory-code-commenting.md`

**Language-specific policies evaluated:**
- PASS (with one non-blocking PARTIAL note) `.claude/rules/python.md`
- PARTIAL `.claude/rules/python-suppressions.md` (one non-pre-authorized `noqa: N802` in production code, no user approval on file)

**Temporary artifacts cleanup:**
- PASS — No temporary scripts created during development.

---

## Rejected Scope Narrowing

None. The caller (orchestrator) explicitly stated "Determine review scope yourself per your SKILL invariants; the orchestrator does not narrow scope." No attempted narrowing was recorded. The audit covers the full branch diff between merge-base `703de5170c37dadb8189eecc01398730d5c50e8d` and head `ad8c84fa25aa52296360284ff39ba5176ac1494d`.

---

## Evidence Location Compliance

The reviewer scanned the branch diff for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`. Result: no files. Every evidence artifact for the executor is under the canonical `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/<kind>/` path. Scan command:

```
git diff --name-only 703de5170c37dadb8189eecc01398730d5c50e8d..HEAD \
  | grep -E "^artifacts/(baselines|qa|coverage|evidence)/"
```

Result: zero matches. PASS.

The bundled `validate_evidence_locations.py` is not present in this repository; per the persisted reviewer memory, the equivalent git-diff scan above is the substitute and produced a clean result.

---

## Modified-Workflow Policy Rule

Per the `modified-workflow-needs-green-run` rule in `feature-review-workflow/SKILL.md`, the branch diff was scanned for paths matching `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**`. Scan command:

```
git diff --name-only 703de5170c37dadb8189eecc01398730d5c50e8d..HEAD \
  | grep -E "^(\.github/workflows/|scripts/benchmarks/|\.github/actions/)"
```

Result: zero matches. The rule does not fire. PASS.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Independence — Tests run in any order | PASS | Tests under `tests/gui/**` use function-scoped fixtures, no shared module-level state, no inter-test ordering dependency. The Qt fixtures route through `pytest-qt` `qtbot`, which manages widget lifetime per test. |
| Isolation — Each test targets single behavior | PASS | Each test exercises one presenter method, one widget signal/slot, or one exporter call. Test names follow `test_<unit>_<scenario>` (for example `test_worker_emits_error_with_message_on_failure`). |
| Fast Execution | PASS | Final QA reports 279 tests pass; the harness uses `qtbot.waitSignal` (event-driven) rather than wall-clock waits. No `time.sleep`, `QThread.sleep`, or `QTest.qWait` calls in test code (verified by grep). |
| Determinism — Consistent results | PASS | No randomness without seeding (hypothesis is the only RNG source, seeded by pytest-hypothesis). No clock dependencies. All I/O routed through fakes/`BytesIO`/`:memory:` SQLite. |
| Readability & Maintainability | PASS | Tests are organized by module mirror, use AAA structure with explicit Arrange/Act/Assert comments, and carry intent docstrings. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| Baseline Coverage Documented | PASS | `evidence/baseline/pytest-coverage.2026-05-27T20-59.md`: line 100% (881 stmts), branch 100% (192 branches). Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. |
| No Coverage Regression | PASS | Post-change line 100% / branch 100% (1538 stmts / 238 branches). Pre-existing `src/` modules remain at 100% line / 100% branch. See `evidence/qa-gates/coverage-delta.2026-05-27T20-59.md`. |
| New Code Coverage >= 85% line / >= 75% branch | PASS | Every `src/gui/**` module reports 100% line / 100% branch (657 new stmts, 46 new branches). All thresholds met. |
| Comprehensive Coverage | PASS | All public methods on every new class exercised; every Protocol-implementing fake covered; per-module rows in `final-pytest-coverage.2026-05-27T20-59.md`. |
| Positive Flows | PASS | Examples: `test_pipeline_presenter` exercises import-one, import-all, run, save, open success paths; `test_excel_exporter` writes one sheet per selected table to a `BytesIO`. |
| Negative Flows | PASS | Examples: `test_pipeline_presenter::test_on_import_one_routes_value_error_to_view_show_error`, `test_export_presenter::test_export_rejects_empty_selection`, `test_pipeline_service` covers loader `ValueError` propagation. |
| Edge Cases | PASS | Single-tab workbook, duplicate tab names, max-rows preview clamp, export-all vs partial-checklist, SKU_LU default path fallback. |
| Error Handling | PASS | Worker error path tested on both main thread (synchronous coverage) and QThread (event-driven via `qtbot.waitSignal`). `test_pipeline_worker::test_worker_emits_error_with_message_on_failure`. |
| Concurrency | PASS | Worker tests verify the QThread path emits `finished`/`error` correctly through `qtbot.waitSignal`. |
| State Transitions | PASS | `PipelinePresenter` IDLE→IMPORTING→IDLE and IDLE→RUNNING→IDLE transitions are exercised; `can_run` guard tested in both states. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 100% lines -> Post-change: 100% lines. Change: +0% lines (881 -> 1538 stmts, still at 100%). Branch: baseline 100% (192) -> post-change 100% (238), change +0%. New/changed-code coverage: 100% line / 100% branch (every `src/gui/**` module). Disposition: PASS. Evidence: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` and `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/coverage-delta.2026-05-27T20-59.md`.
- TypeScript: N/A — no changed files on branch.
- PowerShell: N/A — no changed files on branch.
- C#: N/A — no changed files on branch.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clear Failure Messages | PASS | Tests use plain pytest `assert` with informative comparisons; signal-blocker assertions narrow `None` before reading args, producing legible failure traces. |
| Arrange-Act-Assert Pattern | PASS | All test functions follow AAA with explicit comments (for example `# Arrange:`, `# Act:`, `# Assert:` in `test_pipeline_worker.py`). |
| Document Intent | PASS | Every test function has a docstring stating the behavior it verifies (for example `"""A successful task moved to a QThread emits finished with the result."""`). |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| Avoid External Dependencies | PASS | No network, no databases except `sqlite3.connect(":memory:")` (verified in `test_db_service.py`), no external processes. |
| Use Mocks/Stubs | PASS | Test fakes are in `tests/gui/fakes/**` (FakeWorkbookReader, FakePipelineService, FakeDbService, fake views, fake exporters); each implements the Protocol surface the unit depends on. |
| Environment Stability | PASS | `conftest.py` sets `QT_QPA_PLATFORM=offscreen` via session-scoped autouse fixture; no temp file creation (grep over `tempfile`/`NamedTemporaryFile`/`TemporaryDirectory` returned zero matches). |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| Pre-submission Review | PASS | This artifact and the companion `code-review.2026-05-27T21-00.md` / `feature-audit.2026-05-27T21-00.md` satisfy the policy audit requirement. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clarify the objective | PASS | `issue.md` and `spec.md` enumerate the nine capabilities; the architecture research at `artifacts/research/mix-pipeline-gui-architecture.2026-05-27T00-00.md` was consumed by the plan. |
| Read existing change plans | PASS | `plan.2026-05-27T20-59.md` is present and was executed in twelve phases as recorded in the per-phase QA artifacts. |
| Document the plan | PASS | Plan file is checked in alongside per-phase QA evidence (`evidence/qa-gates/phase1..11-qa.*.md`). |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Simplicity first | PASS | Passive-view MVP with constructor injection; no DI framework; presenters are plain Python. |
| Reusability | PASS | `PipelineService.run_pipeline` calls the existing pure transforms (`pivot_le`, `pivot_aop`, `build_*`, `run_transforms`) directly without duplicating logic. The CLI surface is unchanged. |
| Extensibility | PASS | The `ExporterRegistry` lets new formats register without changes to `ExportPresenter`. Source selection uses `WorkbookReaderProtocol` so the openpyxl reader can be substituted. |
| Separation of concerns | PASS | View Protocols carry no Qt import; presenters carry no Qt import; transforms are pure and untouched; I/O routes through `src/pandas_io.py` and the new `DbService`/`WorkbookReader`. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Cohesive modules | PASS | `src/gui/` package layout matches the spec: presenters, widgets, services, exporters, workers each in their own subpackage. |
| Under 500 lines | PASS | Largest production file is `src/gui/pipeline_service.py` at 389 lines; largest test file is `tests/gui/test_pipeline_service.py` at 424 lines. All files <= 500 lines. |
| Public vs internal | PASS | Every module declares `__all__`; private helpers are `_prefixed` (for example `_LE_KEY`, `_MAX_SHEET_NAME`, `_import_one_frame`). |
| No circular dependencies | PASS | Dependency direction: `widgets` and `services` know nothing of `presenters`; `presenters` import `protocols` and the `pipeline_service`; `app.py` is the only module wiring them together. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| Descriptive names | PASS | `PipelineService`, `ExporterRegistry`, `SourceSelectionPresenter`, `MainWindowPipelineView`, etc. No abbreviations beyond standard (`db`, `le`, `aop`, `sku_lu`). |
| Docs/docstrings | PASS | Every class and function carries a docstring with Purpose/Responsibilities/Usage/Args/Returns sections per `self-explanatory-code-commenting.md`. Verified in `protocols.py`, `pipeline_service.py`, `pipeline_presenter.py`, and `pipeline_worker.py`. |
| Comment why, not what | PASS | Branching and loop sites carry intent comments (for example the routing-table comment in `_import_one_frame` and the boundary comment in `PipelineWorker.run`). |

### 2.5 After Making Changes — Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| 1. Formatting | PASS | `poetry run black .` -> EXIT_CODE 0; 82 files unchanged. See `evidence/qa-gates/final-black.2026-05-27T20-59.md`. |
| 2. Linting | PASS | `poetry run ruff check .` -> EXIT_CODE 0; 0 errors. See `evidence/qa-gates/final-ruff.2026-05-27T20-59.md`. |
| 3. Type checking | PASS | `poetry run pyright` -> EXIT_CODE 0; 0 errors, 0 warnings, 0 informations (strict). See `evidence/qa-gates/final-pyright.2026-05-27T20-59.md`. |
| 4. Testing | PASS | `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` -> EXIT_CODE 0; 279 pass / 0 fail. See `evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md`. |
| Full toolchain loop | PASS | Per-phase QA artifacts (`phase1..11-qa.*.md`) record clean passes; the final loop completed in a single pass. |
| Explicit reporting | PASS | This audit cites every command and exit code from the canonical evidence artifacts. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| Summarize changes | PASS | The `pr_context.summary.txt` and the feature folder docs summarize the change. |
| Design choices explained | PASS | `spec.md` documents the MVP passive-view design, the typed-Protocol containment of openpyxl/pytest-qt loose typings, and the dependency rationale for `pytest-qt`. |
| Update supporting documents | PASS | `README.md` updated (+53 lines); `quality-tiers.yml` adds entries for every new project. |
| Provide next steps | PASS | The plan's Definition of Done is satisfied; the orchestrator's S9 CI green gate is the residual gate before merge. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| Formatting with Black | PASS | EXIT 0; 82 files unchanged. |
| Linting with Ruff | PASS | EXIT 0; 0 errors. One pre-authorized `# noqa: ARG002 - match ... API` per fake-service mock signature; one non-pre-authorized `# noqa: N802` in `excel_exporter.py:69` recorded under Section 8 Gaps. |
| Type checking with Pyright | PASS | EXIT 0; 0 errors, 0 warnings, 0 informations. No per-call `# type: ignore` or `# pyright: ignore` introduced; loose openpyxl/pytest-qt types contained via typed Protocol views + `typing.cast`. |
| Testing with Pytest | PASS | 279 tests pass; coverage 100% line / 100% branch. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| Strong typing | PASS | All public functions and methods carry full type hints (verified in `protocols.py`, `pipeline_service.py`, `pipeline_presenter.py`, `pipeline_worker.py`). No `Any` introduced; pyright strict zero-error. |
| Dataclasses for value objects | PASS | `ImportSpec` is `@dataclass(frozen=True)` with the six per-input fields; `WiredApplication` is a `@dataclass` carrying the composition handles. |
| Protocols/ABCs for interfaces | PASS | `PipelineServiceProtocol`, `WorkbookReaderProtocol`, `ExporterProtocol`, three view Protocols, plus typed adapter protocols inside `excel_exporter.py` and `test_pipeline_worker.py` for openpyxl/pytest-qt containment. |
| Avoid utility classes | PASS | No static-method-only utility classes; helpers are module-level functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| Specific exceptions | PASS | Presenters catch `ValueError` only and route to `view.show_error`; non-ValueError exceptions propagate. The single broad-catch is in `PipelineWorker.run`, documented as the worker thread's failure boundary (the worker emits `error(str)` to the UI thread and logs; it does not silently swallow). |
| Logging over print | PASS | All production modules use `logging.getLogger(__name__)`; no `print` statements in production code. |
| Invariants at construction | PASS | `ImportSpec` is frozen; `PipelineService.__init__` accepts an optional `DbService` and constructs a default when absent. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | PASS | All tests use Pytest. Qt tests use `pytest-qt` (added as a dev dependency this feature). |
| Coverage expectation | PASS | Repo-wide line 100% (>= 85%) and branch 100% (>= 75%). New code 100% line / 100% branch (>= 85% / 75% targets met with margin). |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Focused unit tests | PASS | Each test exercises a single presenter method, signal/slot, or exporter call. Property tests (`hypothesis`) cover pure-function-like presenter paths in `test_source_selection_presenter`, `test_pipeline_presenter`, and `test_export_presenter`. |
| Mocking sparingly | PASS | Fakes implement the Protocol surface the unit depends on; the test fakes do not patch arbitrary internals. |
| Organization | PASS | Tests mirror code structure: `tests/gui/test_<module>.py` for `src/gui/<area>/<module>.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| Naming conventions | PASS | `test_<unit>_<scenario>` form used throughout (for example `test_worker_emits_finished_with_result_on_success`). |
| Docstrings/comments | PASS | Each test function has a docstring; Arrange/Act/Assert phases are commented. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | PASS | `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` -> EXIT 0; 279 pass / 0 fail. |
| No Alternative Test Runners | PASS | Only Pytest is used. |

---

## 5. Test Coverage Detail

Repo-wide and per-module coverage is documented in `evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md`. Every `src/gui/**` module reports 100% line and 100% branch coverage:

```
src/gui/__init__.py                                    0 stmts, 100%
src/gui/app.py                                        70 stmts, 100%
src/gui/main_window.py                                63 stmts, 100%
src/gui/pipeline_service.py                           67 stmts, 100%
src/gui/protocols.py                                  18 stmts, 100%
src/gui/exporters/base.py                              8 stmts, 100%
src/gui/exporters/registry.py                         14 stmts, 100%
src/gui/exporters/excel_exporter.py                   15 stmts, 100%
src/gui/exporters/csv_exporter.py                     18 stmts, 100%
src/gui/presenters/source_selection_presenter.py      31 stmts, 100%
src/gui/presenters/pipeline_presenter.py             106 stmts, 100%
src/gui/presenters/export_presenter.py                24 stmts, 100%
src/gui/services/workbook_reader.py                   26 stmts, 100%
src/gui/services/db_service.py                        26 stmts, 100%
src/gui/widgets/source_input_widget.py                56 stmts, 100%
src/gui/widgets/preview_widget.py                     27 stmts, 100%
src/gui/widgets/export_dialog.py                      46 stmts, 100%
src/gui/widgets/progress_dialog.py                    20 stmts, 100%
src/gui/workers/pipeline_worker.py                    22 stmts, 100%
```

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 279 | PASS |
| Tests Passed | 279 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | Not separately captured; final QA artifact records only the pass/fail and coverage outputs | informational |
| Functions/Classes Tested | All public methods on every new class (see Section 5) | PASS |
| Code Coverage | 100% line / 100% branch repo-wide | PASS |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | EXIT 0; 82 files unchanged | PASS |
| Ruff Linting | `poetry run ruff check .` | EXIT 0; 0 errors | PASS |
| Pyright Type Checking | `poetry run pyright` | EXIT 0; 0 errors strict | PASS |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` | EXIT 0; 279 pass | PASS |

**Notes:** All toolchain commands above were executed by the executor and recorded in `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-*.md`. The reviewer verified the artifacts' presence and contents; no re-execution was performed (per the SKILL contract).

---

## 8. Gaps and Exceptions

### Identified Gaps

1. **Non-pre-authorized `# noqa: N802` in production code** (PARTIAL, non-blocking).
   - **Location:** `src/gui/exporters/excel_exporter.py:69`.
   - **Suppression:** `def ExcelWriter(  # noqa: N802 - mirrors the pandas API member name`.
   - **Context:** This is a method on a TYPE_CHECKING-only `_PandasExcelWriters` Protocol that typed-views the pandas module's `ExcelWriter` factory. The method must be named `ExcelWriter` (PascalCase) to match the real pandas API member; renaming it would break the typed view.
   - **Policy reference:** `.claude/rules/python-suppressions.md` does not list `N802` among pre-authorized patterns, and there is no recorded explicit user approval on file.
   - **Risk:** None to runtime correctness; the suppression is the narrowest possible (single line) and the rationale is factual. The code does not introduce a renamed-symbol surprise to callers because the symbol is on a Protocol matching an existing public API.
   - **Recommended remediation (non-blocking):** Either obtain explicit user approval for this single-line `N802` (and the policy could later add a pre-authorized pattern for "TYPE_CHECKING Protocol view mirroring a third-party API member"), or replace the typed-view approach with a `cast(Any, pd).ExcelWriter(...)` call (which would re-introduce `Any` and trade one strict-mode concession for another). The current choice (contained `noqa: N802`) is the cleaner outcome under strict mode and matches the typed-view containment pattern already used in `src/pandas_io.py`.

2. **Property test density on T2 service/registry modules** (NON-BLOCKING NOTE).
   - **Modules:** `src/gui/pipeline_service.py`, `src/gui/exporters/registry.py`, `src/gui/exporters/base.py`.
   - **Observation:** The general-unit-test policy requires ">= 1 property test per pure function" for T1/T2 modules. These T2 modules expose mostly orchestration over impure I/O (loader delegation, registry mutation) rather than pure functions; the executor placed property tests on the three T2 presenters where pure-function-like content concentrates. No property test exists on these three modules.
   - **Risk:** Low. The methods are essentially adapters; behavior is exercised by example-based tests with full branch coverage.
   - **Recommended remediation (non-blocking):** Not required by the strict reading of the rule because these modules contain no pure functions in the sense the policy targets. If the team wants stricter conformance, add a property test for `ExporterRegistry.register/get/available_formats` round-trips.

### Approved Exceptions

None on file.

### Removed/Skipped Tests

None.

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. `ad8c84f` feat(mix-pipeline-gui): add main window, app entry, and e2e tests
2. `4253c22` feat(mix-pipeline-gui): add presenters, worker, and widget layer
3. `3bcc209` feat(mix-pipeline-gui): add initial GUI service and exporter stack

### Files Modified

- 24 new production modules under `src/gui/**`
- 19 new test modules under `tests/gui/**` (plus `conftest.py` and `fakes/**`)
- 26 evidence artifacts under `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/**`
- 4 scoping docs under `docs/features/active/2026-05-27-mix-pipeline-gui-19/` (`issue.md`, `spec.md`, `user-story.md`, `plan.2026-05-27T20-59.md`)
- `pyproject.toml` (+4 lines: `pytest-qt` dev dependency and `mix-pipeline-gui` console script)
- `poetry.lock` (+23 lines)
- `quality-tiers.yml` (+32 lines)
- `README.md` (+53 lines)
- Two memory artifacts under `.claude/agent-memory/atomic-executor/`

---

## 10. Compliance Verdict

### Overall Status: PARTIALLY COMPLIANT — minor non-blocking suppression deviation

The change is functionally complete, fully tested, and meets every uniform coverage gate. The only deviation is a single-line `# noqa: N802` in production code that is not on the pre-authorized list in `.claude/rules/python-suppressions.md`. This is a non-blocking PARTIAL finding because:

- It is the narrowest possible suppression scope (one line).
- The rationale is factual ("mirrors the pandas API member name") and non-discretionary — the Protocol method must match the pandas API name.
- The alternative (re-introducing `cast(Any, pd)`) would weaken strict typing elsewhere.
- The same containment pattern (typed Protocol view) is the documented approach already used in `src/pandas_io.py`.

The reviewer recommends either an explicit one-time user approval for this single suppression or a small policy extension to pre-authorize "TYPE_CHECKING Protocol view mirroring a third-party API member" as an approved `N802` pattern. Either outcome is appropriate; neither blocks merge under a reasonable read of the policy.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure
- PASS Naming, Docs, Comments
- PASS Toolchain Execution
- PASS Summarize & Document

#### Language-Specific Code Change Policy (Section 3)
- PASS Python Tooling & Baseline (with PARTIAL note on `N802` suppression)
- PASS Python Design & Typing
- PASS Python Error Handling

#### General Unit Test Policy (Section 1)
- PASS Core Principles
- PASS Coverage & Scenarios
- PASS Test Structure
- PASS External Dependencies
- PASS Policy Audit

#### Language-Specific Unit Test Policy (Section 4)
- PASS Python Framework & Scope
- PASS Python Test Style & Structure
- PASS Python Naming & Readability
- PASS Python Toolchain

### Metrics Summary

- PASS 279/279 tests passing (100%)
- PASS 100% line and 100% branch coverage repo-wide
- PASS 100% line and 100% branch on every `src/gui/**` module (657 new stmts, 46 new branches)
- PASS All files under 500 lines (largest production 389, largest test 424)
- PASS All code quality checks passing
- PASS Every new project classified in `quality-tiers.yml`

### Recommendation

**Ready for merge after either a one-time user approval for the single `N802` suppression in `src/gui/exporters/excel_exporter.py:69`, or an equivalent policy extension. The remediation is documentation-only; no code or test change is required.**

Because the finding is non-blocking and presents no correctness or security risk, no remediation plan is created for this audit. The orchestrator's S9 CI green gate remains the operational pre-merge gate.

---

## Appendix A: Test Inventory

Test modules under `tests/gui/**` (19 files, 279 collected tests). One-line module summary per file:

- `tests/gui/conftest.py` — session-scoped `QT_QPA_PLATFORM=offscreen` harness.
- `tests/gui/fakes/fake_views.py` — `FakeSourceSelectionView`, `FakePipelineView`, `FakeExportView` implementing the three view Protocols.
- `tests/gui/fakes/fake_services.py` — `FakeWorkbookReader`, `FakePipelineService`, `FakeDbService` implementing service Protocols.
- `tests/gui/fakes/fake_exporters.py` — `FakeExporter` implementing the `ExporterProtocol` for registry tests.
- `tests/gui/test_app_composition.py` — composition root tests: registry build, view-adapter routing, presenter wiring.
- `tests/gui/test_source_selection_presenter.py` — tab discovery on file selection, preview rendering, error routing, plus hypothesis property test on tab-list pass-through.
- `tests/gui/test_pipeline_presenter.py` — import-one, import-all, run guard, save, open, ValueError-to-view error routing, plus hypothesis property test on running-state symmetry.
- `tests/gui/test_export_presenter.py` — registry-driven format resolution, empty-selection rejection, plus hypothesis property test on export-all selection.
- `tests/gui/test_exporter_registry.py` — register, get, available_formats round-trips, duplicate registration handling.
- `tests/gui/test_excel_exporter.py` — one-sheet-per-selected-table write to a `BytesIO` target.
- `tests/gui/test_csv_exporter.py` — one-file-per-selected-table write to a fake-filesystem directory.
- `tests/gui/test_pipeline_service.py` — import_le/import_aop/import_skulu/import_sources, run_pipeline orchestration, save/open delegation.
- `tests/gui/test_workbook_reader.py` — get_sheet_names and read_sheet_preview against an in-memory `BytesIO` workbook.
- `tests/gui/test_db_service.py` — save_tables and open_tables round-trip through `sqlite3.connect(":memory:")`.
- `tests/gui/test_source_input_widget.py` — `pytest-qt` widget tests for the per-input file/tab signal/slot wiring.
- `tests/gui/test_preview_widget.py` — `pytest-qt` widget tests for the `QTableView`-backed preview surface.
- `tests/gui/test_export_dialog.py` — `pytest-qt` widget tests for the checklist + export-all dialog.
- `tests/gui/test_pipeline_worker.py` — QThread + main-thread coverage of `finished`/`error` emissions with event-driven `qtbot.waitSignal`.
- `tests/gui/test_gui_integration.py` — end-to-end select -> import -> run -> save -> reopen -> export integration scenarios against fakes.

Full enumeration of the 279 individual test IDs is recorded in `evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` (the post-change pytest run output).

---

## Appendix B: Toolchain Commands Reference

```bash
poetry run black .
poetry run ruff check .
poetry run pyright
QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
```

Branch-diff scope commands used during this audit:

```bash
git diff --name-only 703de5170c37dadb8189eecc01398730d5c50e8d..HEAD
git diff --name-only 703de5170c37dadb8189eecc01398730d5c50e8d..HEAD \
  | grep -E "^artifacts/(baselines|qa|coverage|evidence)/"
git diff --name-only 703de5170c37dadb8189eecc01398730d5c50e8d..HEAD \
  | grep -E "^(\.github/workflows/|scripts/benchmarks/|\.github/actions/)"
```

---

**Audit Completed By:** feature-review agent (Claude Opus 4.7 1M)
**Audit Date:** 2026-05-27
**Policy Version:** Current (as of audit date)
