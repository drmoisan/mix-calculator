# Policy Compliance Audit: edit-schema-columns-assignment (Issue #62)

**Audit Date:** 2026-06-09
**Code Under Test:**
- `src/gui/presenters/_columns_tab_presenter.py` (MODIFIED, Python)
- `tests/gui/test_columns_tab_presenter.py` (MODIFIED, Python)
- `tests/gui/test_schema_builder_presenter_core.py` (MODIFIED, Python)
- Feature-folder docs/evidence (issue.md, plan, evidence/**) — non-code

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 3 files | 1027 repo / 28 targeted | ✅ 1027 pass, 0 fail | 98.27% lines, 93.83% branch | 98.27% lines, 93.87% branch | 100% changed-line |

**Note:** Python is the only language with changed files in the branch diff. No TypeScript, PowerShell, C#, Bash, or JSON files changed; those rows are omitted as out of scope (zero changed files).

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (zero TypeScript files changed)
- TypeScript post-change coverage artifact: `N/A - out of scope` (zero TypeScript files changed)
- PowerShell baseline coverage artifact: `N/A - out of scope` (zero PowerShell files changed)
- PowerShell post-change coverage artifact: `N/A - out of scope` (zero PowerShell files changed)
- Python post-change coverage artifact: `artifacts/python/lcov.info` (present; inspected, not regenerated)
- Per-language comparison summary: see section 1.2.1; supporting evidence `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/qa-gates/coverage-comparison.md`

---

## Executive Summary

This is a `minor-audit` bug fix for issue #62. The Columns tab of the schema builder rendered every canonical column as unassigned when a schema was opened for editing via `SchemaBuilderPresenter.load_existing`, because the edit-from-button path supplies no live `preview_slice` and the existing fuzzy-match pass had nothing to match against. The fix adds a second pass `_seed_from_persisted_aliases()` to `ColumnsTabPresenter.prepopulate()` that seeds any still-unassigned row from its first persisted alias, while preserving the live-match-wins ordering and the one-source-per-row invariant.

Scope is Python only. The full Python toolchain was run check-only against the changed files: Black (clean), Ruff (clean), Pyright (0 errors), and Pytest (28 targeted tests pass; executor full-suite evidence reports 1027 passing). Coverage was verified by inspecting the pre-existing `artifacts/python/lcov.info` rather than regenerating it. The modified production file shows 96.5% line / 85.3% branch coverage (whole-file, lcov), with 100% coverage on the changed lines; the three uncovered lines (263, 285, 286) are in pre-existing helpers untouched by this change. Repo-wide coverage is 98.27% line / 93.87% branch.

The production fix has a verified real call site: `DragTabBinder.set_columns` (`src/gui/widgets/_schema_builder_drag_tabs.py:123`) calls `prepopulate()`, and `SchemaBuilderPresenter.load_existing` (`schema_builder_presenter.py:215`) reaches `_render_state` -> `view.set_columns` -> the binder. The new seam is wired through production, not only exercised by unit tests.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ Python: `python.md` + `python-suppressions.md`
- N/A PowerShell, TypeScript, C#, Bash, JSON (zero changed files)

**Temporary artifacts cleanup:**
- ✅ No temporary or one-time scripts were created by this review.
- ✅ No throwaway scripts to dispose of.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | The four new tests each construct their own `FakeColumnsTabView` / `FakeSchemaBuilderView` and `SchemaBuilderState`; no shared mutable module state. |
| **Isolation** - Each test targets single behavior | ✅ PASS | One AC per test: empty-pool seeding (AC-1), alias-free unassigned (AC-2), live-match-wins (AC-3), edit-then-save round-trip (AC-4). |
| **Fast Execution** - Tests complete quickly | ✅ PASS | Targeted run of both files: 28 passed in 0.63s. |
| **Determinism** - Consistent results | ✅ PASS | Pure presenter/state logic, no clock/RNG/network/filesystem. Inputs are literal tuples. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive `test_*` names, AC-tagged docstrings, explicit Arrange/Act/Assert comments. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Baseline 98.27% lines / 93.83% branch repo-wide; modified file 92.52% lines / 82.14% branch. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Timestamp 2026-06-10 02:11. Source: `evidence/qa-gates/coverage-comparison.md`. |
| **No Coverage Regression** | ✅ PASS | Post-change repo-wide 98.27% lines / 93.87% branch (+0.00pp / +0.04pp). Modified file 93.33% lines / 85.29% branch (improved). No regression. |
| **New Code Coverage >= 90%** | ✅ PASS | Changed lines (call site 108, helper 111-154) are 100% covered; none appear in the post-change missing set [263, 285, 286]. Independently confirmed by lcov parse. |
| **Comprehensive Coverage** | ✅ PASS | `_seed_from_persisted_aliases` is exercised for: aliased row seeds (AC-1), alias-free row stays unassigned (AC-2), already-consumed row not overridden (AC-3). |
| **Positive Flows** - Valid inputs | ✅ PASS | `test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool` seeds two aliased rows. Total positive: 1 plus round-trip. |
| **Negative Flows** - Invalid inputs | ✅ PASS | `test_prepopulate_leaves_alias_free_row_unassigned_empty_pool` asserts `(canonical, None)` for an alias-free row. |
| **Edge Cases** - Boundary conditions | ✅ PASS | Empty source pool (no preview slice); alias-free row; live-vs-persisted conflict resolved to live. |
| **Error Handling** - Error paths | ✅ PASS | No new error paths introduced; the helper only mutates `consumed_columns` for unassigned aliased rows. No exceptions are part of the new contract. |
| **Concurrency** - If applicable | N/A | Single-threaded GUI presenter logic. |
| **State Transitions** - If applicable | ✅ PASS | The transition under test is "loaded-with-aliases -> rendered-as-assigned" via `consumed_columns`; round-trip test (AC-4) confirms load->save preserves aliases. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98.27% lines -> Post-change: 98.27% lines. Change: +0.00pp lines / +0.04pp branch (852/908 -> 858/914). New/changed-code coverage: 100% (changed lines 108, 111-154 all covered). Disposition: PASS. Evidence: `artifacts/python/lcov.info`, `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/qa-gates/coverage-comparison.md`.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Assertions compare concrete tuples/dicts (`state.consumed_columns == {...}`), producing readable diffs on failure. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Each test labels Arrange/Act/Assert explicitly in comments. |
| **Document Intent** | ✅ PASS | Each test docstring names the AC and the scenario. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No database, network, API, process, or filesystem dependency in the new tests. |
| **Use Mocks/Stubs** | ✅ PASS | `FakeColumnsTabView` / `FakeSchemaBuilderView` / `FakeSchemaService` are in-memory fakes, not heavy mocks. |
| **Environment Stability** | ✅ PASS | No temp files; no global state; inputs are literal in each test. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required policy review for the change. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | issue.md states the bug, verified root cause, and proposed behavior for #62. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-09T21-57.md` present in the feature folder. |
| **Document the plan** | ✅ PASS | Plan and phase-0 evidence captured under `evidence/baseline/`. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | A single private helper appended after the existing fuzzy-match loop; minimal control flow. |
| **Reusability** | ✅ PASS | Seeding logic is centralized in `_seed_from_persisted_aliases`, called once from `prepopulate`. |
| **Extensibility** | ✅ PASS | The seam is internal; no public API change. The "live-match-wins" ordering is explicit and documented. |
| **Separation of concerns** | ✅ PASS | Pure state mutation on `consumed_columns`; no I/O, no Qt import added (confirmed by inspection). |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | The change stays within the Columns-tab presenter responsibility. |
| **Under 500 lines** | ✅ PASS | `_columns_tab_presenter.py` 406, `test_columns_tab_presenter.py` 312, `test_schema_builder_presenter_core.py` 343 (awk line counts). All under 500. |
| **Public vs internal** | ✅ PASS | New method is `_`-prefixed (internal). |
| **No circular dependencies** | ✅ PASS | No new imports added; call graph unchanged in shape. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `_seed_from_persisted_aliases` describes intent precisely. |
| **Docs/docstrings** | ✅ PASS | The new method carries a full Google-style docstring (Purpose, Behavior/ordering, Design decision, Returns, Side effects). |
| **Comment why, not what** | ✅ PASS | Inline comments explain the live-match-wins ordering and the deliberate no-source-pool-reflection decision. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black --check` on the 3 changed files: "3 files would be left unchanged." |
| **2. Linting** | ✅ PASS | `poetry run ruff check` on the 3 changed files: "All checks passed!" |
| **3. Type checking** | ✅ PASS | `poetry run pyright` on the 3 changed files: 0 errors, 0 warnings. |
| **4. Testing** | ✅ PASS | `poetry run pytest tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py`: 28 passed. |
| **Full toolchain loop** | ✅ PASS | All check-only stages pass in a single pass; no auto-fixes were needed. |
| **Explicit reporting** | ✅ PASS | Commands and results recorded in this audit and Appendix B. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `db1c9f0` and issue.md summarize the fix. |
| **Design choices explained** | ✅ PASS | The "no source-pool reflection" decision is documented in the method docstring. |
| **Update supporting documents** | ✅ PASS | issue.md AC checkboxes and evidence/** updated by the executor. |
| **Provide next steps** | ✅ PASS | Next step recorded in issue.md (minor-audit review — this artifact). |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check <3 files>` — unchanged. |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check <3 files>` — All checks passed. |
| **Type checking with Pyright** | ✅ PASS | `poetry run pyright <3 files>` — 0 errors. |
| **Testing with Pytest** | ✅ PASS | 28 targeted tests pass; full suite 1027 pass per executor evidence. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | `_seed_from_persisted_aliases(self) -> None` fully annotated; loop unpacks the typed `columns` tuple. No `Any` introduced. |
| **Dataclasses for value objects** | ✅ PASS | Operates on the existing `SchemaBuilderState`; no new value object needed. |
| **Protocols/ABCs for interfaces** | N/A | No new interface introduced. |
| **Avoid utility classes** | ✅ PASS | Logic added as a method on the existing presenter, not a static utility. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | No broad `except`; no new exception handling added. |
| **Logging over print** | ✅ PASS | No `print` introduced. |
| **Invariants at construction** | ✅ PASS | One-source-per-row invariant preserved: only unassigned rows are seeded, at most one alias each. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Plain `test_*` functions, no class scaffolding. |
| **Coverage expectation** | ✅ PASS | Changed-line coverage 100%; repo-wide 98.27% line / 93.87% branch (>= 85% / >= 75%). |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | In-memory fakes, no `unittest.mock` patching of the unit under test. |
| **Organization** | ✅ PASS | Tests live in `tests/gui/` mirroring `src/gui/`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Names encode the scenario (e.g., `test_live_fuzzy_match_wins_over_persisted_alias`). |
| **Docstrings/comments** | ✅ PASS | Each test has an AC-tagged docstring. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest tests/gui/...` — 28 passed in 0.63s. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### ColumnsTabPresenter._seed_from_persisted_aliases (3 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool | Positive | 108, 111-154 (seed branch) | ✅ |
| test_prepopulate_leaves_alias_free_row_unassigned_empty_pool | Negative/Edge | 111-154 (alias-free skip) | ✅ |
| test_live_fuzzy_match_wins_over_persisted_alias | Edge (ordering) | 111-154 (already-consumed skip) | ✅ |

**Coverage:** Changed lines 100%. Whole file 96.5% line / 85.3% branch (lcov).

**Not covered:** Lines 263, 285, 286 — pre-existing helpers (`_release_*`, `_render_assignments_and_dtypes`), not touched by this change.

### SchemaBuilderPresenter edit-then-save round-trip (1 test)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_edit_then_save_preserves_persisted_aliases | Positive (round-trip) | load_existing -> save path | ✅ |

**Coverage:** Confirms aliases survive a load->save round-trip (AC-4).

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests (targeted) | 28 | ✅ |
| Tests Passed | 28 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | 0.63s total (targeted) | ✅ Fast |
| Full-suite (executor evidence) | 1027 passed | ✅ |
| Test File Size | 312 / 343 lines | ✅ Maintainable |
| Code Coverage (modified file) | 96.5% lines, 85.3% branches | ✅ |
| Code Coverage (repo-wide) | 98.27% lines, 93.87% branches | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check <3 files>` | 3 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check <3 files>` | All checks passed | ✅ |
| Pyright Type Checking | `poetry run pyright <3 files>` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `poetry run pytest tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py` | 28 passed | ✅ |

**Notes:**
No pre-existing failures observed in the targeted scope. Suppression scan (`noqa` / `type: ignore` / `pyright: ignore`) on the three changed files returned zero matches; no suppression authorization is required.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements are met.

### Approved Exceptions
**None.** No exceptions needed.

### Removed/Skipped Tests
**None.** All planned tests implemented; 4 new tests added (AC-1..AC-4).

---

## Evidence Location Compliance

A diff scan for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned zero matches. All feature evidence is written to the canonical `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/<kind>/` paths (baseline, qa-gates, regression-testing). The repo evidence-validator script `scripts/validate_evidence_locations.py` is absent in this repository; a git-diff scan was used as the substitute and found no violations. No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` entries were required.

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. **db1c9f0** — fix(gui): seed Columns-tab assignments from persisted aliases on schema edit (#62)

### Files Modified

1. **src/gui/presenters/_columns_tab_presenter.py** (MODIFIED)
   - Added `_seed_from_persisted_aliases()` and a call to it at the end of `prepopulate()`.
   - Live-match-wins ordering; seeds at most one alias per unassigned row; does not reflect into `source_columns`.

2. **tests/gui/test_columns_tab_presenter.py** (MODIFIED)
   - Added 3 tests covering AC-1, AC-2, AC-3.

3. **tests/gui/test_schema_builder_presenter_core.py** (MODIFIED)
   - Added 1 test covering AC-4 (edit-then-save round-trip).

Plus feature-folder docs and evidence (issue.md, plan, evidence/**) — non-code.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The change satisfies the cross-language and Python-specific code-change and unit-test policies. The full Python toolchain (Black, Ruff, Pyright, Pytest) is clean on the changed files, coverage is verified from the pre-existing `artifacts/python/lcov.info` with 100% changed-line coverage and no regression, all changed files are under the 500-line cap, no suppressions were introduced, and the production fix has a verified real call site through `DragTabBinder.set_columns` and `SchemaBuilderPresenter.load_existing`.

**Fail-closed reminder:** All required baseline, QA, and coverage artifacts are present and were inspected; no fail-closed condition applies.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes: documented in issue.md and plan
- ✅ Design Principles: simple, cohesive, no I/O
- ✅ Module & File Structure: all files < 500 lines
- ✅ Naming, Docs, Comments: full docstring + intent comments
- ✅ Toolchain Execution: clean single-pass
- ✅ Summarize & Document: complete

#### Language-Specific Code Change Policy (Section 3)
**For Python:**
- ✅ Tooling & Baseline: Black/Ruff/Pyright/Pytest clean
- ✅ Python Design & Typing: fully annotated, no `Any`
- ✅ Error Handling: invariant preserved, no broad catches

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

- ✅ 1027/1027 tests passing (full suite, executor evidence); 28/28 targeted
- ✅ 100% changed-line coverage
- ✅ 98.27% repo-wide line coverage, 93.87% branch
- ✅ All changed files under 500 lines (406 / 312 / 343)
- ✅ All Python code quality checks passing
- ✅ Targeted test execution time 0.63s (fast)

---

### Recommendation

**Ready for merge.**

No blocking or partial findings. The fix is correctly wired into production, the toolchain is clean, coverage thresholds are met with no regression, and all four acceptance criteria are satisfied (see feature-audit).

---

## Appendix A: Test Inventory

- tests/gui/test_columns_tab_presenter.py::test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool
- tests/gui/test_columns_tab_presenter.py::test_prepopulate_leaves_alias_free_row_unassigned_empty_pool
- tests/gui/test_columns_tab_presenter.py::test_live_fuzzy_match_wins_over_persisted_alias
- tests/gui/test_schema_builder_presenter_core.py::test_edit_then_save_preserves_persisted_aliases

(Plus the pre-existing tests in both files, re-run green.)

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
env -u VIRTUAL_ENV poetry run black --check src/gui/presenters/_columns_tab_presenter.py tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py

# Linting
env -u VIRTUAL_ENV poetry run ruff check src/gui/presenters/_columns_tab_presenter.py tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py

# Type checking
env -u VIRTUAL_ENV poetry run pyright src/gui/presenters/_columns_tab_presenter.py tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py

# Testing
env -u VIRTUAL_ENV poetry run pytest tests/gui/test_columns_tab_presenter.py tests/gui/test_schema_builder_presenter_core.py -q

# Coverage (inspected, not regenerated): artifacts/python/lcov.info
```

---

**Audit Completed By:** feature-review agent (Claude)
**Audit Date:** 2026-06-09
**Policy Version:** Current (as of audit date)
