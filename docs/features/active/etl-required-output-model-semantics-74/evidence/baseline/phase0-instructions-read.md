# Phase 0 — Policy Read Evidence

Timestamp: 2026-06-17T12-40

Policy Order: CLAUDE.md; .claude/rules/general-code-change.md; .claude/rules/general-unit-test.md; .claude/rules/python.md; .claude/rules/python-suppressions.md; .claude/rules/quality-tiers.md; .claude/rules/self-explanatory-code-commenting.md; .claude/rules/tonality.md

Files read (in order):
- CLAUDE.md (standing instructions; auto-loaded)
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/quality-tiers.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/tonality.md

Notes:
- Python toolchain order confirmed: black -> ruff -> pyright -> pytest --cov --cov-branch. Restart from black on any failure or file change.
- Coverage thresholds uniform across tiers: line >= 85%, branch >= 75%; no regression on changed lines.
- 500-line file cap on production and test files; extract a helper module rather than exceeding it.
- Suppressions only if pre-authorized in python-suppressions.md; otherwise fix root cause.
