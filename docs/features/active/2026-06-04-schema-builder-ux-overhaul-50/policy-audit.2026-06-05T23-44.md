# Policy Compliance Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 4 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-44
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `a45a987` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Code Under Test:** full branch diff `main...HEAD` (Python + JSON only). Cycle-4 commit delta is `cc5b282..a45a987`.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | src + test files | 942 tests | 942 pass, 0 fail | 99.06% line / 94.04% branch (cycle-4 entry baseline) | 99.06% line / 94.04% branch (TOTAL row 98%) | `src/schema_formula.py` 100% line / 100% branch |
| JSON | 2 schema files | N/A | load without error (tests/test_default_schemas.py) | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- TypeScript post-change coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- PowerShell baseline coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- PowerShell post-change coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- Python baseline coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-pytest.2026-06-05T23-23.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T23-23.md`; live re-run by this reaudit at HEAD `a45a987`
- Per-language comparison summary: see section 1.2.1

**Non-negotiable verdict rule:** numeric baseline and post-change coverage are present for the only in-scope language (Python). JSON has no coverage requirement. Coverage thresholds are met and the full test suite is GREEN (942 passed, 0 failed, EXIT 0) — the cycle-3 blocking RED-suite condition is resolved.

---

## Executive Summary

This is the EXIT reaudit of remediation cycle 4 for issue #50. The cycle-entry inputs (`remediation-inputs.2026-06-05T23-23.md`) carried blocking_count=1: a single blocking finding C1 — the formula-engine `col`-shadowing defect that left the full pytest suite RED at the cycle-3 exit (940 passed, 1 failed).

**C1 is closed at HEAD `a45a987`.** The fix in `src/schema_formula.py._build_symtable` (lines 301-314) restructures the symbol-table construction so the column-alias loop populates the dict first, then the whitelisted callables (`safe_div`, `sum`, `col`) are bound LAST. A column whose identifier alias collides with `col`/`sum`/`safe_div` can no longer overwrite the helper. The `col` accessor reads from the closed-over `context`, not from `symtable`, so `col("col")` (and `col("sum")`, `col("safe_div")`) still returns the exact-name column value. The previously-failing Hypothesis property test `tests/test_schema_formula.py::test_property_col_round_trips_values` now passes, and a new regression test `test_evaluate_column_named_col_round_trips_via_col_callable` (tests/test_schema_formula.py:249-269) asserts that columns named `col`, `sum`, and `safe_div` each round-trip through `col(...)` and return their stored values (7.0, 3.0, 11.0) without shadowing the helper. Both tests verified passing by this reaudit.

**Full toolchain is GREEN at HEAD `a45a987` (independently re-run by this reaudit):**

- Black: `env -u VIRTUAL_ENV poetry run black --check .` -> `222 files would be left unchanged`, EXIT 0.
- Ruff: `env -u VIRTUAL_ENV poetry run ruff check .` -> `All checks passed!`, EXIT 0.
- Pyright: `env -u VIRTUAL_ENV poetry run pyright` -> `0 errors, 0 warnings, 0 informations`, EXIT 0.
- Pytest: `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch` -> `942 passed, 0 failed`, EXIT 0.

The four-stage Python loop completes clean in a single pass. No files were changed by the format/lint/type-check stages.

**No regression of prior work.** B1/B2 (cycle-3 runtime-crash guards) remain in place: the blank/whitespace path-or-sheet guard at `src/gui/presenters/source_selection_presenter.py:237` and the `ValueError` absent-sheet contract at `src/gui/services/workbook_reader.py:164-165`. R1–R6 production wiring is intact at HEAD: `_on_partial_match` at `src/gui/app.py:327-349` (passed to three `SourceSelectionPresenter` constructions), `BuildSpecProvider` via `spec_provider=build_spec_provider(_svc)` at `src/gui/app.py:430`, `DragTabBinder` at `src/gui/widgets/schema_builder_dialog.py:98`, and `new_from_template` wired via `src/gui/_schema_open_helpers.py:159`. AC-2 auto-selection is re-confirmed by `tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables`. The schema model/migration and default-schema tests pass.

**Repo-wide coverage exceeds thresholds:** 99.06% line / 94.04% branch (reported TOTAL 98%). The targeted module `src/schema_formula.py` is 100% line / 100% branch; the three new production statements added by the fix are all exercised. The masking scan is clean, no unauthorized suppressions were added in cycle 4 (`NO_SUPPRESSIONS_ADDED`), no changed `.py` file exceeds 500 lines (`src/schema_formula.py` 315 lines, `tests/test_schema_formula.py` 379 lines), and no `.github/workflows/**` or `scripts/benchmarks/**` files changed across the whole feature diff.

**Verdict: PASS (0 BLOCKING).** C1 is closed, the full toolchain is green, all prior work is preserved, coverage holds, and all 38 acceptance criteria are satisfied. The remediation loop exit condition is met.

**Policy documents evaluated:**
- `general-code-change.md` (cross-language code change policy)
- `general-unit-test.md` (cross-language unit test policy)

**Language-specific policies evaluated:**
- `python.md` + `python-suppressions.md`
- N/A PowerShell (no PowerShell files in branch diff)
- N/A Bash (no Bash files in branch diff)
- JSON (two bundled schema files migrated in cycle 0; load-validated)

**Temporary artifacts cleanup:**
- No temporary/throwaway scripts left behind. `scripts/checks/scan_masked_fixtures.py` is a permanent, tested confidentiality tool.

---

## Rejected Scope Narrowing

None. The caller prompt directed a full branch-vs-base exit reaudit and did not attempt to narrow scope to any plan, task, phase, or file subset. The audit scope is the full `main...HEAD` diff; the cycle-4 commit delta (`cc5b282..a45a987`) is the change under remediation review. The caller's verification checklist (C1 closure, full toolchain green, no regression, coverage, masking, whole-feature AC sign-off) is consistent with the full-branch scope and is honored.

---

## Evidence Location Compliance

A git-diff scan over `main...HEAD` for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned no matches (`NO_NONCANONICAL_EVIDENCE_PATHS`). All evidence is under the canonical `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/` tree. The repository does not ship `scripts/validate_evidence_locations.py`; a git-diff scan was used as the substitute per the established convention. No evidence-location violations. No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events.

Note: pytest writes `artifacts/python/lcov.info` as the configured coverage output (a tool-generated coverage artifact, not an agent-authored evidence file). This is the language-standard coverage artifact path declared in the Coverage Verification table and is not a feature-evidence location; it is not a violation.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | PASS | 942 tests pass deterministically in a single pytest run at HEAD `a45a987`; no ordering dependency. |
| **Isolation** - Each test targets single behavior | PASS | The new regression test targets exactly one behavior (colliding-column round-trip via `col()`); the property test exercises the `col` round-trip invariant. |
| **Fast Execution** - Tests complete quickly | PASS | Full suite ran in 21.86s for 942 tests under `QT_QPA_PLATFORM=offscreen`. |
| **Determinism** - Consistent results | PASS | The previously-deterministic falsifying example `{'col': 0.0}` now passes; the suite is fully green with no flakiness. |
| **Readability & Maintainability** - Clear structure | PASS | The new regression test carries a descriptive name and an intent docstring naming C1, with explicit Arrange/Act/Assert sections. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | PASS | **Baseline (cycle-4 P0-T5):** `evidence/remediation-baseline/baseline-pytest.2026-06-05T23-23.md` (99.06% line / 94.04% branch; 940 passed, 1 failed entry state). |
| **No Coverage Regression** | PASS | **Post-change (this reaudit, HEAD `a45a987`):** 99.06% line / 94.04% branch (TOTAL row 98%). No regression; the targeted module remains 100%/100%. |
| **New Code Coverage >=85% line / >=75% branch** | PASS | `src/schema_formula.py` 100% line, 100% branch; the 3 added production statements are all exercised. |
| **Comprehensive Coverage** | PASS | C1 covered by the now-passing property test plus the new colliding-column regression test (columns named `col`/`sum`/`safe_div`). |
| **Positive Flows** | PASS | `col("col")`/`col("sum")`/`col("safe_div")` return stored values (7.0/3.0/11.0). |
| **Negative Flows** | PASS | `test_evaluate_col_unknown_column_raises` (col() on a missing column raises FormulaError) retained and passing. |
| **Edge Cases** | PASS | Column names that exactly equal whitelisted callable names are the edge case the fix addresses. |
| **Error Handling** | PASS | `col()` still raises `FormulaError` for unknown columns; the whitelisted callables are not shadowed. |
| **Concurrency** | N/A | Not applicable to the symbol-table construction change in this cycle. |
| **State Transitions** | N/A | Not applicable to the pure symbol-table builder. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.06% line / 94.04% branch -> Post-change: 99.06% line / 94.04% branch. Change: +3 covered production statements (alias-loop-first restructuring plus three explicit whitelisted-callable bindings), coverage-neutral repo-wide. New/changed-code coverage: `src/schema_formula.py` 100% line / 100% branch. Disposition: PASS (thresholds line >=85% and branch >=75% both hold; no regression on changed lines). Evidence: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T23-23.md` plus this reaudit's live re-run at HEAD `a45a987`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero PowerShell files in branch diff).
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero TypeScript files in branch diff).
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero C# files in branch diff).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | PASS | The regression test asserts exact returned values per colliding name. |
| **Arrange-Act-Assert Pattern** | PASS | `test_evaluate_column_named_col_round_trips_via_col_callable` uses explicit Arrange/Act/Assert comments. |
| **Document Intent** | PASS | The new test's docstring names C1 and explains the shadowing invariant. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | PASS | The formula tests are pure in-memory; no network/DB/temp files. |
| **Use Mocks/Stubs** | PASS | No mocks required; the test uses a real `FormulaEvaluator` against an in-memory context dict. |
| **Environment Stability** | PASS | `QT_QPA_PLATFORM=offscreen`; no runtime temp-file creation; masking scan clean. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | PASS | This artifact is the required review for the cycle-4 exit reaudit. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | PASS | Cycle scope = C1 (formula-engine `col`-shadowing fix), per `remediation-inputs.2026-06-05T23-23.md`. |
| **Read existing change plans** | PASS | `remediation-plan.2026-06-05T23-23.md` executed; phase-0 policy-read evidence present (`evidence/remediation-baseline/phase0-instructions-read.2026-06-05T23-23.md`). |
| **Document the plan** | PASS | Remediation plan + evidence tree under canonical paths. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | PASS | The fix reorders the symbol-table construction so whitelisted callables bind last; no new abstraction introduced. |
| **Reusability** | PASS | The fix makes `_build_symtable` robust for every column name without special-casing. |
| **Extensibility** | PASS | No public API signature change; `validate()` requires no change (its `allowed_names` already covers the alias set). |
| **Separation of concerns** | PASS | The change is confined to one private method; the `col` accessor still reads from the closed-over context. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | PASS | The fix lives in the owning formula-engine module. |
| **Under 500 lines** | PASS | `src/schema_formula.py` = 315 lines; `tests/test_schema_formula.py` = 379 lines; no `.py` file in the branch diff over 500 lines. |
| **Public vs internal** | PASS | `_build_symtable` is an internal `_`-prefixed method; its docstring was updated to document the bind-last ordering. |
| **No circular dependencies** | PASS | Pyright passes (0 errors). |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | PASS | snake_case functions; the regression test name describes the behavior. |
| **Docs/docstrings** | PASS | `_build_symtable` Returns docstring updated to state callables bind last and `col("col")` returns the column value; intent comments explain the alias-first / callables-last ordering. |
| **Comment why, not what** | PASS | Inline comments explain the anti-shadowing rationale, not line-by-line narration. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check .` -> `222 files would be left unchanged`, EXIT 0 (reaudit live run at HEAD `a45a987`). |
| **2. Linting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check .` -> `All checks passed!`, EXIT 0. |
| **3. Type checking** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright` -> `0 errors, 0 warnings, 0 informations`, EXIT 0. |
| **4. Testing** | PASS | **Command:** `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch` -> `942 passed, 0 failed`, EXIT 0. |
| **Full toolchain loop** | PASS | All four stages green in a single pass at HEAD `a45a987`; no stage changed files, so no restart required. |
| **Explicit reporting** | PASS | Commands and results documented here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | PASS | Remediation plan + traceability evidence. |
| **Design choices explained** | PASS | The bind-callables-last anti-shadowing approach is documented in `remediation-plan.2026-06-05T23-23.md`. |
| **Update supporting documents** | PASS | spec.md / user-story.md AC unchanged (the cycle changed no feature surface; it fixed a latent engine defect). |
| **Provide next steps** | PASS | This is the final cycle; no further remediation inputs required (blocking_count=0). |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | PASS | `black --check .` EXIT 0, 222 files unchanged. |
| **Linting with Ruff** | PASS | `ruff check .` EXIT 0, all checks passed. |
| **Type checking with Pyright** | PASS | `pyright` 0 errors (strict mode). |
| **Testing with Pytest** | PASS | 942 passed, 0 failed, EXIT 0. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | PASS | `_build_symtable` retains `symtable: dict[str, object]` annotation; no new `Any`. |
| **Dataclasses for value objects** | PASS | Unchanged from prior cycles. |
| **Protocols/ABCs for interfaces** | PASS | Unchanged this cycle. |
| **Avoid utility classes** | PASS | No new utility class; the fix is method-local. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | PASS | `col()` raises a specific `FormulaError` for an unknown column; the whitelisted callables are preserved. |
| **Logging over print** | PASS | No ad-hoc print added. |
| **Invariants at construction** | PASS | Unchanged from prior cycles. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | pytest + pytest-qt (`qtbot`) + Hypothesis. |
| **Coverage expectation** | PASS | Repo-wide 99.06% line / 94.04% branch (>= thresholds); `schema_formula.py` 100% line / 100% branch. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | PASS | One behavior per test; the new regression test asserts the colliding-column round-trip. |
| **Mocking sparingly** | PASS | No mocks; a real `FormulaEvaluator` is exercised. |
| **Organization** | PASS | The regression test is placed in `tests/test_schema_formula.py` mirroring `src/schema_formula.py`; no test file exceeds 500 lines. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | PASS | Descriptive `test_*` name. |
| **Docstrings/comments** | PASS | The regression test carries an intent docstring naming C1. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | `pytest --cov --cov-branch` invoked. |
| **No Alternative Test Runners** | PASS | Pytest only. |
| **Suite is green** | PASS | 942 passed, 0 failed, EXIT 0. |

---

## 5. Test Coverage Detail

### C1 — Formula-engine `col`-shadowing fix

| Proof | Test | Status |
|-------|------|--------|
| `col(name)` round-trips for arbitrary column names (Hypothesis) | `tests/test_schema_formula.py::test_property_col_round_trips_values` | PASS (was failing at cycle-3 exit) |
| Columns named `col`/`sum`/`safe_div` round-trip via `col(...)`; helpers not shadowed | `tests/test_schema_formula.py::test_evaluate_column_named_col_round_trips_via_col_callable` | PASS (new regression test) |

Production site: `src/schema_formula.py:301-314` (`_build_symtable` binds the column aliases first, then the whitelisted callables `safe_div`/`sum`/`col` last; the `col` accessor reads from the closed-over `context`).

### B1/B2 (cycle 3) — No regression

| Seam | Production site at HEAD `a45a987` | Status |
|------|----------------------------------|--------|
| B1 blank/whitespace path-or-sheet guard | `src/gui/presenters/source_selection_presenter.py:237` (`if not path.strip() or not sheet.strip()`) | INTACT |
| B2 absent-sheet ValueError contract | `src/gui/services/workbook_reader.py:164-165` (membership check + `raise ValueError`) | INTACT |

### R1–R6 prior production wiring — No regression

| Seam | Production call site | Status |
|------|---------------------|--------|
| `on_partial_match` | `src/gui/app.py:327-349` (`_on_partial_match` passed to three `SourceSelectionPresenter` constructions) | INTACT |
| `BuildSpecProvider` | `src/gui/app.py:430` (`spec_provider=build_spec_provider(_svc)`) | INTACT |
| Columns/Key drag tabs | `src/gui/widgets/schema_builder_dialog.py:98` (`DragTabBinder`) | INTACT |
| `new_from_template` | `src/gui/_schema_open_helpers.py:159` (`presenter.new_from_template(template_name)`) | INTACT |
| Derived dialog | wired via shared open path; surfaces on Columns via `set_derived` | INTACT |

### AC-2 — No regression (auto-select on a real match)

| Proof | Test | Status |
|-------|------|--------|
| `build_application` path auto-selects matched schema and enables Import | `tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables` | PASS |

The cycle-4 commit delta (`cc5b282..a45a987`) touches only `src/schema_formula.py` and `tests/test_schema_formula.py` (plus agent-memory docs), confirming no GUI/schema/migration/wiring file was modified.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 942 | — |
| Tests Passed | 942 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | 21.86s total | PASS (fast) |
| Code Coverage | 99.06% line / 94.04% branch (TOTAL 98%) | PASS |
| Largest changed `.py` file | <= 500 lines (no changed file over cap) | PASS (under cap) |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | 222 files unchanged | PASS |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed | PASS |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors | PASS |
| Pytest Tests | `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch` | 942 passed, 0 failed | PASS |
| Confidentiality masking scan | grep over `cc5b282..a45a987` changed lines for secrets/PII/real values | NO_CONFIDENTIAL_VALUES | PASS |
| Suppression scan (added lines) | git-diff `cc5b282..a45a987` grep `noqa\|type: ignore\|pyright: ignore\|pragma: no cover\|skip\|xfail` (code files) | NO_SUPPRESSIONS_ADDED | PASS |
| File-size gate | scan over all changed `.py` files in `main...HEAD` for >500 lines | NO_FILE_OVER_500 | PASS |
| Workflow change scan | git-diff `main...HEAD` for `.github/workflows/**` and `scripts/benchmarks/**` | NO_WORKFLOW_CHANGES, NO_BENCHMARK_CHANGES | PASS |

**Notes:** No `.github/workflows/**` or `scripts/benchmarks/**` change is present across the whole feature diff, so `modified-workflow-needs-green-run` and the benchmark-baseline provenance rule do not apply. All quality gates pass.

---

## 8. Gaps and Exceptions

### Identified Gaps

**None.** The single cycle-entry blocking finding (C1, the pre-existing `col`-shadowing defect) is closed. The full toolchain is green, coverage holds, no file exceeds 500 lines, the masking scan is clean, and no unauthorized suppressions were added.

### Approved Exceptions

**None.**

### Removed/Skipped Tests

**None.** No skip/xfail introduced. The previously-failing property test now passes legitimately; the new regression test was added.

---

## 9. Summary of Changes

### Commits in This PR/Branch

- HEAD `a45a987` — remediation cycle 4 (C1: prevent column names from shadowing whitelisted helpers). Prior cycle head was `cc5b282`; feature merge-base `5e659f2`.

### Files Modified This Cycle (`cc5b282..a45a987`, excluding docs/memory)

1. `src/schema_formula.py` (MODIFIED) — `_build_symtable` binds column aliases first, then whitelisted callables (`safe_div`/`sum`/`col`) last; docstring/inline comments updated (C1).
2. `tests/test_schema_formula.py` (MODIFIED) — added `test_evaluate_column_named_col_round_trips_via_col_callable` regression test (C1).

No production source outside `src/schema_formula.py`, no workflow, and no benchmark files changed this cycle.

---

## 10. Compliance Verdict

### Overall Status: COMPLIANT (0 BLOCKING) — cycle-4 C1 closed; full toolchain green; all prior work preserved

C1 is closed at HEAD `a45a987` with a now-passing property test plus a new regression test. The full Python toolchain (Black/Ruff/Pyright/Pytest) is green in a single pass, all 38 acceptance criteria are satisfied and backed by passing tests, prior B1/B2 guards and R1–R6 wiring are intact, coverage holds (99.06% line / 94.04% branch), no `.py` file exceeds 500 lines, the masking scan is clean, and no workflow/benchmark files changed.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure (all changed `.py` <= 500)
- PASS Naming, Docs, Comments
- PASS Toolchain Execution (all four stages green)
- PASS Summarize & Document

#### Language-Specific Code Change Policy (Section 3) — Python
- PASS Tooling & Baseline (format/lint/type-check)
- PASS Python Design & Typing
- PASS Error Handling

#### General Unit Test Policy (Section 1)
- PASS Core Principles
- PASS Coverage & Scenarios
- PASS Test Structure
- PASS External Dependencies
- PASS Policy Audit

#### Language-Specific Unit Test Policy (Section 4) — Python
- PASS Framework & Scope
- PASS Test Style & Structure
- PASS Naming & Readability
- PASS Toolchain (suite green)

### Metrics Summary

- 942/942 tests passing; 0 failing
- 99.06% line coverage, 94.04% branch coverage (>= 85% / >= 75%); `schema_formula.py` 100% line / 100% branch
- Black / Ruff / Pyright all clean at HEAD `a45a987`
- Masking scan clean; no suppressions added in cycle 4; no workflow/benchmark change
- All changed `.py` files <= 500 lines

### Recommendation

**Ready for merge.** All cycle-entry blocking findings are closed and the full toolchain is green at HEAD `a45a987`. The remediation loop exit condition is met (blocking_count=0); this is the final cycle.

---

## Appendix A: Test Inventory

Cycle-4 proof tests:

- tests/test_schema_formula.py::test_property_col_round_trips_values (C1, Hypothesis property test — now passing)
- tests/test_schema_formula.py::test_evaluate_column_named_col_round_trips_via_col_callable (C1, new regression test)

No regression of prior proof tests (full suite: 942 tests, 942 pass / 0 fail):

- tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables (AC-2, integration)
- tests/gui/test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader (B1, wiring-level)
- tests/gui/test_workbook_reader.py::test_read_sheet_preview_unknown_sheet_raises_value_error (B2, reader)

## Appendix B: Toolchain Commands Reference

```bash
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing
```

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-05
**Policy Version:** Current (as of audit date)
