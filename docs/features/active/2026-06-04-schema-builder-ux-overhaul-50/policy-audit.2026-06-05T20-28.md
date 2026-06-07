# Policy Compliance Audit: schema-builder-ux-overhaul (Issue #50)

**Audit Date:** 2026-06-05
**Code Under Test:** Full branch diff `feature/schema-builder-ux-overhaul-50` vs `main` (merge-base `5e659f2`, head `d8275d9`). Python source under `src/`, tests under `tests/`, bundled JSON schemas under `src/schemas/`, and `scripts/checks/scan_masked_fixtures.py`.
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Scope:** the full feature-vs-base branch diff; NOT any plan/task/phase subset.

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| Python | 60+ files | 922 tests | ✅ 922 pass, 0 fail | 99.5% lines, 96.6% branch | 97.63% lines, 93.63% branch | 93%+ lines |
| JSON | 2 files | N/A | ✅ load validation | N/A (config files) | N/A (config files) | N/A |

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: N/A - out of scope
- TypeScript post-change coverage artifact: N/A - out of scope
- PowerShell baseline coverage artifact: N/A - out of scope
- PowerShell post-change coverage artifact: N/A - out of scope
- Per-language comparison summary: see Section 1.2.1 and `evidence/qa-gates/coverage-comparison.md`

---

## Rejected Scope Narrowing

None. The caller requested the full feature-vs-base audit with the correct base
(`main`) and feature folder. No narrowing to a plan/task/phase subset or
single-language exclusion was attempted. The audit covers the full branch diff.

## Evidence Location Compliance

The branch diff was scanned for evidence files written under non-canonical paths
(`artifacts/baselines/`, `artifacts/qa/`, `artifacts/evidence/`,
`artifacts/coverage/`). No such files were added. All feature evidence is under
the canonical `.../evidence/<kind>/` tree (baseline, qa-gates,
regression-testing, other). The only `artifacts/` write on the branch is
`artifacts/python/lcov.info`, which is the configured pytest coverage output
(`pyproject.toml` `addopts`), not relocatable evidence.

- `scripts/validate_evidence_locations.py`: ABSENT in this repo (persistent
  memory). A git-diff scan was used; result: no violations. Disposition: PASS.

---

## Executive Summary

Overall: PARTIALLY COMPLIANT (blocking). The toolchain (Black, Ruff, Pyright,
Pytest) is green; coverage, masking/confidentiality, tonality, suppression
policy, and evidence-location policy all PASS. The model-layer work
(expected_dtype, version bump, forward migration, structured key parts, aggregate
dedup) is correct and integrated. The blocking findings are
acceptance-criteria/wiring defects: a set of new interactive UI modules and two
presenter seams and the per-tab build-spec provider are implemented and
unit-tested but never wired into the dialog or the composition root. These are
enumerated and counted as AC defects in `feature-audit.2026-06-05T20-28.md`.

**Policy documents evaluated:**
- ✅ `general-code-change.md`
- ✅ `general-unit-test.md`

**Language-specific policies evaluated:**
- ✅ Python: `python.md` + `python-suppressions.md` + `general-unit-test.md`
- N/A PowerShell, TypeScript, C#: no files changed on this branch
- ✅ JSON: bundled schemas validated by load tests (`tests/test_default_schemas.py`)

**Temporary artifacts cleanup:**
- ✅ No throwaway scripts left behind. `scripts/checks/scan_masked_fixtures.py` is a retained, tested tooling script.
- The masking-scan helper is documented and exits cleanly; no ad-hoc temp files.

---

## 1. General Unit Test Policy Compliance

### 1.1 Core Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Independence | ✅ PASS | 922 tests pass under the standard runner; no inter-test ordering dependencies observed; presenter/widget tests construct seams directly. |
| Isolation | ✅ PASS | Pure logic (`dtype_check`, `_schema_activation`) tested without Qt; drag widgets route one gesture to one callback so presenter tests do not simulate Qt drag events. |
| Fast execution | ✅ PASS | Full suite runs headless (offscreen Qt) in the CI/local loop; no sleeps or wall-clock waits in tests. |
| Determinism | ✅ PASS | No randomness or real I/O in unit tests; reader/service collaborators are faked. |
| Readability/maintainability | ✅ PASS | Descriptive `test_...` names, AAA structure, mirrored to code layout. |

### 1.2 Coverage and Scenarios

| Requirement | Status | Evidence |
|------------|--------|----------|
| Baseline coverage documented | ✅ PASS | Baseline 99.5% line / 96.6% branch (`evidence/baseline/baseline-pytest.md`). |
| No coverage regression | ✅ PASS | Post-change 97.63% line / 93.63% branch; decrease attributable to new Qt widget/protocol-stub lines, not regression on previously covered lines. |
| New code coverage | ✅ PASS | New pure-logic modules 95–100%; presenters 93–100%; drag widgets exercised by added tests. |
| Comprehensive coverage | ⚠️ PARTIAL | High line coverage of new modules is achieved via isolated unit tests; the drag/dialog/dtype modules have NO production callers, so coverage does not evidence integrated behavior (see Section 7 and the feature-audit). |
| Positive/negative/edge/error flows | ✅ PASS | Migration, dtype-coercion, activation outcomes (proceed/partial/none), and reader-error paths are covered. |
| Concurrency | N/A | No new concurrency introduced by this feature. |
| State transitions | ✅ PASS | Activation decision routing and builder state transitions are tested. |

### 1.2.1 Per-Language Coverage Comparison

- Python: Baseline: 99.5% line / 96.6% branch. Post-change: 97.63% line / 93.63% branch. Change: -1.87% line / -2.97% branch, attributable to newly added Qt drag-and-drop widget and protocol-stub lines with no regression on previously covered lines. New/changed-code coverage: 93% line minimum across new modules. Disposition: PASS. Evidence: `evidence/qa-gates/coverage-comparison.md`, `evidence/qa-gates/final-pytest.md`, `artifacts/python/lcov.info` (independently computed 98.37% line).
- TypeScript: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no TypeScript files changed on this branch.
- PowerShell: Baseline: N/A. Post-change: N/A. Change: N/A. Disposition: N/A. Evidence: N/A — no PowerShell files changed on this branch.

### 1.2.2 Coverage Threshold Disposition

Repo-wide thresholds (line >= 85%, branch >= 75%) hold with margin. No
regression on changed lines. Caveat noted above re: orphaned-module coverage.

### 1.3 Test Structure and Diagnostics

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clear failure messages | ✅ PASS | Behavioral assertions with explicit expected values. |
| Arrange-Act-Assert | ✅ PASS | Tests follow AAA. |
| Document intent | ✅ PASS | Descriptive names + docstrings. |

### 1.4 External Dependencies and Environment

| Requirement | Status | Evidence |
|------------|--------|----------|
| Avoid external dependencies | ✅ PASS | No network/DB; workbook reader faked. |
| Use mocks/stubs | ✅ PASS | Fake views/readers/services; `QDrag` stubbed in drag tests. |
| Environment stability | ✅ PASS | No prohibited runtime temp files; offscreen Qt. |

### 1.5 Policy Audit Requirement

| Requirement | Status | Evidence |
|------------|--------|----------|
| Pre-submission review | ✅ PASS | This audit plus `code-review` and `feature-audit` artifacts. |

---

## 2. General Code Change Policy Compliance

### 2.1 Before Making Changes

| Requirement | Status | Evidence |
|------------|--------|----------|
| Clarify the objective | ✅ PASS | Issue #50, spec.md with resolved design decisions. |
| Read existing change plans | ✅ PASS | `plan.2026-06-05T1042.md` (110 tasks). |
| Document the plan | ✅ PASS | Plan + evidence folder. |

### 2.2 Design Principles

| Requirement | Status | Evidence |
|------------|--------|----------|
| Simplicity first | ✅ PASS | Small single-purpose modules. |
| Reusability | ✅ PASS | Reuses `FormulaEvaluator`, `find_best_match`, `load_existing`. |
| Extensibility | ✅ PASS | View-protocol seams; keyword-style optional params. |
| Separation of concerns | ✅ PASS | Pure logic separated from Qt widgets. |

### 2.3 Module & File Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Cohesive modules | ✅ PASS | Decomposition matches the spec's planned split. |
| Under 500 lines | ⚠️ PARTIAL | All production/script `.py` files <= 500 (largest 497, recounted via `awk`). `tests/test_schema_serialization.py` is 669 lines — EXCEEDS the cap; `.py` test modules are not exempt. Non-blocking. |
| Public vs internal | ✅ PASS | New helpers are `_`-prefixed internal modules. |
| No circular dependencies | ✅ PASS | Local import of activation classifier avoids an import cycle. |

### 2.4 Naming, Docs, and Comments

| Requirement | Status | Evidence |
|------------|--------|----------|
| Descriptive names | ✅ PASS | PEP 8 conventions. |
| Docs/docstrings | ✅ PASS | Class/function docstrings throughout. |
| Comment why, not what | ✅ PASS | Intent comments on loops/branches; no narration. |

### 2.5 After Making Changes - Toolchain Execution

| Requirement | Status | Evidence |
|------------|--------|----------|
| 1. Formatting | ✅ PASS | `black .` exit 0 (`evidence/qa-gates/final-black.md`). |
| 2. Linting | ✅ PASS | `ruff check .` exit 0 (`evidence/qa-gates/final-ruff.md`). |
| 3. Type checking | ✅ PASS | `pyright` 0 errors strict (`evidence/qa-gates/final-pyright.md`). |
| 4. Testing | ✅ PASS | `pytest` 922 passed (`evidence/qa-gates/final-pytest.md`). |
| Full toolchain loop | ✅ PASS | Single clean pass per evidence. |
| Explicit reporting | ✅ PASS | Commands/results recorded in evidence. |

### 2.6 Summarize and Document

| Requirement | Status | Evidence |
|------------|--------|----------|
| Summarize changes | ✅ PASS | Spec/plan/evidence. |
| Design choices explained | ✅ PASS | Decisions 1-10 + deviation memory. |
| Update supporting documents | ⚠️ PARTIAL | Spec text on AOP dedup migration needs reconciliation (Section 8). |
| Provide next steps | ✅ PASS | Remediation inputs written. |

---

## 3. Language-Specific Code Change Policy Compliance

### Section 3A: Python Code Change Policy Compliance

#### 3A.1 Tooling & Baseline

| Requirement | Status | Evidence |
|------------|--------|----------|
| Formatting with Black | ✅ PASS | exit 0. |
| Linting with Ruff | ✅ PASS | exit 0; no unauthorized suppressions (see 3A.4 note). |
| Type checking with Pyright | ✅ PASS | 0 errors strict. |
| Testing with Pytest | ✅ PASS | 922 passed. |

#### 3A.2 Python Design & Typing

| Requirement | Status | Evidence |
|------------|--------|----------|
| Strong typing | ✅ PASS | Full annotations; Pyright strict clean. |
| Dataclasses for value objects | ✅ PASS | `CallerBuildSpec`, spec dataclasses, key-part model. |
| Protocols/ABCs for interfaces | ✅ PASS | `BuildSpecProvider`, tab protocols, view protocols. |
| Avoid utility classes | ✅ PASS | Pure logic lives in module functions. |

#### 3A.3 Python Error Handling

| Requirement | Status | Evidence |
|------------|--------|----------|
| Specific exceptions | ✅ PASS | Reader `ValueError` surfaced to view; others propagate. |
| Logging over print | ✅ PASS | `logging` used; no stray prints. |
| Invariants at construction | ✅ PASS | `SchemaDefinition`/`DedupPolicy` validate discriminator at init. |

#### 3A.4 Suppression Audit

`# noqa: N802 - Qt override` appears on Qt event handlers in
`_columns_tab_drag.py` (78, 207, 222) and `_key_tab_drag.py` (76, 169, 252, 267).
The `N` (pep8-naming) ruleset is NOT in `pyproject.toml` `[tool.ruff.lint]
select`, so these directives suppress an unselected rule and have no enforcement
effect (no-op). `# type: ignore[...]` additions are all in test files
(drag-event stubs, `QDrag` monkeypatch). Disposition: PASS (procedural note:
remove the no-op `noqa`).

---

## 4. Language-Specific Unit Test Policy Compliance

### Section 4A: Python Unit Test Policy Compliance

#### 4A.1 Framework and Scope

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | ✅ PASS | pytest + pytest-qt. |
| Coverage expectation | ✅ PASS | Repo-wide 97.63% line / 93.63% branch; new code 93%+. |

#### 4A.2 Test Style and Structure

| Requirement | Status | Evidence |
|------------|--------|----------|
| Focused unit tests | ✅ PASS | One behavior per test. |
| Mocking sparingly | ✅ PASS | Fakes for view/reader/service; real pure logic exercised. |
| Organization | ✅ PASS | Tests mirror code layout. |

#### 4A.3 Naming and Readability

| Requirement | Status | Evidence |
|------------|--------|----------|
| Naming conventions | ✅ PASS | Descriptive `test_...` names. |
| Docstrings/comments | ✅ PASS | Scenario docstrings present. |

#### 4A.4 Running the Toolchain

| Requirement | Status | Evidence |
|------------|--------|----------|
| Use Pytest | ✅ PASS | 922 passed. |
| No alternative runners | ✅ PASS | Pytest only. |

---

## 5. Test Coverage Detail

### New/changed modules (per coverage-comparison evidence)

| Module | Coverage | Status |
|--------|----------|--------|
| `src/dtype_check.py` | 95% line | ✅ |
| `src/_schema_model_specs.py` | 100% | ✅ |
| `src/gui/_schema_activation.py` | 100% | ✅ |
| `src/gui/_schema_build_specs.py` | 100% | ✅ |
| `src/gui/_schema_discovery_wiring.py` | 100% | ✅ |
| `src/gui/presenters/_columns_tab_presenter.py` | 93% line | ✅ |
| `src/gui/presenters/_key_tab_presenter.py` | 100% | ✅ |
| `src/gui/presenters/schema_builder_presenter.py` | 98% line | ✅ |
| `src/gui/presenters/source_selection_presenter.py` | 99% line | ✅ |
| `src/gui/widgets/_dtype_check_widget.py` | 100% | ✅ |
| `src/gui/widgets/_columns_tab_drag.py` / `_key_tab_drag.py` | drag handlers exercised; residual uncovered = defensive Qt-event guards | ✅ |

**Not covered:** protocol-stub method bodies (`...`) carry no executable logic.
**Caveat:** these figures derive from isolated unit tests; the drag/dialog/dtype
modules have no production caller (Section 7).

---

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 922 | ✅ |
| Tests Passed | 922 (100%) | ✅ |
| Tests Failed | 0 | ✅ |
| Code Coverage | 97.63% lines, 93.63% branch | ✅ |
| New Code Coverage | 93%+ lines | ✅ |
| Largest test module | 669 lines (`test_schema_serialization.py`) | ⚠️ over cap |

---

## 7. Code Quality Checks

**For Python:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Black Formatting | `poetry run black .` | exit 0 | ✅ |
| Ruff Linting | `poetry run ruff check .` | exit 0 | ✅ |
| Pyright Type Checking | `poetry run pyright` | 0 errors | ✅ |
| Pytest Tests | `poetry run pytest` | 922 passed | ✅ |

**Production wiring / call-site verification (central concern):**

| Seam | Production caller? | Status |
|------|--------------------|--------|
| `on_schema_discovery` ↔ `_tab_combo.currentTextChanged` | Yes (`app.py:436` → `_schema_discovery_wiring.py:123`) | ✅ |
| Import gating ↔ `schema_selected` | Yes (`_schema_discovery_wiring.py:115-124`) | ✅ |
| Drag Columns/Key tabs, dtype widget, derived dialog | No — zero production importers | ❌ |
| `new_from_template` | No — only test callers | ❌ |
| `on_partial_match` (partial → new-from-template) | No — not injected at `app.py:340-347` | ❌ |
| Per-tab `BuildSpecProvider` | No — never constructed | ❌ |

**Notes:** The actual `SchemaBuilderDialog` (via `_schema_builder_tabs.py`
`build_columns_tab`/`build_key_tab`/`build_derived_tab`) still uses pre-feature
plain-text/single-line editors. Workflow policy: no `.github/workflows/**` files
were modified, so `modified-workflow-needs-green-run` does NOT apply.

---

## 8. Gaps and Exceptions

### Identified Gaps

- Production wiring incomplete: the drag-and-drop UI redesign, dtype-check
  display, PowerQuery-style derived dialog, per-tab caller-spec injection, and
  new-from-template flow are implemented and unit-tested but unreachable in
  production. Detailed/counted in `feature-audit.2026-06-05T20-28.md`.
- File-size: `tests/test_schema_serialization.py` (669 lines) exceeds the cap.
- No-op `# noqa: N802` directives in the two drag modules.

### Approved Exceptions

- **AOP dedup mode deviation (P12-T2):** APPROVED by adjudication (Section below).

### Removed/Skipped Tests

- None.

### Dedup-Mode Scope Deviation Adjudication (P12-T2)

Plan P12-T2 directed migrating `default_aop.schema.json` to `aggregate`. The
executor migrated `default_le.schema.json` to `aggregate` (it has discriminator
`YTD/YTG`) and kept `default_aop.schema.json` at `mode: none` (verified in the
diff). The model invariant (`schema_model.py:227`) requires any
`collapse`/`aggregate` mode to name a declared discriminator; AOP has none and
"does not collapse rows." Forcing `aggregate` would violate the invariant and
break AOP loader parity. **Adjudication: PASS** — the deviation is correct;
migrating AOP to aggregate would have been a defect. **Spec reconciliation
(non-blocking):** `spec.md` Decision 1 and AC 14 ("bundled defaults migrated to
aggregate mode") should be amended to "migrate to a collapsing mode where a
discriminator exists (LE); schemas without a discriminator (AOP) retain
`none`." Documentation-only.

---

## 9. Summary of Changes

### Commits in This PR/Branch

- `d8275d9` (head) — feature implementation committed (single feature head per caller).

### Files Modified (high level)

- Model/serialization: `src/schema_model.py`, `src/_schema_model_specs.py` (NEW), `src/schema_serialization.py`, `src/_schema_loader_helpers.py`, `src/dtype_check.py` (NEW).
- Bundled schemas: `src/schemas/default_aop.schema.json`, `src/schemas/default_le.schema.json` (MODIFIED — format 2.0).
- GUI wiring/presenters: `src/gui/app.py`, `src/gui/_schema_wiring.py`, `src/gui/_schema_discovery_wiring.py` (NEW), `src/gui/_schema_activation.py` (NEW), `src/gui/_schema_build_specs.py` (NEW), presenters and protocols.
- New (orphaned in production) widgets: `_columns_tab_drag.py`, `_key_tab_drag.py`, `_derived_formula_dialog.py`, `_dtype_check_widget.py`.
- Tooling: `scripts/checks/scan_masked_fixtures.py` (NEW).
- Tests: extensive additions/updates across `tests/`.

---

## 10. Compliance Verdict

### Overall Status: ⚠️ PARTIALLY COMPLIANT

Toolchain, coverage, masking/confidentiality, tonality, suppression, and
evidence-location policies PASS. Blocking gap: production wiring of the
interactive UI and caller/new-from-template seams is incomplete (counted as 6
distinct AC defects in the feature-audit). One non-blocking file-size finding.

**Fail-closed reminder:** all required baseline/QA/coverage artifacts are present;
the PARTIAL verdict reflects wiring/AC defects, not missing evidence.

---

### Policy-by-Policy Summary

#### General Code Change Policy (Section 2)
- ✅ Before Making Changes
- ✅ Design Principles
- ⚠️ Module & File Structure (one over-cap test module)
- ✅ Naming, Docs, Comments
- ✅ Toolchain Execution
- ⚠️ Summarize & Document (spec text reconciliation pending)

#### Language-Specific Code Change Policy (Section 3)
**For Python:**
- ✅ Tooling & Baseline
- ✅ Python Design & Typing
- ✅ Error Handling

#### General Unit Test Policy (Section 1)
- ✅ Core Principles
- ⚠️ Coverage & Scenarios (orphaned-module coverage caveat)
- ✅ Test Structure
- ✅ External Dependencies
- ✅ Policy Audit

#### Language-Specific Unit Test Policy (Section 4)
**For Python:**
- ✅ Framework & Scope
- ✅ Test Style & Structure
- ✅ Naming & Readability
- ✅ Toolchain

---

### Metrics Summary

- ✅ 922/922 tests passing (100%)
- ✅ 97.63% line coverage, 93.63% branch coverage
- ✅ All four toolchain checks passing
- ❌ Interactive UI redesign + new-from-template + per-tab specs not wired in production

---

### Recommendation

**Needs revision (blocked for merge).** Address the six wiring/AC defects in
`remediation-inputs.2026-06-05T20-28.md` (R1–R6), then re-run the toolchain and
re-verify each seam has a production caller reachable from `build_application`.
Non-blocking: split the over-cap test module, remove no-op `noqa`, reconcile the
spec dedup text.

---

## Appendix A: Test Inventory

| Area | Test module(s) | Status |
|---|---|---|
| Schema model / specs | `tests/test_schema_model.py` | pass |
| Serialization + migration | `tests/test_schema_serialization.py` | pass |
| Dtype check (pure) | `tests/test_dtype_check.py` | pass |
| Activation matching | `tests/gui/test_schema_activation.py` | pass |
| Discovery wiring | `tests/gui/test_schema_discovery_wiring.py` | pass |
| Columns/Key presenters | `tests/gui/test_columns_tab_presenter.py`, `tests/gui/test_key_tab_presenter.py` | pass |
| Drag widgets (isolated) | `tests/gui/test_columns_tab_widgets.py`, `tests/gui/test_key_tab_widget.py` | pass |
| Derived formula dialog (isolated) | `tests/gui/test_derived_formula_dialog.py` | pass |
| Schema builder presenter/dialog | `tests/gui/test_schema_builder_presenter.py`, `tests/gui/test_schema_builder_dialog.py` | pass |
| Source selection presenter | `tests/gui/test_source_selection_presenter.py` | pass |
| App composition/wiring | `tests/gui/test_app_composition.py`, `tests/gui/test_app_wiring*.py` | pass |
| Default schemas load | `tests/test_default_schemas.py` | pass |

Total: 922 tests pass. The isolated drag/dialog widget tests pass but do not
exercise an integrated dialog (those modules are not wired into
`SchemaBuilderDialog`).

## Appendix B: Toolchain Commands Reference

**For Python:**
```bash
env -u VIRTUAL_ENV poetry run black .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
env -u VIRTUAL_ENV poetry run python scripts/checks/scan_masked_fixtures.py
```

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-06-05
**Policy Version:** Current (as of audit date)
