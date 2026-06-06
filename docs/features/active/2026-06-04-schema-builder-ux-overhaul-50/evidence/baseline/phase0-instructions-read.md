# Phase 0 — Instructions Read (Cycle 3 Remediation)

Timestamp: 2026-06-05T23-08

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/quality-tiers.md
5. .claude/rules/python.md
6. .claude/rules/python-suppressions.md
7. .claude/rules/self-explanatory-code-commenting.md
8. .claude/rules/tonality.md

Files read:
- CLAUDE.md
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/quality-tiers.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/tonality.md

Additional authoritative references read:
- docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md (v1.0)
- docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md
- docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/issue.md
- docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/remediation-inputs.2026-06-05T22-30.md

Key constraints noted:
- T3 tier; coverage line >= 85%, branch >= 75%, no regression on changed lines.
- 500-line per-file cap on production, test, and reusable script files.
- Confidentiality: no real workbook values or proprietary source column names in any committed file.
- Python toolchain order: Black -> Ruff -> Pyright -> Pytest, repeated until a clean single pass.
- Poetry must be prefixed with `env -u VIRTUAL_ENV`; pytest-qt requires QT_QPA_PLATFORM=offscreen.
- No unauthorized suppressions per python-suppressions.md.
