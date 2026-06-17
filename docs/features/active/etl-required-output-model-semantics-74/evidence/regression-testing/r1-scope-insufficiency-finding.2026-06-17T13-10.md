# Finding: R1 (as scoped) cannot achieve flag-independent AOP `none`-path order

Timestamp: 2026-06-17T13-10

Status: NEW FINDING — execution halted before completing Phase 1 (R1) / Phase 2 (R2).
Working tree left clean (R1 source edits reverted; `src/_schema_loader_helpers.py` restored
to the 464-line baseline; AOP+LE parity green: 11 passed).

## Summary

The cycle-2 plan scopes R1 as an ordering-only change in `resolve_and_rename`
(`src/_schema_loader_helpers.py`) with `_by_name_optional_columns` explicitly held unchanged
(plan task P1-T3). The plan's stated mechanism (plan lines 31-39) assumes the AOP by-name
optionals are exactly `{KEY, YTG}`. That assumption holds before R2 but is destroyed by R2:
flipping the seventeen measure columns to `required: false` makes them indistinguishable from
the genuine presence-optional `YTG`, so they are swept into the by-name-optional set and
reorder the emitted `none`-path output. No flag-independent, schema-driven rule reproduces
`load_aop`'s `YTG`-trailing order after the flip.

## Reproduction (clean baseline tree, no R1 applied)

Command: `poetry run python` snippet exercising `_by_name_optional_columns` and a simulated R2
flip via `dataclasses.replace`.

EXIT_CODE: 0

Output:
```
PRE-R2 by_name_optional(default_aop):  ['KEY', 'YTG']
POST-R2 by_name_optional(default_aop): ['KEY', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'YTD', 'Q1', 'Q2', 'Q3', 'Q4', 'YTG']
YTG fields:  role=measure required=False in_output=True numeric=True
Jan fields:  role=measure required=False in_output=True numeric=True
YTG vs Jan field-identical (except name): True
```

Simulated R2 on top of an ordering-only R1 (keep-list ordered by declared index, by-name
optionals appended) produced:
```
POST-R2 SchemaLoader: Customer, SKU Descripiton, SKU #, Customer Master, Type, Super Category, PPG, Jan..Dec, YTD, Q1..Q4, YTG, KEY
load_aop ORACLE     : Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY
MATCH: False
```
The measures move AFTER `Super Category`/`PPG` — the same column-ORDER regression recorded in
cycle 1 (`r1-output-order-regression.2026-06-17T12-35.md`). The binding parity oracle
(`tests/test_schema_loader_parity_aop.py`) would fail on the with-YTG fixture.

## Root cause (precise)

Two lines in `src/_schema_loader_helpers.py` couple the `none`-path emitted ORDER to the
`required` flag:
1. `resolve_and_rename` builds `required_expected` from `c.required` (keep-list body), and
2. `_by_name_optional_columns` appends every `not column.required` column to the by-name
   optional set, which the keep-list then appends AFTER the body.

The cycle-2 plan addresses (1) via the keep-list reorder but holds (2) unchanged (P1-T3).
After R2, (2) sweeps the measures into the by-name optionals. The keep-list reorder cannot
separate the genuine presence-optional `YTG` from the now-non-required measures because, in
the schema, `YTG` and every month/quarter/`YTD` measure are field-identical except for their
name (role=measure, required=False, in_output=True, numeric=True). The only signal that ever
distinguished `YTG` (presence-optional; older AOP sheets predate it) from the measures
(always present) was the pre-3.0 `required` flag, and R2 removes it.

`load_aop` reproduces its order via the hardcoded literal `{"KEY", "YTG"}`
(`src/_load_aop_helpers.py` line 83, `EXPECTED_COLUMNS = [c for c in SOURCE_COLUMNS if c not
in {"KEY", "YTG"}]`). A schema-driven loader has no equivalent flag-independent signal.

## Why this is outside the authorized scope

Reproducing `load_aop`'s `YTG`-trailing order flag-independently requires one of:
- a new schema-model "presence-optional" concept (a `ColumnSpec` field + schema-JSON change),
  which is a CF-level change and outside CF1's "ordering-only loader change" remit and the
  spec Non-Goal "no loader enforcement changes"; or
- a brittle hardcoded `{"KEY", "YTG"}` name set inside the schema-driven loader, which
  contradicts the schema-driven design and is AOP-specific.

Either is a new independent outcome not described by R1/R2/R3. Per the executor scope-change
rule, execution stopped and the working tree was left clean rather than expanding scope.

## Recommended remediation (for a follow-up planning cycle)

Add a flag-independent presence-optionality signal to the schema model so the by-name-located
optional set (`KEY` plus presence-optional carried columns such as the AOP `YTG`) is
expressible without the `required` flag. Options to evaluate:
- a `ColumnSpec.presence_optional: bool` (or `source_optional`) field, set true for `KEY` and
  `YTG` in `default_aop.schema.json`, consumed by `_by_name_optional_columns` and the
  keep-list split; the `2.0 -> 3.0` migration would seed `presence_optional = (not
  required(2.0))` so the pre-flip {KEY, YTG} set is preserved; then R2's `required` flip no
  longer affects ordering; or
- mark the by-name optionals via the existing `role`/structure if a non-additive encoding is
  preferred.

This keeps R2 (the `required`-flag flip) and R3 (the accessor test) intact and makes R1 a
real, flag-independent decoupling.

## Tree state at halt

- `src/_schema_loader_helpers.py`: reverted to baseline (464 lines).
- `src/schemas/default_aop.schema.json`: unchanged (R2 not applied).
- `tests/test_default_schemas.py`: unchanged (R3 not applied).
- AOP+LE parity: 11 passed (green baseline preserved).
