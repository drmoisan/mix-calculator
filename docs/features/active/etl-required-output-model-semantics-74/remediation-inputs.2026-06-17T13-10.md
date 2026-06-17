# Remediation Inputs: etl-required-output-model-semantics (#74, epic child CF1) — cycle 2

**Entry timestamp:** 2026-06-17T13-10
**Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Base branch:** `main` (`0a47fef`)
**Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
**Supersedes:** cycle 1 (`remediation-inputs.2026-06-17T12-35.md`), which failed because the AOP
required-flag flip reorders SchemaLoader output for the `none`-dedup path. This cycle authorizes
the loader-ordering fix that cycle 1 was not scoped to make.

## Provenance

- Cycle-1 regression dossier: `evidence/regression-testing/r1-output-order-regression.2026-06-17T12-35.md`
- Cycle-1 audits: `policy-audit.2026-06-17T12-35.md`, `code-review.2026-06-17T12-35.md`, `feature-audit.2026-06-17T12-35.md` (AC #3 PARTIAL).

## Root Cause (confirmed)

In `src/_schema_loader_helpers.py`:
- `resolve_and_rename` builds `columns_to_keep` as the `required` columns first (declared order),
  then the by-name-located optional columns appended (`KEY`, then declared `required=False`
  columns in schema order).
- `emit_output_columns` for `dedup.mode == "none"` (AOP) preserves the working frame's natural
  column order.

Therefore, for the AOP (`none`) path the emitted column ORDER depends on the `required` flag.
Flipping AOP measures (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`) to `required: false` moves them from the
required group into the appended group, reordering the output (no data loss; columns reorder).
The `default_le` (`aggregate`) path is unaffected because `emit_output_columns` rebuilds canonical
order via `_output_column_order` for collapsing modes.

## Enumerated Fix List

### R1 — Decouple `none`-dedup emitted column ORDER from the `required` flag (Major; loader-ordering only)

- **File:** `src/_schema_loader_helpers.py`
- **Goal:** Make the AOP (`none`-dedup) output column order independent of which columns are
  marked `required`, so the required-output semantics change does not reorder output.
- **Constraint (binding oracle):** `tests/test_schema_loader_parity_aop.py` must pass UNCHANGED —
  the SchemaLoader AOP output (columns, order, dtypes, values, index) must remain byte-identical
  to the pre-change baseline and to `src/load_aop.py`. Confirm the exact target order against
  `src/load_aop.py` / `src/_load_aop_helpers.py` and the parity test before choosing the mechanism.
- **Allowed mechanisms (planner's choice, whichever preserves parity):** order the `none`-path
  output (and/or the `resolve_and_rename` keep-list) by a flag-independent rule — e.g. by the
  schema's declared column order for `in_output` columns with `KEY`/derived placed exactly where
  `load_aop` places them — rather than by required-vs-optional grouping. The change must be
  ordering-only: no change to which columns are emitted, no dtype/value change, no change to the
  collapsing (`default_le`) path output.
- **Do not** alter `default_le` output (its parity tests must also remain unchanged).

### R2 — Align `default_aop.schema.json` `required` flags to the 3.0 required-output meaning (Major)

- **File:** `src/schemas/default_aop.schema.json`
- Set `required: false` on measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4`; keep their `in_output: true`.
- Keep dimensions `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`,
  `Super Category`, `PPG` as `required: true` (AOP `Super Category` is a genuine source dimension,
  `derived_columns` is empty — unlike LE where it is a `copy_from` derived column).
- `KEY` and `YTG` remain `required: false`, `in_output: true`.
- No change to `in_output`, column order, dtypes, key, dedup, or any value.

### R3 — Add `default_aop` `required_output_columns()` accessor test

- **File:** `tests/test_default_schemas.py`
- Mirror the existing `default_le` accessor test. Assert the returned tuple is exactly the AOP
  output-identity dimensions in declared order — `("Customer", "SKU Descripiton", "SKU #",
  "Customer Master", "Type", "Super Category", "PPG")` — and excludes all measures, `KEY`, and `YTG`.

## Verification

- `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q` — AOP and LE parity unchanged + new accessor test passes.
- Print check: `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` — only the seven output-identity dimensions.
- Full toolchain single clean pass: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Coverage >= 85% line, >= 75% branch; no regression on changed lines.
- After success, re-check spec DoD AC #3 to `- [x]`.

## Do-Not-Do List

- Do not change any emitted output for AOP or LE (columns, order, dtypes, values, index): zero regression is mandatory; the parity tests are the oracle.
- Do not extend scope into CF2-CF7 beyond the single ordering-only decoupling in `_schema_loader_helpers.py` required to keep AOP parity (no matching redesign, no GUI, no `normalize_le` work, no "drop unassigned" behavior change).
- Do not relax identity-dimension `required` flags on AOP; only the measure columns change.
- Do not weaken or remove existing tests, parity assertions, or coverage thresholds.
- Do not introduce suppressions; none are authorized for this change.
- Do not add dependencies.
- Do not exceed the 500-line file cap. `src/_schema_loader_helpers.py` is 465 lines; keep the ordering change minimal or extract a helper rather than growing past 500.

## Notes for the Planner

- The ordering fix is the enabling change; do it (R1) before flipping the AOP flags (R2) so the
  flip lands on a flag-independent ordering and parity stays green throughout.
- Confirm the exact AOP output column order from `src/load_aop.py` and the parity test fixture
  before choosing the mechanism; the declared schema order may differ from `load_aop`'s emitted
  order (for example `KEY`/`YTG` placement), so match the parity oracle, not the raw declared order.
