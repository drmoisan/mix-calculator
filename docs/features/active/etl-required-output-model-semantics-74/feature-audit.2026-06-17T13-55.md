# Feature Audit: etl-required-output-model-semantics (#74, epic child CF1)

**Audit Date:** 2026-06-17
**Feature Folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Base Branch:** `main` (`0a47fef`)
**Head Branch:** `refactor/etl-required-output-model-semantics-74` (`1182cad`)
**Work Mode:** `full-feature`
**Audit Type:** Post-remediation acceptance verification (cycle 3)

---

## Scope and Baseline

- **Base branch:** `main` (commit `0a47fef2869b97d8a290d33570ebeee834c80987`)
- **Head branch/commit:** `refactor/etl-required-output-model-semantics-74` (commit `1182cad0b93b1c2d3fce771863bbd38b2f0c8cd5`)
- **Merge base:** `0a47fef2869b97d8a290d33570ebeee834c80987`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/etl-required-output-model-semantics-74/evidence/**`
  - Additional evidence: independent toolchain run + schema-flag dumps performed during this review.
- **Feature folder used:** `docs/features/active/etl-required-output-model-semantics-74/`
- **Requirements source:** `spec.md` (Definition of Done). Work mode `full-feature` resolves to `spec.md` and `user-story.md`; `user-story.md` does not exist in this CF1 feature folder, so the authoritative AC source is the `spec.md` Definition of Done (the parent `issue.md` carries an epic-level early-draft AC list spanning all of CF1-CF7, not the CF1 DoD).
- **Work mode resolution note:** `issue.md` (parent epic folder) declares `- Work Mode: full-feature`. Per the work-mode contract, the CF1 child DoD in `spec.md` is the authoritative acceptance source for this child review.
- **Scope note:** AC #3 is rescoped to `default_le` only; AOP `required`-flag minimization is descoped to CF2 (see the spec Descope note and epic `initiative.md`). This review verified the descope against the live diff: `git diff main -- src/schemas/default_aop.schema.json` is empty.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/etl-required-output-model-semantics-74/spec.md` — primary / only source (Definition of Done).
- `docs/features/active/etl-required-output-model-semantics-74/user-story.md` — not present; no checkbox source to track.

### Acceptance criteria

From `spec.md` Definition of Done:

1. `SCHEMA_FORMAT_VERSION == "3.0"`; docstrings define `required` = required-output column.
2. Deterministic `2.0 -> 3.0` migration with documented, output-preserving mapping + test.
3. `default_le` updated to 3.0; months/FY/quarters (and the loader-produced `Super Category`) `required: false`, `in_output` unchanged; quirks preserved. (`default_aop` minimization descoped to CF2 — see Descope note; CF1 makes no AOP schema-file change.)
4. `required_output_columns()` accessor returns the ordered required-output set.
5. Bundled-schema loader output unchanged (zero regression); negative/positive load tests pass.
6. Toolchain clean (format -> lint -> type-check -> test); coverage maintained.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | `SCHEMA_FORMAT_VERSION == "3.0"`; docstrings define `required` = required-output | PASS | `src/schema_model.py` sets `SCHEMA_FORMAT_VERSION: str = "3.0"`; module + `SchemaDefinition` docstrings define `required` as "required OUTPUT column"; `_schema_model_specs.py` `ColumnSpec` docstrings rewritten. `test_schema_format_version_value` asserts `== "3.0"`. | `git diff main...HEAD -- src/schema_model.py`; `poetry run pytest tests/test_schema_model.py::test_schema_format_version_value` | No remaining `"2.0"` literal except a docstring example. |
| 2 | Deterministic `2.0 -> 3.0` migration with documented mapping + test | PASS | `_version_predates_required_output` + `migrate_required` plumbing applies `required(3.0) = required(2.0) AND in_output(2.0)` for pre-3.0 sources only; documented in `_object_to_column`. Five migration tests cover drop/stay/pass-through/round-trip/unparseable. | `poetry run pytest tests/test_schema_migration.py` | New migration code at 100% coverage. |
| 3 | `default_le` updated to 3.0; months/FY/quarters and `Super Category` `required: false`, `in_output` unchanged; quirks preserved (LE-scoped; AOP descoped to CF2) | PASS | `default_le.schema.json` version `3.0`; dump confirms `Customer/SKU Descripiton/SKU #/Type/GtN Mapping/PPG` `required: true`; `Jan`–`Dec`/`FY`/`Q1`–`Q4`/`Super Category` `required: false`, `in_output: true`; `KEY`/`YTD/YTG` unchanged. AOP file zero-diff vs `main`. | `python -c "import json; ..."` flag dump; `git diff main -- src/schemas/default_aop.schema.json` (empty) | AC rescoped to LE; AOP minimization deferred to CF2 per spec Descope note. LE portion fully met. |
| 4 | `required_output_columns()` accessor returns the ordered required-output set | PASS | `SchemaDefinition.required_output_columns()` returns declared-order `required` source columns; `test_default_le_required_output_columns_accessor` asserts it equals the six ordered dimensions and excludes `Super Category`/measures. | `poetry run pytest tests/test_default_schemas.py::test_default_le_required_output_columns_accessor` | Derived contribution intentionally empty in CF1; structurally extensible. |
| 5 | Bundled-schema loader output unchanged (zero regression); negative/positive load tests pass | PASS | LE + AOP parity tests pass; `test_default_le_resolves_when_only_months_are_absent` (positive) and `test_default_le_resolve_raises_when_required_dimension_absent` (negative) pass. | `poetry run pytest tests/test_schema_loader_parity_le.py tests/test_schema_loader_parity_aop.py tests/test_schema_loader_core.py tests/test_default_schemas.py` | Output parity is the zero-regression oracle for both bundled schemas. |
| 6 | Toolchain clean; coverage maintained | PASS | Independent single clean pass this review: Black (243 unchanged), Ruff (passed), Pyright (0/0/0), Pytest (1058 passed). Repo 98% line / 94% branch; changed modules 100%/100%/98%. | `poetry run black --check .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest --cov --cov-branch --cov-report=term-missing` | No regression on changed lines. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 6 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Carry AOP `required`-flag minimization into CF2 along with the loader located-by-name/presence-optional decouple (already tracked in epic `initiative.md`).
2. When CF2 introduces a required-derived output, extend `required_output_columns()` to populate its derived contribution and add coverage.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All six DoD criteria evaluate to PASS; the `spec.md` DoD checkboxes are already `- [x]` (set during execution). No change is required.
- AC #3 is verified under its rescoped (LE-only) wording; the AOP portion is descoped to CF2 and is not a CF1 gap.

### AC Status Summary

- Source: `docs/features/active/etl-required-output-model-semantics-74/spec.md`
- Total AC items: 6
- Checked off (delivered): 6
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 6 | 6 | 0 | Checkbox-backed (DoD); all already `- [x]` and verified PASS this review. |
| `user-story.md` | 0 | 0 | 0 | Not present in the CF1 feature folder; not an authoritative source for this child. |

No additional source-file checkbox change was made because all DoD items were already checked during execution and each independently verifies to PASS in this audit.
