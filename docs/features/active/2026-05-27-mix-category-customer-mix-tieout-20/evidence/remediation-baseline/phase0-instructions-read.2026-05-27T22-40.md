# Phase 0 — Policy Read (Remediation Cycle)

Timestamp: 2026-05-27T22-40

Policy Order:
1. CLAUDE.md
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/self-explanatory-code-commenting.md
7. .claude/rules/quality-tiers.md
8. .claude/rules/tonality.md
9. .claude/rules/benchmark-baselines.md
10. .claude/rules/ci-workflows.md

Files Read:
- CLAUDE.md (auto-loaded by Claude Code via system instructions)
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/self-explanatory-code-commenting.md
- .claude/rules/quality-tiers.md
- .claude/rules/tonality.md
- .claude/rules/benchmark-baselines.md (auto-loaded via project instructions)
- .claude/rules/ci-workflows.md (auto-loaded via project instructions)

File Size Limit (quotation from `.claude/rules/general-code-change.md`):

> ## File Size Limit
>
> - No production code, test code, or reusable script file may exceed **500 lines**.
> - Exceptions: temporary throwaway scripts created and deleted within an agent session; raw text fixtures for language-processing test data; Markdown documentation files.

Test-module placement excerpts:

From `.claude/rules/general-unit-test.md`:
> Group related tests logically within the same file or test class.

From `.claude/rules/general-code-change.md`:
> 2. **Reusability** — Factor out logic that is clearly reusable. Avoid copy-paste; share behavior via composition or helper methods.
> 4. **Separation of concerns** — Keep pure logic (transforms, calculations, parsing) separate from I/O (disk, network, DB), UI/CLI, and framework-specific glue.

These excerpts support the cohesive-split design in the plan: shared fixture helpers live in a single non-test module (`tests/_mix_rollups_fixtures.py`), and tests are split by topic (general rollup/layer/stage vs. AC8 four-layer tie-out).

Additional test-module placement excerpt from `.claude/rules/python.md`:
> Organize tests to mirror code structure (for example, `tests/test_module_name.py` for `module_name.py`).

