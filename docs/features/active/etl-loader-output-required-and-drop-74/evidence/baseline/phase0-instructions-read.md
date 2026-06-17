# Phase 0 — Policy Instructions Read (CF2, issue #74)

Timestamp: 2026-06-17T14-05

Policy Order: per `.claude/skills/policy-compliance-order` and plan [P0-T1].

Files read (in order):
1. CLAUDE.md (standing instructions; loaded into context)
2. .claude/rules/general-code-change.md (loaded into context)
3. .claude/rules/general-unit-test.md (loaded into context)
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/quality-tiers.md (loaded into context)
7. .claude/rules/self-explanatory-code-commenting.md
8. .claude/rules/tonality.md (loaded into context)

Key constraints absorbed for this work:
- Toolchain order: black -> ruff -> pyright -> pytest (restart on any change/failure).
- Coverage >= 85% line, >= 75% branch; no regression on changed lines.
- 500-line cap on all production/test/script files.
- No suppressions except pre-authorized patterns in python-suppressions.md.
- Mandatory docstrings for every class and function; intent comments on loops/branches.
- Binding constraint: tests/test_schema_loader_parity_aop.py and tests/test_schema_loader_parity_le.py must pass UNCHANGED (zero output regression).
