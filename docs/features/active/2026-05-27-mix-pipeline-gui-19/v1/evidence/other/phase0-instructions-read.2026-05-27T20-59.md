# Phase 0 — Policy Instructions Read

Timestamp: 2026-05-27T20-59

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. Language-specific rules (Python files in scope): .claude/rules/python.md, .claude/rules/python-suppressions.md
5. Domain/quality rules: .claude/rules/quality-tiers.md, .claude/rules/self-explanatory-code-commenting.md, .claude/rules/tonality.md

Files read (explicit list):
- CLAUDE.md
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/quality-tiers.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/tonality.md

Key constraints internalized:
- Toolchain loop order: Black -> Ruff -> Pyright (strict) -> Pytest (coverage). Restart on any failure or file change.
- Coverage gate: line >= 85%, branch >= 75%, no regression on changed lines.
- No production/test/script file may exceed 500 lines.
- No runtime temp files and no external dependencies in unit tests; deterministic tests only.
- Constructor injection only; no DI framework.
- Suppressions only per pre-authorized patterns in python-suppressions.md (ARG002 mock-signature in tests; import-untyped).
- Confidentiality: no real SKU Description/Category, customer, SKU, price, or discount values.
- Pyright strict with no new Any and no strictness reduction.
- Professional tone; no humor, hyperbole, or decorative metaphor.
