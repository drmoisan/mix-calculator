# Phase 0 — Policy Read Evidence (Issue #43)

Timestamp: 2026-05-30T07-45

Policy Order: CLAUDE.md -> .claude/rules/general-code-change.md -> .claude/rules/general-unit-test.md -> .claude/rules/python.md -> .claude/rules/python-suppressions.md -> .claude/rules/quality-tiers.md -> .claude/rules/self-explanatory-code-commenting.md -> .claude/rules/tonality.md

Files read (in precedence order):

1. CLAUDE.md (standing instructions; loaded via auto-context)
2. .claude/rules/general-code-change.md (cross-language code change policy; design principles, mandatory toolchain loop, 500-line file limit, error handling)
3. .claude/rules/general-unit-test.md (five unit-test properties, coverage thresholds >=85% line / >=75% branch, property/golden/contract test categories, determinism infrastructure)
4. .claude/rules/python.md (Black -> Ruff -> Pyright strict -> Pytest toolchain order; PEP 8 naming; strong typing; pytest rules; prohibited behaviors)
5. .claude/rules/python-suppressions.md (suppression authorization policy; pre-authorized noqa/type:ignore patterns; escalation path; import-untyped only for optional try/except imports)
6. .claude/rules/quality-tiers.md (T1-T4 tier system; uniform coverage thresholds; tier-dependent property-test density, mutation, golden, determinism)
7. .claude/rules/self-explanatory-code-commenting.md (mandatory class/function docstrings; loop/branch intent comments; no numbered NOTE tags)
8. .claude/rules/tonality.md (professional tone; no humor, hyperbole, or decorative metaphor)

Output Summary: All eight policy files read in the required precedence order. Key constraints noted for this feature: additive-only changes, no suppressions outside pre-authorized patterns (asteval-untyped solved by local stub, NOT type:ignore), every new file < 500 lines, T1 modules require >= 1 property test per pure function, coverage >= 85% line / >= 75% branch, deterministic tests with no temp files / network / filesystem.
