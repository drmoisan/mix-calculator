Timestamp: 2026-05-28T23-20

Policy Order:
1. CLAUDE.md (standing instructions; not present at repo root in this worktree — recorded as absent during the read pass)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/quality-tiers.md
7. .claude/rules/self-explanatory-code-commenting.md
8. .claude/rules/tonality.md

Files read (in order):
- CLAUDE.md — NOT FOUND at repo root; the project relies on rule files under .claude/rules and skill prompts as standing instructions.
- .claude/rules/general-code-change.md — loaded by skill prompt.
- .claude/rules/general-unit-test.md — loaded by skill prompt.
- .claude/rules/python.md — read for this phase.
- .claude/rules/python-suppressions.md — read for this phase.
- .claude/rules/quality-tiers.md — loaded by skill prompt.
- .claude/rules/self-explanatory-code-commenting.md — read for this phase.
- .claude/rules/tonality.md — loaded by skill prompt.

Notes:
- The cycle-1 remediation operates only on Python files; the Python rules and
  the docstring/commenting rule are the load-bearing standards for this cycle.
- Suppressions policy unchanged from v2 execution; no new suppression patterns
  are required by the planned diff.
- Tonality: professional; no humor, hyperbole, metaphor.
- Banned APIs in tests (`time.sleep`, `QThread.sleep`, `QTest.qWait`,
  `qtbot.waitUntil`) confirmed; the planned edits do not reintroduce them.
