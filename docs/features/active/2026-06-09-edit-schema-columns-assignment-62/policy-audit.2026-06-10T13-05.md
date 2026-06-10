# Policy Compliance Audit: edit-schema-columns-assignment (Issue #62) — Cycle-1 Re-audit (R4)

**Audit Date:** 2026-06-10
**Code Under Test (changed production):**
- `src/gui/_schema_discovery_wiring.py` (MODIFIED)
- `src/gui/presenters/_columns_tab_presenter.py` (MODIFIED)
- `src/gui/presenters/source_selection_presenter.py` (MODIFIED)
- `src/gui/widgets/_columns_tab_drag.py` (MODIFIED)
- `src/gui/widgets/_schema_builder_tabs.py` (MODIFIED)
- `src/gui/widgets/_schema_builder_window_setup.py` (NEW)
- `src/gui/widgets/schema_builder_dialog.py` (MODIFIED)

**Code Under Test (changed tests):**
- `tests/gui/test_columns_tab_presenter.py`, `tests/gui/test_columns_tab_widgets.py`,
  `tests/gui/test_edit_schema_wiring.py`, `tests/gui/test_schema_builder_dialog.py`,
  `tests/gui/test_schema_builder_presenter_core.py`, `tests/gui/test_worksheet_header_columns.py` (NEW)

**Scope:** Full branch diff `f7aea0f...150d42a` (base `main`). Work mode `minor-audit`;
AC source is `issue.md` `## Acceptance Criteria` (AC-1..AC-9).

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 7 prod + 6 test | 1037 | ✅ 1037 pass, 0 fail | 98% lines (pre-cycle suite) | 99.1% lines, 94.1% branches (repo-wide) | 100% (new file `_schema_builder_window_setup.py`) |
| PowerShell | 0 files | N/A | N/A | N/A (no PowerShell changes) | N/A (no PowerShell changes) | N/A |
| TypeScript | 0 files | N/A | N/A | N/A (no TypeScript changes) | N/A (no TypeScript changes) | N/A |
| C# | 0 files | N/A | N/A | N/A (no C# changes) | N/A (no C# changes) | N/A |

**Note:** Only Python source has changed files on this branch. PowerShell, TypeScript, and C#
have zero changed files; their coverage verdicts are N/A per the scope invariant (acceptable
only for languages with zero changed files).

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (zero TypeScript changed files)
- TypeScript post-change coverage artifact: `N/A - out of scope` (zero TypeScript changed files)
- PowerShell baseline coverage artifact: `N/A - out of scope` (zero PowerShell changed files)
- PowerShell post-change coverage artifact: `N/A - out of scope` (zero PowerShell changed files)
- Python post-change coverage artifact: `artifacts/python/lcov.info` (refreshed via full-suite run during this audit, 2026-06-10)
- Per-language comparison summary: see section 1.2.1 below.

---

## Executive Summary

This is the cycle-1 re-audit (R4) of the issue #62 remediation. Cycle-0 delivered alias-seeding
(AC-1..AC-4) that passed audit and CI but did not fix the user-observable defect: the bundled
default schemas carry empty aliases and the Edit Schema button opened the builder with no
`preview_slice`, leaving the Columns tab fully unassigned. Cycle-1 delivers the production fix
(AC-5..AC-9) plus retains the cycle-0 behavior.

Independent verification confirms the fix is genuinely wired into the real Edit-Schema control
flow, not merely exercised by fakes:

`app.py:424` `wire_schema_discovery_and_gating(...)` → `wire_edit_schema_buttons(window, service,
le_presenter, aop_presenter, skulu_presenter)` → per-widget `_open_edit` closure →
`_build_edit_preview_slice` → `read_worksheet_header_columns(presenter.reader, service, path, sheet)`
→ `open_schema_builder(..., preview_slice=...)` → retained `schema_builder_presenter.load_existing(name)`.
The three per-tab presenters carrying `.reader` are passed at the composition root (app.py:427-429),
so production can reach the new seam. This is not an instance of the repo's recurring tested-but-unwired
seam pattern.

AC-6 is asserted against the real rendered assignment state: `test_edit_renders_matching_canonical_rows_as_assigned`
drives the real `SchemaBuilderDialog` + real `SchemaBuilderPresenter`, resolves the live
`ColumnsTabWidget` via `findChild`, and asserts `row_assignment_text("Customer") == "Customer"`
(the on-screen assignment label), not an internal presenter state object.

Toolchain executed clean in a single pass: Black, Ruff, Pyright (0 errors), Pytest (1037 passed).
Coverage on all changed files is above the uniform thresholds (line >= 85%, branch >= 75%).

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A `powershell.md` (zero PowerShell changes)
- N/A TypeScript / C# (zero changes)

**Temporary artifacts cleanup:**
- ✅ One throwaway coverage-extraction script (`_covscan_tmp.py`) was created and deleted within this audit session.
- ✅ No ongoing tooling scripts were added.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | GUI tests use `qtbot.addWidget` for lifetime management and construct fresh `MainWindow`/`SchemaBuilderDialog` per test; no shared mutable module state. Full suite passes single-pass. |
| **Isolation** - Each test targets single behavior | ✅ PASS | E.g. `test_edit_populates_preview_slice_from_real_worksheet_headers` (AC-5), `test_edit_renders_matching_canonical_rows_as_assigned` (AC-6), `test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool` (AC-1) each assert one behavior. |
| **Fast Execution** - Tests complete quickly | ✅ PASS | Full suite (1037 tests) completed in ~40s with coverage; offscreen Qt. |
| **Determinism** - Consistent results | ✅ PASS | Fakes (`FakeWorkbookReader`, `FakeSchemaService`, `FakeSourceSelectionView`) supply deterministic preview rows and match results; no wall-clock, no RNG, no network/disk. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive `test_*` names map to AC numbers in docstrings; AAA structure with Arrange/Act/Assert comments. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Pre-cycle suite at 98% lines (see `evidence/baseline/pytest-coverage.md`). Command: `poetry run pytest --cov --cov-branch`. |
| **No Coverage Regression** | ✅ PASS | Post-change repo-wide: 99.1% lines (4859/4903), 94.1% branches (868/922). No regression on changed lines; all changed files re-measured this audit. |
| **New Code Coverage >= 85% line / 75% branch** | ✅ PASS | New file `_schema_builder_window_setup.py`: 100% line (9/9), no branches. Changed lines in other files fully covered. |
| **Comprehensive Coverage** | ✅ PASS | New seams covered: `read_worksheet_header_columns` (100%), `_build_edit_preview_slice`/`_open_edit` wiring (100% via `_schema_discovery_wiring.py`), `_seed_from_persisted_aliases` (covered in `_columns_tab_presenter.py` at 96.5%), scroll-area wrap and window flags. |
| **Positive Flows** - Valid inputs | ✅ PASS | AC-5/AC-6 positive paths (real headers populate pool, matching rows render assigned). |
| **Negative Flows** - Invalid inputs | ✅ PASS | AC-9 no-file/no-sheet seam (`test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call`); placeholder short-circuit. |
| **Edge Cases** - Boundary conditions | ✅ PASS | Alias-free row stays unassigned (AC-2); live-match-wins over persisted alias (AC-3); empty preview returns empty tuple. |
| **Error Handling** - Error paths | ✅ PASS | Stub presenter lacking `load_existing` tolerated via getattr guard (`test_edit_with_stub_presenter_lacking_load_existing_does_not_crash`). |
| **Concurrency** - If applicable | N/A | No concurrency in presenter/wiring logic. |
| **State Transitions** - If applicable | ✅ PASS | Live-match then persisted-alias seeding ordering verified (consumed_columns transitions). |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98% lines (pre-cycle full suite) -> Post-change: 99.1% lines (4859/4903). Change: +~1% lines, branch 94.1% (868/922). New/changed-code coverage: 100% on new file `_schema_builder_window_setup.py`; changed lines on the other six files fully covered (per-file line: `_schema_discovery_wiring.py` 100% (46/46), `source_selection_presenter.py` 100% (96/96), `_columns_tab_presenter.py` 96.5% (83/86), `_columns_tab_drag.py` 98.1% (101/103), `_schema_builder_tabs.py` 100% (90/90), `schema_builder_dialog.py` 99.1% (112/113)). Disposition: PASS. Evidence: `artifacts/python/lcov.info` (refreshed full-suite run this audit), `evidence/qa-gates/final-pytest-coverage.md`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope`. Disposition: N/A (zero PowerShell changed files). Evidence: branch diff name-status shows no `.ps1` changes.
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope`. Disposition: N/A (zero TypeScript changed files). Evidence: branch diff name-status shows no `.ts`/`.tsx` changes.
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope`. Disposition: N/A (zero C# changed files). Evidence: branch diff name-status shows no `.cs` changes.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Equality assertions on assignment text/preview slice header produce readable diffs. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Each new test has explicit Arrange/Act/Assert comment sections. |
| **Document Intent** | ✅ PASS | Docstrings cite the AC each test exercises. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No network/db/process; fakes used. No real `.xlsx`. |
| **Use Mocks/Stubs** | ✅ PASS | `FakeWorkbookReader`, `FakeSchemaService`, recording dialog/presenter; no over-mocking (real dialog+presenter used for AC-6). |
| **Environment Stability** | ✅ PASS | `QT_QPA_PLATFORM=offscreen`; no temporary files created in tests. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This audit constitutes the required review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Issue #62 + `remediation-inputs.2026-06-10T12-24.md` define AC-5..AC-9. |
| **Read existing change plans** | ✅ PASS | `remediation-plan.2026-06-10T12-24.md` present on branch. |
| **Document the plan** | ✅ PASS | Plan + remediation inputs committed in feature folder. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | The fix reuses the existing `best_header_row`/preview-slice path rather than introducing a parallel reader; `read_worksheet_header_columns` is a small pure-ish helper over the reader. |
| **Reusability** | ✅ PASS | `best_header_row` promoted to public and reused by both discovery and edit-seeding. Window-flag setup extracted into a reusable helper module. |
| **Extensibility** | ✅ PASS | `wire_edit_schema_buttons` uses keyword presenters and optional factories with defaults; degrades to empty pool when a presenter is absent. |
| **Separation of concerns** | ✅ PASS | Reader/header path is Qt-free; window-flag setup isolated from dialog logic; wiring holds no transform logic. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | New `_schema_builder_window_setup.py` has a single responsibility (window flags + default size). |
| **Under 500 lines** | ✅ PASS | All changed production files <= 500 (verified `wc -l`/`awk NR`): `_schema_discovery_wiring.py` 336, `_columns_tab_presenter.py` 406, `source_selection_presenter.py` 436, `_columns_tab_drag.py` 441, `_schema_builder_tabs.py` 290, `_schema_builder_window_setup.py` 61, `schema_builder_dialog.py` 499. All changed test files <= 500: max `test_edit_schema_wiring.py` 471. |
| **Public vs internal** | ✅ PASS | `_`-prefixed helper modules for internals; `read_worksheet_header_columns`/`best_header_row` exported via `__all__`. |
| **No circular dependencies** | ✅ PASS | `_schema_discovery_wiring.py` imports the presenter helper at module top (no cycle); activation classifier imported locally in the presenter to avoid an import-time dependency. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `read_worksheet_header_columns`, `_build_edit_preview_slice`, `apply_schema_builder_window_flags`, `_seed_from_persisted_aliases`. |
| **Docs/docstrings** | ✅ PASS | Every new function/method/class carries a Google-style docstring with Args/Returns/Side effects. |
| **Comment why, not what** | ✅ PASS | Intent comments above branches and the seed loop explain rationale (e.g. live-match-wins ordering, AC-9 empty-pool seam). |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black --check src/gui tests/gui` → 142 files unchanged, exit 0. |
| **2. Linting** | ✅ PASS | `poetry run ruff check src/gui tests/gui` → All checks passed, exit 0. |
| **3. Type checking** | ✅ PASS | `poetry run pyright src/gui tests/gui` → 0 errors, 0 warnings. |
| **4. Testing** | ✅ PASS | `QT_QPA_PLATFORM=offscreen poetry run pytest ... --cov --cov-branch` → 1037 passed, 0 failed. |
| **Full toolchain loop** | ✅ PASS | All stages clean in a single pass during this audit. |
| **Explicit reporting** | ✅ PASS | Commands and results documented in this audit and section 7. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | See section 9. |
| **Design choices explained** | ✅ PASS | Helper extraction for the 500-line cap; no source-pool reflection for seeded aliases documented in `_seed_from_persisted_aliases` docstring. |
| **Update supporting documents** | ✅ PASS | `issue.md` AC checkboxes maintained; evidence artifacts present. |
| **Provide next steps** | ✅ PASS | See section 10 recommendation. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check src/gui tests/gui` → unchanged. |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check src/gui tests/gui` → All checks passed. |
| **Type checking with Pyright** | ✅ PASS | `poetry run pyright src/gui tests/gui` → 0 errors. |
| **Testing with Pytest** | ✅ PASS | 1037 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | All new functions fully annotated; `PreviewSlice | None`, `tuple[str, ...]` return types. No `Any` introduced. |
| **Dataclasses for value objects** | ✅ PASS | `PreviewSlice` reused; control bundles remain dataclasses. |
| **Protocols/ABCs for interfaces** | ✅ PASS | `WorkbookReaderProtocol`, `SchemaServiceProtocol` used as injected seams. |
| **Avoid utility classes** | ✅ PASS | New helpers are module-level functions, not static-method classes. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | No broad catches added; reader `ValueError` policy unchanged in the presenter. |
| **Logging over print** | ✅ PASS | No print statements added. |
| **Invariants at construction** | ✅ PASS | Empty-header/empty-preview guards enforce the empty-pool invariant; one-source-per-row preserved. |

#### 3A.4 Suppressions

| Requirement | Status | Evidence |
|------------|--------|----------|
| **No unauthorized suppressions** | ✅ PASS | Added-line scan for `noqa`/`type: ignore`/`pyright: ignore` returned NONE. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Pytest + pytest-qt (`qtbot`). |
| **Coverage expectation** | ✅ PASS | Repo-wide 99.1% line / 94.1% branch; changed files all >= 85% line / >= 75% branch. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | Real dialog + presenter for AC-6; fakes only at the I/O boundary (reader, service). |
| **Organization** | ✅ PASS | Tests mirror code (`tests/gui/test_worksheet_header_columns.py` for the new helper). |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_edit_*`, `test_prepopulate_*` names. |
| **Docstrings/comments** | ✅ PASS | AC-referencing docstrings. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | 1037 passed. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### read_worksheet_header_columns (source_selection_presenter.py)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `tests/gui/test_worksheet_header_columns.py` (header read, best-header-row honored, blank path/sheet → (), empty preview → ()) | Positive/Negative/Edge | ✅ |

**Coverage:** module 100% line (96/96), 96.4% branch (27/28). The single partial branch (399->401)
is a pre-existing branch in unchanged `_apply_activation_decision`, not this cycle's edits.

### Edit-Schema wiring (_schema_discovery_wiring.py)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_edit_populates_preview_slice_from_real_worksheet_headers` | Positive (AC-5) | ✅ |
| `test_edit_renders_matching_canonical_rows_as_assigned` | Positive (AC-6, real rendered state) | ✅ |
| `test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call` | Negative (AC-9) | ✅ |
| `test_edit_with_placeholder_short_circuits_without_opening` | Negative (AC-9) | ✅ |
| `test_edit_with_stub_presenter_lacking_load_existing_does_not_crash` | Error handling | ✅ |

**Coverage:** module 100% line (46/46), 100% branch (14/14).

### Persisted-alias seeding (_columns_tab_presenter.py)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool` | Positive (AC-1) | ✅ |
| `test_prepopulate_leaves_alias_free_row_unassigned_empty_pool` | Edge (AC-2) | ✅ |
| `test_live_fuzzy_match_wins_over_persisted_alias` | Edge/invariant (AC-3) | ✅ |

**Coverage:** module 96.5% line (83/86), 85.3% branch (29/34); the new seed method is exercised.

**Not covered:** None material. Residual misses (`schema_builder_dialog.py:378`, `_columns_tab_drag.py`)
are in unchanged set_derived/handler paths, not this cycle's edits.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 1037 | ✅ |
| Tests Passed | 1037 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | ~40s total (with coverage) | ✅ Fast |
| Functions/Classes Tested | New seams all covered | ✅ |
| Test File Size | max 471 lines (test_edit_schema_wiring.py) | ✅ Maintainable |
| Code Coverage | 99.1% lines, 94.1% branches (repo-wide) | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check src/gui tests/gui` | 142 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check src/gui tests/gui` | All checks passed | ✅ |
| Pyright Type Checking | `poetry run pyright src/gui tests/gui` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen poetry run pytest ... --cov --cov-branch` | 1037 passed | ✅ |

**Notes:**
No pre-existing failures observed. The Phase-0 flaky Hypothesis test
(`tests/test_normalize_le_io.py::test_validate_tieouts_property_roundtrip`) passed in this run.

---

## Evidence Location Compliance

A branch-diff scan for files written under `artifacts/baselines/`, `artifacts/qa/`,
`artifacts/evidence/`, or `artifacts/coverage/` returned NONE. All feature evidence is written
under the canonical `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/<kind>/`.
The repo's `validate_evidence_locations.py` script is absent (only the PowerShell PreToolUse hook
exists); a git-diff name-only scan was used instead. No violations found.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements are met.

### Approved Exceptions
**None.** No suppressions or exceptions used.

### Removed/Skipped Tests
**None.** All planned tests implemented; cycle-0 AC-1..AC-4 tests retained.

---

## 9. Summary of Changes

### Commits in This PR/Branch (relative to base `main` / `f7aea0f`)
- `db1c9f0` — fix(gui): seed Columns-tab assignments from persisted aliases on schema edit (#62) [cycle-0]
- `fe50718` — docs(orchestration): #62 feature-review artifacts [cycle-0]
- (cycle-1 production + tests through head `150d42a`)

### Files Modified
1. **src/gui/_schema_discovery_wiring.py** (MODIFIED) — `wire_edit_schema_buttons` now accepts the three per-tab presenters and builds a live `preview_slice` via `_build_edit_preview_slice`/`read_worksheet_header_columns` before `open_schema_builder`.
2. **src/gui/presenters/source_selection_presenter.py** (MODIFIED) — `best_header_row` promoted to public; new public `read_worksheet_header_columns` helper reusing the best-header-row path with the AC-9 blank-guard.
3. **src/gui/presenters/_columns_tab_presenter.py** (MODIFIED) — `_seed_from_persisted_aliases` second pass (live-match-wins) [cycle-0].
4. **src/gui/widgets/_schema_builder_tabs.py** (MODIFIED) — Columns tab wrapped in a resizable `QScrollArea` (AC-7).
5. **src/gui/widgets/schema_builder_dialog.py** (MODIFIED) — applies window flags via the new setup helper (AC-8).
6. **src/gui/widgets/_schema_builder_window_setup.py** (NEW) — `apply_schema_builder_window_flags` (resizable + min/max/close + default size).
7. **src/gui/widgets/_columns_tab_drag.py** (MODIFIED) — two public test seams (`assignment_text`, `row_assignment_text`) for asserting rendered assignments.
8. Tests (6 files) — AC-1..AC-9 coverage including real-rendered-state AC-6 assertion.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The cycle-1 production fix is wired into the real Edit-Schema control flow, AC-6 is asserted
against the rendered widget state, file-size and suppression policies hold, no confidential data
was committed, and the full Python toolchain is green with no coverage regression.

**Fail-closed reminder:** All required baseline, QA, and coverage artifacts are present; no PASS
was issued in the absence of evidence.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes; ✅ Design Principles; ✅ Module & File Structure; ✅ Naming/Docs/Comments; ✅ Toolchain Execution; ✅ Summarize & Document

#### Language-Specific Code Change Policy (Section 3)
**For Python:** ✅ Tooling & Baseline; ✅ Design & Typing; ✅ Error Handling; ✅ Suppressions

#### General Unit Test Policy (Section 1)
- ✅ Core Principles; ✅ Coverage & Scenarios; ✅ Test Structure; ✅ External Dependencies; ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4)
**For Python:** ✅ Framework & Scope; ✅ Test Style & Structure; ✅ Naming & Readability; ✅ Toolchain

### Metrics Summary
- ✅ 1037/1037 tests passing (100%)
- ✅ 99.1% line coverage, 94.1% branch coverage (repo-wide)
- ✅ All changed files <= 500 lines
- ✅ All code quality checks passing
- ✅ Test execution ~40s (fast)

### Recommendation

**Ready for merge.** No blocking findings. Total blocking count from this artifact: 0.

---

## Appendix A: Test Inventory (cycle-1 additions)

- tests/gui/test_worksheet_header_columns.py (new helper: header read / best-header-row / blank-guard / empty-preview)
- tests/gui/test_edit_schema_wiring.py::test_edit_populates_preview_slice_from_real_worksheet_headers (AC-5)
- tests/gui/test_edit_schema_wiring.py::test_edit_renders_matching_canonical_rows_as_assigned (AC-6)
- tests/gui/test_edit_schema_wiring.py::test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call (AC-9)
- tests/gui/test_columns_tab_presenter.py::test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool (AC-1)
- tests/gui/test_columns_tab_presenter.py::test_prepopulate_leaves_alias_free_row_unassigned_empty_pool (AC-2)
- tests/gui/test_columns_tab_presenter.py::test_live_fuzzy_match_wins_over_persisted_alias (AC-3)
- tests/gui/test_schema_builder_dialog.py (window flags / scroll area)
- tests/gui/test_columns_tab_widgets.py (row_assignment_text seam)
- tests/gui/test_schema_builder_presenter_core.py (load_existing render)

## Appendix B: Toolchain Commands Reference

```bash
poetry run black --check src/gui tests/gui
poetry run ruff check src/gui tests/gui
poetry run pyright src/gui tests/gui
QT_QPA_PLATFORM=offscreen poetry run pytest tests/ --cov --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent (Claude Opus 4.8)
**Audit Date:** 2026-06-10
**Policy Version:** Current (as of audit date)
