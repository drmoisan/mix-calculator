# Phase 0 — Policy Instructions Read

Timestamp: 2026-06-07T20-45

Policy Order: CLAUDE.md (harness-auto-loaded) -> .claude/rules/general-code-change.md -> .claude/rules/general-unit-test.md -> .claude/rules/python.md -> .claude/rules/python-suppressions.md -> .claude/rules/quality-tiers.md -> .claude/rules/self-explanatory-code-commenting.md -> .claude/rules/tonality.md

Files read (in required order):
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/quality-tiers.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/tonality.md

Note: CLAUDE.md is auto-loaded by the harness and is not a files-to-read item per the plan (P0-T1).

Key constraints absorbed:
- Mandatory toolchain loop: Black -> Ruff -> Pyright -> Pytest (--cov --cov-branch), restart on any change/failure.
- Coverage: line >= 85%, branch >= 75%, uniform across tiers; no regression on changed lines.
- File size cap: 500 lines for production/test/script files.
- Suppressions only per pre-authorized patterns in python-suppressions.md.
- Docstrings mandatory for every class/function; intent comments on loops and branches.
- No temp files in tests; pure in-memory fixtures.
- Professional tone; no emojis, no hyperbole.
