# configurable-etl-core — Spec

- **Issue:** #43
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30
- **Status:** Ready for planning
- **Version:** 1.0

## Overview

Feature C implements the **configurable ETL core**: a `SchemaLoader` that takes a
`SchemaDefinition` (Feature A) and a raw sheet DataFrame and produces the
canonical normalized output, driven entirely by the schema — resolve columns,
establish the business key, fill blank totals, deduplicate complementary rows
(additive sum or select-from-discriminator per measure), compute derived columns
via a sandboxed **runtime formula engine** (the approved `asteval` dependency),
and emit the declared output columns. It also provides the **column builder**
(derived columns constructed from other columns) and **ratio recompute**
(non-additive measures dropped before aggregation and recomputed afterward from
the summed dollar/volume columns using safe-division), per the
`Rate_Impacts_corrected.m` pattern.

This feature is **additive**: it adds new modules only. It does NOT modify
`src/normalize_le.py`, `src/load_aop.py`, `src/_load_aop_helpers.py`, the
transforms, the GUI, or the CLI. The configurable loader is a parallel path. All
GUI/CLI wiring is deferred to Feature D.

The defining correctness requirement: `SchemaLoader` driven by the bundled
`default_le` schema must reproduce `normalize_le.normalize` output exactly on the
same fixtures, and driven by `default_aop` must reproduce `load_aop`'s validated
frame exactly (same columns, order, values, and the `Super Category <- PPG`
quirk).

## Behavior

End-to-end `SchemaLoader.load(raw_frame, schema)`:

1. Resolve source columns to canonical names using the schema's column
   aliases (reuse `resolve_columns` / the Feature B probe); rename to canonical.
2. Drop blank-key/blank-Customer padding rows, matching current loader behavior.
3. Establish the business key from `KeySpec` (reuse `src/etl_key.resolve_key` /
   `rebuild_key` / `coerce_sku`) — identical key semantics to today.
4. Apply `fill_rules` (reuse `src/etl_totals.fill_blank_totals`).
5. Coerce numeric measures and clean label sentinels (reuse the existing neutral
   helpers) so behavior matches the current loaders.
6. Deduplicate per `DedupPolicy`:
   - `mode == none`: no row collapse (AOP).
   - `mode == collapse`: group by key; dimensions taken from the first row;
     each measure aggregated by its declared policy — `additive` (sum) or
     `select_from` a discriminator value; non-additive/ratio measures are NOT
     summed (dropped pre-aggregation, recomputed in step 7).
7. Compute derived columns (`DerivedColumnSpec`): `copy_from` (the PPG quirk) and
   `expression` formulas evaluated by the formula engine AFTER aggregation,
   including ratio recompute from summed dollars/volume with safe-division
   (denominator null or `<= 0` yields 0).
8. Drop `drop_columns` and emit exactly the declared canonical output columns in
   order.

Formula engine (`schema_formula`):
- Wraps an `asteval` `Interpreter` behind a fully-typed adapter. The evaluation
  symtable contains only the row/column values plus a whitelisted function set
  (at minimum `safe_div(num, den)` returning 0 when `den` is null or `<= 0`, and
  `sum`); no imports, no attribute access to dunders, no file/OS access (asteval
  restricts these; the adapter further constrains the symtable).
- Supports column names that are not valid Python identifiers (e.g. `SKU #`,
  `Off Invoice $`) via a `col("exact name")` accessor and/or a deterministic
  identifier-aliasing map exposed in the symtable.
- Validates an expression on entry: a syntactically invalid or
  disallowed-construct expression raises a descriptive `FormulaError`; an
  expression referencing an unknown column raises a descriptive error naming the
  column. Evaluation is vectorized over the frame where practical, or applied
  row-wise deterministically.

## Inputs / Outputs

- Inputs: a raw sheet DataFrame; a `SchemaDefinition`.
- Outputs: a normalized DataFrame with the schema's declared canonical columns.
  No file or DB writes in this feature (persistence stays with existing sinks /
  Feature D wiring).
- Config keys/defaults: per-column fuzzy threshold reused from the resolver.
- Dependency change: `asteval` (^1.0.8) added to `pyproject.toml` (user-approved
  2026-05-30) with a local type stub `typings/asteval/__init__.pyi` for the
  narrow `Interpreter` surface used, so Pyright strict passes with no suppression.

## API / CLI Surface

No new CLI in this feature. Public Python surface (planner finalizes names):

- `src/schema_formula.py`: `FormulaError`; a typed `FormulaEvaluator` (or
  functions) with `evaluate(expression, frame/row-context) -> Series/scalar` and
  an expression-validation entry point; the whitelisted `safe_div` and `col`
  helpers.
- `src/schema_loader.py`: `SchemaLoader` with `load(raw, schema) -> DataFrame`
  (plus private phase helpers split into a `_schema_loader_helpers.py` if needed
  for the 500-line cap).

## Data & State

- Pure transforms over DataFrames; reuse the existing neutral ETL leaf modules
  (`etl_key`, `etl_totals`, the AOP coerce/sentinel helpers) to guarantee parity
  rather than reimplementing.
- Determinism: no wall-clock, no RNG; group/first-row order preserved
  (first-appearance), matching `normalize_le.normalize`.
- The formula engine must be deterministic and side-effect free.

## Constraints & Risks

- Additive only; protected files unchanged; existing suite stays green.
- `asteval` is the only new dependency (approved). It lacks `py.typed`; do NOT
  add `# type: ignore` — instead ship the local stub under `typings/` so Pyright
  strict passes cleanly. If a suppression appears unavoidable, STOP and escalate.
- Formula-engine security is the top risk: even with asteval's restrictions, the
  adapter must constrain the symtable and reject disallowed constructs; include
  fuzz/property tests for rejection of unsafe input and for safe-division edge
  cases (zero/negative/null/NaN denominators).
- Exact-reproduction risk: column order, the PPG quirk, key resolution, blank-row
  drop, fill rules, sentinel cleaning, and numeric coercion must match the
  current loaders byte-for-equivalent on the existing fixtures.
- Every new file < 500 lines; split helpers as needed.
- T1 classification is appropriate for the formula engine and loader core (a bug
  causes silent data corruption); classify in `quality-tiers.yml`. T1 implies a
  property test per pure function and a mutation-score target (trend/nightly).

## Implementation Strategy

- Add `typings/asteval/__init__.pyi` (minimal typed `Interpreter` surface).
- Add `src/schema_formula.py` — typed asteval adapter, `safe_div`, `col`,
  validation, `FormulaError`.
- Add `src/schema_loader.py` (+ `_schema_loader_helpers.py` if needed) — the
  schema-driven loader reusing `etl_key`, `etl_totals`, and existing coerce/
  sentinel helpers.
- Add parity tests proving `SchemaLoader(default_le)` == `normalize_le.normalize`
  and `SchemaLoader(default_aop)` == `load_aop` validated frame on the existing
  fixtures; plus an integration test feeding the loader output through the
  existing pipeline transforms to a consistent result.
- Update `pyproject.toml`/`poetry.lock` (asteval) and `quality-tiers.yml`.
- No GUI/CLI/transform/loader changes.

## Definition of Done

- [x] `SchemaLoader(default_le)` reproduces `normalize_le.normalize` output exactly on the existing LE fixtures (columns, order, values, PPG quirk, derived YTG, dropped YTD/YTG).
- [x] `SchemaLoader(default_aop)` reproduces `load_aop`'s validated frame exactly on the existing AOP fixtures.
- [x] Dedup honors `additive` vs `select_from` per measure; `mode == none` preserves rows.
- [x] The column builder constructs a missing column from others via a derived-column expression.
- [x] Ratio/per-unit/%GS-style measures recompute post-aggregation from summed dollars/volume with safe-division edge cases handled (zero/negative/null/NaN denominator yields 0).
- [x] The formula engine evaluates valid expressions (including columns with spaces/special chars) and rejects unsafe/invalid expressions with descriptive `FormulaError`s; fuzz/property tests included.
- [x] `asteval` added to `pyproject.toml`; a local `typings/asteval/__init__.pyi` stub makes Pyright strict pass with no suppression.
- [x] An integration test feeds `SchemaLoader` output through the existing pipeline transforms to a consistent result.
- [x] New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; T1/T2 classified in `quality-tiers.yml` with property tests per pure function for T1 modules.
- [x] Existing test suite remains green; no existing loader/transform/CLI/GUI behavior changed.
