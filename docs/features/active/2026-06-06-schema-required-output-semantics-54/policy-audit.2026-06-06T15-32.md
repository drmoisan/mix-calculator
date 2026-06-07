# Policy Compliance Audit: schema-required-output-semantics (#54)

**Audit Date:** 2026-06-06
**Code Under Test:** Isolated #54 delta `git diff 7bfa57c..HEAD` (HEAD = 55261bf) on branch `feature/schema-builder-ux-overhaul-50` (rides in PR #51). Changed Python production: `src/_schema_loader_helpers.py`, `src/_schema_model_specs.py`, `src/schema_serialization.py`, `src/gui/_schema_view_protocols.py`, `src/gui/presenters/_columns_tab_presenter.py`, `src/gui/presenters/_schema_builder_state.py`, `src/gui/presenters/schema_builder_presenter.py`, `src/gui/widgets/_schema_builder_drag_tabs.py`, `src/gui/widgets/schema_builder_dialog.py`. Changed JSON: `src/schemas/default_le.schema.json`, `src/schemas/default_aop.schema.json`. Changed tests: 12 files (see Section 9).

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 9 prod files | 966 tests | ✅ 966 pass, 0 fail | 99.07% lines, 94.15% branch | 99.07% lines, 94.15% branch | >=92% per edited module; 100% on new test files |
| JSON | 2 files | N/A | ✅ validation (parse + bundled-schema tests pass) | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - no TypeScript files in diff`
- TypeScript post-change coverage artifact: `N/A - no TypeScript files in diff`
- PowerShell baseline coverage artifact: `N/A - no PowerShell files in diff`
- PowerShell post-change coverage artifact: `N/A - no PowerShell files in diff`
- Python coverage artifact (post-change): `artifacts/python/lcov.info` (regenerated during this audit, 966 passed)
- Per-language comparison summary: Section 1.2.1 below; executor evidence `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-coverage-delta.md`

**Non-negotiable verdict rule:** This audit reports numeric baseline and post-change coverage for the only in-scope language with changed files (Python). PASS is permitted.

---

## Executive Summary

The #54 change adds an explicit `in_output: bool = True` field to `ColumnSpec` and switches the schema loader's output determination from `drop_columns` by-name exclusion to `in_output` inclusion (plus `KEY` and derived columns, in schema order). `required` retains its source-presence meaning. The bundled `default_le` `YTD/YTG` becomes `required:false, in_output:false` with `drop_columns: []`; `default_aop` gains explicit `in_output:true` on all columns (AOP `YTG` stays `required:false, in_output:true`). The #50 schema-builder column-row tuple migrates from 4-tuple to 5-tuple end-to-end. No `SCHEMA_FORMAT_VERSION` bump.

The change is well-scoped, parity-preserving, and policy-compliant. The full toolchain was independently re-run during this audit and is green: Black clean, Ruff clean, Pyright `0 errors, 0 warnings`, Pytest `966 passed, 0 failed`. Coverage is well above thresholds (99.07% line / 94.15% branch repo-wide; >=92% per edited module). The design separates source-presence (`required`) from output-membership (`in_output`) cleanly, which was the explicit user directive and the locked research approach.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ `python.md` + `python-suppressions.md` (Python in scope)
- N/A `powershell.md` (no PowerShell files in diff)
- N/A TypeScript / C# (no such files in diff)
- ✅ `self-explanatory-code-commenting.md` (docstrings/intent comments)
- ✅ `tonality.md` (artifacts only; no source-code prose change of concern)
- N/A `ci-workflows.md`, `benchmark-baselines.md` (no `.github/workflows/**` or benchmark-baseline changes; confirmed below)

**Temporary artifacts cleanup:**
- ✅ No temporary/one-time scripts created during development.
- ✅ No throwaway scripts introduced by the diff.

---

## Rejected Scope Narrowing

None. The caller brief requested the full isolated #54 delta (`7bfa57c..HEAD`), which is the correct full-feature scope for the #54 work as it rides in PR #51. The #54 work is itself a sub-feature of PR #51; isolating it via the rebased pre-#54 HEAD (`7bfa57c`) is a legitimate baseline, not a narrowing of the #54 audit. Every language with changed files (Python, JSON) received an explicit verdict.

## Evidence Location Compliance

A git-diff scan for evidence files written under non-canonical paths (`artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`, `artifacts/coverage/`) returned no matches. All #54 evidence is under the canonical `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/<kind>/`. The Python coverage artifact `artifacts/python/lcov.info` is the configured pytest coverage output path (not an evidence-location violation). `scripts/validate_evidence_locations.py` is absent in this repo; the git-diff scan was used instead. No FAIL findings.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Independence** | ✅ PASS | New tests construct `SchemaBuilderState`/`SchemaDefinition`/JSON inline per test; no shared mutable state. 966 passed in a single ordered run. |
| **Isolation** | ✅ PASS | Each new test targets one behavior (e.g., `test_in_output_false_column_is_excluded_from_output`, `test_absent_in_output_defaults_to_true`). |
| **Fast Execution** | ✅ PASS | Full suite ~23s for 966 tests; the #54-targeted subset (54 tests) runs in 1.64s. |
| **Determinism** | ✅ PASS | No wall-clock, RNG, sleep, or network. Property test (`_draw_column`) draws `in_output` via Hypothesis `st.booleans()` with the repo's seeded config. |
| **Readability & Maintainability** | ✅ PASS | Descriptive `test_...` names; docstrings cite the AC each test covers; AAA structure with explicit Arrange/Act/Assert comments. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Baseline Coverage Documented** | ✅ PASS | Baseline (pre-#54): 99.07% lines, 94.15% branch (`evidence/baseline/baseline-pytest.md`). Command: `poetry run pytest --cov --cov-branch`. |
| **No Coverage Regression** | ✅ PASS | Post-change: 99.07% lines, 94.15% branch (independently re-run this audit). Change: +0.00%. New code paths covered by new tests. |
| **New Code Coverage >=90%** | ✅ PASS | New/edited modules: `_schema_model_specs` 100%, `_schema_view_protocols` 100%, `schema_serialization` 98%, `schema_builder_presenter` 98%, `schema_builder_dialog` 98%, `_schema_builder_drag_tabs` 96%, `_schema_provider_factory` 95%, `_schema_builder_state` 94%, `_columns_tab_presenter` 93%, `_schema_loader_helpers` 92%. New `in_output` branches in the loader, serialization, and model are exercised. |
| **Comprehensive Coverage** | ✅ PASS | `in_output` covered for: model default; serialization emit/parse/absent-default/round-trip; loader inclusion/exclusion both modes; discriminator-used-for-dedup-yet-excluded; builder assemble forwarding; provider-factory split. |
| **Positive Flows** | ✅ PASS | `test_in_output_true_column_is_included_in_output`, `test_assemble_schema_forwards_in_output_true_and_false` (True case), `test_in_output_false_round_trips`. |
| **Negative Flows** | ✅ PASS | `test_in_output_false_column_is_excluded_from_output`, `test_processing_only_discriminator_used_for_dedup_but_excluded`. |
| **Edge Cases** | ✅ PASS | `test_absent_in_output_defaults_to_true` (legacy JSON without the field); discriminator required:false located by name (absence tolerated). |
| **Error Handling** | ✅ PASS | Serialization `reject_unknown_keys` still enforced; `optional_bool` default path covered. No new error path introduced beyond defaulted parse. |
| **Concurrency** | N/A | No concurrent behavior in this change. |
| **State Transitions** | ✅ PASS | Builder schema -> state -> schema round-trip preserves `in_output` (`test_assemble_schema_*`, presenter round-trip). |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.07% lines (94.15% branch) -> Post-change: 99.07% lines (94.15% branch). Change: +0.00% lines (+0.00% branch). New/changed-code coverage: >=92% per edited module (lowest `_schema_loader_helpers` at 92%). Disposition: PASS. Evidence: `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-coverage-delta.md`, `artifacts/python/lcov.info`, independent audit re-run (966 passed).
- PowerShell: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: no PowerShell files in `git diff 7bfa57c..HEAD`.
- TypeScript: Baseline: N/A - out of scope -> Post-change: N/A - out of scope. Change: N/A. New/changed-code coverage: N/A - out of scope. Disposition: N/A. Evidence: no TypeScript files in `git diff 7bfa57c..HEAD`.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clear Failure Messages** | ✅ PASS | Behavioral assertions (`"Discriminator" not in out.columns`, `out.loc[0, "Amt"] == 15.0`) give actionable messages. |
| **Arrange-Act-Assert Pattern** | ✅ PASS | All new tests labelled with Arrange/Act/Assert comments. |
| **Document Intent** | ✅ PASS | Each new test has a docstring naming the AC and scenario. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Avoid External Dependencies** | ✅ PASS | Tests use in-memory `pd.DataFrame` and inline schema objects/JSON strings. The provider-factory test reads the bundled schema via `SchemaRegistry(Path("."), ...)` — a packaged read-only resource, not a runtime temp file or network. |
| **Use Mocks/Stubs** | ✅ PASS | `FakeSchemaService`, `FakeSchemaBuilderView` used at the existing seams; no real Qt. |
| **Environment Stability** | ✅ PASS | No temp file creation; no mutable global state; legacy-JSON test uses an inline string literal, not a file. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Pre-submission Review** | ✅ PASS | This audit serves as the required review. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Clarify the objective** | ✅ PASS | Spec v1.0 (Final) and issue #54 define the objective and locked design. |
| **Read existing change plans** | ✅ PASS | Plan `plan.2026-06-06T14-44.md` present; Phase 0 evidence records policy read. |
| **Document the plan** | ✅ PASS | Plan + per-phase QA-gate evidence artifacts present under `evidence/`. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Simplicity first** | ✅ PASS | Output determination is a single inclusion predicate (`if c.in_output`) replacing the prior drop-set computation; the additive field has a safe default. |
| **Reusability** | ✅ PASS | `_output_column_order` and the `none`-mode emit path both filter by the same `in_output` concept; `_by_name_optional_columns` already keyed on `required` and absorbed the discriminator without new code. |
| **Extensibility** | ✅ PASS | `in_output` is an additive, defaulted dataclass field; `drop_columns` kept in the JSON shape for backward compatibility. |
| **Separation of concerns** | ✅ PASS | Source-presence (`required`) and output-membership (`in_output`) are now distinct concepts, documented in the `ColumnSpec` docstring. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Cohesive modules** | ✅ PASS | Each edited module retained its single responsibility; no grab-bag additions. |
| **Under 500 lines** | ✅ PASS | Independently measured (`awk END{print NR}`): `schema_builder_dialog.py` 493, `_schema_model_specs.py` 480, `schema_builder_presenter.py` 470, `_schema_loader_helpers.py` 464, `schema_serialization.py` 432, `_schema_view_protocols.py` 378, `_columns_tab_presenter.py` 357, `_schema_builder_drag_tabs.py` 307, `_schema_builder_state.py` 293. Largest test file changed: `test_schema_serialization.py` 463. All under 500. (Confirms the brief's 493-line dialog check.) |
| **Public vs internal** | ✅ PASS | Internal helpers `_`-prefixed; `ColumnSpec` public field is additive and documented. |
| **No circular dependencies** | ✅ PASS | No new imports that introduce cycles; Pyright clean. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Descriptive names** | ✅ PASS | `in_output` is descriptive; snake_case throughout. |
| **Docs/docstrings** | ✅ PASS | `ColumnSpec` gained a "Required vs. in_output" docstring section and an `Attributes:` entry; serialization, loader, protocol, presenter, and dialog docstrings updated to reflect the new field. |
| **Comment why, not what** | ✅ PASS | Loader comments explain the discriminator carry-through rationale (e.g., "carried through processing but excluded here by omission"); serialization comment explains the additive default. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| **1. Formatting** | ✅ PASS | `poetry run black --check src/ tests/` -> "223 files would be left unchanged" (independently re-run this audit). |
| **2. Linting** | ✅ PASS | `poetry run ruff check src/ tests/` -> "All checks passed!" |
| **3. Type checking** | ✅ PASS | `poetry run pyright` -> "0 errors, 0 warnings, 0 informations". |
| **4. Testing** | ✅ PASS | `poetry run pytest --cov=src --cov-branch` -> "966 passed". |
| **Full toolchain loop** | ✅ PASS | All four stages green in a single audit pass. |
| **Explicit reporting** | ✅ PASS | Commands and results recorded here and in `evidence/qa-gates/`. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Summarize changes** | ✅ PASS | Commit `55261bf` message and spec/plan summarize the change. |
| **Design choices explained** | ✅ PASS | Spec "Design decision (locked)" documents the chosen and rejected approaches. |
| **Update supporting documents** | ✅ PASS | `ColumnSpec`/serialization/loader docstrings and the bundled-schema JSON updated; AC checkboxes checked in issue.md/spec.md. |
| **Provide next steps** | ✅ PASS | Plan Phase 5 records final QA and AC traceability. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Formatting with Black** | ✅ PASS | `poetry run black --check src/ tests/` clean. |
| **Linting with Ruff** | ✅ PASS | `poetry run ruff check src/ tests/` clean. |
| **Type checking with Pyright** | ✅ PASS | `poetry run pyright` 0 errors. |
| **Testing with Pytest** | ✅ PASS | 966 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Strong typing** | ✅ PASS | `in_output: bool = True` fully typed; 4-tuple->5-tuple annotations updated at every site (`tuple[str, str, bool, bool, tuple[str, ...]]`). No `Any` introduced. |
| **Dataclasses for value objects** | ✅ PASS | `ColumnSpec` is a dataclass; the new field is a defaulted dataclass field. |
| **Protocols/ABCs for interfaces** | ✅ PASS | `SchemaBuilderViewProtocol` signatures updated for the 5-tuple, keeping the Protocol contract precise. |
| **Avoid utility classes** | ✅ PASS | Loader logic remains module-level functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Specific exceptions** | ✅ PASS | No new broad handlers; serialization still uses `reject_unknown_keys`/`optional_bool` with specific behavior. |
| **Logging over print** | ✅ PASS | No `print` added (git-diff scan returned none); existing `logging` pattern retained. |
| **Invariants at construction** | ✅ PASS | `ColumnSpec` dataclass invariants unchanged; field defaults preserve construction safety. |

---

## 3.x Python Suppression Policy (`python-suppressions.md`)

| Requirement | Status | Evidence |
|------------|--------|----------|
| **No unauthorized suppressions** | ✅ PASS | Git-diff scan of `7bfa57c..HEAD` for `noqa`, `type: ignore`, `pyright: ignore`, `# nosec` returned NONE. No suppressions were added. |

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | All tests Pytest; Hypothesis used for the existing serialization property test. |
| **Coverage expectation** | ✅ PASS | Repo-wide 99.07% line / 94.15% branch; edited modules >=92% line; thresholds (85% line / 75% branch) exceeded. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Focused unit tests** | ✅ PASS | One behavior per test. |
| **Mocking sparingly** | ✅ PASS | Real pure code paths preferred; fakes used only at GUI seams. |
| **Organization** | ✅ PASS | Tests mirror code: loader tests in `tests/test_schema_loader_derived.py`, serialization in `tests/test_schema_serialization.py`, builder in `tests/gui/`. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Naming conventions** | ✅ PASS | Descriptive `test_...` names. |
| **Docstrings/comments** | ✅ PASS | Each new test documents its scenario and AC. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| **Use Pytest** | ✅ PASS | `poetry run pytest` -> 966 passed. |
| **No Alternative Test Runners** | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### in_output output determination (loader) — 4 tests

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_in_output_false_excludes_le_discriminator_from_output` | Negative (exclusion) | ✅ |
| `test_in_output_true_column_is_included_in_output` | Positive (inclusion) | ✅ |
| `test_in_output_false_column_is_excluded_from_output` | Negative (exclusion) | ✅ |
| `test_processing_only_discriminator_used_for_dedup_but_excluded` | Edge (dedup + exclusion) | ✅ |

**Coverage:** `_schema_loader_helpers.py` 92% (missing lines are pre-existing and untouched).

### in_output serialization — 3 contributions

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_absent_in_output_defaults_to_true` | Edge (legacy JSON) | ✅ |
| `test_in_output_false_round_trips` | Positive (round-trip) | ✅ |
| `_draw_column` property extension (in_output drawn independently) | Property | ✅ |

**Coverage:** `schema_serialization.py` 98%.

### builder forwarding + provider factory — 3 tests

| Test Name | Scenario Type | Status |
|-----------|--------------|--------|
| `test_assemble_schema_forwards_in_output_true_and_false` | Positive/Negative | ✅ |
| `test_assemble_schema_default_in_output_true_row` | Positive | ✅ |
| `test_real_bundled_le_ytd_ytg_is_in_optional_specs` | Integration (bundled split) | ✅ |

**Coverage:** `_schema_builder_state.py` 94%, `_schema_provider_factory.py` 95%.

**Not covered:** None specific to this change; residual missing lines per module are pre-existing.

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 966 | ✅ |
| Tests Passed | 966 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Execution Time | ~23s total | ✅ Fast |
| Code Coverage | 99.07% lines, 94.15% branches | ✅ |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black --check src/ tests/` | 223 files unchanged | ✅ |
| Ruff Linting | `poetry run ruff check src/ tests/` | All checks passed | ✅ |
| Pyright Type Checking | `poetry run pyright` | 0 errors, 0 warnings | ✅ |
| Pytest Tests | `poetry run pytest --cov=src --cov-branch` | 966 passed | ✅ |

**Notes:** No pre-existing failures. `.github/workflows/**` confirmed unchanged (`git diff --stat 7bfa57c..HEAD -- .github/` empty), so `modified-workflow-needs-green-run`, `ci-workflows.md`, and `benchmark-baselines.md` are N/A for this delta.

---

## 8. Gaps and Exceptions

### Identified Gaps
**None.** All policy requirements are met.

### Approved Exceptions
**None.** No exceptions needed.

### Removed/Skipped Tests
**None.** The prior `test_drop_columns_removed_from_output` was renamed to `test_in_output_false_excludes_le_discriminator_from_output` with the `"YTD/YTG" not in out.columns` assertion preserved and strengthened — a rename, not a removal.

---

## 9. Summary of Changes

### Commits in This Delta
1. **55261bf** - refactor(schema): determine output by in_output inclusion, not drop-by-name (#54)

### Files Modified
1. `src/_schema_model_specs.py` (MODIFIED) — add `in_output: bool = True`, docstring section.
2. `src/schema_serialization.py` (MODIFIED) — emit/parse `in_output` with default True.
3. `src/_schema_loader_helpers.py` (MODIFIED) — output by inclusion in `_output_column_order` and `none`-mode emit; discriminator carry-through docstrings.
4. `src/gui/_schema_view_protocols.py`, `src/gui/presenters/_columns_tab_presenter.py`, `src/gui/presenters/_schema_builder_state.py`, `src/gui/presenters/schema_builder_presenter.py`, `src/gui/widgets/_schema_builder_drag_tabs.py`, `src/gui/widgets/schema_builder_dialog.py` (MODIFIED) — 4-tuple->5-tuple migration.
5. `src/schemas/default_le.schema.json`, `src/schemas/default_aop.schema.json` (MODIFIED) — explicit `in_output`; LE `YTD/YTG` required:false in_output:false, drop_columns [].
6. 12 test files (MODIFIED/NEW) including new `tests/gui/test_schema_builder_assemble.py`.

---

## 10. Compliance Verdict

### Overall Status: ✅ FULLY COMPLIANT

The #54 delta meets the cross-language and Python-specific code-change and unit-test policies, the suppression policy (no suppressions), the self-explanatory commenting policy, and the file-size policy. The full toolchain is green on an independent re-run; parity is preserved (LE 5 + AOP 4 parity tests pass). No FAIL or blocking-PARTIAL findings.

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes / Design Principles / Module & File Structure / Naming, Docs, Comments / Toolchain / Summarize & Document: all PASS.

#### Language-Specific Code Change Policy (Section 3) — Python
- ✅ Tooling & Baseline / Design & Typing / Error Handling: all PASS. Suppressions: none.

#### General Unit Test Policy (Section 1)
- ✅ Core Principles / Coverage & Scenarios / Test Structure / External Dependencies / Policy Audit: all PASS.

#### Language-Specific Unit Test Policy (Section 4) — Python
- ✅ Framework & Scope / Test Style & Structure / Naming & Readability / Toolchain: all PASS.

### Metrics Summary
- ✅ 966/966 tests passing (100%)
- ✅ 99.07% line coverage, 94.15% branch coverage
- ✅ All edited files under 500 lines (dialog 493)
- ✅ All code quality checks passing
- ✅ No suppressions added; no workflow changes

### Recommendation

**Ready for merge.** No remediation required for the #54 delta.

---

## Appendix A: Test Inventory (#54-relevant additions/changes)

- `tests/gui/test_schema_builder_assemble.py::test_assemble_schema_forwards_in_output_true_and_false`
- `tests/gui/test_schema_builder_assemble.py::test_assemble_schema_default_in_output_true_row`
- `tests/gui/test_schema_provider_factory.py::test_real_bundled_le_ytd_ytg_is_in_optional_specs`
- `tests/test_default_schemas.py::test_le_drops_ytd_ytg_source_column` (updated)
- `tests/test_schema_loader_derived.py::test_in_output_false_excludes_le_discriminator_from_output`
- `tests/test_schema_loader_derived.py::test_in_output_true_column_is_included_in_output`
- `tests/test_schema_loader_derived.py::test_in_output_false_column_is_excluded_from_output`
- `tests/test_schema_loader_derived.py::test_processing_only_discriminator_used_for_dedup_but_excluded`
- `tests/test_schema_serialization.py::test_absent_in_output_defaults_to_true`
- `tests/test_schema_serialization.py::test_in_output_false_round_trips`
- `tests/test_schema_loader_parity_le.py` (5 tests, parity — unchanged, pass)
- `tests/test_schema_loader_parity_aop.py` (4 tests, parity — unchanged, pass)

## Appendix B: Toolchain Commands Reference

```bash
env -u VIRTUAL_ENV poetry run black --check src/ tests/
env -u VIRTUAL_ENV poetry run ruff check src/ tests/
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing
```

---

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-06
**Policy Version:** Current (as of audit date)
