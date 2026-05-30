# schema-model-and-registry — Spec

- **Issue:** #41
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30
- **Status:** Ready for planning
- **Version:** 1.0

## Overview

Feature A is the foundation of the configurable-schema epic. It introduces a
persisted, typed **schema definition model**, a **shared schema registry** (a
common directory independent of any single `.db`, resolved via a settings/path
mechanism), and **bundled default AOP and LE schemas** that structurally encode
the behavior currently hardcoded in `src/_load_aop_helpers.py` and
`src/normalize_le.py`.

This feature is **additive only**: it must not modify the existing loaders,
transforms, GUI, or CLI behavior. No file currently loaded by the pipeline is
changed. Evaluation of schemas (matching, dedup, formulas) is delivered by later
features (B and C); Feature A only defines, serializes, persists, and validates
the model's expressiveness.

- Target users: developers and (later) the GUI schema builder, which consume the
  model; end users benefit indirectly once B–D ship.
- Success metric: the two bundled default schemas parse into `SchemaDefinition`
  objects whose declared columns, key, dedup policy, and derived-column
  definitions match the canonical sets the current AOP/LE loaders use.

## Behavior

- The model can represent every aspect of the current AOP and LE schemas:
  the canonical column set and order, each column's role and match aliases, the
  business-key composition, the dedup policy (LE = collapse-by-key with additive
  measures and first-row dimensions; AOP = no collapse), the derived columns
  (LE `YTG = sum(May..Dec)`), the blank-total fill rules, the drop columns
  (LE `YTD/YTG`), the sentinel-clean label columns, and the LE as-built quirk
  (`Super Category` and `PPG` both sourced from `PPG`).
- A `SchemaRegistry` resolves a shared registry directory, then lists, loads, and
  saves schema definitions as JSON files in that directory.
- Round-trip: `SchemaDefinition` → JSON string → `SchemaDefinition` is lossless.
- Error handling: malformed JSON or a JSON object missing required fields raises
  a specific, descriptive error (not a bare `KeyError`/`ValueError` without
  context). Unknown/extra JSON keys are rejected with a message naming them.

## Inputs / Outputs

- Inputs: schema JSON files in the registry directory; an optional environment
  variable (e.g. `MIX_CALCULATOR_SCHEMA_DIR`) overriding the default directory.
- Outputs: persisted `*.schema.json` files; the two bundled default schemas
  shipped in the package (e.g. `src/schemas/default_aop.schema.json`,
  `src/schemas/default_le.schema.json`).
- Config keys/defaults: registry directory defaults to a per-user application
  data location (Windows: under `%APPDATA%`; otherwise an XDG-style path),
  overridable by the environment variable. Path-resolution logic must be pure
  and unit-testable by injecting the environment lookup and platform marker
  (no real filesystem access in unit tests).
- Backward compatibility: existing CLI loaders and the current test suite must
  remain unchanged and green. No schema is consumed by the pipeline yet.

## API / CLI Surface

No new CLI commands in this feature. Public Python surface (illustrative; the
planner finalizes names):

- `SchemaDefinition` and nested frozen dataclasses (`ColumnSpec`, `DedupPolicy`,
  `MeasureAggregation`, `DerivedColumnSpec`, `KeySpec`, `FillRule`).
- `schema_to_json(schema) -> str` / `schema_from_json(text) -> SchemaDefinition`
  (typed adapter; no untyped `dict` leaks into callers).
- `SchemaRegistry` with `resolve_registry_dir(...) -> Path`, `list_schemas()`,
  `load(name)`, `save(schema)`, and `load_bundled_default(name)`.

## Data & State

- Schema JSON shape (self-contained object): identity (`name`, `version`,
  `description`), `source_sheet_hints`, `header_row`, `columns[]` (each with
  `canonical_name`, `role` ∈ {dimension, measure, discriminator, drop},
  `required`, `aliases[]`, `numeric`, `sentinel_clean`), `key` (ordered
  `columns[]` plus a `sku_coercion` flag mirroring `coerce_sku`), `dedup`
  (`mode` ∈ {none, collapse}, `discriminator_column`, per-measure aggregation
  = additive or `select_from` a discriminator value, default additive),
  `derived_columns[]` (`name`, `expression` string, optional `copy_from` for the
  PPG quirk), `fill_rules[]` (total → component columns), `drop_columns[]`.
- The `expression` string is stored verbatim in Feature A; it is **not evaluated
  here** (evaluation is Feature C). Validation in Feature A is structural only.
- Invariants enforced in `__post_init__`: non-empty `name`; `version` present;
  every `key.columns` entry and every `dedup`/`fill_rule`/`derived` reference
  names a declared column; `discriminator_column` is declared when `mode` is
  collapse.
- Persistence: JSON files in the registry directory. A schema `version` field
  exists from day one to support later format migration.

## Constraints & Risks

- New modules only. Do not grow `src/normalize_le.py` (at the 500-line ceiling).
  Keep every new file < 500 lines; split helpers if needed.
- Pyright strict: the JSON boundary must be type-safe; wrap
  `json.loads`/`dataclasses.asdict` in a typed adapter (pattern like
  `src/pandas_io.py`). No untyped `dict[str, Any]` in public signatures.
- Tests must not create temp files or touch the network/real filesystem. Test
  serialization via pure string round-trips; test directory resolution via
  injected environment/platform seams; test file I/O via an injected
  reader/writer abstraction (e.g. callables or a small Protocol), not real disk.
- No new runtime dependency for this feature (stdlib `json`, `dataclasses`,
  `pathlib`). `asteval` is introduced later in Feature C.
- T2 (Core) classification for the new schema modules; add entries to
  `quality-tiers.yml`. Property-based tests (`hypothesis`) for the JSON
  round-trip are appropriate for T2.

## Implementation Strategy

- Add `src/schema_model.py` — the frozen dataclasses + `__post_init__` invariants.
- Add `src/schema_serialization.py` (or a typed adapter section) — the typed
  JSON round-trip, raising descriptive errors on malformed/incomplete input.
- Add `src/schema_settings.py` — pure registry-directory resolution with injected
  environment and platform seams.
- Add `src/schema_registry.py` — list/load/save plus bundled-default loading,
  with file I/O behind an injectable boundary.
- Add `src/schemas/default_aop.schema.json` and `src/schemas/default_le.schema.json`.
- Update `quality-tiers.yml` for the new modules.
- No changes to existing loaders, transforms, GUI, or CLI.

## Definition of Done

- [ ] `SchemaDefinition` model expresses every aspect of the current AOP and LE hardcoded schemas (verified by tests asserting canonical columns, key, dedup, derived defs).
- [ ] JSON save/load/list round-trip is lossless and Pyright-strict clean.
- [ ] Malformed/incomplete schema JSON raises descriptive errors (tested).
- [ ] Shared registry directory resolves via a settings/path mechanism with an env override, independent of the `.db` path; resolution is unit-tested without disk.
- [ ] Bundled `default_aop` and `default_le` schemas are present and validated structurally against the current canonical column sets.
- [ ] New modules are formatted (Black), lint-clean (Ruff), Pyright-strict clean; >= 85% line / >= 75% branch coverage on changed code.
- [ ] Existing test suite remains green; no existing loader/CLI/GUI behavior changed.
- [ ] `quality-tiers.yml` updated for new modules.
