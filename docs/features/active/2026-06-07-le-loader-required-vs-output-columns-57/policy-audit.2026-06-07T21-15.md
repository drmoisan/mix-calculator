# Policy Compliance Audit: le-loader-required-vs-output-columns (#57)

**Audit Date:** 2026-06-07
**Code Under Test:** `src/_normalize_le_columns.py`, `src/normalize_le.py`, `tests/test_normalize_le.py`, `tests/test_normalize_le_columns.py` (new), `tests/test_normalize_le_header.py`

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 5 files | 11 new tests | ✅ 987 pass, 0 fail | 99.08% lines, 96.15% branch | 99.08% lines, 93.96% branch | 100% lines (both changed src modules) |

**Note:** No PowerShell, TypeScript, C#, Bash, or JSON files changed in the #57 delta (`git diff 721a1bf..HEAD`). `.vscode/launch.json` is part of a separate preceding chore commit (`fceb35e`), not the #57 delta, and is not source-governed.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - no TypeScript files changed`
- TypeScript post-change coverage artifact: `N/A - no TypeScript files changed`
- PowerShell baseline coverage artifact: `N/A - no PowerShell files changed`
- PowerShell post-change coverage artifact: `N/A - no PowerShell files changed`
- Python baseline coverage artifact: `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/baseline/baseline-pytest-coverage.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/qa-gates/final-pytest-coverage.md`
- Per-language comparison summary: Section 1.2.1 below; `evidence/qa-gates/coverage-delta.md`

**Non-negotiable verdict rule:** Numeric baseline and post-change coverage metrics are provided for the only in-scope language (Python).

**Fail-closed rule:** No required artifact is missing.

---

## Executive Summary

This audit covers the isolated #57 delta on branch `fix/loader-header-row-detection` against base `main`. The #57 change makes the protected LE loader (`src/normalize_le.load_source` via `src/_normalize_le_columns.resolve_le_columns`) require only the 23 must-have source columns and treat `YTD/YTG` and source `Super Category` as optional-by-name (located if present, tolerated if absent), mirroring the AOP `load_aop` `KEY`/`YTG` pattern.

The change is verified Python-only. The independent toolchain run (Black, Ruff, Pyright on the changed files; full Pytest suite) passed in a single pass. The parity invariant — byte-identical output for the standard full-column `LE-8 + 4` source — is confirmed by a dedicated test that passes. AOP modules and CI workflows are unchanged. No suppressions were added. All changed files are at or under the 500-line limit.

**Scope determination:** Scope is the full branch delta isolated to #57 (`git diff 721a1bf..HEAD`), per the caller-provided isolation against the already-reviewed #55 work. Base branch is `main` (merge-base `b655d81`, timestamp 2026-06-06T22:10:29-04:00). No caller instruction narrowed scope below the full #57 delta; see Rejected Scope Narrowing.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A `powershell.md` (no PowerShell files changed)
- N/A TypeScript / C# / Bash / JSON (no such files changed)

**Temporary artifacts cleanup:**
- ✅ No temporary or one-time scripts were created during this review.
- ✅ No ongoing tooling scripts were added.

---

## Rejected Scope Narrowing

None. The caller instructed isolation of the #57 delta from the already-reviewed #55 header-detection work via `git diff 721a1bf..HEAD`, which defines the legitimate review scope for this feature (the #57 implementation plus its tests). This is a baseline selection between two completed features, not a narrowing to a plan/task/phase subset or a subset of the #57 changed files. All files in the #57 delta with changes were audited, and the only in-scope language (Python) received an explicit PASS coverage verdict. No attempted narrowing to "plan scope," "out of scope," or "informational only" was present.

---

## Evidence Location Compliance

Scanned the #57 branch delta for evidence files written under non-canonical paths (`artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, `artifacts/coverage/`). None found. All executor evidence is under the canonical `docs/features/active/2026-06-07-le-loader-required-vs-output-columns-57/evidence/<kind>/` location (baseline, qa-gates, regression-testing, other). No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events. The repository's `scripts/validate_evidence_locations.py` is absent (see persistent memory); a `git diff --stat 721a1bf..HEAD` path scan was used instead and returned no violations.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** | ✅ PASS | Each new test builds its own in-memory workbook/column list; no shared mutable state. `test_normalize_le_columns.py` uses pure column-name lists; `test_normalize_le.py` helpers `_row`/`_pruned` construct fresh inputs per test. |
| **Isolation** | ✅ PASS | `test_normalize_le_columns.py` targets the pure `resolve_le_columns` helper directly; `test_normalize_le.py`/`test_normalize_le_header.py` target `load_source`/`normalize` integration paths. One behavior per test. |
| **Fast Execution** | ✅ PASS | Targeted LE/AOP/parity subset (102 tests) ran in 8.07s; full suite (987 tests) in 26.04s. |
| **Determinism** | ✅ PASS | No clock, RNG, network, or filesystem temp files. Workbooks built via `io.BytesIO`. |
| **Readability & Maintainability** | ✅ PASS | Descriptive `test_...` names and AAA-structured docstrings/comments on each new test. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Baseline 99.08% lines / 96.15% branch (4761 stmts, 884 branches), 976 tests. Source: `evidence/baseline/baseline-pytest-coverage.md`. |
| **No Coverage Regression** | ✅ PASS | Post-change 99.08% lines / 93.96% branch. Changed modules both at 100% line. The branch-percentage move (96.15%->93.96%) reflects 10 new branches added (884->894) with partial count held at 54; no regression on changed lines. Evidence: `evidence/qa-gates/coverage-delta.md`. |
| **New Code Coverage** | ✅ PASS | `src/_normalize_le_columns.py`: 100% line / 100% branch. `src/normalize_le.py`: 100% line / 96% branch (the one partial branch 162->167 is the pre-existing seekable-buffer guard, not introduced by #57). New test file `tests/test_normalize_le_columns.py` exercises required-count, both-present, each-absent, both-absent, and missing-required paths. |
| **Comprehensive Coverage** | ✅ PASS | `resolve_le_columns`: 6 unit tests (required count, optional-by-name list, YTD/YTG absent, Super Category absent, both present/carried, missing-required raises). `load_source`/`normalize`: YTD/YTG-absent, Super-Category-absent, both-absent, parity, flat LE84Data sheet. |
| **Positive Flows** | ✅ PASS | `test_both_optionals_present_are_located_and_carried_to_canonical_names`, `test_full_column_source_output_parity_with_standard_fixture`. |
| **Negative Flows** | ✅ PASS | `test_missing_required_column_raises_value_error_naming_it` (drops PPG, asserts `ValueError` matches "PPG"). |
| **Edge Cases** | ✅ PASS | `test_load_source_without_both_optionals_yields_all_target_columns`, `test_flat_le84data_style_sheet_imports_to_target_columns` (header index 0, no YTD/YTG, no KEY). |
| **Error Handling** | ✅ PASS | Missing-required-column path raises a clear, column-naming `ValueError`; verified by the negative test. |
| **Concurrency** | N/A | Pure synchronous column resolution; no concurrency. |
| **State Transitions** | N/A | No stateful component introduced. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.08% line / 96.15% branch -> Post-change: 99.08% line / 93.96% branch. Change: +0.00% line / -2.19% branch (added optional-by-name branches; no regression on changed lines). New/changed-code coverage: 100% line on both changed source modules (`_normalize_le_columns.py` 100%/100% branch; `normalize_le.py` 100%/96% branch). Disposition: PASS. Evidence: `evidence/baseline/baseline-pytest-coverage.md`, `evidence/qa-gates/final-pytest-coverage.md`, `evidence/qa-gates/coverage-delta.md`.
- TypeScript: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope`. Disposition: N/A (zero TypeScript files in the branch delta). Evidence: N/A.
- PowerShell: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope`. Disposition: N/A (zero PowerShell files in the branch delta). Evidence: N/A.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | `pytest.raises(ValueError, match="PPG")` and `pd.testing.assert_frame_equal` for parity give precise diagnostics. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Each new test has explicit Arrange/Act/Assert comments. |
| **Document Intent** | ✅ PASS | Each new test carries a one-line docstring naming the scenario and expected outcome. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No network/DB/process. Workbooks via `io.BytesIO`; column tests use plain lists. |
| **Use Mocks/Stubs** | ✅ PASS | No mocking required; tests exercise real pure code paths. |
| **Environment Stability** | ✅ PASS | No runtime temp files; no mutable global state. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required policy review for #57. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Objective is issue #57 (spec.md v1.0): require only must-have LE columns. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-07T20-29.md` present in feature folder. |
| **Document the plan** | ✅ PASS | spec.md "Proposed Fix" and the plan document the design. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | The change reuses the existing KEY-location pattern for the two optionals; control flow stays a single resolution pass. |
| **Reusability** | ✅ PASS | `REQUIRED_COLUMNS`/`OPTIONAL_BY_NAME` constants are shared between the resolver and `load_source`; mirrors the AOP module convention. |
| **Extensibility** | ✅ PASS | Adding future optional-by-name columns is a one-line list edit. |
| **Separation of concerns** | ✅ PASS | Pure column resolution stays in `_normalize_le_columns.py`; I/O selection stays in `normalize_le.load_source`. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | Constants + pure resolver in `_normalize_le_columns.py`; loader in `normalize_le.py`. |
| **Under 500 lines** | ✅ PASS | `_normalize_le_columns.py` 209, `normalize_le.py` 479, `test_normalize_le.py` 499, `test_normalize_le_columns.py` 103, `test_normalize_le_header.py` 73 (via `awk END{print NR}`). `test_normalize_le.py` is at 499 — compliant but 1 line below the cap; flagged as a Minor watch item in the code review. |
| **Public vs internal** | ✅ PASS | New `REQUIRED_COLUMNS`/`OPTIONAL_BY_NAME` added to `__all__` of both the helper module and the re-exporting `normalize_le.py`. |
| **No circular dependencies** | ✅ PASS | `normalize_le` imports from `_normalize_le_columns`; no reverse import. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `REQUIRED_COLUMNS`, `OPTIONAL_BY_NAME`, `optional_actual`, `located` are descriptive. |
| **Docs/docstrings** | ✅ PASS | `resolve_le_columns` docstring updated to describe optional-by-name location, raises, and side effects. |
| **Comment why, not what** | ✅ PASS | Comments explain why YTD/YTG and source Super Category are safe to tolerate as absent (dropped/derived downstream) and why parity holds. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black --check` on the 5 changed files: "5 files would be left unchanged." |
| **2. Linting** | ✅ PASS | `poetry run ruff check` on the 5 changed files: "All checks passed!" |
| **3. Type checking** | ✅ PASS | `poetry run pyright` on the 5 changed files: "0 errors, 0 warnings, 0 informations." |
| **4. Testing** | ✅ PASS | `poetry run pytest` whole suite: 987 passed, 0 failed (executor `final-pytest-coverage.md`); reviewer targeted re-run: 102 passed across LE/AOP/parity/etl_columns. |
| **Full toolchain loop** | ✅ PASS | All stages clean in a single pass on review. |
| **Explicit reporting** | ✅ PASS | Commands and results documented here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `3ae79b1` message and spec.md summarize the change. |
| **Design choices explained** | ✅ PASS | spec.md "Design summary" explains the AOP-pattern mirror. |
| **Update supporting documents** | ✅ PASS | issue.md/spec.md AC checkboxes maintained; header-detection comment updated to 23 tokens. |
| **Provide next steps** | ✅ PASS | Rides in PR #56; this audit gives the go recommendation. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `env -u VIRTUAL_ENV poetry run black --check <5 files>` -> unchanged. |
| **Linting with Ruff** | ✅ PASS | `env -u VIRTUAL_ENV poetry run ruff check <5 files>` -> All checks passed. |
| **Type checking with Pyright** | ✅ PASS | `env -u VIRTUAL_ENV poetry run pyright <5 files>` -> 0 errors. |
| **Testing with Pytest** | ✅ PASS | Full suite 987 passed; targeted re-run 102 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | New constants typed `list[str]`; `resolve_le_columns` returns `tuple[dict[str, str], str | None]`; `optional_actual: dict[str, str]`. No `Any` introduced. |
| **Dataclasses for value objects** | N/A | No new value objects; module-level constants and a pure function. |
| **Protocols/ABCs for interfaces** | N/A | Single implementation; no interface needed. |
| **Avoid utility classes** | ✅ PASS | Module-level functions/constants, no static-only utility class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | Missing required column raises `ValueError` (propagated from `resolve_columns`) naming the column; no broad catch. |
| **Logging over print** | ✅ PASS | Extra-column warning uses `logger.warning`; no print. |
| **Invariants at construction** | N/A | No class construction introduced. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | All tests are Pytest functions; `pytest.raises` for negative paths. |
| **Coverage expectation** | ✅ PASS | New code 100% line on both changed src modules; repo-wide 99.08% line / 93.96% branch. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | No mocks; real pure paths and in-memory workbooks. |
| **Organization** | ✅ PASS | `tests/test_normalize_le_columns.py` mirrors `src/_normalize_le_columns.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_<scenario>` names. |
| **Docstrings/comments** | ✅ PASS | Docstring per test; AAA comments. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest`. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### resolve_le_columns (6 tests — tests/test_normalize_le_columns.py)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_required_columns_has_exactly_23_entries | Positive (invariant) | ✅ |
| test_optional_by_name_is_ytd_ytg_and_super_category | Positive (invariant) | ✅ |
| test_ytd_ytg_absent_is_not_required_and_not_in_selection | Edge Case | ✅ |
| test_source_super_category_absent_is_not_required_and_not_in_selection | Edge Case | ✅ |
| test_both_optionals_present_are_located_and_carried_to_canonical_names | Positive (parity) | ✅ |
| test_missing_required_column_raises_value_error_naming_it | Negative/Error | ✅ |

**Coverage:** `src/_normalize_le_columns.py` 100% line / 100% branch.

### load_source / normalize optional handling (5 tests — test_normalize_le.py, test_normalize_le_header.py)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_load_source_without_ytd_ytg_succeeds_and_drops_it | Edge Case | ✅ |
| test_load_source_without_super_category_output_super_from_ppg | Edge Case | ✅ |
| test_load_source_without_both_optionals_yields_all_target_columns | Edge Case | ✅ |
| test_full_column_source_output_parity_with_standard_fixture | Positive (parity) | ✅ |
| test_flat_le84data_style_sheet_imports_to_target_columns | Edge Case (AC-6) | ✅ |

**Coverage:** `src/normalize_le.py` 100% line / 96% branch (pre-existing partial 162->167 only).

**Not covered:** None introduced by #57.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests (whole suite) | 987 | ✅ |
| Tests Passed | 987 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | 26.04s (whole suite) | ✅ Fast |
| New tests added by #57 | 11 | ✅ |
| Code Coverage | 99.08% lines, 93.96% branches (repo-wide) | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check <changed files>` | 5 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check <changed files>` | All checks passed | ✅ |
| Pyright Type Checking | `poetry run pyright <changed files>` | 0 errors | ✅ |
| Pytest Tests | `poetry run pytest` | 987 passed | ✅ |

**Notes:**
No pre-existing failures observed. Suppression scan over the full #57 diff (`git diff 721a1bf..HEAD` for `noqa`/`type: ignore`/`pyright: ignore`) returned no matches in code; the only matches are in feature-folder documentation describing the absence of suppressions. No CI workflow files (`.github/workflows/**`, `.github/actions/**`, `scripts/benchmarks/**`) are in the delta, so the `modified-workflow-needs-green-run` rule does not fire.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements are met.

### Approved Exceptions
**None.** No exceptions needed.

### Removed/Skipped Tests
**None.** No tests were removed or skipped.

---

## 9. Summary of Changes

### Commits in This Delta (721a1bf..HEAD, #57 isolation)

1. **3ae79b1** - fix(loader): require only must-have LE columns; YTD/YTG and source Super Category optional (#57)
2. **fceb35e** - chore(dev): add VS Code debug launch configs (separate chore, `.vscode/launch.json`; not source-governed)

### Files Modified (#57 implementation)

1. **src/_normalize_le_columns.py** (MODIFIED) — Added `REQUIRED_COLUMNS` (23), `OPTIONAL_BY_NAME` (`["YTD/YTG", "Super Category"]`); redefined `EXPECTED_COLUMNS = REQUIRED_COLUMNS`; rewrote `resolve_le_columns` to locate KEY + optionals by normalized name (no fuzzy, no raise) and require only `REQUIRED_COLUMNS`.
2. **src/normalize_le.py** (MODIFIED) — `load_source` builds `columns_to_keep` from `REQUIRED_COLUMNS` + located optionals + KEY; header-detection comment updated to 23 tokens (`min_match=20` unchanged); `normalize()`/`validate_tieouts()` unchanged.
3. **tests/test_normalize_le_columns.py** (NEW) — 6 unit tests for `resolve_le_columns`.
4. **tests/test_normalize_le.py** (MODIFIED) — 4 load/normalize optional-handling tests including the parity test.
5. **tests/test_normalize_le_header.py** (MODIFIED) — 1 flat LE84Data-style import test (AC-6).

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The #57 delta meets the cross-language code-change, unit-test, and Python-specific policies. Toolchain is clean, parity is verified, AOP and CI workflows are untouched, no suppressions were added, and all changed files are within the 500-line limit.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes
- ✅ Design Principles
- ✅ Module & File Structure
- ✅ Naming, Docs, Comments
- ✅ Toolchain Execution
- ✅ Summarize & Document

#### Language-Specific Code Change Policy (Section 3) — Python
- ✅ Tooling & Baseline
- ✅ Python Design & Typing
- ✅ Error Handling

#### General Unit Test Policy (Section 1)
- ✅ Core Principles
- ✅ Coverage & Scenarios
- ✅ Test Structure
- ✅ External Dependencies
- ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4) — Python
- ✅ Framework & Scope
- ✅ Test Style & Structure
- ✅ Naming & Readability
- ✅ Toolchain

### Metrics Summary
- ✅ 987/987 tests passing (100%)
- ✅ 99.08% line coverage repo-wide; 100% line on both changed src modules
- ✅ All code quality checks passing
- ✅ All changed files <= 500 lines

### FAIL + Blocking-PARTIAL count (exit-gate number): 0

### Recommendation

**Ready for merge.** No remediation required.

---

## Appendix A: Test Inventory

- tests/test_normalize_le_columns.py::test_required_columns_has_exactly_23_entries
- tests/test_normalize_le_columns.py::test_optional_by_name_is_ytd_ytg_and_super_category
- tests/test_normalize_le_columns.py::test_ytd_ytg_absent_is_not_required_and_not_in_selection
- tests/test_normalize_le_columns.py::test_source_super_category_absent_is_not_required_and_not_in_selection
- tests/test_normalize_le_columns.py::test_both_optionals_present_are_located_and_carried_to_canonical_names
- tests/test_normalize_le_columns.py::test_missing_required_column_raises_value_error_naming_it
- tests/test_normalize_le.py::test_load_source_without_ytd_ytg_succeeds_and_drops_it
- tests/test_normalize_le.py::test_load_source_without_super_category_output_super_from_ppg
- tests/test_normalize_le.py::test_load_source_without_both_optionals_yields_all_target_columns
- tests/test_normalize_le.py::test_full_column_source_output_parity_with_standard_fixture
- tests/test_normalize_le_header.py::test_flat_le84data_style_sheet_imports_to_target_columns

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
env -u VIRTUAL_ENV poetry run black --check src/_normalize_le_columns.py src/normalize_le.py tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py

# Linting
env -u VIRTUAL_ENV poetry run ruff check src/_normalize_le_columns.py src/normalize_le.py tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py

# Type checking
env -u VIRTUAL_ENV poetry run pyright src/_normalize_le_columns.py src/normalize_le.py tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py

# Testing (targeted)
env -u VIRTUAL_ENV poetry run pytest tests/test_normalize_le.py tests/test_normalize_le_columns.py tests/test_normalize_le_header.py tests/test_etl_columns.py tests/test_load_aop.py tests/test_normalize_le_io.py tests/test_schema_loader_parity_le.py -q

# Coverage (whole suite, executor)
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-07
**Policy Version:** Current (as of audit date)
