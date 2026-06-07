# Policy Compliance Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 1 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T21-27
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `7b8994c` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Code Under Test:** full branch diff `main...HEAD` (114 files; Python + JSON only)

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 64 src/test files | 932 tests | ✅ 932 pass, 0 fail | 98.4% lines, 94.4% branch | 98.7% lines, 94.0% branch | 93–100% (executable feature modules); two TYPE_CHECKING-only protocol modules at 0% — see finding P-2 |
| JSON | 2 schema files | N/A | ✅ load without error (tests/test_default_schemas.py) | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- TypeScript post-change coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- PowerShell baseline coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- PowerShell post-change coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- Python baseline coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-pytest.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.md`; live re-run by this reaudit at HEAD `7b8994c`
- Per-language comparison summary: see section 1.2.1

**Non-negotiable verdict rule:** numeric baseline and post-change coverage are present for the only in-scope language (Python). JSON has no coverage requirement.

---

## Executive Summary

This is the EXIT reaudit of remediation cycle 1 for issue #50. The cycle-entry audit (`*.2026-06-05T20-28.md`) reported blocking_count=6 (R1–R6: a class of defect where new drag-drop tabs, the derived-formula dialog, `BuildSpecProvider`, `new_from_template`, and `on_partial_match` were unit-tested in isolation but never wired into the live `SchemaBuilderDialog` or `build_application`).

All six remediation findings (R1–R6) are now wired into production call sites reachable from `build_application` or the opened `SchemaBuilderDialog`, and each is backed by an integrated test that drives the production object (not an isolated widget/presenter unit test). The full Python toolchain is green at HEAD `7b8994c` (Black, Ruff, Pyright 0 errors, 932 pytest pass), the masking scan is clean, no unauthorized suppressions were added, and repo-wide coverage exceeds thresholds (98.7% line, 94.0% branch).

One blocking finding remains: **P-1** — `tests/gui/test_schema_builder_presenter.py` is 506 lines, exceeding the 500-line cap (`general-code-change.md` File Size Limit). The cycle was tasked with eliminating a file-size violation (N1) but introduced a new one in a file it heavily modified (229 → 506 lines), and the executor's own P7-T8 file-size evidence omitted this file.

**Policy documents evaluated:**
- ✅ `general-code-change.md` (cross-language code change policy)
- ✅ `general-unit-test.md` (cross-language unit test policy)

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A PowerShell (no PowerShell files in branch diff)
- N/A Bash (no Bash files in branch diff)
- ✅ JSON (two bundled schema files migrated; load-validated)

**Temporary artifacts cleanup:**
- ✅ No temporary/throwaway scripts left behind. `scripts/checks/scan_masked_fixtures.py` is a permanent, tested confidentiality tool added this feature (covered by tests/check usage).

---

## Rejected Scope Narrowing

None. The caller prompt directed a full branch-vs-base audit and did not attempt to narrow scope to any plan, task, phase, or file subset. The audit scope is the full `main...HEAD` diff.

---

## Evidence Location Compliance

A git-diff scan for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned no matches (`NO_NONCANONICAL_EVIDENCE_PATHS`). All evidence is under the canonical `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/` tree. The repository does not ship `scripts/validate_evidence_locations.py`; a git-diff scan was used as the substitute per the established convention. No evidence-location violations. No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | 932 tests pass in a single pytest run; GUI tests use `qtbot` fixtures and per-test dialog/`build_application` construction; no inter-test shared mutable state observed. |
| **Isolation** - Each test targets single behavior | ✅ PASS | Integrated tests added this cycle each assert one wiring outcome (e.g., `test_live_columns_tab_has_drag_tokens_and_dtype_indicators`). |
| **Fast Execution** - Tests complete quickly | ✅ PASS | Full suite ran in 22.46s for 932 tests under `QT_QPA_PLATFORM=offscreen`. |
| **Determinism** - Consistent results | ✅ PASS | Qt offscreen platform; no wall-clock/RNG dependence in changed tests; dialog `exec` monkeypatched in derived-dialog test rather than real modal loop. |
| **Readability & Maintainability** - Clear structure | ⚠️ PARTIAL | Tests are well-named and AAA-structured, but `tests/gui/test_schema_builder_presenter.py` is 506 lines (> 500-line cap). See finding P-1. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | **Baseline (remediation P0-T5):** 98.4% lines, 94.4% branch. **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch`. **Timestamp:** 2026-06-05 20:28. |
| **No Coverage Regression** | ✅ PASS | **Post-change:** 98.7% lines, 94.0% branch. **Change:** +0.3% lines, -0.4% branch. The branch dip is from newly-added defensive Qt-guard branches, not regression on previously-covered lines; line coverage increased. Re-verified live at HEAD `7b8994c`. |
| **New Code Coverage ≥85% line / ≥75% branch** | ⚠️ PARTIAL | Executable feature modules: 93–100% (e.g., `_schema_builder_drag_tabs.py` 96%, `_schema_provider_factory.py` 95%, `_schema_open_helpers.py` 93%, `_columns_tab_drag.py` 95%, `_key_tab_drag.py` 86%, `schema_builder_dialog.py` 98%). Two new modules `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` report 0% (TYPE_CHECKING-only `typing.Protocol` contracts, never imported at runtime). See finding P-2 (non-blocking). |
| **Comprehensive Coverage** | ✅ PASS | R1–R6 seams each exercised by an integrated test driving the production object; positive/negative/edge paths covered (no-match, partial-match, blank menu path, seeded per-tab path). |
| **Positive Flows** | ✅ PASS | e.g., `test_build_application_per_tab_button_seeds_via_injected_provider` (seeded path). |
| **Negative Flows** | ✅ PASS | e.g., `test_wire_build_buttons_blank_path_without_provider`; `test_on_schema_discovery_no_match_sets_placeholder`. |
| **Edge Cases** | ✅ PASS | Partial-match band, unknown discriminator rejection, empty-header guard. |
| **Error Handling** | ✅ PASS | Reader value-error routes to show_error; invalid formula surfaces FormulaError through the existing evaluator. |
| **Concurrency** | N/A | Not applicable to the dialog/wiring changes in this cycle. |
| **State Transitions** | ✅ PASS | Import-gate enable/disable on schema selection and placeholder return covered. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98.4% line / 94.4% branch -> Post-change: 98.7% line / 94.0% branch. Change: +0.3% line / -0.4% branch. New/changed-code coverage: 93–100% for executable feature modules; two TYPE_CHECKING-only protocol modules at 0% (non-executable contracts). Disposition: PASS (thresholds line ≥85% and branch ≥75% both hold; no regression on previously-covered lines). Evidence: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.md` plus this reaudit's live re-run at HEAD `7b8994c`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero PowerShell files in branch diff).
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero TypeScript files in branch diff).
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero C# files in branch diff).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Behavioral assertions on widget tree (`findChild`), `token_names()`, `parts_text()`, presenter state. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Integrated tests follow Arrange (build app/dialog), Act (trigger signal), Assert (production state). |
| **Document Intent** | ✅ PASS | Descriptive `test_*` names referencing the R#/AC they prove. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | Fake schema services and synchronous runners injected; no network/DB. |
| **Use Mocks/Stubs** | ✅ PASS | `FakeSchemaService`, `SynchronousRunner`, recording dialog/presenter factories; `monkeypatch` for dialog `exec`. |
| **Environment Stability** | ✅ PASS | `QT_QPA_PLATFORM=offscreen`; no runtime temp-file creation introduced; masking scan clean. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This artifact is the required review for the exit reaudit. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Cycle scope = R1–R6 wiring + N1–N3, per `remediation-inputs.2026-06-05T20-28.md`. |
| **Read existing change plans** | ✅ PASS | `remediation-plan.2026-06-05T20-28.md` (41 tasks) executed; phase-0 policy-read evidence present. |
| **Document the plan** | ✅ PASS | Remediation plan + evidence tree under canonical paths. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | Wiring reuses existing seams via a single shared `open_schema_builder` path for both menu and per-tab buttons. |
| **Reusability** | ✅ PASS | `open_new_from_template_builder` shared by R5 affordance and R6 partial-match hand-off; `DragTabBinder` centralizes column/key routing. |
| **Extensibility** | ✅ PASS | `BuildSpecProvider` is a Protocol; keyword-only seeding params with defaults preserve the blank menu path. |
| **Separation of concerns** | ✅ PASS | Pure dtype/matching logic kept out of Qt widgets; presenters drive passive views; provider factory isolates composition-root construction. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | Four Phase-5 helper extractions (`_schema_builder_drag_tabs.py`, `_schema_provider_factory.py`, `_schema_open_helpers.py`, `_source_signal_wiring.py`) each have a single, documented purpose. |
| **Under 500 lines** | ❌ FAIL | `tests/gui/test_schema_builder_presenter.py` = 506 lines (> 500). All production files ≤ 500 (largest: `app.py` 490, `schema_builder_dialog.py` 489). See finding P-1. |
| **Public vs internal** | ✅ PASS | Internal modules `_`-prefixed; `__all__` declared. |
| **No circular dependencies** | ✅ PASS | Pyright strict passes (0 errors); cross-module imports use TYPE_CHECKING where needed. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | snake_case functions, PascalCase classes; intent-revealing names. |
| **Docs/docstrings** | ✅ PASS | Class and function docstrings present on new/changed modules with Args/Returns/Side effects. |
| **Comment why, not what** | ✅ PASS | Decision-logic comments cite Decisions 2/4/5/6/7 and explain branch rationale. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check .` → `220 files would be left unchanged`, EXIT 0 (reaudit live run). |
| **2. Linting** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check .` → `All checks passed!`, EXIT 0. |
| **3. Type checking** | ✅ PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright` → `0 errors, 0 warnings, 0 informations`, EXIT 0. |
| **4. Testing** | ✅ PASS | **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` → `932 passed`, EXIT 0. |
| **Full toolchain loop** | ✅ PASS | All four stages green in a single pass at HEAD `7b8994c`. |
| **Explicit reporting** | ✅ PASS | Commands and results documented here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Remediation plan + traceability evidence. |
| **Design choices explained** | ✅ PASS | Decisions referenced in code and spec. |
| **Update supporting documents** | ✅ PASS | spec.md Decision 1 / AC 14 reconciled (N3). |
| **Provide next steps** | ✅ PASS | This reaudit lists the remaining blocking item. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `black --check .` EXIT 0, 220 files unchanged. |
| **Linting with Ruff** | ✅ PASS | `ruff check .` EXIT 0, all checks passed. |
| **Type checking with Pyright** | ✅ PASS | `pyright` 0 errors (strict mode). |
| **Testing with Pytest** | ✅ PASS | 932 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | Full annotations; strict Pyright clean; no new `Any`. |
| **Dataclasses for value objects** | ✅ PASS | Tab control bundles and `CallerBuildSpec` are dataclasses. |
| **Protocols/ABCs for interfaces** | ✅ PASS | `BuildSpecProvider`, `ColumnsTabViewProtocol`, `KeyTabViewProtocol` are `typing.Protocol`. |
| **Avoid utility classes** | ✅ PASS | Module-level functions for wiring/open-path helpers. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | Formula validation reuses `FormulaError`; no broad catches added (suppression scan clean). |
| **Logging over print** | ✅ PASS | No ad-hoc print added. |
| **Invariants at construction** | ✅ PASS | Discriminator dropdown-only enforces the existing-column invariant. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | pytest + pytest-qt (`qtbot`). |
| **Coverage expectation** | ⚠️ PARTIAL | Repo-wide 98.7% line / 94.0% branch (≥ thresholds). Executable new modules 93–100%; two TYPE_CHECKING-only protocol modules at 0% (P-2, non-blocking). |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | Fakes/recorders for service/runner; real pure code paths preferred. |
| **Organization** | ⚠️ PARTIAL | Mirrors code structure; one test file over the 500-line cap (P-1). |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_*` names. |
| **Docstrings/comments** | ✅ PASS | Integrated tests carry intent docstrings citing R#/AC. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `pytest --cov --cov-branch` → 932 passed. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### R1–R6 Production Wiring (integrated tests)

| Test Name | Scenario Type | Proves | Status |
|-----------|--------------|--------|--------|
| `test_live_columns_tab_has_drag_tokens_and_dtype_indicators` | Positive | R1: live dialog Columns tab is `ColumnsTabWidget` with tokens + dtype indicators | ✅ |
| `test_live_key_tab_has_drag_widget_with_seeded_parts` | Positive | R2: live dialog Key tab is `KeyTabWidget` with seeded parts + Generic Text | ✅ |
| `test_live_derived_button_adds_column_to_columns_tab` | Positive | R3: Derived button opens real `DerivedFormulaDialog`, accepted column surfaces on Columns | ✅ |
| `test_build_application_per_tab_button_seeds_via_injected_provider` | Positive | R4: `build_application` injects `BuildSpecProvider`; per-tab seeds, menu blank | ✅ |
| `test_build_application_new_from_template_seeds_live_dialog` | Positive | R5: `new_from_template` reached, dialog seeded from template, blank name | ✅ |
| `test_build_application_partial_match_reaches_new_from_template` | Positive/Edge | R6: partial match through `build_application` invokes `on_partial_match` | ✅ |

**Production-caller evidence (grep at HEAD `7b8994c`):** `new_from_template(` → `src/gui/_schema_open_helpers.py:159`; `on_partial_match=` → `src/gui/app.py:335,342,349`; `build_spec_provider(` → `src/gui/app.py:430`; `wire_build_schema_buttons(...spec_provider=)` → `src/gui/_schema_discovery_wiring.py:82`; `DerivedFormulaDialog` opened via `install_new_derived_handler` from the shared `open_schema_builder` path (`_schema_wiring.py:153`); `ColumnsTabWidget`/`KeyTabWidget` constructed in `build_columns_tab`/`build_key_tab` (`_schema_builder_tabs.py:186,206`), replacing the prior `QPlainTextEdit`/`QLineEdit` editors.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 932 | ✅ |
| Tests Passed | 932 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | 22.46s total | ✅ Fast |
| Code Coverage | 98.7% lines, 94.0% branches | ✅ |
| Largest changed test file | 506 lines (`test_schema_builder_presenter.py`) | ❌ Over cap |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | 220 files unchanged | ✅ |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed | ✅ |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors | ✅ |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` | 932 passed | ✅ |
| Confidentiality masking scan | `python scripts/checks/scan_masked_fixtures.py` | clean (no forbidden patterns) | ✅ |
| Suppression scan (added lines) | git-diff grep `noqa|type: ignore|pyright: ignore` | NO_SUPPRESSIONS_ADDED | ✅ |
| Workflow change scan | git-diff `.github/workflows/**` | NO_WORKFLOW_CHANGES | ✅ |

**Notes:** No `.github/workflows/**` change is present, so `modified-workflow-needs-green-run` does not apply. Confidentiality: AOP retains `mode: none` (null discriminator); LE migrated to `aggregate` (discriminator `YTD/YTG`) — consistent with spec Decision 1 / AC 14.

---

## 8. Gaps and Exceptions

### Identified Gaps

- **P-1 (BLOCKING / FAIL):** `tests/gui/test_schema_builder_presenter.py:1-506` exceeds the 500-line cap by 6 lines (grew from 229 lines on `main` to 506). Violates `general-code-change.md` File Size Limit (applies to test code). The remediation cycle's own P7-T8 file-size evidence (`evidence/qa-gates/final-file-sizes.md`) omits this file. Plan: split into focused modules (e.g., presenter-state tests vs. seeding/new-from-template tests), preserving all tests.
- **P-2 (NON-BLOCKING / PARTIAL):** `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` report 0% line coverage. Both are pure `typing.Protocol` contracts imported only inside `TYPE_CHECKING` blocks (never imported at runtime); the `...` method bodies are excluded by coverage config, so the only counted lines are non-executable signature lines. The behavior is implemented and well-covered in the concrete widgets/presenters (`_columns_tab_drag.py` 95%, `_columns_tab_presenter.py` 93%, `_key_tab_presenter.py` 100%). No untested critical behavior. Recommended (non-blocking): add `# pragma: no cover` to these contract modules or a thin runtime import so the coverage figure reflects their type-only nature.

### Approved Exceptions

**None.** No exceptions needed.

### Removed/Skipped Tests

**None.** All planned tests implemented; the N1 split preserved the prior serialization test set.

---

## 9. Summary of Changes

### Commits in This PR/Branch

- HEAD `7b8994c` — remediation cycle 1 (R1–R6 wiring, N1–N3, Phase-5 helper extractions). Prior cycle entry head was `d8275d9`.

### Files Modified (high level)

1. `src/gui/widgets/_schema_builder_tabs.py` (MODIFIED) — Columns/Key tabs build `ColumnsTabWidget`/`KeyTabWidget`; Derived tab adds "New derived column" button.
2. `src/gui/widgets/schema_builder_dialog.py` (MODIFIED) — constructs `DragTabBinder`; exposes `set_new_derived_handler`; routes column/key setters/getters through the binder.
3. `src/gui/widgets/_schema_builder_drag_tabs.py` (NEW) — `DragTabBinder` driving the tab presenters.
4. `src/gui/_schema_open_helpers.py` (NEW) — `install_new_derived_handler`, `seed_dialog_preview_slice`, `open_new_from_template_builder`.
5. `src/gui/_schema_provider_factory.py` (NEW) — production `BuildSpecProvider` (`build_spec_provider`).
6. `src/gui/_source_signal_wiring.py` (NEW) — source-signal wiring extraction.
7. `src/gui/app.py` (MODIFIED) — constructs/injects provider; passes `on_partial_match` to the three `SourceSelectionPresenter` constructions.
8. `src/schemas/default_le.schema.json` / `default_aop.schema.json` (MODIFIED) — forward migration (LE → aggregate, AOP retains none).
9. `tests/...` (NEW/MODIFIED) — integrated tests for R1–R6; N1 serialization split.

---

## 10. Compliance Verdict

### Overall Status: ⚠️ PARTIALLY COMPLIANT (1 BLOCKING FAIL)

R1–R6 are correctly wired into production and integration-tested; the toolchain is green; coverage, confidentiality, and suppression policy are satisfied. One blocking finding remains: a test file exceeds the 500-line cap (P-1).

**Fail-closed reminder:** This audit is NOT marked PASS/ready-for-merge because finding P-1 is an unresolved blocking policy violation.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes
- ✅ Design Principles
- ❌ Module & File Structure (P-1: 506-line test file over cap)
- ✅ Naming, Docs, Comments
- ✅ Toolchain Execution
- ✅ Summarize & Document

#### Language-Specific Code Change Policy (Section 3) — Python
- ✅ Tooling & Baseline
- ✅ Python Design & Typing
- ✅ Error Handling

#### General Unit Test Policy (Section 1)
- ✅ Core Principles (one PARTIAL on maintainability tied to P-1)
- ⚠️ Coverage & Scenarios (P-2 non-blocking)
- ✅ Test Structure
- ✅ External Dependencies
- ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4) — Python
- ✅ Framework & Scope (P-2 non-blocking)
- ⚠️ Test Style & Structure (P-1)
- ✅ Naming & Readability
- ✅ Toolchain

### Metrics Summary

- ✅ 932/932 tests passing (100%)
- ✅ 98.7% line coverage, 94.0% branch coverage (≥ 85% / ≥ 75%)
- ✅ Black / Ruff / Pyright all clean at HEAD `7b8994c`
- ✅ Masking scan clean; no suppressions added; no workflow change
- ❌ One test file over the 500-line cap (P-1)

### Recommendation

**Needs revision (one blocking item).** Split `tests/gui/test_schema_builder_presenter.py` (506 → ≤ 500 lines) preserving all tests, then re-run the toolchain. All other policy requirements are satisfied.

---

## Appendix A: Test Inventory

Representative integrated tests proving R1–R6 (full suite: 932 tests):

- tests/gui/test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators
- tests/gui/test_schema_builder_dialog.py::test_live_key_tab_has_drag_widget_with_seeded_parts
- tests/gui/test_schema_builder_dialog.py::test_live_derived_button_adds_column_to_columns_tab
- tests/gui/test_app_wiring_schema.py::test_build_application_per_tab_button_seeds_via_injected_provider
- tests/gui/test_app_wiring_schema.py::test_build_application_new_from_template_seeds_live_dialog
- tests/gui/test_source_selection_presenter.py::test_build_application_partial_match_reaches_new_from_template

## Appendix B: Toolchain Commands Reference

```bash
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
python scripts/checks/scan_masked_fixtures.py
```

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-05
**Policy Version:** Current (as of audit date)
