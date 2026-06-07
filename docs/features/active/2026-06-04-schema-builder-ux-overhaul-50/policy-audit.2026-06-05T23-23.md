# Policy Compliance Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 3 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-23
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `cc5b282` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Code Under Test:** full branch diff `main...HEAD` (Python + JSON only). Cycle-3 commit diff is `fd8a022..cc5b282`.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | src + test files | 941 tests | 940 pass, 1 fail | 98% lines, 94.0% branch (cycle-2 baseline) | 98% lines (TOTAL row), ~94% branch | 99–100% (cycle-3 changed modules: `_schema_discovery_wiring.py` 100%, `source_selection_presenter.py` 99%, `workbook_reader.py` 100%) |
| JSON | 2 schema files | N/A | load without error (tests/test_default_schemas.py) | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- TypeScript post-change coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- PowerShell baseline coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- PowerShell post-change coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- Python baseline coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/baseline/pytest.baseline.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T22-30.md`; live re-run by this reaudit at HEAD `cc5b282`
- Per-language comparison summary: see section 1.2.1

**Non-negotiable verdict rule:** numeric baseline and post-change coverage are present for the only in-scope language (Python). JSON has no coverage requirement. Coverage thresholds are met, but the test suite is RED (1 failed) — see the Executive Summary and Gaps section; the RED suite is a BLOCKING toolchain-not-green finding independent of coverage.

---

## Executive Summary

This is the EXIT reaudit of remediation cycle 3 for issue #50. The cycle-entry inputs (`remediation-inputs.2026-06-05T22-30.md`) carried blocking_count=1 (one blocking defect with two coupled gaps): B1 (schema discovery not guarded against a blank/whitespace path or sheet, causing a post-PR runtime crash on tab activation) and B2 (the reader/presenter error-type contract mismatch — `read_sheet_preview` raised `KeyError` for an absent sheet while the presenter catches only `ValueError`, so a stale/blank worksheet crashed discovery).

**Cycle-3 objectives B1 and B2 are met (closed) at HEAD `cc5b282`:**

- **B1 (closed).** `SourceSelectionPresenter.on_schema_discovery` (`src/gui/presenters/source_selection_presenter.py:233-235`) now returns early when `path` or `sheet` is blank/whitespace, before the reader is invoked. `_on_tab_activated` (`src/gui/_schema_discovery_wiring.py:131-138`) applies the same short-circuit as defense in depth. Both methods' docstrings were updated to document the no-op. Proof is wiring-level: `tests/gui/test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader` and `::test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet` drive the real `tab_combo.currentTextChanged` signal over a `MainWindow` wired by `wire_schema_discovery_and_gating`; they assert the reader is never called with a blank sheet, no exception propagates, the dropdown stays on `<Choose Schema>`, and Import stays disabled. These are integration tests against the production signal path, not isolated presenter unit calls.
- **B2 (closed).** `WorkbookReader.read_sheet_preview` (`src/gui/services/workbook_reader.py:164-165`) now checks `sheet_name not in workbook.sheetnames` and raises `ValueError` for an absent/blank sheet, inside the `try` so the `finally` still closes the workbook. The `Raises:` sections of both `WorkbookReaderProtocol.read_sheet_preview` (`workbook_reader.py:78-81`) and `WorkbookReader.read_sheet_preview` (`workbook_reader.py:149-152`) were updated from `KeyError` to `ValueError`. Unit proof: `tests/gui/test_workbook_reader.py::test_read_sheet_preview_unknown_sheet_raises_value_error` and `::test_read_sheet_preview_blank_sheet_name_raises_value_error`. Presenter-routing proof: `tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_stale_sheet_value_error_routes_to_show_error` asserts the `ValueError` reaches `view.show_error` with no crash and no auto-selection.

**No regression of prior work.** AC-2 still auto-selects for a real match: `tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables` builds the real composition root via `build_application`, selects a file and a worksheet, fires the production activation path, and asserts the matched schema is auto-selected and Import is enabled. The cycle-1/cycle-2 production seams remain wired and intact at HEAD (drag Columns/Key tabs, derived dialog, `BuildSpecProvider`, `new_from_template`, `on_partial_match`) — see section 5. The cycle-3 commit diff (`fd8a022..cc5b282`) touches only three production files (`_schema_discovery_wiring.py`, `source_selection_presenter.py`, `workbook_reader.py`), three test files, and docs/memory.

**BLOCKING finding (toolchain not green).** The full test suite is RED at HEAD `cc5b282`: 940 passed, **1 failed** — `tests/test_schema_formula.py::test_property_col_round_trips_values` (line 306). A RED suite is a blocking merge/CI condition regardless of cause. The failure is a **pre-existing, out-of-cycle-3-scope latent defect** in the formula engine, not introduced by B1/B2. Root cause: in `src/schema_formula.py._build_symtable`, the symbol table seeds the whitelisted `col` callable (line 304), then the alias-binding loop at line 306-307 (`symtable[alias] = context[column]`) overwrites `symtable["col"]` with the column value when a source column is literally named `col`. The Hypothesis falsifying example `{'col': 0.0}` therefore makes `col(name)` evaluate `0.0(...)`, producing `TypeError: '0.0' is not callable`. `src/schema_formula.py` and `tests/test_schema_formula.py` are NOT in the `main...HEAD` branch diff (verified: `git diff --stat main...HEAD -- src/schema_formula.py` is empty), so this defect predates the entire feature branch and is attributable to the `col`-shadowing behavior in `src/schema_formula.py:301-307`, not to the cycle-3 B1/B2 changes. It is scoped into the next cycle via `remediation-inputs.2026-06-05T23-23.md`.

Black, Ruff, and Pyright are all green at HEAD `cc5b282` (0 errors). Repo-wide coverage exceeds thresholds (98% line TOTAL, ~94% branch). The masking scan is clean, no unauthorized suppressions were added in cycle 3, no changed `.py` file exceeds 500 lines, and no `.github/workflows/**` or `scripts/benchmarks/**` files changed across the whole feature diff.

**Verdict: PARTIAL (1 BLOCKING).** Cycle-3 B1/B2 objectives are met independent of the pre-existing failure; the RED suite (pre-existing `col`-shadowing defect) is the single remaining blocking finding.

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

None. The caller prompt directed a full branch-vs-base audit and did not attempt to narrow scope to any plan, task, phase, or file subset. The audit scope is the full `main...HEAD` diff; the cycle-3 commit diff (`fd8a022..cc5b282`) is the delta under remediation review. The caller's instruction to classify the pre-existing formula failure as blocking and attribute it to `src/schema_formula.py` (not B1/B2) is consistent with the full-branch scope and is honored.

---

## Evidence Location Compliance

A git-diff scan over `main...HEAD` for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned no matches (`NO_NONCANONICAL_EVIDENCE_PATHS`). All evidence is under the canonical `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/` tree. The repository does not ship `scripts/validate_evidence_locations.py`; a git-diff scan was used as the substitute per the established convention. No evidence-location violations. No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | PASS | 940 tests pass and 1 fails deterministically in a single pytest run at HEAD `cc5b282`; the one failure is a Hypothesis property test isolated to `schema_formula`, not an ordering effect. GUI tests use `qtbot` fixtures; no inter-test shared mutable state. |
| **Isolation** - Each test targets single behavior | PASS | Cycle-3 added tests each target one behavior (B1 no-file, B1 file-no-worksheet, B2 reader ValueError, B2 presenter routing, AC-2 full-match). |
| **Fast Execution** - Tests complete quickly | PASS | Full suite ran in 23.25s for 941 tests under `QT_QPA_PLATFORM=offscreen`. |
| **Determinism** - Consistent results | PARTIAL | The cycle-3 tests are deterministic. The failing `test_property_col_round_trips_values` is deterministic given the recorded falsifying example `{'col': 0.0}`; it surfaces a real product defect in `src/schema_formula.py`, not flakiness. |
| **Readability & Maintainability** - Clear structure | PASS | Cycle-3 tests carry descriptive names and AAA structure with intent docstrings. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | PASS | **Baseline (cycle-3 P0-T6):** recorded in `evidence/baseline/pytest.baseline.md`. **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch`. |
| **No Coverage Regression** | PASS | **Post-change (this reaudit, HEAD `cc5b282`):** 98% lines (TOTAL row), ~94% branch. Cycle-3 changed modules rose to 99–100%; no regression on changed lines. |
| **New Code Coverage >=85% line / >=75% branch** | PASS | Cycle-3 changed modules: `_schema_discovery_wiring.py` 100% line, `source_selection_presenter.py` 99% line, `workbook_reader.py` 100% line (live per-module re-run by this reaudit). |
| **Comprehensive Coverage** | PASS | B1 covered by no-file and file-no-worksheet wiring tests plus parametrized presenter-guard tests; B2 covered by reader-unit and presenter-routing tests; AC-2 covered by a `build_application` integration test. |
| **Positive Flows** | PASS | `test_ac2_full_match_through_build_application_auto_selects_and_enables`. |
| **Negative Flows** | PASS | `test_tab_activation_no_file_selected_does_not_call_reader`; `test_read_sheet_preview_unknown_sheet_raises_value_error`. |
| **Edge Cases** | PASS | Whitespace-only sheet guard case (`test_on_schema_discovery_blank_path_or_sheet_is_noop`, `("workbook.xlsx", "   ")`). |
| **Error Handling** | PASS | Reader absent-sheet ValueError routes to `show_error` without crash (`test_on_schema_discovery_stale_sheet_value_error_routes_to_show_error`). |
| **Concurrency** | N/A | Not applicable to the defensive-guard/error-contract changes in this cycle. |
| **State Transitions** | PASS | Placeholder-stays / Import-disabled assertions in the B1 wiring tests. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98% line / 94.0% branch -> Post-change: 98% line / ~94% branch. Change: coverage-neutral repo-wide; cycle-3 changed modules rose to 99–100% line. New/changed-code coverage: `_schema_discovery_wiring.py` 100% line, `source_selection_presenter.py` 99% line, `workbook_reader.py` 100% line. Disposition: PASS (thresholds line >=85% and branch >=75% both hold; no regression on changed lines). Evidence: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T22-30.md` plus this reaudit's live re-run at HEAD `cc5b282`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero PowerShell files in branch diff).
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero TypeScript files in branch diff).
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero C# files in branch diff).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | PASS | Behavioral assertions in cycle-3 tests carry actionable messages; the property-test failure prints the falsifying example `{'col': 0.0}`. |
| **Arrange-Act-Assert Pattern** | PASS | Cycle-3 tests use explicit Arrange/Act/Assert sections. |
| **Document Intent** | PASS | Each cycle-3 test has a docstring naming B1/B2/AC-2 and the scenario. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | PASS | Fakes injected (`FakeWorkbookReader`, `FakeSchemaService`); in-memory `BytesIO` workbook for the reader unit tests; no network/DB. |
| **Use Mocks/Stubs** | PASS | `FakeSourceSelectionView`, fake services; no runtime temp files. |
| **Environment Stability** | PASS | `QT_QPA_PLATFORM=offscreen`; no runtime temp-file creation; masking scan clean. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | PASS | This artifact is the required review for the cycle-3 exit reaudit. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | PASS | Cycle scope = B1 (guard) + B2 (error contract), per `remediation-inputs.2026-06-05T22-30.md`. |
| **Read existing change plans** | PASS | `remediation-plan.2026-06-05T22-30.md` executed; phase-0 policy-read evidence present (`evidence/baseline/phase0-instructions-read.md`). |
| **Document the plan** | PASS | Remediation plan + evidence tree under canonical paths. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | PASS | B1 fixed with a minimal guard clause; B2 fixed with a single membership check converting the error type. |
| **Reusability** | PASS | The presenter guard makes `on_schema_discovery` safe for any caller, not just the wiring. |
| **Extensibility** | PASS | No public API signature change; only the reader's documented exception type changed from KeyError to ValueError. |
| **Separation of concerns** | PASS | Guard in presenter + defense-in-depth in wiring; error-type normalization in the reader service. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | PASS | Each fix lives in its owning module (presenter, wiring, reader). |
| **Under 500 lines** | PASS | All changed `.py` files <= 500 (verified by file-size scan over the full branch diff: no `.py` file over 500 lines). |
| **Public vs internal** | PASS | Internal modules `_`-prefixed; protocol docstring updated to match implementation. |
| **No circular dependencies** | PASS | Pyright passes (0 errors). |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | PASS | snake_case functions, PascalCase classes. |
| **Docs/docstrings** | PASS | `on_schema_discovery`, `_on_tab_activated`, and both `read_sheet_preview` docstrings updated to describe the no-op guard and the ValueError contract. |
| **Comment why, not what** | PASS | Intent comments explain the currentTextChanged-before-selection window and the KeyError->ValueError conversion rationale. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check .` -> `222 files would be left unchanged`, EXIT 0 (reaudit live run at HEAD `cc5b282`). |
| **2. Linting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check .` -> `All checks passed!`, EXIT 0. |
| **3. Type checking** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright` -> `0 errors, 0 warnings, 0 informations`, EXIT 0. |
| **4. Testing** | **FAIL (BLOCKING)** | **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` -> `1 failed, 940 passed`, EXIT non-zero. Failure: `tests/test_schema_formula.py::test_property_col_round_trips_values` (pre-existing `col`-shadowing defect in `src/schema_formula.py:301-307`; not introduced by cycle 3). |
| **Full toolchain loop** | **FAIL (BLOCKING)** | Stages 1-3 green; stage 4 RED in a single pass at HEAD `cc5b282`. The loop does not complete clean. |
| **Explicit reporting** | PASS | Commands and results documented here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | PASS | Remediation plan + traceability evidence. |
| **Design choices explained** | PASS | B2 contract choice (reader raises ValueError) rationale documented in the plan. |
| **Update supporting documents** | PASS | spec.md / user-story.md AC unchanged (cycle changed no features). |
| **Provide next steps** | PASS | `remediation-inputs.2026-06-05T23-23.md` scopes the pre-existing `col`-shadowing defect into the next cycle. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | PASS | `black --check .` EXIT 0, 222 files unchanged. |
| **Linting with Ruff** | PASS | `ruff check .` EXIT 0, all checks passed. |
| **Type checking with Pyright** | PASS | `pyright` 0 errors (strict mode). |
| **Testing with Pytest** | **FAIL (BLOCKING)** | 940 passed, 1 failed (pre-existing `schema_formula` defect). |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | PASS | Cycle-3 changes fully annotated; no new `Any`. |
| **Dataclasses for value objects** | PASS | Unchanged from prior cycles. |
| **Protocols/ABCs for interfaces** | PASS | `WorkbookReaderProtocol.read_sheet_preview` docstring updated in lockstep with the concrete implementation. |
| **Avoid utility classes** | PASS | Guard clauses are method-local; no new utility class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | PASS | Reader now raises a specific `ValueError` naming the missing sheet, replacing the leaking `KeyError`. The presenter routes it via the existing ValueError-only policy. |
| **Logging over print** | PASS | No ad-hoc print added; `logger.info` retained in `on_schema_discovery`. |
| **Invariants at construction** | PASS | Unchanged from prior cycles. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | pytest + pytest-qt (`qtbot`) + Hypothesis. |
| **Coverage expectation** | PASS | Repo-wide 98% line / ~94% branch (>= thresholds). Cycle-3 changed modules 99–100% line. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | PASS | One behavior per cycle-3 test. |
| **Mocking sparingly** | PASS | Fakes for reader/service; real Qt signal path used for wiring proofs. |
| **Organization** | PASS | B1/B2 tests placed in the modules mirroring the code under test; no test file exceeds 500 lines. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | PASS | Descriptive `test_*` names. |
| **Docstrings/comments** | PASS | Each cycle-3 test carries an intent docstring naming the defect it proves. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | `pytest --cov --cov-branch` invoked. |
| **No Alternative Test Runners** | PASS | Pytest only. |
| **Suite is green** | **FAIL (BLOCKING)** | 1 failed (pre-existing `schema_formula` defect). |

---

## 5. Test Coverage Detail

### B1 — Blank/whitespace path-or-sheet guard

| Proof | Test | Level | Status |
|-------|------|-------|--------|
| No file selected -> reader never called, placeholder stays, Import disabled | `test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader` | Wiring-level (real `currentTextChanged`) | PASS |
| File but no worksheet -> reader never called with blank sheet | `test_schema_discovery_wiring.py::test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet` | Wiring-level (real `currentTextChanged`) | PASS |
| Presenter guard for blank path / blank sheet / whitespace sheet | `test_source_selection_presenter.py::test_on_schema_discovery_blank_path_or_sheet_is_noop` (3 cases) | Presenter unit | PASS |

Production guard sites: `source_selection_presenter.py:233-235` (presenter contract) and `_schema_discovery_wiring.py:131-138` (defense in depth).

### B2 — Absent/blank-sheet reader error contract

| Proof | Test | Status |
|-------|------|--------|
| Reader raises ValueError for unknown sheet | `test_workbook_reader.py::test_read_sheet_preview_unknown_sheet_raises_value_error` | PASS |
| Reader raises ValueError for blank sheet | `test_workbook_reader.py::test_read_sheet_preview_blank_sheet_name_raises_value_error` | PASS |
| Presenter routes the reader ValueError to show_error without crash | `test_source_selection_presenter.py::test_on_schema_discovery_stale_sheet_value_error_routes_to_show_error` | PASS |

Production sites: `workbook_reader.py:164-165` (membership check + ValueError, inside `try`, workbook still closed by `finally`); docstrings at `workbook_reader.py:78-81` (protocol) and `:149-152` (impl).

### AC-2 — No regression (auto-select on a real match)

| Proof | Test | Status |
|-------|------|--------|
| `build_application` path auto-selects matched schema and enables Import | `test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables` | PASS |

### Prior production wiring (unchanged this cycle; spot-checked intact at HEAD `cc5b282`)

| Seam | Production call site | Status |
|------|---------------------|--------|
| `new_from_template` | `src/gui/_schema_open_helpers.py` (`open_new_from_template_builder`) | INTACT |
| `on_partial_match` | `src/gui/app.py:327-349` (`_on_partial_match` passed to three `SourceSelectionPresenter` constructions) | INTACT |
| `BuildSpecProvider` | `src/gui/app.py:430` (`spec_provider=build_spec_provider(_svc)`) | INTACT |
| Columns/Key drag tabs | `src/gui/widgets/schema_builder_dialog.py:98` (`DragTabBinder`); `_schema_builder_drag_tabs.py` | INTACT |
| Derived dialog | wired via shared open path; surfaces on Columns via `set_derived` | INTACT |

Cycle-3 commit diff (`fd8a022..cc5b282`) contains only three production files (the B1/B2 targets), confirming prior wiring was not touched.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 941 | — |
| Tests Passed | 940 (99.9%) | — |
| Tests Failed | 1 (`test_property_col_round_trips_values`) | **FAIL (BLOCKING)** |
| Execution Time | 23.25s total | PASS (fast) |
| Code Coverage | 98% lines (TOTAL), ~94% branches | PASS |
| Largest changed `.py` file | <= 500 lines (no changed file over cap) | PASS (under cap) |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | 222 files unchanged | PASS |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed | PASS |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors | PASS |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` | 940 passed, 1 failed | FAIL |
| Confidentiality masking scan | grep over `fd8a022..cc5b282` changed lines for secrets/PII/real values | NO_CONFIDENTIAL_VALUES | PASS |
| Suppression scan (added lines) | git-diff `fd8a022..cc5b282` grep `noqa\|type: ignore\|pyright: ignore` (code files) | NO_SUPPRESSIONS_ADDED | PASS |
| File-size gate | scan over all changed `.py` files in `main...HEAD` for >500 lines | NO_FILE_OVER_500 | PASS |
| Workflow change scan | git-diff `main...HEAD` for `.github/workflows/**` and `scripts/benchmarks/**` | NO_WORKFLOW_CHANGES, NO_BENCHMARK_CHANGES | PASS |

**Notes:** No `.github/workflows/**` or `scripts/benchmarks/**` change is present across the whole feature diff, so `modified-workflow-needs-green-run` and the benchmark-baseline provenance rule do not apply. The single FAIL is the pytest suite (one pre-existing `schema_formula` defect); all other quality gates pass.

---

## 8. Gaps and Exceptions

### Identified Gaps

**One blocking finding (pre-existing, out of cycle-3 scope):**

- **BLOCKING — RED test suite.** `tests/test_schema_formula.py::test_property_col_round_trips_values` (line 306) fails with `FormulaError: failed to evaluate formula 'col(name)': ... TypeError: '0.0' is not callable`. Root cause at `src/schema_formula.py:301-307`: `_build_symtable` seeds the whitelisted `col` callable, then the alias-binding loop overwrites `symtable["col"]` with a column value when a source column is literally named `col`. This defect is in `src/schema_formula.py`, which is NOT in the `main...HEAD` branch diff, so it predates the feature branch and is NOT attributable to the B1/B2 cycle-3 changes. A RED suite is a blocking merge/CI condition. Scoped to the next cycle via `remediation-inputs.2026-06-05T23-23.md`.

**Cycle-3 B1/B2 objectives are met (closed)** independent of this pre-existing failure.

### Approved Exceptions

**None.**

### Removed/Skipped Tests

**None.** No skip/xfail introduced. The failing test is a legitimate property test exposing a real product defect; it is correct for it to fail.

---

## 9. Summary of Changes

### Commits in This PR/Branch

- HEAD `cc5b282` — remediation cycle 3 (B1 blank-path/sheet guard; B2 reader ValueError contract). Prior cycle head was `fd8a022`; feature base commit `d8275d9`.

### Files Modified This Cycle (`fd8a022..cc5b282`, excluding docs/memory)

1. `src/gui/presenters/source_selection_presenter.py` (MODIFIED) — blank/whitespace path-or-sheet guard in `on_schema_discovery`; docstring updated (B1).
2. `src/gui/_schema_discovery_wiring.py` (MODIFIED) — `_on_tab_activated` short-circuit on blank path/sheet; docstring updated (B1 defense in depth).
3. `src/gui/services/workbook_reader.py` (MODIFIED) — `read_sheet_preview` raises ValueError for absent/blank sheet; protocol + impl docstrings updated KeyError->ValueError (B2).
4. `tests/gui/test_schema_discovery_wiring.py` (MODIFIED) — two B1 wiring-level integration tests + one AC-2 `build_application` test.
5. `tests/gui/test_source_selection_presenter.py` (MODIFIED) — B2 presenter-routing test + parametrized B1 guard test.
6. `tests/gui/test_workbook_reader.py` (MODIFIED) — two B2 reader-unit tests.

No production source outside the three B1/B2 targets, no workflow, and no benchmark files changed this cycle.

---

## 10. Compliance Verdict

### Overall Status: NON-COMPLIANT (1 BLOCKING) — cycle-3 B1/B2 objectives met; blocking finding is a pre-existing, out-of-scope defect

Cycle-entry findings B1 and B2 are both closed at HEAD `cc5b282` with wiring-level and unit proof, and AC-2 is re-confirmed with no regression. The single blocking finding is the RED test suite caused by a pre-existing `col`-shadowing defect in `src/schema_formula.py` (not introduced by cycle 3), which makes the toolchain not green and is therefore a blocking merge/CI condition.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure (all changed `.py` <= 500)
- PASS Naming, Docs, Comments
- FAIL Toolchain Execution (stage 4 RED: pre-existing `schema_formula` defect)
- PASS Summarize & Document

#### Language-Specific Code Change Policy (Section 3) — Python
- PASS Tooling & Baseline (format/lint/type-check)
- PASS Python Design & Typing
- PASS Error Handling

#### General Unit Test Policy (Section 1)
- PASS Core Principles (PARTIAL on Determinism note: failing property test is a real defect, not flakiness)
- PASS Coverage & Scenarios
- PASS Test Structure
- PASS External Dependencies
- PASS Policy Audit

#### Language-Specific Unit Test Policy (Section 4) — Python
- PASS Framework & Scope
- PASS Test Style & Structure
- PASS Naming & Readability
- FAIL Toolchain (suite RED)

### Metrics Summary

- 940/941 tests passing; 1 failing (pre-existing `col`-shadowing defect in `src/schema_formula.py`)
- 98% line coverage, ~94% branch coverage (>= 85% / >= 75%); cycle-3 changed modules 99–100% line
- Black / Ruff / Pyright all clean at HEAD `cc5b282`
- Masking scan clean; no suppressions added in cycle 3; no workflow/benchmark change
- All changed `.py` files <= 500 lines

### Recommendation

**Not ready for merge until the RED suite is green.** Cycle-3 B1/B2 are complete and verified. Fix the pre-existing `col`-shadowing defect in `src/schema_formula.py:301-307` in the next cycle (scoped in `remediation-inputs.2026-06-05T23-23.md`): bind the `col` accessor after the alias loop, or guard the alias loop from overwriting reserved whitelisted names, then re-run the toolchain to green.

---

## Appendix A: Test Inventory

Cycle-3 proof tests (full suite: 941 tests, 940 pass / 1 fail):

- tests/gui/test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader (B1, wiring-level)
- tests/gui/test_schema_discovery_wiring.py::test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet (B1, wiring-level)
- tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables (AC-2, integration)
- tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_blank_path_or_sheet_is_noop (B1, 3 parametrized cases)
- tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_stale_sheet_value_error_routes_to_show_error (B2 routing)
- tests/gui/test_workbook_reader.py::test_read_sheet_preview_unknown_sheet_raises_value_error (B2 reader)
- tests/gui/test_workbook_reader.py::test_read_sheet_preview_blank_sheet_name_raises_value_error (B2 reader)

Failing (pre-existing, out of scope):
- tests/test_schema_formula.py::test_property_col_round_trips_values (`col`-shadowing defect in `src/schema_formula.py:301-307`)

## Appendix B: Toolchain Commands Reference

```bash
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
```

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-05
**Policy Version:** Current (as of audit date)
