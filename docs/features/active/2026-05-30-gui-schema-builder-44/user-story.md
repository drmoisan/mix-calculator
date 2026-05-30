# `gui-schema-builder` — User Story

- Issue: #44
- Parent: Epic #40
- Owner: drmoisan
- Status: Ready for planning
- Last Updated: 2026-05-30

## Story Statement

- As an analyst, I want a visual, point-and-click schema builder, so that I can
  onboard an input file in a slightly different format without writing code.
- As an analyst whose file does not match any known schema, I want a clear
  explanation and a point-and-click way to map columns or build a new schema, so
  that I can still process the file.
- As an analyst, I want to enter a formula for a calculated column the source
  lacks and have it validated immediately, so that I trust the derived values.

## Problem / Why

Features A–C provide the model, matching, and configurable loader, but only
through code. Feature D makes the subsystem usable: schema discovery in the
import flow, a manual column-matching dialog when fuzzy matching fails, a visual
schema builder, and runtime formula entry — wired into the existing MVP GUI
without regressing known-file behavior.

## Personas & Scenarios

- Persona: analyst loading a drifted LE export.
  - Cares about: getting correct output without code; understanding non-matches;
    safe formula entry.
  - Constraints: point-and-click only; known files must behave exactly as today.
- Scenario: the analyst loads a renamed-column LE file. Discovery reports the LE
  schema as the closest match but below threshold, listing the two unmatched
  required columns and closest candidates. The analyst opens the manual matcher,
  assigns the two columns from fuzzy suggestions, optionally saves them as
  aliases, and imports; for a missing calculated column the analyst opens the
  builder, enters a formula, sees it validated, saves the schema, and re-imports
  successfully.

## Acceptance Criteria

- [x] AC1: On import, the system finds the best-matching schema via the Feature B engine over the Feature A registry; a suitable match drives import via the Feature C `SchemaLoader`, with identical results for known AOP/LE files.
- [x] AC2: When no schema is a suitable match, the GUI shows the Feature B mismatch explanation and offers to open the manual column-matching dialog or the schema builder.
- [x] AC3: The manual column-matching dialog lets the user assign unmatched required columns to source columns point-and-click, shows fuzzy suggestions with similarity scores, supports ignoring optional columns, and can persist accepted assignments as schema alias additions via the registry.
- [x] AC4: The schema builder dialog creates/edits and persists a schema point-and-click across identity, columns (role/aliases/required), key, dedup policy (additive vs select-from per measure), derived/formula columns, and a preview tab.
- [x] AC5: Runtime formula entry validates via the Feature C `FormulaEvaluator`; invalid/unsafe/unknown-column expressions are rejected inline with the descriptive `FormulaError` message; valid expressions are accepted.
- [x] AC6: A "Schema Builder..." menu/action opens the builder outside the import flow.
- [x] AC7: The `SchemaBuilderPresenter` and `ColumnMatchingPresenter` are unit-tested without a `QApplication`; the dialogs and import-flow wiring are tested via `pytest-qt`.
- [x] AC8: New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage on presenters/service; `quality-tiers.yml` classifies new modules.
- [x] AC9: The existing test suite remains green; existing import for known files yields identical results; no existing CLI, transform, or loader module behavior is modified.

## Non-Goals

- No change to the analytical transforms or the CLI pipeline.
- No new persistence format beyond the Feature A registry.
- No automatic schema inference beyond the Feature B fuzzy matching (the builder is manual/point-and-click).
