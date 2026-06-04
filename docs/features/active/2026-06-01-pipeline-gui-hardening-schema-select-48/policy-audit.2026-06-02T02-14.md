# Policy Compliance Audit: Pipeline GUI Hardening and Schema Selection — Issue #48 (R4 re-audit, cycle 2)

**Audit Date:** 2026-06-02
**Code Under Test:** Branch `feature/pipeline-gui-hardening-schema-select-48` head `176289e` vs base `main` merge-base `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`. Python only. Changed production files: `src/_load_aop_helpers.py`, `src/build_exe.py`, `src/load_aop.py`, `src/schema_registry.py`, `src/gui/app.py`, `src/gui/pipeline_service.py`, `src/gui/protocols.py`, `src/gui/runners.py`, `src/gui/_main_window_view.py`, `src/gui/_schema_wiring.py`, `src/gui/presenters/import_dispatch.py`, `src/gui/presenters/pipeline_presenter.py`, `src/gui/presenters/source_selection_presenter.py`, `src/gui/widgets/source_input_widget.py`, and new modules `src/gui/_key_mismatch_dialog.py`, `src/gui/_key_mismatch_seam.py`, `src/gui/_run_wiring.py`, `src/gui/_schema_list_wiring.py`, `src/gui/_shutdown_wiring.py`. Cycle-2 production delta (commit `176289e`) is `src/gui/runners.py` and `src/gui/_shutdown_wiring.py` plus the single `app.py` call site.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 19 prod + ~22 test files | 818 tests | ✅ 818 pass, 0 fail | 99% lines, 96.6% branch | 99.48% lines, 96.63% branch | 100% (runners.py, _shutdown_wiring.py) |
| PowerShell | 0 files | N/A | N/A | N/A | N/A | N/A |
| TypeScript | 0 files | N/A | N/A | N/A | N/A | N/A |
| C# | 0 files | N/A | N/A | N/A | N/A | N/A |

**Note:** Python is the only language with changed files on the branch. PowerShell, TypeScript, and C# have zero changed files; their N/A verdicts are therefore admissible per the scope invariant.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope`
- TypeScript post-change coverage artifact: `N/A - out of scope`
- PowerShell baseline coverage artifact: `N/A - out of scope`
- PowerShell post-change coverage artifact: `N/A - out of scope`
- Python baseline coverage artifact: `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/baseline/pytest-baseline.2026-06-02T01-06.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/qa-gates/pytest-final.2026-06-02T01-06.md`
- Per-language comparison summary: Section 1.2.1 below; `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/qa-gates/coverage-delta.2026-06-02T01-06.md`

**Non-negotiable verdict rule:** This audit reports numeric baseline and post-change coverage for the only in-scope language (Python), plus 100% new-code coverage for the cycle-2 modules.

**Fail-closed rule:** All required baseline, QA, and coverage-comparison artifacts are present and were re-verified by an independent toolchain run during this audit.

---

## Executive Summary

This is the cycle-2 re-audit (R4) for issue #48. Cycle 1 (commits `c526e4f`, `a07bce4`) delivered AC-1..AC-15 and R-AC-1..R-AC-6. Cycle 2 (commit `176289e`) addresses Blocking finding F1 from `remediation-inputs.2026-06-02T01-06.md`: the `ThreadedRunner` cross-thread `QObject` lifecycle defect that produced `QBasicTimer::stop: Failed. Possibly trying to stop from a different thread`.

The cycle-2 fix in `src/gui/runners.py` is correct and complete against the required-fix shape (R-AC-7 a-d):
- worker `deleteLater` is wired to `thread.finished` (runners.py:282), destroying the worker on its own thread;
- active dispatches are tracked in a `set[_ActiveDispatch]` collection (runners.py:217, 291-292), replacing the single overwriteable attributes, so a second dispatch cannot drop a still-running prior thread;
- an application-shutdown hook in the new `src/gui/_shutdown_wiring.py` connects `QApplication.aboutToQuit` to a closure that calls `runner.await_active()` (quit + wait), wired at `app.py:432`;
- the queued-connection `_RunnerReceiver` pattern (AC-6) is preserved unchanged (runners.py:265-270, `Qt.ConnectionType.QueuedConnection`); no direct cross-thread outcome delivery was reintroduced.

The toolchain was re-run independently for this audit and passes in a single pass: Black clean (190 files), Ruff clean, Pyright 0 errors/0 warnings, Pytest 818 passed / 0 failed, TOTAL 99% line / 96.6% branch. `src/gui/runners.py` is 100% line / 100% branch; `src/gui/_shutdown_wiring.py` is 100% line / 100% branch (independently re-measured at 26 passed for the runner/shutdown subset).

One coverage exclusion was added: a `# pragma: no cover` on the defensive `except RuntimeError` branch in `await_active` (runners.py:343). It is dispositioned ACCEPTABLE (Section 8). No `# noqa` or `# type: ignore` suppressions were introduced. The diff touches no `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**`, so `modified-workflow-needs-green-run` does not fire. No evidence-location violations were found.

**Policy documents evaluated:**
- ✅ `.claude/rules/general-code-change.md`
- ✅ `.claude/rules/general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `.claude/rules/python.md` + `.claude/rules/python-suppressions.md`
- ✅ `.claude/rules/self-explanatory-code-commenting.md`
- ✅ `.claude/rules/tonality.md`
- N/A `.claude/rules/powershell.md` (no PowerShell changes)
- N/A `.claude/rules/typescript.md` (no TypeScript changes)
- N/A `.claude/rules/csharp.md` (no C# changes)

**Temporary artifacts cleanup:**
- ✅ No temporary/throwaway scripts were created during this review.
- ✅ This review produced audit artifacts only; no source or policy files were modified.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | The cycle-2 lifecycle tests (`tests/gui/test_runners_threaded_lifecycle.py`, `tests/gui/test_shutdown_wiring.py`) each construct a fresh `ThreadedRunner` and drain via `await_active`; no shared module state. Full suite passes (818) under default pytest ordering. |
| **Isolation** - Each test targets single behavior | ✅ PASS | Each lifecycle test targets one R-AC-7 sub-property: deleteLater wiring (a), two-record tracking (b), quit+wait (c), GUI-thread delivery (d). |
| **Fast Execution** - Tests complete quickly | ✅ PASS | Full suite ran in 23.30s during this audit; the runner/shutdown subset (26 tests) ran in 1.56s. |
| **Determinism** - Consistent results | ✅ PASS | Offscreen Qt forced by `tests/gui/conftest.py` (`QT_QPA_PLATFORM=offscreen`); synchronization via `threading.Event` gates and `qtbot.waitSignal`/`waitUntil`, no sleeps. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive `test_...` names, Arrange/Act/Assert comments, module docstring mapping each test to its R-AC-7 sub-property. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | **Baseline (pre-cycle-2):** 99% lines, 96.6% branch (3804 stmts, 678 branches), 811 tests.<br>**Command:** `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`<br>**Timestamp:** 2026-06-02T01-06<br>Artifact: `evidence/baseline/pytest-baseline.2026-06-02T01-06.md`. |
| **No Coverage Regression** | ✅ PASS | **Post-change coverage:** 99.48% lines, 96.63% branch (3830 stmts, 682 branches).<br>**Change:** +0.01% lines, +0.03% branch; +7 tests (811 → 818).<br>**Status:** No regression. Independently re-verified this audit: TOTAL 99% line / 96.6% branch. |
| **New Code Coverage** (uniform tier rule) | ✅ PASS | **New/modified cycle-2 files:** `src/gui/runners.py` 100% line / 100% branch; `src/gui/_shutdown_wiring.py` (new) 100% line / 100% branch. Independently re-measured: `runners.py` 61 stmts 0 missed, 2 branches 0 partial; `_shutdown_wiring.py` 9 stmts 0 missed, 2 branches 0 partial. Both exceed the uniform thresholds (line >= 85%, branch >= 75%) and the new-code expectation. |
| **Comprehensive Coverage** | ✅ PASS | `ThreadedRunner.run` (lifecycle wiring), `await_active`, `active_dispatches`, and `_ActiveDispatch` are each exercised. `_shutdown_wiring.wire_shutdown_cleanup` covers both the `await_active`-present path and the no-op degradation path for a runner lacking it. |
| **Positive Flows** - Valid inputs | ✅ PASS | `test_worker_deletelater_wired_to_thread_finished`, `test_queued_outcome_still_delivers_on_gui_thread` (success path), `test_about_to_quit_calls_await_active`. |
| **Negative Flows** - Invalid inputs | ✅ PASS | `test_queued_outcome_still_delivers_on_gui_thread` (error path via a task raising `ValueError`); `test_wire_shutdown_cleanup_noop_for_runner_without_await_active`. |
| **Edge Cases** - Boundary conditions | ✅ PASS | `test_second_dispatch_does_not_drop_running_prior_thread` (two concurrent dispatches), `test_await_active_drains_repeated_dispatches_without_error` (repeated drain cycles). |
| **Error Handling** - Error paths | ✅ PASS | Error-callback delivery on the GUI thread is asserted; the defensive `except RuntimeError` shutdown-race guard is `# pragma: no cover` (dispositioned in Section 8). |
| **Concurrency** - If applicable | ✅ PASS | This is the core of cycle 2: real `QThread` dispatch, two concurrent records, quit+wait teardown, and GUI-thread queued delivery are all asserted with deterministic gates. |
| **State Transitions** - If applicable | ✅ PASS | The dispatch lifecycle (registered before start → removed on `thread.finished`) and the empty-after-drain end state are asserted (`active_dispatches() == ()`). |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99% lines (96.6% branch) -> Post-change: 99.48% lines (96.63% branch). Change: +0.01% lines (+0.03% branch). New/changed-code coverage: 100% (runners.py and _shutdown_wiring.py line and branch). Disposition: PASS. Evidence: `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/qa-gates/coverage-delta.2026-06-02T01-06.md`, `.../evidence/qa-gates/pytest-final.2026-06-02T01-06.md`, plus this audit's independent re-run.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero PowerShell files changed on the branch).
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero TypeScript files changed on the branch).
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero C# files changed on the branch).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Assertions are specific (`len(active_dispatches()) == 2`, `thread.isRunning() is False`, `success_threads == [gui_thread]`); pytest reports the offending value on failure. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Each lifecycle test is explicitly sectioned with Arrange/Act/Assert comments. |
| **Document Intent** | ✅ PASS | Module docstring maps each test to its R-AC-7 sub-property; per-test docstrings restate the property and method. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No network, DB, or external process. Real `QThread` is in-process and offscreen. No real stdin (KEY-mismatch is injected). |
| **Use Mocks/Stubs** | ✅ PASS | Shutdown tests use a recording fake runner and the real/qtbot `QApplication` seam; lifecycle tests use trivial in-process tasks. |
| **Environment Stability** | ✅ PASS | No temporary files created in tests. Offscreen Qt set in `conftest.py`; gates are `threading.Event`, not wall-clock. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This audit, together with `code-review.2026-06-02T02-14.md` and `feature-audit.2026-06-02T02-14.md`, serves as the required pre-merge review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Cycle-2 objective fixed by `remediation-inputs.2026-06-02T01-06.md` (Finding F1, Blocking) and R-AC-7. |
| **Read existing change plans** | ✅ PASS | `remediation-plan.2026-06-02T01-06.md` drives the cycle; Phase 0 records the policy read. |
| **Document the plan** | ✅ PASS | The plan and per-phase evidence artifacts under `evidence/` document the approach. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | The fix uses standard Qt lifecycle idioms (`thread.finished -> deleteLater`, a tracking set, a quit+wait teardown) without introducing indirection. |
| **Reusability** | ✅ PASS | `_ActiveDispatch` is a small value object; `await_active` and `active_dispatches` are reusable public seams. The shutdown wiring follows the `_run_wiring.py`/`_schema_list_wiring.py` precedent. |
| **Extensibility** | ✅ PASS | `wire_shutdown_cleanup` degrades safely for any runner via `getattr`, so additional runner implementations require no change. |
| **Separation of concerns** | ✅ PASS | Lifecycle logic lives on `ThreadedRunner`; the composition root only routes `aboutToQuit` to it; `app.py` gains a single import and call site. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | `_shutdown_wiring.py` performs Qt signal wiring only; `runners.py` remains the runner abstraction. |
| **Under 500 lines** | ✅ PASS | All touched files <= 500: `src/gui/app.py` 500, `src/gui/runners.py` 416, `src/gui/_shutdown_wiring.py` 72, `tests/gui/test_runners_threaded_lifecycle.py` 213, `tests/gui/test_shutdown_wiring.py` 113. Largest other touched files: `pipeline_presenter.py` 492, `pipeline_service.py` 481, `source_input_widget.py` 472, `test_pipeline_service.py` 471. Measured this audit via `awk 'END{print NR}'` over each changed file. |
| **Public vs internal** | ✅ PASS | Wiring helpers are `_`-prefixed modules; `_RunnerReceiver`/`_ActiveDispatch`/`_discard_record` are internal. `__all__` is declared in both `runners.py` and `_shutdown_wiring.py`. |
| **No circular dependencies** | ✅ PASS | `_shutdown_wiring.py` imports `RunnerProtocol`/`QApplication` under `TYPE_CHECKING` only; no runtime import cycle. Pyright clean. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `_ActiveDispatch`, `await_active`, `active_dispatches`, `wire_shutdown_cleanup`, `_drain_active_threads` are descriptive and snake_case/PascalCase per convention. |
| **Docs/docstrings** | ✅ PASS | Every new class/method/function carries a Google-style docstring with Purpose/Responsibilities/Args/Returns/Side effects; the `ThreadedRunner` docstring documents the lifecycle invariant. |
| **Comment why, not what** | ✅ PASS | Inline comments explain intent (why deleteLater is wired to `thread.finished`, why registration precedes `thread.start()`, why `await_active` iterates a snapshot). No low-value narration. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check .`<br>**Result:** `All done`, 190 files unchanged, EXIT 0 (re-run this audit). |
| **2. Linting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check .`<br>**Result:** `All checks passed!`, EXIT 0 (re-run this audit). |
| **3. Type checking** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright`<br>**Result:** `0 errors, 0 warnings, 0 informations`, EXIT 0 (re-run this audit). |
| **4. Testing** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`<br>**Result:** 818 passed, 0 failed, TOTAL 99% line / 96.6% branch, EXIT 0 (re-run this audit). |
| **Full toolchain loop** | ✅ PASS | All four stages passed in a single pass during this audit; the executor's final-QA artifacts corroborate. |
| **Explicit reporting** | ✅ PASS | Commands and results are documented here (Sections 2.5, 7) and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `176289e` message and `evidence/qa-gates/remediation-summary.2026-06-02T01-06.md` summarize the cycle. |
| **Design choices explained** | ✅ PASS | The plan's Design Direction section and the in-code docstrings explain the collection-based tracking and shutdown hook. |
| **Update supporting documents** | ✅ PASS | `spec.md` adds R-AC-7 (checked); the evidence tree records baselines, QA gates, and coverage delta. |
| **Provide next steps** | ✅ PASS | F2 (`on_schema_discovery` unwired) is recorded as a deferred follow-up in the cycle-2 inputs and summary. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `env -u VIRTUAL_ENV poetry run black --check .` → EXIT 0, 190 files unchanged. |
| **Linting with Ruff** | ✅ PASS | `env -u VIRTUAL_ENV poetry run ruff check .` → `All checks passed!`. |
| **Type checking with Pyright** | ✅ PASS | `env -u VIRTUAL_ENV poetry run pyright` → 0 errors, 0 warnings. |
| **Testing with Pytest** | ✅ PASS | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` → 818 passed, 0 failed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | All new functions/methods fully annotated; `await_active(self, timeout_ms: int = 5000) -> None`, `wire_shutdown_cleanup(app: QApplication, runner: RunnerProtocol) -> None`. No `Any`. Pyright clean. |
| **Dataclasses for value objects** | ✅ PASS | `_ActiveDispatch` is `@dataclass(eq=False)` so records are identity-hashed and can coexist in a `set`. |
| **Protocols/ABCs for interfaces** | ✅ PASS | `RunnerProtocol` (`runtime_checkable`) remains the injection seam; the shutdown hook degrades via `getattr` rather than widening the protocol. |
| **Avoid utility classes** | ✅ PASS | No static-only utility classes added; wiring is module-level functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | The only new catch is `except RuntimeError` in `await_active`, a defined Qt-object-lifetime boundary (deleted C++ QThread during teardown), not a broad `except Exception`. |
| **Logging over print** | ✅ PASS | No `print` added; no ad-hoc logging needed in the lifecycle path. |
| **Invariants at construction** | ✅ PASS | `ThreadedRunner.__init__` initializes the empty active-dispatch set; dispatch records are registered before `thread.start()`. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Pytest with `pytest-qt` (`qtbot`) and offscreen Qt; `hypothesis` available for property tests elsewhere in the suite. |
| **Coverage expectation** | ✅ PASS | Cycle-2 modules at 100% line/branch; repo-wide 99% line / 96.6% branch — above the uniform thresholds. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test across the five lifecycle and two shutdown tests. |
| **Mocking sparingly** | ✅ PASS | Real `QThread` used; only the shutdown caller test uses a recording fake runner. |
| **Organization** | ✅ PASS | `tests/gui/test_runners_threaded_lifecycle.py` and `tests/gui/test_shutdown_wiring.py` mirror `src/gui/runners.py` and `src/gui/_shutdown_wiring.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_...` names tied to R-AC-7 sub-properties. |
| **Docstrings/comments** | ✅ PASS | Module and per-test docstrings; AAA comments throughout. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` → 818 passed. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### src/gui/runners.py — ThreadedRunner lifecycle (5 lifecycle tests + existing runner tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_worker_deletelater_wired_to_thread_finished | Positive | run wiring, thread.finished→deleteLater | ✅ |
| test_second_dispatch_does_not_drop_running_prior_thread | Edge Case | collection tracking of 2 records | ✅ |
| test_await_active_quits_and_waits_then_no_running_thread | Error Handling / teardown | await_active quit+wait | ✅ |
| test_queued_outcome_still_delivers_on_gui_thread | Positive + Negative | queued success/error delivery (AC-6) | ✅ |
| test_await_active_drains_repeated_dispatches_without_error | Edge Case | repeated drain cycles | ✅ |

**Coverage:** 100% line / 100% branch for `src/gui/runners.py` (independently re-measured; the `# pragma: no cover` shutdown-race branch is excluded).

**Not covered:** The defensive `except RuntimeError` branch in `await_active` (runners.py:343) — excluded by `# pragma: no cover`; see Section 8.

### src/gui/_shutdown_wiring.py — wire_shutdown_cleanup (2 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_about_to_quit_calls_await_active | Positive | aboutToQuit → await_active | ✅ |
| test_wire_shutdown_cleanup_noop_for_runner_without_await_active | Negative / degradation | getattr no-op path | ✅ |

**Coverage:** 100% line / 100% branch (9 stmts, 2 branches).

**Not covered:** None.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 818 | ✅ |
| Tests Passed | 818 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | 23.30s total (full suite, this audit) | ✅ Fast |
| Runner/shutdown subset | 26 passed in 1.56s | ✅ Fast |
| Code Coverage | 99% line, 96.6% branch (TOTAL) | ✅ |
| Cycle-2 module coverage | runners.py 100%/100%; _shutdown_wiring.py 100%/100% | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | All done, 190 files unchanged, EXIT 0 | ✅ |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed! | ✅ |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors, 0 warnings, 0 informations | ✅ |
| Pytest Tests | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` | 818 passed, 0 failed | ✅ |

**Notes:** All four stages were re-run independently for this audit and corroborate the executor's `evidence/qa-gates/` artifacts. One non-error pytest warning observed (unrelated to the change).

---

## 8. Gaps and Exceptions

### Identified Gaps

**None.** All policy requirements relevant to the cycle-2 scope and the full feature-vs-base diff are met.

### Approved Exceptions

**`# pragma: no cover` on the `await_active` shutdown-race guard (runners.py:343) — ACCEPTABLE, narrowly scoped.**

- **What:** A single `except RuntimeError: # pragma: no cover - defensive Qt-lifetime guard` branch in `ThreadedRunner.await_active`. The branch discards the record and continues when the C++ `QThread` was already deleted (its `deleteLater` ran while `await_active` was spinning the event loop waiting on another thread in the snapshot).
- **Why excluded:** Forcing this branch deterministically requires deleting a live C++ `QThread` (e.g. `shiboken6.delete`), which aborts the interpreter and cannot be asserted in-process. The branch is a real production-robustness guard against a genuine `deleteLater`/`await_active` race during shutdown.
- **Scope:** Single branch, single line of exclusion, with a full inline rationale comment. It guards a defined Qt object-lifetime boundary, not business logic, and masks no untested behavior path that could be reached by ordinary inputs. The surrounding `try` body (quit + wait) is covered.
- **Disposition:** ACCEPTABLE. This exclusion does not lower the verdict. It is consistent with `general-code-change.md` (explicit, bounded error handling) and does not violate `python-suppressions.md` (a coverage pragma is not a `# noqa`/`# type: ignore` and is therefore outside that policy; no lint/type suppression was introduced).

### Removed/Skipped Tests

**None.** No tests were removed or skipped. The cycle added 7 tests (811 → 818).

---

## 9. Summary of Changes

### Commits in This Branch (vs base `main` merge-base `1df3301`)

1. **c526e4f** - feat(gui): harden pipeline GUI interaction, errors, and AOP validation (#48) — cycle 1, AC-1..AC-15.
2. **a07bce4** - fix(schema): surface bundled default schemas in selection, matching, and load (#48) — cycle 1, R-AC-1..R-AC-6.
3. **176289e** - fix(gui): correct ThreadedRunner QThread/worker lifecycle (#48 cycle 2) — cycle 2, R-AC-7 (this re-audit's primary delta).

### Files Modified (cycle-2 production delta)

1. **src/gui/runners.py** (MODIFIED) — collection-based dispatch tracking (`_ActiveDispatch`, `_active` set), `thread.finished → worker.deleteLater`/`thread.deleteLater`, `await_active`, `active_dispatches`. Queued `_RunnerReceiver` wiring unchanged (AC-6).
2. **src/gui/_shutdown_wiring.py** (NEW) — `wire_shutdown_cleanup` connecting `aboutToQuit` to `runner.await_active()`, degrading via `getattr`.
3. **src/gui/app.py** (MODIFIED) — one import and one call site (`wire_shutdown_cleanup(application, runner_resolved)` at line 432); remains at the 500-line cap.

Tests added: `tests/gui/test_runners_threaded_lifecycle.py` (213 lines), `tests/gui/test_shutdown_wiring.py` (113 lines); `tests/gui/test_runners_threaded.py` updated to join via the public `await_active` seam.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The cycle-2 fix resolves Blocking finding F1 (the cross-thread `QObject` lifecycle defect) completely and correctly. R-AC-7 (a-d) is fully implemented and tested. The full feature-vs-base diff passes the Python toolchain in a single pass, coverage exceeds the uniform thresholds with no regression, all touched files are within the 500-line cap, no unauthorized suppressions were introduced, the single coverage pragma is acceptable and narrowly scoped, and no workflow/benchmark or evidence-location rules are triggered.

**Fail-closed reminder:** All required baseline, QA, and coverage-comparison artifacts are present and were independently re-verified.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes: requirements and plan present.
- ✅ Design Principles: simple, cohesive, extensible, separated.
- ✅ Module & File Structure: all touched files <= 500; no cycles.
- ✅ Naming, Docs, Comments: complete docstrings, intent comments.
- ✅ Toolchain Execution: single-pass clean, re-verified.
- ✅ Summarize & Document: spec/evidence updated.

#### Language-Specific Code Change Policy (Section 3)
**For Python:**
- ✅ Tooling & Baseline: Black/Ruff/Pyright/Pytest clean.
- ✅ Python Design & Typing: fully typed, dataclass/protocol use correct.
- ✅ Error Handling: specific exception boundary; no broad catch.

#### General Unit Test Policy (Section 1)
- ✅ Core Principles: independent, isolated, fast, deterministic, readable.
- ✅ Coverage & Scenarios: 100% on cycle-2 modules; scenarios complete.
- ✅ Test Structure: AAA, clear diagnostics.
- ✅ External Dependencies: none; no temp files.
- ✅ Policy Audit: this document.

#### Language-Specific Unit Test Policy (Section 4)
**For Python:**
- ✅ Framework & Scope: Pytest + pytest-qt.
- ✅ Test Style & Structure: focused, real `QThread`.
- ✅ Naming & Readability: descriptive, documented.
- ✅ Toolchain: Pytest only.

---

### Metrics Summary

- ✅ 818/818 tests passing (100%)
- ✅ 99% repo-wide line coverage, 96.6% branch
- ✅ runners.py and _shutdown_wiring.py at 100% line/branch
- ✅ All touched files <= 500 lines (app.py at 500)
- ✅ All four Python quality stages passing in a single pass
- ✅ Full-suite execution time 23.30s

---

### Recommendation

**Ready for merge.**

The cycle-2 remediation is complete and verified. No Blocking or material findings remain. The single deferred item (F2: `SourceSelectionPresenter.on_schema_discovery` has no production caller) is out of scope for this cycle, does not affect the crash fix, and is recorded as a recommended follow-up; it does not block merge of this cycle.

---

## Rejected Scope Narrowing

None. The caller prompt explicitly directed a full feature-vs-base audit with no scope narrowing and asked that specific points be confirmed (not that scope be limited). No attempt to narrow scope, mark a changed-file language as out of scope, or skip a toolchain check was present. The full branch diff against `main` (merge-base `1df3301`) was audited.

## Evidence Location Compliance

No violations. A git-diff scan for files written under `artifacts/baselines/`, `artifacts/baseline/`, `artifacts/qa/`, `artifacts/qa-gates/`, `artifacts/evidence/`, or `artifacts/coverage/` returned none (`NO_NONCANONICAL_EVIDENCE_PATHS`). All cycle evidence is under the canonical `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/<kind>/` scheme. The repository's `scripts/validate_evidence_locations.py` is absent (per agent memory `evidence-validator-script-absent`), so the equivalent git-diff scan was used.

---

## Appendix A: Test Inventory

Cycle-2 tests (the re-audit delta):

- tests/gui/test_runners_threaded_lifecycle.py::test_worker_deletelater_wired_to_thread_finished
- tests/gui/test_runners_threaded_lifecycle.py::test_second_dispatch_does_not_drop_running_prior_thread
- tests/gui/test_runners_threaded_lifecycle.py::test_await_active_quits_and_waits_then_no_running_thread
- tests/gui/test_runners_threaded_lifecycle.py::test_queued_outcome_still_delivers_on_gui_thread
- tests/gui/test_runners_threaded_lifecycle.py::test_await_active_drains_repeated_dispatches_without_error
- tests/gui/test_shutdown_wiring.py::test_about_to_quit_calls_await_active
- tests/gui/test_shutdown_wiring.py::test_wire_shutdown_cleanup_noop_for_runner_without_await_active

Full suite: 818 tests passing (cycle 1 AC-1..AC-15 and R-AC-1..R-AC-6 tests remain green).

---

## Appendix B: Toolchain Commands Reference

```bash
# Formatting
env -u VIRTUAL_ENV poetry run black --check .

# Linting
env -u VIRTUAL_ENV poetry run ruff check .

# Type checking
env -u VIRTUAL_ENV poetry run pyright

# Testing (full suite with coverage)
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing

# Targeted cycle-2 module coverage
env -u VIRTUAL_ENV poetry run pytest tests/ -k "runner or shutdown" \
  --cov=src.gui.runners --cov=src.gui._shutdown_wiring --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-02
**Policy Version:** Current (as of audit date)
