# Phase 0 — Instructions Read Evidence

Timestamp: 2026-05-28T22-10

Policy Order:
1. CLAUDE.md (standing instructions)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. .claude/rules/python.md (Python-specific toolchain and coding standards)
5. .claude/rules/python-suppressions.md (pre-authorized suppressions)
6. .claude/rules/quality-tiers.md (T1-T4 module rigor tiers)
7. .claude/rules/self-explanatory-code-commenting.md (Google-style docstrings and intent comments)
8. .claude/rules/tonality.md (professional, factual tone)

Files Read:
- CLAUDE.md — not present at repository root; standing instructions sourced from the agent-system prompt block instead (Policy Compliance Order, Atomic Plan Contract, Evidence Conventions, Acceptance Criteria Tracking). Repository policy files under `.claude/rules/` are the operative source of truth for this execution.
- .claude/rules/general-code-change.md — read; 500-line file cap, format-lint-type-test-integration loop, fail-fast error handling, no broad catches, isolate I/O from pure logic, no new dependency without approval.
- .claude/rules/general-unit-test.md — read; coverage thresholds line >= 85% / branch >= 75% uniform across T1-T4; banned APIs in tests (`time.sleep`, `QThread.sleep`, `QTest.qWait`, `qtbot.waitUntil`, `setTimeout`, `Date.now()` outside Clock interface); no temp files; AAA structure; T2 property-test density >= 1 per pure function.
- .claude/rules/python.md — read; Black, Ruff, Pyright strict, Pytest with coverage; full type hints; Google-style docstrings.
- .claude/rules/python-suppressions.md — read; only pre-authorized `# noqa` patterns; `# type: ignore` allowed only for `import-untyped`; escalation requires five distinct refactor attempts before user approval.
- .claude/rules/quality-tiers.md — read; tier source of truth is `quality-tiers.yml`; new `src/gui/runners.py` classified T2 in P1-T1.
- .claude/rules/self-explanatory-code-commenting.md — read; intent-first docstrings, decision-logic comments, no narration comments.
- .claude/rules/tonality.md — read; professional, factual, no hyperbole, no humor, no metaphor unless strictly utilitarian.
