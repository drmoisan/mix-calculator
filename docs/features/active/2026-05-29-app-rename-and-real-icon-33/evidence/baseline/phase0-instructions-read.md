# Phase 0 — Policy Instructions Read

Timestamp: 2026-05-29T20-00

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. Language-specific rules: .claude/rules/python.md, .claude/rules/python-suppressions.md
5. Domain rules: .claude/rules/self-explanatory-code-commenting.md, .claude/rules/quality-tiers.md, .claude/rules/tonality.md

Files Read:
- [P0-T1] .claude/rules/general-code-change.md — cross-language code change policy; precedence acknowledged over agent defaults.
- [P0-T2] .claude/rules/general-unit-test.md — confirmed: no real temp files in tests; >= 85% line / >= 75% branch coverage; AAA structure.
- [P0-T3] .claude/rules/quality-tiers.md — uniform coverage thresholds T1-T4; modules in scope (build scripts T4, GUI wiring T3) follow uniform >= 85% line / >= 75% branch; quality-tiers.yml is source of truth for project classification.
- [P0-T4] .claude/rules/python.md — confirmed Python toolchain stages Black -> Ruff -> Pyright -> Pytest with restart-on-change semantics.
- [P0-T5] .claude/rules/python-suppressions.md — confirmed only pre-authorized noqa/type-ignore patterns may be used; new suppressions outside that list require explicit user approval.
- [P0-T6] .claude/rules/self-explanatory-code-commenting.md — confirmed mandatory docstrings (purpose/args/returns/raises/side-effects), intent comments on loops/comprehensions, decision-logic comments on non-trivial branching.
- [P0-T7] .claude/rules/tonality.md — confirmed professional tone for human-readable strings, doc updates, READMEs; no hyperbole, no jokes, metaphor restricted to utilitarian use.

Output Summary: All seven policy files read; precedence acknowledged; toolchain and suppression rules captured.
