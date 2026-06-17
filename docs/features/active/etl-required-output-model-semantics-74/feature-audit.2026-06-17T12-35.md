# Feature Audit: etl-required-output-model-semantics (#74, epic child CF1)

**Audit Date:** 2026-06-17
**Feature Folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Base Branch:** `main`
**Head Branch:** `refactor/etl-required-output-model-semantics-74`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `0a47fef2869b97d8a290d33570ebeee834c80987`)
- **Head branch/commit:** `refactor/etl-required-output-model-semantics-74` (commit `02e157984442a97dcc39cc41967f1adb10771f5b`)
- **Merge base:** `0a47fef2869b97d8a290d33570ebeee834c80987`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` (verified current: its resolved head `02e1579` and base `0a47fef` match the branch under review)
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt` and live `git diff 0a47fef...02e1579`
  - Feature evidence: `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/**` and `evidence/qa-gates/**`
  - Additional evidence: independent full-suite re-run (`poetry run pytest tests/ --cov=... --cov-branch`, exit 0, 1058 passed)
- **Feature folder used:** `docs/features/active/etl-required-output-model-semantics-74/`
- **Requirements source:** `spec.md` Definition of Done (full-feature work mode)
- **Work mode resolution note:** No `issue.md` exists in this active feature folder. Per the work-mode contract, a missing/malformed marker fails closed to `full-feature`. The atomic plan records `- Work Mode: full-feature`, and the caller explicitly designated the spec.md Definition of Done as the AC source; both agree on full-feature. For full-feature, AC sources are normally `spec.md` and `user-story.md`; no `user-story.md` exists in this folder, so the spec.md Definition of Done is the sole authoritative AC source for this child.
- **Scope note:** Scope is the full branch diff against `main` (single language with changed code files: Python; plus two bundled JSON schemas). The PR-context summary was cross-checked against the live head and is not stale. No PR exists yet for this branch (author-asserted autoclose issue #74).

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/etl-required-output-model-semantics-74/spec.md` — only authoritative AC source (Definition of Done)
- `user-story.md` — not present in this feature folder; not applicable

### Acceptance criteria

From `spec.md` "## Definition of Done":

1. `SCHEMA_FORMAT_VERSION == "3.0"`; docstrings define `required` = required-output column.
2. Deterministic `2.0 → 3.0` migration with documented, output-preserving mapping + test.
3. `default_le`/`default_aop` updated to 3.0; months/FY/quarters `required: false`, `in_output` unchanged; quirks preserved.
4. `required_output_columns()` accessor returns the ordered required-output set.
5. Bundled-schema loader output unchanged (zero regression); negative/positive load tests pass.
6. Toolchain clean (format → lint → type-check → test); coverage maintained.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | `SCHEMA_FORMAT_VERSION == "3.0"`; docstrings define `required` = required-output | PASS | `src/schema_model.py` sets `SCHEMA_FORMAT_VERSION: str = "3.0"`; module/class/version docstrings and `ColumnSpec` docstring rewritten to "required OUTPUT column" / "emitted (may be true without `required`)". | `git diff 0a47fef...02e1579 -- src/schema_model.py src/_schema_model_specs.py` | No `"2.0"` literal remains as the format version. |
| 2 | Deterministic `2.0 → 3.0` migration with output-preserving mapping + test | PASS | `_version_predates_required_output` + `migrated_required = parsed_required and in_output if migrate_required else parsed_required` in `schema_serialization.py`; preserves `in_output`. Five migration tests pass. | `poetry run pytest tests/test_schema_migration.py` | Mapping is `required(3.0) = required(2.0) AND in_output(2.0)`; documented in code and spec. |
| 3 | `default_le`/`default_aop` updated to 3.0; months/FY/quarters `required: false`, `in_output` unchanged; quirks preserved | PARTIAL | `default_le`: version `3.0`; `Jan`–`Dec`, `FY`, `Q1`–`Q4` and `Super Category` set `required: false` with `in_output: true`; identity dimensions remain required; quirks preserved. `default_aop`: version `3.0` only — `required` flags NOT aligned to the 3.0 meaning (measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4` still `required: true`). | `python -c "import json; ..."` dumps of both schema files; `git diff` of both | The DoD clause "months/FY/quarters `required: false`" is satisfied for LE. Both schemas are "updated to 3.0" by version. However spec Scope additionally directs "align `required` flags to the new meaning" for AOP, which was not done — marked PARTIAL for the AOP alignment gap. |
| 4 | `required_output_columns()` accessor returns the ordered required-output set | PASS | `SchemaDefinition.required_output_columns()` returns declared-order required source columns plus a (currently empty) required-derived contribution; for `default_le` returns `('Customer', 'SKU Descripiton', 'SKU #', 'Type', 'GtN Mapping', 'PPG')`, excluding measures and `Super Category`. | `poetry run pytest tests/test_default_schemas.py::test_default_le_required_output_columns_accessor` | 100% line/branch coverage of the accessor. |
| 5 | Bundled-schema loader output unchanged (zero regression); negative/positive load tests pass | PASS | Parity tests assert `SchemaLoader(default_le)`/`SchemaLoader(default_aop)` output equals the protected reference in columns/order/dtypes/values (36 passed). Loader positive test: source missing only month/quarter columns loads; negative test: source missing `Customer` still raises. | `poetry run pytest tests/test_schema_loader_parity_le.py tests/test_schema_loader_parity_aop.py tests/test_schema_loader_core.py` | Zero output regression confirmed for both bundled schemas. |
| 6 | Toolchain clean (format → lint → type-check → test); coverage maintained | PASS | Black 243 unchanged; Ruff 0 errors (no new suppressions); Pyright 0 errors/warnings; Pytest 1058 passed. Repo coverage 99.09% line / 94.10% branch; changed modules 98-100% line. Independently re-run, exit 0. | `poetry run black . && poetry run ruff check . && poetry run pyright && poetry run pytest --cov --cov-branch` | Single clean pass; coverage maintained, no regression on changed lines. |

---

## Summary

**Overall Feature Readiness:** NEEDS REVISION

**Criteria summary:**
- **PASS:** 5 criteria
- **PARTIAL:** 1 criterion
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. AC #3 (PARTIAL): `default_aop.schema.json` `required` flags not aligned to the 3.0 required-output meaning — only the version was bumped. Spec Scope directs aligning AOP `required` flags to the new meaning; AOP measure columns remain `required: true`. Non-blocking to quality gates (AOP output unchanged, parity passes), but the foundational semantic is inconsistent across the two bundled schemas.

**Recommended follow-up verification steps:**

1. Set AOP measure columns (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`) to `required: false` (keep `in_output: true`), preserve identity-dimension `required: true`, re-run bundled parity to confirm zero AOP output change, and add an AOP `required_output_columns()` assertion.
2. Re-run the full toolchain (black → ruff → pyright → pytest --cov --cov-branch) and confirm a single clean pass.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if represented as markdown checkboxes and not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.

The spec.md Definition of Done items were already checked off (`- [x]`) by the executor before this review. AC #3 is evaluated PARTIAL by this review because of the AOP `required`-flag alignment gap; its DoD checkbox should be reverted to unchecked until the AOP alignment is completed. The remaining five items (1, 2, 4, 5, 6) are confirmed PASS and remain checked. See the AOP gap in the policy audit (section 8) and remediation inputs.

### AC Status Summary

- Source: `docs/features/active/etl-required-output-model-semantics-74/spec.md` (Definition of Done)
- Total AC items: 6
- Checked off (delivered): 5 (items 1, 2, 4, 5, 6)
- Remaining (unchecked): 1 (item 3 — PARTIAL pending AOP alignment)
- Items remaining: "`default_le`/`default_aop` updated to 3.0; months/FY/quarters `required: false`, `in_output` unchanged; quirks preserved." (AOP `required` flags not aligned to 3.0 meaning)

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/etl-required-output-model-semantics-74/spec.md` | 6 | 5 | 1 | Checkbox-backed; item 3 reverted to unchecked pending AOP alignment. |

The review reverted the AC #3 checkbox in spec.md from `- [x]` to `- [ ]` to reflect the PARTIAL evaluation, preserving the criterion text verbatim.
