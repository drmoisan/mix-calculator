# etl-required-output-model-semantics - Refactor Spec

- **Issue:** #74 (epic child CF1)
- **Parent:** docs/features/active/2026-06-17-configurable-etl-required-column-contract-74/
- **Owner:** drmoisan
- **Last Updated:** 2026-06-17
- **Status:** Draft
- **Version:** 0.1

## Intent & Outcomes

Redefine the schema column `required` flag to mean "required OUTPUT column" — the
output-identity set for a pipeline: one value column plus its dimension columns. Input
columns, including columns consumed by derived-formula expressions, are no longer
required merely to be read. This is the foundational semantic change (approved
recommendation A) on which the rest of epic #74 builds.

Outcome: the bundled `default_le` schema requires only its output-identity columns, not
the 12 months / `FY` / `Q1`–`Q4`. Those measure columns remain emitted (`in_output: true`)
because the downstream mix pipeline (`src/mix_q1.py` via the persisted `LE` table) consumes
them, so the LE OUTPUT is unchanged (zero regression). Only the input-presence requirement
is relaxed.

- Success metric: `SchemaLoader` happy-path output for `default_le` is byte-identical to
  the pre-change output; a source sheet missing only month/quarter/FY columns no longer
  fails resolution at load time.

## Invariants (must not change)

- `SchemaLoader` output columns and values for `default_le` and `default_aop` on the bundled
  fixtures are unchanged (same `in_output` set, same order, same values).
- As-built LE quirks preserved: derived `YTG = sum(May..Dec)`; `Super Category` derived via
  `copy_from: PPG`; both `Super Category` and `PPG` populated from source `PPG`.
- KEY composition, dedup policy, and fill rules unchanged.
- No change to the loader pipeline shape, the GUI, matching, or `normalize_le` in this child
  (those are CF2–CF7).

## Scope (structural changes)

- `src/schema_model.py`: bump `SCHEMA_FORMAT_VERSION` from `"2.0"` to `"3.0"`. Update the
  module and `ColumnSpec` docstrings so `required` is documented as "required OUTPUT column"
  and `in_output` is documented as "emitted in output (may be true without `required`)".
- `src/_schema_model_specs.py`: update `ColumnSpec.required` docstring to the new meaning.
  Add a read-only helper on `SchemaDefinition` (e.g. `required_output_columns()`) returning
  the ordered required-output canonical names (source columns with `required=True` plus any
  derived column the schema designates as a required output). The exact representation of a
  required derived value column is a planner decision; keep it minimal and typed.
- `src/schema_serialization.py`: add a deterministic forward migration `2.0 → 3.0`. Document
  the mapping. For a pre-3.0 schema the migration must not change emitted output; a safe
  default mapping is: `required(3.0) = required(2.0) AND in_output(2.0)` (a column that was a
  source-presence requirement but is not emitted is no longer a required-output column).
  Round-trip (deserialize → serialize) of a 3.0 schema is stable.
- `src/schemas/default_le.schema.json`: bump `version` to `3.0`; set `required: false` on
  `Jan`–`Dec`, `FY`, `Q1`–`Q4`; keep their `in_output: true`. Keep `required: true` on the
  output-identity columns (`Customer`, `SKU Descripiton`, `SKU #`, `Type`, `GtN Mapping`,
  `PPG`). Quirks and derived columns unchanged.
- `src/schemas/default_aop.schema.json`: NO change in CF1. The forward migration upgrades it to
  3.0 in memory on load (functionally identical: every AOP measure is `in_output: true`, so
  `required = required AND in_output` keeps it `required: true`). AOP required-flag minimization
  is DEFERRED to CF2 — see the descope note below.

### Descope note (AOP -> CF2)

CF1 originally intended to align `default_aop` required flags too. Verification during remediation
(see `evidence/regression-testing/r1-output-order-regression.2026-06-17T12-35.md` and
`r1-scope-insufficiency-finding.2026-06-17T13-10.md`) established that flipping AOP measures to
`required: false` reorders the SchemaLoader output for the `none`-dedup (AOP) path, because the
loader (`src/_schema_loader_helpers.py`) couples emitted column ORDER and the located-by-name /
which-columns-to-keep decision to the `required` flag. Decoupling that requires a new schema-model
"located-by-name / presence-optional" signal plus a loader change to which columns are kept and
their order — which is CF2 (loader) scope, not CF1 (model semantics). AOP minimization therefore
moves to CF2. CF1 ships the redefined `required` semantics applied to `default_le` (whose
`aggregate`-dedup emit rebuilds canonical order independently of the `required` flag, so it has no
ordering coupling).

## Non-Goals

- No loader enforcement changes, no "drop unassigned" behavior change (CF2).
- No `default_aop` required-flag change (deferred to CF2 with the loader decouple).
- No formula coercion (CF3), no auto-identification (CF4), no GUI changes (CF5).
- No `normalize_le` migration or removal (CF6/CF7).
- No change to which columns are emitted for the bundled schemas.

## Dependencies / Touchpoints

- `src/schema_loader.py` / `src/_schema_loader_helpers.py` read `required` at resolve time
  (raise-if-absent). Relaxing month/quarter `required` to false changes only the absent-column
  behavior; present columns still resolve. Verify loader tests still pass.
- `src/schema_matching.py` `_required_columns` reads `required`; its denominator changes.
  Confirm matching tests still pass (deeper matching redesign is CF4).
- Persisted user schemas at the schema settings path are upgraded by the migration on load.

## Risks & Mitigations

- Risk: matching coverage tests assume months are required. Mitigation: update those tests to
  the new required set; document that full matching redesign is CF4.
- Risk: migration changes output for some persisted schema. Mitigation: the mapping preserves
  `in_output`; only `required` is recomputed. Add a round-trip + migration test.
- Risk: 500-line cap. `_schema_model_specs.py` is ~480 lines. Mitigation: keep additions
  minimal; extract a helper module if needed rather than growing past the cap.

## Technical Specifications

- Files expected to change: `src/schema_model.py`, `src/_schema_model_specs.py`,
  `src/schema_serialization.py`, `src/schemas/default_le.schema.json`, plus their tests.
  (`src/schemas/default_aop.schema.json` is NOT changed in CF1; AOP -> CF2.)
- Public surface: `SCHEMA_FORMAT_VERSION` value; new `required_output_columns()` accessor;
  serialization migration behavior. No change to existing constructor signatures.
- Data flow: unchanged at runtime for bundled schemas; only input-presence gating relaxes.

## Test Strategy

- Update `tests/test_default_schemas.py` and any schema-model/serialization tests for the new
  `required` semantics and version `3.0`.
- Add a migration test: a 2.0 JSON deserializes, upgrades to 3.0 with the documented mapping,
  and re-serializes stably.
- Add/keep a loader parity check that `default_le` output is unchanged after the schema edit.
- Add a negative test: a source missing only month/quarter columns now loads without a
  required-column ValueError (months no longer required), while a source missing `Customer`
  (a required-output dimension) still raises.
- Toolchain: `poetry run black .` → `poetry run ruff check .` → `poetry run pyright` →
  `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Coverage >= 85% line,
  >= 75% branch; no regression on changed lines.

## Definition of Done

- [x] `SCHEMA_FORMAT_VERSION == "3.0"`; docstrings define `required` = required-output column.
- [x] Deterministic `2.0 → 3.0` migration with documented, output-preserving mapping + test.
- [x] `default_le` updated to 3.0; months/FY/quarters (and the loader-produced `Super Category`)
      `required: false`, `in_output` unchanged; quirks preserved. (`default_aop` minimization
      descoped to CF2 — see Descope note; CF1 makes no AOP schema-file change.)
- [x] `required_output_columns()` accessor returns the ordered required-output set.
- [x] Bundled-schema loader output unchanged (zero regression); negative/positive load tests pass.
- [x] Toolchain clean (format → lint → type-check → test); coverage maintained.
