# schema-required-output-semantics (Issue #54)

- Date captured: 2026-06-06
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/schema-required-output-semantics/ (Issue #54)

- Issue: #54
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/54
- Last Updated: 2026-06-06
- Work Mode: full-feature

## Problem / Why

The bundled `default_le` schema (`src/schemas/default_le.schema.json`, v2.0)
declares `YTD/YTG` as `required: true` and also lists it in `drop_columns:
["YTD/YTG"]`. The column is required only so it can be dropped before output —
it is the dedup discriminator (a processing-only column), not part of the final
table.

User directive (2026-06-06):
- Required columns should include only those necessary for the final table.
- Columns should not be dropped by name; dropped columns should be those not in
  the required (final-table) set — i.e., drop by exclusion.
- Do not require a column only to drop it.

## Analysis / Constraints

The current schema model conflates two distinct concepts under `required`:

1. Source-presence: whether the column must exist in the source workbook for the
   load to succeed (`resolve_columns` raises if a `required` column is absent).
2. Output-membership: whether the column appears in the final table.

These differ across real columns:

- `KEY` (both schemas): `required: false`, not in source (created by the loader),
  but IS in the output.
- LE `YTD/YTG`: `required: true`, in source, NOT in output (discriminator). This
  is the require-then-drop defect the user reported.
- AOP `YTG`: `required: false` (optional in source — older AOP sheets predate it,
  it is produced by a fill rule), but IS in the output.

So a naive rule "output = required columns + derived" would correctly drop LE
`YTD/YTG` but would incorrectly drop AOP `YTG`. The model needs to express
"present for processing/output but not source-required" separately from
"in the final table".

Parity is mandatory: `SchemaLoader` must keep producing output byte-identical to
the protected loaders (`normalize_le.TARGET_COLUMNS` for LE; the full AOP layout
for AOP). The `test_schema_loader` parity tests pin this.

This work also reshapes the semantics the #50 schema-builder is built on
(required/optional tabs, any drop affordance), so it is being folded into the
#50 branch (PR #51) before that merges.

## Proposed Behavior

- Output column set is determined by inclusion (final-table membership) plus the
  business `KEY` and derived columns, not by a `drop_columns` by-name list.
- The LE discriminator (`YTD/YTG`) is no longer required and no longer named in a
  drop list; it is retained for processing and excluded from output by exclusion.
- AOP output is unchanged (its optional-but-output columns, e.g. `YTG`, stay in
  the final table).
- `SchemaLoader` output remains byte-identical to the protected loaders.

## Acceptance Criteria

Canonical AC list (mirrors spec.md v1.0):

- [x] AC-1: No bundled schema requires a column only to drop it; `default_le`
      `YTD/YTG` is `required: false` and `in_output: false`, and `drop_columns`
      is `[]`.
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

## Constraints & Risks

- Parity with the protected loaders must be preserved (byte-identical output).
- `required` currently drives source-presence enforcement; redefining it toward
  output-membership risks breaking optional-source columns (AOP `YTG`) and
  required-source columns absent from output (LE `YTD/YTG`).
- Coupled to the unreleased #50 schema-builder; lands in PR #51.

## Test Conditions to Consider

- [ ] LE schema-driven load output equals `normalize_le.TARGET_COLUMNS` exactly.
- [ ] AOP schema-driven load output equals the AOP loader output exactly.
- [ ] A source with extra/processing-only columns drops them by exclusion.
- [ ] Round-trip serialization of the migrated bundled schemas.

## Next Step

- [ ] Promote to GitHub issue
- [ ] Create active feature folder from the template