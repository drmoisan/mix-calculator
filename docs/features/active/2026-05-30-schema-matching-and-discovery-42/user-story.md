# `schema-matching-and-discovery` — User Story

- Issue: #42
- Parent: Epic #40
- Owner: drmoisan
- Status: Ready for planning
- Last Updated: 2026-05-30

## Story Statement

- As a user loading a new input file, I want the system to automatically find the
  schema that best matches my file's columns, so that I do not have to choose a
  schema manually for known formats.
- As a user whose file does not match any schema, I want a clear explanation of
  which required columns could not be matched and the closest candidates in my
  file, so that I understand what to fix or how to build a new schema.

## Problem / Why

Today column resolution is hardcoded per loader and raises on the first
unmatched column with no overall picture. There is no way to compare a file
against multiple candidate schemas, score them, or explain a non-match. Feature B
adds that engine on top of Feature A's model, as pure logic the later features
consume.

## Personas & Scenarios

- Persona: analyst loading AOP/LE or a drifted variant.
  - Cares about: correct automatic schema selection; a precise explanation when
    nothing matches.
  - Constraints: no code changes for format drift; deterministic results.
- Scenario: the analyst loads a sheet whose headers mostly match the LE default
  but rename two columns. `find_best_match` selects the LE schema with a score
  below the acceptance threshold and returns a report: the two unmatched required
  columns, their known aliases, and the closest actual headers with similarity
  scores — enough to proceed to manual matching or a new schema later.

## Acceptance Criteria

- [x] AC1: `probe_columns` returns matched mapping, unmatched expected, and unmatched actual without raising; `resolve_columns` retains its raising contract unchanged.
- [x] AC2: `find_best_match` scores each candidate schema by required-column coverage (with alias support) and returns the highest-scoring schema and its score.
- [x] AC3: Ties break deterministically by newer schema version, then name; results are deterministic for a given input.
- [x] AC4: A registry-integrated entry point loads candidate schemas from the Feature A `SchemaRegistry` and applies matching.
- [x] AC5: Non-matching headers produce a typed `MismatchReport` naming each unmatched required column, its aliases, and up to N closest actual candidates with similarity scores, plus the unrecognized actual columns.
- [x] AC6: `MismatchReport.render()` returns a concise, professional, human-readable explanation string.
- [x] AC7: New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; a `hypothesis` property test covers scoring determinism.
- [x] AC8: The existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified; `quality-tiers.yml` classifies the new modules.

## Non-Goals

- No configurable ETL / dedup / column building / formula evaluation (Feature C).
- No GUI manual-matching dialog (Feature D).
- No change to existing CLI loaders or the running pipeline; `resolve_columns` is not altered.
