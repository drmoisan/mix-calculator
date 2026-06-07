---
name: configurable-schema-persisted-matching
description: Schema-builder column matching must be persisted (as ColumnSpec aliases), not ephemeral; partial match -> new-from-template
metadata:
  type: feedback
---

For the configurable Schema Builder, the matched source-column-to-canonical mapping must be **persisted** on the schema (via `ColumnSpec` aliases), not recomputed as ephemeral UI state.

**Why:** The user corrected my recommendation to make matching ephemeral. The entire point of a configurable schema is that the matching persists. Required (canonical) columns are fixed and do not change across schemas; the *matching/alias* columns are what vary, which is why multiple schemas are persisted for the same canonical set. Source workbooks differ in their column names, so a saved schema must remember which source names map to which canonical column.

**How to apply:** On source-tab activation, run fuzzy matching **first against the persisted consumed/alias columns** of existing schemas to confirm whether a pre-existing schema is genuinely a match. If many columns match but not all, treat it as a possibly-new schema and offer a **"New from template"** action that seeds a new schema from the closest existing one. Do not propose ephemeral/recompute-on-open designs for schema matching state. Decided for issue #50; see [[derived-aggregates-are-confidential]] and [[subagents-cannot-open-xlsx]] for the related masking constraints.
