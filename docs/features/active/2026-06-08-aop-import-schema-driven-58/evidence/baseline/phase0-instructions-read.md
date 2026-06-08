# Phase 0 — Policy Read Evidence

Timestamp: 2026-06-08T14-30

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. Language/domain-specific rules (Python files in scope):
   - .claude/rules/python.md
   - .claude/rules/python-suppressions.md
   - .claude/rules/quality-tiers.md
   - .claude/rules/self-explanatory-code-commenting.md
   - .claude/rules/tonality.md

Files Read:
- CLAUDE.md (loaded into context via system reminder)
- .claude/rules/general-code-change.md (loaded into context)
- .claude/rules/general-unit-test.md (loaded into context)
- .claude/rules/python.md (read this session)
- .claude/rules/python-suppressions.md (read this session)
- .claude/rules/quality-tiers.md (loaded into context)
- .claude/rules/self-explanatory-code-commenting.md (read this session)
- .claude/rules/tonality.md (loaded into context)

Key constraints acknowledged for this feature:
- Toolchain order: black -> ruff -> pyright -> pytest (--cov --cov-branch); restart on any change.
- Coverage >= 85% line / >= 75% branch; no regression on changed lines.
- No new dependencies; no new suppressions (python-suppressions escalation path required).
- 500-line file cap for production/test/script files.
- Docstrings mandatory for all classes/functions; intent comments for loops/branches.
- Professional tone in all authored content.
- src/schema_loader.py is T1 (property-test + mutation obligation).
