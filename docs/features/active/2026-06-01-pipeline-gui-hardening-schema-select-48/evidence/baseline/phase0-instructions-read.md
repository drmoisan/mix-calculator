# Phase 0 — Policy Read Evidence (Remediation cycle 2026-06-01T23-31, Issue #48)

Timestamp: 2026-06-01T23-31

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. .claude/rules/quality-tiers.md (module rigor tiers T1–T4 and gate matrix)
5. .claude/rules/python.md (Python code standards and toolchain)
6. .claude/rules/python-suppressions.md (Python suppression authorization)
7. .claude/rules/self-explanatory-code-commenting.md (commenting/docstring policy)
8. .claude/rules/tonality.md (tone policy)

Files Read:
- CLAUDE.md
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/quality-tiers.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/tonality.md

Output Summary: All required policy files read in the prescribed order prior to any
source change for the 2026-06-01T23-31 remediation cycle. Key constraints noted:
500-line hard file cap (src/gui/app.py at 494, 6 lines headroom); four-stage Python
toolchain (Black, Ruff, Pyright, Pytest) restart-on-change; coverage >= 85% line /
>= 75% branch uniform across tiers with no regression on changed lines; suppressions
only per pre-authorized patterns; evidence only under the canonical
`<FEATURE>/evidence/<kind>/` scheme; mandatory docstrings and intent comments.
