# Policy Compliance Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 2 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T22-04
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `fd8a022` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Code Under Test:** full branch diff `main...HEAD` (Python + JSON only). Cycle-2 commit diff is `7b8994c..fd8a022`.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | src + test files | 932 tests | 932 pass, 0 fail | 98.4% lines, 94.4% branch (cycle-1 baseline) | 98% lines, 94.0% branch | 86–100% (executable feature modules); two TYPE_CHECKING-only protocol modules now omitted from the report (N4 closed) |
| JSON | 2 schema files | N/A | load without error (tests/test_default_schemas.py) | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- TypeScript post-change coverage artifact: `N/A - out of scope` (no TypeScript files in branch diff)
- PowerShell baseline coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- PowerShell post-change coverage artifact: `N/A - out of scope` (no PowerShell files in branch diff)
- Python baseline coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-pytest.2026-06-05T21-27.md`
- Python post-change coverage artifact: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T21-27.md`; live re-run by this reaudit at HEAD `fd8a022`
- Per-language comparison summary: see section 1.2.1

**Non-negotiable verdict rule:** numeric baseline and post-change coverage are present for the only in-scope language (Python). JSON has no coverage requirement.

---

## Executive Summary

This is the EXIT reaudit of remediation cycle 2 for issue #50. The cycle-entry inputs (`remediation-inputs.2026-06-05T21-27.md`) carried blocking_count=1 (B1: `tests/gui/test_schema_builder_presenter.py` at 506 lines, over the 500-line cap) plus one non-blocking finding (N4: two TYPE_CHECKING-only protocol modules reporting 0% coverage).

Both findings are now closed at HEAD `fd8a022`:

- **B1 (closed):** `tests/gui/test_schema_builder_presenter.py` no longer exists. It was split into `tests/gui/test_schema_builder_presenter_core.py` (310 lines), `tests/gui/test_schema_builder_presenter_seeding.py` (156 lines), and a shared helper module `tests/gui/_schema_builder_presenter_fixtures.py` (83 lines). All three are well under the 500-line cap. The split preserved every test: pre-split 18 `test_` functions + 1 parametrize block (3 cases) + 51 asserts; post-split combined 18 `test_` functions + 1 parametrize block (3 cases) + 51 asserts. No assertion was deleted or weakened; no skip/xfail was introduced.
- **N4 (closed):** No `# pragma: no cover` remains in `src/gui/_columns_tab_protocol.py` or `src/gui/_key_tab_protocol.py`. Both are added to `[tool.coverage.run].omit` in `pyproject.toml` and no longer appear as rows in the coverage report. This is a non-behavioral coverage-config change.

Cycle 2 touched no production source: the cycle-2 commit diff (`7b8994c..fd8a022`) contains only `pyproject.toml`, the three split test files, and memory/docs artifacts. The cycle-1 R1–R6 production wiring is therefore unchanged and remains intact (spot-checked at HEAD). The full Python toolchain is green at HEAD `fd8a022` (Black, Ruff, Pyright 0 errors, 932 pytest pass), the masking scan is clean, no unauthorized suppressions were added, and repo-wide coverage exceeds thresholds (98% line, 94.0% branch). No `.github/workflows/**` or `scripts/benchmarks/**` files changed across the whole feature diff, so `modified-workflow-needs-green-run` does not apply.

**Policy documents evaluated:**
- `general-code-change.md` (cross-language code change policy)
- `general-unit-test.md` (cross-language unit test policy)

**Language-specific policies evaluated:**
- `python.md` + `python-suppressions.md`
- N/A PowerShell (no PowerShell files in branch diff)
- N/A Bash (no Bash files in branch diff)
- JSON (two bundled schema files migrated; load-validated)

**Temporary artifacts cleanup:**
- No temporary/throwaway scripts left behind. `scripts/checks/scan_masked_fixtures.py` is a permanent, tested confidentiality tool.

---

## Rejected Scope Narrowing

None. The caller prompt directed a full branch-vs-base audit and did not attempt to narrow scope to any plan, task, phase, or file subset. The audit scope is the full `main...HEAD` diff; the cycle-2 commit diff (`7b8994c..fd8a022`) is the delta under remediation review.

---

## Evidence Location Compliance

A git-diff scan over `main...HEAD` for files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` returned no matches (`NO_NONCANONICAL_EVIDENCE_PATHS`). All evidence is under the canonical `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/` tree. The repository does not ship `scripts/validate_evidence_locations.py`; a git-diff scan was used as the substitute per the established convention. No evidence-location violations. No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | PASS | 932 tests pass in a single pytest run at HEAD `fd8a022`; GUI tests use `qtbot` fixtures; no inter-test shared mutable state. |
| **Isolation** - Each test targets single behavior | PASS | Split presenter tests retain one-behavior-per-test structure; shared helpers extracted to `_schema_builder_presenter_fixtures.py`. |
| **Fast Execution** - Tests complete quickly | PASS | Full suite ran in 24.09s for 932 tests under `QT_QPA_PLATFORM=offscreen`. |
| **Determinism** - Consistent results | PASS | Qt offscreen platform; no wall-clock/RNG dependence in changed tests. |
| **Readability & Maintainability** - Clear structure | PASS | The cycle-1 PARTIAL (506-line file) is resolved: the file is split into three sub-500-line modules with a shared fixtures module. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | PASS | **Baseline (remediation P0-T5):** 98.4% lines, 94.4% branch. **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch`. |
| **No Coverage Regression** | PASS | **Post-change (this reaudit, HEAD `fd8a022`):** 98% lines (TOTAL row), 94.0% branch. The test-split and protocol-omit are coverage-neutral on executable lines; no regression on changed lines. |
| **New Code Coverage >=85% line / >=75% branch** | PASS | All changed executable modules >= 86% line (lowest: `_key_tab_drag.py` 86%; others 93–100%). The two protocol modules are now omitted (N4 closed) and no longer appear as 0% rows. |
| **Comprehensive Coverage** | PASS | R1–R6 seams remain exercised by the cycle-1 integrated tests (unchanged); positive/negative/edge paths covered. |
| **Positive Flows** | PASS | e.g., `test_build_application_per_tab_button_seeds_via_injected_provider`. |
| **Negative Flows** | PASS | e.g., `test_on_schema_discovery_no_match_sets_placeholder`. |
| **Edge Cases** | PASS | Partial-match band, unknown discriminator rejection, blank menu path. |
| **Error Handling** | PASS | Reader value-error routes to show_error; invalid formula surfaces FormulaError. |
| **Concurrency** | N/A | Not applicable to the config/test-split changes in this cycle. |
| **State Transitions** | PASS | Import-gate enable/disable on schema selection covered. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98.4% line / 94.4% branch -> Post-change: 98% line / 94.0% branch. Change: coverage-neutral (test-split and protocol-omit do not change executable-line coverage). New/changed-code coverage: 86–100% for executable feature modules; two TYPE_CHECKING-only protocol modules now omitted from the report (N4 closed). Disposition: PASS (thresholds line >=85% and branch >=75% both hold; no regression on previously-covered lines). Evidence: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T21-27.md` plus this reaudit's live re-run at HEAD `fd8a022`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero PowerShell files in branch diff).
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero TypeScript files in branch diff).
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A - out of scope. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: N/A - out of scope (zero C# files in branch diff).

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | PASS | Behavioral assertions preserved verbatim in the split files. |
| **Arrange-Act-Assert Pattern** | PASS | AAA structure preserved by verbatim copy of test bodies. |
| **Document Intent** | PASS | Descriptive `test_*` names retained; new fixtures module carries a purpose docstring. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | PASS | Fakes/recorders injected; no network/DB. |
| **Use Mocks/Stubs** | PASS | `FakeSchemaBuilderView`, fake services; `monkeypatch` for dialog `exec`. |
| **Environment Stability** | PASS | `QT_QPA_PLATFORM=offscreen`; no runtime temp-file creation; masking scan clean. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | PASS | This artifact is the required review for the cycle-2 exit reaudit. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | PASS | Cycle scope = B1 (split) + N4 (coverage-omit), per `remediation-inputs.2026-06-05T21-27.md`. |
| **Read existing change plans** | PASS | `remediation-plan.2026-06-05T21-27.md` executed; phase-0 policy-read evidence present. |
| **Document the plan** | PASS | Remediation plan + evidence tree under canonical paths. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | PASS | N4 fixed with the minimal config change (omit list) rather than scattering pragmas. |
| **Reusability** | PASS | Shared helpers extracted once to `_schema_builder_presenter_fixtures.py`, imported by both split modules. |
| **Extensibility** | PASS | No public API change. |
| **Separation of concerns** | PASS | Core/state tests vs. seeding tests are now in separate cohesive modules. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | PASS | Core tests, seeding tests, and shared fixtures separated by responsibility. |
| **Under 500 lines** | PASS | All changed `.py` files <= 500 (largest changed file overall: `source_input_widget.py` 497; split outputs: core 310, seeding 156, fixtures 83). The 506-line over-cap original is removed (B1 closed). |
| **Public vs internal** | PASS | Internal modules `_`-prefixed; `__all__` declared on protocol modules. |
| **No circular dependencies** | PASS | Pyright passes (0 errors). |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | PASS | snake_case functions, PascalCase classes. |
| **Docs/docstrings** | PASS | Fixtures module and split test modules carry docstrings; protocol docstrings unchanged. |
| **Comment why, not what** | PASS | No new ad-hoc comments; pyproject omit entries are self-describing. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run black --check .` -> `222 files would be left unchanged`, EXIT 0 (reaudit live run at HEAD `fd8a022`). |
| **2. Linting** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run ruff check .` -> `All checks passed!`, EXIT 0. |
| **3. Type checking** | PASS | **Command:** `env -u VIRTUAL_ENV poetry run pyright` -> `0 errors, 0 warnings, 0 informations`, EXIT 0. |
| **4. Testing** | PASS | **Command:** `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` -> `932 passed`, EXIT 0. |
| **Full toolchain loop** | PASS | All four stages green in a single pass at HEAD `fd8a022`. |
| **Explicit reporting** | PASS | Commands and results documented here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | PASS | Remediation plan + traceability evidence. |
| **Design choices explained** | PASS | N4 omit-list rationale documented in the plan. |
| **Update supporting documents** | PASS | spec.md / user-story.md AC unchanged (cycle changed no features). |
| **Provide next steps** | PASS | This reaudit confirms the cycle exit condition is met. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | PASS | `black --check .` EXIT 0, 222 files unchanged. |
| **Linting with Ruff** | PASS | `ruff check .` EXIT 0, all checks passed. |
| **Type checking with Pyright** | PASS | `pyright` 0 errors (strict mode). |
| **Testing with Pytest** | PASS | 932 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | PASS | Split test files preserve type annotations; no new `Any`. |
| **Dataclasses for value objects** | PASS | Unchanged from cycle 1. |
| **Protocols/ABCs for interfaces** | PASS | `ColumnsTabViewProtocol`, `KeyTabViewProtocol` retain signatures; only coverage-omit added. |
| **Avoid utility classes** | PASS | Module-level helpers for shared fixtures. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | PASS | No error-handling change this cycle; suppression scan clean. |
| **Logging over print** | PASS | No ad-hoc print added. |
| **Invariants at construction** | PASS | Unchanged from cycle 1. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | pytest + pytest-qt (`qtbot`). |
| **Coverage expectation** | PASS | Repo-wide 98% line / 94.0% branch (>= thresholds). Executable changed modules 86–100%; protocol modules omitted (N4 closed). |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | PASS | One behavior per test, preserved through the split. |
| **Mocking sparingly** | PASS | Fakes/recorders for service/runner. |
| **Organization** | PASS | The cycle-1 over-cap file is resolved; no test file exceeds 500 lines. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | PASS | Descriptive `test_*` names retained verbatim. |
| **Docstrings/comments** | PASS | Test intent docstrings preserved by verbatim copy. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | PASS | `pytest --cov --cov-branch` -> 932 passed. |
| **No Alternative Test Runners** | PASS | Pytest only. |

---

## 5. Test Coverage Detail

### B1 — Test-split fidelity

| Metric | Pre-split (`7b8994c:test_schema_builder_presenter.py`) | Post-split (`core` + `seeding` + `fixtures`) | Status |
|--------|--------|--------|--------|
| File line count | 506 (over cap) | 310 / 156 / 83 (all <= 500) | PASS |
| `def test_` functions | 18 | 18 | PASS (parity) |
| `@pytest.mark.parametrize` blocks | 1 (3 cases) | 1 (3 cases) | PASS (parity) |
| `assert` statements | 51 | 51 | PASS (parity) |
| skip/xfail introduced | 0 | 0 | PASS |
| Original file present | yes (506) | removed | PASS (B1 closed) |

### N4 — Protocol-module coverage omit

| File | Pre-cycle | Post-cycle | Status |
|------|-----------|------------|--------|
| `src/gui/_columns_tab_protocol.py` | 0% row, no pragma present at `7b8994c` | omitted via `[tool.coverage.run].omit`; absent from report; no pragma | PASS (N4 closed) |
| `src/gui/_key_tab_protocol.py` | 0% row, no pragma present at `7b8994c` | omitted via `[tool.coverage.run].omit`; absent from report; no pragma | PASS (N4 closed) |

Note: the cycle-1 head (`7b8994c`) protocol files contained no `# pragma: no cover`, so the plan's "revert pragma" sub-step was a verified no-op; the end state contains no pragmas, which satisfies the N4 acceptance.

### R1–R6 production wiring (unchanged this cycle; spot-checked at HEAD `fd8a022`)

| Seam | Production call site | Status |
|------|---------------------|--------|
| R5 `new_from_template` | `src/gui/_schema_open_helpers.py:159` (`presenter.new_from_template(...)`) | INTACT |
| R6 `on_partial_match` | `src/gui/app.py:335,342,349` (passed to three `SourceSelectionPresenter` constructions) | INTACT |
| R4 `BuildSpecProvider` | `src/gui/app.py:430` (`spec_provider=build_spec_provider(_svc)`) | INTACT |
| R1 Columns drag tab | `src/gui/widgets/_schema_builder_tabs.py:186` (`ColumnsTabWidget()`) | INTACT |
| R2 Key drag tab | `src/gui/widgets/_schema_builder_tabs.py:206` (`KeyTabWidget()`) | INTACT |
| R3 Derived dialog | wired via shared open path (`_schema_wiring.py`) | INTACT |

Cycle-2 commit diff (`7b8994c..fd8a022`) contains zero `src/` production changes, confirming the wiring was not touched.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 932 | PASS |
| Tests Passed | 932 (100%) | PASS |
| Tests Failed | 0 | PASS |
| Execution Time | 24.09s total | PASS (fast) |
| Code Coverage | 98% lines, 94.0% branches | PASS |
| Largest changed test file | 494 lines (`test_app_wiring.py`); split outputs all <= 310 | PASS (under cap) |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `env -u VIRTUAL_ENV poetry run black --check .` | 222 files unchanged | PASS |
| Ruff Linting | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed | PASS |
| Pyright Type Checking | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors | PASS |
| Pytest Tests | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch` | 932 passed | PASS |
| Confidentiality masking scan | `python scripts/checks/scan_masked_fixtures.py` | clean (no forbidden patterns) | PASS |
| Suppression scan (added lines) | git-diff `7b8994c..fd8a022` grep `noqa\|type: ignore\|pyright: ignore` (code files) | NO_SUPPRESSIONS_ADDED | PASS |
| Workflow change scan | git-diff `main...HEAD` for `.github/workflows/**` and `scripts/benchmarks/**` | NO_WORKFLOW_CHANGES, NO_BENCHMARK_CHANGES | PASS |

**Notes:** No `.github/workflows/**` or `scripts/benchmarks/**` change is present across the whole feature diff, so `modified-workflow-needs-green-run` and the benchmark-baseline provenance rule do not apply. Confidentiality: changed `src/schemas/*.json` contain canonical column-name definitions (schema metadata) only, not real workbook data values.

---

## 8. Gaps and Exceptions

### Identified Gaps

**None blocking.** Both cycle-entry findings are closed:
- B1 (was BLOCKING / FAIL) is CLOSED: the 506-line test file is split into three sub-500-line modules with full test parity.
- N4 (was NON-BLOCKING / PARTIAL) is CLOSED: the two TYPE_CHECKING-only protocol modules are omitted from the coverage report; no pragmas remain.

### Approved Exceptions

**None.**

### Removed/Skipped Tests

**None.** The split preserved every test (18 functions, 3 parametrize cases, 51 asserts); no skip/xfail introduced.

---

## 9. Summary of Changes

### Commits in This PR/Branch

- HEAD `fd8a022` — remediation cycle 2 (B1 test split; N4 coverage-omit). Prior cycle head was `7b8994c`; feature base commit `d8275d9`.

### Files Modified This Cycle (`7b8994c..fd8a022`, excluding docs/memory)

1. `pyproject.toml` (MODIFIED) — added the two type-only protocol modules to `[tool.coverage.run].omit` (N4).
2. `tests/gui/test_schema_builder_presenter.py` -> `tests/gui/test_schema_builder_presenter_core.py` (RENAMED + reduced to 310 lines; core/state/edit-load/formula tests).
3. `tests/gui/test_schema_builder_presenter_seeding.py` (NEW, 156 lines; seeding / new-from-template tests).
4. `tests/gui/_schema_builder_presenter_fixtures.py` (NEW, 83 lines; shared helpers).

No production source, workflow, or benchmark files changed this cycle.

---

## 10. Compliance Verdict

### Overall Status: COMPLIANT (0 BLOCKING)

Both cycle-entry findings (B1, N4) are closed. R1–R6 production wiring is intact and untouched this cycle. The toolchain is green at HEAD `fd8a022`; coverage, confidentiality, suppression, evidence-location, and tonality policies are satisfied. No test file exceeds the 500-line cap.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- PASS Before Making Changes
- PASS Design Principles
- PASS Module & File Structure (B1 closed: all changed `.py` <= 500)
- PASS Naming, Docs, Comments
- PASS Toolchain Execution
- PASS Summarize & Document

#### Language-Specific Code Change Policy (Section 3) — Python
- PASS Tooling & Baseline
- PASS Python Design & Typing
- PASS Error Handling

#### General Unit Test Policy (Section 1)
- PASS Core Principles
- PASS Coverage & Scenarios (N4 closed)
- PASS Test Structure
- PASS External Dependencies
- PASS Policy Audit

#### Language-Specific Unit Test Policy (Section 4) — Python
- PASS Framework & Scope
- PASS Test Style & Structure (B1 closed)
- PASS Naming & Readability
- PASS Toolchain

### Metrics Summary

- 932/932 tests passing (100%)
- 98% line coverage, 94.0% branch coverage (>= 85% / >= 75%)
- Black / Ruff / Pyright all clean at HEAD `fd8a022`
- Masking scan clean; no suppressions added; no workflow/benchmark change
- All changed `.py` files <= 500 lines

### Recommendation

**Ready for PR/merge review.** Both blocking and non-blocking cycle-entry findings are resolved with full test parity and a green toolchain.

---

## Appendix A: Test Inventory

Representative integrated tests proving R1–R6 (full suite: 932 tests):

- tests/gui/test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators
- tests/gui/test_schema_builder_dialog.py::test_live_key_tab_has_drag_widget_with_seeded_parts
- tests/gui/test_schema_builder_dialog.py::test_live_derived_button_adds_column_to_columns_tab
- tests/gui/test_app_wiring_schema.py::test_build_application_per_tab_button_seeds_via_injected_provider
- tests/gui/test_app_wiring_schema.py::test_build_application_new_from_template_seeds_live_dialog
- tests/gui/test_source_selection_presenter.py::test_build_application_partial_match_reaches_new_from_template

Split presenter test modules (B1):
- tests/gui/test_schema_builder_presenter_core.py (310 lines, 13 test functions incl. parametrized formula test)
- tests/gui/test_schema_builder_presenter_seeding.py (156 lines, 5 test functions)
- tests/gui/_schema_builder_presenter_fixtures.py (83 lines, 2 shared helpers)

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
