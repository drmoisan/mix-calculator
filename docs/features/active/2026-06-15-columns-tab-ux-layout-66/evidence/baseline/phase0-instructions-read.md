# Phase 0 — Policy Instructions Read

Timestamp: 2026-06-15T21-45

Policy Order:
1. CLAUDE.md — not present at repo root (no CLAUDE.md file found); auto-loaded rule files cover policy
2. .claude/rules/general-code-change.md — read (cross-language code change policy)
3. .claude/rules/general-unit-test.md — read (cross-language unit test policy)
4. .claude/rules/python.md — read (Python toolchain and coding standards)
5. .claude/rules/python-suppressions.md — read (pre-authorized suppression patterns)
6. .claude/rules/quality-tiers.md — read (module rigor tier system)

## Files Read

- `.claude/rules/general-code-change.md` — confirmed loaded via auto-inject
- `.claude/rules/general-unit-test.md` — confirmed loaded via auto-inject
- `.claude/rules/python.md` — confirmed loaded via auto-inject
- `.claude/rules/python-suppressions.md` — confirmed loaded via auto-inject
- `.claude/rules/quality-tiers.md` — confirmed loaded via auto-inject
- `.claude/rules/tonality.md` — confirmed loaded via auto-inject
- `.claude/rules/self-explanatory-code-commenting.md` — confirmed loaded via auto-inject
- `.claude/rules/benchmark-baselines.md` — confirmed loaded via auto-inject
- `.claude/rules/ci-workflows.md` — confirmed loaded via auto-inject

## Key Policy Constraints Noted

- File size limit: 500 lines max per production/test file
- Toolchain order: black -> ruff -> pyright -> pytest
- Coverage: >= 85% line, >= 75% branch
- Suppression policy: pre-authorized patterns only
- `_columns_tab_drag.py` currently at 499 lines — must not exceed 500 after changes
