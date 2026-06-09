# Phase 0 — Policy Read Evidence (Issue #60)

Timestamp: 2026-06-09T14-05

Policy Order:
1. CLAUDE.md (standing instructions, always loaded)
2. .claude/rules/general-code-change.md (cross-language code change policy)
3. .claude/rules/general-unit-test.md (cross-language unit test policy)
4. .claude/rules/python.md (Python toolchain and coding standards)
5. .claude/rules/python-suppressions.md (pre-authorized suppression patterns)
6. .claude/rules/quality-tiers.md (T1–T4 module rigor tiers)
7. .claude/rules/benchmark-baselines.md (benchmark baseline provenance)
8. .claude/rules/self-explanatory-code-commenting.md (docstring/commenting policy)

Files Read (explicit list):
- CLAUDE.md (auto-loaded project instructions, plus the .claude/rules/* set surfaced in context)
- .claude/rules/general-code-change.md
- .claude/rules/general-unit-test.md
- .claude/rules/quality-tiers.md
- .claude/rules/benchmark-baselines.md
- .claude/rules/ci-workflows.md
- .claude/rules/tonality.md
- .claude/rules/python.md
- .claude/rules/python-suppressions.md
- .claude/rules/self-explanatory-code-commenting.md

Notes:
- No suppressions are pre-authorized for this work beyond the documented test-mock
  ARG002 pattern already in use by the test fakes; no new noqa/type:ignore is planned.
- 500-line cap applies to all production and test .py files.
- Coverage gates: line >= 85%, branch >= 75%, no regression on changed lines.
