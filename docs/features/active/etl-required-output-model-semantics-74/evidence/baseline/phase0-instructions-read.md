# Phase 0 — Policy Read Evidence (cycle 2)

Timestamp: 2026-06-17T13-10

Policy Order: per `.claude/skills/policy-compliance-order` — CLAUDE.md first (standing
instructions, always loaded), then cross-language code-change policy, then cross-language
unit-test policy, then tier rules, then Python language-specific rules, then the Python
suppression policy, then the commenting policy applicable to the Python edits in scope.

Files read (in order):
- CLAUDE.md (standing instructions; auto-loaded)
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/quality-tiers.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/self-explanatory-code-commenting.md

Notes:
- Scope (cycle 2): R1 loader-ordering decouple in `src/_schema_loader_helpers.py`; R2 AOP
  measure `required`-flag flip in `src/schemas/default_aop.schema.json`; R3 AOP accessor
  test in `tests/test_default_schemas.py`. R1 lands before R2.
- Python toolchain order: black -> ruff check -> pyright -> pytest --cov --cov-branch.
  Restart from black on any failure or file change.
- Coverage thresholds uniform across tiers: line >= 85%, branch >= 75%; no regression on
  changed lines.
- 500-line file cap on `src/_schema_loader_helpers.py` (465 lines pre-change); keep the R1
  change minimal or extract one small helper.
- No suppressions authorized for this change; no dependencies may be added.
- Binding oracle: `tests/test_schema_loader_parity_aop.py` and
  `tests/test_schema_loader_parity_le.py` must pass UNCHANGED.
