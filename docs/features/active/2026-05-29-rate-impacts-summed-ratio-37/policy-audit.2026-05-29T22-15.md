# Policy Compliance Audit: rate-impacts-summed-ratio (Issue #37)

**Audit Date:** 2026-05-29
**Code Under Test:** `src/mix_rate_impacts.py` (MODIFIED), `tests/test_mix_rate_impacts.py` (MODIFIED)

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 2 files | 7 tests (file) / 510 tests (suite) | ✅ 510 pass, 0 fail | 99% lines, ~98.9% branch | 99% lines, ~98.9% branch | 100% lines (43/43 on `src/mix_rate_impacts.py`) |

**Note:** No TypeScript, PowerShell, C#, Bash, or JSON files changed on this branch; coverage verdicts for those languages are N/A because they have zero changed files in the branch diff.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope`
- TypeScript post-change coverage artifact: `N/A - out of scope`
- PowerShell baseline coverage artifact: `N/A - out of scope`
- PowerShell post-change coverage artifact: `N/A - out of scope`
- Per-language comparison summary: see Section 1.2.1 and `artifacts/python/lcov.info`

**Non-negotiable verdict rule:** This audit reports PASS only because it includes numeric baseline and post-change coverage metrics for the single in-scope language (Python), plus changed-code coverage.

**Fail-closed rule:** All required baseline, QA, and coverage-comparison artifacts are present (see Appendix B). No fail-closed condition is triggered.

---

## Executive Summary

This is a minor-audit bugfix for issue #37. `build_rate_impacts` previously read the carried/summed per-unit and %GS ratio columns (`Net Rev Per Lb - Diff`, `Gross Sales Per Lb - Diff`, `OI/Trade/Non-Trade %GS - AOP/Diff`) produced by `stack_pivot` with `aggfunc="sum"`. Summing a ratio across split sub-rows is mathematically invalid, so a SKU split across fine-grain groups (a deduction sub-row carrying dollars with zero volume) could collapse the carried ratio to zero and misclassify rate movement as mix. The fix recomputes those metrics at the `{Customer, SKU #}` grain from the additive dollar/volume wide columns, using a local `_guarded_div` helper whose `den > 0` semantics match `calc_ratios`/`_safe_div`. The six impact formulas (`RATE_IMPACT_COLUMNS`) are structurally unchanged; only their ratio inputs were re-sourced.

The full Python toolchain (Black, Ruff, Pyright, Pytest) was re-run independently during this review and passed. Changed-file coverage is 100% line. The change is scoped to one production file plus its test file.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md` + `self-explanatory-code-commenting.md`
- N/A `powershell.md`
- N/A Bash
- N/A JSON

**Temporary artifacts cleanup:**
- ✅ No temporary or throwaway scripts were created during this review.
- ✅ No ongoing tooling scripts were added.
- No scripts were created during development of this audit.

---

## Rejected Scope Narrowing

None. The caller prompt directed a full feature-vs-base audit and explicitly instructed the reviewer to determine scope from the branch diff per the scope invariant. No instruction attempted to narrow scope to a plan/task/phase, limit to a file subset, or mark any in-scope language as out of scope. The audit scope is the full branch diff `ae52c3f..9fffb6b` against base `main`.

---

## Evidence Location Compliance

A git-diff scan was used in place of `scripts/validate_evidence_locations.py`, which does not exist in this repository (only the PowerShell PreToolUse hook `enforce-evidence-locations.ps1` is present). Command:

```
git diff --name-only ae52c3f48f6233a91b6613ceb1c390c291a0a6db..9fffb6b82366407dae6207faaae15ee28ff1447d -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'
```

Result: zero matches. All feature evidence is written under the canonical `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/<kind>/` path. No non-canonical evidence-location violations were found.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | Each test builds its own fixture via `_aop_vs_le_fixture`/`_zero_volume_deduction_fixture`; no shared mutable state or ordering dependency. |
| **Isolation** - Each test targets single behavior | ✅ PASS | Seven tests each assert one behavior: filtering, six derived columns, column presence, zero-volume regression, single-SKU rollup, single-fine-grain preservation, SKU enrichment. |
| **Fast Execution** - Tests complete quickly | ✅ PASS | `tests/test_mix_rate_impacts.py` ran in 0.50s (7 tests); full suite 22.41s. |
| **Determinism** - Consistent results | ✅ PASS | Pure in-memory DataFrame fixtures; no clock, RNG, network, or filesystem I/O. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive `test_*` names, Arrange-Act-Assert structure, docstrings naming the AC each test maps to. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | **Baseline:** 99% lines, ~98.9% branch; `src/mix_rate_impacts.py` 100% (21 stmts). **Command:** `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`. **Timestamp:** 2026-05-29 21:59. Source: `evidence/baseline/pytest-coverage.2026-05-29T21-59.md`. |
| **No Coverage Regression** | ✅ PASS | **Post-change:** 99% lines, ~98.9% branch. **Change:** 0% lines, 0% branch. **Status:** No regression. `src/mix_rate_impacts.py` remained 100% line (21 -> 43 stmts, 0 missed). |
| **New Code Coverage ≥85%** | ✅ PASS | **Modified file** `src/mix_rate_impacts.py`: 43/43 statements covered = 100% line (lcov `LF:43`, `LH:43` in `artifacts/python/lcov.info`). Uniform threshold per quality-tiers.md is ≥85% line / ≥75% branch. |
| **Comprehensive Coverage** | ✅ PASS | `build_rate_impacts` and `_guarded_div` are exercised by all seven tests; the recompute block and guard branch (`den > 0` true and false) are covered by the zero-volume fixture (`Lbs - AOP = 0`, `Gross Sales = 0` sub-rows). |
| **Positive Flows** - Valid inputs | ✅ PASS | `test_build_rate_impacts_derived_columns_match_hand_computed`, `test_single_fine_grain_recompute_equals_carried_ratio`. Total positive tests: 4. |
| **Negative Flows** - Invalid inputs | ✅ PASS | `test_build_rate_impacts_filters_non_normal_rows` (non-normal lines filtered). The function's contract has no user-facing validation path; invalid-denominator handling is covered under Edge Cases. Total negative tests: 1. |
| **Edge Cases** - Boundary conditions | ✅ PASS | `test_zero_volume_deduction_yields_dollar_derived_net_price_impact` exercises the zero-denominator guard (`Lbs = 0`, `Gross Sales = 0`). Total edge case tests: 1. |
| **Error Handling** - Error paths | ✅ PASS | The zero/non-positive-denominator path returns `0.0` rather than raising/`inf`/`NaN`; asserted via the zero-volume regression test. |
| **Concurrency** - If applicable | N/A | Pure synchronous transform; no concurrency. |
| **State Transitions** - If applicable | N/A | Stateless function; no state machine. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99% line / 98.9% branch (repo-wide); `src/mix_rate_impacts.py` 100% line. Post-change: 99% line / 98.9% branch (repo-wide); `src/mix_rate_impacts.py` 100% line. Change: no regression (0% delta repo-wide; changed file held at 100% line as statements grew 21 -> 43). New/changed-code coverage: 100% line / N/A branch (0 branches in the module). Disposition: PASS. Evidence: `artifacts/python/lcov.info` (`SF:src\mix_rate_impacts.py`, `LF:43`, `LH:43`); `evidence/qa-gates/coverage-delta.2026-05-29T21-59.md`; `evidence/qa-gates/pytest-coverage.2026-05-29T21-59.md`.
- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no TypeScript files changed on this branch.
- PowerShell: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no PowerShell files changed on this branch.

### 1.2.2 Coverage Comparison Scan Terminator

This heading terminates the per-language comparison-line scan.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Tolerance-based asserts (`abs(... ) < 1e-9`) on named columns; a failure identifies the specific impact column and expected value. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | All seven tests use explicit `# Arrange` / `# Act` / `# Assert` sections. |
| **Document Intent** | ✅ PASS | Each test carries a docstring stating the scenario and, for the new tests, the AC it maps to. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No databases, networks, APIs, processes, or filesystem access; fixtures are in-memory DataFrames. |
| **Use Mocks/Stubs** | ✅ PASS | No mocks required; the unit is pure and tested against real (synthetic) data. |
| **Environment Stability** | ✅ PASS | No global state, config files, or temporary files. No prohibited temp-file creation. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required policy review for issue #37. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Objective stated in `issue.md` #37 (summed-ratio defect) with AC1–AC6. |
| **Read existing change plans** | ✅ PASS | `plan.2026-05-29T21-59.md` present with phased tasks P0/P1 mapping to ACs. |
| **Document the plan** | ✅ PASS | Plan documented in the feature folder and reflected in commit history. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | A single private helper plus a linear recompute block; no new abstractions or indirection. |
| **Reusability** | ✅ PASS | `_guarded_div` reuses the documented `_safe_div` guard semantics rather than duplicating ad-hoc divide logic across sites. |
| **Extensibility** | ✅ PASS | Recomputed metrics are local variables feeding the existing formula block; adding metrics follows the same pattern. |
| **Separation of concerns** | ✅ PASS | The module remains pure (no I/O); the docstring reiterates that I/O lives in `pandas_io`/`mix_pipeline`. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | The module retains its single purpose: the `build_rate_impacts` transform. |
| **Under 500 lines** | ✅ PASS | `src/mix_rate_impacts.py` = 192 lines; `tests/test_mix_rate_impacts.py` = 319 lines (`wc -l`). |
| **Public vs internal** | ✅ PASS | `__all__` exports only `RATE_IMPACT_COLUMNS` and `build_rate_impacts`; the new helper is `_guarded_div` (underscore-prefixed). |
| **No circular dependencies** | ✅ PASS | Imports `numpy`, `pandas`, and `src.mix_transforms.stack_pivot`; no new module-graph cycle. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `net_rev_per_lb_aop/le/diff`, `oi_pct_*`, etc. are descriptive snake_case. |
| **Docs/docstrings** | ✅ PASS | `_guarded_div` has a full Google-style docstring; `build_rate_impacts` docstring was updated to describe the recompute and the six formulas. |
| **Comment why, not what** | ✅ PASS | The recompute block carries a meta-what/why comment explaining the summed-ratio invalidity; the `np.errstate` line explains why the warning is silenced. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check src/mix_rate_impacts.py tests/test_mix_rate_impacts.py`<br>**Result:** "2 files would be left unchanged." |
| **2. Linting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check src/mix_rate_impacts.py tests/test_mix_rate_impacts.py`<br>**Result:** "All checks passed!" |
| **3. Type checking** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright src/mix_rate_impacts.py`<br>**Result:** 0 errors, 0 warnings, 0 informations. |
| **4. Testing** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py -q`<br>**Result:** 7 passed. Full suite: 510 passed (per `evidence/qa-gates/pytest-coverage.2026-05-29T21-59.md`). |
| **Full toolchain loop** | ✅ PASS | All four stages pass in a single pass; coverage verified from `artifacts/python/lcov.info`. |
| **Explicit reporting** | ✅ PASS | Commands and results recorded here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Summarized in this audit and the accompanying code review. |
| **Design choices explained** | ✅ PASS | The local-`_guarded_div` decision (over re-export or direct private import) is documented in the code comment and plan task P1-T4. |
| **Update supporting documents** | ✅ PASS | `issue.md` ACs checked off; evidence and plan present in the feature folder. |
| **Provide next steps** | ✅ PASS | Recommendation in Section 10 (ready for merge). |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `black --check` reports no changes. |
| **Linting with Ruff** | ✅ PASS | `ruff check` reports all checks passed; no suppressions added (no `# noqa`/`# type: ignore` in the diff). |
| **Type checking with Pyright** | ✅ PASS | 0 errors/0 warnings on the changed file. The change promotes `pandas` from a `TYPE_CHECKING`-only import to a runtime import (now used at runtime by `_guarded_div`), which is correct typing. |
| **Testing with Pytest** | ✅ PASS | 7/7 file tests, 510/510 suite. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | `_guarded_div(num: pd.Series, den: pd.Series) -> pd.Series` is fully annotated; no `Any` introduced. |
| **Dataclasses for value objects** | N/A | No value objects added; the transform operates on DataFrames. |
| **Protocols/ABCs for interfaces** | N/A | Single concrete pure function; no multiple-implementation seam needed. |
| **Avoid utility classes** | ✅ PASS | Logic is module-level functions, not a static-method utility class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | No broad `except`; the guard returns `0.0` for non-positive denominators by design (matching `calc_ratios`). |
| **Logging over print** | ✅ PASS | No `print` statements; the module performs no logging by design (pure transform). |
| **Invariants at construction** | N/A | No class/constructor introduced. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Tests are Pytest functions; no other runner used. |
| **Coverage expectation** | ✅ PASS | Changed file 100% line (≥85% threshold); repo-wide 99% line / ~98.9% branch (≥75% branch threshold). |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test across the seven tests. |
| **Mocking sparingly** | ✅ PASS | No mocks; the unit is pure and tested against synthetic DataFrames. |
| **Organization** | ✅ PASS | `tests/test_mix_rate_impacts.py` mirrors `src/mix_rate_impacts.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_*` names (e.g. `test_zero_volume_deduction_yields_dollar_derived_net_price_impact`). |
| **Docstrings/comments** | ✅ PASS | Each test has a docstring stating the scenario and mapped AC. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py -q`<br>**Result:** 7 passed. |
| **No Alternative Test Runners** | ✅ PASS | Only Pytest is used. |

---

## 5. Test Coverage Detail

### build_rate_impacts / _guarded_div (7 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_build_rate_impacts_filters_non_normal_rows` | Negative | classification filter | ✅ |
| `test_build_rate_impacts_derived_columns_match_hand_computed` | Positive | recompute + six formulas | ✅ |
| `test_build_rate_impacts_includes_all_six_impact_columns` | Positive | column presence | ✅ |
| `test_zero_volume_deduction_yields_dollar_derived_net_price_impact` | Edge Case / Error Handling | `_guarded_div` zero-denominator branch | ✅ |
| `test_single_sku_group_rolls_up_to_category_net_price_impact` | Positive (reconciliation) | net-price rollup | ✅ |
| `test_single_fine_grain_recompute_equals_carried_ratio` | Positive (behavior preservation) | recompute == carried | ✅ |
| `test_build_rate_impacts_enriches_with_sku_lookup` | Positive | SKU lookup merge | ✅ |

**Coverage:** 100% of `src/mix_rate_impacts.py` (43/43 statements; 0 branches).

**Not covered:** None.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests (module) | 7 | ✅ |
| Tests Passed | 7 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time (module) | 0.50s | ✅ Fast |
| Functions Tested | 2/2 (100%) | ✅ |
| Test File Size | 319 lines | ✅ Maintainable |
| Code Coverage | 100% lines, N/A branches (module) | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check ...` | 2 files unchanged | ✅ |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check ...` | All checks passed | ✅ |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright src/mix_rate_impacts.py` | 0 errors/0 warnings | ✅ |
| Pytest Tests | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py -q` | 7 passed | ✅ |

**Notes:** No pre-existing failures observed. The Python coverage artifact `artifacts/python/lcov.info` was inspected directly (not regenerated) and contains the changed module with `LF:43`/`LH:43`.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements applicable to a Python bugfix are met.

### Approved Exceptions
**None.** No exceptions needed.

### Removed/Skipped Tests
**None.** All planned tests are implemented; three regression/reconciliation/behavior tests were added.

---

## 9. Summary of Changes

### Commits in This PR/Branch

Branch range `ae52c3f..9fffb6b`. Core change: recompute per-unit and %GS metrics from additive dollar/volume columns in `build_rate_impacts`; add the seven-test module update.

### Files Modified

1. **`src/mix_rate_impacts.py`** (MODIFIED, +89/-20)
   - Added `_guarded_div` helper (documented `den > 0` guard matching `_safe_div`).
   - Added a recompute block deriving per-Lb and %GS AOP/LE/Diff metrics from additive dollar/volume columns.
   - Re-sourced the six impact formula inputs to the recomputed metrics; formula arithmetic unchanged.
   - Promoted `pandas` import from `TYPE_CHECKING` to runtime; added `numpy` import.

2. **`tests/test_mix_rate_impacts.py`** (MODIFIED, +160/-0)
   - Added the zero-volume-deduction regression fixture and tests for AC3, AC4, AC5.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The change is a focused, well-documented bugfix that recomputes ratio metrics from additive dollars/volume to fix the summed-ratio defect. The full Python toolchain passes, changed-file coverage is 100% line with no repo-wide regression, and both files are within the 500-line limit. No suppressions were introduced and no evidence-location or workflow-modification rules were triggered.

**Fail-closed reminder:** No required artifact is missing; PASS is supported by the present baseline, QA-gate, coverage-delta, and lcov artifacts.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes: plan and issue present.
- ✅ Design Principles: simple, reuses guard semantics, pure.
- ✅ Module & File Structure: 192/319 lines, no cycles.
- ✅ Naming, Docs, Comments: descriptive, why-comments present.
- ✅ Toolchain Execution: all four stages pass.
- ✅ Summarize & Document: ACs checked, evidence present.

#### Language-Specific Code Change Policy (Section 3)
**For Python:**
- ✅ Tooling & Baseline: Black/Ruff/Pyright/Pytest clean.
- ✅ Python Design & Typing: fully typed, no `Any`.
- ✅ Error Handling: guard returns 0.0 by design; no broad catches.

#### General Unit Test Policy (Section 1)
- ✅ Core Principles: independent, isolated, fast, deterministic, readable.
- ✅ Coverage & Scenarios: 100% changed-file line; positive/negative/edge/error covered.
- ✅ Test Structure: AAA, clear diagnostics.
- ✅ External Dependencies: none; in-memory only.
- ✅ Policy Audit: this document.

#### Language-Specific Unit Test Policy (Section 4)
**For Python:**
- ✅ Framework & Scope: Pytest; coverage thresholds met.
- ✅ Test Style & Structure: focused, no mocks needed.
- ✅ Naming & Readability: descriptive `test_*` names with docstrings.
- ✅ Toolchain: Pytest only.

---

### Metrics Summary

- ✅ 510/510 suite tests passing (100%); 7/7 module tests.
- ✅ 2/2 module functions tested (100%).
- ✅ 100% changed-file line coverage; 99% repo-wide line / ~98.9% branch.
- ✅ File organization within 500-line limit (192/319).
- ✅ All code quality checks passing.
- ✅ Module test execution time 0.50s (fast).

---

### Recommendation

**Ready for merge.** No blocking or partial findings. Remediation is not required.

---

## Appendix A: Test Inventory

### Complete Test List

- `tests/test_mix_rate_impacts.py::test_build_rate_impacts_filters_non_normal_rows`
- `tests/test_mix_rate_impacts.py::test_build_rate_impacts_derived_columns_match_hand_computed`
- `tests/test_mix_rate_impacts.py::test_build_rate_impacts_includes_all_six_impact_columns`
- `tests/test_mix_rate_impacts.py::test_zero_volume_deduction_yields_dollar_derived_net_price_impact`
- `tests/test_mix_rate_impacts.py::test_single_sku_group_rolls_up_to_category_net_price_impact`
- `tests/test_mix_rate_impacts.py::test_single_fine_grain_recompute_equals_carried_ratio`
- `tests/test_mix_rate_impacts.py::test_build_rate_impacts_enriches_with_sku_lookup`

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
env -u VIRTUAL_ENV poetry run black --check src/mix_rate_impacts.py tests/test_mix_rate_impacts.py

# Linting
env -u VIRTUAL_ENV poetry run ruff check src/mix_rate_impacts.py tests/test_mix_rate_impacts.py

# Type checking
env -u VIRTUAL_ENV poetry run pyright src/mix_rate_impacts.py

# Testing + coverage (executor run; artifact inspected, not regenerated)
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py -q
```

Coverage artifact inspected: `artifacts/python/lcov.info` (`SF:src\mix_rate_impacts.py`, `LF:43`, `LH:43`).

Evidence-location scan:
```bash
git diff --name-only ae52c3f48f6233a91b6613ceb1c390c291a0a6db..9fffb6b82366407dae6207faaae15ee28ff1447d -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'
```

---

**Audit Completed By:** Claude (feature-review agent)
**Audit Date:** 2026-05-29
**Policy Version:** Current (as of audit date)
