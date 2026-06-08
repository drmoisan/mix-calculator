# Policy Compliance Audit: loader-header-row-detection (Issue #55)

**Audit Date:** 2026-06-06
**Code Under Test:** `src/_header_detection.py` (new), `src/load_aop.py`, `src/normalize_le.py`, `src/pandas_io.py`, `tests/test_header_detection.py` (new), `tests/test_normalize_le_header.py` (new), `tests/test_load_aop_header.py` (new), `tests/le_fixtures.py`, `tests/aop_fixtures.py`. Markdown scoping/evidence docs under `docs/features/active/2026-06-06-loader-header-row-detection-55/` and agent-memory notes are non-code.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 9 files | 976 tests | ✅ 976 pass, 0 fail | 98% lines, 94.1% branch | 98% lines, 93.9% branch | 97-100% (4 in-scope modules; 0 missed changed stmts) |

**Note:** No PowerShell, TypeScript, C#, Bash, or JSON files are changed in the branch diff (`git diff main...HEAD`). Those languages have zero changed files and are therefore N/A.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - no TypeScript files changed`
- TypeScript post-change coverage artifact: `N/A - no TypeScript files changed`
- PowerShell baseline coverage artifact: `N/A - no PowerShell files changed`
- PowerShell post-change coverage artifact: `N/A - no PowerShell files changed`
- Per-language comparison summary: see section 1.2.1 below and `docs/features/active/2026-06-06-loader-header-row-detection-55/evidence/qa-gates/coverage-delta.md`

**Non-negotiable verdict rule:** This audit reports PASS and includes numeric baseline and post-change coverage metrics for Python (the only language with changed files), plus changed-code coverage.

---

## Executive Summary

Issue #55 replaces the hardcoded `read_excel_sheet(..., header=2)` in the LE and AOP loaders with deterministic header-row detection (`src/_header_detection.detect_header_row`). The change is Python-only, single-commit (`721a1bf`), against base `main` (merge-base `b655d81`). All eight acceptance criteria (AC-1..AC-8) are satisfied by the diff and tests. The toolchain was re-run independently during this audit: Black clean, Ruff 0 findings, Pyright 0 errors on the four changed `src` modules, and 63 detection + parity tests pass. The executor's full-suite evidence reports 976 passed and 98% line / ~93.9% branch coverage with zero missed changed statements.

No blocking or partial findings were identified. No suppressions were introduced. No `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` paths were modified, so the `modified-workflow-needs-green-run` rule does not fire. All changed files are at or under the 500-line cap.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A `powershell.md` (no PowerShell files changed)
- N/A Bash (no Bash files changed)
- N/A JSON (no governed JSON files changed)

**Temporary artifacts cleanup:**
- ✅ No temporary or one-time scripts were created in source; the change adds one production module and three test modules.
- ✅ No throwaway scripts remain.
- No development scripts were created that require disposition.

---

## Rejected Scope Narrowing

None. The caller prompt explicitly imposed no scope narrowing ("record any attempted scope narrowing under the appropriate section (none is being imposed here)"). The audit scope is the full branch diff of `fix/loader-header-row-detection` (HEAD `721a1bf`) against `main` (merge-base `b655d81`).

---

## Evidence Location Compliance

A `git diff main...HEAD --name-only` scan for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned no matches. All executor evidence is written to the canonical `<FEATURE>/evidence/<kind>/` path (`docs/features/active/2026-06-06-loader-header-row-detection-55/evidence/{baseline,qa-gates,regression-testing,issue-updates}/`). The repository's `scripts/validate_evidence_locations.py` is absent (see agent memory); the git-diff scan is the substitute and reports zero violations. No evidence-location override was required.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | Each test builds its own in-memory `BytesIO` workbook via `_build_sheet`/`build_workbook`/`build_aop_workbook`; no shared mutable state. The rewind test (`test_bytesio_rewind_makes_repeated_calls_deterministic`) deliberately reuses one buffer within a single test, not across tests. |
| **Isolation** - Each test targets single behavior | ✅ PASS | `test_header_detection.py` has six tests each asserting one detection behavior (index 0, index 2, index 3, no-match raises, threshold guard, rewind determinism). The two sibling parity modules each have one resolve test and one parity-equality test. |
| **Fast Execution** - Tests complete quickly | ✅ PASS | The detection + parity subset (63 tests) ran in 4.69s during this audit. |
| **Determinism** - Consistent results | ✅ PASS | No wall-clock, randomness, network, or temp files. Detection is deterministic (topmost-highest with strict `>`). BytesIO rewind makes repeated calls deterministic, asserted by a dedicated test. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive `test_...` names, Arrange-Act-Assert comments, and module docstrings explaining intent. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | **Baseline (pre-development):** 98% lines, 94.1% branch (4725 stmts, 44 missed; 872 branch, 51 partial)<br>**Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing`<br>**Source:** `evidence/baseline/pytest-baseline.md`, `evidence/qa-gates/coverage-delta.md` |
| **No Coverage Regression** | ✅ PASS | **Post-change coverage:** 98% lines, ~93.9% branch (4761 stmts, 44 missed; 884 branch, 54 partial)<br>**Change:** line 98%→98% (no regression); branch ~94.1%→~93.9% (above the 75% floor; three intentionally untested arms of the new path/non-seekable rewind guard). Zero missed statements across all four in-scope modules. |
| **New Code Coverage** | ✅ PASS | **New module** `src/_header_detection.py`: 97% line (sole partial `69->exit` is the non-seekable/path arm of `_rewind_if_seekable`, never exercised because unit tests use BytesIO). Above the 85% line / 75% branch uniform threshold. |
| **Comprehensive Coverage** | ✅ PASS | `detect_header_row` (lines 73-158): 6 unit tests covering positive (index 0/2/3), negative (no-match raises), edge (coincidental-token threshold guard), determinism (rewind). Wiring covered by the four parity/resolve tests plus the pre-existing 53 LE/AOP loader tests. |
| **Positive Flows** - Valid inputs | ✅ PASS | `test_detects_header_at_index_zero`, `test_detects_header_at_index_two`, `test_detects_header_at_index_three`; `test_flat_sheet_header_at_index_zero_resolves_columns` (LE + AOP). |
| **Negative Flows** - Invalid inputs | ✅ PASS | `test_no_qualifying_row_raises_value_error_naming_sheet_and_columns` asserts ValueError naming sheet and a normalized expected column. |
| **Edge Cases** - Boundary conditions | ✅ PASS | `test_data_row_with_few_coincidental_tokens_below_threshold_not_selected` (score 2 < floor 5 → raises). Topmost-highest tie behavior validated by the index-2 and rewind tests. |
| **Error Handling** - Error paths | ✅ PASS | The ValueError path is asserted both for content (sheet + columns named) and behavior (raises). |
| **Concurrency** - If applicable | N/A | No concurrency in the detection or loader read path. |
| **State Transitions** - If applicable | N/A | No stateful component; detection is a pure scan over a probe frame plus a buffer rewind side effect. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98% line / 94.1% branch -> Post-change: 98% line / 93.9% branch. Change: +0.0% line / -0.2% branch (no regression; branch movement is the new path/non-seekable rewind guard arms, far above the 75% floor). New/changed-code coverage: 97-100% across the four in-scope modules (`_header_detection.py` 97% line; `pandas_io.py` 100%; `normalize_le.py` 99%; `load_aop.py` 99%), with 0 missed changed statements. Disposition: PASS. Evidence: `docs/features/active/2026-06-06-loader-header-row-detection-55/evidence/qa-gates/coverage-delta.md`, `evidence/baseline/pytest-baseline.md`, `evidence/qa-gates/final-pytest.md`.
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A (zero changed files). Evidence: N/A - no TypeScript files changed.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A (zero changed files). Evidence: N/A - no PowerShell files changed.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Behavioral assertions (`assert detected == 0`, `pd.testing.assert_frame_equal`) and substring assertions on the ValueError message produce actionable diagnostics. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Every test is explicitly commented with Arrange / Act / Assert sections. |
| **Document Intent** | ✅ PASS | Descriptive test names plus per-test docstrings stating the scenario and expected outcome. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No network, DB, or external process. Workbooks are built in-memory with openpyxl. |
| **Use Mocks/Stubs** | ✅ PASS | No mocks needed; real pure code paths over in-memory buffers are exercised (preferred per policy). |
| **Environment Stability** | ✅ PASS | No temp files (module docstrings explicitly state in-memory BytesIO, no disk), no mutable global state, no env config. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required policy review for issue #55. No outstanding items. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Objective stated in `issue.md`/`spec.md` (#55): replace hardcoded header=2 with detection. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-06T22-16.md` present; `evidence/baseline/phase0-instructions-read.md` records policy review. |
| **Document the plan** | ✅ PASS | Plan file plus spec "Proposed Fix"/"Outcome" sections document the approach. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | A single deterministic scan-and-score helper; no indirection beyond the existing `pandas_io` boundary. |
| **Reusability** | ✅ PASS | One shared `detect_header_row` consumed by both loaders (AC-3), avoiding copy-paste. |
| **Extensibility** | ✅ PASS | Keyword-only `max_rows`/`min_match` with a default constant; callers supply per-sheet thresholds. |
| **Separation of concerns** | ✅ PASS | Detection (pure scan) is separated from I/O (read routed through the typed `pandas_io` boundary); loaders keep their transform logic unchanged. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | `_header_detection.py` has one purpose (locate the header row); the `_`-prefix marks it internal. |
| **Under 500 lines** | ✅ PASS | Independently re-counted with `wc -l`: `_header_detection.py` 158, `load_aop.py` 416, `normalize_le.py` 470, `pandas_io.py` 172, `aop_fixtures.py` 317, `le_fixtures.py` 353, `test_header_detection.py` 167, `test_load_aop_header.py` 59, `test_normalize_le_header.py` 59. Largest touched pre-existing test files remain under cap (`test_normalize_le.py` 446, `test_load_aop.py` 494). |
| **Public vs internal** | ✅ PASS | The detection module is `_`-prefixed internal; only `detect_header_row` is imported by the loaders. |
| **No circular dependencies** | ✅ PASS | `_header_detection` imports `etl_columns` and `pandas_io` only; loaders import `_header_detection`. No cycle. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `detect_header_row`, `expected_tokens`, `min_match`, `_rewind_if_seekable` are descriptive and follow snake_case. |
| **Docs/docstrings** | ✅ PASS | Module, function, and helper docstrings include Args/Returns/Raises/Side effects per the commenting policy. Loader docstrings updated to describe detection. |
| **Comment why, not what** | ✅ PASS | Inline comments explain rationale (e.g., why buffers are rewound, why `min_match` clears the 12 month tokens, why the strict `>` resolves ties to the topmost row). |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | **Command:** `poetry run black --check src/ tests/`<br>**Result (this audit):** 227 files unchanged, exit 0. |
| **2. Linting** | ✅ PASS | **Command:** `poetry run ruff check src/ tests/`<br>**Result (this audit):** All checks passed, exit 0. |
| **3. Type checking** | ✅ PASS | **Command:** `poetry run pyright src/_header_detection.py src/load_aop.py src/normalize_le.py src/pandas_io.py`<br>**Result (this audit):** 0 errors, 0 warnings. |
| **4. Testing** | ✅ PASS | **Command:** `poetry run pytest tests/test_header_detection.py tests/test_normalize_le_header.py tests/test_load_aop_header.py tests/test_normalize_le.py tests/test_load_aop.py -q`<br>**Result (this audit):** 63 passed. Executor full suite: 976 passed (`evidence/qa-gates/final-pytest.md`). |
| **Full toolchain loop** | ✅ PASS | All four stages pass in a single pass per executor `final-*` evidence and re-verified here. |
| **Explicit reporting** | ✅ PASS | Commands and results documented in this audit and executor evidence. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `721a1bf` message and spec "Outcome" summarize the change. |
| **Design choices explained** | ✅ PASS | spec "Proposed Fix" explains the two-read probe, scoring, and threshold rationale. |
| **Update supporting documents** | ✅ PASS | `issue.md`/`spec.md` AC checkboxes checked; `spec.md` "Outcome" section added. |
| **Provide next steps** | ✅ PASS | spec "Rollout & Follow-up" notes a non-scope follow-up (schema header_row reconciliation). |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check src/ tests/` exit 0 (this audit). |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check src/ tests/` exit 0 (this audit). |
| **Type checking with Pyright** | ✅ PASS | `poetry run pyright` on the four changed src modules: 0 errors (this audit). |
| **Testing with Pytest** | ✅ PASS | 63 detection/parity tests pass (this audit); 976 full suite (executor). |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | Full annotations: `detect_header_row(source: ExcelSource, sheet_name: str, expected_tokens: frozenset[str], *, max_rows: int = ..., min_match: int) -> int`. `read_excel_sheet` widened to `header: int | None` (function and Protocol). No `Any`. |
| **Dataclasses for value objects** | N/A | No value object introduced; the helper is a pure function. |
| **Protocols/ABCs for interfaces** | ✅ PASS | The existing `_PandasReaders` Protocol in `pandas_io.py` was updated in lockstep with the function signature. |
| **Avoid utility classes** | ✅ PASS | Detection is a module-level function, not a static-method utility class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | Raises `ValueError` naming the sheet, scan window, floor, and expected columns; no broad catch. Fails fast (no silent fallback to header=2). |
| **Logging over print** | ✅ PASS | The detection module emits no logging or print (documented); loaders retain their existing `logging` usage. |
| **Invariants at construction** | N/A | No class constructor; the floor invariant is enforced at the point of selection. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | All new tests use Pytest (`pytest.raises`, plain `assert`). |
| **Coverage expectation** | ✅ PASS | New module 97% line; repo-wide 98% line / 93.9% branch; >= 85% line / 75% uniform threshold met. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | No mocks; real openpyxl reads over in-memory buffers. |
| **Organization** | ✅ PASS | `test_header_detection.py` mirrors `src/_header_detection.py`; sibling header modules mirror the loaders, split out to keep the pre-existing files under 500 lines. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_...` names stating scenario and outcome. |
| **Docstrings/comments** | ✅ PASS | Per-test docstrings and AAA comments. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest ... -q` → 63 passed (this audit). |
| **No Alternative Test Runners** | ✅ PASS | Only Pytest is used. |

---

## 5. Test Coverage Detail

### detect_header_row (6 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| test_detects_header_at_index_zero | Positive | 119-146, 158 | ✅ |
| test_detects_header_at_index_two | Positive | 119-146, 158 | ✅ |
| test_detects_header_at_index_three | Positive (3 leading rows) | 119-146, 158 | ✅ |
| test_no_qualifying_row_raises_value_error_naming_sheet_and_columns | Negative / Error | 150-156 | ✅ |
| test_data_row_with_few_coincidental_tokens_below_threshold_not_selected | Edge (threshold guard) | 136-156 | ✅ |
| test_bytesio_rewind_makes_repeated_calls_deterministic | Determinism | 50-71, 119-146 | ✅ |

**Coverage:** 97% of `_header_detection.py`. Sole partial `69->exit` is the path/non-seekable arm of `_rewind_if_seekable` (unit tests use BytesIO).

### Loader wiring (4 parity/resolve tests + 53 pre-existing)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_flat_sheet_header_at_index_zero_resolves_columns (LE) | Positive (index 0) | ✅ |
| test_flat_sheet_load_equals_standard_header_at_index_two (LE) | Parity | ✅ |
| test_flat_sheet_header_at_index_zero_resolves_columns (AOP) | Positive (index 0) | ✅ |
| test_flat_sheet_load_equals_standard_header_at_index_two (AOP) | Parity | ✅ |
| existing test_normalize_le.py + test_load_aop.py (53) | Parity at index 2 | ✅ |

**Not covered:** the path-source non-rewind arms in `normalize_le.py` (`157->162`) and `load_aop.py` (`199->204`, pre-existing). No changed statement is missed.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests (full suite) | 976 | ✅ |
| Tests Passed | 976 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time (detection+parity subset, this audit) | 4.69s | ✅ Fast |
| Functions/Classes Tested (in-scope) | detect_header_row + both loaders + read_excel_sheet | ✅ |
| Test File Size | all <= 167 lines (new); 446/494 (pre-existing) | ✅ Maintainable |
| Code Coverage | 98% lines, ~93.9% branches | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check src/ tests/` | 227 files unchanged, exit 0 | ✅ |
| Ruff Linting | `poetry run ruff check src/ tests/` | All checks passed, exit 0 | ✅ |
| Pyright Type Checking | `poetry run pyright src/_header_detection.py src/load_aop.py src/normalize_le.py src/pandas_io.py` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `poetry run pytest tests/test_header_detection.py tests/test_*_header.py tests/test_normalize_le.py tests/test_load_aop.py -q` | 63 passed | ✅ |

**Notes:**
No pre-existing failures observed. Suppression scan (`git diff main...HEAD` over `*.py` for `noqa`/`type: ignore`/`pyright: ignore`) returned no matches; no suppressions to authorize against `python-suppressions.md`.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements are met. PR-context artifacts (`artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`, dated 2026-06-01) predate the branch HEAD and are stale relative to this single-commit branch; the audit used the authoritative `git diff main...HEAD` and `git log main..HEAD` as the evidence source per the scope invariant. This staleness does not affect any verdict and is not a policy gap.

### Approved Exceptions
**None.** No exceptions needed.

### Removed/Skipped Tests
**None.** All planned tests implemented; +10 tests added (966 → 976).

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. **721a1bf** - fix(loader): detect the LE/AOP header row instead of hardcoding header=2 (#55)

### Files Modified

1. **src/_header_detection.py** (NEW) - `detect_header_row` two-read probe (`header=None`), normalized-token scoring, topmost-highest selection with `min_match` floor, BytesIO rewind; deterministic.
2. **src/normalize_le.py** (MODIFIED) - wires detection (`min_match=20` of 25 LE tokens), rewinds seekable buffer, reads with detected index; docstring updated.
3. **src/load_aop.py** (MODIFIED) - wires detection (`min_match=17` of 24 AOP tokens), rewinds seekable buffer, reads with detected index; docstring updated.
4. **src/pandas_io.py** (MODIFIED) - `read_excel_sheet` and `_PandasReaders` Protocol widened to `header: int | None`.
5. **tests/test_header_detection.py** (NEW) - 6 unit tests.
6. **tests/test_normalize_le_header.py** (NEW) - LE flat-sheet resolve + parity.
7. **tests/test_load_aop_header.py** (NEW) - AOP flat-sheet resolve + parity.
8. **tests/le_fixtures.py / tests/aop_fixtures.py** (MODIFIED) - added keyword `leading_rows` param (default 2) for flat-workbook builds; backward-compatible.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

All cross-language and Python-specific code-change and unit-test policies are satisfied. AC-1..AC-8 PASS. Toolchain clean on independent re-run. No suppressions, no workflow changes, all files under the 500-line cap, coverage at/above thresholds with no regression on changed lines.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes: documented plan and policy read
- ✅ Design Principles: simple, reusable shared helper, separated I/O
- ✅ Module & File Structure: all files <= 500 lines, no cycles
- ✅ Naming, Docs, Comments: descriptive, rationale comments
- ✅ Toolchain Execution: clean single pass
- ✅ Summarize & Document: spec Outcome + AC check-off

#### Language-Specific Code Change Policy (Section 3)

**For Python:**
- ✅ Tooling & Baseline: Black/Ruff/Pyright clean
- ✅ Python Design & Typing: fully typed, Protocol updated in lockstep
- ✅ Error Handling: specific ValueError, fail-fast

#### General Unit Test Policy (Section 1)
- ✅ Core Principles
- ✅ Coverage & Scenarios
- ✅ Test Structure
- ✅ External Dependencies (in-memory only, no temp files)
- ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4)

**For Python:**
- ✅ Framework & Scope
- ✅ Test Style & Structure
- ✅ Naming & Readability
- ✅ Toolchain

---

### Metrics Summary

- ✅ 976/976 tests passing (100%)
- ✅ 98% line coverage, ~93.9% branch coverage
- ✅ New module 97% line; 0 missed changed statements across 4 in-scope modules
- ✅ All files <= 500 lines
- ✅ All code-quality checks passing (re-verified this audit)

---

### Recommendation

**Ready for merge.** No blocking or partial findings. Exit-gate count (FAIL + blocking-PARTIAL) is 0.

---

## Appendix A: Test Inventory

- tests/test_header_detection.py::test_detects_header_at_index_zero
- tests/test_header_detection.py::test_detects_header_at_index_two
- tests/test_header_detection.py::test_detects_header_at_index_three
- tests/test_header_detection.py::test_no_qualifying_row_raises_value_error_naming_sheet_and_columns
- tests/test_header_detection.py::test_data_row_with_few_coincidental_tokens_below_threshold_not_selected
- tests/test_header_detection.py::test_bytesio_rewind_makes_repeated_calls_deterministic
- tests/test_normalize_le_header.py::test_flat_sheet_header_at_index_zero_resolves_columns
- tests/test_normalize_le_header.py::test_flat_sheet_load_equals_standard_header_at_index_two
- tests/test_load_aop_header.py::test_flat_sheet_header_at_index_zero_resolves_columns
- tests/test_load_aop_header.py::test_flat_sheet_load_equals_standard_header_at_index_two

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
poetry run black --check src/ tests/

# Linting
poetry run ruff check src/ tests/

# Type checking
poetry run pyright src/_header_detection.py src/load_aop.py src/normalize_le.py src/pandas_io.py

# Testing (subset re-verified this audit)
poetry run pytest tests/test_header_detection.py tests/test_normalize_le_header.py tests/test_load_aop_header.py tests/test_normalize_le.py tests/test_load_aop.py -q

# Coverage (executor full-suite evidence)
poetry run pytest --cov --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent (Claude)
**Audit Date:** 2026-06-06
**Policy Version:** Current (as of audit date)
