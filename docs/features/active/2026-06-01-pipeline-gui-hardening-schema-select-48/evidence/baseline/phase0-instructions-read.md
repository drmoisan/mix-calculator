# Phase 0 — Policy Read Evidence (Issue #48)

Timestamp: 2026-06-01T12-05

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. .claude/rules/python.md (Python code standards)
5. .claude/rules/python-suppressions.md (Python suppression authorization)
6. .claude/rules/quality-tiers.md (module rigor tiers T1–T4)
7. .claude/rules/self-explanatory-code-commenting.md (commenting/docstring policy)

Files Read:
- CLAUDE.md (loaded via path-scoped rules; benchmark-baselines, ci-workflows, general-code-change, general-unit-test, quality-tiers, tonality)
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/quality-tiers.md
- .claude/rules/self-explanatory-code-commenting.md

Output Summary: All required policy files read in the prescribed order prior to any
source change. Key constraints noted: 500-line hard file cap; four-stage Python
toolchain (Black, Ruff, Pyright, Pytest) restart-on-change; coverage >= 85% line /
>= 75% branch uniform across tiers; T2 modules require >= 1 property test per pure
function and no untyped escape hatches; suppressions only per pre-authorized patterns;
evidence only under the canonical `<FEATURE>/evidence/<kind>/` scheme.
