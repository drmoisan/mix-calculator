# Phase 0 — Policy Reads Evidence

Timestamp: 2026-06-08T17-45

Policy Order: CLAUDE.md -> .claude/rules/general-code-change.md -> .claude/rules/general-unit-test.md -> .claude/rules/python.md

Files read:
- CLAUDE.md (standing instructions; loaded via project context)
- .claude/rules/general-code-change.md (cross-language code change policy; 500-line file-size cap, mandatory toolchain loop)
- .claude/rules/general-unit-test.md (cross-language unit test policy; coverage >= 85% line / >= 75% branch, no temp files)
- .claude/rules/python.md (Python toolchain: Black -> Ruff -> Pyright -> Pytest; coverage thresholds; patch-at-import-location)
- .claude/rules/quality-tiers.md (T1-T4 tier system; uniform coverage thresholds; loaded via project context)

Notes:
- This is a test-only split refactor to clear Blocking finding B1 (two test files over the 500-line cap).
- Python tooling is invoked with `env -u VIRTUAL_ENV poetry run <tool>` per orchestrator constraint and the Poetry virtual-env quirk.
