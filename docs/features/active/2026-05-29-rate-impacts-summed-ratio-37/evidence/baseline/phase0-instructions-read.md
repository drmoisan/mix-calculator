# Phase 0 — Instructions Read (Issue #37)

Timestamp: 2026-05-29T21-59

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/self-explanatory-code-commenting.md
7. .claude/rules/quality-tiers.md
8. .claude/rules/tonality.md

Files read (explicit list):
- CLAUDE.md (loaded via session context)
- .claude/rules/general-code-change.md (loaded via session context)
- .claude/rules/general-unit-test.md (loaded via session context)
- .claude/rules/python.md (loaded via session context)
- .claude/rules/python-suppressions.md (loaded via session context)
- .claude/rules/self-explanatory-code-commenting.md (loaded via session context)
- .claude/rules/quality-tiers.md (loaded via session context)
- .claude/rules/tonality.md (loaded via session context)

Notes:
- Suppressions (`# noqa`, `# type: ignore`) require pre-authorization per python-suppressions.md. None planned.
- Scope locked to src/mix_rate_impacts.py (production) and tests/test_mix_rate_impacts.py (test).
- Coverage thresholds uniform across tiers: line >= 85%, branch >= 75%.
