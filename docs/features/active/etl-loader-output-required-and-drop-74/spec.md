# etl-loader-output-required-and-drop - Refactor Spec

- **Issue:** #74 (epic child CF2)
- **Parent:** docs/features/active/2026-06-17-configurable-etl-required-column-contract-74/
- **Owner:** drmoisan
- **Last Updated:** 2026-06-17
- **Status:** Draft
- **Version:** 0.1

## Intent & Outcomes

Make the schema-driven loader honor the redefined `required` (required-output) semantics from CF1
without coupling load behavior to the `required` flag. Today `src/_schema_loader_helpers.py`
infers "located by name / tolerate-absent" from `not required` and orders the `none`-dedup (AOP)
output by required-vs-optional grouping. After CF1, `required` means output-identity, so that
inference is wrong: flipping AOP measures to `required: false` reorders AOP output (verified in CF1
remediation). CF2 introduces an explicit located-by-name signal and decouples which-columns-to-keep
and output ORDER from the `required` flag, then minimizes `default_aop` required flags (deferred
from CF1).

Outcome: AOP and LE SchemaLoader output (columns, order, dtypes, values, index) is unchanged
(parity tests are the oracle), while `default_aop` measures (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`) become
`required: false`. A schema may mark any column `required: false` without affecting which columns
are emitted or their order.

## Invariants (must not change)

- `tests/test_schema_loader_parity_aop.py` and `tests/test_schema_loader_parity_le.py` pass
  UNCHANGED: `list(schema_output.columns) == list(load_aop/normalize_le output.columns)` and all
  values/dtypes/index identical (zero output regression).
- KEY composition, dedup, fill rules, derived columns, and the as-built quirks unchanged.
- No GUI, matching, or `normalize_le` changes (CF5/CF4/CF6/CF7).

## Scope (structural changes)

1. **Located-by-name signal (schema model).** Add a typed `ColumnSpec` boolean (proposed
   `located_by_name`, default `False`) meaning "located by normalized name, tolerated if absent,
   not a source-presence requirement." Serialize/deserialize it (`src/schema_serialization.py`)
   and seed it in the migration to reproduce prior behavior: a column that was located-by-name
   under the old loader (the columns that were `required=False` before CF1 — `KEY`, AOP `YTG`, LE
   `YTD/YTG`) gets `located_by_name=True`. Keep `_schema_model_specs.py` and
   `schema_serialization.py` under the 500-line cap (extract helpers if needed;
   `schema_serialization.py` is near the cap).
2. **Loader decouple (`src/_schema_loader_helpers.py`).**
   - `_by_name_optional_columns` uses `located_by_name` instead of `not required`.
   - Which-columns-to-keep in `resolve_and_rename` becomes flag-independent: keep every declared
     source column that is needed — `required` (raise if absent), or `in_output`, or referenced by
     key/dedup/fill/derived, or `located_by_name` (tolerate absent) — present in the source.
   - The `none`-dedup emitted column ORDER is derived from a flag-independent rule that reproduces
     `load_aop`'s order (match the parity oracle), not from required-vs-optional grouping.
   - `required` still gates presence: a `required` source column that is absent still raises.
3. **AOP schema minimization (`src/schemas/default_aop.schema.json`).** Set `required: false` on
   measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4` (keep `in_output: true`); set `located_by_name` where the
   prior behavior implies it (`KEY`, `YTG`); keep dimensions `required: true`. No emitted-output change.
4. **LE schema alignment (`src/schemas/default_le.schema.json`).** Set `located_by_name` on the
   columns that were located-by-name under the old loader (`KEY`, `YTD/YTG`) so the LE path is
   explicit and parity holds. No emitted-output change.

## Non-Goals

- No "exactly one value column" model validation (kept lenient; AOP is a pass-through pipeline).
- No formula coercion (CF3), no auto-identification (CF4), no GUI (CF5), no migrate/remove of
  `normalize_le` (CF6/CF7).
- No change to emitted output for any bundled schema.

## Dependencies / Touchpoints

- `src/schema_loader.py` calls the helpers; confirm no change needed there.
- `src/schema_matching.py` `_required_columns` reads `required`; confirm unaffected (deeper matching is CF4).
- Persisted user schemas gain the new field via the migration default.

## Risks & Mitigations

- Risk: ordering change breaks AOP/LE parity. Mitigation: parity tests are the oracle; run them
  after the loader change before and after the AOP flag flip.
- Risk: which-columns-to-keep change drops a needed input or keeps an extra. Mitigation: derive the
  keep-set from explicit needs (required/in_output/referenced/located_by_name); cover with a
  fabricated-schema test where a required:false, in_output:true measure survives in the right slot.
- Risk: 500-line cap on `schema_serialization.py` / `_schema_model_specs.py`. Mitigation: extract.

## Technical Specifications

- Files expected to change: `src/_schema_model_specs.py`, `src/schema_serialization.py`,
  `src/_schema_loader_helpers.py`, `src/schemas/default_aop.schema.json`,
  `src/schemas/default_le.schema.json`, plus tests.
- Public surface: new `ColumnSpec` field with a default (backward-compatible construction).
- Data flow: unchanged emitted output; load gating and ordering become flag-independent.

## Test Strategy

- AOP + LE parity tests pass unchanged (oracle).
- New `default_aop` `required_output_columns()` test (the seven dimensions; measures excluded).
- Migration test: a pre-field schema deserializes with `located_by_name` seeded correctly and
  round-trips stably.
- Fabricated-schema test: a `none`-dedup schema whose measures are `required: false, in_output: true`
  emits columns in the declared/expected order (order independent of `required`).
- Negative test: a `required` source column absent still raises; a `located_by_name` column absent
  loads without error.
- Toolchain: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` ->
  `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Coverage >= 85% line,
  >= 75% branch; no regression on changed lines.

## Definition of Done

- [x] `ColumnSpec` has a typed located-by-name signal, serialized and migration-seeded.
- [x] Loader which-columns-to-keep and `none`-dedup output ORDER are independent of `required`.
- [x] `default_aop` measures are `required: false` (`in_output: true`); dimensions `required: true`.
- [x] AOP and LE parity tests pass unchanged (zero output regression).
- [x] Fabricated-schema order-independence test and negative presence tests pass.
- [x] Toolchain clean; coverage maintained; all changed files <= 500 lines.
