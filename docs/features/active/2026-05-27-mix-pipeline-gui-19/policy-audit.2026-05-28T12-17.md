# Policy Compliance Audit: mix-pipeline-gui (Issue #19) — Post-Rebase Re-audit

**Audit Date:** 2026-05-28
**Audit Type:** Re-audit following rebase onto current `main` (#15 / #18 / #20 / #23 merged into base).
**Code Under Test:** Feature branch `feature/mix-pipeline-gui-19` (head `e68ea3d`) vs base `main` at merge-base `7836c24ed350ebe654b924373335aa606c1fa215`. 24 production modules under `src/gui/**`, 19 test modules under `tests/gui/**` (94 GUI tests; full suite 314 per executor's post-rebase toolchain run), `pyproject.toml`, `poetry.lock`, `quality-tiers.yml`, `README.md`, and four feature scoping docs plus prior audit artifacts and per-phase QA evidence under `docs/features/active/2026-05-27-mix-pipeline-gui-19/`.

**Prior audits (superseded):**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/policy-audit.2026-05-27T21-00.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/code-review.2026-05-27T21-00.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/feature-audit.2026-05-27T21-00.md`

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 24 prod + 19 test files (rebased onto post-#15/#18/#20/#23 main) | 314 (full suite) / 94 GUI-only | PASS — 314 pass, 0 fail (per caller-reported post-rebase toolchain run) | 100% line / 100% branch (pre-existing `src/` modules; new base includes mix-bottoms-up, NRR summary, and the bottoms-up tie-out fix) | 100% line / 100% branch | 100% line / 100% branch on every `src/gui/**` module |

Note: Only Python source changed on the branch. No TypeScript, PowerShell, C#, Bash, or governed JSON files changed. Workflow files under `.github/workflows/**`, action files under `.github/actions/**`, and `scripts/benchmarks/**` did not change (verified by git diff scan).

### Coverage Evidence Checklist

- Python baseline coverage artifact: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/baseline/pytest-coverage.2026-05-27T20-59.md` (pre-rebase capture; the executor reported a clean post-rebase toolchain run delta over the new base but did not commit a fresh baseline-on-new-base artifact for this re-audit)
- Python post-change coverage artifact: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` (executor-reported post-rebase numbers reproduce this artifact's verdict: 100% line / 100% branch with 314 pass — see caller delegation summary)
- TypeScript baseline coverage artifact: `N/A - out of scope (no TypeScript files on branch)`
- TypeScript post-change coverage artifact: `N/A - out of scope (no TypeScript files on branch)`
- PowerShell baseline coverage artifact: `N/A - out of scope (no PowerShell files on branch)`
- PowerShell post-change coverage artifact: `N/A - out of scope (no PowerShell files on branch)`
- Per-language comparison summary: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/coverage-delta.2026-05-27T20-59.md`

**Verdict gate:** Numeric baseline and post-change coverage are present for the in-scope language (Python) under the canonical evidence path. The pre-rebase artifacts remain operative because the rebase only changed pre-existing `src/mix_*` modules whose coverage is independently maintained by the upstream features (#15/#18/#20/#23) at 100%; the GUI's coverage surface is identical pre- and post-rebase. The repo-wide post-change percentage reported by the caller (100% line / 100% branch, 314 pass) clears the 85%/75% threshold with substantial margin.

---

## Executive Summary

The branch was rebased onto `7836c24` (post-#15 NRR summary, post-#18 bottoms-up rollups, post-#20 mix tie-out fix). The GUI's `PipelineService.run_pipeline` orchestrates the same import surface as the post-rebase `mix_pipeline.main` (lines 197-204 of `main` on `7836c24`): `pivot_le`, `pivot_aop`, `build_customer_lu`, `build_aop_norm`, `build_le_norm`, `build_aop_vs_le`, `build_mix_base`, then `run_transforms`. No stale imports were introduced; the `src.mix_pipeline_run.run_transforms` chain now includes the bottoms-up and NRR-summary builders, and the GUI consumes the result dict opaquely (`**derived`), so behavioral assumptions remain intact.

The caller reported a clean post-rebase toolchain run (Black/Ruff/Pyright: 0 issues; Pytest: 314 pass / 0 fail; coverage 100% line / 100% branch). The reviewer independently verified that `from src.gui.pipeline_service import PipelineService, ImportSpec` imports cleanly under the rebased base, and that no production file exceeds 500 lines (largest production `pipeline_service.py` at 389 lines).

Three of the four prior non-blocking findings persist verbatim under the new base:

1. **`# noqa: N802` in `src/gui/exporters/excel_exporter.py:69`** still present (PARTIAL, non-blocking). No new pre-authorized N802 pattern was added to `.claude/rules/python-suppressions.md` by the upstream merges, and no explicit user approval was recorded in the rebased history.
2. **Three T2 modules without hypothesis property tests** (`pipeline_service.py`, `exporters/registry.py`, `exporters/base.py`) — unchanged from prior review (NON-BLOCKING NOTE).
3. **`pipeline_worker.py` broad-catch** — documented worker boundary, within policy (INFO, no change).

Finding #2 from the prior review (the synchronous-vs-worker run-path observation) needs to be re-stated more precisely after re-reading the composition root:

- **Re-stated finding (MINOR, non-blocking under spec language):** `src/gui/app.py::build_application` constructs `PipelineWorker` nowhere and connects none of the `MainWindow.run_requested`, `import_one_requested`, `import_all_requested`, `save_requested`, `open_db_requested`, or `export_requested` signals to presenter handlers. Only the per-input `file_selected` and `render_tab_requested` signals are wired (lines 109-114). The Run / Save / Open / Export / Import / Import-All buttons emit their signals into the void in the production composition root. Presenter behavior is fully verified by unit tests that drive `PipelinePresenter` / `ExportPresenter` directly, and the integration test `tests/gui/test_gui_integration.py` exercises the presenter path end-to-end without touching `MainWindow`'s buttons. The spec's Definition of Done is satisfied at the presenter contract level; production button-to-presenter wiring is incomplete. See Section 8 Gaps.

**Policy documents evaluated:**
- PASS `CLAUDE.md` (standing instructions)
- PASS `.claude/rules/general-code-change.md`
- PASS `.claude/rules/general-unit-test.md`
- PASS `.claude/rules/quality-tiers.md`
- PASS `.claude/rules/tonality.md`
- PASS `.claude/rules/self-explanatory-code-commenting.md`
- PASS `.claude/rules/benchmark-baselines.md` (does not fire — no baseline files under `scripts/benchmarks/**` were added/modified)
- PASS `.claude/rules/ci-workflows.md` (does not fire — no `.github/workflows/**` files were added/modified)

**Language-specific policies evaluated:**
- PASS (with one persisting non-blocking PARTIAL note) `.claude/rules/python.md`
- PARTIAL `.claude/rules/python-suppressions.md` (one non-pre-authorized `noqa: N802` in production code, no user approval on file)

**Temporary artifacts cleanup:**
- PASS — No temporary scripts created during development; the per-phase QA artifacts are persisted under the canonical evidence path.

---

## Rejected Scope Narrowing

None. The caller explicitly asked for a full re-audit against the rebased base and did not narrow scope. The audit covers the full branch diff between merge-base `7836c24` and head `e68ea3d`.

---

## Evidence Location Compliance

The reviewer scanned the branch diff for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`. Scan command:

```
git diff --name-only main...HEAD | grep -E "^artifacts/(baselines|qa|coverage|evidence)/"
```

Result: zero matches. Every evidence artifact for the executor is under the canonical `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/<kind>/` path. PASS.

The bundled `validate_evidence_locations.py` is not present in this repository (recorded in agent memory); the equivalent git-diff scan above is the substitute and produced a clean result.

---

## Modified-Workflow Policy Rule

Per the `modified-workflow-needs-green-run` rule, the branch diff was scanned for `.github/workflows/**`, `scripts/benchmarks/**`, and `.github/actions/**`. Scan command:

```
git diff --name-only main...HEAD | grep -E "^(\.github/workflows/|scripts/benchmarks/|\.github/actions/)"
```

Result: zero matches. The rule does not fire. PASS.

`benchmark-baselines.md` does not fire because no baseline file was added/modified; `ci-workflows.md` does not fire because no `pwsh` workflow step was added/modified. The rebase merged #15/#18/#20/#23 into base without those changes appearing in the branch diff against the new base.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Independence — tests run in any order | PASS | Tests under `tests/gui/**` use function-scoped fixtures, no shared module-level state. `pytest-qt` `qtbot` manages widget lifetime per test. |
| Isolation — each test targets single behavior | PASS | Each test exercises one presenter method, one widget signal/slot, or one exporter call. Test names follow `test_<unit>_<scenario>`. |
| Fast Execution | PASS | Caller-reported post-rebase run: 314 tests pass in a single suite. The harness uses `qtbot.waitSignal` (event-driven) rather than wall-clock waits; no `time.sleep`, `QThread.sleep`, or `QTest.qWait` in test code (verified by grep over `tests/gui/**`). |
| Determinism — consistent results | PASS | No randomness without seeding (hypothesis only, seeded by pytest-hypothesis). All I/O routed through fakes/`BytesIO`/`:memory:` SQLite. |
| Readability & Maintainability | PASS | AAA structure with explicit Arrange/Act/Assert comments; per-test docstrings. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| Baseline Coverage Documented | PASS | `evidence/baseline/pytest-coverage.2026-05-27T20-59.md` recorded at 100% line / 100% branch before rebase. Upstream merges added `src/mix_bottomsup.py`, `src/mix_nrr_summary.py`, helper modules, and updates to `src/mix_rollups.py` and `src/mix_pipeline_run.py`, each of which is independently covered at 100% by their respective features per the merged feature-audit artifacts at `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/` and `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`. |
| No Coverage Regression | PASS | Caller-reported post-rebase coverage: 100% line / 100% branch. The GUI's surface did not change in the rebase; pre-existing `src/` modules are at 100% per their feature audits. |
| New Code Coverage >= 85% line / >= 75% branch | PASS | Every `src/gui/**` module reports 100% line / 100% branch in the original final-QA artifact and the rebase did not alter `src/gui/**`. |
| Comprehensive Coverage | PASS | All public methods on every new class exercised; per-module rows in `final-pytest-coverage.2026-05-27T20-59.md`. |
| Positive Flows | PASS | `test_pipeline_presenter` exercises import-one, import-all, run, save, open success paths; `test_excel_exporter` writes one sheet per selected table to a `BytesIO`. |
| Negative Flows | PASS | `test_pipeline_presenter::test_on_import_one_routes_value_error_to_view_show_error`, `test_export_presenter::test_export_rejects_empty_selection`. |
| Edge Cases | PASS | Single-tab workbook, duplicate tab names, max-rows preview clamp, export-all vs partial-checklist, SKU_LU default path fallback. |
| Error Handling | PASS | Worker error path tested on both main thread and after `moveToThread(QThread)`. |
| Concurrency | PASS | Worker tests verify the QThread path emits `finished`/`error` via `qtbot.waitSignal`. |
| State Transitions | PASS | `PipelinePresenter` IDLE→IMPORTING→IDLE and IDLE→RUNNING→IDLE transitions exercised. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 100% line / 100% branch -> Post-change: 100% line / 100% branch. Change: 0%. New/changed-code coverage: 100% line / 100% branch on every `src/gui/**` module. Disposition: PASS. Evidence: `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` (operative because the GUI's coverage surface is unchanged by the rebase) and caller-reported post-rebase run (314 pass, 100%/100%).
- TypeScript: N/A — no changed files on branch.
- PowerShell: N/A — no changed files on branch.
- C#: N/A — no changed files on branch.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clear Failure Messages | PASS | Plain pytest `assert` with informative comparisons; signal-blocker assertions narrow `None` before reading args. |
| Arrange-Act-Assert Pattern | PASS | All tests follow AAA with explicit comments. |
| Document Intent | PASS | Every test function has a docstring. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| Avoid External Dependencies | PASS | No network, no databases except `sqlite3.connect(":memory:")`. |
| Use Mocks/Stubs | PASS | Fakes in `tests/gui/fakes/**` implement the Protocol surface the unit depends on. |
| Environment Stability | PASS | `conftest.py` sets `QT_QPA_PLATFORM=offscreen`; no temp file creation (grep confirmed). |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| Pre-submission Review | PASS | This re-audit and the companion `code-review.2026-05-28T12-17.md` / `feature-audit.2026-05-28T12-17.md` satisfy the requirement. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clarify the objective | PASS | `issue.md` and `spec.md` enumerate the nine capabilities. |
| Read existing change plans | PASS | `plan.2026-05-27T20-59.md` is present and was executed in twelve phases. |
| Document the plan | PASS | Plan file is checked in alongside per-phase QA evidence. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Simplicity first | PASS | Passive-view MVP with constructor injection; no DI framework. |
| Reusability | PASS | `PipelineService.run_pipeline` calls the existing pure transforms directly. The CLI surface is unchanged post-rebase. |
| Extensibility | PASS | `ExporterRegistry` lets new formats register without changes to `ExportPresenter`. |
| Separation of concerns | PASS | View Protocols carry no Qt import; presenters carry no Qt import; transforms reused unchanged. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Cohesive modules | PASS | `src/gui/` layout matches the spec. |
| Under 500 lines | PASS | `wc -l` over `src/gui/**` and `tests/gui/**`: largest production `pipeline_service.py` at 389 lines; largest test `test_pipeline_service.py` at 424 lines. All <= 500. |
| Public vs internal | PASS | Every module declares `__all__`; private helpers `_prefixed`. |
| No circular dependencies | PASS | `widgets` and `services` know nothing of `presenters`; `presenters` import `protocols` and the `pipeline_service`; `app.py` wires them. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| Descriptive names | PASS | No abbreviations beyond standard (`db`, `le`, `aop`, `sku_lu`). |
| Docs/docstrings | PASS | Every class and function carries a docstring per `self-explanatory-code-commenting.md`. |
| Comment why, not what | PASS | Branching and loop sites carry intent comments. |

### 2.5 After Making Changes — Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| 1. Formatting | PASS | Caller-reported post-rebase `poetry run black .` -> 0 issues. The persisted pre-rebase artifact `evidence/qa-gates/final-black.2026-05-27T20-59.md` recorded EXIT 0. |
| 2. Linting | PASS | Caller-reported post-rebase `poetry run ruff check .` -> 0 issues. Persisted `evidence/qa-gates/final-ruff.2026-05-27T20-59.md` recorded EXIT 0. |
| 3. Type checking | PASS | Caller-reported post-rebase `poetry run pyright` -> 0 issues. Persisted `evidence/qa-gates/final-pyright.2026-05-27T20-59.md` recorded 0 errors / 0 warnings strict. |
| 4. Testing | PASS | Caller-reported post-rebase `QT_QPA_PLATFORM=offscreen poetry run pytest` -> 314 pass / 0 fail; coverage 100% line / 100% branch. |
| Full toolchain loop | PASS | The caller confirmed the loop completed in one pass on the rebased branch. |
| Explicit reporting | PASS | Commands and outcomes are reported above. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| Summarize changes | PASS | The feature folder docs and the pre-rebase `pr_context.summary.txt` (and the executor's caller-reported summary) describe the change. NOTE: the persisted `artifacts/pr_context.summary.txt` reflects the pre-rebase head `ad8c84fa…` and pre-rebase base `b0e048f…`; the reviewer used `git diff --name-only main...HEAD` against the current head `e68ea3d` and base `7836c24` for diff scope. The pr_context artifacts should be regenerated before merge so PR-creation tooling sees the post-rebase context. |
| Design choices explained | PASS | `spec.md` documents the MVP passive-view design and the typed-Protocol containment of openpyxl/pytest-qt loose typings. |
| Update supporting documents | PASS | `README.md` updated; `quality-tiers.yml` adds entries for every new project. |
| Provide next steps | PASS | The plan's Definition of Done remains satisfied at the presenter level; the production button-wiring gap (Section 8) is documented as the next step before user-facing GUI use. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| Formatting with Black | PASS | EXIT 0 pre-rebase; caller reported clean post-rebase. |
| Linting with Ruff | PASS | EXIT 0; one pre-authorized `ARG002 - match … API` per fake-service mock signature; one non-pre-authorized `N802` in `excel_exporter.py:69` recorded under Section 8 Gaps. |
| Type checking with Pyright | PASS | EXIT 0; 0 errors, 0 warnings, 0 informations. No per-call `# type: ignore` or `# pyright: ignore` introduced. |
| Testing with Pytest | PASS | 314 tests pass post-rebase; coverage 100% line / 100% branch. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| Strong typing | PASS | All public functions and methods carry full type hints. Pyright strict zero-error. |
| Dataclasses for value objects | PASS | `ImportSpec` is `@dataclass(frozen=True)`; `WiredApplication` is a `@dataclass`. |
| Protocols/ABCs for interfaces | PASS | `PipelineServiceProtocol`, `WorkbookReaderProtocol`, `ExporterProtocol`, three view Protocols, plus typed adapter protocols inside `excel_exporter.py` and `test_pipeline_worker.py`. |
| Avoid utility classes | PASS | No static-method-only utility classes; helpers are module-level functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| Specific exceptions | PASS | Presenters catch `ValueError` only and route to `view.show_error`. The single broad-catch is in `PipelineWorker.run`, documented as the worker thread's failure boundary. |
| Logging over print | PASS | All production modules use `logging.getLogger(__name__)`. |
| Invariants at construction | PASS | `ImportSpec` is frozen; `PipelineService.__init__` accepts an optional `DbService`. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | PASS | All tests use Pytest. Qt tests use `pytest-qt`. |
| Coverage expectation | PASS | Repo-wide line 100% (>= 85%) and branch 100% (>= 75%). New code 100% line / 100% branch. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Focused unit tests | PASS | One behavior per test. Property tests cover pure-function-like presenter paths. |
| Mocking sparingly | PASS | Fakes implement the Protocol surface; no patching of arbitrary internals. |
| Organization | PASS | Tests mirror code structure. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| Naming conventions | PASS | `test_<unit>_<scenario>` form. |
| Docstrings/comments | PASS | Per-test docstrings; AAA comments. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | PASS | `QT_QPA_PLATFORM=offscreen poetry run pytest` -> 314 pass post-rebase. |
| No Alternative Test Runners | PASS | Only Pytest. |

---

## 5. Test Coverage Detail

Per-module coverage from `evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` remains operative; the GUI module set did not change in the rebase. Every `src/gui/**` module reports 100% line and 100% branch coverage. Repo-wide coverage post-rebase is 100% line / 100% branch (314 pass).

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 314 (full suite post-rebase, caller-reported) | PASS |
| Tests Passed | 314 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Code Coverage | 100% line / 100% branch repo-wide | PASS |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | 0 issues (caller-reported post-rebase) | PASS |
| Ruff Linting | `poetry run ruff check .` | 0 errors (caller-reported post-rebase) | PASS |
| Pyright Type Checking | `poetry run pyright` | 0 errors strict (caller-reported post-rebase) | PASS |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` | 314 pass, 100%/100% (caller-reported post-rebase) | PASS |

**Notes:** The pre-rebase canonical evidence artifacts under `evidence/qa-gates/final-*.2026-05-27T20-59.md` recorded identical verdicts (279 pass; the 314-vs-279 delta is the additional tests added during the rebase preparation, not a behavioral change). The reviewer independently smoke-tested `from src.gui.pipeline_service import PipelineService, ImportSpec` under the rebased base and confirmed clean import.

---

## 8. Gaps and Exceptions

### Identified Gaps

1. **Non-pre-authorized `# noqa: N802` in production code** (PARTIAL, non-blocking — persists from prior audit).
   - **Location:** `src/gui/exporters/excel_exporter.py:69`.
   - **Suppression:** `def ExcelWriter(  # noqa: N802 - mirrors the pandas API member name`.
   - **Status post-rebase:** Unchanged. No new pre-authorized N802 pattern was added to `.claude/rules/python-suppressions.md` by the upstream merges (#15/#18/#20/#23 did not touch the suppressions policy). No explicit user approval is recorded in the rebased history.
   - **Risk:** None to runtime correctness; narrowest possible suppression; factual rationale.
   - **Recommended remediation (non-blocking):** Either obtain explicit user approval for this single-line `N802`, or extend `.claude/rules/python-suppressions.md` to pre-authorize "TYPE_CHECKING Protocol view mirroring a third-party API member" as an `N802` pattern. Documentation-only.

2. **MainWindow control-button signals not wired in the production composition root** (MINOR, non-blocking under spec language — re-stated from prior audit).
   - **Location:** `src/gui/app.py::build_application` (lines 73-137).
   - **Observation:** The composition root constructs `PipelinePresenter` and `ExportPresenter` and the three `SourceSelectionPresenter` instances, but only connects the per-input `file_selected` and `render_tab_requested` signals (lines 109-114). The six `MainWindow` button signals — `import_one_requested`, `import_all_requested`, `run_requested`, `save_requested`, `open_db_requested`, `export_requested` — emit but are never connected to `pipeline_presenter.on_import_one` / `on_import_all` / `on_run` / `on_save` / `on_open_db` / `export_presenter.on_export_requested` in the production code path. Tests drive the presenters directly (verified in `tests/gui/test_pipeline_presenter.py`, `tests/gui/test_export_presenter.py`, and `tests/gui/test_gui_integration.py`), so behavior is verified at the presenter contract level. The integration test does not exercise `MainWindow.run_btn.click()` -> presenter; it calls the presenter directly.
   - **Behavioral impact in production:** Pressing the Run / Save / Open / Export / Import / Import-All buttons in the launched GUI emits the signal but no presenter handler is connected, so the action does not execute. The `PipelineWorker` exists and is independently tested but is not constructed in `build_application`. The synchronous path (`PipelinePresenter.on_run`) is not wired either; both paths are inert in the production composition root.
   - **Policy reference:** The spec (`docs/features/active/2026-05-27-mix-pipeline-gui-19/spec.md`) states the presenters are the authoritative behavior layer and that view-model/controller logic must be testable without a live Qt event loop. It does not explicitly mandate that `MainWindow` button signals be wired in `build_application` (the wiring decision is left to the composition root). However, acceptance criterion #5 ("a Run button executes the mix pipeline") and AC #6/#7/#8 (Save/Open/Export) read as user-visible button-press-triggers-action behaviors. The unit-test coverage of the presenter satisfies the AC at the contract level; the production-wired path is not exercised by any test.
   - **Risk:** A user launching `mix-pipeline-gui` would see the window and the buttons but no button (other than per-input file selection and tab render) would do anything. This is a correctness gap for the user-facing experience but not a policy or test-coverage gap.
   - **Recommended remediation (non-blocking under a strict read of the AC; arguably blocking under a user-visible read):** Add the six signal-to-presenter `connect` calls in `build_application` (or document explicitly that the production composition root is intentionally inert pending a follow-up wiring task). If the team prefers the `PipelineWorker` path in production, wire the QThread + worker into the Run handler. This is implementation work, not documentation.

3. **Property test density on T2 service/registry modules** (NON-BLOCKING NOTE — persists).
   - **Modules:** `src/gui/pipeline_service.py`, `src/gui/exporters/registry.py`, `src/gui/exporters/base.py`.
   - **Observation:** Unchanged from prior review. These T2 modules contain mostly orchestration over impure I/O and registry mutation rather than pure functions; the executor placed property tests on the three T2 presenters where pure-function-like content concentrates. Branch coverage is 100% on every line.
   - **Risk:** Low.
   - **Recommended remediation (non-blocking):** Not required by a strict reading of the rule. If the team wants stricter conformance, add a property test for `ExporterRegistry.register/get/available_formats` round-trips.

4. **PR-context artifacts predate the rebase** (INFO — operational gap, not a policy violation).
   - **Location:** `artifacts/pr_context.summary.txt` and `artifacts/pr_context.appendix.txt`.
   - **Observation:** The persisted PR-context files reflect pre-rebase base `b0e048f…` and head `ad8c84fa…`. The current head is `e68ea3d` and the current base is `7836c24`. The reviewer used `git diff --name-only main...HEAD` against the live refs for diff scope, so the audit is not affected; downstream tooling that consumes the PR-context artifacts to compose a PR body should regenerate them before submission.
   - **Recommended remediation:** Regenerate the PR-context artifacts before merge (via the orchestrator's collect-PR-context tool).

### Approved Exceptions

None on file.

### Removed/Skipped Tests

None.

---

## 9. Summary of Changes

### Commits in This PR/Branch (post-rebase)

1. `e68ea3d` (docs): audit documents for feature
2. `f78b5f4` feat(mix-pipeline-gui): add main window, app entry, and e2e tests
3. `3b5d1a5` feat(mix-pipeline-gui): add presenters, worker, and widget layer
4. `86b763e` feat(mix-pipeline-gui): add initial GUI service and exporter stack

### Files Modified

- 24 new production modules under `src/gui/**`
- 19 new test modules under `tests/gui/**` (plus `conftest.py` and `fakes/**`)
- Evidence artifacts under `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/**`
- Scoping docs (`issue.md`, `spec.md`, `user-story.md`, `plan.2026-05-27T20-59.md`)
- Prior audit artifacts under `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
- `pyproject.toml`, `poetry.lock`, `quality-tiers.yml`, `README.md`
- Two memory artifacts under `.claude/agent-memory/atomic-executor/`

---

## 10. Compliance Verdict

### Overall Status: PARTIALLY COMPLIANT — same non-blocking findings as prior audit, plus a re-stated MINOR on production button-wiring

The change is functionally complete at the presenter contract level under the rebased base, fully tested, and meets every uniform coverage gate. The post-rebase toolchain passes cleanly (caller-reported and reviewer-spot-checked: import-level smoke test and file-size check). The two deviations are:

- The persisting `N802` suppression in `excel_exporter.py:69` (PARTIAL, non-blocking, documentation-only remediation).
- The newly-re-stated MINOR observation that `build_application` does not connect the six `MainWindow` control-button signals to the presenter handlers, so the Run / Save / Open / Export / Import buttons are inert in the production composition root. Behavior is verified at the presenter contract level but no test exercises the wired button-to-presenter path.

Under a strict read of the policy and the spec's contract-level Definition of Done, neither finding is blocking. Under a user-visible read of acceptance criteria 4-8 ("Run button executes the pipeline", "Save button persists", "Open button loads", "Export action exports"), the wiring gap matters and would surprise a user.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure
- PASS Naming, Docs, Comments
- PASS Toolchain Execution
- PASS Summarize & Document (with note on stale `pr_context.*` artifacts)

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

#### Cross-cutting policy rules
- PASS `benchmark-baselines.md` (rule does not fire — no baseline files in diff)
- PASS `ci-workflows.md` (rule does not fire — no workflow files in diff)
- PASS `modified-workflow-needs-green-run` (rule does not fire — no workflow files in diff)
- PASS Evidence Location Compliance

### Metrics Summary

- PASS 314/314 tests passing (100%) post-rebase
- PASS 100% line and 100% branch coverage repo-wide
- PASS 100% line and 100% branch on every `src/gui/**` module
- PASS All files under 500 lines (largest production 389, largest test 424)
- PASS All code quality checks passing
- PASS Every new project classified in `quality-tiers.yml`

### Recommendation

Recommendation: **Remediate** — pursue the button-wiring fix in `src/gui/app.py::build_application` before merge so the acceptance criteria 4-8 hold for a user pressing the buttons in the launched application. The `N802` documentation remediation can ride along (one-time user approval or a one-line policy extension). The PR-context artifacts should be regenerated before opening a PR. None of the findings affect coverage, typing, or correctness of the presenter contract; the wiring fix is a small, mechanical change to `build_application`.

If the team accepts a contract-level reading of the AC and treats the wiring as a follow-up task on a separate issue, the branch is mergeable as is under the same "PARTIALLY COMPLIANT — documentation-only remediation" verdict the prior audit recorded.

---

## Appendix A: Test Inventory

Test modules under `tests/gui/**` (19 files, 94 GUI tests collected; full repo suite 314 post-rebase):

- `tests/gui/conftest.py` — session-scoped `QT_QPA_PLATFORM=offscreen` harness.
- `tests/gui/fakes/fake_views.py` — view-protocol fakes.
- `tests/gui/fakes/fake_services.py` — service-protocol fakes.
- `tests/gui/fakes/fake_exporters.py` — exporter-protocol fake.
- `tests/gui/test_app_composition.py` — composition root tests.
- `tests/gui/test_source_selection_presenter.py` — tab discovery, preview rendering, error routing.
- `tests/gui/test_pipeline_presenter.py` — import/run/save/open paths and error routing.
- `tests/gui/test_export_presenter.py` — registry-driven format resolution, empty-selection rejection.
- `tests/gui/test_exporter_registry.py` — register/get/available_formats.
- `tests/gui/test_excel_exporter.py` — Excel writer per selected table.
- `tests/gui/test_csv_exporter.py` — CSV writer per selected table.
- `tests/gui/test_pipeline_service.py` — import/run/save/open at the service seam.
- `tests/gui/test_workbook_reader.py` — `get_sheet_names`/`read_sheet_preview`.
- `tests/gui/test_db_service.py` — `save_tables`/`open_tables` round-trip.
- `tests/gui/test_source_input_widget.py` — `pytest-qt` widget tests.
- `tests/gui/test_preview_widget.py` — `pytest-qt` preview widget tests.
- `tests/gui/test_export_dialog.py` — `pytest-qt` dialog tests.
- `tests/gui/test_pipeline_worker.py` — QThread + main-thread `finished`/`error` emission.
- `tests/gui/test_gui_integration.py` — end-to-end select -> import -> run -> save -> reopen -> export against fakes (presenter-driven, not button-driven).

| Language | Coverage Artifact | Baseline | Post-change | Disposition |
|---|---|---|---|---|
| Python | `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` | 100% line / 100% branch | 100% line / 100% branch | PASS |

---

## Appendix B: Toolchain Commands Reference

```bash
poetry run black .
poetry run ruff check .
poetry run pyright
QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
```

Branch-diff scope commands used during this re-audit:

```bash
git merge-base main HEAD
git diff --name-only main...HEAD
git diff --name-only main...HEAD | grep -E "^artifacts/(baselines|qa|coverage|evidence)/"
git diff --name-only main...HEAD | grep -E "^(\.github/workflows/|scripts/benchmarks/|\.github/actions/)"
```

Reviewer-side smoke checks (no source modification):

```bash
poetry run python -c "from src.gui.pipeline_service import PipelineService, ImportSpec; print('ok')"
find src/gui tests/gui -name "*.py" -exec wc -l {} +
```

---

**Audit Completed By:** feature-review agent (Claude Opus 4.7 1M)
**Audit Date:** 2026-05-28
**Policy Version:** Current (as of audit date)
