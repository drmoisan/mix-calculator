# aop-import-schema-driven (Issue #58)

- Date captured: 2026-06-08
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/aop-import-schema-driven/ (Issue #58)

- Issue: #58
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/58
- Last Updated: 2026-06-08
- Work Mode: full-feature

## Problem / Why

The GUI AOP import routes through the legacy `src.load_aop.load_aop`, whose
`validate_aop` (in `src/_load_aop_helpers.py`) enforces per-row arithmetic
identities between value columns: `YTD == sum(months)`, `YTG == sum(May..Dec)`,
and `Q1..Q4 == sum(constituent months)`. These identities are not stable across
real source workbooks. Two of the user's real workbooks encode `YTD`
differently (one partial-year `sum(Jan..Apr)`, one full-year `sum(Jan..Dec)`),
both with a `YTG` column. The hardcoded validation rejects the full-year
workbook with `AOP validation failed: YTD != sum(months)`, blocking import.

The root issue is architectural: the legacy AOP loader hardcodes a fixed
value-column layout (Jan..Dec + YTD + Q1..Q4 + YTG) and validates relationships
between those columns. The repository already contains a configurable,
schema-driven load path (`src.schema_loader.SchemaLoader` driven by
`SchemaDefinition`/`ColumnSpec`) that treats value columns as data
(`role="measure"`, any number) and performs no arithmetic identity validation;
the priority there is matching source headers to the correct canonical value
columns via `aliases`. That path is currently used only when discovery selects a
non-default schema; the default AOP import still uses the legacy loader.

## Proposed Behavior

Route the default AOP import through the configurable schema-driven loader so:

- Value (measure) columns are defined by the schema and may be any number of
  columns; there is no hardcoded month/total layout requirement.
- Importing maps each source column to the correct canonical value column
  (column matching) rather than validating arithmetic relationships between
  columns.
- The arithmetic identity validation (`YTD/YTG/quarter == sum(...)`) is removed
  from the AOP import path.
- The derived blank-total fill (filling blank `YTD`/quarter/`YTG` cells from
  component months) is removed; source values are taken as-is.

The legacy arithmetic-validating AOP loader is retired for the import path.

## Acceptance Criteria

Canonical AC list (mirrors spec.md v1.0):

- [x] AC-1: The default GUI AOP import runs through `SchemaLoader(default_aop)`
      and applies no arithmetic identity validation (`YTD/YTG/quarter ==
      sum(...)`); a source whose totals do not satisfy those identities imports
      without error. Likely test: `tests/gui/test_pipeline_service.py`
      (`import_aop` routes through the schema loader) plus a
      no-arithmetic-validation case in `tests/test_schema_loader_parity_aop.py`.
- [x] AC-2: A full-year-YTD source imports successfully through `import_aop`
      (regression for the reported failure). Likely test:
      `tests/gui/test_pipeline_service.py` using the in-memory
      `aop_fixtures` full-year-YTD fixture (header resolved via `detect_header_row`).
- [x] AC-3: A partial-year-YTD source imports successfully through `import_aop`.
      Likely test: `tests/gui/test_pipeline_service.py` using the in-memory
      `aop_fixtures` partial-year-YTD fixture.
- [x] AC-4: No blank-total fill is applied on the AOP import path; a source row
      with a blank total cell (e.g. blank `YTD`) yields `0` in that column after
      numeric coercion, not the computed month sum. Likely test:
      `tests/test_schema_loader_parity_aop.py` blank-total case;
      `tests/test_default_schemas.py` asserts `default_aop.fill_rules == ()`.
- [x] AC-5: `SchemaLoader.load` accepts and forwards `resolver`, `is_tty`, and
      `prompt` to `resolve_key`, and `PipelineService.import_aop` wires
      `self._key_mismatch_resolver`, `never_tty`, and `no_stdin_prompt` (the
      resolver forwarded as a callable, invoked only on KEY divergence). Likely
      test: `tests/test_schema_loader_core.py` seam-forwarding test (incl. property
      test) and `tests/gui/test_pipeline_service_key_seam.py`
      `import_aop` resolver-forwarding test re-targeted at the schema path.
- [x] AC-6: The schema-driven AOP output column set and order, and KEY
      semantics, match the prior loader for columns present and populated in the
      source. Likely test: `tests/test_schema_loader_parity_aop.py`
      (column set/order with `check_like=False`; KEY composition).
- [x] AC-7: `import_aop` resolves the AOP header row via `detect_header_row`
      (issue #55) rather than a hardcoded row; a source whose header sits at a
      non-default offset still imports. Likely test:
      `tests/gui/test_pipeline_service.py` asserting detection drives the read,
      with a non-default-offset `aop_fixtures` case importing successfully.
- [x] AC-8: Existing `SchemaLoader` callers and the LE and SKU_LU import paths
      are unaffected (LE/SKU_LU loaders unchanged; `import_with_schema` and other
      `SchemaLoader.load` callers still pass). Likely test: existing
      `tests/test_schema_loader_core.py`, `tests/test_schema_loader_parity_le.py`,
      and LE/SKU_LU pipeline-service tests remain green.
- [x] AC-9: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch, no regression on changed lines, and
      the T1 property/mutation obligations for `src/schema_loader.py` satisfied.

## Constraints & Risks

- Output parity: the schema-driven AOP output column set/order and KEY behavior
  must remain consistent with what downstream pipeline stages consume.
- Dedup: AOP uses `dedup.mode = none` (rows preserved); must be retained.
- Removing the blank-total fill changes output values only for rows that had
  blank totals in the source (those totals become 0 rather than a computed sum);
  confirm no downstream stage depends on the previously-filled values.
- Confidential figures: do not commit computed workbook aggregates; describe
  qualitatively only.

## Test Conditions to Consider

- [ ] AOP import of a full-year-YTD workbook succeeds (regression for the
      reported failure).
- [ ] AOP import of a partial-year-YTD workbook succeeds.
- [ ] Schema-driven AOP output matches the prior loader's output for value
      columns present and populated in the source (parity where applicable).
- [ ] Integration: end-to-end GUI import + run pipeline with AOP through the
      schema path.

## Next Step

- [ ] Promote to GitHub issue (refactor template)
- [ ] Create the active feature folder from the template