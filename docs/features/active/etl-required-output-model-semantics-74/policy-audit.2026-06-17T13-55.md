# Policy Compliance Audit: etl-required-output-model-semantics (#74, epic child CF1)

**Audit Date:** 2026-06-17
**Code Under Test:** Branch `refactor/etl-required-output-model-semantics-74` @ `1182cad` vs base `main` @ `0a47fef` (merge-base `0a47fef2869b97d8a290d33570ebeee834c80987`). Re-audit after remediation cycle 3 (descope of AOP minimization to CF2). Source/test files modified:
- `src/schema_model.py`
- `src/_schema_model_specs.py`
- `src/schema_serialization.py`
- `src/schemas/default_le.schema.json`
- `tests/test_default_schemas.py`
- `tests/test_schema_loader_core.py`
- `tests/test_schema_migration.py`
- `tests/test_schema_model.py`
- Feature docs/evidence under `docs/features/active/etl-required-output-model-semantics-74/` and the parent epic folder (non-code).

`src/schemas/default_aop.schema.json` was modified in cycles 1–2 (version bump) but the change was reverted in cycle 3; the file is now byte-identical to `main` (`git diff main -- src/schemas/default_aop.schema.json` is empty) and is therefore NOT a changed file on this branch.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 3 src + 4 test files | 1058 tests | ✅ 1058 pass, 0 fail | 98% lines, 94% branch (repo) | 98% lines, 94% branch (repo) | 100% (new `required_output_columns()`, migration helper, and migration plumbing) |
| JSON | 1 file (`default_le.schema.json`) | N/A | ✅ validated by bundled-parity + default-schema tests | N/A (config files) | N/A (config files) | N/A |

**Note:** Only Python and JSON have changed files in the branch diff. TypeScript, PowerShell, and C# have zero changed files on this branch and are N/A.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - no TypeScript files changed`
- TypeScript post-change coverage artifact: `N/A - no TypeScript files changed`
- PowerShell baseline coverage artifact: `N/A - no PowerShell files changed`
- PowerShell post-change coverage artifact: `N/A - no PowerShell files changed`
- Per-language comparison summary: see section 1.2.1 below; Python artifact `artifacts/python/lcov.info` (refreshed by an independent full-suite run during this review).

**Non-negotiable verdict rule:** Numeric baseline and post-change coverage metrics are reported for every language with changed files (Python). JSON has no coverage model.

**Fail-closed rule:** All required baseline and QA artifacts are present under `docs/features/active/etl-required-output-model-semantics-74/evidence/`.

**Evidence rule:** All figures below were independently re-derived from a fresh full-suite run during this review (`poetry run black --check .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest --cov --cov-branch --cov-report=term-missing`, exit 0, 1058 passed) plus direct diff inspection and schema-file flag dumps; none were synthesized from memory.

---

## Executive Summary

This is a post-remediation (cycle 3) re-audit of the foundational semantic change of epic #74 (approved recommendation A): the schema `required` flag is redefined from "must be present in source to load" (input-presence) to "required OUTPUT identity column" (one value column plus its dimension columns). `in_output` continues to mean "emitted in the final table (may be true without `required`)." `SCHEMA_FORMAT_VERSION` is bumped `"2.0" -> "3.0"`. A deterministic forward migration `required(3.0) = required(2.0) AND in_output(2.0)` upgrades pre-3.0 persisted schemas on load while preserving `in_output`, so emitted output is unchanged. A read-only `SchemaDefinition.required_output_columns()` accessor is added.

The prior audit (`2026-06-17T12-35`) raised one Major / material-PARTIAL finding: the `default_aop.schema.json` `required` flags were not aligned to the 3.0 meaning. Remediation across cycles 1–2 established that flipping AOP measures to `required: false` reorders the SchemaLoader output for the `none`-dedup path, because `src/_schema_loader_helpers.py` couples both the which-columns-to-keep decision and the emitted column order to the `required` flag (corroborated in this review: `resolve_and_rename` builds `required_expected` and the `columns_to_keep`/`selection` order from `column.required`). Decoupling that requires a CF2-scoped loader change. The orchestrator therefore descoped AOP minimization to CF2: `spec.md` rescopes AC #3 to `default_le`, the descope note was added, and the cycle-3 remediation reverted the only CF1 AOP change (the version bump) so CF1 makes zero AOP schema-file change. This review verifies that resolution: `git diff main -- src/schemas/default_aop.schema.json` is empty (the AOP file is at on-disk version `2.0` with its original `required` flags), and the on-load migration keeps the loaded AOP schema functionally identical (every AOP measure is `in_output: true`, so `required AND in_output` preserves `required: true`).

The Python toolchain is clean in a single pass (Black, Ruff, Pyright, Pytest), independently verified this cycle. Coverage on the three changed source modules meets thresholds: `schema_model.py` and `_schema_model_specs.py` at 100% line and branch; `schema_serialization.py` at 98% line (single uncovered line 486 is a pre-existing legacy-key error path, not a changed line) with the new migration code (`_version_predates_required_output`, the `migrate_required` plumbing) fully covered by `tests/test_schema_migration.py`. Bundled-schema loader output parity is preserved for both `default_le` and `default_aop` (zero output regression). The LE schema correctly marks only its six output-identity dimensions (`Customer`, `SKU Descripiton`, `SKU #`, `Type`, `GtN Mapping`, `PPG`) as `required: true`; months, `FY`, quarters, and the loader-produced `Super Category` are `required: false`, `in_output: true`.

Overall verdict: FULLY COMPLIANT. The single prior Major finding is resolved by a contract-level descope plus a verified revert. No blocking or material-PARTIAL findings remain. Recommendation: ready for merge.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md`
- N/A `powershell.md` (no PowerShell files changed)
- N/A TypeScript/C# (no files changed)
- ✅ JSON (bundled `default_le` schema) validated by tests

**Temporary artifacts cleanup:**
- ✅ No temporary or one-time scripts were created by this review.
- ✅ No throwaway scripts in the branch diff.

---

## Rejected Scope Narrowing

None. The caller prompt set scope to the full branch diff against `main` (`0a47fef..1182cad`) and instructed "Determine scope yourself." The descope of AOP minimization to CF2 is a legitimate contract-level scope decision recorded in `spec.md` and the epic `initiative.md`; it is not a reviewer-side narrowing of the branch-diff audit. This audit still covers the full feature-vs-base diff, including independently confirming that the AOP file carries zero diff against `main`. No instruction attempted to narrow scope to a plan/task/phase subset, to a subset of changed files, or to mark any changed language as out of scope.

---

## Evidence Location Compliance

No violations. A scan of the branch diff (`git diff --name-only main...HEAD`) found zero files written under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`. All feature evidence is written under the canonical `docs/features/active/etl-required-output-model-semantics-74/evidence/<kind>/` path (baseline, qa-gates, regression-testing). The repo-level `scripts/validate_evidence_locations.py` script is not present in this repository; the scan was performed via `git diff --name-only main...HEAD | grep -E '^artifacts/(baselines|qa|evidence|coverage)/'` (no matches).

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** - Tests run in any order | ✅ PASS | New tests construct their own in-memory `pd.DataFrame` / synthetic JSON fixtures and load bundled schemas read-only; no shared mutable state. Full suite passes under default pytest ordering. |
| **Isolation** - Each test targets single behavior | ✅ PASS | Each added test asserts one behavior: e.g. `test_default_le_resolves_when_only_months_are_absent` (positive resolve), `test_default_le_resolve_raises_when_required_dimension_absent` (negative), `test_pre_3_0_required_drops_when_not_emitted` (migration mapping). |
| **Fast Execution** - Tests complete quickly | ✅ PASS | Full suite (1058 tests) ran in 38.72s; migration tests are pure in-memory. |
| **Determinism** - Consistent results | ✅ PASS | No wall-clock, RNG, network, or filesystem dependency in the added tests; inputs are literal frames/JSON strings. |
| **Readability & Maintainability** - Clear structure | ✅ PASS | Descriptive test names, docstrings, and explicit Arrange/Act/Assert comments; shared constants `_LE_REQUIRED_DIMENSIONS` / `_LE_NON_REQUIRED_MEASURES`. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | **Baseline (pre-development):** captured in `evidence/baseline/baseline-pytest.md` / `pytest-coverage-baseline.md`. Repo-wide ~98% line, ~94% branch.<br>**Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing`<br>**Timestamp:** 2026-06-17 (baseline phase). |
| **No Coverage Regression** | ✅ PASS | **Post-change coverage:** 98% line, 94% branch (repo).<br>**Change:** no regression; changed modules at 100% (model/specs) and 98% (serialization).<br>**Status:** No regression on changed lines. |
| **New Code Coverage >= 90%** | ✅ PASS | **New/modified code:** `required_output_columns()` (100%), `_version_predates_required_output()` (100% incl. the unparseable-version branch via `test_unparseable_version_is_treated_as_legacy`), `migrate_required` plumbing in `_object_to_column`/`_object_to_schema` (100%). |
| **Comprehensive Coverage** | ✅ PASS | LE required-set, accessor, resolve positive/negative, and the four migration mappings (drop-when-not-emitted, stay-when-emitted, 3.0 pass-through, round-trip, unparseable-legacy) are each tested. |
| **Positive Flows** - Valid inputs | ✅ PASS | `test_default_le_resolves_when_only_months_are_absent`, `test_default_le_required_output_columns_accessor`, `test_pre_3_0_required_stays_when_emitted`. |
| **Negative Flows** - Invalid inputs | ✅ PASS | `test_default_le_resolve_raises_when_required_dimension_absent` (missing `Customer` raises `ValueError`). |
| **Edge Cases** - Boundary conditions | ✅ PASS | `test_unparseable_version_is_treated_as_legacy` (non-numeric major); `test_3_0_round_trip_is_stable` (idempotent re-serialize). |
| **Error Handling** - Error paths | ✅ PASS | Negative resolve raises `ValueError`; pre-existing serialization error path (line 486) is unchanged. |
| **Concurrency** - If applicable | N/A | Pure data transforms; no concurrency. |
| **State Transitions** - If applicable | N/A | No stateful component introduced. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 98% line / 94% branch (repo) -> Post-change: 98% line / 94% branch (repo). Change: +0% line / +0% branch (no regression). New/changed-code coverage: 100% (changed source modules; serialization at 98% with the single uncovered line a pre-existing legacy-key error path, not a changed line). Disposition: PASS. Evidence: `artifacts/python/lcov.info` (refreshed this review), `evidence/qa-gates/final-pytest.2026-06-17T13-40.md`, `evidence/qa-gates/coverage-delta.2026-06-17T13-40.md`.
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A (zero changed files). Evidence: `N/A - no TypeScript files changed`.
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A (zero changed files). Evidence: `N/A - no PowerShell files changed`.
- C#: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A (zero changed files). Evidence: `N/A - no C# files changed`.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Assertions include identifying context (e.g. `assert by_name[name].required is True, name`). |
| **Arrange-Act-Assert Pattern** | ✅ PASS | Each new test carries explicit Arrange/Act/Assert comments. |
| **Document Intent** | ✅ PASS | Descriptive names plus docstrings stating scenario and expected outcome. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | No DB/network/process; only in-memory frames and bundled-schema read. |
| **Use Mocks/Stubs** | N/A | No external collaborator requires mocking. |
| **Environment Stability** | ✅ PASS | No temporary files created; synthetic JSON is a literal string. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This document is the required policy review for the cycle-3 re-audit. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Spec, issue #74, and the cycle-3 remediation inputs define the objective and the AOP descope. |
| **Read existing change plans** | ✅ PASS | `plan.2026-06-17T11-54.md` and `remediation-plan.2026-06-17T13-40.md` present. |
| **Document the plan** | ✅ PASS | Plan and remediation-plan artifacts capture the approach. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | Migration is a single boolean recompute `required AND in_output`; accessor is a one-line comprehension plus an empty derived placeholder. |
| **Reusability** | ✅ PASS | Version gate factored into `_version_predates_required_output` and threaded once via `migrate_required`. |
| **Extensibility** | ✅ PASS | `required_output_columns()` documents and structurally supports a future designated required derived column. |
| **Separation of concerns** | ✅ PASS | Model semantics (`schema_model.py`/`_schema_model_specs.py`) stay separate from serialization/migration (`schema_serialization.py`); no loader change. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | Each changed module retains its single responsibility. |
| **Under 500 lines** | ✅ PASS | Independently measured changed source files vs the 500-line cap (`awk END{print NR}`): `schema_model.py` 336, `_schema_model_specs.py` 486, `schema_serialization.py` 497 — all under the cap (see section 2.3 note). |
| **Public vs internal** | ✅ PASS | Only additive public surface is `required_output_columns()` and the `SCHEMA_FORMAT_VERSION` value change; `_schema_model_specs` and `_version_predates_required_output` remain underscore-internal. |
| **No circular dependencies** | ✅ PASS | `schema_model` imports from `_schema_model_specs`; serialization depends on model; no cycle introduced. |

**Section 2.3 note (file-size verification):** Line counts measured with `awk 'END{print NR}'` over the working tree: `schema_model.py` 336, `_schema_model_specs.py` 486, `schema_serialization.py` 497. All under the 500-line limit. No changed file exceeds 500 lines.

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `required_output_columns`, `_version_predates_required_output`, `migrate_required`, `migrated_required`. |
| **Docs/docstrings** | ✅ PASS | New accessor, helper, and `_object_to_column` carry full Purpose/Args/Returns docstrings; module + class docstrings document the 3.0 semantics. |
| **Comment why, not what** | ✅ PASS | Comments explain rationale (e.g. why an unparseable version is treated as legacy; why `Super Category` is hand-authored `required: false`). |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | **Command:** `poetry run black --check .`<br>**Result:** All done; 243 files unchanged. |
| **2. Linting** | ✅ PASS | **Command:** `poetry run ruff check .`<br>**Result:** All checks passed; no new suppressions. |
| **3. Type checking** | ✅ PASS | **Command:** `poetry run pyright`<br>**Result:** 0 errors, 0 warnings, 0 informations. |
| **4. Testing** | ✅ PASS | **Command:** `poetry run pytest --cov --cov-branch --cov-report=term-missing`<br>**Result:** 1058 passed. |
| **Full toolchain loop** | ✅ PASS | Single clean pass this review; no auto-fixes triggered. |
| **Explicit reporting** | ✅ PASS | Commands and results recorded here and under `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Spec DoD and remediation inputs summarize the change and descope. |
| **Design choices explained** | ✅ PASS | Descope note documents why AOP minimization moves to CF2 (loader ordering coupling). |
| **Update supporting documents** | ✅ PASS | `spec.md` and `initiative.md` updated to reflect the descope. |
| **Provide next steps** | ✅ PASS | AOP minimization tracked into CF2 with the loader decouple. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check .` — 243 files unchanged. |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check .` — All checks passed. |
| **Type checking with Pyright** | ✅ PASS | `poetry run pyright` — 0 errors, 0 warnings. |
| **Testing with Pytest** | ✅ PASS | `poetry run pytest` — 1058 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | `required_output_columns() -> tuple[str, ...]`; `_version_predates_required_output(version: str) -> bool`; `migrate_required: bool` keyword-only. No `Any` introduced. |
| **Dataclasses for value objects** | ✅ PASS | `ColumnSpec` / `SchemaDefinition` remain dataclasses; no new value type required. |
| **Protocols/ABCs for interfaces** | N/A | No new interface needed. |
| **Avoid utility classes** | ✅ PASS | New behavior is module functions / a dataclass method, not a static-only class. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | Resolve raises `ValueError`; serialization raises `SchemaSerializationError`; no broad catch. |
| **Logging over print** | ✅ PASS | No print statements added. |
| **Invariants at construction** | ✅ PASS | `SchemaDefinition.__post_init__` validation unchanged; migration computes flags before construction. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | All new tests are pytest functions; `pytest.raises` used for the negative path. |
| **Coverage expectation** | ✅ PASS | New code 100%; repo-wide 98% line / 94% branch, above the 85%/75% thresholds. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | No mocks; real in-memory inputs. |
| **Organization** | ✅ PASS | Tests live in `tests/test_default_schemas.py`, `test_schema_loader_core.py`, `test_schema_migration.py`, `test_schema_model.py`, mirroring source modules. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | `test_<behavior>` snake_case names. |
| **Docstrings/comments** | ✅ PASS | Each new test has a docstring and AAA comments. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest --cov --cov-branch` — 1058 passed. |
| **No Alternative Test Runners** | ✅ PASS | Only pytest used. |

---

## 5. Test Coverage Detail

### `SchemaDefinition.required_output_columns()` (2 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_default_le_required_output_columns_accessor` | Positive | accessor body | ✅ |
| `test_default_le_required_set_is_output_identity_under_3_0` | Positive/Edge | flag assertions | ✅ |

**Coverage:** 100% of the accessor.

### `_version_predates_required_output` + migration plumbing (5 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_pre_3_0_required_drops_when_not_emitted` | Positive (migration) | recompute branch | ✅ |
| `test_pre_3_0_required_stays_when_emitted` | Positive (migration) | recompute branch | ✅ |
| `test_3_0_required_passes_through_unchanged` | Negative (no migration) | pass-through branch | ✅ |
| `test_3_0_round_trip_is_stable` | Edge (idempotence) | serialize+parse | ✅ |
| `test_unparseable_version_is_treated_as_legacy` | Edge (error parse) | `except ValueError` branch | ✅ |

**Coverage:** 100% of the new migration code.

### LE resolve gate (2 tests)

| Test Name | Scenario Type | Lines Covered | Status |
|-----------|--------------|---------------|--------|
| `test_default_le_resolves_when_only_months_are_absent` | Positive | `resolve_and_rename` | ✅ |
| `test_default_le_resolve_raises_when_required_dimension_absent` | Negative/Error | required-column gate | ✅ |

**Not covered:** `schema_serialization.py` line 486 (legacy-key `SchemaSerializationError` raise) — pre-existing, not a changed line.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 1058 | ✅ |
| Tests Passed | 1058 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | 38.72s total | ✅ Fast |
| Average Time per Test | ~37ms | ✅ Fast |
| Code Coverage | 98% lines, 94% branches (repo) | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | 243 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check .` | 0 errors, no new suppressions | ✅ |
| Pyright Type Checking | `poetry run pyright` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `poetry run pytest --cov --cov-branch` | 1058 passed | ✅ |

**Notes:** Five non-blocking warnings observed in the full suite (PySide6 `QMouseEvent` deprecation in GUI tests and a pandas concat FutureWarning) are pre-existing and unrelated to this change. The `modified-workflow-needs-green-run` policy rule does not fire: the branch diff touches no `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` paths.

---

## 8. Gaps and Exceptions

### Identified Gaps

**None.** All policy requirements applicable to the CF1 (model-semantics) scope are met. The prior cycle's Major finding (AOP `required` flags not aligned) is resolved at the contract level: AOP minimization is descoped to CF2 (the loader-ordering coupling is CF2 work), and the CF1 AOP version bump was reverted so CF1 makes zero AOP schema-file change (`git diff main -- src/schemas/default_aop.schema.json` empty).

### Approved Exceptions

**None.** No suppressions were introduced.

### Removed/Skipped Tests

**None.** No CF1 test asserts the AOP file is 3.0 on disk or that AOP measures are `required: false`; the AOP coverage in `tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts` asserts only that AOP loads at `SCHEMA_FORMAT_VERSION` (3.0) via the on-load migration, which holds with the file at on-disk 2.0. No LE assertion was weakened.

---

## 9. Summary of Changes

### Commits in This PR/Branch

Range `0a47fef..1182cad` on `refactor/etl-required-output-model-semantics-74`. Head `1182cad`.

### Files Modified

1. **`src/schema_model.py`** (MODIFIED) — `SCHEMA_FORMAT_VERSION "2.0" -> "3.0"`; module/class docstrings document 3.0 `required`-output semantics; new `required_output_columns()` accessor.
2. **`src/_schema_model_specs.py`** (MODIFIED) — `ColumnSpec.required`/`in_output` docstrings rewritten to the required-output meaning.
3. **`src/schema_serialization.py`** (MODIFIED) — new `_version_predates_required_output`; `migrate_required` threaded through `_object_to_schema`/`_object_to_column`; `required(3.0) = required(2.0) AND in_output(2.0)` applied only for pre-3.0 sources.
4. **`src/schemas/default_le.schema.json`** (MODIFIED) — version `3.0`; months/`FY`/quarters and `Super Category` set `required: false` (`in_output: true`); output-identity dimensions remain `required: true`.
5. **`src/schemas/default_aop.schema.json`** (REVERTED) — cycle-3 restored to `main`; zero diff against base.
6. **`tests/test_default_schemas.py`, `tests/test_schema_loader_core.py`, `tests/test_schema_migration.py`, `tests/test_schema_model.py`** (MODIFIED) — new LE required-set/accessor/resolve tests and migration tests; version assertion updated to 3.0.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The cycle-3 re-audit confirms the prior Major finding is resolved. The CF1 model-semantics change is complete and clean: toolchain green in a single pass, coverage above threshold with the new code at 100%, bundled-schema output parity preserved for both LE and AOP, and the AOP file carrying zero diff against `main` (minimization correctly deferred to CF2). No blocking or material-PARTIAL findings remain.

**Fail-closed reminder:** All required baseline, QA, and coverage artifacts are present; no required artifact is missing.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes: documented plan + remediation inputs.
- ✅ Design Principles: simple, reusable, extensible, well-separated.
- ✅ Module & File Structure: all changed files at or under 500 lines.
- ✅ Naming, Docs, Comments: descriptive, fully documented, rationale comments.
- ✅ Toolchain Execution: single clean pass.
- ✅ Summarize & Document: spec/initiative updated for the descope.

#### Language-Specific Code Change Policy (Section 3)

**For Python:**
- ✅ Tooling & Baseline: Black/Ruff/Pyright/Pytest clean.
- ✅ Python Design & Typing: strongly typed, no `Any`.
- ✅ Error Handling: specific exceptions, no broad catch.

#### General Unit Test Policy (Section 1)
- ✅ Core Principles: independent, isolated, fast, deterministic, readable.
- ✅ Coverage & Scenarios: positive/negative/edge/error covered; new code 100%.
- ✅ Test Structure: AAA, clear diagnostics.
- ✅ External Dependencies: none; no temp files.
- ✅ Policy Audit: this document.

#### Language-Specific Unit Test Policy (Section 4)

**For Python:**
- ✅ Framework & Scope: pytest, coverage above threshold.
- ✅ Test Style & Structure: focused, no mocks, mirrors source.
- ✅ Naming & Readability: descriptive names + docstrings.
- ✅ Toolchain: pytest only.

---

### Metrics Summary

- ✅ 1058/1058 tests passing (100%)
- ✅ New code coverage 100%; repo-wide 98% line / 94% branch
- ✅ All changed source files at or under 500 lines
- ✅ All code-quality checks passing (Black, Ruff, Pyright, Pytest)
- ✅ Test execution time: 38.72s (fast)
- ✅ AOP file zero-diff against `main` (minimization deferred to CF2)

---

### Recommendation

**Ready for merge.**

The CF1 model-semantics scope is fully delivered against the rescoped DoD. The prior Major finding is resolved by a documented descope and a verified revert. AOP `required`-flag minimization is correctly carried forward to CF2 (which owns the located-by-name/presence-optional signal and the loader-ordering decouple). No remediation is required for CF1.

---

## Appendix A: Test Inventory

New/updated tests verified in this review:

- `tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts`
- `tests/test_default_schemas.py::test_default_le_required_set_is_output_identity_under_3_0`
- `tests/test_default_schemas.py::test_default_le_required_output_columns_accessor`
- `tests/test_schema_loader_core.py::test_default_le_resolves_when_only_months_are_absent`
- `tests/test_schema_loader_core.py::test_default_le_resolve_raises_when_required_dimension_absent`
- `tests/test_schema_migration.py::test_pre_3_0_required_drops_when_not_emitted`
- `tests/test_schema_migration.py::test_pre_3_0_required_stays_when_emitted`
- `tests/test_schema_migration.py::test_3_0_required_passes_through_unchanged`
- `tests/test_schema_migration.py::test_3_0_round_trip_is_stable`
- `tests/test_schema_migration.py::test_unparseable_version_is_treated_as_legacy`
- `tests/test_schema_model.py::test_schema_format_version_value`

---

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
# Formatting
poetry run black --check .

# Linting
poetry run ruff check .

# Type checking
poetry run pyright

# Testing + coverage
poetry run pytest --cov --cov-branch --cov-report=term-missing

# AOP revert verification
git diff main -- src/schemas/default_aop.schema.json   # empty == reverted

# LE/AOP flag dump
python -c "import json; d=json.load(open('src/schemas/default_le.schema.json')); print(d['version'])"
```

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-17
**Policy Version:** Current (as of audit date)
