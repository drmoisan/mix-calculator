# schema-required-output-semantics - Refactor Spec

- **Issue:** #54
- **Parent (optional):** #50 (rides in PR #51)
- **Owner:** drmoisan
- **Last Updated:** 2026-06-06
- **Status:** Final
- **Version:** 1.0

## Intent & Outcomes

The bundled `default_le` schema (`src/schemas/default_le.schema.json`, v2.0)
declares `YTD/YTG` as `required: true` and also lists it in
`drop_columns: ["YTD/YTG"]`. The column is required only so it can be dropped
before output — it is the dedup discriminator (a processing-only column), not
part of the final table.

User directive (2026-06-06):
- Required columns should include only those necessary for the final table.
- Columns should not be dropped by name; dropped columns should be those not in
  the required (final-table) set — i.e., drop by exclusion.
- Do not require a column only to drop it.

Outcome: the schema-driven loader determines its output set by output-membership
(inclusion), not by a `drop_columns` by-name list. No column is required only to
be dropped.

## Design decision (locked; from research/schema-required-output-semantics-54.md)

The current `required` flag conflates two independent concepts:
- source-presence: must the column exist in the source to load (enforced by
  `resolve_columns`).
- output-membership: is the column in the final table.

These genuinely differ for `KEY` (not sourced, created, in output), AOP `YTG`
(optional in source, in output), and LE `YTD/YTG` (in source, not in output).
A single flag cannot express all three without breaking parity.

Chosen approach (research option (a) — least risk, parity-preserving, additive):
- Add `in_output: bool = True` to `ColumnSpec`.
- `required` keeps its current meaning (source-presence); `resolve_columns` and
  `resolve_and_rename` are unchanged.
- Output column set = declared columns with `in_output == True`, plus `KEY` (the
  business key) and derived columns, in schema order. Output is computed by
  inclusion, not by `drop_columns`.
- `default_le`: `YTD/YTG` becomes `required: false, in_output: false`;
  `drop_columns: []`. Once `required: false`, it is located by name (no fuzzy, no
  raise on absence), carried through resolve/collapse for the dedup discriminator,
  and excluded from output by `in_output: false`.
- `default_aop`: `YTG` gets `in_output: true` (documents that the optional-source
  measure is an output column); `drop_columns` stays `[]`.
- `drop_columns` remains in the JSON shape for backward compatibility but is no
  longer the output-determination mechanism.
- `SCHEMA_FORMAT_VERSION` stays `"2.0"`: `in_output` is additive with a safe
  default of `true`, so absent values round-trip as `true`.

Rejected: redefining `required` as output-membership (breaks source-presence
enforcement for AOP `YTG`); auto-excluding the discriminator (does not generalize
to schemas where the discriminator is also an output column).

## Invariants (must not change)

- `SchemaLoader` output stays byte-identical to the protected loaders: LE equals
  `normalize_le.TARGET_COLUMNS` (column set/order/values); AOP equals the
  `load_aop` output layout.
- The protected loaders (`src/normalize_le.py`, `src/load_aop.py`) and their
  helpers are not modified.
- `resolve_columns` source-presence semantics are unchanged.
- The CLI surface is unchanged.
- JSON schema shape stays loadable; older JSON without `in_output` loads with
  `in_output=True`.

## Scope (structural changes)

- `ColumnSpec` gains `in_output: bool = True`.
- Serialization reads/writes `in_output` with default `True`.
- Output determination switches from `drop_columns` exclusion to `in_output`
  inclusion (plus KEY and derived).
- Bundled `default_le` and `default_aop` updated as above.
- The #50 schema-builder carries `in_output` through its column row model and
  `assemble_schema` so a builder-authored schema can express processing-only
  columns; the column-spec split in `_schema_provider_factory` reflects the new
  flags.

## Non-Goals

- No change to dedup math, fill rules, derived-column evaluation, or key
  composition.
- No new SCHEMA_FORMAT_VERSION bump.
- No removal of the `drop_columns` field from the JSON shape (kept for
  compatibility; simply unused for output determination).
- No change to the protected loaders.

## Dependencies / Touchpoints

- `src/_schema_model_specs.py` (`ColumnSpec`), `src/schema_model.py` (re-export /
  validation), `src/schema_serialization.py`, `src/_schema_loader_helpers.py`,
  `src/schemas/default_le.schema.json`, `src/schemas/default_aop.schema.json`.
- #50 builder: `src/gui/presenters/_schema_builder_state.py`,
  `schema_builder_presenter.py`, `_columns_tab_presenter.py`,
  `src/gui/_schema_provider_factory.py`.
- Rides in PR #51 on branch `feature/schema-builder-ux-overhaul-50`.

## Risks & Mitigations

- Parity regression: mitigate with the existing LE/AOP parity tests plus new
  output-membership tests; run the full suite.
- Builder tuple-arity change is pervasive (4-tuple -> 5-tuple column rows):
  mitigate by updating every unpack site and adding a builder round-trip test;
  Pyright will catch missed sites.
- DedupPolicy requires a declared discriminator for aggregate mode: `YTD/YTG`
  stays declared in `columns`, so validation still passes (confirmed in research).

## Technical Specifications

- Files/modules expected to change: as listed in Dependencies / Touchpoints.
- Public interfaces affected: `ColumnSpec` gains a field (additive, defaulted);
  serialization key set gains `in_output`.
- Data-flow adjustments: `_output_column_order` filters by `in_output`; the AOP
  (`none` mode) emit path filters declared columns by `in_output` instead of by
  `drop_columns`.
- Migration: none required; additive field with default `True`.

## Test Strategy

- Update `tests/test_default_schemas.py` (currently asserts
  `drop_columns == ("YTD/YTG",)`): assert `drop_columns == ()`, `YTD/YTG`
  `required is False` and `in_output is False`.
- Keep/confirm LE and AOP parity tests
  (`tests/test_schema_loader_parity_le.py`, `..._aop.py`) pass unchanged.
- New: `in_output=False` column excluded from output; `in_output=True` included;
  discriminator case (required:false, in_output:false) present in source, absent
  from output, dedup result still correct; `schema_from_json` defaults absent
  `in_output` to `True`; round-trip for `in_output=False`.
- New: builder `assemble_schema` forwards `in_output` to `ColumnSpec`; the
  provider-factory split places LE `YTD/YTG` in the optional set.
- Toolchain: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch`),
  coverage >= 85% line / >= 75% branch, no regression on changed lines.

## Definition of Done

- [ ] `ColumnSpec.in_output` added and serialized (default True).
- [ ] Output determined by `in_output` inclusion (+ KEY + derived), not
      `drop_columns`.
- [ ] `default_le`: `YTD/YTG` required:false, in_output:false, drop_columns [].
- [ ] `default_aop`: `YTG` in_output:true, drop_columns [].
- [ ] LE and AOP `SchemaLoader` parity preserved (tests pass).
- [ ] Builder carries `in_output`; round-trip test added.
- [ ] Full toolchain pass; coverage thresholds met; no regression.

## Acceptance Criteria

- [x] AC-1: No bundled schema requires a column only to drop it; `default_le`
      `YTD/YTG` is `required: false` and `in_output: false`, and
      `drop_columns` is `[]`.
- [x] AC-2: The schema loader determines output columns by inclusion
      (`in_output` true, plus `KEY` and derived columns), not by a `drop_columns`
      by-name list.
- [x] AC-3: LE schema-driven load output equals `normalize_le.TARGET_COLUMNS`
      exactly (set, order, values).
- [x] AC-4: AOP schema-driven load output equals the `load_aop` output exactly,
      including the optional-but-output `YTG`.
- [x] AC-5: A processing-only column (required:false, in_output:false) is present
      in the source, used for dedup, and excluded from the output.
- [x] AC-6: `ColumnSpec.in_output` defaults to `True`; JSON without the field
      loads as `True`; a schema with `in_output:false` round-trips.
- [x] AC-7: The #50 schema-builder carries `in_output` end-to-end
      (`assemble_schema` -> `ColumnSpec`), and the provider-factory split places
      LE `YTD/YTG` in the optional set.
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Seeded Test Conditions (from potential)
- [ ] LE schema-driven load output equals `normalize_le.TARGET_COLUMNS` exactly.
- [ ] AOP schema-driven load output equals the AOP loader output exactly.
- [ ] A source with extra/processing-only columns drops them by exclusion.
- [ ] Round-trip serialization of the migrated bundled schemas.
