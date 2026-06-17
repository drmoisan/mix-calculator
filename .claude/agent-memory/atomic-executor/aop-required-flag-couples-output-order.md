---
name: aop-required-flag-couples-output-order
description: Flipping AOP measure `required` flags to false reorders SchemaLoader output columns; zero-regression cannot be met by a schema-JSON-only edit
metadata:
  type: project
---

For `default_aop` (dedup mode `none`), flipping measure `required: true -> false` in
`src/schemas/default_aop.schema.json` changes the SchemaLoader EMITTED COLUMN ORDER, breaking
`tests/test_schema_loader_parity_aop.py` (all four parity tests; measures move after the
`Super Category`/`PPG` dimensions). No data is lost — only order changes.

**Why:** `src/_schema_loader_helpers.py::resolve_and_rename` builds `required_expected` from
`c.required` and `_by_name_optional_columns` appends every `not column.required` column; the
select+rename plan puts required columns first then by-name-optional columns last. The AOP
`none`-mode `emit_output_columns` preserves that reordered frame order. `default_le` is immune
because its `aggregate` dedup mode rebuilds canonical declared order via `_output_column_order`,
independent of `required`.

**How to apply:** Epic #74 child CF1 (issue #74) R1 asked to flip AOP measure flags with a
schema-JSON-only scope and zero output regression. Those two constraints are mutually exclusive
without a loader-helper fix. The cycle-2 plan (2026-06-17T13-10) authorized the loader-helper
fix BUT scoped it as "keep-list reorder in `resolve_and_rename`, `_by_name_optional_columns`
unchanged." That is ALSO insufficient: after the flag flip, `_by_name_optional_columns(default_aop)`
goes from `['KEY','YTG']` to `['KEY', Jan..Dec, YTD, Q1..Q4, 'YTG']`, sweeping the measures in.
`YTG` and the measures are then field-identical (role=measure, required=False, in_output=True,
numeric=True) — there is NO flag-independent schema signal separating the genuine
presence-optional `YTG` (older AOP sheets predate it) from the now-non-required measures.
`load_aop` only reproduces its `YTG`-trailing order via the hardcoded literal `{"KEY","YTG"}`
(`src/_load_aop_helpers.py` `EXPECTED_COLUMNS`). A schema-driven loader needs an equivalent
flag-independent signal.

**Real fix:** add a presence-optional concept to the schema model (e.g. `ColumnSpec.presence_optional`
seeded by the 2.0->3.0 migration as `not required(2.0)`) so the by-name-located optional set
({KEY, YTG}) is expressible without the `required` flag. That is a CF-level / schema-model
change, outside "ordering-only loader change," so it needs an explicit plan revision. Executor
halted cycle-2 at P1-T1 with the tree clean and AOP+LE parity green; finding dossier at
`docs/features/active/etl-required-output-model-semantics-74/evidence/regression-testing/r1-scope-insufficiency-finding.2026-06-17T13-10.md`.
Related: [[nrr-summary-mix-total-spec-gap]] (a Check surfacing an upstream defect).
