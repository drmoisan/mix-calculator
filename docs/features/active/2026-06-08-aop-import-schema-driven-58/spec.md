# aop-import-schema-driven - Refactor Spec

- **Issue:** #58
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-08
- **Status:** Final
- **Version:** 1.0

## Intent & Outcomes

The default GUI AOP import routes through the legacy `src.load_aop.load_aop`,
whose `validate_aop` (in `src/_load_aop_helpers.py`) enforces per-row arithmetic
identities between value columns: `YTD == sum(months)`, `YTG == sum(May..Dec)`,
and `Q1..Q4 == sum(constituent months)`. These identities are not stable across
real source workbooks. Two of the user's real workbooks encode `YTD`
differently (one partial-year, one full-year), both with a `YTG` column. The
hardcoded validation rejects the full-year workbook with an `AOP validation
failed: YTD != sum(months)` error, blocking import.

The root issue is architectural. The legacy AOP loader hardcodes a fixed
value-column layout (Jan..Dec + YTD + Q1..Q4 + YTG) and validates relationships
between those columns. The repository already contains a configurable,
schema-driven load path (`src.schema_loader.SchemaLoader` driven by
`SchemaDefinition`/`ColumnSpec`) that treats value columns as data
(`role="measure"`, any number) and performs no arithmetic identity validation;
the priority there is matching source headers to the correct canonical value
columns via aliases. That path is currently used only when discovery selects a
non-default schema; the default AOP import still uses the legacy loader.

Outcome: the default GUI AOP import runs through `SchemaLoader` driven by the
bundled `default_aop` schema. No arithmetic identity validation is applied on
the import path, and the derived blank-total fill is removed so source values
pass through as-is. Both real workbooks import successfully.

## Design decision (locked; from artifacts/research/aop-import-schema-driven-58.md)

Scope 1B (architectural, user-approved): route the default GUI AOP import
through the configurable `SchemaLoader` driven by the bundled `default_aop`
schema; retire the legacy arithmetic-validating `load_aop` for the IMPORT path.

Three production changes, each contained:

- `src/gui/pipeline_service.py` — rewrite `PipelineService.import_aop` to read
  the raw AOP frame at the header row resolved by `detect_header_row` (the issue
  #55 mechanism now on `main`; the standard AOP1 header resolves to row index 2),
  then `read_excel_sheet` at that row, load the
  bundled `default_aop` schema, and call the schema-driven path. Forward the
  injected KEY-mismatch resolver and the no-stdin seams to the loader (see
  KEY-resolver seam below). Remove the module-level `load_aop` import if
  `import_aop` is its only remaining caller in this module.
- `src/schema_loader.py` (T1) — extend `SchemaLoader.load` with optional
  `resolver`, `is_tty`, and `prompt` parameters and forward them into
  `resolve_key`. The parameters are optional with current defaults so existing
  callers are unaffected.
- `src/schemas/default_aop.schema.json` — set `fill_rules` to `[]` (Decision 2,
  user-approved) to disable blank-total filling. Update the informational
  `header_row` field to `2` so the schema accurately describes the source
  layout. No `SchemaLoader` code change is needed to disable filling: the
  existing `if totals_to_months:` guard short-circuits when `fill_rules` is
  empty.

KEY-resolver seam (BLOCKING design requirement). `SchemaLoader.load` currently
calls `resolve_key(frame, "prompt", has_key_column=...)` with no `resolver`,
`is_tty`, or `prompt` arguments. In a GUI session (stdin is not a TTY) a
diverging AOP KEY would reach the non-interactive prompt path and raise
`ValueError` instead of showing the Qt modal, losing the issue #52 resolver
seam. The fix threads `resolver`, `is_tty`, and `prompt` through exactly one
interface boundary (`SchemaLoader.load`), so `import_aop` can pass
`self._key_mismatch_resolver`, `never_tty`, and `no_stdin_prompt` as it does for
`import_le`/`load_aop` today. Because `src/schema_loader.py` is T1 (Critical),
this change carries property-test and mutation obligations and must keep all
existing `SchemaLoader` callers working (new parameters optional, current
defaults preserved).

Rejected alternatives: reading the raw frame and resolving the KEY separately
before the schema path (KEY resolution is integral to the loader pipeline and
cannot be cleanly externalized); threading the seams through
`import_with_schema` only (does not close the gap for direct `SchemaLoader.load`
callers and is a wider surface than necessary).

## Invariants (must not change)

- Output parity for populated source columns: the schema-driven AOP output
  column set and order, and KEY semantics, remain consistent with the prior
  loader's output for columns that are present and populated in the source. The
  natural output order is `[Customer, SKU Descripiton, SKU #, Customer Master,
  Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, KEY, YTG]` (KEY and YTG
  appended last), matching `load_aop` today (confirmed by the existing parity
  suite using `check_like=False`).
- KEY composition: `Customer + coerce_sku(SKU #) + Type` (no separator), with a
  pre-existing source KEY reconciled per the divergence policy. The issue #52
  GUI resolver path is preserved: the injected `resolver` callable is invoked
  only on genuine KEY divergence; `never_tty` and `no_stdin_prompt` keep a GUI
  session off stdin.
- Dedup: AOP uses `dedup.mode = none` (rows preserved in source order); retained.
- The protected loaders' CLI path is unchanged: `src/load_aop.py` `main`,
  `validate_aop`, and `build_per_row_checks` are not modified.
  `coerce_numeric` and `clean_label_sentinels` in `src/_load_aop_helpers.py`
  remain (consumed by `SchemaLoader._coerce_and_clean`).
- Non-AOP imports unchanged: `import_le` (LE) and `import_skulu` (SKU_LU) and
  their loaders are not touched.

## Parity contract (downstream consumers)

Downstream of `import_sources`, only these AOP columns are consumed:

- `build_customer_lu` reads `Customer`, `Customer Master`.
- `pivot_aop` reads `Customer Master`, `Customer`, `Super Category`, `PPG`,
  `SKU Descripiton`, `SKU #`, `Type`, and `YTG` (optional; when absent,
  `pivot_aop` derives it by summing May..Dec).
- `KEY` is present in all cases and used for row identity.

No downstream stage reads `YTD`, `Q1`–`Q4`, or `Jan`–`Dec` from the AOP frame;
those are carried to SQLite only. No downstream code depends on YTD/quarter/
month/YTG internal consistency. Removing blank-total fill and arithmetic
validation therefore does not change any downstream transform result. The only
observable output delta is rows with a genuinely blank source total cell: after
numeric coercion the blank becomes `0` instead of a computed month sum (per
Decision 2, this is the approved behavior).

## Scope (structural changes)

- Route the default GUI AOP import through `SchemaLoader(default_aop)`:
  - Read the raw AOP frame at the header row resolved by `detect_header_row`
    (issue #55), then `read_excel_sheet` at that row (the schema JSON `header_row`
    is informational and does not drive the read).
  - Transform via `SchemaLoader.load`, returning the canonical AOP output frame.
- Remove arithmetic identity validation from the import path (the schema path
  performs none).
- Remove the derived blank-total fill on the import path by clearing
  `fill_rules` in `default_aop`; source values pass through as-is.
- Extend `SchemaLoader.load` with optional `resolver`/`is_tty`/`prompt` and
  forward them to `resolve_key`; wire them from `import_aop`.

## Non-Goals

- The legacy CLI AOP path is out of scope and unchanged: `src/load_aop.py`
  `main`, the `mix_pipeline._import_sources` call to `load_aop.load_aop`, and
  the `validate_aop` / `build_per_row_checks` functions remain as-is. They are
  not called by the GUI import path. Aligning CLI behavior with the new GUI
  behavior is not part of this work.
- No change to dedup math, KEY composition, derived-column evaluation, or
  column matching semantics.
- No change to the LE or SKU_LU import paths or their loaders.
- No new dependency, no new SCHEMA_FORMAT_VERSION bump (clearing `fill_rules`
  and updating the informational `header_row` are data-only edits within the
  existing `2.0` shape).

## Dependencies / Touchpoints

- Production: `src/gui/pipeline_service.py` (`import_aop`),
  `src/schema_loader.py` (`SchemaLoader.load`),
  `src/schemas/default_aop.schema.json` (`fill_rules`, `header_row`).
- Reused without modification: `src/etl_key.py` (`resolve_key`),
  `src/_schema_loader_helpers.py`, `src/_load_aop_helpers.py`
  (`coerce_numeric`, `clean_label_sentinels`),
  `src/gui/_key_mismatch_seam.py` (`never_tty`, `no_stdin_prompt`),
  `src/schema_registry` (`load_bundled_default("default_aop")`),
  `src/pandas_io` (`read_excel_sheet`).
- Downstream consumers (parity contract above): `src/mix_lookups.py`
  (`build_customer_lu`), `src/mix_transforms.py` (`pivot_aop`).

## Risks & Mitigations

- KEY-resolver seam gap (High; Blocking until addressed): routing through
  `SchemaLoader.load` without the new seam parameters would break the issue #52
  GUI resolver. Mitigation: the seam extension is the first implementation step
  and is covered by a forwarding test (`SchemaLoader.load` -> `resolve_key`) and
  by an updated `import_aop` resolver-forwarding test.
- Blank-fill output delta (Medium; Behavioral, approved): rows with blank source
  totals produce `0` instead of a computed sum. Bounded by the parity contract
  (no transform reads those columns). This is the approved intent of Decision 2.
- Test patch-target staleness (Medium; Test maintenance): several GUI tests
  patch `src.load_aop.load_aop` to intercept AOP import. After routing, those
  patches miss the new call path and could pass vacuously. Mitigation: a
  systematic scan of `monkeypatch.setattr("src.load_aop.load_aop", ...)` sites
  and re-targeting them at the schema path. Confirmed sites:
  `test_pipeline_service.py`, `test_pipeline_service_key_seam.py`,
  `test_behavioral_composition.py`, `test_gui_integration.py`,
  `test_key_mismatch_dialog.py`.
- T1 obligations on `SchemaLoader.load` (Process): property tests for the new
  resolver-forwarding path and a mutation score >= 75% are required for
  `src/schema_loader.py`. Mitigation: add property and forwarding tests with the
  seam change and run mutation in the pre-merge/nightly pipeline.

## Technical Specifications

- Files/modules expected to change: `src/gui/pipeline_service.py`,
  `src/schema_loader.py`, `src/schemas/default_aop.schema.json`.
- Public interfaces affected: `SchemaLoader.load` gains three optional keyword
  parameters (`resolver`, `is_tty`, `prompt`) with current defaults, additive
  and backward-compatible. `PipelineService.import_aop` signature is unchanged;
  its internal call path changes from `load_aop.load_aop` to the schema path.
- Data-flow adjustments: `import_aop` reads raw at the `detect_header_row`-resolved header, loads the bundled
  `default_aop` schema, and calls the schema-driven loader with the resolver and
  no-stdin seams. `fill_rules=[]` disables the fill phase via the existing guard.
- Validation adjustments: arithmetic identity validation is removed from the
  import path; column matching (source header -> canonical value column via
  aliases) remains the basis for value-column resolution.
- Logging/telemetry: keep the existing `import_aop` info log; no new telemetry.
- Migration/backfill: none. The schema edits are data-only and round-trip in the
  existing `2.0` shape.

## Test Strategy

- Regression tests (fixtures only; no `.xlsx` on disk, no temp files): import a
  full-year-YTD source successfully (the reported failure) and a partial-year-YTD
  source successfully, both via the in-memory `aop_fixtures` workbook builder,
  with the header row resolved by `detect_header_row`.
- No-arithmetic-validation test: a source whose totals do not satisfy
  `YTD == sum(months)` imports without error through the schema path.
- No-blank-fill test: a source row with a blank total cell yields `0` in that
  column after coercion, not the computed month sum.
- Header-row test: `import_aop` resolves the header row via `detect_header_row`
  (issue #55) rather than a hardcoded row; a source whose header sits at a
  non-default offset still imports.
- Seam-forwarding tests: `SchemaLoader.load(raw, resolver=..., is_tty=...,
  prompt=...)` forwards those arguments to `resolve_key` on a diverging KEY;
  `import_aop` forwards the injected resolver callable (not its result) to the
  schema loader. Add a property test for the resolver-forwarding behavior to
  satisfy the T1 obligation on `src/schema_loader.py`.
- Output parity test: schema-driven AOP output column set/order and KEY for
  populated source columns match the prior behavior (update
  `tests/test_schema_loader_parity_aop.py` to assert the new intended behavior
  rather than legacy fill parity; the four current no-blank-total fixtures
  continue to pass).
- Unaffected-callers tests: existing `SchemaLoader` callers and the LE/SKU_LU
  import paths remain green; update `tests/test_default_schemas.py` `fill_rules`
  structural assertion to expect an empty list.
- Patch-target updates: re-target the five `src.load_aop.load_aop` monkeypatch
  sites listed under Risks at the schema path.
- Toolchain: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch`),
  coverage >= 85% line / >= 75% branch, no regression on changed lines; T1
  property and mutation obligations for `src/schema_loader.py`.

## Definition of Done

- [ ] Default GUI AOP import runs through `SchemaLoader(default_aop)`; no
      arithmetic identity validation on the import path.
- [ ] `default_aop` `fill_rules` is `[]`; blank source totals pass through as 0.
- [ ] `default_aop` `header_row` is `2` (informational, matches the actual read).
- [ ] `SchemaLoader.load` forwards `resolver`/`is_tty`/`prompt` to `resolve_key`;
      `import_aop` wires the resolver and no-stdin seams.
- [ ] Full-year-YTD and partial-year-YTD sources both import successfully.
- [ ] Output column set/order and KEY parity preserved for populated columns.
- [ ] Existing `SchemaLoader` callers and LE/SKU_LU imports unaffected.
- [ ] Full toolchain pass; coverage thresholds met; T1 property/mutation
      obligations satisfied; no regression on changed lines.

## Acceptance Criteria

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

## Seeded Test Conditions (from potential)
- [ ] AOP import of a full-year-YTD workbook succeeds (regression for the
      reported failure).
- [ ] AOP import of a partial-year-YTD workbook succeeds.
- [ ] Schema-driven AOP output matches the prior loader's output for value
      columns present and populated in the source (parity where applicable).
- [ ] Integration: end-to-end GUI import + run pipeline with AOP through the
      schema path.
