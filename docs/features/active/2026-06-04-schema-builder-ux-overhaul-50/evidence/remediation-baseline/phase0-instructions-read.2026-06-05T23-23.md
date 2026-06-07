# Phase 0 — Policy Instructions Read (Cycle 4 Remediation)

Timestamp: 2026-06-05T23-23

Policy Order: per `.claude/skills/policy-compliance-order` baseline ordering — standing instructions first, then cross-language code-change policy, then cross-language unit-test policy, then language-/domain-specific Python rules.

Files read (in order):
1. `CLAUDE.md` (standing project instructions, auto-loaded)
2. `.claude/rules/general-code-change.md` (cross-language code change policy)
3. `.claude/rules/general-unit-test.md` (cross-language unit test policy)
4. `.claude/rules/python.md` (Python code standards)
5. `.claude/rules/python-suppressions.md` (Python suppression authorization policy)
6. `.claude/rules/quality-tiers.md` (T1–T4 rigor tiers, coverage thresholds)
7. `.claude/rules/self-explanatory-code-commenting.md` (docstring/comment policy)
8. `.claude/rules/tonality.md` (professional tone policy)

Key constraints carried into execution:
- Toolchain order: Black -> Ruff -> Pyright -> Pytest; restart on any change/failure.
- Coverage thresholds uniform: line >= 85%, branch >= 75%; no regression on changed lines.
- File-size limit: no production/test/reusable-script file > 500 lines.
- Suppressions require pre-authorization or explicit user approval (`.claude/rules/python-suppressions.md`).
- Scope confined to `src/schema_formula.py` and `tests/test_schema_formula.py`.
