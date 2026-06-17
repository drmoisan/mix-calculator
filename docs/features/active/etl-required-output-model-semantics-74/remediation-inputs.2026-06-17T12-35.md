# Remediation Inputs: etl-required-output-model-semantics (#74, epic child CF1)

**Entry timestamp:** 2026-06-17T12-35
**Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Base branch:** `main` (`0a47fef`)
**Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)

## Source Audit Artifacts (findings provenance)

- `docs/features/active/etl-required-output-model-semantics-74/policy-audit.2026-06-17T12-35.md` (section 8 Gaps; verdict PARTIALLY COMPLIANT)
- `docs/features/active/etl-required-output-model-semantics-74/code-review.2026-06-17T12-35.md` (Findings Table: one Major)
- `docs/features/active/etl-required-output-model-semantics-74/feature-audit.2026-06-17T12-35.md` (AC #3 PARTIAL)

## Finding Severity Summary

- Blocker-severity findings: 0
- Major findings (material PARTIAL, non-blocking to quality gates): 1 — AOP `required`-flag alignment
- Info findings: 2 (file-size proximity to cap; conservative unparseable-version migration) — no action required this cycle

All toolchain gates (Black, Ruff, Pyright, Pytest, coverage, bundled-schema parity) pass. The remediation below is a spec-Scope consistency correction, not a quality-gate failure.

## Enumerated Fix List

### R1 — Align `default_aop.schema.json` `required` flags to the 3.0 required-output meaning (Major)

- **File:** `src/schemas/default_aop.schema.json`
- **Problem:** The file was bumped to `version: "3.0"` but its `required` flags were not aligned to the 3.0 "required OUTPUT identity column" meaning. Measure columns `Jan`–`Dec`, `YTD`, `Q1`–`Q4` remain `required: true` (the old input-presence meaning), inconsistent with the equivalent `default_le` measures, which were correctly set to `required: false`. Spec Scope directs: "`default_aop.schema.json`: bump `version` to `3.0`; align `required` flags to the new meaning without changing its emitted output."
- **Expected behavior:**
  - Set AOP measure columns `Jan`–`Dec`, `YTD`, `Q1`–`Q4` to `required: false`.
  - Keep their `in_output: true` unchanged.
  - Keep identity/dimension columns (`Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`, `PPG`, `Super Category`, and any other output-identity dimension) with their correct `required` values per the 3.0 meaning, without changing emitted output.
  - `KEY` and `YTG` remain `required: false`, `in_output: true` (unchanged).
  - AOP emitted output (columns, order, dtypes, values) must remain byte-identical to the pre-change AOP output (zero regression).
- **Test/coverage to add:** Add a `default_aop` `required_output_columns()` assertion in `tests/test_default_schemas.py` mirroring `test_default_le_required_output_columns_accessor`, asserting the returned tuple contains only the AOP output-identity dimensions and excludes the measure columns.
- **Verification commands:**
  - `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` — expect only output-identity dimensions, no measures.
  - `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_default_schemas.py -q` — bundled AOP parity unchanged + new accessor test passes.
  - `poetry run black . && poetry run ruff check . && poetry run pyright && poetry run pytest --cov --cov-branch --cov-report=term-missing` — single clean pass; coverage >= 85% line, >= 75% branch, no regression on changed lines.
- **Acceptance:** AC #3 in `spec.md` Definition of Done can be re-checked `- [x]` once AOP `required` flags reflect the 3.0 meaning, AOP parity is confirmed unchanged, and the toolchain is clean.

## Do-Not-Do List

- Do not change AOP emitted output: `in_output` flags, column order, dtypes, and values must remain identical (zero regression is mandatory).
- Do not relax identity-dimension `required` flags on AOP; only the measure columns change.
- Do not extend scope into CF2–CF7 (no loader enforcement changes, no matching redesign, no GUI, no `normalize_le` work).
- Do not weaken or remove existing tests, parity assertions, or coverage thresholds.
- Do not introduce suppressions; none are authorized for this change.
- Do not add dependencies.
- Do not exceed the 500-line file cap (`src/schema_serialization.py` is at 497 — if any serialization change is needed, extract a helper module rather than growing the file).

## Notes for the Planner

- This is a single-file data correction plus one test addition; the implementation modules (`schema_model.py`, `schema_serialization.py`, `_schema_model_specs.py`) already support the 3.0 semantics and should not need changes.
- Confirm the exact AOP output-identity dimension set against `src/_load_aop_helpers.py` before flipping flags, so the required-output set matches the as-built AOP identity rather than guessing.
