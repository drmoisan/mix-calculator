---
name: aggregate-dedup-mode-loader-coupling
description: The "aggregate" dedup mode was added as a rename of "collapse"; the loader had a literal `== "collapse"` check that must include aggregate, and AOP cannot be aggregate (no discriminator)
metadata:
  type: project
---

The schema-builder UX overhaul (#50) added `"aggregate"` to `DEDUP_MODES` as the
renamed form of the collapsing behavior (spec Decision 1). Two non-obvious coupling
points matter for future dedup-mode work:

- The schema loader treats any non-`"none"` mode as collapsing for the merge step,
  but `src/_schema_loader_helpers.py` also had a literal `schema.dedup.mode ==
  "collapse"` check selecting the canonical output column ordering. That check now
  reads `in {"collapse", "aggregate"}`. Any new collapsing mode must be added there
  too, or output column ordering silently reverts to the frame's natural order.

- **Why:** the model (`SchemaDefinition`) already uses `{"collapse","aggregate"}`
  for discriminator validation, but the loader's column-ordering branch was the one
  place still keyed on the literal string, so a bundled schema migrated to
  aggregate would have regressed LE's output column order without that fix.

**How to apply:** when adding or renaming a collapsing dedup mode, grep src for
both `== "collapse"` and `== "none"` and confirm every branch handles the new mode.

AOP deviation: the bundled `default_aop.schema.json` was migrated to format 2.0
(structured key parts + expected_dtype) but kept dedup `mode: none`, not
`aggregate`. AOP has no discriminator column, and `DedupPolicy`/`SchemaDefinition`
require a collapsing mode to name a declared discriminator; forcing aggregate would
break the model invariant and the loader-parity tests. The plan's P12-T2 literally
said "aggregate mode" for AOP, but that is only applicable where a discriminator
exists (LE). See [[mix-builder-signature-mix-base]] for related schema-shape change
caveats.
