# configurable-etl-required-column-contract (Issue #74)

- Date captured: 2026-06-17
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/configurable-etl-required-column-contract/ (Issue #74)

- Issue: #74
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/74
- Last Updated: 2026-06-17
- Work Mode: full-feature

## Problem / Why

The LE (Latest Estimate) import is overengineered. The schema-driven import currently
marks all 12 monthly columns plus `FY` and `Q1`–`Q4` as `required`, even though those
columns are only intermediate inputs to a derived value and validation; they are not the
real deliverable. The legacy `src/normalize_le.py` loader is still the live LE import path
in the GUI (`src/gui/pipeline_service.py`) and CLI (`src/mix_pipeline.py`), bypassing the
configurable `SchemaLoader`.

The required-column concept conflates source-presence with output membership. The user's
model is: each ETL pipeline has exactly ONE set of required columns — the final output set
(one value column plus dimensions). A required output value column may be a pre-existing
source column or a derived column. Input columns, including the columns a derived formula
consumes, are never required. Multiple schemas may produce the same required-output set
(one-to-many), and the applicable schema for a given sheet should be auto-identified from
that required-output set.

## Proposed Behavior

Redefine the `required` flag on a schema column to mean "required OUTPUT column" (approved
recommendation A; schema format version bump 2.0 → 3.0). Drive the LE import entirely from
the configurable `SchemaLoader`:

- Only the final output required-set is required; derived-formula inputs are never required.
- After the Columns (assignment) stage, all unassigned columns are dropped (`in_output=false`).
- The Derived stage coerces formula inputs to the needed dtype and raises a coercion error
  attributable to the Derived tab when coercion fails.
- Auto-identify the applicable schema for a sheet by its required-output column set
  (one-to-many: one required set maps to many schemas).
- Migrate the GUI and `mix_pipeline` LE import to `SchemaLoader` via a new LE Excel
  read-boundary helper (mirroring the AOP import helper), then remove `normalize_le.py`,
  `_normalize_le_columns.py`, and the `normalize-le` console script. Rewrite the parity
  tests as standalone correctness tests.

## Acceptance Criteria (early draft)

- [ ] `required` means required-output column across schema model, loader, matching, and GUI.
- [ ] `default_le` requires only the value/dimension output columns (not months/FY/quarters).
- [ ] Derived-formula input columns are not required; unassigned columns are dropped post-derive.
- [ ] Derived-stage type coercion failures surface as errors attributable to the Derived tab.
- [ ] Schema auto-identification matches by required-output set with one-to-many support.
- [ ] LE import in GUI and CLI runs through `SchemaLoader`; `normalize_le` is removed.
- [ ] As-built quirks preserved (Super Category and PPG both from source PPG; YTG = sum(May..Dec)).

## Constraints & Risks

- 500-line file-size cap; several schema files are 450–500 lines and `normalize_le.py` is near it.
- Parity tests reference the loader being removed; they must be rewritten as standalone tests.
- GUI activation-seam guards: integration tests must drive the real no-file/no-sheet paths.
- Acceptance tests must reproduce the real user path with bundled data, not alias-only fakes.
- Schema format version bump affects serialization/deserialization and persisted schemas.

## Test Conditions to Consider

- [ ] Unit coverage for redefined `required` in model, loader, matching, formula engine.
- [ ] Integration: schema-driven LE import end-to-end (GUI and CLI) with bundled default_le.
- [ ] Auto-identification: multiple schemas producing one required-output set.
- [ ] Derived-stage coercion-failure error path.
- [ ] Removal: no remaining references to normalize_le; rewritten parity/correctness tests pass.

## Next Step

- [ ] Promote to GitHub issue (epic) and create the active epic folder with child features.