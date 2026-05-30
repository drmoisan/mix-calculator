# `schema-model-and-registry` — User Story

- Issue: #41
- Parent: Epic #40
- Owner: drmoisan
- Status: Ready for planning
- Last Updated: 2026-05-30

## Story Statement

- As a developer building the configurable-schema subsystem, I want a typed,
  persisted schema definition model and a shared registry, so that later
  features (matching, configurable ETL, and the GUI builder) have a stable,
  serializable contract to read and write.
- As a maintainer, I want the current AOP and LE schemas expressed as bundled
  default schema files, so that backward compatibility can be proven and the
  model's expressiveness is validated before any code depends on it.

## Problem / Why

The AOP and LE schemas are hardcoded constant lists. There is no data structure
to represent a schema, no place to persist one, and no way to express dedup,
derived columns, or match aliases as data. Feature A creates that foundation
without changing any current behavior.

## Personas & Scenarios

- Persona: subsystem developer.
  - Cares about: a strongly-typed, Pyright-clean model; a lossless JSON
    round-trip; an injectable, testable persistence boundary.
  - Constraints: no new runtime dependency; no temp files in tests; 500-line
    file ceiling; strict typing.
  - Goal: a model rich enough to express both AOP (no collapse) and LE
    (collapse-by-key, additive measures, derived YTG, PPG quirk).
- Scenario: the developer serializes the bundled LE default schema, reloads it,
  and asserts the round-tripped object declares the LE canonical columns, the
  `Customer + SKU # + Type` key, the collapse dedup with additive measures, the
  derived `YTG`, the dropped `YTD/YTG`, and the `Super Category <- PPG` quirk.

## Acceptance Criteria

- [x] AC1: A `SchemaDefinition` (and nested frozen dataclasses) can represent column roles/aliases, key composition, dedup policy, derived columns, fill rules, drop columns, and sentinel-clean columns.
- [x] AC2: `SchemaDefinition` → JSON → `SchemaDefinition` round-trips losslessly and is Pyright-strict clean.
- [x] AC3: Malformed JSON, missing required fields, or unknown keys raise descriptive, specific errors.
- [x] AC4: `__post_init__` invariants reject schemas whose key/dedup/derived/fill references do not name declared columns, and require a discriminator column when dedup mode is collapse.
- [x] AC5: The shared registry directory resolves via a settings/path mechanism with an environment-variable override, independent of any `.db` path, and the resolution logic is unit-tested without touching disk.
- [x] AC6: `SchemaRegistry` can list, load, and save schemas through an injectable file-I/O boundary (tested without real files).
- [x] AC7: Bundled `default_aop.schema.json` and `default_le.schema.json` exist and structurally match the current canonical AOP/LE column sets, key, dedup, and derived definitions.
- [x] AC8: The existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified.
- [x] AC9: New modules pass Black, Ruff, and Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; `quality-tiers.yml` classifies the new modules.

## Non-Goals

- No schema matching / discovery (Feature B).
- No configurable ETL, dedup execution, column building, or formula evaluation (Feature C).
- No GUI (Feature D).
- No change to existing CLI loaders or the running pipeline.
