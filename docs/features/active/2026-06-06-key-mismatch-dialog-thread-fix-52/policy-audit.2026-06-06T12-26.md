# Policy Compliance Audit: key-mismatch-dialog-thread-fix (#52)

**Audit Date:** 2026-06-06
**Code Under Test:** `src/_normalize_le_columns.py` (new), `src/etl_key.py`, `src/normalize_le.py`, `src/load_aop.py`, `src/gui/_key_mismatch_bridge.py` (new), `src/gui/_key_mismatch_dialog.py`, `src/gui/_key_mismatch_seam.py`, `src/gui/pipeline_service.py`, `src/gui/app.py`; tests: `tests/test_etl_key.py`, `tests/gui/test_key_mismatch_bridge.py` (new), `tests/gui/test_key_mismatch_dialog.py`, `tests/gui/test_pipeline_service_key_seam.py`, `tests/gui/integration/test_behavioral_composition.py`

- Branch: `fix/key-mismatch-dialog-thread-fix-52` (HEAD `1e49546`)
- Base: `main` (merge-base `5e659f2`)
- Work Mode: full-bug

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 9 src + 5 test files | 834 tests | ✅ 834 pass, 0 fail | 99.48% lines, 96.63% branch | 99.49% lines, 96.70% branch | 100% (app.py 99%) |

**Note:** PowerShell, TypeScript, and C# have zero changed files and are out of scope.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope`
- TypeScript post-change coverage artifact: `N/A - out of scope`
- PowerShell baseline coverage artifact: `N/A - out of scope`
- PowerShell post-change coverage artifact: `N/A - out of scope`
- Per-language comparison summary: section 1.2.1 below; `artifacts/python/lcov.info` (reviewer-regenerated)

**Non-negotiable verdict rule satisfied:** numeric baseline and post-change Python
coverage metrics plus new/changed-code coverage are reported.

**Fail-closed rule:** all required baseline, QA, and coverage-comparison artifacts are
present under the canonical evidence tree.

---

## Executive Summary

The branch fixes the cross-thread Qt crash in the KEY-mismatch dialog and adds example
pairs, per spec v1.0 (full-bug). Nine production source files and five test files
changed; no PowerShell/TypeScript/C# files and no workflow files changed. The reviewer
ran the full Python toolchain against the branch head: Black, Ruff, and Pyright are
clean, and the full pytest suite reports 834 passed. Changed-module coverage is 100%
(app.py 99%, the single uncovered line is a pre-existing QApplication fallback). All
changed/added source files are within the 500-line cap. No unauthorized suppressions,
no temp files in tests, no banned timing APIs. The cross-thread bridge does not swallow
exceptions.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A `powershell.md` (zero changed files)
- N/A `typescript.md` (zero changed files)
- N/A `csharp.md` (zero changed files)

Also evaluated: `self-explanatory-code-commenting.md` (PASS), `tonality.md` (PASS).

The audit scope is the full branch diff vs main. No scope narrowing was attempted by
the caller (see Rejected Scope Narrowing). The verdict is PASS with zero FAIL and zero
blocking-PARTIAL findings.

**Temporary artifacts cleanup:**
- ✅ No temporary/one-time scripts were created by this change.
- ✅ No ongoing tooling scripts added.
- The new modules `_normalize_le_columns.py` and `_key_mismatch_bridge.py` are
  permanent, fully tested production modules, not throwaway scripts.

### Rejected Scope Narrowing

None. The caller prompt enumerated files and review obligations but did not narrow scope
to a plan/task/phase, a file subset, or mark any language out of scope. The audit
proceeded against the full branch diff vs main.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** | ✅ PASS | New tests use `monkeypatch` and function-scoped fixtures; no shared mutable module state persists across tests (the `_FakeMessageBox` class attributes are reset in each test's Arrange). |
| **Isolation** | ✅ PASS | Each test targets one behavior (e.g. truncation, order, default-button, cross-thread marshaling); test files mirror module structure. |
| **Fast Execution** | ✅ PASS | Full suite 834 tests in ~21s; the bridge tests pump the event loop with `qtbot.waitUntil` rather than sleeping. |
| **Determinism** | ✅ PASS | No randomness or wall-clock dependence; cross-thread tests use `threading.Event` + `qtbot.waitUntil` with a fixed timeout, not `time.sleep`. |
| **Readability & Maintainability** | ✅ PASS | Descriptive `test_...` names; AAA structure with Arrange/Act/Assert comments throughout. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Baseline 99.48% lines / 96.63% branch (818 tests), `evidence/baseline/baseline-pytest-coverage.md`, P0-T6. |
| **No Coverage Regression** | ✅ PASS | Post-change 99.49% lines / 96.70% branch (+0.01 / +0.07 pts). No regression on changed lines (all changed modules 100% except pre-existing app.py:297). |
| **New Code Coverage** | ✅ PASS | New files `_normalize_le_columns.py` and `_key_mismatch_bridge.py` at 100% line and 100% branch; all changed modules 100% (app.py 99%). |
| **Comprehensive Coverage** | ✅ PASS | `_collect_diverging_examples`, resolver-aware `resolve_key` branch, `resolve_le_columns`, loader pass-throughs, example-aware seam/dialog, and the bridge are all exercised. |
| **Positive Flows** | ✅ PASS | trust/overwrite mapping, example rendering, same-thread direct call, cross-thread marshaling success. |
| **Negative Flows** | ✅ PASS | resolver-not-invoked on match/no-KEY-column; bridge exception surfaced not swallowed. |
| **Edge Cases** | ✅ PASS | empty-examples body omission; truncation at limit 3; identical-lists empty result. |
| **Error Handling** | ✅ PASS | `test_cross_thread_exception_is_surfaced_on_worker` asserts re-raise; `test_no_stdin_prompt_raises`. |
| **Concurrency** | ✅ PASS | Cross-thread bridge tests run `resolve` on a worker thread and assert GUI-thread delivery and worker unblock. |
| **State Transitions** | N/A | No stateful state-machine introduced. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.48% lines (96.63% branch) -> Post-change: 99.49% lines (96.70% branch). Change: +0.01% lines (+0.07% branch). New/changed-code coverage: 100% line and 100% branch on every changed module except `app.py` (99% line / 90% branch; the one uncovered line 297 is a pre-existing fallback, not a changed line). Disposition: PASS. Evidence: reviewer scoped full-suite run 2026-06-06T12-26 (`artifacts/python/lcov.info`); `evidence/qa-gates/final-pytest-coverage.md`, `evidence/qa-gates/coverage-delta.md`.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Behavioral equality assertions on recorded calls/results; the `no_stdin_prompt` seam raises a descriptive `RuntimeError`. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Every new test has explicit Arrange/Act/Assert comment blocks. |
| **Document Intent** | ✅ PASS | Each test carries a docstring describing scenario and expected outcome; AC references cited. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No network/DB/filesystem; loaders are monkeypatched to return in-memory frames; Qt runs headless (`QT_QPA_PLATFORM=offscreen`). |
| **Use Mocks/Stubs** | ✅ PASS | `ask` stand-ins, `_FakeMessageBox`, recording resolvers/loaders; mocking is scoped to the seam under test. |
| **Environment Stability** | ✅ PASS | No temp files created (diff scan confirms; `.xlsx` literals are mock arguments, never written). No mutable global config. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This audit plus the companion code-review and feature-audit constitute the required review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Issue #52 + spec.md v1.0 (Final) define the objective and root cause. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-06T11-34.md` present and followed. |
| **Document the plan** | ✅ PASS | Plan and per-batch QA-gate evidence under `evidence/qa-gates/`. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | Smallest seam: optional `resolver` parameter defaulting to `None` preserves the CLI path; bridge is a single small QObject. |
| **Reusability** | ✅ PASS | `resolve_le_columns` extracted as a pure reusable helper; bridge mirrors the existing queued-connection pattern in `runners.py`. |
| **Extensibility** | ✅ PASS | Resolver contract is a keyword-style optional callable, extensible without breaking existing callers. |
| **Separation of concerns** | ✅ PASS | Pure example collection (`etl_key`), column resolution (`_normalize_le_columns`), GUI marshaling (`_key_mismatch_bridge`), and dialog rendering (`_key_mismatch_dialog`) are separate. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | Each new module has one clear purpose with a module docstring. |
| **Under 500 lines** | ✅ PASS | _normalize_le_columns 166, etl_key 313, normalize_le 450, load_aop 396, _key_mismatch_bridge 187, _key_mismatch_dialog 159, _key_mismatch_seam 85, pipeline_service 493, app 500 (at cap). |
| **Public vs internal** | ✅ PASS | Internal helpers `_`-prefixed; `__all__` lists explicit public surfaces. |
| **No circular dependencies** | ✅ PASS | `_normalize_le_columns` imports only `etl_columns`; `normalize_le` imports from it (one direction); bridge imports only PySide6 and a TYPE_CHECKING-only MainWindow. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `_collect_diverging_examples`, `resolve_le_columns`, `KeyMismatchBridge`, `_format_examples`. |
| **Docs/docstrings** | ✅ PASS | Every new class/function has a Google-style docstring; `KeyMismatchBridge` documents thread-affinity and exception-surfacing invariants. |
| **Comment why, not what** | ✅ PASS | Loop/branch intent comments present (e.g. same-thread guard rationale, divergence-branch decision logic). |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black --check src tests` -> 191 files unchanged. |
| **2. Linting** | ✅ PASS | `poetry run ruff check src tests` -> All checks passed. |
| **3. Type checking** | ✅ PASS | `poetry run pyright <9 changed files>` -> 0 errors, 0 warnings, 0 informations. |
| **4. Testing** | ✅ PASS | `poetry run pytest` -> 834 passed. |
| **Full toolchain loop** | ✅ PASS | All four stages clean in a single reviewer pass. |
| **Explicit reporting** | ✅ PASS | Commands and results recorded here and in `evidence/qa-gates/final-*`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `1e49546` message and spec.md design summary. |
| **Design choices explained** | ✅ PASS | spec.md Proposed Fix; bridge docstrings. |
| **Update supporting documents** | ✅ PASS | spec.md/issue.md AC checked off; evidence tree populated. |
| **Provide next steps** | ✅ PASS | Ready for PR to main with green CI per spec Rollout. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check src tests` -> 191 unchanged. |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check src tests` -> All checks passed. |
| **Type checking with Pyright** | ✅ PASS | 0 errors on the 9 changed files. |
| **Testing with Pytest** | ✅ PASS | 834 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | Full type hints; resolver typed `Callable[[list[tuple[str, str]]], str] | None`; no `Any` introduced. |
| **Dataclasses for value objects** | N/A | No new value objects; example pairs are plain tuples. |
| **Protocols/ABCs for interfaces** | ✅ PASS | Resolver seam is a typed callable (the established pattern); no new interface needed. |
| **Avoid utility classes** | ✅ PASS | `KeyMismatchBridge` is a stateful QObject with behavior, not a static-method bag; helpers are module functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | The bridge slot's `except Exception` is a deliberate capture-and-re-raise boundary that preserves and propagates the original exception on the worker side; `zip(strict=True)` fails fast on length mismatch. |
| **Logging over print** | ✅ PASS | trust/overwrite and extra-column warnings via `logging`; no `print`. |
| **Invariants at construction** | ✅ PASS | Bridge captures GUI thread and wires the queued connection in `__init__`. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Pytest with `pytest-qt` (`qtbot`) and `monkeypatch`. |
| **Coverage expectation** | ✅ PASS | New code 100% (app.py 99%); repo-wide line 99.49% / branch 96.70%, above floors. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | Real pure code (`_collect_diverging_examples`, `resolve_key`) exercised directly; only the dialog and loaders are stubbed. |
| **Organization** | ✅ PASS | `tests/test_etl_key.py`, `tests/gui/test_key_mismatch_*` mirror module locations. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_...` names encode the scenario. |
| **Docstrings/comments** | ✅ PASS | Each test has a scenario docstring. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest` -> 834 passed. |
| **No Alternative Test Runners** | ✅ PASS | Only Pytest is used. |

---

## 5. Test Coverage Detail

### _collect_diverging_examples (3 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_collect_diverging_examples_returns_only_diverging_pairs_in_order | Positive | etl_key.py 152-159 | ✅ |
| test_collect_diverging_examples_truncates_to_limit_of_three | Edge Case | etl_key.py 155-158 | ✅ |
| test_collect_diverging_examples_empty_when_identical | Negative | etl_key.py 152-159 | ✅ |

**Coverage:** 100% of `_collect_diverging_examples`.

### resolve_key (resolver path) (6 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_resolve_key_invokes_resolver_only_on_divergence_with_examples | Positive | etl_key.py 289-296 | ✅ |
| test_resolve_key_resolver_trust_keeps_existing | Positive | etl_key.py 296-303 | ✅ |
| test_resolve_key_resolver_overwrite_replaces | Positive | etl_key.py 296-303 | ✅ |
| test_resolve_key_resolver_not_invoked_when_matching | Negative | etl_key.py (match branch) | ✅ |
| test_resolve_key_resolver_not_invoked_when_no_key_column | Negative | etl_key.py (no-key branch) | ✅ |
| test_resolve_key_resolver_none_preserves_cli_path | Edge Case | etl_key.py 297 (CLI fallback) | ✅ |

**Coverage:** 100% line and branch of `etl_key.py`.

### KeyMismatchBridge (3 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_same_thread_guard_calls_ask_directly_without_event | Positive | bridge 138-141 | ✅ |
| test_cross_thread_path_marshals_to_gui_thread | Concurrency | bridge 143-176, 178-204 | ✅ |
| test_cross_thread_exception_is_surfaced_on_worker | Error Handling | bridge 173-176, 195-204 | ✅ |

**Coverage:** 100% line and branch of `_key_mismatch_bridge.py`.

**Not covered:** `app.py:297` (pre-existing QApplication-singleton fallback, not a changed line).

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 834 | ✅ |
| Tests Passed | 834 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | ~21s total | ✅ Fast |
| Average Time per Test | ~25ms | ✅ Fast |
| Discovery Time | sub-second | ✅ |
| Functions/Classes Tested | all changed | ✅ |
| Test File Size | all <= 500 lines | ✅ Maintainable |
| Code Coverage | 99.49% lines, 96.70% branches (repo); 100% changed (app.py 99%) | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check src tests` | 191 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check src tests` | All checks passed | ✅ |
| Pyright Type Checking | `poetry run pyright <changed files>` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `poetry run pytest` | 834 passed | ✅ |

**Notes:**
One pre-existing pandas `FutureWarning` in `src/mix_lookups.py:173` is unrelated to this
change. No workflow files changed, so `modified-workflow-needs-green-run` does not apply.

### Suppression Compliance (python-suppressions.md)

Diff scan for `noqa`, `type: ignore`, `pyright: ignore` in `src/**` and `tests/**`:
zero occurrences. The test access to the private `_collect_diverging_examples` uses
`vars(etl_key)[...]` + `typing.cast` specifically to avoid any suppression. PASS.

### Evidence Location Compliance

`git diff --name-only main...HEAD -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'` -> empty.
All executor evidence is under the canonical
`docs/features/active/<feature>/evidence/<kind>/` tree (baseline, qa-gates).
`scripts/validate_evidence_locations.py` does not exist in this repo; the git-diff scan
was used in its place (the PowerShell PreToolUse hook is the live enforcement). No
violations. PASS.

---

## 8. Gaps and Exceptions

### Identified Gaps

**None.** All policy requirements are met. One non-blocking robustness note: the bridge
reuses instance-level `_result`/`_error`; within one import run the resolver calls are
sequential (safe), and a race would require two overlapping import runs both hitting a
divergence (see code-review MINOR-1).

### Approved Exceptions

**None.** No exceptions needed.

### Removed/Skipped Tests

**None.** Pre-existing WS1a resolver tests were reworked (not removed) to the
example-aware contract; equivalent or stronger assertions were retained.

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. **1e49546** - fix(gui): resolve KEY-mismatch dialog cross-thread crash and add examples (#52)

### Files Modified

1. **src/_normalize_le_columns.py** (NEW) - extracted LE column-schema constants and `resolve_le_columns` so normalize_le stays under 500 lines.
2. **src/etl_key.py** (MODIFIED) - added `_collect_diverging_examples` and the optional `resolver` parameter to `resolve_key`.
3. **src/normalize_le.py** (MODIFIED) - imports/re-exports the extracted helpers; threads `resolver` through `load_source`.
4. **src/load_aop.py** (MODIFIED) - threads `resolver` through `load_aop`.
5. **src/gui/_key_mismatch_bridge.py** (NEW) - cross-thread bridge marshaling the dialog onto the GUI thread.
6. **src/gui/_key_mismatch_dialog.py** (MODIFIED) - example-aware resolver/ask; renders pairs; dispatches via the bridge.
7. **src/gui/_key_mismatch_seam.py** (MODIFIED) - default resolver accepts and ignores examples.
8. **src/gui/pipeline_service.py** (MODIFIED) - forwards the resolver callable (no eager call).
9. **src/gui/app.py** (MODIFIED) - builds window before the service so the bridge is GUI-thread parented.
10. **5 test files** (NEW/MODIFIED) - bridge tests (new) plus reworked etl_key/dialog/service/integration tests.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The change is policy-compliant across general code-change, general unit-test, Python
code-change, and Python unit-test policies, with clean toolchain runs and no coverage
regression. Zero FAIL findings and zero blocking-PARTIAL findings.

**Fail-closed reminder:** all required baseline, QA, and coverage-comparison artifacts
are present; the PASS verdict is supported by reviewer-run evidence.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes
- ✅ Design Principles
- ✅ Module & File Structure
- ✅ Naming, Docs, Comments
- ✅ Toolchain Execution
- ✅ Summarize & Document

#### Language-Specific Code Change Policy (Section 3)

**For Python:**
- ✅ Tooling & Baseline
- ✅ Python Design & Typing
- ✅ Error Handling

#### General Unit Test Policy (Section 1)
- ✅ Core Principles
- ✅ Coverage & Scenarios
- ✅ Test Structure
- ✅ External Dependencies
- ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4)

**For Python:**
- ✅ Framework & Scope
- ✅ Test Style & Structure
- ✅ Naming & Readability
- ✅ Toolchain

---

### Metrics Summary

- ✅ 834/834 tests passing (100%)
- ✅ All changed modules tested (100% coverage; app.py 99%)
- ✅ 99.49% repo line coverage / 96.70% branch coverage
- ✅ All changed/added source files <= 500 lines
- ✅ All code quality checks passing
- ✅ Test execution time ~21s (fast)

---

### Recommendation

**Ready for merge.**

The branch satisfies all evaluated policies and all eight acceptance criteria (see the
companion feature-audit). Optional non-blocking follow-up: document or guard the bridge's
single-flight assumption for overlapping concurrent imports (code-review MINOR-1).

---

## Appendix A: Test Inventory

- tests/test_etl_key.py::test_collect_diverging_examples_returns_only_diverging_pairs_in_order
- tests/test_etl_key.py::test_collect_diverging_examples_truncates_to_limit_of_three
- tests/test_etl_key.py::test_collect_diverging_examples_empty_when_identical
- tests/test_etl_key.py::test_resolve_key_invokes_resolver_only_on_divergence_with_examples
- tests/test_etl_key.py::test_resolve_key_resolver_trust_keeps_existing
- tests/test_etl_key.py::test_resolve_key_resolver_overwrite_replaces
- tests/test_etl_key.py::test_resolve_key_resolver_not_invoked_when_matching
- tests/test_etl_key.py::test_resolve_key_resolver_not_invoked_when_no_key_column
- tests/test_etl_key.py::test_resolve_key_resolver_none_preserves_cli_path
- tests/gui/test_key_mismatch_bridge.py::test_same_thread_guard_calls_ask_directly_without_event
- tests/gui/test_key_mismatch_bridge.py::test_cross_thread_path_marshals_to_gui_thread[True/False]
- tests/gui/test_key_mismatch_bridge.py::test_cross_thread_exception_is_surfaced_on_worker
- tests/gui/test_key_mismatch_dialog.py::test_resolver_maps_keep_existing_to_trust
- tests/gui/test_key_mismatch_dialog.py::test_resolver_maps_rebuild_to_overwrite
- tests/gui/test_key_mismatch_dialog.py::test_resolver_forwards_examples_to_ask
- tests/gui/test_key_mismatch_dialog.py::test_qmessagebox_renders_example_pairs
- tests/gui/test_key_mismatch_dialog.py::test_qmessagebox_body_omits_examples_block_when_none
- tests/gui/test_key_mismatch_dialog.py::test_qmessagebox_default_button_is_keep_existing
- tests/gui/test_key_mismatch_dialog.py::test_qmessagebox_resolver_default_maps_to_trust
- tests/gui/test_key_mismatch_dialog.py::test_build_application_injects_resolver_callable
- tests/gui/test_pipeline_service_key_seam.py::test_default_resolver_forwarded_as_callable_and_never_reaches_stdin
- tests/gui/test_pipeline_service_key_seam.py::test_import_le_forwards_injected_resolver_callable
- tests/gui/test_pipeline_service_key_seam.py::test_import_aop_forwards_injected_resolver_callable
- tests/gui/test_pipeline_service_key_seam.py::test_resolver_module_import_location_is_patchable
- tests/gui/test_pipeline_service_key_seam.py::test_default_key_mismatch_resolver_returns_trust
- tests/gui/integration/test_behavioral_composition.py::test_composed_import_path_never_reaches_stdin

## Appendix B: Toolchain Commands Reference

```bash
poetry run black --check src tests
poetry run ruff check src tests
poetry run pyright <changed files>
poetry run pytest
poetry run pytest --cov=src.etl_key --cov=src._normalize_le_columns --cov=src.normalize_le --cov=src.load_aop --cov=src.gui._key_mismatch_bridge --cov=src.gui._key_mismatch_dialog --cov=src.gui._key_mismatch_seam --cov=src.gui.pipeline_service --cov=src.gui.app --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-06
**Policy Version:** Current (as of audit date)
