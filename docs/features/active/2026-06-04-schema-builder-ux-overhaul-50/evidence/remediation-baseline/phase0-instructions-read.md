# Phase 0 — Policy Read Evidence (Remediation Cycle 2)

Timestamp: 2026-06-05T21-27

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/quality-tiers.md
7. .claude/rules/self-explanatory-code-commenting.md
8. .claude/rules/tonality.md

Files read (explicit list):
- CLAUDE.md (standing instructions via loaded rule set; no repo-root CLAUDE.md file present)
- .claude/rules/general-code-change.md (loaded via project instructions)
- .claude/rules/general-unit-test.md (loaded via project instructions)
- .claude/rules/python.md (loaded via project instructions)
- .claude/rules/python-suppressions.md (loaded via project instructions)
- .claude/rules/quality-tiers.md (loaded via project instructions)
- .claude/rules/self-explanatory-code-commenting.md (loaded via project instructions)
- .claude/rules/tonality.md (loaded via project instructions)

Cycle scope: B1 (split over-cap test file `tests/gui/test_schema_builder_presenter.py`,
506 lines) and N4 (coverage pragma on two TYPE_CHECKING-only Protocol contract modules:
`src/gui/_columns_tab_protocol.py`, `src/gui/_key_tab_protocol.py`). No production behavior
changes. R1-R6 remain CLOSED and are not reopened.
Tier: T3 (adapters & UI), Python (PySide6).
Governing gates: 500-line file-size cap (general-code-change.md); uniform coverage
thresholds line >= 85%, branch >= 75%, no regression on changed lines
(general-unit-test.md / quality-tiers.md); Black -> Ruff -> Pyright -> Pytest toolchain
order (python.md), Poetry prefixed with `env -u VIRTUAL_ENV`, pytest-qt with
`QT_QPA_PLATFORM=offscreen`.
