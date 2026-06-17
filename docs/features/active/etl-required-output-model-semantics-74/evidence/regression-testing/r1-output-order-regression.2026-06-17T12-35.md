# R1 Output-Order Regression — blocking finding

Timestamp: 2026-06-17T12-35

Command: poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_default_schemas.py -q

EXIT_CODE: 1

Output Summary: 4 failed, 28 passed. The four `test_schema_loader_parity_aop.py` parity tests fail with a column-ORDER divergence (no data loss; all columns still emitted).

## Failure detail

`assert list(schema_output.columns) == list(protected.columns)` fails at index 5: `'Super Category' != 'Jan'`.

- Protected `load_aop` column order (authoritative, unchanged):
  `Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY`
- `SchemaLoader(default_aop)` order AFTER the R1 schema edit:
  `Customer, SKU Descripiton, SKU #, Customer Master, Type, Super Category, PPG, Jan..Dec, YTD, Q1..Q4, YTG, KEY`

The measures (`Jan`..`YTD`, `Q1`..`Q4`) move to AFTER the `Super Category`/`PPG` dimensions, changing emitted column order. This violates the mandatory zero-output-regression invariant (remediation-inputs Do-Not-Do: "column order ... must remain identical").

## Root cause (outside plan scope)

The AOP `none`-dedup path in `src/_schema_loader_helpers.py` couples emitted column ORDER to the `required` flag:

- `resolve_and_rename` builds `required_expected` from `c.required` (line ~174), so the now-non-required measures drop out of the required set.
- `_by_name_optional_columns` (line ~232) appends every `not column.required` column to the by-name-optional list.
- The select+rename plan places required columns first, then appends by-name-optional columns, so the measures are reordered to the end of the frame.
- `emit_output_columns` (none path) preserves this reordered frame order, so the AOP output order changes.

`emit_output_columns` itself correctly uses `in_output` for membership, but the upstream resolve step reorders by `required` before emit sees the frame.

## Scope conflict

R1 scope restricts edits to `src/schemas/default_aop.schema.json` and `tests/test_default_schemas.py`. The remediation Do-Not-Do list forbids loader changes ("no loader enforcement changes"). Achieving zero output-order regression requires a fix in `src/_schema_loader_helpers.py` (decouple resolve/by-name ordering from `required`, ordering by declared `columns` position instead). That is a new independent outcome not described by any plan task and explicitly outside the authorized scope.

This was observed analogously to be a non-issue for `default_le` only because the LE schema uses `aggregate` dedup mode, whose emit path rebuilds the canonical declared order via `_output_column_order(schema)` independent of `required`. The AOP `none` path has no such canonical reorder, so it is sensitive to the `required`-driven resolve order.

## Action

Execution halted before completing P2-T3. The schema edits made in Phase 1 are reverted to restore the clean baseline tree (no partial regression left on disk). A plan revision is required to authorize a minimal, ordering-only fix in `src/_schema_loader_helpers.py` (order resolved/by-name columns by declared `columns` index so `required` does not affect emitted order), or to re-scope R1.
