# Phase 0 — Instructions Read

Timestamp: 2026-05-30T07-10

Policy Order:
1. CLAUDE.md (standing instructions; loaded via session context)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/quality-tiers.md
7. .claude/rules/self-explanatory-code-commenting.md
8. .claude/rules/tonality.md

Files read (explicit list):
- CLAUDE.md (standing instructions, supplied in session context)
- .claude/rules/general-code-change.md (cross-language code change policy)
- .claude/rules/general-unit-test.md (cross-language unit test policy)
- .claude/rules/python.md (Python toolchain + coding standards)
- .claude/rules/python-suppressions.md (suppression authorization policy)
- .claude/rules/quality-tiers.md (T1–T4 tier system, uniform coverage thresholds)
- .claude/rules/self-explanatory-code-commenting.md (docstring/comment policy)
- .claude/rules/tonality.md (professional tone policy)

Key obligations confirmed for this feature:
- Toolchain order: Black -> Ruff -> Pyright (strict) -> Pytest (coverage). Restart on any failure/auto-fix.
- Coverage: >= 85% line, >= 75% branch, uniform across tiers; no regression on changed lines.
- Pyright strict, no new suppressions beyond pre-authorized patterns (escalate if unavoidable).
- Every new/edited file < 500 lines.
- No new dependency beyond asteval.
- Mandatory class/function docstrings; loop/branch intent comments.
- Tests: no temp files, no network, no real DB/Excel; presenters unit-tested without QApplication.
