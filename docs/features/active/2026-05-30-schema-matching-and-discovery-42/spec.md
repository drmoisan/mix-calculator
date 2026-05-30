# schema-matching-and-discovery — Spec

- **Issue:** #42
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30
- **Status:** Ready for planning
- **Version:** 1.0

## Overview

Feature B delivers the **schema-matching engine** that, given the column headers
of a loaded sheet, scores each registered `SchemaDefinition` (Feature A) and
selects the best match — or, when no schema is a suitable match, produces a
structured, human-readable explanation of which required columns failed to match
and where (closest source-column candidates with similarity scores).

This feature is **additive and pure**: it adds matching/discovery logic and a
clean API that Features C (configurable loader / CLI explanation) and D (GUI
manual matching) consume. It does **not** modify the existing loaders, the
running CLI behavior, the transforms, or the GUI. It builds only on Feature A's
schema model and the existing `src/etl_columns.py` resolver.

- Success metric: for the bundled default schemas, `find_best_match` selects the
  correct schema for matching headers with a high score, and for non-matching
  headers returns a report naming the unmatched required columns and their
  closest candidates.

## Behavior

- A non-raising column probe reports, for a given set of actual headers against a
  schema's essential columns: which expected columns matched (and to which actual
  column), which required expected columns are unmatched, and which actual
  columns are unrecognized — without raising (unlike `resolve_columns`).
- `find_best_match(headers, schemas)` computes a coverage score per schema
  (fraction of required essential columns matched, with alias/pattern support)
  and returns the highest-scoring schema, its score, and a mismatch report. Ties
  break by newer schema `version`, then name.
- A registry-integrated entry point loads candidate schemas from the Feature A
  `SchemaRegistry` and applies `find_best_match`.
- The mismatch report is a typed structure: for each unmatched required column —
  its canonical name, its declared aliases, and up to N closest actual-column
  candidates with similarity scores (the best fuzzy ratios below threshold); and
  the list of unrecognized actual columns. The report renders to a concise,
  professional, human-readable string for CLI/GUI display.
- A configurable "suitable match" threshold determines match vs. explanation
  mode (per-column matching reuses the existing 0.85 resolver threshold; the
  schema-level acceptance policy default is documented in code, e.g. all required
  columns matched, or a documented coverage fraction).

## Inputs / Outputs

- Inputs: a list of actual column header strings; a set of candidate
  `SchemaDefinition` objects (directly, or loaded from the registry).
- Outputs: a typed `MatchResult` (best schema or none, score, mismatch report)
  and a rendered explanation string. No files written by this feature.
- Config keys/defaults: per-column fuzzy threshold (reuse the resolver default);
  schema-acceptance policy default documented in code.
- Backward compatibility: `resolve_columns` keeps its current raising behavior;
  `probe_columns` is added alongside it. Existing callers are untouched.

## API / CLI Surface

No new CLI command in this feature. Public Python surface (illustrative; the
planner finalizes names and home modules):

- `probe_columns(actual, expected, *, threshold=0.85) -> ProbeResult` in
  `src/etl_columns.py` (or a sibling module if the file nears 500 lines),
  returning matched mapping, unmatched expected, and unmatched actual without
  raising.
- `SchemaMatcher` / `find_best_match(headers, schemas, *, threshold=...) ->
  MatchResult` and a registry-integrated variant
  `find_best_match_in_registry(headers, registry, ...)`.
- `MismatchReport` (typed) with a `render() -> str` producing the human-readable
  explanation, and `MatchResult` carrying `schema`, `score`, `report`.

## Data & State

- No persistence. Pure transforms over header lists and schema objects.
- The matcher uses each `ColumnSpec.canonical_name` plus its `aliases` as the
  expanded set of acceptable names for that essential column, and reuses the
  existing normalized-name + `difflib` ratio logic for fuzzy scoring.
- Invariant: scores are deterministic for a given input (no wall-clock, no RNG);
  ties broken deterministically by schema version then name.

## Constraints & Risks

- Additive only. Do NOT modify `src/normalize_le.py`, `src/load_aop.py`,
  `src/_load_aop_helpers.py`, transforms, GUI, or CLI behavior. `resolve_columns`
  retains its raising contract.
- `src/etl_columns.py` is ~205 lines; `probe_columns` may be added there only if
  the file stays well under 500 lines, otherwise add a sibling module. Any new
  module stays < 500 lines.
- No new runtime dependency (stdlib `difflib` + Feature A model). No `asteval`.
- Pyright strict; T2 classification for new modules in `quality-tiers.yml`.
- Tests must not create temp files or touch network/real filesystem; registry
  integration is tested via the Feature A injectable file-store fake.
- Property-based tests (`hypothesis`) for scoring determinism are appropriate for T2.

## Implementation Strategy

- Add `probe_columns` (non-raising) alongside `resolve_columns`, sharing the
  existing normalized-name and fuzzy-ratio helpers.
- Add `src/schema_matching.py` — `MismatchReport`, `MatchResult`, `SchemaMatcher`
  / `find_best_match`, and the registry-integrated variant, plus the report
  renderer.
- Update `quality-tiers.yml` for new modules.
- No changes to existing loaders, transforms, GUI, or CLI.

## Definition of Done

- [x] `probe_columns` returns partial results without raising; `resolve_columns` behavior is unchanged.
- [x] `find_best_match` selects the highest-coverage schema and returns its score; ties break deterministically by version then name.
- [x] A registry-integrated entry point loads candidates from the Feature A registry and matches.
- [x] Non-matching headers yield a structured `MismatchReport` naming unmatched required columns, their aliases, and closest actual candidates with scores, plus unrecognized actual columns.
- [x] `MismatchReport.render()` produces a concise, professional, human-readable explanation.
- [x] New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; includes a `hypothesis` property test.
- [x] Existing test suite remains green; no existing loader/transform/CLI/GUI behavior changed.
- [x] `quality-tiers.yml` updated for new modules.
