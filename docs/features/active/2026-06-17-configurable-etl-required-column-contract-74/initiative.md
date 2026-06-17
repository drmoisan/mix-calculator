# configurable-etl-required-column-contract - Initiative Overview

- Issue: #74
- Owner: drmoisan
- Last Updated: 2026-06-17T11-53

## Goal & Outcomes

Make the LE import fully schema-driven and stop over-requiring columns. Redefine the
schema `required` flag to mean "required OUTPUT column" (one value column plus
dimensions); input columns — including derived-formula inputs — are never required.
Unassigned columns are dropped after the Columns stage. The Derived stage coerces
formula inputs and reports coercion failures attributable to the Derived tab. The
applicable schema for a sheet is auto-identified by its required-output column set
(one-to-many). The legacy `src/normalize_le.py` import is migrated to `SchemaLoader`
and removed.

Outcomes:
- `default_le` requires only value/dimension output columns, not months/FY/quarters.
- LE import in GUI and CLI runs through `SchemaLoader`; `normalize_le` no longer exists.
- As-built quirks preserved: Super Category and PPG both from source PPG; YTG = sum(May..Dec).

## Decomposition (Child Features/Workstreams)

- CF1 Schema-model required-output semantics + bundled schema update (Issue #74)
- CF2 Loader: enforce output-required set + drop unassigned post-derive (Issue #74)
- CF3 Formula engine: input coercion + Derived-stage coercion errors (Issue #74)
- CF4 Schema auto-identification by required-output set (one-to-many) (Issue #74)
- CF5 GUI schema-builder tabs: Derived coercion errors + Columns drop-unassigned (Issue #74)
- CF6 LE Excel read-boundary helper + migrate GUI & CLI import to SchemaLoader (Issue #74)
- CF7 Remove normalize_le + console script; rewrite parity tests as standalone (Issue #74)

Dependencies:
- CF1 → CF2, CF3, CF4 (all depend on the redefined `required` semantics).
- CF5 depends on CF2 and CF3 (GUI surfaces loader/derive behavior).
- CF6 depends on CF2 (loader is the migration target).
- CF7 depends on CF6 (callers must be migrated before removal).
- Safe sequential delivery order: CF1 → CF2 → CF3 → CF4 → CF5 → CF6 → CF7.
- Each child merges to main before the next begins (later children depend on earlier code).

## Cross-Cutting Constraints & Assumptions

- Schema `required` means required-output column everywhere (model, loader, matching, GUI).
- Schema format version bump 2.0 → 3.0; serialization/deserialization and persisted schemas updated.
- As-built quirks preserved exactly (Super Category/PPG copy; YTG = sum(May..Dec)).
- 500-line file-size cap applies to production and test files; extract rather than grow.
- Determinism, coverage (line >= 85%, branch >= 75%), and zero-regression gates apply to all children.
- Acceptance tests reproduce the real user path with bundled data, not alias-only fakes.

## Milestones & Status

- M1 Semantics + schemas (CF1) - Not started
- M2 Loader + formula + matching (CF2, CF3, CF4) - Not started
- M3 GUI tabs (CF5) - Not started
- M4 Migration + removal (CF6, CF7) - Not started

## Initiative-Level Validation

- End-to-end: schema-driven LE import (GUI and CLI) produces the same canonical output as the
  removed `normalize_le` path on the bundled default_le schema, with quirks preserved.
- Integration: auto-identification selects the correct schema by required-output set.
- Determinism/Regression: existing pipeline outputs remain stable; parity replaced by standalone tests.
- Error handling/Resilience: Derived-stage coercion failure produces a clear, tab-attributable error.

## Notes / Follow-Ups

- Approved decisions: redefine `required` (recommendation A); include F4 auto-identification (full epic).
- Research: artifacts/research/2026-06-16-etl-required-columns-redesign-research.md.
- CORRECTION (2026-06-17, verified): The premise that the monthly/quarter columns are "deleted
  before finalize" is incorrect. `src/mix_pipeline.py` persists the LE table and reads it back
  (line 188); `src/mix_q1.py` consumes `Jan`/`Feb`/`Mar`/`Q1` from that table. Dropping months/
  quarters from the LE OUTPUT would break the mix pipeline. Therefore the epic relaxes the INPUT
  requirement (`required` flags) but PRESERVES output membership (`in_output`) for `default_le`,
  so the LE output is unchanged (zero regression). The "drop unassigned after Columns stage"
  behavior remains a generic capability for arbitrary schemas; for `default_le` the months/
  quarters are assigned outputs and are retained.
