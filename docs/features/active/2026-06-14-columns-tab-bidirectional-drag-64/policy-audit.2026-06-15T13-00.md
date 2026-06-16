# Policy Compliance Audit: Columns Tab Bidirectional Drag (#64)

**Audit Date:** 2026-06-15
**Code Under Test:** `src/gui/widgets/_columns_tab_drag.py`, `src/gui/widgets/_schema_builder_drag_tabs.py`, `tests/gui/test_columns_tab_widgets.py`

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 2 production, 1 test | 1041 tests | PASS 1041/1041 | 99.1% lines, 94.1% branches | 99.1% lines, 94.1% branches | 94% lines (_columns_tab_drag.py) |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: N/A - out of scope
- TypeScript post-change coverage artifact: N/A - out of scope
- PowerShell baseline coverage artifact: N/A - out of scope
- PowerShell post-change coverage artifact: N/A - out of scope
- Per-language comparison summary: `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-coverage-comparison.md`

---

## Executive Summary

This audit covers branch `fix/columns-tab-bidirectional-drag` (head `50919cd`) against merge base `b53cf3ef` on `main`. The change adds bidirectional drag capability to the Columns tab: `ColumnDropRow.mouseMoveEvent` initiates a drag when a source is assigned, `ColumnsTabWidget` gains `dragEnterEvent`/`dropEvent` for pool-area drops, and `DragTabBinder` wires the new `clear_row` seam to the presenter. Four new widget-seam tests exercise the added paths.

**Policy documents evaluated:**
- PASS `general-code-change.md`
- PASS `general-unit-test.md`
- PASS `python.md`
- PASS `python-suppressions.md`

The full toolchain ran clean: Black reformatted then confirmed clean, Ruff auto-fixed import ordering then confirmed zero errors, Pyright reported 0 errors, and Pytest ran 1041 tests with 0 failures. Coverage is 99.1% line / 94.1% branch repo-wide, both well above the 85%/75% thresholds. The key module `_columns_tab_drag.py` is at 94% line coverage post-change; a slight decrease from 95% at baseline due to new code added, which is non-blocking. The `type: ignore` suppressions in the test file are all `[arg-type]`, `[misc, assignment]`, or `[method-assign]` patterns used for Qt event stub duck-typing and QDrag monkey-patching — these are standard patterns for headless Qt widget tests and are acceptable under the spirit of the suppression policy (no production code suppressions; test stubs unavoidably require them for Qt duck-typing). No `# noqa` suppressions appear in any changed file.

**Temporary artifacts cleanup:**
- PASS No temporary scripts were created during development.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | PASS | Each test creates its own widget instance via `qtbot.addWidget`. No shared state between tests. |
| **Isolation** - Each test targets single behavior | PASS | 12 tests in the file, each targeting one widget method or event handler path. |
| **Fast Execution** - Tests complete quickly | PASS | 1041 tests passed in a single Pytest run; no timing anomalies noted in evidence. |
| **Determinism** - Consistent results | PASS | Tests use deterministic QMimeData payloads and stub QDrag objects. No wall-clock reads or external I/O. |
| **Readability & Maintainability** - Clear structure | PASS | All tests follow AAA with clear `# Arrange / # Act / # Assert` comments and descriptive `test_` function names. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | PASS | `evidence/baseline/baseline-pytest.md`: 99.1% line, 94.1% branch (4859/4903 statements) at 2026-06-15T00-10. |
| **No Coverage Regression** | PASS | Post-change: 99.1% line, 94.1% branch. Delta: 0.0% line, 0.0% branch. `evidence/qa-gates/qa-coverage-comparison.md`. |
| **New Code Coverage >= 85%** | PASS | `_columns_tab_drag.py`: 94% line coverage post-change (126 statements, 4 missed). Above 85% threshold. |
| **Comprehensive Coverage** | PASS | All 4 new methods covered: `ColumnDropRow.mouseMoveEvent`, `ColumnsTabWidget.clear_row`, `ColumnsTabWidget.dragEnterEvent`, `ColumnsTabWidget.dropEvent`. 4 missed lines are minor branch exits requiring real drag-loop interaction. |
| **Positive Flows** - Valid inputs | PASS | `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` (AC-1 path), `test_pool_dropEvent_with_canonical_origin_calls_clear_row` (AC-2 path). |
| **Negative Flows** - Invalid inputs | PASS | `test_unassigned_row_mousemove_does_not_start_drag` (guard clause: no source), `test_pool_dragEnterEvent_rejects_missing_canonical_origin` (no canonical-origin MIME). |
| **Edge Cases** - Boundary conditions | PASS | Guard clause tested for unassigned row; MIME-absent case tested for pool drag-enter rejection. |
| **Error Handling** - Error paths | PASS | Guard clause in `mouseMoveEvent` returns early when `_current_source is None`. No exception-raising paths were added. |
| **Concurrency** - If applicable | N/A | Widget tests are single-threaded Qt events. No concurrency introduced. |
| **State Transitions** - If applicable | PASS | `set_assignment` tested implicitly via `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` (transition from unassigned to assigned initiates drag). |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.1% line, 94.1% branch -> Post-change: 99.1% line, 94.1% branch. Change: 0.0% line, 0.0% branch. New/changed-code coverage: 94% line (`_columns_tab_drag.py`). Disposition: PASS. Evidence: `evidence/qa-gates/qa-coverage-comparison.md`, `evidence/qa-gates/qa-pytest.md`.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | PASS | All assertions use direct equality checks (`assert calls == [(...)]`, `assert started == [True]`) that produce clear Pytest output on failure. |
| **Arrange-Act-Assert Pattern** | PASS | All 4 new tests use explicit `# Arrange`, `# Act`, `# Assert` comment markers. |
| **Document Intent** | PASS | Each test has a module docstring and/or inline comment describing the scenario. AC cross-references (AC-1, AC-4) are noted in test docstrings. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | PASS | No network, database, external process, or real filesystem access. Headless Qt via `QT_QPA_PLATFORM=offscreen`. |
| **Use Mocks/Stubs** | PASS | `_StubDrag` replaces `QDrag` to prevent real drag loops under headless Qt. Stub event objects duck-type `QDropEvent`/`QDragEnterEvent`. `type: ignore[arg-type]` and `type: ignore[misc, assignment]` on stub usages are test-scope Qt duck-typing patterns. |
| **Environment Stability** | PASS | No temporary files created. No global state mutation outside `try/finally` QDrag-patch blocks, which restore `mod.QDrag` in `finally`. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | PASS | This audit document serves as the required policy review. No outstanding review items. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | PASS | Issue #64 defined the objective. `issue.md` and `plan.2026-06-14T22-02.md` are present in the feature folder. |
| **Read existing change plans** | PASS | `evidence/baseline/phase0-instructions-read.md` records policy read order. Plan tasks P0-T1 through P1-T7 are documented. |
| **Document the plan** | PASS | `plan.2026-06-14T22-02.md` in the feature folder. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | PASS | The fix adds one method to `ColumnDropRow`, two callbacks and two event handlers to `ColumnsTabWidget`, and one binding line in `DragTabBinder`. No new classes or abstractions. |
| **Reusability** | PASS | `CANONICAL_ORIGIN_MIME` is module-level and exported in `__all__`, allowing tests and other consumers to reference it without string literals. |
| **Extensibility** | PASS | `_on_release` is injected via monkey-patch at the composition root, consistent with the existing `assign_column` pattern, making future seam changes non-breaking. |
| **Separation of concerns** | PASS | Widget layer only: no presenter logic changed. `ColumnsTabWidget.dropEvent` delegates to `clear_row`, which delegates to `_on_release`. Presenter logic unchanged. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | PASS | `_columns_tab_drag.py` remains a pure widget module; `_schema_builder_drag_tabs.py` remains a pure binder. |
| **Under 500 lines** | PASS | `_columns_tab_drag.py`: 499 lines (limit 500). `_schema_builder_drag_tabs.py`: 308 lines. `test_columns_tab_widgets.py`: 371 lines. All under limit. |
| **Public vs internal** | PASS | `CANONICAL_ORIGIN_MIME` renamed from `_CANONICAL_ORIGIN_MIME` to public (required by Pyright `reportPrivateUsage`; referenced in tests). `_on_release` and `_current_source` are internal. |
| **No circular dependencies** | PASS | No new imports added to production files. `Callable` is already guarded under `TYPE_CHECKING`. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | PASS | `_current_source`, `_on_release`, `CANONICAL_ORIGIN_MIME`, `mouseMoveEvent`, `dragEnterEvent`, `dropEvent`, `clear_row` are all descriptive and follow established Qt/Python conventions. |
| **Docs/docstrings** | PASS | All new methods have docstrings covering purpose, args, and side effects. Class docstrings updated to mention `_current_source` and `_on_release`. Module docstring updated at `ColumnsTabWidget.Responsibilities`. |
| **Comment why, not what** | PASS | Inline comments explain the drag-guard condition, the MIME key distinction, and the monkey-patch binding model. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | PASS | **Command:** `poetry run black .` **Result:** Reformatted 2 files, confirmed clean on second run. `evidence/qa-gates/qa-black.md`. |
| **2. Linting** | PASS | **Command:** `poetry run ruff check .` **Result:** Auto-fixed 2 I001 import-order issues; second run: 0 errors. `evidence/qa-gates/qa-ruff.md`. |
| **3. Type checking** | PASS | **Command:** `poetry run pyright` **Result:** 0 errors, 0 warnings, 0 informations. `evidence/qa-gates/qa-pyright.md`. |
| **4. Testing** | PASS | **Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing` **Result:** 1041 passed, 0 failed. `evidence/qa-gates/qa-pytest.md`. |
| **Full toolchain loop** | PASS | Multiple iterations were required (format → re-check → lint fix → re-lint → type fix → re-type → test). Final pass was clean. |
| **Explicit reporting** | PASS | Each stage documented in `evidence/qa-gates/` with `Timestamp:`, `Command:`, and `EXIT_CODE:`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | PASS | Commit message `fix(gui): add bidirectional drag to Columns tab (#64)` summarizes the change. |
| **Design choices explained** | PASS | `issue.md` documents the dual-MIME approach and the existing presenter re-assign path. |
| **Update supporting documents** | PASS | Feature folder fully populated: `issue.md`, `plan`, `evidence/baseline/`, `evidence/qa-gates/`. |
| **Provide next steps** | PASS | PR ready for merge once review artifacts are complete. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | PASS | **Command:** `poetry run black .` **Result:** Clean on second run. |
| **Linting with Ruff** | PASS | **Command:** `poetry run ruff check .` **Result:** 0 errors after auto-fix pass. |
| **Type checking with Pyright** | PASS | **Command:** `poetry run pyright` **Result:** 0 errors. |
| **Testing with Pytest** | PASS | **Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing` **Result:** 1041/1041 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | PASS | `_current_source: str | None`, `_on_release: Callable[[str], None]`, `mouseMoveEvent(self, e: QMouseEvent) -> None`. All new parameters and return types annotated. No `Any` introduced. |
| **Dataclasses for value objects** | N/A | No new value objects. |
| **Protocols/ABCs for interfaces** | N/A | No new interfaces. Existing `ColumnsTabViewProtocol` unchanged. |
| **Avoid utility classes** | PASS | No utility classes added. Changes are to existing widget classes. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | PASS | No new exception paths. Guard clauses use early return, not exceptions, per Qt widget convention. |
| **Logging over print** | PASS | No print statements or new logging calls added. |
| **Invariants at construction** | PASS | `_current_source = None` and `_on_release = lambda _c: None` initialized in `__init__`. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | All tests use Pytest with `pytest-qt` (`qtbot` fixture). |
| **Coverage expectation** | PASS | Repo-wide: 99.1% line (>= 85%), 94.1% branch (>= 75%). Changed module: 94% line. `evidence/qa-gates/qa-coverage-comparison.md`. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | PASS | Each test targets a single method: `mouseMoveEvent` (assigned), `mouseMoveEvent` (unassigned), `dropEvent` (pool), `dragEnterEvent` (rejection). |
| **Mocking sparingly** | PASS | Only `QDrag` is stubbed (prevents headless drag loop). Event objects duck-typed with minimal stubs providing only `mimeData()` and `acceptProposedAction()`. |
| **Organization** | PASS | `tests/gui/test_columns_tab_widgets.py` mirrors `src/gui/widgets/_columns_tab_drag.py`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | PASS | `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`, `test_unassigned_row_mousemove_does_not_start_drag`, `test_pool_dropEvent_with_canonical_origin_calls_clear_row`, `test_pool_dragEnterEvent_rejects_missing_canonical_origin`. All follow `test_<subject>_<action>_<expected>` pattern. |
| **Docstrings/comments** | PASS | All 4 new tests have docstrings noting the covered scenario and AC cross-reference. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | **Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing` **Result:** 1041 passed. |
| **No Alternative Test Runners** | PASS | Only Pytest used. |

---

## 5. Test Coverage Detail

### ColumnDropRow.mouseMoveEvent (2 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` | Positive | 254-274 | PASS |
| `test_unassigned_row_mousemove_does_not_start_drag` | Negative (guard clause) | 265-266 (early return) | PASS |

**Coverage:** ~94% of `_columns_tab_drag.py` (4 missed lines are drag-exec branch exits requiring real drag loop)

### ColumnsTabWidget.dragEnterEvent / dropEvent (2 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_pool_dropEvent_with_canonical_origin_calls_clear_row` | Positive | 363-374 | PASS |
| `test_pool_dragEnterEvent_rejects_missing_canonical_origin` | Negative | 352-361 (reject branch) | PASS |

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 1041 | PASS |
| Tests Passed | 1041 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | Not reported in evidence | N/A |
| Functions/Classes Tested | All new public methods covered | PASS |
| Test File Size | 371 lines | PASS (under 500) |
| Code Coverage | 99.1% lines, 94.1% branches | PASS |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | Clean (2 files reformatted, confirmed clean) | PASS |
| Ruff Linting | `poetry run ruff check .` | 0 errors (2 I001 auto-fixed) | PASS |
| Pyright Type Checking | `poetry run pyright` | 0 errors, 0 warnings | PASS |
| Pytest Tests | `poetry run pytest --cov --cov-branch --cov-report=term-missing` | 1041 passed, 0 failed | PASS |

---

## 8. Gaps and Exceptions

### Identified Gaps

**None.** All policy requirements are met.

### Approved Exceptions

The `type: ignore` suppressions in `test_columns_tab_widgets.py` (`[arg-type]`, `[misc, assignment]`, `[method-assign]`) are test-scope Qt duck-typing patterns. `[arg-type]` on stub event objects is an unavoidable consequence of stub duck-typing; the stubs satisfy the runtime interface. `[misc, assignment]` on QDrag monkey-patching is the standard pattern for headless Qt drag testing in this repository (identical to `test_source_token_starts_drag_on_left_button_move` which pre-dates this change). `[method-assign]` on `clear_row` lambda replacement tests the monkey-patching mechanism used in production. No production code suppressions are present.

### Removed/Skipped Tests

**None.** All planned tests implemented. 8 pre-existing tests pass unchanged.

---

## 9. Summary of Changes

### Commits in This PR/Branch

1. `50919cd` — fix(gui): add bidirectional drag to Columns tab (#64)

### Files Modified

1. **`src/gui/widgets/_columns_tab_drag.py`** (MODIFIED, 441→499 lines)
   - Added module-level `CANONICAL_ORIGIN_MIME` constant (public, exported)
   - Added `_current_source: str | None = None` instance variable to `ColumnDropRow.__init__`
   - Updated `ColumnDropRow.set_assignment` to track `_current_source`
   - Added `ColumnDropRow.mouseMoveEvent` drag-source method
   - Added `ColumnsTabWidget.setAcceptDrops(True)`, `_on_release` callback, `clear_row` method, `dragEnterEvent`, `dropEvent`

2. **`src/gui/widgets/_schema_builder_drag_tabs.py`** (MODIFIED, 308 lines, +1 line)
   - Added `columns_widget.clear_row = self._columns_presenter.clear_row` binding in `DragTabBinder.__init__`

3. **`tests/gui/test_columns_tab_widgets.py`** (MODIFIED, 189→371 lines)
   - Added 4 new widget-seam tests covering new drag paths

---

## 10. Compliance Verdict

### Overall Status: FULLY COMPLIANT

All toolchain stages pass (Black, Ruff, Pyright, Pytest). Coverage is above thresholds at all levels. The 499-line count for `_columns_tab_drag.py` is within the 500-line limit. The `type: ignore` suppressions in the test file are standard test-scope Qt duck-typing patterns consistent with pre-existing usage in the same test file.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes: Issue defined, plan documented
- PASS Design Principles: Simple, minimal, separation of concerns maintained
- PASS Module & File Structure: All files under 500 lines, cohesive
- PASS Naming, Docs, Comments: All new methods documented, intent comments present
- PASS Toolchain Execution: All four stages clean
- PASS Summarize & Document: Commit message and feature folder complete

#### Language-Specific Code Change Policy (Section 3)

**For Python:**
- PASS Tooling & Baseline: All four tools clean
- PASS Python Design & Typing: Full type annotations, no `Any`
- PASS Error Handling: Guard clauses, no new exceptions, no print statements

#### General Unit Test Policy (Section 1)
- PASS Core Principles: Independent, isolated, deterministic, fast, readable
- PASS Coverage & Scenarios: 99.1%/94.1% repo-wide; positive, negative, edge cases covered
- PASS Test Structure: AAA pattern, clear assertions, documented intent
- PASS External Dependencies: No network, filesystem, or external process access
- PASS Policy Audit: This document

#### Language-Specific Unit Test Policy (Section 4)

**For Python:**
- PASS Framework & Scope: Pytest with pytest-qt; thresholds met
- PASS Test Style & Structure: Focused, minimal mocking, mirrors code structure
- PASS Naming & Readability: Descriptive names, docstrings, AC cross-references
- PASS Toolchain: `poetry run pytest` 1041/1041 passed

---

### Metrics Summary

- PASS 1041/1041 tests passing (100%)
- PASS 99.1% line coverage (threshold: 85%)
- PASS 94.1% branch coverage (threshold: 75%)
- PASS All changed files under 500-line limit
- PASS All code quality checks passing (Black, Ruff, Pyright)

---

### Recommendation

**Ready for merge** — All policy gates pass. No blocking findings. No remediation required.

---

## Appendix A: Test Inventory

### New tests added in this branch (4)

- `tests/gui/test_columns_tab_widgets.py::test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`
- `tests/gui/test_columns_tab_widgets.py::test_unassigned_row_mousemove_does_not_start_drag`
- `tests/gui/test_columns_tab_widgets.py::test_pool_dropEvent_with_canonical_origin_calls_clear_row`
- `tests/gui/test_columns_tab_widgets.py::test_pool_dragEnterEvent_rejects_missing_canonical_origin`

### Pre-existing tests (passing unchanged)

- `tests/gui/test_columns_tab_widgets.py::test_columns_tab_wraps_widget_in_resizable_scroll_area`
- `tests/gui/test_columns_tab_widgets.py::test_pool_renders_one_token_per_source_column`
- `tests/gui/test_columns_tab_widgets.py::test_rows_display_name_description_and_dtype`
- `tests/gui/test_columns_tab_widgets.py::test_drop_gesture_invokes_assign_column_once`
- `tests/gui/test_columns_tab_widgets.py::test_dtype_indicator_shows_green_for_coercible`
- `tests/gui/test_columns_tab_widgets.py::test_dtype_indicator_shows_red_with_masked_example`
- `tests/gui/test_columns_tab_widgets.py::test_source_token_starts_drag_on_left_button_move`
- `tests/gui/test_columns_tab_widgets.py::test_drop_row_drag_enter_accepts_text_payload`

---

## Appendix B: Toolchain Commands Reference

```bash
# Formatting
poetry run black .

# Linting
poetry run ruff check .

# Type checking
poetry run pyright

# Testing
poetry run pytest --cov --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** Feature Review Agent (Claude Sonnet 4.6)
**Audit Date:** 2026-06-15
**Policy Version:** Current (as of audit date)

## Evidence Location Compliance

Scan result: no files under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` were introduced by this branch. All evidence artifacts are written to `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/` (canonical location). Verdict: PASS.
