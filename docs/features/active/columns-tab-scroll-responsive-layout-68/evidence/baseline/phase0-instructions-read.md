---
Timestamp: 2026-06-16T09-30
Policy Order:
  1. CLAUDE.md (standing instructions)
  2. .claude/rules/general-code-change.md
  3. .claude/rules/general-unit-test.md
  4. .claude/rules/python.md
  5. .claude/rules/python-suppressions.md
  6. .claude/rules/quality-tiers.md
  7. .claude/rules/self-explanatory-code-commenting.md
---

## Files Read

### [P0-T1] `.claude/rules/general-code-change.md`
Status: READ
Key directives noted:
- Design principles: simplicity first, reusability, extensibility, separation of concerns.
- File size limit: 500 lines max for production/test/reusable script files.
- Mandatory toolchain loop: format → lint → type-check → architecture → unit → contract → integration (restart from step 1 if any fails).
- Error handling: fail fast, no silent ignores.
- Naming: snake_case for Python functions/variables, PascalCase for classes.

### [P0-T2] `.claude/rules/general-unit-test.md`
Status: READ
Key directives noted:
- Line coverage >= 85%, branch coverage >= 75% (all tiers T1–T4).
- Five properties: independence, isolation, fast, deterministic, readable.
- Arrange–Act–Assert structure required.
- No external dependencies (no temp files) in unit tests.
- Property-based tests required for T1 and T2 modules.

### [P0-T3] `.claude/rules/python.md` and `.claude/rules/python-suppressions.md`
Status: READ
Key directives noted:
- Toolchain: Black → Ruff → Pyright → Pytest.
- Strong typing; all public methods must have full type hints.
- Suppressions require pre-authorization per python-suppressions.md.
- `# type: ignore[override]` pre-authorized for PySide6 Qt event handler overrides in src/gui/.
- Pyright strict mode; avoid Any.

### [P0-T4] `.claude/rules/quality-tiers.md` and `.claude/rules/self-explanatory-code-commenting.md`
Status: READ
Key directives noted:
- quality-tiers.md: T1–T4 tiers. Coverage uniform: line >= 85%, branch >= 75%.
- self-explanatory-code-commenting.md: Every class and method must have a docstring. Loops need intent comments. Branches need decision-logic comments.
