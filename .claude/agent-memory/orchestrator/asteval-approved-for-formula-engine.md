---
name: asteval-approved-for-formula-engine
description: User explicitly approved adding the asteval dependency for the configurable-schema formula engine, overriding the no-new-dependency rule
metadata:
  type: project
---

The user approved adding `asteval` (third-party safe expression evaluator) as a project dependency for the configurable-schema-subsystem epic's runtime formula engine (calculated/derived columns).

**Why:** `.claude/rules/general-code-change.md` forbids new dependencies without explicit user approval. On 2026-05-30 the user chose option "2b" (asteval) over the stdlib-`ast` custom evaluator for the formula engine in the configurable-schema epic. This is the explicit approval that authorization requires.

**How to apply:** When implementing the formula engine (Feature C of the epic), `asteval` may be added to `pyproject.toml` without re-asking. Keep the evaluator behind a small typed adapter module (e.g. `src/schema_formula.py`) so the underlying engine stays swappable. The approval is scoped to this formula-engine use; adding other new dependencies still requires fresh approval. Related: [[derived-aggregates-are-confidential]] (ratio columns are recomputed, not summed — see the Rate_Impacts_corrected.m safeDiv pattern).
