# Phase 0 — Policy Instructions Read

Timestamp: 2026-05-26T14-03

Policy Order: The repository policy files were read in the precedence order
defined by `policy-compliance-order` and the plan's P0-T1 task.

Files read (in order):

1. `CLAUDE.md` (standing instructions; auto-loaded into context)
2. `.claude/rules/general-code-change.md` (cross-language code change policy)
3. `.claude/rules/general-unit-test.md` (cross-language unit test policy)
4. `.claude/rules/python.md` (Python code standards: Black/Ruff/Pyright/Pytest toolchain)
5. `.claude/rules/python-suppressions.md` (authorized suppression patterns only)
6. `.claude/rules/self-explanatory-code-commenting.md` (mandatory docstrings + intent comments)
7. `.claude/rules/quality-tiers.md` (T1–T4 tiers; uniform coverage line >= 85%, branch >= 75%)
8. `.claude/rules/tonality.md` (professional tone; no humor/hyperbole)

Additional repository rule files present and considered for scope:
`.claude/rules/benchmark-baselines.md`, `.claude/rules/ci-workflows.md` (not in
this feature's code scope; no benchmark baselines or CI workflow steps are modified).

Output Summary: All eight required policy files read in precedence order. Key
operative constraints for this feature: route unknown-typed pandas/openpyxl
members through `src/pandas_io.py` (no Pyright suppressions); coverage line
>= 85% / branch >= 75% uniform across tiers; no new third-party dependency;
every file < 500 lines; mandatory docstrings and intent comments; in-memory test
fixtures only (no temp files); professional tone.
