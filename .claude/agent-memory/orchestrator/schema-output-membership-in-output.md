---
name: schema-output-membership-in-output
description: ColumnSpec.in_output separates output-membership from source-presence (required); the loader emits by inclusion, not drop_columns.
metadata:
  type: project
---

`ColumnSpec` carries two independent booleans: `required` (source-presence — must
the column exist in the source to load; enforced by `resolve_columns`) and
`in_output` (final-table membership; default `True`). The schema-driven loader
(`src/_schema_loader_helpers.py`) determines its output set by INCLUSION:
declared columns with `in_output == True`, plus the business `KEY`, plus derived
columns, in schema order. It does NOT drop by the `drop_columns` name list.

**Why:** The `default_le` schema previously marked the `YTD/YTG` dedup
discriminator `required: true` and listed it in `drop_columns` — requiring a
column only to drop it. The user rejected that: required columns should be only
those needed for the final table, and dropping should be by exclusion, not by
name (issue #54, rode in PR #51). A single flag could not express all three real
cases: `KEY` (created, not sourced, in output), AOP `YTG` (optional in source, in
output), LE `YTD/YTG` (sourced, not in output). So `in_output` was added.

**How to apply:** When editing schemas or the loader, set a processing-only
column (e.g. a dedup discriminator) to `required: false, in_output: false` — it is
located by name, carried through resolve/collapse, and excluded only at emit.
`drop_columns` remains in the JSON shape for backward compatibility but no source
path consults it for output. `in_output` is additive with default `True`, so
legacy JSON loads unchanged and `SCHEMA_FORMAT_VERSION` stayed `"2.0"`. The
`SchemaLoader` parity invariant (byte-identical to the protected
`normalize_le`/`load_aop` loaders) still holds; the parity tests pin it. See also
[[configurable-schema-persisted-matching]].
