# Phase 0 — Policy Read Evidence

Timestamp: 2026-05-30T07-05

Policy Order: per the `policy-compliance-order` skill and the plan "Required References" section.

Files read (all eight, in order):

1. `CLAUDE.md` (standing instructions; auto-loaded into context)
2. `.claude/rules/general-code-change.md` (auto-loaded into context)
3. `.claude/rules/general-unit-test.md` (auto-loaded into context)
4. `.claude/rules/quality-tiers.md` (auto-loaded into context)
5. `.claude/rules/python.md` (auto-loaded into context)
6. `.claude/rules/python-suppressions.md` (read explicitly via Read tool)
7. `.claude/rules/self-explanatory-code-commenting.md` (read explicitly via Read tool)
8. `.claude/rules/tonality.md` (auto-loaded into context)

Key constraints carried into execution:
- Additive only; protected Feature A and ETL files must not change.
- No new runtime dependency (stdlib `difflib` + Feature A model); `hypothesis` is dev/test only.
- Pyright strict, no suppressions beyond pre-authorized patterns.
- Coverage uniform >= 85% line / >= 75% branch across tiers.
- Tonality: professional, no hyperbole/humor in `MismatchReport.render()`.
- Every new/edited file < 500 lines; per-batch budget 3 production + 3 test files.
