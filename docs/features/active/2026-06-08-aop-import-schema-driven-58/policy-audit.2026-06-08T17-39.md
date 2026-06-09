# Policy Compliance Audit: aop-import-schema-driven (Issue #58)

**Audit Date:** 2026-06-08
**Code Under Test:**
- `src/gui/pipeline_service.py` (MODIFIED — `import_aop` rerouted to schema path; module-level `load_aop` import removed; 500 lines, at cap)
- `src/gui/_aop_schema_import.py` (NEW — schema-driven AOP import helper; 133 lines)
- `src/schema_loader.py` (MODIFIED, T1 — `load()` gains optional `resolver`/`is_tty`/`prompt`; 254 lines)
- `src/schemas/default_aop.schema.json` (MODIFIED — `fill_rules: []`, `header_row: 2`)
- Test files: `tests/aop_fixtures.py`, `tests/test_default_schemas.py`, `tests/test_schema_loader_core.py`, `tests/test_schema_loader_parity_aop.py`, `tests/gui/test_pipeline_service.py`, `tests/gui/test_pipeline_service_key_seam.py`, `tests/gui/integration/test_behavioral_composition.py`, `tests/gui/test_gui_integration.py`, `tests/gui/test_key_mismatch_dialog.py`

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 4 prod + 9 test | 998 tests | ✅ 998 pass, 0 fail | 99.08% lines, 93.96% branch | 99.08% lines, 93.96% branch | 100% (all 3 changed prod files) |
| JSON | 1 file | N/A | ✅ parse + round-trip + parity | N/A (data file) | N/A (data file) | N/A |

**Note:** No PowerShell, TypeScript, C#, or Bash files changed on this branch.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - no TypeScript files on branch`
- TypeScript post-change coverage artifact: `N/A - no TypeScript files on branch`
- PowerShell baseline coverage artifact: `N/A - no PowerShell files on branch`
- PowerShell post-change coverage artifact: `N/A - no PowerShell files on branch`
- Per-language comparison summary: see `### 1.2.1 Per-Language Coverage Comparison` below and `evidence/qa-gates/coverage-delta.md`. Python lcov verified independently at `artifacts/python/lcov.info`.

**Non-negotiable verdict rule:** Numeric baseline and post-change coverage metrics are present for the one in-scope language with coverage requirements (Python). Verified independently from `artifacts/python/lcov.info` (lcov.info mtime 2026-06-08 13:34 is newer than all three changed production source files; not stale).

---

## Executive Summary

This is a refactor (work mode `full-feature`, AC sources `spec.md` + `user-story.md`) that reroutes the GUI AOP import from the legacy arithmetic-validating `src.load_aop.load_aop` to the schema-driven `SchemaLoader(default_aop)`, removes per-row arithmetic identity validation and blank-total fill on the import path, and threads the issue #52 KEY-mismatch resolver seam through `SchemaLoader.load`.

The implementation is policy-compliant on toolchain (Black/Ruff/Pyright/Pytest all clean per executor evidence and independently confirmed coverage), suppressions (none added), docstrings/commenting (all new functions and the new module documented), dependency policy (no new deps), and the T1 obligations for `src/schema_loader.py` (a hypothesis property test for the resolver-forwarding path is present; coverage 100% line / 100% branch). The protected CLI loader path is confirmed unchanged via empty `git diff`.

One Blocking finding: two changed test files exceed the repository 500-line file-size cap, which the policy applies to test code, not only production code:
- `tests/test_schema_loader_core.py` — 501 lines (baseline 374; +127 this feature)
- `tests/gui/test_pipeline_service.py` — 638 lines (baseline 471; +167 this feature)

Both crossed the cap as a direct result of this feature's added tests. The executor's `file-size-final.md` evidence tracked only production files and did not surface these test-file regressions.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- ✅ `self-explanatory-code-commenting.md`
- ✅ `quality-tiers.md` (T1 obligations for `src/schema_loader.py`)
- ✅ `tonality.md` (authored docs)
- N/A PowerShell / TypeScript / C# / Bash (no such files on branch)

**Temporary artifacts cleanup:**
- ✅ No temporary or throwaway scripts created.
- N/A No development scripts introduced.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** | ✅ PASS | Tests use function-scoped fixtures and `monkeypatch`; no shared mutable module state. The `_patch_loaders` helper substitutes per-test in-memory buffers. |
| **Isolation** | ✅ PASS | Each AC test targets one behavior (e.g. `test_import_aop_imports_full_year_ytd_source`, `test_import_aop_imports_source_with_broken_totals`, `test_load_forwards_resolver_seams_to_resolve_key_on_divergence`). |
| **Fast Execution** | ✅ PASS | 998 tests run in the per-commit loop; all in-memory, no disk/network. Executor reports clean pytest in the toolchain loop. |
| **Determinism** | ✅ PASS | No wall-clock or RNG dependence in the changed tests; hypothesis property tests are seeded by the framework and reproducible on failure. In-memory `io.BytesIO` workbooks only. |
| **Readability & Maintainability** | ✅ PASS | Descriptive `test_...` names and AAA docstrings throughout the changed test files. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Baseline 99.08% lines / 93.96% branch (4730/4774 lines, 840/894 branch). Source: `evidence/baseline/pytest-coverage-baseline.md`. |
| **No Coverage Regression** | ✅ PASS | Post-change 99.08% lines / 93.96% branch (4749/4793 lines). Flat repo-wide; every changed/new production module at 100% line. Source: `evidence/qa-gates/coverage-delta.md`, independently verified against `artifacts/python/lcov.info`. |
| **New Code Coverage >= threshold** | ✅ PASS | `src/gui/_aop_schema_import.py` 17/17 lines (100%); `src/gui/pipeline_service.py` changed region 76/76 (100%); `src/schema_loader.py` 32/32 lines, 6/6 branch (100%). Parsed directly from `artifacts/python/lcov.info`. |
| **Comprehensive Coverage** | ✅ PASS | `import_aop_via_schema`, the `SchemaLoader.load` seam, the broken-total / blank-total / header-detection paths all have dedicated tests (see Section 5). |
| **Positive Flows** | ✅ PASS | Full-year-YTD and partial-year-YTD imports; backward-compatible `load(raw)` / `load(raw, schema)` calls. |
| **Negative Flows** | ✅ PASS | Broken-total source imports without raising (AC-1); divergence resolver path forwarded to `resolve_key`. |
| **Edge Cases** | ✅ PASS | Blank-total coerces to 0 (AC-4); non-default header offset (AC-7); no-YTG full-year identity. |
| **Error Handling** | ✅ PASS | `ValueError` propagation documented and exercised via header-detection floor and KEY-resolution paths. |
| **Concurrency** | N/A | No concurrency in the import path. |
| **State Transitions** | N/A | Import path is a stateless transform. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.08% lines (93.96% branch) -> Post-change: 99.08% lines (93.96% branch). Change: +0.00% lines (+0.00% branch); flat repo-wide. New/changed-code coverage: 100% line on all three changed production modules (schema_loader.py also 100% branch, 6/6). Disposition: PASS. Evidence: `artifacts/python/lcov.info`, `evidence/qa-gates/coverage-delta.md`, `evidence/baseline/pytest-coverage-baseline.md`.
- PowerShell: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope` (zero PowerShell files changed on branch). Disposition: N/A. Evidence: branch diff contains no `.ps1` files.
- TypeScript: Baseline: N/A - out of scope. Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: `N/A - out of scope` (zero TypeScript files changed on branch). Disposition: N/A. Evidence: branch diff contains no `.ts`/`.tsx` files.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Behavioral assertions on KEY values, frame length, and column membership produce actionable failures. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | All changed tests use explicit Arrange/Act/Assert comment blocks. |
| **Document Intent** | ✅ PASS | Each test carries a docstring naming the AC it verifies. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No DB/network/process dependency. Workbooks built in `io.BytesIO`. |
| **Use Mocks/Stubs** | ✅ PASS | `monkeypatch.setattr` on `detect_header_row`/`read_excel_sheet`/loader entry points redirects to in-memory buffers; the real detection/read logic still executes (non-vacuous). |
| **Environment Stability** | ✅ PASS | No temporary files; no `.xlsx` on disk. Confirmed by inspection of `tests/aop_fixtures.py` (builds `io.BytesIO`). |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Issue #58; `spec.md` v1.0 (Status Final); locked design Scope 1B from `artifacts/research/aop-import-schema-driven-58.md`. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-08T14-30.md` and phase evidence under `evidence/`. |
| **Document the plan** | ✅ PASS | Plan and per-phase QA evidence present. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | `import_aop` is a thin delegator; the detect/read/transform sequence lives in one helper. |
| **Reusability** | ✅ PASS | Reuses `detect_header_row`, `read_excel_sheet`, `SchemaRegistry`, `SchemaLoader`, the `_key_mismatch_seam` no-stdin seams; re-implements nothing. |
| **Extensibility** | ✅ PASS | `SchemaLoader.load` extended with optional keyword-only seams, additive and backward-compatible. |
| **Separation of concerns** | ✅ PASS | AOP schema-import sequence extracted to `_aop_schema_import.py`, separating it from the `PipelineService` orchestration surface. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | New helper has a single purpose (AOP schema-load/detect/read/transform). |
| **Under 500 lines** | ❌ FAIL | Production files compliant (`pipeline_service.py` 500 at cap, `_aop_schema_import.py` 133, `schema_loader.py` 254). **Two changed TEST files exceed the 500-line cap:** `tests/test_schema_loader_core.py` 501 (baseline 374) and `tests/gui/test_pipeline_service.py` 638 (baseline 471). The repo file-size rule (`general-code-change.md`) applies to "production code, test code, or reusable script file." Both crossed the cap due to this feature's added tests. **Blocking.** |
| **Public vs internal** | ✅ PASS | Helper is `_`-prefixed and internal; `import_aop` public signature unchanged. |
| **No circular dependencies** | ✅ PASS | Helper imports schema-path collaborators locally inside the function to keep the import surface minimal and enable test patching at source modules; no import cycle. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `import_aop_via_schema`, `_OPTIONAL_AOP_COLUMNS`, `_AOP_HEADER_MIN_MATCH` follow snake_case/CONSTANT_CASE conventions. |
| **Docs/docstrings** | ✅ PASS | Module docstring plus full Args/Returns/Raises on `import_aop_via_schema`; updated `import_aop` and `SchemaLoader.load` docstrings describe the new contract. |
| **Comment why, not what** | ✅ PASS | Comments explain the local-import rationale, the resolver-callable-not-result intent, and the buffer-rewind reasoning; no trivial narration. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black .` EXIT 0 (no changes). `evidence/qa-gates/final-black.md`. |
| **2. Linting** | ✅ PASS | `poetry run ruff check` EXIT 0. `evidence/qa-gates/final-ruff.md`. |
| **3. Type checking** | ✅ PASS | `poetry run pyright` 0 errors. `evidence/qa-gates/final-pyright.md`. |
| **4. Testing** | ✅ PASS | `poetry run pytest` 998 passed. `evidence/qa-gates/final-pytest-coverage.md`. |
| **Full toolchain loop** | ✅ PASS | Re-run after the post-cap helper extraction; all four stages clean in one pass. |
| **Explicit reporting** | ✅ PASS | Commands/results recorded in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Documented in plan and AC reconciliation evidence. |
| **Design choices explained** | ✅ PASS | KEY-resolver seam rationale and rejected alternatives in `spec.md`. |
| **Update supporting documents** | ✅ PASS | `issue.md`/`spec.md` AC checkboxes updated. |
| **Provide next steps** | ✅ PASS | Plan defines exit gate. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | EXIT 0, no changes. |
| **Linting with Ruff** | ✅ PASS | EXIT 0. No new `# noqa` added (git diff of added lines contains no `noqa`/`type: ignore`). |
| **Type checking with Pyright** | ✅ PASS | 0 errors. New seams fully annotated (`Callable[[list[tuple[str, str]]], str] | None`, etc.). |
| **Testing with Pytest** | ✅ PASS | 998 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | All new params/returns annotated; `from __future__ import annotations` with `TYPE_CHECKING`-gated `Callable`/`pd` imports. No `Any` introduced. |
| **Dataclasses for value objects** | N/A | No new value objects. |
| **Protocols/ABCs for interfaces** | ✅ PASS | Seam expressed as injected `Callable`s, consistent with the existing `resolve_key` contract. |
| **Avoid utility classes** | ✅ PASS | New code is a module-level function, not a static-method class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | `ValueError` propagation from header detection / KEY resolution documented; no broad `except`. |
| **Logging over print** | ✅ PASS | `import_aop` retains the existing `logger.info` call; no `print`. |
| **Invariants at construction** | ✅ PASS | Header-token floor (`_AOP_HEADER_MIN_MATCH`) enforced at detection. |

### Section 3B–3D (PowerShell / Bash / JSON)

- PowerShell, Bash: N/A — no such files on branch.
- JSON: `src/schemas/default_aop.schema.json` is a data-only edit (`fill_rules: []`, `header_row: 2`). Verified valid JSON and round-trips losslessly via `tests/test_default_schemas.py::test_aop_fill_rules_empty_and_header_row_two_round_trips`. No `SCHEMA_FORMAT_VERSION` bump required (within the existing `2.0` shape). Status: ✅ PASS.

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | Pytest + hypothesis property tests. |
| **Coverage expectation** | ✅ PASS | New code 100% line; repo-wide 99.08% line / 93.96% branch, both above the uniform 85%/75% thresholds. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | Only the read boundary is patched; real detection/transform logic executes. |
| **Organization** | ✅ PASS | Tests mirror code (`test_schema_loader_core.py`, `test_pipeline_service.py`, `test_schema_loader_parity_aop.py`). |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_...` names. |
| **Docstrings/comments** | ✅ PASS | AC-referencing docstrings throughout. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | 998 passed. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

### Section 4B: PowerShell Unit Test Policy Compliance

N/A — no PowerShell files or tests on branch.

---

## 5. Test Coverage Detail

### src/gui/_aop_schema_import.py::import_aop_via_schema (NEW)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_import_aop_imports_full_year_ytd_source | Positive (AC-2) | ✅ |
| test_import_aop_imports_partial_year_ytd_source | Positive (AC-3) | ✅ |
| test_import_aop_imports_source_with_broken_totals | Negative/no-validation (AC-1) | ✅ |
| test_import_aop_header_detection_drives_the_read | Edge (AC-7) | ✅ |
| test_import_aop_output_columns_and_key_match_prior_loader | Parity (AC-6) | ✅ |

**Coverage:** 17/17 lines = 100% (from `artifacts/python/lcov.info`).

### src/schema_loader.py::SchemaLoader.load (seam extension, T1)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_load_forwards_resolver_seams_to_resolve_key_on_divergence | Forwarding (AC-5) | ✅ |
| test_property_resolver_action_governs_key_on_divergence (`@given`) | Property/T1 (AC-5) | ✅ |
| test_load_backward_compatible_without_seam_arguments | Backward-compat (AC-8) | ✅ |

**Coverage:** 32/32 lines, 6/6 branches = 100% / 100%.

### src/schemas/default_aop.schema.json (fill_rules / header_row)

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| test_aop_fill_rules_empty_and_header_row_two_round_trips | Data/round-trip (AC-4) | ✅ |
| test_aop_blank_total_coerces_to_zero_not_month_sum | Edge (AC-4) | ✅ |
| test_aop_no_arithmetic_validation_loads_broken_totals | Negative (AC-1) | ✅ |

**Not covered:** None of the changed production code is uncovered.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 998 | ✅ |
| Tests Passed | 998 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Delta vs baseline | +11 (987 -> 998) | ✅ |
| Functions/Classes Tested (changed) | 3/3 changed prod modules | ✅ |
| Test File Size | `test_schema_loader_core.py` 501, `test_pipeline_service.py` 638 | ❌ over 500-line cap |
| Code Coverage | 99.08% lines, 93.96% branch | ✅ |

---

## 7. Code Quality Checks

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | EXIT 0, no changes | ✅ |
| Ruff Linting | `poetry run ruff check` | EXIT 0 | ✅ |
| Pyright Type Checking | `poetry run pyright` | 0 errors | ✅ |
| Pytest Tests | `poetry run pytest` | 998 passed | ✅ |
| File-size cap (test code) | `awk END{NR}` on changed files | 2 test files over 500 lines | ❌ |
| New suppressions | git diff added-line grep | none added | ✅ |
| Coverage (independent) | parse `artifacts/python/lcov.info` | changed prod files 100% line | ✅ |

**Notes:** No PowerShell/TypeScript/C#/Bash files on branch; those toolchains are out of scope for this change. Coverage artifact `artifacts/python/lcov.info` mtime (13:34) is newer than all changed source files; not stale.

---

## 8. Gaps and Exceptions

### Identified Gaps

- **File Size Limit (test code):** `tests/test_schema_loader_core.py` (501) and `tests/gui/test_pipeline_service.py` (638) exceed the 500-line cap. Plan: split each into cohesive sibling test modules (for example, separate the AOP schema-path tests in `test_pipeline_service.py` and the seam/property tests in `test_schema_loader_core.py`). Both regressions are attributable to this feature's added tests.
- **Missing `user-story.md`:** Work mode is `full-feature`, whose AC sources are `spec.md` AND `user-story.md`, but `user-story.md` is absent from the feature folder. The canonical AC list in `spec.md`/`issue.md` (AC-1..AC-9) was used as the AC source; the absent `user-story.md` adds no further criteria. Recorded as a documentation gap, not a code defect. Non-blocking.

### Approved Exceptions

- **None.** The 500-line cap exceptions (throwaway scripts, raw text fixtures, Markdown) do not apply: these are reusable Python test files.

### Removed/Skipped Tests

- **None.** No tests were removed or skipped. The parity suite was re-targeted (column-set/order + KEY parity rather than value-for-value `load_aop` fill parity), consistent with Decision 2; assertions were strengthened, not weakened.

---

## 9. Summary of Changes

### Files Modified

1. **src/gui/pipeline_service.py** (MODIFIED) — `import_aop` rewritten as a thin delegator to `import_aop_via_schema`; module-level `from src import load_aop` removed (only a docstring mention remains); 500 lines.
2. **src/gui/_aop_schema_import.py** (NEW, 133) — schema-load/header-detect/raw-read/transform sequence; forwards resolver + no-stdin seams.
3. **src/schema_loader.py** (MODIFIED, T1, 254) — `load()` gains keyword-only `resolver`/`is_tty`/`prompt`, forwarded to `resolve_key`.
4. **src/schemas/default_aop.schema.json** (MODIFIED) — `fill_rules: []`, `header_row: 2`.
5. **9 test files** — AC coverage, parity re-targeting, monkeypatch-site updates to the schema path.

---

## 10. Compliance Verdict

### Overall Status: ⚠️ PARTIALLY COMPLIANT

The change is functionally and stylistically compliant with one Blocking exception: two changed test files exceed the repository 500-line file-size cap, which policy applies to test code. All other policy dimensions pass with evidence.

### Recommendation

**Needs revision (one Blocking item).**

Blocking:
1. Reduce `tests/gui/test_pipeline_service.py` (638) and `tests/test_schema_loader_core.py` (501) to <= 500 lines each (split into cohesive sibling modules). Re-run the toolchain after the split.

Non-blocking:
1. Add the absent `user-story.md` to the feature folder (or record in the feature docs that the canonical AC list lives in `spec.md`/`issue.md`).

**Fail-closed reminder:** This audit is reported as PARTIALLY COMPLIANT, not PASS, because a mandatory policy (file-size cap on test code) is violated.

---

## Appendix A: Test Inventory

Tests directly verifying the changed surface (selected; full suite is 998):

- tests/gui/test_pipeline_service.py::test_import_aop_imports_full_year_ytd_source
- tests/gui/test_pipeline_service.py::test_import_aop_imports_partial_year_ytd_source
- tests/gui/test_pipeline_service.py::test_import_aop_imports_source_with_broken_totals
- tests/gui/test_pipeline_service.py::test_import_aop_header_detection_drives_the_read
- tests/gui/test_pipeline_service.py::test_import_aop_output_columns_and_key_match_prior_loader
- tests/test_schema_loader_core.py::test_load_forwards_resolver_seams_to_resolve_key_on_divergence
- tests/test_schema_loader_core.py::test_property_resolver_action_governs_key_on_divergence
- tests/test_schema_loader_core.py::test_load_backward_compatible_without_seam_arguments
- tests/test_schema_loader_parity_aop.py::test_aop_parity_with_ytg
- tests/test_schema_loader_parity_aop.py::test_aop_parity_without_ytg
- tests/test_schema_loader_parity_aop.py::test_aop_parity_sentinel_clean_labels
- tests/test_schema_loader_parity_aop.py::test_aop_parity_no_row_collapse
- tests/test_schema_loader_parity_aop.py::test_aop_no_arithmetic_validation_loads_broken_totals
- tests/test_schema_loader_parity_aop.py::test_aop_blank_total_coerces_to_zero_not_month_sum
- tests/test_default_schemas.py::test_aop_fill_rules_cover_ytd_quarters_and_ytg
- tests/test_default_schemas.py::test_aop_fill_rules_empty_and_header_row_two_round_trips
- tests/gui/test_pipeline_service_key_seam.py (AOP resolver-forwarding, re-targeted to SchemaLoader.load)

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
poetry run black .
poetry run ruff check
poetry run pyright
poetry run pytest --cov --cov-branch --cov-report=term-missing
```

Coverage artifact verified independently: `artifacts/python/lcov.info` (parsed for the three changed production files).

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-08
**Policy Version:** Current (as of audit date)
