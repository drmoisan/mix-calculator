# Phase 0 — Policy reads

Timestamp: 2026-05-29T13-00

Policy Order:
1. CLAUDE.md (standing instructions)
2. `.claude/rules/general-code-change.md` (cross-language code change policy)
3. `.claude/rules/general-unit-test.md` (cross-language unit test policy)
4. Language-specific Python rules:
   - `.claude/rules/python.md`
   - `.claude/rules/python-suppressions.md`
   - `.claude/rules/quality-tiers.md`
   - `.claude/rules/self-explanatory-code-commenting.md`
   - `.claude/rules/tonality.md`

Files read:
- `.claude/rules/general-code-change.md`
- `.claude/rules/general-unit-test.md`
- `.claude/rules/python.md`
- `.claude/rules/python-suppressions.md`
- `.claude/rules/quality-tiers.md`
- `.claude/rules/self-explanatory-code-commenting.md`
- `.claude/rules/tonality.md`

Output Summary: All seven policy files were read in the recorded order. The active work is `minor-audit` for issue #35; AC source is `issue.md` (`## Acceptance Criteria`, AC1-AC10). Python toolchain order applies: Black -> Ruff -> Pyright -> Pytest, restart on any auto-fix or failure. Uniform coverage thresholds apply (>= 85% line, >= 75% branch).
