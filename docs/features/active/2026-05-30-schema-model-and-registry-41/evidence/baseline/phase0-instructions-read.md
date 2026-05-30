# Phase 0 — Policy Read Evidence (Issue #41)

Timestamp: 2026-05-30T07-02

Policy Order: per `policy-compliance-order` and the plan's Required References section.

Files read (in required order):

1. `CLAUDE.md` (standing instructions, auto-loaded into context)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/python.md`
5. `.claude/rules/python-suppressions.md`
6. `.claude/rules/self-explanatory-code-commenting.md`
7. `.claude/rules/quality-tiers.md`
8. `.claude/rules/tonality.md`

Additional project policy rules loaded into context this session:
`.claude/rules/benchmark-baselines.md`, `.claude/rules/ci-workflows.md`.

Key constraints applied to this feature:

- Additive only; protected files must not be modified: `src/normalize_le.py`,
  `src/load_aop.py`, `src/_load_aop_helpers.py`, `src/etl_columns.py`,
  `src/etl_key.py`, `src/etl_totals.py`, transforms, GUI, CLI.
- No new runtime dependency (stdlib only); `hypothesis` is an existing dev dependency.
- Every new file < 500 lines.
- Tests must not create temp files or touch network/real filesystem; reading
  committed `src/schemas/*.json` package resources is permitted.
- Pyright strict, no suppressions beyond pre-authorized patterns.
- New schema modules classified T2 (Core); coverage >= 85% line / >= 75% branch.
