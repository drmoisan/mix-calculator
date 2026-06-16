# Phase 0 — Policy Instructions Read

Timestamp: 2026-06-16T18-44

Policy Order: per `.claude/skills/policy-compliance-order` baseline order

Files read (in required order):
1. `CLAUDE.md` (standing instructions; auto-loaded)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/python.md`
5. `.claude/rules/python-suppressions.md`
6. `.claude/rules/quality-tiers.md`
7. `.claude/rules/self-explanatory-code-commenting.md`

Additional project rules in context: `.claude/rules/tonality.md`, `.claude/rules/benchmark-baselines.md`, `.claude/rules/ci-workflows.md`.

Key constraints acknowledged:
- 500-line hard cap on all production AND test files.
- Suppressions limited to pre-authorized patterns (`call-overload` for `setParent(None)`, `override` for Qt event handlers); any new suppression need is a blocking scope-change.
- D-1: do not modify `src/schema_formula.py` or the FormulaEvaluator grammar; bracket handling lives only in the new `_schema_builder_derived_format.py`; stored form is `col("Name")`.
- D-2: Key tab simplified to multi-select; `KeySpec`/`KeyPart` model and key loader unchanged.
- D-3: relax `DedupPolicy` invariant only for the new `auto` mode; LE explicit path preserved.
- Coverage: line >= 85%, branch >= 75%, no regression on changed lines.
- Committed fixtures must be masked/synthetic.
- Evidence only under `docs/features/active/2026-06-16-schema-builder-ux-overhaul-72/evidence/<kind>/`.
